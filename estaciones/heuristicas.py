"""Heurísticas: construyen propuestas factibles eligiendo una estación a la vez.

Todas usan la misma función `goloso`; lo único que cambia es el "puntaje"
con el que se decide cuál estación conviene más en cada paso.
"""

import time

from .lectura import ordenar_por_lote


# ---------------------------------------------------------------------------
# Puntajes: reciben el valor NUEVO que aporta una estación y su costo.
# Mayor puntaje = mejor estación.
# ---------------------------------------------------------------------------

def puntaje_base(valor_nuevo, costo):
    """Regla del enunciado (heurística base): solo importa cuánto valor nuevo agrega."""
    return valor_nuevo


def puntaje_razon(valor_nuevo, costo):
    """Valor nuevo por millón invertido; si empata, más valor y luego menos costo.

    Existe porque la base se gasta el presupuesto en estaciones caras;
    la razón premia a las estaciones que rinden más por cada peso gastado.
    """
    if costo <= 0:
        razon = float("inf")
    else:
        razon = valor_nuevo / costo
    return (razon, valor_nuevo, -costo)


# ---------------------------------------------------------------------------
# Goloso genérico
# ---------------------------------------------------------------------------

def resumir(modelo, propuesta):
    """Devuelve (costo_total, máscara de incidentes cubiertos, lotes usados)."""
    costo_total = 0
    cubiertos = 0
    lotes_usados = set()
    for codigo_lote, tipo in propuesta:
        costo_total += modelo.costo(codigo_lote, tipo)
        cubiertos |= modelo.cobertura_mask(codigo_lote, tipo)
        lotes_usados.add(codigo_lote)
    return costo_total, cubiertos, lotes_usados


def _elegir_siguiente(modelo, propuesta, puntaje):
    """Busca la estación libre y pagable con mayor puntaje; None si ninguna aporta.

    `modelo.opciones` ya viene ordenada por código de lote (orden natural) y,
    dentro del lote, hurto, accidente, incendio. Como solo se reemplaza a la
    mejor con un puntaje ESTRICTAMENTE mayor, en un empate gana la primera:
    justo el desempate que pide el enunciado.
    """
    costo_total, cubiertos, lotes_usados = resumir(modelo, propuesta)
    presupuesto_restante = modelo.presupuesto - costo_total
    mejor_opcion = None
    mejor_puntaje = None
    for opcion in modelo.opciones:
        if opcion["lote"] in lotes_usados:
            continue
        if opcion["costo"] > presupuesto_restante:
            continue
        valor_nuevo = modelo.valor_mask(opcion["mascara"] & ~cubiertos)
        if valor_nuevo == 0:
            continue
        puntaje_de_la_opcion = puntaje(valor_nuevo, opcion["costo"])
        if mejor_opcion is None or puntaje_de_la_opcion > mejor_puntaje:
            mejor_opcion = opcion
            mejor_puntaje = puntaje_de_la_opcion
    return mejor_opcion


def goloso(modelo, puntaje, estaciones_iniciales=None):
    """Agrega estaciones una a una (la de mayor puntaje) hasta que ninguna aporte.

    `estaciones_iniciales` permite arrancar desde una propuesta parcial;
    la usa `propia_ls` para completar propuestas.
    """
    propuesta = []
    if estaciones_iniciales is not None:
        propuesta = list(estaciones_iniciales)
    while True:
        opcion = _elegir_siguiente(modelo, propuesta, puntaje)
        if opcion is None:
            return propuesta
        propuesta.append((opcion["lote"], opcion["tipo"]))


def _resultado(modelo, propuesta):
    """Ordena por código de lote y valida/resume la propuesta con Modelo.evaluar."""
    return modelo.evaluar(ordenar_por_lote(propuesta))


def base(modelo):
    """Heurística base del enunciado (2.1): mayor valor nuevo en cada paso."""
    return _resultado(modelo, goloso(modelo, puntaje_base))


def propia(modelo):
    """Heurística propia simple: mayor valor nuevo por millón en cada paso."""
    return _resultado(modelo, goloso(modelo, puntaje_razon))


# ---------------------------------------------------------------------------
# propia_ls: varios arranques + mejora local
# ---------------------------------------------------------------------------

def _valor_y_costo(modelo, propuesta):
    """Devuelve (valor, costo_total) de una propuesta usando máscaras."""
    costo_total, cubiertos, lotes_usados = resumir(modelo, propuesta)
    return modelo.valor_mask(cubiertos), costo_total


def _es_mejor(modelo, candidata, actual):
    """True si `candidata` tiene más valor, o el mismo valor gastando menos."""
    valor_candidata, costo_candidata = _valor_y_costo(modelo, candidata)
    valor_actual, costo_actual = _valor_y_costo(modelo, actual)
    if valor_candidata != valor_actual:
        return valor_candidata > valor_actual
    return costo_candidata < costo_actual


def _se_acabo_el_tiempo(plazo):
    """True si hay un plazo (instante de time.perf_counter) y ya pasó.

    `plazo` None significa "sin límite": nunca se acaba el tiempo.
    """
    if plazo is None:
        return False
    return time.perf_counter() >= plazo


