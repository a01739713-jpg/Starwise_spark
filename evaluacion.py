"""STARWISE · evaluacion.py

Evaluación DETERMINISTA y separada del tutor. Principios:
- Solo criterios conductuales definidos de antemano y observables en la simulación.
- Nada de proxies débiles: no se premia la longitud del texto, la rapidez,
  el número de acciones, el uso de pocas pistas ni palabras como «porque».
- El texto abierto no se califica automáticamente: «Requiere revisión humana».
- Sin validez psicométrica ni capacidad predictiva de contratación.
- La IA no participa en ningún resultado de este módulo.
"""
from __future__ import annotations

import re

import pandas as pd

import casos
import datos

RUBRIC_VERSION = "starwise-rubrica-2026.11-r1"
TOLERANCIA_PP = 0.5

LOGRADO, NO_OBSERVADO, REVISION = "logrado", "no_observado", "revision"
ETIQUETA_CRITERIO = {LOGRADO: "Observado", NO_OBSERVADO: "No observado", REVISION: "Requiere revisión humana"}
NIVELES = ("Inicial", "En desarrollo", "Aplicado en el caso", "Requiere revisión")


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def parsear_numero(texto: object) -> float | None:
    """Acepta '-12.9', '−12,9 %', '12.9%'. Devuelve None si no es número."""
    if texto is None:
        return None
    if isinstance(texto, (int, float)):
        return float(texto)
    t = str(texto).strip().replace("−", "-").replace("–", "-").replace("%", "").replace(" ", "")
    if re.fullmatch(r"-?\d+,\d+", t):
        t = t.replace(",", ".")
    t = t.replace(",", "")
    try:
        return float(t)
    except ValueError:
        return None


def numeros_en_texto(texto: str) -> list[float]:
    """Extrae cifras de un texto libre: 63,000 · 63 mil · 30% · -12.9 · $72,800."""
    out = []
    for m in re.finditer(r"(-|−)?\$?\s?(\d{1,3}(?:,\d{3})+|\d+(?:[.,]\d+)?)\s*(mil\b|k\b)?", texto.lower()):
        num = m.group(2)
        if re.fullmatch(r"\d{1,3}(?:,\d{3})+", num):
            v = float(num.replace(",", ""))
        else:
            v = float(num.replace(",", "."))
        if m.group(3):
            v *= 1000
        out.append(-v if m.group(1) else v)
    return out


def contiene_cifra_del_caso(texto: str, cifras: list[float]) -> bool:
    for n in numeros_en_texto(texto or ""):
        for c in cifras:
            c = abs(c)
            if c <= 100 and abs(abs(n) - c) <= 0.6:
                return True
            if c > 100 and abs(abs(n) - c) <= max(1.0, c * 0.01):
                return True
    return False


def contar_frases(texto: str) -> int:
    return len([f for f in re.split(r"[.!?]+", texto or "") if f.strip()])


def nivel(criterios: list[dict]) -> str:
    objetivos = [c for c in criterios if c["estado"] != REVISION]
    if not objetivos:
        return "Requiere revisión"
    r = sum(c["estado"] == LOGRADO for c in objetivos) / len(objetivos)
    if r == 1:
        return "Aplicado en el caso"
    if r >= 0.34:
        return "En desarrollo"
    return "Inicial"


def _c(cid: str, desc: str, estado: str, evidencia: str) -> dict:
    return {"id": cid, "descripcion": desc, "estado": estado, "etiqueta": ETIQUETA_CRITERIO[estado], "evidencia": evidencia}


# ---------------------------------------------------------------------------
# Microcasos A y B (demostración independiente)
# ---------------------------------------------------------------------------
SUBCRITERIOS_MICRO = {
    "calculo": "Calculó la variación porcentual total (±0.5 puntos)",
    "segmento": "Señaló el segmento con mayor caída",
    "indicador": "Eligió un indicador pertinente para investigar",
    "cifra": "Su justificación usa al menos una cifra del caso",
    "texto": "Calidad de la justificación",
}


