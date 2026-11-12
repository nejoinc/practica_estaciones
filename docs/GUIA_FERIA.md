# Guía de feria: Estaciones

Para quien atiende el stand. Aquí no se explica código: se cuenta el problema, se muestra el producto y se responde con honestidad.

---

## 1. Gancho y pitch

**Frase gancho:** *"Con un presupuesto fijo, ¿dónde ponemos CAI, tránsito y bomberos para cubrir la mayor cantidad posible de incidentes? Hay más combinaciones que granos de arena en la Tierra."*

**Pitch de 30 segundos:**
"Una ciudad tiene lotes disponibles y un presupuesto. En cada lote puede construir un CAI, una estación de tránsito, una de bomberos o nada. Cada incidente vale distinto: un hurto 1, un accidente 3 y un incendio 5. Nuestro programa decide qué construir y dónde para cubrir el mayor valor posible. Mide la distancia real por las calles y respeta el sentido de cada vía. Se lo mostramos en el mapa."

**Pitch de 2 minutos:**
1. *El problema:* el presupuesto no alcanza para todo y cada lote admite una sola estación. Elegir mal es dejar barrios sin cobertura.
2. *Por qué es difícil:* en la instancia ciudad hay 80 lotes con 4 opciones cada uno. Eso da 4^80 planes posibles, unos 1,46 × 10^48. Ningún computador puede revisarlos uno por uno.
3. *Por qué no basta con "poner la estación más barata o la más valiosa primero":* en la instancia comuna esa regla simple da 1.529 puntos y el óptimo es 1.574. Además tenemos documentado un caso pequeño donde la regla saca 6 y el óptimo es 8.
4. *Qué hace el producto:* en instancias medianas como comuna encuentra el óptimo y lo **certifica**, en menos de un segundo. En la ciudad completa (27.568 nodos de calle) da un plan de 7.827 puntos de 9.800 posibles y usa los 40.000 millones del presupuesto.
5. *Cierre:* "Además se pueden comparar métodos, cambiar el presupuesto y descargar el mapa o la tabla."

---

## 2. La historia en 3 actos

**Acto 1: el problema que duele.** Una ciudad tiene presupuesto limitado y muchos lugares donde podría construir. Los hurtos, los accidentes y los incendios no pesan lo mismo, y una estación solo sirve si llega a tiempo **por las calles**, no "en línea recta".

**Acto 2: por qué es difícil (con números reales del proyecto).**
- Ciudad: 27.568 nodos de calle, 80 lotes candidatos y 40.000 millones de presupuesto. El valor total en incidentes es 9.800.
- 4^80 ≈ 1,46 × 10^48 combinaciones. Probar una por una no termina nunca.
- Las calles tienen sentido: llegar de A a B no cuesta lo mismo que llegar de B a A. Cada cobertura se calcula con rutas reales (Dijkstra).
- La intuición falla: la regla golosa simple pierde contra el óptimo (1.529 contra 1.574 en comuna).

**Acto 3: qué hace el producto.**
- En comuna (15 lotes y 12.000 millones) da el **óptimo certificado**: 7 estaciones, costo de 11.700 y valor de 1.574. Tarda alrededor de un segundo; la guía de estudio mide unos 0,6 s.
- En ciudad, el mejor plan que encontramos vale 7.827, usa 40.000 de los 40.000 millones y cubre 1.768 hurtos, 1.798 accidentes y 133 incendios. El óptimo real no se conoce: está entre 7.827 y 9.800.
- Todo se ve en una interfaz web con mapa, comparador de métodos y descarga del mapa (HTML) y de la tabla (CSV).

---

## 3. Guion de demo en vivo

**Preparación:** use el modo local, `py main.py interfaz`, que abre `http://127.0.0.1:8765`. Antes de abrir el stand, deje comuna y ciudad ya calculadas al menos una vez.

1. **Comuna primero (el golpe de efecto).** Elija la instancia *comuna*, el método *exacto* y pulse Calcular (o Enter).
   *Diga:* "Este es el mejor plan posible, y el programa lo demuestra: valor 1.574 con 7 estaciones, en menos de un segundo."
2. **Señale el mapa.** Muestre las estaciones por tipo con la leyenda, los incidentes cubiertos y los no cubiertos. Abra el popup de una estación.
   *Diga:* "La cobertura se mide por las calles y respeta el sentido de cada una."
3. **Compare métodos.** Use el comparador para correr los cuatro métodos (base, propia, Propia + LS y exacto).
   *Diga:* "La regla simple da 1.529 y el óptimo 1.574. La intuición se queda corta."
4. **Ciudad.** Elija *ciudad* con el método *Propia + LS*.
   *Diga, mientras calcula:* "Ahora está pensando: hay 4^80 planes posibles y no puede mirarlos todos. Busca de forma inteligente."
   Resultado: 7.827 puntos, con todo el presupuesto usado. *Diga:* "Es el mejor plan que encontramos. El óptimo está entre 7.827 y 9.800."
