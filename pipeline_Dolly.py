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
    """Carga las plantillas de correo por segmento."""
    ruta = os.path.join(RUTA_BASE, "plantillas_campanas.json")
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)

    # Plantillas por defecto
    segmentos = [
        "Cliente VIP", "Cliente Activo", "Con Carrito",
        "Alto Valor Reciente", "Alto Valor En Riesgo", "Alto Valor Perdido",
        "Recuperable Urgente", "Recuperable Flete", "Recuperable Temprano",
        "Recuperable Bajo", "Potencial Con Carrito", "Potencial Sin Carrito",
        "Inactivo", "Perdido",
    ]
    return {
        seg: {
            "activa":       False,
            "asunto":       f"Te echamos de menos, {seg}",
            "mensaje":      f"Hola,\n\nTenemos productos esperándote.\n\nVisítanos en dolly.cl",
            "ultimo_envio": None,
        }
        for seg in segmentos
    }


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

    # Badges de compra / abandono
    df["es_comprador"] = df["paso_abandono"] == "Finalizado"
    df["tiene_carrito_abandonado_historico"] = df["tuvo_carrito_abandonado_historico"].fillna(False)

    # Producto de interés: si compró, el producto comprado; si no, el último
    # producto visitado (el dato más cercano a "qué tenía en el carrito" que
    # entrega VTEX — no existe un campo explícito de ítems del carrito).
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

    df["producto_id"]          = df.apply(_producto_comprado_o_visitado, axis=1)
    df["categoria_producto"]   = df.apply(_categoria_comprada_o_visitada, axis=1)
    df["marca_producto"]       = df.apply(_marca_comprada_o_visitada, axis=1)
    df["departamento_producto"] = df["departmentVisitedTag"] if "departmentVisitedTag" in df.columns else None

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
        "monto_mediano":        df["monto_carrito"].median(),
        "pct_contactables":     df["tiene_newsletter"].mean() * 100,
        "pct_sobre_umbral":     df["sobre_umbral"].mean() * 100,
        "recencia_promedio":    df["recencia_dias"].mean(),
        "clientes_por_segmento": df["segmento"].value_counts().to_dict(),
        "monto_por_segmento":   df.groupby("segmento")["monto_carrito"].median().to_dict(),
        "potencial_por_segmento": (
            df.groupby("segmento").apply(
                lambda x: len(x) * x["monto_carrito"].median()
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
    "Cliente VIP":           ("Compra reciente y de alto monto — el cliente de mayor valor actual.",
                              "Cuidar la relación con beneficios exclusivos (acceso anticipado, despacho prioritario). Evitar descuentos genéricos."),
    "Cliente Activo":        ("Compra con frecuencia, montos medios, buena recencia.",
                              "Mantener con novedades y contenido relevante — no necesita incentivo para comprar."),
    "Alto Valor Reciente":   ("Compró caro hace poco; aún no muestra señales de riesgo.",
                              "Cross-sell o contenido de valor sobre lo que compró, para profundizar la relación."),
    "Alto Valor En Riesgo":  ("Fue buen cliente y empieza a alejarse (61-180 días sin actividad).",
                              "Reactivar con una oferta relevante antes de que pase al siguiente nivel de riesgo."),
    "Alto Valor Perdido":    ("Fue un cliente importante, pero lleva mucho tiempo sin comprar (+300 días).",
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
        monto_mediano = ("monto_carrito", "median"),
    ).reset_index()
    resumen["potencial_clp"] = resumen["clientes"] * resumen["monto_mediano"]
    resumen["orden"] = resumen["segmento"].map(ORDEN_PRIORIDAD_SEGMENTOS)
    return resumen.sort_values("orden").drop(columns="orden")
