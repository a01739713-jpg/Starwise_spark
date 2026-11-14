"""STARWISE × ROLELAB · app.py

Juego narrativo de decisiones profesionales (Talavera Valley Hackathon 2026 · EdTech).
Ejecutar:  pip install -r requirements.txt  &&  streamlit run app.py

Flujo por escenas (st.session_state["S"]["escena"]):
inicio → perfil → rutas → expectativa → diag_A → aventura (Talavera Viva) →
resultado_mision → prueba_B → reflexion → logros → portafolio → siguiente_paso → cierre
Extra: facilitador (panel del equipo).
"""
from __future__ import annotations

import hmac
import inspect
import re
import time
from datetime import datetime

import pandas as pd
import streamlit as st

import casos
import chispa
import datos
import evaluacion
import evidencia
import ia
import portafolio
import ui
from ui import esc, html

st.set_page_config(page_title="STARWISE · Explora tu camino", page_icon="✨", layout="wide",
                   initial_sidebar_state="collapsed")
ui.inyectar_css()

LEMA = "Explora tu camino. Vive el reto. Demuestra lo que sabes hacer."
ESCENAS = ["inicio", "perfil", "rutas", "expectativa", "diag_A", "aventura", "resultado_mision", "prueba_B",
           "reflexion", "logros", "portafolio", "siguiente_paso", "cierre"]
ETAPA_DE = {"inicio": 0, "perfil": 0, "rutas": 0, "expectativa": 0, "diag_A": 1, "aventura": 1, "resultado_mision": 1,
            "prueba_B": 2, "reflexion": 2, "logros": 2, "portafolio": 2, "siguiente_paso": 3, "cierre": 3,
            "facilitador": 0}
INTERESES = [("datos", "Datos y finanzas", "Números, hojas de cálculo, indicadores y herramientas digitales."),
             ("mercado", "Mercadotecnia", "Clientes, canales, marca y redes sociales."),
             ("operaciones", "Emprendimiento y operaciones", "Procesos, costos, entregas y decisiones de negocio.")]
RUTAS = [
    {"id": "estrategia", "nombre": "Estrategia comercial y datos", "icono": "mercado", "activa": True,
     "tareas": ["Entender clientes, canales y márgenes de un negocio", "Diseñar un plan comercial con metas medibles"],
     "competencias": ["Investigación de clientes", "Análisis de datos", "Priorización con presupuesto"],
     "mision": "Talavera Viva: recuperar ventas sin despedir a nadie", "tiempo": "≈ 35–45 min"},
    {"id": "bi", "nombre": "Analista de negocios / inteligencia comercial", "icono": "datos", "activa": False,
     "tareas": ["Analizar ventas y construir indicadores (KPI)", "Explicar con datos qué decisión conviene"],
     "competencias": ["Análisis de datos", "Visualización", "Comunicación de hallazgos"],
     "mision": "Tablero y diagnóstico cuantitativo", "tiempo": "Próximamente"},
    {"id": "fin", "nombre": "Analista financiero junior", "icono": "finanzas", "activa": False,
     "tareas": ["Revisar flujos, presupuestos y riesgos", "Comparar escenarios de un negocio (sin trading real)"],
     "competencias": ["Presupuestación", "Análisis de escenarios", "Gestión de riesgos"],
     "mision": "Presupuesto y escenarios", "tiempo": "Próximamente"},
]
MAX_PROYECTO = {"digital": 50_000, "alianzas": 70_000, "producto": 90_000}


# ---------------------------------------------------------------------------
# Compatibilidad de anchos (Streamlit ≥1.50 usa width="stretch")
# ---------------------------------------------------------------------------
def _ancho(fn, **kw):
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        params = {}
    if "width" in params:
        kw.setdefault("width", "stretch")
    elif "use_container_width" in params:
        kw.setdefault("use_container_width", True)
    return kw


def boton(label, key=None, primario=False, **kw):
    return st.button(label, key=key, type="primary" if primario else "secondary", **_ancho(st.button, **kw))


def enviar(label, primario=True, **kw):
    return st.form_submit_button(label, type="primary" if primario else "secondary", **_ancho(st.form_submit_button, **kw))


def descarga(label, data, nombre, mime, key, primario=False):
    return st.download_button(label, data=data, file_name=nombre, mime=mime, key=key,
                              type="primary" if primario else "secondary", **_ancho(st.download_button))


def tabla(df, **kw):
    st.dataframe(df, hide_index=True, **_ancho(st.dataframe, **kw))


def grafica(fig):
    st.plotly_chart(fig, config={"displayModeBar": False, "responsive": True}, **_ancho(st.plotly_chart))


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------
def estado_inicial(tipo: str = "interna", alias: str = "") -> dict:
    return {
        "intento": evidencia.nuevo_intento(), "tipo_registro": tipo, "facilitador_declaro_externa": tipo == "externa_confirmada",
        "escena": "inicio", "escena_previa": "inicio", "_scroll": True,
        "perfil": {"alias": alias, "carrera": "", "semestre": "", "intereses": [], "mayor_18_confirmado": False,
                   "consentimiento_datos_minimos": False},
        "ruta": None, "expectativa_rol": "", "interes_rol_antes": None, "autoeficacia_antes": None,
        "autoeficacia_despues": None, "cambio_interes": {},
        "A": {}, "B": {},
        "sim": {"turnos": 0, "revelados": [], "giro": False, "giro_visto": False, "presupuesto": casos.PRESUPUESTO_INICIAL,
                "log": [], "chat": [], "archivos_abiertos": [], "archivo_activo": None, "filtros_usados": False,
                "hallazgos": {}, "hallazgos_ok": [], "hallazgos_intentos": 0, "feedback_hallazgos": [], "planes": [],
                "ajuste_justificacion": "", "propuesta": {}, "defensa": {}, "resultado_visto": False},
        "pistas": {m: 0 for m in chispa.MISIONES}, "tutor_log": [], "tutor_chat": {m: [] for m in chispa.MISIONES},
        "ia_control": {}, "encuesta": {}, "plan_accion": [], "feedback_ia_B": None,
    }


if "S" not in st.session_state:
    st.session_state["S"] = estado_inicial()
S: dict = st.session_state["S"]
SIM: dict = S["sim"]


def ir(escena: str) -> None:
    if escena == "facilitador" and S["escena"] != "facilitador":
        S["escena_previa"] = S["escena"]
    S["escena"] = escena
    S["_scroll"] = True


def ir_vista(vista: str, sub: str | None = None) -> None:
    st.session_state["w_vista"] = vista
    if sub:
        st.session_state["w_sub_prop"] = sub


def init_widget(key: str, valor) -> None:
    """Restaura el valor de un widget desde S sin usar `value=` y key a la vez (evita conflictos)."""
    if key not in st.session_state and valor is not None:
        st.session_state[key] = valor


def sin_conflicto(key: str, **defaults) -> dict:
    """Pasa value/index solo si el widget no tiene ya un valor en session_state."""
    return {} if key in st.session_state else defaults


def abrir_metodologia(seccion: str) -> None:
    st.session_state["w_met_sec"] = seccion
    dialogo_metodologia(seccion)


def subir_al_inicio() -> None:
    if not S.pop("_scroll", False):
        return
    try:
        import streamlit.components.v1 as components

        components.html(f"<script>/*{S['escena']}*/try{{const d=window.parent.document;"
                        "const m=d.querySelector('[data-testid=\"stMain\"]')||d.querySelector('section.main');"
                        "(m||window.parent).scrollTo({top:0,behavior:'auto'});window.parent.scrollTo(0,0);}catch(e){}</script>",
                        height=0)
    except Exception:  # noqa: BLE001 - el desplazamiento es solo una comodidad
        pass


# ---------------------------------------------------------------------------
# Datos (con caché)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _repo_bytes(b: bytes) -> dict:
    return datos.leer_repositorio(b)


@st.cache_data(show_spinner=False)
def _repo_archivo(_mtime: float) -> dict:
    return datos.leer_repositorio(datos.REPO_PATH)


def repositorio() -> tuple[dict, dict]:
    b = st.session_state.get("repo_bytes")
    if b:
        res = dict(_repo_bytes(b))
        res["origen"] = "archivo cargado en esta sesión"
    else:
        mt = datos.REPO_PATH.stat().st_mtime if datos.REPO_PATH.exists() else 0.0
        res = _repo_archivo(mt)
    return res, datos.validar_indicadores(res.get("df"))


@st.cache_data(show_spinner=False)
def sintetico(nombre: str) -> pd.DataFrame:
    return datos.cargar_sintetico(nombre)


def indicador_verificado(iid: str) -> dict | None:
    _, ind = repositorio()
    i = ind.get(iid)
    return i if i and i["estado"] == "verificado" else None


def mxn(x: float) -> str:
    return f"${x:,.0f}"


# ---------------------------------------------------------------------------
# Metodología (modal accesible siempre)
# ---------------------------------------------------------------------------
SECCIONES = ["Fuentes", "Ruta Base", "Evaluación", "Modelo comercial", "Privacidad", "Acerca"]


