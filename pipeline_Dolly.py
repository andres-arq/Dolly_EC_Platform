# =============================================================================
# pipeline.py
# Proyecto: Dolly Chile — App de Gestión
# Propósito: Funciones centrales que alimentan la app Streamlit.
#            Extraídas de los notebooks para ser reutilizables.
# =============================================================================

import os
import json
import math
import pandas as pd
import numpy as np
from datetime import datetime

# =============================================================================
# PARÁMETROS GLOBALES
# =============================================================================

RUTA_BASE = os.path.dirname(os.path.abspath(__file__))

PARAMS = {
    "ticket_umbral_flete_gratis":  50_000,
    "ticket_promedio_referencia":  55_993,
    "margen_online":               0.15,
    "carrito_horas_min":           2,
    "carrito_horas_max":           24,
    "carrito_monto_minimo":        5_000,
    "carrito_cooldown_horas":      72,
    "periodo_analisis_dias":       1000,
}

UMBRALES = {
    "recencia_activo":    60,
    "recencia_riesgo":    180,
    "recencia_en_riesgo": 300,
    "monto_alto":         100_000,
    "monto_medio":        50_000,
}

# VTEX es una plataforma brasileña — el campo checkouttag llega en portugués.
# Se traduce en dos puntos: al leer el CSV crudo (cargar_csv_vtex) para que
# los datos nuevos ya nazcan en español, y de nuevo al leer el perfil ya
# procesado (cargar_perfil_clientes) por si el archivo guardado es de una
# versión anterior del pipeline y todavía tiene los valores en portugués.
TRADUCCION_PASOS = {
    "DadosPessoais":  "Datos personales",
    "Carrinho":       "Carrito",
    "Endereco":       "Dirección/despacho",
    "FormaPagamento": "Forma de pago",
    "Finalizado":     "Finalizado",
}

# =============================================================================
# CARGA DE DATOS
# =============================================================================

def cargar_csv_vtex(ruta=None):
    """
    Carga y procesa el CSV de VTEX.
    Parsea checkouttag, fechas y montos.
    """
    if ruta is None:
        ruta = os.path.join(RUTA_BASE, "Dolly_Carritos_VTEX.csv")

    df = pd.read_csv(ruta, sep=';', encoding='utf-8-sig', low_memory=False)

    def extraer_paso(val):
        if pd.isna(val):
            return "Desconocido"
        try:
            limpio = str(val).replace('""', '"').strip()
            if limpio.startswith('"') and limpio.endswith('"'):
                limpio = limpio[1:-1]
            parsed    = json.loads(limpio)
            resultado = parsed.get("DisplayValue")
            if resultado and resultado != "null":
                resultado = str(resultado)
                return TRADUCCION_PASOS.get(resultado, resultado)
            return "Desconocido"
        except:
            return "Desconocido"

    df["paso_abandono"]     = df["checkouttag"].apply(extraer_paso)
    df["rclastsessiondate"] = pd.to_datetime(df["rclastsessiondate"], utc=True, errors="coerce")
    df["rclastcartvalue"]   = pd.to_numeric(df["rclastcartvalue"], errors="coerce").fillna(0)

    return df


def cargar_perfil_clientes():
    """Carga el CSV de clientes segmentados. Traduce paso_abandono por si el
    archivo fue generado con una versión del pipeline anterior a la traducción
    portugués→español (defensa extra, no debería hacer nada si ya está al día)."""
    ruta = os.path.join(RUTA_BASE, "clientes_con_perfil.csv")
    if os.path.exists(ruta):
        df = pd.read_csv(ruta)
        if "paso_abandono" in df.columns:
            df["paso_abandono"] = df["paso_abandono"].replace(TRADUCCION_PASOS)
        return df
    return pd.DataFrame()


def cargar_buyer_enrichment():
    """Carga el CSV de enriquecimiento de clientes."""
    ruta = os.path.join(RUTA_BASE, "dolly_buyer_enrichment.csv")
    if os.path.exists(ruta):
        return pd.read_csv(ruta)
    return pd.DataFrame()


def formatear_telefono_cl(numero):
    """
    Formatea a '+56 9 0000 0000'. Acepta el número venga como venga en VTEX
    (con o sin +, con o sin 56, con espacios/guiones) — se queda solo con los
    dígitos y arma el formato chileno estándar de celular (9 dígitos después
    del 56). Si no calza con ese patrón (fijo, extranjero, dato corrupto),
    devuelve el número tal cual llegó en vez de forzar un formato incorrecto.
    Compartida entre Dashboard y Perfil de Cliente para no duplicar la lógica.
    """
    solo_digitos = "".join(ch for ch in str(numero) if ch.isdigit())

    if solo_digitos.startswith("56") and len(solo_digitos) == 11:
        cod_pais, resto = solo_digitos[:2], solo_digitos[2:]
    elif len(solo_digitos) == 9 and solo_digitos.startswith("9"):
        cod_pais, resto = "56", solo_digitos
    else:
        return str(numero)  # formato no reconocido — se muestra tal cual

    return f"+{cod_pais} {resto[0]} {resto[1:5]} {resto[5:9]}"


