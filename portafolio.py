"""STARWISE · portafolio.py

Exportaciones del estudiante: portafolio HTML imprimible (todo el texto del
usuario se ESCAPA con html.escape), propuesta en TXT, plan de presupuesto en CSV
y frase para CV fiel a lo que hizo, sin atribuir empleo real.
"""
from __future__ import annotations

import html
import io
from datetime import datetime

import pandas as pd

import casos
import evaluacion

ROL_SIMULADO = "Estrategia comercial y datos (rol simulado)"


def e(x: object) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def _plan_final(sim: dict) -> dict | None:
    pre, post = evaluacion.plan_pre_y_post(sim.get("planes", []))
    return post or pre


def frase_cv(S: dict) -> str:
    sim = S.get("sim", {})
    ev = evaluacion.evaluar_simulacion(sim)["areas"]
    partes = ["Completé una simulación académica en STARWISE con un caso de empresa ficticia (Talavera Viva) y datos sintéticos:"]
    hechos = []
    if any(c["id"] == "an_anomalia" and c["estado"] == "logrado" for c in ev["analisis"]["criterios"]):
        hechos.append("revisé la calidad de un archivo de ventas y detecté un registro duplicado")
    if any(c["id"] == "an_variacion" and c["estado"] == "logrado" for c in ev["analisis"]["criterios"]):
        hechos.append("calculé la variación trimestral de ventas")
    plan = _plan_final(sim)
    if plan and plan["total"] <= sim.get("presupuesto", casos.PRESUPUESTO_INICIAL):
        hechos.append(f"replaneé un presupuesto de ${plan['total']:,} MXN ante un recorte" if sim.get("giro")
                      else f"armé un plan de ${plan['total']:,} MXN")
    if any(c["id"] == "co_metrica" and c["estado"] == "logrado" for c in ev["comunicacion"]["criterios"]):
        hechos.append("propuse indicadores medibles a 30 días")
    if not hechos:
        hechos.append("practiqué análisis de un caso de negocio")
    return partes[0] + " " + "; ".join(hechos) + "."


def propuesta_txt(S: dict) -> str:
    sim = S.get("sim", {})
    p = sim.get("propuesta", {})
    d = sim.get("defensa", {})
    plan = _plan_final(sim)
    lineas = [
        "STARWISE · Propuesta al consejo de Talavera Viva",
        "Simulación académica · Empresa ficticia · Datos de práctica",
        f"Alias: {S.get('perfil', {}).get('alias') or 'Sin alias'}",
        "",
        f"Diagnóstico: {p.get('diagnostico', '')}",
        "Datos del caso citados:", *[f"  - {x}" for x in p.get("datos_citados", [])],
        f"Solución en una frase: {p.get('solucion', '')}",
        "Acciones:", *[f"  {i}. {a}" for i, a in enumerate(p.get("acciones", []), 1)],
        f"Prioridad: {p.get('accion_prioritaria', '')} → segmento {p.get('segmento_prioritario', '')}",
        f"Justificación: {p.get('justificacion_prioridad', '')}",
        f"Indicador: {p.get('kpi', '')} · Meta a 30 días: {p.get('meta', '')}",
        f"Supuestos: {p.get('supuestos', '')}",
        f"Riesgos: {p.get('riesgos', '')}",
        f"Aporte personal: {p.get('aporte', '')}",
        "",
        "Presupuesto final:",
    ]
    if plan:
        for pr in casos.PROYECTOS:
            lineas.append(f"  {pr['nombre']}: ${plan['montos'].get(pr['id'], 0):,}")
        lineas.append(f"  Total: ${plan['total']:,} de ${sim.get('presupuesto', 0):,}")
    lineas += ["", "Defensa ante Carmen:", f"  Si solo una acción: {d.get('una_accion', '')}",
               f"  ¿Cómo sabremos en 30 días?: {d.get('treinta_dias', '')}", "",
               "Limitación: simulación académica, no práctica laboral formal."]
    return "\n".join(lineas)


