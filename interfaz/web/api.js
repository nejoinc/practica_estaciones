/*
  Llamadas a la API del servidor local (interfaz/servidor.py).

  Cada función devuelve una promesa con el JSON de respuesta. Si el
  servidor responde con error, se rechaza con un Error cuyo mensaje es el
  texto claro que mandó el servidor (nunca una traza).
*/

const Api = (function () {
  "use strict";

  const SIN_CONEXION =
    "No hay conexión con el servidor local. ¿Sigue abierta la consola con «py main.py interfaz»?";

  // Lee el cuerpo de una respuesta con error y saca su mensaje.
  async function mensajeDeError(respuesta) {
    try {
      const datos = await respuesta.json();
      if (datos && typeof datos.error === "string") {
        return datos.error;
      }
    } catch (error) {
      // El cuerpo no era JSON: se usa el mensaje genérico de abajo.
    }
    return "El servidor respondió con el código " + respuesta.status + ".";
  }

  // fetch con manejo de errores común; devuelve la Response si todo salió bien.
  async function pedir(ruta, opciones) {
    let respuesta;
    try {
      respuesta = await fetch(ruta, opciones);
    } catch (error) {
      throw new Error(SIN_CONEXION);
    }
    if (!respuesta.ok) {
      throw new Error(await mensajeDeError(respuesta));
    }
    return respuesta;
  }

  async function enviarJson(ruta, cuerpo) {
    return pedir(ruta, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cuerpo)
    });
  }

  async function instancias() {
    const respuesta = await pedir("/api/instancias", { method: "GET" });
    return respuesta.json();
  }

  async function instancia(nombreORuta) {
    const respuesta = await enviarJson("/api/instancia", { instancia: nombreORuta });
    return respuesta.json();
  }

  async function resolver(configuracion) {
    const respuesta = await enviarJson("/api/resolver", configuracion);
    return respuesta.json();
  }

  async function comparar(configuracion) {
    const respuesta = await enviarJson("/api/comparar", configuracion);
    return respuesta.json();
  }

  // El mapa exportado llega como archivo HTML: se devuelve como Blob para descargarlo.
  async function exportar(configuracion) {
    const respuesta = await enviarJson("/api/exportar", configuracion);
    return respuesta.blob();
  }

  return {
    instancias: instancias,
    instancia: instancia,
    resolver: resolver,
    comparar: comparar,
    exportar: exportar
  };
})();