5. **Juegue con el visitante.** Cambie el presupuesto o los pesos y recalcule.
6. **Descargas.** Pulse **Mapa HTML** (un archivo que se abre con doble clic) y **Tabla CSV**.
   *Diga:* "Se lo puede llevar y revisar sin el programa."

Atajos de teclado: `[` muestra los controles, `]` los resultados y Enter calcula.

**Plan B:**
- **Sin internet:** el fondo de calles del mapa se descarga de internet. Cambie el fondo a **"Sin mapa"**; las estaciones y los incidentes se siguen viendo. Tenga también un mapa HTML ya exportado de comuna y de ciudad.
- **Si ciudad tarda:** Propia + LS puede tardar entre 20 y 35 s en local. Tenga ciudad ya calculada en otra pestaña, o ponga un límite de tiempo bajo en el campo de límite. Use la espera como parte del show ("está pensando").
- **Si el servidor se cae:** la página avisa que no hay conexión. Vuelva a ejecutar `py main.py interfaz` en la consola.

---

## 4. Preguntas típicas

| Pregunta | Respuesta |
|---|---|
| ¿Para qué sirve? | Decide dónde construir cada tipo de estación con un presupuesto fijo, para cubrir el mayor valor posible de incidentes. |
| ¿Es el óptimo? | En comuna y en la instancia pequeña sí, y está certificado. En ciudad es el mejor plan que encontramos (7.827); el óptimo está entre 7.827 y 9.800. |
| ¿Cuánto tarda? | Comuna tarda alrededor de un segundo. Ciudad tarda entre 20 y 35 s en este computador con el método más fuerte, y se puede limitar el tiempo. |
| ¿Lo puede usar la alcaldía? | Es un proyecto académico. El método aplica a este tipo de problema, pero nadie lo ha adoptado y habría que validarlo con datos y criterios oficiales. |
| ¿Usa datos reales de Medellín? | Las instancias son los datos del enunciado del curso. No afirme que son incidentes reales de Medellín (verificar el origen exacto antes de decir más). |
| ¿Qué lo hace diferente de un Excel? | Calcula rutas reales por calles con sentido y busca entre más de 10^48 combinaciones. En comuna demuestra que su respuesta es la mejor. |
| ¿Quién lo hizo? | Estudiantes de Análisis y Diseño de Algoritmos de la Universidad de Medellín, como práctica del curso. |

---

## 5. Vocabulario

| Use | Evite con no técnicos |
|---|---|
| "plan", "propuesta" | "vector solución", "asignación" |
| "por las calles, respetando el sentido" | "Dijkstra en grafo dirigido" |
| "búsqueda inteligente que descarta caminos sin futuro" | "Branch & Bound", "cota", "poda" |
| "regla rápida" | "heurística golosa" |
| "mejor plan que encontramos" | "óptimo", cuando se habla de ciudad |

**Analogías:**
- **La mochila:** hay un presupuesto (la mochila) y objetos con precio y valor (las estaciones). Hay que llenarla con lo que más vale sin pasarse.
- **El tablero de ajedrez gigante:** cada lote es una casilla con 4 opciones. Con 80 casillas hay más jugadas posibles que granos de arena; no se pueden probar todas.
- **La regla rápida que falla:** tomar siempre lo que parece mejor ahora deja huecos. Por eso la regla simple saca 1.529 donde el óptimo es 1.574.

---

## 6. Checklist del stand

- [ ] Correr `py main.py tabla` y comprobar que salen 1.529, 1.574 y 7.827.
- [ ] Abrir `py main.py interfaz` y probar comuna (exacto) y ciudad (Propia + LS).
- [ ] Dejar comuna y ciudad precalculadas.
- [ ] Probar el internet del recinto; si falla, usar el fondo "Sin mapa".
- [ ] Llevar cargador y batería llena.
- [ ] Tener en el escritorio los mapas HTML exportados de comuna y ciudad como respaldo.
- [ ] Poner un cartel con las 3 cifras clave: **4^80 ≈ 1,46 × 10^48 planes**, **1.574 óptimo certificado (comuna)** y **7.827 de 9.800 (ciudad)**.

---

## 7. Líneas que NO se cruzan

El problema ya es difícil de verdad. No hace falta exagerarlo.

| No diga | Diga |
|---|---|
| "El plan de ciudad es óptimo / perfecto." | "Es el mejor plan que encontramos. El óptimo está entre 7.827 y 9.800." |
| "La alcaldía, la Policía, Tránsito o Bomberos lo usan o lo respaldan." | "Es un proyecto académico; nadie lo ha adoptado." |
| "Tenemos clientes o pilotos." | (No hay. No lo mencione.) |
| "Ahorra X %" o "salva X vidas". | "Cubre 7.827 de 9.800 puntos de valor en la instancia ciudad." |
| "Son los incidentes reales de Medellín." | "Son los datos de ejemplo del curso." |
| "Óptimo" sin aclarar la instancia. | "Óptimo certificado", solo para comuna y la instancia pequeña. |

**Logos:** los logos de la interfaz son ilustrativos y solo identifican el tipo de estación. No implican respaldo de ninguna institución. Si alguien pregunta, dígalo así.