def plan_csv(S: dict) -> bytes:
    sim = S.get("sim", {})
    filas = []
    for i, p in enumerate(sim.get("planes", []), 1):
        for pr in casos.PROYECTOS:
            filas.append({"version_plan": i, "despues_del_recorte": p.get("giro"), "guardado_en": p.get("ts"),
                          "proyecto": pr["nombre"], "monto_mxn": p["montos"].get(pr["id"], 0),
                          "total_plan_mxn": p["total"], "presupuesto_vigente_mxn": p["presupuesto"],
                          "nota": "Costos = supuestos del caso ficticio"})
    df = pd.DataFrame(filas or [{"nota": "Sin planes guardados"}])
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8-sig")


def _criterios_html(criterios: list[dict]) -> str:
    return "".join(f"<li><b>{e(c['etiqueta'])}</b> · {e(c['descripcion'])}<br><small>{e(c['evidencia'])}</small></li>"
                   for c in criterios)


def portafolio_html(S: dict, etiqueta_tutor: str) -> str:
    sim = S.get("sim", {})
    perfil = S.get("perfil", {})
    ev = evaluacion.evaluar_simulacion(sim)
    A = (S.get("A") or {}).get("resultado")
    B = (S.get("B") or {}).get("resultado")
    comp = evaluacion.comparar_AB(A, B)
    p = sim.get("propuesta", {})
    plan = _plan_final(sim)
    fecha = datetime.now().strftime("%d/%m/%Y")

    areas = "".join(f"<section class='card'><h3>{e(a['nombre'])}</h3><p class='nivel'>{e(a['nivel'])}</p>"
                    f"<ul>{_criterios_html(a['criterios'])}</ul></section>" for a in ev["areas"].values())
    if comp:
        filas = "".join(f"<tr><td>{e(f['criterio'])}</td><td>{e(f['A'])}</td><td>{e(f['B'])}</td><td>{e(f['cambio'])}</td></tr>"
                        for f in comp["filas"])
        ab = (f"<div class='tabla'><table><thead><tr><th>Criterio</th><th>A</th><th>B</th><th>Cambio observado</th></tr></thead>"
              f"<tbody>{filas}</tbody></table></div><p class='nota'>{e(comp['nota'])}</p>")
    else:
        ab = "<p class='nota'>La comparación A/B solo aparece cuando ambas demostraciones están completas.</p>"
    plan_html = ""
    if plan:
        plan_html = "<ul>" + "".join(f"<li>{e(pr['nombre'])}: ${plan['montos'].get(pr['id'], 0):,}</li>" for pr in casos.PROYECTOS)
        plan_html += f"</ul><p><b>Total:</b> ${plan['total']:,} de ${sim.get('presupuesto', 0):,} (costos = supuestos del caso)</p>"
    pistas = S.get("pistas", {})
    conductas = "".join(f"<li>{e(c)}</li>" for c in ev["conductas"]) or "<li>Sin conductas registradas aún.</li>"
    acciones = "".join(f"<li>{e(a)}</li>" for a in p.get("acciones", []) if a)
    citados = "".join(f"<li>{e(x)}</li>" for x in p.get("datos_citados", []))
    lim = "".join(f"<li>{e(x)}</li>" for x in [
        "Simulación académica, no práctica laboral formal ni experiencia laboral.",
        "Empresa, clienta y datos ficticios (Talavera Viva no existe).",
        "No es certificación oficial ni garantiza empleo o ingresos.",
        "Rúbrica sin validación psicométrica; textos abiertos pendientes de revisión humana.",
        "La autoeficacia es opinión subjetiva y no mide aprendizaje.",
    ])
    plan_accion = "".join(f"<li>{e(a)}</li>" for a in S.get("plan_accion", []) if a)

    return f"""<!DOCTYPE html><html lang="es-MX"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Portafolio STARWISE · {e(perfil.get('alias') or 'Sin alias')}</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;font-family:Nunito,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
background:#F7FAFF;color:#13243F;font-size:16px;line-height:1.5;overflow-wrap:anywhere}}
main{{width:100%;max-width:56rem;margin:0 auto;padding:1rem}}
header{{background:#1E6BE6;color:#fff;border-radius:1.25rem;padding:1.25rem;box-shadow:0 .4rem 0 #1550B8}}
header h1{{margin:0;font-size:clamp(1.4rem,4vw,2rem)}} .chip{{display:inline-block;background:#FFC800;color:#13243F;
border-radius:999px;padding:.2rem .7rem;font-weight:800;font-size:.85rem;margin-top:.5rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,16rem),1fr));gap:1rem;margin-top:1rem}}
.card{{background:#fff;border:2px solid #DCE7FB;border-radius:1rem;padding:1rem;box-shadow:0 .25rem 0 #DCE7FB}}
h2{{margin:1.5rem 0 .5rem;font-size:1.25rem}} h3{{margin:0 0 .25rem;font-size:1.05rem}}
.nivel{{font-weight:800;color:#1550B8;margin:0 0 .5rem}} small{{color:#4A5B78}}
.tabla{{width:100%;overflow-x:auto}} table{{border-collapse:collapse;width:100%;min-width:30rem}}
th,td{{border-bottom:1px solid #DCE7FB;padding:.5rem;text-align:left;vertical-align:top}}
.nota{{color:#4A5B78;font-size:.9rem}} .cv{{background:#FFF6D1;border-left:.4rem solid #FFC800;padding:1rem;border-radius:.75rem}}
@media print{{body{{background:#fff}} header{{box-shadow:none}} .card{{break-inside:avoid;box-shadow:none}}}}
</style></head><body><main>
<header><h1>Portafolio de misión · STARWISE</h1>
<div>{e(perfil.get('alias') or 'Sin alias')} · {e(fecha)} · Rol: {e(ROL_SIMULADO)}</div>
<span class="chip">Simulación académica · Empresa ficticia · Datos de práctica</span></header>

<h2>Misión</h2>
<div class="card"><p><b>Caso:</b> Talavera Viva (empresa ficticia de cerámica en Puebla). Clienta simulada: Carmen Ruiz.</p>
<p><b>Objetivo:</b> proponer cómo recuperar parte de las ventas (−28 % en el caso) sin despedir personal, con un presupuesto que bajó de $150,000 a $60,000 MXN.</p></div>

<h2>Entregables</h2>
<div class="grid">
<section class="card"><h3>Diagnóstico y datos citados</h3><p>{e(p.get('diagnostico') or 'Sin diagnóstico registrado.')}</p><ul>{citados}</ul></section>
<section class="card"><h3>Solución y acciones</h3><p>{e(p.get('solucion') or '—')}</p><ol>{acciones}</ol>
<p><b>Indicador:</b> {e(p.get('kpi') or '—')} · <b>Meta:</b> {e(p.get('meta') or '—')}</p></section>
<section class="card"><h3>Presupuesto final</h3>{plan_html or '<p>Sin plan guardado.</p>'}</section>
<section class="card"><h3>Supuestos y riesgos</h3><p><b>Supuestos:</b> {e(p.get('supuestos') or '—')}</p><p><b>Riesgos:</b> {e(p.get('riesgos') or '—')}</p></section>
</div>

<h2>Criterios observados en la práctica asistida</h2>
<p class="nota">Niveles: Inicial · En desarrollo · Aplicado en el caso · Requiere revisión. Versión de rúbrica: {e(evaluacion.RUBRIC_VERSION)}.</p>
<div class="grid">{areas}</div>
<h2>Conductas observadas en esta simulación</h2><div class="card"><ul>{conductas}</ul></div>

<h2>Demostración independiente (A vs B, sin tutor)</h2><div class="card">{ab}</div>

<h2>Apoyo utilizado</h2><div class="card"><p>Modo de tutor: {e(etiqueta_tutor)}. Pistas por misión: {e(', '.join(f'{k}: {v}' for k, v in pistas.items()) or 'ninguna')}.</p>
<p class="nota">Usar pistas no resta puntos; se reporta para transparencia.</p></div>

<h2>Autopercepción</h2><div class="card"><p>Antes: {e(S.get('autoeficacia_antes', '—'))}/5 · Después: {e(S.get('autoeficacia_despues', '—'))}/5</p>
<p class="nota">Opinión subjetiva; no mide competencia.</p></div>

<h2>Mi siguiente paso</h2><div class="card"><ul>{plan_accion or '<li>Sin plan registrado.</li>'}</ul></div>

<h2>Frase para CV (fiel a lo que hiciste)</h2><p class="cv">{e(frase_cv(S))}</p>
<h2>Limitaciones</h2><div class="card"><ul>{lim}</ul></div>
</main></body></html>"""
