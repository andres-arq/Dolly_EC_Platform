# =============================================================================
# 06_actualizar_data.py — Carga y actualización de datos
# =============================================================================

import streamlit as st
import pandas as pd
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline_Dolly import (
    cargar_csv_vtex,
    segmentar_clientes,
    PARAMS,
    RUTA_BASE,
)
from estilo_Dolly import (
    aplicar_estilo, sidebar_dolly, encabezado_pagina, kpi_card, divisor,
    NEGRO, ROJO, VINO, GRIS,
)

st.set_page_config(page_title="Actualizar Data — Dolly", page_icon="⬆️", layout="wide")
aplicar_estilo()
sidebar_dolly()

encabezado_pagina(
    modulo="Módulo 06 · Actualizar data",
    titulo="Actualizar data",
    subtitulo="Sube un nuevo CSV de VTEX para actualizar la segmentación y todos los archivos.",
)

# ==============================================
# ESTADO ACTUAL
# ==============================================
st.subheader("Estado actual de los archivos")

archivos = {
    "clientes_con_perfil.csv":     "Segmentación de clientes",
    "dolly_powerbi.csv":           "Datos para Power BI",
    "dolly_buyer_enrichment.csv":  "Enriquecimiento de clientes",
    "blue_express_puntos.csv":     "Puntos Blue Express",
    "plantillas_campanas.json":    "Plantillas de campañas",
    "Dolly_Carritos_VTEX.csv":     "CSV fuente VTEX",
}

filas_estado = []
for archivo, descripcion in archivos.items():
    ruta     = os.path.join(RUTA_BASE, archivo)
    existe   = os.path.exists(ruta)
    fecha    = pd.Timestamp(os.path.getmtime(ruta), unit="s").strftime("%Y-%m-%d %H:%M") if existe else "—"
    tamaño   = f"{os.path.getsize(ruta) / 1024:.0f} KB" if existe else "—"
    filas_estado.append({
        "Archivo":     archivo,
        "Descripción": descripcion,
        "Estado":      "✅ Disponible" if existe else "❌ No encontrado",
        "Última mod.": fecha,
        "Tamaño":      tamaño,
    })

st.dataframe(pd.DataFrame(filas_estado), use_container_width=True, hide_index=True)

divisor()

# ==============================================
# UPLOAD CSV
# ==============================================
st.subheader("📂 Cargar nuevo CSV de VTEX")
st.info("""
**Requisitos del archivo:**
- Formato: CSV separado por punto y coma (`;`)
- Encoding: UTF-8
- Debe mantener el mismo esquema de columnas que `Dolly_Carritos_VTEX.csv`
""")

archivo_subido = st.file_uploader(
    "Arrastra o selecciona el archivo CSV",
    type=["csv"],
    help="El archivo debe tener el mismo formato que Dolly_Carritos_VTEX.csv"
)

