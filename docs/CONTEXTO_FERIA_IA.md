# Contexto del proyecto para agentes de IA

## Propósito estratégico

Este proyecto se prepara para la Feria de Ingeniería de Sistemas. El objetivo
no es únicamente que el código funcione: debemos presentar y vender una
aplicación impecable ante jurados que son docentes de Ingeniería de Sistemas.
Cada cambio debe conservar la confiabilidad matemática, la claridad de la
demostración y una experiencia visual y operativa convincente.

La aplicación resuelve dónde construir estaciones de atención sobre una red
vial, maximizando el valor de incidentes cubiertos sin exceder el presupuesto.
La instancia `ciudad` representa una escala grande y permite demostrar que las
heurísticas producen propuestas útiles aun cuando el óptimo exacto requiera
mucho tiempo.

## Público y oportunidad

El destinatario principal es la Alcaldía de Medellín, aunque el producto debe
ser explicable y adaptable a Medellín o a cualquier otra ciudad. El problema
tiene aplicaciones reales en planeación de seguridad, tránsito, bomberos,
respuesta a emergencias y distribución de recursos públicos.

Al presentar la solución, conectar siempre tres niveles:

1. **Decisión pública:** dónde invertir un presupuesto limitado.
2. **Evidencia técnica:** red vial dirigida, incidentes ponderados, coberturas
   calculadas y restricciones verificables.
3. **Resultado accionable:** una propuesta de estaciones, su costo, cobertura,
   mapa y comparación de alternativas.

## Reglas que los agentes deben preservar

- No confundir una heurística con una prueba de optimalidad.
- `exacto` usa Branch & Bound y puede terminar antes si certifica el óptimo o
  continuar hasta el límite que el usuario indique.
- En `ciudad`, el límite de `exacto` y `propia_ls` es exactamente el valor
  elegido en la interfaz; no agregar límites internos por tamaño de instancia.
- Si se agota el tiempo, entregar la mejor propuesta factible encontrada y
  marcarla como no certificada.
- Mantener visible la diferencia entre `Óptimo certificado`, `Mejor
  encontrada` y `Heurística`.
- Validar entradas, conservar la seguridad de la API y evitar que una mejora
  de presentación altere los resultados del núcleo.
- Probar cambios en la API local y en el adaptador de Vercel cuando afecten el
  flujo de resolución.

## Forma de trabajar

Antes de editar, revisar el núcleo en `estaciones/`, la interfaz en
`interfaz/`, las pruebas y la documentación de rendimiento. Preferir cambios
pequeños, explicables durante la sustentación y respaldados por pruebas.
Actualizar la documentación relacionada cuando cambie el comportamiento.

La demostración debe poder contar esta historia: la ciudad entrega datos,
presupuesto y prioridades; la aplicación calcula coberturas sobre la red,
compara estrategias y muestra una inversión defendible para los tomadores de
decisión. La calidad esperada es de producto demostrable ante jurados, no solo
de ejercicio académico.
