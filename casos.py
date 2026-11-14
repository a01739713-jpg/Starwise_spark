"""STARWISE · casos.py

Caso FICTICIO «Talavera Viva» (taller de cerámica en Puebla) y motor por reglas
de la clienta simulada Carmen Ruiz. Carmen es STAKEHOLDER, no tutora: solo
revela hechos del caso cuando la pregunta es pertinente y nunca da la solución.

Todos los números de este archivo son hechos del CASO SINTÉTICO, no datos del
sector real. No existe empresa colaboradora.
"""
from __future__ import annotations

import re

from datos import quitar_tildes

EMPRESA = "Talavera Viva"
ETIQUETA_FICTICIA = "Empresa ficticia · Datos de práctica"
PRESUPUESTO_INICIAL = 150_000
PRESUPUESTO_RECORTE = 60_000
TURNO_GIRO = 4  # en la 4.ª intervención del estudiante con Carmen llega el recorte

CARMEN_SALUDO = (
    "¡Qué bueno que llegaste! Soy Carmen Ruiz, dueña de Talavera Viva. Te soy directa: "
    "las ventas de este trimestre bajaron 28 % frente al anterior. El lunes tengo junta con mi socio "
    "y necesito un plan para recuperar parte de las ventas sin despedir a nadie del taller. "
    "Tengo $150,000 MXN para invertir. ¿Qué necesitas saber?"
)

CARMEN_RECORTE = (
    "Perdón que te interrumpa… acabo de hablar con mi socio. Tuvimos que pagar una reparación del horno "
    "y el presupuesto para el plan baja a $60,000 MXN. Lo que tengas pensado, hay que replanearlo."
)

# Categorías que cuentan para el criterio de Investigación de la rúbrica.
CATEGORIAS_INVESTIGACION = {
    "clientes": "Preguntó por clientes o segmentos",
    "costos": "Preguntó por costos o márgenes",
    "canales": "Preguntó por canales de venta o redes",
    "meta": "Preguntó por la meta, la junta o cómo medir el éxito",
}

