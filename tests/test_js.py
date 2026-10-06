"""Corre las pruebas de JavaScript (tests/js) con Node, si está instalado.

La lógica pura de la página (formato de cifras, lectura de la dirección,
preferencias) se prueba con `node --test`, que viene con Node: no hay que
instalar paquetes. Si Node no está, la prueba se salta y lo dice.
"""

import shutil
import subprocess
import unittest
from pathlib import Path


CARPETA_JS = Path(__file__).resolve().parent / "js"
NODE = shutil.which("node")


@unittest.skipIf(NODE is None, "Node no está instalado: no se pueden correr las pruebas de JavaScript")
class PruebasDeJavaScript(unittest.TestCase):
    def test_node_test(self):
        archivos = sorted(str(ruta) for ruta in CARPETA_JS.glob("*.test.js"))
        self.assertGreater(len(archivos), 0)
        proceso = subprocess.run([NODE, "--test", *archivos], capture_output=True, text=True,
                                 encoding="utf-8", timeout=120)
        self.assertEqual(proceso.returncode, 0, proceso.stdout + proceso.stderr)


if __name__ == "__main__":
    unittest.main()
