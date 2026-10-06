"""Pruebas de robustez: datos mal formados, orden de lotes, límite de tiempo y directorio.

Se ejecutan desde la carpeta del proyecto: py -m unittest discover -s tests
"""

import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from main import LOTES_MAXIMOS_PARA_EXACTO_EN_PARTE4, metodo_por_defecto_parte4
from estaciones.exacto import resolver
from estaciones.heuristicas import base, propia_ls
from estaciones.lectura import cargar_instancia, carpeta_de_instancia, clave_de_lote, ordenar_por_lote
from estaciones.mapa import leer_fechas
from estaciones.modelo import Modelo
from test_exacto import _escribir_csv


PARAMETROS = {
    "presupuesto_millones": 1000,
    "tipos": {
        "hurto": {"costo_base": 1000, "radio_m": 2, "peso": 1},
        "accidente": {"costo_base": 2000, "radio_m": 3, "peso": 2},
        "incendio": {"costo_base": 3000, "radio_m": 4, "peso": 3},
    },
}


def escribir_instancia(carpeta, filas_nodos, filas_lotes, filas_incidentes):
    """Escribe una instancia mínima: nodos 0 y 1 lejos entre sí, y los datos dados."""
    _escribir_csv(carpeta / "nodos.csv", ["id", "lat", "lon"], filas_nodos)
    _escribir_csv(carpeta / "aristas.csv", ["origen", "destino", "longitud_m"],
                  [[0, 1, 1000], [1, 0, 1000]])
    _escribir_csv(carpeta / "lotes.csv", ["lote", "nodo", "factor_zona"], filas_lotes)
    _escribir_csv(carpeta / "incidentes.csv", ["id", "nodo", "tipo"], filas_incidentes)
    (carpeta / "parametros.json").write_text(json.dumps(PARAMETROS), encoding="utf-8")


NODOS = [[0, 0, 0], [1, 0, 1]]
LOTES = [["L1", 0, "1"], ["L2", 1, "1"]]
INCIDENTES = [[1, 0, "hurto"], [2, 1, "hurto"]]


class Duplicados(unittest.TestCase):
    def cargar_con(self, nodos, lotes, incidentes):
        """Escribe la instancia en una carpeta temporal y la carga."""
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal)
            escribir_instancia(carpeta, nodos, lotes, incidentes)
            return cargar_instancia(carpeta)

    def test_codigo_de_lote_repetido(self):
        lotes = [["L1", 0, "1"], ["L2", 1, "1"], ["L1", 1, "1"]]
        with self.assertRaises(ValueError) as error:
            self.cargar_con(NODOS, lotes, INCIDENTES)
        self.assertIn("lotes.csv", str(error.exception))
        self.assertIn("'L1' aparece 2 veces (líneas 2 y 4)", str(error.exception))

    def test_id_de_incidente_repetido(self):
        incidentes = [[1, 0, "hurto"], [1, 1, "hurto"]]
        with self.assertRaises(ValueError) as error:
            self.cargar_con(NODOS, LOTES, incidentes)
        self.assertIn("incidentes.csv", str(error.exception))
        self.assertIn("1 aparece 2 veces", str(error.exception))

    def test_id_de_nodo_repetido(self):
        nodos = [[0, 0, 0], [1, 0, 1], [0, 5, 5]]
        with self.assertRaises(ValueError) as error:
            self.cargar_con(nodos, LOTES, INCIDENTES)
        self.assertIn("nodos.csv", str(error.exception))

    def test_lote_e_incidente_en_nodo_inexistente(self):
        with self.assertRaises(ValueError) as error:
            self.cargar_con(NODOS, [["L1", 9, "1"]], INCIDENTES)
        self.assertIn("lotes.csv", str(error.exception))
        with self.assertRaises(ValueError) as error:
            self.cargar_con(NODOS, LOTES, [[1, 9, "hurto"]])
        self.assertIn("incidentes.csv", str(error.exception))

    def test_instancia_correcta_carga(self):
        instancia = self.cargar_con(NODOS, LOTES, INCIDENTES)
        self.assertEqual(len(instancia.lotes), 2)


class DatosEscritosAMano(unittest.TestCase):
    """Coma decimal y tipos con mayúsculas o espacios, como los deja una hoja de cálculo."""

    def test_coma_decimal_en_distancias_factores_y_coordenadas(self):
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal)
            escribir_instancia(carpeta, [[0, "6,25", "-75,5"], [1, "6,26", "-75,6"]],
                               [["L1", 0, "1,5"]], [[1, 1, "hurto"]])
            _escribir_csv(carpeta / "aristas.csv", ["origen", "destino", "longitud_m"],
                          [[0, 1, "1,5"], [1, 0, "1,5"]])
            instancia = cargar_instancia(carpeta)
        modelo = Modelo(instancia, presupuesto=2000)
        self.assertEqual(instancia.nodos[0], (6.25, -75.5))
        self.assertEqual(modelo.costo("L1", "hurto"), 1500)
        # 1,5 m de distancia queda dentro del radio de 2 m del CAI.
        self.assertEqual(modelo.cobertura("L1", "hurto"), [1])

    def test_tipo_con_mayusculas_y_espacios(self):
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal)
            escribir_instancia(carpeta, NODOS, LOTES, [[1, 0, "Hurto "], [2, 1, " HURTO"]])
            instancia = cargar_instancia(carpeta)
        tipos = []
        for incidente in instancia.incidentes:
            tipos.append(incidente.tipo)
        self.assertEqual(tipos, ["hurto", "hurto"])
        self.assertEqual(Modelo(instancia).cobertura("L1", "hurto"), [1])


