"""Pruebas de la Parte 4: datos del mapa, mapa HTML exportado y subcomando parte4.

Todo con la biblioteca estándar (no hace falta instalar nada).
"""

import contextlib
import io
import json
import re
import tempfile
import unittest
from pathlib import Path

from main import main
from estaciones.exacto import resolver
from estaciones.lectura import cargar_instancia
from estaciones.mapa import (clasificar_incidentes, contar_por_tipo, datos_del_mapa, exportar_html,
                             fila_de_totales, filas_de_estaciones, json_para_html, leer_fechas,
                             lotes_libres, tabla_csv)
from estaciones.modelo import Modelo
from test_exacto import _escribir_csv


RAIZ = Path(__file__).resolve().parent.parent
TEXTO_HOSTIL = "</script><script>alert(1)</script>"


def datos_incrustados(documento):
    """Lee el JSON que exportar_html pone dentro de <script id="datos-del-mapa">."""
    coincidencia = re.search(r'<script type="application/json" id="datos-del-mapa">(.*?)</script>',
                             documento, re.S)
    return json.loads(coincidencia.group(1))


def escribir_instancia_hostil(carpeta):
    """Instancia mínima válida con textos que intentan inyectar HTML."""
    _escribir_csv(carpeta / "nodos.csv", ["id", "lat", "lon"], [[0, 6.25, -75.57], [1, 6.26, -75.56]])
    _escribir_csv(carpeta / "aristas.csv", ["origen", "destino", "longitud_m"], [[0, 1, 10], [1, 0, 10]])
    _escribir_csv(carpeta / "lotes.csv", ["lote", "nodo", "factor_zona"], [[TEXTO_HOSTIL, 0, "1"]])
    _escribir_csv(carpeta / "incidentes.csv", ["id", "nodo", "tipo", "fecha_hora"],
                  [[1, 0, "hurto", "<img src=x onerror=alert(2)>"], [2, 1, "hurto", "2025-01-01 10:00"]])
    parametros = {
        "presupuesto_millones": 1000,
        "tipos": {"hurto": {"estacion": "<b>CAI</b>", "costo_base": 1000, "radio_m": 5, "peso": 1}},
    }
    (carpeta / "parametros.json").write_text(json.dumps(parametros), encoding="utf-8")


class DatosDelMapa(unittest.TestCase):
    def setUp(self):
        self.modelo = Modelo(cargar_instancia("pequena"))
        self.resultado = resolver(self.modelo)

    def test_cubiertos_mas_no_cubiertos_es_el_total(self):
        cubiertos, no_cubiertos = clasificar_incidentes(self.modelo, self.resultado["estaciones"])
        self.assertEqual(len(cubiertos) + len(no_cubiertos), len(self.modelo.instancia.incidentes))

    def test_conteo_de_cubiertos_coincide_con_evaluar(self):
        cubiertos, _ = clasificar_incidentes(self.modelo, self.resultado["estaciones"])
        self.assertEqual(contar_por_tipo(self.modelo, cubiertos), self.resultado["casos_cubiertos"])

    def test_totales_coinciden_con_evaluar(self):
        evaluado = self.modelo.evaluar(self.resultado["estaciones"])
        totales = fila_de_totales(self.modelo, self.resultado)
        self.assertEqual(totales["costo_total"], evaluado["costo_total"])
        self.assertEqual(totales["casos_por_tipo"], evaluado["casos_cubiertos"])
        self.assertEqual(totales["valor"], evaluado["valor"])
        suma = 0
        for fila in filas_de_estaciones(self.modelo, self.resultado):
            suma += fila["costo"]
        self.assertEqual(suma, evaluado["costo_total"])

    def test_filas_en_orden_natural_y_lotes_libres(self):
        filas = filas_de_estaciones(self.modelo, self.resultado)
        self.assertEqual([fila["lote"] for fila in filas], ["L1", "L3", "L4"])
        libres = [lote.codigo for lote in lotes_libres(self.modelo, self.resultado["estaciones"])]
        self.assertEqual(libres, ["L2", "L5"])

    def test_csv_y_fechas(self):
        texto = tabla_csv(self.modelo, self.resultado)
        self.assertIn("L3,accidente", texto)
        self.assertIn("valor,20", texto)
        fechas = leer_fechas(RAIZ / "instancias" / "pequena")
        self.assertEqual(fechas[1], "2025-01-07 08:00")


