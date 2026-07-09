# =============================================================================
# email_html_Dolly.py — Generador de HTML de correo para las campañas
#
# El HTML de un correo NO puede usar flexbox/grid ni CSS moderno — Outlook de
# escritorio renderiza con el motor de Word, que solo entiende tablas y
# estilos inline. Por eso esta plantilla es más "anticuada" que el resto de
# la app: es la forma correcta de hacerlo para que se vea igual en Gmail,
# Outlook y Apple Mail.
#
# SIN BOTÓN NI LINK — a pedido, por la preocupación de que un botón/link
# genérico (sin personalización real) se vea como un patrón de estafa/phishing.
# El HTML es solo el mensaje de marca; Thomas pega esto en MailUp y el bloque
# de producto/marca del carrito (cuando existe) lo agrega su propia
# integración por separado — no es algo que esta app construya.
# =============================================================================

import html as html_lib

NEGRO = "#1A1A1A"
CREMA = "#FAF8F4"
CARD = "#F5F2EC"
BORDE = "#E7E3DA"
TEXTO_SECUNDARIO = "#6E6B64"


def generar_html_email(asunto, mensaje, cta=None):
    """
    Genera el HTML completo de un correo (documento HTML entero, listo para
    pegar en MailUp). `mensaje` se parte por saltos de línea para armar los
    párrafos. `cta` (si se pasa) se muestra como una línea de cierre en
    negrita, en texto plano — nunca como link ni botón.
    """
    asunto_esc = html_lib.escape(asunto or "")
    parrafos = [html_lib.escape(p) for p in (mensaje or "").split("\n") if p.strip() != ""]
    html_parrafos = "\n".join(
        f'<p style="margin:0 0 16px 0; font-size:16px; line-height:1.6; color:{NEGRO};">{p}</p>'
        for p in parrafos
    )

    cta_html = ""
    if cta and cta.strip():
        cta_esc = html_lib.escape(cta.strip())
        cta_html = f'<p style="margin:8px 0 0 0; font-size:16px; font-weight:bold; color:{NEGRO};">{cta_esc}</p>'

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
          <td style="background-color:{NEGRO}; padding:20px 32px;">
            <span style="color:#FFFFFF; font-size:20px; font-weight:bold; letter-spacing:0.02em;">DOLLY</span>
          </td>
        </tr>
        <tr>
          <td style="padding:36px 32px 36px 32px;">
{html_parrafos}
{cta_html}
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
