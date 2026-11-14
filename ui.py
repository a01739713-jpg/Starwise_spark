"""STARWISE · ui.py

Identidad visual de Starwise/Chispa: videojuego educativo por episodios, no
dashboard. CSS responsive mobile-first (360 · 390 · 430 · 768 · 1280 px), sin
fuentes remotas, sin anchos fijos en px para contenedores, objetivos táctiles de
44 px como mínimo, y animaciones que respetan prefers-reduced-motion.
Todo el texto del usuario que pasa por HTML se escapa con `esc()`.
"""
from __future__ import annotations

import html as _html
import re

import streamlit as st

from chispa import chispa_svg

AZUL, AZUL_SOMBRA, DORADO, TEXTO, FONDO = "#1E6BE6", "#1550B8", "#FFC800", "#13243F", "#F7FAFF"

ETAPAS = ["Explorar", "Practicar", "Demostrar", "Próximo paso"]


def esc(x: object) -> str:
    return _html.escape("" if x is None else str(x), quote=True)


def html(fragmento: str) -> None:
    """Inserta HTML propio. Quita sangrías y líneas vacías para que Markdown no lo convierta en código."""
    limpio = "\n".join(l.strip() for l in fragmento.splitlines() if l.strip())
    st.markdown(limpio, unsafe_allow_html=True)


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@600;800;900&display=swap');
:root{{--sw-azul:{AZUL};--sw-sombra:{AZUL_SOMBRA};--sw-oro:{DORADO};--sw-texto:{TEXTO};--sw-fondo:{FONDO};
--sw-borde:#DCE7FB;--sw-suave:#EAF1FF;--sw-gris:#4A5B78;--sw-rojo:#C62E3A;--sw-verde:#1C8C5E}}
html,body,.stApp{{background:var(--sw-fondo);color:var(--sw-texto);
font-family:Nunito,"Nunito Sans",system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}}
.stApp{{overflow-x:hidden}}
*,*::before,*::after{{box-sizing:border-box}}
[data-testid="stMainBlockContainer"],.block-container{{width:100%;max-width:72rem;padding:1rem 1rem 4rem;
padding-left:max(1rem,env(safe-area-inset-left));padding-right:max(1rem,env(safe-area-inset-right))}}
header[data-testid="stHeader"]{{background:transparent}}
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"]{{display:none}}
p,li,label,.stMarkdown{{font-size:1rem;line-height:1.55;overflow-wrap:anywhere}}
h1,h2,h3{{color:var(--sw-texto);font-weight:900;letter-spacing:-.01em}}
/* Botones 3D */
.stButton>button,.stDownloadButton>button,.stFormSubmitButton>button,[data-testid="stPopover"] button{{
min-height:2.9rem;border-radius:1rem;font-weight:800;font-size:1rem;border:2px solid var(--sw-borde);
background:#fff;color:var(--sw-texto);box-shadow:0 .3rem 0 var(--sw-borde);transition:transform .08s,box-shadow .08s;
white-space:normal;overflow-wrap:anywhere;padding:.55rem 1rem}}
.stButton>button:active,.stDownloadButton>button:active,.stFormSubmitButton>button:active{{transform:translateY(.2rem);box-shadow:0 .1rem 0 var(--sw-borde)}}
button[kind="primary"],button[data-testid="stBaseButton-primary"],button[kind="primaryFormSubmit"],
button[data-testid="stBaseButton-primaryFormSubmit"]{{background:var(--sw-azul)!important;color:#fff!important;
border-color:var(--sw-sombra)!important;box-shadow:0 .35rem 0 var(--sw-sombra)!important}}
button:focus-visible,a:focus-visible,input:focus-visible,textarea:focus-visible{{outline:3px solid var(--sw-oro)!important;outline-offset:2px}}
button:disabled{{opacity:.55;box-shadow:none!important}}
input,textarea,select,[data-baseweb="select"] *{{font-size:16px!important}}
[data-baseweb="tab"]{{min-height:2.75rem}}
[data-testid="stSegmentedControl"] button,[data-testid="stButtonGroup"] button{{min-height:2.75rem}}
[data-testid="stDataFrame"]{{width:100%}}
.stSlider [role="slider"]{{width:1.6rem;height:1.6rem}}
/* Componentes propios */
.sw-marca{{display:flex;align-items:center;gap:.6rem;font-weight:900;font-size:1.25rem;color:var(--sw-azul)}}
.sw-marca svg{{width:2.4rem;flex:0 0 auto}}
.sw-barra{{display:flex;flex-wrap:wrap;gap:.35rem;align-items:center;margin:.25rem 0 .75rem;padding:0;list-style:none}}
.sw-barra li{{flex:1 1 0;min-width:0;text-align:center;font-weight:800;font-size:.85rem;padding:.45rem .3rem;border-radius:999px;
background:var(--sw-suave);color:var(--sw-gris);border:2px solid transparent}}
.sw-barra li.hecho{{background:#DDF4EA;color:var(--sw-verde)}}
.sw-barra li.actual{{background:var(--sw-azul);color:#fff;border-color:var(--sw-sombra);box-shadow:0 .2rem 0 var(--sw-sombra)}}
.sw-progreso{{height:.45rem;border-radius:999px;background:var(--sw-suave);overflow:hidden;margin-bottom:.5rem}}
.sw-progreso>span{{display:block;height:100%;background:linear-gradient(90deg,var(--sw-azul),var(--sw-oro))}}
.sw-hero{{display:grid;grid-template-columns:minmax(0,1fr);gap:1rem;align-items:center;text-align:center;
background:radial-gradient(circle at 20% 10%,#fff 0,#EAF1FF 60%,#DCE7FB 100%);border-radius:1.75rem;
padding:clamp(1rem,4vw,2.5rem);border:3px solid var(--sw-borde);box-shadow:0 .5rem 0 var(--sw-borde)}}
.sw-hero .mascota{{width:min(11rem,45%);margin:0 auto}}
.sw-hero h1{{font-size:clamp(2rem,8vw,3.4rem);margin:.2rem 0;color:var(--sw-azul);text-shadow:0 .2rem 0 #fff}}
.sw-lema{{font-size:clamp(1.05rem,3.6vw,1.35rem);font-weight:800;margin:0}}
.sw-sub{{color:var(--sw-gris);margin:.25rem 0 0}}
@media (min-width:768px){{.sw-hero{{grid-template-columns:minmax(0,1fr) minmax(0,2fr);text-align:left}}
.sw-hero .mascota{{width:100%;max-width:13rem}}}}
.sw-card{{background:#fff;border:2px solid var(--sw-borde);border-radius:1.25rem;padding:1rem;box-shadow:0 .3rem 0 var(--sw-borde);
margin-bottom:.5rem;overflow-wrap:anywhere}}
.sw-card h3{{margin:.1rem 0 .4rem;font-size:1.15rem}}
.sw-card.activa{{border-color:var(--sw-azul);box-shadow:0 .35rem 0 var(--sw-sombra)}}
.sw-card.bloqueada{{opacity:.7;background:#F3F6FC}}
.sw-icono{{width:3rem;height:3rem;border-radius:1rem;display:grid;place-items:center;background:var(--sw-suave);margin-bottom:.4rem}}
.sw-icono svg{{width:1.9rem;height:1.9rem}}
.sw-chip{{display:inline-block;border-radius:999px;padding:.15rem .65rem;font-weight:800;font-size:.8rem;margin:.1rem .2rem .1rem 0;
background:var(--sw-suave);color:var(--sw-sombra)}}
.sw-chip.oro{{background:#FFF1B8;color:#6B5200}} .sw-chip.verde{{background:#DDF4EA;color:var(--sw-verde)}}
.sw-chip.rojo{{background:#FCE3E5;color:var(--sw-rojo)}}
.sw-escena{{width:100%;border-radius:1.5rem;overflow:hidden;border:3px solid var(--sw-borde);background:#fff;box-shadow:0 .4rem 0 var(--sw-borde)}}
.sw-escena svg{{display:block;width:100%;height:auto}}
.sw-dialogo{{display:flex;gap:.75rem;align-items:flex-start;margin:.6rem 0}}
.sw-dialogo .avatar{{flex:0 0 auto;width:clamp(2.8rem,12vw,4rem)}}
.sw-dialogo .avatar svg{{width:100%;height:auto;display:block}}
.sw-burbuja{{position:relative;background:#fff;border:2px solid var(--sw-borde);border-radius:1.1rem;padding:.7rem .9rem;
min-width:0;max-width:min(100%,40rem);box-shadow:0 .2rem 0 var(--sw-borde);overflow-wrap:anywhere;word-break:break-word}}
.sw-dialogo>div,.sw-candado>div,.sw-mision>div{{min-width:0}}
.sw-burbuja .quien{{display:block;font-weight:900;font-size:.85rem;color:var(--sw-sombra);margin-bottom:.15rem}}
.sw-dialogo.yo{{flex-direction:row-reverse}}
.sw-dialogo.yo .sw-burbuja{{background:var(--sw-azul);color:#fff;border-color:var(--sw-sombra);box-shadow:0 .2rem 0 var(--sw-sombra)}}
.sw-dialogo.yo .sw-burbuja .quien{{color:#FFE27A}}
.sw-dialogo.chispa .sw-burbuja{{background:#FFFBEA;border-color:#FFE27A;box-shadow:0 .2rem 0 #FFE27A}}
.sw-yo{{flex:0 0 auto;width:clamp(2.4rem,10vw,3rem);height:clamp(2.4rem,10vw,3rem);border-radius:50%;background:var(--sw-oro);
display:grid;place-items:center;font-weight:900;color:var(--sw-texto)}}
.sw-giro{{border:3px solid var(--sw-rojo);background:#FFF5F5;border-radius:1.25rem;padding:1rem;animation:sw-sacudir .6s ease 1}}
.sw-giro h3{{color:var(--sw-rojo);margin:0 0 .3rem}}
.sw-mision{{display:flex;gap:.6rem;align-items:center;padding:.45rem .2rem;border-bottom:1px dashed var(--sw-borde)}}
.sw-mision:last-child{{border-bottom:0}}
.sw-mision .punto{{flex:0 0 auto;width:1.6rem;height:1.6rem;border-radius:50%;display:grid;place-items:center;font-weight:900;font-size:.8rem;
background:var(--sw-suave);color:var(--sw-gris)}}
.sw-mision.hecha .punto{{background:var(--sw-verde);color:#fff}} .sw-mision.actual .punto{{background:var(--sw-oro);color:var(--sw-texto)}}
.sw-semaforo{{display:flex;align-items:center;gap:.6rem;font-weight:900;font-size:1.1rem;padding:.7rem 1rem;border-radius:1rem}}
.sw-semaforo .luz{{width:1.3rem;height:1.3rem;border-radius:50%;flex:0 0 auto}}
.sw-semaforo.verde{{background:#DDF4EA;color:var(--sw-verde)}} .sw-semaforo.verde .luz{{background:var(--sw-verde)}}
.sw-semaforo.amarillo{{background:#FFF6D1;color:#6B5200}} .sw-semaforo.amarillo .luz{{background:var(--sw-oro)}}
.sw-semaforo.rojo{{background:#FCE3E5;color:var(--sw-rojo)}} .sw-semaforo.rojo .luz{{background:var(--sw-rojo)}}
.sw-bolsa{{height:1rem;border-radius:999px;background:var(--sw-suave);overflow:hidden;border:2px solid var(--sw-borde)}}
.sw-bolsa>span{{display:block;height:100%}}
.sw-tabla{{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;border-radius:1rem;border:2px solid var(--sw-borde);background:#fff}}
.sw-tabla table{{border-collapse:collapse;width:100%}}
.sw-tabla th,.sw-tabla td{{padding:.55rem .7rem;text-align:left;border-bottom:1px solid var(--sw-borde);white-space:nowrap}}
.sw-tabla th{{background:var(--sw-suave);font-weight:900}}
.sw-candado{{display:flex;gap:.75rem;align-items:center;background:#F1F5FD;border:2px dashed #B8CBEF;border-radius:1.1rem;padding:.7rem .9rem}}
.sw-candado .avatar{{width:clamp(2.6rem,11vw,3.4rem);flex:0 0 auto}}
.sw-insignia{{text-align:center;padding:.8rem;border-radius:1.1rem;border:2px solid var(--sw-borde);background:#fff;height:100%}}
.sw-insignia.no{{opacity:.45;filter:grayscale(1)}}
.sw-insignia svg{{width:3rem;height:3rem}}
.sw-fuente{{font-size:.85rem;color:var(--sw-gris)}}
.sw-pie{{text-align:center;color:var(--sw-gris);font-size:.85rem;margin-top:2rem}}
.chispa{{animation:sw-flotar 3.2s ease-in-out infinite}}
@keyframes sw-flotar{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-6%)}}}}
@keyframes sw-sacudir{{0%,100%{{transform:translateX(0)}}25%{{transform:translateX(-1.5%)}}75%{{transform:translateX(1.5%)}}}}
@keyframes sw-aparecer{{from{{opacity:0;transform:translateY(.6rem)}}to{{opacity:1;transform:none}}}}
.sw-aparece{{animation:sw-aparecer .45s ease both}}
@media (max-width:480px){{
[data-testid="stMainBlockContainer"],.block-container{{padding-top:.5rem}}
.sw-barra li{{font-size:.72rem;padding:.4rem .15rem}}
.sw-card{{padding:.85rem}}
}}
/* Identidad Starwise (capa visual añadida) */
html,body,.stApp,.stMarkdown,button,input,textarea,select{{font-family:Nunito,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif!important}}
h1,h2,h3,h4,[data-testid="stHeading"] *{{font-family:Nunito,system-ui,sans-serif!important;font-weight:900!important;color:var(--sw-texto)}}
[data-testid="stMainBlockContainer"],.block-container{{padding-top:3.6rem}}
.stButton button,.stFormSubmitButton button,.stDownloadButton button{{min-height:2.9rem;border-radius:1rem!important;
border:2px solid var(--sw-borde)!important;background:#fff!important;color:var(--sw-azul)!important;font-weight:900!important;
text-transform:uppercase;letter-spacing:.04em;box-shadow:0 .3rem 0 var(--sw-borde)!important;white-space:normal!important}}
.stButton button p,.stFormSubmitButton button p,.stDownloadButton button p{{font-weight:900!important;font-family:Nunito,system-ui,sans-serif!important}}
.stButton button:active,.stFormSubmitButton button:active,.stDownloadButton button:active{{transform:translateY(.25rem);box-shadow:none!important}}
.stButton button[kind="primary"],.stFormSubmitButton button[kind="primaryFormSubmit"],button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primaryFormSubmit"]{{background:var(--sw-azul)!important;color:#fff!important;
border-color:var(--sw-sombra)!important;box-shadow:0 .35rem 0 var(--sw-sombra)!important}}
.stTextInput input,.stTextArea textarea,.stNumberInput input,[data-baseweb="select"]>div{{border-radius:.9rem!important;border:2px solid var(--sw-borde)!important;background:#fff!important}}
[data-testid="stForm"]{{border:2px solid var(--sw-borde);border-radius:1.25rem;box-shadow:0 .3rem 0 var(--sw-borde);background:#fff;animation:sw-aparecer .45s ease both}}
.stTabs [data-baseweb="tab-list"]{{gap:.4rem;flex-wrap:wrap}}
.stTabs [data-baseweb="tab"]{{border-radius:.9rem;border:2px solid var(--sw-borde);background:#fff;font-weight:900;padding:.5rem .9rem}}
.stTabs [aria-selected="true"]{{background:var(--sw-azul)!important;color:#fff!important;border-color:var(--sw-sombra)}}
.stTabs [aria-selected="true"] p{{color:#fff!important}}
[data-testid="stExpander"]{{border:2px solid var(--sw-borde);border-radius:1rem;background:#fff}}
[data-testid="stDataFrame"]{{border:2px solid var(--sw-borde);border-radius:.9rem}}
.sw-barra li{{text-transform:uppercase;letter-spacing:.04em}}
.sw-barra li.hecho{{background:#FFF6CC;color:var(--sw-texto);border-color:#E0A800}}
.sw-burbuja .quien{{text-transform:uppercase;letter-spacing:.06em}}
.sw-dialogo.chispa .sw-burbuja{{background:#fff;border-color:var(--sw-borde);box-shadow:0 .2rem 0 var(--sw-borde)}}
.sw-dialogo.chispa .sw-burbuja .quien{{color:var(--sw-azul)}}
/* Chispa animada */
.chispa{{animation:none}}
.chispa .ch-cuerpo{{transform-box:fill-box;transform-origin:50% 60%;animation:ch-flotar 2.6s ease-in-out infinite}}
.chispa-pensando .ch-cuerpo{{animation:ch-pensar .9s ease-in-out infinite}}
.chispa-pensando .ch-destello{{animation:ch-latir .6s ease-in-out infinite}}
.chispa-alerta .ch-cuerpo,.chispa-sorpresa .ch-cuerpo{{animation:ch-temblar .5s ease-in-out 3}}
.chispa-logro .ch-cuerpo{{transform-origin:50% 100%;animation:ch-saltar 1.1s ease-in-out infinite}}
@keyframes ch-flotar{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-4%)}}}}
@keyframes ch-pensar{{0%,100%{{transform:rotate(-7deg)}}50%{{transform:rotate(7deg) scale(1.04)}}}}
@keyframes ch-temblar{{0%,100%{{transform:translateX(0)}}25%{{transform:translateX(-3%)}}75%{{transform:translateX(3%)}}}}
@keyframes ch-saltar{{0%,100%{{transform:translateY(0)}}30%{{transform:translateY(-8%) scale(1.06,.95)}}55%{{transform:translateY(0) scale(.96,1.04)}}}}
@keyframes ch-latir{{0%,100%{{opacity:.35}}50%{{opacity:1}}}}
@media (max-width:480px){{[data-testid="stMainBlockContainer"],.block-container{{padding-top:3.2rem}}}}
@media (prefers-reduced-motion:reduce){{*,*::before,*::after{{animation:none!important;transition:none!important}}}}
</style>
"""


def inyectar_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def marca() -> None:
    html(f'<div class="sw-marca">{chispa_svg("feliz", "2.4rem")}<span>STARWISE</span></div>')


def barra_aventura(etapa: int, progreso: float) -> None:
    items = []
    for i, nombre in enumerate(ETAPAS):
        cls = "actual" if i == etapa else ("hecho" if i < etapa else "")
        marca_txt = "✓ " if i < etapa else ""
        items.append(f'<li class="{cls}" aria-current="{"step" if i == etapa else "false"}">{marca_txt}{nombre}</li>')
    pct = max(0, min(100, int(progreso * 100)))
    html(f'<nav aria-label="Progreso de la aventura"><ol class="sw-barra">{"".join(items)}</ol>'
         f'<div class="sw-progreso" role="progressbar" aria-valuenow="{pct}" aria-valuemin="0" aria-valuemax="100">'
         f'<span style="width:{pct}%"></span></div></nav>')


def hero(titulo: str, lema: str, sub: str, estado: str = "feliz") -> None:
    html(f'<section class="sw-hero sw-aparece"><div class="mascota">{chispa_svg(estado)}</div>'
         f'<div><h1>{esc(titulo)}</h1><p class="sw-lema">{esc(lema)}</p><p class="sw-sub">{esc(sub)}</p></div></section>')


def tarjeta(titulo: str, cuerpo_html: str, icono: str = "", clase: str = "") -> None:
    ic = f'<div class="sw-icono" aria-hidden="true">{ICONOS.get(icono, "")}</div>' if icono else ""
    html(f'<div class="sw-card {clase} sw-aparece">{ic}<h3>{esc(titulo)}</h3>{cuerpo_html}</div>')


def chip(texto: str, tipo: str = "") -> str:
    return f'<span class="sw-chip {tipo}">{esc(texto)}</span>'


def dialogo(quien: str, texto: str, rol: str = "carmen", estado_chispa: str = "feliz") -> None:
    """rol: 'carmen' | 'yo' | 'chispa'."""
    if rol == "carmen":
        av = f'<div class="avatar">{carmen_svg()}</div>'
    elif rol == "chispa":
        av = f'<div class="avatar">{chispa_svg(estado_chispa)}</div>'
    else:
        inicial = esc((quien or "Tú")[:1].upper())
        av = f'<div class="sw-yo" aria-hidden="true">{inicial}</div>'
    html(f'<div class="sw-dialogo {rol}">{av}<div class="sw-burbuja"><span class="quien">{esc(quien)}</span>{esc(texto)}</div></div>')


def candado_tutor() -> None:
    html(f'<div class="sw-candado"><div class="avatar">{chispa_svg("calma")}</div><div><b>Chispa está en pausa.</b> '
         'Esta parte comprueba lo que puedes hacer por tu cuenta. Respira, lee con calma y responde como tú lo harías.</div></div>')


def semaforo(total: int, presupuesto: int) -> None:
    if total > presupuesto:
        cls, txt = "rojo", f"Te pasaste por ${total - presupuesto:,}. Ajusta antes de guardar."
    elif total == 0:
        cls, txt = "amarillo", "Aún no asignas presupuesto."
    else:
        cls, txt = "verde", f"Dentro del presupuesto · quedan ${presupuesto - total:,}"
    pct = min(100, int(total / presupuesto * 100)) if presupuesto else 0
    color = {"rojo": "var(--sw-rojo)", "amarillo": "var(--sw-oro)", "verde": "var(--sw-verde)"}[cls]
    html(f'<div class="sw-semaforo {cls}" role="status"><span class="luz" aria-hidden="true"></span>'
         f'<span>${total:,} de ${presupuesto:,} · {txt}</span></div>'
         f'<div class="sw-bolsa" aria-hidden="true"><span style="width:{pct}%;background:{color}"></span></div>')


def tabla_html(filas: list[list], encabezados: list[str], nota: str = "") -> None:
    th = "".join(f"<th scope='col'>{esc(h)}</th>" for h in encabezados)
    tb = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in f) + "</tr>" for f in filas)
    nota_html = f'<p class="sw-fuente">{esc(nota)}</p>' if nota else ""
    html(f'<div class="sw-tabla" tabindex="0" role="region" aria-label="Tabla"><table><thead><tr>{th}</tr></thead>'
         f'<tbody>{tb}</tbody></table></div>{nota_html}')


def lista_misiones(misiones: list[tuple[str, str, str]]) -> None:
    """misiones: (nombre, descripción, estado 'hecha'|'actual'|'')."""
    filas = []
    for i, (n, d, est) in enumerate(misiones, 1):
        simbolo = "✓" if est == "hecha" else str(i)
        filas.append(f'<div class="sw-mision {est}"><span class="punto" aria-hidden="true">{simbolo}</span>'
                     f'<div><b>{esc(n)}</b><br><span class="sw-fuente">{esc(d)}</span></div></div>')
    html('<div class="sw-card">' + "".join(filas) + "</div>")


def insignia(nombre: str, desc: str, obtenida: bool) -> None:
    html(f'<div class="sw-insignia {"" if obtenida else "no"}">{ICONOS["insignia"]}<br><b>{esc(nombre)}</b><br>'
         f'<span class="sw-fuente">{esc(desc if obtenida else "Aún no desbloqueada")}</span></div>')


def pie() -> None:
    html('<p class="sw-pie">STARWISE · prototipo académico de hackathon · Talavera Viva y Carmen son ficticias · '
         'No es certificación ni garantiza empleo.</p>')


# ---------------------------------------------------------------------------
# Ilustraciones SVG propias
# ---------------------------------------------------------------------------
def carmen_svg() -> str:
    return """<svg viewBox="0 0 80 80" role="img" aria-label="Retrato ilustrado de Carmen Ruiz, personaje ficticio">
<circle cx="40" cy="40" r="38" fill="#EAF1FF" stroke="#1550B8" stroke-width="3"/>
<path d="M14 74 q26 -26 52 0" fill="#1E6BE6"/><path d="M30 58 l10 10 l10 -10" fill="#fff"/>
<circle cx="40" cy="38" r="15" fill="#C98A5E"/><path d="M24 36 q2 -18 16 -18 q14 0 16 18 q-6 -10 -16 -10 q-10 0 -16 10z" fill="#2B1B14"/>
<circle cx="52" cy="20" r="6" fill="#2B1B14"/><circle cx="34" cy="38" r="1.8" fill="#13243F"/><circle cx="46" cy="38" r="1.8" fill="#13243F"/>
<path d="M35 45 q5 4 10 0" stroke="#13243F" stroke-width="2" fill="none" stroke-linecap="round"/>
<circle cx="24" cy="42" r="2.5" fill="#FFC800"/><circle cx="56" cy="42" r="2.5" fill="#FFC800"/></svg>"""


def escena_tienda(giro: bool = False) -> str:
    azulejos = "".join(
        f'<g transform="translate({x},{y})"><rect width="26" height="26" fill="#fff" stroke="#1E6BE6" stroke-width="2"/>'
        f'<circle cx="13" cy="13" r="6" fill="none" stroke="#1E6BE6" stroke-width="2"/><circle cx="13" cy="13" r="2" fill="#FFC800"/></g>'
        for x in range(40, 600, 30) for y in (210,))
    nube = '<g fill="#fff" opacity=".9"><ellipse cx="120" cy="50" rx="40" ry="14"/><ellipse cx="520" cy="40" rx="50" ry="16"/></g>'
    aviso = ('<g transform="translate(420,92)"><rect width="190" height="44" rx="12" fill="#C62E3A"/>'
             '<text x="95" y="29" text-anchor="middle" font-size="17" font-weight="900" fill="#fff" '
             'font-family="system-ui,sans-serif">PRESUPUESTO ↓</text></g>') if giro else ""
    return f"""<div class="sw-escena"><svg viewBox="0 0 640 260" role="img"
aria-label="Ilustración de la fachada del taller ficticio Talavera Viva en una calle del centro histórico">
<rect width="640" height="260" fill="#CFE0FF"/>{nube}
<rect x="30" y="70" width="580" height="170" rx="10" fill="#FFF6E5" stroke="#13243F" stroke-width="3"/>
<rect x="30" y="70" width="580" height="34" rx="10" fill="#1E6BE6"/>
<text x="320" y="94" text-anchor="middle" font-size="20" font-weight="900" fill="#fff" font-family="system-ui,sans-serif">TALAVERA VIVA</text>
<path d="M60 104 h520 l-20 26 h-480z" fill="#FFC800" stroke="#13243F" stroke-width="2"/>
<rect x="80" y="140" width="150" height="62" rx="6" fill="#DCEBFF" stroke="#13243F" stroke-width="3"/>
<circle cx="120" cy="178" r="14" fill="#fff" stroke="#1E6BE6" stroke-width="3"/><rect x="150" y="160" width="20" height="34" rx="6" fill="#fff" stroke="#1E6BE6" stroke-width="3"/>
<circle cx="200" cy="182" r="10" fill="#FFC800" stroke="#1E6BE6" stroke-width="3"/>
<rect x="280" y="136" width="80" height="104" rx="6" fill="#1550B8" stroke="#13243F" stroke-width="3"/><circle cx="345" cy="190" r="4" fill="#FFC800"/>
<rect x="410" y="140" width="150" height="62" rx="6" fill="#DCEBFF" stroke="#13243F" stroke-width="3"/>
<path d="M425 190 q20 -30 40 0 M480 190 q20 -30 40 0" stroke="#1E6BE6" stroke-width="3" fill="none"/>
{azulejos}<rect x="0" y="240" width="640" height="20" fill="#B9C6DA"/>{aviso}</svg></div>"""


ICONOS = {
    "datos": '<svg viewBox="0 0 24 24" fill="none" stroke="#1E6BE6" stroke-width="2.4" stroke-linecap="round"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></svg>',
    "mercado": '<svg viewBox="0 0 24 24" fill="none" stroke="#1E6BE6" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11l15-6v14L3 13z"/><path d="M7 13v5h3"/></svg>',
    "operaciones": '<svg viewBox="0 0 24 24" fill="none" stroke="#1E6BE6" stroke-width="2.4" stroke-linecap="round"><circle cx="12" cy="12" r="3.5"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2"/></svg>',
    "finanzas": '<svg viewBox="0 0 24 24" fill="none" stroke="#1E6BE6" stroke-width="2.4" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M15 9.5c-.5-1-1.6-1.5-3-1.5-1.7 0-3 .8-3 2s1.3 1.7 3 2 3 .8 3 2-1.3 2-3 2c-1.4 0-2.5-.5-3-1.5M12 6v12"/></svg>',
    "carmen": '<svg viewBox="0 0 24 24" fill="none" stroke="#1E6BE6" stroke-width="2.4" stroke-linecap="round"><path d="M4 5h16v11H9l-5 4z"/></svg>',
    "carpeta": '<svg viewBox="0 0 24 24" fill="none" stroke="#1E6BE6" stroke-width="2.4" stroke-linejoin="round"><path d="M3 6h7l2 2h9v11H3z"/></svg>',
    "propuesta": '<svg viewBox="0 0 24 24" fill="none" stroke="#1E6BE6" stroke-width="2.4" stroke-linecap="round"><path d="M6 3h9l4 4v14H6z"/><path d="M9 12h7M9 16h5"/></svg>',
    "archivo": '<svg viewBox="0 0 24 24" fill="none" stroke="#1E6BE6" stroke-width="2.4" stroke-linejoin="round"><path d="M6 3h8l5 5v13H6z"/><path d="M14 3v5h5"/></svg>',
    "insignia": '<svg viewBox="0 0 48 48"><circle cx="24" cy="20" r="14" fill="#FFC800" stroke="#1550B8" stroke-width="3"/><path d="M16 32l-4 12 8-4 4 6 2-14M32 32l4 12-8-4-4 6" fill="#1E6BE6"/><path d="M24 12l2.5 5 5.5.8-4 3.9 1 5.5-5-2.6-5 2.6 1-5.5-4-3.9 5.5-.8z" fill="#fff"/></svg>',
    "digno": '<svg viewBox="0 0 24 24" fill="none" stroke="#1E6BE6" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z"/><path d="M8.5 12l2.5 2.5 4.5-5"/></svg>',
}


def texto_plano(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)
