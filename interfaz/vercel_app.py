"""Adaptador WSGI para desplegar la API en Vercel.

La interfaz local sigue usando ``interfaz.servidor`` y su servidor HTTP.
Este módulo reutiliza el mismo núcleo de validación, cálculo y serialización,
pero expone una aplicación por petición, sin abrir puertos ni usar
``serve_forever``.
"""

import json
import traceback
from urllib.parse import urlparse

from .servidor import (
    POLITICA_DE_CONTENIDO,
    ErrorDePeticion,
    Almacen,
    esta_certificado,
    exportar_html,
    instancias_disponibles,
    leer_configuracion,
    nombre_de_archivo_seguro,
    respuesta_de_propuesta,
    resumen_de_instancia,
    validar_metodo,
)
from estaciones.ejecucion import METODOS, ejecutar_metodo


_METODOS_CON_CUERPO = {"POST"}
_LIMITE_CUERPO = 64 * 1024
_ALMACEN = Almacen()
_RAZONES = {
    200: "OK",
    400: "Bad Request",
    404: "Not Found",
    411: "Length Required",
    413: "Payload Too Large",
    415: "Unsupported Media Type",
    500: "Internal Server Error",
}


def _respuesta(status, cuerpo, tipo, cabeceras=None):
    """Construye una respuesta WSGI con cabeceras de seguridad comunes."""
    cuerpo_bytes = cuerpo if isinstance(cuerpo, bytes) else cuerpo.encode("utf-8")
    cabeceras_finales = [
        ("Content-Type", tipo),
        ("Content-Length", str(len(cuerpo_bytes))),
        ("Cache-Control", "no-store"),
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", "DENY"),
        ("Referrer-Policy", "strict-origin-when-cross-origin"),
        ("Content-Security-Policy", POLITICA_DE_CONTENIDO),
    ]
    if cabeceras:
        cabeceras_finales.extend(cabeceras)
    return status, cabeceras_finales, cuerpo_bytes


def _json(status, datos):
    """Construye una respuesta JSON UTF-8."""
    cuerpo = json.dumps(datos, ensure_ascii=False)
    return _respuesta(status, cuerpo, "application/json; charset=utf-8")


def _error(error):
    return _json(error.codigo, {"error": error.mensaje})


