# =============================================================================
# email_html_Dolly.py — Generador de HTML de correo para las campañas
#
# El HTML de un correo NO puede usar flexbox/grid ni CSS moderno — Outlook de
# escritorio renderiza con el motor de Word, que solo entiende tablas y
# estilos inline. Por eso esta plantilla es más "anticuada" que el resto de
# la app: es la forma correcta de hacerlo para que se vea igual en Gmail,
# Outlook y Apple Mail.
#
# CON BOTÓN — se reincorporó a pedido explícito del usuario (2026-07-11),
# revirtiendo la decisión anterior de no incluirlo por riesgo de verse como
# patrón de phishing. El botón apunta a dolly.cl (genérico, no personalizado
# por cliente) — si más adelante se agrega personalización real (ej. link
# directo al carrito del cliente), reemplazar la URL fija por una dinámica.
#
# El cierre del mensaje sigue siendo "Te esperamos en dolly.cl" en texto plano,
# y el botón va inmediatamente debajo como refuerzo visual del mismo cierre.
#
# El logo es el oficial de Dolly, incrustado en base64 (viene de la imagen
# que compartió el usuario). Si Thomas necesita reemplazarlo por la versión
# alojada en el sitio real de Dolly, puede cambiar el <img src="..."> por esa
# URL directamente en MailUp — el base64 funciona en la mayoría de clientes
# de correo modernos (Gmail, Apple Mail) pero conviene confirmarlo también en
# Outlook de escritorio antes del envío masivo.
# =============================================================================

import html as html_lib

NEGRO = "#1A1A1A"
ROJO = "#D6362E"
CREMA = "#FAF8F4"
CARD = "#F5F2EC"
BORDE = "#E7E3DA"
TEXTO_SECUNDARIO = "#6E6B64"

URL_DOLLY = "https://www.dolly.cl"

LOGO_DOLLY_BASE64 = (
    "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"
)

MENSAJE_CIERRE_FIJO = "Te esperamos en dolly.cl"


def generar_html_email(asunto, mensaje, cta=None):
    """
    Genera el HTML completo de un correo (documento HTML entero, listo para
    pegar en MailUp). `mensaje` se parte por saltos de línea para armar los
    párrafos. El cierre siempre es "Te esperamos en dolly.cl", en texto
    plano — el parámetro `cta` se mantiene por compatibilidad pero ya no se
    usa para el texto de cierre.
    """
    asunto_esc = html_lib.escape(asunto or "")
    parrafos = [html_lib.escape(p) for p in (mensaje or "").split("\n") if p.strip() != ""]
    html_parrafos = "\n".join(
        f'<p style="margin:0 0 16px 0; font-size:16px; line-height:1.6; color:{NEGRO};">{p}</p>'
        for p in parrafos
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{asunto_esc}</title>
</head>
<body style="margin:0; padding:0; background-color:{CREMA}; font-family:Arial, Helvetica, sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{CREMA};">
  <tr>
    <td align="center" style="padding:32px 16px;">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color:#FFFFFF; border:1px solid {BORDE}; max-width:600px;">
        <tr>
          <td style="background-color:#FFFFFF; padding:24px 32px; border-bottom:1px solid {BORDE};">
            <img src="data:image/png;base64,{LOGO_DOLLY_BASE64}" alt="Dolly" height="32" style="height:32px; width:auto; display:block;">
          </td>
        </tr>
        <tr>
          <td style="padding:36px 32px 36px 32px;">
{html_parrafos}
            <p style="margin:8px 0 20px 0; font-size:16px; font-weight:bold; color:{NEGRO};">{MENSAJE_CIERRE_FIJO}</p>
            <table role="presentation" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td bgcolor="{ROJO}" style="border-radius:4px;">
                  <a href="{URL_DOLLY}" target="_blank" style="display:inline-block; padding:12px 28px; font-family:Arial, Helvetica, sans-serif; font-size:14px; font-weight:bold; color:#FFFFFF; text-decoration:none; border-radius:4px;">
                    Visítanos en dolly.cl
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="background-color:{CARD}; padding:18px 32px; border-top:1px solid {BORDE};" align="center">
            <span style="font-size:12px; color:{TEXTO_SECUNDARIO};">
              DOLLY Chile · Recibiste este correo porque tienes una cuenta con nosotros.
            </span>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>
"""


def nombre_archivo_html(prioridad, segmento, variante):
    """Nombre de archivo consistente con el usado en el CSV de campañas A/B."""
    import re
    import unicodedata

    def slug(texto):
        texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
        texto = re.sub(r"[^\w\s-]", "", texto).strip().lower()
        return re.sub(r"[\s_-]+", "_", texto)

    return f"{prioridad:02d}_{slug(segmento)}_{variante}.html"
