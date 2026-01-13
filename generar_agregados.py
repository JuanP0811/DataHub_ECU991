"""
Script para pre-agregar los datos del ECU 911.
Genera archivos pequenos con estadisticas ya calculadas para usar en Streamlit Cloud.
"""
import pandas as pd
import json
import os

# Archivo de entrada
ARCHIVO_CSV = "datos_limpios_2021_2025.csv"
CARPETA_SALIDA = "datos_agregados"

def main():
    print("Cargando datos completos...")
    df = pd.read_csv(ARCHIVO_CSV, low_memory=False)
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df['Año'] = df['Fecha'].dt.year
    df['Mes'] = df['Fecha'].dt.month
    df['Hora'] = df['Fecha'].dt.hour
    df['DiaSemana'] = df['Fecha'].dt.dayofweek
    df['Año_Mes'] = df['Fecha'].dt.to_period('M').astype(str)
    
    total_registros = len(df)
    print(f"Cargados {total_registros:,} registros")
    
    # Crear carpeta de salida
    os.makedirs(CARPETA_SALIDA, exist_ok=True)
    
    # 1. Conteos por Año y Mes (para heatmap temporal)
    print("Generando: conteos_ano_mes.csv")
    conteos_año_mes = df.groupby(['Año', 'Mes']).size().reset_index(name='Cantidad')
    conteos_año_mes.to_csv(f"{CARPETA_SALIDA}/conteos_ano_mes.csv", index=False)
    
    # 2. Conteos por dia de la semana
    print("Generando: conteos_dia_semana.csv")
    conteos_dia = df.groupby('DiaSemana').size().reset_index(name='Cantidad')
    conteos_dia.to_csv(f"{CARPETA_SALIDA}/conteos_dia_semana.csv", index=False)
    
    # 3. Conteos por provincia
    print("Generando: conteos_provincia.csv")
    conteos_provincia = df['provincia'].value_counts().reset_index()
    conteos_provincia.columns = ['Provincia', 'Cantidad']
    conteos_provincia.to_csv(f"{CARPETA_SALIDA}/conteos_provincia.csv", index=False)
    
    # 4. Evolucion por provincia y mes
    print("Generando: evolucion_provincia.csv")
    evolucion = df.groupby(['Año_Mes', 'provincia']).size().reset_index(name='Cantidad')
    evolucion.to_csv(f"{CARPETA_SALIDA}/evolucion_provincia.csv", index=False)
    
    # 5. Conteos por canton y provincia
    print("Generando: conteos_canton.csv")
    conteos_canton = df.groupby(['Canton', 'provincia']).size().reset_index(name='Cantidad')
    conteos_canton.to_csv(f"{CARPETA_SALIDA}/conteos_canton.csv", index=False)
    
    # 6. Conteos por ano y servicio
    print("Generando: conteos_ano_servicio.csv")
    conteos_año_servicio = df.groupby(['Año', 'Servicio']).size().reset_index(name='Cantidad')
    conteos_año_servicio.to_csv(f"{CARPETA_SALIDA}/conteos_ano_servicio.csv", index=False)
    
    # 7. Ranking de parroquias
    print("Generando: ranking_parroquias.csv")
    ranking = df.groupby(['Parroquia', 'provincia']).size().reset_index(name='Cantidad')
    ranking = ranking.sort_values('Cantidad', ascending=False)
    ranking.to_csv(f"{CARPETA_SALIDA}/ranking_parroquias.csv", index=False)
    
    # 8. Metadatos generales
    print("Generando: metadatos.json")
    metadatos = {
        "total_registros": int(total_registros),
        "anos": sorted([int(x) for x in df['Año'].dropna().unique().tolist()]),
        "provincias": int(df['provincia'].nunique()),
        "servicios": int(df['Servicio'].nunique()),
        "columnas": df.columns.tolist()
    }
    with open(f"{CARPETA_SALIDA}/metadatos.json", "w", encoding="utf-8") as f:
        json.dump(metadatos, f, ensure_ascii=False, indent=2)
    
    print("\nAgregacion completada!")
    print(f"Archivos generados en: {CARPETA_SALIDA}/")
    
    # Mostrar tamano de archivos
    total_size = 0
    for archivo in os.listdir(CARPETA_SALIDA):
        size = os.path.getsize(f"{CARPETA_SALIDA}/{archivo}")
        total_size += size
        print(f"   - {archivo}: {size/1024:.1f} KB")
    print(f"\nTamano total: {total_size/1024:.1f} KB (vs ~2 GB original)")

if __name__ == "__main__":
    main()
