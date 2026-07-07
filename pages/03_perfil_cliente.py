# =============================================================================
# 03_perfil_cliente.py — Perfil individual de cliente
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline_Dolly import cargar_perfil_clientes, cargar_buyer_enrichment, PARAMS
from estilo_Dolly import (
    aplicar_estilo, encabezado_pagina, kpi_card, divisor,
    NEGRO, ROJO, VINO, GRIS,
)

st.set_page_config(page_title="Perfil Cliente — Dolly", page_icon="👤", layout="wide")
aplicar_estilo()

encabezado_pagina(
    modulo="Módulo 03 · Perfil de cliente",
    titulo="Perfil de cliente",
    subtitulo="Busca y revisa el perfil completo de un cliente individual.",
)

# Cargar datos
df_perfil   = cargar_perfil_clientes()
df_enrich   = cargar_buyer_enrichment()

if df_perfil.empty:
    st.warning("⚠️  No hay datos disponibles. Ve a **Actualizar Data** para cargar el CSV de VTEX.")
    st.stop()

# Merge si existe enriquecimiento
if not df_enrich.empty:
    df = df_perfil.merge(df_enrich, on="userId", how="left", suffixes=("", "_enrich"))
else:
    df = df_perfil.copy()

# ==============================================
# BÚSQUEDA
# ==============================================
st.subheader("Buscar cliente")
col1, col2 = st.columns([2, 1])

with col1:
    busqueda = st.text_input("Buscar por userId", placeholder="Ingresa el userId...")

with col2:
    segmento_filtro = st.selectbox(
        "O explorar por segmento",
        ["Todos"] + sorted(df["segmento"].unique().tolist())
    )

# Aplicar búsqueda
if busqueda:
    df_resultado = df[df["userId"].astype(str).str.contains(busqueda, case=False)]
elif segmento_filtro != "Todos":
    df_resultado = df[df["segmento"] == segmento_filtro]
else:
    df_resultado = df.copy()

if df_resultado.empty:
    st.info("No se encontraron clientes con ese criterio.")
    st.stop()

# Selector de cliente individual
divisor(margen_top=10)
usuario_seleccionado = st.selectbox(
    f"Selecciona un cliente ({len(df_resultado):,} encontrados)",
    df_resultado["userId"].tolist()
)

cliente = df_resultado[df_resultado["userId"] == usuario_seleccionado].iloc[0]

divisor()

# ==============================================
# PERFIL DEL CLIENTE
# ==============================================
col_info, col_metricas = st.columns([1, 2])

