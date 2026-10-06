"""Parte 4: tablas, datos del mapa y mapa HTML autocontenido de una propuesta.

Este módulo SOLO presenta resultados. Toda cobertura, costo y valor sale del
Modelo (código propio). Leaflet (una librería de dibujo en el navegador)
únicamente pinta los puntos que este módulo le entrega ya calculados.

Hay dos grupos de funciones:
- Datos (puras, sin navegador): filas de la tabla, totales, incidentes
  cubiertos y no cubiertos, CSV, texto para consola y `datos_del_mapa`.
- Exportación: `exportar_html` arma UN archivo HTML que se abre con doble
  clic, con Leaflet, los estilos, el código de dibujo y los datos incluidos.
"""

import base64
import csv
import html
import io
import json
from pathlib import Path

from .lectura import clave_de_lote


# Forma de cada tipo de estación en el mapa. El color lo pone la hoja de
# estilos (interfaz/web/mapa.css). Forma + color: se distinguen también
# sin percibir el color (daltonismo).
FORMA_POR_TIPO = {
    "hurto": "cuadrado",
    "accidente": "triangulo",
    "incendio": "circulo",
}
FORMA_OTRO_TIPO = "rombo"

# Archivos web que se copian dentro del HTML exportado (mismo dibujo y
# mismo estilo que la interfaz). Las rutas son relativas a interfaz/web.
CARPETA_WEB = Path(__file__).resolve().parent.parent / "interfaz" / "web"
ESTILOS_DEL_EXPORTADO = ("vendor/leaflet/leaflet.css", "tokens.css", "mapa.css", "exportado.css")
SCRIPTS_DEL_EXPORTADO = ("vendor/leaflet/leaflet.js", "formato.js", "mapa.js")
FUENTES_DEL_EXPORTADO = (
    ("Familjen Grotesk", "vendor/fuentes/FamiljenGrotesk.ttf"),
    ("Fira Code", "vendor/fuentes/FiraCode.ttf"),
)


# ---------------------------------------------------------------- datos

def leer_fechas(carpeta):
    """Devuelve {id_incidente: fecha_hora} si incidentes.csv trae esa columna (opcional)."""
    ruta = Path(carpeta) / "incidentes.csv"
    fechas = {}
    if not ruta.exists():
        return fechas
    with ruta.open(newline="", encoding="utf-8-sig") as archivo:
        lector = csv.DictReader(archivo)
        if "fecha_hora" not in (lector.fieldnames or []):
            return fechas
        for fila in lector:
            fechas[int(fila["id"])] = fila["fecha_hora"]
    return fechas


def forma_de_tipo(tipo):
    """Forma con que se dibuja un tipo de estación (cuadrado, triángulo, círculo o rombo)."""
    return FORMA_POR_TIPO.get(tipo, FORMA_OTRO_TIPO)


def nombre_de_estacion(modelo, tipo):
    """Nombre legible de la estación (p. ej. 'CAI'); si falta, el tipo."""
    return modelo.parametros["tipos"][tipo].get("estacion", tipo)


def _clave_de_fila(fila):
    """Ordena filas por código de lote en orden natural."""
    return clave_de_lote(fila["lote"])


def filas_de_estaciones(modelo, resultado):
    """Una fila por estación construida: lote, tipo, estación, costo y casos que cubre."""
    filas = []
    for codigo_lote, tipo in resultado["estaciones"]:
        fila = {
            "lote": codigo_lote,
            "tipo": tipo,
            "estacion": nombre_de_estacion(modelo, tipo),
            "costo": modelo.costo(codigo_lote, tipo),
            "casos": len(modelo.cobertura(codigo_lote, tipo)),
        }
        filas.append(fila)
    filas.sort(key=_clave_de_fila)
    return filas


def fila_de_totales(modelo, resultado):
    """Totales de la propuesta tal como los entrega modelo.evaluar."""
    return {
        "costo_total": resultado["costo_total"],
        "presupuesto": modelo.presupuesto,
        "casos_por_tipo": dict(resultado["casos_cubiertos"]),
        "valor": resultado["valor"],
    }


