# STARWISE × ROLELAB

**Explora tu camino. Vive el reto. Demuestra lo que sabes hacer.**
Talavera Valley Hackathon 2026 · EdTech · prototipo académico en Streamlit.

Juego narrativo de decisiones profesionales para universitarios de 18–25 años (negocios, mercadotecnia, finanzas). Complementa la formación universitaria: **no** es certificación, experiencia laboral formal ni garantía de empleo. Talavera Viva, Carmen Ruiz, La Espiga y Mirador son **ficticias**; sus datos son **sintéticos**.

## Recorrido
| Etapa | Pantallas |
|---|---|
| Explorar | Portada con Chispa → perfil (18+, consentimiento, autoconfianza subjetiva) → elegir ruta → expectativa del rol |
| Practicar | **Diagnóstico A** (sin tutor) → **Talavera Viva**: hablar con Carmen, carpeta de datos (ventas/clientes/costos con un duplicado intencional), presupuesto con **giro a $60,000 en el 4.º turno**, propuesta y defensa → reacción de Carmen |
| Demostrar | **Demostración B** (otra empresa, sin tutor) → reflexión → logros (A vs B, cinco áreas, insignias) → portafolio |
| Próximo paso | Mini ruta (requisitos ilustrativos, competencias observadas y no observadas, plan editable, ¿qué hace digno un primer empleo?) → encuesta y evidencia JSON |

Siempre accesibles desde **Opciones · Mi progreso**: descargar evidencia, Metodología y fuentes, Acerca del proyecto, Panel del equipo y Reiniciar.

Solo la ruta **Estrategia comercial y datos** está habilitada. «Analista BI» y «Analista financiero junior» aparecen como *Próximamente* y no son clicables: preferimos una aventura completa a tres que solo cambien el título.

## Ejecutar en macOS
```bash
cd starwise
python3 -m venv .venv && source .venv/bin/activate    # Python 3.11 o superior
pip install -r requirements.txt
cp ~/Descargas/repositorio.csv data/repositorio.csv     # CSV oficial del reto, SIN modificarlo
streamlit run app.py                                   # abre http://localhost:8501
```
Para probar en tu celular dentro de la misma red Wi-Fi: `streamlit run app.py --server.address 0.0.0.0` y abre `http://<IP-de-tu-Mac>:8501` en Safari o Chrome.

Pruebas: `pip install pytest && python -m pytest -q`.
Regenerar los CSV sintéticos: `python datos.py`.

## Streamlit Community Cloud
1. Sube la carpeta a un repositorio de GitHub (el `.gitignore` excluye `secrets.toml` y las evidencias).
2. En share.streamlit.io: *New app* → elige el repo → archivo principal `app.py`.
3. (Opcional) *App settings → Secrets*: pega el contenido de `.streamlit/secrets.toml.example` con tu `GEMINI_API_KEY` y, si quieres, `FACILITADOR_PASSWORD`.
4. Comparte la URL: funciona igual en laptop, tablet y celular.

**Almacenamiento:** el sistema de archivos de Streamlit Cloud es efímero y la app **no guarda nada en el servidor**. El estado vive en `st.session_state`: **recargar o cerrar la pestaña borra lo no exportado**. La evidencia real es el JSON que descarga cada participante.

## IA generativa (opcional)
- Sin clave, Chispa funciona como **«Tutor demo por reglas»** (`chispa.py`, 37 escenarios) y lo dice en pantalla.
- Con `GEMINI_API_KEY` (secrets o variable de entorno), Chispa usa Gemini por REST desde el servidor: modelo `GEMINI_MODEL` (por defecto `gemini-2.5-flash`), timeout de 12 s, 25 consultas por sesión, enfriamiento de 60 s ante un 429, y vuelta automática a las reglas si hay error. Toda la IA está en `ia.py`, con cada llamada marcada `# 🤖 IA:`.
- Solo se envía contexto del caso ficticio. Las respuestas que parezcan revelar la solución se descartan. La IA **nunca** decide criterios de evaluación y está bloqueada durante A y B.

