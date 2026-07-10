# =============================================================================
# 04_campanas.py — Gestión de plantillas de correo por segmento (test A/B)
# =============================================================================

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import sys
import os
import zipfile
import io

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline_Dolly import (
    cargar_perfil_clientes,
    cargar_plantillas,
    guardar_plantillas,
    ORDEN_PRIORIDAD_SEGMENTOS,
    PARAMS,
)
from estilo_Dolly import (
    aplicar_estilo, sidebar_dolly, encabezado_pagina, kpi_card, divisor,
    NEGRO, ROJO, VINO, GRIS,
)
from email_html_Dolly import generar_html_email, nombre_archivo_html

st.set_page_config(page_title="Campañas — Dolly", page_icon="📧", layout="wide")
aplicar_estilo()
sidebar_dolly()

encabezado_pagina(
    modulo="Módulo 04 · Campañas",
    titulo="Gestión de campañas",
    subtitulo="Edita las variantes A/B de cada segmento, genera el HTML del correo y actívalas o desactívalas.",
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
# EDITOR DE PLANTILLA — VARIANTES A/B
# ==============================================
plantilla_actual = plantillas.get(segmento_sel, {})
variantes_actuales = plantilla_actual.get("variantes", {"A": {}, "B": {}})

st.subheader("✏️ Editor — Test A/B")

col_activa, col_hipotesis = st.columns([1, 3])
with col_activa:
    activa = st.toggle(
        "Campaña activa",
        value=plantilla_actual.get("activa", False),
        help="Activa o desactiva el envío para este segmento",
        key=f"activa_{segmento_sel}",
    )
with col_hipotesis:
    hipotesis_ab = st.text_input(
        "Hipótesis a testear (A vs. B)",
        value=plantilla_actual.get("hipotesis_ab", ""),
        placeholder="Ej: Urgencia/escasez (A) vs. Soporte de pago (B)",
        key=f"hipotesis_{segmento_sel}",
    )

# Datos de ejemplo del segmento, para la vista previa con variables reemplazadas
df_seg = df[df["segmento"] == segmento_sel]
if not df_seg.empty:
    ejemplo = df_seg.iloc[0]
    brecha_ejemplo = max(0, PARAMS["ticket_umbral_flete_gratis"] - ejemplo.get("monto_carrito", 0))
    monto_ejemplo = ejemplo.get("monto_carrito", 0)
else:
    brecha_ejemplo = 0
    monto_ejemplo = 0

prioridad_segmento = ORDEN_PRIORIDAD_SEGMENTOS.get(segmento_sel, 0)

tab_a, tab_b = st.tabs(["Variante A", "Variante B"])
nuevas_variantes = {}

for letra, tab in zip(["A", "B"], [tab_a, tab_b]):
    with tab:
        datos_variante = variantes_actuales.get(letra, {})
        col_editor, col_preview = st.columns([1, 1], gap="large")

        with col_editor:
            nombre_variante = st.text_input(
                "Nombre de la variante (para identificar la hipótesis)",
                value=datos_variante.get("nombre_variante", f"Variante {letra}"),
                key=f"nombre_{segmento_sel}_{letra}",
            )
            asunto = st.text_input(
                "Asunto del correo",
                value=datos_variante.get("asunto", ""),
                placeholder="Ej: Tu carrito se libera en 2 horas",
                key=f"asunto_{segmento_sel}_{letra}",
            )
            mensaje = st.text_area(
                "Cuerpo del mensaje",
                value=datos_variante.get("mensaje", ""),
                height=220,
                placeholder="Hola,\n\nTus productos siguen en tu carrito...",
                key=f"mensaje_{segmento_sel}_{letra}",
            )
            cta = st.text_input(
                "Frase de cierre (opcional — ya NO es un botón ni link en el correo real)",
                value=datos_variante.get("cta", ""),
                placeholder="Ej: Finalizar mi compra ahora",
                help="Antes se usaba como texto de un botón. El HTML final del correo ya no incluye "
                     "botones ni links (por riesgo de verse como phishing), así que este texto solo "
                     "se guarda como referencia de la hipótesis — no aparece en el correo enviado.",
                key=f"cta_{segmento_sel}_{letra}",
            )

        nuevas_variantes[letra] = {
            "nombre_variante": nombre_variante,
            "asunto": asunto,
            "mensaje": mensaje,
            "cta": cta,
        }

        with col_preview:
            st.markdown("**Vista previa (texto)**")
            mensaje_preview = (mensaje or "").replace("{{nombre}}", "Cliente")
            mensaje_preview = mensaje_preview.replace("{{monto}}", f"${monto_ejemplo:,.0f}")
            mensaje_preview = mensaje_preview.replace("{{brecha_flete}}", f"${brecha_ejemplo:,.0f}")
            mensaje_preview = mensaje_preview.replace("{{segmento}}", segmento_sel)

            st.markdown(f"**Para:** `cliente@ejemplo.cl`")
            st.markdown(f"**Asunto:** {asunto if asunto else '_(sin asunto)_'}")
            divisor(margen_top=8, margen_bottom=8)
            st.markdown(mensaje_preview if mensaje_preview else "_(mensaje vacío)_")
            st.markdown(f"**Te esperamos en dolly.cl**")
            if cta:
                st.caption(f"📝 Frase de cierre guardada (no aparece en el correo): \"{cta}\"")

            html_generado = generar_html_email(asunto, mensaje, cta)
            archivo_html = nombre_archivo_html(prioridad_segmento, segmento_sel, letra)

            with st.expander("🌐 Ver HTML del correo (como se vería en el cliente de correo)"):
                components.html(html_generado, height=480, scrolling=True)

            st.download_button(
                f"⬇️ Descargar HTML — Variante {letra}",
                data=html_generado,
                file_name=archivo_html,
                mime="text/html",
                use_container_width=True,
                key=f"descargar_{segmento_sel}_{letra}",
            )

st.caption(
    "Las plantillas son genéricas — no usan variables de personalización "
    "(no tenemos el nombre real de cada cliente todavía). Si más adelante se "
    "cuenta con ese dato, se pueden reintroducir variables como `{{nombre}}`."
)

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("💾 Guardar plantilla", type="primary", use_container_width=True):
        plantillas[segmento_sel] = {
            "activa":       activa,
            "hipotesis_ab": hipotesis_ab,
            "variantes":    nuevas_variantes,
            "ultimo_envio": plantilla_actual.get("ultimo_envio"),
        }
        ok_sync, detalle_sync = guardar_plantillas(plantillas)
        st.success("✅ Plantilla guardada correctamente.")
        (st.success if ok_sync else st.warning)(detalle_sync)

with col_btn2:
    if st.button("↩️ Restaurar original", use_container_width=True):
        st.rerun()

divisor()

# ==============================================
# RESUMEN DE TODAS LAS CAMPAÑAS
# ==============================================
st.subheader("Estado de todas las campañas")

filas = []
for seg, config in plantillas.items():
    info_seg = stats_dict.get(seg, {})
    variantes_seg = config.get("variantes", {})
    asunto_a = variantes_seg.get("A", {}).get("asunto", "")
    asunto_b = variantes_seg.get("B", {}).get("asunto", "")
    filas.append({
        "Segmento":       seg,
        "Estado":         "✅ Activa" if config.get("activa") else "⏸️ Inactiva",
        "Clientes":       info_seg.get("clientes", 0),
        "% Newsletter":   info_seg.get("pct_newsletter", 0),
        "% Email":        info_seg.get("pct_email", 0),
        "Hipótesis A/B":  config.get("hipotesis_ab", ""),
        "Asunto A":       (asunto_a[:40] + "...") if len(asunto_a) > 40 else asunto_a,
        "Asunto B":       (asunto_b[:40] + "...") if len(asunto_b) > 40 else asunto_b,
        "Último envío":   config.get("ultimo_envio") or "Nunca",
    })

df_estado = pd.DataFrame(filas).sort_values("Clientes", ascending=False)
st.dataframe(df_estado, use_container_width=True, hide_index=True)

divisor()

# ==============================================
# DESCARGA MASIVA DE TODOS LOS HTML
# ==============================================
st.subheader("📦 Descargar todos los HTML")
st.caption(
    "Genera un .zip con las 28 plantillas (14 segmentos × Variante A/B), con el mismo "
    "contenido que está guardado ahora mismo — no depende de qué segmento tengas "
    "seleccionado arriba."
)

buffer_zip = io.BytesIO()
with zipfile.ZipFile(buffer_zip, "w", zipfile.ZIP_DEFLATED) as zf:
    for seg, config in plantillas.items():
        prioridad = ORDEN_PRIORIDAD_SEGMENTOS.get(seg, 0)
        variantes_zip = config.get("variantes", {})
        for letra in ["A", "B"]:
            v = variantes_zip.get(letra, {})
            html_generado = generar_html_email(v.get("asunto", ""), v.get("mensaje", ""), v.get("cta", ""))
            archivo_html = nombre_archivo_html(prioridad, seg, letra)
            zf.writestr(archivo_html, html_generado)
buffer_zip.seek(0)

st.download_button(
    "⬇️ Descargar dolly_campanas_html.zip (28 archivos)",
    data=buffer_zip,
    file_name="dolly_campanas_html.zip",
    mime="application/zip",
    use_container_width=True,
)
