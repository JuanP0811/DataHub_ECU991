import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

st.set_page_config(page_title="ECU 911 - Dashboard", layout="wide")

st.title("📊 Proyecto ECU 911 de los años 2021-2025")

# ==========================================
# CONFIGURACIÓN DE DATOS
# ==========================================
ARCHIVO_CSV = "datos_limpios_2021_2025.csv"
GOOGLE_DRIVE_FILE_ID = "1BV31271akn6eaJNbduYLYHLvjcreQx9S"

@st.cache_data
def descargar_datos_gdrive():
    """Descarga el archivo CSV desde Google Drive si no existe localmente"""
    if not os.path.exists(ARCHIVO_CSV):
        with st.spinner("📥 Descargando datos desde Google Drive (esto puede tomar unos minutos)..."):
            import gdown
            url = f"https://drive.google.com/uc?id={GOOGLE_DRIVE_FILE_ID}"
            gdown.download(url, ARCHIVO_CSV, quiet=False)
    return ARCHIVO_CSV

# Descargar datos si es necesario
archivo = descargar_datos_gdrive()

# ==========================================
# CARGA DE DATOS
# ==========================================
# Límite de filas para Streamlit Cloud (memoria limitada)
MAX_FILAS = 500000

@st.cache_data
def cargar_datos_completos():
    """Carga datos para análisis (limitado para funcionar en la nube)"""
    df = pd.read_csv(ARCHIVO_CSV, nrows=MAX_FILAS, low_memory=False)
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df['Año'] = df['Fecha'].dt.year
    df['Mes'] = df['Fecha'].dt.month
    df['Hora'] = df['Fecha'].dt.hour
    df['Año_Mes'] = df['Fecha'].dt.to_period('M').astype(str)
    return df

@st.cache_data
def obtener_info_basica():
    """Obtiene info básica"""
    # Contar filas totales del archivo
    total_filas_archivo = sum(1 for _ in open(ARCHIVO_CSV, encoding='utf-8')) - 1
    columnas = pd.read_csv(ARCHIVO_CSV, nrows=0).columns.tolist()
    return min(total_filas_archivo, MAX_FILAS), columnas, total_filas_archivo

# Cargar datos
total_filas, columnas, total_archivo = obtener_info_basica()

with st.spinner("Cargando datos para visualización..."):
    df = cargar_datos_completos()

# Aviso de muestra
if total_archivo > MAX_FILAS:
    st.info(f"📊 Mostrando muestra de **{MAX_FILAS:,}** registros de **{total_archivo:,}** totales (para optimizar rendimiento en la nube)")

# Métricas principales
st.markdown("### 📈 Resumen General")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("Total de Registros", f"{total_filas:,}")
with col_m2:
    st.metric("Período", "2021 - 2025")
with col_m3:
    st.metric("Provincias", df['provincia'].nunique())
with col_m4:
    st.metric("Servicios", df['Servicio'].nunique())

st.divider()

# ==========================================
# CREAR PESTAÑAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📅 Análisis Temporal",
    "🗺️ Análisis Geográfico", 
    "� Análisis Comparativo",
    "📋 Datos"
])