def _mejor_arranque(modelo, plazo=None):
    """Prueba varias construcciones golosas y se queda con la mejor.

    Además de los dos golosos normales, fuerza cada estación posible como
    PRIMERA elección y completa con la razón. Así se corrige el error típico
    del goloso: una mala primera decisión que condiciona todo lo demás.
    Si se acaba el plazo, deja de probar primeras estaciones y compara las
    que ya tiene (todas son factibles).
    """
    mejor = goloso(modelo, puntaje_razon)
    candidatas = [goloso(modelo, puntaje_base)]
    for opcion in modelo.opciones:
        if _se_acabo_el_tiempo(plazo):
            break
        if opcion["costo"] <= modelo.presupuesto:
            primera = [(opcion["lote"], opcion["tipo"])]
            candidatas.append(goloso(modelo, puntaje_razon, primera))
    for candidata in candidatas:
        if _es_mejor(modelo, candidata, mejor):
            mejor = candidata
    return mejor


def _sin_posiciones(propuesta, posiciones):
    """Copia de la propuesta sin las estaciones en esas posiciones."""
    restante = []
    for posicion in range(len(propuesta)):
        if posicion not in posiciones:
            restante.append(propuesta[posicion])
    return restante


def _reemplazos(modelo, propuesta):
    """Vecinos que cambian UNA estación por otra (otro tipo u otro lote libre)."""
    vecinos = []
    for posicion in range(len(propuesta)):
        resto = _sin_posiciones(propuesta, [posicion])
        costo_resto, cubiertos, lotes_usados = resumir(modelo, resto)
        for opcion in modelo.opciones:
            nueva = (opcion["lote"], opcion["tipo"])
            if nueva == propuesta[posicion]:
                continue
            if opcion["lote"] in lotes_usados:
                continue
            if costo_resto + opcion["costo"] > modelo.presupuesto:
                continue
            vecinos.append(resto + [nueva])
    return vecinos


def _quitar_uno_o_dos(modelo, propuesta):
    """Vecinos que quitan una o dos estaciones (el hueco se rellena después)."""
    vecinos = []
    for primera in range(len(propuesta)):
        vecinos.append(_sin_posiciones(propuesta, [primera]))
        for segunda in range(primera + 1, len(propuesta)):
            vecinos.append(_sin_posiciones(propuesta, [primera, segunda]))
    return vecinos


def _dobles_cambios(modelo, propuesta):
    """Vecinos que quitan DOS estaciones y ponen una estación nueva elegida.

    Sirve cuando hay que cambiar dos estaciones a la vez para mejorar (un
    solo cambio empeora). El relleno goloso posterior pone la segunda.
    Es el vecindario más caro, por eso solo se usa si los otros fallan.
    """
    vecinos = []
    for primera in range(len(propuesta)):
        for segunda in range(primera + 1, len(propuesta)):
            resto = _sin_posiciones(propuesta, [primera, segunda])
            costo_resto, cubiertos, lotes_usados = resumir(modelo, resto)
            for opcion in modelo.opciones:
                if opcion["lote"] in lotes_usados:
                    continue
                if costo_resto + opcion["costo"] > modelo.presupuesto:
                    continue
                vecinos.append(resto + [(opcion["lote"], opcion["tipo"])])
    return vecinos


def _mejor_entre(modelo, actual, vecinos, plazo=None):
    """Rellena cada vecino con el goloso y devuelve el mejor si supera a `actual`.

    Devuelve None si ninguno es mejor. Se toma la MEJOR mejora (no la
    primera) para avanzar con pasos grandes. Si se acaba el plazo, deja de
    revisar vecinos y devuelve lo mejor que encontró hasta ahí.
    """
    mejor = None
    for vecino in vecinos:
        if _se_acabo_el_tiempo(plazo):
            break
        completo = goloso(modelo, puntaje_razon, vecino)
        referencia = actual
        if mejor is not None:
            referencia = mejor
        if _es_mejor(modelo, completo, referencia):
            mejor = completo
    return mejor


def _mejor_vecino(modelo, actual, plazo=None):
    """Busca un vecino mejor: primero con cambios simples y, si no hay, dobles."""
    vecinos_simples = _reemplazos(modelo, actual) + _quitar_uno_o_dos(modelo, actual)
    mejor = _mejor_entre(modelo, actual, vecinos_simples, plazo)
    if mejor is not None:
        return mejor
    if _se_acabo_el_tiempo(plazo):
        # Armar la lista de dobles cambios ya cuesta tiempo: no vale la pena.
        return None
    return _mejor_entre(modelo, actual, _dobles_cambios(modelo, actual), plazo)


def _mejora_local(modelo, propuesta, plazo=None):
    """Salta al mejor vecino mientras exista uno mejor (y quede tiempo).

    Termina siempre: cada salto sube el valor o, con el mismo valor, baja el
    costo, y hay una cantidad finita de propuestas. Bajar el costo sin perder
    valor sirve porque libera presupuesto para una estación más después.
    Cada propuesta por la que pasa es factible, así que cortar por tiempo
    devuelve una propuesta válida.
    """
    actual = propuesta
    while not _se_acabo_el_tiempo(plazo):
        vecino = _mejor_vecino(modelo, actual, plazo)
        if vecino is None:
            return actual
        actual = vecino
    return actual


def propia_ls(modelo, limite_segundos=None):
    """Heurística propia fuerte: mejor de varios arranques golosos + mejora local.

    `limite_segundos` (None = sin límite) corta la búsqueda: se devuelve la
    mejor propuesta factible hallada hasta ese momento. Sin límite el
    resultado es siempre el mismo.
    """
    plazo = None
    if limite_segundos is not None:
        plazo = time.perf_counter() + limite_segundos
    inicial = _mejor_arranque(modelo, plazo)
    mejorada = _mejora_local(modelo, inicial, plazo)
    return _resultado(modelo, mejorada)
