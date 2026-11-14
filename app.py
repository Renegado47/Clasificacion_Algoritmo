import os
import random
import re
import unicodedata

import requests
import streamlit as st

# CONFIGURACIÓN 
# Clave para enlazarlo a la API de Machine Learning for Kids
API_KEY = os.getenv("ML4K_API_KEY") or st.secrets.get("ML4K_API_KEY", "")
API_URL = "https://machinelearningforkids.co.uk/api/scratch/{key}/classify"
NUM_PREGUNTAS = 4

CATEGORIAS = {
    "informada": ("Búsqueda informada", "#3B82F6"),
    "noinformada": ("Búsqueda no informada", "#F59E0B"),
    "evolutiva": ("Búsqueda evolutiva", "#10B981"),
    "ninguna": ("Ninguna de las anteriores", "#94A3B8"),
}

# Banco almacenado: (categoría correcta, definición, explicación)
BANCO = [
    ("informada", "Algoritmo que usa una función heurística para decidir qué nodo expandir primero.",
     "La heurística es conocimiento extra del problema: eso es búsqueda informada."),
    ("informada", "Algoritmo que combina el coste recorrido g(n) con una estimación h(n) hacia la meta.",
     "Es A*, el ejemplo clásico de búsqueda informada."),
    ("informada", "Búsqueda que siempre expande el nodo que parece más cercano a la meta según una estimación.",
     "La búsqueda voraz primero el mejor se guía por una heurística."),
    ("informada", "Método que explora menos nodos porque se orienta con una estimación de la distancia a la meta.",
     "Usar una estimación de la distancia a la meta caracteriza a la búsqueda informada."),

    ("noinformada", "Recorre el grafo nivel por nivel sin ningún conocimiento extra del problema.",
     "Es la búsqueda en anchura (BFS): no usa heurística."),
    ("noinformada", "Explora una rama hasta el fondo antes de retroceder, usando una pila.",
     "La búsqueda en profundidad es no informada."),
    ("noinformada", "Expande siempre el nodo con menor coste acumulado desde el inicio, sin estimar la distancia a la meta.",
     "El coste uniforme solo usa g(n); no tiene heurística."),
    ("noinformada", "Solo conoce los estados, las acciones y si un estado es la meta; no sabe qué tan cerca está de ella.",
     "Sin información sobre la cercanía a la meta, la búsqueda es no informada."),

    ("evolutiva", "Mantiene una población de soluciones que evolucionan mediante cruce y mutación.",
     "Es un algoritmo genético, típico de la búsqueda evolutiva."),
    ("evolutiva", "Evalúa cada individuo con una función de aptitud y selecciona a los mejores para reproducirse.",
     "Aptitud y selección son conceptos de la búsqueda evolutiva."),
    ("evolutiva", "Se inspira en la selección natural: los individuos mejor adaptados dejan más descendencia.",
     "Imita la evolución biológica: búsqueda evolutiva."),
    ("evolutiva", "Combina partes de dos soluciones padre y cambia genes al azar para crear nuevas soluciones.",
     "Cruce y mutación pertenecen a la búsqueda evolutiva."),

    ("ninguna", "Técnica para ordenar una lista comparando elementos adyacentes.",
     "Es el ordenamiento burbuja: no es un algoritmo de búsqueda en IA."),
    ("ninguna", "Estructura de datos que almacena pares clave-valor para acceder rápido a la información.",
     "Una tabla hash no es un tipo de búsqueda en IA."),
]


# LÓGICA ML4K
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


# LÓGICA DEL TEST
def crear_test() -> list:
    """4 preguntas: una de cada tipo de búsqueda + una extra al azar, en orden aleatorio."""
    elegidas = [random.choice([q for q in BANCO if q[0] == c])
                for c in ("informada", "noinformada", "evolutiva")]
    restantes = [q for q in BANCO if q not in elegidas]
    elegidas += random.sample(restantes, NUM_PREGUNTAS - len(elegidas))
    random.shuffle(elegidas)
    return [{"correcta": c, "texto": t, "explicacion": e} for c, t, e in elegidas]


def iniciar():
    st.session_state.test = crear_test()
    st.session_state.idx = 0
    st.session_state.puntos = 0
    st.session_state.respondida = False
    st.session_state.ml = None
    st.session_state.ml_error = None
    st.session_state.registro = []
    st.session_state.terminado = False


def responder(key: str):
    idx = st.session_state.idx
    q = st.session_state.test[idx]
    nombres = {v[0]: k for k, v in CATEGORIAS.items()}
    eleccion = nombres[st.session_state[f"op_{idx}"]]
    acierto = eleccion == q["correcta"]

    # Consulta al modelo de ML4K con la definición de la pregunta
    st.session_state.ml, st.session_state.ml_error = None, None
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


