"""STARWISE · evidencia.py

Registro de intentos para la prueba con usuarios. En Streamlit Community Cloud el
sistema de archivos es efímero: la evidencia REAL es el JSON que cada persona
descarga. El panel del equipo importa esos JSON localmente (sin sincronización
en tiempo real), elimina duplicados por attempt_id y exporta un CSV consolidado.
Los registros `synthetic_test` (QA) se excluyen de las métricas de usuarios reales.
"""
from __future__ import annotations

import copy
import json
import uuid
from datetime import datetime, timezone

import pandas as pd

import evaluacion

SCHEMA_VERSION = "starwise-evidencia-1.0"
APP_VERSION = "2.0.0"
TIPOS = {"interna": "Prueba interna del equipo",
         "externa_confirmada": "Persona externa (declarada por facilitador)",
         "synthetic_test": "Registro sintético de QA (excluido de métricas)"}

LIMITACIONES = [
    "Simulación académica con empresa y datos ficticios; no es práctica laboral formal ni experiencia laboral.",
    "No es certificación oficial ni garantiza contratación o ingresos.",
    "Rúbrica sin validación psicométrica; los textos abiertos requieren revisión humana.",
    "La autoeficacia es una opinión subjetiva y no mide aprendizaje.",
    "La comparación A/B describe un cambio observado entre dos ejercicios, no una mejora causal.",
]


def ahora_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def nuevo_intento() -> dict:
    return {"attempt_id": str(uuid.uuid4()), "creado_en": ahora_iso(), "schema_version": SCHEMA_VERSION}


def construir_registro(S: dict, etiqueta_tutor: str) -> dict:
    """S es el estado de la app (dict serializable). No incluye secretos."""
    sim = S.get("sim", {})
    A, B = S.get("A", {}), S.get("B", {})
    reg = {
        "schema_version": SCHEMA_VERSION,
        "app_version": APP_VERSION,
        "rubric_version": evaluacion.RUBRIC_VERSION,
        "attempt_id": S["intento"]["attempt_id"],
        "creado_en": S["intento"]["creado_en"],
        "actualizado_en": ahora_iso(),
        "tipo_registro": S.get("tipo_registro", "interna"),
        "facilitador_declaro_externa": S.get("facilitador_declaro_externa", False),
        "participante": copy.deepcopy(S.get("perfil", {})),
        "ruta": S.get("ruta"),
        "expectativa_rol": S.get("expectativa_rol", ""),
        "cambio_interes": copy.deepcopy(S.get("cambio_interes", {})),
        "autoeficacia": {"antes": S.get("autoeficacia_antes"), "despues": S.get("autoeficacia_despues"),
                         "nota": "Opinión subjetiva (1–5); no mide competencia ni aprendizaje."},
        "diagnostico_A": copy.deepcopy(A),
        "demostracion_B": copy.deepcopy(B),
        "comparacion_AB": evaluacion.comparar_AB(A.get("resultado"), B.get("resultado")),
        "practica": {k: copy.deepcopy(sim.get(k)) for k in
                     ("turnos", "revelados", "giro", "presupuesto", "log", "archivos_abiertos", "filtros_usados",
                      "hallazgos", "planes", "ajuste_justificacion", "propuesta", "defensa")},
        "evaluacion_practica": evaluacion.evaluar_simulacion(sim) if sim else None,
        "apoyo_tutor": {"modo": etiqueta_tutor, "pistas_por_mision": copy.deepcopy(S.get("pistas", {})),
                        "mensajes_tutor": len(S.get("tutor_log", [])), "registro": copy.deepcopy(S.get("tutor_log", [])),
                        "nota": "Usar pistas no penaliza; solo se reporta el nivel de apoyo."},
        "encuesta": copy.deepcopy(S.get("encuesta", {})),
        "plan_siguiente_paso": copy.deepcopy(S.get("plan_accion", [])),
        "etapa_final": S.get("escena"),
        "limitaciones": LIMITACIONES,
    }
    return reg


def a_json(reg: dict) -> str:
    return json.dumps(reg, ensure_ascii=False, indent=2, default=str)


