"""STARWISE · datos.py

Dos mundos de datos que NUNCA se mezclan:

1. Repositorio oficial del reto (data/repositorio.csv): datos de CONTEXTO.
   Se leen con validación de encabezados y encoding, y cada indicador usado en
   la interfaz se busca por su etiqueta EXACTA (sin fuzzy matching ni
   `contains()`), se compara con el valor esperado y, si no coincide, se marca
   «requiere revisión» y no se muestra como dato.

2. Datasets de simulación (100 % sintéticos): caso Talavera Viva y microcasos
   A/B. Se generan de forma determinista y reproducen las cifras narrativas
   (p. ej. la caída de 28 % que menciona Carmen).
"""
from __future__ import annotations

import csv
import io
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
REPO_PATH = DATA_DIR / "repositorio.csv"

COLUMNAS_REPO = ["Bloque", "Tabla", "Dato", "Valor", "Comparación o nota", "Fuente", "Enlace"]

# Dominios que consideramos fuente original/institucional. Cualquier otro enlace
# (prensa, blogs, agregadores) se etiqueta como «referencia secundaria».
DOMINIOS_ORIGINALES = ("sep.gob.mx", "inegi.org.mx", "imco.org.mx", "uvm.mx", "gob.mx", "anuies.mx")


# ---------------------------------------------------------------------------
# Normalización
# ---------------------------------------------------------------------------
def normalizar_texto(s: object) -> str:
    """NFC, espacios duros a normales, colapsa espacios. NO quita tildes."""
    if s is None:
        return ""
    t = unicodedata.normalize("NFC", str(s)).replace(" ", " ").replace("﻿", "")
    return re.sub(r"\s+", " ", t).strip()


def normalizar_valor(s: object) -> str:
    """Para comparar valores: sin espacios, sin «≈»/«~», signo menos unificado."""
    t = normalizar_texto(s).lower()
    for ch in ("≈", "~", "aprox.", "aprox", " "):
        t = t.replace(ch, "")
    return t.replace("−", "-").replace("–", "-")


def quitar_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


# ---------------------------------------------------------------------------
# Indicadores del repositorio que la app puede usar (diccionario EXPLÍCITO)
# ---------------------------------------------------------------------------
INDICADORES: dict[str, dict] = {
    "primer_salario_10k": {
        "dato": "Egresados cuyo primer salario fue de hasta $10,000 al mes (ENE 2025)",
        "valor_esperado": "69.5%",
        "bloque_esperado": "03",
        "titulo": "Primer salario de hasta $10,000 al mes",
        "poblacion": "Personas egresadas que respondieron la Encuesta Nacional de Egresados (ENE) 2025 de la UVM.",
        "anio": "2025",
        "limitacion": (
            "Encuesta no probabilística: describe a quienes respondieron, no a todas las personas egresadas. "
            "No es el salario típico de una carrera ni una predicción de tu ingreso."
        ),
        "uso": "Contexto del primer empleo (pantalla «Tu siguiente paso»).",
    },
    "sin_prestaciones": {
        "dato": "Egresados sin prestaciones en su primer empleo / en su empleo actual (ENE 2025)",
        "valor_esperado": "30.4% / 16.3%",
        "titulo": "Sin prestaciones en su primer empleo",
        "mostrar_primer_valor": True,
        "poblacion": "Personas egresadas que respondieron la ENE 2025 de la UVM (primer empleo).",
        "anio": "2025",
        "limitacion": "Encuesta no probabilística. El 16.3 % corresponde al empleo actual, no al primero.",
        "uso": "«¿Qué hace digno un primer empleo?»",
    },
    "habilidades_clave": {
        "dato": "Habilidades que consideran clave para un mejor empleo: tecnológicas / segunda lengua (ENE 2025)",
        "valor_esperado": "47% / 46.8%",
        "titulo": "Habilidades que consideran clave: tecnológicas / segunda lengua",
        "poblacion": "Personas egresadas que respondieron la ENE 2025 de la UVM.",
        "anio": "2025",
        "limitacion": "Es una percepción de quienes respondieron, no evidencia de que una capacitación funcione.",
        "uso": "Solo si eliges interés en herramientas digitales/datos.",
    },
    "ingreso_promedio": {
        "dato": "Ingreso mensual promedio (pesos de 2026)",
        "valor_esperado": "$17,795",
        "titulo": "Ingreso mensual promedio de profesionistas",
        "poblacion": "Profesionistas en México, todas las carreras, edades y experiencias.",
        "anio": "2026",
        "limitacion": "Promedio general. NO es salario inicial ni salario de ninguna ruta de este juego.",
        "uso": "Solo en «Contexto nacional» de Metodología.",
    },
    "costo_publica": {
        "dato": "Costo directo en pública",
        "valor_esperado": "≈ $55,296",
        "titulo": "Costo directo ilustrativo, universidad pública (4 años)",
        "poblacion": "Referencia ilustrativa del repositorio del reto.",
        "anio": "s. f.",
        "limitacion": "Ilustrativo y con fuentes indirectas; no es el costo de tu universidad.",
        "uso": "Solo en la comparación con la Ruta Base (Metodología).",
    },
    "costo_privada": {
        "dato": "Costo directo en privada",
        "valor_esperado": "≈ $195,608",
        "titulo": "Costo directo ilustrativo, universidad privada (4 años)",
        "poblacion": "Referencia ilustrativa del repositorio del reto.",
        "anio": "s. f.",
        "limitacion": "Ilustrativo y con fuentes indirectas; no es el costo de tu universidad.",
        "uso": "Solo en la comparación con la Ruta Base (Metodología).",
    },
    "finanzas_ingreso": {
        "dato": "3. Finanzas, banca y seguros",
        "valor_esperado": "$27,290",
        "titulo": "Ingreso promedio del campo Finanzas, banca y seguros",
        "poblacion": "Campo de formación general, todas las edades y experiencias.",
        "anio": "s. f.",
        "limitacion": "NO es salario inicial ni de analista junior. Se registra pero la ruta financiera no está habilitada.",
        "uso": "No se muestra en esta versión.",
    },
}


