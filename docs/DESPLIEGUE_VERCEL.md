# Despliegue en Vercel

Esta guía describe el primer corte del despliegue: la interfaz existente se
sirve como archivos estáticos y la API se ejecuta como una función Python
serverless. No cambia la interfaz visual ni duplica los algoritmos.

## Arquitectura

```text
navegador
  ├── /, /app.js, /mapa.js, /vendor/...  -> interfaz/web/
  └── /api/...                           -> api/index.py
                                             └── interfaz/vercel_app.py
                                                 └── estaciones/
```

`interfaz/servidor.py` continúa siendo el servidor local de la feria y las
pruebas HTTP existentes. `interfaz/vercel_app.py` reutiliza su validación,
modelo, métodos, exportación y formato de respuestas, pero no abre un puerto
ni llama a `serve_forever`.

## Requisitos

- Cuenta de Vercel.
- Node.js y la CLI de Vercel.
- Git.
- Python 3.10 o superior para las comprobaciones locales.

El proyecto no necesita paquetes de Python externos. `requirements.txt` existe
para dejar explícita esa decisión al runtime.

## Comprobaciones antes de publicar

Desde la raíz del repositorio:

```text
python3 -m unittest discover -s tests
node --test tests/js/*.test.js
python3 -m py_compile api/index.py interfaz/vercel_app.py
```

En Windows, el primer comando equivale a:

```text
py -m unittest discover -s tests
```

El test de `tests/test_vercel.py` ejercita la aplicación WSGI sin depender de
una red ni de una cuenta de Vercel.

## Publicación

1. Instalar la CLI:

   ```text
   npm install -g vercel
   ```

2. Autenticarse:

   ```text
   vercel login
   ```

3. Desde la raíz del proyecto, crear un despliegue de prueba:

   ```text
   vercel
   ```

4. Confirmar que el directorio raíz es este repositorio y que no se agregará
   un framework frontend. `vercel.json` define la función Python y las rutas
   de archivos estáticos.

5. Publicar producción cuando las pruebas manuales pasen:

   ```text
   vercel --prod
   ```

6. Comprobar estas rutas en el dominio generado:

   ```text
   /
   /api/instancias
   ```

   Las demás rutas de API se prueban desde la interfaz, porque son solicitudes
   `POST`.

## Restricción de instancias en producción

El servidor local permite escribir una ruta absoluta para una carpeta nueva.
La función pública no lo hace: solo acepta `pequena`, `comuna` y `ciudad`,
que son las instancias versionadas en `instancias/`. Una función cloud no
puede leer una carpeta del computador del visitante.

La opción de carpeta local se conserva para el modo local. Para publicar
instancias nuevas en Vercel, primero se incorporan al repositorio; una futura
rebanada puede agregar carga de archivos con límites y validación explícitos.

## Rendimiento y límites actuales

- En instancias de más de 30 lotes, la API pública limita `propia_ls` y
  `exacto` a 30 segundos como máximo. Devuelven la mejor propuesta factible
  encontrada dentro de ese tiempo; el exacto no se presenta como certificado
  si la búsqueda no termina.
- En `ciudad`, `comparar` ejecuta los cuatro métodos. Las heurísticas rápidas
  terminan antes y `propia_ls` y `exacto` comparten el límite de 30 segundos.
- El estado de modelos y resultados es un caché oportunista de una instancia
  serverless; no se considera persistente.
- `/api/exportar` recalcula si la petición cae en otra instancia que no tiene
  el resultado en memoria.
- `ciudad + exacto` es válido para probar la búsqueda acotada; la interfaz
  muestra explícitamente cuando entrega una mejor propuesta no certificada.

La lógica de esta política está en `interfaz/vercel_app.py`; el servidor local
conserva el comportamiento completo para estudiar y experimentar con todos
los métodos.

## Verificación manual posterior al despliegue

1. Abrir la URL desde una ventana privada.
2. Cargar `pequena` y resolver con `exacto`.
3. Cambiar a `ciudad` y resolver con `propia_ls`.
4. Cambiar tema, presupuesto y pesos.
5. Descargar CSV y mapa.
6. Repetir desde un teléfono y desde la red de la feria.

No se debe afirmar “óptimo” cuando la respuesta indique que el exacto no quedó
certificado. La interfaz debe conservar la diferencia entre una heurística,
una mejor solución encontrada y un óptimo certificado.
