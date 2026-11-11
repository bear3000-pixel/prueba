/**
 * Food Saver — interfaz web / Android.
 *
 * Este archivo SOLO arma la pantalla y conecta botones; las reglas están en modelo.js, logica.js y
 * recetasUsuario.js (que se comparan con el Python en web/tests/), y el guardado en almacenamiento.js.
 * Los textos y mensajes son los mismos de la versión de escritorio.
 */
import {
  DIAS_POR_VENCER, UNIDADES, ErrorValidacion, autoformatearFecha, crearIngrediente, describirVencimiento,
  diasParaVencer, estaPorVencer, formatearCantidad, formatearFecha, hoyIso, parsearFecha, textoCantidad,
} from "./modelo.js";
import {
  clasificar, coincideIngrediente, esCompleta, sugerirRecetas, totalIngredientes, usoMasUrgente,
} from "./logica.js";
import { RECETAS } from "./recetas.js";
import { MAX_INGREDIENTES, crearReceta, validarIngredienteReceta } from "./recetasUsuario.js";
import {
  almacenDelNavegador, cargarIngredientes, cargarRecetas, guardarIngredientes, guardarRecetas,
} from "./almacenamiento.js";
import { ingredientesDeEjemplo } from "./ejemplos.js";

// --------------------------------------------------------------------------- //
// Estado y utilidades
// --------------------------------------------------------------------------- //
const estado = {
  ingredientes: [],
  recetasPropias: [],
  enEdicion: null,        // id del ingrediente que se está editando
  hoy: hoyIso(),
  abierta: undefined,     // nombre de la receta con el detalle abierto (undefined = abrir la primera; null = ninguna)
  soloCompletas: false,
  mensajeFecha: null,     // el aviso de fecha inválida que mostramos en vivo
  fechaAnterior: "",
};
let almacen = null; // localStorage, o null si el navegador no deja guardar