def cargar_puntos_blueexpress():
    """
    Carga puntos Blue Express desde CSV si existe,
    o retorna el MOCK por defecto.
    """
    ruta = os.path.join(RUTA_BASE, "blue_express_puntos.csv")
    if os.path.exists(ruta):
        return pd.read_csv(ruta)

    # MOCK por defecto
    puntos = [
        {"nombre": "Blue Express Copec Panamericana",    "ciudad": "Puerto Montt", "region": "Los Lagos",    "latitud": -41.4693, "longitud": -72.9424, "estado": "Abierto 24/7"},
        {"nombre": "Blue Express Copec Angelmo",         "ciudad": "Puerto Montt", "region": "Los Lagos",    "latitud": -41.4751, "longitud": -72.9562, "estado": "Abierto 24/7"},
        {"nombre": "Blue Express Copec Alerce",          "ciudad": "Puerto Montt", "region": "Los Lagos",    "latitud": -41.4123, "longitud": -72.9187, "estado": "Abierto 24/7"},
        {"nombre": "Blue Express Copec Osorno Centro",   "ciudad": "Osorno",       "region": "Los Lagos",    "latitud": -40.5740, "longitud": -73.1343, "estado": "Abierto 24/7"},
        {"nombre": "Blue Express Copec Osorno Norte",    "ciudad": "Osorno",       "region": "Los Lagos",    "latitud": -40.5512, "longitud": -73.1289, "estado": "Abierto 24/7"},
        {"nombre": "Blue Express Copec Castro Centro",   "ciudad": "Castro",       "region": "Los Lagos",    "latitud": -42.4782, "longitud": -73.7606, "estado": "Abierto 24/7"},
        {"nombre": "Blue Express Copec Calbuco",         "ciudad": "Calbuco",      "region": "Los Lagos",    "latitud": -41.7726, "longitud": -73.1310, "estado": "Abierto 24/7"},
        {"nombre": "Blue Express Copec Valdivia Centro", "ciudad": "Valdivia",     "region": "Los Ríos",     "latitud": -39.8142, "longitud": -73.2459, "estado": "Abierto 24/7"},
        {"nombre": "Blue Express Copec Temuco Centro",   "ciudad": "Temuco",       "region": "La Araucanía", "latitud": -38.7359, "longitud": -72.5904, "estado": "Abierto 24/7"},
        {"nombre": "Blue Express Copec Concepción",      "ciudad": "Concepción",   "region": "Biobío",       "latitud": -36.8270, "longitud": -73.0498, "estado": "Abierto 24/7"},
    ]
    return pd.DataFrame(puntos)


def cargar_plantillas():
    """
    Carga las plantillas de correo por segmento. Cada segmento tiene DOS
    variantes (A y B) para test A/B, más la hipótesis que se está testeando.
    Si el archivo guardado es de una versión anterior (una sola plantilla por
    segmento, sin variantes), se migra automáticamente a la nueva estructura
    metiendo el contenido viejo en la Variante A y dejando B vacía.
    """
    ruta = os.path.join(RUTA_BASE, "plantillas_campanas.json")
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            plantillas = json.load(f)
        return _migrar_plantillas_a_variantes(plantillas)

    return _plantillas_por_defecto()


def _migrar_plantillas_a_variantes(plantillas):
    """Convierte el formato viejo (un solo asunto/mensaje) al formato con variantes A/B."""
    migradas = {}
    for seg, config in plantillas.items():
        if "variantes" in config:
            migradas[seg] = config
        else:
            migradas[seg] = {
                "activa": config.get("activa", False),
                "hipotesis_ab": "",
                "variantes": {
                    "A": {
                        "nombre_variante": "Variante A",
                        "asunto": config.get("asunto", ""),
                        "mensaje": config.get("mensaje", ""),
                        "cta": "Ver más",
                    },
                    "B": {
                        "nombre_variante": "Variante B",
                        "asunto": "",
                        "mensaje": "",
                        "cta": "",
                    },
                },
                "ultimo_envio": config.get("ultimo_envio"),
            }
    return migradas


