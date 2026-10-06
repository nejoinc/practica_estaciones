"""Pruebas del servidor de la interfaz (interfaz/servidor.py) con pedidos HTTP reales.

Se levanta el servidor en un puerto libre de 127.0.0.1 dentro de un hilo y se
le habla con http.client (biblioteca estándar), como lo haría el navegador.
"""

import http.client
import json
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

from estaciones.exacto import resolver
from estaciones.lectura import cargar_instancia
from estaciones.modelo import Modelo
from interfaz.servidor import crear_servidor
from test_robustez import LOTES, INCIDENTES, NODOS, escribir_instancia


RAIZ = Path(__file__).resolve().parent.parent


class ServidorDePrueba(unittest.TestCase):
    """Un servidor para toda la clase (se apaga al terminar)."""

    @classmethod
    def setUpClass(cls):
        cls.servidor = crear_servidor(0, silencioso=True)
        cls.puerto = cls.servidor.server_address[1]
        cls.hilo = threading.Thread(target=cls.servidor.serve_forever, daemon=True)
        cls.hilo.start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()

    def pedir(self, metodo, ruta, cuerpo=None, cabeceras=None, crudo=None):
        """Hace un pedido y devuelve (código, cabeceras, cuerpo en bytes)."""
        conexion = http.client.HTTPConnection("127.0.0.1", self.puerto, timeout=120)
        todas = {}
        datos = crudo
        if cuerpo is not None:
            datos = json.dumps(cuerpo).encode("utf-8")
            todas["Content-Type"] = "application/json"
        if cabeceras:
            todas.update(cabeceras)
        conexion.request(metodo, ruta, body=datos, headers=todas)
        respuesta = conexion.getresponse()
        contenido = respuesta.read()
        conexion.close()
        return respuesta.status, dict(respuesta.getheaders()), contenido

    def pedir_json(self, ruta, cuerpo):
        """POST con JSON; devuelve (código, objeto JSON)."""
        codigo, _cabeceras, contenido = self.pedir("POST", ruta, cuerpo)
        return codigo, json.loads(contenido.decode("utf-8"))

    def resolver(self, instancia, metodo, **extra):
        """Atajo para /api/resolver."""
        cuerpo = {"instancia": instancia, "metodo": metodo, "limite_segundos": 60}
        cuerpo.update(extra)
        return self.pedir_json("/api/resolver", cuerpo)


