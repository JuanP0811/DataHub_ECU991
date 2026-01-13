import pandas as pd

# Cargar el CSV
print("Cargando emergencias_octubre_2021.csv...")
df = pd.read_csv('emergencias_octubre_2021.csv', sep=';', encoding='utf-8')

print(f"\n=== TOTAL DE FILAS: {len(df)} ===\n")

# 1. PROBLEMA: Columna 7 con tipos mixtos
print("=== PROBLEMA 1: COLUMNA 7 (Unnamed: 7) ===")
print(f"Nombre de columnas: {df.columns.tolist()}")
if 'Unnamed: 7' in df.columns:
    print(f"Valores no nulos en columna 7: {df['Unnamed: 7'].notna().sum()}")
    print(f"Valores únicos: {df['Unnamed: 7'].dropna().unique()[:10]}")

# 2. PROBLEMA: Filas con provincia problemática
print("\n=== PROBLEMA 2: PROVINCIAS PROBLEMÁTICAS ===")
print("Todas las provincias únicas:")
print(df['provincia'].value_counts(dropna=False))

# Buscar '0' y 'zona no delimitada'
mask_cero = df['provincia'] == '0'
mask_zona = df['provincia'].str.upper() == 'ZONA NO DELIMITADA'
mask_na = df['provincia'].isna()

print(f"\nFilas con provincia = '0': {mask_cero.sum()}")
print(f"Filas con provincia = 'ZONA NO DELIMITADA': {mask_zona.sum()}")
print(f"Filas con provincia = NaN: {mask_na.sum()}")
print(f"TOTAL a eliminar: {(mask_cero | mask_zona | mask_na).sum()}")

# Ejemplos
if (mask_cero | mask_zona | mask_na).sum() > 0:
    casos = df[mask_cero | mask_zona | mask_na][['provincia', 'Canton', 'Parroquia', 'Cod_Parroquia']].head(20)
    print("\nEjemplos de casos problemáticos:")
    print(casos)

# 3. PROBLEMA: Parroquias sin match
print("\n=== PROBLEMA 3: ANÁLISIS DE CÓDIGOS DE PARROQUIA ===")
print("Muestra de códigos de parroquia:")
print(df['Cod_Parroquia'].head(20))
print(f"\nCódigos únicos: {df['Cod_Parroquia'].nunique()}")

# Revisar las parroquias específicas que no hicieron match
print("\n=== REVISANDO PARROQUIAS SIN MATCH ===")
print("\n1. 'el carmen de pijili' en Azuay / Camilo Ponce Enriquez:")
caso1 = df[
    (df['provincia'].str.upper() == 'AZUAY') & 
    (df['Canton'].str.upper() == 'CAMILO PONCE ENRIQUEZ') &
    (df['Parroquia'].str.upper() == 'EL CARMEN DE PIJILI')
]
if len(caso1) > 0:
    print(caso1[['provincia', 'Canton', 'Parroquia', 'Cod_Parroquia']].head())
else:
    # Buscar variantes
    caso1_var = df[
        (df['Parroquia'].str.contains('carmen', case=False, na=False)) &
        (df['Parroquia'].str.contains('pijili', case=False, na=False))
    ]
    print(f"Variantes encontradas: {len(caso1_var)}")
    if len(caso1_var) > 0:
        print(caso1_var[['provincia', 'Canton', 'Parroquia', 'Cod_Parroquia']].head())

print("\n2. 'tiputini' en Orellana / Aguarico:")
caso2 = df[
    (df['provincia'].str.upper() == 'ORELLANA') & 
    (df['Canton'].str.upper() == 'AGUARICO') &
    (df['Parroquia'].str.upper() == 'TIPUTINI')
]
if len(caso2) > 0:
    print(caso2[['provincia', 'Canton', 'Parroquia', 'Cod_Parroquia']].head())
else:
    # Buscar variantes
    caso2_var = df[df['Parroquia'].str.contains('tiputini', case=False, na=False)]
    print(f"Variantes encontradas: {len(caso2_var)}")
    if len(caso2_var) > 0:
        print(caso2_var[['provincia', 'Canton', 'Parroquia', 'Cod_Parroquia']].head())

# Cargar INEC para comparar
print("\n=== VERIFICANDO CONTRA CODIFICACIÓN INEC ===")
dataI = pd.read_excel("CODIFICACIÓN_2021.xlsx", header=0, skiprows=1)
dataI = dataI.dropna(axis=1, how="any")

from unidecode import unidecode

def norm_nombre(s):
    if pd.isna(s):
        return None
    s = str(s).strip()
    s = " ".join(s.split())
    s = unidecode(s).lower()
    return s

print("\n1. Buscando 'el carmen de pijili' en INEC:")
inec_carmen = dataI[
    dataI['DPA_DESPAR'].apply(norm_nombre).str.contains('carmen.*pijili', case=False, na=False, regex=True)
]
print(f"Resultados: {len(inec_carmen)}")
if len(inec_carmen) > 0:
    print(inec_carmen[['DPA_DESPRO', 'DPA_DESCAN', 'DPA_DESPAR', 'DPA_PARROQ']])

print("\n2. Buscando 'tiputini' en INEC:")
inec_tiputini = dataI[
    dataI['DPA_DESPAR'].apply(norm_nombre) == 'tiputini'
]
print(f"Resultados: {len(inec_tiputini)}")
if len(inec_tiputini) > 0:
    print(inec_tiputini[['DPA_DESPRO', 'DPA_DESCAN', 'DPA_DESPAR', 'DPA_PARROQ']])
else:
    # Buscar similar
    inec_tiputini_like = dataI[
        dataI['DPA_DESPAR'].apply(norm_nombre).str.contains('tipu', case=False, na=False)
    ]
    print(f"Resultados similares: {len(inec_tiputini_like)}")
    if len(inec_tiputini_like) > 0:
        print(inec_tiputini_like[['DPA_DESPRO', 'DPA_DESCAN', 'DPA_DESPAR', 'DPA_PARROQ']])
