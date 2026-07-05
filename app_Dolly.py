# =============================================================================
# app.py
# Proyecto: Dolly Chile — App de Gestión
# =============================================================================

import streamlit as st

st.set_page_config(
    page_title="Dolly — Panel de Gestión",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Dolly_logo.svg/200px-Dolly_logo.svg.png", use_column_width=True)
st.sidebar.title("Dolly Chile")
st.sidebar.caption("Panel de Gestión E-commerce")

st.sidebar.markdown("---")
st.sidebar.markdown("### Navegación")
st.sidebar.page_link("pages/01_dashboard.py",       label="📊 Dashboard",           icon="📊")
st.sidebar.page_link("pages/02_segmentacion.py",    label="👥 Segmentación",         icon="👥")
st.sidebar.page_link("pages/03_perfil_cliente.py",  label="👤 Perfil de Cliente",    icon="👤")
st.sidebar.page_link("pages/04_campanas.py",        label="📧 Campañas",             icon="📧")
st.sidebar.page_link("pages/05_blue_express.py",    label="📍 Blue Express",         icon="📍")
st.sidebar.page_link("pages/06_actualizar_data.py", label="⬆️  Actualizar Data",     icon="⬆️")

st.sidebar.markdown("---")
st.sidebar.caption("Versión MVP — Capstone 2026")

# Página de inicio
st.title("👟 Dolly Chile — Panel de Gestión")
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("### 📊 Dashboard\nVisualiza KPIs y estadísticas generales de la base de clientes.")

with col2:
    st.info("### 👥 Segmentación\nExplora y filtra los segmentos de clientes con sus métricas.")

with col3:
    st.info("### 👤 Perfil de Cliente\nBusca y revisa el perfil enriquecido de cada cliente.")

col4, col5, col6 = st.columns(3)

with col4:
    st.info("### 📧 Campañas\nEdita las plantillas de correo por segmento.")

with col5:
    st.info("### 📍 Blue Express\nGestiona los puntos de retiro disponibles.")

with col6:
    st.info("### ⬆️ Actualizar Data\nSube un nuevo CSV de VTEX para actualizar todo.")