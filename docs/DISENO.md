# Diseño de la interfaz: decisiones y evidencia

Este documento explica **por qué la interfaz se ve como se ve**. Las recomendaciones de partida
salen de ejecutar el buscador de la Skill de diseño **ui-ux-pro-max** (del Vault de NejoInc,
`08_SKILLS/ui-ux-pro-max/scripts/search.py`, con Python 3.13). Una Skill recomienda; no manda:
las reglas del enunciado (solo dibujar, nada de calcular) y las del proyecto (sin
dependencias, código para principiantes, accesibilidad) pesan más.

## 1. El producto

- **Qué es:** un tablero geoespacial de planeación de estaciones de emergencia y seguridad
  (CAI, tránsito, bomberos) para presentar en una feria y sustentar.
- **Qué importa:** que el mapa se lea al primer vistazo, que las cifras sean exactas y
  comparables, y que se pueda cambiar instancia, presupuesto, pesos y método en vivo.
- **Contexto de uso:** proyector o portátil, a veces con luz baja; también un teléfono.

## 2. Consultas hechas al buscador y lo que respondió

| # | Consulta | Dominio | Resultado principal |
|---|---|---|---|
| 1 | `geospatial emergency services dashboard dark mode dense data` con `--design-system --density 8 --motion 3 --variance 6` | sistema de diseño | Estilo **Dark Mode (OLED)**; paleta oscura (fondo `#020617`, tarjeta `#0E1223`, borde `#334155`, acento verde `#22C55E`); tipografía **Fira Code + Fira Sans** ("Dashboard Data"); evitar "modo claro por defecto" y "render lento"; lista previa a la entrega (sin emojis como iconos, foco visible, `prefers-reduced-motion`, 375/768/1024/1440 px). El patrón de página sugerido fue "Enterprise Gateway" (portal corporativo). |
| 2 | `public safety emergency operations map` | product | "Emergency SOS & Safety": estilo accesible + plano; secundarios Dark Mode (OLED) y Minimalism & Swiss Style; paleta "rojo de alerta + azul de seguridad". "Public Transit Guide": "Real-Time Monitoring + Map". |
| 3 | `dashboard data dense technical` | typography | 1) Fira Code + Fira Sans ("Code for data, Sans for labels"); 2) Exo + Roboto Mono; 3) Space Mono. |
| 4 | `grotesk display tabular figures` | google-fonts | Familjen Grotesk, Space Grotesk, Host Grotesk, Schibsted Grotesk (todas sans serif variables). |
| 5 | `emergency safety dark map` | color | "Ride Hailing / Transportation": fondo `#0F172A`, borde `rgba(255,255,255,0.08)`, "Map dark + route blue". "Emergency SOS": rojo `#DC2626` + azul `#2563EB`. |
| 6 | `map geospatial points layers` | chart | Mapa geográfico: con 1000 elementos o más, **Canvas/WebGL**; colores categóricos para tipos discretos; leyenda clara; "la ubicación no puede depender solo del color"; alternativa accesible: **tabla** + resumen; teclado: botones +/− de zoom. Librería recomendada: D3, Mapbox o **Leaflet**. |
| 7 | `dark mode contrast` | ux | Contraste mínimo 4,5:1; anillo de foco de 2 px con contraste 3:1 (`outline: 2px solid currentColor; outline-offset: 2px`). |
| 8 | `focus visible keyboard` | ux | Anillo de foco visible en todo control; no tapar el elemento con foco con paneles persistentes. |
| 9 | `collapsible side panel` | ux | **0 resultados.** Se reintentó una vez con `sidebar navigation drawer`: devolvió "Sticky Navigation" (no tapar contenido), "Keyboard Navigation" (orden del tabulador = orden visual, sin trampas de teclado) y "Breadcrumbs" (no aplica). Para el panel plegable no hubo coincidencia directa: la decisión (sección 4) se tomó con esas dos guías y criterio propio, y se declara así. |
| 10 | `loading long operation progress` | ux | Mostrar progreso (barra o pasos); nunca "sin indicación de progreso". |
| 11 | `reduced motion` | ux | Respetar `prefers-reduced-motion`; animar 1 o 2 elementos por vista como máximo. |
| 12 | `color blind not color only` | ux | No transmitir información solo con color: sumar icono o texto. |
| 13 | `data table numbers alignment` | ux | Tablas: contenedor con desplazamiento horizontal en pantallas chicas; separadores de miles. |
| 14 | `dashboard dense data` | style | "Data-Dense Dashboard": padding 8–12 px, filas de tabla de 36 px, encabezados fijos, resaltado de fila al pasar el cursor, exportar datos. |
| 15 | `touch target size` | ux | En web, el mínimo WCAG es 24×24 px (no confundir con 44 pt de iOS o 48 dp de Android). |
| 16 | `monospace tabular numbers` | google-fonts | Share Tech Mono, Monofett, Lekton… (fuera de tema; se descartó la consulta). |

## 3. Qué se adoptó y qué se descartó

### Adoptado

- **Oscuro primero** (consultas 1 y 2): el mapa es denso y los puntos de color se leen mejor
  sobre fondo oscuro; además se usa en proyector. Hay tema claro completo, porque algunos
  proyectores lavan los oscuros.
- **Tipografía:** **Fira Code** para las cifras (consultas 1 y 3: "Code for data"), con
  ligaduras desactivadas y dígitos de igual ancho, y **Familjen Grotesk** (consulta 4) para el
  texto en lugar de Fira Sans: es un grotesco con más carácter y da identidad sin perder
  legibilidad. Las dos tienen licencia **SIL OFL 1.1** (verificado en
  `data/google-font-licenses.json` de la Skill) y se sirven desde el propio servidor
  (`interfaz/web/vendor/fuentes`, con su archivo de licencia), sin Google Fonts en línea.