@st.dialog("Metodología y fuentes", width="large")
def dialogo_metodologia(seccion: str = "Fuentes") -> None:
    init_widget("w_met_sec", seccion)
    sec = st.segmented_control("Sección", SECCIONES, key="w_met_sec", label_visibility="collapsed") or seccion
    res, ind = repositorio()

    if sec == "Fuentes":
        st.markdown("**Dos tipos de datos, siempre separados**")
        st.markdown("- **Simulación (sintéticos):** Talavera Viva, Carmen y los microcasos A/B son ficticios.\n"
                    "- **Contexto (repositorio oficial del reto):** `data/repositorio.csv`. Cada indicador se busca por su "
                    "etiqueta exacta y se verifica su valor; si no coincide, no se muestra.")
        estado = res["estado"]
        if estado == "ok":
            st.success(f"Repositorio leído desde {res['origen']}: {res['mensaje']}")
        else:
            st.error(f"Repositorio no disponible ({estado}): {res['mensaje']} La simulación sigue funcionando con datos sintéticos.")
        filas = []
        for i in ind.values():
            fila = i.get("fila", {})
            filas.append({"Indicador": i["titulo"], "Estado": datos.ETIQUETA_ESTADO[i["estado"]],
                          "Valor en CSV": i.get("valor_csv", "—"), "Población": i["poblacion"], "Año": i["anio"],
                          "Limitación": i["limitacion"], "Dónde se usa": i["uso"],
                          "Fuente (CSV)": fila.get("Fuente", "—"), "Calidad": i.get("calidad", "—"),
                          "Enlace": fila.get("Enlace", "—")})
        tabla(pd.DataFrame(filas))
        st.caption("Desliza la tabla horizontalmente para ver todas las columnas. «Referencia secundaria» = el enlace del "
                   "CSV no es un dominio institucional (p. ej., prensa). La ENE 2025 de la UVM es una encuesta no probabilística.")
        with st.expander("Contexto nacional (no es salario de ninguna ruta)"):
            ip = ind["ingreso_promedio"]
            if ip["estado"] == "verificado":
                st.markdown(f"**{esc(ip['titulo'])}: {esc(ip['valor_csv'])}** — {esc(ip['limitacion'])}")
            else:
                st.markdown("Dato no verificado en el CSV: no se muestra.")
            st.markdown("No usamos «% que trabaja fuera de lo que estudió» al elegir ruta: no indica falta de competencias. "
                        "La encuesta de Manpower sobre dificultad para cubrir vacantes es privada y entre empleadores; no se "
                        "usa como indicador personal. El 43.3 % de «falta de experiencia» no proviene del CSV y no se muestra.")
        archivo = st.file_uploader("Cargar repositorio.csv (solo para esta sesión)", type=["csv"], key="w_repo_up")
        if archivo is not None:
            st.session_state["repo_bytes"] = archivo.getvalue()
            st.info("Archivo cargado. Cierra y vuelve a abrir esta ventana para ver la verificación actualizada.")

    elif sec == "Ruta Base":
        def val(iid):
            return ind[iid]["valor_csv"] if ind[iid]["estado"] == "verificado" else "No verificado en el CSV"
        tabla(pd.DataFrame([
            {"Concepto": "Duración académica", "Ruta Base: licenciatura de 4 años": "4 años (referencia ilustrativa del hackathon)",
             "Licenciatura + sesión STARWISE": "Igual: STARWISE no cambia la duración"},
            {"Concepto": "Costo directo ilustrativo", "Ruta Base: licenciatura de 4 años":
                f"Pública {val('costo_publica')} · Privada {val('costo_privada')}",
             "Licenciatura + sesión STARWISE": "Mismo costo base"},
            {"Concepto": "Costo incremental", "Ruta Base: licenciatura de 4 años": "—",
             "Licenciatura + sesión STARWISE": "$0 durante la demo; precio comercial no validado"},
            {"Concepto": "Resultado del programa", "Ruta Base: licenciatura de 4 años": "No medido en este prototipo",
             "Licenciatura + sesión STARWISE": "Evidencia de resolución de un caso y autoevaluación; NO ingreso ni contratación medidos"},
        ]))
        st.caption("Los costos del repositorio son ilustrativos, con fuentes indirectas, y no son directamente comparables con "
                   "el valor de una sesión de práctica. No se usan para elegir ruta profesional.")

    elif sec == "Evaluación":
        st.markdown(f"Versión de rúbrica: `{evaluacion.RUBRIC_VERSION}`")
        st.markdown(
            "- **Diagnóstico A y demostración B:** dos microcasos distintos y comparables, sin tutor, con 4 criterios objetivos "
            "(variación ±0.5 pp, segmento con mayor caída, indicador pertinente, cifra del caso en la justificación). La calidad "
            "del texto queda **pendiente de revisión humana**.\n"
            "- **Práctica asistida (Talavera Viva):** cinco áreas con criterios conductuales fijados de antemano: investigación, "
            "análisis, priorización, comunicación y adaptación. Se muestran niveles (Inicial · En desarrollo · Aplicado en el caso "
            "· Requiere revisión), no una nota única.\n"
            "- **No se usa:** longitud del texto, rapidez, número de acciones, pocas pistas ni palabras clave como «porque».\n"
            "- **Autoeficacia** antes/después: opinión subjetiva, no aprendizaje.\n"
            "- **Comparación A/B:** cambio observado, no mejora causal.\n"
            "- La IA (si está configurada) solo orienta y redacta comentarios; nunca decide criterios.\n"
            "- La rúbrica no tiene validación psicométrica ni capacidad predictiva de contratación.")
        st.markdown(f"**Tutor:** {chispa.MAX_PISTAS_POR_MISION} pistas por misión; explicar conceptos no consume pistas. "
                    f"Banco por reglas con {chispa.total_escenarios()} escenarios.")

    elif sec == "Modelo comercial":
        st.markdown(
            "STARWISE/ROLELAB se propone como **software complementario de práctica profesional** para instituciones de "
            "educación superior (cliente: universidades; usuarios: estudiantes; empresas colaboradoras: **futuras**, hoy no hay "
            "ninguna).\n\n"
            "- Precio por estudiante o por cohorte: **hipótesis no validada**; no hay ventas ni licencias conseguidas.\n"
            "- Frente a Forage, Riipen, DataCamp o CONCORA buscamos combinar práctica individual lúdica, datos manipulables, "
            "retroalimentación y demostración independiente. No afirmamos que la combinación sea exclusiva.\n"
            "- No usamos marcas de universidades ni de empresas como si existiera autorización.")

    elif sec == "Privacidad":
        st.markdown(
            "- Solo participan personas **mayores de 18 años** (confirmación explícita).\n"
            "- Datos mínimos: alias opcional, carrera y semestre opcionales, intereses y tus respuestas.\n"
            "- **Nada se guarda en el servidor.** Al cerrar o recargar se pierde lo no exportado. Tú decides si descargas y "
            "compartes tu archivo de evidencia (JSON).\n"
            "- No escribas nombre completo, correo, teléfono ni datos de terceros en las respuestas.\n"
            "- Si hay IA configurada, solo se envía contexto del caso ficticio y tu mensaje al tutor; nunca tu alias ni tu perfil.\n"
            "- Las preguntas al tutor no se usan para inferir honestidad, inteligencia, empleabilidad ni personalidad.")

    else:
        st.markdown(
            f"**STARWISE × ROLELAB** · Talavera Valley Hackathon 2026 / EdTech · versión {evidencia.APP_VERSION}.\n\n"
            "Prototipo académico. Complementa la formación universitaria; **no** es certificación oficial, experiencia laboral "
            "formal ni garantía de contratación. Talavera Viva, Carmen Ruiz, La Espiga y Mirador son ficticias. Mascota: Chispa.")
    if boton("Cerrar", key="w_met_cerrar"):
        st.rerun()


def boton_fuente(key: str, seccion: str = "Fuentes", texto: str = "¿De dónde viene este dato?") -> None:
    if st.button(texto, key=key, type="tertiary"):
        abrir_metodologia(seccion)


# ---------------------------------------------------------------------------
# Barra superior: marca + Opciones
# ---------------------------------------------------------------------------
def barra_superior() -> None:
    c1, c2 = st.columns([3, 1], vertical_alignment="center")
    with c1:
        ui.marca()
    with c2:
        with st.popover("Opciones · Mi progreso", **_ancho(st.popover)):
            idx = ESCENAS.index(S["escena"]) if S["escena"] in ESCENAS else 0
            st.markdown(f"**Mi progreso:** escena {idx + 1} de {len(ESCENAS)} · intento `{S['intento']['attempt_id'][:8]}`")
            reg = evidencia.construir_registro(S, ia.estado_ia(S["ia_control"])["etiqueta"])
            descarga("Descargar mi evidencia (JSON)", evidencia.a_json(reg).encode("utf-8"),
                     f"starwise_evidencia_{S['intento']['attempt_id'][:8]}.json", "application/json", "w_dl_menu")
            st.caption("Recargar o cerrar la página puede borrar lo no exportado.")
            if boton("Metodología y fuentes", key="w_menu_met"):
                abrir_metodologia("Fuentes")
            if boton("Acerca del proyecto", key="w_menu_acerca"):
                abrir_metodologia("Acerca")
            if S["escena"] != "facilitador":
                boton("Panel del equipo (facilitador)", key="w_menu_fac", on_click=ir, args=("facilitador",))
            confirmar = st.checkbox("Quiero reiniciar y borrar este intento", key="w_conf_reset")
            if boton("Reiniciar", key="w_menu_reset", disabled=not confirmar):
                st.session_state.clear()
                st.rerun()
    etapa = ETAPA_DE.get(S["escena"], 0)
    prog = (ESCENAS.index(S["escena"]) + 1) / len(ESCENAS) if S["escena"] in ESCENAS else 0
    if S["escena"] != "facilitador":
        ui.barra_aventura(etapa, prog)


# ---------------------------------------------------------------------------
# Chispa · panel de tutoría (solo práctica)
# ---------------------------------------------------------------------------
def _ctx_tutor(mision: str) -> dict:
    hechos = [h["dato"] for h in casos.HECHOS if h["id"] in SIM["revelados"] and h["dato"]]
    return {"fase": "practica", "mision": mision, "mision_nombre": chispa.MISIONES[mision], "hechos": hechos,
            "presupuesto": SIM["presupuesto"], "nivel_pista": S["pistas"][mision] + 1}


def tutor_accion(mision: str, tipo: str, mensaje: str = "") -> None:
    chat = S["tutor_chat"][mision]
    if tipo == "pista" and S["pistas"][mision] >= chispa.MAX_PISTAS_POR_MISION:
        chat.append({"rol": "chispa", "texto": "Ya usaste las 3 pistas de esta misión. Aún puedo explicarte conceptos o "
                                                "decirte por dónde empezar.", "fuente": "reglas"})
        return
    if mensaje:
        chat.append({"rol": "yo", "texto": mensaje[:500]})
    r = ia.tutor(mensaje or tipo, tipo, _ctx_tutor(mision), S["ia_control"])
    if r["es_pista"]:
        if S["pistas"][mision] >= chispa.MAX_PISTAS_POR_MISION:
            r = {**r, "texto": "Ya usaste las 3 pistas de esta misión.", "es_pista": False}
        else:
            S["pistas"][mision] += 1
    chat.append({"rol": "chispa", "texto": r["texto"], "fuente": r["fuente"], "nota": r.get("nota", "")})
    S["tutor_log"].append({"ts": evidencia.ahora_iso(), "mision": mision, "tipo": tipo, "fuente": r["fuente"],
                           "es_pista": r["es_pista"], "nivel": S["pistas"][mision] if r["es_pista"] else None})


