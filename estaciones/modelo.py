"""Modelo del problema: costos, coberturas y evaluación de propuestas.

Idea clave: los incidentes se guardan como bits de un número entero
(una "máscara"). El incidente número k es el bit k: vale 1 si está cubierto
y 0 si no. Así, juntar coberturas de dos estaciones es un simple `|` (o),
y quitar los ya cubiertos es `& ~cubiertos`. Python maneja enteros de
cualquier tamaño, por eso sirve aunque haya miles de incidentes.
"""

from decimal import Decimal, ROUND_HALF_UP

from .grafo import dijkstra_con_corte
from .lectura import clave_de_lote, normalizar_numero


TIPOS = ("hurto", "accidente", "incendio")


class Modelo:
    """Guarda todo lo precalculado de una instancia para consultarlo rápido."""

    def __init__(self, instancia, presupuesto=None, pesos=None):
        """Precalcula costos, coberturas y máscaras de todas las estaciones posibles."""
        self.instancia = instancia
        self.parametros = instancia.parametros
        if presupuesto is None:
            presupuesto = instancia.parametros["presupuesto_millones"]
        self.presupuesto = presupuesto
        self.pesos = {}
        for tipo, datos in instancia.parametros["tipos"].items():
            self.pesos[tipo] = datos["peso"]
        if pesos:
            self.pesos.update(pesos)
        self.tipos = self._tipos_en_orden()
        self._lote_por_codigo = {}
        for lote in instancia.lotes:
            self._lote_por_codigo[lote.codigo] = lote
        self._preparar_incidentes()
        self._preparar_estaciones()

    def _tipos_en_orden(self):
        """Ordena los tipos como pide el enunciado: hurto, accidente, incendio y luego otros."""
        tipos = []
        for tipo in TIPOS:
            if tipo in self.pesos:
                tipos.append(tipo)
        for tipo in self.pesos:
            if tipo not in tipos:
                tipos.append(tipo)
        return tipos

    def _preparar_incidentes(self):
        """Asigna a cada incidente su número de bit y arma una máscara por tipo."""
        self._bit_del_incidente = {}
        self._incidentes_por_tipo = {}
        self._mascara_por_tipo = {}
        for tipo in self.tipos:
            self._incidentes_por_tipo[tipo] = []
            self._mascara_por_tipo[tipo] = 0
        posicion = 0
        for incidente in self.instancia.incidentes:
            self._bit_del_incidente[incidente.identificador] = posicion
            self._incidentes_por_tipo[incidente.tipo].append(incidente)
            self._mascara_por_tipo[incidente.tipo] |= 1 << posicion
            posicion += 1

    def _preparar_estaciones(self):
        """Calcula costo y cobertura de cada (lote, tipo) y la lista de opciones.

        Se corre UN solo Dijkstra por lote, cortado en el radio más grande,
        y esas distancias se reutilizan para los tres tipos de estación.
        """
        radios = {}
        for tipo in self.tipos:
            radios[tipo] = self._a_entero(self.parametros["tipos"][tipo]["radio_m"])
        mayor_radio = max(radios.values(), default=0)
        self._costos = {}
        self._coberturas = {}
        self._mascaras = {}
        self.opciones = []
        for lote in sorted(self.instancia.lotes, key=_codigo_del_lote):
            distancias = dijkstra_con_corte(self.instancia.grafo, lote.nodo, mayor_radio)
            for tipo in self.tipos:
                self._agregar_estacion(lote, tipo, distancias, radios[tipo])

    def _agregar_estacion(self, lote, tipo, distancias, radio):
        """Guarda costo, incidentes cubiertos y máscara de la estación (lote, tipo)."""
        clave = (lote.codigo, tipo)
        costo = self._calcular_costo(lote, tipo)
        cubiertos = []
        mascara = 0
        for incidente in self._incidentes_por_tipo[tipo]:
            if incidente.nodo in distancias and distancias[incidente.nodo] <= radio:
                cubiertos.append(incidente.identificador)
                mascara |= 1 << self._bit_del_incidente[incidente.identificador]
        cubiertos.sort()
        self._costos[clave] = costo
        self._coberturas[clave] = cubiertos
        self._mascaras[clave] = mascara
        opcion = {"lote": lote.codigo, "tipo": tipo, "costo": costo, "mascara": mascara}
        self.opciones.append(opcion)

    def _a_entero(self, valor):
        """Pasa un radio en metros a la misma escala entera de las aristas (sin floats)."""
        escala = self.instancia.escala_distancias
        decimal = Decimal(normalizar_numero(valor)) * escala
        if decimal != decimal.to_integral_value():
            raise ValueError(f"Radio no representable con escala {escala}: {valor}")
        return int(decimal)

    def _calcular_costo(self, lote, tipo):
        """Costo = costo_base * factor_zona, redondeado al millón (con Decimal, exacto)."""
        costo_base = Decimal(normalizar_numero(self.parametros["tipos"][tipo]["costo_base"]))
        factor = Decimal(normalizar_numero(lote.factor_zona))
        return int((costo_base * factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    def _validar_estacion(self, codigo_lote, tipo):
        """Lanza un error claro si el lote o el tipo no existen."""
        if codigo_lote not in self._lote_por_codigo:
            raise ValueError(f"Lote inexistente: {codigo_lote}")
        if tipo not in self.pesos:
            raise ValueError(f"Tipo inexistente: {tipo}")

    def costo(self, codigo_lote, tipo):
        """Costo en millones de construir la estación `tipo` en el lote."""
        self._validar_estacion(codigo_lote, tipo)
        return self._costos[(codigo_lote, tipo)]

    def cobertura(self, codigo_lote, tipo):
        """Lista ordenada de ids de incidentes que cubre la estación por sí sola."""
        self._validar_estacion(codigo_lote, tipo)
        return list(self._coberturas[(codigo_lote, tipo)])

    def cobertura_mask(self, codigo_lote, tipo):
        """Lo mismo que `cobertura`, pero como máscara de bits."""
        self._validar_estacion(codigo_lote, tipo)
        return self._mascaras[(codigo_lote, tipo)]

    def valor_mask(self, mascara):
        """Suma de pesos de los incidentes marcados en la máscara.

        Por cada tipo se cuentan los bits en 1 (`bit_count`) que son de ese
        tipo y se multiplican por su peso. Todo con enteros: resultado exacto.
        """
        valor = 0
        for tipo in self.tipos:
            cantidad = (mascara & self._mascara_por_tipo[tipo]).bit_count()
            valor += cantidad * self.pesos[tipo]
        return valor

    def evaluar(self, propuesta):
        """Valida una propuesta desde cero y devuelve su resumen.

        Es independiente de las heurísticas: recalcula todo con listas de ids,
        así sirve para comprobar que ninguna máscara tuvo un error.
        """
        lotes_usados = set()
        costo_total = 0
        cubiertos_por_tipo = {}
        for tipo in self.tipos:
            cubiertos_por_tipo[tipo] = set()
        for codigo_lote, tipo in propuesta:
            if codigo_lote in lotes_usados:
                raise ValueError(f"Lote repetido en propuesta: {codigo_lote}")
            lotes_usados.add(codigo_lote)
            costo_total += self.costo(codigo_lote, tipo)
            cubiertos_por_tipo[tipo].update(self.cobertura(codigo_lote, tipo))
        if costo_total > self.presupuesto:
            raise ValueError(f"Presupuesto excedido: {costo_total} > {self.presupuesto}")
        casos = {}
        valor = 0
        for tipo in self.tipos:
            casos[tipo] = len(cubiertos_por_tipo[tipo])
            valor += casos[tipo] * self.pesos[tipo]
        return {"estaciones": list(propuesta), "costo_total": costo_total,
                "casos_cubiertos": casos, "valor": valor}

    def todas_las_opciones(self):
        """Lista de pares (lote, tipo) en el orden del enunciado."""
        pares = []
        for opcion in self.opciones:
            pares.append((opcion["lote"], opcion["tipo"]))
        return pares


def _codigo_del_lote(lote):
    """Clave para ordenar lotes por su código (orden natural, ver clave_de_lote)."""
    return clave_de_lote(lote.codigo)
