# =============================================================================
# estilo_Dolly.py — Sistema visual compartido (paleta Dolly: blanco/negro/gris/rojo)
# Importar en cada página y llamar aplicar_estilo() justo después de set_page_config.
# =============================================================================

import streamlit as st

# =============================================================================
# PALETA — extraída de la presentación de referencia (Hito 3)
# =============================================================================

NEGRO             = "#1A1A1A"   # títulos, barras "activo/con carrito", texto fuerte
ROJO              = "#D6362E"   # acento de marca, urgencia, eyebrows
VINO              = "#7A1F2B"   # alto valor / riesgo (distinto del rojo de urgencia)
GRIS              = "#9B9890"   # segmentos neutros / baja prioridad (Perdido, Inactivo)
GRIS_CLARO        = "#D9D6CF"   # barras secundarias, líneas divisoras suaves
FONDO             = "#FAF8F4"   # fondo de página (crema)
CARD              = "#F5F2EC"   # fondo de tarjetas
BORDE             = "#E7E3DA"   # borde de tarjetas
TEXTO_PRIMARIO    = "#1A1A1A"
TEXTO_SECUNDARIO  = "#6E6B64"

# Escalas para gráficos Plotly
ESCALA_NEUTRA = [[0, GRIS_CLARO], [0.5, GRIS], [1, NEGRO]]      # volumen / conteo
ESCALA_ROJA   = [[0, "#F3D6D3"], [0.5, ROJO], [1, VINO]]        # potencial / riesgo
SECUENCIA_CATEGORICA = [NEGRO, ROJO, VINO, GRIS, GRIS_CLARO]    # pie / categorías


def aplicar_estilo():
    """Inyecta el CSS global con la paleta Dolly. Llamar una vez por página."""
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: {FONDO};
        }}
        section[data-testid="stSidebar"] {{
            background-color: {NEGRO};
        }}
        section[data-testid="stSidebar"] * {{
            color: #F5F2EC !important;
        }}
        section[data-testid="stSidebar"] a[aria-current="page"] {{
            background-color: {ROJO} !important;
            border-radius: 6px;
        }}
        h1, h2, h3 {{
            color: {TEXTO_PRIMARIO} !important;
            font-weight: 700 !important;
        }}
        p, span, label, .stMarkdown {{
            color: {TEXTO_PRIMARIO};
        }}
        [data-testid="stMetric"] {{
            background-color: {CARD};
            border: 0.5px solid {BORDE};
            border-radius: 10px;
            padding: 14px 16px;
        }}
        [data-testid="stMetricLabel"] {{
            color: {TEXTO_SECUNDARIO} !important;
        }}
        [data-testid="stMetricValue"] {{
            color: {TEXTO_PRIMARIO} !important;
        }}
        div[data-testid="stDataFrame"] {{
            border: 0.5px solid {BORDE};
            border-radius: 10px;
        }}
        hr {{
            border-color: {BORDE} !important;
        }}
        .stButton > button[kind="primary"] {{
            background-color: {NEGRO};
            border: none;
        }}
        .stButton > button[kind="primary"]:hover {{
            background-color: {ROJO};
        }}
    </style>
    """, unsafe_allow_html=True)


def eyebrow(texto):
    """Etiqueta pequeña en rojo, mayúscula, con tracking — encabeza cada sección."""
    st.markdown(
        f"<div style='font-size:12px; letter-spacing:0.08em; color:{ROJO}; "
        f"font-weight:600; text-transform:uppercase; margin-bottom:4px;'>{texto}</div>",
        unsafe_allow_html=True,
    )


def encabezado_pagina(modulo, titulo, subtitulo):
    """Encabezado estándar de página: eyebrow + título + subtítulo + línea."""
    eyebrow(f"Dolly · {modulo}")
    st.markdown(f"<div style='font-size:26px; font-weight:700; color:{TEXTO_PRIMARIO}; "
                f"margin-bottom:4px;'>{titulo}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:14px; color:{TEXTO_SECUNDARIO}; "
                f"margin-bottom:18px;'>{subtitulo}</div>", unsafe_allow_html=True)
    st.markdown(f"<hr style='margin:0 0 20px 0; border:none; border-top:0.5px solid {BORDE};'>",
                unsafe_allow_html=True)


def kpi_card(label, value, color=None, ayuda=None):
    """Tarjeta KPI custom (reemplaza st.metric) con la estética de la referencia."""
    color = color or TEXTO_PRIMARIO
    ayuda_html = f"<div style='font-size:11px; color:{TEXTO_SECUNDARIO}; margin-top:4px;'>{ayuda}</div>" if ayuda else ""
    st.markdown(f"""
        <div style="background:{CARD}; border:0.5px solid {BORDE}; border-radius:10px;
                    padding:14px 16px; height:100%;">
            <div style="font-size:24px; font-weight:700; color:{color};">{value}</div>
            <div style="font-size:12px; color:{TEXTO_SECUNDARIO}; margin-top:2px;">{label}</div>
            {ayuda_html}
        </div>
    """, unsafe_allow_html=True)


def divisor(margen_top=20, margen_bottom=20):
    st.markdown(
        f"<hr style='margin:{margen_top}px 0 {margen_bottom}px 0; border:none; "
        f"border-top:0.5px solid {BORDE};'>",
        unsafe_allow_html=True,
    )


def feature_card(icono, titulo, descripcion):
    """Tarjeta de acceso a un módulo, usada en la portada (app_Dolly.py)."""
    st.markdown(f"""
        <div style="background:{CARD}; border:0.5px solid {BORDE}; border-left:3px solid {ROJO};
                    border-radius:0 10px 10px 0; padding:16px 18px; height:100%; min-height:110px;">
            <div style="font-size:16px; font-weight:700; color:{TEXTO_PRIMARIO}; margin-bottom:6px;">
                {icono} {titulo}
            </div>
            <div style="font-size:13px; color:{TEXTO_SECUNDARIO};">{descripcion}</div>
        </div>
    """, unsafe_allow_html=True)


def estilizar_grafico(fig):
    """
    Fuerza la paleta Dolly (fondo transparente, texto negro) en un gráfico Plotly.
    IMPORTANTE: usar siempre junto con st.plotly_chart(fig, theme=None) — si no se
    pasa theme=None, Streamlit reemplaza estos colores por su propio tema
    (claro/oscuro automático de Streamlit Cloud) y el texto queda casi invisible.
    """
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color=NEGRO,
        title_font_color=NEGRO,
        legend_font_color=NEGRO,
    )
    try:
        fig.update_xaxes(tickfont_color=NEGRO, title_font_color=NEGRO, gridcolor=BORDE, linecolor=BORDE)
        fig.update_yaxes(tickfont_color=NEGRO, title_font_color=NEGRO, gridcolor=BORDE, linecolor=BORDE)
    except Exception:
        pass  # figuras sin ejes cartesianos (ej. mapas, pie charts)
    return fig