def panel_tutor(mision: str) -> None:
    est = ia.estado_ia(S["ia_control"])
    usadas = S["pistas"][mision]
    with st.container(border=True):
        tipo_chip = "verde" if est["disponible"] else ""
        html(f'<div>{ui.chip(est["etiqueta"], tipo_chip)}{ui.chip(f"Pistas en esta misión: {usadas}/3", "oro")}</div>')
        caja = st.container()
        c1, c2, c3 = st.columns(3)
        with c1:
            boton("Dame una pista", key=f"w_pista_{mision}", primario=True, disabled=usadas >= 3,
                  on_click=tutor_accion, args=(mision, "pista"))
        with c2:
            boton("¿Por dónde comienzo?", key=f"w_comienzo_{mision}", on_click=tutor_accion, args=(mision, "comienzo"))
        with c3:
            with st.popover("No entiendo este concepto", **_ancho(st.popover)):
                for k, nombre in chispa.lista_conceptos():
                    boton(nombre.capitalize(), key=f"w_conc_{mision}_{k}", on_click=tutor_accion,
                          args=(mision, "concepto", f"¿Qué es {chispa.CONCEPTOS[k][1][0]}?"))
        with st.form(f"form_tutor_{mision}", clear_on_submit=True, border=False):
            msg = st.text_input("Pregúntale a Chispa", key=f"w_tutor_txt_{mision}", max_chars=300,
                                placeholder="Ej.: ¿qué es un indicador controlable?")
            if enviar("Preguntar a Chispa", primario=False) and msg.strip():
                tutor_accion(mision, "libre", msg.strip())
        st.caption("Regla: máximo 3 pistas por misión (1 · pregunta guía, 2 · dónde buscar, 3 · ejemplo con otras cifras). "
                   "Explicar conceptos no gasta pistas. Usar ayuda no resta puntos.")
        with caja:
            mensajes = S["tutor_chat"][mision][-4:]
            if not mensajes:
                ui.dialogo("Chispa · tutora", "Estoy aquí si me necesitas. No te daré la respuesta, pero sí te ayudo a encontrarla.",
                           "chispa", "feliz")
            for m in mensajes:
                if m["rol"] == "yo":
                    ui.dialogo(S["perfil"].get("alias") or "Tú", m["texto"], "yo")
                else:
                    etiqueta = "Chispa · IA generativa" if m.get("fuente") == "gemini" else "Chispa · reglas"
                    ui.dialogo(etiqueta, m["texto"], "chispa", "pensando")
                    if m.get("nota"):
                        st.caption(m["nota"])


# ---------------------------------------------------------------------------
# CAPÍTULO 0 · Aventura inicial
# ---------------------------------------------------------------------------
def toggle_interes(iid: str) -> None:
    lst = S["perfil"]["intereses"]
    nombre = next(n for i, n, _ in INTERESES if i == iid)
    if nombre in lst:
        lst.remove(nombre)
    else:
        lst.append(nombre)


def escena_inicio() -> None:
    ui.hero("STARWISE", LEMA, "Un juego de decisiones profesionales para universitarios: vives un reto de negocio, "
                              "practicas con datos y demuestras lo que sabes hacer.", "feliz")
    st.markdown("### ¿Qué te gustaría experimentar?")
    cols = st.columns(3)
    for col, (iid, nombre, desc) in zip(cols, INTERESES):
        elegido = nombre in S["perfil"]["intereses"]
        with col:
            ui.tarjeta(nombre, f"<p>{esc(desc)}</p>", iid, "activa" if elegido else "")
            boton(("✓ Me interesa" if elegido else "Me interesa"), key=f"w_int_{iid}", primario=elegido,
                  on_click=toggle_interes, args=(iid,))
    st.write("")
    boton("Comenzar mi aventura", key="w_comenzar", primario=True, on_click=ir, args=("perfil",))
    st.caption("Puedes elegir varios intereses o ninguno. Duración total aproximada: 45–60 minutos.")


def escena_perfil() -> None:
    ui.dialogo("Chispa", "Antes de salir de viaje, cuéntame un poco de ti. Todo es opcional excepto confirmar tu edad y "
                         "aceptar cómo tratamos tus datos.", "chispa", "feliz")
    p = S["perfil"]
    init_widget("w_alias", p.get("alias", ""))
    init_widget("w_carrera", p.get("carrera", ""))
    init_widget("w_semestre", p.get("semestre", ""))
    init_widget("w_mayor", p.get("mayor_18_confirmado", False))
    init_widget("w_consent", p.get("consentimiento_datos_minimos", False))
    init_widget("w_autoef", S.get("autoeficacia_antes") or 3)
    with st.form("form_perfil", border=True):
        st.text_input("Alias (opcional, no uses tu nombre completo)", key="w_alias", max_chars=30)
        c1, c2 = st.columns(2)
        c1.text_input("Carrera actual (opcional)", key="w_carrera", max_chars=60)
        c2.text_input("Semestre (opcional)", key="w_semestre", max_chars=10)
        st.slider("¿Qué tan capaz te sientes HOY de analizar datos de un negocio y proponer una solución?", 1, 5,
                  key="w_autoef", help="1 = nada capaz · 5 = muy capaz")
        st.caption("Es tu opinión subjetiva, no una calificación ni una medida de competencia.")
        st.checkbox("Confirmo que tengo 18 años o más.", key="w_mayor")
        st.checkbox("Acepto participar en la prueba de este prototipo académico. Solo se registran mi alias opcional, mis "
                    "intereses y mis respuestas en esta sesión; nada se guarda en el servidor y yo decido si descargo y "
                    "comparto mi archivo de evidencia.", key="w_consent")
        st.caption("No escribas correo, teléfono ni datos de otras personas en tus respuestas.")
        ok = enviar("Elegir misión")
    if ok:
        errores = []
        if not st.session_state["w_mayor"]:
            errores.append("Por ahora esta demo es solo para personas mayores de 18 años.")
        if not st.session_state["w_consent"]:
            errores.append("Necesitamos tu aceptación del tratamiento mínimo de datos para continuar.")
        if errores:
            for e_ in errores:
                st.error(e_)
            return
        p.update({"alias": st.session_state["w_alias"].strip(), "carrera": st.session_state["w_carrera"].strip(),
                  "semestre": st.session_state["w_semestre"].strip(), "mayor_18_confirmado": True,
                  "consentimiento_datos_minimos": True, "consentimiento_ts": evidencia.ahora_iso()})
        S["autoeficacia_antes"] = int(st.session_state["w_autoef"])
        ir("rutas")
        st.rerun()
    boton("← Volver", key="w_perfil_volver", on_click=ir, args=("inicio",))


# ---------------------------------------------------------------------------
# CAPÍTULO 1 · Elegir camino con sentido
# ---------------------------------------------------------------------------
def elegir_ruta(rid: str) -> None:
    S["ruta"] = rid
    ir("expectativa")


def escena_rutas() -> None:
    st.markdown("## Elige tu misión")
    st.markdown("Cada ruta es una forma de trabajar. Elige la que quieras **experimentar**; después de vivirla podrás decir "
                "si te acerca o te aleja de ese rol.")
    cols = st.columns(3)
    for col, r in zip(cols, RUTAS):
        with col:
            cuerpo = ("<p><b>En esta profesión podrías hacer…</b></p><ul>" + "".join(f"<li>{esc(t)}</li>" for t in r["tareas"]) +
                      "</ul><p><b>Competencias a explorar</b></p><p>" + "".join(ui.chip(c) for c in r["competencias"]) + "</p>"
                      f"<p><b>Misión:</b> {esc(r['mision'])}<br><b>Tiempo:</b> {esc(r['tiempo'])}</p>"
                      '<p class="sw-fuente">Descripción didáctica del rol; no es una vacante de ninguna empresa.</p>')
            ui.tarjeta(r["nombre"], cuerpo, r["icono"], "activa" if r["activa"] else "bloqueada")
            if r["activa"]:
                boton("Elegir esta misión", key=f"w_ruta_{r['id']}", primario=True, on_click=elegir_ruta, args=(r["id"],))
            else:
                boton("Próximamente", key=f"w_ruta_{r['id']}", disabled=True)
    st.write("")
    with st.container(border=True):
        st.markdown("**¿Y cuánto se gana en estos roles?** El repositorio no ofrece una cifra comparable de salario inicial "
                    "para estas ocupaciones, así que no te mostramos una. Preferimos que pruebes el trabajo.")
        hab = indicador_verificado("habilidades_clave")
        if hab and "Datos y finanzas" in S["perfil"]["intereses"]:
            st.markdown(f"Como te interesan los datos: en la ENE 2025 de la UVM, **{esc(hab['valor_csv'])}** de las personas "
                        "egresadas encuestadas consideró clave las habilidades **tecnológicas / segunda lengua** para un mejor "
                        "empleo. Es su percepción, no prueba de que una capacitación funcione.")
        boton_fuente("w_fuente_rutas")
    boton("← Volver", key="w_rutas_volver", on_click=ir, args=("perfil",))


def escena_expectativa() -> None:
    ruta = next(r for r in RUTAS if r["id"] == S["ruta"])
    ui.dialogo("Chispa", f"¡Elegiste «{ruta['nombre']}»! Antes de entrar, anota qué esperas. Al final verás si cambió algo.",
               "chispa", "sorpresa")
    init_widget("w_expect", S.get("expectativa_rol", ""))
    init_widget("w_interes_antes", S.get("interes_rol_antes") or 3)
    with st.form("form_expect"):
        st.text_area("¿Qué crees que hace alguien en este rol en su día a día?", key="w_expect", max_chars=400, height=100)
        st.slider("¿Qué tanto te interesa este rol hoy?", 1, 5, key="w_interes_antes", help="Opinión personal")
        ok = enviar("Empezar la prueba inicial")
    if ok:
        S["expectativa_rol"] = st.session_state["w_expect"].strip()
        S["interes_rol_antes"] = int(st.session_state["w_interes_antes"])
        ir("diag_A")
        st.rerun()
    boton("← Cambiar de misión", key="w_exp_volver", on_click=ir, args=("rutas",))