class Api(ServidorDePrueba):
    def test_es_multihilo_y_solo_local(self):
        self.assertIsInstance(self.servidor, ThreadingHTTPServer)
        self.assertEqual(self.servidor.server_address[0], "127.0.0.1")

    def test_lista_de_instancias(self):
        codigo, _cabeceras, contenido = self.pedir("GET", "/api/instancias")
        self.assertEqual(codigo, 200)
        self.assertEqual(json.loads(contenido)["instancias"][:3], ["pequena", "comuna", "ciudad"])

    def test_datos_de_la_instancia(self):
        codigo, datos = self.pedir_json("/api/instancia", {"instancia": "pequena"})
        self.assertEqual(codigo, 200)
        self.assertEqual(datos["presupuesto"], 6000)
        self.assertEqual([tipo["peso"] for tipo in datos["tipos"]], [1, 3, 5])
        self.assertFalse(datos["mapa"]["hay_propuesta"])

    def test_valores_de_pequena_por_metodo(self):
        esperados = {"base": 15, "propia": 19, "propia_ls": 20, "exacto": 20}
        for metodo, valor in esperados.items():
            codigo, datos = self.resolver("pequena", metodo)
            self.assertEqual(codigo, 200, metodo)
            self.assertEqual(datos["valor"], valor, metodo)
        self.assertTrue(datos["optimo_certificado"])

    def test_valores_de_comuna(self):
        _codigo, base = self.resolver("comuna", "base")
        _codigo, mejorada = self.resolver("comuna", "propia_ls")
        _codigo, exacto = self.resolver("comuna", "exacto")
        self.assertEqual(base["valor"], 1529)
        self.assertIsNone(base["optimo_certificado"])
        self.assertEqual(mejorada["valor"], 1574)
        self.assertEqual(exacto["valor"], 1574)
        self.assertTrue(exacto["optimo_certificado"])

    def test_respuesta_coherente_con_el_modelo(self):
        _codigo, datos = self.resolver("comuna", "exacto")
        modelo = Modelo(cargar_instancia("comuna"))
        propuesta = []
        for fila in datos["filas"]:
            propuesta.append((fila["lote"], fila["tipo"]))
        evaluado = modelo.evaluar(propuesta)
        self.assertEqual(datos["casos_cubiertos"], evaluado["casos_cubiertos"])
        self.assertEqual(datos["costo_total"], evaluado["costo_total"])
        self.assertEqual(datos["mapa"]["cubiertos"], sum(evaluado["casos_cubiertos"].values()))
        self.assertEqual(datos["mapa"]["cubiertos"] + datos["mapa"]["no_cubiertos"], 913)
        self.assertIn("valor,1574", datos["csv"])

    def test_presupuesto_y_pesos_cambian_la_propuesta(self):
        _codigo, sin_dinero = self.resolver("pequena", "exacto", presupuesto=0)
        self.assertEqual(sin_dinero["valor"], 0)
        self.assertEqual(sin_dinero["filas"], [])
        pesos = {"hurto": 1, "accidente": 1, "incendio": 1}
        _codigo, iguales = self.resolver("pequena", "exacto", pesos=pesos)
        esperado = resolver(Modelo(cargar_instancia("pequena"), pesos=pesos))
        self.assertEqual(iguales["valor"], esperado["valor"])
        self.assertEqual(iguales["pesos"], pesos)

    def test_comparar(self):
        codigo, datos = self.pedir_json("/api/comparar", {"instancia": "pequena", "limite_segundos": 30})
        self.assertEqual(codigo, 200)
        valores = [fila["valor"] for fila in datos["filas"]]
        self.assertEqual(valores, [15, 19, 20, 20])
        self.assertTrue(datos["filas"][3]["optimo_certificado"])

    def test_exportar_mapa(self):
        cuerpo = {"instancia": "pequena", "metodo": "exacto", "limite_segundos": 30}
        codigo, cabeceras, contenido = self.pedir("POST", "/api/exportar", cuerpo)
        self.assertEqual(codigo, 200)
        self.assertIn("attachment", cabeceras["Content-Disposition"])
        self.assertIn("mapa_pequena_exacto.html", cabeceras["Content-Disposition"])
        self.assertIn(b"datos-del-mapa", contenido)

    def test_ruta_absoluta_de_carpeta_nueva(self):
        ruta = str(RAIZ / "instancias" / "pequena")
        codigo, datos = self.pedir_json("/api/instancia", {"instancia": ruta})
        self.assertEqual(codigo, 200)
        self.assertEqual(datos["nombre"], "pequena")

    def test_calculo_largo_no_bloquea_otros_pedidos(self):
        resultado_largo = {}

        def calcular_ciudad():
            resultado_largo["respuesta"] = self.resolver("ciudad", "exacto", limite_segundos=4)

        hilo = threading.Thread(target=calcular_ciudad)
        hilo.start()
        time.sleep(1.0)
        inicio = time.perf_counter()
        codigo, _cabeceras, _contenido = self.pedir("GET", "/api/instancias")
        demora = time.perf_counter() - inicio
        hilo.join()
        self.assertEqual(codigo, 200)
        self.assertLess(demora, 1.0)
        codigo_largo, datos_largos = resultado_largo["respuesta"]
        self.assertEqual(codigo_largo, 200)
        self.assertFalse(datos_largos["optimo_certificado"])


