"""Línea de comandos del proyecto (Partes 1 a 4).

Uso:
    py main.py parte1 <instancia>
    py main.py parte2 <instancia> [base|propia|propia_ls]
    py main.py parte3 <instancia> [--limite SEGUNDOS]
    py main.py tabla
    py main.py parte4 <instancia> [--metodo base|propia|propia_ls|exacto]
                                  [--salida ruta.html] [--limite SEGUNDOS]
    py main.py interfaz [--puerto 8765] [--no-abrir]

Todo usa solo la biblioteca estándar de Python.
"""

import argparse
import sys
import time
from pathlib import Path

from estaciones.ejecucion import HEURISTICAS, METODOS, ejecutar_metodo
from estaciones.exacto import resolver
from estaciones.lectura import cargar_instancia, carpeta_de_instancia
from estaciones.mapa import exportar_html, leer_fechas, tabla_texto
from estaciones.modelo import Modelo


USO = ("Uso: py main.py parte1|parte2 <instancia> [base|propia|propia_ls]  o  "
       "py main.py parte3 <instancia> [--limite SEGUNDOS]  o  py main.py tabla  o  "
       "py main.py parte4 <instancia> [--metodo M] [--salida R] [--limite S]  o  "
       "py main.py interfaz [--puerto P] [--no-abrir]")
SEGUNDOS_POR_ANIO = 365.25 * 24 * 3600
LIMITE_PARTE3_POR_DEFECTO = 60
# El exacto de parte4 siempre tiene límite: en una instancia nueva y grande
# podría no terminar nunca. Si se corta, se dice que no quedó certificado.
LIMITE_PARTE4_POR_DEFECTO = 60
# En `tabla` no se corre el exacto con más de 30 lotes: comuna (15 lotes)
# termina en ~1 s, pero 4^30 ya es ~10^18 propuestas y no hay garantía
# de terminar; ciudad (80 lotes) queda fuera.
LOTES_MAXIMOS_PARA_EXACTO_EN_TABLA = 30
# parte4 sin --metodo: con más lotes que este límite se usa propia_ls y no
# el exacto. Se decide por el TAMAÑO y no por el nombre de la carpeta, así
# una instancia nueva y grande de la sustentación no se queda esperando al
# exacto (que en ella no alcanzaría a certificar). Mismo criterio que `tabla`.
LOTES_MAXIMOS_PARA_EXACTO_EN_PARTE4 = 30


def mostrar_resultado(resultado):
    """Imprime una propuesta con el formato de salida del enunciado."""
    print(f"estaciones={resultado['estaciones']}")
    print(f"costo_total={resultado['costo_total']}")
    print(f"casos_cubiertos={resultado['casos_cubiertos']}")
    print(f"valor={resultado['valor']}")


def parte1(modelo):
    """Costo y lista de incidentes cubiertos de cada (lote, tipo)."""
    for codigo_lote, tipo in modelo.todas_las_opciones():
        costo = modelo.costo(codigo_lote, tipo)
        cubiertos = modelo.cobertura(codigo_lote, tipo)
        print(f"{codigo_lote} {tipo}: costo={costo} incidentes={cubiertos}")


def parte2(modelo, nombre_heuristica):
    """Ejecuta una heurística y muestra su propuesta y su tiempo."""
    if nombre_heuristica not in HEURISTICAS:
        raise SystemExit(f"Heurística desconocida: {nombre_heuristica}")
    inicio = time.perf_counter()
    resultado = HEURISTICAS[nombre_heuristica](modelo)
    tiempo = time.perf_counter() - inicio
    print(f"heuristica={nombre_heuristica}")
    mostrar_resultado(resultado)
    print(f"tiempo_s={tiempo:.4f}")


