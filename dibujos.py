"""Dibujos (Graphviz / HTML) y mini-simulaciones para los ejemplos de cada búsqueda.

Todos los diagramas se pintan con colores explícitos para que se vean bien en tema oscuro.
"""
import heapq
import random

AZUL = "#3B82F6"
NARANJA = "#F59E0B"
VERDE = "#10B981"
ROJO = "#EF4444"
FONDO_NODO = "#1F2937"
BORDE = "#6B7280"
TEXTO = "#F9FAFB"
OSCURO = "#111827"

_CABECERA = (
    'bgcolor="transparent"; '
    'node [fontname="Helvetica", fontsize=12, style=filled, fillcolor="%s", '
    'fontcolor="%s", color="%s"]; '
    'edge [color="#9CA3AF", fontcolor="#D1D5DB", fontname="Helvetica", fontsize=11, arrowsize=0.7];'
    % (FONDO_NODO, TEXTO, BORDE)
)


# ============================================================================
# NO INFORMADA — BFS / DFS paso a paso sobre un árbol
# ============================================================================
HIJOS = {"A": ["B", "C"], "B": ["D", "E"], "C": ["F", "G"], "D": ["H", "I"]}
NODOS_ARBOL = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
META_ARBOL = "G"


def simular_arbol(tipo: str):
    """Devuelve una lista de pasos. Cada paso: (orden_de_expansion, nodo_actual, frontera)."""
    frontera, orden, pasos = ["A"], [], []
    while frontera:
        n = frontera.pop(0) if tipo == "bfs" else frontera.pop()
        orden.append(n)
        if n == META_ARBOL:
            pasos.append((list(orden), n, list(frontera)))
            break
        hijos = HIJOS.get(n, [])
        frontera.extend(hijos if tipo == "bfs" else reversed(hijos))
        pasos.append((list(orden), n, list(frontera)))
    return pasos


def dot_arbol(orden, actual, color):
    out = ["digraph G {", _CABECERA, "node [shape=circle];"]
    for n in NODOS_ARBOL:
        attrs = []
        if n in orden:
            attrs += [f'fillcolor="{color}"', f'fontcolor="{OSCURO}"',
                      f'label="{n}\\n{orden.index(n) + 1}"']
        if n == META_ARBOL:
            attrs += ["shape=doublecircle"]
        if n == actual:
            attrs += ['color="white"', "penwidth=3"]
        out.append(f'{n} [{", ".join(attrs)}];')
    for padre, hijos in HIJOS.items():
        for h in hijos:
            out.append(f"{padre} -> {h};")
    out.append("}")
    return "\n".join(out)


def dot_bidireccional():
    nodos = ["Inicio", "a", "b", "Encuentro", "c", "d", "Meta"]
    out = ["digraph G {", _CABECERA, "rankdir=LR; node [shape=circle];"]
    for i, n in enumerate(nodos):
        if i < 3:
            out.append(f'"{n}" [fillcolor="{AZUL}", fontcolor="{OSCURO}"];')
        elif i == 3:
            out.append(f'"{n}" [fillcolor="{VERDE}", fontcolor="{OSCURO}", shape=doublecircle];')
        else:
            out.append(f'"{n}" [fillcolor="{NARANJA}", fontcolor="{OSCURO}"];')
    for i in range(3):
        out.append(f'"{nodos[i]}" -> "{nodos[i + 1]}" [color="{AZUL}", penwidth=2];')
    for i in range(3, 6):
        out.append(f'"{nodos[i + 1]}" -> "{nodos[i]}" [color="{NARANJA}", penwidth=2];')
    out.append("}")
    return "\n".join(out)


# ============================================================================
# GRAFO PONDERADO — Costo uniforme / Voraz / A*
# ============================================================================
GRAFO = {"S": [("A", 2), ("B", 3)], "A": [("D", 2)], "B": [("G", 6)], "D": [("G", 2)], "G": []}
H = {"S": 6, "A": 4, "B": 2, "D": 2, "G": 0}   # heurística admisible