# ---------------------------------------------------------------------------
# CAPÍTULO 2 y 5 · Microcasos sin ayuda (A y B)
# ---------------------------------------------------------------------------
def escena_micro(clave: str) -> None:
    caso = casos.MICROCASOS[clave]
    df = sintetico(caso["csv"])
    reg = S[clave]
    reg.setdefault("inicio", evidencia.ahora_iso())
    reg.setdefault("_t0", time.time())
    titulo = "Prueba inicial · sin ayuda" if clave == "A" else "Demostración final · sin ayuda"
    st.markdown(f"## {titulo}")
    ui.candado_tutor()

    if reg.get("entregado"):
        if clave == "A":
            ui.dialogo("Chispa", "¡Recibido! Verás cómo te fue al final, después de la demostración B, para que esta respuesta "
                                 "no influya en la siguiente. Ahora sí: te espera Talavera Viva.", "chispa", "feliz")
            boton("Entrar a Talavera Viva", key="w_A_sig", primario=True, on_click=ir, args=("aventura",))
        else:
            boton("Continuar", key="w_B_sig", primario=True, on_click=ir, args=("reflexion",))
        return

    html(f'<div class="sw-card"><h3>{esc(caso["titulo"])}</h3><p>{esc(caso["historia"])}</p>'
         f'{ui.chip("Empresa ficticia · Datos de práctica", "oro")}{ui.chip("3 a 5 minutos")}</div>')
    p1, p2 = df["periodo_1"].iloc[0], df["periodo_2"].iloc[0]
    nom_unidad = datos.MICRO[clave]["unidad"]
    ui.tabla_html([[r["segmento"], mxn(r["ventas_periodo_1_mxn"]), mxn(r["ventas_periodo_2_mxn"])] for _, r in df.iterrows()],
                  [nom_unidad, f"Ventas {p1}", f"Ventas {p2}"], "Cifras en pesos MXN. Datos sintéticos.")
    descarga(f"Descargar {caso['csv']}", df.to_csv(index=False).encode("utf-8-sig"), caso["csv"], "text/csv", f"w_dl_{clave}")

    ops_ind = {i: lbl for i, lbl, _ in caso["indicadores"]}
    with st.form(f"form_micro_{clave}"):
        st.number_input(f"a) ¿Cuál fue la variación porcentual de las ventas TOTALES de {p1} a {p2}?", value=None,
                        min_value=-100.0, max_value=1000.0, step=0.1, format="%.1f", key=f"w_{clave}_var",
                        help="Usa signo negativo si bajaron. Ejemplo de formato: -5.3")
        st.selectbox(f"b) ¿Qué {nom_unidad.lower()} tuvo la mayor caída porcentual?", list(df["segmento"]), index=None,
                     placeholder="Elige una opción", key=f"w_{clave}_seg")
        st.radio("c) ¿Qué indicador revisarías primero para entender la caída?", list(ops_ind), index=None,
                 format_func=lambda k: ops_ind[k], key=f"w_{clave}_ind")
        st.text_area("d) En dos frases: ¿qué le recomendarías? Incluye al menos un número de la tabla.", max_chars=400,
                     key=f"w_{clave}_just", height=110)
        st.caption("Solo puedes entregar una vez. El tiempo se registra, pero no se usa para calificarte.")
        ok = enviar("Entregar mi respuesta (una sola vez)")
    if ok:
        r = {"variacion_pct": st.session_state.get(f"w_{clave}_var"), "segmento": st.session_state.get(f"w_{clave}_seg"),
             "indicador": st.session_state.get(f"w_{clave}_ind"), "justificacion": (st.session_state.get(f"w_{clave}_just") or "").strip()}
        faltan = [n for n, v in [("a) variación", r["variacion_pct"]), ("b) segmento", r["segmento"]),
                                 ("c) indicador", r["indicador"]), ("d) recomendación", r["justificacion"])] if v in (None, "")]
        if faltan:
            st.error("Completa antes de entregar: " + ", ".join(faltan))
            return
        reg["respuestas"] = {**r, "indicador_texto": ops_ind[r["indicador"]]}
        reg["fin"] = evidencia.ahora_iso()
        reg["duracion_s"] = round(time.time() - reg.pop("_t0", time.time()), 1)
        reg["resultado"] = evaluacion.evaluar_micro(clave, df, r)
        reg["rubric_version"] = evaluacion.RUBRIC_VERSION
        reg["entregado"] = True
        S["_scroll"] = True
        st.rerun()


# ---------------------------------------------------------------------------
# CAPÍTULO 3 · Aventura «Tu primer día con Talavera Viva»
# ---------------------------------------------------------------------------
def estado_misiones() -> list[tuple[str, str, str]]:
    _, post = evaluacion.plan_pre_y_post(SIM["planes"])
    hechas = [SIM["turnos"] >= 3, bool(SIM["hallazgos"]),
              bool(SIM["giro"] and post and post["total"] <= casos.PRESUPUESTO_RECORTE),
              bool(SIM["defensa"]), SIM["resultado_visto"]]
    desc = ["Hazle al menos 3 preguntas a Carmen.", "Abre los archivos, revisa los números y registra tus hallazgos.",
            "Replanea con el presupuesto actualizado." if SIM["giro"] else "Algo podría cambiar en la historia…",
            "Presenta tu propuesta y defiéndela ante Carmen.", "Descubre cómo reacciona Carmen."]
    nombres = list(chispa.MISIONES.values()) + ["Resultado de la misión"]
    out, actual_puesto = [], False
    for n, d, h in zip(nombres, desc, hechas):
        est = "hecha" if h else ("actual" if not actual_puesto else "")
        if not h:
            actual_puesto = True
        out.append((n, d, est))
    return out


def mision_actual() -> str:
    for (_, _, est), m in zip(estado_misiones(), chispa.MISIONES):
        if est != "hecha":
            return m
    return "m4"


def preguntar_carmen(texto: str) -> None:
    texto = texto.strip()[:500]
    if not texto:
        return
    SIM["chat"].append({"rol": "yo", "texto": texto})
    r = casos.carmen_responder(texto, SIM)
    SIM["chat"].append({"rol": "carmen", "texto": r["texto"]})


def ver_giro() -> None:
    SIM["giro_visto"] = True
    ir_vista("Preparar propuesta", "Presupuesto")


def escena_aventura() -> None:
    if not SIM["chat"]:
        SIM["chat"].append({"rol": "carmen", "texto": casos.CARMEN_SALUDO})
    st.markdown("## Tu primer día con Talavera Viva")
    html(ui.escena_tienda(SIM["giro"]))
    c1, c2 = st.columns([3, 1], vertical_alignment="center")
    with c1:
        html(f'<p>{ui.chip(casos.ETIQUETA_FICTICIA, "oro")}{ui.chip("Presupuesto: " + mxn(SIM["presupuesto"]), "rojo" if SIM["giro"] else "")}'
             f'{ui.chip("Rol: estrategia comercial y datos")}</p>')
    with c2:
        boton_fuente("w_fuente_caso", "Fuentes", "Ver detalle del caso")

    if SIM["giro"] and not SIM["giro_visto"]:
        html(f'<div class="sw-giro" role="alert"><h3>¡Giro en la historia!</h3><p>{esc(casos.CARMEN_RECORTE)}</p></div>')
        boton("Replanear ahora", key="w_giro_btn", primario=True, on_click=ver_giro)

    vistas = ["Taller", "Hablar con Carmen", "Abrir carpeta de datos", "Preparar propuesta"]
    init_widget("w_vista", "Taller")
    vista = st.segmented_control("Ir a", vistas, key="w_vista", label_visibility="collapsed") or "Taller"

    if vista == "Taller":
        vista_taller()
    elif vista == "Hablar con Carmen":
        vista_carmen()
        panel_tutor("m1")
    elif vista == "Abrir carpeta de datos":
        vista_carpeta()
        panel_tutor("m2")
    else:
        sub = vista_propuesta()
        panel_tutor("m3" if sub == "Presupuesto" else "m4")


def vista_taller() -> None:
    ui.dialogo("Carmen Ruiz · dueña (personaje ficticio)", casos.CARMEN_SALUDO, "carmen")
    c1, c2, c3 = st.columns(3)
    for col, (titulo, desc, icono, destino) in zip((c1, c2, c3), [
        ("Hablar con Carmen", "Pregunta lo que necesites. Ella solo cuenta lo que le preguntas.", "carmen", "Hablar con Carmen"),
        ("Abrir carpeta de datos", "ventas.csv, clientes.csv y costos.csv. ¿Todo cuadra?", "carpeta", "Abrir carpeta de datos"),
        ("Preparar propuesta", "Presupuesto, propuesta y defensa ante Carmen.", "propuesta", "Preparar propuesta"),
    ]):
        with col:
            ui.tarjeta(titulo, f"<p>{esc(desc)}</p>", icono)
            boton(f"Ir: {titulo}", key=f"w_hub_{icono}", primario=True, on_click=ir_vista, args=(destino,))
    st.markdown("#### Tus misiones")
    ui.lista_misiones(estado_misiones())
    panel_tutor(mision_actual())


def vista_carmen() -> None:
    html(f'<div class="sw-dialogo carmen"><div class="avatar">{ui.carmen_svg()}</div><div><b>Carmen Ruiz</b><br>'
         '<span class="sw-fuente">Dueña de Talavera Viva · personaje ficticio · responde según lo que preguntes</span></div></div>')
    caja = st.container()
    pendientes = [q for q in casos.PREGUNTAS_SUGERIDAS if q not in [m["texto"] for m in SIM["chat"] if m["rol"] == "yo"]][:3]
    if pendientes:
        st.caption("Preguntas sugeridas (opcionales):")
        cols = st.columns(len(pendientes))
        for i, (col, q) in enumerate(zip(cols, pendientes)):
            with col:
                boton(q, key=f"w_sug_{i}_{SIM['turnos']}", on_click=preguntar_carmen, args=(q,))
    with st.form("form_carmen", clear_on_submit=True):
        q = st.text_input("Escribe tu pregunta para Carmen", key="w_q_carmen", max_chars=300,
                          placeholder="Ej.: ¿qué clientes dejaron de comprar?")
        if enviar("Enviar a Carmen") and q.strip():
            preguntar_carmen(q)
    with caja:
        for m in SIM["chat"]:
            if m["rol"] == "carmen":
                ui.dialogo("Carmen", m["texto"], "carmen")
            else:
                ui.dialogo(S["perfil"].get("alias") or "Tú", m["texto"], "yo")
    if SIM["revelados"]:
        cats = casos.categorias_descubiertas(SIM["revelados"])
        html('<div class="sw-card"><h3>Tarjetas que descubriste</h3><p>' +
             "".join(ui.chip(h["dato"] or h["id"]) for h in casos.HECHOS if h["id"] in SIM["revelados"] and h["dato"]) +
             f'</p><p class="sw-fuente">Temas clave explorados: {len(cats)} de {len(casos.CATEGORIAS_INVESTIGACION)}</p></div>')


def abrir_archivo(nombre: str) -> None:
    SIM["archivo_activo"] = nombre
    if nombre not in SIM["archivos_abiertos"]:
        SIM["archivos_abiertos"].append(nombre)
    extra = {"clientes": ["clientes_restaurantes", "turistas"], "costos": ["margen_personalizada"]}.get(nombre, [])
    for k in extra:
        if k not in SIM["hallazgos_ok"]:
            SIM["hallazgos_ok"].append(k)
    st.session_state["w_carpeta"] = "Datos"