def parte3(modelo, limite_segundos):
    """Branch & Bound con límite de tiempo; dice si el óptimo quedó certificado."""
    explicar_espacio(modelo)
    resultado = resolver(modelo, limite_segundos=limite_segundos)
    mostrar_resultado(resultado)
    print(f"tiempo_s={resultado['tiempo_s']:.4f}")
    print(f"estadisticas_bb={resultado['estadisticas_bb']}")
    if resultado["optimo_certificado"]:
        print("optimo_certificado=True (la búsqueda terminó completa: es el óptimo)")
    else:
        print(f"optimo_certificado=False (se cortó a los {limite_segundos} s: "
              f"es la mejor propuesta encontrada, no necesariamente el óptimo)")


def tamanio_del_espacio(modelo):
    """Devuelve (opciones_por_lote, cantidad_lotes, espacio) con enteros exactos."""
    cantidad_lotes = len(modelo.instancia.lotes)
    opciones_por_lote = len(modelo.tipos) + 1
    return opciones_por_lote, cantidad_lotes, opciones_por_lote ** cantidad_lotes


def explicar_espacio(modelo):
    """Muestra el tamaño del espacio de búsqueda y cuánto tardaría la fuerza bruta."""
    opciones_por_lote, cantidad_lotes, espacio = tamanio_del_espacio(modelo)
    anios = espacio / 10**9 / SEGUNDOS_POR_ANIO
    print(f"espacio completo = {opciones_por_lote}^{cantidad_lotes} = {espacio}")
    print(f"a 10^9 propuestas por segundo serían unos {anios:.3g} años de fuerza bruta")


def medir(funcion, modelo):
    """Ejecuta funcion(modelo) y devuelve (valor, segundos)."""
    inicio = time.perf_counter()
    resultado = funcion(modelo)
    return resultado["valor"], time.perf_counter() - inicio


def tabla():
    """Tabla comparativa de valor y tiempo para las tres instancias."""
    for nombre_instancia in ("pequena", "comuna", "ciudad"):
        modelo = Modelo(cargar_instancia(nombre_instancia))
        print(f"instancia={nombre_instancia}")
        for nombre_heuristica, heuristica in HEURISTICAS.items():
            valor, tiempo = medir(heuristica, modelo)
            print(f"  {nombre_heuristica}: valor={valor} tiempo_s={tiempo:.4f}")
        opciones_por_lote, cantidad_lotes, espacio = tamanio_del_espacio(modelo)
        if cantidad_lotes > LOTES_MAXIMOS_PARA_EXACTO_EN_TABLA:
            print(f"  optimo: no calculado (espacio {opciones_por_lote}^{cantidad_lotes}; "
                  f"ver py main.py parte3 {nombre_instancia})")
        else:
            valor, tiempo = medir(resolver, modelo)
            print(f"  optimo: valor={valor} tiempo_s={tiempo:.4f}")


def metodo_por_defecto_parte4(modelo):
    """Instancia grande (más de 30 lotes): propia_ls; si no, el óptimo exacto."""
    if len(modelo.instancia.lotes) > LOTES_MAXIMOS_PARA_EXACTO_EN_PARTE4:
        return "propia_ls"
    return "exacto"


def leer_opciones_parte4(opciones):
    """Lee `<instancia> [--metodo M] [--salida R] [--limite S]` de parte4."""
    lector = argparse.ArgumentParser(prog="main.py parte4",
                                     description="Parte 4: tabla y mapa de una propuesta.")
    lector.add_argument("instancia", help="nombre (pequena, comuna, ciudad) o ruta de carpeta")
    lector.add_argument("--metodo", choices=METODOS, default=None)
    lector.add_argument("--salida", default=None, help="ruta del mapa HTML")
    lector.add_argument("--limite", type=float, default=LIMITE_PARTE4_POR_DEFECTO,
                        help=f"segundos máximos del exacto (por defecto {LIMITE_PARTE4_POR_DEFECTO})")
    return lector.parse_args(opciones)