# Cada hecho: id, categoría de investigación (o None), palabras clave (ya sin tildes,
# se buscan como raíz), respuesta de Carmen y «dato citables» que se habilitan para
# la propuesta cuando el hecho se descubre.
HECHOS: list[dict] = [
    {"id": "segmentos", "cat": "clientes",
     "claves": ["segment", "cliente", "quien compra", "quienes compran", "mercado", "publico", "comprador"],
     "texto": "Vendemos a cuatro grupos: restaurantes, hoteles, novias y novios que hacen bodas, y turistas que "
              "entran a la tienda del centro histórico. Los restaurantes eran nuestro cliente más grande.",
     "dato": "Hay 4 segmentos: restaurantes, hoteles, bodas y turistas; restaurantes era el más grande"},
    {"id": "restaurantes", "cat": "clientes",
     "claves": ["restaurant", "fonda", "cocina", "vajilla", "plato"],
     "texto": "Dos restaurantes del centro se cambiaron a vajilla industrial. No fue por el diseño: cuando se les "
              "rompe una pieza, la reposición nos tarda hasta 4 semanas si no hay inventario, y ellos la necesitan en 2.",
     "dato": "Restaurantes piden reposición en 2 semanas; Talavera Viva tarda hasta 4 sin stock"},
    {"id": "hoteles", "cat": "clientes",
     "claves": ["hotel", "hospedaje", "boutique"],
     "texto": "Los hoteles boutique nos compran para habitaciones y regalos de bienvenida. Siempre piden piezas con su "
              "logo; les encantan, pero se quejan de la espera.",
     "dato": "Hoteles boutique piden piezas con logo y se quejan de la espera"},
    {"id": "bodas", "cat": "clientes",
     "claves": ["boda", "novia", "novio", "evento", "recuerdo", "regalo"],
     "texto": "En bodas vendemos recuerdos personalizados. Este trimestre fue temporada baja y varias parejas "
              "compararon nuestro precio con piezas de imitación.",
     "dato": "En bodas compiten con imitaciones más baratas"},
    {"id": "turismo", "cat": "clientes",
     "claves": ["turis", "centro historico", "tienda", "local", "calle", "peaton", "visitante"],
     "texto": "La tienda está en el centro histórico. Este trimestre hubo obras en nuestra calle y pasó mucha menos "
              "gente. Los turistas que entran sí compran, pero entraron menos.",
     "dato": "Obras en la calle redujeron el paso de turistas a la tienda"},
    {"id": "instagram", "cat": "canales",
     "claves": ["instagram", "redes", "red social", "digital", "internet", "en linea", "online", "canal", "facebook",
                "tiktok", "whatsapp", "publicidad", "marketing", "promocion"],
     "texto": "Tenemos Instagram, pero publico como una vez al mes. Por ahí entra menos del 5 % de lo que vendemos; "
              "casi todo es venta directa a negocios y la tienda.",
     "dato": "Instagram aporta menos del 5 % de las ventas; casi todo es venta directa y tienda"},
    {"id": "competencia", "cat": None,
     "claves": ["competen", "precio", "caro", "barato", "imitacion", "industrial", "rival"],
     "texto": "Hay tiendas que venden cerámica de imitación a la mitad del precio. El cliente muchas veces no "
              "distingue una pieza hecha a mano de una industrial.",
     "dato": "La imitación cuesta cerca de la mitad y el cliente no distingue lo artesanal"},
    {"id": "margen", "cat": "costos",
     "claves": ["margen", "costo", "cost", "ganancia", "utilidad", "rentab", "gasto"],
     "texto": "Los costos están en la carpeta. Te adelanto: lo personalizado es lo que más margen deja, alrededor "
              "de 55 %; el azulejo es lo que menos deja.",
     "dato": "Personalizados dejan ~55 % de margen; azulejo es el de menor margen"},
    {"id": "entrega", "cat": None,
     "claves": ["entrega", "tiempo", "tarda", "semana", "demora", "produccion", "capacidad", "horno", "inventario", "stock"],
     "texto": "Una pieza personalizada tarda 5 semanas: modelado, secado, dos quemas y pintado a mano. Si tuviéramos "
              "piezas base en inventario, podríamos recortar tiempos de reposición.",
     "dato": "Personalizados tardan 5 semanas"},
    {"id": "personalizados", "cat": None,
     "claves": ["personaliz", "logo", "a la medida", "diseno", "pedido especial"],
     "texto": "Lo personalizado es lo que más nos piden hoteles y bodas. El reto es que ocupa más horas del taller.",
     "dato": "Lo personalizado es lo más pedido por hoteles y bodas, pero usa más horas de taller"},
    {"id": "meta", "cat": "meta",
     "claves": ["meta", "objetivo", "junta", "lunes", "socio", "exito", "medir", "esperas", "quieres lograr",
                "cuanto recuperar", "plazo", "30 dias", "kpi", "indicador"],
     "texto": "En la junta del lunes quiero un plan que podamos revisar a los 30 días: qué vamos a hacer, cuánto "
              "cuesta y cómo vamos a saber si está funcionando. No espero milagros, pero sí señales claras.",
     "dato": "Carmen quiere revisar el plan a los 30 días con señales medibles"},
    {"id": "equipo", "cat": None,
     "claves": ["emplead", "artesan", "equipo", "trabajador", "despedir", "personal", "taller", "cuantos son"],
     "texto": "Somos 9 personas en el taller, casi todas artesanas con años de oficio. Despedir no es opción.",
     "dato": "El taller tiene 9 personas y despedir no es opción"},
    {"id": "presupuesto", "cat": None,
     "claves": ["presupuesto", "dinero", "invertir", "inversion", "cuanto tienes", "fondos", "recursos"],
     "texto": "__PRESUPUESTO__",
     "dato": None},
    {"id": "autenticidad", "cat": None,
     "claves": ["artesanal", "autentic", "hecho a mano", "certific", "denominacion", "origen", "sello", "tradicion", "calidad"],
     "texto": "Nuestro proceso es artesanal de principio a fin, pero el cliente no lo reconoce. Ojo: no tenemos un "
              "sello o certificación comprobada para presumir, así que no prometas eso en el plan.",
     "dato": "El proceso artesanal no es reconocido por el cliente; no hay sello comprobado"},
    {"id": "carpeta", "cat": None,
     "claves": ["datos", "archivo", "carpeta", "excel", "csv", "informacion", "numeros", "reporte", "registro"],
     "texto": "Te dejé una carpeta con tres archivos: ventas, clientes y costos. Ábrela; ahí está el detalle. "
              "Yo saqué el 28 % de mi reporte, pero no sé si mi sistema registra bien todo.",
     "dato": None},
]