# ---------------------------------------------------------------------------
# Lectura del repositorio oficial
# ---------------------------------------------------------------------------
def _decodificar(raw: bytes) -> tuple[str, str]:
    for enc in ("utf-8-sig", "utf-8"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    try:
        return raw.decode("cp1252"), "cp1252"
    except UnicodeDecodeError:
        return raw.decode("latin-1"), "latin-1"


def leer_repositorio(fuente: bytes | str | Path | None = None) -> dict:
    """Lee y valida el CSV del repositorio. Nunca inventa filas.

    Devuelve dict con: estado ('ok' | 'ausente' | 'encabezados_invalidos' |
    'vacio' | 'error'), mensaje, df (o None), encoding, separador, origen.
    """
    origen = "archivo cargado en esta sesión"
    if fuente is None:
        fuente = REPO_PATH
    if isinstance(fuente, (str, Path)):
        p = Path(fuente)
        origen = str(p.relative_to(BASE)) if p.is_absolute() and BASE in p.parents else str(p)
        if not p.exists():
            return {"estado": "ausente", "df": None, "origen": origen,
                    "mensaje": "No se encontró data/repositorio.csv. Colócalo en la carpeta data/ "
                               "o cárgalo desde Metodología → Fuentes."}
        raw = p.read_bytes()
    else:
        raw = bytes(fuente)

    if not raw.strip():
        return {"estado": "vacio", "df": None, "origen": origen, "mensaje": "El archivo está vacío."}

    texto, enc = _decodificar(raw)
    muestra = texto[:4096]
    try:
        sep = csv.Sniffer().sniff(muestra, delimiters=",;\t|").delimiter
    except csv.Error:
        sep = ","
    try:
        df = pd.read_csv(io.StringIO(texto), sep=sep, dtype=str, keep_default_na=False)
    except Exception as exc:  # noqa: BLE001
        return {"estado": "error", "df": None, "origen": origen, "encoding": enc,
                "mensaje": f"No se pudo interpretar el CSV ({type(exc).__name__})."}

    columnas = [normalizar_texto(c) for c in df.columns]
    df.columns = columnas
    faltan = [c for c in COLUMNAS_REPO if c not in columnas]
    if faltan:
        return {"estado": "encabezados_invalidos", "df": None, "origen": origen, "encoding": enc,
                "separador": sep, "columnas_detectadas": columnas,
                "mensaje": "Faltan columnas exactas: " + ", ".join(faltan)}
    if df.empty:
        return {"estado": "vacio", "df": None, "origen": origen, "encoding": enc,
                "mensaje": "El CSV no tiene filas."}
    return {"estado": "ok", "df": df, "origen": origen, "encoding": enc, "separador": sep,
            "filas": len(df), "mensaje": f"{len(df)} filas leídas ({enc}, separador «{sep}»)."}


def calidad_fuente(enlace: str) -> str:
    enlace = normalizar_texto(enlace)
    if not enlace:
        return "Sin enlace"
    dominio = urlparse(enlace if "://" in enlace else "https://" + enlace).netloc.lower()
    if dominio.startswith("www."):
        dominio = dominio[4:]
    if any(dominio == d or dominio.endswith("." + d) for d in DOMINIOS_ORIGINALES):
        return "Fuente original (dominio institucional)"
    return "Referencia secundaria"


def primer_valor(valor: str) -> str:
    return normalizar_texto(valor.split("/")[0])


def validar_indicadores(df: pd.DataFrame | None) -> dict[str, dict]:
    """Busca cada indicador por etiqueta EXACTA y valida su valor."""
    out: dict[str, dict] = {}
    for iid, meta in INDICADORES.items():
        base = {"id": iid, **meta}
        if df is None:
            out[iid] = {**base, "estado": "sin_csv"}
            continue
        objetivo = normalizar_texto(meta["dato"])
        filas = df[df["Dato"].map(normalizar_texto) == objetivo]
        if filas.empty:
            out[iid] = {**base, "estado": "no_encontrado"}
            continue
        valores = {normalizar_valor(v) for v in filas["Valor"]}
        if len(valores) > 1:
            out[iid] = {**base, "estado": "ambiguo", "valores_csv": sorted(filas["Valor"].tolist())}
            continue
        fila = {k: normalizar_texto(v) for k, v in filas.iloc[0].to_dict().items()}
        ok = normalizar_valor(fila["Valor"]) == normalizar_valor(meta["valor_esperado"])
        out[iid] = {
            **base,
            "estado": "verificado" if ok else "valor_distinto",
            "fila": fila,
            "valor_csv": fila["Valor"],
            "valor_mostrado": primer_valor(fila["Valor"]) if meta.get("mostrar_primer_valor") else fila["Valor"],
            "calidad": calidad_fuente(fila.get("Enlace", "")),
        }
    return out


ETIQUETA_ESTADO = {
    "verificado": "Verificado contra el CSV",
    "valor_distinto": "Requiere revisión: el valor del CSV no coincide con el esperado",
    "no_encontrado": "No encontrado con la etiqueta exacta",
    "ambiguo": "Requiere revisión: etiqueta repetida con valores distintos",
    "sin_csv": "Sin CSV: no se puede verificar",
}


# ---------------------------------------------------------------------------
# Datasets SINTÉTICOS · Caso Talavera Viva (empresa ficticia)
# ---------------------------------------------------------------------------
TRIMESTRES = {"2026-T2": ["2026-04", "2026-05", "2026-06"], "2026-T3": ["2026-07", "2026-08", "2026-09"]}
PESOS_MES = {"2026-T2": [0.36, 0.33, 0.31], "2026-T3": [0.35, 0.33, 0.32]}

# Ventas por segmento (MXN): diseñadas para que el total limpio caiga exactamente 28 %.
VENTAS_SEGMENTO = {
    "Restaurantes": (420_000, 260_000),
    "Hoteles": (380_000, 300_000),
    "Bodas": (300_000, 240_000),
    "Turistas (tienda)": (150_000, 100_000),
}
MEZCLA = {
    "Restaurantes": [("Vajilla", "Venta directa B2B", 0.62), ("Vajilla", "Instagram", 0.04),
                     ("Azulejo", "Venta directa B2B", 0.12), ("Pieza personalizada", "Venta directa B2B", 0.22)],
    "Hoteles": [("Vajilla", "Venta directa B2B", 0.28), ("Azulejo", "Venta directa B2B", 0.30),
                ("Pieza personalizada", "Venta directa B2B", 0.38), ("Pieza personalizada", "Instagram", 0.04)],
    "Bodas": [("Pieza personalizada", "Tienda centro", 0.55), ("Pieza personalizada", "Instagram", 0.07),
              ("Vajilla", "Tienda centro", 0.18), ("Pieza personalizada", "Venta directa B2B", 0.20)],
    "Turistas (tienda)": [("Vajilla", "Tienda centro", 0.40), ("Azulejo", "Tienda centro", 0.20),
                          ("Pieza personalizada", "Tienda centro", 0.40)],
}
COLUMNAS_VENTAS = ["id_venta", "trimestre", "mes", "segmento", "producto", "canal", "importe_mxn", "nota"]


def generar_ventas() -> pd.DataFrame:
    """Ventas sintéticas con UNA anomalía documentada: un registro duplicado (mismo id_venta)."""
    filas = []
    for tri, meses in TRIMESTRES.items():
        idx = 0 if tri == "2026-T2" else 1
        for seg, totales in VENTAS_SEGMENTO.items():
            total_seg = totales[idx]
            celdas = [(m, p, c, w * pm) for m, pm in zip(meses, PESOS_MES[tri]) for (p, c, w) in MEZCLA[seg]]
            acumulado = 0
            for i, (mes, prod, canal, w) in enumerate(celdas):
                if i < len(celdas) - 1:
                    imp = int(round(total_seg * w / 100.0)) * 100
                    acumulado += imp
                else:
                    imp = total_seg - acumulado  # la última fila cuadra el total exacto
                filas.append({"trimestre": tri, "mes": mes, "segmento": seg, "producto": prod,
                              "canal": canal, "importe_mxn": imp, "nota": ""})
    df = pd.DataFrame(filas).sort_values(["mes", "segmento", "producto", "canal"], kind="stable").reset_index(drop=True)
    df.insert(0, "id_venta", [f"V-{i:04d}" for i in range(1, len(df) + 1)])
    # Anomalía intencional: se duplica una venta de agosto a restaurantes y se inserta al final.
    objetivo = df[(df["mes"] == "2026-08") & (df["segmento"] == "Restaurantes") &
                  (df["producto"] == "Vajilla") & (df["canal"] == "Venta directa B2B")].iloc[0].copy()
    df.loc[df["id_venta"] == objetivo["id_venta"], "nota"] = "pedido recurrente"
    objetivo["nota"] = "pedido recurrente"
    df = pd.concat([df, pd.DataFrame([objetivo])], ignore_index=True)
    return df[COLUMNAS_VENTAS]


def id_duplicado(df: pd.DataFrame) -> list[str]:
    return sorted(df.loc[df["id_venta"].duplicated(keep=False), "id_venta"].unique().tolist())


def limpiar_duplicados(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates(subset=["id_venta"], keep="first").reset_index(drop=True)


def resumen_trimestres(df: pd.DataFrame) -> dict:
    t = df.groupby("trimestre")["importe_mxn"].sum()
    t2, t3 = float(t.get("2026-T2", 0)), float(t.get("2026-T3", 0))
    var = (t3 - t2) / t2 * 100 if t2 else None
    return {"T2": t2, "T3": t3, "variacion_pct": var}


def variacion_por(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    p = df.pivot_table(index=columna, columns="trimestre", values="importe_mxn", aggfunc="sum", fill_value=0)
    for c in ("2026-T2", "2026-T3"):
        if c not in p.columns:
            p[c] = 0
    p = p[["2026-T2", "2026-T3"]].copy()
    p["variación_%"] = ((p["2026-T3"] - p["2026-T2"]) / p["2026-T2"].where(p["2026-T2"] != 0) * 100).round(1)
    return p.reset_index()


CLIENTES = [
    # segmento, clientes T2, T3, pedidos T2, T3, motivo reportado por Carmen
    ("Restaurantes", 14, 11, 56, 36, "La reposición de vajilla tarda; dos restaurantes cambiaron a vajilla industrial"),
    ("Hoteles", 9, 8, 30, 24, "Piden piezas con su logo y entregas más rápidas"),
    ("Bodas", 40, 30, 40, 30, "Comparan precio con imitaciones; temporada más baja"),
    ("Turistas (tienda)", 1250, 800, 1250, 800, "Menos paso peatonal por obras en la calle de la tienda"),
]


def generar_clientes() -> pd.DataFrame:
    filas = []
    for seg, c2, c3, p2, p3, motivo in CLIENTES:
        v2, v3 = VENTAS_SEGMENTO[seg]
        filas.append({"segmento": seg, "clientes_activos_T2": c2, "clientes_activos_T3": c3,
                      "pedidos_T2": p2, "pedidos_T3": p3,
                      "ticket_promedio_T2_mxn": round(v2 / p2, 1), "ticket_promedio_T3_mxn": round(v3 / p3, 1),
                      "motivo_reportado": motivo})
    return pd.DataFrame(filas)


def generar_costos() -> pd.DataFrame:
    base = [
        ("Vajilla", "Juego de 6 platos", 2400, 1320, 2, 4),
        ("Azulejo", "Caja de 1 m²", 1600, 992, 3, 3),
        ("Pieza personalizada", "Pieza con diseño del cliente", 1800, 810, 5, 5),
    ]
    filas = []
    for prod, unidad, precio, costo, ent, ent_sin in base:
        filas.append({"producto": prod, "unidad": unidad, "precio_promedio_mxn": precio, "costo_unitario_mxn": costo,
                      "margen_bruto_pct": round((precio - costo) / precio * 100, 1),
                      "entrega_semanas_con_stock": ent, "entrega_semanas_sin_stock": ent_sin,
                      "nota": "Supuesto del caso ficticio, no precio de mercado"})
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------
# Microcasos de demostración independiente (A y B): empresas ficticias distintas
# ---------------------------------------------------------------------------
MICRO = {
    "A": {"empresa": "Panadería La Espiga (ficticia)", "unidad": "Sucursal",
          "periodo_1": "Enero", "periodo_2": "Febrero",
          "filas": [("Centro", 120_000, 108_000), ("Norte", 90_000, 63_000), ("Sur", 70_000, 72_800)]},
    "B": {"empresa": "Librería Mirador (ficticia)", "unidad": "Categoría",
          "periodo_1": "Trimestre 1", "periodo_2": "Trimestre 2",
          "filas": [("Infantil", 80_000, 84_000), ("Novela", 150_000, 121_500), ("Papelería", 60_000, 39_000)]},
}


def generar_micro(clave: str) -> pd.DataFrame:
    m = MICRO[clave]
    return pd.DataFrame([{"empresa": m["empresa"], "segmento": s, "periodo_1": m["periodo_1"],
                          "periodo_2": m["periodo_2"], "ventas_periodo_1_mxn": a, "ventas_periodo_2_mxn": b}
                         for s, a, b in m["filas"]])


GENERADORES = {
    "ventas_talavera.csv": generar_ventas,
    "clientes_talavera.csv": generar_clientes,
    "costos_talavera.csv": generar_costos,
    "evaluacion_A.csv": lambda: generar_micro("A"),
    "evaluacion_B.csv": lambda: generar_micro("B"),
}


def cargar_sintetico(nombre: str) -> pd.DataFrame:
    """Lee data/<nombre> si existe y tiene las columnas esperadas; si no, lo genera en memoria."""
    esperado = GENERADORES[nombre]()
    p = DATA_DIR / nombre
    if p.exists():
        try:
            df = pd.read_csv(p, keep_default_na=False)
            if list(df.columns) == list(esperado.columns):
                return df
        except Exception:  # noqa: BLE001
            pass
    return esperado


def escribir_sinteticos() -> list[Path]:
    DATA_DIR.mkdir(exist_ok=True)
    rutas = []
    for nombre, gen in GENERADORES.items():
        p = DATA_DIR / nombre
        gen().to_csv(p, index=False, encoding="utf-8")
        rutas.append(p)
    return rutas


def micro_resumen(df: pd.DataFrame) -> dict:
    t1, t2 = df["ventas_periodo_1_mxn"].sum(), df["ventas_periodo_2_mxn"].sum()
    seg = df.assign(var=(df["ventas_periodo_2_mxn"] - df["ventas_periodo_1_mxn"]) / df["ventas_periodo_1_mxn"] * 100)
    return {"total_1": float(t1), "total_2": float(t2), "variacion_total_pct": float((t2 - t1) / t1 * 100),
            "variacion_segmento": dict(zip(seg["segmento"], seg["var"].round(2))),
            "segmento_mayor_caida": seg.sort_values("var").iloc[0]["segmento"]}


if __name__ == "__main__":
    for r in escribir_sinteticos():
        print("escrito", r.relative_to(BASE))
