"""Parte 3: la mejor propuesta posible con backtracking y Branch & Bound.

Se recorre un árbol de decisiones: en el nivel i se decide qué hacer con el
lote i (no construir, o construir una de sus estaciones). Para no recorrer los
4^n caminos, se "podan" las ramas que con seguridad no pueden mejorar la mejor
propuesta ya encontrada.

Regla de desempate (determinista): gana la propuesta de MAYOR valor; entre
las de igual valor, la de MENOR costo; si también empatan en costo, se queda
la primera que se encontró (la del arranque o, si no, la primera en el orden
fijo de exploración).

Límite de tiempo opcional, de extremo a extremo (arranque incluido): si se
acaba, se devuelve la mejor propuesta encontrada hasta ese momento (nunca
peor que el arranque heurístico) y el resultado dice `optimo_certificado: False`.
"""

import time

from .heuristicas import propia_ls
from .lectura import clave_de_lote, ordenar_por_lote


# Mirar el reloj en cada nodo gastaría tiempo; cada 1000 nodos basta
# (en comuna 1000 nodos tardan unos milisegundos).
NODOS_ENTRE_REVISIONES_DEL_RELOJ = 1000


def _opciones_utiles(modelo, codigo_lote):
    """Estaciones de un lote, sin las "dominadas", ordenadas por rendimiento.

    Una estación A está dominada por otra B del MISMO lote si B cubre todo lo
    que cubre A y cuesta lo mismo o menos. Descartar A es seguro: en cualquier
    propuesta con A se puede poner B en su lugar (mismo lote) y el valor no
    baja ni el costo sube, así que nunca se pierde el óptimo.
    """
    todas = []
    for opcion in modelo.opciones:
        if opcion["lote"] == codigo_lote:
            todas.append(opcion)
    utiles = []
    for posicion in range(len(todas)):
        if not _esta_dominada(todas, posicion):
            utiles.append(todas[posicion])
    utiles.sort(key=lambda opcion: _rendimiento(modelo, opcion), reverse=True)
    return utiles


def _esta_dominada(opciones, posicion):
    """True si alguna otra opción cubre al menos lo mismo y no cuesta más.

    Si dos opciones son idénticas (misma cobertura y costo) se conserva la
    primera de la lista (orden hurto, accidente, incendio).
    """
    candidata = opciones[posicion]
    for otra_posicion in range(len(opciones)):
        if otra_posicion == posicion:
            continue
        otra = opciones[otra_posicion]
        cubre_todo = (candidata["mascara"] | otra["mascara"]) == otra["mascara"]
        no_cuesta_mas = otra["costo"] <= candidata["costo"]
        if not (cubre_todo and no_cuesta_mas):
            continue
        es_identica = otra["mascara"] == candidata["mascara"] and otra["costo"] == candidata["costo"]
        if not es_identica or otra_posicion < posicion:
            return True
    return False


def _rendimiento(modelo, opcion):
    """Valor de la estación por millón; se usa solo para decidir el ORDEN de exploración."""
    valor = modelo.valor_mask(opcion["mascara"])
    if opcion["costo"] <= 0:
        return float("inf")
    return valor / opcion["costo"]


def _preparar_lotes(modelo):
    """Lista de lotes a decidir: los de mayor potencial primero.

    Explorar primero los lotes que más valor pueden aportar hace que se
    encuentren pronto propuestas buenas, y con ellas las podas son mayores.
    El orden no afecta la correctitud: el árbol completo sigue siendo el mismo.
    """
    codigos = []
    for lote in modelo.instancia.lotes:
        codigos.append(lote.codigo)
    codigos.sort(key=clave_de_lote)
    lotes = []
    for codigo in codigos:
        opciones = _opciones_utiles(modelo, codigo)
        potencial = 0
        for opcion in opciones:
            potencial = max(potencial, modelo.valor_mask(opcion["mascara"]))
        lotes.append({"codigo": codigo, "opciones": opciones, "potencial": potencial})
    # sort es estable: a igual potencial se mantiene el orden por código.
    lotes.sort(key=lambda lote: lote["potencial"], reverse=True)
    return lotes


