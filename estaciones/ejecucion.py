"""Correr un método de solución por su nombre y medir cuánto tardó.

Lo usan `main.py parte4` y el servidor de la interfaz, así los dos
ejecutan exactamente el mismo código (no hay una copia por cada uno).
"""

import time

from .exacto import resolver
from .heuristicas import base, propia, propia_ls


HEURISTICAS = {"base": base, "propia": propia, "propia_ls": propia_ls}
METODOS = ("base", "propia", "propia_ls", "exacto")


def ejecutar_metodo(modelo, metodo, limite_segundos=None):
    """Corre el método elegido y devuelve (resultado, segundos).

    El límite de tiempo solo se usa en el exacto: las heurísticas siempre
    terminan y así su resultado es siempre el mismo.
    """
    if metodo not in METODOS:
        raise ValueError(f"Método desconocido: {metodo}")
    inicio = time.perf_counter()
    if metodo == "exacto":
        resultado = resolver(modelo, limite_segundos=limite_segundos)
    else:
        resultado = HEURISTICAS[metodo](modelo)
    return resultado, time.perf_counter() - inicio


def esta_certificado(metodo, resultado):
    """True/False si el método es el exacto (¿terminó la búsqueda?); None si es heurística."""
    if metodo != "exacto":
        return None
    return bool(resultado.get("optimo_certificado", True))
