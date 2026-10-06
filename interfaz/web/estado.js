/*
  Estado de la interfaz y preferencias guardadas.

  - leerHash: lee parámetros de la dirección (#instancia=comuna&auto=1...)
    para abrir la página ya configurada (útil en la feria y para capturas).
  - Preferencias: tema, fondo y paneles abiertos, en localStorage. Todo va
    dentro de try/catch: en modo privado o con almacenamiento bloqueado,
    la página funciona igual, solo que no recuerda.

  Funciones puras salvo Preferencias: se prueban con Node (tests/js).
*/

const Estado = (function () {
  "use strict";

  const METODOS = ["base", "propia", "propia_ls", "exacto"];
  const TEMAS = ["oscuro", "claro"];
  const FONDOS = ["calle", "gris", "oscuro", "sin"];
  const PANELES = ["abierto", "cerrado"];
  const PREFIJO = "estaciones.";

  // Solo se aceptan valores de una lista conocida; lo demás se ignora.
  function valorPermitido(valor, permitidos) {
    if (permitidos.indexOf(valor) >= 0) {
      return valor;
    }
    return null;
  }

  // Entero no negativo escrito como texto ("12000"); si no lo es, null.
  function enteroNoNegativo(texto) {
    if (!/^[0-9]{1,10}$/.test(texto || "")) {
      return null;
    }
    return Number(texto);
  }

  // Lee "#clave=valor&clave2=valor2" y devuelve solo las claves conocidas y válidas.
  function leerHash(hash) {
    const texto = (hash || "").replace(/^#/, "");
    const parametros = new URLSearchParams(texto);
    const instancia = parametros.get("instancia");
    return {
      instancia: instancia && instancia.length <= 500 ? instancia : null,
      metodo: valorPermitido(parametros.get("metodo"), METODOS),
      tema: valorPermitido(parametros.get("tema"), TEMAS),
      fondo: valorPermitido(parametros.get("fondo"), FONDOS),
      panel: valorPermitido(parametros.get("panel"), PANELES),
      resultados: valorPermitido(parametros.get("resultados"), PANELES),
      presupuesto: enteroNoNegativo(parametros.get("presupuesto")),
      limite: enteroNoNegativo(parametros.get("limite")),
      auto: parametros.get("auto") === "1",
      comparar: parametros.get("comparar") === "1"
    };
  }

  // El fondo del mapa sigue al tema, salvo que el usuario haya elegido otro.
  // En claro se usa "gris": el mapa de calles a todo color compite con los puntos.
  function fondoPorDefecto(tema) {
    return tema === "claro" ? "gris" : "oscuro";
  }

  // Abierto <-> cerrado.
  function alternar(estadoDelPanel) {
    return estadoDelPanel === "abierto" ? "cerrado" : "abierto";
  }

  // localStorage con try/catch: nunca rompe la página.
  const Preferencias = {
    leer: function (clave, porDefecto, permitidos) {
      try {
        const valor = window.localStorage.getItem(PREFIJO + clave);
        if (valor !== null && permitidos.indexOf(valor) >= 0) {
          return valor;
        }
      } catch (error) {
        // Almacenamiento no disponible (modo privado, bloqueado): se usa el valor por defecto.
      }
      return porDefecto;
    },
    guardar: function (clave, valor) {
      try {
        window.localStorage.setItem(PREFIJO + clave, valor);
      } catch (error) {
        // Sin almacenamiento la preferencia solo dura mientras la página esté abierta.
      }
    }
  };

  return {
    METODOS: METODOS,
    TEMAS: TEMAS,
    FONDOS: FONDOS,
    PANELES: PANELES,
    leerHash: leerHash,
    fondoPorDefecto: fondoPorDefecto,
    alternar: alternar,
    Preferencias: Preferencias
  };
})();

if (typeof module !== "undefined" && module.exports) {
  module.exports = Estado;
}