def _plantillas_por_defecto():
    """
    Plantillas por defecto — 100% genéricas, sin variables de personalización
    ({{nombre}}, {{monto}}, etc.). No se cuenta con el dato del nombre real
    de cada cliente, así que las plantillas están escritas para funcionar
    igual de bien sin ninguna variable — mismo tono cálido y familiar, sin
    descuentos ni beneficios no acordados, sin presión de escasez y sin
    mencionar problemas.
    """
    datos = {
        "Recuperable Urgente": (
            "Enfoque en el producto (A) vs. Enfoque en acompañamiento sin mencionar el problema de pago (B)",
            ("Enfoque en el producto", "Tus productos te están esperando",
             "Hola,\nQueríamos avisarte que tus productos siguen guardados en tu carrito, listos para cuando quieras.\nSi todavía te interesan, puedes terminar tu compra con calma, cuando gustes.",
             "Ver mi carrito"),
            ("Acompañamiento", "¿Seguimos con tu compra?",
             "Hola,\nNotamos que tu compra quedó a mitad de camino.\nEstamos disponibles para ayudarte si lo necesitas.",
             "Completar mi compra"),
        ),
        "Recuperable Flete": (
            "Recordatorio simple sobre el producto (A) vs. Información completa del pedido, sin mencionar costos (B)",
            ("Recordatorio simple", "Tu pedido está listo para revisarlo",
             "Hola,\nTus productos siguen en tu carrito.\nCuando quieras, puedes revisar los detalles de tu pedido con toda la calma del mundo.",
             "Ver mi carrito"),
            ("Información completa del pedido", "Toda la información de tu pedido, cuando la necesites",
             "Hola,\nSabemos que a veces se quiere revisar bien los detalles antes de decidir.\nPor eso dejamos toda la información de tu pedido disponible, para cuando quieras consultarla. Tu carrito sigue esperándote.",
             "Ver el detalle de mi pedido"),
        ),
        "Recuperable Temprano": (
            "Recordatorio simple sobre el producto (A) vs. Foco en flexibilidad y sin apuro (B)",
            ("Recordatorio simple", "Dejaste algunas cosas lindas en tu carrito",
             "Hola,\nHace poco visitaste DOLLY y dejaste algunos productos guardados.\nSiguen ahí, esperando por si quieres darles una segunda mirada.",
             "Ver mi carrito"),
            ("Sin apuro", "Guardamos tu carrito por si necesitas más tiempo",
             "Hola,\nSabemos que a veces simplemente falta tiempo para decidir con calma o conversarlo en casa.\nPor eso dejamos tu carrito guardado, para que lo retomes cuando quieras, sin ningún apuro.",
             "Retomar mi carrito cuando quiera"),
        ),
        "Recuperable Bajo": (
            "Recordatorio simple y cercano (A) vs. Acompañamiento cercano, sin pedir explicaciones (B)",
            ("Recordatorio cercano", "Tus productos DOLLY siguen ahí",
             "Hola,\nTodavía tienes productos guardados en tu carrito.\nCuando quieras retomarlos, ahí van a estar esperándote, sin ningún apuro de nuestra parte.",
             "Ver mi carrito"),
            ("Acompañamiento cercano", "Estamos aquí si nos necesitas",
             "Hola,\nVimos que tu compra quedó pendiente.\nSi tienes alguna consulta sobre tallas, colores o despacho, con mucho gusto te ayudamos a encontrar lo que buscas.",
             "Conversar con nosotros"),
        ),
        "Cliente VIP": (
            "Acceso anticipado cálido (A) vs. Reconocimiento profesional a la preferencia (B) — beneficios NO monetarios, confirmar con Thomas",
            ("Acceso anticipado cálido", "Algo especial para ti antes que nadie",
             "Hola,\nComo reconocimiento a tu preferencia por DOLLY, queremos mostrarte nuestras próximas novedades antes que al resto de nuestros clientes.",
             "Ver novedades exclusivas"),
            ("Reconocimiento a la preferencia", "Gracias por confiar en DOLLY",
             "Hola,\nTu preferencia significa mucho para nosotros.\nComo reconocimiento, tus pedidos van a tener preparación prioritaria en nuestra bodega.",
             "Conocer más sobre DOLLY"),
        ),
        "Cliente Activo": (
            "Foco en el producto nuevo (A) vs. Foco en la relación de largo plazo (B)",
            ("Foco en producto", "Esto es lo nuevo en DOLLY",
             "Hola,\nLlegaron productos nuevos pensados para ti, que ya conoces lo mejor de nuestra tienda.\nTe invitamos a darles una mirada con calma.",
             "Ver lo nuevo"),
            ("Relación de largo plazo", "Gracias por seguir prefiriendo DOLLY",
             "Hola,\nComo cliente frecuente, quisimos que fueras de los primeros en conocer las novedades que hemos preparado.\nGracias por seguir eligiéndonos.",
             "Ver novedades"),
        ),
        "Alto Valor Reciente": (
            "Cuidado del producto (A) vs. Sugerencias que complementan tu compra (B)",
            ("Cuidado del producto", "Todo lo que puede servirte sobre tu compra",
             "Hola,\nGracias por tu compra reciente.\nTe dejamos algunos tips de cuidado y uso para que le saques el máximo provecho a tus productos, directo de nuestro equipo.",
             "Ver guía de cuidado"),
            ("Sugerencias complementarias", "Esto combina perfecto con tu compra",
             "Hola,\nHace poco elegiste comprar en DOLLY.\nSeleccionamos algunos productos que complementan justo lo que llevaste, para que armes el look completo si te interesa.",
             "Ver productos sugeridos"),
        ),
        "Alto Valor En Riesgo": (
            "Curaduría personalizada por historial (A) vs. Reconexión relacional cálida (B)",
            ("Curaduría personalizada", "Preparamos una selección pensando en ti",
             "Hola,\nComo uno de nuestros clientes más importantes, armamos una selección con las categorías y estilos que más te han gustado en tus visitas anteriores.",
             "Ver mi selección"),
            ("Reconexión cálida", "Nos encantaría volver a acompañarte",
             "Hola,\nDurante mucho tiempo confiaste en DOLLY.\nNos encantaría seguir acompañándote en tus próximas compras, con las novedades que hemos preparado.",
             "Ver qué hay de nuevo"),
        ),
        "Alto Valor Perdido": (
            "Evolución de marca y prueba social (A) vs. Reconexión emocional cálida (B)",
            ("Evolución de marca", "Redescubre lo que construimos para ti",
             "Hola,\nEn algún momento fuiste uno de nuestros clientes más importantes y valoramos mucho esa etapa.\nHemos seguido mejorando nuestros materiales y nuestro servicio, y te invitamos a conocer los productos favoritos de nuestra comunidad actual.",
             "Ver los favoritos de la temporada"),
            ("Reconexión emocional", "Te extrañamos en DOLLY",
             "Hola,\nEn algún momento fuiste un cliente importante para DOLLY.\nNos encantaría reencontrarnos y mostrarte todo lo que hemos cuidado y mejorado desde tu última visita.",
             "Volver a visitarnos"),
        ),
        "Con Carrito": (
            "Recordatorio directo y simple (A) vs. Acompañamiento cercano ante dudas (B)",
            ("Recordatorio simple", "Tu carrito sigue esperándote",
             "Hola,\nTus productos siguen guardados en tu carrito.\nCuando quieras, puedes retomar tu compra sin ningún apuro.",
             "Ver mi carrito"),
            ("Acompañamiento cercano", "¿Te ayudamos con tu compra en DOLLY?",
             "Hola,\nVimos que tienes productos guardados en tu carrito.\nSi tienes dudas sobre talla, color o despacho, con gusto te ayudamos a decidir con calma.",
             "Conversar con nosotros"),
        ),
        "Potencial Con Carrito": (
            "Cierre simple y cálido (A) vs. Confianza y cercanía para tu primera compra (B)",
            ("Cierre simple", "Tu primera compra está lista para confirmarse",
             "Hola,\nYa encontraste productos que te interesan.\nCuando quieras, puedes confirmar tu pedido para recibirlo en casa, con toda la calma que necesites.",
             "Confirmar mi pedido"),
            ("Confianza y cercanía", "Compra con toda la tranquilidad en DOLLY",
             "Hola,\nYa armaste tu carrito en DOLLY. Queremos que tu primera experiencia sea muy grata: contamos con seguimiento de tu pedido y una política de cambios simple y cercana. Estamos disponibles para ayudarte en lo que necesites.",
             "Finalizar mi compra"),
        ),
        "Potencial Sin Carrito": (
            "Descubrimiento por popularidad (A) vs. Invitación personalizada y cercana (B)",
            ("Descubrimiento por popularidad", "Lo más elegido por nuestros clientes esta semana",
             "Hola,\nSabemos que ya conoces DOLLY.\nPara ayudarte a inspirarte, reunimos los productos favoritos de esta temporada, elegidos por cientos de clientes.",
             "Ver los favoritos de la semana"),
            ("Invitación cercana", "Te ayudamos a encontrar lo tuyo",
             "Hola,\nQueremos ayudarte a encontrar productos pensados para ti y tu estilo de vida, con la misma cercanía de siempre.",
             "Explorar el catálogo"),
        ),
        "Inactivo": (
            "Novedades del catálogo (A) vs. Encuesta cercana de reactivación (B)",
            ("Novedades del catálogo", "Esto es lo nuevo en DOLLY",
             "Hola,\nQueremos volver a ser parte de tus próximas compras. Por eso te presentamos los productos nuevos que acaban de llegar.",
             "Explorar novedades"),
            ("Encuesta cercana", "Tu opinión nos ayuda a mejorar",
             "Hola,\nHace tiempo que no sabemos de ti, y nos encantaría saber qué buscas hoy en día o qué podemos hacer mejor. Te tomará menos de 1 minuto.",
             "Responder encuesta corta"),
        ),
        "Perdido": (
            "Renovación de marca (A) vs. Invitación abierta y cálida a redescubrir (B)",
            ("Renovación de marca", "DOLLY ha renovado su catálogo",
             "Hola,\nHa pasado bastante tiempo desde tu última compra.\nRenovamos nuestro catálogo y mejoramos la experiencia de nuestra tienda — te invitamos a conocer esta nueva etapa de DOLLY.",
             "Descubrir la nueva experiencia"),
            ("Invitación cálida", "Queremos volver a encontrarnos contigo",
             "Hola,\nSabemos que el tiempo pasa, y nosotros seguimos mejorando pensando siempre en nuestros clientes.\nCuando quieras, las puertas de DOLLY están abiertas para que veas todo lo que hemos cuidado para ti.",
             "Ver catálogo actualizado"),
        ),
    }

    plantillas = {}
    for seg, (hipotesis, var_a, var_b) in datos.items():
        nombre_a, asunto_a, mensaje_a, cta_a = var_a
        nombre_b, asunto_b, mensaje_b, cta_b = var_b
        plantillas[seg] = {
            "activa": False,
            "hipotesis_ab": hipotesis,
            "variantes": {
                "A": {"nombre_variante": nombre_a, "asunto": asunto_a, "mensaje": mensaje_a, "cta": cta_a},
                "B": {"nombre_variante": nombre_b, "asunto": asunto_b, "mensaje": mensaje_b, "cta": cta_b},
            },
            "ultimo_envio": None,
        }
    return plantillas