def vista_carpeta() -> None:
    init_widget("w_carpeta", "Archivos")
    sub = st.segmented_control("Carpeta", ["Archivos", "Datos", "Hallazgos"], key="w_carpeta",
                               label_visibility="collapsed") or "Archivos"
    ventas = sintetico("ventas_talavera.csv")
    if sub == "Archivos":
        st.markdown("Carmen te dejó tres archivos. **Todos son datos sintéticos del caso.**")
        cols = st.columns(3)
        for col, (n, desc) in zip(cols, [("ventas", "Cada venta de abril a septiembre por segmento, producto y canal."),
                                          ("clientes", "Clientes activos, pedidos y ticket promedio por segmento."),
                                          ("costos", "Precio, costo, margen y tiempos de entrega por producto.")]):
            with col:
                abierto = n in SIM["archivos_abiertos"]
                ui.tarjeta(f"{n}.csv", f"<p>{esc(desc)}</p>" + (ui.chip("Abierto", "verde") if abierto else ""), "archivo")
                boton(f"Abrir {n}.csv", key=f"w_abrir_{n}", primario=not abierto, on_click=abrir_archivo, args=(n,))
        return

    if sub == "Datos":
        if not SIM["archivos_abiertos"]:
            st.info("Primero abre un archivo en la pestaña «Archivos».")
            return
        activo = st.selectbox("Archivo", SIM["archivos_abiertos"], format_func=lambda x: f"{x}.csv",
                              index=SIM["archivos_abiertos"].index(SIM["archivo_activo"]) if SIM["archivo_activo"] in SIM["archivos_abiertos"] else 0,
                              key="w_archivo_sel")
        SIM["archivo_activo"] = activo
        if activo == "ventas":
            vista_ventas(ventas)
        else:
            df = sintetico(f"{activo}_talavera.csv")
            tabla(df)
            st.caption("Desliza la tabla horizontalmente para ver todas las columnas.")
            descarga(f"Descargar {activo}.csv", df.to_csv(index=False).encode("utf-8-sig"), f"{activo}.csv", "text/csv",
                     f"w_dl_{activo}")
        return

    vista_hallazgos(ventas)


def vista_ventas(ventas: pd.DataFrame) -> None:
    anomalia_ok = "anomalia" in SIM["hallazgos_ok"]
    limpio = False
    if anomalia_ok:
        limpio = st.toggle("Quitar el registro duplicado que detectaste", key="w_limpio", value=True)
    d = datos.limpiar_duplicados(ventas) if limpio else ventas
    f1, f2, f3 = st.columns(3)
    prod = f1.multiselect("Producto", sorted(ventas["producto"].unique()), key="w_f_prod", placeholder="Todos")
    seg = f2.multiselect("Segmento", sorted(ventas["segmento"].unique()), key="w_f_seg", placeholder="Todos")
    can = f3.multiselect("Canal", sorted(ventas["canal"].unique()), key="w_f_can", placeholder="Todos")
    if prod or seg or can:
        SIM["filtros_usados"] = True
    if prod:
        d = d[d["producto"].isin(prod)]
    if seg:
        d = d[d["segmento"].isin(seg)]
    if can:
        d = d[d["canal"].isin(can)]
    r = datos.resumen_trimestres(d)
    var = "—" if r["variacion_pct"] is None else f"{r['variacion_pct']:+.1f} %"
    c1, c2, c3 = st.columns(3)
    for col, (t, v) in zip((c1, c2, c3), [("Ventas abr–jun (T2)", mxn(r["T2"])), ("Ventas jul–sep (T3)", mxn(r["T3"])),
                                          ("Variación T2 → T3", var)]):
        with col:
            html(f'<div class="sw-card"><span class="sw-fuente">{esc(t)}</span><h3>{esc(v)}</h3></div>')
    st.caption(("Datos sin el duplicado. " if limpio else "Archivo tal como viene. ") +
               f"Filas mostradas: {len(d)}. Carmen dijo −28 %: compruébalo con los datos.")
    if not d.empty:
        resumen = d.groupby(["segmento", "trimestre"], as_index=False)["importe_mxn"].sum()
        try:
            import plotly.express as px

            fig = px.bar(resumen, x="segmento", y="importe_mxn", color="trimestre", barmode="group",
                         color_discrete_map={"2026-T2": "#9DB9F2", "2026-T3": "#1E6BE6"},
                         labels={"importe_mxn": "Ventas (MXN)", "segmento": "", "trimestre": ""})
            fig.update_layout(height=320, margin=dict(l=8, r=8, t=30, b=8), legend=dict(orientation="h", y=1.12),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(family="Nunito, system-ui, sans-serif", size=14, color="#13243F"))
            grafica(fig)
        except ImportError:
            st.bar_chart(resumen.pivot(index="segmento", columns="trimestre", values="importe_mxn"))
    tabla(d, height=320)
    st.caption("Toca el encabezado de una columna para ordenarla. Desliza la tabla para ver más columnas.")
    descarga("Descargar ventas filtradas (CSV)", d.to_csv(index=False).encode("utf-8-sig"), "ventas_filtradas.csv",
             "text/csv", "w_dl_ventas")


def vista_hallazgos(ventas: pd.DataFrame) -> None:
    st.markdown("**Registra lo que encontraste.** Puedes corregir y volver a registrar: estás practicando.")
    h = SIM["hallazgos"]
    segs = sorted(ventas["segmento"].unique())
    tipos = ["Registro duplicado", "Devolución con monto negativo", "Monto en cero", "No encontré nada raro"]
    init_widget("w_h_var", h.get("variacion_reportada"))
    init_widget("w_h_seg", h.get("segmento"))
    init_widget("w_h_tipo", h.get("anomalia_tipo"))
    init_widget("w_h_id", h.get("anomalia_id") or "")
    init_widget("w_h_just", h.get("justificacion_anomalia", ""))
    with st.form("form_hallazgos"):
        st.number_input("Variación de las ventas totales de T2 a T3 (%)", min_value=-100.0, max_value=1000.0,
                        step=0.1, format="%.1f", key="w_h_var", help="Usa signo negativo si bajaron.",
                        **sin_conflicto("w_h_var", value=None))
        st.selectbox("Segmento con mayor caída porcentual", segs, placeholder="Elige un segmento", key="w_h_seg",
                     **sin_conflicto("w_h_seg", index=None))
        st.radio("¿Encontraste algo raro en ventas.csv?", tipos, key="w_h_tipo", **sin_conflicto("w_h_tipo", index=None))
        st.text_input("Si encontraste algo, ¿qué id_venta es? (ej. V-0001)", key="w_h_id", max_chars=10)
        st.text_area("¿Por qué crees que es un problema?", key="w_h_just", max_chars=300, height=80)
        ok = enviar("Registrar hallazgos")
    if ok:
        aid = re.sub(r"\s", "", (st.session_state["w_h_id"] or "").upper())
        if re.fullmatch(r"V-?\d{1,4}", aid):
            aid = "V-" + aid.replace("V", "").replace("-", "").zfill(4)
        h.update({"variacion_reportada": st.session_state["w_h_var"], "segmento": st.session_state["w_h_seg"],
                  "anomalia_tipo": st.session_state["w_h_tipo"], "anomalia_id": aid or None,
                  "justificacion_anomalia": st.session_state["w_h_just"].strip(), "registrado_en": evidencia.ahora_iso()})
        SIM["hallazgos_intentos"] += 1
        SIM["feedback_hallazgos"] = retro_hallazgos(ventas)
    for tipo, txt in SIM.get("feedback_hallazgos", []):
        (st.success if tipo == "ok" else st.info)(txt)


def retro_hallazgos(ventas: pd.DataFrame) -> list[tuple[str, str]]:
    """Retroalimentación formativa de PRÁCTICA (no es la evaluación independiente)."""
    h, out = SIM["hallazgos"], []
    limpio = datos.limpiar_duplicados(ventas)
    v_ok = datos.resumen_trimestres(limpio)["variacion_pct"]
    v_raw = datos.resumen_trimestres(ventas)["variacion_pct"]
    v = evaluacion.parsear_numero(h.get("variacion_reportada"))
    ok_keys = SIM["hallazgos_ok"]

    def marcar(k, bien):
        if bien and k not in ok_keys:
            ok_keys.append(k)
        if not bien and k in ok_keys:
            ok_keys.remove(k)
    if v is None:
        out.append(("info", "Falta tu cálculo de variación."))
        marcar("var_total", False)
    elif abs(v - v_ok) <= evaluacion.TOLERANCIA_PP:
        out.append(("ok", "Tu cálculo coincide con los datos limpios. Ya puedes citarlo en tu propuesta."))
        marcar("var_total", True)
    elif abs(v - v_raw) <= evaluacion.TOLERANCIA_PP:
        out.append(("info", "Tu cálculo coincide con el archivo tal como viene. ¿Cada fila es una venta distinta?"))
        marcar("var_total", False)
    else:
        out.append(("info", "Revisa la fórmula: (T3 − T2) ÷ T2 × 100."))
        marcar("var_total", False)
    dup = datos.id_duplicado(ventas)
    if h.get("anomalia_tipo") == "Registro duplicado" and h.get("anomalia_id") in dup:
        out.append(("ok", f"¡Bien visto! {h['anomalia_id']} aparece dos veces e inflaba el trimestre. En «Datos» ya puedes quitarlo."))
        marcar("anomalia", True)
    elif h.get("anomalia_tipo") in (None, "No encontré nada raro"):
        out.append(("info", "Vale la pena revisar si todos los id_venta son únicos."))
        marcar("anomalia", False)
    else:
        out.append(("info", "Ese registro o ese tipo de problema no parece ser el que afecta los totales. Revisa la columna id_venta."))
        marcar("anomalia", False)
    por_seg = datos.variacion_por(limpio, "segmento").sort_values("variación_%")
    if h.get("segmento") == por_seg.iloc[0]["segmento"]:
        out.append(("ok", "Tu segmento coincide con lo que muestran los datos."))
        marcar("seg_restaurantes", True)
    else:
        out.append(("info", "Filtra por segmento y compara la variación de cada uno."))
        marcar("seg_restaurantes", False)
    return out


def guardar_plan(montos: dict, total: int) -> None:
    SIM["planes"].append({"montos": montos, "total": total, "presupuesto": SIM["presupuesto"], "giro": SIM["giro"],
                          "ts": evidencia.ahora_iso()})


def vista_propuesta() -> str:
    if S.get("_ir_sub"):
        st.session_state["w_sub_prop"] = S.pop("_ir_sub")
    init_widget("w_sub_prop", "Presupuesto")
    sub = st.segmented_control("Etapa", ["Presupuesto", "Propuesta", "Defensa"], key="w_sub_prop",
                               label_visibility="collapsed") or "Presupuesto"
    if sub == "Presupuesto":
        vista_presupuesto()
    elif sub == "Propuesta":
        vista_form_propuesta()
    else:
        vista_defensa()
    return sub


