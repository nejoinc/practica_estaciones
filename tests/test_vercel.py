"""Pruebas del adaptador WSGI usado por Vercel."""

import io
import json
import unittest

from interfaz.vercel_app import app


def pedir(metodo, ruta, cuerpo=None):
    """Ejecuta una petición WSGI en memoria y devuelve estado, cabeceras y bytes."""
    crudo = b"" if cuerpo is None else json.dumps(cuerpo).encode("utf-8")
    entorno = {
        "REQUEST_METHOD": metodo,
        "PATH_INFO": ruta,
        "CONTENT_TYPE": "application/json" if cuerpo is not None else "",
        "CONTENT_LENGTH": str(len(crudo)),
        "wsgi.input": io.BytesIO(crudo),
    }
    respuesta = {}

    def iniciar_respuesta(estado, cabeceras):
        respuesta["estado"] = estado
        respuesta["cabeceras"] = dict(cabeceras)

    contenido = b"".join(app(entorno, iniciar_respuesta))
    return respuesta["estado"], respuesta["cabeceras"], contenido


class AdaptadorVercel(unittest.TestCase):
    def test_lista_instancias(self):
        estado, cabeceras, contenido = pedir("GET", "/api/instancias")
        self.assertEqual(estado, "200 OK")
        self.assertEqual(cabeceras["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(json.loads(contenido)["instancias"][:3], ["pequena", "comuna", "ciudad"])

    def test_resuelve_con_el_mismo_contrato(self):
        estado, _cabeceras, contenido = pedir(
            "POST",
            "/api/resolver",
            {"instancia": "pequena", "metodo": "exacto", "limite_segundos": 5},
        )
        datos = json.loads(contenido)
        self.assertEqual(estado, "200 OK")
        self.assertEqual(datos["valor"], 20)
        self.assertTrue(datos["optimo_certificado"])

    def test_no_expone_rutas_locales(self):
        estado, _cabeceras, contenido = pedir(
            "POST",
            "/api/instancia",
            {"instancia": "/home/usuario/instancia"},
        )
        self.assertEqual(estado, "404 Not Found")
        self.assertIn("publicadas", json.loads(contenido)["error"])

    def test_exporta_html(self):
        estado, cabeceras, contenido = pedir(
            "POST",
            "/api/exportar",
            {"instancia": "pequena", "metodo": "exacto", "limite_segundos": 5},
        )
        self.assertEqual(estado, "200 OK")
        self.assertEqual(cabeceras["Content-Type"], "text/html; charset=utf-8")
        self.assertIn("attachment", cabeceras["Content-Disposition"])
        self.assertIn(b"datos-del-mapa", contenido)

    def test_ruta_desconocida_es_json(self):
        estado, cabeceras, contenido = pedir("POST", "/api/no-existe", {})
        self.assertEqual(estado, "404 Not Found")
        self.assertEqual(cabeceras["Content-Type"], "application/json; charset=utf-8")
        self.assertIn("Ruta de la API desconocida", json.loads(contenido)["error"])


if __name__ == "__main__":
    unittest.main()