def leer_registros(archivos: list[tuple[str, bytes]]) -> tuple[list[dict], list[str]]:
    registros, errores = [], []
    for nombre, raw in archivos:
        try:
            data = json.loads(raw.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            errores.append(f"{nombre}: no es un JSON válido.")
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if not isinstance(it, dict) or not str(it.get("schema_version", "")).startswith("starwise-evidencia-"):
                errores.append(f"{nombre}: no es un registro de evidencia STARWISE.")
                continue
            if not it.get("attempt_id"):
                errores.append(f"{nombre}: registro sin attempt_id.")
                continue
            registros.append(it)
    return registros, errores


def deduplicar(registros: list[dict]) -> list[dict]:
    """Un registro por attempt_id: se conserva el más reciente (actualizado_en)."""
    por_id: dict[str, dict] = {}
    for r in registros:
        k = r["attempt_id"]
        if k not in por_id or str(r.get("actualizado_en", "")) > str(por_id[k].get("actualizado_en", "")):
            por_id[k] = r
    return list(por_id.values())


def aplanar(r: dict) -> dict:
    A = (r.get("diagnostico_A") or {}).get("resultado") or {}
    B = (r.get("demostracion_B") or {}).get("resultado") or {}
    enc = r.get("encuesta") or {}
    part = r.get("participante") or {}
    pistas = (r.get("apoyo_tutor") or {}).get("pistas_por_mision") or {}
    return {
        "attempt_id": r.get("attempt_id"), "tipo_registro": r.get("tipo_registro"),
        "externa_confirmada": r.get("tipo_registro") == "externa_confirmada",
        "synthetic_test": r.get("tipo_registro") == "synthetic_test",
        "creado_en": r.get("creado_en"), "app_version": r.get("app_version"), "rubric_version": r.get("rubric_version"),
        "carrera": part.get("carrera", ""), "intereses": "; ".join(part.get("intereses", []) or []),
        "ruta": r.get("ruta"),
        "A_logrados": A.get("logrados"), "B_logrados": B.get("logrados"), "AB_total_criterios": A.get("total_objetivos"),
        "A_duracion_s": (r.get("diagnostico_A") or {}).get("duracion_s"),
        "B_duracion_s": (r.get("demostracion_B") or {}).get("duracion_s"),
        "pistas_usadas": sum(int(v) for v in pistas.values()) if pistas else 0,
        "etapa_final": r.get("etapa_final"),
        "autoeficacia_antes": (r.get("autoeficacia") or {}).get("antes"),
        "autoeficacia_despues": (r.get("autoeficacia") or {}).get("despues"),
        "relevancia_1a5": enc.get("relevancia"), "claridad_1a5": enc.get("claridad"),
        "usaria_portafolio_cv": enc.get("usaria_cv"), "comentario": enc.get("comentario", ""),
    }


def consolidar(registros: list[dict]) -> pd.DataFrame:
    filas = [aplanar(r) for r in deduplicar(registros)]
    return pd.DataFrame(filas)


def metricas(df: pd.DataFrame) -> dict:
    """Métricas descriptivas SOLO con registros no sintéticos."""
    if df is None or df.empty:
        return {"n_total": 0, "n_reales": 0}
    reales = df[~df["synthetic_test"]]
    def prom(col):
        s = pd.to_numeric(reales[col], errors="coerce").dropna()
        return round(float(s.mean()), 2) if len(s) else None
    return {
        "n_total": int(len(df)), "n_sinteticos_excluidos": int(df["synthetic_test"].sum()),
        "n_reales": int(len(reales)), "n_externas_confirmadas": int(reales["externa_confirmada"].sum()),
        "n_completaron_B": int(reales["B_logrados"].notna().sum()),
        "relevancia_promedio": prom("relevancia_1a5"), "claridad_promedio": prom("claridad_1a5"),
        "autoeficacia_antes_prom": prom("autoeficacia_antes"), "autoeficacia_despues_prom": prom("autoeficacia_despues"),
    }


def registro_qa_sintetico() -> dict:
    """Registro de QA marcado `synthetic_test`. Nunca cuenta como usuario real."""
    intento = nuevo_intento()
    S = {"intento": intento, "tipo_registro": "synthetic_test",
         "perfil": {"alias": "QA-sintetico", "carrera": "QA", "intereses": ["Datos y finanzas"]},
         "ruta": "estrategia", "escena": "qa", "sim": {}, "A": {}, "B": {}, "encuesta": {"comentario": "Registro de QA"}}
    reg = construir_registro(S, "QA")
    reg["evaluacion_practica"] = None
    return reg