# ESTADO Y ESTILOS
st.set_page_config(page_title="Test de búsquedas en IA", page_icon="🧠", layout="centered")

if "test" not in st.session_state:
    iniciar()

st.markdown(
    """
    <style>
    .block-container {padding-top: 2.2rem; max-width: 800px;}
    .titulo {font-size: 2.2rem; font-weight: 800; margin-bottom: 0;}
    .subtitulo {color: #9CA3AF; margin-bottom: 1.4rem;}
    .pregunta {font-size: 1.25rem; font-weight: 700; margin: 6px 0 14px;
               background: #1F2937; border-radius: 12px; padding: 16px;}
    .puntaje {border-radius: 16px; padding: 28px; text-align: center; color: white;
              font-size: 2.4rem; font-weight: 800; margin-bottom: 8px;}
    .rev {background: #1F2937; border-radius: 12px; padding: 10px 14px; margin-bottom: 8px;}
    .fila {display: flex; justify-content: space-between; font-size: .85rem; margin-top: 10px;}
    .pista {background: #1F2937; border-radius: 99px; height: 10px; margin-top: 5px;}
    .relleno {height: 10px; border-radius: 99px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="titulo">Test de búsquedas en IA</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitulo">Lee la definición y elige qué tipo de búsqueda describe. '
    "El modelo de Machine Learning for Kids dará su opinión.</div>",
    unsafe_allow_html=True,
)

# Barra lateral: permite pegar la API key sin tocar el código
with st.sidebar:
    st.header("Configuración")
    key_usuario = st.text_input("API key de ML4K", value="", type="password",
                                help="Si lo dejas vacío se usa la clave definida en app.py")
    st.caption("La clave está en la sección de Python de tu proyecto en Machine Learning for Kids.")

key_activa = key_usuario.strip() or API_KEY

# INTERFAZ
if not st.session_state.terminado:
    idx = st.session_state.idx
    q = st.session_state.test[idx]

    st.progress(idx / NUM_PREGUNTAS, text=f"Pregunta {idx + 1} de {NUM_PREGUNTAS}")
    st.markdown(f'<div class="pregunta">{q["texto"]}</div>', unsafe_allow_html=True)
    st.write("¿Qué tipo de búsqueda describe esta definición?")

    opciones = [v[0] for v in CATEGORIAS.values()]
    st.radio("Elige una opción", opciones, index=None, key=f"op_{idx}",
             label_visibility="collapsed", disabled=st.session_state.respondida)

    if not st.session_state.respondida:
        sin_respuesta = st.session_state.get(f"op_{idx}") is None
        st.button("Responder", type="primary", on_click=responder, args=(key_activa,),
                  disabled=sin_respuesta, use_container_width=True)
    else:
        ultimo = st.session_state.registro[-1]
        if ultimo["acierto"]:
            st.success("¡Es correcto! " + q["explicacion"])
        else:
            st.error(f"Es incorrecto. La respuesta correcta era: "
                     f"**{CATEGORIAS[q['correcta']][0]}**. " + q["explicacion"])

        # Opinión del modelo de ML4K
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

        etiqueta = "Siguiente pregunta" if idx + 1 < NUM_PREGUNTAS else "Ver resultado"
        st.button(etiqueta, type="primary", on_click=siguiente, use_container_width=True)

else:
    puntos = st.session_state.puntos
    if puntos == NUM_PREGUNTAS:
        color, msg = "#10B981", "¡Excelente haz comprendido el tema"
    elif puntos >= NUM_PREGUNTAS / 2:
        color, msg = "#3B82F6", "¡Buen esfuerzo! Creo que puedes mejorar más"
    else:
        color, msg = "#F59E0B", "Repasa los conceptos e inténtalo de nuevo"

    st.markdown(f'<div class="puntaje" style="background:{color}">{puntos} / {NUM_PREGUNTAS}</div>',
                unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center'>{msg}</p>", unsafe_allow_html=True)

    st.subheader("Revisión")
    for i, r in enumerate(st.session_state.registro, start=1):
        icono = "Bien" if r["acierto"] else "Mal"
        detalle = "" if r["acierto"] else f"<br><small>Tu respuesta: {CATEGORIAS[r['eleccion']][0]}</small>"
        st.markdown(
            f'<div class="rev"><b>{icono} {i}. {r["q"]["texto"]}</b><br>'
            f'<small>Correcta: {CATEGORIAS[r["q"]["correcta"]][0]}</small>{detalle}</div>',
            unsafe_allow_html=True,
        )

    st.button("Realizar otro test", type="primary", on_click=iniciar, use_container_width=True)