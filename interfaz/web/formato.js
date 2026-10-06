/*
  Formato de cifras y textos para la pantalla.

  Funciones puras (no tocan la página): por eso se prueban con Node en
  tests/js/formato.test.js. Se usan en la interfaz y en el mapa exportado.
*/

const Formato = (function () {
  "use strict";

  // Separa los miles con punto, como se escribe en Colombia: 12000 -> "12.000".
  // Se hace a mano para no depender del idioma configurado en el navegador.
  function numero(valor) {
    const entero = Math.round(Number(valor));
    const signo = entero < 0 ? "-" : "";
    const digitos = String(Math.abs(entero));
    let resultado = "";
    for (let posicion = 0; posicion < digitos.length; posicion += 1) {
      const quedan = digitos.length - posicion;
      if (posicion > 0 && quedan % 3 === 0) {
        resultado += ".";
      }
      resultado += digitos[posicion];
    }
    return signo + resultado;
  }

  // Número con decimales y coma decimal: (0.6123, 2) -> "0,61".
  function decimal(valor, decimales) {
    return Number(valor).toFixed(decimales).replace(".", ",");
  }

  // Porcentaje de parte sobre total con un decimal: (486, 612) -> "79,4 %".
  // Si el total es 0 no hay porcentaje que mostrar.
  function porcentaje(parte, total) {
    if (!total) {
      return "—";
    }
    return decimal((parte / total) * 100, 1) + " %";
  }

  // Fracción entre 0 y 1 (para el ancho de las barras); nunca se sale del rango.
  function fraccion(parte, total) {
    if (!total || total <= 0) {
      return 0;
    }
    const valor = parte / total;
    if (valor < 0) {
      return 0;
    }
    if (valor > 1) {
      return 1;
    }
    return valor;
  }

  // Tiempo legible: menos de 10 s con dos decimales, más con uno.
  // Lo que tarda menos de una centésima se muestra como "< 0,01 s" (no "0,00 s").
  function segundos(valor) {
    if (valor < 0.01) {
      return "< 0,01 s";
    }
    if (valor < 10) {
      return decimal(valor, 2) + " s";
    }
    return decimal(valor, 1) + " s";
  }

  // Nombre corto de cada método para botones y tablas.
  const NOMBRES_DE_METODO = {
    base: "Base",
    propia: "Propia",
    propia_ls: "Propia + LS",
    exacto: "Exacto (B&B)"
  };

  function nombreDeMetodo(metodo) {
    return NOMBRES_DE_METODO[metodo] || metodo;
  }

  // "hurto" -> "Hurto" (para etiquetas).
  function capitalizar(texto) {
    if (!texto) {
      return "";
    }
    return texto.charAt(0).toUpperCase() + texto.slice(1);
  }

  return {
    numero: numero,
    decimal: decimal,
    porcentaje: porcentaje,
    fraccion: fraccion,
    segundos: segundos,
    nombreDeMetodo: nombreDeMetodo,
    capitalizar: capitalizar
  };
})();

// En Node (pruebas) se exporta como módulo; en el navegador queda como variable global.
if (typeof module !== "undefined" && module.exports) {
  module.exports = Formato;
}