def clasificar_incidentes(modelo, propuesta):
    """Separa los incidentes en (cubiertos, no_cubiertos) según la propuesta."""
    ids_cubiertos = set()
    for codigo_lote, tipo in propuesta:
        ids_cubiertos.update(modelo.cobertura(codigo_lote, tipo))
    cubiertos = []
    no_cubiertos = []
    for incidente in modelo.instancia.incidentes:
        if incidente.identificador in ids_cubiertos:
            cubiertos.append(incidente)
        else:
            no_cubiertos.append(incidente)
    return cubiertos, no_cubiertos


def contar_por_tipo(modelo, incidentes):
    """Cuántos incidentes hay de cada tipo en la lista."""
    conteo = {}
    for tipo in modelo.tipos:
        conteo[tipo] = 0
    for incidente in incidentes:
        conteo[incidente.tipo] += 1
    return conteo


def lotes_libres(modelo, propuesta):
    """Lotes donde la propuesta no construye nada, en orden natural."""
    usados = set()
    for codigo_lote, _tipo in propuesta:
        usados.add(codigo_lote)
    libres = []
    for lote in modelo.instancia.lotes:
        if lote.codigo not in usados:
            libres.append(lote)
    libres.sort(key=_clave_de_objeto_lote)
    return libres


def _clave_de_objeto_lote(lote):
    """Ordena objetos Lote por su código en orden natural."""
    return clave_de_lote(lote.codigo)


def tabla_csv(modelo, resultado):
    """Tabla de estaciones + fila de totales como texto CSV."""
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(["lote", "tipo", "estacion", "costo_millones", "casos_que_cubre"])
    for fila in filas_de_estaciones(modelo, resultado):
        escritor.writerow([fila["lote"], fila["tipo"], fila["estacion"], fila["costo"], fila["casos"]])
    totales = fila_de_totales(modelo, resultado)
    escritor.writerow([])
    escritor.writerow(["costo_total", totales["costo_total"], "presupuesto", totales["presupuesto"]])
    for tipo in modelo.tipos:
        escritor.writerow(["casos_cubiertos_" + tipo, totales["casos_por_tipo"][tipo]])
    escritor.writerow(["valor", totales["valor"]])
    return salida.getvalue()


def tabla_texto(modelo, resultado):
    """Tabla de estaciones alineada para imprimir en consola."""
    lineas = [f"{'lote':<8}{'tipo':<11}{'estación':<32}{'costo':>8}{'casos':>8}"]
    for fila in filas_de_estaciones(modelo, resultado):
        lineas.append(f"{fila['lote']:<8}{fila['tipo']:<11}{fila['estacion'][:31]:<32}"
                      f"{fila['costo']:>8}{fila['casos']:>8}")
    totales = fila_de_totales(modelo, resultado)
    lineas.append("-" * 67)
    lineas.append(f"costo_total={totales['costo_total']} de presupuesto={totales['presupuesto']}")
    lineas.append(f"casos_cubiertos={totales['casos_por_tipo']}")
    lineas.append(f"valor={totales['valor']}")
    return "\n".join(lineas)


def limites(modelo):
    """[[lat_min, lon_min], [lat_max, lon_max]] de lotes e incidentes."""
    nodos = modelo.instancia.nodos
    puntos = []
    for lote in modelo.instancia.lotes:
        puntos.append(nodos[lote.nodo])
    for incidente in modelo.instancia.incidentes:
        puntos.append(nodos[incidente.nodo])
    latitudes = []
    longitudes = []
    for latitud, longitud in puntos:
        latitudes.append(latitud)
        longitudes.append(longitud)
    return [[min(latitudes), min(longitudes)], [max(latitudes), max(longitudes)]]