# ==========================================
# TAB 1: ANÁLISIS TEMPORAL
# ==========================================
with tab1:
    st.subheader("📅 Análisis Temporal de Incidentes")
    
    col1, col2 = st.columns(2)
    
    # --- HEATMAP: ¿Hay meses con más incidentes? ---
    with col1:
        st.markdown("#### 🔥 Heatmap: Incidentes por Año y Mes")
        st.caption("¿Hay meses con más incidentes?")
        
        # Crear tabla pivote para heatmap
        heatmap_data = df.groupby(['Año', 'Mes']).size().reset_index(name='Cantidad')
        heatmap_pivot = heatmap_data.pivot(index='Año', columns='Mes', values='Cantidad').fillna(0)
        
        # Nombres de los meses
        meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=heatmap_pivot.values,
            x=meses,
            y=heatmap_pivot.index.astype(str),
            colorscale='YlOrRd',
            text=heatmap_pivot.values.astype(int),
            texttemplate="%{text:,}",
            textfont={"size": 10},
            hovertemplate='Año: %{y}<br>Mes: %{x}<br>Incidentes: %{z:,}<extra></extra>'
        ))
        
        fig_heatmap.update_layout(
            height=400,
            xaxis_title="Mes",
            yaxis_title="Año",
            yaxis=dict(type='category'),
            xaxis=dict(showgrid=False),
            yaxis_showgrid=False
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # --- BARRAS: ¿Qué día tiene más emergencias? ---
    with col2:
        st.markdown("#### 📊 Incidentes por Día de la Semana")
        st.caption("¿Qué día tiene más emergencias?")
        
        # Agregar día de la semana
        df['DiaSemana'] = df['Fecha'].dt.dayofweek
        
        # Nombres de días
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        
        # Agrupar por día de semana
        datos_dia = df.groupby('DiaSemana').size().reset_index(name='Cantidad')
        datos_dia['Dia'] = datos_dia['DiaSemana'].apply(lambda x: dias[x])
        
        # Ordenar por día de semana
        datos_dia = datos_dia.sort_values('DiaSemana')
        
        # Crear gráfico de barras
        fig_dias = px.bar(
            datos_dia,
            x='Dia',
            y='Cantidad',
            color='Cantidad',
            color_continuous_scale='YlOrRd',
            text='Cantidad'
        )
        
        fig_dias.update_traces(
            texttemplate='%{text:,}',
            textposition='outside'
        )
        
        fig_dias.update_layout(
            height=400,
            xaxis_title="Día de la semana",
            yaxis_title="Cantidad de incidentes",
            showlegend=False,
            xaxis={'categoryorder': 'array', 'categoryarray': dias, 'showgrid': False},
            yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig_dias, use_container_width=True)
        
        # Mostrar día con más incidentes
        dia_pico = datos_dia.loc[datos_dia['Cantidad'].idxmax()]
        st.info(f"📌 **Día con más emergencias:** {dia_pico['Dia']} con {dia_pico['Cantidad']:,} incidentes")
    
    # Insights adicionales
    st.markdown("---")
    col_i1, col_i2, col_i3 = st.columns(3)
    
    mes_pico = heatmap_data.loc[heatmap_data['Cantidad'].idxmax()]
    mes_min = heatmap_data.loc[heatmap_data['Cantidad'].idxmin()]
    
    with col_i1:
        st.info(f"📅 **Mes pico:** {meses[int(mes_pico['Mes'])-1]} {int(mes_pico['Año'])} con {mes_pico['Cantidad']:,} incidentes")
    with col_i2:
        st.info(f"� **Mes más bajo:** {meses[int(mes_min['Mes'])-1]} {int(mes_min['Año'])} con {mes_min['Cantidad']:,} incidentes")
    with col_i3:
        promedio_diario = total_filas / ((df['Fecha'].max() - df['Fecha'].min()).days or 1)
        st.info(f"📊 **Promedio diario:** {promedio_diario:,.0f} incidentes")

# ==========================================
# TAB 2: ANÁLISIS GEOGRÁFICO
# ==========================================
with tab2:
    st.subheader("🗺️ Análisis Geográfico de Incidentes")
    
    # --- BARRAS HORIZONTALES: Provincias más afectadas ---
    st.markdown("#### 📍 Provincias más Afectadas")
    
    datos_provincia = df['provincia'].value_counts().reset_index()
    datos_provincia.columns = ['Provincia', 'Cantidad']
    
    fig_provincias = px.bar(
        datos_provincia,
        x='Cantidad',
        y='Provincia',
        orientation='h',
        color='Cantidad',
        color_continuous_scale='Blues',
        text='Cantidad'
    )
    fig_provincias.update_traces(texttemplate='%{text:,}', textposition='outside')
    fig_provincias.update_layout(
        height=600,
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False
    )
    st.plotly_chart(fig_provincias, use_container_width=True)
    
    st.markdown("---")
    
    # --- LÍNEAS MÚLTIPLES: Evolución por provincia ---
    st.markdown("#### 📈 Evolución de Provincias en el Tiempo")
    st.caption("¿Cómo cambia cada provincia en el tiempo?")
    
    # Selector de provincias (top 10 por defecto)
    top_provincias = datos_provincia.head(10)['Provincia'].tolist()
    provincias_seleccionadas = st.multiselect(
        "Selecciona provincias a comparar:",
        options=datos_provincia['Provincia'].tolist(),
        default=top_provincias[:5]
    )
    
    if provincias_seleccionadas:
        # Filtrar y agrupar datos
        df_filtrado = df[df['provincia'].isin(provincias_seleccionadas)]
        evolucion = df_filtrado.groupby(['Año_Mes', 'provincia']).size().reset_index(name='Cantidad')
        
        fig_evolucion = px.line(
            evolucion,
            x='Año_Mes',
            y='Cantidad',
            color='provincia',
            markers=True,
            title="Evolución mensual de incidentes por provincia"
        )
        fig_evolucion.update_layout(
            height=450,
            xaxis_tickangle=45,
            legend_title="Provincia"
        )
        st.plotly_chart(fig_evolucion, use_container_width=True)
    else:
        st.warning("Selecciona al menos una provincia para ver la evolución.")

# ==========================================
# TAB 3: ANÁLISIS COMPARATIVO
# ==========================================
with tab3:
    st.subheader(" 📊 Análisis Comparativo")
    
    col1, col2 = st.columns(2)
    
    # --- BARRAS AGRUPADAS: Año vs Año ---
    with col1:
        st.markdown("#### 📅 Comparación Año vs Año")
        st.caption("¿2024 tuvo más incidentes que 2023?")
        
        # Agrupar por año y servicio
        datos_anio_servicio = df.groupby(['Año', 'Servicio']).size().reset_index(name='Cantidad')
        
        fig_anio = px.bar(
            datos_anio_servicio,
            x='Año',
            y='Cantidad',
            color='Servicio',
            barmode='group',
            text='Cantidad',
            title="Incidentes por Año y Servicio"
        )
        fig_anio.update_traces(texttemplate='%{text:,.0f}', textposition='outside', textfont_size=9)
        fig_anio.update_layout(
            height=450, 
            xaxis={'type': 'category', 'showgrid': False},
            yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig_anio, use_container_width=True)
        
        
    
    # --- TOP N PARROQUIAS: Puntos críticos ---
    with col2:
        st.markdown("#### 🎯 Ranking de Parroquias (Puntos Críticos)")
        st.caption("¿Cuáles son los puntos críticos?")
        
        n_parroquias = st.slider("Número de parroquias a mostrar:", 10, 30, 15)
        
        datos_parroquia = df.groupby(['Parroquia', 'provincia']).size().reset_index(name='Cantidad')
        datos_parroquia = datos_parroquia.nlargest(n_parroquias, 'Cantidad')
        datos_parroquia['Etiqueta'] = datos_parroquia['Parroquia'] + ' (' + datos_parroquia['provincia'] + ')'
        
        fig_parroquias = px.bar(
            datos_parroquia,
            x='Cantidad',
            y='Etiqueta',
            orientation='h',
            color='provincia',
            title=f"Top {n_parroquias} Parroquias con más Incidentes",
            text='Cantidad'
        )
        fig_parroquias.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_parroquias.update_layout(
            height=500,
            yaxis={'categoryorder': 'total ascending'},
            showlegend=True,
            legend_title="Provincia"
        )
        st.plotly_chart(fig_parroquias, use_container_width=True)

# ==========================================
# TAB 4: DATOS
# ==========================================
with tab4:
    st.subheader("📋 Explorador de Datos")
    
    # Filtros
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        año_filtro = st.multiselect("Filtrar por Año:", options=sorted(df['Año'].dropna().unique()))
    with col_f2:
        prov_filtro = st.multiselect("Filtrar por Provincia:", options=sorted(df['provincia'].dropna().unique()))
    with col_f3:
        serv_filtro = st.multiselect("Filtrar por Servicio:", options=sorted(df['Servicio'].dropna().unique()))
    
    # Aplicar filtros
    df_mostrar = df.copy()
    if año_filtro:
        df_mostrar = df_mostrar[df_mostrar['Año'].isin(año_filtro)]
    if prov_filtro:
        df_mostrar = df_mostrar[df_mostrar['provincia'].isin(prov_filtro)]
    if serv_filtro:
        df_mostrar = df_mostrar[df_mostrar['Servicio'].isin(serv_filtro)]
    
    # Paginación
    col1, col2 = st.columns([1, 3])
    with col1:
        filas_por_pagina = st.selectbox(
            "Filas por página:",
            options=[100, 500, 1000, 5000],
            index=1
        )

    total_filtrado = len(df_mostrar)
    total_paginas = max(1, (total_filtrado + filas_por_pagina - 1) // filas_por_pagina)

    with col2:
        pagina = st.number_input(
            f"Página (1 - {total_paginas:,}):",
            min_value=1,
            max_value=total_paginas,
            value=1
        )

    inicio = (pagina - 1) * filas_por_pagina
    fin = min(inicio + filas_por_pagina, total_filtrado)
    
    st.write(f"Mostrando filas **{inicio + 1:,}** a **{fin:,}** de **{total_filtrado:,}** (filtrado de {total_filas:,} total)")
    
    # Mostrar columnas originales
    columnas_mostrar = ['Fecha', 'provincia', 'Canton', 'Parroquia', 'Servicio', 'Subtipo']
    st.dataframe(df_mostrar[columnas_mostrar].iloc[inicio:fin], use_container_width=True, height=500)
