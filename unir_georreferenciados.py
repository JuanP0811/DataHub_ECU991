import pandas as pd
import glob
import os

def unir_archivos_georreferenciados():
    """
    Une todos los archivos *_georreferenciado.csv en un solo archivo.
    """
    print("="*60)
    print("UNIENDO ARCHIVOS GEORREFERENCIADOS")
    print("="*60)
    
    # Buscar todos los archivos georreferenciados
    archivos = glob.glob("emergencias_*_georreferenciado.csv")
    
    if not archivos:
        print("\n❌ No se encontraron archivos *_georreferenciado.csv")
        return
    
    print(f"\n[OK] Se encontraron {len(archivos)} archivos:")
    for archivo in sorted(archivos):
        tamano_mb = os.path.getsize(archivo) / (1024 * 1024)
        print(f"  - {archivo} ({tamano_mb:.2f} MB)")
    
    # Leer y concatenar todos los archivos
    print(f"\n[PROCESO] Leyendo archivos...")
    dataframes = []
    
    for i, archivo in enumerate(sorted(archivos), 1):
        print(f"  [{i}/{len(archivos)}] Cargando {archivo}...")
        df = pd.read_csv(archivo, encoding='utf-8')
        
        # Agregar columna con el nombre del archivo de origen (opcional)
        df['archivo_origen'] = os.path.basename(archivo)
        
        dataframes.append(df)
        print(f"      [OK] {len(df):,} filas cargadas")
    
    # Concatenar todos los dataframes
    print(f"\n[PROCESO] Concatenando {len(dataframes)} archivos...")
    df_completo = pd.concat(dataframes, ignore_index=True)
    
    print(f"  [OK] Total de filas: {len(df_completo):,}")
    print(f"  [OK] Total de columnas: {len(df_completo.columns)}")
    
    # Mostrar estadísticas
    print(f"\n[ESTADISTICAS]")
    print(f"  - Con codigo INEC: {df_completo['DPA_PARROQ'].notna().sum():,} ({df_completo['DPA_PARROQ'].notna().sum()/len(df_completo)*100:.2f}%)")
    print(f"  - Sin codigo INEC: {df_completo['DPA_PARROQ'].isna().sum():,} ({df_completo['DPA_PARROQ'].isna().sum()/len(df_completo)*100:.2f}%)")
    
    if 'Fecha' in df_completo.columns:
        df_completo['Fecha'] = pd.to_datetime(df_completo['Fecha'], errors='coerce')
        print(f"  - Rango de fechas: {df_completo['Fecha'].min()} a {df_completo['Fecha'].max()}")
    
    # Guardar archivo unificado
    output_file = "emergencias_2021_completo_georreferenciado.csv"
    print(f"\n[GUARDANDO] Archivo unificado: {output_file}")
    df_completo.to_csv(output_file, index=False, encoding='utf-8')
    
    tamano_final_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"  [OK] Archivo guardado exitosamente ({tamano_final_mb:.2f} MB)")
    
    # Reporte por archivo de origen
    print(f"\n[DISTRIBUCION] Por archivo:")
    conteo_origen = df_completo['archivo_origen'].value_counts().sort_index()
    for archivo, cantidad in conteo_origen.items():
        print(f"  - {archivo}: {cantidad:,} filas")
    
    print(f"\n{'='*60}")
    print("[OK] PROCESO COMPLETADO")
    print(f"{'='*60}")
    print(f"\nArchivo final: {output_file}")
    print(f"Total de registros: {len(df_completo):,}")
    
    return df_completo

if __name__ == "__main__":
    df_unificado = unir_archivos_georreferenciados()