def _tipos_para_el_mapa(modelo):
    """Lista de tipos con su nombre de estación y su forma, en el orden del modelo."""
    tipos = []
    for tipo in modelo.tipos:
        tipos.append({"tipo": tipo, "estacion": nombre_de_estacion(modelo, tipo),
                      "forma": forma_de_tipo(tipo)})
    return tipos


def _lotes_para_el_mapa(modelo, resultado):
    """Cada lote con su posición y, si se construye ahí, los datos de su estación."""
    fila_por_lote = {}
    if resultado is not None:
        for fila in filas_de_estaciones(modelo, resultado):
            fila_por_lote[fila["lote"]] = fila
    lotes = []
    for lote in sorted(modelo.instancia.lotes, key=_clave_de_objeto_lote):
        latitud, longitud = modelo.instancia.nodos[lote.nodo]
        estacion = None
        if lote.codigo in fila_por_lote:
            fila = fila_por_lote[lote.codigo]
            estacion = {"tipo": fila["tipo"], "nombre": fila["estacion"],
                        "costo": fila["costo"], "casos": fila["casos"]}
        lotes.append({"codigo": lote.codigo, "lat": latitud, "lon": longitud, "estacion": estacion})
    return lotes


def _incidentes_para_el_mapa(modelo, resultado, fechas):
    """Incidentes como listas cortas [id, lat, lon, posición_del_tipo, cubierto, fecha].

    Se usan listas y no diccionarios porque ciudad tiene 5.300 incidentes:
    así el JSON pesa menos de la mitad.
    """
    ids_cubiertos = set()
    if resultado is not None:
        cubiertos, _no_cubiertos = clasificar_incidentes(modelo, resultado["estaciones"])
        for incidente in cubiertos:
            ids_cubiertos.add(incidente.identificador)
    posicion_del_tipo = {}
    for posicion in range(len(modelo.tipos)):
        posicion_del_tipo[modelo.tipos[posicion]] = posicion
    incidentes = []
    for incidente in modelo.instancia.incidentes:
        latitud, longitud = modelo.instancia.nodos[incidente.nodo]
        cubierto = 1 if incidente.identificador in ids_cubiertos else 0
        fecha = fechas.get(incidente.identificador, "")
        incidentes.append([incidente.identificador, latitud, longitud,
                           posicion_del_tipo[incidente.tipo], cubierto, fecha])
    return incidentes


def datos_del_mapa(modelo, resultado=None, fechas=None):
    """Todo lo que el navegador necesita para dibujar la propuesta, listo para JSON.

    Con `resultado=None` se dibuja la instancia sin propuesta (vista previa):
    lotes vacíos e incidentes sin clasificar.
    """
    if fechas is None:
        fechas = {}
    incidentes = _incidentes_para_el_mapa(modelo, resultado, fechas)
    cantidad_cubiertos = 0
    for incidente in incidentes:
        cantidad_cubiertos += incidente[4]
    return {
        "hay_propuesta": resultado is not None,
        "tipos": _tipos_para_el_mapa(modelo),
        "lotes": _lotes_para_el_mapa(modelo, resultado),
        "incidentes": incidentes,
        "limites": limites(modelo),
        "cubiertos": cantidad_cubiertos,
        "no_cubiertos": len(incidentes) - cantidad_cubiertos,
    }


# ---------------------------------------------------------------- exportación

def json_para_html(datos):
    """JSON que se puede pegar dentro de <script> sin que un texto de los CSV lo rompa.

    Un nombre de lote como `</script><script>alert(1)` cerraría la etiqueta.
    Por eso <, > y & se escriben como \\u003c, \\u003e y \\u0026: el JSON
    significa lo mismo, pero el HTML ya no ve etiquetas.
    """
    texto = json.dumps(datos, ensure_ascii=False)
    texto = texto.replace("<", "\\u003c")
    texto = texto.replace(">", "\\u003e")
    texto = texto.replace("&", "\\u0026")
    # U+2028 y U+2029 (separadores de línea y de párrafo) son válidos en JSON,
    # pero los navegadores viejos los toman como fin de línea dentro de
    # JavaScript. Se escriben con escapes de Python ("\u2028"): NO pegar aquí
    # los caracteres literales, son invisibles y si se pierden queda
    # replace("", ...), que mete el texto entre cada letra y rompe el JSON.
    texto = texto.replace("\u2028", "\\u2028")
    texto = texto.replace("\u2029", "\\u2029")
    return texto


