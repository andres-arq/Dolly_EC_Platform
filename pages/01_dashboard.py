# =============================================================================
# 01_dashboard.py — Dashboard principal
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline_Dolly import (
    cargar_perfil_clientes, calcular_estadisticas,
    clientes_prioritarios, resumen_recuperables,
    DESCRIPCION_SEGMENTOS, ORDEN_PRIORIDAD_SEGMENTOS, SEGMENTOS_RECUPERABLES, PARAMS,
)
from estilo_Dolly import (
    aplicar_estilo, encabezado_pagina, kpi_card, divisor, estilizar_grafico,
    NEGRO, ROJO, VINO, GRIS, GRIS_CLARO, CARD, BORDE, TEXTO_SECUNDARIO, ESCALA_NEUTRA, ESCALA_ROJA,
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

# ==============================================
# FILTRO DE RECENCIA (afecta a todo el Dashboard)
# ==============================================
recencia_min, recencia_max = int(df["recencia_dias"].min()), int(df["recencia_dias"].max())
rango_recencia = st.slider(
    "Filtrar por recencia (días desde última sesión)",
    min_value=recencia_min,
    max_value=recencia_max,
    value=(recencia_min, recencia_max),
)
df = df[
    (df["recencia_dias"] >= rango_recencia[0]) &
    (df["recencia_dias"] <= rango_recencia[1])
]
st.caption(f"{len(df):,} clientes dentro del rango seleccionado.")

if df.empty:
    st.info("No hay clientes en el rango de recencia seleccionado.")
    st.stop()

divisor()

stats = calcular_estadisticas(df)
resumen_rec = resumen_recuperables(df)
total_recuperables = int(resumen_rec["clientes"].sum()) if not resumen_rec.empty else 0

# ==============================================
# CLIENTE MÁS PRIORITARIO AHORA
# ==============================================
top_cliente_df = clientes_prioritarios(df, n=1)

if not top_cliente_df.empty:
    c = top_cliente_df.iloc[0]

    def _o_sin_dato(valor):
        return valor if pd.notna(valor) and str(valor).strip() not in ("", "nan", "None") else "Sin dato"

    producto_txt = _o_sin_dato(c.get("marca_producto"))
    categoria_txt = _o_sin_dato(c.get("categoria_producto"))
    sku_txt = _o_sin_dato(c.get("producto_id"))

    st.markdown(f"""
        <div style="background:{CARD}; border:0.5px solid {BORDE}; border-left:5px solid {ROJO};
                    border-radius:0 12px 12px 0; padding:20px 24px; margin-bottom:8px;">
            <div style="font-size:11px; letter-spacing:0.08em; color:{ROJO}; font-weight:600;
                        text-transform:uppercase; margin-bottom:6px;">
                🔴 Cliente más prioritario ahora
            </div>
            <div style="display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:12px;">
                <div>
                    <div style="font-size:20px; font-weight:700; color:{NEGRO};">{c.get('segmento','—')}</div>
                    <div style="font-size:13px; color:{TEXTO_SECUNDARIO}; margin-top:2px;">
                        userId: <code>{c.get('userId','—')}</code> · paso: {c.get('paso_abandono','—')} ·
                        hace {c.get('recencia_dias','—')} días
                    </div>
                    <div style="font-size:13px; color:{TEXTO_SECUNDARIO}; margin-top:4px;">
                        Interés: <b style="color:{NEGRO};">{producto_txt} - {categoria_txt} - {sku_txt}</b>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:26px; font-weight:700; color:{ROJO};">${c.get('monto_carrito',0):,.0f}</div>
                    <div style="font-size:12px; color:{TEXTO_SECUNDARIO};">
                        {'📞 Teléfono' if c.get('tiene_telefono') else '—'} ·
                        {'📧 Newsletter' if c.get('tiene_newsletter') else '—'}
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.caption("Ve a **Perfil de Cliente** y busca este userId para contactarlo. Excluye siempre a quienes ya compraron (paso \"Finalizado\").")
else:
    st.info("No hay clientes pendientes de contacto en este momento — todos están en \"Finalizado\" o sin actividad reciente.")

divisor()

# ==============================================
# KPI CARDS
# ==============================================
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    kpi_card("Total clientes", f"{stats['total_clientes']:,}")

with col2:
    kpi_card("Clientes recuperables ahora", f"{total_recuperables:,}", color=ROJO)

with col3:
    kpi_card("Monto mediano carrito (toda la base)", f"${stats['monto_mediano']:,.0f}")

with col4:
    kpi_card("% Contactables (newsletter)", f"{stats['pct_contactables']:.1f}%", color=GRIS)

with col5:
    kpi_card("% Sobre umbral flete gratis", f"{stats['pct_sobre_umbral']:.1f}%", color=VINO)

divisor()

# ==============================================
# OPORTUNIDADES DE RECUPERACIÓN
# ==============================================
st.subheader("Oportunidades de recuperación")
st.caption(
    "Clientes que llegaron a un paso real del checkout (Carrito, Dirección/despacho, "
    "Forma de pago o Datos personales) sin completar la compra — son pocos frente al "
    "total de la base, por eso tienen su propio gráfico en vez de perderse en el de abajo. "
    "Ambas barras están en % del total recuperable, para comparar directamente si un "
    "segmento pesa más en clientes o en plata."
)

if not resumen_rec.empty:
    total_clientes_rec  = resumen_rec["clientes"].sum()
    total_potencial_rec = resumen_rec["potencial_clp"].sum()
    resumen_rec["pct_clientes"]  = resumen_rec["clientes"] / total_clientes_rec * 100
    resumen_rec["pct_potencial"] = resumen_rec["potencial_clp"] / total_potencial_rec * 100

    col_rec1, col_rec2 = st.columns(2, gap="large")
    with col_rec1:
        fig_rec1 = px.bar(
            resumen_rec.sort_values("pct_clientes"),
            x="pct_clientes", y="segmento", orientation="h",
            color_discrete_sequence=[ROJO],
            text=resumen_rec.sort_values("pct_clientes")["clientes"].map(lambda v: f"{v:,}"),
            title="% de clientes recuperables, por segmento",
        )
        fig_rec1.update_traces(textposition="outside")
        fig_rec1.update_layout(showlegend=False, yaxis_title=None, xaxis_title="% del total recuperable")
        fig_rec1.update_xaxes(range=[0, 100], ticksuffix="%")
        fig_rec1.update_yaxes(automargin=True)
        st.plotly_chart(estilizar_grafico(fig_rec1), use_container_width=True, theme=None)
    with col_rec2:
        fig_rec2 = px.bar(
            resumen_rec.sort_values("pct_potencial"),
            x="pct_potencial", y="segmento", orientation="h",
            color_discrete_sequence=[VINO],
            text=resumen_rec.sort_values("pct_potencial")["potencial_clp"].map(lambda v: f"${v:,.0f}"),
            title="% del potencial CLP recuperable, por segmento",
        )
        fig_rec2.update_traces(textposition="outside")
        fig_rec2.update_layout(showlegend=False, yaxis_title=None, xaxis_title="% del total recuperable")
        fig_rec2.update_xaxes(range=[0, 100], ticksuffix="%")
        fig_rec2.update_yaxes(automargin=True)
        st.plotly_chart(estilizar_grafico(fig_rec2), use_container_width=True, theme=None)
else:
    st.info("No hay clientes en segmentos de recuperación en este momento.")

divisor()

# ==============================================
# CLIENTES PRIORITARIOS Y RECIENTES
# ==============================================
st.subheader("🎯 Clientes prioritarios ahora")
st.caption(
    "Ordenados primero por urgencia de segmento (Recuperable Urgente/Flete arriba) "
    "y, dentro de cada nivel, por quién tuvo actividad más reciente. Es la lista "
    "de a quién contactar hoy."
)

cantidad = st.slider("Cantidad de clientes a mostrar", min_value=10, max_value=100, value=25, step=5)
df_prioritarios = clientes_prioritarios(df, n=cantidad)

columnas_prioridad = [
    "userId", "segmento", "recencia_dias", "monto_carrito",
    "producto_id", "categoria_producto", "marca_producto",
    "paso_abandono", "es_comprador", "tiene_carrito_abandonado_historico",
    "tiene_telefono", "tiene_newsletter",
]
columnas_existentes_prioridad = [c for c in columnas_prioridad if c in df_prioritarios.columns]

st.dataframe(
    df_prioritarios[columnas_existentes_prioridad],
    use_container_width=True,
    hide_index=True,
)

csv_prioritarios = df_prioritarios[columnas_existentes_prioridad].to_csv(index=False, encoding="utf-8-sig")
st.download_button(
    label="⬇️  Descargar lista de contacto prioritario",
    data=csv_prioritarios,
    file_name="dolly_clientes_prioritarios.csv",
    mime="text/csv",
)

divisor()

# ==============================================
# PANORAMA GENERAL — TODOS LOS SEGMENTOS
# ==============================================
st.subheader("Panorama general de la base")
st.caption(
    "Torta con todos los segmentos. El gráfico de barras de la derecha excluye "
    "Perdido, Inactivo y los 4 Recuperable (ya tienen su propio gráfico arriba) "
    "para que el resto de los segmentos —donde también hay decisiones que tomar— "
    "no quede invisible al lado de esos volúmenes tan grandes."
)

# ==============================================
# GRÁFICOS
# ==============================================
col_izq, col_der = st.columns(2, gap="large")

with col_izq:
    df_pot = pd.DataFrame({
        "Segmento":   list(stats["potencial_por_segmento"].keys()),
        "Potencial":  list(stats["potencial_por_segmento"].values()),
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

with col_der:
    SEGMENTOS_EXCLUIDOS_PANORAMA = SEGMENTOS_RECUPERABLES + ["Perdido", "Inactivo"]

    df_seg = pd.DataFrame({
        "Segmento": list(stats["clientes_por_segmento"].keys()),
        "Clientes": list(stats["clientes_por_segmento"].values()),
    })
    df_seg = df_seg[~df_seg["Segmento"].isin(SEGMENTOS_EXCLUIDOS_PANORAMA)]
    df_seg = df_seg.sort_values("Clientes", ascending=True)

    # Color por accionabilidad (mismo orden de urgencia que el resto del
    # Dashboard) en vez de por volumen — así el segmento más urgente destaca
    # aunque tenga pocos clientes, y no al revés.
    n_segmentos_totales = max(len(ORDEN_PRIORIDAD_SEGMENTOS), 1)
    mapa_color_prioridad = {
        seg: px.colors.sample_colorscale(
            [GRIS_CLARO, VINO, ROJO],
            [1 - (rank - 1) / max(n_segmentos_totales - 1, 1)],
        )[0]
        for seg, rank in ORDEN_PRIORIDAD_SEGMENTOS.items()
    }

    fig = px.bar(
        df_seg,
        x="Clientes",
        y="Segmento",
        orientation="h",
        color="Segmento",
        color_discrete_map=mapa_color_prioridad,
        title="Clientes por segmento (excluye Perdido/Inactivo/Recuperables)",
    )
    fig.update_layout(showlegend=False, yaxis_title=None)
    fig.update_yaxes(automargin=True)
    st.plotly_chart(estilizar_grafico(fig), use_container_width=True, theme=None)

divisor()

# ==============================================
# FLUJO DE CLASIFICACIÓN — CÓMO AVANZA UN CLIENTE ENTRE SEGMENTOS
# ==============================================
st.subheader("🧭 Cómo avanza un cliente entre segmentos")
st.caption(
    "Haz clic en cada segmento para ver su detalle y la recomendación. Es una "
    "simplificación en 3 rutas de la misma lógica que usa el sistema para clasificar "
    "— en la realidad es un árbol de decisión, no una sola línea, pero estas son las "
    "rutas que más se repiten."
)


def _paso_flujo(nombre_segmento):
    descripcion, recomendacion = DESCRIPCION_SEGMENTOS.get(nombre_segmento, ("", ""))
    with st.expander(nombre_segmento):
        st.markdown(f"**Qué significa:** {descripcion}")
        st.markdown(f"**Recomendación:** {recomendacion}")


def _flujo_vertical(secuencia):
    for i, seg in enumerate(secuencia):
        _paso_flujo(seg)
        if i < len(secuencia) - 1:
            st.markdown(
                f"<div style='text-align:center; font-size:20px; color:{ROJO}; margin:-4px 0 4px 0;'>↓</div>",
                unsafe_allow_html=True,
            )


col_ruta1, col_ruta2, col_ruta3 = st.columns(3, gap="large")

with col_ruta1:
    st.markdown(
        "**Ruta 1 — Abandonó el checkout** *(no es secuencial — cada cliente cae en "
        "una sola, según el paso exacto donde se detuvo, ordenadas de más a menos urgente)*"
    )
    _flujo_vertical(["Recuperable Urgente", "Recuperable Flete", "Recuperable Temprano", "Recuperable Bajo"])

with col_ruta2:
    st.markdown("**Ruta 2 — Cliente de alto monto (≥$100.000), a medida que pasa el tiempo sin volver a comprar**")
    _flujo_vertical(["Cliente VIP", "Alto Valor Reciente", "Alto Valor En Riesgo", "Alto Valor Perdido"])

with col_ruta3:
    st.markdown("**Ruta 3 — Actividad general, a medida que pasa el tiempo sin actividad**")
    _flujo_vertical(["Potencial Sin Carrito", "Potencial Con Carrito", "Cliente Activo", "Inactivo", "Perdido"])

divisor()

col_izq2, col_der2 = st.columns(2, gap="large")

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
    st.plotly_chart(estilizar_grafico(fig3), use_container_width=True, theme=None)

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
    st.plotly_chart(estilizar_grafico(fig4), use_container_width=True, theme=None)

divisor()

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