class DatosParaElNavegador(unittest.TestCase):
    def test_pequena_con_propuesta(self):
        modelo = Modelo(cargar_instancia("pequena"))
        resultado = resolver(modelo)
        datos = datos_del_mapa(modelo, resultado, leer_fechas(RAIZ / "instancias" / "pequena"))
        self.assertTrue(datos["hay_propuesta"])
        self.assertEqual(datos["cubiertos"] + datos["no_cubiertos"], len(modelo.instancia.incidentes))
        cubiertos, _ = clasificar_incidentes(modelo, resultado["estaciones"])
        self.assertEqual(datos["cubiertos"], len(cubiertos))
        con_estacion = [lote["codigo"] for lote in datos["lotes"] if lote["estacion"]]
        self.assertEqual(con_estacion, ["L1", "L3", "L4"])
        self.assertEqual([tipo["forma"] for tipo in datos["tipos"]], ["cuadrado", "triangulo", "circulo"])
        primero = datos["incidentes"][0]
        self.assertEqual(primero[0], 1)
        self.assertEqual(primero[5], "2025-01-07 08:00")

    def test_sin_propuesta_nada_cubierto(self):
        modelo = Modelo(cargar_instancia("pequena"))
        datos = datos_del_mapa(modelo)
        self.assertFalse(datos["hay_propuesta"])
        self.assertEqual(datos["cubiertos"], 0)
        for lote in datos["lotes"]:
            self.assertIsNone(lote["estacion"])

    def test_comuna_cuenta_igual_que_evaluar(self):
        modelo = Modelo(cargar_instancia("comuna"))
        resultado = resolver(modelo)
        datos = datos_del_mapa(modelo, resultado)
        self.assertEqual(datos["cubiertos"], sum(resultado["casos_cubiertos"].values()))


class MapaExportado(unittest.TestCase):
    def test_comuna_exacto_autocontenido(self):
        modelo = Modelo(cargar_instancia("comuna"))
        resultado = resolver(modelo)
        documento = exportar_html(modelo, resultado, titulo="Estaciones · comuna", detalle="exacto")
        self.assertTrue(documento.startswith("<!doctype html>"))
        self.assertIn("Leaflet 1.9.4", documento)
        self.assertIn("MapaEstaciones.iniciarExportado()", documento)
        self.assertIn("font/ttf;base64,", documento)
        self.assertNotIn('src="http', documento)
        self.assertNotIn("folium", documento.lower())
        datos = datos_incrustados(documento)
        self.assertEqual(datos["resumen"]["valor"], 1574)
        self.assertEqual(datos["cubiertos"], 850)
        self.assertEqual(datos["no_cubiertos"], 63)
        self.assertEqual(len([lote for lote in datos["lotes"] if lote["estacion"]]), 7)

    def test_escapa_textos_hostiles(self):
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal)
            escribir_instancia_hostil(carpeta)
            modelo = Modelo(cargar_instancia(carpeta))
            resultado = resolver(modelo)
            documento = exportar_html(modelo, resultado, leer_fechas(carpeta),
                                      titulo="<script>alert(3)</script>")
        self.assertNotIn("<script>alert", documento)
        self.assertNotIn("<img src=x", documento)
        self.assertNotIn("<b>CAI</b>", documento)
        self.assertIn("&lt;script&gt;alert(3)", documento)
        datos = datos_incrustados(documento)
        self.assertEqual(datos["lotes"][0]["codigo"], TEXTO_HOSTIL)
        self.assertEqual(datos["incidentes"][0][5], "<img src=x onerror=alert(2)>")

    def test_json_para_html_conserva_el_significado(self):
        datos = {"texto": "</script>&<b>\u2028"}
        self.assertEqual(json.loads(json_para_html(datos)), datos)
        self.assertNotIn("<", json_para_html(datos))

    def test_json_para_html_separadores_de_linea(self):
        """Regresión: los separadores U+2028/U+2029 se escapan sin corromper el JSON.

        Antes el patrón de reemplazo quedó vacío (replace("", ...)) y metía
        texto entre cada carácter: el JSON dejaba de decodificar.
        """
        datos = {"nombre": "Lote\u2028norte\u2029</script>&fin", "numeros": [1, 2, 3]}
        texto = json_para_html(datos)
        self.assertEqual(json.loads(texto), datos)
        self.assertNotIn("<", texto)
        self.assertNotIn("\u2028", texto)
        self.assertNotIn("\u2029", texto)
        self.assertLess(len(texto), 3 * len(json.dumps(datos)))


class SubcomandoParte4(unittest.TestCase):
    def test_escribe_tabla_y_mapa(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "mapa.html"
            salida = io.StringIO()
            with contextlib.redirect_stdout(salida):
                main(["parte4", "pequena", "--salida", str(ruta)])
            documento = ruta.read_text(encoding="utf-8")
        texto = salida.getvalue()
        self.assertIn("metodo=exacto", texto)
        self.assertIn("óptimo certificado", texto)
        self.assertIn("valor=20", texto)
        self.assertEqual(datos_incrustados(documento)["resumen"]["valor"], 20)

    def test_limite_cero_no_certifica(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "mapa.html"
            salida = io.StringIO()
            with contextlib.redirect_stdout(salida):
                main(["parte4", "comuna", "--salida", str(ruta), "--limite", "0"])
        self.assertIn("no certificada", salida.getvalue())

    def test_instancia_inexistente_mensaje_claro(self):
        with self.assertRaises(SystemExit) as error:
            main(["parte4", "no_existe_esta_instancia"])
        self.assertIn("Error al leer la instancia", str(error.exception))


if __name__ == "__main__":
    unittest.main()