def evaluar_micro(clave: str, df: pd.DataFrame, resp: dict) -> dict:
    res = datos.micro_resumen(df)
    correcta = res["variacion_total_pct"]
    crit = []

    v = parsear_numero(resp.get("variacion_pct"))
    if v is None:
        crit.append(_c("calculo", SUBCRITERIOS_MICRO["calculo"], NO_OBSERVADO, "No se registró un número."))
    elif abs(v - correcta) <= TOLERANCIA_PP:
        crit.append(_c("calculo", SUBCRITERIOS_MICRO["calculo"], LOGRADO, f"Respondió {v:.1f} %."))
    elif abs(-v - correcta) <= TOLERANCIA_PP:
        crit.append(_c("calculo", SUBCRITERIOS_MICRO["calculo"], NO_OBSERVADO,
                       f"Respondió {v:.1f} %: magnitud correcta con signo invertido."))
    else:
        crit.append(_c("calculo", SUBCRITERIOS_MICRO["calculo"], NO_OBSERVADO, f"Respondió {v:.1f} %."))

    seg = resp.get("segmento")
    crit.append(_c("segmento", SUBCRITERIOS_MICRO["segmento"],
                   LOGRADO if seg == res["segmento_mayor_caida"] else NO_OBSERVADO,
                   f"Eligió «{seg}»." if seg else "Sin selección."))

    opciones = {i: ok for i, _, ok in casos.MICROCASOS[clave]["indicadores"]}
    ind = resp.get("indicador")
    crit.append(_c("indicador", SUBCRITERIOS_MICRO["indicador"],
                   LOGRADO if opciones.get(ind) else NO_OBSERVADO,
                   "Indicador relacionado con la caída." if opciones.get(ind) else "Indicador no relacionado o sin selección."))

    texto = (resp.get("justificacion") or "").strip()
    cifras = list(df["ventas_periodo_1_mxn"]) + list(df["ventas_periodo_2_mxn"]) + [res["total_1"], res["total_2"], correcta]
    cifras += list(res["variacion_segmento"].values())
    crit.append(_c("cifra", SUBCRITERIOS_MICRO["cifra"],
                   LOGRADO if contiene_cifra_del_caso(texto, cifras) else NO_OBSERVADO,
                   "Incluye una cifra que aparece en la tabla o se deriva de ella." if contiene_cifra_del_caso(texto, cifras)
                   else "No se encontró una cifra del caso."))
    crit.append(_c("texto", SUBCRITERIOS_MICRO["texto"], REVISION if texto else NO_OBSERVADO,
                   "Texto pendiente de revisión humana; no se califica automáticamente." if texto else "Sin justificación."))

    objetivos = [c for c in crit if c["estado"] != REVISION]
    return {"clave": clave, "rubric_version": RUBRIC_VERSION, "criterios": crit,
            "logrados": sum(c["estado"] == LOGRADO for c in objetivos), "total_objetivos": len(objetivos),
            "nivel": nivel(crit), "frases_justificacion": contar_frases(texto)}


def comparar_AB(a: dict | None, b: dict | None) -> dict | None:
    """Solo si existen ambas. Describe cambio OBSERVADO por subcriterio; no afirma causalidad."""
    if not a or not b:
        return None
    ea = {c["id"]: c["estado"] for c in a["criterios"]}
    eb = {c["id"]: c["estado"] for c in b["criterios"]}
    filas = []
    for cid, desc in SUBCRITERIOS_MICRO.items():
        x, y = ea.get(cid), eb.get(cid)
        if REVISION in (x, y):
            cambio = "Pendiente de revisión humana"
        elif x == LOGRADO and y == LOGRADO:
            cambio = "Observado en A y en B"
        elif y == LOGRADO:
            cambio = "Observado en B, no en A"
        elif x == LOGRADO:
            cambio = "Observado en A, no en B"
        else:
            cambio = "No observado en ninguna"
        filas.append({"id": cid, "criterio": desc, "A": ETIQUETA_CRITERIO.get(x, "—"), "B": ETIQUETA_CRITERIO.get(y, "—"),
                      "cambio": cambio})
    return {"filas": filas, "logrados_A": a["logrados"], "logrados_B": b["logrados"], "total": a["total_objetivos"],
            "nota": "Cambio observado entre dos ejercicios distintos. No demuestra que la práctica lo haya causado."}


# ---------------------------------------------------------------------------
# Práctica asistida en Talavera Viva (cinco áreas)
# ---------------------------------------------------------------------------
def plan_pre_y_post(planes: list[dict]) -> tuple[dict | None, dict | None]:
    pre = [p for p in planes if not p.get("giro")]
    post = [p for p in planes if p.get("giro")]
    return (pre[-1] if pre else None), (post[-1] if post else None)


