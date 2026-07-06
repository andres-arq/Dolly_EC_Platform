# =============================================================================
# 01_dashboard.py — Dashboard principal
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline_Dolly import cargar_perfil_clientes, calcular_estadisticas, PARAMS
from estilo_Dolly import (
    aplicar_estilo, encabezado_pagina, kpi_card, divisor,
    NEGRO, ROJO, VINO, GRIS, ESCALA_NEUTRA, ESCALA_ROJA,
)

st.set_page_config(page_title="Dashboard — Dolly", page_icon="📊", layout="wide")
aplicar_estilo()

encabezado_pagina(
    modulo="Módulo 01 · Dashboard",
    titulo="Visión general de la base de clientes",
    subtitulo="KPIs, segmentación y oportunidades de negocio.",
)

# Cargar datos
df = cargar_perfil_clientes()

if df.empty:
    st.warning("⚠️  No hay datos disponibles. Ve a **Actualizar Data** para cargar el CSV de VTEX.")
    st.stop()

stats = calcular_estadisticas(df)

# ==============================================
# KPI CARDS
# ==============================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    kpi_card("Total clientes", f"{stats['total_clientes']:,}")

with col2:
    kpi_card("Monto mediano carrito", f"${stats['monto_mediano']:,.0f}")

with col3:
    kpi_card("% Contactables (newsletter)", f"{stats['pct_contactables']:.1f}%", color=GRIS)

with col4:
    kpi_card("% Sobre umbral flete gratis", f"{stats['pct_sobre_umbral']:.1f}%", color=ROJO)

divisor()

# ==============================================
# GRÁFICOS
# ==============================================
col_izq, col_der = st.columns(2)

with col_izq:
    st.subheader("Distribución por segmento")
    df_seg = pd.DataFrame({
        "Segmento": list(stats["clientes_por_segmento"].keys()),
        "Clientes": list(stats["clientes_por_segmento"].values()),
    }).sort_values("Clientes", ascending=True)

    fig = px.bar(
        df_seg,
        x="Clientes",
        y="Segmento",
        orientation="h",
        color="Clientes",
        color_continuous_scale=ESCALA_NEUTRA,
        title="Clientes por segmento",
    )
    fig.update_layout(
        showlegend=False, coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color=NEGRO,
    )
    st.plotly_chart(fig, use_container_width=True)

with col_der:
    st.subheader("Potencial de facturación por segmento")
    df_pot = pd.DataFrame({
        "Segmento":   list(stats["potencial_por_segmento"].keys()),
        "Potencial":  list(stats["potencial_por_segmento"].values()),
    }).sort_values("Potencial", ascending=True)

    fig2 = px.bar(
        df_pot,
        x="Potencial",
        y="Segmento",
        orientation="h",
        color="Potencial",
        color_continuous_scale=ESCALA_ROJA,
        title="Potencial CLP (clientes × monto mediano)",
    )
    fig2.update_layout(
        showlegend=False, coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color=NEGRO,
    )
    fig2.update_xaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig2, use_container_width=True)

divisor()

col_izq2, col_der2 = st.columns(2)

with col_izq2:
    st.subheader("Distribución de recencia")
    fig3 = px.histogram(
        df,
        x="recencia_dias",
        nbins=30,
        color_discrete_sequence=[NEGRO],
        title="Días desde última sesión",
        labels={"recencia_dias": "Días"},
    )
    fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color=NEGRO)
    st.plotly_chart(fig3, use_container_width=True)

with col_der2:
    st.subheader("Distribución de monto de carrito")
    df_monto = df[df["monto_carrito"] > 0]
    fig4 = px.histogram(
        df_monto,
        x="monto_carrito",
        nbins=30,
        color_discrete_sequence=[VINO],
        title="Valor del carrito (CLP)",
        labels={"monto_carrito": "CLP"},
    )
    fig4.add_vline(
        x=PARAMS["ticket_umbral_flete_gratis"],
        line_dash="dash",
        line_color=ROJO,
        annotation_text=f"Umbral flete ${PARAMS['ticket_umbral_flete_gratis']:,}",
    )
    fig4.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color=NEGRO)
    st.plotly_chart(fig4, use_container_width=True)

divisor()

# ==============================================
# TABLA RESUMEN
# ==============================================
st.subheader("Resumen por segmento")
df_resumen = df.groupby("segmento").agg(
    clientes      = ("userId",        "count"),
    recencia_prom = ("recencia_dias",  "mean"),
    monto_mediano = ("monto_carrito",  "median"),
    pct_newsletter= ("tiene_newsletter","mean"),
    pct_telefono  = ("tiene_telefono", "mean"),
).round(1).reset_index()

df_resumen["potencial_clp"]    = (df_resumen["clientes"] * df_resumen["monto_mediano"]).astype(int)
df_resumen["pct_newsletter"]   = (df_resumen["pct_newsletter"] * 100).round(1)
df_resumen["pct_telefono"]     = (df_resumen["pct_telefono"] * 100).round(1)
df_resumen                     = df_resumen.sort_values("clientes", ascending=False)

df_resumen.columns = [
    "Segmento", "Clientes", "Recencia Prom (días)",
    "Monto Mediano", "% Newsletter", "% Teléfono", "Potencial CLP"
]

st.dataframe(df_resumen, use_container_width=True, hide_index=True)