def _alcanzable_desde(lotes):
    """alcanzable[i] = máscara de todo lo que cubrirían los lotes i, i+1, ... juntos."""
    alcanzable = [0] * (len(lotes) + 1)
    for indice in range(len(lotes) - 1, -1, -1):
        union = alcanzable[indice + 1]
        for opcion in lotes[indice]["opciones"]:
            union |= opcion["mascara"]
        alcanzable[indice] = union
    return alcanzable


def _cota_mochila(modelo, lotes, indice, cubiertos, presupuesto_restante):
    """Cota superior del valor final por "mochila fraccional" (con enteros).

    Por qué es válida (nunca subestima):
    1. A cada estación restante se le da su ganancia marginal SOLA, respecto a
       lo ya cubierto. Dos estaciones juntas nunca suman más que sus
       ganancias por separado (un incidente compartido cuenta una sola vez).
    2. Se ignora la regla de un lote, una estación (relajar reglas solo puede
       subir el máximo).
    3. Se permite comprar "un pedazo" de una estación (mochila fraccional);
       llenarla por mejor razón ganancia/costo da el máximo de esa relajación.
    El pedazo se redondea hacia abajo (//): como el valor real siempre es un
    entero, si la cota real es 20.7 ninguna propuesta pasa de 20.
    """
    estaciones = []
    total = modelo.valor_mask(cubiertos)
    for lote in lotes[indice:]:
        for opcion in lote["opciones"]:
            ganancia = modelo.valor_mask(opcion["mascara"] & ~cubiertos)
            if ganancia == 0:
                continue
            if opcion["costo"] <= 0:
                total += ganancia
                continue
            # La razón en float solo ORDENA; con números de este tamaño dos
            # razones distintas nunca se confunden, y empates no cambian la cota.
            estaciones.append((ganancia / opcion["costo"], ganancia, opcion["costo"]))
    estaciones.sort(reverse=True)
    capacidad = presupuesto_restante
    for razon, ganancia, costo in estaciones:
        if costo <= capacidad:
            total += ganancia
            capacidad -= costo
        else:
            total += (ganancia * capacidad) // costo
            break
    return total


def _no_puede_ganar(busqueda, cota, costo_actual):
    """True si con esa cota la rama no puede superar a la mejor propuesta.

    Se poda si la cota es menor que el mejor valor, o si es igual pero ya se
    gastó tanto como la mejor (agregar estaciones solo sube el costo, así que
    no se puede ganar ni por el desempate de menor costo).
    """
    if cota < busqueda["mejor_valor"]:
        return True
    return cota == busqueda["mejor_valor"] and costo_actual >= busqueda["mejor_costo"]


def _hay_que_podar(busqueda, indice, cubiertos, presupuesto_restante, costo_actual):
    """Aplica primero la cota barata y, si no alcanza, la de mochila."""
    modelo = busqueda["modelo"]
    # Cota barata: aunque construyeramos todo lo que queda, no se puede
    # cubrir más que la unión de coberturas de los lotes restantes.
    todo_lo_alcanzable = cubiertos | busqueda["alcanzable"][indice]
    if _no_puede_ganar(busqueda, modelo.valor_mask(todo_lo_alcanzable), costo_actual):
        return True
    cota = _cota_mochila(modelo, busqueda["lotes"], indice, cubiertos, presupuesto_restante)
    return _no_puede_ganar(busqueda, cota, costo_actual)


def _considerar(busqueda, propuesta, cubiertos, costo_actual):
    """Si la propuesta actual es mejor que la guardada, la guarda (copiada)."""
    valor = busqueda["modelo"].valor_mask(cubiertos)
    mejora_valor = valor > busqueda["mejor_valor"]
    mismo_valor_mas_barato = valor == busqueda["mejor_valor"] and costo_actual < busqueda["mejor_costo"]
    if mejora_valor or mismo_valor_mas_barato:
        busqueda["mejor_valor"] = valor
        busqueda["mejor_costo"] = costo_actual
        busqueda["mejor_propuesta"] = list(propuesta)


