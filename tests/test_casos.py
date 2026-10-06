"""Pruebas de las Partes 1 y 2 con los ejemplos del enunciado."""

import unittest

from estaciones.heuristicas import base, propia, propia_ls
from estaciones.lectura import cargar_instancia
from estaciones.modelo import Modelo


class Casos(unittest.TestCase):
    def setUp(self):
        self.pequena = Modelo(cargar_instancia("pequena"))

    def test_parte1(self):
        self.assertEqual(self.pequena.costo("L3", "accidente"), 2800)
        self.assertEqual(self.pequena.cobertura("L3", "accidente"), [1, 2, 4, 6])
        self.assertEqual(self.pequena.costo("L2", "hurto"), 1500)
        self.assertEqual(self.pequena.cobertura("L2", "hurto"), [9, 10, 11, 12, 13])

    def test_base_pequena(self):
        resultado = base(self.pequena)
        self.assertEqual(resultado["estaciones"], [("L1", "incendio")])
        self.assertEqual(resultado["costo_total"], 5500)
        self.assertEqual(resultado["casos_cubiertos"], {"hurto": 0, "accidente": 0, "incendio": 3})
        self.assertEqual(resultado["valor"], 15)

    def test_base_comuna(self):
        resultado = base(Modelo(cargar_instancia("comuna")))
        esperadas = [("L05", "accidente"), ("L06", "hurto"), ("L08", "accidente"),
                     ("L09", "incendio"), ("L13", "hurto"), ("L14", "hurto"),
                     ("L15", "accidente")]
        self.assertEqual(resultado["estaciones"], esperadas)
        self.assertEqual(resultado["costo_total"], 11950)
        self.assertEqual(resultado["casos_cubiertos"], {"hurto": 486, "accidente": 296, "incendio": 31})
        self.assertEqual(resultado["valor"], 1529)

    def test_propias_pequena_y_comuna(self):
        comuna = Modelo(cargar_instancia("comuna"))
        self.assertEqual(propia(self.pequena)["valor"], 19)
        self.assertEqual(propia(comuna)["valor"], 1492)
        self.assertEqual(propia_ls(self.pequena)["valor"], 20)
        self.assertGreaterEqual(propia_ls(comuna)["valor"], base(comuna)["valor"])

    def test_heuristicas_pasan_por_evaluar(self):
        """Lo que devuelve cada heurística coincide con una evaluación desde cero."""
        for heuristica in (base, propia, propia_ls):
            resultado = heuristica(self.pequena)
            revisado = self.pequena.evaluar(resultado["estaciones"])
            self.assertEqual(resultado, revisado)

    def test_evaluar_rechaza(self):
        with self.assertRaises(ValueError):
            self.pequena.evaluar([("L1", "incendio"), ("L2", "incendio")])
        with self.assertRaises(ValueError):
            self.pequena.evaluar([("L1", "hurto"), ("L1", "accidente")])


if __name__ == "__main__":
    unittest.main()
