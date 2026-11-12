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


def _peso_de_opcion(modelo, opcion):
    """Peso del tipo de la opción (una estación solo cubre incidentes de su tipo)."""
    return modelo.pesos[opcion["tipo"]]


def _elegir_siguiente_con_estado(modelo, costo_total, cubiertos, lotes_usados, puntaje, cotas=None):
    """Busca la siguiente estación sin reconstruir el estado de la propuesta.

    Da exactamente la misma elección que `_elegir_siguiente`, pero más rápido:
    - una estación solo cubre incidentes de SU tipo, así que su valor nuevo es
      (bits nuevos) * peso del tipo: un solo `&` en vez de uno por tipo;
    - `cotas[i]` es un valor nuevo que la opción i NO puede superar (el que
      tenía antes: al cubrir más incidentes el valor nuevo solo baja). Se
      revisan las opciones de mayor a menor cota y se para cuando la cota ya
      no alcanza a la mejor: esas opciones no pueden ganar. Los empates se
      resuelven por la posición en `modelo.opciones`, como en el original.
    """
    presupuesto_restante = modelo.presupuesto - costo_total
    libres = ~cubiertos
    opciones = modelo.opciones
    candidatas = []
    for posicion in range(len(opciones)):
        opcion = opciones[posicion]
        if opcion["lote"] in lotes_usados:
            continue
        if opcion["costo"] > presupuesto_restante:
            continue
        if cotas is not None:
            cota = cotas[posicion]
            if cota == 0:
                continue
            candidatas.append((puntaje(cota, opcion["costo"]), posicion))
        else:
            candidatas.append((None, posicion))
    if cotas is not None:
        candidatas.sort(key=lambda par: (par[0], -par[1]), reverse=True)
    mejor_posicion = None
    mejor_puntaje = None
    for cota_puntaje, posicion in candidatas:
        if mejor_posicion is not None and cota_puntaje is not None and cota_puntaje < mejor_puntaje:
            break
        opcion = opciones[posicion]
        valor_nuevo = (opcion["mascara"] & libres).bit_count() * _peso_de_opcion(modelo, opcion)
        if cotas is not None:
            cotas[posicion] = valor_nuevo
        if valor_nuevo == 0:
            continue
        puntaje_de_la_opcion = puntaje(valor_nuevo, opcion["costo"])
        if (mejor_posicion is None or puntaje_de_la_opcion > mejor_puntaje
                or (puntaje_de_la_opcion == mejor_puntaje and posicion < mejor_posicion)):
            mejor_posicion = posicion
            mejor_puntaje = puntaje_de_la_opcion
    if mejor_posicion is None:
        return None
    return opciones[mejor_posicion]


def _cotas_iniciales(modelo):
    """Valor de cada opción sola (cota válida para cualquier propuesta), en caché."""
    cotas = getattr(modelo, "_cotas_del_goloso", None)
    if cotas is None:
        cotas = []
        for opcion in modelo.opciones:
            cotas.append(opcion["mascara"].bit_count() * _peso_de_opcion(modelo, opcion))
        modelo._cotas_del_goloso = cotas
    return list(cotas)


def _cotas_exactas(modelo, cubiertos):
    """Valor nuevo exacto de cada opción dado lo ya cubierto.

    Sirve de cota para cualquier propuesta que cubra AL MENOS eso: la búsqueda
    local la calcula una vez por cada "resto" y la reutiliza en todos los
    vecinos que salen de ese resto.
    """
    libres = ~cubiertos
    cotas = []
    for opcion in modelo.opciones:
        cotas.append((opcion["mascara"] & libres).bit_count() * _peso_de_opcion(modelo, opcion))
    return cotas


def goloso(modelo, puntaje, estaciones_iniciales=None, cotas=None):
    """Agrega estaciones una a una (la de mayor puntaje) hasta que ninguna aporte.

    `estaciones_iniciales` permite arrancar desde una propuesta parcial;
    la usa `propia_ls` para completar propuestas. `cotas` (opcional) son
    cotas válidas del valor nuevo de cada opción para esa propuesta parcial;
    solo aceleran, nunca cambian la elección.
    """
    propuesta = []
    if estaciones_iniciales is not None:
        propuesta = list(estaciones_iniciales)
    costo_total, cubiertos, lotes_usados = resumir(modelo, propuesta)
    if cotas is None:
        cotas = _cotas_iniciales(modelo)
    else:
        cotas = list(cotas)
    while True:
        opcion = _elegir_siguiente_con_estado(
            modelo, costo_total, cubiertos, lotes_usados, puntaje, cotas
        )
        if opcion is None:
            return propuesta
        estacion = (opcion["lote"], opcion["tipo"])
        propuesta.append(estacion)
        costo_total += opcion["costo"]
        cubiertos |= opcion["mascara"]
        lotes_usados.add(opcion["lote"])


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


def _contexto_de_resto(modelo, resto):
    """Lo que comparten todos los vecinos que salen de un mismo `resto`.

    Costo, cobertura y lotes del resto, más las opciones ordenadas de mayor a
    menor cota (su valor nuevo exacto respecto al resto). Así completar cada
    vecino no recorre todas las opciones: ver `_rellenar`.
    """
    costo_resto, cubiertos, lotes_usados = resumir(modelo, resto)
    cotas = _cotas_exactas(modelo, cubiertos)
    orden = []
    for posicion in range(len(modelo.opciones)):
        if cotas[posicion] > 0:
            opcion = modelo.opciones[posicion]
            orden.append((puntaje_razon(cotas[posicion], opcion["costo"]), posicion))
    orden.sort(key=lambda par: (par[0], -par[1]), reverse=True)
    return {"resto": resto, "costo": costo_resto, "cubiertos": cubiertos,
            "lotes": lotes_usados, "orden": orden}