def _tiempo_agotado(busqueda):
    """True si hay límite de tiempo y ya se pasó.

    El reloj se mira en el nodo 1, 1001, 2001...: así hasta un límite casi
    cero se nota desde el primer nodo.
    """
    if busqueda["limite_segundos"] is None:
        return False
    if busqueda["nodos"] % NODOS_ENTRE_REVISIONES_DEL_RELOJ != 1:
        return False
    transcurrido = time.perf_counter() - busqueda["inicio"]
    return transcurrido >= busqueda["limite_segundos"]


def _explorar(busqueda, indice, cubiertos, presupuesto_restante, propuesta):
    """Backtracking: decide el lote `indice` y baja recursivamente al siguiente."""
    if busqueda["cortada_por_tiempo"]:
        # Ya se acabó el tiempo: todas las llamadas pendientes terminan aquí.
        return
    busqueda["nodos"] += 1
    if _tiempo_agotado(busqueda):
        busqueda["cortada_por_tiempo"] = True
        return
    costo_actual = busqueda["modelo"].presupuesto - presupuesto_restante
    _considerar(busqueda, propuesta, cubiertos, costo_actual)
    if indice == len(busqueda["lotes"]):
        return
    if _hay_que_podar(busqueda, indice, cubiertos, presupuesto_restante, costo_actual):
        busqueda["podas_cota"] += 1
        return
    lote = busqueda["lotes"][indice]
    for opcion in lote["opciones"]:
        if opcion["costo"] > presupuesto_restante:
            busqueda["podas_presupuesto"] += 1
            continue
        if opcion["mascara"] & ~cubiertos == 0:
            # No cubre nada nuevo: construirla solo gastaría. La rama
            # "no construir" ya da el mismo valor con menos costo.
            continue
        propuesta.append((lote["codigo"], opcion["tipo"]))
        _explorar(busqueda, indice + 1, cubiertos | opcion["mascara"],
                  presupuesto_restante - opcion["costo"], propuesta)
        propuesta.pop()
    # Última rama: no construir nada en este lote.
    _explorar(busqueda, indice + 1, cubiertos, presupuesto_restante, propuesta)


def _tiempo_restante(inicio, limite_segundos):
    """Segundos que quedan del límite (nunca negativo); None si no hay límite."""
    if limite_segundos is None:
        return None
    gastado = time.perf_counter() - inicio
    return max(0, limite_segundos - gastado)


def resolver(modelo, limite_segundos=None):
    """Devuelve la mejor propuesta (validada con Modelo.evaluar) y estadísticas.

    Arranca con la mejor heurística como "mejor conocida" (warm start): así,
    desde el primer nodo, la poda compara contra una propuesta buena.
    `limite_segundos` (None = sin límite) cuenta desde que empieza la función,
    incluido el arranque: propia_ls recibe solo el tiempo que queda y, si lo
    gasta todo, el B&B se corta en su primer nodo. `optimo_certificado` dice
    si la búsqueda terminó completa.
    """
    inicio = time.perf_counter()
    lotes = _preparar_lotes(modelo)
    arranque = propia_ls(modelo, _tiempo_restante(inicio, limite_segundos))
    busqueda = {
        "modelo": modelo,
        "lotes": lotes,
        "alcanzable": _alcanzable_desde(lotes),
        "mejor_valor": arranque["valor"],
        "mejor_costo": arranque["costo_total"],
        "mejor_propuesta": list(arranque["estaciones"]),
        "nodos": 0,
        "podas_presupuesto": 0,
        "podas_cota": 0,
        "inicio": inicio,
        "limite_segundos": limite_segundos,
        "cortada_por_tiempo": False,
    }
    _explorar(busqueda, 0, 0, modelo.presupuesto, [])
    resultado = modelo.evaluar(ordenar_por_lote(busqueda["mejor_propuesta"]))
    resultado["optimo_certificado"] = not busqueda["cortada_por_tiempo"]
    resultado["estadisticas_bb"] = {
        "nodos": busqueda["nodos"],
        "podas_presupuesto": busqueda["podas_presupuesto"],
        "podas_cota": busqueda["podas_cota"],
        "valor_arranque": arranque["valor"],
    }
    resultado["tiempo_s"] = time.perf_counter() - inicio
    return resultado
