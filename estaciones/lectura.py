"""Lectura y validación de instancias (los cinco archivos de una carpeta)."""

import csv
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path


@dataclass(frozen=True)
class Lote:
    codigo: str
    nodo: int
    factor_zona: str


@dataclass(frozen=True)
class Incidente:
    identificador: int
    nodo: int
    tipo: str


@dataclass
class Instancia:
    nodos: dict
    grafo: dict
    lotes: list
    incidentes: list
    parametros: dict
    escala_distancias: int = 1


def _leer_filas(ruta, columnas):
    """Lee un CSV como lista de diccionarios y exige que tenga ciertas columnas."""
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo de instancia: {ruta}")
    with ruta.open(newline="", encoding="utf-8-sig") as archivo:
        lector = csv.DictReader(archivo)
        encabezados = lector.fieldnames or []
        for columna in columnas:
            if columna not in encabezados:
                raise ValueError(f"{ruta.name}: falta la columna {columna}")
        return list(lector)


def _leer_parametros(ruta):
    """Lee parametros.json y revisa que tenga lo necesario para cada tipo."""
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo de instancia: {ruta}")
    with ruta.open(encoding="utf-8-sig") as archivo:
        parametros = json.load(archivo)
    for clave in ("presupuesto_millones", "tipos"):
        if clave not in parametros:
            raise ValueError(f"parametros.json: falta {clave}")
    for tipo, datos in parametros["tipos"].items():
        for clave in ("costo_base", "radio_m", "peso"):
            if clave not in datos:
                raise ValueError(f"parametros.json: falta tipos.{tipo}.{clave}")
    return parametros


def normalizar_numero(texto):
    """Texto de un número listo para Decimal o float: sin espacios y con punto decimal.

    Acepta coma decimal ("367,9" -> "367.9") porque una hoja de cálculo en
    español guarda así los CSV. No acepta separador de miles ("1.234,5").
    """
    return str(texto).strip().replace(",", ".")


def _cantidad_de_decimales(texto):
    """Cuántos decimales tiene un número escrito como texto (p. ej. '49.9' -> 1)."""
    try:
        numero = Decimal(normalizar_numero(texto))
    except InvalidOperation:
        raise ValueError(f"Distancia no numérica: {texto!r}")
    if not numero.is_finite():
        raise ValueError(f"Distancia no numérica: {texto!r}")
    exponente = numero.as_tuple().exponent
    if exponente >= 0:
        return 0
    return -exponente


def _escala_de_distancias(filas_aristas, parametros):
    """Elige una escala (1, 10, 100...) que vuelva enteras TODAS las distancias.

    Por qué: en float, 49.9 + 68.4 (dos aristas reales de comuna) da
    118.30000000000001, y una comparación justo en el borde del radio
    fallaría. En décimas de metro (499 + 684 = 1183) la suma es exacta.
    """
    mayor = 0
    for fila in filas_aristas:
        mayor = max(mayor, _cantidad_de_decimales(fila["longitud_m"]))
    for datos in parametros["tipos"].values():
        mayor = max(mayor, _cantidad_de_decimales(datos["radio_m"]))
    return 10 ** mayor


def _a_entero(texto, escala):
    """Convierte una distancia en texto a entero multiplicando por la escala."""
    numero = Decimal(normalizar_numero(texto)) * escala
    if numero != numero.to_integral_value():
        raise ValueError(f"Distancia no representable con escala {escala}: {texto}")
    return int(numero)


def _texto_de_lineas(lineas):
    """Escribe [2, 5, 7] como '2, 5 y 7' para los mensajes de error."""
    textos = []
    for linea in lineas:
        textos.append(str(linea))
    if len(textos) == 1:
        return textos[0]
    return ", ".join(textos[:-1]) + " y " + textos[-1]


def _revisar_repetidos(nombre_archivo, descripcion, valores):
    """Lanza ValueError si algún valor aparece más de una vez en la columna.

    `valores` viene en el orden de las filas. La fila 0 de datos es la
    línea 2 del archivo, porque la línea 1 es el encabezado.
    """
    lineas_por_valor = {}
    for posicion in range(len(valores)):
        valor = valores[posicion]
        if valor not in lineas_por_valor:
            lineas_por_valor[valor] = []
        lineas_por_valor[valor].append(posicion + 2)
    for valor, lineas in lineas_por_valor.items():
        if len(lineas) > 1:
            raise ValueError(
                f"{nombre_archivo}: {descripcion} {valor!r} aparece {len(lineas)} veces "
                f"(líneas {_texto_de_lineas(lineas)}); cada uno debe ser único")


def _leer_nodos(carpeta):
    """Devuelve {id_nodo: (lat, lon)}; rechaza ids de nodo repetidos."""
    filas = _leer_filas(carpeta / "nodos.csv", ["id", "lat", "lon"])
    identificadores = []
    for fila in filas:
        identificadores.append(int(fila["id"]))
    _revisar_repetidos("nodos.csv", "el id de nodo", identificadores)
    nodos = {}
    for fila in filas:
        latitud = float(normalizar_numero(fila["lat"]))
        longitud = float(normalizar_numero(fila["lon"]))
        nodos[int(fila["id"])] = (latitud, longitud)
    return nodos