with col_info:
    st.subheader("Información general")

    # Badge de segmento
    COLORES_SEGMENTO = {
        "Cliente VIP":         "🟢",
        "Cliente Activo":      "🔵",
        "Alto Valor Reciente": "🟡",
        "Alto Valor En Riesgo":"🟠",
        "Alto Valor Perdido":  "🔴",
        "Recuperable Urgente": "🟣",
        "Recuperable Flete":   "🟣",
        "Recuperable Temprano":"🟣",
        "Recuperable Bajo":    "🟣",
        "Con Carrito":         "🔵",
        "Potencial Con Carrito":"⚪",
        "Potencial Sin Carrito":"⚪",
        "Inactivo":            "⚫",
        "Perdido":             "⚫",
    }
    icono = COLORES_SEGMENTO.get(cliente.get("segmento", ""), "⚪")
    st.markdown(f"### {icono} {cliente.get('segmento', 'Sin segmento')}")

    st.markdown(f"**userId:** `{cliente['userId']}`")

    if "genero" in cliente and pd.notna(cliente.get("genero")):
        st.markdown(f"**Género:** {cliente['genero']}")

    if "edad" in cliente and pd.notna(cliente.get("edad")):
        st.markdown(f"**Edad:** {int(cliente['edad'])} años")

    if "generacion" in cliente and pd.notna(cliente.get("generacion")):
        st.markdown(f"**Generación:** {cliente['generacion']}")

    if "mes_cumpleanos" in cliente and pd.notna(cliente.get("mes_cumpleanos")):
        meses = {1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
                 7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"}
        st.markdown(f"**Cumpleaños:** {meses.get(int(cliente['mes_cumpleanos']), '')}")

    divisor(margen_top=12, margen_bottom=12)
    st.markdown("**Canales de contacto:**")

    tiene_tel  = cliente.get("tiene_telefono", False)
    tiene_news = cliente.get("tiene_newsletter", False)

    st.markdown(f"{'✅' if tiene_tel else '❌'} Teléfono")
    st.markdown(f"{'✅' if tiene_news else '❌'} Newsletter")

    if "canal_contacto" in cliente and pd.notna(cliente.get("canal_contacto")):
        st.info(f"📡 {cliente['canal_contacto']}")

with col_metricas:
    st.subheader("Métricas de comportamiento")

    m1, m2, m3 = st.columns(3)
    with m1:
        kpi_card("Monto carrito", f"${cliente.get('monto_carrito', 0):,.0f}")
    with m2:
        kpi_card("Recencia", f"{cliente.get('recencia_dias', 0):.0f} días", color=GRIS)
    with m3:
        kpi_card("Frecuencia", f"{cliente.get('frecuencia', 0):.0f} sesiones")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    m4, m5, m6 = st.columns(3)
    with m4:
        kpi_card("Ticket promedio", f"${cliente.get('ticket_prom', 0):,.0f}")
    with m5:
        umbral = PARAMS["ticket_umbral_flete_gratis"]
        brecha = max(0, umbral - cliente.get("monto_carrito", 0))
        kpi_card(
            "Brecha flete gratis",
            f"${brecha:,.0f}",
            color=VINO if brecha > 0 else NEGRO,
            ayuda="Flete gratis ✅" if brecha == 0 else f"Faltan ${brecha:,.0f}",
        )
    with m6:
        kpi_card("Paso abandono", cliente.get("paso_abandono", "Desconocido"), color=ROJO)

divisor()

# ==============================================
# PREFERENCIAS DE COMPRA
# ==============================================
if any(col in cliente.index for col in ["marca_preferida", "categoria_preferida"]):
    st.subheader("Preferencias de compra")
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        marca = cliente.get("marca_preferida")
        kpi_card("Marca preferida", marca if pd.notna(marca) else "Sin dato")

    with col_b:
        cat = cliente.get("categoria_preferida")
        kpi_card("Categoría preferida", cat if pd.notna(cat) else "Sin dato")

    with col_c:
        es_escolar = cliente.get("es_cliente_escolar", 0)
        kpi_card("Cliente escolar", "Sí ✅" if es_escolar else "No")

    if "sku_sin_stock_visitado" in cliente and pd.notna(cliente.get("sku_sin_stock_visitado")):
        st.warning(f"⚠️  Visitó producto sin stock: SKU `{cliente['sku_sin_stock_visitado']}`")

divisor()

# ==============================================
# CLIENTES SIMILARES
# ==============================================
st.subheader("Clientes similares")
st.caption("Mismo segmento, monto similar (±30%)")

monto     = cliente.get("monto_carrito", 0)
segmento  = cliente.get("segmento", "")
similares = df[
    (df["segmento"] == segmento) &
    (df["userId"] != usuario_seleccionado) &
    (df["monto_carrito"] >= monto * 0.7) &
    (df["monto_carrito"] <= monto * 1.3)
].head(5)

if not similares.empty:
    cols_sim = ["userId", "segmento", "recencia_dias", "monto_carrito", "paso_abandono"]
    cols_sim = [c for c in cols_sim if c in similares.columns]
    st.dataframe(similares[cols_sim], use_container_width=True, hide_index=True)
else:
    st.info("No hay clientes similares con esos criterios.")