if archivo_subido:
    st.success(f"✅ Archivo recibido: **{archivo_subido.name}** ({archivo_subido.size / 1024:.0f} KB)")

    # Vista previa
    try:
        df_preview = pd.read_csv(archivo_subido, sep=";", encoding="utf-8-sig", nrows=5, low_memory=False)
        st.subheader("Vista previa (primeras 5 filas)")
        st.dataframe(df_preview, use_container_width=True, hide_index=True)

        # Verificar columnas mínimas requeridas
        COLUMNAS_REQUERIDAS = [
            "userId", "rclastcartvalue", "rclastsessiondate",
            "checkouttag", "homePhone", "isNewsletterOptIn",
        ]
        columnas_faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df_preview.columns]

        if columnas_faltantes:
            st.error(f"❌ Faltan columnas requeridas: {columnas_faltantes}")
            st.stop()
        else:
            st.success("✅ Estructura del archivo validada correctamente.")

        divisor()

        # Botón para procesar
        if st.button("🚀 Procesar y actualizar todo", type="primary", use_container_width=True):
            with st.spinner("Procesando datos..."):
                from github_sync import subir_archivo_a_github, github_configurado

                sync_disponible = github_configurado()
                if not sync_disponible:
                    st.warning(
                        "⚠️ GitHub no está configurado en Secrets (GITHUB_TOKEN / GITHUB_REPO) — "
                        "los archivos se guardarán solo localmente y se perderán si la app se reinicia."
                    )

                # 1. Guardar CSV nuevo
                archivo_subido.seek(0)
                df_raw = pd.read_csv(archivo_subido, sep=";", encoding="utf-8-sig", low_memory=False)
                ruta_csv = os.path.join(RUTA_BASE, "Dolly_Carritos_VTEX.csv")
                df_raw.to_csv(ruta_csv, sep=";", index=False, encoding="utf-8-sig")
                st.write("✅ CSV guardado")
                if sync_disponible:
                    ok, detalle = subir_archivo_a_github(ruta_csv, "Dolly_Carritos_VTEX.csv")
                    st.write(f"{'✅' if ok else '⚠️'} {detalle}")

                # 2. Segmentar clientes
                df_raw_procesado = cargar_csv_vtex(ruta_csv)
                df_segmentado    = segmentar_clientes(df_raw_procesado)
                st.write(f"✅ Segmentación completada: {len(df_segmentado):,} clientes")

                # 3. Exportar clientes_con_perfil.csv
                COLUMNAS_PERFIL = [
                    "userId", "segmento", "recencia_dias",
                    "monto_carrito", "ticket_prom", "ticket_max",
                    "frecuencia", "paso_abandono", "brecha_flete",
                    "sobre_umbral", "tiene_telefono", "homePhone", "tiene_newsletter",
                    "email", "tiene_email",
                    "es_comprador", "tiene_carrito_abandonado_historico",
                    "producto_id", "categoria_producto", "marca_producto", "departamento_producto",
                    "ultima_sesion", "primera_sesion",
                ]
                cols_existentes = [c for c in COLUMNAS_PERFIL if c in df_segmentado.columns]
                ruta_perfil = os.path.join(RUTA_BASE, "clientes_con_perfil.csv")
                df_segmentado[cols_existentes].to_csv(ruta_perfil, index=False, encoding="utf-8-sig")
                st.write("✅ clientes_con_perfil.csv actualizado")
                if sync_disponible:
                    ok, detalle = subir_archivo_a_github(ruta_perfil, "clientes_con_perfil.csv")
                    st.write(f"{'✅' if ok else '⚠️'} {detalle}")

                # 4. Exportar dolly_powerbi.csv
                COLUMNAS_POWERBI = [
                    "userId", "segmento", "paso_abandono",
                    "recencia_dias", "monto_carrito", "ticket_prom",
                    "frecuencia", "sobre_umbral", "brecha_flete",
                    "tiene_telefono", "tiene_newsletter", "tiene_email",
                    "es_comprador", "tiene_carrito_abandonado_historico",
                    "producto_id", "categoria_producto", "marca_producto", "departamento_producto",
                ]
                cols_pbi = [c for c in COLUMNAS_POWERBI if c in df_segmentado.columns]
                df_pbi   = df_segmentado[cols_pbi].copy()

                for col in ["ultima_sesion", "primera_sesion"]:
                    if col in df_pbi.columns:
                        df_pbi[col] = pd.to_datetime(df_pbi[col], errors="coerce").dt.tz_localize(None)

                for col in ["sobre_umbral", "tiene_telefono", "tiene_newsletter", "tiene_email",
                            "es_comprador", "tiene_carrito_abandonado_historico"]:
                    if col in df_pbi.columns:
                        df_pbi[col] = df_pbi[col].astype(int)

                ruta_pbi = os.path.join(RUTA_BASE, "dolly_powerbi.csv")
                df_pbi.to_csv(ruta_pbi, index=False, encoding="utf-8-sig")
                st.write("✅ dolly_powerbi.csv actualizado")
                if sync_disponible:
                    ok, detalle = subir_archivo_a_github(ruta_pbi, "dolly_powerbi.csv")
                    st.write(f"{'✅' if ok else '⚠️'} {detalle}")

            divisor()
            st.success("🎉 ¡Todo actualizado correctamente!")

            # Resumen
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                kpi_card("Total clientes procesados", f"{len(df_segmentado):,}")
            with col2:
                kpi_card("Segmentos generados", df_segmentado["segmento"].nunique(), color=GRIS)
            with col3:
                kpi_card("Monto medio", f"${df_segmentado['monto_carrito'].mean():,.0f}", color=ROJO)
            with col4:
                kpi_card("Monto mediano", f"${df_segmentado['monto_carrito'].median():,.0f}", color=ROJO)

            st.subheader("Distribución de segmentos generada")
            conteo = df_segmentado["segmento"].value_counts().reset_index()
            conteo.columns = ["Segmento", "Clientes"]
            conteo["% Base"] = (conteo["Clientes"] / len(df_segmentado) * 100).round(1)
            st.dataframe(conteo, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"❌ Error procesando el archivo: {e}")