const $ = (id) => document.getElementById(id);
const esc = (texto) => String(texto).replace(/[&<>"']/g,
  (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const capitalizar = (texto) => texto.charAt(0).toUpperCase() + texto.slice(1).toLowerCase();
const primeraMayuscula = (texto) => texto.charAt(0).toUpperCase() + texto.slice(1);
const plural = (n, singular, pluralTxt) => `${n} ${n === 1 ? singular : pluralTxt}`;

function ponerMensaje(elemento, texto, error = false) {
  elemento.textContent = texto;
  elemento.className = `mensaje ${error ? "error" : "ok"}`;
  elemento.hidden = !texto;
}
const mostrarMensaje = (texto, error = false) => ponerMensaje($("mensaje"), texto, error);
const mostrarMensajeRecetas = (texto, error = false) => ponerMensaje($("mensaje-recetas"), texto, error);

function avisoGeneral(texto) {
  const aviso = $("aviso-general");
  aviso.textContent = texto;
  aviso.hidden = !texto;
}

// --------------------------------------------------------------------------- //
// Guardado
// --------------------------------------------------------------------------- //
function guardar(guardarFn, datos) {
  if (!almacen) return true; // sin almacenamiento: todo vive en memoria (ya se avisó al abrir)
  try {
    guardarFn(almacen, datos);
    return true;
  } catch (error) {
    avisoGeneral(`${error.message}\nLo que hiciste sigue en pantalla mientras no cierres la aplicación.`);
    return false;
  }
}
const guardarLosIngredientes = () => guardar(guardarIngredientes, estado.ingredientes);
const guardarLasRecetas = () => guardar(guardarRecetas, estado.recetasPropias);

// --------------------------------------------------------------------------- //
// Despensa: dibujar
// --------------------------------------------------------------------------- //
function renderTodo() {
  estado.hoy = hoyIso();
  const [vigentes, vencidos] = clasificar(estado.ingredientes, estado.hoy);
  const porVencer = vigentes.filter((i) => estaPorVencer(i, estado.hoy));

  $("chip-vigentes").textContent = plural(vigentes.length, "vigente", "vigentes");
  $("chip-por-vencer").textContent = `${porVencer.length} por vencer`;
  $("chip-vencidos").textContent = plural(vencidos.length, "vencido", "vencidos");

  $("titulo-vigentes").textContent = `Ingredientes vigentes (${vigentes.length}) — el que vence primero, arriba`;
  $("titulo-vencidos").textContent = `Vencidos (${vencidos.length}) — no se usan en las recetas`;
  $("lista-vigentes").innerHTML = vigentes.map(itemIngrediente).join("");
  $("lista-vencidos").innerHTML = vencidos.map(itemIngrediente).join("");
  $("vacio-vigentes").hidden = vigentes.length > 0;
  $("vacio-vencidos").hidden = vencidos.length > 0;
  renderRecetas();
}

function itemIngrediente(ing) {
  const dias = diasParaVencer(ing, estado.hoy);
  let textoEstado = primeraMayuscula(describirVencimiento(dias));
  let clase = "";
  if (dias < 0) {
    clase = "vencido";
  } else if (estaPorVencer(ing, estado.hoy)) {
    textoEstado = `⚠ ${textoEstado}`;
    clase = "por-vencer";
  }
  const nombre = esc(ing.nombre);
  return `<li class="ing ${clase}${ing.id === estado.enEdicion ? " seleccionado" : ""}" data-id="${ing.id}">
    <span class="nombre">${nombre}</span>
    <span class="estado">${esc(textoEstado)}</span>
    <span class="detalle">${esc(textoCantidad(ing.cantidad, ing.unidad))} · vence ${formatearFecha(ing.vencimiento)}</span>
    <div class="acciones">
      <button type="button" class="boton chico" data-accion="editar" data-id="${ing.id}" aria-label="Editar ${nombre}">Editar</button>
      <button type="button" class="boton chico peligro" data-accion="eliminar" data-id="${ing.id}" aria-label="Eliminar ${nombre}">Eliminar</button>
    </div>
  </li>`;
}

// --------------------------------------------------------------------------- //
// Despensa: formulario (agregar / editar)
// --------------------------------------------------------------------------- //
const CAMPOS = { nombre: "nombre", cantidad: "cantidad", unidad: "unidad", vencimiento: "vence" };

function enfocarCampo(campo) {
  $(CAMPOS[campo] ?? "nombre").focus();
}

function enviarFormulario(evento) {
  evento.preventDefault();
  let ingrediente;
  try {
    ingrediente = crearIngrediente($("nombre").value, $("cantidad").value, $("unidad").value, $("vence").value, estado.enEdicion);
  } catch (error) {
    if (!(error instanceof ErrorValidacion)) throw error;
    // Dato inválido: no se guarda nada, se explica qué corregir y se enfoca ese campo.
    mostrarMensaje(error.message, true);
    enfocarCampo(error.campo);
    return;
  }
  const editando = estado.enEdicion !== null;
  estado.ingredientes = editando
    ? estado.ingredientes.map((i) => (i.id === estado.enEdicion ? ingrediente : i))
    : [...estado.ingredientes, ingrediente];
  guardarLosIngredientes();
  salirDeEdicion();
  limpiarFormulario();
  renderTodo();
  mostrarMensaje(`«${ingrediente.nombre}» ${editando ? "actualizado" : "agregado"}.`);
  $("nombre").focus();
}

function limpiarFormulario() {
  $("nombre").value = "";
  $("cantidad").value = "";
  $("unidad").value = UNIDADES[0];
  $("vence").value = "";
  estado.fechaAnterior = "";
  estado.mensajeFecha = null;
}

function editarIngrediente(id) {
  const ing = estado.ingredientes.find((i) => i.id === id);
  if (!ing) return;
  estado.enEdicion = id;
  $("nombre").value = ing.nombre;
  $("cantidad").value = formatearCantidad(ing.cantidad);
  $("unidad").value = ing.unidad;
  $("vence").value = formatearFecha(ing.vencimiento);
  estado.fechaAnterior = $("vence").value;
  $("titulo-formulario").textContent = `Editando «${ing.nombre}»`;
  $("boton-guardar").textContent = "Guardar cambios";
  $("boton-cancelar-edicion").hidden = false;
  mostrarMensaje("");
  renderTodo();
  $("formulario").scrollIntoView({ block: "start" });
  $("nombre").focus();
}

function salirDeEdicion() {
  estado.enEdicion = null;
  $("titulo-formulario").textContent = "Agregar ingrediente";
  $("boton-guardar").textContent = "Agregar";
  $("boton-cancelar-edicion").hidden = true;
}

function cancelarEdicion() {
  salirDeEdicion();
  limpiarFormulario();
  mostrarMensaje("");
  renderTodo();
}

async function eliminarIngrediente(id) {
  const ing = estado.ingredientes.find((i) => i.id === id);
  if (!ing || !(await confirmar("Eliminar ingrediente", `¿Eliminar «${ing.nombre}»?`))) return;
  estado.ingredientes = estado.ingredientes.filter((i) => i.id !== id);
  if (estado.enEdicion === id) cancelarEdicion();
  guardarLosIngredientes();
  renderTodo();
  mostrarMensaje(`«${ing.nombre}» eliminado.`);
}

function cargarEjemplo() {
  const nuevos = ingredientesDeEjemplo(hoyIso());
  estado.ingredientes = [...estado.ingredientes, ...nuevos];
  guardarLosIngredientes();
  renderTodo();
  mostrarMensaje(`Se agregaron ${nuevos.length} ingredientes de ejemplo.`);
}

async function borrarTodo() {
  const n = estado.ingredientes.length;
  if (!n) return;
  const que = n === 1 ? "el ingrediente guardado" : `los ${n} ingredientes guardados`;
  if (!(await confirmar("Borrar todo", `¿Borrar ${que}?`))) return;
  estado.ingredientes = [];
  cancelarEdicion();
  guardarLosIngredientes();
  renderTodo();
  mostrarMensaje("Se borraron todos los ingredientes.");
}

// ---- Fecha con barras automáticas (02112026 -> 02/11/2026) ----
function alEscribirFecha(evento) {
  const campo = evento.target;
  const tipo = String(evento.inputType ?? "");
  // Al BORRAR no se vuelve a poner la barra, o no se podría retroceder.
  const escribiendo = tipo ? !tipo.startsWith("delete") : campo.value.length > estado.fechaAnterior.length;
  const formateada = autoformatearFecha(campo.value, escribiendo);
  if (formateada !== campo.value) campo.value = formateada;
  estado.fechaAnterior = formateada;
  validarFechaEnVivo(formateada);
}

function validarFechaEnVivo(texto) {
  if (texto.length === 10) { // DD/MM/AAAA completo: avisar apenas se sabe que no existe
    try {
      parsearFecha(texto);
    } catch (error) {
      if (!(error instanceof ErrorValidacion)) throw error;
      estado.mensajeFecha = error.message;
      mostrarMensaje(error.message, true);
      return;
    }
  }
  // Fecha incompleta o correcta: si el aviso en pantalla era el de la fecha, se quita.
  if (estado.mensajeFecha !== null && $("mensaje").textContent === estado.mensajeFecha) mostrarMensaje("");
  estado.mensajeFecha = null;
}

// --------------------------------------------------------------------------- //
// Recetas: lista y detalle
// --------------------------------------------------------------------------- //
const todasLasRecetas = () => [...RECETAS, ...estado.recetasPropias];
const nombresDeRecetas = (excluirId = null) =>
  todasLasRecetas().filter((r) => !(excluirId && r.id === excluirId)).map((r) => r.nombre);

function renderRecetas() {
  const sugerencias = sugerirRecetas(estado.ingredientes, todasLasRecetas(), estado.hoy, estado.soloCompletas);
  estado.sugerencias = sugerencias;
  // Si la receta abierta ya no está en la lista, vuelve a abrirse la primera.
  if (estado.abierta && !sugerencias.some((s) => s.receta.nombre === estado.abierta)) estado.abierta = undefined;
  // undefined = «todavía no eligió»: se abre la primera apenas haya recetas (null = la cerró a propósito).
  if (estado.abierta === undefined && sugerencias.length) estado.abierta = sugerencias[0].receta.nombre;

  $("lista-recetas").innerHTML = sugerencias.map(itemReceta).join("");
  const vacio = $("vacio-recetas");
  if (sugerencias.length) {
    vacio.textContent = "";
  } else if (!estado.ingredientes.length) {
    vacio.textContent = "Agrega ingredientes (o pulsa «Cargar ejemplo») para ver recetas sugeridas.";
  } else if (estado.soloCompletas) {
    vacio.textContent = "Ninguna receta se puede cocinar completa con lo que tienes vigente. Desmarca la casilla para ver recetas con ingredientes faltantes.";
  } else {
    vacio.textContent = "Ninguna receta usa tus ingredientes vigentes. Revisa la lista de vencidos o agrega más ingredientes.";
  }
  vacio.hidden = sugerencias.length > 0;
}

function itemReceta(sug) {
  const receta = sug.receta;
  const abierta = estado.abierta === receta.nombre;
  const urgente = sug.diasMasUrgente <= DIAS_POR_VENCER;
  let aprovecha = "";
  if (urgente) {
    const uso = usoMasUrgente(sug);
    aprovecha = ` · Aprovecha: ${uso.lote.nombre} (${describirVencimiento(uso.dias).replace("vence ", "")})`;
  }
  const meta = `Tienes ${sug.usados.length} de ${totalIngredientes(sug)}${aprovecha}`;
  return `<li class="receta${urgente ? " urgente" : ""}">
    <button type="button" class="receta-cabecera" data-accion="receta" data-nombre="${esc(receta.nombre)}" aria-expanded="${abierta}">
      <span class="receta-titulo">${receta.propia ? "★ " : ""}${esc(receta.nombre)}</span>
      <span class="receta-meta">${esc(meta)}</span>
    </button>
    ${abierta ? `<div class="receta-detalle">${detalleReceta(sug)}</div>` : ""}
  </li>`;
}

function detalleReceta(sug) {
  const receta = sug.receta;
  const partes = [];
  if (receta.propia) partes.push('<p class="etiqueta-propia">Receta creada por ti</p>');
  if (esCompleta(sug)) {
    partes.push('<p class="bueno">✔ Tienes todos los ingredientes: puedes cocinarla ya.</p>');
  } else {
    partes.push(`<p class="alerta">Te faltan ${sug.faltantes.length + sug.insuficientes.length} ingrediente(s).</p>`);
  }

  partes.push("<h3>Lo que usarías de tu despensa</h3><ul>");
  for (const uso of [...sug.usados].sort((a, b) => a.dias - b.dias)) {
    const lote = uso.lote;
    const pide = uso.necesita ? ` — la receta pide ${textoCantidad(...uso.necesita)}` : ""; // solo recetas propias
    partes.push(`<li class="${uso.dias <= DIAS_POR_VENCER ? "alerta" : ""}">${esc(lote.nombre)} (${esc(textoCantidad(lote.cantidad, lote.unidad))}) — ${esc(describirVencimiento(uso.dias))}${esc(pide)}</li>`);
  }
  partes.push("</ul>");

  if (sug.insuficientes.length) {
    partes.push("<h3>Lo tienes, pero en poca cantidad</h3><ul>");
    for (const poco of sug.insuficientes) {
      const falta = Number((poco.necesita[0] - poco.tienes[0]).toFixed(3));
      partes.push(`<li class="falta">${esc(poco.lote.nombre)}: pide ${esc(textoCantidad(...poco.necesita))}, tienes ${esc(textoCantidad(...poco.tienes))} (te faltan ${esc(textoCantidad(falta, poco.necesita[1]))})</li>`);
    }
    partes.push("</ul>");
  }

  if (sug.faltantes.length) {
    partes.push("<h3>Te faltan</h3><ul>");
    const cantidades = new Map(receta.ingredientes.map((n, i) => [n, receta.cantidades[i]])); // vacío en las predefinidas
    for (const nombre of sug.faltantes) {
      const nota = sug.descartadosPorVencidos.includes(nombre) ? " (lo tienes, pero está vencido)" : "";
      const pide = cantidades.get(nombre) ? ` — pide ${textoCantidad(...cantidades.get(nombre))}` : "";
      partes.push(`<li class="falta">${esc(capitalizar(nombre))}${esc(pide)}${esc(nota)}</li>`);
    }
    partes.push("</ul>");
  }

  partes.push("<h3>Preparación</h3><ol>");
  for (const paso of receta.instrucciones) partes.push(`<li>${esc(paso)}</li>`);
  partes.push("</ol>");
  return partes.join("");
}

function alternarReceta(nombre) {
  estado.abierta = estado.abierta === nombre ? null : nombre;
  renderRecetas();
}

// --------------------------------------------------------------------------- //
// Recetas propias: crear / editar / eliminar
// --------------------------------------------------------------------------- //
const editor = { receta: null, filas: [], filaEnEdicion: null };

const avisoReceta = (texto, error = false) => ponerMensaje($("receta-mensaje"), texto, error);
const CAMPOS_RECETA = {
  nombre: "receta-nombre", ingredientes: "receta-ingrediente", cantidad: "receta-cantidad",
  unidad: "receta-unidad", pasos: "receta-pasos",
};

function abrirEditorReceta(receta = null) {
  editor.receta = receta;
  editor.filas = receta ? receta.ingredientes.map((n, i) => [n, receta.cantidades[i][0], receta.cantidades[i][1]]) : [];
  editor.filaEnEdicion = null;
  $("titulo-dialogo-receta").textContent = receta ? "Editar mi receta" : "Crear mi receta";
  $("receta-nombre").value = receta ? receta.nombre : "";
  $("receta-ingrediente").value = "";
  $("receta-cantidad").value = "";
  $("receta-unidad").value = UNIDADES[0];
  $("receta-pasos").value = receta ? receta.instrucciones.join("\n") : "";
  $("receta-agregar").textContent = "Agregar ingrediente";
  avisoReceta("");
  renderFilasReceta();
  const dialogo = $("dialogo-receta");
  if (!dialogo.open) dialogo.showModal();
  $("receta-nombre").focus();
}

function renderFilasReceta() {
  $("receta-lista").innerHTML = editor.filas.map(([nombre, cantidad, unidad], i) => `<li class="ing">
    <span class="nombre">${esc(nombre)}</span><span class="estado"></span>
    <span class="detalle">${esc(textoCantidad(cantidad, unidad))}</span>
    <div class="acciones">
      <button type="button" class="boton chico" data-accion="receta-editar-fila" data-indice="${i}" aria-label="Editar ${esc(nombre)}">Editar</button>
      <button type="button" class="boton chico peligro" data-accion="receta-quitar-fila" data-indice="${i}" aria-label="Quitar ${esc(nombre)}">Quitar</button>
    </div></li>`).join("");
}

function agregarIngredienteReceta() {
  let fila;
  try {
    fila = validarIngredienteReceta($("receta-ingrediente").value, $("receta-cantidad").value, $("receta-unidad").value);
  } catch (error) {
    if (!(error instanceof ErrorValidacion)) throw error;
    avisoReceta(error.message, true);
    $(CAMPOS_RECETA[error.campo] ?? "receta-ingrediente").focus();
    return;
  }
  const repetido = editor.filas.some((otra, i) => i !== editor.filaEnEdicion
    && coincideIngrediente(fila[0], otra[0]) && coincideIngrediente(otra[0], fila[0]));
  if (repetido) {
    avisoReceta(`«${fila[0]}» ya está en la lista de ingredientes.`, true);
    $("receta-ingrediente").focus();
    return;
  }
  if (editor.filaEnEdicion === null && editor.filas.length >= MAX_INGREDIENTES) {
    avisoReceta(`Una receta puede tener como máximo ${MAX_INGREDIENTES} ingredientes.`, true);
    return;
  }
  if (editor.filaEnEdicion === null) {
    editor.filas.push(fila);
    avisoReceta(`«${fila[0]}» agregado a la receta.`);
  } else {
    editor.filas[editor.filaEnEdicion] = fila;
    avisoReceta(`«${fila[0]}» actualizado.`);
    salirDeEdicionFila();
  }
  $("receta-ingrediente").value = "";
  $("receta-cantidad").value = "";
  renderFilasReceta();
  $("receta-ingrediente").focus();
}

function editarFilaReceta(indice) {
  const [nombre, cantidad, unidad] = editor.filas[indice];
  $("receta-ingrediente").value = nombre;
  $("receta-cantidad").value = formatearCantidad(cantidad);
  $("receta-unidad").value = unidad;
  editor.filaEnEdicion = indice;
  $("receta-agregar").textContent = "Guardar cambio";
  avisoReceta(`Editando «${nombre}». Cambia lo que necesites y pulsa «Guardar cambio».`);
  $("receta-ingrediente").focus();
}

function quitarFilaReceta(indice) {
  const [nombre] = editor.filas.splice(indice, 1)[0];
  salirDeEdicionFila();
  renderFilasReceta();
  avisoReceta(`«${nombre}» quitado de la receta.`);
}

function salirDeEdicionFila() {
  editor.filaEnEdicion = null;
  $("receta-agregar").textContent = "Agregar ingrediente";
}

/** ¿Hay algo escrito que se perdería al cerrar? (compara con la receta original si se está editando) */
function recetaTieneCambios() {
  const nombre = $("receta-nombre").value.trim();
  const pasos = $("receta-pasos").value.trim();
  const sinAgregar = Boolean($("receta-ingrediente").value.trim() || $("receta-cantidad").value.trim());
  const original = editor.receta;
  if (!original) return Boolean(nombre || editor.filas.length || pasos || sinAgregar);
  const filasOriginales = original.ingredientes.map((n, i) => [n, original.cantidades[i][0], original.cantidades[i][1]]);
  return sinAgregar || nombre !== original.nombre || pasos !== original.instrucciones.join("\n").trim()
    || JSON.stringify(editor.filas) !== JSON.stringify(filasOriginales);
}

async function cerrarEditorReceta() {
  if (recetaTieneCambios() && !(await confirmar(
    "Cerrar sin guardar", "Tienes cambios sin guardar en esta receta.\n¿Quieres cerrar y perderlos?"))) return;
  $("dialogo-receta").close();
}

function guardarRecetaDelEditor(evento) {
  evento.preventDefault();
  // Lo escrito en el mini formulario de ingredientes y no agregado se perdería sin avisar.
  if ($("receta-ingrediente").value.trim() || $("receta-cantidad").value.trim()) {
    avisoReceta("Tienes un ingrediente escrito que no has agregado. Pulsa «Agregar ingrediente» o borra lo escrito.", true);
    $("receta-ingrediente").focus();
    return;
  }
  let receta;
  try {
    receta = crearReceta($("receta-nombre").value, editor.filas, $("receta-pasos").value,
      nombresDeRecetas(editor.receta?.id ?? null), editor.receta?.id ?? null);
  } catch (error) {
    if (!(error instanceof ErrorValidacion)) throw error;
    avisoReceta(error.message, true);
    $(CAMPOS_RECETA[error.campo] ?? "receta-nombre").focus();
    return;
  }
  if (guardarRecetaPropia(receta)) $("dialogo-receta").close();
}

/** Agrega la receta, o reemplaza la que tenga su mismo id. Devuelve false si no se pudo guardar en el dispositivo. */
function guardarRecetaPropia(receta) {
  const esNueva = estado.recetasPropias.every((r) => r.id !== receta.id);
  estado.recetasPropias = esNueva
    ? [...estado.recetasPropias, receta]
    : estado.recetasPropias.map((r) => (r.id === receta.id ? receta : r));
  const guardada = guardarLasRecetas();
  const verbo = esNueva ? "guardada" : "actualizada";
  const aparece = sugerirRecetas(estado.ingredientes, todasLasRecetas(), estado.hoy, estado.soloCompletas)
    .some((s) => s.receta.id === receta.id);
  if (aparece) estado.abierta = receta.nombre; // se abre para que se vea
  renderRecetas();
  renderMisRecetas();
  mostrarMensajeRecetas(aparece
    ? `Receta «${receta.nombre}» ${verbo}. Ya aparece en las recetas sugeridas.`
    : `Receta «${receta.nombre}» ${verbo}. Aparecerá en las sugerencias cuando tengas alguno de sus ingredientes (vigente) en la despensa.`);
  return guardada;
}

async function eliminarRecetaPropia(id) {
  const receta = estado.recetasPropias.find((r) => r.id === id);
  if (!receta || !(await confirmar("Eliminar receta", `¿Eliminar tu receta «${receta.nombre}»?`))) return;
  estado.recetasPropias = estado.recetasPropias.filter((r) => r.id !== id);
  guardarLasRecetas();
  renderRecetas();
  renderMisRecetas();
  mostrarMensajeRecetas(`Receta «${receta.nombre}» eliminada.`);
}

function abrirMisRecetas() {
  renderMisRecetas();
  const dialogo = $("dialogo-mis-recetas");
  if (!dialogo.open) dialogo.showModal();
}

function renderMisRecetas() {
  const recetas = [...estado.recetasPropias].sort((a, b) => a.nombre.toLowerCase().localeCompare(b.nombre.toLowerCase(), "es"));
  $("mis-recetas-lista").innerHTML = recetas.map((r) => `<li class="ing">
    <span class="nombre">${esc(r.nombre)}</span><span class="estado"></span>
    <span class="detalle">${r.ingredientes.length} ingredientes · ${r.instrucciones.length} pasos</span>
    <div class="acciones">
      <button type="button" class="boton chico" data-accion="mis-editar" data-id="${r.id}" aria-label="Editar ${esc(r.nombre)}">Editar</button>
      <button type="button" class="boton chico peligro" data-accion="mis-eliminar" data-id="${r.id}" aria-label="Eliminar ${esc(r.nombre)}">Eliminar</button>
    </div></li>`).join("");
  $("mis-recetas-vacio").hidden = recetas.length > 0;
}

// --------------------------------------------------------------------------- //
// Confirmaciones (en lugar de window.confirm, que se ve distinto en cada celular)
// --------------------------------------------------------------------------- //
function confirmar(titulo, texto) {
  return new Promise((resolver) => {
    const dialogo = $("dialogo-confirmar");
    $("confirmar-titulo").textContent = titulo;
    $("confirmar-texto").textContent = texto;
    $("confirmar-texto").style.whiteSpace = "pre-line";
    const responder = (valor) => { dialogo.close(); resolver(valor); };
    $("confirmar-si").onclick = (e) => { e.preventDefault(); responder(true); };
    $("confirmar-no").onclick = () => responder(false);
    dialogo.oncancel = () => resolver(false); // la tecla Esc o el botón «atrás» de Android
    dialogo.showModal();
    $("confirmar-no").focus(); // por defecto, la opción segura
  });
}

// --------------------------------------------------------------------------- //
// Pestañas, eventos y arranque
// --------------------------------------------------------------------------- //
function mostrarPestana(cual) {
  for (const nombre of ["despensa", "recetas"]) {
    const activa = nombre === cual;
    $(`pestana-${nombre}`).setAttribute("aria-selected", String(activa));
    $(`vista-${nombre}`).hidden = !activa;
  }
}

/** Enter en un campo pasa al siguiente en lugar de enviar el formulario a medias. */
function avanzarConEnter(origenId, destinoId) {
  $(origenId).addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); $(destinoId).focus(); }
  });
}

