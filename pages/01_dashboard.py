# =============================================================================
# 01_dashboard.py — Dashboard principal
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
    clientes_prioritarios, resumen_recuperables,
    DESCRIPCION_SEGMENTOS, ORDEN_PRIORIDAD_SEGMENTOS, SEGMENTOS_RECUPERABLES, PARAMS,
)
from estilo_Dolly import (
    aplicar_estilo, sidebar_dolly, encabezado_pagina, kpi_card, divisor, estilizar_grafico,
    NEGRO, ROJO, VINO, GRIS, GRIS_CLARO, CARD, BORDE, TEXTO_SECUNDARIO, ESCALA_NEUTRA, ESCALA_ROJA,
)

st.set_page_config(page_title="Dashboard — Dolly", page_icon="📊", layout="wide")
aplicar_estilo()
sidebar_dolly()

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
# CLIENTES PRIORITARIOS AHORA — MÁS RECIENTE Y MÁS VALIOSO
# ==============================================
# Ambos salen del mismo pool que compone el KPI "Clientes recuperables ahora"
# (los 4 segmentos Recuperable, sin contar a quienes ya compraron) — así el
# número de la tarjeta siempre corresponde a alguien contado en esos 324.
pool_recuperables = df[df["segmento"].isin(SEGMENTOS_RECUPERABLES)].copy()
if "es_comprador" in pool_recuperables.columns:
    pool_recuperables = pool_recuperables[pool_recuperables["es_comprador"] != True]  # noqa: E712

pool_recuperables["_prioridad"] = pool_recuperables["segmento"].map(ORDEN_PRIORIDAD_SEGMENTOS).fillna(99)

cliente_reciente_df = pool_recuperables.sort_values(["_prioridad", "recencia_dias"], ascending=[True, True])
cliente_valioso_df  = pool_recuperables.sort_values("monto_carrito", ascending=False)


def _o_sin_dato(valor):
    return valor if pd.notna(valor) and str(valor).strip() not in ("", "nan", "None") else "Sin dato"


def _formatear_telefono_cl(numero):
    """
    Formatea a '+56 9 0000 0000'. Acepta el número venga como venga en VTEX
    (con o sin +, con o sin 56, con espacios/guiones) — se queda solo con los
    dígitos y arma el formato chileno estándar de celular (9 dígitos después
    del 56). Si no calza con ese patrón (fijo, extranjero, dato corrupto),
    devuelve el número tal cual llegó en vez de forzar un formato incorrecto.
    """
    solo_digitos = "".join(ch for ch in str(numero) if ch.isdigit())

    if solo_digitos.startswith("56") and len(solo_digitos) == 11:
        cod_pais, resto = solo_digitos[:2], solo_digitos[2:]
    elif len(solo_digitos) == 9 and solo_digitos.startswith("9"):
        cod_pais, resto = "56", solo_digitos
    else:
        return str(numero)  # formato no reconocido — se muestra tal cual

    return f"+{cod_pais} {resto[0]} {resto[1:5]} {resto[5:9]}"


def _telefono_visible(c):
    """Muestra el número real (formateado) si existe; si solo tenemos el
    booleano tiene_telefono=True pero no el número (datos antiguos sin
    re-procesar), cae de vuelta al ícono genérico en vez de mostrar 'None'."""
    numero = c.get("homePhone")
    if pd.notna(numero) and str(numero).strip() not in ("", "nan", "None"):
        return f"📞 {_formatear_telefono_cl(numero)}"
    return "📞 Teléfono" if c.get("tiene_telefono") else "—"