RESPUESTAS_SOLUCION = [
    "Si yo supiera qué hacer, no te habría llamado. Pregúntame lo que necesites para armar tu propuesta.",
    "Eso quiero escucharlo de ti el lunes. ¿Qué información te falta para decidir?",
]
RESPUESTAS_GENERICAS = [
    "Mmm, eso no lo tengo tan claro. Puedo contarte de mis clientes, los canales de venta, los costos o lo que espero de la junta.",
    "No sé si te entendí. ¿Me preguntas por los clientes, por cómo vendemos o por los números del taller?",
    "Buena pregunta, pero ahí no tengo información. Quizá la carpeta de datos te ayude; o pregúntame por clientes, costos o canales.",
]
RESPUESTAS_SALUDO = ["¡Hola! Cuéntame, ¿qué necesitas saber del negocio?"]

PREGUNTAS_SUGERIDAS = [
    "¿Quiénes son sus principales clientes?",
    "¿Por qué cree que bajaron las ventas?",
    "¿Cómo venden por internet o redes?",
    "¿Qué productos dejan más margen?",
    "¿Qué espera lograr en la junta del lunes?",
]


def normalizar(s: str) -> str:
    s = quitar_tildes(s.lower())
    s = re.sub(r"[^a-z0-9ñ%$ ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _puntaje(texto: str, hecho: dict) -> int:
    return sum(1 for k in hecho["claves"] if k in texto)


def carmen_responder(pregunta: str, estado: dict) -> dict:
    """Motor por reglas de Carmen.

    `estado` es el dict del caso (se modifica): revelados (lista ids), turnos (int),
    giro (bool), presupuesto (int), log (lista).
    Devuelve {'texto', 'hechos': [ids], 'giro_ahora': bool}.
    """
    q = normalizar(pregunta)
    estado["turnos"] = estado.get("turnos", 0) + 1
    revelados = estado.setdefault("revelados", [])
    nuevos: list[str] = []
    partes: list[str] = []

    if re.search(r"\b(solucion|que hago|que hacer|respuesta correcta|que deberia|dime que)\b", q):
        partes.append(RESPUESTAS_SOLUCION[estado["turnos"] % len(RESPUESTAS_SOLUCION)])
    else:
        # «bajaron/cayeron» se interpreta como pregunta por causas → segmentos o restaurantes
        if re.search(r"\b(bajar|bajaron|cayeron|caida|cayo|baja|perdieron|por que)\b", q) and not any(
                _puntaje(q, h) for h in HECHOS):
            q = q + " cliente restaurant"
        candidatos = sorted(((_puntaje(q, h), i, h) for i, h in enumerate(HECHOS)), key=lambda x: (-x[0], x[1]))
        candidatos = [c for c in candidatos if c[0] > 0]
        # Preferir hechos no revelados; máximo 2 por turno para que el estudiante siga preguntando.
        no_rev = [c for c in candidatos if c[2]["id"] not in revelados]
        elegidos = (no_rev or candidatos)[:2]
        for _, _, h in elegidos:
            txt = h["texto"]
            if txt == "__PRESUPUESTO__":
                txt = (f"Para el plan tengo ${estado.get('presupuesto', PRESUPUESTO_INICIAL):,} MXN. "
                       "No es dinero de sobra: cada peso tiene que tener una razón.")
            elif h["id"] in revelados:
                txt = "Como te comenté: " + txt
            partes.append(txt)
            if h["id"] not in revelados:
                revelados.append(h["id"])
                nuevos.append(h["id"])
        if not partes:
            if re.search(r"\b(hola|buen dia|buenos dias|buenas tardes|que tal|mucho gusto)\b", q):
                partes.append(RESPUESTAS_SALUDO[0])
            else:
                partes.append(RESPUESTAS_GENERICAS[estado["turnos"] % len(RESPUESTAS_GENERICAS)])

    giro_ahora = False
    if estado["turnos"] == TURNO_GIRO and not estado.get("giro"):
        estado["giro"] = True
        estado["presupuesto"] = PRESUPUESTO_RECORTE
        giro_ahora = True
        partes.append(CARMEN_RECORTE)

    texto = " ".join(partes)
    estado.setdefault("log", []).append({"turno": estado["turnos"], "pregunta": pregunta[:500],
                                         "respuesta": texto, "hechos_nuevos": nuevos})
    return {"texto": texto, "hechos": nuevos, "giro_ahora": giro_ahora}


def categorias_descubiertas(revelados: list[str]) -> list[str]:
    cats = {h["cat"] for h in HECHOS if h["id"] in revelados and h["cat"]}
    return [c for c in CATEGORIAS_INVESTIGACION if c in cats]


# ---------------------------------------------------------------------------
# Datos citables para la propuesta (solo los que el estudiante ya descubrió)
# ---------------------------------------------------------------------------
HALLAZGOS_DATOS = {
    "var_total": "Ventas totales: −28 % de T2 a T3 (tras quitar el registro duplicado)",
    "seg_restaurantes": "Restaurantes: −38.1 %, la mayor caída por segmento",
    "anomalia": "El reporte original incluía un registro duplicado (V-0072)",
    "margen_personalizada": "Pieza personalizada: margen bruto de 55 % (costos.csv)",
    "clientes_restaurantes": "Restaurantes activos: de 14 a 11 clientes (clientes.csv)",
    "turistas": "Turistas en tienda: de 1,250 a 800 tickets (clientes.csv)",
}


def datos_citables(revelados: list[str], hallazgos: list[str]) -> list[str]:
    out = [h["dato"] for h in HECHOS if h["id"] in revelados and h["dato"]]
    out += [HALLAZGOS_DATOS[k] for k in hallazgos if k in HALLAZGOS_DATOS]
    return out


# ---------------------------------------------------------------------------
# Proyectos del presupuestador (costos = SUPUESTOS del caso)
# ---------------------------------------------------------------------------
PROYECTOS = [
    {"id": "digital", "nombre": "Campaña digital y catálogo en Instagram",
     "desc": "Fotos del proceso artesanal, catálogo con precios y publicaciones semanales.",
     "supuesto": "Supuesto del caso: un mes de contenido + pauta cuesta entre $10,000 y $50,000."},
    {"id": "alianzas", "nombre": "Alianzas con hoteles y restaurantes",
     "desc": "Kit de muestras, visitas comerciales y un paquete de reposición garantizada.",
     "supuesto": "Supuesto del caso: muestras y visitas entre $15,000 y $70,000."},
    {"id": "producto", "nombre": "Mejora de producto y entregas",
     "desc": "Inventario de piezas base para reponer en 2 semanas y una línea resistente para cocinas.",
     "supuesto": "Supuesto del caso: inventario base entre $20,000 y $90,000."},
]


# ---------------------------------------------------------------------------
# Microcasos A y B (demostración independiente) · preguntas comparables
# ---------------------------------------------------------------------------
MICROCASOS = {
    "A": {
        "titulo": "Misión relámpago: Panadería La Espiga",
        "historia": "La Espiga (empresa ficticia) tiene tres sucursales. La dueña te muestra las ventas de enero y "
                    "febrero y te pide una lectura rápida antes de su reunión.",
        "csv": "evaluacion_A.csv",
        "indicadores": [
            ("clientes_ticket", "Número de clientes atendidos y ticket promedio por sucursal", True),
            ("dias_semana", "Ventas por día de la semana en cada sucursal", True),
            ("seguidores", "Cantidad total de seguidores de la marca en redes", False),
            ("inflacion_otro", "Inflación anual de otro país", False),
        ],
    },
    "B": {
        "titulo": "Demostración final: Librería Mirador",
        "historia": "Mirador (empresa ficticia) vende tres categorías. El gerente te comparte las ventas de dos "
                    "trimestres y quiere tu recomendación por escrito.",
        "csv": "evaluacion_B.csv",
        "indicadores": [
            ("compradores_ticket", "Número de compradores y ticket promedio por categoría", True),
            ("inventario", "Inventario disponible y rotación por categoría", True),
            ("likes", "Número de «me gusta» de la última publicación", False),
            ("tipo_cambio", "Tipo de cambio peso-yen", False),
        ],
    },
}
