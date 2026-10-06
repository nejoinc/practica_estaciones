"""Servidor local de la interfaz (feria): páginas web + una API JSON pequeña.

Usa solo la biblioteca estándar (http.server). Escucha ÚNICAMENTE en
127.0.0.1, así nadie de la red puede usarlo. El navegador pide:

    GET  /                      la página (interfaz/web/index.html) y sus archivos
    GET  /api/instancias        carpetas de instancias/ con los cinco archivos
    POST /api/instancia         datos de una instancia (y su mapa sin propuesta)
    POST /api/resolver          propuesta de un método con presupuesto y pesos
    POST /api/comparar          valor y tiempo de los cuatro métodos
    POST /api/exportar          mapa HTML autocontenido para descargar

El servidor NO calcula nada por su cuenta: valida lo que llega, llama al
paquete `estaciones` (Modelo, heurísticas, exacto) y devuelve el resultado.
"""

import json
import math
import re
import sys
import threading
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from estaciones.ejecucion import METODOS, ejecutar_metodo, esta_certificado
from estaciones.lectura import cargar_instancia
from estaciones.mapa import (contar_por_tipo, datos_del_mapa, exportar_html, fila_de_totales,
                             filas_de_estaciones, leer_fechas, tabla_csv)
from estaciones.modelo import Modelo


RAIZ_DEL_PROYECTO = Path(__file__).resolve().parent.parent
CARPETA_WEB = RAIZ_DEL_PROYECTO / "interfaz" / "web"
CARPETA_INSTANCIAS = RAIZ_DEL_PROYECTO / "instancias"
ARCHIVOS_DE_INSTANCIA = ("nodos.csv", "aristas.csv", "lotes.csv", "incidentes.csv", "parametros.json")
ORDEN_PREFERIDO = ("pequena", "comuna", "ciudad")
DIRECCION = "127.0.0.1"
PUERTO_POR_DEFECTO = 8765

# Límites de lo que se acepta del navegador (el cliente no es confiable).
TAMANO_MAXIMO_DEL_CUERPO = 64 * 1024
PRESUPUESTO_MAXIMO = 10**9
PESO_MAXIMO = 10**6
LIMITE_MAXIMO_SEGUNDOS = 600
LIMITE_POR_DEFECTO_SEGUNDOS = 30
LARGO_MAXIMO_DE_RUTA = 500
MODELOS_EN_MEMORIA = 16
# Un nombre corto de instancia: letras, números, guion y guion bajo (sin / ni ..).
PATRON_DE_NOMBRE = re.compile(r"[A-Za-z0-9_-]{1,64}")

TIPOS_DE_CONTENIDO = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".ttf": "font/ttf",
    ".txt": "text/plain; charset=utf-8",
    ".svg": "image/svg+xml",
}

