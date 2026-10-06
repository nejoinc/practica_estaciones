/*
  Dibujo del mapa con Leaflet (incluido en vendor/leaflet, sin CDN).

  Este archivo SOLO dibuja: recibe los datos ya calculados por el servidor
  (lotes, estaciones e incidentes cubiertos o no) y los pinta. No calcula
  distancias ni coberturas. Lo usan la interfaz (app.js) y el mapa HTML
  exportado (estaciones/mapa.py lo copia dentro del archivo).

  Todo texto que viene de los CSV se escribe con textContent, nunca como
  HTML: un nombre de lote como "<script>" se ve tal cual y no se ejecuta.
*/

const MapaEstaciones = (function () {
  "use strict";

  // Teselas estándar de OpenStreetMap: no piden clave. Solo se usan como imágenes.
  const URL_TESELAS = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
  const ATRIBUCION =
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
  const ZOOM_MAXIMO = 19;
  const TIPOS_CON_COLOR = ["hurto", "accidente", "incendio"];
  const NOMBRES_DE_FONDO = { calle: "Calle", gris: "Gris", oscuro: "Oscuro", sin: "Sin mapa" };

  // Figuras SVG fijas (no llevan datos de la instancia). Forma distinta por tipo
  // para que se distingan también sin ver el color.
  const FIGURAS = {
    cuadrado: '<rect class="figura" x="3" y="3" width="14" height="14"/>',
    triangulo: '<polygon class="figura" points="10,1.5 18.8,17.5 1.2,17.5"/>',
    circulo: '<circle class="figura" cx="10" cy="10" r="7.6"/>',
    rombo: '<polygon class="figura" points="10,1.2 18.8,10 10,18.8 1.2,10"/>'
  };

  function svgDeForma(forma) {
    const figura = FIGURAS[forma] || FIGURAS.rombo;
    return '<svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">' + figura + "</svg>";
  }

  // Clase CSS del color de un tipo; los tipos nuevos usan un color de reserva.
  function claseDeTipo(tipo) {
    if (TIPOS_CON_COLOR.indexOf(tipo) >= 0) {
      return "tipo-" + tipo;
    }
    return "tipo-otro";
  }

  // El canvas necesita colores concretos: se leen de los tokens CSS del tema actual.
  function leerColor(nombreVariable) {
    return getComputedStyle(document.documentElement).getPropertyValue(nombreVariable).trim();
  }

  function colorDeTipo(tipo) {
    if (TIPOS_CON_COLOR.indexOf(tipo) >= 0) {
      return leerColor("--color-" + tipo);
    }
    return leerColor("--color-otro");
  }

  function prefiereMenosMovimiento() {
    return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  // Crea un elemento con clase y texto (sin innerHTML).
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

  // ---------------------------------------------------------------- vista

  // Crea el mapa vacío. `opciones.margenes()` dice cuánto tapan los paneles
  // flotantes, para que el ajuste automático deje los puntos a la vista.
  function crearVista(contenedor, opciones) {
    const menosMovimiento = prefiereMenosMovimiento();
    const mapa = L.map(contenedor, {
      preferCanvas: true,
      zoomControl: false,
      minZoom: 3,
      maxZoom: ZOOM_MAXIMO,
      zoomSnap: 0.25,
      zoomAnimation: !menosMovimiento,
      fadeAnimation: !menosMovimiento,
      markerZoomAnimation: !menosMovimiento
    });
    mapa.attributionControl.setPrefix(false);
    L.control.zoom({ position: "topright", zoomInTitle: "Acercar", zoomOutTitle: "Alejar" }).addTo(mapa);
    L.control.scale({ position: "bottomright", imperial: false }).addTo(mapa);
    const teselas = L.tileLayer(URL_TESELAS, { maxZoom: ZOOM_MAXIMO, attribution: ATRIBUCION });
    const vista = {
      mapa: mapa,
      contenedor: contenedor,
      teselas: teselas,
      renderizador: L.canvas({ padding: 0.3 }),
      opciones: opciones || {},
      datos: null,
      grupos: {},
      marcasPorLote: {},
      visibles: {},
      fondo: null,
      leyenda: null
    };
    vista.leyenda = crearControlDeLeyenda(vista);
    vista.leyenda.addTo(mapa);
    // Vista inicial del mundo: si la instancia no carga, el mapa no queda en negro.
    // Al llegar los datos, el encuadre automático la reemplaza.
    mapa.setView([0, 0], 3);
    return vista;
  }

  // ---------------------------------------------------------------- fichas (popups)

  function fichaDeEstacion(lote) {
    const ficha = elemento("div");
    ficha.appendChild(elemento("span", "ficha-titulo", lote.codigo));
    ficha.appendChild(elemento("span", "ficha-linea", lote.estacion.nombre + " · " + lote.estacion.tipo));
    const costo = elemento("span", "ficha-linea", "Costo ");
    costo.appendChild(elemento("span", "ficha-cifra", Formato.numero(lote.estacion.costo) + " M"));
    ficha.appendChild(costo);
    const casos = elemento("span", "ficha-linea", "Cubre ");
    casos.appendChild(elemento("span", "ficha-cifra", Formato.numero(lote.estacion.casos)));
    casos.appendChild(document.createTextNode(" casos (contados solo para esta estación)"));
    ficha.appendChild(casos);
    return ficha;
  }

  function fichaDeIncidente(fila, tipos, hayPropuesta) {
    const tipo = tipos[fila[3]].tipo;
    const ficha = elemento("div");
    ficha.appendChild(elemento("span", "ficha-titulo", "Incidente " + fila[0]));
    let estado = Formato.capitalizar(tipo);
    if (hayPropuesta) {
      estado += fila[4] === 1 ? " · cubierto" : " · no cubierto";
    }
    ficha.appendChild(elemento("span", "ficha-linea", estado));
    if (fila[5]) {
      ficha.appendChild(elemento("span", "ficha-linea", fila[5]));
    }
    return ficha;
  }

  // ---------------------------------------------------------------- capas

  function quitarGrupos(vista) {
    Object.keys(vista.grupos).forEach(function (clave) {
      vista.mapa.removeLayer(vista.grupos[clave]);
    });
    vista.grupos = {};
    vista.marcasPorLote = {};
  }

  function grupo(vista, clave) {
    if (!vista.grupos[clave]) {
      vista.grupos[clave] = L.layerGroup();
    }
    return vista.grupos[clave];
  }

  // Incidentes en canvas: 5.300 puntos en ciudad, un solo lienzo en vez de miles de nodos.
  function dibujarIncidentes(vista, datos) {
    const colorNoCubierto = leerColor("--color-no-cubierto");
    const colores = datos.tipos.map(function (tipo) {
      return colorDeTipo(tipo.tipo);
    });
    datos.incidentes.forEach(function (fila) {
      const tipo = datos.tipos[fila[3]].tipo;
      let estilo;
      let clave;
      if (!datos.hay_propuesta) {
        // Sin propuesta no se afirma nada sobre cobertura: aro del color del tipo.
        estilo = { radius: 3, weight: 1.2, color: colores[fila[3]], opacity: 0.8, fill: false };
        clave = "incidentes-" + tipo;
      } else if (fila[4] === 1) {
        estilo = { radius: 3.2, stroke: false, fillColor: colores[fila[3]], fillOpacity: 0.9 };
        clave = "cubiertos-" + tipo;
      } else {
        estilo = { radius: 3, weight: 1, color: colorNoCubierto, opacity: 0.85, fill: false };
        clave = "no-cubiertos";
      }
      estilo.renderer = vista.renderizador;
      const marca = L.circleMarker([fila[1], fila[2]], estilo);
      // La ficha se arma solo cuando el cursor pasa por encima (no 5.300 fichas por adelantado).
      marca.bindTooltip(function () {
        return fichaDeIncidente(fila, datos.tipos, datos.hay_propuesta);
      }, { direction: "top", offset: [0, -4] });
      marca.addTo(grupo(vista, clave));
    });
  }

  function iconoDeLote(lote, datos) {
    if (lote.estacion) {
      const forma = formaDeTipo(datos, lote.estacion.tipo);
      return L.divIcon({
        className: "marca marca-estacion " + claseDeTipo(lote.estacion.tipo),
        html: svgDeForma(forma),
        iconSize: [24, 24],
        iconAnchor: [12, 12],
        popupAnchor: [0, -11]
      });
    }
    return L.divIcon({
      className: "marca marca-lote",
      html: svgDeForma("rombo"),
      iconSize: [15, 15],
      iconAnchor: [7.5, 7.5]
    });
  }

  function formaDeTipo(datos, tipo) {
    for (let posicion = 0; posicion < datos.tipos.length; posicion += 1) {
      if (datos.tipos[posicion].tipo === tipo) {
        return datos.tipos[posicion].forma;
      }
    }
    return "rombo";
  }

  // Lotes (con o sin estación): pocos (80 en ciudad), por eso van como marcas HTML con forma.
  function dibujarLotes(vista, datos) {
    datos.lotes.forEach(function (lote) {
      const marca = L.marker([lote.lat, lote.lon], {
        icon: iconoDeLote(lote, datos),
        keyboard: true,
        title: "",
        riseOnHover: true
      });
      let clave;
      let descripcion;
      if (lote.estacion) {
        descripcion = lote.codigo + " · " + lote.estacion.nombre;
        marca.bindPopup(fichaDeEstacion(lote), { maxWidth: 260 });
        clave = "estaciones-" + lote.estacion.tipo;
      } else {
        descripcion = "Lote " + lote.codigo + " · sin estación";
        clave = "lotes-libres";
      }
      // El texto va como nodo (no como HTML) porque el código del lote viene del CSV.
      marca.bindTooltip(elemento("span", null, descripcion), { direction: "top", offset: [0, -10] });
      // Para lectores de pantalla: la marca es un botón con nombre.
      marca.on("add", function () {
        marca.getElement().setAttribute("role", "button");
        marca.getElement().setAttribute("aria-label", descripcion);
      });
      marca.on("mouseover", function () {
        avisarResaltado(vista, lote.codigo, true);
      });
      marca.on("mouseout", function () {
        avisarResaltado(vista, lote.codigo, false);
      });
      marca.addTo(grupo(vista, clave));
      vista.marcasPorLote[lote.codigo] = marca;
    });
  }

  // Cuando el cursor pasa por una marca, la interfaz resalta la fila de la tabla.
  function avisarResaltado(vista, codigo, activo) {
    resaltarLote(vista, codigo, activo);
    if (vista.opciones.alResaltarLote) {
      vista.opciones.alResaltarLote(codigo, activo);
    }
  }

  function aplicarVisibilidad(vista) {
    Object.keys(vista.grupos).forEach(function (clave) {
      const visible = vista.visibles[clave] !== false;
      const capa = vista.grupos[clave];
      if (visible && !vista.mapa.hasLayer(capa)) {
        capa.addTo(vista.mapa);
      }
      if (!visible && vista.mapa.hasLayer(capa)) {
        vista.mapa.removeLayer(capa);
      }
    });
  }

  // Ajusta el encuadre a todos los lotes e incidentes, sin quedar debajo de los paneles.
  function encuadrar(vista) {
    if (!vista.datos) {
      return;
    }
    let margenes = { arribaIzquierda: [32, 32], abajoDerecha: [32, 32] };
    if (vista.opciones.margenes) {
      margenes = vista.opciones.margenes();
    }
    vista.mapa.fitBounds(vista.datos.limites, {
      paddingTopLeft: margenes.arribaIzquierda,
      paddingBottomRight: margenes.abajoDerecha,
      animate: false
    });
  }

  // Dibuja (o vuelve a dibujar) todo. `encuadre` = true ajusta el zoom a los datos.
  function dibujar(vista, datos, encuadre) {
    quitarGrupos(vista);
    vista.datos = datos;
    dibujarIncidentes(vista, datos);
    dibujarLotes(vista, datos);
    aplicarVisibilidad(vista);
    actualizarLeyenda(vista);
    if (encuadre) {
      encuadrar(vista);
    }
  }

  // Al cambiar de tema cambian los colores del canvas: se redibuja sin mover el mapa.
  function redibujar(vista) {
    if (vista.datos) {
      dibujar(vista, vista.datos, false);
    }
  }

  // ---------------------------------------------------------------- fondo

  function cambiarFondo(vista, fondo) {
    vista.fondo = fondo;
    vista.contenedor.dataset.fondo = fondo;
    const conTeselas = fondo !== "sin";
    if (conTeselas && !vista.mapa.hasLayer(vista.teselas)) {
      vista.teselas.addTo(vista.mapa);
    }
    if (!conTeselas && vista.mapa.hasLayer(vista.teselas)) {
      vista.mapa.removeLayer(vista.teselas);
    }
    actualizarLeyenda(vista);
  }

  // ---------------------------------------------------------------- resaltado y enfoque

  function resaltarLote(vista, codigo, activo) {
    const marca = vista.marcasPorLote[codigo];
    if (!marca || !marca.getElement()) {
      return;
    }
    marca.getElement().classList.toggle("resaltada", activo);
  }

  // Vuela hasta el lote (o salta, si el usuario pidió menos movimiento) y abre su ficha.
  function enfocarLote(vista, codigo) {
    const marca = vista.marcasPorLote[codigo];
    if (!marca) {
      return;
    }
    const destino = marca.getLatLng();
    const zoom = Math.max(vista.mapa.getZoom(), 15);
    if (prefiereMenosMovimiento()) {
      vista.mapa.setView(destino, zoom, { animate: false });
      marca.openPopup();
      return;
    }
    vista.mapa.once("moveend", function () {
      marca.openPopup();
    });
    vista.mapa.flyTo(destino, zoom, { duration: 0.6 });
  }

  // ---------------------------------------------------------------- leyenda

  function crearControlDeLeyenda(vista) {
    const Leyenda = L.Control.extend({
      options: { position: "bottomleft" },
      onAdd: function () {
        const caja = elemento("section", "leyenda");
        caja.setAttribute("aria-label", "Leyenda y capas del mapa");
        L.DomEvent.disableClickPropagation(caja);
        L.DomEvent.disableScrollPropagation(caja);
        vista.cajaLeyenda = caja;
        return caja;
      }
    });
    return new Leyenda();
  }

  function cantidadDeIncidentes(datos, condicion) {
    let cantidad = 0;
    datos.incidentes.forEach(function (fila) {
      if (condicion(fila)) {
        cantidad += 1;
      }
    });
    return cantidad;
  }

  // Una fila de la leyenda con su casilla para mostrar/ocultar la capa.
  function filaDeCapa(vista, clave, simbolo, texto, cantidad) {
    const fila = elemento("label", "leyenda-fila");
    const casilla = document.createElement("input");
    casilla.type = "checkbox";
    casilla.checked = vista.visibles[clave] !== false;
    casilla.addEventListener("change", function () {
      vista.visibles[clave] = casilla.checked;
      aplicarVisibilidad(vista);
    });
    fila.appendChild(casilla);
    fila.appendChild(simbolo);
    fila.appendChild(elemento("span", null, texto));
    fila.appendChild(elemento("span", "cuenta", Formato.numero(cantidad)));
    return fila;
  }

  function simboloDeForma(forma, clase) {
    const simbolo = elemento("span", "simbolo marca " + clase);
    simbolo.innerHTML = svgDeForma(forma); // SVG fijo de este archivo, sin datos de la instancia.
    return simbolo;
  }

  function puntoDeTipo(tipo, hueco) {
    let clase = "punto " + claseDeTipo(tipo);
    if (hueco) {
      clase = "punto hueco";
    }
    return elemento("span", clase);
  }

  function grupoDeLeyenda(titulo) {
    const conjunto = elemento("fieldset", "leyenda-grupo");
    conjunto.appendChild(elemento("legend", null, titulo));
    return conjunto;
  }

  function seccionDeEstaciones(vista, datos) {
    if (!datos.hay_propuesta) {
      // Sin propuesta todavía no hay estaciones: solo los lotes donde se podría construir.
      const lotes = grupoDeLeyenda("Lotes");
      lotes.appendChild(filaDeCapa(vista, "lotes-libres", simboloDeForma("rombo", "marca-lote"),
        "Lote disponible", datos.lotes.length));
      return lotes;
    }
    const conjunto = grupoDeLeyenda("Estaciones construidas");
    datos.tipos.forEach(function (tipo) {
      const cantidad = datos.lotes.filter(function (lote) {
        return lote.estacion && lote.estacion.tipo === tipo.tipo;
      }).length;
      const simbolo = simboloDeForma(tipo.forma, claseDeTipo(tipo.tipo));
      conjunto.appendChild(filaDeCapa(vista, "estaciones-" + tipo.tipo, simbolo, tipo.estacion, cantidad));
    });
    const libres = datos.lotes.filter(function (lote) {
      return !lote.estacion;
    }).length;
    const rombo = simboloDeForma("rombo", "marca-lote");
    conjunto.appendChild(filaDeCapa(vista, "lotes-libres", rombo, "Lote sin estación", libres));
    return conjunto;
  }

  function seccionDeIncidentes(vista, datos) {
    if (!datos.hay_propuesta) {
      const conjunto = grupoDeLeyenda("Incidentes (sin propuesta aún)");
      datos.tipos.forEach(function (tipo, posicion) {
        const cantidad = cantidadDeIncidentes(datos, function (fila) {
          return fila[3] === posicion;
        });
        const punto = elemento("span", "punto hueco");
        punto.style.borderColor = colorDeTipo(tipo.tipo);
        conjunto.appendChild(filaDeCapa(vista, "incidentes-" + tipo.tipo, punto,
          Formato.capitalizar(tipo.tipo), cantidad));
      });
      return conjunto;
    }
    const conjunto = grupoDeLeyenda("Incidentes cubiertos (relleno)");
    datos.tipos.forEach(function (tipo, posicion) {
      const cantidad = cantidadDeIncidentes(datos, function (fila) {
        return fila[3] === posicion && fila[4] === 1;
      });
      conjunto.appendChild(filaDeCapa(vista, "cubiertos-" + tipo.tipo, puntoDeTipo(tipo.tipo, false),
        Formato.capitalizar(tipo.tipo), cantidad));
    });
    conjunto.appendChild(filaDeCapa(vista, "no-cubiertos", puntoDeTipo(null, true),
      "No cubiertos (aro gris)", datos.no_cubiertos));
    return conjunto;
  }

  function seccionDeFondo(vista) {
    const conjunto = grupoDeLeyenda("Fondo");
    const selector = elemento("div", "selector-fondo");
    selector.setAttribute("role", "group");
    selector.setAttribute("aria-label", "Fondo del mapa");
    Object.keys(NOMBRES_DE_FONDO).forEach(function (fondo) {
      const boton = elemento("button", null, NOMBRES_DE_FONDO[fondo]);
      boton.type = "button";
      boton.setAttribute("aria-pressed", String(vista.fondo === fondo));
      boton.addEventListener("click", function () {
        cambiarFondo(vista, fondo);
        if (vista.opciones.alCambiarFondo) {
          vista.opciones.alCambiarFondo(fondo);
        }
        // Tras redibujar la leyenda se devuelve el foco al botón equivalente.
        const nuevo = vista.cajaLeyenda.querySelector('[data-fondo="' + fondo + '"]');
        if (nuevo) {
          nuevo.focus();
        }
      });
      boton.dataset.fondo = fondo;
      selector.appendChild(boton);
    });
    conjunto.appendChild(selector);
    return conjunto;
  }

  // La leyenda va dentro de <details>: en el teléfono empieza plegada para no tapar el mapa.
  function actualizarLeyenda(vista) {
    const caja = vista.cajaLeyenda;
    if (!caja) {
      return;
    }
    const anterior = caja.querySelector("details");
    let abierta = !vista.opciones.leyendaPlegada;
    if (anterior) {
      abierta = anterior.open;
    }
    const plegable = document.createElement("details");
    plegable.open = abierta;
    plegable.appendChild(elemento("summary", "leyenda-titulo", "Capas y leyenda"));
    if (vista.datos) {
      plegable.appendChild(seccionDeEstaciones(vista, vista.datos));
      plegable.appendChild(seccionDeIncidentes(vista, vista.datos));
    }
    plegable.appendChild(seccionDeFondo(vista));
    plegable.appendChild(elemento("p", "leyenda-nota",
      "La cobertura se mide por la red vial con sentido de las calles; por eso no se dibujan círculos de radio."));
    caja.replaceChildren(plegable);
  }

  // ---------------------------------------------------------------- mapa exportado

  function cifra(etiqueta, valor) {
    const bloque = elemento("div", "exportado-cifra");
    bloque.appendChild(elemento("dt", null, etiqueta));
    bloque.appendChild(elemento("dd", null, valor));
    return bloque;
  }

  function llenarCabeceraExportada(cabecera, resumen) {
    const titulo = elemento("div", "exportado-titulos");
    titulo.appendChild(elemento("h1", null, resumen.titulo));
    titulo.appendChild(elemento("p", null, resumen.detalle));
    cabecera.appendChild(titulo);
    const lista = elemento("dl", "exportado-cifras");
    lista.appendChild(cifra("Valor", Formato.numero(resumen.valor)));
    lista.appendChild(cifra("Costo", Formato.numero(resumen.costo_total) + " / " +
      Formato.numero(resumen.presupuesto) + " M"));
    lista.appendChild(cifra("Estaciones", Formato.numero(resumen.estaciones)));
    Object.keys(resumen.casos_cubiertos).forEach(function (tipo) {
      lista.appendChild(cifra(Formato.capitalizar(tipo), Formato.numero(resumen.casos_cubiertos[tipo])));
    });
    cabecera.appendChild(lista);
  }

  // Punto de entrada del HTML exportado: lee el JSON incrustado y dibuja.
  function iniciarExportado() {
    const datos = JSON.parse(document.getElementById("datos-del-mapa").textContent);
    llenarCabeceraExportada(document.getElementById("cabecera"), datos.resumen);
    const vista = crearVista(document.getElementById("mapa"), {});
    const tema = document.documentElement.dataset.tema === "claro" ? "claro" : "oscuro";
    cambiarFondo(vista, tema === "claro" ? "gris" : "oscuro");
    dibujar(vista, datos, true);
  }

  return {
    crearVista: crearVista,
    dibujar: dibujar,
    redibujar: redibujar,
    encuadrar: encuadrar,
    cambiarFondo: cambiarFondo,
    resaltarLote: resaltarLote,
    enfocarLote: enfocarLote,
    svgDeForma: svgDeForma,
    claseDeTipo: claseDeTipo,
    iniciarExportado: iniciarExportado
  };
})();
