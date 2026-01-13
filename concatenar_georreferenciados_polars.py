import polars as pl
import glob
import os

def concatenar_archivos_georreferenciados():
    """
    Concatena todos los archivos georreferenciados de eventos y emergencias
    de los años 2021-2025 usando Polars, manejando errores de parsing y 
    diferencias en columnas.
    """
    print("="*80)
    print("CONCATENANDO ARCHIVOS GEORREFERENCIADOS CON POLARS")
    print("="*80)
    
    # Buscar archivos en todos los años
    patrones = [
        "emergencias_*_completo_georreferenciado.csv",
        "eventos_*_completo_georreferenciado.csv",
        "../2022/emergencias_*_completo_georreferenciado.csv",
        "../2022/eventos_*_completo_georreferenciado.csv",
        "../2023/emergencias_*_completo_georreferenciado.csv",
        "../2023/eventos_*_completo_georreferenciado.csv",
        "../2024/emergencias_*_completo_georreferenciado.csv",
        "../2024/eventos_*_completo_georreferenciado.csv",
        "../2025/emergencias_*_completo_georreferenciado.csv",
        "../2025/eventos_*_completo_georreferenciado.csv",
    ]
    
    archivos = []
    for patron in patrones:
        archivos.extend(glob.glob(patron))
    
    if not archivos:
        print("\n❌ No se encontraron archivos georreferenciados")
        return None
    
    print(f"\n✅ Se encontraron {len(archivos)} archivos:")
    for archivo in sorted(archivos):
        tamano_mb = os.path.getsize(archivo) / (1024 * 1024)
        print(f"  • {archivo} ({tamano_mb:.2f} MB)")
    
    # Leer archivos con Polars
    dataframes = []
    columnas_comunes = None
    
    for i, archivo in enumerate(sorted(archivos), 1):
        print(f"\n[{i}/{len(archivos)}] Procesando {os.path.basename(archivo)}...")
        
        try:
            # Leer con columnas como strings para evitar errores de parsing
            df_temp = pl.read_csv(
                archivo,
                encoding='utf-8',
                infer_schema_length=0,  # Leer todo como string primero
                ignore_errors=True
            )
            
            print(f"  ✓ Leído: {df_temp.shape[0]:,} filas, {df_temp.shape[1]} columnas")
            
            # Identificar columnas comunes
            if columnas_comunes is None:
                columnas_comunes = set(df_temp.columns)
            else:
                columnas_comunes = columnas_comunes.intersection(set(df_temp.columns))
            
            # Convertir columnas numéricas con manejo de errores
            for col in df_temp.columns:
                if col in ['Cod_Provincia', 'Cod_Canton', 'Cod_Parroquia']:
                    # Limpiar valores tipo "000nan" y convertir
                    df_temp = df_temp.with_columns(
                        pl.when(pl.col(col).str.contains("nan"))
                        .then(None)
                        .otherwise(pl.col(col))
                        .cast(pl.Int64, strict=False)
                        .alias(col)
                    )
            
            # Agregar columna de origen
            df_temp = df_temp.with_columns(
                pl.lit(os.path.basename(archivo)).alias("archivo_origen")
            )
            
            dataframes.append(df_temp)
            print(f"  ✓ Procesado correctamente")
            
        except Exception as e:
            print(f"  ❌ Error al leer {archivo}: {e}")
            continue
    
    if not dataframes:
        print("\n❌ No se pudieron leer archivos")
        return None
    
    print(f"\n{'='*80}")
    print(f"CONCATENANDO {len(dataframes)} DATAFRAMES")
    print(f"{'='*80}")
    
    # Asegurar que todos tengan las mismas columnas base
    print(f"\n📋 Columnas comunes encontradas: {len(columnas_comunes)}")
    
    # Seleccionar solo columnas comunes + archivo_origen de cada dataframe
    dataframes_normalizados = []
    for df in dataframes:
        cols_seleccionar = [col for col in df.columns if col in columnas_comunes or col == "archivo_origen"]
        df_normalizado = df.select(cols_seleccionar)
        dataframes_normalizados.append(df_normalizado)
    
    # Concatenar usando vertical_relaxed para mayor flexibilidad
    try:
        df_final = pl.concat(dataframes_normalizados, how='vertical_relaxed')
        print(f"\n✅ DataFrame final creado con {df_final.shape[0]:,} filas y {df_final.shape[1]} columnas")
        print(f"\n📊 Columnas: {df_final.columns}")
        
        # Estadísticas
        print(f"\n{'='*80}")
        print("ESTADÍSTICAS")
        print(f"{'='*80}")
        
        if 'DPA_PARROQ' in df_final.columns:
            con_codigo = df_final.filter(pl.col('DPA_PARROQ').is_not_null()).shape[0]
            sin_codigo = df_final.filter(pl.col('DPA_PARROQ').is_null()).shape[0]
            print(f"  • Con código INEC: {con_codigo:,} ({con_codigo/df_final.shape[0]*100:.2f}%)")
            print(f"  • Sin código INEC: {sin_codigo:,} ({sin_codigo/df_final.shape[0]*100:.2f}%)")
        
        # Distribución por archivo
        print(f"\n{'='*80}")
        print("DISTRIBUCIÓN POR ARCHIVO")
        print(f"{'='*80}")
        
        dist_archivos = df_final.group_by("archivo_origen").agg(
            pl.count().alias("cantidad")
        ).sort("archivo_origen")
        
        print(dist_archivos)
        
        # Guardar archivo final
        output_file = "todos_georreferenciados_2021_2025.csv"
        print(f"\n💾 Guardando archivo: {output_file}")
        df_final.write_csv(output_file)
        
        tamano_final_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"✅ Archivo guardado exitosamente ({tamano_final_mb:.2f} MB)")
        
        print(f"\n{'='*80}")
        print("✅ PROCESO COMPLETADO")
        print(f"{'='*80}")
        
        return df_final
        
    except Exception as e:
        print(f"\n❌ Error al concatenar: {e}")
        print(f"\n🔍 Información de debug:")
        for i, df in enumerate(dataframes_normalizados):
            print(f"  DataFrame {i+1}: {df.shape[0]} filas x {df.shape[1]} columnas")
            print(f"    Columnas: {df.columns}")
        return None

if __name__ == "__main__":
    df_unificado = concatenar_archivos_georreferenciados()
