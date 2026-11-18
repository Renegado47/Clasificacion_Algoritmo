import base64
import html
import inspect
import os
import random
import re
import unicodedata
from pathlib import Path

import requests
import streamlit as st

import contenido as C
import dibujos as D

# La barra superior usa streamlit-option-menu; si no está instalado, se usa un radio horizontal.
try:
    from streamlit_option_menu import option_menu
except ImportError:  # pragma: no cover
    option_menu = None

st.set_page_config(page_title="Búsquedas en IA", page_icon="🧠", layout="centered")

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
try:
    API_KEY = os.getenv("ML4K_API_KEY") or st.secrets.get("ML4K_API_KEY", "")
except Exception:  # noqa: BLE001  (no existe secrets.toml)
    API_KEY = os.getenv("ML4K_API_KEY", "")

API_URL = "https://machinelearningforkids.co.uk/api/scratch/{key}/classify"
NUM_PREGUNTAS = 10
PDF_PATH = Path(__file__).parent / "ClasificacionBusquedaAlgoritmo.pdf"
# Compatible con versiones nuevas (width="stretch") y antiguas (use_container_width=True) de Streamlit
ANCHO = ({"width": "stretch"} if "width" in inspect.signature(st.button).parameters
         else {"use_container_width": True})

CATEGORIAS = {
    "informada": ("Búsqueda informada", "#3B82F6"),
    "noinformada": ("Búsqueda no informada", "#F59E0B"),
    "evolutiva": ("Búsqueda evolutiva", "#10B981"),
    "ninguna": ("Ninguna de las anteriores", "#94A3B8"),
}