divisor()

# ==============================================
# DESCARGA DE ARCHIVOS GENERADOS
# ==============================================
st.subheader("⬇️ Descargar archivos generados")
st.caption("Descarga los CSV generados por el pipeline para uso externo.")

col1, col2, col3 = st.columns(3)

archivos_descarga = [
    ("clientes_con_perfil.csv",    "👥 Clientes segmentados",  col1),
    ("dolly_powerbi.csv",          "📊 Datos Power BI",         col2),
    ("dolly_buyer_enrichment.csv", "🧩 Buyer Enrichment",       col3),
]

for archivo, label, col in archivos_descarga:
    ruta = os.path.join(RUTA_BASE, archivo)
    with col:
        if os.path.exists(ruta):
            with open(ruta, "rb") as f:
                st.download_button(
                    label=label,
                    data=f,
                    file_name=archivo,
                    mime="text/csv",
                    use_container_width=True,
                )
        else:
            st.button(label, disabled=True, use_container_width=True,
                      help="Archivo no disponible aún")

divisor()

# ==============================================
# ESTADO DE INTEGRACIONES
# ==============================================
st.subheader("🔌 Estado de integraciones")
st.caption(
    "Las credenciales se configuran en Streamlit Cloud → tu app → Settings (⋮) → "
    "Secrets, nunca en el código. Al pegarlas ahí, esta página debería mostrarlas "
    "como configuradas sin necesidad de tocar nada más."
)

from secretos_Dolly import resumen_configuracion
from integraciones_Dolly import (
    vtex_configurado, probar_conexion_vtex,
    mailup_configurado, probar_conexion_mailup,
)
from github_sync import github_configurado

col_vtex, col_mailup, col_github = st.columns(3)

with col_vtex:
    st.markdown("**VTEX**")
    if vtex_configurado():
        st.success("✅ Credenciales configuradas")
        if st.button("Probar conexión VTEX", use_container_width=True):
            ok, detalle = probar_conexion_vtex()
            (st.success if ok else st.error)(detalle)
    else:
        st.warning("⏳ Pendiente — faltan VTEX_ACCOUNT_NAME / VTEX_API_KEY / VTEX_API_TOKEN")

with col_mailup:
    st.markdown("**MailUp**")
    if mailup_configurado():
        st.success("✅ Credenciales configuradas")
        if st.button("Probar conexión MailUp", use_container_width=True):
            ok, detalle = probar_conexion_mailup()
            (st.success if ok else st.error)(detalle)
    else:
        st.warning("⏳ Pendiente — faltan MAILUP_CLIENT_ID / MAILUP_CLIENT_SECRET / usuario / password")

with col_github:
    st.markdown("**GitHub (persistencia)**")
    if github_configurado():
        st.success("✅ Configurado — los datos se respaldan solos")
    else:
        st.warning("⏳ Pendiente — faltan GITHUB_TOKEN / GITHUB_REPO")

with st.expander("Ver detalle de todas las claves de Secrets"):
    for etiqueta, configurada in resumen_configuracion().items():
        st.markdown(f"{'✅' if configurada else '⬜'} {etiqueta}")
