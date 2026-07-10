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
    aplicar_estilo, sidebar_dolly, encabezado_pagina, kpi_card, divisor, estilizar_grafico,
    NEGRO, ROJO, VINO, GRIS, SECUENCIA_CATEGORICA,
)

st.set_page_config(page_title="Blue Express — Dolly", page_icon="📍", layout="wide")
aplicar_estilo()
sidebar_dolly()

encabezado_pagina(
    modulo="Módulo 05 · Blue Express",
    titulo="Gestión de puntos Blue Express",
    subtitulo="Administra los puntos de retiro disponibles y visualiza su cobertura.",
)

# Cargar datos
df_puntos  = cargar_puntos_blueexpress()
df_clientes = cargar_perfil_clientes()

# Mensajes pendientes de un guardado que hizo st.rerun() justo después —
# se guardan en session_state para que no desaparezcan antes de que se lean.
if "mensaje_guardado" in st.session_state:
    tipo, texto = st.session_state.pop("mensaje_guardado")
    (st.success if tipo == "ok" else st.warning)(texto)
if "mensaje_sync" in st.session_state:
    ok_sync, detalle_sync = st.session_state.pop("mensaje_sync")
    (st.success if ok_sync else st.warning)(detalle_sync)

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


def _calcular_zoom_y_centro(df_puntos_geo, padding_grados=0.3):
    """
    Calcula un centro y zoom razonables a partir del bounding box real de los
    puntos, en vez de un center/zoom fijo — evita mostrar territorio sin
    puntos (ej. Argentina) cuando los puntos reales están agrupados en una
    zona chica del mapa.
    """
    if df_puntos_geo.empty:
        return {"lat": -40.0, "lon": -73.0}, 5

    lat_min, lat_max = df_puntos_geo["latitud"].min(), df_puntos_geo["latitud"].max()
    lon_min, lon_max = df_puntos_geo["longitud"].min(), df_puntos_geo["longitud"].max()

    centro = {
        "lat": (lat_min + lat_max) / 2,
        "lon": (lon_min + lon_max) / 2,
    }

    rango_max = max(lat_max - lat_min, lon_max - lon_min) + padding_grados
    # Tabla aproximada rango(°) -> zoom para mapbox/OSM (a mayor rango, menor zoom)
    if rango_max <= 0.05:
        zoom = 12
    elif rango_max <= 0.1:
        zoom = 11
    elif rango_max <= 0.3:
        zoom = 9
    elif rango_max <= 0.6:
        zoom = 8
    elif rango_max <= 1.2:
        zoom = 7
    elif rango_max <= 2.5:
        zoom = 6
    else:
        zoom = 5

    return centro, zoom


centro_mapa, zoom_mapa = _calcular_zoom_y_centro(df_puntos_mapa)

fig_mapa = px.scatter_mapbox(
    df_puntos_mapa,
    lat="latitud",
    lon="longitud",
    hover_name="nombre",
    hover_data=["ciudad", "region", "estado"],
    color="region",
    color_discrete_sequence=SECUENCIA_CATEGORICA,
    zoom=zoom_mapa,
    center=centro_mapa,
    height=450,
    title="Puntos Blue Express — Sur de Chile",
)
fig_mapa.update_layout(mapbox_style="open-street-map")
fig_mapa.update_traces(marker=dict(size=13))
fig_mapa.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0})
st.plotly_chart(estilizar_grafico(fig_mapa), use_container_width=True, theme=None)

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
        ok_sync, detalle_sync = guardar_puntos_blueexpress(df_editable)
        st.session_state["mensaje_guardado"] = ("ok", "✅ Puntos guardados correctamente.")
        st.session_state["mensaje_sync"] = (ok_sync, detalle_sync)
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
            ok_sync, detalle_sync = guardar_puntos_blueexpress(df_actualizado)
            st.session_state["mensaje_guardado"] = ("ok", f"✅ Punto '{nuevo_nombre}' agregado correctamente.")
            st.session_state["mensaje_sync"] = (ok_sync, detalle_sync)
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
fig_cob.update_layout(xaxis_tickangle=-30)
st.plotly_chart(estilizar_grafico(fig_cob), use_container_width=True, theme=None)