def _armar_grafo(nodos, filas_aristas, escala):
    """Lista de adyacencia dirigida: {origen: [(destino, longitud_entera), ...]}."""
    grafo = {}
    for nodo in nodos:
        grafo[nodo] = []
    for fila in filas_aristas:
        origen = int(fila["origen"])
        destino = int(fila["destino"])
        if origen not in nodos or destino not in nodos:
            raise ValueError(f"Arista con nodo inexistente: {origen}->{destino}")
        longitud = _a_entero(fila["longitud_m"], escala)
        if longitud < 0:
            raise ValueError(f"Longitud negativa en arista {origen}->{destino}")
        grafo[origen].append((destino, longitud))
    return grafo


def _leer_lotes(carpeta, nodos):
    """Lee lotes.csv: códigos únicos y cada lote en un nodo existente."""
    lotes = []
    for fila in _leer_filas(carpeta / "lotes.csv", ["lote", "nodo", "factor_zona"]):
        lote = Lote(fila["lote"], int(fila["nodo"]), normalizar_numero(fila["factor_zona"]))
        if lote.nodo not in nodos:
            raise ValueError(f"lotes.csv: el lote {lote.codigo!r} usa el nodo {lote.nodo}, "
                             f"que no existe en nodos.csv")
        lotes.append(lote)
    codigos = []
    for lote in lotes:
        codigos.append(lote.codigo)
    _revisar_repetidos("lotes.csv", "el código de lote", codigos)
    return lotes


def _leer_incidentes(carpeta, nodos, parametros):
    """Lee incidentes.csv: ids únicos, nodo existente y tipo con parámetros."""
    incidentes = []
    for fila in _leer_filas(carpeta / "incidentes.csv", ["id", "nodo", "tipo"]):
        # "Hurto " o "HURTO" se leen como "hurto": el tipo escrito a mano
        # en una hoja de cálculo suele traer mayúsculas o espacios de más.
        tipo = fila["tipo"].strip().lower()
        incidente = Incidente(int(fila["id"]), int(fila["nodo"]), tipo)
        if incidente.nodo not in nodos:
            raise ValueError(f"incidentes.csv: el incidente {incidente.identificador} usa el "
                             f"nodo {incidente.nodo}, que no existe en nodos.csv")
        if incidente.tipo not in parametros["tipos"]:
            raise ValueError(f"Tipo de incidente sin parámetros: {incidente.tipo}")
        incidentes.append(incidente)
    identificadores = []
    for incidente in incidentes:
        identificadores.append(incidente.identificador)
    _revisar_repetidos("incidentes.csv", "el id de incidente", identificadores)
    return incidentes


def clave_de_lote(codigo):
    """Clave para ordenar códigos de lote en ORDEN NATURAL: L2 antes que L10.

    Decisión: un código "letras + número" (L7, L10, L01) se ordena por sus
    letras y luego por el número como entero. Con códigos con ceros
    (L01..L15) da el mismo orden que el texto. Si el código no sigue ese
    patrón (p. ej. 'A-3' o '12'), se ordena por su texto (respaldo estable).
    Para volver al orden por texto basta con agregar `return codigo` como
    primera línea de esta función.
    """
    letras = codigo.rstrip("0123456789")
    digitos = codigo[len(letras):]
    if digitos == "" or not letras.isalpha():
        # -1 deja estos códigos antes que los numerados con las mismas letras.
        return (codigo, -1, codigo)
    # El tercer elemento desempata 'L1' contra 'L01' (mismo número).
    return (letras, int(digitos), codigo)


def ordenar_por_lote(propuesta):
    """Copia de una propuesta [(lote, tipo), ...] ordenada por código de lote."""
    return sorted(propuesta, key=_clave_de_estacion)


def _clave_de_estacion(estacion):
    """Clave de una estación (lote, tipo): la de su código de lote."""
    return clave_de_lote(estacion[0])


def carpeta_de_instancia(nombre_o_ruta):
    """Ruta existente tal cual; si no, `instancias/<nombre>` del proyecto.

    Se busca junto al proyecto (la carpeta que contiene `estaciones`) y no
    en el directorio actual, así un nombre corto funciona desde cualquier lugar.
    La usan `cargar_instancia` y quien necesite otros archivos de la misma
    carpeta (p. ej. las fechas de incidentes para el mapa).
    """
    carpeta = Path(nombre_o_ruta)
    if carpeta.exists():
        return carpeta
    raiz_del_proyecto = Path(__file__).resolve().parent.parent
    return raiz_del_proyecto / "instancias" / str(nombre_o_ruta)


def cargar_instancia(nombre_o_ruta):
    """Carga una instancia por nombre ('pequena') o por ruta de carpeta."""
    carpeta = carpeta_de_instancia(nombre_o_ruta)
    if not carpeta.is_dir():
        raise FileNotFoundError(f"No existe la instancia: {nombre_o_ruta}")
    nodos = _leer_nodos(carpeta)
    filas_aristas = _leer_filas(carpeta / "aristas.csv", ["origen", "destino", "longitud_m"])
    parametros = _leer_parametros(carpeta / "parametros.json")
    escala = _escala_de_distancias(filas_aristas, parametros)
    grafo = _armar_grafo(nodos, filas_aristas, escala)
    lotes = _leer_lotes(carpeta, nodos)
    incidentes = _leer_incidentes(carpeta, nodos, parametros)
    return Instancia(nodos, grafo, lotes, incidentes, parametros, escala)
