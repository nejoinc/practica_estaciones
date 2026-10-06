// Pruebas de interfaz/web/formato.js con el ejecutor de pruebas de Node (node --test).
const prueba = require("node:test");
const assert = require("node:assert/strict");
const Formato = require("../../interfaz/web/formato.js");

prueba("numero separa los miles con punto", () => {
  assert.equal(Formato.numero(0), "0");
  assert.equal(Formato.numero(850), "850");
  assert.equal(Formato.numero(12000), "12.000");
  assert.equal(Formato.numero(1234567), "1.234.567");
  assert.equal(Formato.numero(-1574), "-1.574");
});

prueba("porcentaje usa coma decimal y no divide por cero", () => {
  assert.equal(Formato.porcentaje(519, 562), "92,3 %");
  assert.equal(Formato.porcentaje(31, 31), "100,0 %");
  assert.equal(Formato.porcentaje(0, 0), "—");
});

prueba("fraccion queda entre 0 y 1", () => {
  assert.equal(Formato.fraccion(11700, 12000), 0.975);
  assert.equal(Formato.fraccion(5, 0), 0);
  assert.equal(Formato.fraccion(20, 10), 1);
  assert.equal(Formato.fraccion(-1, 10), 0);
});

prueba("segundos legibles", () => {
  assert.equal(Formato.segundos(0.001), "< 0,01 s");
  assert.equal(Formato.segundos(0.6123), "0,61 s");
  assert.equal(Formato.segundos(27.04), "27,0 s");
});

prueba("nombres de método y mayúscula inicial", () => {
  assert.equal(Formato.nombreDeMetodo("propia_ls"), "Propia + LS");
  assert.equal(Formato.nombreDeMetodo("otro"), "otro");
  assert.equal(Formato.capitalizar("hurto"), "Hurto");
  assert.equal(Formato.capitalizar(""), "");
});
