# =============================================================================
# secretos_Dolly.py — Lectura centralizada de credenciales (Streamlit Secrets)
#
# Nada de esto guarda claves en el código ni en GitHub. Las keys se pegan en:
#   Streamlit Cloud → tu app → Settings (⋮) → Secrets
# usando exactamente los mismos nombres que se listan en secrets_ejemplo.toml.
#
# En local, para probar, se puede crear un archivo .streamlit/secrets.toml
# con la misma estructura — pero ese archivo NUNCA debe subirse a GitHub
# (confirma que está en .gitignore).
# =============================================================================

import os

try:
    import streamlit as st
    _TIENE_STREAMLIT = True
except ImportError:
    _TIENE_STREAMLIT = False


def obtener_secreto(clave, default=None):
    """
    Busca `clave` primero en st.secrets (Streamlit Cloud / secrets.toml local)
    y, si no existe, en las variables de entorno. Nunca lanza error si falta
    la clave — devuelve `default` para que la app pueda seguir funcionando
    (mostrando "no configurado" en vez de romperse).
    """
    if _TIENE_STREAMLIT:
        try:
            if clave in st.secrets:
                return st.secrets[clave]
        except Exception:
            pass
    return os.environ.get(clave, default)


def resumen_configuracion():
    """
    Devuelve qué credenciales están configuradas y cuáles faltan, sin
    exponer los valores — solo para mostrar el estado en la UI.
    """
    claves = {
        "VTEX_ACCOUNT_NAME":   "VTEX · nombre de cuenta",
        "VTEX_API_KEY":        "VTEX · AppKey",
        "VTEX_API_TOKEN":      "VTEX · AppToken",
        "MAILUP_CLIENT_ID":    "MailUp · Client ID",
        "MAILUP_CLIENT_SECRET":"MailUp · Client Secret",
        "MAILUP_USERNAME":     "MailUp · Usuario consola",
        "MAILUP_PASSWORD":     "MailUp · Password consola",
        "GITHUB_TOKEN":        "GitHub · Token de acceso",
        "GITHUB_REPO":         "GitHub · Repositorio (usuario/repo)",
    }
    return {
        etiqueta: bool(obtener_secreto(clave))
        for clave, etiqueta in claves.items()
    }
