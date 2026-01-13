import pandas as pd
from unidecode import unidecode
import glob
import os


# ============================================================
# 1. NORMALIZACIÓN DE TEXTO
# ============================================================

def norm_nombre(s):
    """
    Normaliza nombres de provincia/cantón/parroquia:
    - strip espacios
    - colapsa espacios múltiples
    - quita acentos
    - pasa a minúsculas
    """
    if pd.isna(s):
        return None
    s = str(s).strip()
    s = " ".join(s.split())
    s = unidecode(s).lower()
    return s


def norm_provincia(s):
    """
    Normaliza provincia y convierte a None si es '0' o 'zona no delimitada'.
    """
    s_norm = norm_nombre(s)
    if s_norm in ['0', 'zona no delimitada']:
        return None
    return s_norm


# ============================================================
# 2. CARGAR DATASET DE EMERGENCIAS
# ============================================================

def load_emergencias(path_csv: str) -> pd.DataFrame:
    """
    Lee el CSV de emergencias con los parámetros correctos.
    """
    df = pd.read_csv(path_csv, sep=";", encoding="utf-8")
    df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
    return df


# ============================================================
# 3. LIMPIEZA DE EMERGENCIAS
# ============================================================

def clean_emergencias(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia el dataset de emergencias:
    - Normaliza texto en provincia, cantón, parroquia, servicio, subtipo
    - Marca provincias inválidas ('0', 'zona no delimitada') como None
    - Limpia Cod_Parroquia y la deja como string (6 dígitos cuando aplique)
    - Crea columnas prov_norm, canton_norm, parr_norm
    - Elimina filas sin provincia (None)
    """
    df0 = df.copy()

    # Normalizar columnas de texto
    text_cols = ['provincia', 'Canton', 'Parroquia', 'Servicio', 'Subtipo']
    for col in text_cols:
        if col not in df0.columns:
            continue
        if col == 'provincia':
            df0[col] = df0[col].apply(norm_provincia)
        else:
            df0[col] = df0[col].apply(norm_nombre)
            
    if 'Cod_Parroquia' in df0.columns:
        df0['Cod_Parroquia'] = (
            df0['Cod_Parroquia']
            .astype(str)
            .str.replace(r'\.0$', '', regex=True)
            .str.strip()
        )

    df0['Cod_Parroquia'] = df0['Cod_Parroquia'].apply(
        lambda x: x.zfill(6) if x.isdigit() and len(x) <= 6 else x
    )

    

    # Columnas normalizadas explícitas (para el match con INEC)
    df0['prov_norm']   = df0['provincia'].apply(norm_nombre)
    df0['canton_norm'] = df0['Canton'].apply(norm_nombre)
    df0['parr_norm']   = df0['Parroquia'].apply(norm_nombre)

    # Eliminar filas sin provincia (None/NaN) porque no se pueden georreferenciar
    antes = len(df0)
    df0 = df0[df0['provincia'].notna()].copy()
    despues = len(df0)
    print(f"[clean_emergencias] Filas eliminadas por provincia None: {antes - despues}")

    return df0


# ============================================================
# 4. CARGAR Y PREPARAR CODIFICACIÓN INEC 2021
# ============================================================

def load_inec_codificacion(dataI: pd.DataFrame) -> pd.DataFrame:
    """
    Lee el archivo CODIFICACIÓN_2021 del INEC y prepara un DataFrame de referencia
    con:
    - DPA_PARROQ (código parroquial de 6 dígitos)
    - Nombres oficiales de provincia, cantón, parroquia
    - Versiones normalizadas para el match (prov_norm, canton_norm, parr_norm)
    """
    cols = ['DPA_PROVIN', 'DPA_DESPRO',
            'DPA_CANTON', 'DPA_DESCAN',
            'DPA_PARROQ', 'DPA_DESPAR']
    inec_ref = dataI[cols].copy()
    
    # Normalizar nombres
    inec_ref['prov_norm']   = inec_ref['DPA_DESPRO'].apply(norm_nombre)
    inec_ref['canton_norm'] = inec_ref['DPA_DESCAN'].apply(norm_nombre)
    inec_ref['parr_norm']   = inec_ref['DPA_DESPAR'].apply(norm_nombre)

    return inec_ref


# ============================================================
# 5. MAPEAR PARROQUIAS A CÓDIGO INEC
# ============================================================

def mapear_parroquias_inec(df_emerg: pd.DataFrame, inec_ref: pd.DataFrame) -> pd.DataFrame:
    """
    Mapea el código de parroquia de df_emerg contra el catálogo INEC.
    
    Si Cod_Parroquia coincide con DPA_PARROQ -> asigna el código.
    Si NO coincide -> coloca NaN.
    """
    # Nos aseguramos que los códigos estén limpios y comparables
    df = df_emerg.copy()
    df['Cod_Parroquia'] = (
        df['Cod_Parroquia']
        .astype(str)
        .str.replace(r'\.0$', '', regex=True)
        .str.strip()
        .str.zfill(6)
    )
    
    inec = inec_ref.copy()
    inec['DPA_PARROQ'] = (
        inec['DPA_PARROQ']
        .astype(str)
        .str.replace(r'\.0$', '', regex=True)
        .str.strip()
        .str.zfill(6)
    )

    # Merge SOLO por código parroquial
    df_geo = df.merge(
        inec[['DPA_PARROQ']],   # solo necesitamos el código oficial
        left_on='Cod_Parroquia',
        right_on='DPA_PARROQ',
        how='left'
    )

    return df_geo



# ============================================================
# 6. REPORTE DE GEOREFERENCIACIÓN
# ============================================================

def reporte_geocodificacion(df_geo: pd.DataFrame) -> None:
    """
    Imprime un resumen de qué tan bien se mapeó a INEC:
    - % de filas con código parroquial asignado
    - ejemplos de parroquias sin match
    """
    total = len(df_geo)
    con_codigo = df_geo['DPA_PARROQ'].notna().sum()
    sin_codigo = total - con_codigo

    print("=== REPORTE GEOREFERENCIACIÓN ===")
    print(f"Filas totales: {total}")
    print(f"Con código INEC (DPA_PARROQ): {con_codigo} ({con_codigo/total*100:.2f}%)")
    print(f"Sin código INEC: {sin_codigo} ({sin_codigo/total*100:.2f}%)")

    if sin_codigo > 0:
        print("\nEjemplos de parroquias SIN match (provincia / cantón / parroquia):")
        ejemplos = (
            df_geo[df_geo['DPA_PARROQ'].isna()]
            [['provincia', 'Canton', 'Parroquia']]
            .drop_duplicates()
            .head(300)
        )
        print(ejemplos)


# ============================================================
# 7. PIPELINE COMPLETO
# ============================================================

def pipeline_georreferenciacion(path_emerg: str, dataI: pd.DataFrame) -> pd.DataFrame:
    """
    Ejecuta todo el flujo:
    1) Carga emergencias
    2) Limpia texto, provincias y Cod_Parroquia
    3) Carga catálogo INEC
    4) Mapea parroquias y agrega DPA_PARROQ
    5) Imprime reporte
    Devuelve df_geo (listo para unir con shapefile).
    """
    print(f"\n{'='*60}")
    print(f"Procesando: {os.path.basename(path_emerg)}")
    print(f"{'='*60}")
    
    print("1) Cargando emergencias...")
    df = load_emergencias(path_emerg)

    print("2) Limpiando emergencias...")
    df_clean = clean_emergencias(df)

    print("3) Cargando codificación INEC...")
    inec_ref = load_inec_codificacion(dataI)

    print("4) Mapeando parroquias a INEC...")
    df_geo = mapear_parroquias_inec(df_clean, inec_ref)

    print("5) Reporte de georreferenciación:")
    reporte_geocodificacion(df_geo)

    return df_geo


# ============================================================
# 8. PROCESAR TODOS LOS ARCHIVOS
# ============================================================

def procesar_todos_emergencias():
    """
    Encuentra todos los archivos emergencias_*.csv y los procesa.
    Guarda cada uno con el nombre: emergencias_X_georreferenciado.csv
    """
    # Cargar el archivo de codificación INEC
    print("Cargando CODIFICACIÓN_2021.xlsx...")
    dataI = pd.read_excel("CODIFICACIÓN_2021.xlsx", header=0, skiprows=1)
    dataI = dataI.dropna(axis=1, how="any")
    print(f"Codificación INEC cargada: {dataI.shape[0]} parroquias")
    
    # Encontrar todos los archivos emergencias_*.csv
    archivos_emergencias = glob.glob("emergencias_*.csv")
    
    if not archivos_emergencias:
        print("\n¡No se encontraron archivos emergencias_*.csv!")
        return
    
    print(f"\n[OK] Se encontraron {len(archivos_emergencias)} archivos para procesar")
    print("Archivos:")
    for archivo in archivos_emergencias:
        print(f"  - {archivo}")
    
    # Procesar cada archivo
    for path_emerg in archivos_emergencias:
        try:
            # Ejecutar el pipeline
            df_geo = pipeline_georreferenciacion(path_emerg, dataI)
            
            # Crear nombre del archivo de salida
            nombre_base = os.path.splitext(os.path.basename(path_emerg))[0]
            output_path = f"{nombre_base}_georreferenciado.csv"
            
            # Guardar resultado
            df_geo.to_csv(output_path, index=False, encoding='utf-8')
            print(f"[OK] Archivo guardado: {output_path}")
            
        except Exception as e:
            print(f"[ERROR] al procesar {path_emerg}: {str(e)}")
            continue
    
    print(f"\n{'='*60}")
    print("[OK] PROCESAMIENTO COMPLETADO")
    print(f"{'='*60}")


# ============================================================
# 9. EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    procesar_todos_emergencias()
