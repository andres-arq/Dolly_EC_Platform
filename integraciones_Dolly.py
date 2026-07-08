# =============================================================================
# integraciones_Dolly.py — Conectores VTEX y MailUp
#
# Hoy: solo dejan la estructura de autenticación lista y un botón de
# "probar conexión" en la UI. Mañana, al pegar las keys en Secrets, deberían
# funcionar sin tocar código — salvo las funciones marcadas TODO, que dependen
# del endpoint exacto que confirme cada equipo (VTEX / MailUp).
# =============================================================================

import requests
from secretos_Dolly import obtener_secreto

TIMEOUT = 10


# =============================================================================
# VTEX
# =============================================================================

def credenciales_vtex():
    return {
        "account":     obtener_secreto("VTEX_ACCOUNT_NAME"),
        "app_key":     obtener_secreto("VTEX_API_KEY"),
        "app_token":   obtener_secreto("VTEX_API_TOKEN"),
        "environment": obtener_secreto("VTEX_ENVIRONMENT", "vtexcommercestable"),
    }


def vtex_configurado():
    c = credenciales_vtex()
    return all([c["account"], c["app_key"], c["app_token"]])


def probar_conexion_vtex():
    """
    Prueba mínima de autenticación contra VTEX (endpoint público de catálogo,
    no depende de permisos especiales). Devuelve (ok: bool, detalle: str).
    """
    c = credenciales_vtex()
    if not vtex_configurado():
        return False, "Faltan credenciales de VTEX en Secrets (cuenta, AppKey o AppToken)."

    url = f"https://{c['account']}.{c['environment']}.com.br/api/catalog_system/pvt/category/1"
    headers = {
        "X-VTEX-API-AppKey":   c["app_key"],
        "X-VTEX-API-AppToken": c["app_token"],
        "Accept": "application/json",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        if resp.status_code == 200:
            return True, "Conexión con VTEX exitosa."
        if resp.status_code in (401, 403):
            return False, "VTEX rechazó las credenciales (401/403) — revisa AppKey/AppToken y permisos."
        return False, f"VTEX respondió {resp.status_code}: {resp.text[:200]}"
    except requests.exceptions.RequestException as e:
        return False, f"Error de conexión con VTEX: {e}"


def descargar_carritos_vtex():
    """
    TODO (mañana, con las keys reales):
    Reemplazar por el endpoint real que uso el equipo de Dolly para generar
    Dolly_Carritos_VTEX.csv — probablemente la Orders API o un feed de
    checkout abandonado. Mientras no se confirme el endpoint exacto, el
    flujo sigue funcionando con la carga manual de CSV en 06_actualizar_data.
    """
    raise NotImplementedError(
        "Endpoint VTEX para carritos aún no confirmado. Usar carga manual de "
        "CSV en 'Actualizar Data' mientras tanto."
    )


# =============================================================================
# MAILUP
# =============================================================================

def credenciales_mailup():
    return {
        "client_id":     obtener_secreto("MAILUP_CLIENT_ID"),
        "client_secret": obtener_secreto("MAILUP_CLIENT_SECRET"),
        "username":      obtener_secreto("MAILUP_USERNAME"),
        "password":      obtener_secreto("MAILUP_PASSWORD"),
    }


def mailup_configurado():
    c = credenciales_mailup()
    return all([c["client_id"], c["client_secret"], c["username"], c["password"]])


def _obtener_token_mailup():
    """
    MailUp usa OAuth2. Este flujo asume grant_type=password (login con
    usuario/clave de consola + client_id/secret de la app registrada) — es
    el más común para integraciones server-to-server, pero CONFIRMAR mañana
    con la documentación que entreguen junto a las keys, por si corresponde
    'authorization_code' en su lugar.
    """
    c = credenciales_mailup()
    url = "https://services.mailup.com/Authorization/OAuth/Token"
    payload = {
        "grant_type":    "password",
        "client_id":     c["client_id"],
        "client_secret": c["client_secret"],
        "username":      c["username"],
        "password":      c["password"],
    }
    resp = requests.post(url, data=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()["access_token"]


def probar_conexion_mailup():
    """Prueba de autenticación OAuth2 contra MailUp. Devuelve (ok, detalle)."""
    if not mailup_configurado():
        return False, "Faltan credenciales de MailUp en Secrets (Client ID/Secret o usuario/clave)."
    try:
        _obtener_token_mailup()
        return True, "Conexión con MailUp exitosa (token OAuth2 obtenido)."
    except requests.exceptions.HTTPError as e:
        return False, f"MailUp rechazó las credenciales: {e}"
    except requests.exceptions.RequestException as e:
        return False, f"Error de conexión con MailUp: {e}"


def enviar_campana_mailup(destinatarios, asunto, mensaje_html):
    """
    TODO (mañana, con las keys reales):
    Confirmar si se usa el endpoint de envío por lista (importar destinatarios
    + disparar mensaje) o el de envío transaccional directo. La firma de esta
    función puede cambiar según eso — se deja aquí como punto único de
    integración para que 04_campanas.py solo necesite llamar a esta función.
    """
    raise NotImplementedError(
        "Flujo de envío MailUp aún no confirmado. Definir mañana si es "
        "envío por lista o transaccional antes de implementar."
    )