def vista_presupuesto() -> None:
    pres = SIM["presupuesto"]
    ultimo = SIM["planes"][-1]["montos"] if SIM["planes"] else {p["id"]: 0 for p in casos.PROYECTOS}
    st.markdown(f"**Bolsa disponible: {mxn(pres)}.** Reparte el dinero entre las acciones. 0 = no se hace. "
                "Los costos son **supuestos del caso**, no precios de mercado.")
    montos = {}
    cols = st.columns(3)
    for col, p in zip(cols, casos.PROYECTOS):
        k = f"w_m_{p['id']}"
        init_widget(k, int(ultimo.get(p["id"], 0)))
        with col:
            ui.tarjeta(p["nombre"], f"<p>{esc(p['desc'])}</p><p class='sw-fuente'>{esc(p['supuesto'])}</p>")
            montos[p["id"]] = int(st.slider(f"Monto · {p['nombre']}", 0, MAX_PROYECTO[p["id"]], step=5_000, key=k,
                                            format="$%d"))
    total = sum(montos.values())
    ui.semaforo(total, pres)
    excedido = total > pres
    if excedido:
        st.error(f"El total ({mxn(total)}) supera la bolsa de {mxn(pres)}. Reduce algún monto para poder guardar.")
    aj_ok = True
    if SIM["giro"]:
        init_widget("w_ajuste", SIM.get("ajuste_justificacion", ""))
        st.text_area("Tras el recorte: ¿qué sacrificaste o cambiaste y por qué?", key="w_ajuste", max_chars=400, height=90)
        aj_ok = bool(st.session_state["w_ajuste"].strip())
    if boton("Guardar plan", key="w_guardar_plan", primario=True, disabled=excedido or total == 0):
        if not aj_ok:
            st.error("Escribe en una o dos frases qué cambiaste tras el recorte.")
        else:
            if SIM["giro"]:
                SIM["ajuste_justificacion"] = st.session_state["w_ajuste"].strip()
            guardar_plan(montos, total)
            st.success(f"Plan guardado (versión {len(SIM['planes'])}).")
    if SIM["planes"]:
        u = SIM["planes"][-1]
        st.caption(f"Último plan guardado: {mxn(u['total'])} de {mxn(u['presupuesto'])}"
                   + (" · después del recorte" if u["giro"] else ""))
        descarga("Descargar presupuesto (CSV)", portafolio.plan_csv(S), "starwise_presupuesto.csv", "text/csv", "w_dl_plan")


def vista_form_propuesta() -> None:
    pre, post = evaluacion.plan_pre_y_post(SIM["planes"])
    plan = post or pre
    if not plan:
        st.info("Primero guarda un plan en «Presupuesto».")
        return
    citables = casos.datos_citables(SIM["revelados"], SIM["hallazgos_ok"])
    p = SIM["propuesta"]
    claves = {"w_p_diag": p.get("diagnostico", ""), "w_p_datos": [x for x in p.get("datos_citados", []) if x in citables],
              "w_p_sol": p.get("solucion", ""), "w_p_a1": (p.get("acciones") or ["", "", ""])[0],
              "w_p_a2": (p.get("acciones") or ["", "", ""])[1], "w_p_a3": (p.get("acciones") or ["", "", ""])[2],
              "w_p_prio": p.get("accion_prioritaria"), "w_p_seg": p.get("segmento_prioritario"),
              "w_p_just": p.get("justificacion_prioridad", ""), "w_p_kpi": p.get("kpi", ""), "w_p_meta": p.get("meta", ""),
              "w_p_sup": p.get("supuestos", ""), "w_p_rie": p.get("riesgos", ""), "w_p_apo": p.get("aporte", "")}
    for k, v in claves.items():
        init_widget(k, v)
    if len(citables) < 2:
        st.info("Para respaldar tu diagnóstico necesitas datos: pregúntale a Carmen o registra hallazgos en la carpeta.")
    with st.form("form_propuesta"):
        st.text_area("1. Diagnóstico: ¿cuál es el problema principal?", key="w_p_diag", max_chars=500, height=90)
        st.multiselect("2. Datos del caso que lo respaldan (elige al menos 2)", citables, key="w_p_datos",
                       placeholder="Solo aparecen datos que ya descubriste")
        st.text_input("3. Tu solución en una frase", key="w_p_sol", max_chars=200)
        st.markdown("**4. Tres acciones**")
        for i in (1, 2, 3):
            st.text_input(f"Acción {i}", key=f"w_p_a{i}", max_chars=200)
        c1, c2 = st.columns(2)
        c1.selectbox("5. Si solo pudieras hacer una acción del presupuesto…", [x["nombre"] for x in casos.PROYECTOS],
                     placeholder="Elige", key="w_p_prio", **sin_conflicto("w_p_prio", index=None))
        c2.selectbox("…¿a qué segmento la dirigirías?", sorted(datos.VENTAS_SEGMENTO), placeholder="Elige",
                     key="w_p_seg", **sin_conflicto("w_p_seg", index=None))
        st.text_area("¿Por qué esa prioridad, considerando el presupuesto?", key="w_p_just", max_chars=400, height=80)
        c3, c4 = st.columns(2)
        c3.text_input("6. Indicador que Carmen puede revisar", key="w_p_kpi", max_chars=150,
                      placeholder="Ej.: pedidos nuevos de hoteles por semana")
        c4.text_input("Meta a 30 días (con número)", key="w_p_meta", max_chars=100, placeholder="Ej.: de 2 a 4 por semana")
        st.text_area("7. Supuestos (qué das por cierto)", key="w_p_sup", max_chars=300, height=70)
        st.text_area("8. Riesgos (qué podría salir mal)", key="w_p_rie", max_chars=300, height=70)
        st.text_area("9. ¿Qué aportas tú personalmente a este plan?", key="w_p_apo", max_chars=300, height=70)
        st.caption(f"Presupuesto que se adjunta: {mxn(plan['total'])} de {mxn(SIM['presupuesto'])}.")
        ok = enviar("Presentar a Carmen")
    if ok:
        g = st.session_state
        faltan = [n for n, k in [("diagnóstico", "w_p_diag"), ("solución", "w_p_sol"), ("indicador", "w_p_kpi"),
                                 ("meta", "w_p_meta")] if not (g[k] or "").strip()]
        if len(g["w_p_datos"]) < 2:
            faltan.append("al menos 2 datos del caso")
        if not all((g[f"w_p_a{i}"] or "").strip() for i in (1, 2, 3)):
            faltan.append("las tres acciones")
        if not SIM["giro"]:
            st.warning("Carmen quiere revisar algo contigo antes de la junta. Sigue la conversación con ella.")
            return
        if not post or post["total"] > casos.PRESUPUESTO_RECORTE:
            st.error("Tu plan debe actualizarse al presupuesto actual ($60,000). Ve a «Presupuesto» y guarda un plan nuevo.")
            return
        if faltan:
            st.error("Completa: " + ", ".join(faltan) + ".")
            return
        SIM["propuesta"] = {"diagnostico": g["w_p_diag"].strip(), "datos_citados": list(g["w_p_datos"]),
                            "solucion": g["w_p_sol"].strip(), "acciones": [g[f"w_p_a{i}"].strip() for i in (1, 2, 3)],
                            "accion_prioritaria": g["w_p_prio"], "segmento_prioritario": g["w_p_seg"],
                            "justificacion_prioridad": g["w_p_just"].strip(), "kpi": g["w_p_kpi"].strip(),
                            "meta": g["w_p_meta"].strip(), "supuestos": g["w_p_sup"].strip(), "riesgos": g["w_p_rie"].strip(),
                            "aporte": g["w_p_apo"].strip(), "presupuesto_total": post["total"], "enviada_en": evidencia.ahora_iso()}
        S["_ir_sub"] = "Defensa"
        st.rerun()


def vista_defensa() -> None:
    if not SIM["propuesta"]:
        st.info("Primero presenta tu propuesta.")
        return
    ui.dialogo("Carmen", "Gracias, me gusta tener algo por escrito. Antes del lunes, dos preguntas que seguro me hará mi socio: "
                         "si solo pudiéramos hacer UNA de tus acciones, ¿cuál sería y por qué? Y, ¿cómo vamos a saber en 30 días "
                         "si está funcionando?", "carmen")
    d = SIM["defensa"]
    init_widget("w_d_una", d.get("una_accion", ""))
    init_widget("w_d_30", d.get("treinta_dias", ""))
    with st.form("form_defensa"):
        st.text_area("Tu respuesta sobre la prioridad", key="w_d_una", max_chars=400, height=90)
        st.text_area("Tu respuesta sobre cómo medir en 30 días", key="w_d_30", max_chars=400, height=90)
        ok = enviar("Responder a Carmen")
    if ok:
        if not st.session_state["w_d_una"].strip() or not st.session_state["w_d_30"].strip():
            st.error("Responde las dos preguntas de Carmen.")
            return
        SIM["defensa"] = {"una_accion": st.session_state["w_d_una"].strip(),
                          "treinta_dias": st.session_state["w_d_30"].strip(), "ts": evidencia.ahora_iso()}
        ir("resultado_mision")
        st.rerun()


def escena_resultado_mision() -> None:
    SIM["resultado_visto"] = True
    ev = evaluacion.evaluar_simulacion(SIM)["areas"]
    def ok(area, cid):
        return any(c["id"] == cid and c["estado"] == "logrado" for c in ev[area]["criterios"])
    p = SIM["propuesta"]
    frases = []
    if ok("adaptacion", "ad_dentro"):
        frases.append("Me tranquiliza que el plan cabe en los $60,000.")
    if ok("comunicacion", "co_problema"):
        frases.append("Me convence que te apoyes en datos: «" + "» y «".join(p["datos_citados"][:2]) + "».")
    if ok("comunicacion", "co_metrica"):
        frases.append(f"Puedo revisar «{p['kpi']}» en 30 días con una meta clara.")
    if ok("analisis", "an_anomalia"):
        frases.append("Y gracias por avisarme del registro duplicado: mi reporte inflaba las ventas.")
    else:
        frases.append("Me quedé con la duda de si mis datos están bien registrados.")
    if not ok("comunicacion", "co_metrica"):
        frases.append("Me falta saber exactamente cómo mediremos el avance.")
    frases.append("No sé si esto recuperará las ventas —eso solo se sabe en la práctica—, pero ya tengo algo concreto para el lunes.")
    st.markdown("## Resultado de la misión")
    ui.dialogo("Carmen", " ".join(frases), "carmen")
    ui.dialogo("Chispa", "En esta misión practicaste: hacer preguntas antes de proponer, calcular una variación porcentual, "
                         "revisar la calidad de los datos, priorizar con un presupuesto limitado y definir un indicador "
                         "controlable. Es una simulación: no se midió ningún resultado comercial real.", "chispa", "logro")
    conductas = evaluacion.conductas_observadas(SIM)
    if conductas:
        html('<div class="sw-card"><h3>Conductas observadas en esta simulación</h3><ul>' +
             "".join(f"<li>{esc(c)}</li>" for c in conductas) + "</ul></div>")
    st.write("")
    st.markdown("**Último reto:** una demostración breve, sin ayuda, con otra empresa ficticia.")
    boton("Ir a la demostración final", key="w_res_B", primario=True, on_click=ir, args=("prueba_B",))


