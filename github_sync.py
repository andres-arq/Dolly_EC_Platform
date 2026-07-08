# =============================================================================
# github_sync.py — Persistencia real de datos en Streamlit Cloud
#
# Streamlit Cloud borra el filesystem de la app en cada reinicio/redeploy —
# por eso los CSV que se generan en 06_actualizar_data.py se "pierden". El
# repo de GitHub, en cambio, SÍ persiste. Este módulo sube (crea o actualiza)
# un archivo directo al repo usando la API de contenidos de GitHub, así el
# archivo sobrevive al próximo reinicio (se vuelve a clonar desde el repo).
#
# Requiere en Secrets:
#   GITHUB_TOKEN  → Personal Access Token con permiso "repo" (contents: write)
#   GITHUB_REPO   → "usuario/repositorio", ej: "andres-arq/Dolly_EC_Platform"
#   GITHUB_BRANCH → opcional, default "main"
# =============================================================================

import base64
import os
import requests
from secretos_Dolly import obtener_secreto

TIMEOUT = 15


def github_configurado():
    return bool(obtener_secreto("GITHUB_TOKEN")) and bool(obtener_secreto("GITHUB_REPO"))


def subir_archivo_a_github(ruta_local, ruta_repo=None, mensaje=None):
    """
    Sube `ruta_local` al repo configurado en Secrets, en la ruta `ruta_repo`
    (por defecto, el mismo nombre de archivo en la raíz del repo).

    Devuelve (ok: bool, detalle: str) — nunca lanza excepción hacia afuera,
    para que un fallo de sincronización no rompa el flujo normal de guardado
    local de la app.
    """
    token = obtener_secreto("GITHUB_TOKEN")
    repo  = obtener_secreto("GITHUB_REPO")
    rama  = obtener_secreto("GITHUB_BRANCH", "main")

    if not token or not repo:
        return False, (
            "GitHub no está configurado en Secrets (GITHUB_TOKEN / GITHUB_REPO) — "
            "el archivo se guardó localmente, pero se perderá si la app se reinicia."
        )

    if not os.path.exists(ruta_local):
        return False, f"No se encontró el archivo local: {ruta_local}"

    ruta_repo = ruta_repo or os.path.basename(ruta_local)
    mensaje   = mensaje or f"Actualización automática desde la app: {ruta_repo}"

    url = f"https://api.github.com/repos/{repo}/contents/{ruta_repo}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    with open(ruta_local, "rb") as f:
        contenido_b64 = base64.b64encode(f.read()).decode("utf-8")

    # GitHub exige el sha del archivo actual para poder actualizarlo (si ya existe).
    sha = None
    try:
        resp_get = requests.get(url, headers=headers, params={"ref": rama}, timeout=TIMEOUT)
        if resp_get.status_code == 200:
            sha = resp_get.json().get("sha")
        elif resp_get.status_code not in (404,):
            return False, f"GitHub respondió {resp_get.status_code} al consultar el archivo: {resp_get.text[:200]}"
    except requests.exceptions.RequestException as e:
        return False, f"Error consultando GitHub: {e}"

    payload = {"message": mensaje, "content": contenido_b64, "branch": rama}
    if sha:
        payload["sha"] = sha

    try:
        resp_put = requests.put(url, headers=headers, json=payload, timeout=TIMEOUT)
        if resp_put.status_code in (200, 201):
            return True, f"'{ruta_repo}' sincronizado con GitHub ({repo}@{rama})."
        if resp_put.status_code in (401, 403):
            return False, "GitHub rechazó el token (401/403) — revisa GITHUB_TOKEN y sus permisos."
        return False, f"GitHub respondió {resp_put.status_code}: {resp_put.text[:200]}"
    except requests.exceptions.RequestException as e:
        return False, f"Error subiendo a GitHub: {e}"
