# =============================================================================
# 02_segmentacion.py — Explorador de segmentos
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline_Dolly import (
    cargar_perfil_clientes, calcular_estadisticas,
    ORDEN_PRIORIDAD_SEGMENTOS, SEGMENTOS_RECUPERABLES, PARAMS, UMBRALES,
)
from estilo_Dolly import (
    aplicar_estilo, sidebar_dolly, encabezado_pagina, kpi_card, divisor, estilizar_grafico,
    NEGRO, ROJO, VINO, GRIS, GRIS_CLARO, TEXTO_SECUNDARIO, SECUENCIA_CATEGORICA,
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
# PANORAMA GENERAL — TODOS LOS SEGMENTOS
# (trasladado desde 01_dashboard.py — este es el lugar único para explorar
# y entender la base completa; el Dashboard se enfoca en urgencia del día)
# ==============================================
st.subheader("Panorama general de la base")
st.caption(
    "Usa los filtros de arriba. La barra excluye Perdido/Inactivo/Recuperables "
    "(ya tienen su análisis en Oportunidades de recuperación)."
)

if df_filtrado.empty:
    st.warning("No hay clientes que calcen con los filtros de arriba.")
else:
    df_panorama = df_filtrado
    stats_panorama = calcular_estadisticas(df_panorama)

    # ==============================================
    # GRÁFICOS — DOS TORTAS LADO A LADO
    # ==============================================
    col_izq_pan, col_der_pan = st.columns(2, gap="large")

    with col_izq_pan:
        df_pot = pd.DataFrame({
            "Segmento":   list(stats_panorama["potencial_por_segmento"].keys()),
            "Potencial":  list(stats_panorama["potencial_por_segmento"].values()),
        }).sort_values("Potencial", ascending=False)

        colores_pot = px.colors.sample_colorscale(
            ["#F3D6D3", ROJO, VINO],
            [i / max(len(df_pot) - 1, 1) for i in range(len(df_pot))],
        )

        fig2 = px.pie(
            df_pot,
            names="Segmento",
            values="Potencial",
            title="Potencial CLP por segmento (% del total)",
            color_discrete_sequence=colores_pot,
        )
        fig2.update_traces(textposition="inside", textinfo="percent+label", showlegend=False)
        st.plotly_chart(estilizar_grafico(fig2), use_container_width=True, theme=None)

    with col_der_pan:
        df_paso = df_panorama[df_panorama["paso_abandono"] != "Desconocido"]
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
                fig_paso = px.pie(
                    df_paso,
                    names="paso_abandono",
                    title="Paso de abandono (clientes con dato)",
                    color_discrete_sequence=SECUENCIA_CATEGORICA,
                )
                fig_paso.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(estilizar_grafico(fig_paso), use_container_width=True, theme=None)
            st.caption(
                "El paso de abandono vía CSV VTEX solo cubre ~30-31 días hacia atrás — "
                "argumento a favor de la conexión por API."
            )
        else:
            st.info("No hay clientes con paso de abandono conocido en este filtro.")

    divisor()

    # ==============================================
    # GRÁFICO — BARRA CLIENTES POR SEGMENTO (ancho completo)
    # ==============================================
    SEGMENTOS_EXCLUIDOS_PANORAMA = SEGMENTOS_RECUPERABLES + ["Perdido", "Inactivo"]

    df_seg = pd.DataFrame({
        "Segmento": list(stats_panorama["clientes_por_segmento"].keys()),
        "Clientes": list(stats_panorama["clientes_por_segmento"].values()),
    })
    df_seg = df_seg[~df_seg["Segmento"].isin(SEGMENTOS_EXCLUIDOS_PANORAMA)]
    df_seg = df_seg.sort_values("Clientes", ascending=True)

    # Color por accionabilidad (mismo orden de urgencia que el resto de
    # la app) en vez de por volumen — así el segmento más urgente destaca
    # aunque tenga pocos clientes, y no al revés.
    n_segmentos_totales = max(len(ORDEN_PRIORIDAD_SEGMENTOS), 1)
    mapa_color_prioridad = {
        seg: px.colors.sample_colorscale(
            [GRIS_CLARO, VINO, ROJO],
            [1 - (rank - 1) / max(n_segmentos_totales - 1, 1)],
        )[0]
        for seg, rank in ORDEN_PRIORIDAD_SEGMENTOS.items()
    }

    if df_seg.empty:
        st.info("Los segmentos elegidos quedan todos excluidos de este gráfico (Perdido/Inactivo/Recuperables).")
    else:
        fig_barra_pan = px.bar(
            df_seg,
            x="Clientes",
            y="Segmento",
            orientation="h",
            color="Segmento",
            color_discrete_map=mapa_color_prioridad,
            title="Clientes por segmento (excluye Perdido/Inactivo/Recuperables)",
        )
        fig_barra_pan.update_layout(showlegend=False, yaxis_title=None)
        fig_barra_pan.update_yaxes(automargin=True)
        st.plotly_chart(estilizar_grafico(fig_barra_pan), use_container_width=True, theme=None)

    divisor()

    # ==============================================
    # DISTRIBUCIÓN DE RECENCIA
    # ==============================================
    st.subheader("Distribución de recencia")

    # Binning manual (en vez de px.histogram directo) para poder colorear cada
    # barra según su propio valor. Gradiente invertido a propósito: el bin más
    # reciente (menos días) recibe el color más denso/vivo, y se va difuminando
    # a medida que aumenta la recencia — la intensidad del color representa
    # "qué tan vivo" está ese grupo de clientes.
    conteos, bordes = np.histogram(df_panorama["recencia_dias"], bins=30)
    centros = (bordes[:-1] + bordes[1:]) / 2
    df_bins_recencia = pd.DataFrame({
        "centro": centros,
        "clientes": conteos,
        "rango": [f"{int(bordes[i])}–{int(bordes[i+1])} días" for i in range(len(bordes) - 1)],
    })

    ESCALA_ROJA_INVERTIDA = [[0, VINO], [0.5, ROJO], [1, "#F3D6D3"]]

    fig3 = px.bar(
        df_bins_recencia,
        x="centro",
        y="clientes",
        color="centro",
        color_continuous_scale=ESCALA_ROJA_INVERTIDA,
        title="Tendencia de sesiones",
        labels={"centro": "Días", "clientes": "Clientes"},
        custom_data=["rango"],
    )
    fig3.update_traces(
        marker_line_color="#FFFFFF",
        marker_line_width=1.5,
        hovertemplate="%{customdata[0]}<br>%{y:,} clientes<extra></extra>",
        name="Clientes",
    )

    # Línea de tendencia — promedio móvil de 3 bins para suavizar el "diente de
    # sierra" propio del binning, sin ocultar las barras reales debajo.
    tendencia = pd.Series(conteos).rolling(window=3, center=True, min_periods=1).mean()
    fig3.add_trace(go.Scatter(
        x=centros, y=tendencia,
        mode="lines",
        line=dict(color=NEGRO, width=2.5, shape="spline"),
        name="Tendencia",
        hoverinfo="skip",
    ))

    fig3.update_layout(bargap=0.12, coloraxis_showscale=False, showlegend=True, legend_title_text="")
    st.plotly_chart(estilizar_grafico(fig3), use_container_width=True, theme=None)
    st.caption("Clientes por última sesión, con línea de tendencia suavizada.")

    divisor()

    # ==============================================
    # DISTRIBUCIÓN DE MONTO DE CARRITO
    # ==============================================
    st.subheader("Distribución de monto de carrito")
    df_monto = df_panorama[df_panorama["monto_carrito"] > 0]

    if df_monto.empty:
        st.info("No hay carritos con monto mayor a 0 en los segmentos seleccionados.")
    else:
        umbral = PARAMS["ticket_umbral_flete_gratis"]

        # Acotamos el eje a una zona donde realmente vive la decisión de negocio
        # (cerca del umbral de flete gratis) — el histograma completo hasta el
        # máximo real queda dominado por unos pocos carritos gigantes y aplasta
        # todo lo demás contra el eje Y. Los outliers no se ocultan: se cuentan
        # aparte en el caption de abajo.
        eje_max = max(umbral * 3, df_monto["monto_carrito"].quantile(0.95))
        df_monto_visible = df_monto[df_monto["monto_carrito"] <= eje_max]
        n_outliers = len(df_monto) - len(df_monto_visible)

        fig4 = px.histogram(
            df_monto_visible,
            x="monto_carrito",
            nbins=30,
            color_discrete_sequence=[VINO],
            title="Valor del carrito (CLP)",
            labels={"monto_carrito": "CLP"},
        )
        # Bandas de color: convierte la línea de umbral en una zona accionable —
        # "bajo el umbral" (candidatos a empujar con un cross-sell/recordatorio)
        # vs. "ya calificó para flete gratis", en vez de solo una referencia
        # descriptiva.
        fig4.add_vrect(
            x0=0, x1=umbral,
            fillcolor=ROJO, opacity=0.10, line_width=0,
            annotation_text="Bajo el umbral", annotation_position="top left",
            annotation_font_color=ROJO,
        )
        fig4.add_vrect(
            x0=umbral, x1=eje_max,
            fillcolor=GRIS_CLARO, opacity=0.25, line_width=0,
            annotation_text="Flete gratis ✓", annotation_position="top right",
            annotation_font_color=TEXTO_SECUNDARIO,
        )
        fig4.add_vline(
            x=umbral,
            line_dash="dash",
            line_color=ROJO,
            annotation_text=f"${umbral:,}",
        )
        fig4.update_xaxes(range=[0, eje_max])
        fig4.update_traces(marker_line_color="#FFFFFF", marker_line_width=1.5)
        fig4.update_layout(bargap=0.12)
        st.plotly_chart(estilizar_grafico(fig4), use_container_width=True, theme=None)
        if n_outliers > 0:
            st.caption(f"+{n_outliers:,} clientes con carrito sobre ${eje_max:,.0f} (fuera del rango visible, para no aplastar la escala).")

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