class Validaciones(ServidorDePrueba):
    def assert_error(self, codigo_esperado, ruta, cuerpo, texto):
        """El pedido falla con ese código y un mensaje claro (sin traza de Python)."""
        codigo, datos = self.pedir_json(ruta, cuerpo)
        self.assertEqual(codigo, codigo_esperado, datos)
        self.assertIn(texto, datos["error"])
        self.assertNotIn("Traceback", datos["error"])

    def test_metodo_invalido(self):
        self.assert_error(400, "/api/resolver", {"instancia": "pequena", "metodo": "magia"}, "Método desconocido")

    def test_presupuesto_invalido(self):
        for presupuesto in (-1, "100", True, 1.5, 10**10):
            self.assert_error(400, "/api/resolver",
                              {"instancia": "pequena", "metodo": "base", "presupuesto": presupuesto},
                              "presupuesto")

    def test_pesos_invalidos(self):
        self.assert_error(400, "/api/resolver",
                          {"instancia": "pequena", "metodo": "base", "pesos": {"hurto": -1}}, "peso de hurto")
        self.assert_error(400, "/api/resolver",
                          {"instancia": "pequena", "metodo": "base", "pesos": {"robo": 1}}, "desconocido")
        self.assert_error(400, "/api/resolver",
                          {"instancia": "pequena", "metodo": "base", "pesos": [1, 2, 3]}, "pesos")

    def test_limite_fuera_de_rango(self):
        for limite in (-1, 601, "30"):
            self.assert_error(400, "/api/resolver",
                              {"instancia": "pequena", "metodo": "exacto", "limite_segundos": limite},
                              "límite")

    def test_json_invalido(self):
        codigo, _cabeceras, contenido = self.pedir("POST", "/api/resolver", crudo=b"{no es json",
                                                   cabeceras={"Content-Type": "application/json"})
        self.assertEqual(codigo, 400)
        self.assertIn("JSON", json.loads(contenido)["error"])

    def test_cuerpo_enorme(self):
        enorme = b"{" + b" " * (65 * 1024) + b"}"
        codigo, _cabeceras, contenido = self.pedir("POST", "/api/resolver", crudo=enorme,
                                                   cabeceras={"Content-Type": "application/json"})
        self.assertEqual(codigo, 413)
        self.assertIn("demasiado grande", json.loads(contenido)["error"])

    def test_tipo_de_contenido(self):
        codigo, _cabeceras, _contenido = self.pedir("POST", "/api/resolver", crudo=b"{}",
                                                    cabeceras={"Content-Type": "text/plain"})
        self.assertEqual(codigo, 415)

    def test_instancia_inexistente(self):
        self.assert_error(404, "/api/resolver", {"instancia": "no_existe", "metodo": "base"}, "No existe")

    def test_ruta_de_instancia_con_trucos(self):
        self.assert_error(400, "/api/instancia", {"instancia": "../instancias/pequena"}, "ruta completa")
        self.assert_error(400, "/api/instancia", {"instancia": "pequena/../comuna"}, "ruta completa")
        self.assert_error(404, "/api/instancia", {"instancia": str(RAIZ)}, "cinco archivos")
        self.assert_error(404, "/api/instancia", {"instancia": "C:\\Windows\\System32"}, "cinco archivos")
        self.assert_error(400, "/api/instancia", {"instancia": 123}, "instancia")

    def test_instancia_con_datos_malos(self):
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = Path(temporal)
            lotes = LOTES + [["L1", 1, "1"]]
            escribir_instancia(carpeta, NODOS, lotes, INCIDENTES)
            self.assert_error(400, "/api/instancia", {"instancia": str(carpeta)}, "lotes.csv")

    def test_estaticos_sin_salir_de_la_carpeta_web(self):
        for ruta in ("/../main.py", "/%2e%2e/main.py", "/vendor/../../servidor.py",
                     "/..%5cservidor.py", "/C:/Windows/win.ini", "/estado.py"):
            codigo, _cabeceras, _contenido = self.pedir("GET", ruta)
            self.assertEqual(codigo, 404, ruta)

    def test_cabeceras_de_seguridad(self):
        codigo, cabeceras, contenido = self.pedir("GET", "/")
        self.assertEqual(codigo, 200)
        self.assertIn(b"Estaciones", contenido)
        self.assertEqual(cabeceras["X-Content-Type-Options"], "nosniff")
        self.assertIn("default-src 'self'", cabeceras["Content-Security-Policy"])
        self.assertIn("https://tile.openstreetmap.org", cabeceras["Content-Security-Policy"])
        codigo, cabeceras, _contenido = self.pedir("GET", "/api/instancias")
        self.assertEqual(cabeceras["Cache-Control"], "no-store")

    def test_host_ajeno_rechazado(self):
        codigo, _cabeceras, _contenido = self.pedir("GET", "/api/instancias",
                                                    cabeceras={"Host": "malicioso.example:80"})
        self.assertEqual(codigo, 400)

    def test_ruta_de_api_desconocida(self):
        codigo, _cabeceras, _contenido = self.pedir("GET", "/api/secreto")
        self.assertEqual(codigo, 404)


if __name__ == "__main__":
    unittest.main()