# ---------------------------------------------------------------------------
# CAPÍTULO 6 · Reflexión, logros, portafolio, siguiente paso, cierre
# ---------------------------------------------------------------------------
def escena_reflexion() -> None:
    ui.dialogo("Chispa", "¡Lo lograste! Antes de ver tus resultados, una pausa para ti.", "chispa", "feliz")
    init_widget("w_autoef2", S.get("autoeficacia_despues") or S.get("autoeficacia_antes") or 3)
    init_widget("w_cambio", S["cambio_interes"].get("respuesta"))
    init_widget("w_cambio_raz", S["cambio_interes"].get("razones", ""))
    with st.form("form_reflexion"):
        st.slider("Ahora, ¿qué tan capaz te sientes de analizar datos de un negocio y proponer una solución?", 1, 5,
                  key="w_autoef2", help="1 = nada capaz · 5 = muy capaz")
        st.caption("Opinión subjetiva: no mide aprendizaje.")
        st.radio("Después de vivir el rol, tu interés en «estrategia comercial y datos»…",
                 ["Aumentó", "Sigue igual", "Disminuyó", "Aún no lo sé"], key="w_cambio",
                 **sin_conflicto("w_cambio", index=None))
        st.text_area("¿Por qué?", key="w_cambio_raz", max_chars=400, height=80)
        ok = enviar("Ver mis resultados")
    if ok:
        if not st.session_state["w_cambio"]:
            st.error("Elige una opción sobre tu interés.")
            return
        S["autoeficacia_despues"] = int(st.session_state["w_autoef2"])
        S["cambio_interes"] = {"interes_antes": S.get("interes_rol_antes"), "respuesta": st.session_state["w_cambio"],
                               "razones": st.session_state["w_cambio_raz"].strip(), "expectativa_previa": S.get("expectativa_rol")}
        ir("logros")
        st.rerun()


