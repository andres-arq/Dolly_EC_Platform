# =============================================================================
# 04_campanas.py — Gestión de plantillas de correo por segmento
# =============================================================================

import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline_Dolly import (
    cargar_perfil_clientes,
    cargar_plantillas,
    guardar_plantillas,
    PARAMS,
)
from estilo_Dolly import (
    aplicar_estilo, encabezado_pagina, kpi_card, divisor,
    NEGRO, ROJO, VINO, GRIS,
)

st.set_page_config(page_title="Campañas — Dolly", page_icon="📧", layout="wide")
aplicar_estilo()

encabezado_pagina(
    modulo="Módulo 04 · Campañas",
    titulo="Gestión de campañas",
    subtitulo="Edita las plantillas de correo por segmento y activa o desactiva campañas.",
)

# Cargar datos
df         = cargar_perfil_clientes()
plantillas = cargar_plantillas()

if df.empty:
    st.warning("⚠️  No hay datos disponibles. Ve a **Actualizar Data** para cargar el CSV de VTEX.")
    st.stop()

# Estadísticas por segmento para mostrar junto a cada plantilla
stats_segmento = df.groupby("segmento").agg(
    clientes      = ("userId",         "count"),
    monto_mediano = ("monto_carrito",   "median"),
    pct_newsletter= ("tiene_newsletter","mean"),
).round(1).reset_index()
stats_segmento["pct_newsletter"] = (stats_segmento["pct_newsletter"] * 100).round(1)

if "tiene_email" in df.columns:
    pct_email_seg = df.groupby("segmento")["tiene_email"].mean() * 100
    stats_segmento["pct_email"] = stats_segmento["segmento"].map(pct_email_seg).round(1)
else:
    stats_segmento["pct_email"] = 0.0

stats_dict = stats_segmento.set_index("segmento").to_dict("index")

# ==============================================
# SELECTOR DE SEGMENTO
# ==============================================
st.subheader("Seleccionar segmento")

segmentos = list(plantillas.keys())
segmento_sel = st.selectbox(
    "Segmento a editar",
    segmentos,
    format_func=lambda s: f"{s} ({stats_dict.get(s, {}).get('clientes', 0):,} clientes)"
)

divisor()

# Info del segmento seleccionado
info = stats_dict.get(segmento_sel, {})
if info:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Clientes en segmento", f"{info.get('clientes', 0):,}")
    with col2:
        kpi_card("Monto mediano", f"${info.get('monto_mediano', 0):,.0f}")
    with col3:
        kpi_card("% Contactables newsletter", f"{info.get('pct_newsletter', 0):.1f}%", color=GRIS)
    with col4:
        pct_email_val = info.get("pct_email", 0)
        kpi_card(
            "% Con email disponible",
            f"{pct_email_val:.1f}%",
            color=ROJO if pct_email_val < 50 else NEGRO,
        )

divisor()

# ==============================================
# EDITOR DE PLANTILLA
# ==============================================
plantilla_actual = plantillas.get(segmento_sel, {})

col_editor, col_preview = st.columns([1, 1])

with col_editor:
    st.subheader("✏️ Editor")

    activa = st.toggle(
        "Campaña activa",
        value=plantilla_actual.get("activa", False),
        help="Activa o desactiva el envío automático para este segmento"
    )

    asunto = st.text_input(
        "Asunto del correo",
        value=plantilla_actual.get("asunto", ""),
        placeholder="Ej: Tu carrito te espera 👟",
    )

    mensaje = st.text_area(
        "Cuerpo del mensaje",
        value=plantilla_actual.get("mensaje", ""),
        height=300,
        placeholder="Escribe el mensaje aquí...\n\nPuedes usar:\n{{nombre}} → nombre del cliente\n{{monto}} → monto del carrito\n{{brecha_flete}} → cuánto falta para flete gratis",
    )

    st.caption("Variables disponibles: `{{nombre}}` `{{monto}}` `{{brecha_flete}}` `{{segmento}}`")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Guardar plantilla", type="primary", use_container_width=True):
            plantillas[segmento_sel] = {
                "activa":       activa,
                "asunto":       asunto,
                "mensaje":      mensaje,
                "ultimo_envio": plantilla_actual.get("ultimo_envio"),
            }
            ok_sync, detalle_sync = guardar_plantillas(plantillas)
            st.success("✅ Plantilla guardada correctamente.")
            (st.success if ok_sync else st.warning)(detalle_sync)

    with col_btn2:
        if st.button("↩️ Restaurar original", use_container_width=True):
            st.rerun()

with col_preview:
    st.subheader("👁️ Vista previa")

    # Simular variables con datos reales del segmento
    df_seg = df[df["segmento"] == segmento_sel]
    if not df_seg.empty:
        ejemplo = df_seg.iloc[0]
        brecha  = max(0, PARAMS["ticket_umbral_flete_gratis"] - ejemplo.get("monto_carrito", 0))

        mensaje_preview = mensaje.replace("{{nombre}}", "Cliente")
        mensaje_preview = mensaje_preview.replace("{{monto}}", f"${ejemplo.get('monto_carrito', 0):,.0f}")
        mensaje_preview = mensaje_preview.replace("{{brecha_flete}}", f"${brecha:,.0f}")
        mensaje_preview = mensaje_preview.replace("{{segmento}}", segmento_sel)
    else:
        mensaje_preview = mensaje

    st.markdown(f"**Para:** cliente@ejemplo.cl")
    st.markdown(f"**Asunto:** {asunto if asunto else '_(sin asunto)_'}")
    divisor(margen_top=10, margen_bottom=10)
    st.markdown(mensaje_preview if mensaje_preview else "_(mensaje vacío)_")

divisor()

# ==============================================
# RESUMEN DE TODAS LAS CAMPAÑAS
# ==============================================
st.subheader("Estado de todas las campañas")

filas = []
for seg, config in plantillas.items():
    info_seg = stats_dict.get(seg, {})
    filas.append({
        "Segmento":     seg,
        "Estado":       "✅ Activa" if config.get("activa") else "⏸️ Inactiva",
        "Clientes":     info_seg.get("clientes", 0),
        "% Newsletter": info_seg.get("pct_newsletter", 0),
        "% Email":      info_seg.get("pct_email", 0),
        "Último envío": config.get("ultimo_envio") or "Nunca",
        "Asunto":       config.get("asunto", "")[:50] + "..." if len(config.get("asunto", "")) > 50 else config.get("asunto", ""),
    })

df_estado = pd.DataFrame(filas).sort_values("Clientes", ascending=False)
st.dataframe(df_estado, use_container_width=True, hide_index=True)
