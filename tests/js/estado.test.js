// Pruebas de interfaz/web/estado.js: lectura de la dirección (#...) y preferencias.
const prueba = require("node:test");
const assert = require("node:assert/strict");
const Estado = require("../../interfaz/web/estado.js");

prueba("leerHash acepta solo valores conocidos", () => {
  const opciones = Estado.leerHash("#instancia=comuna&metodo=exacto&auto=1&panel=cerrado&tema=claro&fondo=sin");
  assert.equal(opciones.instancia, "comuna");
  assert.equal(opciones.metodo, "exacto");
  assert.equal(opciones.auto, true);
  assert.equal(opciones.panel, "cerrado");
  assert.equal(opciones.tema, "claro");
  assert.equal(opciones.fondo, "sin");
});

prueba("leerHash ignora valores inválidos", () => {
  const opciones = Estado.leerHash("#metodo=borrar&panel=quizas&presupuesto=-5&limite=abc&tema=rosa");
  assert.equal(opciones.metodo, null);
  assert.equal(opciones.panel, null);
  assert.equal(opciones.presupuesto, null);
  assert.equal(opciones.limite, null);
  assert.equal(opciones.tema, null);
  assert.equal(opciones.auto, false);
  assert.equal(Estado.leerHash("").instancia, null);
});

prueba("presupuesto y límite enteros desde la dirección", () => {
  const opciones = Estado.leerHash("#presupuesto=8000&limite=45");
  assert.equal(opciones.presupuesto, 8000);
  assert.equal(opciones.limite, 45);
});

prueba("alternar el panel siempre da un estado válido", () => {
  assert.equal(Estado.alternar("abierto"), "cerrado");
  assert.equal(Estado.alternar("cerrado"), "abierto");
  assert.equal(Estado.alternar(Estado.alternar("abierto")), "abierto");
});

prueba("fondo por defecto según el tema", () => {
  assert.equal(Estado.fondoPorDefecto("oscuro"), "oscuro");
  assert.equal(Estado.fondoPorDefecto("claro"), "gris");
});

prueba("preferencias no rompen sin localStorage", () => {
  // En Node no existe window: leer devuelve el valor por defecto y guardar no lanza error.
  global.window = {};
  assert.equal(Estado.Preferencias.leer("tema", "oscuro", Estado.TEMAS), "oscuro");
  assert.doesNotThrow(() => Estado.Preferencias.guardar("tema", "claro"));
  global.window = {
    localStorage: {
      datos: {},
      getItem(clave) { return clave in this.datos ? this.datos[clave] : null; },
      setItem(clave, valor) { this.datos[clave] = valor; }
    }
  };
  Estado.Preferencias.guardar("panel-controles", "cerrado");
  assert.equal(Estado.Preferencias.leer("panel-controles", "abierto", Estado.PANELES), "cerrado");
  window.localStorage.datos["estaciones.tema"] = "rosa";
  assert.equal(Estado.Preferencias.leer("tema", "oscuro", Estado.TEMAS), "oscuro");
  delete global.window;
});