- **Leaflet con canvas** para los 5.300 incidentes de ciudad (consulta 6: con más de 1000
  puntos, canvas). **Tabla** de estaciones como alternativa accesible al mapa (consulta 6).
- **Color + forma** (consultas 6 y 12): cuadrado CAI, triángulo tránsito, círculo bomberos;
  incidentes cubiertos rellenos y no cubiertos como aros grises; lotes libres como rombos
  huecos. La forma se repite en la tabla, la leyenda y los pesos.
- **Densidad de tablero** (consultas 1 y 14): espaciado en pasos de 4 px, filas de 32 px,
  cifras alineadas a la derecha, resaltado de fila ↔ estación en el mapa.
- **Foco visible** de 2 px con separación de 2 px (consultas 7 y 8), con un color de anillo por
  tema (lima en oscuro, casi negro en claro) para mantener el contraste.
- **Progreso visible** (consulta 10): reloj en segundos y, en el exacto, barra frente al límite.
- **Movimiento mínimo** (consulta 11): transiciones de 140–220 ms solo en paneles, resaltado y
  `flyTo`; con `prefers-reduced-motion` todo se desactiva y el mapa salta sin animar.
- **Objetivos táctiles** de 40 px en botones, campos y contadores (por encima del mínimo web de
  24 px de la consulta 15); las filas de la leyenda miden 26 px con ratón y 40 px en pantallas
  táctiles (`pointer: coarse`).

### Descartado (y por qué)

- **Acento verde `#22C55E`** (consulta 1): es el verde genérico de los tableros y aquí se
  confundiría con un estado "bien/mal". Se eligió **un solo acento lima `#D4FF3F`**, el
  amarillo verdoso de los chalecos reflectivos de los servicios de emergencia: es cortante
  sobre negro y da identidad. En tema claro, para texto y barras se usa un oliva (`#4B6000` y
  `#5F7A00`) porque el lima no tiene contraste sobre fondo claro.
- **Paleta azul pizarra** (`#0F172A`, `#1E293B`) de las consultas 1 y 5: es la de casi toda
  plantilla generada; se usaron grises neutros casi negros (`#0A0B0D`, `#111317`) para que el
  único color sea el de los datos y el acento.
- **Patrón "Enterprise Gateway"** (consulta 1: héroe con video, logos de clientes, "Contact
  Sales"): es para páginas comerciales, no para una herramienta. No hay portada ni texto de
  "héroe": la página abre directamente en el mapa.
- **Rojo de alerta como color principal** (consultas 2 y 5): un tablero entero en rojo se lee
  como emergencia permanente; el rojo/bermellón queda solo para bomberos y para errores.
- **"Minimal glow"** (efecto de la consulta 1) y vidrio esmerilado: se usan superficies sólidas
  con bordes de 1 px; nada de brillos ni sombras difusas en los paneles.
- **GSAP** (fragmento de la consulta 1): no hace falta una librería de animación para tres
  transiciones CSS.
- **Fira Sans** para el texto: ver "Tipografía" arriba.

## 4. Decisiones propias (sin coincidencia directa en el buscador)

- **Paneles flotantes sobre el mapa a pantalla completa**: controles a la izquierda,
  resultados a la derecha, con bordes finos y esquinas de 2–4 px. Los controles de Leaflet y
  el encuadre automático se corren para no quedar debajo de los paneles abiertos.
- **El botón para reabrir el panel nunca se oculta**: vive en la barra superior fija (el
  problema de la versión anterior era que el botón estaba en una barra que el CSS escondía).
  Tiene `aria-expanded`, atajo de teclado (`[` y `]`) y el estado se recuerda en
  `localStorage` dentro de `try/catch`. Un panel cerrado queda con `visibility: hidden`, así
  sus campos salen del orden del tabulador (no hay trampas de teclado, consulta 9).
- **Fondos del mapa sin clave**: teselas estándar de OpenStreetMap con filtros CSS ("Calle",
  "Gris", "Oscuro") y "Sin mapa" (no pide teselas; sirve sin internet). Con tema oscuro el
  fondo por defecto es "Oscuro"; con claro, "Gris" (el mapa a todo color compite con los
  puntos).
- **Teléfono**: los paneles pasan a ser hojas que suben desde abajo; abrir una cierra la otra;
  los botones de la barra quedan solo con icono (el texto sigue para lectores de pantalla) y la
  leyenda empieza plegada.
- **Sello de marca**: un cuadrado lima con una esquina cortada, en la barra y como icono de la
  pestaña. Es el único elemento decorativo.

## 5. Tokens

Todos los valores están en `interfaz/web/tokens.css` (colores por tema, espaciado, radios,
tipografía, duraciones). Los colores de los tipos son:

| Tipo | Forma | Oscuro | Claro |
|---|---|---|---|
| hurto (CAI) | cuadrado | `#5B9BFF` | `#1F5FD1` |
| accidente (tránsito) | triángulo | `#F2A93B` | `#A86500` |
| incendio (bomberos) | círculo | `#FF6A3D` | `#CC3D14` |
| no cubierto | aro | `#6F7680` | `#8A9099` |
| lote libre | rombo hueco | `#9AA1AA` | `#6F757E` |

## 6. Cómo se verificó

Capturas con Chrome sin ventana (Chrome DevTools Protocol, viewport exacto) en 1440×900,
1024×768 y 390×844; tema oscuro y claro; panel abierto y cerrado (con la tecla `[` simulada y
comprobando `aria-expanded` y `localStorage`); estados vacío, de carga, de error y de
resultado; ciudad completa; y el mapa exportado abierto como archivo. No se probó con un lector
de pantalla real ni en navegadores distintos de Chrome.