function conectarEventos() {
  $("formulario").addEventListener("submit", enviarFormulario);
  $("vence").addEventListener("input", alEscribirFecha);
  $("boton-cancelar-edicion").addEventListener("click", cancelarEdicion);
  $("boton-ejemplo").addEventListener("click", cargarEjemplo);
  $("boton-borrar-todo").addEventListener("click", borrarTodo);
  avanzarConEnter("nombre", "cantidad");
  avanzarConEnter("cantidad", "vence");

  $("pestana-despensa").addEventListener("click", () => mostrarPestana("despensa"));
  $("pestana-recetas").addEventListener("click", () => mostrarPestana("recetas"));
  $("solo-completas").addEventListener("change", (e) => { estado.soloCompletas = e.target.checked; renderRecetas(); });
  $("boton-crear-receta").addEventListener("click", () => abrirEditorReceta());
  $("boton-mis-recetas").addEventListener("click", abrirMisRecetas);

  // Editor de recetas
  $("formulario-receta").addEventListener("submit", guardarRecetaDelEditor);
  $("receta-agregar").addEventListener("click", agregarIngredienteReceta);
  $("receta-cancelar").addEventListener("click", cerrarEditorReceta);
  $("cerrar-receta").addEventListener("click", cerrarEditorReceta);
  $("dialogo-receta").addEventListener("cancel", (e) => { e.preventDefault(); cerrarEditorReceta(); }); // Esc / «atrás»
  avanzarConEnter("receta-nombre", "receta-ingrediente");
  avanzarConEnter("receta-ingrediente", "receta-cantidad");
  $("receta-cantidad").addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); agregarIngredienteReceta(); }
  });

  // «Mis recetas»
  $("cerrar-mis-recetas").addEventListener("click", () => $("dialogo-mis-recetas").close());
  $("mis-recetas-nueva").addEventListener("click", () => abrirEditorReceta());

  // Botones dentro de las listas (se dibujan de nuevo cada vez, por eso se usa delegación)
  document.addEventListener("click", (evento) => {
    const boton = evento.target.closest("[data-accion]");
    if (!boton) return;
    const { accion, id, nombre, indice } = boton.dataset;
    if (accion === "editar") editarIngrediente(id);
    else if (accion === "eliminar") eliminarIngrediente(id);
    else if (accion === "receta") alternarReceta(nombre);
    else if (accion === "receta-editar-fila") editarFilaReceta(Number(indice));
    else if (accion === "receta-quitar-fila") quitarFilaReceta(Number(indice));
    else if (accion === "mis-editar") abrirEditorReceta(estado.recetasPropias.find((r) => r.id === id));
    else if (accion === "mis-eliminar") eliminarRecetaPropia(id);
  });

  // Si la app queda abierta pasada la medianoche (o se vuelve a ella), los «días restantes» cambian.
  const siCambioElDia = () => { if (hoyIso() !== estado.hoy) renderTodo(); };
  setInterval(siCambioElDia, 60_000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) siCambioElDia(); });
}