def buscar(alg: str):
    """alg: 'ucs' | 'voraz' | 'astar'. Devuelve (orden_expansion, camino, costo)."""
    clave = {"ucs": lambda g, h: g, "voraz": lambda g, h: h, "astar": lambda g, h: g + h}[alg]
    cont = 0
    frontera = [(clave(0, H["S"]), cont, "S", 0, ["S"])]
    cerrados, orden = set(), []
    while frontera:
        _, _, n, g, camino = heapq.heappop(frontera)
        if n in cerrados:
            continue
        cerrados.add(n)
        orden.append(n)
        if n == "G":
            return orden, camino, g
        for m, c in GRAFO[n]:
            if m not in cerrados:
                cont += 1
                heapq.heappush(frontera, (clave(g + c, H[m]), cont, m, g + c, camino + [m]))
    return orden, [], 0


def dot_grafo(alg: str, mostrar_h: bool):
    orden, camino, _ = buscar(alg)
    color = NARANJA if alg == "ucs" else AZUL
    aristas_camino = set(zip(camino, camino[1:]))
    out = ["digraph G {", _CABECERA, "rankdir=LR; node [shape=circle];"]
    for n in GRAFO:
        etiqueta = n
        if mostrar_h:
            etiqueta += f"\\nh={H[n]}"
        attrs = []
        if n in orden:
            etiqueta += f"\\n(#{orden.index(n) + 1})"
            attrs += [f'fillcolor="{color}"', f'fontcolor="{OSCURO}"']
        if n == "G":
            attrs.append("shape=doublecircle")
        out.append(f'{n} [label="{etiqueta}", {", ".join(attrs)}];')
    for n, vecinos in GRAFO.items():
        for m, c in vecinos:
            extra = f', color="{VERDE}", penwidth=3' if (n, m) in aristas_camino else ""
            out.append(f'{n} -> {m} [label="{c}"{extra}];')
    out.append("}")
    return "\n".join(out)


# ============================================================================
# INFORMADA — 8-puzzle con heurística de Manhattan
# ============================================================================
def html_puzzle():
    estado = [[1, 2, 3], [4, 0, 6], [7, 5, 8]]
    meta = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]
    pos_meta = {v: (r, c) for r, fila in enumerate(meta) for c, v in enumerate(fila)}
    manhattan, fuera = 0, 0
    mal = set()
    for r, fila in enumerate(estado):
        for c, v in enumerate(fila):
            if v:
                gr, gc = pos_meta[v]
                d = abs(r - gr) + abs(c - gc)
                manhattan += d
                if d:
                    fuera += 1
                    mal.add(v)

    def tablero(m, resaltar):
        celdas = ""
        for fila in m:
            celdas += "<div style='display:flex'>"
            for v in fila:
                if v == 0:
                    estilo = "background:transparent;border:2px dashed #6B7280;"
                    txt = ""
                elif v in resaltar:
                    estilo = f"background:{NARANJA};color:{OSCURO};"
                    txt = v
                else:
                    estilo = f"background:{AZUL};color:{OSCURO};"
                    txt = v
                celdas += (f"<div style='width:46px;height:46px;line-height:46px;margin:2px;"
                           f"text-align:center;font-weight:800;border-radius:8px;{estilo}'>{txt}</div>")
            celdas += "</div>"
        return celdas

    html = (
        "<div style='display:flex;gap:40px;align-items:center;flex-wrap:wrap;'>"
        f"<div><b>Estado actual</b>{tablero(estado, mal)}</div>"
        "<div style='font-size:2rem'>→</div>"
        f"<div><b>Meta</b>{tablero(meta, set())}</div>"
        "</div>"
    )
    return html, manhattan, fuera