class MetodoPorDefectoDeParte4(unittest.TestCase):
    def test_decide_por_numero_de_lotes_y_no_por_nombre(self):
        cantidad_nodos = LOTES_MAXIMOS_PARA_EXACTO_EN_PARTE4 + 1
        nodos = []
        lotes = []
        for nodo in range(cantidad_nodos):
            nodos.append([nodo, 0, nodo])
            lotes.append([f"L{nodo}", nodo, "1"])
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal)
            escribir_instancia(carpeta, nodos, lotes, INCIDENTES)
            grande = Modelo(cargar_instancia(carpeta))
        self.assertEqual(metodo_por_defecto_parte4(grande), "propia_ls")
        self.assertEqual(metodo_por_defecto_parte4(Modelo(cargar_instancia("comuna"))), "exacto")
        self.assertEqual(metodo_por_defecto_parte4(Modelo(cargar_instancia("ciudad"))), "propia_ls")


class OrdenNatural(unittest.TestCase):
    def test_l2_antes_que_l10(self):
        self.assertLess(clave_de_lote("L2"), clave_de_lote("L10"))
        codigos = ["L10", "L2", "L1", "L01", "A-3", "L"]
        codigos.sort(key=clave_de_lote)
        self.assertEqual(codigos, ["A-3", "L", "L01", "L1", "L2", "L10"])
        propuesta = [("L10", "hurto"), ("L2", "incendio")]
        self.assertEqual(ordenar_por_lote(propuesta), [("L2", "incendio"), ("L10", "hurto")])

    def test_base_desempata_por_orden_natural(self):
        """L2 y L10 empatan (cubren lo mismo); como texto ganaría L10, natural gana L2."""
        lotes = []
        for numero in range(1, 13):
            nodo = 1
            if numero in (2, 10):
                nodo = 0
            lotes.append([f"L{numero}", nodo, "1"])
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal)
            escribir_instancia(carpeta, NODOS, lotes, [[1, 0, "hurto"]])
            modelo = Modelo(cargar_instancia(carpeta))
        self.assertEqual(base(modelo)["estaciones"], [("L2", "hurto")])


class LimiteDeTiempo(unittest.TestCase):
    def test_limite_casi_cero_no_certifica(self):
        modelo = Modelo(cargar_instancia("comuna"))
        resultado = resolver(modelo, limite_segundos=0.000001)
        self.assertFalse(resultado["optimo_certificado"])
        revisado = modelo.evaluar(resultado["estaciones"])
        self.assertEqual(revisado["valor"], resultado["valor"])
        self.assertGreaterEqual(resultado["valor"], resultado["estadisticas_bb"]["valor_arranque"])

    def test_sin_limite_certifica(self):
        resultado = resolver(Modelo(cargar_instancia("comuna")))
        self.assertTrue(resultado["optimo_certificado"])
        self.assertEqual(resultado["valor"], 1574)

    def test_limite_se_cumple_en_ciudad(self):
        """El límite cuenta también el arranque (propia_ls tarda ~20 s sin límite)."""
        modelo = Modelo(cargar_instancia("ciudad"))
        inicio = time.perf_counter()
        resultado = resolver(modelo, limite_segundos=5)
        segundos = time.perf_counter() - inicio
        self.assertLess(segundos, 8)
        self.assertFalse(resultado["optimo_certificado"])
        revisado = modelo.evaluar(resultado["estaciones"])
        self.assertEqual(revisado["valor"], resultado["valor"])

    def test_propia_ls_con_limite_es_factible(self):
        modelo = Modelo(cargar_instancia("comuna"))
        resultado = propia_ls(modelo, limite_segundos=0)
        self.assertEqual(modelo.evaluar(resultado["estaciones"]), resultado)
        self.assertEqual(propia_ls(modelo)["valor"], 1574)


class DirectorioActual(unittest.TestCase):
    def test_nombre_corto_desde_otro_directorio(self):
        directorio_original = os.getcwd()
        with tempfile.TemporaryDirectory() as temporal:
            try:
                os.chdir(temporal)
                instancia = cargar_instancia("pequena")
            finally:
                os.chdir(directorio_original)
        self.assertEqual(len(instancia.lotes), 5)

    def test_carpeta_de_instancia_desde_otro_directorio(self):
        """Un nombre corto apunta a instancias/<nombre> del proyecto, no al directorio actual."""
        directorio_original = os.getcwd()
        with tempfile.TemporaryDirectory() as temporal:
            try:
                os.chdir(temporal)
                carpeta = carpeta_de_instancia("pequena")
            finally:
                os.chdir(directorio_original)
        self.assertTrue((carpeta / "incidentes.csv").exists())
        self.assertEqual(leer_fechas(carpeta)[1], "2025-01-07 08:00")


if __name__ == "__main__":
    unittest.main()
