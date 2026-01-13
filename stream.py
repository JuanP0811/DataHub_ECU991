import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import json

st.set_page_config(page_title="ECU 911 - Dashboard", layout="wide")

st.title("📊 Proyecto ECU 911 de los años 2021-2025")

# ==========================================
# CONFIGURACIÓN DE DATOS AGREGADOS
# ==========================================
CARPETA_DATOS = "datos_agregados"
GOOGLE_DRIVE_IDS = {
    "conteos_ano_mes.csv": None,  # Se actualizará después de subir a Drive
    "conteos_dia_semana.csv": None,
    "conteos_provincia.csv": None,
    "evolucion_provincia.csv": None,
    "conteos_canton.csv": None,
    "conteos_ano_servicio.csv": None,
    "ranking_parroquias.csv": None,
    "metadatos.json": None
}

# ==========================================
# CARGA DE DATOS AGREGADOS
# ==========================================
@st.cache_data
def cargar_metadatos():
    with open(f"{CARPETA_DATOS}/metadatos.json", "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def cargar_csv(nombre):
    return pd.read_csv(f"{CARPETA_DATOS}/{nombre}")

# Cargar metadatos
metadatos = cargar_metadatos()
total_registros = metadatos["total_registros"]

# Métricas principales
st.markdown("### 📈 Resumen General")
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("Total de Registros", f"{total_registros:,}")
with col_m2:
    años = metadatos["anos"]
    st.metric("Período", f"{min(años)} - {max(años)}")
with col_m3:
    st.metric("Provincias", metadatos["provincias"])
with col_m4:
    st.metric("Servicios", metadatos["servicios"])

st.divider()

# ==========================================
# CREAR PESTAÑAS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📅 Análisis Temporal",
    "🗺️ Análisis Geográfico", 
    "📊 Análisis Comparativo",
    "📋 Información"
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
        
        heatmap_data = cargar_csv("conteos_ano_mes.csv")
        heatmap_pivot = heatmap_data.pivot(index='Año', columns='Mes', values='Cantidad').fillna(0)
        
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
        
        datos_dia = cargar_csv("conteos_dia_semana.csv")
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        datos_dia['Dia'] = datos_dia['DiaSemana'].apply(lambda x: dias[int(x)])
        datos_dia = datos_dia.sort_values('DiaSemana')
        
        fig_dias = px.bar(
            datos_dia,
            x='Dia',
            y='Cantidad',
            color='Cantidad',
            color_continuous_scale='YlOrRd',
            text='Cantidad'
        )
        
        fig_dias.update_traces(texttemplate='%{text:,}', textposition='outside')
        fig_dias.update_layout(
            height=400,
            xaxis_title="Día de la semana",
            yaxis_title="Cantidad de incidentes",
            showlegend=False,
            xaxis={'categoryorder': 'array', 'categoryarray': dias, 'showgrid': False},
            yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig_dias, use_container_width=True)
        
        dia_pico = datos_dia.loc[datos_dia['Cantidad'].idxmax()]
        st.info(f"📌 **Día con más emergencias:** {dia_pico['Dia']} con {dia_pico['Cantidad']:,} incidentes")
    
    # Insights
    st.markdown("---")
    col_i1, col_i2, col_i3 = st.columns(3)
    
    mes_pico = heatmap_data.loc[heatmap_data['Cantidad'].idxmax()]
    mes_min = heatmap_data.loc[heatmap_data['Cantidad'].idxmin()]
    
    with col_i1:
        st.info(f"📅 **Mes pico:** {meses[int(mes_pico['Mes'])-1]} {int(mes_pico['Año'])} con {mes_pico['Cantidad']:,} incidentes")
    with col_i2:
        st.info(f"📉 **Mes más bajo:** {meses[int(mes_min['Mes'])-1]} {int(mes_min['Año'])} con {mes_min['Cantidad']:,} incidentes")
    with col_i3:
        promedio_mensual = heatmap_data['Cantidad'].mean()
        st.info(f"📊 **Promedio mensual:** {promedio_mensual:,.0f} incidentes")

# ==========================================
# TAB 2: ANÁLISIS GEOGRÁFICO
# ==========================================
with tab2:
    st.subheader("🗺️ Análisis Geográfico de Incidentes")
    
    # Provincias más afectadas
    st.markdown("#### 📍 Provincias más Afectadas")
    
    datos_provincia = cargar_csv("conteos_provincia.csv")
    
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
    
    # Evolución por provincia
    st.markdown("#### 📈 Evolución de Provincias en el Tiempo")
    st.caption("¿Cómo cambia cada provincia en el tiempo?")
    
    evolucion = cargar_csv("evolucion_provincia.csv")
    top_provincias = datos_provincia.head(10)['Provincia'].tolist()
    
    provincias_seleccionadas = st.multiselect(
        "Selecciona provincias a comparar:",
        options=datos_provincia['Provincia'].tolist(),
        default=top_provincias[:5]
    )
    
    if provincias_seleccionadas:
        evolucion_filtrada = evolucion[evolucion['provincia'].isin(provincias_seleccionadas)]
        
        fig_evolucion = px.line(
            evolucion_filtrada,
            x='Año_Mes',
            y='Cantidad',
            color='provincia',
            markers=True,
            title="Evolución mensual de incidentes por provincia"
        )
        fig_evolucion.update_layout(height=450, xaxis_tickangle=45, legend_title="Provincia")
        st.plotly_chart(fig_evolucion, use_container_width=True)
    else:
        st.warning("Selecciona al menos una provincia para ver la evolución.")

# ==========================================
# TAB 3: ANÁLISIS COMPARATIVO
# ==========================================
with tab3:
    st.subheader("📊 Análisis Comparativo")
    
    # Año vs Año
    st.markdown("#### 📅 Comparación Año vs Año")
    st.caption("¿2024 tuvo más incidentes que 2023?")
    
    datos_año_servicio = cargar_csv("conteos_ano_servicio.csv")
    
    fig_anio = px.bar(
        datos_año_servicio,
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
    
    st.markdown("---")
    
    # Ranking de parroquias
    st.markdown("#### 🎯 Ranking de Parroquias (Puntos Críticos)")
    st.caption("¿Cuáles son los puntos críticos?")
    
    n_parroquias = st.slider("Número de parroquias a mostrar:", 10, 30, 15)
    
    ranking = cargar_csv("ranking_parroquias.csv")
    datos_parroquia = ranking.head(n_parroquias).copy()
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
# TAB 4: INFORMACIÓN
# ==========================================
with tab4:
    st.subheader("📋 Información del Dataset")
    
    st.markdown(f"""
    ### Datos ECU 911 (2021-2025)
    
    - **Total de registros:** {total_registros:,}
    - **Período:** {min(años)} - {max(años)}
    - **Provincias:** {metadatos['provincias']}
    - **Servicios:** {metadatos['servicios']}
    
    ### Columnas originales del dataset:
    """)
    
    for col in metadatos['columnas']:
        st.markdown(f"- `{col}`")
    
    st.markdown("""
    ---
    ### Notas técnicas
    
    Este dashboard utiliza datos pre-agregados para optimizar el rendimiento en la nube.
    Los gráficos muestran estadísticas calculadas sobre los **16.3 millones de registros** originales.
    """)