def _tarjeta_cliente(titulo, icono, color, c):
    producto_txt  = _o_sin_dato(c.get("marca_producto"))
    categoria_txt = _o_sin_dato(c.get("categoria_producto"))
    sku_txt       = _o_sin_dato(c.get("producto_id"))

    st.markdown(f"""
        <div style="background:{CARD}; border:0.5px solid {BORDE}; border-left:5px solid {color};
                    border-radius:0 12px 12px 0; padding:20px 24px; height:100%;">
            <div style="font-size:11px; letter-spacing:0.08em; color:{color}; font-weight:600;
                        text-transform:uppercase; margin-bottom:6px;">
                {icono} {titulo}
            </div>
            <div style="font-size:20px; font-weight:700; color:{NEGRO};">{c.get('segmento','—')}</div>
            <div style="font-size:13px; color:{TEXTO_SECUNDARIO}; margin-top:2px;">
                userId: <code>{c.get('userId','—')}</code> · paso: {c.get('paso_abandono','—')} ·
                hace {c.get('recencia_dias','—')} días
            </div>
            <div style="font-size:13px; color:{TEXTO_SECUNDARIO}; margin-top:4px;">
                Interés: <b style="color:{NEGRO};">{producto_txt} - {categoria_txt} - {sku_txt}</b>
            </div>
            <div style="font-size:26px; font-weight:700; color:{color}; margin-top:10px;">
                ${c.get('monto_carrito', 0):,.0f}
            </div>
            <div style="font-size:12px; color:{TEXTO_SECUNDARIO};">
                {_telefono_visible(c)} ·
                {'📧 Newsletter' if c.get('tiene_newsletter') else '—'}
            </div>
        </div>
    """, unsafe_allow_html=True)


if not pool_recuperables.empty:
    col_reciente, col_valioso = st.columns(2, gap="large")
    with col_reciente:
        _tarjeta_cliente("Cliente más reciente", "🔴", ROJO, cliente_reciente_df.iloc[0])
    with col_valioso:
        _tarjeta_cliente("Cliente más valioso", "💎", VINO, cliente_valioso_df.iloc[0])
    st.caption("Ve a **Perfil de Cliente** y busca el userId para contactarlo. Excluye siempre a quienes ya compraron (paso \"Finalizado\").")
else:
    st.info("No hay clientes recuperables pendientes de contacto en este momento.")

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
    "Torta con todos los segmentos. El gráfico de barras excluye "
    "Perdido, Inactivo y los 4 Recuperable (ya tienen su propio gráfico arriba) "
    "para que el resto de los segmentos —donde también hay decisiones que tomar— "
    "no quede invisible al lado de esos volúmenes tan grandes."
)

segmentos_disponibles_panorama = sorted(df["segmento"].unique().tolist())
segmentos_filtro_panorama = st.multiselect(
    "Filtrar esta sección por segmento",
    options=segmentos_disponibles_panorama,
    default=segmentos_disponibles_panorama,
    help="Afecta solo los 4 gráficos de Panorama general (torta, barras y las "
         "dos distribuciones de abajo) — no al resto del Dashboard.",
)

if not segmentos_filtro_panorama:
    st.warning("Selecciona al menos un segmento para ver el panorama.")
else:
    df_panorama = df[df["segmento"].isin(segmentos_filtro_panorama)]
    stats_panorama = calcular_estadisticas(df_panorama)

    # ==============================================
    # GRÁFICOS — TORTA Y BARRA
    # ==============================================
    col_izq, col_der = st.columns(2, gap="large")

    with col_izq:
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

    with col_der:
        SEGMENTOS_EXCLUIDOS_PANORAMA = SEGMENTOS_RECUPERABLES + ["Perdido", "Inactivo"]

        df_seg = pd.DataFrame({
            "Segmento": list(stats_panorama["clientes_por_segmento"].keys()),
            "Clientes": list(stats_panorama["clientes_por_segmento"].values()),
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

        if df_seg.empty:
            st.info("Los segmentos elegidos quedan todos excluidos de este gráfico (Perdido/Inactivo/Recuperables).")
        else:
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
    st.caption("Cuántos clientes tuvieron su última sesión hace X días — la línea suaviza el conteo bin a bin para ver la tendencia real detrás del vaivén.")

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