def evaluar_simulacion(sim: dict) -> dict:
    revelados = sim.get("revelados", [])
    cats = casos.categorias_descubiertas(revelados)
    areas = {}

    inv = [_c(f"inv_{k}", d, LOGRADO if k in cats else NO_OBSERVADO,
              "Hecho descubierto en la conversación." if k in cats else "No preguntó por este tema.")
           for k, d in casos.CATEGORIAS_INVESTIGACION.items()]
    areas["investigacion"] = {"nombre": "Investigación y preguntas relevantes", "criterios": inv}

    h = sim.get("hallazgos", {})
    ventas = datos.cargar_sintetico("ventas_talavera.csv")
    dup = datos.id_duplicado(ventas)
    correcta = datos.resumen_trimestres(datos.limpiar_duplicados(ventas))["variacion_pct"]
    v = parsear_numero(h.get("variacion_reportada"))
    abrio = "ventas" in sim.get("archivos_abiertos", [])
    por_seg = datos.variacion_por(datos.limpiar_duplicados(ventas), "segmento").sort_values("variación_%")
    seg_correcto = por_seg.iloc[0]["segmento"]
    an = [
        _c("an_descenso", "Identificó el descenso de ventas en los datos", LOGRADO if (abrio and v is not None and v < 0) else NO_OBSERVADO,
           "Abrió ventas.csv y reportó una variación negativa." if (abrio and v is not None and v < 0) else "Sin registro."),
        _c("an_variacion", "Calculó la variación total correctamente con datos limpios (±0.5 pp)",
           LOGRADO if (v is not None and abs(v - correcta) <= TOLERANCIA_PP) else NO_OBSERVADO,
           f"Reportó {v:.1f} %." if v is not None else "Sin registro."),
        _c("an_anomalia", "Señaló la anomalía del archivo (registro duplicado)",
           LOGRADO if (h.get("anomalia_id") in dup and h.get("anomalia_tipo") == "Registro duplicado") else NO_OBSERVADO,
           f"Señaló {h.get('anomalia_id')} como «{h.get('anomalia_tipo')}»." if h.get("anomalia_id") else "Sin registro."),
        _c("an_segmento", "Identificó el segmento con mayor caída",
           LOGRADO if h.get("segmento") == seg_correcto else NO_OBSERVADO,
           f"Eligió «{h.get('segmento')}»." if h.get("segmento") else "Sin registro."),
    ]
    areas["analisis"] = {"nombre": "Análisis de datos", "criterios": an}

    pre, post = plan_pre_y_post(sim.get("planes", []))
    final = post or pre
    pres = sim.get("presupuesto", casos.PRESUPUESTO_INICIAL)
    prop = sim.get("propuesta", {})
    just = (prop.get("justificacion_prioridad") or "").strip()
    pr = [
        _c("pr_dentro", "Su plan final no excede el presupuesto vigente",
           LOGRADO if (final and 0 < final["total"] <= pres) else NO_OBSERVADO,
           f"Plan final de ${final['total']:,} con presupuesto de ${pres:,}." if final else "No guardó un plan."),
        _c("pr_prioridad", "Eligió una acción prioritaria para el segmento que decidió atender",
           LOGRADO if (prop.get("accion_prioritaria") and prop.get("segmento_prioritario")) else NO_OBSERVADO,
           f"Prioridad: {prop.get('accion_prioritaria')} → {prop.get('segmento_prioritario')}." if prop.get("accion_prioritaria") else "Sin registro."),
        _c("pr_justifica", "Justificó la prioridad considerando la restricción", REVISION if just else NO_OBSERVADO,
           "Texto pendiente de revisión humana." if just else "Sin justificación."),
    ]
    areas["priorizacion"] = {"nombre": "Estructuración y priorización", "criterios": pr}

    citados = prop.get("datos_citados", [])
    acciones = [a for a in prop.get("acciones", []) if (a or "").strip()]
    co = [
        _c("co_problema", "Explicitó el problema con al menos 2 datos del caso",
           LOGRADO if ((prop.get("diagnostico") or "").strip() and len(citados) >= 2) else NO_OBSERVADO,
           f"Citó {len(citados)} dato(s) del caso." if prop else "Sin propuesta."),
        _c("co_acciones", "Describió tres acciones concretas", LOGRADO if len(acciones) == 3 else NO_OBSERVADO,
           f"{len(acciones)} acción(es) descrita(s)."),
        _c("co_metrica", "Definió un indicador con meta numérica a 30 días",
           LOGRADO if ((prop.get("kpi") or "").strip() and numeros_en_texto(prop.get("meta") or "")) else NO_OBSERVADO,
           f"Indicador: {prop.get('kpi') or '—'} · Meta: {prop.get('meta') or '—'}"),
        _c("co_texto", "Claridad de la propuesta y de la defensa ante Carmen",
           REVISION if (prop.get("solucion") or "").strip() else NO_OBSERVADO,
           "Texto pendiente de revisión humana." if (prop.get("solucion") or "").strip() else "Sin propuesta."),
    ]
    areas["comunicacion"] = {"nombre": "Comunicación de propuestas", "criterios": co}

    giro = sim.get("giro", False)
    aj = (sim.get("ajuste_justificacion") or "").strip()
    if not giro:
        ad = [_c("ad_dentro", "Replaneó dentro del nuevo presupuesto", NO_OBSERVADO, "El recorte aún no ocurrió.")]
    else:
        cambio = bool(pre and post and pre["montos"] != post["montos"])
        ad = [
            _c("ad_edito", "Editó su plan después del recorte", LOGRADO if cambio else NO_OBSERVADO,
               "Modificó montos respecto a su plan previo." if cambio else
               ("No había un plan previo al recorte para comparar." if not pre else "No se registró cambio.")),
            _c("ad_dentro", "Replaneó dentro del nuevo presupuesto ($60,000)",
               LOGRADO if (post and 0 < post["total"] <= casos.PRESUPUESTO_RECORTE) else NO_OBSERVADO,
               f"Plan posterior de ${post['total']:,}." if post else "No guardó plan después del recorte."),
            _c("ad_explica", "Explicó qué sacrificó y por qué", REVISION if aj else NO_OBSERVADO,
               "Texto pendiente de revisión humana." if aj else "Sin explicación."),
        ]
    areas["adaptacion"] = {"nombre": "Adaptación al presupuesto", "criterios": ad}

    for a in areas.values():
        a["nivel"] = nivel(a["criterios"])
        obj = [c for c in a["criterios"] if c["estado"] != REVISION]
        a["logrados"], a["total_objetivos"] = sum(c["estado"] == LOGRADO for c in obj), len(obj)
    return {"rubric_version": RUBRIC_VERSION, "areas": areas, "conductas": conductas_observadas(sim)}


