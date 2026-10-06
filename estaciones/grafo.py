"""Caminos más cortos sobre la red vial (grafo dirigido)."""

import heapq


def dijkstra_con_corte(grafo, origen, corte):
    """Distancia mínima desde `origen` a cada nodo que esté a <= `corte`.

    Es el Dijkstra clásico con una cola de prioridad (heapq). El corte existe
    porque solo interesan los nodos dentro del radio de alguna estación:
    no seguir más lejos ahorra mucho tiempo en la ciudad.
    Las distancias son enteros (ver lectura.py), así no hay errores de redondeo.
    """
    distancias = {origen: 0}
    cola = [(0, origen)]
    while cola:
        distancia, nodo = heapq.heappop(cola)
        if distancia > distancias[nodo]:
            # Entrada vieja de la cola: ya encontramos un camino más corto.
            continue
        for vecino, longitud in grafo.get(nodo, []):
            nueva_distancia = distancia + longitud
            if nueva_distancia > corte:
                continue
            if vecino not in distancias or nueva_distancia < distancias[vecino]:
                distancias[vecino] = nueva_distancia
                heapq.heappush(cola, (nueva_distancia, vecino))
    return distancias