# ============================================================================
# EVOLUTIVA — ciclo, cruce/mutación y mini algoritmo genético
# ============================================================================
def dot_ciclo_evolutivo():
    pasos = [
        ("ini", "Población inicial\\n(aleatoria)", AZUL),
        ("apt", "Evaluar aptitud\\nf(x)", NARANJA),
        ("sel", "Selección\\n(ruleta, torneo)", VERDE),
        ("cru", "Cruce\\n(probabilidad pc)", VERDE),
        ("mut", "Mutación\\n(probabilidad pm)", VERDE),
        ("nue", "Nueva\\ngeneración", AZUL),
    ]
    out = ["digraph G {", _CABECERA, "rankdir=LR; node [shape=box, style=\"filled,rounded\"];"]
    for k, label, col in pasos:
        out.append(f'{k} [label="{label}", fillcolor="{col}", fontcolor="{OSCURO}"];')
    out.append(f'paro [label="¿Criterio\\nde paro?", shape=diamond, fillcolor="{ROJO}", fontcolor="{OSCURO}"];')
    out.append(f'fin [label="Mejor\\nsolución", shape=box, style="filled,rounded", fillcolor="{VERDE}", fontcolor="{OSCURO}"];')
    out.append("ini -> apt -> sel -> cru -> mut -> nue -> paro;")
    out.append('paro -> fin [label="sí"];')
    out.append('paro -> apt [label="no (t + 1)", constraint=false];')
    out.append("}")
    return "\n".join(out)


def _gen(bit, color, borde_izq=False, resaltar=False):
    extra = ""
    if borde_izq:
        extra += "border-left:4px solid #F9FAFB;"
    if resaltar:
        extra += f"outline:3px solid {ROJO};"
    return (f"<span style='display:inline-block;width:34px;height:34px;line-height:34px;"
            f"text-align:center;margin:2px;border-radius:6px;font-weight:800;"
            f"color:{OSCURO};background:{color};{extra}'>{bit}</span>")


def html_cruce(corte: int, pos_mut: int):
    p1 = [1, 1, 0, 1, 0, 0, 1, 1]
    p2 = [0, 0, 1, 0, 1, 1, 0, 0]
    h1 = p1[:corte] + p2[corte:]
    h2 = p2[:corte] + p1[corte:]
    h1m = h1[:]
    h1m[pos_mut] = 1 - h1m[pos_mut]

    def fila(titulo, bits, colores, mut=None):
        celdas = "".join(_gen(b, colores[i], borde_izq=(i == corte), resaltar=(i == mut))
                         for i, b in enumerate(bits))
        return (f"<div style='display:flex;align-items:center;margin-bottom:4px'>"
                f"<div style='width:190px;font-size:.9rem'>{titulo}<br>"
                f"<small style='color:#9CA3AF'>aptitud = {sum(bits)}</small></div>{celdas}</div>")

    n = len(p1)
    c_p1, c_p2 = [AZUL] * n, [NARANJA] * n
    c_h1 = [AZUL if i < corte else NARANJA for i in range(n)]
    c_h2 = [NARANJA if i < corte else AZUL for i in range(n)]
    return (
        fila("Padre 1", p1, c_p1) + fila("Padre 2", p2, c_p2)
        + "<div style='margin:6px 0;color:#9CA3AF'>↓ cruce en un punto (línea blanca)</div>"
        + fila("Hijo 1", h1, c_h1) + fila("Hijo 2", h2, c_h2)
        + "<div style='margin:6px 0;color:#9CA3AF'>↓ mutación: se invierte un gen del Hijo 1 (borde rojo)</div>"
        + fila("Hijo 1 mutado", h1m, c_h1, mut=pos_mut)
    )


def ejecutar_ga(n_genes: int, tam_pob: int, pm: float, generaciones: int, pc: float = 0.8):
    """Algoritmo genético sencillo para el problema 'OneMax': maximizar la cantidad de 1s."""
    pob = [[random.randint(0, 1) for _ in range(n_genes)] for _ in range(tam_pob)]
    mejor_hist, prom_hist = [], []
    for _ in range(generaciones + 1):
        apt = [sum(i) for i in pob]
        mejor_hist.append(max(apt))
        prom_hist.append(sum(apt) / len(apt))
        if max(apt) == n_genes:
            break
        nueva = [max(pob, key=sum)[:]]  # elitismo: pasa el mejor
        while len(nueva) < tam_pob:
            p1 = max(random.sample(pob, 3), key=sum)   # selección por torneo
            p2 = max(random.sample(pob, 3), key=sum)
            if random.random() < pc:                    # cruce
                corte = random.randint(1, n_genes - 1)
                hijo = p1[:corte] + p2[corte:]
            else:
                hijo = p1[:]
            hijo = [1 - b if random.random() < pm else b for b in hijo]  # mutación
            nueva.append(hijo)
        pob = nueva
    return mejor_hist, prom_hist, max(pob, key=sum)
