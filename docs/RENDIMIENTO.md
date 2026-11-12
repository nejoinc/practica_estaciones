# Rendimiento y política de cálculo

## Objetivo

La aplicación debe responder con una propuesta útil durante una exposición en
vivo. La calidad matemática sigue siendo importante, pero no se deja que una
búsqueda exacta o una mejora local prolongada congele la interfaz.

La política distingue dos entornos:

- **Local/estudio:** se conservan todos los métodos y los límites que el
  usuario indique. Sirve para experimentar, validar y estudiar.
- **Vercel/producción:** se aplican límites operativos para priorizar una
  respuesta fluida y honesta.

## Medición de referencia

La medición se hizo ejecutando Python 3.14 sobre las instancias versionadas.
El tiempo de `Modelo` incluye lectura, construcción del grafo y precálculo de
las coberturas; los tiempos de método se miden después de tener el modelo.

| Instancia | Lotes | Incidentes | Modelo | Base | Propia | Propia + LS sin límite | Exacto |
|---|---:|---:|---:|---:|---:|---:|---:|
| pequena | 5 | 18 | 0,002 s | <0,001 s | <0,001 s | 0,002 s | 0,003 s |
| comuna | 15 | 913 | 0,2 s | <0,001 s | <0,001 s | 0,13 s | 1,16 s |
| ciudad | 80 | 5300 | 1,6 s | <0,1 s | <0,1 s | 40–50 s | no viable sin límite |

Los tiempos dependen del equipo y no son un certificado universal. La utilidad
de la medición es identificar el orden de magnitud y detectar regresiones.

## Política pública de Vercel

La política está implementada en
[`interfaz/vercel_app.py`](../interfaz/vercel_app.py):

1. Hasta 30 lotes:
   - `exacto` está disponible;
   - `propia_ls` respeta el límite recibido.
2. Más de 30 lotes:
   - `exacto` y `propia_ls` reciben como máximo 30 segundos;
   - `comparar` ejecuta los cuatro métodos con el mismo límite efectivo.
3. La respuesta mantiene el método real utilizado y el campo
   `optimo_certificado`.

El límite de `propia_ls` se aplica en
[`estaciones/ejecucion.py`](../estaciones/ejecucion.py), no solamente en la
capa HTTP. Así todas las entradas que usan `ejecutar_metodo` respetan el
límite.

## Interpretación para la sustentación

- `Óptimo certificado`: Branch & Bound terminó todo el árbol y la cota
  demuestra que no existe una propuesta mejor.
- `Mejor encontrada`: se agotó el límite; la propuesta es factible, pero no se
  afirma que sea óptima.
- `Heurística`: se construyó una propuesta con una regla rápida; no hay
  certificado de optimalidad.

La frase recomendada es:

> En escalas pequeñas demostramos el óptimo; en la escala grande entregamos
> una solución factible y mejorable en un tiempo acotado, sin confundir rapidez
> con una garantía matemática que no tenemos.

## Pruebas que protegen la política

[`tests/test_vercel.py`](../tests/test_vercel.py) verifica que:

- `ciudad + exacto` devuelve la mejor propuesta encontrada hasta 30 segundos;
- `ciudad + comparar` ejecuta también `exacto`, con el mismo límite de 30 segundos;
- las respuestas siguen siendo JSON y conservan el contrato de la interfaz.

Las pruebas algorítmicas existentes siguen comprobando el óptimo mediante
fuerza bruta en instancias pequeñas y aleatorias.
