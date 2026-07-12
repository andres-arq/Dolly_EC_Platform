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
    clientes_prioritarios, resumen_recuperables, formatear_telefono_cl,
    DESCRIPCION_SEGMENTOS, ORDEN_PRIORIDAD_SEGMENTOS, SEGMENTOS_RECUPERABLES, PARAMS,
)
from estilo_Dolly import (
    aplicar_estilo, sidebar_dolly, encabezado_pagina, kpi_card, divisor, estilizar_grafico,
    NEGRO, ROJO, VINO, GRIS, CARD, BORDE, TEXTO_SECUNDARIO,
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


def _telefono_visible(c):
    """Muestra el número real (formateado) si existe; si solo tenemos el
    booleano tiene_telefono=True pero no el número (datos antiguos sin
    re-procesar), cae de vuelta al ícono genérico en vez de mostrar 'None'."""
    numero = c.get("homePhone")
    if pd.notna(numero) and str(numero).strip() not in ("", "nan", "None"):
        return f"📞 {formatear_telefono_cl(numero)}"
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
    "Carritos abandonados en un paso real del checkout. Barras en % del total "
    "recuperable, para comparar clientes vs. plata por segmento."
)

if not resumen_rec.empty:
    total_clientes_rec  = resumen_rec["clientes"].sum()
    total_potencial_rec = resumen_rec["potencial_clp"].sum()
    resumen_rec["pct_clientes"]  = resumen_rec["clientes"] / total_clientes_rec * 100
    resumen_rec["pct_potencial"] = resumen_rec["potencial_clp"] / total_potencial_rec * 100

    # Orden de segmentos consistente en ambas series (de mayor a menor % de clientes)
    orden_segmentos_rec = (
        resumen_rec.sort_values("pct_clientes", ascending=True)["segmento"].tolist()
    )

    # Combinamos ambas métricas en un solo dataframe "largo" para graficar barras
    # agrupadas — un color para clientes, otro para potencial CLP, mismo eje %
    # para que se puedan comparar directamente sin perder el detalle (el texto
    # de cada barra sigue mostrando el número real, no solo el %).
    df_combo = pd.concat([
        pd.DataFrame({
            "segmento": resumen_rec["segmento"],
            "tipo": "Clientes",
            "pct": resumen_rec["pct_clientes"],
            "texto": resumen_rec["clientes"].map(lambda v: f"{v:,}"),
        }),
        pd.DataFrame({
            "segmento": resumen_rec["segmento"],
            "tipo": "Potencial CLP",
            "pct": resumen_rec["pct_potencial"],
            "texto": resumen_rec["potencial_clp"].map(lambda v: f"${v:,.0f}"),
        }),
    ], ignore_index=True)

    fig_rec = px.bar(
        df_combo,
        x="pct", y="segmento", color="tipo", orientation="h", barmode="group",
        text="texto",
        color_discrete_map={"Clientes": ROJO, "Potencial CLP": VINO},
        category_orders={"segmento": orden_segmentos_rec},
        title="Clientes vs. potencial CLP recuperable, por segmento (% del total recuperable)",
    )
    fig_rec.update_traces(textposition="outside")
    fig_rec.update_layout(
        yaxis_title=None, xaxis_title="% del total recuperable",
        legend_title_text="", legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig_rec.update_xaxes(range=[0, 100], ticksuffix="%")
    fig_rec.update_yaxes(automargin=True)
    st.plotly_chart(estilizar_grafico(fig_rec), use_container_width=True, theme=None)
    st.caption(
        "El paso de abandono vía CSV VTEX solo cubre ~30-31 días hacia atrás — "
        "argumento a favor de la conexión por API."
    )
else:
    st.info("No hay clientes en segmentos de recuperación en este momento.")

divisor()

# ==============================================
# CLIENTES PRIORITARIOS Y RECIENTES
# ==============================================
st.subheader("🎯 Clientes prioritarios ahora")
st.caption("Ordenados por urgencia de segmento, luego por actividad más reciente.")

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

# NOTA: la sección "Panorama general de la base" (torta, barra y las dos
# distribuciones) se trasladó a 02_segmentacion.py — el Dashboard se enfoca
# en "a quién atacar con urgencia hoy" (KPIs, cliente prioritario, oportunidades
# de recuperación, clientes prioritarios), y Segmentación pasa a ser el único
# lugar para explorar/entender la base completa. Pendiente: definir qué
# reemplaza este espacio (top urgencias / racha sin campaña / matriz de
# priorización — a decidir).

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
st.caption("Haz clic en cada segmento para ver el detalle y la recomendación.")


def _caja_intro_ruta(html_contenido):
    """Caja que diferencia visualmente el párrafo introductorio de cada ruta.
    Altura fija (no min-height) para que las 3 columnas queden con exactamente
    el mismo tamaño, sin importar cuánto texto tenga cada una."""
    st.markdown(
        f"""<div style="background:{CARD}; border:0.5px solid {BORDE}; border-radius:10px;
                    padding:14px 16px; margin-bottom:16px; height:110px; overflow:hidden;">
            {html_contenido}
        </div>""",
        unsafe_allow_html=True,
    )


def _paso_flujo(nombre_segmento):
    """Cada segmento como un rectángulo de solo borde (sin relleno) que se
    expande hacia abajo con el detalle y la recomendación al hacer clic."""
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
    _caja_intro_ruta(
        f"<b>Ruta 1 — Abandonó el checkout</b><br>"
        f"<span style='font-size:13px; color:{TEXTO_SECUNDARIO};'>"
        f"Según el paso exacto donde abandonó, ordenado de más a menos urgente.</span>"
    )
    _flujo_vertical(["Recuperable Urgente", "Recuperable Flete", "Recuperable Temprano", "Recuperable Bajo"])

with col_ruta2:
    _caja_intro_ruta(
        f"<b>Ruta 2 — Cliente de alto monto</b><br>"
        f"<span style='font-size:13px; color:{TEXTO_SECUNDARIO};'>"
        f"≥$100.000, a medida que pasa el tiempo sin volver a comprar.</span>"
    )
    _flujo_vertical(["Cliente VIP", "Alto Valor Reciente", "Alto Valor En Riesgo", "Alto Valor Perdido"])

with col_ruta3:
    _caja_intro_ruta(
        f"<b>Ruta 3 — Actividad general</b><br>"
        f"<span style='font-size:13px; color:{TEXTO_SECUNDARIO};'>"
        f"A medida que pasa el tiempo sin actividad.</span>"
    )
    _flujo_vertical(["Potencial Sin Carrito", "Potencial Con Carrito", "Cliente Activo", "Inactivo", "Perdido"])
