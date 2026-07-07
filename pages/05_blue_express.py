# =============================================================================
# 05_blue_express.py — Gestión de puntos Blue Express
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline_Dolly import (
    cargar_puntos_blueexpress,
    guardar_puntos_blueexpress,
    cargar_perfil_clientes,
    distancia_haversine,
)
from estilo_Dolly import (
    aplicar_estilo, encabezado_pagina, kpi_card, divisor,
    NEGRO, ROJO, VINO, GRIS, SECUENCIA_CATEGORICA,
)

st.set_page_config(page_title="Blue Express — Dolly", page_icon="📍", layout="wide")
aplicar_estilo()

encabezado_pagina(
    modulo="Módulo 05 · Blue Express",
    titulo="Gestión de puntos Blue Express",
    subtitulo="Administra los puntos de retiro disponibles y visualiza su cobertura.",
)

# Cargar datos
df_puntos  = cargar_puntos_blueexpress()
df_clientes = cargar_perfil_clientes()

# ==============================================
# MÉTRICAS GENERALES
# ==============================================
col1, col2, col3 = st.columns(3)
with col1:
    kpi_card("Total puntos", len(df_puntos))
with col2:
    kpi_card("Ciudades cubiertas", df_puntos["ciudad"].nunique(), color=GRIS)
with col3:
    kpi_card("Regiones cubiertas", df_puntos["region"].nunique(), color=ROJO)

divisor()

# ==============================================
# MAPA DE PUNTOS
# ==============================================
st.subheader("🗺️ Mapa de cobertura")

df_puntos_mapa = df_puntos.dropna(subset=["latitud", "longitud"])

fig_mapa = px.scatter_mapbox(
    df_puntos_mapa,
    lat="latitud",
    lon="longitud",
    hover_name="nombre",
    hover_data=["ciudad", "region", "estado"],
    color="region",
    color_discrete_sequence=SECUENCIA_CATEGORICA,
    zoom=5,
    center={"lat": -40.0, "lon": -73.0},
    height=450,
    title="Puntos Blue Express — Sur de Chile",
)
fig_mapa.update_layout(mapbox_style="open-street-map")
fig_mapa.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0})
st.plotly_chart(fig_mapa, use_container_width=True)

divisor()

# ==============================================
# TABLA EDITABLE
# ==============================================
st.subheader("✏️ Editar puntos de retiro")
st.caption("Puedes agregar, editar o eliminar puntos directamente en la tabla.")

df_editable = st.data_editor(
    df_puntos,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "nombre":   st.column_config.TextColumn("Nombre del punto", width="large"),
        "ciudad":   st.column_config.TextColumn("Ciudad"),
        "region":   st.column_config.TextColumn("Región"),
        "latitud":  st.column_config.NumberColumn("Latitud",  format="%.4f"),
        "longitud": st.column_config.NumberColumn("Longitud", format="%.4f"),
        "estado":   st.column_config.SelectboxColumn(
            "Estado",
            options=["Abierto 24/7", "Abierto", "Cerrado temporalmente"]
        ),
    },
    hide_index=True,
)

col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    if st.button("💾 Guardar cambios", type="primary", use_container_width=True):
        guardar_puntos_blueexpress(df_editable)
        st.success("✅ Puntos guardados correctamente.")
        st.rerun()

divisor()

# ==============================================
# AGREGAR PUNTO NUEVO
# ==============================================
st.subheader("➕ Agregar punto nuevo")

with st.form("form_nuevo_punto"):
    col_a, col_b = st.columns(2)
    with col_a:
        nuevo_nombre  = st.text_input("Nombre del punto", placeholder="Blue Express Copec ...")
        nueva_ciudad  = st.text_input("Ciudad", placeholder="Puerto Montt")
        nueva_region  = st.selectbox("Región", [
            "Los Lagos", "Los Ríos", "La Araucanía", "Biobío",
            "Ñuble", "Maule", "O'Higgins", "Metropolitana", "Otra"
        ])
    with col_b:
        nueva_lat     = st.number_input("Latitud",  value=-41.4693, format="%.4f")
        nueva_lon     = st.number_input("Longitud", value=-72.9424, format="%.4f")
        nuevo_estado  = st.selectbox("Estado", ["Abierto 24/7", "Abierto", "Cerrado temporalmente"])

    submitted = st.form_submit_button("➕ Agregar punto", type="primary")
    if submitted:
        if nuevo_nombre and nueva_ciudad:
            nuevo = pd.DataFrame([{
                "nombre":   nuevo_nombre,
                "ciudad":   nueva_ciudad,
                "region":   nueva_region,
                "latitud":  nueva_lat,
                "longitud": nueva_lon,
                "estado":   nuevo_estado,
            }])
            df_actualizado = pd.concat([df_puntos, nuevo], ignore_index=True)
            guardar_puntos_blueexpress(df_actualizado)
            st.success(f"✅ Punto '{nuevo_nombre}' agregado correctamente.")
            st.rerun()
        else:
            st.error("❌ Nombre y ciudad son obligatorios.")

divisor()

# ==============================================
# ANÁLISIS DE COBERTURA
# ==============================================
st.subheader("📊 Análisis de cobertura por ciudad")

cobertura = df_puntos.groupby(["ciudad", "region"]).agg(
    n_puntos = ("nombre", "count")
).reset_index().sort_values("n_puntos", ascending=False)

fig_cob = px.bar(
    cobertura,
    x="ciudad",
    y="n_puntos",
    color="region",
    color_discrete_sequence=SECUENCIA_CATEGORICA,
    title="Puntos Blue Express por ciudad",
    labels={"n_puntos": "N° puntos", "ciudad": "Ciudad"},
)
fig_cob.update_layout(
    xaxis_tickangle=-30,
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color=NEGRO,
)
st.plotly_chart(fig_cob, use_container_width=True)