# ============================================================================
# ESTILOS
# ============================================================================
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.6rem; max-width: 900px;}
    .titulo {font-size: 2.2rem; font-weight: 800; margin-bottom: 0;}
    .subtitulo {color: #9CA3AF; margin-bottom: 1rem;}
    .banda {background: #1F2937; border-left: 6px solid #3B82F6; border-radius: 10px;
            padding: 14px 18px; margin: 6px 0 14px;}
    .banda small {color: #9CA3AF;}
    .pregunta {font-size: 1.25rem; font-weight: 700; margin: 6px 0 14px;
               background: #1F2937; border-radius: 12px; padding: 16px;}
    .puntaje {border-radius: 16px; padding: 28px; text-align: center; color: white;
              font-size: 2.4rem; font-weight: 800; margin-bottom: 8px;}
    .rev {background: #1F2937; border-radius: 12px; padding: 10px 14px; margin-bottom: 8px;}
    .fila {display: flex; justify-content: space-between; font-size: .85rem; margin-top: 10px;}
    .pista {background: #1F2937; border-radius: 99px; height: 10px; margin-top: 5px;}
    .relleno {height: 10px; border-radius: 99px;}
    .etiqueta {display:inline-block; font-size:.75rem; padding:2px 10px; border-radius:99px;
               background:#374151; color:#D1D5DB; margin-bottom:6px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="titulo">🧠 Algoritmos de búsqueda en IA</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Estudia la teoría, consulta el infográfico y ponte a prueba.</div>',
            unsafe_allow_html=True)

# ============================================================================
# BARRA SUPERIOR DE NAVEGACIÓN
# ============================================================================
SECCIONES = ["Información", "Infográfico PDF", "Test"]
ICONOS = ["book", "file-earmark-pdf", "patch-question"]

if option_menu:
    seccion = option_menu(
        None, SECCIONES, icons=ICONOS, orientation="horizontal", default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#1F2937", "border-radius": "12px"},
            "icon": {"font-size": "16px"},
            "nav-link": {"font-size": "15px", "text-align": "center", "margin": "4px",
                         "color": "#D1D5DB", "--hover-color": "#374151"},
            "nav-link-selected": {"background-color": "#3B82F6", "color": "white"},
        },
    )
else:
    seccion = st.radio("Sección", SECCIONES, horizontal=True, label_visibility="collapsed")

st.write("")


# ============================================================================
# SECCIÓN 1 — INFORMACIÓN
# ============================================================================
def lista(items):
    st.markdown("\n".join(f"- {x}" for x in items))


def mostrar_teoria(clave):
    f = C.FAMILIAS[clave]
    color = C.COLORES[clave]
    st.markdown(
        f"<div class='banda' style='border-left-color:{color}'>"
        f"<b style='font-size:1.3rem'>{f['titulo']}</b> <small>· {f['alias']}</small><br>{f['resumen']}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("#### ¿Cómo es?")
    lista(f["caracteristicas"])

    st.markdown(f"#### {f['parametros_titulo']}")
    lista(f["parametros"])

    st.markdown(f"#### {f['frontera_titulo']}")
    lista(f["frontera"])

    st.markdown(f"#### {f['criterios_titulo']}")
    lista(f["criterios"])

    st.markdown(f"#### {f['algoritmos_titulo']}")
    for a in f["algoritmos"]:
        with st.expander(a["nombre"]):
            st.markdown(a["definicion"])
            st.markdown(f"**Estructura:** {a['estructura']}")
            st.markdown("**Cómo funciona**")
            if len(a["pasos"]) == 1:
                st.markdown(a["pasos"][0])
            else:
                st.markdown("\n".join(f"{i}. {p}" for i, p in enumerate(a["pasos"], 1)))
            st.markdown(f"**Aplicación real:** {a['aplicacion']}")

    st.markdown("#### Resumen")
    filas = "\n".join(f"| {k} | {v} |" for k, v in f["tabla"])
    st.markdown(f"| Característica | {f['titulo'].replace('Búsqueda ', '').capitalize()} |\n| --- | --- |\n{filas}")


def ejemplos_noinformada():
    st.markdown("### 🎨 Ejemplos con dibujos")

    # --- BFS vs DFS
    st.markdown("#### 1. BFS vs DFS sobre el mismo árbol")
    st.caption("La meta es el nodo **G** (doble círculo). Los números indican el orden de expansión. "
               "Mueve el control para ver cada paso.")
    algoritmo = st.radio("Algoritmo", ["Amplitud (BFS)", "Profundidad (DFS)"], horizontal=True, key="ni_alg")
    tipo = "bfs" if algoritmo.startswith("Amplitud") else "dfs"
    pasos = D.simular_arbol(tipo)
    paso = st.slider("Paso", 1, len(pasos), min(3, len(pasos)), key=f"ni_paso_{tipo}")
    orden, actual, frontera = pasos[paso - 1]
    st.graphviz_chart(D.dot_arbol(orden, actual, C.COLORES["noinformada"]))
    if tipo == "bfs":
        st.markdown(f"**Frontera (cola FIFO, el primero sale primero):** `{frontera or 'vacía'}`")
    else:
        st.markdown(f"**Frontera (pila LIFO, el tope va primero):** `{list(reversed(frontera)) or 'vacía'}`")
    st.markdown(f"**Orden de expansión hasta ahora:** `{' → '.join(orden)}`")
    if paso == len(pasos):
        st.success(f"¡Meta encontrada! {algoritmo} expandió {len(orden)} nodos para llegar a G.")
    st.info("BFS encuentra la ruta con menos pasos, pero guarda muchos nodos en la cola. "
            "DFS usa poca memoria, pero puede explorar ramas largas que no llevan a la meta.")

    # --- UCS
    st.markdown("#### 2. Costo uniforme (Dijkstra)")
    st.caption("Los números sobre las flechas son los costos. Se expande siempre el nodo con menor costo acumulado g(n).")
    st.graphviz_chart(D.dot_grafo("ucs", mostrar_h=False))
    orden, camino, costo = D.buscar("ucs")
    st.markdown(f"Orden de expansión: `{' → '.join(orden)}` · Camino óptimo: `{' → '.join(camino)}` · Costo = **{costo}**")
    st.info("Observa que el camino S → B → G tiene menos pasos (2), pero cuesta 9. "
            "Costo uniforme prefiere el de menor costo (6), aunque tenga más pasos.")

    # --- Bidireccional
    st.markdown("#### 3. Búsqueda bidireccional")
    st.caption("Azul: búsqueda desde el inicio. Naranja: búsqueda desde la meta. Verde: donde se encuentran las fronteras.")
    st.graphviz_chart(D.dot_bidireccional())


def ejemplos_informada():
    st.markdown("### 🎨 Ejemplos con dibujos")

    st.markdown("#### 1. Una heurística real: el 8-puzzle")
    st.caption("En naranja, las fichas que no están en su lugar. h(n) = suma de las distancias Manhattan de cada ficha a su posición meta.")
    html_puzzle, manhattan, fuera = D.html_puzzle()
    st.markdown(html_puzzle, unsafe_allow_html=True)
    st.markdown(f"Fichas fuera de lugar: **{fuera}** · Heurística de Manhattan: **h(n) = {manhattan}**")
    st.info("La ficha 5 y la ficha 8 están a 1 movimiento de su lugar, por eso h(n) = 1 + 1 = 2. "
            "Es admisible: nunca sobreestima los movimientos reales que faltan.")

    st.markdown("#### 2. Voraz vs A* sobre el mismo grafo")
    st.caption("Sobre las flechas va el costo real; dentro de cada nodo, la heurística h(n). "
               "Los nodos naranjas/azules son los expandidos (con su orden) y el camino final va en verde.")
    alg = st.radio("Algoritmo", ["Voraz (solo h)", "A* (g + h)"], horizontal=True, key="inf_alg")
    clave = "voraz" if alg.startswith("Voraz") else "astar"
    st.graphviz_chart(D.dot_grafo(clave, mostrar_h=True))
    orden, camino, costo = D.buscar(clave)
    st.markdown(f"Orden de expansión: `{' → '.join(orden)}` · Camino: `{' → '.join(camino)}` · Costo = **{costo}**")
    if clave == "voraz":
        st.warning("La voraz se dejó llevar por h(B) = 2, que parece más cerca de la meta, y terminó con un camino de costo 9.")
    else:
        st.success("A* suma lo ya recorrido g(n) a la estimación h(n): f(B) = 3 + 2 = 5 se explora, "
                   "pero f(A) = 2 + 4 = 6 y luego f(D) = 4 + 2 = 6 llevan al camino óptimo de costo 6.")

    st.markdown("#### 3. Fórmulas clave")
    st.markdown("- Voraz: **f(n) = h(n)**\n- A*: **f(n) = g(n) + h(n)**\n- A* ponderado: **f(n) = g(n) + w·h(n)**, con w > 1")


def ejemplos_evolutiva():
    st.markdown("### 🎨 Ejemplos con dibujos")

    st.markdown("#### 1. El ciclo de un algoritmo evolutivo")
    st.graphviz_chart(D.dot_ciclo_evolutivo())

    st.markdown("#### 2. Cruce y mutación con cromosomas de bits")
    st.caption("Aptitud = cantidad de unos. Cambia el punto de cruce y el gen que muta.")
    c1, c2 = st.columns(2)
    corte = c1.slider("Punto de cruce", 1, 7, 4, key="ev_corte")
    pos = c2.slider("Gen que muta (0 a 7)", 0, 7, 2, key="ev_mut")
    st.markdown(D.html_cruce(corte, pos), unsafe_allow_html=True)

    st.markdown("#### 3. Pruébalo: algoritmo genético en vivo")
    st.caption("Problema “OneMax”: encontrar el cromosoma con todos los bits en 1 usando selección por torneo, cruce y mutación.")
    c1, c2, c3 = st.columns(3)
    n_genes = c1.slider("Genes por individuo", 10, 60, 30, key="ga_genes")
    tam_pob = c2.slider("Tamaño de población", 6, 100, 30, key="ga_pob")
    pm = c3.slider("Prob. de mutación (pm)", 0.0, 0.2, 0.02, 0.005, key="ga_pm")
    gens = st.slider("Máximo de generaciones", 5, 200, 60, key="ga_gens")
    if st.button("▶ Ejecutar algoritmo genético", key="ga_run"):
        mejor, prom, ind = D.ejecutar_ga(n_genes, tam_pob, pm, gens)
        st.line_chart({"Mejor aptitud": mejor, "Aptitud promedio": prom})
        st.markdown(f"Generaciones usadas: **{len(mejor) - 1}** · Mejor aptitud: **{mejor[-1]} / {n_genes}**")
        st.code("".join(map(str, ind)), language=None)
        if mejor[-1] == n_genes:
            st.success("¡Solución óptima encontrada! El criterio de paro fue alcanzar la aptitud objetivo.")
        else:
            st.info("Se llegó al máximo de generaciones con una buena aproximación: "
                    "la búsqueda evolutiva no garantiza el óptimo.")


def seccion_informacion():
    st.header("Información general")
    st.write("Elige una familia de algoritmos de búsqueda. Cada una incluye teoría, algoritmos y ejemplos con dibujos.")
    t1, t2, t3 = st.tabs(["🟧 No informada", "🟦 Informada", "🟩 Evolutiva"])
    with t1:
        mostrar_teoria("noinformada")
        ejemplos_noinformada()
    with t2:
        mostrar_teoria("informada")
        ejemplos_informada()
    with t3:
        mostrar_teoria("evolutiva")
        ejemplos_evolutiva()


# ============================================================================
# SECCIÓN 2 — PDF
# ============================================================================
@st.cache_data(show_spinner="Preparando el infográfico…")
def pdf_a_imagenes(ruta: str, zoom: float = 1.6):
    import pymupdf
    doc = pymupdf.open(ruta)
    return [p.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).tobytes("png") for p in doc]


def seccion_pdf():
    st.header("Infográfico: clasificación de los algoritmos")
    if not PDF_PATH.exists():
        st.error(f"No se encontró el archivo `{PDF_PATH.name}`. Súbelo al repositorio junto a app.py.")
        return

    datos = PDF_PATH.read_bytes()
    st.download_button("⬇ Descargar PDF", datos, file_name=PDF_PATH.name, mime="application/pdf")
    st.caption("Pasa el cursor sobre la imagen y pulsa el icono de pantalla completa para verla más grande.")
    try:
        for img in pdf_a_imagenes(str(PDF_PATH)):
            st.image(img, **ANCHO)
    except Exception:  # noqa: BLE001  (si PyMuPDF no está disponible, se incrusta el PDF)
        b64 = base64.b64encode(datos).decode()
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="900" type="application/pdf"></iframe>',
            unsafe_allow_html=True,
        )


# ============================================================================
# SECCIÓN 3 — TEST (ML4K)
# ============================================================================
def normalizar_etiqueta(nombre: str) -> str:
    n = unicodedata.normalize("NFD", nombre.lower())
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    n = re.sub(r"[\s_\-]+", "", n)
    if "noinformada" in n or "desinformada" in n:
        return "noinformada"
    if "informada" in n:
        return "informada"
    if "evolutiv" in n:
        return "evolutiva"
    return "ninguna"


def clasificar(texto: str, key: str) -> dict:
    if not key or key.startswith("PEGA_AQUI"):
        raise RuntimeError("Falta la API key de Machine Learning for Kids.")

    resp = requests.get(API_URL.format(key=key), params={"data": texto}, timeout=20)
    if resp.status_code == 409:
        raise RuntimeError("El modelo aún no está entrenado. Entrénalo en 'Learn & Test'.")
    resp.raise_for_status()

    datos = resp.json()
    if isinstance(datos, dict):
        datos = datos.get("classes") or [datos]

    resultado = {k: 0.0 for k in CATEGORIAS}
    for item in datos:
        nombre = item.get("class_name") or item.get("label") or ""
        clave = normalizar_etiqueta(nombre)
        resultado[clave] = max(resultado[clave], float(item.get("confidence", 0)))
    return resultado


def crear_test() -> list:
    """10 preguntas: 3 de clasificar definiciones (una por familia, con opinión de ML4K)
    + 7 al azar entre las demás (conceptos del documento y más definiciones), en orden aleatorio."""
    clasif = [(k, t, e) for k, t, e in C.BANCO_CLASIFICAR]
    elegidas = [random.choice([q for q in clasif if q[0] == c])
                for c in ("informada", "noinformada", "evolutiva")]

    preguntas = []
    for cat, texto, expl in elegidas:
        preguntas.append({"tipo": "clasificar", "texto": texto,
                          "opciones": [v[0] for v in CATEGORIAS.values()],
                          "correcta": CATEGORIAS[cat][0], "explicacion": expl})

    pool = [("clasificar", q) for q in clasif if q not in elegidas] + \
           [("concepto", q) for q in C.BANCO_CONCEPTOS]
    for tipo, q in random.sample(pool, NUM_PREGUNTAS - len(preguntas)):
        if tipo == "clasificar":
            cat, texto, expl = q
            preguntas.append({"tipo": "clasificar", "texto": texto,
                              "opciones": [v[0] for v in CATEGORIAS.values()],
                              "correcta": CATEGORIAS[cat][0], "explicacion": expl})
        else:
            texto, correcta, malas, expl = q
            opciones = [correcta] + list(malas)
            random.shuffle(opciones)
            preguntas.append({"tipo": "concepto", "texto": texto, "opciones": opciones,
                              "correcta": correcta, "explicacion": expl})
    random.shuffle(preguntas)
    return preguntas


def iniciar():
    st.session_state.test_id = st.session_state.get("test_id", 0) + 1  # claves nuevas para los radios
    st.session_state.test = crear_test()
    st.session_state.idx = 0
    st.session_state.puntos = 0
    st.session_state.respondida = False
    st.session_state.ml = None
    st.session_state.ml_error = None
    st.session_state.registro = []
    st.session_state.terminado = False


def clave_radio(idx: int) -> str:
    return f"op_{st.session_state.test_id}_{idx}"


def responder(key: str):
    idx = st.session_state.idx
    q = st.session_state.test[idx]
    eleccion = st.session_state[clave_radio(idx)]
    acierto = eleccion == q["correcta"]

    st.session_state.ml, st.session_state.ml_error = None, None
    if q["tipo"] == "clasificar":   # solo las definiciones se consultan al modelo de ML4K
        try:
            st.session_state.ml = clasificar(q["texto"], key)
        except Exception as e:  # noqa: BLE001
            st.session_state.ml_error = str(e)

    st.session_state.respondida = True
    st.session_state.puntos += int(acierto)
    st.session_state.registro.append({"q": q, "eleccion": eleccion, "acierto": acierto})


def siguiente():
    if st.session_state.idx + 1 >= NUM_PREGUNTAS:
        st.session_state.terminado = True
    else:
        st.session_state.idx += 1
        st.session_state.respondida = False
        st.session_state.ml, st.session_state.ml_error = None, None


def seccion_test(key_activa: str):
    if "test" not in st.session_state:
        iniciar()

    st.header(f"Test de {NUM_PREGUNTAS} preguntas")

    if not st.session_state.terminado:
        idx = st.session_state.idx
        q = st.session_state.test[idx]

        st.progress(idx / NUM_PREGUNTAS, text=f"Pregunta {idx + 1} de {NUM_PREGUNTAS}")
        etiqueta = "Clasifica la definición" if q["tipo"] == "clasificar" else "Concepto"
        st.markdown(f'<span class="etiqueta">{etiqueta}</span>'
                    f'<div class="pregunta">{html.escape(q["texto"])}</div>', unsafe_allow_html=True)
        if q["tipo"] == "clasificar":
            st.write("¿Qué tipo de búsqueda describe esta definición?")

        st.radio("Elige una opción", q["opciones"], index=None, key=clave_radio(idx),
                 label_visibility="collapsed", disabled=st.session_state.respondida)

        if not st.session_state.respondida:
            sin_respuesta = st.session_state.get(clave_radio(idx)) is None
            st.button("Responder", type="primary", on_click=responder, args=(key_activa,),
                      disabled=sin_respuesta, **ANCHO)
        else:
            ultimo = st.session_state.registro[-1]
            if ultimo["acierto"]:
                st.success("¡Es correcto! " + q["explicacion"])
            else:
                st.error(f"Es incorrecto. La respuesta correcta era: **{q['correcta']}**. " + q["explicacion"])

            if q["tipo"] == "clasificar":
                st.markdown("**Opinión del modelo de Machine Learning for Kids**")
                if st.session_state.ml_error:
                    st.warning(f"No se pudo consultar el modelo: {st.session_state.ml_error}")
                elif st.session_state.ml:
                    ml = st.session_state.ml
                    for clave, (nombre, color) in CATEGORIAS.items():
                        v = max(0.0, min(100.0, ml[clave]))
                        st.markdown(
                            f'<div class="fila"><span>{nombre}</span><b>{v:.0f}%</b></div>'
                            f'<div class="pista"><div class="relleno" style="width:{v}%;background:{color}"></div></div>',
                            unsafe_allow_html=True,
                        )

            etiqueta_btn = "Siguiente pregunta" if idx + 1 < NUM_PREGUNTAS else "Ver resultado"
            st.button(etiqueta_btn, type="primary", on_click=siguiente, **ANCHO)

    else:
        puntos = st.session_state.puntos
        if puntos >= NUM_PREGUNTAS * 0.9:
            color, msg = "#10B981", "¡Excelente! Has comprendido el tema"
        elif puntos >= NUM_PREGUNTAS * 0.6:
            color, msg = "#3B82F6", "¡Buen esfuerzo! Creo que puedes mejorar más"
        else:
            color, msg = "#F59E0B", "Repasa los conceptos en la sección de Información e inténtalo de nuevo"

        st.markdown(f'<div class="puntaje" style="background:{color}">{puntos} / {NUM_PREGUNTAS}</div>',
                    unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center'>{msg}</p>", unsafe_allow_html=True)

        st.subheader("Revisión")
        for i, r in enumerate(st.session_state.registro, start=1):
            icono = "✅" if r["acierto"] else "❌"
            detalle = "" if r["acierto"] else f"<br><small>Tu respuesta: {html.escape(r['eleccion'])}</small>"
            st.markdown(
                f'<div class="rev"><b>{icono} {i}. {html.escape(r["q"]["texto"])}</b><br>'
                f'<small>Correcta: {html.escape(r["q"]["correcta"])}</small>{detalle}</div>',
                unsafe_allow_html=True,
            )

        st.button("Realizar otro test", type="primary", on_click=iniciar, **ANCHO)


# ============================================================================
# ENRUTADOR
# ============================================================================
with st.sidebar:
    st.header("Configuración")
    key_usuario = st.text_input("API key de ML4K", value="", type="password",
                                help="Si lo dejas vacío se usa la clave definida en los secrets / variable de entorno")
    st.caption("La clave está en la sección de Python de tu proyecto en Machine Learning for Kids.")
key_activa = key_usuario.strip() or API_KEY

if seccion == "Información":
    seccion_informacion()
elif seccion == "Infográfico PDF":
    seccion_pdf()
else:
    seccion_test(key_activa)