def guardar_plantillas(plantillas):
    """Guarda las plantillas de correo localmente y las sincroniza con GitHub
    (si está configurado) para que no se pierdan al reiniciar Streamlit Cloud.
    Devuelve (ok: bool, detalle: str) para que la página lo muestre de forma
    persistente (no un toast que se desvanece solo)."""
    ruta = os.path.join(RUTA_BASE, "plantillas_campanas.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(plantillas, f, indent=2, ensure_ascii=False)
    return _sincronizar_con_github(ruta, "plantillas_campanas.json")


def guardar_puntos_blueexpress(df_puntos):
    """Guarda el DataFrame de puntos Blue Express como CSV localmente y lo
    sincroniza con GitHub (si está configurado).
    Devuelve (ok: bool, detalle: str)."""
    ruta = os.path.join(RUTA_BASE, "blue_express_puntos.csv")
    df_puntos.to_csv(ruta, index=False)
    return _sincronizar_con_github(ruta, "blue_express_puntos.csv")


def _sincronizar_con_github(ruta_local, ruta_repo):
    """
    Intenta subir el archivo a GitHub para que persista entre reinicios.
    Nunca lanza excepción — si algo falla, devuelve (False, motivo) para que
    la página lo muestre, pero el guardado local ya se hizo de todas formas.
    """
    try:
        from github_sync import subir_archivo_a_github, github_configurado
    except Exception as e:
        return False, f"No se pudo cargar el módulo de sincronización: {e}"

    if not github_configurado():
        return False, "GitHub no configurado — cambio guardado solo localmente (se perderá al reiniciar)."

    try:
        return subir_archivo_a_github(ruta_local, ruta_repo)
    except Exception as e:
        return False, f"Error inesperado sincronizando con GitHub: {e}"


# =============================================================================
# SEGMENTACIÓN
# =============================================================================

def segmentar_clientes(df_raw):
    """
    Aplica el pipeline completo de segmentación al DataFrame raw de VTEX.
    Retorna DataFrame con columna 'segmento' y variables RFM.

    Cambios clave:
    - Se usa SIEMPRE la sesión más reciente de cada cliente para definir su estado
      actual (antes se priorizaba cualquier sesión con paso de checkout conocido,
      aunque fuera más antigua que una sesión "Desconocido" o "Finalizado" posterior).
    - "Finalizado" ya no se trata como abandono: se guarda como badge `es_comprador`
      (compró en su sesión más reciente) y no participa en la Capa 1 de recuperación.
    - Se agrega `tuvo_carrito_abandonado_historico`: True si en CUALQUIER sesión
      pasada (no solo la más reciente) el cliente llegó a un paso de abandono
      conocido. Permite identificar, por ejemplo, a un comprador reciente que
      antes dejó carritos abandonados.
    """
    df = df_raw.copy()
    df["rclastsessiondate"] = pd.to_datetime(df["rclastsessiondate"], utc=True, errors="coerce")
    df["rclastcartvalue"]   = pd.to_numeric(df["rclastcartvalue"], errors="coerce").fillna(0)

    FECHA_CORTE = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=PARAMS["periodo_analisis_dias"])

    PASOS_ABANDONO = ["Forma de pago", "Dirección/despacho", "Carrito", "Datos personales"]

    # Métricas y badges calculados sobre el HISTORIAL COMPLETO (todas las sesiones),
    # antes de quedarnos con una sola fila por cliente.
    metricas = df.groupby("userId").agg(
        num_sesiones       = ("userId",           "count"),
        monto_max_carrito  = ("rclastcartvalue",  "max"),
        monto_prom_carrito = ("rclastcartvalue",  "mean"),
        primera_sesion     = ("rclastsessiondate","min"),
        ultima_sesion      = ("rclastsessiondate","max"),
    ).reset_index()

    badges = df.groupby("userId")["paso_abandono"].agg(
        tuvo_carrito_abandonado_historico = lambda s: s.isin(PASOS_ABANDONO).any(),
        tuvo_compra_finalizada_historico  = lambda s: (s == "Finalizado").any(),
    ).reset_index()

    metricas = metricas.merge(badges, on="userId", how="left")

    # Deduplicar: nos quedamos con la sesión MÁS RECIENTE de cada cliente, sin
    # excepción — antes se le daba prioridad a cualquier fila con paso conocido
    # por sobre la recencia real, lo que podía mostrar un estado de checkout
    # viejo en vez del estado actual del cliente.
    df = df.sort_values("rclastsessiondate", ascending=False).drop_duplicates(subset="userId", keep="first")
    df = df.merge(metricas, on="userId", how="left")
    df = df[df["ultima_sesion"] >= FECHA_CORTE]

    # Variables RFM
    df["recencia_dias"] = (pd.Timestamp.now(tz="UTC") - df["ultima_sesion"]).dt.days
    df["monto_carrito"] = df["rclastcartvalue"]
    df["ticket_prom"]   = df["monto_prom_carrito"].round(0)
    df["ticket_max"]    = df["monto_max_carrito"].round(0)
    df["frecuencia"]    = df["num_sesiones"]
    df["brecha_flete"]  = (PARAMS["ticket_umbral_flete_gratis"] - df["monto_carrito"]).clip(lower=0)
    df["sobre_umbral"]  = df["monto_carrito"] >= PARAMS["ticket_umbral_flete_gratis"]
    df["tiene_telefono"]   = df["homePhone"].notna()
    df["tiene_newsletter"] = df["isNewsletterOptIn"].fillna(False)

    # Email: puede venir vacío en el CSV de VTEX (por eso existe el notebook
    # que lo completa cruzando con carritos_2026.csv antes de subir el CSV).
    # Se calcula de forma defensiva por si la columna no viene en el archivo.
    if "email" in df.columns:
        df["tiene_email"] = df["email"].notna() & (df["email"].astype(str).str.strip() != "")
    else:
        df["email"] = None
        df["tiene_email"] = False

    # Badges de compra / abandono
    df["es_comprador"] = df["paso_abandono"] == "Finalizado"
    df["tiene_carrito_abandonado_historico"] = df["tuvo_carrito_abandonado_historico"].fillna(False)

    # Producto de interés: si compró, el producto comprado; si no, el último
    # producto visitado (el dato más cercano a "qué tenía en el carrito" que
    # entrega VTEX — no existe un campo explícito de ítems del carrito).
    #
    # Estas columnas vienen en el mismo formato JSON que checkouttag (con
    # "DisplayValue" adentro, más metadata de "Scores" que no se necesita) —
    # hay que parsearlas igual que extraer_paso(), si no se guarda el JSON
    # completo como si fuera el nombre del producto/marca.
    def _extraer_display_value(val):
        if pd.isna(val):
            return None
        try:
            limpio = str(val).replace('""', '"').strip()
            if limpio.startswith('"') and limpio.endswith('"'):
                limpio = limpio[1:-1]
            parsed = json.loads(limpio)
            resultado = parsed.get("DisplayValue")
            if resultado and str(resultado).lower() != "null":
                return str(resultado)
            return None
        except Exception:
            return None

    for _col in ["productPurchasedTag", "productVisitedTag",
                 "categoryPurchasedTag", "categoryVisitedTag",
                 "brandPurchasedTag", "brandVisitedTag",
                 "departmentVisitedTag"]:
        if _col in df.columns:
            df[_col] = df[_col].apply(_extraer_display_value)
        else:
            df[_col] = None

    def _producto_comprado_o_visitado(row):
        if row.get("es_comprador"):
            return row.get("productPurchasedTag")
        return row.get("productVisitedTag")

    def _categoria_comprada_o_visitada(row):
        if row.get("es_comprador"):
            return row.get("categoryPurchasedTag")
        return row.get("categoryVisitedTag")

    def _marca_comprada_o_visitada(row):
        if row.get("es_comprador"):
            return row.get("brandPurchasedTag")
        return row.get("brandVisitedTag")

    df["producto_id"]           = df.apply(_producto_comprado_o_visitado, axis=1)
    df["categoria_producto"]    = df.apply(_categoria_comprada_o_visitada, axis=1)
    df["marca_producto"]        = df.apply(_marca_comprada_o_visitada, axis=1)
    df["departamento_producto"] = df["departmentVisitedTag"]

    df["segmento"] = df.apply(_asignar_segmento, axis=1)
    df["segmento_reglas"] = df["segmento"]

    return df