def conductas_observadas(sim: dict) -> list[str]:
    """Hechos documentados de esta simulación, no rasgos psicológicos."""
    out = []
    if "segmentos" in sim.get("revelados", []) or "restaurantes" in sim.get("revelados", []):
        out.append("Preguntó por los clientes antes de recomendar.")
    if len(set(sim.get("archivos_abiertos", []))) == 3:
        out.append("Abrió los tres archivos de la carpeta de datos.")
    if sim.get("filtros_usados"):
        out.append("Usó filtros para examinar los datos por partes.")
    h = sim.get("hallazgos", {})
    if h.get("anomalia_tipo") == "Registro duplicado" and h.get("anomalia_id"):
        out.append("Revisó la calidad de los datos y señaló un posible duplicado.")
    pre, post = plan_pre_y_post(sim.get("planes", []))
    if pre and post and pre["montos"] != post["montos"]:
        out.append("Ajustó su presupuesto cuando cambió la restricción.")
    return out


def insignias(sim: dict, A: dict | None, B: dict | None) -> list[dict]:
    ev = evaluar_simulacion(sim)["areas"]
    def ok(area, cid):
        return any(c["id"] == cid and c["estado"] == LOGRADO for c in ev[area]["criterios"])
    lista = [
        ("Buenas preguntas", "Descubriste al menos 3 temas clave con Carmen.", ev["investigacion"]["logrados"] >= 3),
        ("Detective de datos", "Encontraste el registro duplicado.", ok("analisis", "an_anomalia")),
        ("Presupuesto bajo control", "Replaneaste dentro de $60,000.", ok("adaptacion", "ad_dentro")),
        ("Propuesta con datos", "Respaldaste tu diagnóstico con 2 o más datos.", ok("comunicacion", "co_problema")),
        ("Por tu cuenta", "Completaste las dos demostraciones sin tutor.", bool(A and B)),
    ]
    return [{"nombre": n, "desc": d, "obtenida": bool(o)} for n, d, o in lista]