def _leer_web(ruta_relativa):
    """Texto de un archivo de interfaz/web (estilos o código de dibujo)."""
    return (CARPETA_WEB / ruta_relativa).read_text(encoding="utf-8")


def _script_seguro(codigo):
    """Evita que un `</script` dentro del código cierre la etiqueta antes de tiempo."""
    return codigo.replace("</script", "<\\/script")


def _fuentes_incrustadas():
    """Reglas @font-face con las fuentes dentro (base64): el archivo no depende de nada."""
    reglas = []
    for familia, ruta_relativa in FUENTES_DEL_EXPORTADO:
        contenido = (CARPETA_WEB / ruta_relativa).read_bytes()
        codificado = base64.b64encode(contenido).decode("ascii")
        reglas.append(f"@font-face {{ font-family: '{familia}'; font-weight: 300 700; "
                      f"font-display: swap; src: url(data:font/ttf;base64,{codificado}) "
                      f"format('truetype'); }}")
    return "\n".join(reglas)


def resumen_de_propuesta(modelo, resultado, titulo, detalle):
    """Cifras que el HTML exportado muestra en su cabecera."""
    return {
        "titulo": titulo,
        "detalle": detalle,
        "valor": resultado["valor"],
        "costo_total": resultado["costo_total"],
        "presupuesto": modelo.presupuesto,
        "estaciones": len(resultado["estaciones"]),
        "casos_cubiertos": dict(resultado["casos_cubiertos"]),
    }


def exportar_html(modelo, resultado, fechas=None, titulo="Propuesta", detalle="", tema="oscuro"):
    """HTML completo y autocontenido del mapa de la propuesta (se abre sin servidor).

    Incluye Leaflet, las fuentes, los estilos y el mismo código de dibujo
    de la interfaz. Los datos van como JSON escapado (ver json_para_html).
    Solo el fondo de calles (teselas de OpenStreetMap) necesita internet.
    """
    datos = datos_del_mapa(modelo, resultado, fechas)
    datos["resumen"] = resumen_de_propuesta(modelo, resultado, titulo, detalle)
    estilos = [_fuentes_incrustadas()]
    for ruta_relativa in ESTILOS_DEL_EXPORTADO:
        estilos.append(_leer_web(ruta_relativa))
    scripts = []
    for ruta_relativa in SCRIPTS_DEL_EXPORTADO:
        scripts.append(f"<script>{_script_seguro(_leer_web(ruta_relativa))}</script>")
    tema_seguro = "claro" if tema == "claro" else "oscuro"
    politica = ("default-src 'none'; img-src https://tile.openstreetmap.org data:; "
                "style-src 'unsafe-inline'; script-src 'unsafe-inline'; font-src data:")
    partes = [
        "<!doctype html>",
        f'<html lang="es" data-tema="{tema_seguro}">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f'<meta http-equiv="Content-Security-Policy" content="{politica}">',
        f"<title>{html.escape(titulo)}</title>",
        "<style>\n" + "\n".join(estilos) + "\n</style>",
        "</head>",
        '<body class="exportado">',
        '<header class="exportado-cabecera" id="cabecera"></header>',
        '<main class="mapa exportado-mapa" id="mapa" aria-label="Mapa de la propuesta"></main>',
        f'<script type="application/json" id="datos-del-mapa">{json_para_html(datos)}</script>',
    ]
    partes.extend(scripts)
    partes.append("<script>MapaEstaciones.iniciarExportado();</script>")
    partes.append("</body>")
    partes.append("</html>")
    return "\n".join(partes)