## Datos y fuentes
- `data/repositorio.csv` **no está incluido** porque no se adjuntó. Colócalo en `data/` o cárgalo desde *Metodología → Fuentes* (solo para la sesión). Sin él, la simulación funciona completa y los datos de contexto aparecen como «no disponibles».
- `datos.py` valida columnas exactas, encoding y separador. Cada indicador se busca por su **etiqueta exacta** (diccionario `INDICADORES`, sin `contains()` ni fuzzy matching) y se compara su valor. Si no coincide, queda como «requiere revisión» y no se muestra.
- Indicadores que se usan en pantalla, cada uno solo donde corresponde: 30.4 % sin prestaciones en el primer empleo y 69.5 % con primer salario de hasta $10,000 (en *¿Qué hace digno un primer empleo?*), 47 % / 46.8 % de habilidades clave (solo si te interesan los datos), $17,795 (solo en *Contexto nacional*) y costos de 4 años (solo en *Ruta Base*). El selector de rutas **no muestra salarios**.
- Sintéticos: `ventas_talavera.csv` (el total limpio cae **−28.0 %**; con el duplicado V-0072, −23.7 %; Restaurantes cae −38.1 %), `clientes_talavera.csv`, `costos_talavera.csv`, `evaluacion_A.csv` y `evaluacion_B.csv`.

## Evaluación
`evaluacion.py` es determinista, está separado del tutor y versionado (`rubric_version`).
- **A y B:** cuatro criterios objetivos (variación con tolerancia de ±0.5 pp, segmento con mayor caída, indicador pertinente, cifra del caso en la justificación). La calidad del texto queda **pendiente de revisión humana**. La comparación A/B describe un cambio observado, no una causa.
- **Práctica:** cinco áreas (investigación, análisis, priorización, comunicación, adaptación) con niveles *Inicial / En desarrollo / Aplicado en el caso / Requiere revisión*.
- No se usan la longitud del texto, la rapidez, el número de acciones, cuántas pistas se pidieron ni palabras clave. La rúbrica no tiene validación psicométrica.

## Prueba con usuarios (facilitador)
1. *Opciones → Panel del equipo → Comenzar prueba con persona externa*: alias y declaración del facilitador.
2. La persona juega de 10 a 20 minutos (puede tomar más, sin penalización) y al final descarga su `starwise_evidencia_*.json`.
3. En el panel, importa varios JSON: se eliminan duplicados por `attempt_id` y puedes exportar el consolidado en CSV. Los registros `synthetic_test` de QA se excluyen de las métricas. Sin archivos, el panel muestra «Aún no hay pruebas».

## Estructura
```
app.py  ui.py  chispa.py  casos.py  datos.py  evaluacion.py  ia.py  portafolio.py  evidencia.py
requirements.txt  .gitignore  .streamlit/config.toml  .streamlit/secrets.toml.example
data/  (sintéticos + LEEME_repositorio.md; aquí va repositorio.csv)
evidencia/.gitkeep   deck/README.md (pitch y demo de 2 min)
tests/test_datos.py  tests/test_evaluacion.py  tests/test_caso_tutor_export.py  tests/test_app_flow.py
```

## Verificaciones hechas y pendientes
**Hechas en el entorno de desarrollo** (Python 3.13, pandas 3.0, Chrome; **sin Streamlit ni Plotly instalados ni red para instalarlos**):
- `pytest`: 31 pruebas de lógica en verde (validación del CSV, reconciliación de datos, rúbrica, Carmen y el giro, tutor y caída a reglas ante un 429, escape de HTML, evidencia y deduplicación). `test_app_flow.py` se omite sin Streamlit.
- Recorrido completo (perfil → A → Carmen y giro → datos → presupuesto → propuesta → B → portafolio → evidencia → panel del equipo) ejecutado con un **stub de Streamlit**. El stub imita los callbacks, la limpieza de widgets y los errores de session_state, pero **no es Streamlit real**.
- Componentes HTML/CSS y portafolio renderizados en Chrome a 360, 390, 430, 768 y 1280 px: sin scroll horizontal y con botones de al menos 44 px.

**Pendientes (hazlas antes de presentar):**
1. `pip install -r requirements.txt && python -m pytest -q` (activa `test_app_flow.py`).
2. `streamlit run app.py` y recorrer la demo completa en escritorio.
3. En un celular real (Safari en iPhone y Chrome en Android): el teclado virtual con el chat, los sliders del presupuesto, las tablas y las descargas HTML/JSON.
4. Copiar `repositorio.csv` y confirmar en *Metodología → Fuentes* que los indicadores salgan «Verificado». Si alguno sale «No encontrado», la etiqueta del CSV difiere: ajusta `INDICADORES` en `datos.py` **solo** si el texto oficial lo confirma.

## Limitaciones conocidas
- La rúbrica no está validada. Las encuestas son de opinión y no miden aprendizaje. El impacto sobre ingresos no está medido.
- No hay persistencia en el servidor ni sincronización en tiempo real.
- El desplazamiento automático al inicio de cada escena usa un pequeño iframe de componentes. Si el navegador lo bloquea, la app sigue funcionando.
- El modelo comercial es una hipótesis: no hay ventas, convenios ni empresas aliadas.