# Política de contenido: solo archivos propios; imágenes también de las
# teselas de OpenStreetMap. Sin scripts en línea ni de otros sitios.
POLITICA_DE_CONTENIDO = ("default-src 'self'; script-src 'self'; style-src 'self'; "
                         "img-src 'self' data: https://tile.openstreetmap.org; "
                         "font-src 'self'; connect-src 'self'; object-src 'none'; "
                         "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


class ErrorDePeticion(Exception):
    """Error que se le muestra al usuario: código HTTP + mensaje claro (sin trazas)."""

    def __init__(self, codigo, mensaje):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


# ---------------------------------------------------------------- instancias

def es_carpeta_de_instancia(carpeta):
    """True si la carpeta existe y tiene los cinco archivos de una instancia."""
    if not carpeta.is_dir():
        return False
    for nombre_archivo in ARCHIVOS_DE_INSTANCIA:
        if not (carpeta / nombre_archivo).is_file():
            return False
    return True


def instancias_disponibles():
    """Nombres de las carpetas válidas de instancias/: pequena, comuna, ciudad y luego el resto."""
    nombres = []
    if CARPETA_INSTANCIAS.is_dir():
        for carpeta in CARPETA_INSTANCIAS.iterdir():
            if es_carpeta_de_instancia(carpeta):
                nombres.append(carpeta.name)
    ordenados = []
    for nombre in ORDEN_PREFERIDO:
        if nombre in nombres:
            ordenados.append(nombre)
    resto = []
    for nombre in nombres:
        if nombre not in ordenados:
            resto.append(nombre)
    resto.sort()
    return ordenados + resto


def carpeta_pedida(texto):
    """Convierte lo que envió el navegador en una carpeta de instancia segura.

    - Un nombre corto (p. ej. 'comuna') solo puede ser una carpeta de instancias/.
    - Cualquier otra cosa se trata como ruta de una carpeta nueva: debe ser
      absoluta (así '../' no sirve para moverse desde el proyecto) y tener
      los cinco archivos. No se puede leer ningún otro archivo del equipo.
    """
    if not isinstance(texto, str) or texto.strip() == "":
        raise ErrorDePeticion(400, "Falta indicar la instancia.")
    texto = texto.strip()
    if len(texto) > LARGO_MAXIMO_DE_RUTA or "\x00" in texto:
        raise ErrorDePeticion(400, "La ruta de la instancia no es válida.")
    if PATRON_DE_NOMBRE.fullmatch(texto):
        carpeta = CARPETA_INSTANCIAS / texto
        if not es_carpeta_de_instancia(carpeta):
            raise ErrorDePeticion(404, f"No existe la instancia «{texto}» en la carpeta instancias.")
        return carpeta.resolve()
    ruta = Path(texto)
    if not ruta.is_absolute():
        raise ErrorDePeticion(400, "Escribe la ruta completa de la carpeta "
                                   "(por ejemplo C:\\datos\\sustentacion).")
    carpeta = ruta.resolve()
    if not es_carpeta_de_instancia(carpeta):
        raise ErrorDePeticion(404, "No se encontró una carpeta con los cinco archivos de una "
                                   "instancia (nodos.csv, aristas.csv, lotes.csv, incidentes.csv "
                                   "y parametros.json) en esa ruta.")
    return carpeta


def clave_de_configuracion(carpeta, presupuesto, pesos):
    """Clave para guardar un Modelo: carpeta + presupuesto + pesos (ordenados por tipo)."""
    pesos_ordenados = []
    for tipo in sorted(pesos):
        pesos_ordenados.append((tipo, pesos[tipo]))
    return (str(carpeta), presupuesto, tuple(pesos_ordenados))


class Almacen:
    """Instancias, Modelos y propuestas ya calculadas, guardados en memoria.

    Varios pedidos pueden llegar a la vez (el servidor usa un hilo por
    pedido); el candado evita que dos hilos modifiquen los diccionarios
    al mismo tiempo. Los cálculos largos (resolver) se hacen FUERA del
    candado para no bloquear a los demás.
    """

    def __init__(self):
        self.candado = threading.Lock()
        self.instancias = {}
        self.modelos = {}
        self.resultados = {}

    def instancia(self, carpeta):
        """(instancia, fechas) de la carpeta; se lee una sola vez."""
        clave = str(carpeta)
        with self.candado:
            if clave not in self.instancias:
                self.instancias[clave] = (_leer_instancia(carpeta), leer_fechas(carpeta))
            return self.instancias[clave]

    def modelo(self, carpeta, presupuesto, pesos):
        """Modelo de la carpeta con ese presupuesto y esos pesos (se reutiliza si ya existe)."""
        instancia, _fechas = self.instancia(carpeta)
        clave = clave_de_configuracion(carpeta, presupuesto, pesos)
        with self.candado:
            if clave not in self.modelos:
                if len(self.modelos) >= MODELOS_EN_MEMORIA:
                    self.modelos.clear()
                    self.resultados.clear()
                self.modelos[clave] = Modelo(instancia, presupuesto=presupuesto, pesos=pesos)
            return self.modelos[clave]

    def ultimo_resultado(self, clave):
        """Propuesta ya calculada para (configuración, método, límite), o None."""
        with self.candado:
            return self.resultados.get(clave)

    def guardar_resultado(self, clave, resultado):
        """Recuerda la propuesta: así el mapa exportado es el mismo que se ve en pantalla."""
        with self.candado:
            self.resultados[clave] = resultado


def _leer_instancia(carpeta):
    """cargar_instancia con los errores de datos convertidos en un mensaje para el usuario."""
    try:
        return cargar_instancia(carpeta)
    except (ValueError, KeyError, TypeError, FileNotFoundError) as error:
        raise ErrorDePeticion(400, f"No se pudo leer la instancia. {error}")


# ---------------------------------------------------------------- validación

def _es_entero(valor):
    """True si es un entero de JSON (en Python, True/False también son int: se excluyen)."""
    return isinstance(valor, int) and not isinstance(valor, bool)


def _es_numero(valor):
    """True si es un número finito de JSON (entero o decimal, no booleano)."""
    if isinstance(valor, bool):
        return False
    if isinstance(valor, int):
        return True
    return isinstance(valor, float) and math.isfinite(valor)


def validar_metodo(valor):
    """El método debe ser uno de la lista blanca."""
    if valor not in METODOS:
        raise ErrorDePeticion(400, "Método desconocido. Usa base, propia, propia_ls o exacto.")
    return valor


def validar_presupuesto(valor, por_defecto):
    """Entero entre 0 y PRESUPUESTO_MAXIMO; si no viene, el de parametros.json."""
    if valor is None:
        return por_defecto
    if not _es_entero(valor) or valor < 0 or valor > PRESUPUESTO_MAXIMO:
        raise ErrorDePeticion(400, "El presupuesto debe ser un número entero de millones "
                                   f"entre 0 y {PRESUPUESTO_MAXIMO}.")
    return valor


def validar_pesos(valor, tipos):
    """Diccionario {tipo: entero >= 0} solo con tipos de la instancia."""
    if valor is None:
        return {}
    if not isinstance(valor, dict):
        raise ErrorDePeticion(400, "Los pesos deben enviarse como {tipo: número}.")
    pesos = {}
    for tipo, peso in valor.items():
        if tipo not in tipos:
            raise ErrorDePeticion(400, f"Tipo de incidente desconocido en los pesos: {tipo}.")
        if not _es_entero(peso) or peso < 0 or peso > PESO_MAXIMO:
            raise ErrorDePeticion(400, f"El peso de {tipo} debe ser un entero entre 0 y {PESO_MAXIMO}.")
        pesos[tipo] = peso
    return pesos


def validar_limite(valor):
    """Segundos máximos del exacto: número entre 0 y LIMITE_MAXIMO_SEGUNDOS."""
    if valor is None:
        return LIMITE_POR_DEFECTO_SEGUNDOS
    if not _es_numero(valor) or valor < 0 or valor > LIMITE_MAXIMO_SEGUNDOS:
        raise ErrorDePeticion(400, "El límite de tiempo debe ser un número de segundos "
                                   f"entre 0 y {LIMITE_MAXIMO_SEGUNDOS}.")
    return float(valor)


def leer_configuracion(cuerpo, almacen):
    """Valida el cuerpo de /api/resolver, /api/comparar y /api/exportar.

    Devuelve un diccionario con la carpeta, el modelo y el límite ya validados.
    """
    if not isinstance(cuerpo, dict):
        raise ErrorDePeticion(400, "El cuerpo debe ser un objeto JSON.")
    carpeta = carpeta_pedida(cuerpo.get("instancia"))
    instancia, fechas = almacen.instancia(carpeta)
    presupuesto = validar_presupuesto(cuerpo.get("presupuesto"),
                                      instancia.parametros["presupuesto_millones"])
    pesos = validar_pesos(cuerpo.get("pesos"), instancia.parametros["tipos"])
    limite = validar_limite(cuerpo.get("limite_segundos"))
    modelo = almacen.modelo(carpeta, presupuesto, pesos)
    return {"carpeta": carpeta, "nombre": carpeta.name, "modelo": modelo,
            "fechas": fechas, "limite": limite,
            "clave": clave_de_configuracion(carpeta, presupuesto, pesos)}


def calcular(configuracion, metodo, almacen):
    """Corre el método (código del núcleo) y guarda la propuesta para exportarla después."""
    resultado, segundos = ejecutar_metodo(configuracion["modelo"], metodo, configuracion["limite"])
    almacen.guardar_resultado((configuracion["clave"], metodo, configuracion["limite"]), resultado)
    return resultado, segundos


# ---------------------------------------------------------------- respuestas

def resumen_de_instancia(nombre, modelo, fechas):
    """Datos para llenar los controles: presupuesto, pesos, tipos y totales por tipo."""
    totales = contar_por_tipo(modelo, modelo.instancia.incidentes)
    tipos = []
    for tipo in modelo.tipos:
        tipos.append({
            "tipo": tipo,
            "estacion": modelo.parametros["tipos"][tipo].get("estacion", tipo),
            "peso": modelo.pesos[tipo],
            "casos": totales[tipo],
        })
    return {
        "nombre": nombre,
        "lotes": len(modelo.instancia.lotes),
        "incidentes": len(modelo.instancia.incidentes),
        "presupuesto": modelo.presupuesto,
        "tipos": tipos,
        "mapa": datos_del_mapa(modelo, None, fechas),
    }


def respuesta_de_propuesta(configuracion, metodo, resultado, segundos):
    """Todo lo que muestra la interfaz de una propuesta: cifras, tabla, CSV y mapa."""
    modelo = configuracion["modelo"]
    return {
        "instancia": configuracion["nombre"],
        "metodo": metodo,
        "presupuesto": modelo.presupuesto,
        "pesos": dict(modelo.pesos),
        "limite_segundos": configuracion["limite"],
        "valor": resultado["valor"],
        "costo_total": resultado["costo_total"],
        "casos_cubiertos": dict(resultado["casos_cubiertos"]),
        "casos_totales": contar_por_tipo(modelo, modelo.instancia.incidentes),
        "cantidad_estaciones": len(resultado["estaciones"]),
        "tiempo_s": segundos,
        "optimo_certificado": esta_certificado(metodo, resultado),
        "filas": filas_de_estaciones(modelo, resultado),
        "totales": fila_de_totales(modelo, resultado),
        "csv": tabla_csv(modelo, resultado),
        "mapa": datos_del_mapa(modelo, resultado, configuracion["fechas"]),
    }


def comparar_metodos(configuracion):
    """Valor, costo y tiempo de los cuatro métodos con los mismos parámetros."""
    filas = []
    for metodo in METODOS:
        resultado, segundos = ejecutar_metodo(configuracion["modelo"], metodo, configuracion["limite"])
        filas.append({
            "metodo": metodo,
            "valor": resultado["valor"],
            "costo_total": resultado["costo_total"],
            "cantidad_estaciones": len(resultado["estaciones"]),
            "tiempo_s": segundos,
            "optimo_certificado": esta_certificado(metodo, resultado),
        })
    return {"instancia": configuracion["nombre"], "limite_segundos": configuracion["limite"],
            "filas": filas}


def nombre_de_archivo_seguro(texto):
    """Solo letras, números, guion y guion bajo (para Content-Disposition)."""
    if PATRON_DE_NOMBRE.fullmatch(texto):
        return texto
    return "instancia"


# ---------------------------------------------------------------- servidor HTTP

class Manejador(BaseHTTPRequestHandler):
    """Atiende cada pedido del navegador (un hilo por pedido)."""

    server_version = "Estaciones"
    sys_version = ""

    # ---- utilidades de respuesta

    def _cabeceras_comunes(self, tipo, largo, cache):
        """Cabeceras que llevan todas las respuestas (incluidas las de seguridad)."""
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(largo))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Content-Security-Policy", POLITICA_DE_CONTENIDO)

    def _enviar(self, codigo, contenido, tipo, cache="no-store", extra=None):
        """Envía una respuesta completa con su cuerpo en bytes."""
        self.send_response(codigo)
        self._cabeceras_comunes(tipo, len(contenido), cache)
        if extra:
            for nombre, valor in extra.items():
                self.send_header(nombre, valor)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(contenido)

    def _enviar_json(self, codigo, datos):
        """Envía un objeto como JSON (UTF-8)."""
        contenido = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self._enviar(codigo, contenido, "application/json; charset=utf-8")

    def _enviar_error(self, codigo, mensaje):
        """Error para el usuario: {"error": mensaje}."""
        self._enviar_json(codigo, {"error": mensaje})

    def log_message(self, formato, *argumentos):
        """Registro corto en la consola: método, ruta y código."""
        sys.stderr.write(f"[interfaz] {formato % argumentos}\n")

    # ---- entrada

    def _revisar_host(self):
        """Solo se aceptan pedidos dirigidos a 127.0.0.1 o localhost.

        Evita el "DNS rebinding": una página de internet que hace que su
        dominio apunte a 127.0.0.1 para hablar con este servidor.
        """
        host = self.headers.get("Host", "")
        nombre = host.rsplit(":", 1)[0]
        if nombre not in ("127.0.0.1", "localhost"):
            raise ErrorDePeticion(400, "Host no permitido.")

    def _leer_cuerpo_json(self):
        """Lee el cuerpo JSON respetando el tamaño máximo y el tipo de contenido."""
        tipo = self.headers.get("Content-Type", "")
        if not tipo.lower().startswith("application/json"):
            raise ErrorDePeticion(415, "El cuerpo debe enviarse como application/json.")
        largo_texto = self.headers.get("Content-Length")
        if largo_texto is None or not largo_texto.isdigit():
            raise ErrorDePeticion(411, "Falta el tamaño del cuerpo (Content-Length).")
        largo = int(largo_texto)
        if largo > TAMANO_MAXIMO_DEL_CUERPO:
            raise ErrorDePeticion(413, "El cuerpo es demasiado grande (máximo 64 KB).")
        crudo = self.rfile.read(largo)
        try:
            return json.loads(crudo.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ErrorDePeticion(400, "El cuerpo no es un JSON válido.")

    # ---- rutas

    def do_GET(self):
        """Archivos de la página y /api/instancias."""
        self._atender(self._responder_get)

    def do_HEAD(self):
        """Igual que GET pero sin cuerpo."""
        self._atender(self._responder_get)

    def do_POST(self):
        """Pedidos de la API que reciben JSON."""
        self._atender(self._responder_post)

    def _atender(self, responder):
        """Ejecuta la respuesta y convierte cualquier error en un mensaje claro."""
        try:
            self._revisar_host()
            responder()
        except ErrorDePeticion as error:
            if error.codigo == 413:
                # No se leyó el cuerpo: se cierra la conexión para no mezclarlo con otro pedido.
                self.close_connection = True
            self._enviar_error(error.codigo, error.mensaje)
        except Exception:
            # Para el desarrollador, la traza completa en la consola;
            # para el usuario, un mensaje sin detalles internos.
            traceback.print_exc()
            self._enviar_error(500, "Error interno del servidor al procesar el pedido.")

    def _responder_get(self):
        """GET: API de instancias o archivos estáticos."""
        ruta = urlparse(self.path).path
        if ruta == "/api/instancias":
            self._enviar_json(200, {"instancias": instancias_disponibles()})
            return
        if ruta.startswith("/api/"):
            raise ErrorDePeticion(404, "Ruta de la API desconocida.")
        self._enviar_estatico(ruta)

    def _responder_post(self):
        """POST: instancia, resolver, comparar y exportar."""
        ruta = urlparse(self.path).path
        acciones = {
            "/api/instancia": self._api_instancia,
            "/api/resolver": self._api_resolver,
            "/api/comparar": self._api_comparar,
            "/api/exportar": self._api_exportar,
        }
        if ruta not in acciones:
            raise ErrorDePeticion(404, "Ruta de la API desconocida.")
        cuerpo = self._leer_cuerpo_json()
        acciones[ruta](cuerpo)

    def _api_instancia(self, cuerpo):
        """Resumen de la instancia con sus valores por defecto y el mapa sin propuesta."""
        if not isinstance(cuerpo, dict):
            raise ErrorDePeticion(400, "El cuerpo debe ser un objeto JSON.")
        carpeta = carpeta_pedida(cuerpo.get("instancia"))
        instancia, fechas = self.server.almacen.instancia(carpeta)
        modelo = self.server.almacen.modelo(carpeta, instancia.parametros["presupuesto_millones"], {})
        self._enviar_json(200, resumen_de_instancia(carpeta.name, modelo, fechas))

    def _api_resolver(self, cuerpo):
        """Calcula la propuesta del método pedido."""
        metodo = validar_metodo(cuerpo.get("metodo") if isinstance(cuerpo, dict) else None)
        configuracion = leer_configuracion(cuerpo, self.server.almacen)
        resultado, segundos = calcular(configuracion, metodo, self.server.almacen)
        self._enviar_json(200, respuesta_de_propuesta(configuracion, metodo, resultado, segundos))

    def _api_comparar(self, cuerpo):
        """Corre los cuatro métodos y devuelve la tabla comparativa."""
        configuracion = leer_configuracion(cuerpo, self.server.almacen)
        self._enviar_json(200, comparar_metodos(configuracion))

    def _api_exportar(self, cuerpo):
        """Mapa HTML autocontenido de la propuesta, como archivo para descargar."""
        metodo = validar_metodo(cuerpo.get("metodo") if isinstance(cuerpo, dict) else None)
        configuracion = leer_configuracion(cuerpo, self.server.almacen)
        tema = "claro" if cuerpo.get("tema") == "claro" else "oscuro"
        modelo = configuracion["modelo"]
        clave = (configuracion["clave"], metodo, configuracion["limite"])
        resultado = self.server.almacen.ultimo_resultado(clave)
        if resultado is None:
            resultado, _segundos = calcular(configuracion, metodo, self.server.almacen)
        detalle = metodo
        certificado = esta_certificado(metodo, resultado)
        if certificado is True:
            detalle = "exacto · óptimo certificado"
        if certificado is False:
            detalle = "exacto · mejor encontrada (no certificada)"
        titulo = f"Estaciones · {configuracion['nombre']}"
        documento = exportar_html(modelo, resultado, configuracion["fechas"],
                                  titulo=titulo, detalle=detalle, tema=tema)
        nombre_archivo = f"mapa_{nombre_de_archivo_seguro(configuracion['nombre'])}_{metodo}.html"
        self._enviar(200, documento.encode("utf-8"), "text/html; charset=utf-8",
                     extra={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'})

    def _enviar_estatico(self, ruta):
        """Archivo de interfaz/web, sin permitir salir de esa carpeta."""
        relativa = unquote(ruta).lstrip("/")
        if relativa == "":
            relativa = "index.html"
        if "\\" in relativa or "\x00" in relativa or ":" in relativa:
            raise ErrorDePeticion(404, "Archivo no encontrado.")
        archivo = (CARPETA_WEB / relativa).resolve()
        if not archivo.is_relative_to(CARPETA_WEB) or not archivo.is_file():
            raise ErrorDePeticion(404, "Archivo no encontrado.")
        tipo = TIPOS_DE_CONTENIDO.get(archivo.suffix.lower())
        if tipo is None:
            raise ErrorDePeticion(404, "Archivo no encontrado.")
        self._enviar(200, archivo.read_bytes(), tipo, cache="no-cache")


class Servidor(ThreadingHTTPServer):
    """Servidor multihilo: un cálculo largo no bloquea a los demás pedidos."""

    daemon_threads = True

    def __init__(self, puerto, silencioso):
        super().__init__((DIRECCION, puerto), Manejador)
        self.almacen = Almacen()
        self.silencioso = silencioso


def crear_servidor(puerto=PUERTO_POR_DEFECTO, silencioso=False):
    """Crea el servidor en 127.0.0.1 (puerto 0 = uno libre cualquiera, útil en pruebas)."""
    try:
        return Servidor(puerto, silencioso)
    except OSError as error:
        raise SystemExit(f"No se pudo usar el puerto {puerto} ({error.strerror}). "
                         "Prueba con otro: py main.py interfaz --puerto 8766")


def iniciar(puerto=PUERTO_POR_DEFECTO, abrir_navegador=True):
    """Arranca el servidor y, si se pide, abre el navegador. Ctrl+C lo detiene."""
    servidor = crear_servidor(puerto)
    direccion = f"http://{DIRECCION}:{servidor.server_address[1]}/"
    print(f"Interfaz lista en {direccion}  (Ctrl+C para detener)")
    if abrir_navegador:
        threading.Timer(0.5, webbrowser.open, args=(direccion,)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("Servidor detenido.")
    finally:
        servidor.server_close()
