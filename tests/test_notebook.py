"""Pruebas del notebook practica_estaciones.ipynb (solo biblioteca estándar, sin Jupyter).

Criterio de velocidad: se EJECUTAN solo las celdas rápidas (las de los casos
del enunciado, la configuración y las que definen parte1, parte2, parte3 y
el mapa), que tardan unos segundos. Las celdas que corren propia_ls en ciudad
(entre 20 y 35 s) no se ejecutan aquí: de ellas se revisan sus salidas
guardadas (sin errores, sin rutas absolutas, contador correlativo).
"""

import contextlib
import hashlib
import io
import json
import os
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent
NOTEBOOK = RAIZ / "practica_estaciones.ipynb"

# SHA-256 de la fuente de cada celda del enunciado, calculado del archivo
# original. Si alguien edita una celda del enunciado, esta prueba falla.
HUELLAS_DEL_ENUNCIADO = {
    "c00": "21cece3a74e9b9aaf0c20f64e0871e5d1fcc491c682d3ef121ea7eff327f4eef",
    "c01": "40dc3d9cd4499dd7d49d67614eb16967f505ff1180cdb8dc3c4cd51951c934b4",
    "c02": "8c33d44f7b570c029d741bb6e98b100b34ef1dc5649705983d1e9276bc42dba0",
    "c03": "91b2fe7dea67db9e4183e24ad379827bf1e420c74a3efac2eea70eafc23f2efd",
    "c04": "2764d3c770ca9bd3e43147dba8bdf88a32f48a087689c4d7758fce0155a813e3",
    "c05": "3f35310500ce914b1a651a13d6055e169f4afd43ca641b6ffbfe7c46775fc322",
    "c06": "1b56c7dae8c52bae91e1e2e7d05b24c174dc7b7603268841f73fd19c1656780d",
    "c07": "d112f12d285c3888617aad03443d87a6af124372f7d52f33d0a69f428c12193e",
    "c08": "636b50e5c5e8588fcf2ca97ca8f78d4c32d9e879db233998d711ea5812d4a6fe",
    "c09": "5d9c57fcff12ee8664fe4171403b56ca583a3c4dc3283f16c37376a373d5d310",
}

# Celdas que se ejecutan, en el orden en que aparecen en el notebook.
CELDAS_RAPIDAS = ("c04", "sol-config", "sol-parte1", "c06", "sol-parte2",
                  "c08", "sol-parte3", "sol-parte4")


def leer_notebook():
    """El notebook como diccionario (falla si no es JSON válido)."""
    return json.loads(NOTEBOOK.read_text(encoding="utf-8"))


def fuente(celda):
    """Texto completo de una celda."""
    return "".join(celda["source"])


class EstructuraDelNotebook(unittest.TestCase):
    def setUp(self):
        self.notebook = leer_notebook()
        self.celdas = self.notebook["cells"]

    def test_es_nbformat_4(self):
        self.assertEqual(self.notebook["nbformat"], 4)

    def test_celdas_del_enunciado_intactas_y_en_orden(self):
        encontradas = []
        for celda in self.celdas:
            if celda["id"] in HUELLAS_DEL_ENUNCIADO:
                encontradas.append(celda["id"])
                huella = hashlib.sha256(fuente(celda).encode("utf-8")).hexdigest()
                self.assertEqual(huella, HUELLAS_DEL_ENUNCIADO[celda["id"]], celda["id"])
        self.assertEqual(encontradas, sorted(HUELLAS_DEL_ENUNCIADO))

    def test_salidas_sin_errores_ni_rutas_absolutas(self):
        contador_esperado = 1
        for celda in self.celdas:
            if celda["cell_type"] != "code" or celda["id"] in HUELLAS_DEL_ENUNCIADO:
                continue
            self.assertEqual(celda["execution_count"], contador_esperado, celda["id"])
            contador_esperado += 1
            for salida in celda["outputs"]:
                self.assertNotEqual(salida["output_type"], "error", celda["id"])
                texto = "".join(salida.get("text", []))
                self.assertNotIn(":\\", texto, celda["id"])
                self.assertNotIn("Users", texto, celda["id"])


class EjecucionDeLasCeldasRapidas(unittest.TestCase):
    def test_asserts_contra_los_casos_del_enunciado(self):
        celdas_por_id = {}
        for celda in leer_notebook()["cells"]:
            celdas_por_id[celda["id"]] = celda
        espacio = {"__name__": "__main__"}
        salida = io.StringIO()
        directorio_anterior = os.getcwd()
        os.chdir(RAIZ)
        try:
            with contextlib.redirect_stdout(salida):
                for identificador in CELDAS_RAPIDAS:
                    codigo = compile(fuente(celdas_por_id[identificador]), identificador, "exec")
                    exec(codigo, espacio)
        finally:
            os.chdir(directorio_anterior)
        texto = salida.getvalue()
        self.assertIn("OK: los 2 casos de ejemplo de la Parte 1 coinciden", texto)
        self.assertIn("OK: los 2 casos de ejemplo de la Parte 2 coinciden", texto)
        self.assertIn("OK: el caso de ejemplo de la Parte 3 coincide", texto)
        resultado = espacio["parte2"]({"instancia": "pequena", "heuristica": "propia"})
        self.assertEqual(sorted(resultado), ["casos_cubiertos", "costo_total", "estaciones", "valor"])


if __name__ == "__main__":
    unittest.main()