def _rellenar(modelo, contexto, opcion_nueva):
    """resto + opcion_nueva, completado con el goloso de la razón.

    Devuelve (propuesta, valor, costo) y elige EXACTAMENTE lo mismo que
    `goloso(modelo, puntaje_razon, resto + [nueva])`: se revisan las opciones
    en orden de cota decreciente y se para cuando la cota ya no alcanza a la
    mejor (el valor nuevo nunca supera la cota, porque la propuesta cubre al
    menos lo del resto). Los empates van a la opción de menor posición.
    """
    opciones = modelo.opciones
    pesos = modelo.pesos
    presupuesto = modelo.presupuesto
    propuesta = contexto["resto"] + [(opcion_nueva["lote"], opcion_nueva["tipo"])]
    costo_total = contexto["costo"] + opcion_nueva["costo"]
    cubiertos = contexto["cubiertos"] | opcion_nueva["mascara"]
    lotes_usados = set(contexto["lotes"])
    lotes_usados.add(opcion_nueva["lote"])
    orden = contexto["orden"]
    agotadas = set()
    while True:
        restante = presupuesto - costo_total
        libres = ~cubiertos
        mejor_posicion = None
        mejor_puntaje = None
        for cota_puntaje, posicion in orden:
            if mejor_posicion is not None and cota_puntaje < mejor_puntaje:
                break
            if posicion in agotadas:
                continue
            opcion = opciones[posicion]
            if opcion["lote"] in lotes_usados or opcion["costo"] > restante:
                continue
            valor_nuevo = (opcion["mascara"] & libres).bit_count() * pesos[opcion["tipo"]]
            if valor_nuevo == 0:
                # Con más cobertura seguirá en 0: no se vuelve a mirar.
                agotadas.add(posicion)
                continue
            puntaje_de_la_opcion = puntaje_razon(valor_nuevo, opcion["costo"])
            if (mejor_posicion is None or puntaje_de_la_opcion > mejor_puntaje
                    or (puntaje_de_la_opcion == mejor_puntaje and posicion < mejor_posicion)):
                mejor_posicion = posicion
                mejor_puntaje = puntaje_de_la_opcion
        if mejor_posicion is None:
            return propuesta, modelo.valor_mask(cubiertos), costo_total
        opcion = opciones[mejor_posicion]
        propuesta.append((opcion["lote"], opcion["tipo"]))
        costo_total += opcion["costo"]
        cubiertos |= opcion["mascara"]
        lotes_usados.add(opcion["lote"])


def _reemplazos(modelo, propuesta):
    """Vecinos que cambian UNA estación por otra (otro tipo u otro lote libre)."""
    vecinos = []
    for posicion in range(len(propuesta)):
        resto = _sin_posiciones(propuesta, [posicion])
        contexto = _contexto_de_resto(modelo, resto)
        for opcion in modelo.opciones:
            nueva = (opcion["lote"], opcion["tipo"])
            if nueva == propuesta[posicion]:
                continue
            if opcion["lote"] in contexto["lotes"]:
                continue
            if contexto["costo"] + opcion["costo"] > modelo.presupuesto:
                continue
            vecinos.append((contexto, opcion))
    return vecinos


def _quitar_uno_o_dos(modelo, propuesta):
    """Vecinos que quitan una o dos estaciones (el hueco se rellena después)."""
    vecinos = []
    for primera in range(len(propuesta)):
        vecinos.append((_sin_posiciones(propuesta, [primera]), None))
        for segunda in range(primera + 1, len(propuesta)):
            vecinos.append((_sin_posiciones(propuesta, [primera, segunda]), None))
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
            contexto = _contexto_de_resto(modelo, resto)
            for opcion in modelo.opciones:
                if opcion["lote"] in contexto["lotes"]:
                    continue
                if contexto["costo"] + opcion["costo"] > modelo.presupuesto:
                    continue
                vecinos.append((contexto, opcion))
    return vecinos


def _mejor_entre(modelo, actual, vecinos, plazo=None):
    """Rellena cada vecino con el goloso y devuelve el mejor si supera a `actual`.

    Devuelve None si ninguno es mejor. Se toma la MEJOR mejora (no la
    primera) para avanzar con pasos grandes. Si se acaba el plazo, deja de
    revisar vecinos y devuelve lo mejor que encontró hasta ahí.
    """
    mejor = None
    # (valor, costo) de la referencia: se calcula una vez, no por cada vecino.
    valor_referencia, costo_referencia = _valor_y_costo(modelo, actual)
    for vecino, opcion in vecinos:
        if _se_acabo_el_tiempo(plazo):
            break
        if opcion is None:
            completo = goloso(modelo, puntaje_razon, vecino)
            valor, costo = _valor_y_costo(modelo, completo)
        else:
            completo, valor, costo = _rellenar(modelo, vecino, opcion)
        # Misma regla que `_es_mejor`: más valor, o el mismo valor gastando menos.
        if valor > valor_referencia or (valor == valor_referencia and costo < costo_referencia):
            mejor = completo
            valor_referencia, costo_referencia = valor, costo
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