def _asignar_segmento(row):
    """Lógica de segmentación en dos capas."""
    paso          = row.get("paso_abandono", "Desconocido")
    dias          = row["recencia_dias"]
    monto         = row["monto_carrito"]
    es_comprador  = row.get("es_comprador", False)

    # Un cliente "comprador" (su sesión más reciente terminó en Finalizado) no
    # tiene un carrito pendiente que recuperar — su monto_carrito es la compra
    # que ya se cerró, no una oportunidad futura. Por eso no cuenta como
    # "tiene_carrito" para las reglas de Con Carrito / Potencial Con Carrito.
    tiene_carrito = (monto > 0) and not es_comprador

    # Capa 1 — paso de checkout conocido (abandono real, nunca "Finalizado")
    if paso == "Forma de pago":
        return "Recuperable Urgente"
    elif paso == "Dirección/despacho":
        return "Recuperable Flete"
    elif paso == "Carrito":
        return "Recuperable Temprano"
    elif paso == "Datos personales":
        return "Recuperable Bajo"

    # Capa 2 — recencia y monto
    if dias <= UMBRALES["recencia_activo"] and monto >= UMBRALES["monto_alto"]:
        return "Cliente VIP"
    elif dias <= UMBRALES["recencia_activo"] and monto >= UMBRALES["monto_medio"]:
        return "Cliente Activo"
    elif UMBRALES["recencia_activo"] < dias <= UMBRALES["recencia_riesgo"] and monto >= UMBRALES["monto_alto"]:
        return "Alto Valor Reciente"
    elif UMBRALES["recencia_riesgo"] < dias <= UMBRALES["recencia_en_riesgo"] and monto >= UMBRALES["monto_alto"]:
        return "Alto Valor En Riesgo"
    elif dias > UMBRALES["recencia_en_riesgo"] and monto >= UMBRALES["monto_alto"]:
        return "Alto Valor Perdido"
    elif dias <= UMBRALES["recencia_en_riesgo"] and tiene_carrito and monto >= UMBRALES["monto_medio"]:
        return "Con Carrito"
    elif dias <= UMBRALES["recencia_activo"] and tiene_carrito:
        return "Potencial Con Carrito"
    elif dias <= UMBRALES["recencia_activo"]:
        return "Potencial Sin Carrito"
    elif dias > UMBRALES["recencia_en_riesgo"]:
        return "Perdido"
    else:
        return "Inactivo"


