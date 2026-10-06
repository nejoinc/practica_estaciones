/*
  Interfaz: conecta los controles, la API y el mapa.

  Separación de responsabilidades:
  - api.js      habla con el servidor (que es quien calcula todo).
  - mapa.js     dibuja con Leaflet.
  - estado.js   lee la dirección (#...) y guarda preferencias.
  - formato.js  da formato a las cifras.
  - app.js      (este archivo) reacciona a lo que hace el usuario.

  Ningún dato de la instancia se inserta como HTML: siempre textContent.
*/

(function () {
  "use strict";

  const OTRA_CARPETA = "__otra__";
  const LOTES_PARA_AVISAR_EXACTO = 40;
  const PRESUPUESTO_MAXIMO = 1000000000;
  const PESO_MAXIMO = 1000000;
  const LIMITE_MAXIMO = 600;
  const LIMITE_POR_DEFECTO = 30;
  const CONSULTA_TELEFONO = "(max-width: 720px)";

  const $ = function (id) {
    return document.getElementById(id);
  };

  const elementos = {
    cuerpo: document.body,
    botonControles: $("boton-controles"),
    botonResultados: $("boton-resultados"),
    botonTema: $("boton-tema"),
    panelControles: $("panel-controles"),
    panelResultados: $("panel-resultados"),
    formulario: $("formulario"),
    instancia: $("instancia"),
    bloqueRuta: $("bloque-ruta"),
    ruta: $("ruta"),
    cargarRuta: $("cargar-ruta"),
    infoInstancia: $("info-instancia"),
    errorInstancia: $("error-instancia"),
    presupuesto: $("presupuesto"),
    presupuestoRango: $("presupuesto-rango"),
    ayudaPresupuesto: $("ayuda-presupuesto"),
    restablecerPresupuesto: $("restablecer-presupuesto"),
    pesos: $("pesos"),
    restablecerPesos: $("restablecer-pesos"),
    bloqueLimite: $("bloque-limite"),
    limite: $("limite"),
    avisoExacto: $("aviso-exacto"),
    errorFormulario: $("error-formulario"),
    calcular: $("calcular"),
    vistaVacia: $("vista-vacia"),
    vistaCarga: $("vista-carga"),
    vistaError: $("vista-error"),
    vistaResultado: $("vista-resultado"),
    cargaTitulo: $("carga-titulo"),
    cargaSegundos: $("carga-segundos"),
    cargaLimite: $("carga-limite"),
    cargaBarra: $("carga-barra"),
    cargaRelleno: $("carga-relleno"),
    cargaNota: $("carga-nota"),
    errorTexto: $("error-texto"),
    reintentar: $("reintentar"),
    metaResultado: $("meta-resultado"),
    sello: $("sello"),
    avisoDesactualizado: $("aviso-desactualizado"),
    valor: $("valor"),
    costoTexto: $("costo-texto"),
    costoRelleno: $("costo-relleno"),
    cantidadEstaciones: $("cantidad-estaciones"),
    cantidadCubiertos: $("cantidad-cubiertos"),
    tiempo: $("tiempo"),
    cobertura: $("cobertura"),
    tablaCuerpo: $("tabla-cuerpo"),
    tablaPie: $("tabla-pie"),
    descargarCsv: $("descargar-csv"),
    descargarMapa: $("descargar-mapa"),
    comparar: $("comparar"),
    mensajeAcciones: $("mensaje-acciones"),
    bloqueComparacion: $("bloque-comparacion"),
    comparacionCuerpo: $("comparacion-cuerpo"),
    comparacionNota: $("comparacion-nota"),
    anuncio: $("anuncio")
  };

  const estado = {
    claveInstancia: null,
    instancia: null,
    resultado: null,
    configuracionUsada: null,
    calculando: false,
    reintentar: null,
    tema: "oscuro",
    fondoElegido: false,
    filasPorLote: {},
    vista: null,
    reloj: null
  };

  // ---------------------------------------------------------------- utilidades

  function esTelefono() {
    return window.matchMedia(CONSULTA_TELEFONO).matches;
  }

  function elemento(etiqueta, clase, texto) {
    const nodo = document.createElement(etiqueta);
    if (clase) {
      nodo.className = clase;
    }
    if (texto !== undefined && texto !== null) {
      nodo.textContent = String(texto);
    }
    return nodo;
  }

  function anunciar(texto) {
    elementos.anuncio.textContent = texto;
  }

  // Forma de un tipo según los datos del mapa (cuadrado, triángulo, círculo...).
  function formaDeTipo(tipo) {
    const tipos = estado.instancia ? estado.instancia.mapa.tipos : [];
    for (let posicion = 0; posicion < tipos.length; posicion += 1) {
      if (tipos[posicion].tipo === tipo) {
        return tipos[posicion].forma;
      }
    }
    return "rombo";
  }

  function simboloDeTipo(tipo) {
    const simbolo = elemento("span", "simbolo marca " + MapaEstaciones.claseDeTipo(tipo));
    simbolo.innerHTML = MapaEstaciones.svgDeForma(formaDeTipo(tipo)); // SVG fijo, sin datos del CSV.
    return simbolo;
  }

  function nombreParaArchivo(texto) {
    return String(texto).replace(/[^A-Za-z0-9_-]/g, "_");
  }

  // Descarga un Blob con el nombre indicado (enlace temporal).
  function descargar(blob, nombreArchivo) {
    const direccion = URL.createObjectURL(blob);
    const enlace = document.createElement("a");
    enlace.href = direccion;
    enlace.download = nombreArchivo;
    document.body.appendChild(enlace);
    enlace.click();
    enlace.remove();
    setTimeout(function () {
      URL.revokeObjectURL(direccion);
    }, 1000);
  }

  // ---------------------------------------------------------------- paneles

  // Abre o cierra un panel. El botón de la barra superior nunca se oculta,
  // así que siempre hay forma de volver a abrirlo.
  function ponerPanel(nombre, estadoDelPanel, guardar) {
    const panel = nombre === "controles" ? elementos.panelControles : elementos.panelResultados;
    const boton = nombre === "controles" ? elementos.botonControles : elementos.botonResultados;
    const abierto = estadoDelPanel === "abierto";
    panel.classList.toggle("cerrado", !abierto);
    elementos.cuerpo.classList.toggle(nombre + "-abierto", abierto);
    boton.setAttribute("aria-expanded", String(abierto));
    if (guardar) {
      Estado.Preferencias.guardar("panel-" + nombre, estadoDelPanel);
    }
    // En el teléfono las dos hojas ocupan el mismo lugar: abrir una cierra la otra.
    if (abierto && esTelefono()) {
      const otro = nombre === "controles" ? "resultados" : "controles";
      if (elementos.cuerpo.classList.contains(otro + "-abierto")) {
        ponerPanel(otro, "cerrado", false);
      }
    }
  }

  function alternarPanel(nombre) {
    const abierto = elementos.cuerpo.classList.contains(nombre + "-abierto");
    ponerPanel(nombre, Estado.alternar(abierto ? "abierto" : "cerrado"), true);
  }

  // Cuánto tapan los paneles: el encuadre automático deja los puntos en la zona libre.
  function margenesDelMapa() {
    if (esTelefono()) {
      // En el teléfono el panel abierto es una hoja que tapa la parte de abajo.
      let abajo = 24;
      if (elementos.cuerpo.classList.contains("controles-abierto")) {
        abajo += elementos.panelControles.offsetHeight;
      } else if (elementos.cuerpo.classList.contains("resultados-abierto")) {
        abajo += elementos.panelResultados.offsetHeight;
      }
      return { arribaIzquierda: [24, 72], abajoDerecha: [24, abajo] };
    }
    const estilos = getComputedStyle(document.documentElement);
    const anchoControles = parseInt(estilos.getPropertyValue("--ancho-controles"), 10);
    const anchoResultados = parseInt(estilos.getPropertyValue("--ancho-resultados"), 10);
    let izquierda = 40;
    if (elementos.cuerpo.classList.contains("controles-abierto")) {
      izquierda += anchoControles;
    }
    // La leyenda ocupa la esquina inferior izquierda: en pantallas anchas se le deja espacio.
    if (window.innerWidth >= 1280) {
      izquierda += 230;
    }
    let derecha = 72;
    if (elementos.cuerpo.classList.contains("resultados-abierto")) {
      derecha += anchoResultados;
    }
    return { arribaIzquierda: [izquierda, 80], abajoDerecha: [derecha, 40] };
  }

  // ---------------------------------------------------------------- tema y fondo

  function aplicarTema(tema, guardar) {
    estado.tema = tema;
    document.documentElement.dataset.tema = tema;
    const otro = tema === "oscuro" ? "claro" : "oscuro";
    elementos.botonTema.setAttribute("aria-label", "Cambiar a tema " + otro);
    elementos.botonTema.title = "Cambiar a tema " + otro;
    if (guardar) {
      Estado.Preferencias.guardar("tema", tema);
    }
    if (estado.vista) {
      if (!estado.fondoElegido) {
        MapaEstaciones.cambiarFondo(estado.vista, Estado.fondoPorDefecto(tema));
      }
      // Los puntos del canvas toman los colores del tema nuevo.
      MapaEstaciones.redibujar(estado.vista);
    }
  }

  function alCambiarFondo(fondo) {
    estado.fondoElegido = true;
    Estado.Preferencias.guardar("fondo", fondo);
  }

  // ---------------------------------------------------------------- vistas del panel de resultados

  function mostrarVista(nombre) {
    elementos.vistaVacia.hidden = nombre !== "vacia";
    elementos.vistaCarga.hidden = nombre !== "carga";
    elementos.vistaError.hidden = nombre !== "error";
    elementos.vistaResultado.hidden = nombre !== "resultado";
    elementos.panelResultados.setAttribute("aria-busy", String(nombre === "carga"));
  }

  function detenerReloj() {
    if (estado.reloj) {
      clearInterval(estado.reloj);
      estado.reloj = null;
    }
  }

  // Estado de carga con reloj: el cálculo corre en el servidor y la página sigue respondiendo.
  function mostrarCarga(configuracion) {
    mostrarVista("carga");
    const nombre = Formato.nombreDeMetodo(configuracion.metodo);
    elementos.cargaTitulo.textContent = nombre + " · " + estado.instancia.nombre;
    const conLimite = configuracion.metodo === "exacto";
    elementos.cargaBarra.classList.toggle("indeterminada", !conLimite);
    elementos.cargaLimite.textContent = conLimite ? "de " + configuracion.limite_segundos + " s" : "";
    if (conLimite) {
      elementos.cargaNota.textContent =
        "Si llega al límite, entrega la mejor propuesta encontrada y avisa que no está certificada.";
    } else if (configuracion.metodo === "propia_ls" && estado.instancia.lotes >= LOTES_PARA_AVISAR_EXACTO) {
      elementos.cargaNota.textContent = "La mejora local en una instancia grande puede tardar unos segundos.";
    } else {
      elementos.cargaNota.textContent = "El cálculo corre en el servidor local; la página sigue respondiendo.";
    }
    const inicio = performance.now();
    elementos.cargaRelleno.style.width = conLimite ? "0%" : "";
    detenerReloj();
    estado.reloj = setInterval(function () {
      const segundos = (performance.now() - inicio) / 1000;
      elementos.cargaSegundos.textContent = Formato.decimal(segundos, 1) + " s";
      if (conLimite) {
        const fraccion = Formato.fraccion(segundos, configuracion.limite_segundos);
        elementos.cargaRelleno.style.width = (fraccion * 100).toFixed(1) + "%";
        elementos.cargaBarra.setAttribute("aria-valuenow", String(Math.round(fraccion * 100)));
      }
    }, 100);
    elementos.cargaSegundos.textContent = "0,0 s";
  }

  function mostrarError(mensaje, reintento) {
    detenerReloj();
    mostrarVista("error");
    elementos.errorTexto.textContent = mensaje;
    estado.reintentar = reintento;
    elementos.reintentar.hidden = !reintento;
    anunciar("Error: " + mensaje);
  }

  // ---------------------------------------------------------------- instancia

  function llenarSelector(nombres, elegido) {
    elementos.instancia.replaceChildren();
    nombres.forEach(function (nombre) {
      const opcion = elemento("option", null, nombre);
      opcion.value = nombre;
      elementos.instancia.appendChild(opcion);
    });
    const otra = elemento("option", null, "Otra carpeta…");
    otra.value = OTRA_CARPETA;
    elementos.instancia.appendChild(otra);
    elementos.instancia.value = elegido;
  }

  function mostrarErrorDeInstancia(mensaje) {
    elementos.errorInstancia.textContent = mensaje;
    elementos.errorInstancia.hidden = !mensaje;
  }

  // Pide la instancia al servidor, llena los controles con sus valores y dibuja la vista previa.
  async function cargarInstancia(clave) {
    mostrarErrorDeInstancia("");
    elementos.infoInstancia.textContent = "Cargando…";
    try {
      const datos = await Api.instancia(clave);
      estado.claveInstancia = clave;
      estado.instancia = datos;
      elementos.calcular.disabled = false;
      estado.resultado = null;
      estado.configuracionUsada = null;
      llenarControles(datos);
      MapaEstaciones.dibujar(estado.vista, datos.mapa, true);
      mostrarVista("vacia");
      return true;
    } catch (error) {
      estado.claveInstancia = null;
      estado.instancia = null;
      elementos.calcular.disabled = true;
      elementos.infoInstancia.textContent = "";
      mostrarErrorDeInstancia(error.message);
      mostrarError(error.message, function () {
        cargarInstancia(clave);
      });
      return false;
    }
  }

  function llenarControles(datos) {
    elementos.infoInstancia.textContent =
      Formato.numero(datos.lotes) + " lotes · " + Formato.numero(datos.incidentes) + " incidentes";
    const maximo = Math.max(1000, Math.ceil((datos.presupuesto * 2) / 100) * 100);
    elementos.presupuestoRango.max = String(maximo);
    ponerPresupuesto(datos.presupuesto);
    elementos.ayudaPresupuesto.textContent =
      "Valor de parametros.json: " + Formato.numero(datos.presupuesto) + " millones";
    construirPesos(datos.tipos);
    const avisar = datos.lotes >= LOTES_PARA_AVISAR_EXACTO;
    elementos.avisoExacto.hidden = !avisar;
    elementos.avisoExacto.textContent = avisar
      ? "Con " + datos.lotes + " lotes el óptimo puede no certificarse a tiempo: se mostrará la mejor propuesta hallada dentro del límite."
      : "";
    actualizarAvisoDesactualizado();
  }

  // ---------------------------------------------------------------- presupuesto y pesos

  function ponerPresupuesto(valor) {
    elementos.presupuesto.value = String(valor);
    elementos.presupuestoRango.value = String(Math.min(valor, Number(elementos.presupuestoRango.max)));
  }

  function construirPesos(tipos) {
    elementos.pesos.replaceChildren();
    tipos.forEach(function (tipo) {
      elementos.pesos.appendChild(filaDePeso(tipo));
    });
  }

  // Fila: forma del tipo, nombre, y botones − / + alrededor del número.
  function filaDePeso(tipo) {
    const fila = elemento("div", "peso");
    fila.appendChild(simboloDeTipo(tipo.tipo));
    const nombre = elemento("span", "peso-nombre", Formato.capitalizar(tipo.tipo));
    nombre.appendChild(elemento("small", null, tipo.estacion + " · por defecto " + tipo.peso));
    fila.appendChild(nombre);
    const contador = elemento("div", "contador");
    const menos = elemento("button", null, "−");
    menos.type = "button";
    menos.setAttribute("aria-label", "Bajar el peso de " + tipo.tipo);
    const campo = document.createElement("input");
    campo.type = "number";
    campo.min = "0";
    campo.max = String(PESO_MAXIMO);
    campo.step = "1";
    campo.inputMode = "numeric";
    campo.value = String(tipo.peso);
    campo.dataset.tipo = tipo.tipo;
    campo.dataset.porDefecto = String(tipo.peso);
    campo.setAttribute("aria-label", "Peso de " + tipo.tipo);
    const mas = elemento("button", null, "+");
    mas.type = "button";
    mas.setAttribute("aria-label", "Subir el peso de " + tipo.tipo);
    menos.addEventListener("click", function () {
      cambiarPeso(campo, -1);
    });
    mas.addEventListener("click", function () {
      cambiarPeso(campo, 1);
    });
    campo.addEventListener("input", actualizarAvisoDesactualizado);
    contador.appendChild(menos);
    contador.appendChild(campo);
    contador.appendChild(mas);
    fila.appendChild(contador);
    return fila;
  }

  function cambiarPeso(campo, paso) {
    const actual = parseInt(campo.value, 10);
    const base = Number.isFinite(actual) ? actual : 0;
    campo.value = String(Math.min(PESO_MAXIMO, Math.max(0, base + paso)));
    actualizarAvisoDesactualizado();
  }

  function camposDePeso() {
    return Array.prototype.slice.call(elementos.pesos.querySelectorAll("input"));
  }

  // ---------------------------------------------------------------- leer y validar la configuración

  function metodoElegido() {
    const marcado = elementos.formulario.querySelector('input[name="metodo"]:checked');
    return marcado ? marcado.value : "propia_ls";
  }

  // Entero dentro de [minimo, maximo] o null (para mostrar el error junto al campo).
  function enteroEnRango(texto, minimo, maximo) {
    if (!/^[0-9]+$/.test(String(texto).trim())) {
      return null;
    }
    const valor = Number(texto);
    if (valor < minimo || valor > maximo) {
      return null;
    }
    return valor;
  }

  function marcarInvalido(campo, invalido) {
    campo.setAttribute("aria-invalid", String(invalido));
  }

  // Lee los controles. Valida para ayudar al usuario; el servidor vuelve a validar todo.
  function leerConfiguracion() {
    if (!estado.claveInstancia) {
      throw new Error("Primero carga una instancia válida.");
    }
    const presupuesto = enteroEnRango(elementos.presupuesto.value, 0, PRESUPUESTO_MAXIMO);
    marcarInvalido(elementos.presupuesto, presupuesto === null);
    if (presupuesto === null) {
      throw new Error("El presupuesto debe ser un entero de millones, 0 o mayor.");
    }
    const pesos = {};
    camposDePeso().forEach(function (campo) {
      const peso = enteroEnRango(campo.value, 0, PESO_MAXIMO);
      marcarInvalido(campo, peso === null);
      if (peso === null) {
        throw new Error("El peso de " + campo.dataset.tipo + " debe ser un entero, 0 o mayor.");
      }
      pesos[campo.dataset.tipo] = peso;
    });
    const limite = enteroEnRango(elementos.limite.value, 0, LIMITE_MAXIMO);
    marcarInvalido(elementos.limite, limite === null);
    if (limite === null) {
      throw new Error("El límite del exacto debe estar entre 0 y " + LIMITE_MAXIMO + " segundos.");
    }
    return {
      instancia: estado.claveInstancia,
      metodo: metodoElegido(),
      presupuesto: presupuesto,
      pesos: pesos,
      limite_segundos: limite
    };
  }

  function mostrarErrorDeFormulario(mensaje) {
    elementos.errorFormulario.textContent = mensaje;
    elementos.errorFormulario.hidden = !mensaje;
  }

  // Si los controles ya no coinciden con lo calculado, se avisa (sin recalcular solo).
  function actualizarAvisoDesactualizado() {
    if (!estado.configuracionUsada) {
      elementos.avisoDesactualizado.hidden = true;
      return;
    }
    let actual = null;
    try {
      actual = JSON.stringify(leerConfiguracion());
    } catch (error) {
      actual = null;
    }
    elementos.avisoDesactualizado.hidden = actual === JSON.stringify(estado.configuracionUsada);
  }

  // ---------------------------------------------------------------- calcular

  async function calcular() {
    if (estado.calculando) {
      return;
    }
    let configuracion;
    try {
      configuracion = leerConfiguracion();
      mostrarErrorDeFormulario("");
    } catch (error) {
      mostrarErrorDeFormulario(error.message);
      return;
    }
    estado.calculando = true;
    elementos.calcular.disabled = true;
    elementos.calcular.firstElementChild.textContent = "Calculando…";
    ponerPanel("resultados", "abierto", false);
    mostrarCarga(configuracion);
    try {
      const respuesta = await Api.resolver(configuracion);
      estado.configuracionUsada = configuracion;
      mostrarResultado(respuesta);
      if (esTelefono()) {
        ponerPanel("controles", "cerrado", false);
      }
    } catch (error) {
      mostrarError(error.message, calcular);
    } finally {
      detenerReloj();
      estado.calculando = false;
      elementos.calcular.disabled = estado.instancia === null;
      elementos.calcular.firstElementChild.textContent = "Calcular propuesta";
    }
  }

  // ---------------------------------------------------------------- resultado

  function mostrarResultado(respuesta) {
    estado.resultado = respuesta;
    mostrarVista("resultado");
    elementos.metaResultado.textContent =
      respuesta.instancia + " · " + Formato.nombreDeMetodo(respuesta.metodo);
    mostrarSello(respuesta.optimo_certificado);
    elementos.valor.textContent = Formato.numero(respuesta.valor);
    elementos.costoTexto.textContent =
      Formato.numero(respuesta.costo_total) + " / " + Formato.numero(respuesta.presupuesto) + " M";
    const fraccion = Formato.fraccion(respuesta.costo_total, respuesta.presupuesto);
    elementos.costoRelleno.style.width = (fraccion * 100).toFixed(1) + "%";
    elementos.cantidadEstaciones.textContent = Formato.numero(respuesta.cantidad_estaciones);
    elementos.cantidadCubiertos.textContent = Formato.numero(respuesta.mapa.cubiertos);
    elementos.tiempo.textContent = Formato.segundos(respuesta.tiempo_s);
    llenarCobertura(respuesta);
    llenarTabla(respuesta);
    elementos.bloqueComparacion.hidden = true;
    elementos.mensajeAcciones.textContent = "";
    elementos.avisoDesactualizado.hidden = true;
    MapaEstaciones.dibujar(estado.vista, respuesta.mapa, true);
    anunciar("Propuesta lista. Valor " + Formato.numero(respuesta.valor) + ", " +
      respuesta.cantidad_estaciones + " estaciones.");
  }

  function mostrarSello(certificado) {
    elementos.sello.hidden = certificado === null;
    elementos.sello.classList.toggle("no-certificado", certificado === false);
    if (certificado === true) {
      elementos.sello.textContent = "Óptimo certificado";
    }
    if (certificado === false) {
      elementos.sello.textContent = "No certificada";
      elementos.sello.title = "Se agotó el límite de tiempo: es la mejor propuesta encontrada.";
    }
  }

  function llenarCobertura(respuesta) {
    elementos.cobertura.replaceChildren();
    Object.keys(respuesta.casos_cubiertos).forEach(function (tipo) {
      const cubiertos = respuesta.casos_cubiertos[tipo];
      const total = respuesta.casos_totales[tipo];
      const fila = elemento("li", "cobertura-fila " + MapaEstaciones.claseDeTipo(tipo));
      fila.appendChild(simboloDeTipo(tipo));
      fila.appendChild(elemento("span", null, Formato.capitalizar(tipo)));
      const cifras = elemento("span", "cobertura-cifras");
      cifras.appendChild(elemento("strong", null, Formato.numero(cubiertos)));
      cifras.appendChild(document.createTextNode(" / " + Formato.numero(total)));
      fila.appendChild(cifras);
      fila.appendChild(elemento("span", "cobertura-porcentaje", Formato.porcentaje(cubiertos, total)));
      const barra = elemento("div", "barra-medidor");
      const relleno = elemento("span");
      relleno.style.width = (Formato.fraccion(cubiertos, total) * 100).toFixed(1) + "%";
      barra.appendChild(relleno);
      fila.appendChild(barra);
      elementos.cobertura.appendChild(fila);
    });
  }

  function celda(texto, clase) {
    return elemento("td", clase, texto);
  }

  // Fila de la tabla enlazada con su marca en el mapa (resaltado y vuelo).
  function filaDeEstacion(fila) {
    const tr = document.createElement("tr");
    tr.tabIndex = 0;
    tr.dataset.lote = fila.lote;
    tr.setAttribute("aria-label", fila.lote + ", " + fila.estacion + ", costo " + fila.costo +
      " millones, cubre " + fila.casos + " casos. Enter para ubicar en el mapa.");
    tr.appendChild(celda(fila.lote, "cifras"));
    const estacion = elemento("td");
    const contenido = elemento("span", "celda-estacion");
    contenido.title = fila.estacion + " (" + fila.tipo + ")";
    contenido.appendChild(simboloDeTipo(fila.tipo));
    contenido.appendChild(elemento("span", null, fila.estacion));
    estacion.appendChild(contenido);
    tr.appendChild(estacion);
    tr.appendChild(celda(Formato.numero(fila.costo), "numero"));
    tr.appendChild(celda(Formato.numero(fila.casos), "numero"));
    tr.addEventListener("mouseenter", function () {
      MapaEstaciones.resaltarLote(estado.vista, fila.lote, true);
    });
    tr.addEventListener("mouseleave", function () {
      MapaEstaciones.resaltarLote(estado.vista, fila.lote, false);
    });
    tr.addEventListener("focus", function () {
      MapaEstaciones.resaltarLote(estado.vista, fila.lote, true);
    });
    tr.addEventListener("blur", function () {
      MapaEstaciones.resaltarLote(estado.vista, fila.lote, false);
    });
    tr.addEventListener("click", function () {
      MapaEstaciones.enfocarLote(estado.vista, fila.lote);
    });
    tr.addEventListener("keydown", function (evento) {
      if (evento.key === "Enter" || evento.key === " ") {
        evento.preventDefault();
        MapaEstaciones.enfocarLote(estado.vista, fila.lote);
      }
    });
    return tr;
  }

  function llenarTabla(respuesta) {
    elementos.tablaCuerpo.replaceChildren();
    estado.filasPorLote = {};
    if (respuesta.filas.length === 0) {
      const vacia = elemento("tr", "vacia");
      const texto = celda("Con este presupuesto y estos pesos no se construye ninguna estación.");
      texto.colSpan = 4;
      vacia.appendChild(texto);
      elementos.tablaCuerpo.appendChild(vacia);
    }
    respuesta.filas.forEach(function (fila) {
      const tr = filaDeEstacion(fila);
      estado.filasPorLote[fila.lote] = tr;
      elementos.tablaCuerpo.appendChild(tr);
    });
    llenarTotales(respuesta);
  }

  // Totales: costo frente al presupuesto, casos por tipo (cada incidente una vez) y valor.
  function llenarTotales(respuesta) {
    elementos.tablaPie.replaceChildren();
    const totales = respuesta.totales;
    let cubiertos = 0;
    Object.keys(totales.casos_por_tipo).forEach(function (tipo) {
      cubiertos += totales.casos_por_tipo[tipo];
    });
    const filaTotal = document.createElement("tr");
    const rotulo = elemento("th", null, "Total");
    rotulo.scope = "row";
    filaTotal.appendChild(rotulo);
    filaTotal.appendChild(celda(respuesta.cantidad_estaciones + " estaciones"));
    filaTotal.appendChild(celda(Formato.numero(totales.costo_total), "numero"));
    filaTotal.appendChild(celda(Formato.numero(cubiertos), "numero"));
    elementos.tablaPie.appendChild(filaTotal);
    const partes = ["Presupuesto " + Formato.numero(totales.presupuesto) + " M"];
    Object.keys(totales.casos_por_tipo).forEach(function (tipo) {
      partes.push(Formato.capitalizar(tipo) + " " + Formato.numero(totales.casos_por_tipo[tipo]));
    });
    partes.push("Valor " + Formato.numero(totales.valor));
    const filaDesglose = document.createElement("tr");
    const desglose = celda(partes.join(" · "), "desglose cifras");
    desglose.colSpan = 4;
    filaDesglose.appendChild(desglose);
    elementos.tablaPie.appendChild(filaDesglose);
  }

  // La marca del mapa avisa que el cursor está encima: se resalta su fila.
  function resaltarFila(codigo, activo) {
    const fila = estado.filasPorLote[codigo];
    if (fila) {
      fila.classList.toggle("resaltada", activo);
    }
  }

  // ---------------------------------------------------------------- descargas y comparación

  function descargarCsv() {
    if (!estado.resultado) {
      return;
    }
    // La marca BOM hace que Excel lea bien las tildes.
    const blob = new Blob(["﻿" + estado.resultado.csv], { type: "text/csv;charset=utf-8" });
    descargar(blob, "estaciones_" + nombreParaArchivo(estado.resultado.instancia) + "_" +
      estado.resultado.metodo + ".csv");
  }

  async function descargarMapa() {
    if (!estado.configuracionUsada) {
      return;
    }
    elementos.descargarMapa.disabled = true;
    elementos.mensajeAcciones.textContent = "Preparando el mapa HTML…";
    try {
      const pedido = Object.assign({}, estado.configuracionUsada, { tema: estado.tema });
      const blob = await Api.exportar(pedido);
      descargar(blob, "mapa_" + nombreParaArchivo(estado.resultado.instancia) + "_" +
        estado.resultado.metodo + ".html");
      elementos.mensajeAcciones.textContent = "Mapa descargado: se abre con doble clic, sin servidor.";
    } catch (error) {
      elementos.mensajeAcciones.textContent = error.message;
    } finally {
      elementos.descargarMapa.disabled = false;
    }
  }

  function filaDeComparacion(fila, mejorValor) {
    const tr = document.createElement("tr");
    if (fila.valor === mejorValor) {
      tr.className = "mejor";
    }
    let nombre = Formato.nombreDeMetodo(fila.metodo);
    if (fila.optimo_certificado === true) {
      nombre += " ✓";
    }
    if (fila.optimo_certificado === false) {
      nombre += " (no cert.)";
    }
    tr.appendChild(celda(nombre));
    tr.appendChild(celda(Formato.numero(fila.valor), "numero"));
    tr.appendChild(celda(Formato.numero(fila.costo_total), "numero"));
    tr.appendChild(celda(Formato.segundos(fila.tiempo_s), "numero"));
    return tr;
  }

  async function comparar() {
    if (!estado.configuracionUsada || estado.calculando) {
      return;
    }
    estado.calculando = true;
    elementos.comparar.disabled = true;
    elementos.calcular.disabled = true;
    elementos.bloqueComparacion.hidden = false;
    elementos.comparacionCuerpo.replaceChildren();
    const limite = estado.configuracionUsada.limite_segundos;
    elementos.comparacionNota.textContent =
      "Comparando los cuatro métodos… (el exacto puede tardar hasta " + limite + " s)";
    try {
      const respuesta = await Api.comparar(estado.configuracionUsada);
      let mejorValor = 0;
      respuesta.filas.forEach(function (fila) {
        mejorValor = Math.max(mejorValor, fila.valor);
      });
      respuesta.filas.forEach(function (fila) {
        elementos.comparacionCuerpo.appendChild(filaDeComparacion(fila, mejorValor));
      });
      elementos.comparacionNota.textContent =
        "✓ = óptimo certificado (la búsqueda terminó). La raya a la izquierda marca el mayor valor.";
      anunciar("Comparación lista.");
    } catch (error) {
      elementos.comparacionNota.textContent = error.message;
    } finally {
      estado.calculando = false;
      elementos.comparar.disabled = false;
      elementos.calcular.disabled = estado.instancia === null;
    }
  }

  // ---------------------------------------------------------------- eventos

  function esCampoDeTexto(objetivo) {
    const etiqueta = objetivo && objetivo.tagName;
    return etiqueta === "INPUT" || etiqueta === "SELECT" || etiqueta === "TEXTAREA" ||
      (objetivo && objetivo.isContentEditable);
  }

  // Atajos: [ controles, ] resultados, Enter calcula (si el foco no está en otro control).
  function alPresionarTecla(evento) {
    if (evento.ctrlKey || evento.metaKey || evento.altKey || esCampoDeTexto(evento.target)) {
      return;
    }
    if (evento.key === "[") {
      evento.preventDefault();
      alternarPanel("controles");
    }
    if (evento.key === "]") {
      evento.preventDefault();
      alternarPanel("resultados");
    }
    if (evento.key === "Enter" && evento.target === document.body) {
      evento.preventDefault();
      calcular();
    }
  }

  function alCambiarInstancia() {
    const valor = elementos.instancia.value;
    const esOtra = valor === OTRA_CARPETA;
    elementos.bloqueRuta.hidden = !esOtra;
    if (esOtra) {
      elementos.ruta.focus();
      return;
    }
    cargarInstancia(valor);
  }

  function cargarRutaEscrita() {
    const ruta = elementos.ruta.value.trim();
    if (ruta === "") {
      mostrarErrorDeInstancia("Escribe la ruta completa de la carpeta.");
      return;
    }
    cargarInstancia(ruta);
  }

  function actualizarLimiteVisible() {
    elementos.bloqueLimite.hidden = metodoElegido() !== "exacto";
  }

  function conectarEventos() {
    elementos.botonControles.addEventListener("click", function () {
      alternarPanel("controles");
    });
    elementos.botonResultados.addEventListener("click", function () {
      alternarPanel("resultados");
    });
    elementos.botonTema.addEventListener("click", function () {
      aplicarTema(estado.tema === "oscuro" ? "claro" : "oscuro", true);
    });
    elementos.formulario.addEventListener("submit", function (evento) {
      evento.preventDefault();
      calcular();
    });
    elementos.formulario.addEventListener("change", function (evento) {
      if (evento.target.name === "metodo") {
        actualizarLimiteVisible();
      }
      actualizarAvisoDesactualizado();
    });
    elementos.instancia.addEventListener("change", alCambiarInstancia);
    elementos.cargarRuta.addEventListener("click", cargarRutaEscrita);
    elementos.ruta.addEventListener("keydown", function (evento) {
      if (evento.key === "Enter") {
        evento.preventDefault();
        cargarRutaEscrita();
      }
    });
    elementos.presupuesto.addEventListener("input", function () {
      const valor = parseInt(elementos.presupuesto.value, 10);
      if (Number.isFinite(valor)) {
        elementos.presupuestoRango.value = String(Math.min(valor, Number(elementos.presupuestoRango.max)));
      }
      actualizarAvisoDesactualizado();
    });
    elementos.presupuestoRango.addEventListener("input", function () {
      elementos.presupuesto.value = elementos.presupuestoRango.value;
      actualizarAvisoDesactualizado();
    });
    elementos.restablecerPresupuesto.addEventListener("click", function () {
      if (estado.instancia) {
        ponerPresupuesto(estado.instancia.presupuesto);
        actualizarAvisoDesactualizado();
      }
    });
    elementos.restablecerPesos.addEventListener("click", function () {
      camposDePeso().forEach(function (campo) {
        campo.value = campo.dataset.porDefecto;
      });
      actualizarAvisoDesactualizado();
    });
    elementos.reintentar.addEventListener("click", function () {
      if (estado.reintentar) {
        estado.reintentar();
      }
    });
    elementos.descargarCsv.addEventListener("click", descargarCsv);
    elementos.descargarMapa.addEventListener("click", descargarMapa);
    elementos.comparar.addEventListener("click", comparar);
    document.addEventListener("keydown", alPresionarTecla);
  }

  // ---------------------------------------------------------------- arranque

  function estadoInicialDePanel(nombre, desdeHash) {
    if (desdeHash) {
      return desdeHash;
    }
    const porDefecto = nombre === "resultados" && esTelefono() ? "cerrado" : "abierto";
    return Estado.Preferencias.leer("panel-" + nombre, porDefecto, Estado.PANELES);
  }

  function elegirMetodo(metodo) {
    const radio = elementos.formulario.querySelector('input[name="metodo"][value="' + metodo + '"]');
    if (radio) {
      radio.checked = true;
    }
    actualizarLimiteVisible();
  }

  // Aplica los valores de la dirección (#presupuesto=...) después de cargar la instancia.
  function aplicarHashALaInstancia(opciones) {
    if (opciones.presupuesto !== null) {
      ponerPresupuesto(opciones.presupuesto);
    }
  }

  async function iniciar() {
    const opciones = Estado.leerHash(window.location.hash);
    aplicarTema(opciones.tema || Estado.Preferencias.leer("tema", "oscuro", Estado.TEMAS), false);
    ponerPanel("controles", estadoInicialDePanel("controles", opciones.panel), false);
    ponerPanel("resultados", estadoInicialDePanel("resultados", opciones.resultados), false);

    estado.vista = MapaEstaciones.crearVista(document.getElementById("mapa"), {
      margenes: margenesDelMapa,
      alResaltarLote: resaltarFila,
      alCambiarFondo: alCambiarFondo,
      // En pantallas angostas la leyenda empieza plegada para no tapar los puntos.
      leyendaPlegada: window.innerWidth < 1280
    });
    const fondoGuardado = Estado.Preferencias.leer("fondo", null, Estado.FONDOS);
    estado.fondoElegido = Boolean(opciones.fondo || fondoGuardado);
    MapaEstaciones.cambiarFondo(estado.vista,
      opciones.fondo || fondoGuardado || Estado.fondoPorDefecto(estado.tema));

    elementos.limite.value = String(opciones.limite !== null ? Math.min(opciones.limite, LIMITE_MAXIMO) : LIMITE_POR_DEFECTO);
    elegirMetodo(opciones.metodo || "propia_ls");
    conectarEventos();

    let nombres = [];
    try {
      const respuesta = await Api.instancias();
      nombres = respuesta.instancias;
    } catch (error) {
      mostrarError(error.message, function () {
        window.location.reload();
      });
      return;
    }
    let clave = opciones.instancia || nombres[0] || null;
    if (clave === null) {
      mostrarError("No hay instancias en la carpeta instancias/. Usa «Otra carpeta…».", null);
      llenarSelector(nombres, OTRA_CARPETA);
      elementos.bloqueRuta.hidden = false;
      return;
    }
    const esDeLaLista = nombres.indexOf(clave) >= 0;
    llenarSelector(nombres, esDeLaLista ? clave : OTRA_CARPETA);
    if (!esDeLaLista) {
      elementos.bloqueRuta.hidden = false;
      elementos.ruta.value = clave;
    }
    const cargada = await cargarInstancia(clave);
    if (!cargada) {
      return;
    }
    aplicarHashALaInstancia(opciones);
    if (opciones.auto) {
      await calcular();
      if (opciones.comparar) {
        await comparar();
      }
    }
  }

  iniciar();
})();