function llenarUnidades() {
  const opciones = UNIDADES.map((u) => `<option value="${u}">${u}</option>`).join("");
  $("unidad").innerHTML = opciones;
  $("receta-unidad").innerHTML = opciones;
}

function registrarServiceWorker() {
  const seguro = location.protocol === "https:" || ["localhost", "127.0.0.1"].includes(location.hostname);
  if ("serviceWorker" in navigator && seguro) {
    navigator.serviceWorker.register("sw.js").catch(() => { /* sin el modo sin conexión la app se usa igual */ });
  }
}

function iniciar() {
  llenarUnidades();
  almacen = almacenDelNavegador();
  const avisos = [];
  if (almacen) {
    const ingredientes = cargarIngredientes(almacen);
    const recetas = cargarRecetas(almacen);
    estado.ingredientes = ingredientes.ingredientes;
    estado.recetasPropias = recetas.recetas;
    avisos.push(ingredientes.aviso, recetas.aviso);
  } else {
    avisos.push("Este navegador no permite guardar datos: lo que agregues se perderá al cerrar la página.");
  }
  avisoGeneral(avisos.filter(Boolean).join("\n"));
  conectarEventos();
  mostrarPestana("despensa");
  renderTodo();
  registrarServiceWorker();
}

iniciar();