# =============================================================================
# MATCH BLUE EXPRESS
# =============================================================================

def distancia_haversine(lat1, lon1, lat2, lon2):
    """Distancia en km entre dos coordenadas."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def punto_mas_cercano(lat, lon, df_puntos):
    """Retorna el punto Blue Express más cercano a una coordenada."""
    df = df_puntos.dropna(subset=["latitud", "longitud"]).copy()
    df["distancia_km"] = df.apply(
        lambda r: distancia_haversine(lat, lon, r["latitud"], r["longitud"]), axis=1
    )
    return df.sort_values("distancia_km").iloc[0]


# =============================================================================
# ESTADÍSTICAS
# =============================================================================

def calcular_estadisticas(df):
    """
    Calcula KPIs principales desde el DataFrame segmentado.
    Retorna dict con métricas listas para mostrar en dashboard.
    """
    return {
        "total_clientes":       len(df),
        "monto_medio":          df["monto_carrito"].mean(),
        "pct_contactables":     df["tiene_newsletter"].mean() * 100,
        "pct_sobre_umbral":     df["sobre_umbral"].mean() * 100,
        "recencia_promedio":    df["recencia_dias"].mean(),
        "clientes_por_segmento": df["segmento"].value_counts().to_dict(),
        "monto_por_segmento":   df.groupby("segmento")["monto_carrito"].mean().to_dict(),
        "potencial_por_segmento": (
            df.groupby("segmento").apply(
                lambda x: len(x) * x["monto_carrito"].mean()
            ).to_dict()
        ),
    }


# =============================================================================
# PRIORIZACIÓN DE CONTACTO
# =============================================================================

# Orden de urgencia de contacto: los "Recuperable" primero (dinero casi cerrado,
# se enfría rápido), luego alto valor en riesgo/VIP, y así hasta los segmentos
# de menor urgencia. Los que no aparecen aquí (por si se agrega un segmento
# nuevo) quedan al final automáticamente.
ORDEN_PRIORIDAD_SEGMENTOS = {
    "Recuperable Urgente":   1,
    "Recuperable Flete":     2,
    "Recuperable Temprano":  3,
    "Recuperable Bajo":      4,
    "Alto Valor En Riesgo":  5,
    "Cliente VIP":           6,
    "Alto Valor Reciente":   7,
    "Con Carrito":           8,
    "Potencial Con Carrito": 9,
    "Cliente Activo":        10,
    "Alto Valor Perdido":    11,
    "Potencial Sin Carrito": 12,
    "Inactivo":              13,
    "Perdido":               14,
}

# Glosario ejecutivo: qué significa cada segmento y qué hacer con él. Se usa
# en el Dashboard para que cualquiera (no solo quien construyó la segmentación)
# entienda de un vistazo por qué un cliente cae en cada categoría.
DESCRIPCION_SEGMENTOS = {
    "Recuperable Urgente":   ("Llegó hasta \"Forma de pago\" y no completó — alta intención, dinero casi cerrado.",
                              "Contactar hoy (llamada/WhatsApp). Revisar si hubo un problema con el método de pago."),
    "Recuperable Flete":     ("Abandonó justo al ver el costo de despacho.",
                              "Mostrar cuánto le falta para el despacho gratis, o financiar el envío si el monto lo justifica."),
    "Recuperable Temprano":  ("Dejó el carrito en un paso inicial del checkout — interés reciente pero aún tibio.",
                              "Recordatorio simple, sin presión ni descuento todavía."),
    "Recuperable Bajo":      ("Abandonó muy temprano (datos personales) — baja probabilidad de conversión.",
                              "Último intento; si no responde a un recordatorio, requiere incentivo concreto (descuento)."),
    "Cliente VIP":           ("Compra de alto monto (≥$100.000) hace 60 días o menos — el cliente de mayor valor actual.",
                              "Cuidar la relación con beneficios exclusivos (acceso anticipado, despacho prioritario). Evitar descuentos genéricos."),
    "Cliente Activo":        ("Compra con frecuencia, montos medios, buena recencia.",
                              "Mantener con novedades y contenido relevante — no necesita incentivo para comprar."),
    "Alto Valor Reciente":   ("Compra de alto monto (≥$100.000), entre 61 y 180 días sin volver — aún no muestra señales de riesgo.",
                              "Cross-sell o contenido de valor sobre lo que compró, para profundizar la relación."),
    "Alto Valor En Riesgo":  ("Compra de alto monto (≥$100.000), entre 181 y 300 días sin volver — empieza a alejarse.",
                              "Reactivar con una oferta relevante antes de que pase al siguiente nivel de riesgo."),
    "Alto Valor Perdido":    ("Compra de alto monto (≥$100.000), pero lleva más de 300 días sin comprar.",
                              "Oferta fuerte de reactivación — es la última oportunidad real antes de darlo por perdido."),
    "Con Carrito":           ("Tiene un carrito armado con monto medio/alto, sin abandono de checkout identificado.",
                              "Recordatorio de carrito estándar."),
    "Potencial Con Carrito": ("Cliente nuevo o poco frecuente que ya armó un carrito.",
                              "Incentivo de primera compra (descuento de bienvenida) para cerrar la conversión inicial."),
    "Potencial Sin Carrito": ("Visita la tienda, pero no arma carrito.",
                              "Contenido de descubrimiento (productos populares), no venta directa todavía."),
    "Inactivo":              ("Recencia alta (más de 300 días) sin las características de alto valor.",
                              "Campaña de reactivación general, de bajo costo."),
    "Perdido":               ("Más de un año sin actividad — la menor probabilidad de conversión de toda la base.",
                              "Solo justifica un incentivo fuerte; en general es mejor priorizar el resto de la base primero."),
}


def clientes_prioritarios(df, n=25):
    """
    Devuelve los `n` clientes a contactar primero: ordenados por urgencia de
    segmento (Recuperable Urgente/Flete arriba) y, dentro del mismo nivel de
    urgencia, por quién tuvo actividad más reciente.

    Excluye siempre a los "compradores" (paso_abandono == "Finalizado") — no
    tiene sentido priorizar el contacto de alguien que ya completó su compra;
    solo se consideran clientes en "Desconocido" o en un paso de abandono real.
    """
    df = df.copy()
    if "es_comprador" in df.columns:
        df = df[df["es_comprador"] != True]  # noqa: E712 (evita ambigüedad con NaN)
    df["_prioridad"] = df["segmento"].map(ORDEN_PRIORIDAD_SEGMENTOS).fillna(99)
    df = df.sort_values(["_prioridad", "recencia_dias"], ascending=[True, True])
    return df.head(n).drop(columns="_prioridad")


SEGMENTOS_RECUPERABLES = [
    "Recuperable Urgente", "Recuperable Flete", "Recuperable Temprano", "Recuperable Bajo",
]


def resumen_recuperables(df):
    """
    Resumen de los 4 segmentos de recuperación de carrito — los más urgentes
    y accionables, pero que en el gráfico general de todos los segmentos
    quedan invisibles al lado de Perdido/Inactivo (miles de clientes vs.
    decenas). Se calcula aparte para que tengan su propio gráfico y escala.
    """
    df_rec = df[df["segmento"].isin(SEGMENTOS_RECUPERABLES)]
    if df_rec.empty:
        return pd.DataFrame(columns=["segmento", "clientes", "potencial_clp"])
    resumen = df_rec.groupby("segmento").agg(
        clientes = ("userId", "count"),
        monto_medio = ("monto_carrito", "mean"),
    ).reset_index()
    resumen["potencial_clp"] = resumen["clientes"] * resumen["monto_medio"]
    resumen["orden"] = resumen["segmento"].map(ORDEN_PRIORIDAD_SEGMENTOS)
    return resumen.sort_values("orden").drop(columns="orden")
