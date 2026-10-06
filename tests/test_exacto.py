"""Pruebas de la Parte 3 (exacto) y de las instancias donde fallan las heurísticas.

Se ejecutan desde la carpeta del proyecto: py -m unittest discover -s tests
"""

import csv
import json
import random
import tempfile
import unittest
from pathlib import Path

from estaciones.exacto import resolver
from estaciones.heuristicas import base, propia, propia_ls
from estaciones.lectura import cargar_instancia
from estaciones.modelo import Modelo


def fuerza_bruta(modelo):
    """Mejor valor probando TODAS las propuestas (solo para instancias chicas).

    Es independiente del B&B: no poda nada y mide cada propuesta con
    Modelo.evaluar, que trabaja con listas de ids y no con máscaras.
    """
    codigos = []
    for lote in modelo.instancia.lotes:
        codigos.append(lote.codigo)
    return _probar_todo(modelo, codigos, 0, [])


def _probar_todo(modelo, codigos, indice, propuesta):
    """Recorre recursivamente: en cada lote, no construir o construir cada tipo."""
    if indice == len(codigos):
        costo_total = 0
        for codigo_lote, tipo in propuesta:
            costo_total += modelo.costo(codigo_lote, tipo)
        if costo_total > modelo.presupuesto:
            return 0
        return modelo.evaluar(propuesta)["valor"]
    mejor = _probar_todo(modelo, codigos, indice + 1, propuesta)
    for tipo in modelo.tipos:
        con_estacion = propuesta + [(codigos[indice], tipo)]
        mejor = max(mejor, _probar_todo(modelo, codigos, indice + 1, con_estacion))
    return mejor


def escribir_instancia_aleatoria(carpeta, generador):
    """Escribe en `carpeta` una instancia chica al azar con los 5 archivos."""
    cantidad_nodos = 4 + generador.randrange(4)
    _escribir_csv(carpeta / "nodos.csv", ["id", "lat", "lon"],
                  _filas_de_nodos(cantidad_nodos))
    _escribir_csv(carpeta / "aristas.csv", ["origen", "destino", "longitud_m"],
                  _filas_de_aristas(cantidad_nodos, generador))
    filas_lotes = []
    for nodo in range(cantidad_nodos):
        filas_lotes.append([f"L{nodo}", nodo, "1"])
    _escribir_csv(carpeta / "lotes.csv", ["lote", "nodo", "factor_zona"], filas_lotes)
    tipos = ["hurto", "accidente", "incendio"]
    filas_incidentes = []
    for identificador in range(cantidad_nodos * 2):
        nodo = generador.randrange(cantidad_nodos)
        filas_incidentes.append([identificador, nodo, tipos[identificador % 3]])
    _escribir_csv(carpeta / "incidentes.csv", ["id", "nodo", "tipo"], filas_incidentes)
    parametros = {
        "presupuesto_millones": generador.randrange(3000, 9001),
        "tipos": {
            "hurto": {"costo_base": 1000, "radio_m": 2, "peso": 1},
            "accidente": {"costo_base": 2000, "radio_m": 3, "peso": 2},
            "incendio": {"costo_base": 3000, "radio_m": 4, "peso": 3},
        },
    }
    (carpeta / "parametros.json").write_text(json.dumps(parametros), encoding="utf-8")


def _filas_de_nodos(cantidad_nodos):
    """Nodos en línea recta (las coordenadas no afectan el cálculo)."""
    filas = []
    for nodo in range(cantidad_nodos):
        filas.append([nodo, 0, nodo])
    return filas


def _filas_de_aristas(cantidad_nodos, generador):
    """Un camino de ida y vuelta (asegura conexión) más algunas aristas al azar."""
    filas = []
    for nodo in range(cantidad_nodos - 1):
        filas.append([nodo, nodo + 1, 1])
        filas.append([nodo + 1, nodo, 1])
    for _ in range(cantidad_nodos):
        origen = generador.randrange(cantidad_nodos)
        destino = generador.randrange(cantidad_nodos)
        if origen != destino:
            filas.append([origen, destino, generador.randrange(1, 5)])
    return filas


def _escribir_csv(ruta, encabezado, filas):
    """Escribe un CSV con encabezado."""
    with ruta.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(encabezado)
        for fila in filas:
            escritor.writerow(fila)


class Exacto(unittest.TestCase):
    def test_pequena_optimo(self):
        modelo = Modelo(cargar_instancia("pequena"))
        resultado = resolver(modelo)
        self.assertEqual(resultado["valor"], 20)
        self.assertEqual(resultado["valor"], fuerza_bruta(modelo))
        self.assertEqual(resultado["estaciones"],
                         [("L1", "hurto"), ("L3", "accidente"), ("L4", "hurto")])
        self.assertEqual(resultado["costo_total"], 5400)

    def test_comuna_optimo(self):
        modelo = Modelo(cargar_instancia("comuna"))
        resultado = resolver(modelo)
        self.assertEqual(resultado["valor"], 1574)
        revisado = modelo.evaluar(resultado["estaciones"])
        self.assertEqual(revisado["valor"], 1574)
        for heuristica in (base, propia, propia_ls):
            self.assertGreaterEqual(resultado["valor"], heuristica(modelo)["valor"])

    def test_instancias_malas(self):
        """Cada heurística queda por debajo del óptimo en su instancia mala.

        Las tres usan los costos, radios y pesos oficiales del enunciado.
        Valores esperados: (heurística, óptimo), explicados en cada README.
        """
        casos = {
            "base": (base, 11, 13),
            "propia": (propia, 6, 8),
            "propia_ls": (propia_ls, 12, 13),
        }
        for nombre, (heuristica, valor_heuristica, valor_optimo) in casos.items():
            modelo = Modelo(cargar_instancia(f"instancias_malas/{nombre}"))
            self.assertLessEqual(len(modelo.instancia.nodos), 6, nombre)
            optimo = fuerza_bruta(modelo)
            self.assertEqual(optimo, valor_optimo, nombre)
            self.assertEqual(resolver(modelo)["valor"], optimo, nombre)
            self.assertEqual(heuristica(modelo)["valor"], valor_heuristica, nombre)

    def test_treinta_instancias_aleatorias(self):
        generador = random.Random(20261005)
        for numero in range(30):
            with tempfile.TemporaryDirectory() as temporal:
                carpeta = Path(temporal)
                escribir_instancia_aleatoria(carpeta, generador)
                modelo = Modelo(cargar_instancia(carpeta))
                optimo = fuerza_bruta(modelo)
                self.assertEqual(resolver(modelo)["valor"], optimo, f"instancia {numero}")
                self.assertLessEqual(propia_ls(modelo)["valor"], optimo, f"instancia {numero}")


if __name__ == "__main__":
    unittest.main()