def _leer_json(environ):
    """Lee y valida el cuerpo JSON de una petición POST."""
    tipo = environ.get("CONTENT_TYPE", "")
    if not tipo.lower().startswith("application/json"):
        raise ErrorDePeticion(415, "El cuerpo debe enviarse como application/json.")
    texto_largo = environ.get("CONTENT_LENGTH")
    if texto_largo is None or not texto_largo.isdigit():
        raise ErrorDePeticion(411, "Falta el tamaño del cuerpo (Content-Length).")
    largo = int(texto_largo)
    if largo > _LIMITE_CUERPO:
        raise ErrorDePeticion(413, "El cuerpo es demasiado grande (máximo 64 KB).")
    crudo = environ["wsgi.input"].read(largo)
    try:
        return json.loads(crudo.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ErrorDePeticion(400, "El cuerpo no es un JSON válido.")


def _nombre_de_instancia(cuerpo):
    """Rechaza rutas locales: Vercel solo puede usar instancias publicadas."""
    if not isinstance(cuerpo, dict):
        raise ErrorDePeticion(400, "El cuerpo debe ser un objeto JSON.")
    nombre = cuerpo.get("instancia")
    disponibles = instancias_disponibles()
    if not isinstance(nombre, str) or nombre not in disponibles:
        raise ErrorDePeticion(
            404,
            "La instancia debe ser una de las publicadas: " + ", ".join(disponibles) + ".",
        )
    return nombre


def _configuracion_publica(cuerpo):
    """Valida la configuración usando exclusivamente una carpeta incluida en el despliegue."""
    nombre = _nombre_de_instancia(cuerpo)
    cuerpo_publico = dict(cuerpo)
    cuerpo_publico["instancia"] = nombre
    return leer_configuracion(cuerpo_publico, _ALMACEN)


def _metodo_en_vivo(configuracion, metodo):
    """Conserva el límite elegido por el usuario para cualquier instancia."""
    return metodo, configuracion["limite"]


def _api_instancia(cuerpo):
    nombre = _nombre_de_instancia(cuerpo)
    # La ruta se obtiene mediante la misma validación central del servidor local.
    configuracion = _configuracion_publica({
        "instancia": nombre,
        "presupuesto": None,
        "pesos": None,
        "limite_segundos": None,
    })
    modelo = configuracion["modelo"]
    return _json(200, resumen_de_instancia(nombre, modelo, configuracion["fechas"]))


def _resolver(cuerpo):
    metodo = validar_metodo(cuerpo.get("metodo") if isinstance(cuerpo, dict) else None)
    configuracion = _configuracion_publica(cuerpo)
    metodo, limite = _metodo_en_vivo(configuracion, metodo)
    configuracion["limite"] = limite
    resultado, segundos = ejecutar_metodo(configuracion["modelo"], metodo, limite)
    _ALMACEN.guardar_resultado((configuracion["clave"], metodo, limite), resultado)
    return _json(200, respuesta_de_propuesta(configuracion, metodo, resultado, segundos))


def _comparar(cuerpo):
    configuracion = _configuracion_publica(cuerpo)
    filas = []
    for metodo in METODOS:
        metodo_real, limite = _metodo_en_vivo(configuracion, metodo)
        resultado, segundos = ejecutar_metodo(configuracion["modelo"], metodo_real, limite)
        filas.append({
            "metodo": metodo_real,
            "valor": resultado["valor"],
            "costo_total": resultado["costo_total"],
            "cantidad_estaciones": len(resultado["estaciones"]),
            "tiempo_s": segundos,
            "optimo_certificado": esta_certificado(metodo_real, resultado),
        })
    return _json(200, {
        "instancia": configuracion["nombre"],
        "limite_segundos": configuracion["limite"],
        "filas": filas,
    })


def _exportar(cuerpo):
    metodo = validar_metodo(cuerpo.get("metodo") if isinstance(cuerpo, dict) else None)
    configuracion = _configuracion_publica(cuerpo)
    metodo, limite = _metodo_en_vivo(configuracion, metodo)
    configuracion["limite"] = limite
    tema = "claro" if cuerpo.get("tema") == "claro" else "oscuro"
    clave = (configuracion["clave"], metodo, limite)
    resultado = _ALMACEN.ultimo_resultado(clave)
    if resultado is None:
        resultado, _segundos = ejecutar_metodo(configuracion["modelo"], metodo, limite)
        _ALMACEN.guardar_resultado(clave, resultado)
    certificado = esta_certificado(metodo, resultado)
    detalle = metodo
    if certificado is True:
        detalle = "exacto · óptimo certificado"
    elif certificado is False:
        detalle = "exacto · mejor encontrada (no certificada)"
    documento = exportar_html(
        configuracion["modelo"],
        resultado,
        configuracion["fechas"],
        titulo=f"Estaciones · {configuracion['nombre']}",
        detalle=detalle,
        tema=tema,
    )
    nombre = nombre_de_archivo_seguro(configuracion["nombre"])
    return _respuesta(
        200,
        documento,
        "text/html; charset=utf-8",
        [("Content-Disposition", f'attachment; filename="mapa_{nombre}_{metodo}.html"')],
    )


def _atender(environ):
    metodo = environ.get("REQUEST_METHOD", "GET").upper()
    ruta = urlparse(environ.get("PATH_INFO", "/")).path
    if metodo == "GET" and ruta == "/api/instancias":
        return _json(200, {"instancias": instancias_disponibles()})
    if metodo not in _METODOS_CON_CUERPO:
        raise ErrorDePeticion(404, "Ruta de la API desconocida.")
    cuerpo = _leer_json(environ)
    acciones = {
        "/api/instancia": _api_instancia,
        "/api/resolver": _resolver,
        "/api/comparar": _comparar,
        "/api/exportar": _exportar,
    }
    if ruta not in acciones:
        raise ErrorDePeticion(404, "Ruta de la API desconocida.")
    return acciones[ruta](cuerpo)


def app(environ, start_response):
    """Aplicación WSGI compatible con el runtime Python de Vercel."""
    try:
        resultado = _atender(environ)
    except ErrorDePeticion as error:
        resultado = _error(error)
    except Exception:
        traceback.print_exc()
        resultado = _json(500, {"error": "Error interno del servidor al procesar el pedido."})
    status, cabeceras, cuerpo = resultado
    start_response(f"{status} {_RAZONES.get(status, 'Error')}", cabeceras)
    if environ.get("REQUEST_METHOD", "GET").upper() == "HEAD":
        return [b""]
    return [cuerpo]