def parte4(opciones):
    """Calcula la propuesta, imprime la tabla y guarda el mapa HTML autocontenido."""
    argumentos = leer_opciones_parte4(opciones)
    if argumentos.limite < 0:
        raise SystemExit("--limite no puede ser negativo")
    nombre = Path(argumentos.instancia).name
    try:
        instancia = cargar_instancia(argumentos.instancia)
    except (ValueError, FileNotFoundError) as error:
        raise SystemExit(f"Error al leer la instancia: {error}")
    modelo = Modelo(instancia)
    metodo = argumentos.metodo or metodo_por_defecto_parte4(modelo)
    salida = Path(argumentos.salida or f"salidas/mapa_{nombre}_{metodo}.html")
    resultado, segundos = ejecutar_metodo(modelo, metodo, argumentos.limite)
    print(f"instancia={nombre} metodo={metodo} tiempo_s={segundos:.3f}")
    detalle = metodo
    if metodo == "exacto":
        if resultado["optimo_certificado"]:
            texto_certificado = "óptimo certificado"
        else:
            texto_certificado = (f"mejor encontrada en {argumentos.limite:g} s "
                                 "(no certificada)")
        print(texto_certificado)
        detalle = f"exacto · {texto_certificado}"
    print(tabla_texto(modelo, resultado))
    inicio = time.perf_counter()
    fechas = leer_fechas(carpeta_de_instancia(argumentos.instancia))
    titulo = f"Estaciones · {nombre}"
    documento = exportar_html(modelo, resultado, fechas, titulo=titulo, detalle=detalle)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(documento, encoding="utf-8")
    segundos_mapa = time.perf_counter() - inicio
    tamano_kb = salida.stat().st_size / 1024
    print(f"mapa={salida} ({tamano_kb:.0f} KB, generado en {segundos_mapa:.2f} s)")


def leer_opciones_interfaz(opciones):
    """Lee `[--puerto P] [--no-abrir]` del subcomando interfaz."""
    lector = argparse.ArgumentParser(prog="main.py interfaz",
                                     description="Interfaz web local (feria).")
    lector.add_argument("--puerto", type=int, default=8765, help="puerto local (por defecto 8765)")
    lector.add_argument("--no-abrir", action="store_true", help="no abrir el navegador")
    return lector.parse_args(opciones)


def interfaz(opciones):
    """Levanta el servidor local de la interfaz (solo 127.0.0.1)."""
    # Se importa aquí: las Partes 1 a 3 no necesitan cargar el servidor.
    from interfaz.servidor import iniciar

    argumentos = leer_opciones_interfaz(opciones)
    iniciar(argumentos.puerto, abrir_navegador=not argumentos.no_abrir)


def main(argumentos):
    """Lee los argumentos y llama a la parte pedida."""
    if len(argumentos) == 0:
        raise SystemExit(USO)
    comando = argumentos[0]
    if comando == "tabla":
        tabla()
        return
    if comando == "parte4":
        parte4(argumentos[1:])
        return
    if comando == "interfaz":
        interfaz(argumentos[1:])
        return
    if comando not in ("parte1", "parte2", "parte3") or len(argumentos) < 2:
        raise SystemExit(USO)
    nombre_instancia = argumentos[1]
    modelo = Modelo(cargar_instancia(nombre_instancia))
    if comando == "parte1":
        parte1(modelo)
    elif comando == "parte2":
        nombre_heuristica = "base"
        if len(argumentos) > 2:
            nombre_heuristica = argumentos[2]
        parte2(modelo, nombre_heuristica)
    else:
        parte3(modelo, leer_limite(argumentos[2:]))


def leer_limite(opciones):
    """Lee `--limite SEGUNDOS` de los argumentos de parte3 (por defecto 60)."""
    if len(opciones) == 0:
        return LIMITE_PARTE3_POR_DEFECTO
    if len(opciones) != 2 or opciones[0] != "--limite":
        raise SystemExit(USO)
    try:
        limite = float(opciones[1])
    except ValueError:
        raise SystemExit(f"--limite debe ser un número de segundos, no {opciones[1]!r}")
    if limite < 0:
        raise SystemExit("--limite no puede ser negativo")
    return limite


if __name__ == "__main__":
    main(sys.argv[1:])