def escena_logros() -> None:
    A, B = S["A"].get("resultado"), S["B"].get("resultado")
    ui.hero("¡Misión completada!", "Talavera Viva ya tiene un plan para el lunes.", "Esto es lo que se observó, con evidencia.",
            "logro")
    comp = evaluacion.comparar_AB(A, B)
    ev = evaluacion.evaluar_simulacion(SIM)
    c1, c2, c3 = st.columns(3)
    with c1:
        cuerpo = "<p class='sw-fuente'>Diagnóstico A y demostración B, sin tutor.</p><ul>"
        if comp:
            cuerpo += "".join(f"<li><b>{esc(f['criterio'])}:</b> {esc(f['cambio'])}</li>" for f in comp["filas"])
        cuerpo += "</ul>"
        ui.tarjeta("Lo que demostraste por tu cuenta", cuerpo, "datos")
    with c2:
        cuerpo = "<p class='sw-fuente'>Práctica con datos, Carmen y pistas.</p><ul>" + "".join(
            f"<li><b>{esc(a['nombre'])}:</b> {esc(a['nivel'])}</li>" for a in ev["areas"].values()) + "</ul>"
        ui.tarjeta("Lo que aplicaste en el caso", cuerpo, "propuesta")
    with c3:
        pistas = sum(S["pistas"].values())
        cuerpo = (f"<p>Autoconfianza: <b>{esc(S.get('autoeficacia_antes'))}/5 → {esc(S.get('autoeficacia_despues'))}/5</b></p>"
                  "<p class='sw-fuente'>Tu opinión; no mide aprendizaje.</p>"
                  f"<p>Apoyo usado: <b>{pistas}</b> pista(s) · {len(S['tutor_log'])} consulta(s) a Chispa.</p>")
        ui.tarjeta("Cómo te ves y qué apoyo usaste", cuerpo, "carmen")
    if comp:
        try:
            import plotly.graph_objects as go

            fig = go.Figure(go.Bar(x=["Diagnóstico A", "Demostración B"], y=[comp["logrados_A"], comp["logrados_B"]],
                                   marker_color=["#9DB9F2", "#1E6BE6"], text=[comp["logrados_A"], comp["logrados_B"]],
                                   textposition="outside"))
            fig.update_layout(height=260, yaxis=dict(range=[0, comp["total"] + 0.6], dtick=1, title=f"Criterios observados (de {comp['total']})"),
                              margin=dict(l=8, r=8, t=16, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(family="Nunito, system-ui, sans-serif", size=14, color="#13243F"))
            grafica(fig)
        except ImportError:
            st.bar_chart(pd.DataFrame({"criterios": [comp["logrados_A"], comp["logrados_B"]]}, index=["A", "B"]))
        st.caption(comp["nota"] + " La justificación escrita queda pendiente de revisión humana.")
    st.markdown("#### Insignias")
    cols = st.columns(5)
    for col, b in zip(cols, evaluacion.insignias(SIM, A, B)):
        with col:
            ui.insignia(b["nombre"], b["desc"], b["obtenida"])
    with st.expander("Ver criterios y evidencia de cada área"):
        for a in ev["areas"].values():
            st.markdown(f"**{a['nombre']} · {a['nivel']}**")
            for c in a["criterios"]:
                st.markdown(f"- {c['etiqueta']}: {c['descripcion']} — _{c['evidencia']}_")
    est = ia.estado_ia(S["ia_control"])
    if est["disponible"] and comp and S.get("feedback_ia_B") is None:
        if boton("Pedir un comentario de Chispa (IA generativa)", key="w_fb_ia"):
            resumen = "; ".join(f"{f['criterio']}: {f['cambio']}" for f in comp["filas"])
            S["feedback_ia_B"] = ia.feedback_cualitativo_B(resumen, S["ia_control"]) or {"texto": "", "fuente": "sin_respuesta"}
            st.rerun()
    if S.get("feedback_ia_B") and S["feedback_ia_B"].get("texto"):
        ui.dialogo("Chispa · IA generativa (no modifica resultados)", S["feedback_ia_B"]["texto"], "chispa", "feliz")
    boton("Ver mi portafolio", key="w_logros_sig", primario=True, on_click=ir, args=("portafolio",))


def _slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", datos.quitar_tildes((s or "sin-alias").lower())).strip("-")
    return s[:30] or "sin-alias"


def escena_portafolio() -> None:
    st.markdown("## Tu portafolio de misión")
    etiqueta = ia.estado_ia(S["ia_control"])["etiqueta"]
    ui.dialogo("Chispa", "Aquí está todo lo que hiciste, contado con honestidad: lo que se observó, lo que no se midió y "
                         "la ayuda que usaste.", "chispa", "feliz")
    frase = portafolio.frase_cv(S)
    html(f'<div class="sw-card"><h3>Frase para tu CV (fiel a lo que hiciste)</h3><p>{esc(frase)}</p>'
         '<p class="sw-fuente">No la presentes como empleo ni práctica en Talavera Viva: es una simulación académica.</p></div>')
    fecha = datetime.now().strftime("%Y%m%d")
    alias = _slug(S["perfil"].get("alias"))
    c1, c2 = st.columns(2)
    with c1:
        descarga("Descargar portafolio (HTML imprimible)", portafolio.portafolio_html(S, etiqueta).encode("utf-8"),
                 f"starwise_portafolio_{alias}_{fecha}.html", "text/html", "w_dl_html", primario=True)
        descarga("Descargar propuesta (TXT)", portafolio.propuesta_txt(S).encode("utf-8"),
                 f"starwise_propuesta_{alias}_{fecha}.txt", "text/plain", "w_dl_txt")
    with c2:
        reg = evidencia.construir_registro(S, etiqueta)
        descarga("Descargar evidencia (JSON)", evidencia.a_json(reg).encode("utf-8"),
                 f"starwise_evidencia_{S['intento']['attempt_id'][:8]}.json", "application/json", "w_dl_json")
        descarga("Descargar presupuesto (CSV)", portafolio.plan_csv(S), f"starwise_presupuesto_{alias}_{fecha}.csv",
                 "text/csv", "w_dl_plan2")
    st.caption("En el celular, el archivo se guarda en Descargas o se abre en una pestaña nueva según tu navegador. "
               "El HTML se puede imprimir o guardar como PDF desde el navegador.")
    boton("Tu siguiente paso hacia tu primer ingreso", key="w_port_sig", primario=True, on_click=ir, args=("siguiente_paso",))


def escena_siguiente_paso() -> None:
    st.markdown("## Tu siguiente paso hacia tu primer ingreso")
    ev = evaluacion.evaluar_simulacion(SIM)
    st.markdown("#### 1 · Requisitos típicos del rol (ilustrativos)")
    html("<div class='sw-card'><ul><li>Hojas de cálculo: tablas dinámicas, filtros y fórmulas básicas.</li>"
         "<li>Leer ventas por segmento y calcular variaciones e indicadores.</li><li>Explicar una propuesta por escrito y en voz alta.</li>"
         "<li>Nociones de mercadotecnia digital y atención a clientes empresariales.</li></ul>"
         "<p class='sw-fuente'>Lista ilustrativa elaborada por el equipo; no proviene de vacantes concretas.</p></div>")
    st.markdown("#### 2 · Lo que mostraste y lo que aún no se observó")
    mostradas = [c["descripcion"] for a in ev["areas"].values() for c in a["criterios"] if c["estado"] == "logrado"]
    pendientes = [c["descripcion"] for a in ev["areas"].values() for c in a["criterios"] if c["estado"] == "no_observado"]
    c1, c2 = st.columns(2)
    with c1:
        ui.tarjeta("Observado en esta simulación", "<ul>" + ("".join(f"<li>{esc(x)}</li>" for x in mostradas) or "<li>—</li>") + "</ul>")
    with c2:
        ui.tarjeta("Aún no observado aquí", "<ul>" + ("".join(f"<li>{esc(x)}</li>" for x in pendientes) or "<li>—</li>") + "</ul>"
                   "<p class='sw-fuente'>No es un déficit tuyo: solo no se vio en este caso.</p>")
    st.markdown("#### 3 · Tu plan de 2–3 acciones (edítalo)")
    sugeridas = S["plan_accion"] or ["Practicar tablas dinámicas con un dataset abierto durante 2 semanas.",
                                     "Construir un segundo proyecto de análisis de ventas y agregarlo a mi portafolio.",
                                     "Preguntar en mi universidad por prácticas profesionales o estadías con convenio."]
    for i in range(3):
        init_widget(f"w_pa_{i}", sugeridas[i] if i < len(sugeridas) else "")
    with st.form("form_plan_accion"):
        for i in range(3):
            st.text_input(f"Acción {i + 1}", key=f"w_pa_{i}", max_chars=200)
        if enviar("Guardar mi plan", primario=False):
            S["plan_accion"] = [st.session_state[f"w_pa_{i}"].strip() for i in range(3) if st.session_state[f"w_pa_{i}"].strip()]
            st.success("Plan guardado. Aparecerá en tu portafolio y evidencia.")

    st.markdown("#### 4 · ¿Qué hace digno un primer empleo?")
    cols = st.columns(4)
    for col, (t, d) in zip(cols, [("Pago", "Que sea claro, puntual y por escrito; compáralo con el costo de vida de tu ciudad."),
                                  ("Prestaciones", "Seguridad social y prestaciones de ley desde el inicio."),
                                  ("Condiciones y horarios", "Contrato, jornada definida y trato respetuoso."),
                                  ("Aprendizaje", "Que te enseñen y puedas crecer, no solo «hacer bulto».")]):
        with col:
            ui.tarjeta(t, f"<p>{esc(d)}</p>", "digno")
    sp = indicador_verificado("sin_prestaciones")
    ps = indicador_verificado("primer_salario_10k")
    with st.container(border=True):
        if sp:
            st.markdown(f"**{esc(sp['valor_mostrado'])}** de las personas egresadas que respondieron la Encuesta Nacional de "
                        "Egresados 2025 de la UVM **no tuvo prestaciones en su primer empleo**. Por eso vale la pena preguntar "
                        "por ellas antes de aceptar.")
            if ps:
                st.markdown(f"En la misma encuesta, {esc(ps['valor_csv'])} reportó un primer salario de hasta $10,000 al mes. "
                            "Es contexto de quienes respondieron, no el salario típico de una carrera ni una predicción del tuyo.")
            st.caption(f"Encuesta no probabilística · {sp['calidad']}. No existe un umbral universal de «salario digno» en esta app.")
        else:
            st.markdown("El dato de prestaciones del repositorio no está disponible o no coincide con el valor esperado, así "
                        "que no lo mostramos. Revisa Metodología → Fuentes.")
        boton_fuente("w_fuente_digno")
    st.markdown("#### 5 · Dónde buscar")
    html("<div class='sw-card'><ul><li>Bolsa de trabajo y oficina de prácticas profesionales de tu universidad.</li>"
         "<li>Programas de estadías o servicio social con convenio institucional.</li>"
         "<li>Antes de aceptar: pide por escrito sueldo, prestaciones, horario y actividades.</li></ul>"
         "<p class='sw-fuente'>Instrucciones generales. STARWISE no está conectado a ninguna bolsa de empleo: no mostramos "
         "vacantes, coincidencias ni reclutadores.</p></div>")
    st.caption("Esta pantalla convierte lo que practicaste en un siguiente paso; el efecto sobre tu ingreso futuro no está medido.")
    boton("Terminar y dar mi opinión", key="w_sig_cierre", primario=True, on_click=ir, args=("cierre",))


def escena_cierre() -> None:
    ui.hero("¡Gracias por jugar!", "Tu opinión nos ayuda a mejorar STARWISE.", "Toma 1 minuto.", "feliz")
    e = S["encuesta"]
    init_widget("w_e_rel", e.get("relevancia") or 3)
    init_widget("w_e_cla", e.get("claridad") or 3)
    init_widget("w_e_com", e.get("comentario", ""))
    init_widget("w_e_cv", e.get("usaria_cv"))
    with st.form("form_encuesta"):
        st.slider("¿Qué tan relevante fue la experiencia para tu formación? (1–5)", 1, 5, key="w_e_rel")
        st.slider("¿Qué tan claro fue qué tenías que hacer? (1–5)", 1, 5, key="w_e_cla")
        st.radio("¿Usarías tu portafolio en tu CV?", ["Sí", "Tal vez", "No"], key="w_e_cv", horizontal=True,
                 **sin_conflicto("w_e_cv", index=None))
        st.text_area("Comentario (qué te confundió, qué falló, qué mejorarías)", key="w_e_com", max_chars=600, height=90)
        st.caption("Es una encuesta de opinión; no equivale a aprendizaje medido.")
        ok = enviar("Guardar mi opinión")
    if ok:
        S["encuesta"] = {"relevancia": int(st.session_state["w_e_rel"]), "claridad": int(st.session_state["w_e_cla"]),
                         "usaria_cv": st.session_state["w_e_cv"], "comentario": st.session_state["w_e_com"].strip(),
                         "ts": evidencia.ahora_iso()}
        st.success("¡Guardado! Ahora descarga tu evidencia.")
    reg = evidencia.construir_registro(S, ia.estado_ia(S["ia_control"])["etiqueta"])
    descarga("Descargar mi evidencia (JSON)", evidencia.a_json(reg).encode("utf-8"),
             f"starwise_evidencia_{S['intento']['attempt_id'][:8]}.json", "application/json", "w_dl_final", primario=True)
    st.caption("Si participas en una prueba con facilitador, entrégale este archivo. Nada se guardó en el servidor.")


# ---------------------------------------------------------------------------
# Panel del equipo (facilitador)
# ---------------------------------------------------------------------------
def iniciar_externa(alias: str) -> None:
    st.session_state.clear()
    st.session_state["S"] = estado_inicial("externa_confirmada", alias)


def escena_facilitador() -> None:
    st.markdown("## Panel del equipo")
    clave = ia._leer_config("FACILITADOR_PASSWORD")
    if clave and not st.session_state.get("fac_ok"):
        with st.form("form_fac_login"):
            pw = st.text_input("Contraseña del facilitador", type="password", key="w_fac_pw")
            if enviar("Entrar"):
                if hmac.compare_digest(pw.encode(), clave.encode()):
                    st.session_state["fac_ok"] = True
                    st.rerun()
                st.error("Contraseña incorrecta.")
        boton("← Volver al juego", key="w_fac_volver0", on_click=ir, args=(S.get("escena_previa", "inicio"),))
        return
    st.caption("Este panel no guarda nada en el servidor: solo analiza los archivos JSON que cargues en esta sesión."
               + ("" if clave else " Sin FACILITADOR_PASSWORD configurada: no subas aquí datos sensibles en una app pública."))
    with st.container(border=True):
        st.markdown(f"**Sesión actual:** intento `{S['intento']['attempt_id'][:8]}` · tipo «{evidencia.TIPOS[S['tipo_registro']]}» · "
                    f"escena «{S.get('escena_previa')}»")
    with st.expander("Comenzar prueba con persona externa", expanded=False):
        st.markdown("Reinicia la app para una persona nueva y marca el intento como **externa** solo si tú lo declaras.")
        with st.form("form_externa"):
            alias = st.text_input("Alias de la persona (sin nombre completo)", key="w_ext_alias", max_chars=30)
            decl = st.checkbox("Declaro como facilitador que esta persona no forma parte del equipo y aceptó participar.",
                               key="w_ext_decl")
            if enviar("Comenzar prueba externa"):
                if not decl:
                    st.error("Se necesita tu declaración para marcarla como externa.")
                else:
                    iniciar_externa(alias.strip())
                    st.rerun()
    with st.expander("Protocolo de prueba (10–20 min)"):
        st.markdown("1. Explica que es un prototipo y que puede dejar de participar cuando quiera; tiempo extra sin penalización.\n"
                    "2. Observa sin ayudar: ¿entiende la elección de ruta?, ¿navega?, ¿manipula los datos?, ¿exporta el portafolio?\n"
                    "3. Anota fallos y comentarios tal como ocurren; no registres mejoras que no observaste.\n"
                    "4. Al final pide que descargue su evidencia JSON y te la entregue.\n"
                    "5. Recuerda: la encuesta es opinión subjetiva, no aprendizaje medido.")
    st.markdown("### Importar evidencias")
    archivos = st.file_uploader("Archivos JSON de evidencia", type=["json"], accept_multiple_files=True, key="w_fac_up")
    regs, errores = evidencia.leer_registros([(a.name, a.getvalue()) for a in (archivos or [])])
    for e_ in errores:
        st.warning(e_)
    df = evidencia.consolidar(regs) if regs else pd.DataFrame()
    if df.empty:
        html('<div class="sw-card"><h3>Aún no hay pruebas</h3><p>Carga uno o varios JSON exportados por participantes.</p></div>')
    else:
        m = evidencia.metricas(df)
        st.markdown(f"**Registros únicos:** {m['n_total']} · **reales:** {m['n_reales']} · **externas confirmadas:** "
                    f"{m['n_externas_confirmadas']} · **completaron B:** {m['n_completaron_B']} · "
                    f"**QA sintéticos excluidos:** {m['n_sinteticos_excluidos']}")
        st.caption(f"Opinión promedio (solo reales) · relevancia: {m['relevancia_promedio']} · claridad: {m['claridad_promedio']}. "
                   "Son percepciones, no aprendizaje.")
        tabla(df)
        descarga("Exportar consolidado (CSV)", df.to_csv(index=False).encode("utf-8-sig"), "starwise_consolidado.csv",
                 "text/csv", "w_fac_csv", primario=True)
    st.markdown("### Pruebas de QA")
    descarga("Descargar registro de QA sintético (synthetic_test)", evidencia.a_json(evidencia.registro_qa_sintetico()).encode("utf-8"),
             "starwise_QA_synthetic_test.json", "application/json", "w_fac_qa")
    st.caption("Los registros synthetic_test se excluyen de las métricas de usuarios reales.")
    boton("← Volver al juego", key="w_fac_volver", on_click=ir, args=(S.get("escena_previa", "inicio"),))


# ---------------------------------------------------------------------------
# Enrutador
# ---------------------------------------------------------------------------
ESCENA_FN = {
    "inicio": escena_inicio, "perfil": escena_perfil, "rutas": escena_rutas, "expectativa": escena_expectativa,
    "diag_A": lambda: escena_micro("A"), "aventura": escena_aventura, "resultado_mision": escena_resultado_mision,
    "prueba_B": lambda: escena_micro("B"), "reflexion": escena_reflexion, "logros": escena_logros,
    "portafolio": escena_portafolio, "siguiente_paso": escena_siguiente_paso, "cierre": escena_cierre,
    "facilitador": escena_facilitador,
}


def main() -> None:
    subir_al_inicio()
    barra_superior()
    ESCENA_FN.get(S["escena"], escena_inicio)()
    ui.pie()


main()
