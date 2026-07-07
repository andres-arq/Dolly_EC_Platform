# =============================================================================
# app.py
# Proyecto: Dolly Chile — App de Gestión
# =============================================================================

import streamlit as st
from estilo_Dolly import aplicar_estilo, feature_card, divisor, NEGRO, ROJO, TEXTO_SECUNDARIO

st.set_page_config(
    page_title="Dolly — Panel de Gestión",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded",
)
aplicar_estilo()

# ==============================================
# SIDEBAR
# ==============================================
st.sidebar.markdown(f"""
    <div style='font-size:22px; font-weight:700; color:#fff; margin-bottom:0px;'>👟 Dolly Chile</div>
    <div style='font-size:13px; color:#B7B4AC; margin-bottom:14px;'>Panel de Gestión E-commerce</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<hr style='border-top:0.5px solid #3A3A3A; margin:10px 0;'>", unsafe_allow_html=True)
st.sidebar.markdown("### Navegación")
st.sidebar.page_link("pages/01_dashboard.py",       label="Dashboard",           icon="📊")
st.sidebar.page_link("pages/02_segmentacion.py",    label="Segmentación",        icon="👥")
st.sidebar.page_link("pages/03_perfil_cliente.py",  label="Perfil de Cliente",   icon="👤")
st.sidebar.page_link("pages/04_campanas.py",        label="Campañas",            icon="📧")
st.sidebar.page_link("pages/05_blue_express.py",    label="Blue Express",        icon="📍")
st.sidebar.page_link("pages/06_actualizar_data.py", label="Actualizar Data",     icon="⬆️")

st.sidebar.markdown("<hr style='border-top:0.5px solid #3A3A3A; margin:10px 0;'>", unsafe_allow_html=True)
st.sidebar.caption("Versión MVP — Capstone 2026")

# ==============================================
# PÁGINA DE INICIO
# ==============================================
st.markdown(f"""
    <div style='font-size:13px; letter-spacing:0.08em; color:{ROJO}; font-weight:600;
                text-transform:uppercase; margin-bottom:6px;'>Dolly Chile</div>
    <div style='font-size:32px; font-weight:700; color:{NEGRO};'>Panel de gestión e-commerce</div>
    <div style='font-size:14px; color:{TEXTO_SECUNDARIO}; margin-top:4px;'>
        Segmentación de clientes, recuperación de carrito y gestión de campañas — VTEX.
    </div>
""", unsafe_allow_html=True)

divisor()

col1, col2, col3 = st.columns(3)

with col1:
    feature_card("📊", "Dashboard", "Visualiza KPIs y estadísticas generales de la base de clientes.")

with col2:
    feature_card("👥", "Segmentación", "Explora y filtra los segmentos de clientes con sus métricas.")

with col3:
    feature_card("👤", "Perfil de Cliente", "Busca y revisa el perfil enriquecido de cada cliente.")

st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)

with col4:
    feature_card("📧", "Campañas", "Edita las plantillas de correo por segmento.")

with col5:
    feature_card("📍", "Blue Express", "Gestiona los puntos de retiro disponibles.")

with col6:
    feature_card("⬆️", "Actualizar Data", "Sube un nuevo CSV de VTEX para actualizar todo.")
