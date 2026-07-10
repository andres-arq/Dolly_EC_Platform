# =============================================================================
# 02_segmentacion.py — Explorador de segmentos
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline_Dolly import cargar_perfil_clientes, PARAMS, UMBRALES
from estilo_Dolly import (
    aplicar_estilo, sidebar_dolly, encabezado_pagina, kpi_card, divisor, estilizar_grafico,
    NEGRO, ROJO, VINO, GRIS, SECUENCIA_CATEGORICA,
)

st.set_page_config(page_title="Segmentación — Dolly", page_icon="👥", layout="wide")
aplicar_estilo()
sidebar_dolly()

encabezado_pagina(
    modulo="Módulo 02 · Segmentación",
    titulo="Segmentación de clientes",
    subtitulo="Explora y filtra la base de clientes por segmento, monto y recencia.",
)

# Cargar datos
df = cargar_perfil_clientes()

if df.empty:
    st.warning("⚠️  No hay datos disponibles. Ve a **Actualizar Data** para cargar el CSV de VTEX.")
    st.stop()

# ==============================================
# FILTROS
# ==============================================
st.subheader("Filtros")
col1, col2, col3 = st.columns(3)

with col1:
    segmentos_disponibles = ["Todos"] + sorted(df["segmento"].unique().tolist())
    segmento_seleccionado = st.selectbox("Segmento", segmentos_disponibles)

with col2:
    monto_min, monto_max = int(df["monto_carrito"].min()), int(df["monto_carrito"].max())
    rango_monto = st.slider(
        "Rango de monto carrito (CLP)",
        min_value=monto_min,
        max_value=monto_max,
        value=(monto_min, monto_max),
        step=1_000,
        format="$%d",
    )

with col3:
    recencia_min, recencia_max = int(df["recencia_dias"].min()), int(df["recencia_dias"].max())
    rango_recencia = st.slider(
        "Rango de recencia (días)",
        min_value=recencia_min,
        max_value=recencia_max,
        value=(recencia_min, recencia_max),
    )

# Aplicar filtros
df_filtrado = df.copy()
if segmento_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["segmento"] == segmento_seleccionado]
df_filtrado = df_filtrado[
    (df_filtrado["monto_carrito"] >= rango_monto[0]) &
    (df_filtrado["monto_carrito"] <= rango_monto[1]) &
    (df_filtrado["recencia_dias"] >= rango_recencia[0]) &
    (df_filtrado["recencia_dias"] <= rango_recencia[1])
]

divisor()
st.subheader(f"Resultados — {len(df_filtrado):,} clientes")
col1, col2, col3, col4 = st.columns(4)

with col1:
    kpi_card("Clientes filtrados", f"{len(df_filtrado):,}")
with col2:
    kpi_card("Monto mediano", f"${df_filtrado['monto_carrito'].median():,.0f}")
with col3:
    kpi_card("Recencia promedio", f"{df_filtrado['recencia_dias'].mean():.0f} días", color=GRIS)
with col4:
    potencial = len(df_filtrado) * df_filtrado["monto_carrito"].median()
    kpi_card("Potencial CLP", f"${potencial:,.0f}", color=ROJO)

divisor()

# ==============================================
# GRÁFICOS
# ==============================================
col_izq, col_der = st.columns(2)

with col_izq:
    fig = px.scatter(
        df_filtrado,
        x="recencia_dias",
        y="monto_carrito",
        color="segmento",
        color_discrete_sequence=SECUENCIA_CATEGORICA,
        title="Recencia vs Monto por segmento",
        labels={
            "recencia_dias":  "Días desde última sesión",
            "monto_carrito":  "Monto carrito (CLP)",
        },
        hover_data=["userId", "paso_abandono"],
    )
    fig.update_traces(marker=dict(opacity=0.65, size=9))
    fig.add_hline(
        y=PARAMS["ticket_umbral_flete_gratis"],
        line_dash="dash",
        line_color=ROJO,
        annotation_text="Umbral flete gratis",
    )
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(estilizar_grafico(fig), use_container_width=True, theme=None)

with col_der:
    df_paso = df_filtrado[df_filtrado["paso_abandono"] != "Desconocido"]
    if not df_paso.empty:
        n_categorias = df_paso["paso_abandono"].nunique()
        if n_categorias == 1:
            categoria_unica = df_paso["paso_abandono"].iloc[0]
            st.markdown("**Paso de abandono (clientes con dato)**")
            kpi_card(
                "100% de estos clientes",
                categoria_unica,
                color=ROJO,
                ayuda="Todos los clientes con dato en este filtro abandonaron en el mismo paso.",
            )
        else:
            fig2 = px.pie(
                df_paso,
                names="paso_abandono",
                title="Paso de abandono (clientes con dato)",
                color_discrete_sequence=SECUENCIA_CATEGORICA,
            )
            fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(estilizar_grafico(fig2), use_container_width=True, theme=None)
    else:
        st.info("No hay clientes con paso de abandono conocido en este filtro.")

divisor()

# ==============================================
# TABLA DE CLIENTES
# ==============================================
st.subheader("Detalle de clientes")

columnas_mostrar = [
    "userId", "segmento", "recencia_dias", "monto_carrito",
    "ticket_prom", "frecuencia", "paso_abandono",
    "sobre_umbral", "tiene_newsletter", "tiene_telefono",
]

columnas_existentes = [c for c in columnas_mostrar if c in df_filtrado.columns]

st.dataframe(
    df_filtrado[columnas_existentes].sort_values("monto_carrito", ascending=False),
    use_container_width=True,
    hide_index=True,
)

# Botón de descarga
csv = df_filtrado[columnas_existentes].to_csv(index=False, encoding="utf-8-sig")
st.download_button(
    label="⬇️  Descargar segmento filtrado como CSV",
    data=csv,
    file_name=f"dolly_segmento_{segmento_seleccionado.lower().replace(' ', '_')}.csv",
    mime="text/csv",
)
