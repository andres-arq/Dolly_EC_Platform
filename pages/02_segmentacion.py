# =============================================================================
# 02_segmentacion.py — Explorador de segmentos
# =============================================================================

import streamlit as st
import pandas as pd
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
    NEGRO, ROJO, VINO, GRIS, GRIS_CLARO, CARD, BORDE, TEXTO_SECUNDARIO, SECUENCIA_CATEGORICA, ESCALA_ROJA,
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
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    kpi_card("Clientes filtrados", f"{len(df_filtrado):,}")
with col2:
    kpi_card("Monto medio", f"${df_filtrado['monto_carrito'].mean():,.0f}")
with col3:
    kpi_card("Monto mediano", f"${df_filtrado['monto_carrito'].median():,.0f}")
with col4:
    kpi_card("Recencia promedio", f"{df_filtrado['recencia_dias'].mean():.0f} días", color=GRIS)
with col5:
    potencial = len(df_filtrado) * df_filtrado["monto_carrito"].mean()
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
    # ==============================================
    # GRÁFICO — CLIENTES VS. POTENCIAL CLP POR SEGMENTO (ancho completo)
    # ==============================================
    SEGMENTOS_EXCLUIDOS_PANORAMA = SEGMENTOS_RECUPERABLES + ["Perdido", "Inactivo"]

    df_seg = pd.DataFrame({
        "Segmento":  list(stats_panorama["clientes_por_segmento"].keys()),
        "Clientes":  list(stats_panorama["clientes_por_segmento"].values()),
        "Potencial": [stats_panorama["potencial_por_segmento"].get(s, 0)
                      for s in stats_panorama["clientes_por_segmento"].keys()],
    })
    df_seg = df_seg[~df_seg["Segmento"].isin(SEGMENTOS_EXCLUIDOS_PANORAMA)]

    if df_seg.empty:
        st.info("Los segmentos elegidos quedan todos excluidos de este gráfico (Perdido/Inactivo/Recuperables).")
    else:
        # Orden por urgencia real (mismo criterio que el resto de la app), no por
        # tamaño — así la lectura de arriba hacia abajo es literalmente "a qué
        # prestarle atención primero", no solo "quién es más grande".
        df_seg["_prioridad"] = df_seg["Segmento"].map(ORDEN_PRIORIDAD_SEGMENTOS).fillna(99)
        orden_seg = df_seg.sort_values("_prioridad", ascending=False)["Segmento"].tolist()

        total_clientes_seg  = df_seg["Clientes"].sum()
        total_potencial_seg = df_seg["Potencial"].sum()
        df_seg["pct_clientes"]  = df_seg["Clientes"]  / total_clientes_seg  * 100
        df_seg["pct_potencial"] = df_seg["Potencial"] / total_potencial_seg * 100

        df_combo_seg = pd.concat([
            pd.DataFrame({
                "Segmento": df_seg["Segmento"], "tipo": "Clientes",
                "pct": df_seg["pct_clientes"],
                "texto": df_seg["Clientes"].map(lambda v: f"{v:,}"),
            }),
            pd.DataFrame({
                "Segmento": df_seg["Segmento"], "tipo": "Potencial CLP",
                "pct": df_seg["pct_potencial"],
                "texto": df_seg["Potencial"].map(lambda v: f"${v:,.0f}"),
            }),
        ], ignore_index=True)

        fig_barra_pan = px.bar(
            df_combo_seg,
            x="pct", y="Segmento", color="tipo", orientation="h", barmode="group",
            text="texto",
            color_discrete_map={"Clientes": ROJO, "Potencial CLP": VINO},
            category_orders={"Segmento": orden_seg},
            title="Clientes vs. potencial CLP por segmento (excluye Perdido/Inactivo/Recuperables)",
        )
        fig_barra_pan.update_traces(textposition="outside")
        fig_barra_pan.update_layout(
            yaxis_title=None, xaxis_title="% del total de este grupo de segmentos",
            legend_title_text="", legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        )
        fig_barra_pan.update_xaxes(ticksuffix="%")
        fig_barra_pan.update_yaxes(automargin=True)
        st.plotly_chart(estilizar_grafico(fig_barra_pan), use_container_width=True, theme=None)

        # Insight automático — la lectura ejecutiva de un vistazo, sin tener que
        # interpretar el gráfico para llegar a la conclusión.
        seg_top_potencial = df_seg.loc[df_seg["Potencial"].idxmax()]
        st.caption(
            f"Mayor potencial fuera de las prioridades ya cubiertas arriba: "
            f"**{seg_top_potencial['Segmento']}** (${seg_top_potencial['Potencial']:,.0f}, "
            f"{seg_top_potencial['Clientes']:,.0f} clientes)."
        )

    divisor()

    # ==============================================
    # DISTRIBUCIÓN DE RECENCIA
    # ==============================================
    st.subheader("Distribución de recencia")

    # Usamos la fecha real de última sesión (no "días" relativos) para que el
    # eje X hable en mes/año — mucho más legible para planificar que un
    # conteo de días desde hoy que cambia cada vez que se mira el dashboard.
    fechas = pd.to_datetime(df_panorama["ultima_sesion"], errors="coerce", utc=True)
    recencia_valida = df_panorama.loc[fechas.notna(), "recencia_dias"]
    fechas = fechas.dropna()

    MESES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

    if fechas.empty:
        st.info("No hay fechas de última sesión válidas en este filtro.")
    else:
        meses = fechas.dt.tz_localize(None).values.astype("datetime64[M]")
        df_bins_recencia = (
            pd.Series(meses).value_counts().sort_index().rename_axis("mes").reset_index(name="clientes")
        )
        df_bins_recencia["mes"] = pd.to_datetime(df_bins_recencia["mes"])
        # "orden" cronológico (ascendente) se usa SOLO para el color — el más
        # reciente siempre tiene el ordinal más alto, sin importar en qué
        # posición del eje X se dibuje.
        df_bins_recencia["orden"] = df_bins_recencia["mes"].map(pd.Timestamp.toordinal)
        df_bins_recencia["anio"] = df_bins_recencia["mes"].dt.year.astype(str)
        df_bins_recencia["mes_abrev"] = df_bins_recencia["mes"].apply(lambda d: MESES_ES[d.month - 1])

        # Más reciente a la izquierda, más antiguo a la derecha (igual que
        # "0 días de recencia" siempre partía a la izquierda en la versión anterior).
        df_bins_recencia = df_bins_recencia.sort_values("mes", ascending=False).reset_index(drop=True)

        # Barra "espaciadora" invisible (altura 0, sin etiqueta de mes) entre
        # cada cambio de año — da una separación notoria pero sutil entre años.
        filas = []
        for i, fila in df_bins_recencia.iterrows():
            filas.append(fila)
            es_ultimo = i == len(df_bins_recencia) - 1
            if not es_ultimo and df_bins_recencia.loc[i + 1, "anio"] != fila["anio"]:
                filas.append(pd.Series({
                    "mes": pd.NaT, "clientes": 0, "orden": fila["orden"],
                    "anio": "", "mes_abrev": "",
                }))
        df_grafico = pd.DataFrame(filas).reset_index(drop=True)

        # Posiciones numéricas fijas (0, 1, 2...) en vez de un eje de categorías
        # — así Plotly no puede reordenar los meses por su cuenta (le pasó con
        # el eje multicategoría: reordenaba alfabético/numérico y arruinaba la
        # línea de tendencia). Con posiciones numéricas, el orden que armamos
        # a mano (más reciente a la izquierda) queda garantizado.
        df_grafico["x_pos"] = range(len(df_grafico))

        colores_bar = px.colors.sample_colorscale(
            ESCALA_ROJA,
            [(v - df_bins_recencia["orden"].min()) / max(df_bins_recencia["orden"].max() - df_bins_recencia["orden"].min(), 1)
             for v in df_grafico["orden"]],
        )

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=df_grafico["x_pos"], y=df_grafico["clientes"],
            marker=dict(color=colores_bar, line=dict(color="#FFFFFF", width=1.5)),
            name="Clientes",
            hovertemplate="%{customdata}<br>%{y:,} clientes<extra></extra>",
            customdata=[f"{m} {a}" if m else "" for m, a in zip(df_grafico["mes_abrev"], df_grafico["anio"])],
        ))
        fig3.add_trace(go.Scatter(
            x=df_grafico["x_pos"],
            y=df_grafico["clientes"].rolling(window=3, center=True, min_periods=1).mean(),
            mode="lines",
            line=dict(color=NEGRO, width=2.5, shape="spline"),
            name="Tendencia",
            hoverinfo="skip",
        ))

        # Etiqueta de mes en el tick, año como anotación centrada debajo del
        # grupo de meses que le corresponde (reemplaza el agrupamiento
        # automático de Plotly, que no respetaba nuestro orden cronológico).
        fig3.update_xaxes(
            tickmode="array",
            tickvals=df_grafico["x_pos"],
            ticktext=df_grafico["mes_abrev"],
        )
        for anio_valor in [a for a in df_grafico["anio"].unique() if a]:
            posiciones = df_grafico.loc[df_grafico["anio"] == anio_valor, "x_pos"]
            fig3.add_annotation(
                x=(posiciones.min() + posiciones.max()) / 2, y=-0.16, yref="paper",
                text=f"<b>{anio_valor}</b>", showarrow=False,
                font=dict(size=11, color=TEXTO_SECUNDARIO),
            )

        fig3.update_layout(
            title="Tendencia de sesiones", bargap=0.12, showlegend=True, legend_title_text="",
            yaxis_title="Clientes", xaxis_title=None, margin=dict(b=80),
        )
        st.plotly_chart(estilizar_grafico(fig3), use_container_width=True, theme=None)

        # ---- Valor agregado: métricas de urgencia con los mismos umbrales
        # que usa la segmentación real (UMBRALES en pipeline_Dolly.py), para
        # que el gráfico no sea solo descriptivo sino que diga "actúa aquí".
        total_validos = len(recencia_valida)
        idx_ventana_vtex = recencia_valida[recencia_valida <= 30].index
        n_ventana_vtex   = len(idx_ventana_vtex)
        monto_ventana_vtex = df_panorama.loc[idx_ventana_vtex, "monto_carrito"].sum()
        n_activos      = int((recencia_valida <= UMBRALES["recencia_activo"]).sum())
        n_riesgo       = int(((recencia_valida > UMBRALES["recencia_activo"]) &
                               (recencia_valida <= UMBRALES["recencia_riesgo"])).sum())

        st.markdown(f"""
            <div style="display:flex; gap:20px; align-items:stretch; flex-wrap:nowrap;">
                <div style="flex:1 1 0; min-width:0; background:{CARD}; border:0.5px solid {BORDE};
                            border-radius:10px; padding:18px 20px;">
                    <div style="font-size:26px; font-weight:700; color:{ROJO};">{n_ventana_vtex:,}</div>
                    <div style="font-size:13px; color:{TEXTO_SECUNDARIO}; margin-top:2px;">Con dato de abandono confiable</div>
                    <div style="font-size:11px; color:{TEXTO_SECUNDARIO}; margin-top:2px;">
                        Últimos 30 días (ventana real del CSV VTEX) · {n_ventana_vtex/total_validos*100:.0f}% del filtro
                    </div>
                    <hr style="margin:14px 0; border:none; border-top:0.5px solid {BORDE};">
                    <div style="font-size:26px; font-weight:700; color:{ROJO};">${monto_ventana_vtex:,.0f}</div>
                    <div style="font-size:13px; color:{TEXTO_SECUNDARIO}; margin-top:2px;">Potencial recuperable en esa ventana</div>
                    <div style="font-size:11px; color:{TEXTO_SECUNDARIO}; margin-top:2px;">
                        Suma de monto_carrito de esos clientes con dato confiable.
                    </div>
                </div>
                <div style="flex:1 1 0; min-width:0; display:flex; flex-direction:column; gap:10px;">
                    <div style="flex:1; background:{CARD}; border:0.5px solid {BORDE}; border-radius:10px;
                                padding:14px 16px;">
                        <div style="font-size:24px; font-weight:700; color:{NEGRO};">{n_activos:,}</div>
                        <div style="font-size:12px; color:{TEXTO_SECUNDARIO}; margin-top:2px;">Activos</div>
                        <div style="font-size:11px; color:{TEXTO_SECUNDARIO}; margin-top:4px;">
                            ≤{UMBRALES['recencia_activo']} días sin sesión · {n_activos/total_validos*100:.0f}%
                        </div>
                    </div>
                    <div style="flex:1; background:{CARD}; border:0.5px solid {BORDE}; border-radius:10px;
                                padding:14px 16px;">
                        <div style="font-size:24px; font-weight:700; color:{VINO};">{n_riesgo:,}</div>
                        <div style="font-size:12px; color:{TEXTO_SECUNDARIO}; margin-top:2px;">Entrando en riesgo</div>
                        <div style="font-size:11px; color:{TEXTO_SECUNDARIO}; margin-top:4px;">
                            {UMBRALES['recencia_activo']}-{UMBRALES['recencia_riesgo']} días · {n_riesgo/total_validos*100:.0f}%
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.caption("Umbrales de urgencia: los mismos que usa la segmentación (Cliente Activo / En Riesgo).")

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
