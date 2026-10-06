# Estaciones

Práctica de Análisis y Diseño de Algoritmos (Universidad de Medellín). Decide qué estaciones
(CAI, tránsito y grúas, bomberos) construir y en qué lotes, sin pasar el presupuesto, para cubrir
el mayor valor de incidentes medidos sobre la red vial dirigida de la ciudad.

La explicación completa (algoritmos, decisiones, resultados y preguntas de sustentación) está en
[docs/GUIA_DE_ESTUDIO.md](docs/GUIA_DE_ESTUDIO.md); las decisiones de diseño de la interfaz, en
[docs/DISENO.md](docs/DISENO.md).

## Requisitos

- Python 3.10 o superior (se usa `int.bit_count`); probado con Python 3.13 en Windows.
- **Sin dependencias**: todo usa la biblioteca estándar. No hay que instalar nada.
- Opcional: Node (solo para correr las pruebas de JavaScript; si no está, esa prueba se salta).
- El fondo de calles del mapa (teselas de OpenStreetMap) necesita internet; todo lo demás
  funciona sin conexión.

## Cómo ejecutar

Todos los comandos se ejecutan desde la carpeta raíz del proyecto. `<instancia>` es un nombre de
`instancias/` (`pequena`, `comuna`, `ciudad`) o la ruta de una carpeta con los cinco archivos.

```text
py main.py parte1 <instancia>                          costo y cobertura de cada (lote, tipo)
py main.py parte2 <instancia> [base|propia|propia_ls]  heurísticas (por defecto: base)
py main.py parte3 <instancia> [--limite SEGUNDOS]      óptimo con Branch & Bound (límite 60 s)
py main.py tabla                                       tabla comparativa de las 3 instancias
py main.py parte4 <instancia> [--metodo base|propia|propia_ls|exacto]
                              [--salida ruta.html] [--limite SEGUNDOS]
py main.py interfaz [--puerto 8765] [--no-abrir]       interfaz web de la feria
py -m unittest discover -s tests                       tests
```

`parte4` imprime la tabla de estaciones y escribe un mapa HTML autocontenido (se abre con doble
clic) en `salidas/mapa_<instancia>_<método>.html`. Sin `--metodo` decide por tamaño: con más de
30 lotes (como ciudad) usa `propia_ls`; si no, el exacto con límite de 60 s.

Los CSV pueden traer coma decimal (`367,9`) y tipos con mayúsculas o espacios (`Hurto `): se
normalizan al leer.

## Notebook

`practica_estaciones.ipynb` es la entrega: conserva las celdas del enunciado y agrega debajo de
cada parte la solución con salidas guardadas (funciones `parte1`, `parte2` y `parte3` con
`assert` contra los casos del enunciado, tablas, instancias malas, cálculo de 4^80, mapas y el
párrafo de justificación al concejo). Sus celdas solo llaman al paquete `estaciones/`. Se abre
con Jupyter o VS Code desde esta carpeta y se ejecuta todo en orden (unos 35 s, casi todo
`propia_ls` en ciudad). `tests/test_notebook.py` lo valida.

`interfaz` levanta un servidor local en `http://127.0.0.1:8765` y abre el navegador: elegir
instancia, presupuesto, pesos y método, y ver la propuesta sobre el mapa. Atajos: `[` controles,
`]` resultados, Enter calcula.

## Estructura

```text
practica/
├── README.md                   este resumen
├── docs/GUIA_DE_ESTUDIO.md     guía de estudio y sustentación
├── docs/DISENO.md              decisiones de diseño de la interfaz (con evidencia)
├── main.py                     único punto de entrada: parte1..parte4, tabla, interfaz
├── estaciones/                 paquete núcleo (biblioteca estándar)
│   ├── lectura.py              lectura y validación de instancias
│   ├── grafo.py                Dijkstra con corte
│   ├── modelo.py               costos, coberturas (máscaras de bits) y evaluación
│   ├── heuristicas.py          base, propia y propia_ls
│   ├── exacto.py               backtracking + Branch & Bound
│   ├── ejecucion.py            correr un método por nombre y medir el tiempo
│   └── mapa.py                 tabla, datos del mapa y mapa HTML autocontenido
├── interfaz/
│   ├── servidor.py             servidor local (http.server) + API JSON, solo 127.0.0.1
│   └── web/                    página: HTML, CSS, JavaScript; vendor/ con Leaflet y fuentes
├── tests/                      pruebas con unittest (y tests/js con node --test)
├── instancias/                 pequena, comuna y ciudad (datos del enunciado)
├── instancias_malas/           una instancia donde falla cada heurística, con su README
├── .gitignore
└── practica_estaciones.ipynb   enunciado + solución (Partes 1 a 4)
```

La carpeta `salidas/` la crea `main.py parte4`; no se versiona.

Archivos de terceros incluidos (sin CDN): Leaflet 1.9.4 (`interfaz/web/vendor/leaflet`, licencia
BSD-2-Clause) y las fuentes Familjen Grotesk y Fira Code (`interfaz/web/vendor/fuentes`, licencia
SIL OFL 1.1).

## Resultados

Valor de cada método (`py main.py tabla`):

| Instancia | base | propia | propia_ls | óptimo |
|---|---|---|---|---|
| pequena | 15 | 19 | 20 | 20 |
| comuna | 1529 | 1492 | 1574 | 1574 (certificado en ~1 s) |
| ciudad | 7591 | 7706 | 7827 (20 a 35 s) | no calculado (4^80 propuestas) |

- `propia` construye una estación a la vez (razón valor/costo) y es la que cumple el requisito
  2.2: supera a la base en pequena y ciudad. `propia_ls` es **híbrida**: arranques golosos de una
  estación a la vez + mejora local que quita y cambia estaciones.
- Los tiempos no incluyen el precálculo de coberturas (lectura + Dijkstra: menos de 1 s en
  ciudad), que se hace una vez por instancia.
- Instancias malas (`instancias_malas/`, con los costos, radios y pesos oficiales y a lo sumo 6
  nodos): base 11 vs óptimo 13, propia 6 vs 8, propia_ls 12 vs 13.

## Sustentación: instancia nueva

Copiar la carpeta con `nodos.csv`, `aristas.csv`, `lotes.csv`, `incidentes.csv` y
`parametros.json` en cualquier lugar y pasar su ruta:

```text
py main.py parte2 C:\ruta\nueva propia_ls
py main.py parte3 C:\ruta\nueva --limite 30
py main.py parte4 C:\ruta\nueva --limite 30
```

En la interfaz: "Datos" > "Otra carpeta…" y escribir la ruta completa. Los datos mal formados se
rechazan con un mensaje claro (archivo y dato con problema; en ids repetidos, también las líneas).

## Estado

- Partes 1, 2, 3 y 4 y el notebook completos; 71 tests (`py -m unittest discover -s tests`).
- Interfaz revisada con capturas de Chrome sin ventana en escritorio y teléfono, tema oscuro y
  claro; no se probó con lectores de pantalla ni en otros navegadores.
- El notebook se ejecutó con Python (sin Jupyter, que no estaba instalado); los mapas se ven
  dentro de él solo si IPython está disponible, y si no, la celda imprime la ruta del HTML.
