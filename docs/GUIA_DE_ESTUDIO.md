# Estaciones: guía de estudio y sustentación

Práctica de Análisis y Diseño de Algoritmos (Universidad de Medellín): decidir qué estaciones
(CAI, tránsito y grúas, bomberos) construir y en qué lotes, sin pasarse del presupuesto, para
cubrir el mayor valor posible de incidentes.

Este documento explica **qué hace el código y por qué se hizo así**. Todo número, salida o
fragmento de código que aparece aquí se obtuvo ejecutando o copiando el código actual del
repositorio (Python 3.13, comando `py`; todo usa solo la biblioteca estándar). Cuando algo es
teoría que no se comprobó aquí, se marca como **"dato de referencia, no verificado aquí"**.

Esta guía vive en `docs/`; todos los comandos se ejecutan desde la **carpeta raíz** del
proyecto (la que contiene `main.py`). El `README.md` de la raíz es el resumen corto.

## Índice

- [0. Cómo usar este documento](#0-cómo-usar-este-documento)
- [1. El problema en palabras simples](#1-el-problema-en-palabras-simples)
- [2. Mapa del proyecto](#2-mapa-del-proyecto)
- [3. Recorrido completo a mano con `pequena`](#3-recorrido-completo-a-mano-con-pequena)
- [4. Cada módulo, línea por línea](#4-cada-módulo-línea-por-línea)
- [5. Greedy: por qué sirve y por qué no es óptimo](#5-greedy-por-qué-sirve-y-por-qué-no-es-óptimo)
- [6. Parte 3: el óptimo exacto](#6-parte-3-el-óptimo-exacto)
- [7. Por qué estos métodos y no otros](#7-por-qué-estos-métodos-y-no-otros)
- [8. Complejidad](#8-complejidad)
- [9. Resultados](#9-resultados)
- [10. Qué cambiar si los datos cambian en la sustentación](#10-qué-cambiar-si-los-datos-cambian-en-la-sustentación)
- [11. Banco de preguntas de sustentación](#11-banco-de-preguntas-de-sustentación)
- [12. Glosario](#12-glosario)
- [13. Parte 4: mapa, subcomando `parte4` e interfaz](#13-parte-4-mapa-subcomando-parte4-e-interfaz)
- [14. Estado y límites honestos](#14-estado-y-límites-honestos)
- [15. El notebook](#15-el-notebook)

---

## 0. Cómo usar este documento

### Ruta de estudio sugerida

| Orden | Qué leer | Tiempo aprox. | Objetivo |
|---|---|---|---|
| 1 | Sección 1 (el problema) | 20 min | Saber explicar el problema sin código. |
| 2 | Sección 3 (pequena a mano) | 60 min | Hacerlo con lápiz y papel: Dijkstra, cobertura, costo, heurística base. |
| 3 | Sección 2 y 4.1 a 4.3 | 60 min | Lectura, grafo, modelo, máscaras de bits. |
| 4 | Secciones 4.4 y 5 | 60 min | Heurísticas y por qué fallan (instancias malas). |
| 5 | Sección 6 | 90 min | Backtracking, Branch & Bound y la cota. Es lo más preguntado. |
| 6 | Secciones 7 y 8 | 40 min | Decisiones de diseño y complejidad. |
| 7 | Sección 10 | 30 min | Qué tocar si cambian los datos (se hace en vivo). |
| 8 | Sección 11 | 60 min | Practicar las respuestas en voz alta. |
| 9 | Sección 13 | 60 min | Mapa, `parte4`, servidor e interfaz web: ensayar la demo de la feria. |

### Chuleta de 1 página (para el día de la sustentación)

Comandos (los nombres cortos como `pequena` se buscan en `instancias/` del proyecto, desde
cualquier carpeta; ver sección 10):

```text
py main.py parte1 pequena                 costo y cobertura de cada (lote, tipo)
py main.py parte2 pequena base            heurística base (también: propia, propia_ls)
py main.py parte3 pequena                 óptimo exacto con Branch & Bound (límite 60 s)
py main.py parte3 ciudad --limite 20      espacio 4^80 y mejor propuesta en 20 s (sin certificar)
py main.py tabla                          tabla comparativa de las 3 instancias
py main.py parte2 C:\ruta\a\carpeta base  cualquier instancia por ruta de carpeta
py -m unittest discover -s tests          71 tests, OK (incluye servidor, mapa, notebook y JavaScript)
py main.py parte4 comuna                  tabla + mapa en salidas\mapa_comuna_exacto.html
py main.py interfaz                       interfaz web de la feria en http://127.0.0.1:8765
```

Valores clave (ejecutados con `py main.py tabla`):

| Instancia | base | propia | propia_ls | óptimo |
|---|---|---|---|---|
| pequena | 15 | 19 | 20 | 20 |
| comuna | 1529 | 1492 | 1574 | 1574 (en ~0,6 s) |
| ciudad | 7591 | 7706 | 7827 (en 20 a 35 s) | no calculado: 4^80 propuestas |

- Óptimo pequena: L1 hurto, L3 accidente, L4 hurto; costo 5400; casos 8/4/0; valor 20.
- Óptimo comuna: L03 accidente, L06 hurto, L09 hurto, L11 hurto, L13 accidente, L14 hurto,
  L15 incendio; costo 11700; casos 519/300/31; valor 1574; 41.493 nodos, 2.283 podas por
  presupuesto, 29.799 podas por cota.
- Instancias malas (parámetros oficiales, solo cambia el presupuesto): base 11 vs óptimo 13;
  propia 6 vs 8; propia_ls 12 vs 13.
- Notebook: `practica_estaciones.ipynb` tiene las Partes 1 a 4 con salidas guardadas; sus
  celdas solo llaman al paquete `estaciones/` (sección 15).

Diez frases que hay que saber decir:

1. "Es un problema de **cobertura máxima con presupuesto**: elegir estaciones que cubran el mayor
   peso de incidentes sin pasarse del dinero; un incidente cubierto dos veces cuenta una vez."
2. "Usamos **Dijkstra** porque las calles tienen longitud (pesos positivos) y sentido; BFS no
   sirve con pesos y Floyd-Warshall sería V^3 con 27.568 nodos."
3. "Medimos la distancia **desde la estación hacia el incidente**, respetando los tramos de un
   solo sentido, porque es el vehículo el que va al incidente."
4. "Cortamos Dijkstra en el **radio mayor** (3000 m): más allá nada nos sirve."
5. "Las distancias se guardan como **enteros en décimas de metro** para que la comparación
   `<= radio` sea exacta; el costo se redondea con **Decimal y ROUND_HALF_UP**, no con `round()`."
6. "Cada cobertura es un **entero usado como máscara de bits**: unir es `|`, lo nuevo es
   `& ~cubiertos`, contar es `bit_count()`. Así el incidente repetido cuenta una sola vez."
7. "El greedy no es óptimo: en la instancia mala de la base elige el CAI de valor 8 y ocupa el
   único lote cuya estación de tránsito cubre los dos accidentes; el óptimo vale 13 y la base 11."
8. "El óptimo se obtiene con **backtracking + Branch & Bound**: por cada lote, no construir o
   construir uno de 3 tipos, y podamos ramas que no pueden ganar."
9. "La **cota** es válida porque suma las ganancias marginales por separado (sobreestima por
   el solapamiento), ignora la regla de un lote y permite fracciones: relajar solo sube el
   máximo, así que nunca poda el óptimo."
10. "Lo validamos contra **fuerza bruta independiente** en pequena, en las 3 instancias malas y
    en 30 instancias aleatorias; eso es evidencia, no demostración; la demostración es el
    argumento de la cota."

---

## 1. El problema en palabras simples

### Qué es

- Hay una **red de calles** (grafo dirigido): intersecciones (nodos) y tramos (aristas) con
  longitud en metros. Un tramo `origen -> destino` solo se recorre en ese sentido.
- Hay **lotes** donde se puede construir. Cada lote está en un nodo y tiene un `factor_zona`.
- Hay **incidentes** históricos: cada uno ocurrió en un nodo y es de tipo `hurto`, `accidente`
  o `incendio`.
- Hay **tres tipos de estación**, uno por tipo de incidente, cada uno con costo base, radio y
  peso (en `parametros.json`):

| Tipo | Estación | Costo base (millones) | Radio | Peso |
|---|---|---|---|---|
| hurto | CAI | 1000 | 1000 m | 1 |
| accidente | Tránsito y grúas | 2000 | 2000 m | 3 |
| incendio | Bomberos | 5000 | 3000 m | 5 |

**Qué se decide:** en cada lote, construir nada o construir **una** estación de uno de los 3 tipos.

**Qué se maximiza:** el **valor**, la suma de los pesos de los incidentes cubiertos. Un incidente
está cubierto si existe una estación **de su mismo tipo** cuya distancia más corta por la red,
**desde la estación hasta el incidente**, es `<=` al radio del tipo.

**Restricciones:**

1. Costo de una estación = `costo_base × factor_zona`, redondeado al millón más cercano.
2. Un lote admite a lo sumo una estación.
3. La suma de costos no puede superar el presupuesto.
4. Un incidente cubierto por varias estaciones cuenta **una sola vez**.

### Modelo formal

Conjuntos:

- `L` = lotes, `T` = {hurto, accidente, incendio}, `I` = incidentes.
- Para cada par `(l, t)`: costo `c(l,t)` y conjunto cubierto `C(l,t) ⊆ I` (solo incidentes de
  tipo `t` a distancia `<= radio(t)` desde el nodo de `l`).
- `w(i)` = peso del tipo del incidente `i`.

Variable de decisión: `x(l,t) ∈ {0,1}` (1 si se construye la estación de tipo `t` en `l`).

```text
maximizar   valor(x) = Σ  w(i)   sobre todos los i que están en la UNIÓN de los C(l,t) con x(l,t)=1

sujeto a    Σ_t x(l,t) <= 1                 para cada lote l        (un lote, una estación)
            Σ_{l,t} c(l,t) · x(l,t) <= P    (presupuesto P)
            x(l,t) ∈ {0,1}
```

La palabra clave es **UNIÓN**: el valor no es la suma de los valores de cada estación.

### A qué problema conocido se parece

- **Cobertura máxima con presupuesto** (budgeted maximum coverage): elegir conjuntos con costo
  para cubrir el máximo peso de elementos. Es exactamente esto, más la regla de un lote.
- **Mochila 0/1**: cada estación es un objeto con costo (peso de la mochila) y valor. Pero en
  la mochila los valores se **suman**; aquí no, porque si dos estaciones cubren el mismo
  incidente, ese incidente cuenta una vez. Por eso decimos "mochila con cobertura que se solapa".

Que la cobertura máxima con presupuesto sea NP-difícil es un resultado conocido de la teoría
(**dato de referencia, no verificado aquí**). Lo que sí se verifica aquí es la explosión
combinatoria:

### Por qué es difícil: el cálculo real

Cada lote tiene 4 opciones (nada, hurto, accidente, incendio). Con `n` lotes hay `4^n`
propuestas (antes de filtrar por presupuesto):

| Instancia | Lotes | 4^lotes |
|---|---|---|
| pequena | 5 | 1.024 |
| comuna | 15 | 1.073.741.824 |
| ciudad | 80 | 1461501637330902918203684832716283019655932542976 |

Primeras líneas reales de `py main.py parte3 ciudad --limite 20` (después imprime la mejor
propuesta encontrada en 20 s, 7827, con `optimo_certificado=False`; ver sección 6.6):

```text
espacio completo = 4^80 = 1461501637330902918203684832716283019655932542976
a 10^9 propuestas por segundo serían unos 4.63e+31 años de fuerza bruta
```

### Por qué importa que un incidente cuente una sola vez

En `pequena`, `L1 accidente` cubre los accidentes [1, 2, 3, 4] y `L3 accidente` cubre
[1, 2, 4, 6]. Por separado valen 12 y 12 (4 accidentes × peso 3). Juntas **no valen 24**:
la unión es {1, 2, 3, 4, 6}, 5 accidentes, valor 15. La segunda estación solo aporta el
accidente 6 (valor 3).

Consecuencias:

1. **Rompe la mochila simple.** En la mochila el valor de un objeto es fijo. Aquí el valor de
   una estación depende de qué otras se eligieron. Por eso la programación dinámica clásica de
   la mochila no sirve directamente (ver 7).
2. **Hace que el greedy falle más.** Una estación que parece buena sola puede aportar poco al
   lado de otra. El greedy decide con lo que ve en ese momento y no puede deshacer.
3. **Por eso el código siempre habla de "valor nuevo"** (ganancia marginal): lo que agrega la
   estación sobre lo ya cubierto.

---

## 2. Mapa del proyecto

### Qué es

```text
practica/
├── README.md                   resumen corto: instalación, comandos, resultados
├── docs/GUIA_DE_ESTUDIO.md     esta guía
├── main.py                     línea de comandos: parte1, parte2, parte3, parte4, tabla, interfaz
├── estaciones/
│   ├── __init__.py             marca la carpeta como paquete (solo un docstring)
│   ├── lectura.py              lee y valida los 5 archivos; distancias a enteros exactos
│   ├── grafo.py                dijkstra_con_corte (heapq)
│   ├── modelo.py               clase Modelo: costos, coberturas, máscaras, evaluar
│   ├── heuristicas.py          goloso genérico; base, propia, propia_ls
│   ├── exacto.py               backtracking + Branch & Bound (resolver)
│   ├── ejecucion.py            correr un método por su nombre y medir el tiempo (parte4 e interfaz)
│   └── mapa.py                 Parte 4: tabla, datos del mapa y mapa HTML autocontenido
├── interfaz/
│   ├── servidor.py             servidor local (http.server) + API JSON; solo 127.0.0.1
│   └── web/                    la página: index.html, estilos, JavaScript y vendor/ (Leaflet, fuentes)
├── tests/
│   ├── test_casos.py           Partes 1 y 2 contra los ejemplos del enunciado
│   ├── test_exacto.py          Parte 3 contra fuerza bruta independiente
│   ├── test_robustez.py        datos mal formados, coma decimal, orden natural, límite de tiempo
│   ├── test_notebook.py        el notebook: celdas del enunciado intactas y asserts de los casos
│   ├── test_mapa.py            Parte 4: datos del mapa, mapa exportado y parte4
│   ├── test_interfaz.py        servidor: API, validaciones y seguridad con pedidos HTTP reales
│   ├── test_js.py              corre las pruebas de JavaScript con Node (si está instalado)
│   └── js/                     pruebas de formato.js y estado.js (node --test)
├── instancias/                 pequena, comuna, ciudad (datos del curso; no se modifican)
├── instancias_malas/           base, propia, propia_ls: una instancia donde falla cada heurística
│   └── <nombre>/README.md      explicación de cada caso
├── salidas/                    mapas HTML que genera parte4 (no se versiona; se regenera)
├── docs/DISENO.md              decisiones de diseño de la interfaz y su evidencia
├── .gitignore
└── practica_estaciones.ipynb   enunciado + solución de las Partes 1 a 4 (sección 15)
```

Cada instancia es una carpeta con 5 archivos: `nodos.csv` (id, lat, lon), `aristas.csv`
(origen, destino, longitud_m, nombre), `lotes.csv` (lote, nodo, factor_zona),
`incidentes.csv` (id, nodo, tipo, fecha_hora) y `parametros.json`.

### Cómo se conectan

```text
 nodos.csv  aristas.csv  lotes.csv  incidentes.csv  parametros.json
     \          |            |            |              /
      \         |            |            |             /
       +--------+------------+------------+------------+
                             |
                    lectura.cargar_instancia      valida, escala distancias a enteros
                             |
                         Instancia                (nodos, grafo, lotes, incidentes, parametros, escala)
                             |
                     modelo.Modelo(instancia, presupuesto=None, pesos=None)
                             |
          por cada lote: grafo.dijkstra_con_corte(grafo, nodo_del_lote, mayor_radio)
                             |
          por cada tipo: costo (Decimal) + incidentes a <= radio  ->  máscara de bits
                             |
                    modelo.opciones  (lista de {lote, tipo, costo, mascara})
                       /                         \
     heuristicas.base / propia / propia_ls    exacto.resolver (arranca con propia_ls)
                       \                         /
                    Modelo.evaluar(propuesta)   <- árbitro: valida reglas y recalcula desde cero
                             |
                    main.py imprime estaciones, costo_total, casos_cubiertos, valor
```

### Cómo ejecutar cada parte

```text
py main.py parte1 <instancia>
py main.py parte2 <instancia> [base|propia|propia_ls]     (por defecto: base)
py main.py parte3 <instancia> [--limite SEGUNDOS]          (por defecto: 60)
py main.py tabla
py main.py parte4 <instancia> [--metodo M] [--salida R] [--limite S]   (exacto: límite 60 s)
py main.py interfaz [--puerto 8765] [--no-abrir]
py -m unittest discover -s tests
```

`<instancia>` puede ser un nombre de `instancias/` (`pequena`, `comuna`, `ciudad`) o la ruta a
cualquier carpeta con los 5 archivos (así se usan las instancias malas:
`py main.py parte2 instancias_malas/base base`).

---

## 3. Recorrido completo a mano con `pequena`

Esta sección se puede reproducir con lápiz y papel. Al final de cada paso está la salida real
del código que lo confirma.

### 3.1 El grafo

Cuadrícula de 3 × 3 (copiada del enunciado), con las longitudes de `aristas.csv`:

```text
        970        910
   6 ──────── 7 ──────── 8          Calle 3
   │          │          ↑
990│       940│          │990  (solo 5 -> 8)
   │          │          │
   3 ──────── 4 ──────→─ 5          Calle 2
   │   900    │   960    │
930│       920│          │950       (solo 4 -> 5)
   │          │          │
   0 ──────── 1 ──────── 2          Calle 1
       950        980
```

Todos los tramos son de doble sentido (dos filas en `aristas.csv`) **excepto** `4 -> 5` y
`5 -> 8`, que solo existen en ese sentido. Lista de salidas de cada nodo (lista de adyacencia):

```text
0: 1(950) 3(930)
1: 0(950) 2(980) 4(920)
2: 1(980) 5(950)
3: 0(930) 4(900) 6(990)
4: 1(920) 3(900) 5(960) 7(940)
5: 2(950) 8(990)                 <- no hay 5->4
6: 3(990) 7(970)
7: 4(940) 6(970) 8(910)
8: 7(910)                        <- no hay 8->5
```

Lotes: L1 en nodo 1 (factor 1.1), L2 en 3 (1.5), L3 en 5 (1.4), L4 en 6 (1.5), L5 en 8 (1.5).
Presupuesto 6000.

Incidentes (id: nodo, tipo):

```text
accidente: 1:2  2:2  3:4  4:5  5:6  6:8
hurto:     7:1  8:2  9:3  10:3  11:3  12:4  13:4  14:7  15:8
incendio:  16:2  17:6  18:8
```

### 3.2 Dijkstra a mano desde L3 (nodo 5), con corte 3000

El corte es el radio mayor (incendio, 3000 m): no se sigue ningún camino que pase de 3000.
Se saca siempre de la cola el par (distancia, nodo) más pequeño.

| Paso | Sale de la cola | Qué hace | Cola después |
|---|---|---|---|
| 1 | (0, 5) | 2: 0+950=950; 8: 0+990=990 | (950,2) (990,8) |
| 2 | (950, 2) | 1: 950+980=1930; 5: 1900 no mejora 0 | (990,8) (1930,1) |
| 3 | (990, 8) | 7: 990+910=1900 | (1900,7) (1930,1) |
| 4 | (1900, 7) | 4: 2840; 6: 2870; 8: 2810 no mejora 990 | (1930,1) (2840,4) (2870,6) |
| 5 | (1930, 1) | 0: 2880; 2: 2910 no mejora; 4: 2850 no mejora 2840 | (2840,4) (2870,6) (2880,0) |
| 6 | (2840, 4) | 1: 3760, 3: 3740, 5: 3800, 7: 3780: **todos > 3000, se descartan** | (2870,6) (2880,0) |
| 7 | (2870, 6) | 3: 3860, 7: 3840: > 3000 | (2880,0) |
| 8 | (2880, 0) | 1: 3830, 3: 3810: > 3000 | vacía |

Resultado: `{5:0, 2:950, 8:990, 7:1900, 1:1930, 4:2840, 6:2870, 0:2880}`. El nodo 3 **no
aparece**: su distancia real es 3740 (se comprobó sin corte), mayor que 3000.

**El efecto del sentido único:** de 4 a 5 hay un tramo directo de 960 m, pero de 5 a 4 no;
el camino más corto 5 -> 4 es 5 -> 8 -> 7 -> 4 = 990 + 910 + 940 = 2840 m.

Salida real (`dijkstra_con_corte(grafo, 5, 3000)`, ordenada por nodo):

```text
dijkstra desde 5 [(0, 2880), (1, 1930), (2, 950), (4, 2840), (5, 0), (6, 2870), (7, 1900), (8, 990)]
```

### 3.3 Cobertura de L3 accidente

Radio de accidente = 2000. Nodos a `<= 2000` desde 5: 5 (0), 2 (950), 8 (990), 7 (1900),
1 (1930). Accidentes en esos nodos: 1 y 2 (nodo 2), 4 (nodo 5), 6 (nodo 8). El 3 (nodo 4,
2840) y el 5 (nodo 6, 2870) quedan fuera.

**Cobertura de L3 accidente = [1, 2, 4, 6]**, que coincide con el enunciado.

Costo: 2000 × 1.4 = 2800.

Cobertura de L3 hurto (radio 1000): nodos 5, 2 (950), 8 (990). Hurtos: 8 (nodo 2), 15 (nodo 8).
Resultado [8, 15]. Los hurtos 12 y 13 del nodo 4 **no** se cubren: 5 -> 4 son 2840 m. Si se
midiera al revés (4 -> 5 = 960) se cubrirían por error. Por eso importa el sentido.

### 3.4 Dijkstra y cobertura de L2 hurto (nodo 3)

Salida real desde el nodo 3 con corte 3000:

```text
dijkstra desde 3 [(0, 930), (1, 1820), (2, 2800), (3, 0), (4, 900), (5, 1860), (6, 990), (7, 1840), (8, 2750)]
```

A mano: 3 -> 4 = 900, 3 -> 0 = 930, 3 -> 6 = 990 son tramos directos, y todo lo demás pasa de
1000. Nodos a `<= 1000`: 3, 4, 0, 6. Hurtos: 9, 10, 11 (nodo 3), 12, 13 (nodo 4).
**Cobertura de L2 hurto = [9, 10, 11, 12, 13]**. Costo 1000 × 1.5 = **1500**. Coincide con el
enunciado.

### 3.5 Costos con redondeo

`costo = costo_base × factor_zona` redondeado al millón (mitades hacia arriba). En pequena
todos los productos son exactos (no hay mitades), por ejemplo L1 hurto = 1000 × 1.1 = 1100.
Salida completa de `py main.py parte1 pequena`:

```text
L1 hurto: costo=1100 incidentes=[7, 8, 12, 13]
L1 accidente: costo=2200 incidentes=[1, 2, 3, 4]
L1 incendio: costo=5500 incidentes=[16, 17, 18]
L2 hurto: costo=1500 incidentes=[9, 10, 11, 12, 13]
L2 accidente: costo=3000 incidentes=[3, 4, 5]
L2 incendio: costo=7500 incidentes=[16, 17, 18]
L3 hurto: costo=1400 incidentes=[8, 15]
L3 accidente: costo=2800 incidentes=[1, 2, 4, 6]
L3 incendio: costo=7000 incidentes=[16, 17, 18]
L4 hurto: costo=1500 incidentes=[9, 10, 11, 14]
L4 accidente: costo=3000 incidentes=[3, 5, 6]
L4 incendio: costo=7500 incidentes=[17, 18]
L5 hurto: costo=1500 incidentes=[14, 15]
L5 accidente: costo=3000 incidentes=[3, 5, 6]
L5 incendio: costo=7500 incidentes=[17, 18]
```

### 3.6 Heurística base paso a paso

Regla del enunciado: entre las estaciones con lote libre y costo `<=` presupuesto restante,
elegir la de **mayor valor nuevo**; empate: menor código de lote, y dentro del lote hurto,
accidente, incendio. Parar cuando ninguna agregue valor.

**Paso 0** (nada construido, restante 6000). Valor nuevo = valor de la estación sola
(cantidad de incidentes × peso):

| Estación | Costo | Valor nuevo | ¿Cabe? |
|---|---|---|---|
| L1 hurto | 1100 | 4 | sí |
| L1 accidente | 2200 | 12 | sí |
| **L1 incendio** | **5500** | **15** | **sí** |
| L2 hurto | 1500 | 5 | sí |
| L2 accidente | 3000 | 9 | sí |
| L2 incendio | 7500 | - | no |
| L3 hurto | 1400 | 2 | sí |
| L3 accidente | 2800 | 12 | sí |
| L3 incendio | 7000 | - | no |
| L4 hurto | 1500 | 4 | sí |
| L4 accidente | 3000 | 9 | sí |
| L4 incendio | 7500 | - | no |
| L5 hurto | 1500 | 2 | sí |
| L5 accidente | 3000 | 9 | sí |
| L5 incendio | 7500 | - | no |

Gana **L1 incendio** con 15. Restante: 6000 - 5500 = 500.

**Paso 1** (restante 500): la estación más barata que queda cuesta 1400. Ninguna cabe:
termina.

Resultado: `[('L1', 'incendio')]`, costo 5500, casos 0/0/3, **valor 15**. Salida real:

```text
heuristica=base
estaciones=[('L1', 'incendio')]
costo_total=5500
casos_cubiertos={'hurto': 0, 'accidente': 0, 'incendio': 3}
valor=15
```

Ya se ve el problema: gastó 5500 en 15 puntos y dejó 500 inútiles. El óptimo (L1 hurto + L3
accidente + L4 hurto, costo 5400) vale 20: 4 + 12 + 4 = 20 (los hurtos de L1 [7, 8, 12, 13] y
de L4 [9, 10, 11, 14] no se solapan).

---

## 4. Cada módulo, línea por línea

### 4.1 `lectura.py`

**Qué es.** `cargar_instancia(nombre_o_ruta)` lee los 5 archivos, valida y devuelve una
`Instancia`. Si el texto no es una carpeta existente, busca `instancias/<nombre>` dentro de la
carpeta del proyecto (la que contiene `estaciones`), no en el directorio actual
(`carpeta_de_instancia`); así `pequena` funciona desde cualquier carpeta. Esa función es
pública porque también la usa `main.py parte4` para encontrar `incidentes.csv` y
leer las fechas de los incidentes (una sola regla en un solo lugar).

**Validaciones que hace** (todas lanzan error con mensaje claro): archivo inexistente, columna
faltante (`_leer_filas`), falta `presupuesto_millones`, `tipos` o `costo_base`/`radio_m`/`peso`
de un tipo (`_leer_parametros`), distancia no numérica, arista con nodo inexistente, longitud
negativa (`_armar_grafo`), lote en nodo inexistente (`_leer_lotes`), incidente en nodo
inexistente o de un tipo sin parámetros (`_leer_incidentes`), y valores repetidos
(`_revisar_repetidos`): id de nodo en `nodos.csv`, código de lote en `lotes.csv` e id de
incidente en `incidentes.csv`. Ejemplo de mensaje real: `lotes.csv: el código de lote 'L1'
aparece 2 veces (líneas 2 y 4); cada uno debe ser único`.

**Datos escritos a mano** (los que deja una hoja de cálculo en español): los números aceptan
coma decimal (`normalizar_numero`: `"367,9"` se lee como 367.9) y el tipo de incidente se
normaliza con `fila["tipo"].strip().lower()`, así `"Hurto "` o `"HURTO"` se leen como `hurto`.

**Orden de los códigos de lote** (`clave_de_lote`): orden **natural**, letras y luego el número
como entero, así `L2` va antes que `L10`. Con códigos con ceros (`L01..L15`) da el mismo orden
que el texto, por eso los resultados de las instancias del curso no cambian. Un código que no
sea "letras + número" se ordena por su texto. Se usa en todo lugar donde se ordena o desempata
por lote: `modelo.py`, la salida de las heurísticas (`ordenar_por_lote`) y `exacto.py`.

**Por qué distancias ENTERAS.** En comuna y ciudad las longitudes tienen un decimal (por ejemplo
`0,10,49.9` en `instancias/comuna/aristas.csv` y `0,2,266.1` en la de ciudad). Un `float` no
puede representar exactamente 0.1, así que las sumas acumulan error:

```pycon
>>> 0.1 + 0.2
0.30000000000000004
```

Se comprobó con un Dijkstra en `float` (script aparte, no es código del proyecto) sobre
comuna: de 34.810 distancias calculadas desde los 15 lotes, **18.431** no coinciden exactamente
con la distancia exacta. Ejemplo: desde L01 al nodo 221 la distancia exacta es 173,3 m y en
`float` sale `173.29999999999998`.

¿Importa en el borde `<= radio`? Sí puede importar: en ciudad hay **8 pares (lote, incidente)
cuya distancia es exactamente igual al radio** (en comuna, 0). Con enteros, `1733 <= 10000`
es una comparación exacta y esos 8 incidentes quedan cubiertos sin ambigüedad. Honestamente:
al repetir la cobertura de ciudad con `float` no cambió ninguna decisión de cobertura (se
comprobó: 0 diferencias), pero eso fue suerte del orden de las sumas; con enteros no depende
de la suerte.

El comentario de `_escala_de_distancias` usa dos longitudes reales de aristas de comuna
(verificado en Python 3.13):

```pycon
>>> 49.9 + 68.4
118.30000000000001
```

En décimas de metro, `499 + 684 = 1183` es exacto.

**Cómo se detecta la escala.** Se busca la mayor cantidad de decimales entre todas las
longitudes y radios y se multiplica todo por `10 ** decimales` (`lectura.py`,
`_escala_de_distancias`):

```python
    mayor = 0
    for fila in filas_aristas:
        mayor = max(mayor, _cantidad_de_decimales(fila["longitud_m"]))
    for datos in parametros["tipos"].values():
        mayor = max(mayor, _cantidad_de_decimales(datos["radio_m"]))
    return 10 ** mayor
```

- `_cantidad_de_decimales` convierte el texto a `Decimal` (exacto) y mira su exponente:
  `'49.9'` tiene exponente -1, o sea 1 decimal.
- pequena: escala 1 (todo entero). comuna y ciudad: escala 10 (décimas de metro). Verificado:
  `escala 1`, `comuna escala 10`, `ciudad escala 10`.

La conversión (`lectura.py`, `_a_entero`):

```python
    numero = Decimal(normalizar_numero(texto)) * escala
    if numero != numero.to_integral_value():
        raise ValueError(f"Distancia no representable con escala {escala}: {texto}")
    return int(numero)
```

- `normalizar_numero(texto)` quita espacios y cambia la coma decimal por punto (`"367,9"` →
  `"367.9"`, como guarda los CSV una hoja de cálculo en español); no acepta separador de miles.
  Se usa en longitudes, radios, `factor_zona`, `costo_base` y coordenadas.
- `Decimal(...)`: se construye desde el texto, no desde un float, así `49.9` es
  exactamente 49.9.
- Si después de escalar no es entero, es un error (no debería pasar porque la escala se eligió
  para que todos lo sean).

El grafo se arma como lista de adyacencia dirigida (`lectura.py`, `_armar_grafo`):

```python
        grafo[origen].append((destino, longitud))
```

Solo se agrega `origen -> destino`. Una calle de doble sentido aparece dos veces en el CSV, así
que queda con dos aristas; una de un solo sentido, con una.

### 4.2 `grafo.py`: Dijkstra con corte

**Qué es** (`grafo.py`, `dijkstra_con_corte`):

```python
    distancias = {origen: 0}
    cola = [(0, origen)]
    while cola:
        distancia, nodo = heapq.heappop(cola)
        if distancia > distancias[nodo]:
            # Entrada vieja de la cola: ya encontramos un camino más corto.
            continue
        for vecino, longitud in grafo.get(nodo, []):
            nueva_distancia = distancia + longitud
            if nueva_distancia > corte:
                continue
            if vecino not in distancias or nueva_distancia < distancias[vecino]:
                distancias[vecino] = nueva_distancia
                heapq.heappush(cola, (nueva_distancia, vecino))
    return distancias
```

Línea por línea:

- `distancias = {origen: 0}`: mejor distancia conocida a cada nodo. Al final, solo contiene los
  nodos alcanzables a `<= corte`.
- `cola = [(0, origen)]`: cola de prioridad (montículo mínimo) de pares `(distancia, nodo)`.
- `heapq.heappop(cola)`: saca el par de **menor distancia**. Con pesos no negativos, cuando un
  nodo sale con su distancia mínima, esa distancia ya es definitiva (propiedad de Dijkstra).
- `if distancia > distancias[nodo]: continue`: `heapq` no permite "bajar la prioridad" de un
  elemento, así que cuando se mejora una distancia se mete un par nuevo y el viejo queda en la
  cola. Al sacarlo, se ignora. Esto se llama "lazy deletion".
- `if nueva_distancia > corte: continue`: **el corte**. No se registra ni se expande nada más
  lejos que el radio mayor.
- `grafo.get(nodo, [])`: si un nodo no tiene salidas, no falla.

**Por qué Dijkstra y no BFS.** BFS encuentra el camino con menos **tramos**, no el más corto
en **metros**. Un camino de 2 tramos de 990 m (1980) es peor que uno de 3 tramos de 100 m (300).
BFS solo sirve si todas las aristas pesan lo mismo.

**Por qué no Bellman-Ford.** Bellman-Ford existe para manejar pesos **negativos**; aquí todas las
longitudes son `>= 0` (`lectura.py` rechaza negativas). Su costo es O(V·E) por origen, mucho más
que Dijkstra.

**Por qué no Floyd-Warshall.** Calcula todas las distancias entre todos los pares en O(V^3) y
necesita una matriz V × V. Con V = 27.568 nodos (ciudad): 27.568^3 ≈ 2,1 × 10^13 operaciones y
≈ 7,6 × 10^8 celdas. Además no hace falta: solo interesan distancias **desde los 80 lotes**, no
desde todos los nodos.

**Por qué el corte.** Ningún radio pasa de 3000 m. Un nodo a 5 km de un lote no puede ser
cubierto por él. Sin corte, cada Dijkstra recorrería toda la ciudad (27.568 nodos); con corte,
solo la "bolita" de 3 km alrededor del lote. En comuna, las 15 ejecuciones con corte alcanzaron
34.810 nodos en total (≈ 2.300 por lote de 2.893). La lectura más el modelo de ciudad (80
Dijkstras + coberturas) tardaron 0,29 s + 0,21 s en esta máquina; el enunciado exige menos de
un minuto.

**Por qué la dirección importa.** La regla 4 dice: distancia **desde el nodo de la estación
hasta el nodo del incidente**, respetando el sentido, "porque es el vehículo de la estación el
que se desplaza". Por eso Dijkstra se corre **desde el lote** sobre el grafo **tal cual** (no
invertido). Ejemplo real en pequena: 4 -> 5 mide 960 m, pero 5 -> 4 mide 2840 m. L3 (nodo 5)
no cubre los hurtos del nodo 4.

**Por qué `heapq`.** Es la cola de prioridad de la biblioteca estándar, permitida
explícitamente por el enunciado. Sacar el mínimo y meter cuestan O(log n).

**Complejidad.** O((V' + E') log V') por lote, donde V' y E' son los nodos y aristas dentro del
corte. En el peor caso (corte enorme) es O((V + E) log V), el Dijkstra clásico con montículo.

**networkx prohibido.** El enunciado prohíbe `networkx`, `osmnx`, `scipy`, `itertools` y
cualquier librería que calcule rutas, distancias o combinaciones. El núcleo (`estaciones/`)
solo importa `csv`, `json`, `dataclasses`, `decimal`, `pathlib`, `heapq`, `time` (y `mapa.py`,
`base64`, `html` e `io`); `main.py` agrega `sys` y `argparse`; el servidor (`interfaz/servidor.py`)
usa `http.server`, `threading`, `urllib.parse`, `webbrowser`, `re`, `math` y `traceback`; los
tests, `unittest`, `random`, `tempfile`, `os`, `io`, `contextlib`, `http.client`, `subprocess` y
`shutil`. **No hay librerías externas de Python.** En el navegador se usa Leaflet (incluido en
el repositorio) solo para **dibujar** (sección 13): no calcula nada del problema.

### 4.3 `modelo.py`

**Qué es.** La clase `Modelo` precalcula todo lo de una instancia: costo y cobertura de cada
`(lote, tipo)`, y ofrece `evaluar`. Recibe opcionalmente `presupuesto` y `pesos` para
sobreescribir los del JSON (útil en la sustentación y en la interfaz, que los deja editar).

```python
    def __init__(self, instancia, presupuesto=None, pesos=None):
```

#### Costo con Decimal y ROUND_HALF_UP

`modelo.py`, `_calcular_costo`:

```python
        costo_base = Decimal(normalizar_numero(self.parametros["tipos"][tipo]["costo_base"]))
        factor = Decimal(normalizar_numero(lote.factor_zona))
        return int((costo_base * factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
```

- Se multiplica con `Decimal` desde texto: exacto.
- `quantize(Decimal("1"), rounding=ROUND_HALF_UP)`: redondea a entero, con las mitades hacia
  arriba ("redondeo al millón más cercano" como se enseña en el colegio).

**Por qué no `round()` de Python.** `round()` usa **redondeo bancario** (las mitades van al par
más cercano) y además trabaja sobre `float`, que ya trae error:

```pycon
>>> round(2.5), round(3.5)
(2, 4)
>>> 1000 * 1.1
1100.0
>>> Decimal(1.1)
Decimal('1.100000000000000088817841970012523233890533447265625')
>>> round(1000 * 1.0005)
1000
```

`1000 × 1.1` da `1100.0` por casualidad del redondeo del float, aunque `1.1` guardado es
1.1000000000000000888... Con un factor que produzca una mitad, por ejemplo `1.0005`, el
resultado real es 1000,5: `round()` da **1000** y el código da **1001** (verificado con una
instancia temporal: `factor 1.0005 L1 hurto costo 1001 round python 1000`). Con los datos
actuales no aparecen mitades, pero las instancias de la sustentación podrían traerlas.

#### Cobertura: UN Dijkstra por lote, reutilizado por los tres tipos

`modelo.py`, `_preparar_estaciones` (verificado en el código):

```python
        mayor_radio = max(radios.values(), default=0)
        self._costos = {}
        self._coberturas = {}
        self._mascaras = {}
        self.opciones = []
        for lote in sorted(self.instancia.lotes, key=_codigo_del_lote):
            distancias = dijkstra_con_corte(self.instancia.grafo, lote.nodo, mayor_radio)
            for tipo in self.tipos:
                self._agregar_estacion(lote, tipo, distancias, radios[tipo])
```

Dijkstra se ejecuta una sola vez por lote con el radio mayor, y el mismo diccionario
`distancias` se usa para hurto (1000), accidente (2000) e incendio (3000). Correrlo 3 veces
repetiría trabajo: los nodos a `<= 1000` ya están dentro de los nodos a `<= 3000`.

Los lotes se recorren ordenados por código (orden natural, `clave_de_lote`) y los tipos en el orden hurto,
accidente, incendio (`_tipos_en_orden`). Así `self.opciones` queda en el orden del desempate del
enunciado.

`modelo.py`, `_agregar_estacion`, la línea que decide la cobertura:

```python
            if incidente.nodo in distancias and distancias[incidente.nodo] <= radio:
```

- `incidente.nodo in distancias`: si no está, es inalcanzable o está más lejos que el corte.
- `<= radio`: la regla 4 dice "menor o igual". Con `<` se perderían los 8 incidentes de ciudad
  que están exactamente a la distancia del radio.

#### Qué es una máscara de bits y por qué

Cada incidente recibe un número de posición (`_preparar_incidentes`): en pequena el id 1 es el
bit 0, el id 2 el bit 1, ..., el id 18 el bit 17. La cobertura de una estación es **un solo
entero** cuyos bits en 1 son los incidentes que cubre.

Ejemplo didáctico con 8 incidentes (bits 7 ... 0):

```text
estación A cubre los incidentes 0, 1, 3     A        = 0b00001011
estación B cubre los incidentes 1, 2, 7     B        = 0b10000110

unión (lo que cubren juntas)                A | B    = 0b10001111   -> 5 incidentes
lo que B agrega si ya tengo A               B & ~A   = 0b10000100   -> 2 incidentes (2 y 7)
contar                                      (A | B).bit_count() = 5
```

El incidente 1 está en las dos pero en la unión aparece **una vez**: un bit es 1 o 0, no "2".
La regla "cuenta una sola vez" sale gratis.

Ejemplo real de pequena (verificado): L3 accidente = 43 = `0b101011` (bits 0,1,3,5 = ids
1,2,4,6); L1 accidente = 15 = `0b1111` (ids 1,2,3,4). Unión `0b101111`: 5 accidentes, valor 15.
L3 accidente `& ~` L1 accidente = `0b100000`: solo el id 6, valor nuevo 3.

El valor de una máscara (`modelo.py`, `valor_mask`):

```python
        valor = 0
        for tipo in self.tipos:
            cantidad = (mascara & self._mascara_por_tipo[tipo]).bit_count()
            valor += cantidad * self.pesos[tipo]
        return valor
```

`_mascara_por_tipo[tipo]` tiene en 1 los bits de todos los incidentes de ese tipo; el `&`
separa los de ese tipo y `bit_count()` (Python 3.10 o superior) los cuenta.

**Ventajas frente a `set`:**

- **Velocidad:** `|`, `&`, `~` y `bit_count` operan sobre palabras de máquina dentro de C: con
  913 incidentes son unas 15 palabras de 64 bits. Un `set` recorre elemento por elemento con
  hash. (Que sea más rápido es lo esperado por cómo están implementados; no se midió aquí un
  benchmark set vs máscara.)
- **Copiar es gratis:** un entero es inmutable; en el backtracking se pasa
  `cubiertos | opcion["mascara"]` a la recursión sin copiar conjuntos ni deshacer cambios.
- **Unión que cuenta una vez:** automática.
- Python tiene enteros de tamaño arbitrario, así que sirve con 5.300 incidentes (ciudad).

#### `evaluar`: el árbitro independiente

`modelo.py`, `evaluar` recalcula todo **desde cero con listas de ids y `set`, sin máscaras**:

```python
        for codigo_lote, tipo in propuesta:
            if codigo_lote in lotes_usados:
                raise ValueError(f"Lote repetido en propuesta: {codigo_lote}")
            lotes_usados.add(codigo_lote)
            costo_total += self.costo(codigo_lote, tipo)
            cubiertos_por_tipo[tipo].update(self.cobertura(codigo_lote, tipo))
        if costo_total > self.presupuesto:
            raise ValueError(f"Presupuesto excedido: {costo_total} > {self.presupuesto}")
```

- Rechaza lote repetido y presupuesto excedido; `self.costo` rechaza lote o tipo inexistente.
- Cuenta casos por tipo con `set` (una vez cada incidente) y calcula el valor.

**Por qué TODA heurística pasa por él.** `base`, `propia` y `propia_ls` devuelven
`_resultado(modelo, propuesta)`, que hace `modelo.evaluar(ordenar_por_lote(propuesta))`; `resolver`
también termina con `modelo.evaluar(...)`. Así:

1. Ninguna propuesta inválida puede imprimirse: si una heurística tuviera un error, `evaluar`
   lanzaría excepción.
2. El valor reportado se calcula por un camino distinto (sets) al que usaron las heurísticas
   (máscaras). Si las máscaras tuvieran un error, el test `test_heuristicas_pasan_por_evaluar`
   lo detectaría.
3. Las estaciones salen ordenadas por código de lote, como pide la salida.

### 4.4 `heuristicas.py`

**Qué es.** Una única función `goloso(modelo, puntaje, estaciones_iniciales=None)` que agrega
estaciones una por una. Lo que cambia entre heurísticas es la función `puntaje`.

`heuristicas.py`, `_elegir_siguiente` (el corazón):

```python
    for opcion in modelo.opciones:
        if opcion["lote"] in lotes_usados:
            continue
        if opcion["costo"] > presupuesto_restante:
            continue
        valor_nuevo = modelo.valor_mask(opcion["mascara"] & ~cubiertos)
        if valor_nuevo == 0:
            continue
        puntaje_de_la_opcion = puntaje(valor_nuevo, opcion["costo"])
        if mejor_opcion is None or puntaje_de_la_opcion > mejor_puntaje:
            mejor_opcion = opcion
            mejor_puntaje = puntaje_de_la_opcion
    return mejor_opcion
```

- Filtra lote ocupado y costo que no cabe (paso 2 del enunciado).
- `valor_nuevo`: lo que la estación agrega sobre lo ya cubierto (paso 3).
- `if valor_nuevo == 0: continue`: si no agrega nada, no se considera (paso 4: si ninguna
  agrega, termina).
- `puntaje_de_la_opcion > mejor_puntaje` con **mayor estricto**: en un empate se queda la que
  apareció primero. Como `modelo.opciones` está ordenada por código de lote y luego hurto,
  accidente, incendio, ese es exactamente el desempate del enunciado.

`goloso` repite hasta que `_elegir_siguiente` devuelve `None`:

```python
    while True:
        opcion = _elegir_siguiente(modelo, propuesta, puntaje)
        if opcion is None:
            return propuesta
        propuesta.append((opcion["lote"], opcion["tipo"]))
```

#### base

```python
def puntaje_base(valor_nuevo, costo):
    """Regla del enunciado (heurística base): solo importa cuánto valor nuevo agrega."""
    return valor_nuevo
```

Llega adonde llega porque **ignora el costo**: en pequena elige L1 incendio (15 por 5500) y se
queda sin dinero.

#### propia (razón valor/costo)

```python
    if costo <= 0:
        razon = float("inf")
    else:
        razon = valor_nuevo / costo
    return (razon, valor_nuevo, -costo)
```

- Puntaje = valor nuevo por millón. Si dos razones empatan, gana más valor nuevo; si también,
  menos costo (`-costo`: tuplas se comparan elemento a elemento). Si todo empata, el orden de
  `opciones`.
- Idea: es el greedy clásico de la mochila fraccional. En pequena elige L1 accidente (razón
  12/2200 ≈ 0,00545, la mayor), luego L2 hurto y L3 hurto: valor 19.
- Pierde contra base en comuna (1492 < 1529) porque nunca construye bomberos: la estación de
  incendio L09 aporta 155 pero cuesta 4250 (razón ≈ 0,0365) y siempre hay CAI o tránsito
  pequeños con mejor razón; al final sobran 400 y ya no cabe. Ver sección 9.

#### propia_ls (multi-arranque + mejora local)

`propia_ls` es **híbrida**: sus arranques construyen una estación a la vez (golosos), pero
después la **mejora local** quita y cambia estaciones ya elegidas. Por eso no la presentamos
como "constructiva pura": el requisito 2.2 del enunciado ("construya la propuesta eligiendo
una estación a la vez y supere a la base en al menos una instancia") se cumple con `propia`
(19 > 15 en pequena y 7706 > 7591 en ciudad). `propia_ls` es la que recomendamos por valor.

```python
    plazo = None
    if limite_segundos is not None:
        plazo = time.perf_counter() + limite_segundos
    inicial = _mejor_arranque(modelo, plazo)
    mejorada = _mejora_local(modelo, inicial, plazo)
    return _resultado(modelo, mejorada)
```

`limite_segundos` es opcional (por defecto `None`, sin límite: es lo que usan `parte2`, `tabla`
y los tests, y el resultado es siempre el mismo). El exacto lo usa para que su límite de tiempo
sea real; se explica en 6.6.

**1. Multi-arranque** (`_mejor_arranque`): prueba el goloso por razón, el goloso base y, para
**cada** estación que cabe en el presupuesto, el goloso por razón forzando esa estación como
**primera** elección:

```python
    for opcion in modelo.opciones:
        if _se_acabo_el_tiempo(plazo):
            break
        if opcion["costo"] <= modelo.presupuesto:
            primera = [(opcion["lote"], opcion["tipo"])]
            candidatas.append(goloso(modelo, puntaje_razon, primera))
```

Por qué: el error típico del greedy es una primera decisión mala que condiciona todo. Probar
todas las primeras corrige eso. En pequena, el arranque ya devuelve
`[('L1', 'hurto'), ('L3', 'accidente'), ('L4', 'hurto')]` (valor 20).

**2. Comparación** (`_es_mejor`): mayor valor, o igual valor y menor costo.

```python
    if valor_candidata != valor_actual:
        return valor_candidata > valor_actual
    return costo_candidata < costo_actual
```

Aceptar "mismo valor, menos costo" sirve porque libera presupuesto para que después quepa una
estación más.

**3. Mejora local** (`_mejora_local`): desde la propuesta actual se generan **vecinos**, se
**rellena** cada uno con el goloso por razón y se salta al mejor si supera a la actual. Se
repite hasta que ningún vecino mejore.

Vecindarios (`_mejor_vecino`):

```python
    vecinos_simples = _reemplazos(modelo, actual) + _quitar_uno_o_dos(modelo, actual)
    mejor = _mejor_entre(modelo, actual, vecinos_simples, plazo)
    if mejor is not None:
        return mejor
    if _se_acabo_el_tiempo(plazo):
        # Armar la lista de dobles cambios ya cuesta tiempo: no vale la pena.
        return None
    return _mejor_entre(modelo, actual, _dobles_cambios(modelo, actual), plazo)
```

- `_reemplazos`: cambiar UNA estación por otra (otro tipo en el mismo lote u otro lote libre).
- `_quitar_uno_o_dos`: quitar una o dos estaciones (el relleno goloso decide qué poner).
- `_dobles_cambios`: quitar DOS y poner una elegida a mano (la segunda la pone el relleno). Es
  el más caro, por eso solo se usa si los otros no mejoran.

**Termina siempre** (docstring de `_mejora_local`): cada salto sube el valor o, con igual
valor, baja el costo; hay un número finito de propuestas, así que no puede ciclar.

Por qué llega adonde llega: en pequena y comuna alcanza el óptimo (20 y 1574); en ciudad llega
a 7827, el mejor de los tres métodos, pero no sabemos si es óptimo. Su límite (ver 5.3): solo
elige a mano una estación nueva por movimiento; si para mejorar hay que meter dos estaciones
concretas a la vez y el relleno prefiere otra, se queda atascada.

### 4.5 `exacto.py`

Se explica completo en la sección 6.

### 4.6 `main.py` y tests

`main.py` es el **único punto de entrada** de la línea de comandos. Lee los argumentos,
construye `Modelo(cargar_instancia(nombre))` y llama a `parte1`, `parte2`, `parte3`, `parte4`
o `tabla`. Detalles verificados en el código:

- `parte3 <instancia> [--limite SEGUNDOS]` (por defecto `LIMITE_PARTE3_POR_DEFECTO = 60`)
  sirve para **cualquier** instancia: siempre imprime el tamaño del espacio
  (`explicar_espacio`), ejecuta `resolver(modelo, limite_segundos=...)` e imprime
  `optimo_certificado=True` si la búsqueda terminó completa o `False` si se cortó por tiempo.
- `tamanio_del_espacio` calcula `opciones_por_lote ** cantidad_lotes` con enteros (exacto) y
  `explicar_espacio` los años con `SEGUNDOS_POR_ANIO = 365.25 * 24 * 3600`.
- `tabla` recorre `("pequena", "comuna", "ciudad")` y no ejecuta el exacto si la instancia
  tiene más de `LOTES_MAXIMOS_PARA_EXACTO_EN_TABLA = 30` lotes (decide por **tamaño**, no por
  nombre): imprime `optimo: no calculado (espacio 4^80; ...)`.
- `parte4` sin `--metodo` decide igual, por tamaño: con más de
  `LOTES_MAXIMOS_PARA_EXACTO_EN_PARTE4 = 30` lotes usa `propia_ls` y si no, el exacto
  (`metodo_por_defecto_parte4(modelo)`). Así una instancia nueva grande con otro nombre no se
  queda esperando al exacto.
- `parte4` (tabla + mapa HTML autocontenido) e `interfaz` (servidor local de la feria) se
  explican en la sección 13.

Tests: `py -m unittest discover -s tests` da `Ran 71 tests` / `OK`, sin nada que instalar
(las pruebas de JavaScript usan Node si está instalado; si no, esa prueba se salta y lo dice).
Lo que comprueba cada uno:

| Test | Qué comprueba |
|---|---|
| `test_parte1` | Costos y coberturas de L3 accidente y L2 hurto (ejemplos del enunciado). |
| `test_base_pequena`, `test_base_comuna` | La base da exactamente la salida del enunciado. |
| `test_propias_pequena_y_comuna` | propia 19 / 1492; propia_ls 20 y `>=` base en comuna. |
| `test_heuristicas_pasan_por_evaluar` | Lo que devuelve cada heurística es igual a `evaluar` desde cero. |
| `test_evaluar_rechaza` | `evaluar` rechaza presupuesto excedido y lote repetido. |
| `test_pequena_optimo` | B&B da 20 = fuerza bruta, con la propuesta y costo del enunciado. |
| `test_comuna_optimo` | B&B da 1574, `evaluar` lo confirma y es `>=` que las tres heurísticas. |
| `test_instancias_malas` | En cada instancia mala (≤ 6 nodos): fuerza bruta = óptimo esperado (13, 8, 13), B&B = fuerza bruta y la heurística da exactamente 11, 6 y 12. |
| `test_treinta_instancias_aleatorias` | 30 instancias al azar (semilla fija 20261005): B&B = fuerza bruta. |
| `test_robustez.py`, clase `Duplicados` | Lote, incidente o nodo repetidos, y lote/incidente en nodo inexistente, dan `ValueError` que nombra archivo y valor. |
| `test_robustez.py`, clase `DatosEscritosAMano` | Coma decimal (`"1,5"`) en longitudes, `factor_zona` y coordenadas; tipos `"Hurto "` y `" HURTO"` se leen como `hurto`. |
| `test_robustez.py`, clase `MetodoPorDefectoDeParte4` | `parte4` elige `propia_ls` con 31 lotes aunque la carpeta no se llame ciudad, y el exacto en comuna. |
| `test_robustez.py`, clase `OrdenNatural` | `L2` antes que `L10`; con `L1..L12` sin ceros la base desempata a favor de `L2`. |
| `test_robustez.py`, clase `LimiteDeTiempo` | Comuna con límite casi 0: `optimo_certificado` False y propuesta válida; sin límite: True y 1574. Ciudad con límite de 5 s: termina en menos de 8 s, sin certificar y con propuesta válida. `propia_ls` con límite 0 devuelve una propuesta factible y sin límite sigue dando 1574 en comuna. |
| `test_robustez.py`, clase `DirectorioActual` | `cargar_instancia("pequena")` y `carpeta_de_instancia("pequena")` (con las fechas de `incidentes.csv`) funcionan tras cambiar el directorio actual. |
| `test_mapa.py`, clase `DatosDelMapa` | Las funciones de datos del mapa coinciden con `evaluar`: cubiertos + no cubiertos = total, conteos, totales, orden natural, lotes libres, CSV y fechas. |
| `test_mapa.py`, clase `DatosParaElNavegador` | `datos_del_mapa` (lo que recibe el navegador) cuenta igual que `evaluar`, marca las estaciones correctas, trae formas y fechas; sin propuesta no marca nada como cubierto. |
| `test_mapa.py`, clase `MapaExportado` | El HTML de comuna trae Leaflet, fuentes y datos dentro (valor 1574, 850 cubiertos, 63 no cubiertos, 7 estaciones), sin recursos de internet salvo teselas; un lote llamado `</script><script>alert(1)</script>` no se convierte en código. |
| `test_mapa.py`, clase `SubcomandoParte4` | `main.py parte4 pequena` imprime "óptimo certificado", la tabla (valor 20) y escribe el mapa; con `--limite 0` dice "no certificada"; una instancia inexistente da un mensaje claro. |
| `test_interfaz.py`, clase `Api` | Servidor real en un puerto libre: lista de instancias, valores intocables por método (pequena 15/19/20/20, comuna 1529/1574/1574 certificado), coherencia con `Modelo.evaluar`, presupuesto y pesos, comparar, exportar, ruta absoluta de carpeta nueva y que un exacto de ciudad no bloquee otros pedidos. |
| `test_interfaz.py`, clase `Validaciones` | Método, presupuesto, pesos y límite inválidos (400), JSON inválido (400), cuerpo de más de 64 KB (413), tipo de contenido (415), instancia inexistente (404), rutas con `../` o carpetas sin los 5 archivos, datos malos con su mensaje, archivos fuera de `web/` (404), cabeceras de seguridad y `Host` ajeno. |
| `test_mapa.py`, `test_json_para_html_separadores_de_linea` | Regresión: un texto con U+2028, U+2029, `</script>` y `&` da JSON válido, igual al original, sin `<` ni separadores crudos y sin crecer de más. |
| `test_notebook.py` | El notebook es JSON nbformat 4, las 10 celdas del enunciado no cambiaron (huella SHA-256), las salidas guardadas no tienen errores ni rutas absolutas, y las celdas rápidas se ejecutan en un espacio limpio con sus `assert` contra los casos del enunciado. |
| `test_js.py` | Corre `node --test` sobre `tests/js/`: formato de cifras (`12.000`, `92,3 %`), lectura de `#instancia=...` con lista blanca y preferencias sin `localStorage`. |

---

## 5. Greedy: por qué sirve y por qué no es óptimo

### Qué es y por qué es buena idea

Un algoritmo **goloso (greedy)** construye la solución tomando en cada paso la decisión que
mejor se ve **ahora**, sin volver atrás. Ventajas:

- Rápido: en ciudad, base y propia tardan ~0,007 s.
- Fácil de explicar y de reproducir a mano.
- Suele dar soluciones buenas: en comuna, base queda a 45 puntos del óptimo (1529 vs 1574).

### Por qué NO garantiza el óptimo

Porque una decisión buena localmente puede impedir una combinación mejor después, y el goloso
nunca deshace. Para cada heurística hay una instancia de máximo 6 nodos en `instancias_malas/`
donde falla (lo exige el enunciado).

Las tres usan los **costos, radios y pesos oficiales** del enunciado (CAI 1000 / 1000 m / 1;
tránsito 2000 / 2000 m / 3; bomberos 5000 / 3000 m / 5); solo cambia el presupuesto. Así nadie
puede decir que el contraejemplo funciona por haber inventado parámetros raros. Cada carpeta
tiene un `README.md` con la traza completa, y `test_instancias_malas` comprueba los valores con
fuerza bruta.

#### 5.1 Instancia mala de `base` (3 nodos, presupuesto 7000)

```text
   [1] <──1000── [0] ──600──> [2]        calles de un solo sentido, salen del nodo 0
   L1             L2           L3
```

Estaciones que aportan algo (salida real de la parte 1 para esta instancia):

| Estación | Costo | Cubre | Valor |
|---|---|---|---|
| L1 hurto | 1200 | hurtos 4, 5, 7, 9 | 4 |
| L1 incendio | 6000 | incendio 6 | 5 |
| L2 hurto | 1500 | hurtos 1, 3, 4, 5, 7, 8, 9, 11 | 8 |
| L2 accidente | 3000 | accidentes 2, 10 | 6 |
| L3 hurto | 1500 | hurtos 1, 3, 8 | 3 |
| L3 accidente | 3000 | accidente 2 | 3 |

Decisión que la desvía: en el paso 1, el mayor valor nuevo es L2 hurto (8). Ocupa el lote L2,
el único cuya estación de tránsito cubre los **dos** accidentes. En el paso 2 L1 hurto y L3 hurto
ya no agregan nada, L1 incendio (6000) no cabe en los 5500 restantes y solo queda L3 accidente
(3). **Base = 11** (costo 4500). Óptimo (fuerza bruta y B&B): L1 hurto + L2 accidente + L3 hurto
= **13** (costo 5700). El error: mirar solo el valor de la siguiente estación y no lo que ese
lote impide construir después.

#### 5.2 Instancia mala de `propia` (6 nodos, presupuesto 5000)

Red dirigida de 13 calles; L2 no cubre nada y el único incendio (peso 5) solo se alcanza desde
L3 o L4.

| Estación | Costo | Cubre | Valor | Razón |
|---|---|---|---|---|
| L1 accidente | 2400 | accidente 5 | 3 | 0,00125 |
| L3 accidente | 1600 | accidente 5 | 3 | 0,001875 |
| L3 incendio | 4000 | incendio 3 | 5 | 0,00125 |
| L4 hurto | 500 | hurtos 1, 2, 4 | 3 | 0,006 |
| L4 accidente | 1000 | accidente 5 | 3 | 0,003 |
| L4 incendio | 2500 | incendio 3 | 5 | 0,002 |

(Más L1 hurto y L3 hurto, que cubren solo el hurto 2.)

Decisión que la desvía: paso 1, la mejor razón es L4 hurto (0,006). Paso 2, entre L3 accidente
(0,001875) y L3 incendio (0,00125) gana la de tránsito, y con eso se ocupa el último lote desde
el que se llegaba al incendio. **propia = 6** (costo 2100). Óptimo: L3 accidente + L4 incendio =
**8** (costo 4100); elegir L3 incendio en el paso 2 también daba 8. El error: la razón
valor/costo no ve que un lote es un recurso escaso.

En esta instancia la base y propia_ls sí llegan a 8.

#### 5.3 Instancia mala de `propia_ls` (6 nodos, presupuesto 6000)

Red dirigida de 15 calles con tres lotes.

| Estación | Costo | Cubre | Valor |
|---|---|---|---|
| L1 hurto | 1000 | hurtos 1, 2, 3, 4, 9, 12 | 6 |
| L1 accidente | 2000 | accidentes 10, 11 | 6 |
| L1 incendio | 5000 | incendios 7, 8 | 10 |
| L2 hurto | 500 | hurtos 3, 9 | 2 |
| L2 incendio | 2500 | incendio 7 | 5 |
| L3 hurto | 1200 | hurtos 3, 9 | 2 |
| L3 incendio | 6000 | incendio 7 | 5 |

El mejor arranque es el goloso base: `[('L1', 'incendio'), ('L2', 'hurto')]`, valor 12, costo
5500. Ningún vecino lo mejora y propia_ls termina ahí. Óptimo: `[('L1', 'accidente'),
('L2', 'incendio'), ('L3', 'hurto')]`: valor **13**, costo 5700.

Por qué propia_ls se atasca: hay que cambiar **a la vez** las dos estaciones (L1 a tránsito y L2
a bomberos). El vecindario más grande quita dos y elige a mano solo **una** nueva; la otra la
pone el relleno goloso por razón, que siempre prefiere el CAI barato del lote libre. Ejemplos
reales: quitar las dos y poner L1 accidente → el relleno pone L2 hurto (2/500 > 5/2500): valor
8. Quitar las dos y poner L2 incendio → el relleno pone L1 hurto (6/1000 > 6/2000): valor 11.

### Por qué el empate y el orden importan

Con mayor estricto (`>`), en un empate gana la **primera** opción en el orden de
`modelo.opciones`. Cambiar el orden o usar `>=` cambiaría qué estación se elige y, por efecto
dominó, todo el resto de la propuesta (y el valor final). El enunciado fija el desempate
(menor código de lote; hurto, accidente, incendio) para que todos los equipos obtengan la
misma salida de la base; por eso `test_base_comuna` puede exigir la lista exacta de 7
estaciones.

Los códigos se comparan en **orden natural** (`clave_de_lote` en `lectura.py`): `L2` antes que
`L10`. Con `L01..L15` (formato con ceros) coincide con el orden de texto, así que la salida de
comuna no cambia. Si el profesor quisiera orden de texto, basta agregar `return codigo` como
primera línea de `clave_de_lote` (ver sección 10).

### Cuándo gana la razón y cuándo el mayor valor

| Instancia | base (mayor valor) | propia (razón) | Quién gana |
|---|---|---|---|
| pequena | 15 | 19 | razón |
| comuna | 1529 | 1492 | mayor valor |
| ciudad | 7591 | 7706 | razón |

- **Gana la razón** cuando el mayor valor está en estaciones caras que se comen el presupuesto
  (pequena: incendio de 5500 por 15 puntos, mientras accidente da 12 por 2200).
- **Gana el mayor valor** cuando hay una estación cara que aporta algo que nada más puede cubrir:
  en comuna, la base construye L09 incendio (155 puntos de los 31 incendios); la razón la
  posterga siempre detrás de estaciones baratas, gasta en pequeñas mejoras (L02 hurto aporta
  solo 12) y termina con 400 sobrantes y 0 incendios cubiertos.

Trazas reales de comuna (estación elegida, costo, valor nuevo):

```text
base ('L15', 'accidente') costo 1700 valor_nuevo 714 razon 0.42
base ('L13', 'hurto') costo 1050 valor_nuevo 240 razon 0.2286
base ('L06', 'hurto') costo 850 valor_nuevo 168 razon 0.1976
base ('L09', 'incendio') costo 4250 valor_nuevo 155 razon 0.0365
base ('L05', 'accidente') costo 1700 valor_nuevo 141 razon 0.0829
base ('L14', 'hurto') costo 800 valor_nuevo 78 razon 0.0975
base ('L08', 'accidente') costo 1600 valor_nuevo 33 razon 0.0206
base fin costo 11950 sobra 50
razon ('L15', 'accidente') costo 1700 valor_nuevo 714 razon 0.42
razon ('L13', 'hurto') costo 1050 valor_nuevo 240 razon 0.2286
razon ('L14', 'hurto') costo 800 valor_nuevo 159 razon 0.1988
razon ('L06', 'hurto') costo 850 valor_nuevo 87 razon 0.1024
razon ('L05', 'accidente') costo 1700 valor_nuevo 141 razon 0.0829
razon ('L09', 'hurto') costo 850 valor_nuevo 34 razon 0.04
razon ('L10', 'accidente') costo 1900 valor_nuevo 66 razon 0.0347
razon ('L03', 'accidente') costo 1800 valor_nuevo 39 razon 0.0217
razon ('L02', 'hurto') costo 950 valor_nuevo 12 razon 0.0126
razon fin costo 11600 sobra 400
```

(Esta traza se obtuvo con un script aparte que llama a `_elegir_siguiente` paso a paso.)

Conclusión: ninguna regla golosa simple domina a la otra. Por eso existe `propia_ls`, que
prueba muchos arranques y corrige con mejora local.

---

## 6. Parte 3: el óptimo exacto

El enunciado pide **garantizar** que no existe una propuesta mejor. Una heurística no puede
garantizarlo. Se necesita un método exacto.

### 6.1 Fuerza bruta

**Qué es.** Probar las `4^n` propuestas (por lote: nada o uno de 3 tipos), descartar las que se
pasan del presupuesto y quedarse con la de mayor valor. Está en `tests/test_exacto.py`,
`fuerza_bruta` / `_probar_todo`:

```python
    mejor = _probar_todo(modelo, codigos, indice + 1, propuesta)
    for tipo in modelo.tipos:
        con_estacion = propuesta + [(codigos[indice], tipo)]
        mejor = max(mejor, _probar_todo(modelo, codigos, indice + 1, con_estacion))
    return mejor
```

- pequena: 4^5 = 1.024 propuestas: instantáneo.
- comuna: 4^15 = 1.073.741.824. Aun a 10^9 propuestas por segundo sería ~1 s, pero en Python
  cada propuesta cuesta mucho más que 1 ns (llama a `evaluar`), así que serían horas o días
  (no se midió; estimación).
- ciudad: 4^80 ≈ 1,46 × 10^48: imposible.

**Su papel: juez de los tests.** No poda nada y mide con `Modelo.evaluar` (sets, no máscaras).
Si el B&B tuviera una poda mal hecha, en alguna instancia chica daría menos que la fuerza bruta
y el test fallaría.

### 6.2 Backtracking

**Qué es.** Recorrer el árbol de decisiones en profundidad. Nivel `i` = decidir el lote `i`.
Cada **nodo** del árbol es una propuesta parcial (decisiones de los lotes `0..i-1`). Las hojas
son propuestas completas.

```text
                         [ ] (nada decidido)
          ┌──────────┬──────────┬──────────┐
       L1 hurto  L1 accid.  L1 incend.  L1 nada          nivel 1: lote L1
        ┌─┬─┬─┐   ...        ...       ┌─┬─┬─┐
       L2 h a i nada                  L2 h a i nada      nivel 2: lote L2
        ...                             ...
```

Con 5 lotes el árbol completo tiene (4^6 - 1) / 3 = 1.365 nodos.

**Podar por presupuesto.** Si una estación no cabe en el presupuesto restante, esa rama ni se
abre (`exacto.py`, `_explorar`):

```python
        if opcion["costo"] > presupuesto_restante:
            busqueda["podas_presupuesto"] += 1
            continue
```

Además se salta una estación que no cubre nada nuevo: construirla solo gastaría, y la rama
"no construir" da el mismo valor con menos costo:

```python
        if opcion["mascara"] & ~cubiertos == 0:
            # No cubre nada nuevo: construirla solo gastaría. La rama
            # "no construir" ya da el mismo valor con menos costo.
            continue
```

La recursión completa (`_explorar`):

```python
        propuesta.append((lote["codigo"], opcion["tipo"]))
        _explorar(busqueda, indice + 1, cubiertos | opcion["mascara"],
                  presupuesto_restante - opcion["costo"], propuesta)
        propuesta.pop()
    # Última rama: no construir nada en este lote.
    _explorar(busqueda, indice + 1, cubiertos, presupuesto_restante, propuesta)
```

`append` / recursión / `pop` es el patrón típico de backtracking: probar, bajar, deshacer.
`cubiertos` es un entero (inmutable), así que no hay que deshacerlo.

### 6.3 Branch & Bound

**Qué agrega.** Antes de abrir un nodo se calcula una **cota superior**: un número que el valor
de **cualquier** propuesta completa que salga de ese nodo no puede superar. Si la cota no supera
a la mejor propuesta ya encontrada, la rama entera se descarta.

```python
def _no_puede_ganar(busqueda, cota, costo_actual):
    """True si con esa cota la rama no puede superar a la mejor propuesta.

    Se poda si la cota es menor que el mejor valor, o si es igual pero ya se
    gastó tanto como la mejor (agregar estaciones solo sube el costo, así que
    no se puede ganar ni por el desempate de menor costo).
    """
    if cota < busqueda["mejor_valor"]:
        return True
    return cota == busqueda["mejor_valor"] and costo_actual >= busqueda["mejor_costo"]
```

#### La cota de mochila, paso a paso con un ejemplo real

Usamos la raíz de `instancias_malas/propia_ls` (nada construido, presupuesto 6000). Código
(`exacto.py`, `_cota_mochila`):

```python
    estaciones = []
    total = modelo.valor_mask(cubiertos)
    for lote in lotes[indice:]:
        for opcion in lote["opciones"]:
            ganancia = modelo.valor_mask(opcion["mascara"] & ~cubiertos)
            if ganancia == 0:
                continue
            if opcion["costo"] <= 0:
                total += ganancia
                continue
            # La razón en float solo ORDENA; con números de este tamaño dos
            # razones distintas nunca se confunden, y empates no cambian la cota.
            estaciones.append((ganancia / opcion["costo"], ganancia, opcion["costo"]))
    estaciones.sort(reverse=True)
    capacidad = presupuesto_restante
    for razon, ganancia, costo in estaciones:
        if costo <= capacidad:
            total += ganancia
            capacidad -= costo
        else:
            total += (ganancia * capacidad) // costo
            break
    return total
```

**(a) Ganancia marginal de cada opción restante** (respecto a lo cubierto, aquí nada):

| Estación | Ganancia | Costo | Razón |
|---|---|---|---|
| L1 hurto | 6 | 1000 | 0,0060 |
| L2 hurto | 2 | 500 | 0,0040 |
| L1 accidente | 6 | 2000 | 0,0030 |
| L1 incendio | 10 | 5000 | 0,0020 |
| L2 incendio | 5 | 2500 | 0,0020 |
| L3 hurto | 2 | 1200 | 0,0017 |
| L3 incendio | 5 | 6000 | 0,0008 |

**Llenar la mochila fraccional** con capacidad 6000, en orden de razón (a igual razón, primero
la de mayor ganancia, porque se ordenan tuplas `(razón, ganancia, costo)`):

```text
L1 hurto     1000  -> total  6, capacidad 5000
L2 hurto      500  -> total  8, capacidad 4500
L1 accidente 2000  -> total 14, capacidad 2500
L1 incendio  5000 no cabe: pedazo = (10 * 2500) // 5000 = 25000 // 5000 = 5 -> total 19
```

Cota = **19**. Verificado con la traza real del B&B: `cota_mochila=19` en la raíz. El óptimo
es 13; la cota es una sobreestimación, como debe ser.

**(b) Por qué la suma de marginales sobreestima (submodularidad).** L1 hurto cubre
{1, 2, 3, 4, 9, 12} y L2 hurto cubre {3, 9}. La cota les cuenta 6 + 2 = 8, pero juntas cubren
{1, 2, 3, 4, 9, 12}: valor 6. Los hurtos 3 y 9 se contaron dos veces. Esto es la
**submodularidad**: lo que agrega una estación nunca aumenta al agregar otras antes (si ya
tengo L1 hurto, L2 hurto agrega 0). Por eso la suma de ganancias por separado siempre
es `>=` que la ganancia conjunta, nunca menor.

**(c) Relajación de mochila fraccional.** La cota resuelve un problema "más fácil" (relajado):

1. Usa ganancias separadas (sobreestima, por (b)).
2. Ignora la regla "un lote, una estación" (en el ejemplo usa L1 hurto, L1 accidente y un pedazo
   de L1 incendio a la vez).
3. Permite comprar una fracción de una estación.

Quitar o aflojar restricciones solo puede hacer que el máximo **suba** (todas las soluciones
del problema original siguen siendo válidas en el relajado). Y la mochila fraccional se resuelve
de forma **óptima** con el greedy por razón (resultado clásico; argumento corto: si la mochila
óptima tuviera menos de un objeto de mejor razón y más de uno de peor razón, cambiar un poco de
peso del peor al mejor no baja el valor).

**(d) Por qué se redondea hacia abajo con enteros.** El valor real de una propuesta es siempre
un **entero** (suma de pesos enteros). Si la cota real fuera 20,7, ninguna propuesta puede
valer 21, así que 20 sigue siendo cota. `(ganancia * capacidad) // costo` calcula la fracción
redondeada hacia abajo **sin floats**. Una cota más baja (pero válida) poda más.

**(e) Prueba de que la cota nunca poda un óptimo.** Sea un nodo con lo cubierto `C` y
presupuesto restante `R`, y sea `S` cualquier conjunto de estaciones de los lotes restantes con
costo total `<= R`. Entonces:

```text
valor(C ∪ S)  =  valor(C) + ganancia conjunta de S sobre C
             <=  valor(C) + Σ_{s ∈ S} ganancia(s sobre C)          (submodularidad, b)
             <=  valor(C) + óptimo de la mochila 0/1 con esas ganancias y capacidad R
             <=  valor(C) + óptimo de la mochila fraccional         (relajación, c)
             =   cota real (con decimales)
```

y como `valor(C ∪ S)` es entero, también es `<=` la cota redondeada hacia abajo (d). Por lo
tanto, si `cota < mejor_valor`, ninguna completación supera a la mejor: podar no pierde nada.
Si `cota == mejor_valor` y `costo_actual >= mejor_costo`, cualquier completación vale a lo sumo
lo mismo y cuesta al menos lo mismo, así que no gana ni por el desempate de menor costo.

Detalle honesto: el orden se hace con razones `float`. El comentario del código argumenta que
con números de este tamaño el orden es correcto; no se demostró formalmente aquí.

#### Cota barata previa

`exacto.py`, `_hay_que_podar`:

```python
    # Cota barata: aunque construyeramos todo lo que queda, no se puede
    # cubrir más que la unión de coberturas de los lotes restantes.
    todo_lo_alcanzable = cubiertos | busqueda["alcanzable"][indice]
    if _no_puede_ganar(busqueda, modelo.valor_mask(todo_lo_alcanzable), costo_actual):
        return True
    cota = _cota_mochila(modelo, busqueda["lotes"], indice, cubiertos, presupuesto_restante)
    return _no_puede_ganar(busqueda, cota, costo_actual)
```

`alcanzable[i]` se precalcula una vez (`_alcanzable_desde`): la unión de todas las coberturas de
los lotes `i, i+1, ...`. Es válida (no se puede cubrir más que todo lo cubrible) e ignora el
presupuesto. Cuesta un `|` y un `valor_mask`, mucho menos que ordenar estaciones. Ninguna de las
dos cotas domina siempre: en la raíz de la instancia mala de propia_ls, la barata da 22 y la de
mochila 19; en el nodo `[('L1', 'hurto')]` de esa misma instancia, la barata da 11 y la de
mochila 13 (traza real).

#### Opciones dominadas

`exacto.py`, `_esta_dominada`:

```python
        cubre_todo = (candidata["mascara"] | otra["mascara"]) == otra["mascara"]
        no_cuesta_mas = otra["costo"] <= candidata["costo"]
```

`A | B == B` significa que todo bit de A está en B (B cubre todo lo de A). Si además B, **del
mismo lote**, no cuesta más, A está dominada: en cualquier propuesta con A se puede poner B en
su lugar (mismo lote, así no se viola la regla de un lote), el valor no baja y el costo no sube.
Descartar A es seguro. Si son idénticas se conserva la primera. En ciudad quedan 233 opciones
útiles de 240; en pequena y comuna no se descarta ninguna (15 y 45).

#### Orden de exploración

`_preparar_lotes` ordena los lotes por "potencial" (el mayor valor de una estación del lote) de
mayor a menor, y `_opciones_utiles` ordena las estaciones de cada lote por valor/costo. El
**árbol es el mismo** con cualquier orden; solo cambia cuándo se encuentran propuestas buenas.
Encontrarlas pronto sube `mejor_valor` y la poda corta más. Afecta el **tiempo**, no el
resultado (salvo cuál de varias propuestas empatadas se reporta).

#### Arranque con la heurística (warm start)

`exacto.py`, `resolver`:

```python
    arranque = propia_ls(modelo, _tiempo_restante(inicio, limite_segundos))
```

y `mejor_valor` empieza en `arranque["valor"]` (el segundo argumento es la parte del límite de
tiempo que queda; sin límite es `None`, ver 6.6). Sin esto, la primera comparación sería contra 0
y casi nada se podaría al principio. En pequena y comuna el arranque **ya es el óptimo**
(`valor_arranque` 20 y 1574): el B&B no encuentra nada mejor, su trabajo es **demostrar** que no
existe nada mejor. En la instancia mala de propia_ls, el arranque es 12 y el B&B encuentra 13.

#### Regla de desempate

Docstring de `exacto.py`: mayor valor; si empata, menor costo; si también, la primera
encontrada (la del arranque o la primera en el orden fijo). Implementado en `_considerar`:

```python
    mejora_valor = valor > busqueda["mejor_valor"]
    mismo_valor_mas_barato = valor == busqueda["mejor_valor"] and costo_actual < busqueda["mejor_costo"]
```

#### Traza real del B&B en `instancias_malas/propia_ls`

Orden de lotes: L1, L2, L3. Arranque: 12 con costo 5500 (salida de un script que envuelve
`_explorar` y `_hay_que_podar` para imprimir):

```text
nodo nivel=0 prop=[] valor=0 restante=6000 mejor=12/5500
   cota_barata=22 cota_mochila=19 -> sigue
  nodo nivel=1 prop=[('L1', 'hurto')] valor=6 restante=5000 mejor=12/5500
     cota_barata=11 cota_mochila=13 -> PODA
  nodo nivel=1 prop=[('L1', 'accidente')] valor=6 restante=4000 mejor=12/5500
     cota_barata=13 cota_mochila=14 -> sigue
    nodo nivel=2 prop=[('L1', 'accidente'), ('L2', 'hurto')] valor=8 restante=3500 mejor=12/5500
       cota_barata=13 cota_mochila=10 -> PODA
    nodo nivel=2 prop=[('L1', 'accidente'), ('L2', 'incendio')] valor=11 restante=1500 mejor=12/5500
       cota_barata=13 cota_mochila=13 -> sigue
      nodo nivel=3 prop=[('L1', 'accidente'), ('L2', 'incendio'), ('L3', 'hurto')] valor=13 restante=300 mejor=12/5500
      nodo nivel=3 prop=[('L1', 'accidente'), ('L2', 'incendio')] valor=11 restante=1500 mejor=13/5700
    nodo nivel=2 prop=[('L1', 'accidente')] valor=6 restante=4000 mejor=13/5700
       cota_barata=13 cota_mochila=10 -> PODA
  nodo nivel=1 prop=[('L1', 'incendio')] valor=10 restante=1000 mejor=13/5700
     cota_barata=12 cota_mochila=12 -> PODA
  nodo nivel=1 prop=[] valor=0 restante=6000 mejor=13/5700
     cota_barata=7 cota_mochila=10 -> PODA
[('L1', 'accidente'), ('L2', 'incendio'), ('L3', 'hurto')] 13 {'nodos': 10, 'podas_presupuesto': 1, 'podas_cota': 5, 'valor_arranque': 12}
```

Lectura: en el nodo de nivel 3 `L1 accidente + L2 incendio + L3 hurto` (valor 13) ya se
decidieron los tres lotes; `_considerar` lo guarda como nuevo mejor (13/5700) y la rama
termina. Desde ahí todas las ramas que quedan se podan: por ejemplo, `L1 incendio` vale 10 y
solo le quedan 1000, así que ninguna de sus completaciones pasa de 12. La única poda por
presupuesto es L3 incendio (6000) en el nodo `L1 accidente + L2 incendio`, que no aparece
como nodo porque se descarta antes de bajar. Con 10 nodos se recorrió un árbol que completo
tiene (4^4 - 1) / 3 = 85.

### 6.4 Evidencia de correctitud

Tests en `tests/test_exacto.py` que comparan contra la fuerza bruta independiente:

- `test_pequena_optimo`: 20 = fuerza bruta, y además la propuesta y el costo del enunciado.
- `test_instancias_malas`: en las 3 instancias malas, B&B = fuerza bruta y la heurística queda
  por debajo.
- `test_treinta_instancias_aleatorias`: 30 instancias de 4 a 7 nodos con aristas y
  presupuestos al azar (semilla fija): B&B = fuerza bruta en todas.
- `test_comuna_optimo`: comuna es muy grande para fuerza bruta; solo se comprueba que 1574 es
  válido según `evaluar` y `>=` que las heurísticas.

**Qué demuestra:** que en esas 34 instancias chicas el B&B no podó ningún óptimo, y que
el valor de comuna corresponde a una propuesta válida.

**Qué NO demuestra:** un test no es una prueba. No garantiza que no exista una instancia
donde falle. La garantía viene del **argumento** de 6.3 (e) más las podas seguras (presupuesto,
opciones dominadas, estaciones sin aporte). Los tests dan confianza en que el código
**implementa** ese argumento sin errores.

### 6.5 Estadísticas reales de comuna

Salida real de `py main.py parte3 comuna` (la segunda línea, `a 10^9 propuestas...`, y la
última, `optimo_certificado=True (...)`, se omiten aquí; las estadísticas no cambiaron al agregar
el límite de tiempo):

```text
espacio completo = 4^15 = 1073741824
estaciones=[('L03', 'accidente'), ('L06', 'hurto'), ('L09', 'hurto'), ('L11', 'hurto'), ('L13', 'accidente'), ('L14', 'hurto'), ('L15', 'incendio')]
costo_total=11700
casos_cubiertos={'hurto': 519, 'accidente': 300, 'incendio': 31}
valor=1574
tiempo_s=0.6545
estadisticas_bb={'nodos': 41493, 'podas_presupuesto': 2283, 'podas_cota': 29799, 'valor_arranque': 1574}
```

- **nodos = 41.493**: llamadas a `_explorar`. El árbol completo tiene (4^16 - 1) / 3 =
  1.431.655.765 nodos: se visitó ≈ 0,003 % de él.
- **podas_presupuesto = 2.283**: estaciones que no cabían en el presupuesto restante.
- **podas_cota = 29.799**: nodos donde la cota barata o la de mochila mostró que la rama no
  podía ganar. Es la poda que más trabaja: cada una elimina un subárbol entero.
- **valor_arranque = 1574**: propia_ls ya traía el óptimo; el B&B lo **certifica**.
- Tiempo: 0,59 s en `tabla` y 0,65 s en `parte3` (varía entre ejecuciones).

**Por qué el tiempo pasó de 339 s a 0,6 s.** Según el historial del desarrollo (dato del equipo,
**no reproducible con el código actual**, porque esa versión ya no existe), una versión previa
calculaba la cota con `Fraction` (fracciones exactas, lentas) y tardaba unos 339 s. El código
actual usa enteros con `//` para la fracción, la cota barata `alcanzable` antes de la de
mochila, opciones dominadas, el orden por potencial y el arranque con propia_ls. Lo que sí está
medido aquí es el tiempo actual (~0,6 s).

### 6.6 Por qué no se calcula el óptimo de ciudad

Lo que **sí** se sabe (calculado con enteros por `tamanio_del_espacio` de `main.py`):

- 80 lotes, 4 opciones cada uno: 4^80 = 1461501637330902918203684832716283019655932542976
  propuestas.
- A 10^9 propuestas por segundo: ≈ 4,63 × 10^31 años.
- La cota en la raíz de ciudad es 14.236 (mochila) y 9.800 (todo lo alcanzable), frente a
  7.827 de propia_ls: la brecha inicial es grande, lo que sugiere que la poda tendría mucho
  trabajo.

Lo que **no** se sabe: el B&B poda, así que no recorre los 4^80 nodos. Podría terminar en un
tiempo razonable o no; no hay garantía, porque en el peor caso el B&B es exponencial. Por eso
`parte3` corre con límite de tiempo (`--limite`, por defecto 60 s).

#### El límite de tiempo es real de extremo a extremo

**Qué es.** `resolver(modelo, limite_segundos)` promete terminar en unos `limite_segundos`
contando **todo**: el arranque con `propia_ls` y el B&B.

**Por qué hizo falta.** El arranque `propia_ls` tarda unos 20 s en ciudad. Antes solo el B&B
miraba el reloj, así que con `--limite 3` el programa tardaba ~25 s: primero los 20 s
completos de `propia_ls` y después el B&B se cortaba en su primer nodo. Un límite que no se
cumple no sirve en la feria ni en la interfaz.

**Cómo se ve en el código.** `propia_ls` acepta `limite_segundos` y lo convierte en un
**plazo** (el instante en que hay que parar). Una función mira el reloj:

```python
def _se_acabo_el_tiempo(plazo):
    """True si hay un plazo (instante de time.perf_counter) y ya pasó.

    `plazo` None significa "sin límite": nunca se acaba el tiempo.
    """
    if plazo is None:
        return False
    return time.perf_counter() >= plazo
```

Se consulta entre arranques (`_mejor_arranque`), entre vecinos (`_mejor_entre`), antes de
armar los dobles cambios (`_mejor_vecino`) y entre vueltas de mejora (`_mejora_local`):

```python
    actual = propuesta
    while not _se_acabo_el_tiempo(plazo):
        vecino = _mejor_vecino(modelo, actual, plazo)
        if vecino is None:
            return actual
        actual = vecino
    return actual
```

Al cortar se devuelve la mejor propuesta hallada hasta ese momento, y **siempre es factible**:
toda propuesta por la que pasa `propia_ls` es completa y válida (los vecinos ya se filtran
por lote libre y presupuesto) y al final pasa por `Modelo.evaluar`. `resolver` le pasa a
`propia_ls` solo el tiempo que queda (`exacto.py`, `_tiempo_restante`):

```python
    if limite_segundos is None:
        return None
    gastado = time.perf_counter() - inicio
    return max(0, limite_segundos - gastado)
```

Si el arranque se gasta todo el tiempo, el B&B se corta en su primer nodo y el resultado es
el del arranque con `optimo_certificado=False`. **Sin límite nada cambia**: `plazo` es `None`,
`_se_acabo_el_tiempo` devuelve siempre `False` y los valores son los mismos de siempre (lo
comprueban `test_sin_limite_certifica`, `test_propia_ls_con_limite_es_factible` y la tabla de
la sección 9).

**Ejecutado** (en esta máquina; los tiempos varían):

| Comando | Tiempo | Valor | Certificado |
|---|---|---|---|
| `py main.py parte3 ciudad --limite 5` | 5,00 s | 7803 | no |
| `py main.py parte3 ciudad --limite 20` | 20,00 s | 7827 | no |
| `resolver` con límite 0 (script aparte) | 0,02 s | 7706 (el goloso por razón) | no |

Salida real de `py main.py parte3 ciudad --limite 20` (sin las dos primeras líneas ni la
lista de estaciones):

```text
costo_total=40000
casos_cubiertos={'hurto': 1768, 'accidente': 1798, 'incendio': 133}
valor=7827
tiempo_s=20.0017
estadisticas_bb={'nodos': 1, 'podas_presupuesto': 0, 'podas_cota': 0, 'valor_arranque': 7827}
optimo_certificado=False (se cortó a los 20.0 s: es la mejor propuesta encontrada, no necesariamente el óptimo)
```

Con 20 s, `propia_ls` alcanza a llegar a 7827 y el B&B solo visita 1 nodo. Con 5 s la mejora
local se corta antes y queda en 7803. La propuesta devuelta nunca es peor que el arranque,
pero **no** está certificada como óptima.

Cómo se corta el B&B (`exacto.py`): `_explorar` mira el reloj en el nodo 1, 1001, 2001...
(`NODOS_ENTRE_REVISIONES_DEL_RELOJ = 1000`); si se pasó el límite marca
`cortada_por_tiempo` y todas las llamadas pendientes regresan sin explorar más.

---

## 7. Por qué estos métodos y no otros

| Decisión | Alternativa descartada | Razón |
|---|---|---|
| Dijkstra con corte desde cada lote | BFS | BFS ignora longitudes. |
| | Bellman-Ford | Solo necesario con pesos negativos; O(V·E). |
| | Floyd-Warshall | O(V^3) y matriz V×V con 27.568 nodos; además solo interesan 80 orígenes. |
| | networkx | Prohibido por el enunciado. |
| Máscaras de bits (enteros) | `set` de ids | Más lento y hay que copiar; la máscara une con `|` y es inmutable. `evaluar` sí usa `set` a propósito, para ser independiente. |
| Distancias enteras (décimas de m) | `float` | 18.431 de 34.810 distancias de comuna salen inexactas en float; en ciudad hay 8 casos exactamente en el borde. |
| `Decimal` + `ROUND_HALF_UP` | `round()` | Redondeo bancario y error del float (1000,5 -> 1000). |
| Backtracking + B&B | Fuerza bruta | 4^15 ≈ 10^9 en comuna; se usa solo como juez de los tests. |
| | Programación dinámica | Ver abajo. |
| | Programación entera (solver) | Requiere librerías externas (PuLP, OR-Tools...) que no están en la lista permitida; además el curso pide implementar el algoritmo. |
| Greedy con puntajes | Aleatorizado / metaheurísticas (genético, recocido) | Mejora local determinista: misma salida siempre, se explica y se depura fácil; un genético tiene muchos parámetros y resultados que varían. |
| `evaluar` independiente | Confiar en lo que calcula cada heurística | Un solo árbitro valida reglas y detecta errores de máscaras. |

### Por qué no programación dinámica

La mochila 0/1 se resuelve con DP porque el estado `(objeto i, presupuesto usado)` basta: el
valor de agregar un objeto **no depende** de los otros. Aquí sí depende: lo que agrega una
estación depende de **qué incidentes ya están cubiertos**. El estado tendría que incluir el
conjunto cubierto, y hay 2^I conjuntos posibles (2^913 en comuna). Además el presupuesto en
millones da miles de valores. La DP clásica no aplica directamente.

### Relación con lo visto en clase

| Paradigma | Dónde se usa | Para qué |
|---|---|---|
| Fuerza bruta | `tests/test_exacto.py`, `fuerza_bruta` | Oráculo: verdad de referencia en instancias chicas. |
| Backtracking | `exacto.py`, `_explorar` | Recorrer el árbol de decisiones con poda por presupuesto. |
| Branch & Bound | `exacto.py`, `_hay_que_podar` + `_cota_mochila` | Backtracking con cotas para cortar ramas. |
| Greedy | `heuristicas.py`, `goloso` | base, propia y el relleno de propia_ls. |
| Búsqueda local | `heuristicas.py`, `_mejora_local` | Corregir decisiones del greedy. |

### Por qué la heurística propia elegida

- `propia` (razón) es la idea más simple que mejora a la base en al menos una instancia
  (pequena y ciudad), que es lo que pide el enunciado 2.2.
- `propia_ls` existe porque la razón sola falla en comuna. Es la que se usa como arranque del
  B&B y la recomendable para ciudad (7827, la mejor de las tres).

---

## 8. Complejidad

Variables: `V` nodos, `E` aristas, `L` lotes, `I` incidentes, `T` tipos (3), `O = L·T` opciones,
`k` estaciones en una propuesta (`k <= L`), `w` = tamaño de palabra (64). Las operaciones
sobre máscaras cuestan O(I / w) cada una (en la práctica, muy poco).

| Componente | Complejidad | Comentario |
|---|---|---|
| Lectura | O(V + E + L + I) | Una pasada por archivo. |
| Dijkstra por lote | O((V' + E') log V') | V', E' = lo que está dentro del corte; peor caso O((V+E) log V). |
| Todos los Dijkstra | L × lo anterior | Ciudad: lectura 0,29 s + modelo 0,21 s medidos. |
| Coberturas | O(L · I) | Para cada lote y tipo se recorren los incidentes de ese tipo. |
| `valor_mask` | O(T · I / w) | |
| Un paso del goloso | O(k + O · T · I / w) | `resumir` + revisar todas las opciones. |
| Goloso completo | O(k · O · T · I / w) | Como mucho `k <= L` pasos. |
| `_mejor_arranque` | O(O) golosos completos | Uno por cada estación forzada como primera. |
| Mejora local, una iteración | O((k·O + k² + k²·O) golosos completos) | Reemplazos + quitar 1-2 + dobles cambios; cota aproximada. |
| Mejora local, total | iteraciones × lo anterior | No hay cota polinomial demostrada del número de iteraciones; termina porque cada salto mejora estrictamente (valor, -costo). Ciudad: entre 20 y 35 s medidos según el equipo. |
| `_cota_mochila` | O(O · T · I / w + O log O) | Ganancias + ordenar. |
| B&B peor caso | O(4^L) nodos × costo de la cota | Exponencial: sin podas recorre todo el árbol. |
| B&B en la práctica | 51 nodos (pequena), 41.493 (comuna) | Las podas eliminan casi todo el árbol en estas instancias. |
| Fuerza bruta | O(4^L · L · I) | Solo instancias chicas. |

El peor caso del B&B es exponencial porque se pueden construir instancias donde la cota casi
nunca alcanza para podar (por ejemplo, muchas estaciones con valores y costos parecidos). Que
en la práctica pode tanto es una observación de estas instancias, no una garantía.

---

## 9. Resultados

### Tabla comparativa

Salida real de `py main.py tabla` (tiempos en segundos; varían entre ejecuciones). Los tiempos
de cada método **no incluyen** el precálculo del `Modelo` (lectura + Dijkstra + costos: menos de
1 s en ciudad), que se hace una sola vez por instancia; el notebook lo mide aparte:

```text
instancia=pequena
  base: valor=15 tiempo_s=0.0000
  propia: valor=19 tiempo_s=0.0000
  propia_ls: valor=20 tiempo_s=0.0007
  optimo: valor=20 tiempo_s=0.0009
instancia=comuna
  base: valor=1529 tiempo_s=0.0002
  propia: valor=1492 tiempo_s=0.0003
  propia_ls: valor=1574 tiempo_s=0.0490
  optimo: valor=1574 tiempo_s=0.5917
instancia=ciudad
  base: valor=7591 tiempo_s=0.0097
  propia: valor=7706 tiempo_s=0.0089
  propia_ls: valor=7827 tiempo_s=20.0672
  optimo: no calculado (espacio 4^80; ver py main.py parte3 ciudad)
```

| Instancia | base | propia | propia_ls | óptimo |
|---|---|---|---|---|
| pequena | 15 (0,0000 s) | 19 (0,0000 s) | 20 (0,0007 s) | 20 (0,0009 s) |
| comuna | 1529 (0,0002 s) | 1492 (0,0003 s) | 1574 (0,05 s) | 1574 (0,59 s) |
| ciudad | 7591 (0,01 s) | 7706 (0,009 s) | 7827 (20 a 35 s) | no calculado |

Nota: los tiempos de la tabla no incluyen leer la instancia ni construir el `Modelo` (eso se
hace antes de medir).

### Mejores propuestas

**pequena** (óptimo, coincide con el enunciado):

```text
estaciones=[('L1', 'hurto'), ('L3', 'accidente'), ('L4', 'hurto')]
costo_total=5400
casos_cubiertos={'hurto': 8, 'accidente': 4, 'incendio': 0}
valor=20
```

**comuna** (óptimo): L03 accidente, L06 hurto, L09 hurto, L11 hurto, L13 accidente, L14 hurto,
L15 incendio; costo 11700 de 12000; casos 519 / 300 / 31; valor 1574.

**ciudad** (mejor heurística, propia_ls): valor 7827. Base: 20 estaciones, costo 39850, casos
1350 / 1757 / 194. Propia: 23 estaciones, costo 39950, casos 1887 / 1718 / 133.

### Interpretación

- **Propia pierde contra base en comuna** (1492 vs 1529): nunca construye bomberos (ver la
  traza de la sección 5). Los 31 incendios valen 155 y solo se cubren con una estación cara
  (L09 incendio, 4250); la razón la deja para el final y entonces ya no cabe.
- **El óptimo de comuna sí cubre los 31 incendios**, pero con L15 incendio en vez de L09, y
  combina 4 CAI y 2 de tránsito: menos accidentes que propia (300 vs 320) pero incluye los 155
  puntos de incendio.
- **propia_ls alcanza el óptimo** en pequena y comuna porque el multi-arranque prueba cada
  primera estación (incluidas las de incendio) y la mejora local cambia estaciones de a una o
  dos.
- **Distancia al óptimo:** en comuna, base queda a 45 puntos (2,9 %) y propia a 82 (5,2 %).
  En ciudad no se conoce el óptimo: solo se sabe que está entre 7827 y 9800 (la cota
  `alcanzable` de la raíz; la de mochila, 14.236, es más floja allí).

---

## 10. Qué cambiar si los datos cambian en la sustentación

El enunciado dice que en la sustentación entregan **nuevos lotes e incidentes** con el mismo
formato. Todo lo de esta sección se **ejecutó** con instancias temporales (copias modificadas de
`pequena` en una carpeta fuera del proyecto), salvo que se diga otra cosa.

### Nada está escrito a mano en el código

Radios, costos base, pesos y presupuesto se leen de `parametros.json`; lotes e incidentes de sus
CSV. Comprobado: no hay valores de las instancias en `estaciones/`. Las únicas cosas fijas son:

- Los nombres de tipos `("hurto", "accidente", "incendio")` en `modelo.py` (`TIPOS`), pero solo
  para el **orden**; un tipo extra en el JSON se agrega al final (`_tipos_en_orden`).
- `main.py`: `tabla` recorre las tres instancias conocidas y salta el exacto con más de 30
  lotes (`LOTES_MAXIMOS_PARA_EXACTO_EN_TABLA`); `parte3` usa un límite de tiempo
  (`--limite`, por defecto 60 s); `parte4` usa `propia_ls` si la carpeta se llama `ciudad` y el
  exacto en cualquier otra (se cambia con `--metodo`).

### Si piden X, toco Y

| Si piden... | Qué hago | Qué pasó al probarlo |
|---|---|---|
| Correr con datos nuevos | `py main.py parte2 C:\ruta\nueva base` (carpeta con los 5 archivos) | Funciona con cualquier ruta. |
| Otro presupuesto | Editar `presupuesto_millones` en el JSON, o en Python `Modelo(instancia, presupuesto=9000)` | Ver filas siguientes. |
| Otros pesos | Editar `peso` en el JSON, o `Modelo(instancia, pesos={"accidente": 4})` | Pesos todos 1 en pequena: base 11, propia 12, propia_ls 12, óptimo 12. |
| Otro radio o costo base | Editar `radio_m` / `costo_base` en el JSON | Presupuesto 9000 + incendio 3000 + peso accidente 4: base 35, propia 36, propia_ls 36, óptimo 36. |
| Radio con decimales | Nada: la escala se ajusta sola | Radio hurto 920.5: escala pasó a 10; L1 hurto = [7, 12, 13]. |
| Distancia exactamente igual al radio | Nada: se cubre (`<=`) | Radio hurto 920 (= distancia 1 -> 4): L1 hurto = [7, 12, 13]; con 919: [7]. |
| Presupuesto 0 | Nada | Las 4 respuestas: propuesta vacía, valor 0. |
| Presupuesto 10 veces mayor | Nada | pequena con 60000: base 38, propia 40, propia_ls 41 = óptimo 41 (0,002 s). comuna con 120000: óptimo 1669 en 0,25 s (3.758 nodos), base 1630. |
| Un lote nuevo | Agregar una fila a `lotes.csv` | L6 en nodo 4, factor 0.5: costos 500/1000/2500; óptimo pasó a 27 (`L1 accidente` + `L6 incendio`, costo 4700). |
| Lote en nodo sin salidas (inalcanzable) | Nada | L6 en un nodo 9 sin aristas: coberturas `[[], [], []]`; nunca se elige; resultados iguales. |
| Lote en nodo que no existe | Corregir el CSV | Error claro: `lotes.csv: el lote 'L6' usa el nodo 99, que no existe en nodos.csv` (mensaje actual; la prueba original se hizo con el mensaje anterior). |
| Código de lote, id de incidente o id de nodo repetido | Corregir el CSV (renombrar o renumerar) | Error claro que nombra archivo, valor y líneas (tests de la clase `Duplicados`). |
| Códigos sin ceros (`L1..L12`) | Nada: orden natural, `L2` antes que `L10` | Test `test_base_desempata_por_orden_natural`. |
| Incidentes duplicados en el mismo nodo | Nada (ids distintos) | 2 hurtos más en el nodo 3: L2 hurto = [9, 10, 11, 12, 13, 19, 20]; óptimo 22. |
| Sin incidentes de un tipo | Nada | Sin incendios en pequena: base 18, propia 19, propia_ls 20, óptimo 20. |
| Sin ningún incidente | Nada | Todo vacío, valor 0. |
| Coma decimal (`367,9`) o tipo `"Hurto "` | Nada | Se normalizan al leer (tests de la clase `DatosEscritosAMano`). |
| Tipo de incidente desconocido | Agregar el tipo al JSON | Error claro: `Tipo de incidente sin parámetros: robo`. |
| Columna faltante o mal escrita | Corregir el CSV | Error claro: `lotes.csv: falta la columna factor_zona`. |
| Falta un parámetro | Corregir el JSON | Error claro: `parametros.json: falta tipos.hurto.peso`. |
| Longitud no numérica | Corregir el CSV | Error claro: `Distancia no numérica: 'abc'`. |
| Factor que produce una mitad | Nada | Factor 1.0005: costo 1001 (half-up); `round()` daría 1000. |
| Instancia nueva grande (muchos lotes) con `parte3` | `py main.py parte3 <ruta> --limite 30` | Se corta en el límite y dice `optimo_certificado=False` (probado con ciudad, 20 s). |

### Riesgos encontrados al probar (ya corregidos)

1. **Códigos de lote repetidos.** Antes la lectura los aceptaba y daba resultados incoherentes.
   Ahora `cargar_instancia` falla con `ValueError` que nombra el código y las líneas. Lo mismo
   para ids de incidente y de nodo repetidos.
2. **Orden de códigos como texto.** Antes `L10` iba antes que `L2`. Ahora se usa orden natural
   (`clave_de_lote`); para volver al de texto, agregar `return codigo` como primera línea.
3. **`parte3` decidía por el nombre `ciudad`.** Ahora decide por tiempo: cualquier instancia
   corre con límite y se informa si el óptimo quedó certificado.
4. **Directorio de trabajo.** Antes `pequena` solo se encontraba desde la carpeta del proyecto.
   Ahora se busca en `instancias/` junto al paquete `estaciones`. Las rutas relativas que pase
   el usuario (como `instancias_malas/base`) siguen siendo relativas a la carpeta actual.
5. **El límite de tiempo del exacto no se cumplía.** El arranque `propia_ls` (~20 s en ciudad)
   no miraba el reloj: con `--limite 3` se tardaba ~25 s. Ahora el límite cuenta de extremo a
   extremo (sección 6.6): con `--limite 5` en ciudad termina en 5,0 s.
6. **Dos reglas para encontrar la carpeta de una instancia.** El mapa tenía su propia copia,
   que buscaba `instancias/` en el directorio actual. Ahora todos usan
   `lectura.carpeta_de_instancia`.

### Qué haría con 1.000 lotes

No se probó. Lo que se puede decir: la lectura y los Dijkstra crecen lineal en lotes (cada uno
cortado en 3 km). La base y la propia siguen siendo rápidas. `propia_ls` hace un goloso completo
por cada una de las 3.000 opciones en el arranque, y su mejora local revisa vecindarios
cuadráticos; con 240 opciones (ciudad) ya tarda ~20 s, así que con 3.000 tardaría mucho más
(estimación, no medida). El B&B no es viable sin garantía de terminar.

---

## 11. Banco de preguntas de sustentación

### Problema y modelo

> **Pregunta típica:** ¿Qué problema están resolviendo?
>
> **Cómo responder:** Cobertura máxima con presupuesto: elegir a lo sumo una estación por lote,
> sin pasar el presupuesto, para maximizar la suma de pesos de los incidentes cubiertos. Se
> parece a la mochila, pero el valor no es aditivo porque un incidente cubierto dos veces
> cuenta una vez.

> **Pregunta típica:** ¿Qué pasa con dos estaciones que cubren el mismo incidente?
>
> **Cómo responder:** Cuenta una sola vez (regla 5). En código, las coberturas son máscaras de
> bits y se unen con `|`: un bit no puede valer 2. En pequena, L1 accidente (12) y L3
> accidente (12) juntas valen 15, no 24.

> **Pregunta típica:** ¿Por qué el problema es difícil?
>
> **Cómo responder:** 4^n propuestas: 4^15 ≈ 1,07 × 10^9 en comuna y 4^80 ≈ 1,46 × 10^48 en
> ciudad. Es de la familia de problemas NP-difíciles (dato de referencia).

> **Pregunta típica:** ¿Por qué no es simplemente una mochila?
>
> **Cómo responder:** En la mochila, cada objeto tiene un valor fijo. Aquí el valor de una
> estación depende de las otras elegidas (solapamiento).

### Distancias y grafo

> **Pregunta típica:** ¿Por qué Dijkstra?
>
> **Cómo responder:** Necesitamos el camino más corto en metros, en un grafo dirigido con pesos
> no negativos. Dijkstra es el algoritmo para eso. BFS ignora pesos, Bellman-Ford es para pesos
> negativos y más lento, Floyd-Warshall es V^3 con 27.568 nodos.

> **Pregunta típica:** ¿Por qué `<=` y no `<`?
>
> **Cómo responder:** La regla 4 dice "menor o igual al radio". Y no es teórico: en ciudad hay
> 8 pares lote-incidente exactamente a la distancia del radio.

> **Pregunta típica:** ¿Por qué el grafo es dirigido y desde dónde miden?
>
> **Cómo responder:** Hay tramos de un solo sentido y el vehículo va de la estación al
> incidente. Dijkstra arranca en el lote sobre el grafo sin invertir. En pequena, 4 -> 5 son
> 960 m pero 5 -> 4 son 2840 m; por eso L3 hurto no cubre los hurtos del nodo 4.

> **Pregunta típica:** ¿Para qué el corte en Dijkstra?
>
> **Cómo responder:** Ningún radio pasa de 3000 m; seguir más lejos no sirve. Se hace un solo
> Dijkstra por lote con el radio mayor y se reutiliza para los 3 tipos.

> **Pregunta típica:** ¿Por qué enteros y no float?
>
> **Cómo responder:** Las longitudes tienen decimales y el float acumula error: en comuna
> 18.431 de 34.810 distancias salen inexactas (173,3 m sale 173.29999999999998). Con décimas
> de metro enteras, la comparación con el radio es exacta.

> **Pregunta típica:** ¿Por qué no usaron networkx o itertools?
>
> **Cómo responder:** El enunciado los prohíbe. Solo se permite `csv`/`json`/`pandas` para leer
> y `heapq`. Todo lo demás está implementado a mano con la biblioteca estándar.

### Costos

> **Pregunta típica:** ¿Por qué Decimal y no `round()`?
>
> **Cómo responder:** `round()` redondea mitades al par (`round(2.5)` es 2) y trabaja con float
> inexacto. El enunciado pide "al millón más cercano": usamos `Decimal` con `ROUND_HALF_UP`.
> Con factor 1.0005, el costo real 1000,5 da 1001; `round()` daría 1000.

### Máscaras

> **Pregunta típica:** ¿Por qué bitmask?
>
> **Cómo responder:** Cada incidente es un bit. Unión con `|`, lo nuevo con `& ~cubiertos`,
> contar con `bit_count()`. Es rápido, el entero es inmutable (no hay que copiar en el
> backtracking) y la unión cuenta cada incidente una vez.

> **Pregunta típica:** ¿Cómo saben que las máscaras no tienen errores?
>
> **Cómo responder:** `evaluar` recalcula todo con listas de ids y sets, sin máscaras, y toda
> salida pasa por él. Hay un test que compara ambas.

### Greedy

> **Pregunta típica:** ¿Por qué greedy no es óptimo? Dame un contraejemplo.
>
> **Cómo responder:** `instancias_malas/base` (parámetros oficiales, presupuesto 7000): la base
> elige L2 hurto (valor 8, el mayor) y con eso ocupa L2, el único lote cuya estación de tránsito
> cubre los dos accidentes. Termina con L2 hurto + L3 accidente = 11. El óptimo es L1 hurto +
> L2 accidente + L3 hurto = 13.

> **Pregunta típica:** ¿Y la de razón valor/costo?
>
> **Cómo responder:** `instancias_malas/propia`: elige L4 hurto (razón 0,006) y luego L3
> accidente (0,001875) en vez de L3 incendio (0,00125); así ocupa el último lote que llegaba al
> incendio. Da 6; el óptimo, L3 accidente + L4 incendio, da 8.

> **Pregunta típica:** ¿Qué pasa en empates?
>
> **Cómo responder:** Se usa mayor **estricto** y se recorren las opciones ordenadas por código
> de lote y hurto, accidente, incendio: gana la primera, que es el desempate del enunciado.

> **Pregunta típica:** ¿Por qué propia pierde contra base en comuna?
>
> **Cómo responder:** Nunca construye bomberos: la estación de incendio aporta 155 pero cuesta
> 4250 y siempre hay opciones baratas con mejor razón. Termina con 400 sobrantes y 0 incendios.

> **Pregunta típica:** ¿Qué hace propia_ls?
>
> **Cómo responder:** Prueba muchas construcciones golosas (forzando cada estación como
> primera) y luego mejora localmente: cambia una estación, quita una o dos, o quita dos y pone
> una, rellenando con el goloso. Acepta mejoras de valor o de costo con igual valor. Termina
> porque cada paso mejora estrictamente.

> **Pregunta típica:** ¿Dónde falla propia_ls?
>
> **Cómo responder:** `instancias_malas/propia_ls`: se queda en L1 incendio + L2 hurto (12). El
> óptimo (L1 accidente + L2 incendio + L3 hurto, 13) exige cambiar dos estaciones a la vez; la
> mejora local elige a mano solo una y el relleno por razón pone siempre el CAI barato.

### Exacto

> **Pregunta típica:** ¿Cómo sabes que tu óptimo es óptimo?
>
> **Cómo responder:** El B&B recorre implícitamente todo el árbol: solo descarta ramas con
> argumentos que demuestran que no pueden ganar (no caben, opción dominada, no aporta, o cota
> que no supera al mejor). Además lo comparamos con fuerza bruta en 34 instancias chicas.

> **Pregunta típica:** ¿Por qué la cota es válida?
>
> **Cómo responder:** Suma la ganancia marginal de cada estación por separado (sobreestima por
> el solapamiento), ignora la regla de un lote y permite fracciones. Es una relajación: su
> máximo es `>=` que el real. El greedy por razón resuelve exactamente la mochila fraccional.
> Y como el valor real es entero, se puede redondear hacia abajo.

> **Pregunta típica:** ¿Qué es la submodularidad?
>
> **Cómo responder:** Rendimientos decrecientes: lo que agrega una estación es menor o igual si
> ya hay más estaciones. L2 accidente sola agrega 6; si ya está L3 accidente, agrega 0.

> **Pregunta típica:** ¿Qué diferencia hay entre backtracking y Branch & Bound?
>
> **Cómo responder:** Backtracking explora el árbol y poda por factibilidad (presupuesto). B&B
> además calcula una cota del mejor valor alcanzable en la rama y poda si no puede superar a
> la mejor conocida.

> **Pregunta típica:** ¿Para qué arrancan con la heurística?
>
> **Cómo responder:** Para tener desde el principio una propuesta buena contra la cual comparar
> las cotas; si empezara en 0 casi nada se podaría al inicio. En comuna el arranque ya era el
> óptimo y el B&B lo certificó en 41.493 nodos.

> **Pregunta típica:** ¿El orden de exploración cambia el resultado?
>
> **Cómo responder:** No el valor: el árbol es el mismo. Cambia el tiempo (y cuál propuesta se
> reporta si hay empates de valor y costo).

> **Pregunta típica:** ¿Por qué es seguro descartar opciones dominadas?
>
> **Cómo responder:** Si B, del mismo lote, cubre todo lo de A y no cuesta más, en cualquier
> propuesta con A se cambia A por B sin perder valor ni gastar más.

> **Pregunta típica:** ¿Por qué no programación dinámica?
>
> **Cómo responder:** La DP de la mochila funciona porque el valor de un objeto no depende de los
> otros. Aquí sí depende (solapamiento): el estado necesitaría el conjunto de incidentes
> cubiertos, 2^913 en comuna.

> **Pregunta típica:** ¿Por qué no reportan el óptimo de ciudad?
>
> **Cómo responder:** 4^80 ≈ 1,46 × 10^48 propuestas, ~4,63 × 10^31 años a 10^9 por segundo. Las
> podas podrían ayudar, pero no hay garantía de terminar y no lo ejecutamos.

> **Pregunta típica:** ¿Qué pasa si el presupuesto fuera 10 veces mayor?
>
> **Cómo responder:** Lo probamos: en comuna con 120.000, el óptimo es 1669 en 0,25 s (todas las
> estaciones útiles caben, la cota `alcanzable` poda rápido). En pequena con 60.000, el óptimo es
> 41 y propia_ls también lo encuentra. No hay nada que cambiar en el código.

### Complejidad y escala

> **Pregunta típica:** ¿Cuál es la complejidad?
>
> **Cómo responder:** Dijkstra O((V+E) log V) por lote (en la práctica menos por el corte). Un
> paso del goloso revisa las L·T opciones; el goloso completo hace a lo sumo L pasos. El B&B es
> exponencial en el peor caso, O(4^L), pero en comuna visitó 41.493 nodos de 1,43 × 10^9.

> **Pregunta típica:** ¿Qué haría tu código con 1.000 lotes?
>
> **Cómo responder:** Lectura, Dijkstra, base y propia funcionarían. propia_ls sería lenta (en
> ciudad, con 240 opciones, ya tarda ~20 s). El exacto no. No lo medimos.

> **Pregunta típica:** ¿Cómo mejorarías ciudad?
>
> **Cómo responder:** Ideas no implementadas: dejar el B&B corriendo con límite de tiempo y
> reportar la mejor propuesta y la brecha con la cota; vecindarios que elijan a mano dos
> estaciones nuevas; acelerar propia_ls evaluando ganancias incrementales en vez de recalcular
> `resumir`. Hoy sabemos que el óptimo de ciudad está entre 7827 y 9800.

### Implementación y pruebas

> **Pregunta típica:** ¿Por qué `evaluar` es independiente?
>
> **Cómo responder:** Es el árbitro: valida reglas (lote repetido, presupuesto) y recalcula el
> valor con sets. Si una heurística o una máscara tuviera un error, se notaría.

> **Pregunta típica:** ¿Un test prueba que el código es correcto?
>
> **Cómo responder:** No. Los tests muestran que en esas instancias coincide con la fuerza bruta.
> La correctitud del B&B viene del argumento de la cota; los tests dan confianza en la
> implementación.

> **Pregunta típica:** ¿Qué cambias si te dan datos nuevos?
>
> **Cómo responder:** Nada del código: todo se lee de los archivos. Se ejecuta
> `py main.py parte2 <ruta> propia_ls`. Si hay códigos de lote o ids repetidos, la lectura
> los rechaza con un mensaje que dice archivo, valor y líneas; los códigos sin ceros se
> ordenan en orden natural (`L2` antes que `L10`).

> **Pregunta típica:** ¿Dónde se cambia el presupuesto o los pesos?
>
> **Cómo responder:** En `parametros.json`, o en `Modelo(instancia, presupuesto=..., pesos=...)`.
> En la interfaz, con los controles del panel izquierdo (por dentro hacen lo mismo).

### Mapa e interfaz (Parte 4)

> **Pregunta típica:** ¿Leaflet o el servidor calculan algo del problema?
>
> **Cómo responder:** No. El servidor solo valida lo que llega del navegador y llama al paquete
> `estaciones` (`Modelo`, heurísticas, `resolver`) por medio de `ejecutar_metodo`. Leaflet solo
> dibuja los puntos que le manda el servidor, ya marcados como cubiertos o no. Coberturas,
> costos, valor y optimización salen de nuestro código.

> **Pregunta típica:** ¿Por qué dejaron Streamlit y folium y hicieron su propio servidor?
>
> **Cómo responder:** Por tres problemas reales: el panel lateral no se podía volver a abrir
> (la barra donde vive ese botón quedaba oculta), las teselas que usábamos empezaron a pedir
> clave y el aspecto era el de cualquier app de Streamlit. Con `http.server` (biblioteca
> estándar) más una página propia controlamos todo, y el proyecto quedó **sin dependencias**:
> se ejecuta con `py`, sin entorno virtual ni `pip`. El enunciado permite cualquier librería de
> interfaz; aquí la única "librería" es Leaflet en el navegador, y solo dibuja.

> **Pregunta típica:** ¿Por qué no dibujaron el radio de cada estación como un círculo?
>
> **Cómo responder:** Porque la cobertura se mide por la red vial dirigida, no en línea recta.
> Un círculo ignora el sentido de las calles: en pequena, de 4 a 5 hay 960 m, pero de 5 a 4 hay
> 2840 m, y por eso L3 no cubre los hurtos del nodo 4. Pintamos cada incidente como cubierto o
> no según el `Modelo`. La leyenda del mapa lo dice en una frase.

> **Pregunta típica:** ¿Cómo se distinguen los tipos si alguien no ve bien los colores?
>
> **Cómo responder:** Cada tipo tiene además una forma: cuadrado CAI, triángulo tránsito,
> círculo bomberos. Los incidentes cubiertos van rellenos y los no cubiertos son aros grises;
> los lotes libres, rombos huecos. La tabla y la leyenda repiten la forma junto al nombre.

> **Pregunta típica:** ¿Por qué el mapa no pide clave y qué pasa sin internet?
>
> **Cómo responder:** Usamos las teselas estándar de OpenStreetMap
> (`tile.openstreetmap.org`), que no piden clave; lo comprobamos pidiendo una tesela sin clave
> y respondió 200 con una imagen PNG. Los estilos "Gris" y "Oscuro" no son otro servicio: son
> filtros CSS sobre esas mismas imágenes. Sin internet solo faltan las calles de fondo: con
> "Sin mapa" se ven los puntos, la leyenda y todo lo demás, porque Leaflet, las fuentes y los
> datos están en el repositorio.

> **Pregunta típica:** ¿Para qué el canvas de Leaflet?
>
> **Cómo responder:** Ciudad tiene 5.300 incidentes. Con `preferCanvas: true` Leaflet los pinta
> en un solo lienzo en lugar de crear un elemento por punto. Los 80 lotes sí son marcas HTML,
> porque son pocos y necesitan forma, resaltado y teclado.

> **Pregunta típica:** Si `propia_ls` en ciudad tarda unos 20 s, ¿la página se congela?
>
> **Cómo responder:** No. El servidor es `ThreadingHTTPServer` (un hilo por pedido) y la página
> usa `fetch`, que no bloquea: mientras tanto se ve un reloj con los segundos y, en el exacto,
> una barra frente al límite. Un test (`test_calculo_largo_no_bloquea_otros_pedidos`) lanza un
> exacto de ciudad y comprueba que otro pedido responde en menos de 1 s.

> **Pregunta típica:** ¿Qué pasa si eligen el exacto con ciudad en la interfaz?
>
> **Cómo responder:** Se respeta el límite elegido (por defecto 30 s, máximo 600) de extremo a
> extremo: el arranque `propia_ls` recibe solo el tiempo que queda. Se muestra la mejor
> propuesta encontrada con el sello "No certificada"; si la búsqueda terminó, "Óptimo
> certificado". Con 40 lotes o más aparece un aviso antes de calcular.

> **Pregunta típica:** ¿Cómo cargan la instancia nueva de la sustentación?
>
> **Cómo responder:** En "Datos" se elige "Otra carpeta…" y se escribe la ruta **completa** de la
> carpeta. Si falta un archivo, una columna o hay ids repetidos, se muestra el mensaje de la
> lectura (por ejemplo "lotes.csv: el código de lote 'L1' aparece 2 veces (líneas 2 y 4)") en
> vez de caerse. Por consola: `py main.py parte4 C:\ruta\nueva`.

> **Pregunta típica:** ¿Eso no deja leer cualquier archivo del computador?
>
> **Cómo responder:** No. El servidor escucha solo en 127.0.0.1; un nombre corto solo puede ser
> una carpeta de `instancias/`; una ruta tiene que ser absoluta (así `../` no sirve) y la carpeta
> debe tener los cinco archivos; y los archivos estáticos se sirven solo si, después de
> resolver la ruta, siguen dentro de `interfaz/web`. Hay tests con `../`, `%2e%2e` y rutas de
> Windows que deben dar 404.

> **Pregunta típica:** ¿Qué pasa si un CSV trae un nombre de lote con código HTML?
>
> **Cómo responder:** Se ve como texto. En la página todo texto de la instancia se escribe con
> `textContent` (nunca como HTML) y en el HTML exportado los datos van como JSON con `<`, `>` y
> `&` escapados. Un test usa el lote `</script><script>alert(1)</script>` y comprueba que no
> aparece como etiqueta.

> **Pregunta típica:** ¿Por qué la suma de la columna "casos" de la tabla no da el total?
>
> **Cómo responder:** Cada fila cuenta los casos de esa estación sola; si dos estaciones cubren
> el mismo incidente, aparece en las dos filas. Los totales cuentan cada incidente una vez,
> como pide la regla del enunciado. La nota bajo la tabla lo aclara.

> **Pregunta típica:** ¿Cómo se vuelve a abrir el panel si lo cierran?
>
> **Cómo responder:** El botón "Controles" está en la barra superior, que nunca se oculta (en
> la versión anterior el botón vivía en una barra que el CSS escondía). También con la tecla
> `[` (y `]` para resultados). El botón dice si el panel está abierto con `aria-expanded` y la
> preferencia se guarda en `localStorage` dentro de `try/catch`.

### Decisiones de interpretación y notebook

> **Pregunta típica:** ¿Por qué usan `decimal` si el enunciado solo menciona csv, json, pandas
> y heapq?
>
> **Cómo responder:** La restricción prohíbe librerías que calculen rutas, distancias en grafos
> o combinaciones. `decimal` no hace nada de eso: solo lee números escritos como texto sin
> errores de float (las longitudes se vuelven enteros exactos) y redondea el costo. Las
> distancias las calcula nuestro Dijkstra con `heapq`.

> **Pregunta típica:** ¿Cómo redondean el costo y por qué no con `round()`?
>
> **Cómo responder:** Con `.5` hacia arriba (`ROUND_HALF_UP`), que es "el millón más cercano"
> como se enseña en el colegio. `round()` de Python manda `.5` al par (`round(2.5)` da 2) y
> trabaja con float. En las tres instancias entregadas ningún costo cambia entre las dos reglas;
> en una instancia nueva con mitades sí cambiaría.

> **Pregunta típica:** ¿Qué es el "menor código de lote" si hay `L2` y `L10`?
>
> **Cómo responder:** Orden natural: `L2` antes que `L10` (`clave_de_lote`). Con códigos con
> ceros (`L01`…) es igual al orden de texto. Si el profesor quiere orden de texto, basta con
> agregar `return codigo` al inicio de `clave_de_lote`.

> **Pregunta típica:** ¿`propia_ls` construye una estación a la vez como pide el 2.2?
>
> **Cómo responder:** No del todo, y lo decimos: es híbrida (arranques golosos + mejora local
> que quita y cambia estaciones). El 2.2 lo cumple `propia`, constructiva pura, que supera a la
> base en pequena (19 > 15) y en ciudad (7706 > 7591).

> **Pregunta típica:** ¿Sus instancias malas no hacen trampa con los parámetros?
>
> **Cómo responder:** No: usan los costos, radios y pesos oficiales y solo cambian el
> presupuesto; tienen 3 o 6 nodos. base 11 vs 13, propia 6 vs 8, propia_ls 12 vs 13, comprobado
> con fuerza bruta en `test_instancias_malas`.

> **Pregunta típica:** ¿Por qué el notebook importa el paquete en vez de tener el código adentro?
>
> **Cómo responder:** Para que haya **un solo código**: el notebook, `main.py` y la interfaz
> llaman a las mismas funciones de `estaciones/`, así nada se desincroniza y los tests prueban
> lo mismo que se entrega. El notebook queda corto y legible; sus `assert` comparan contra los
> casos del enunciado.

---

## 12. Glosario

| Término | Definición |
|---|---|
| Arista / tramo | Calle de un nodo a otro, en un solo sentido, con longitud. |
| Grafo dirigido | Grafo donde cada arista tiene sentido. |
| Lista de adyacencia | Para cada nodo, la lista de (vecino, longitud) a los que se llega. |
| Dijkstra | Algoritmo de caminos más cortos desde un origen con pesos no negativos. |
| Corte (cutoff) | Distancia máxima a partir de la cual Dijkstra deja de expandir. |
| Montículo / heap | Estructura que entrega el mínimo en O(log n); `heapq`. |
| Lazy deletion | Dejar entradas viejas en el heap e ignorarlas al sacarlas. |
| Cobertura | Incidentes del mismo tipo a distancia `<=` radio desde la estación. |
| Máscara de bits | Entero cuyos bits en 1 representan incidentes cubiertos. |
| Ganancia marginal / valor nuevo | Lo que una estación agrega sobre lo ya cubierto. |
| Submodularidad | La ganancia marginal no crece al agregar más estaciones antes. |
| Greedy / goloso | Elegir en cada paso lo mejor ahora, sin volver atrás. |
| Heurística | Método que da una buena solución sin garantizar la mejor. |
| Búsqueda local | Mejorar una solución probando cambios pequeños (vecinos). |
| Vecino | Propuesta que se obtiene con un cambio pequeño de la actual. |
| Multi-arranque | Ejecutar el goloso desde varios puntos de partida y quedarse con el mejor. |
| Fuerza bruta | Probar todas las propuestas posibles. |
| Backtracking | Recorrer el árbol de decisiones en profundidad, deshaciendo al volver. |
| Branch & Bound | Backtracking que poda ramas con una cota del mejor valor posible. |
| Cota superior | Número que ningún valor de la rama puede superar. |
| Relajación | Versión del problema con restricciones quitadas; su óptimo es `>=` al real. |
| Mochila fraccional | Mochila donde se pueden tomar fracciones; se resuelve por razón. |
| Opción dominada | Estación que otra del mismo lote supera en cobertura sin costar más. |
| Warm start | Empezar la búsqueda exacta con una solución heurística ya conocida. |
| ROUND_HALF_UP | Redondeo con mitades hacia arriba (1000,5 -> 1001). |
| Redondeo bancario | Mitades al par más cercano; lo que hace `round()` (2,5 -> 2). |
| Oráculo | Método lento pero seguro que se usa como referencia en tests. |

---

## 13. Parte 4: mapa, subcomando `parte4` e interfaz

La Parte 4 pide, para `ciudad` (propuesta recomendada) y para `comuna` (mejor propuesta
posible): **un mapa** donde se distingan lotes no usados, estaciones por tipo e incidentes
cubiertos y no cubiertos; **una tabla** de estaciones con costo total, casos por tipo y valor;
y **un párrafo** que justifique la recomendación. Para la feria, además, una **aplicación
interactiva** donde se elija la instancia, se cambien presupuesto y pesos y se vea la propuesta
sobre el mapa. Aquí se elige `propia_ls` para ciudad (7827, la mejor de las tres heurísticas;
el óptimo no se conoce) y el exacto para comuna (1574, óptimo certificado).

Todo funciona **solo con la biblioteca estándar de Python**: no hay entorno virtual ni `pip`.

### 13.1 Arquitectura: servidor local + API + página web

**Qué es.** Tres piezas, cada una con un trabajo:

```text
 navegador (interfaz/web)                servidor (interfaz/servidor.py)          núcleo (estaciones/)
 ─────────────────────────               ───────────────────────────────          ────────────────────
 index.html + estilos.css                GET  /            archivos de web/
 app.js     reacciona al usuario  ──►    POST /api/resolver  valida  ──────►      ejecutar_metodo
 api.js     fetch() con JSON      ◄──    respuesta JSON      ◄───────────────     Modelo / heurísticas /
 mapa.js    dibuja con Leaflet                                                    resolver / evaluar
                                         mapa.py: tabla, CSV, datos del mapa, HTML exportado
```

- `py main.py interfaz` crea el servidor en `http://127.0.0.1:8765` y abre el navegador
  (`--puerto` cambia el puerto; `--no-abrir` no abre el navegador).
- La página pide `/api/instancias` (carpetas de `instancias/` con los cinco archivos),
  `/api/instancia` (valores por defecto y el mapa sin propuesta), `/api/resolver` (la
  propuesta), `/api/comparar` (los cuatro métodos con los mismos parámetros) y
  `/api/exportar` (el mapa HTML para descargar).

**Por qué así.**

1. **Una sola fuente de verdad.** El servidor no tiene lógica de cálculo: valida y llama al
   mismo código que `main.py`. Para eso existe `estaciones/ejecucion.py`, que usan los dos:

   ```python
       inicio = time.perf_counter()
       if metodo == "exacto":
           resultado = resolver(modelo, limite_segundos=limite_segundos)
       else:
           resultado = HEURISTICAS[metodo](modelo)
       return resultado, time.perf_counter() - inicio
   ```

2. **Sin dependencias.** `http.server` viene con Python. Leaflet (la librería de mapas del
   navegador) y las fuentes están copiados en `interfaz/web/vendor/` con sus licencias: no se
   descarga nada de otros sitios al abrir la página (salvo las imágenes del fondo de calles).
3. **No se congela.** El servidor atiende cada pedido en su propio hilo:

   ```python
   class Servidor(ThreadingHTTPServer):
       """Servidor multihilo: un cálculo largo no bloquea a los demás pedidos."""

       daemon_threads = True
   ```

   Mientras el exacto o `propia_ls` trabajan, la página sigue respondiendo y muestra un reloj.
4. **Se guarda lo ya preparado.** La clase `Almacen` guarda en memoria las instancias leídas,
   los `Modelo` por (carpeta, presupuesto, pesos) y la última propuesta de cada método, con un
   `threading.Lock` para que dos hilos no escriban a la vez. Así el mapa que se descarga es el
   mismo que se ve, sin recalcular.

### 13.2 Datos separados del dibujo (`estaciones/mapa.py`)

**Qué es.** `mapa.py` tiene dos mitades:

- **Datos** (funciones puras): `filas_de_estaciones`, `fila_de_totales`,
  `clasificar_incidentes`, `contar_por_tipo`, `lotes_libres`, `tabla_texto`, `tabla_csv`,
  `leer_fechas`, `limites` y `datos_del_mapa` (lo que recibe el navegador).
- **Exportación:** `exportar_html` arma un único archivo HTML con Leaflet, las fuentes, los
  estilos, el mismo código de dibujo (`mapa.js`) y los datos. Se abre con doble clic.

**Por qué así.** Ninguna función de `mapa.py` calcula coberturas ni costos: todo sale del
`Modelo`. Por ejemplo, qué incidentes están cubiertos (`clasificar_incidentes`):

```python
    ids_cubiertos = set()
    for codigo_lote, tipo in propuesta:
        ids_cubiertos.update(modelo.cobertura(codigo_lote, tipo))
```

Si el mapa calculara la cobertura por su cuenta (por ejemplo con círculos), podría
contradecir a la tabla. `test_mapa.py` comprueba que cubiertos + no cubiertos = total y que
los conteos coinciden con `evaluar`.

`datos_del_mapa` manda los incidentes como listas cortas
`[id, lat, lon, posición_del_tipo, cubierto, fecha]` y no como diccionarios: en ciudad son
5.300 y así el JSON pesa menos de la mitad. La fecha (`fecha_hora`) se lee de
`incidentes.csv` con `leer_fechas`, porque `lectura.py` no la necesita para el cálculo.

### 13.3 El mapa

**Qué se dibuja** (cada grupo se puede apagar en la leyenda, que está dentro del mapa):

| Elemento | Cómo se ve | Por qué |
|---|---|---|
| Estación construida | Forma propia por tipo: cuadrado (CAI), triángulo (tránsito), círculo (bomberos); ficha con lote, tipo, costo y casos | Forma **y** color: se distinguen aun sin percibir el color (daltonismo). |
| Incidente cubierto | Punto relleno del color de su tipo | Se ve qué cubre cada tipo de estación. |
| Incidente no cubierto | Aro gris | Lo que queda sin atender se ve sin competir con lo cubierto. |
| Lote sin estación | Rombo hueco gris | Pide el enunciado: lotes no usados. |
| Leyenda y capas | Recuadro abajo a la izquierda, con casillas y el conteo de cada capa | El mapa se entiende sin explicación oral. |

La forma de cada tipo sale de `mapa.py` (el color lo ponen los tokens CSS):

```python
FORMA_POR_TIPO = {
    "hurto": "cuadrado",
    "accidente": "triangulo",
    "incendio": "circulo",
}
```

**Por qué NO círculos de radio.** La cobertura se mide por la **red vial dirigida**
(sección 4.2). Un círculo mide en línea recta y trata igual la ida y la vuelta; la red no: en
pequena, de 4 a 5 hay una calle de 960 m, pero de 5 a 4 hay 2840 m, y por eso L3 (nodo 5) no
cubre los hurtos del nodo 4. Un círculo haría creer que cubre zonas que no cubre.

**Fondo sin clave.** Las teselas son las estándar de OpenStreetMap:

```js
  const URL_TESELAS = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
```

con la atribución "© OpenStreetMap contributors" y zoom máximo 19 (su política de uso pide
atribución y no descargar masivamente). Los estilos "Gris" y "Oscuro" son filtros CSS sobre
las mismas imágenes, por ejemplo:

```css
.mapa[data-fondo="oscuro"] .leaflet-tile-pane {
  filter: invert(1) hue-rotate(180deg) grayscale(0.75) brightness(0.78) contrast(0.92);
}
```

"Sin mapa" quita la capa de teselas (no pide ninguna imagen): sirve sin internet.

**Canvas.** Los incidentes se pintan en un solo lienzo (`preferCanvas: true` y un
`L.canvas` compartido); los 80 lotes, en cambio, son marcas HTML con forma SVG porque son
pocos y necesitan resaltado y teclado. No se dibujan los 27.568 nodos: el fondo ya muestra
las calles y taparían lo importante.

**Encuadre.** `limites(modelo)` calcula el rectángulo de lotes e incidentes y Leaflet ajusta
el zoom ahí (`fitBounds`), dejando libre el espacio que tapan los paneles abiertos.

**Interacción.** Al pasar el cursor (o el foco del teclado) por una fila de la tabla, la
estación crece y se marca en el mapa; al pasar por la estación, se marca su fila. Clic o
Enter en la fila vuela hasta la estación (`flyTo`) y abre su ficha; si el sistema pide menos
movimiento (`prefers-reduced-motion`), salta sin animación.

### 13.4 El subcomando `parte4`

```text
py main.py parte4 <instancia> [--metodo base|propia|propia_ls|exacto]
                              [--salida ruta.html] [--limite SEGUNDOS]
```

- Por defecto: una instancia con más de 30 lotes (como ciudad, con 80) usa `propia_ls` y las
  demás usan `exacto` (`metodo_por_defecto_parte4(modelo)` y
  `LOTES_MAXIMOS_PARA_EXACTO_EN_PARTE4`); se decide por tamaño, no por el nombre de la carpeta. El exacto tiene **siempre** límite: 60 s por defecto
  (`LIMITE_PARTE4_POR_DEFECTO`), en cualquier instancia; si se corta, imprime "mejor
  encontrada en 60 s (no certificada)".
- Imprime la tabla (`tabla_texto`) y escribe el mapa autocontenido en
  `salidas/mapa_<instancia>_<método>.html` (la carpeta se crea si no existe y no se sube al
  repositorio porque se regenera).

Salida real de `py main.py parte4 comuna`:

```text
instancia=comuna metodo=exacto tiempo_s=0.715
óptimo certificado
lote    tipo       estación                           costo   casos
L03     accidente  Estación de tránsito y grúas        1800     222
L06     hurto      CAI                                  850     180
L09     hurto      CAI                                  850     166
L11     hurto      CAI                                 1050     200
L13     accidente  Estación de tránsito y grúas        2100     213
L14     hurto      CAI                                  800     159
L15     incendio   Estación de bomberos                4250      31
-------------------------------------------------------------------
costo_total=11700 de presupuesto=12000
casos_cubiertos={'hurto': 519, 'accidente': 300, 'incendio': 31}
valor=1574
mapa=salidas\mapa_comuna_exacto.html (706 KB, generado en 0.01 s)
```

Ciudad (`py main.py parte4 ciudad`): `propia_ls`, 23 estaciones, costo 40000 de 40000, casos
1768 / 1798 / 133, valor 7827, en 21,4 s en esa medición (entre 20 y 35 s según el equipo); el mapa (`salidas\mapa_ciudad_propia_ls.html`,
959 KB) se generó en 0,03 s. El archivo pesa poco porque Leaflet y las fuentes
ocupan ~600 KB fijos y los datos van compactos.

Ojo con "casos": en la tabla cada estación cuenta sus casos por separado, así que la suma de
la columna puede ser mayor que los casos cubiertos (un incidente cubierto por dos estaciones
aparece en ambas filas). La línea `casos_cubiertos` cuenta cada incidente una vez.

### 13.5 La interfaz web (`py main.py interfaz`)

**Qué es.** Una página a pantalla completa: el **mapa** es el protagonista; a la izquierda
flota el panel de **controles** y a la derecha el de **resultados**. Ambos se pueden ocultar.

| Control | Qué hace |
|---|---|
| Datos (instancia) | Lista las carpetas de `instancias/` con los cinco archivos (pequena, comuna, ciudad primero). "Otra carpeta…" muestra un campo para la ruta completa de la instancia nueva. Al cargarla, el mapa ya muestra lotes e incidentes. |
| Presupuesto | Campo numérico + deslizador + "Restablecer" (vuelve al de `parametros.json`). Se pasa a `Modelo(..., presupuesto=...)`. |
| Pesos de prioridad | Una fila por tipo con su forma, botones − / + y el número; "Restablecer". Se pasan a `Modelo(..., pesos=...)`. |
| Método | Base, Propia, Propia + LS o Exacto. Con Exacto aparece el límite (0 a 600 s, por defecto 30) y, con 40 lotes o más, un aviso. |
| Calcular propuesta | Botón principal (también Enter). Mientras calcula muestra el reloj; no recalcula solo en cada cambio, pero avisa "Los controles cambiaron". |

**Resultados:** valor en cifra grande, costo frente al presupuesto (barra), estaciones,
incidentes cubiertos y tiempo; casos cubiertos por tipo con porcentaje del total de ese tipo;
sello "Óptimo certificado" o "No certificada" en el exacto; la tabla de estaciones con fila
de totales; botones "Tabla CSV", "Mapa HTML" y "Comparar métodos" (valor, costo y tiempo de
los cuatro métodos con los mismos parámetros, útil para la Parte 3).

**Estados.** Vacío (aún no hay propuesta), cargando (reloj y barra), error (mensaje claro del
servidor y "Reintentar") y resultado. Los errores nunca muestran trazas de Python: el
servidor responde `{"error": "mensaje"}` y escribe la traza solo en su consola.

**El panel siempre se puede reabrir.** El botón vive en la barra superior, que nunca se
oculta. Abrir o cerrar cambia la clase del panel, la del cuerpo y `aria-expanded`:

```js
    panel.classList.toggle("cerrado", !abierto);
    elementos.cuerpo.classList.toggle(nombre + "-abierto", abierto);
    boton.setAttribute("aria-expanded", String(abierto));
```

Atajos: `[` controles, `]` resultados, Enter calcula. El estado se recuerda en
`localStorage` (dentro de `try/catch`: en modo privado la página funciona igual).

**Dirección de la página.** Se puede abrir ya configurada, por ejemplo
`http://127.0.0.1:8765/#instancia=comuna&metodo=exacto&auto=1&panel=cerrado&tema=claro`
(`auto=1` calcula al cargar). `estado.js` acepta solo valores de una lista conocida.

**Diseño.** Oscuro primero, un solo acento lima (como un chaleco reflectivo), bordes finos y
esquinas casi rectas, Familjen Grotesk para el texto y Fira Code para las cifras. Las
decisiones, con lo que recomendó la Skill de diseño ui-ux-pro-max y lo que se descartó, están
en [DISENO.md](DISENO.md).

**Funciona en:** escritorio (1440×900 y 1024×768) y teléfono (390×844: los paneles pasan a
ser hojas que suben desde abajo).

### 13.6 Seguridad del servidor local

Aunque solo se use en el propio computador, el servidor trata todo lo que llega como no
confiable:

- **Solo 127.0.0.1** y solo pedidos con `Host` 127.0.0.1 o localhost (evita que una página de
  internet use el servidor a través de un dominio que apunte al equipo).
- **Validación de todo:** método en lista blanca; presupuesto entero entre 0 y 10^9; pesos
  enteros entre 0 y 10^6 y solo de tipos de la instancia; límite entre 0 y 600 s; cuerpo JSON
  de máximo 64 KB (`413`) y con `Content-Type: application/json` (`415`).
- **Rutas:** un nombre corto solo puede ser una carpeta de `instancias/`; una ruta nueva debe
  ser absoluta y tener los cinco archivos:

  ```python
      ruta = Path(texto)
      if not ruta.is_absolute():
  ```

  y los archivos de la página se sirven solo si siguen dentro de `interfaz/web`:

  ```python
          archivo = (CARPETA_WEB / relativa).resolve()
          if not archivo.is_relative_to(CARPETA_WEB) or not archivo.is_file():
              raise ErrorDePeticion(404, "Archivo no encontrado.")
  ```

- **Textos de los CSV:** en la página se escriben con `textContent`; en el HTML exportado los
  datos van como JSON con `<`, `>` y `&` escapados (`json_para_html`), y el título con
  `html.escape`.
- **Cabeceras:** `Content-Security-Policy` (solo archivos propios; imágenes también de
  `tile.openstreetmap.org`), `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` y
  `Cache-Control: no-store` en la API. Sin telemetría ni CDN.

### 13.7 En la sustentación

1. Abrir una terminal en la carpeta del proyecto.
2. `py main.py interfaz` (se abre el navegador; si el puerto está ocupado, el mensaje sugiere
   `--puerto 8766`).
3. En "Datos" elegir "Otra carpeta…", escribir la ruta completa de la carpeta nueva y pulsar
   "Cargar carpeta".
4. Elegir el método (Exacto con límite en instancias pequeñas; Propia + LS en grandes) y
   pulsar "Calcular propuesta". "Comparar métodos" da la tabla de la Parte 3.
5. Por consola, lo equivalente es `py main.py parte4 C:\ruta\nueva` (mapa en `salidas/`).

**Qué se verificó y qué no.** Los tests levantan el servidor de verdad y le hacen pedidos
HTTP (sección 4.6). La interfaz se revisó con capturas de Chrome sin ventana (1440×900,
1024×768, 390×844; tema oscuro y claro; panel abierto y cerrado; estados vacío y de error) y
con acciones simuladas (tecla `[`, resaltado de fila). No se probó con un lector de pantalla
real ni en otros navegadores distintos de Chrome.

---

## 14. Estado y límites honestos

### Hecho y verificado

- **Parte 1:** costo y cobertura de cada (lote, tipo); coincide con los ejemplos del enunciado.
  Ciudad se calcula en menos de un segundo (requisito: menos de un minuto).
- **Parte 2:** heurística base (coincide exactamente con las salidas de pequena y comuna del
  enunciado), `propia` (mejor que base en pequena y ciudad), `propia_ls` (mejor de las tres en
  las tres instancias) e instancias malas de máximo 6 nodos para cada heurística, con su
  README explicativo.
- **Parte 3:** óptimo exacto con backtracking + Branch & Bound para pequena (20) y comuna
  (1574, ~0,7 s, `optimo_certificado=True`), tabla comparativa, cálculo del espacio y
  búsqueda con límite de tiempo (`--limite`) para cualquier instancia; el límite se cumple de
  extremo a extremo, arranque incluido (ciudad con `--limite 5`: 5,0 s).
- **Parte 4:** tabla y mapa HTML autocontenido para ciudad (`propia_ls`, 7827) y comuna
  (exacto, 1574) con `main.py parte4` (mapas en `salidas/`), y la interfaz web de la feria
  (`py main.py interfaz`: servidor `http.server` + página propia con Leaflet incluido). Sin
  dependencias externas. Ver sección 13.
- **Robustez:** duplicados rechazados con mensaje claro, orden natural de códigos, nombres
  cortos desde cualquier carpeta.
- **Notebook:** `practica_estaciones.ipynb` tiene las Partes 1 a 4 con salidas guardadas,
  los `assert` contra los casos del enunciado, las tres instancias malas, la tabla comparativa,
  el cálculo de 4^80, los dos mapas y el párrafo de justificación al concejo (sección 15).
- **Datos escritos a mano:** coma decimal y tipos con mayúsculas o espacios se aceptan.
- **Tests:** 71 tests con `py -m unittest discover -s tests`: OK (incluyen el servidor con
  pedidos HTTP reales, el notebook y, con Node instalado, las pruebas de JavaScript).

### Pendiente

- Nada de las Partes 1 a 4. El notebook no se ejecutó dentro de Jupyter (no está instalado en
  la máquina donde se preparó): sus celdas se ejecutaron con Python en un solo espacio de
  nombres y las salidas guardadas son las de esa ejecución. Los mapas se ven dentro del
  notebook solo si IPython está disponible; si no, la celda imprime la ruta del archivo.

### No verificado o con riesgo

- **Lo visual** se revisó con capturas de Chrome sin ventana (sección 13.7), no con usuarios
  reales, lectores de pantalla ni otros navegadores. Las teselas de OpenStreetMap necesitan
  internet; sin conexión se usa "Sin mapa".

- Comportamiento con las instancias nuevas de la sustentación (no existen aún).
- Orden natural de códigos: es una decisión del equipo; el enunciado solo dice "menor código".
  Si el profesor lo interpreta como texto, ver sección 10.
- Que el orden con razones `float` en `_cota_mochila` nunca afecte la validez de la cota es un
  argumento del comentario del código, no una demostración hecha aquí.
- NP-dificultad del problema y comparaciones de velocidad set vs máscara: dato de referencia,
  no verificado aquí.
- El tiempo de 339 s de una versión anterior es un dato del historial, no reproducible con el
  código actual.
- El óptimo de ciudad: desconocido; solo se sabe que está entre 7827 y 9800.

---

## 15. El notebook

**Qué contiene.** `practica_estaciones.ipynb` conserva sin cambios las 10 celdas del
enunciado (`c00` a `c09`) y agrega celdas nuevas debajo de la parte que corresponde:

- **Parte 1:** una celda de configuración, `parte1(entrada)` con su `assert` contra
  `casos_ej_001_parte1`, la tabla de los 15 pares de pequena y el resumen de comuna y ciudad
  (pares y tiempo; ciudad en menos de 1 s).
- **Parte 2:** explicación de las tres heurísticas, `parte2(entrada)` con su `assert`, los
  resultados de base, propia y propia_ls en las tres instancias (estaciones, costo, casos por
  tipo, valor y tiempo) y las tres instancias malas (resumen, heurística frente al óptimo y la
  decisión que la desvía).
- **Parte 3:** explicación del Branch & Bound, `parte3(entrada)` con su `assert` (además exige
  `optimo_certificado`), los óptimos de pequena y comuna con estadísticas, la tabla comparativa
  con el precálculo medido aparte y el cálculo de 4^80 para ciudad.
- **Parte 4:** los mapas de ciudad (`propia_ls`) y comuna (óptimo) con el mismo exportador de
  `py main.py parte4` (en `salidas/`), sus tablas, la comparación de las tres heurísticas en
  ciudad y el párrafo de justificación al concejo.
- **Notas de interpretación y límites** al final.

**Por qué las celdas son finas.** El código vive en `estaciones/`; el notebook solo lo llama.
`parte1`, `parte2` y `parte3` reciben el diccionario `entrada` de los casos del enunciado y
devuelven exactamente sus claves (sin claves extra como `tiempo_s`), así un evaluador puede
compararlas con `==`.

**Cómo se ejecuta.** Abrirlo con Jupyter o VS Code desde la carpeta del proyecto y ejecutar
todo en orden. La primera celda busca la carpeta que contiene `estaciones/` (la actual o una
superior) y la agrega a `sys.path`; si no la encuentra, lo dice. Ejecutar todo tarda alrededor
de 30 a 45 s, casi todo por `propia_ls` en ciudad. Los mapas se ven dentro del notebook si
IPython está disponible; si no, la celda imprime la ruta del archivo HTML.

**Cómo se valida.** `tests/test_notebook.py` comprueba que es JSON válido (nbformat 4), que las
celdas del enunciado no cambiaron (huella SHA-256 de cada una), que las salidas guardadas no
tienen errores ni rutas absolutas y que el contador de ejecución es correlativo, y ejecuta en
un espacio de nombres limpio las celdas rápidas (casos del enunciado, configuración y las
funciones `parte1` a `parte3`), cuyos `assert` deben pasar. Las celdas lentas (propia_ls en
ciudad) no se ejecutan en los tests para que la suite siga siendo rápida.
