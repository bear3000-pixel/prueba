/**
 * Recetas creadas por el usuario (versión web / Android): validación de lo que escribe.
 *
 * Mismas reglas y mensajes que food_saver/recetas_usuario.py. Una receta propia tiene nombre,
 * ingredientes (cada uno con CANTIDAD y UNIDAD) y pasos de preparación. Reutiliza las validaciones de
 * modelo.js, así que valen las mismas reglas que al agregar un ingrediente: no se aceptan cantidades
 * vacías, cero, negativas, con letras, en notación científica ni enormes.
 */
import {
  ErrorValidacion, normalizar, nuevoId, validarCantidad, validarNombre, validarUnidad,
} from "./modelo.js";
import { coincideIngrediente } from "./logica.js";

export const MAX_INGREDIENTES = 20;
export const MAX_PASOS = 20;
export const LARGO_MAX_NOMBRE = 60;
export const LARGO_MAX_PASO = 300;

const largo = (texto) => [...texto].length;
const tieneLetra = (texto) => /\p{L}/u.test(texto);

export function validarNombreReceta(texto) {
  const nombre = String(texto ?? "").split(/\s+/).filter(Boolean).join(" ");
  if (!nombre) throw new ErrorValidacion("Escribe el nombre de la receta.", "nombre");
  if (largo(nombre) > LARGO_MAX_NOMBRE) {
    throw new ErrorValidacion(
      `El nombre de la receta es demasiado largo (máximo ${LARGO_MAX_NOMBRE} caracteres).`, "nombre");
  }
  if (!tieneLetra(nombre)) throw new ErrorValidacion("El nombre de la receta debe contener letras.", "nombre");
  return nombre;
}

/** Un ingrediente de la receta: nombre con letras, cantidad > 0 y unidad de la lista. Devuelve [nombre, cantidad, unidad]. */
export function validarIngredienteReceta(nombre, cantidad, unidad) {
  const nombreOk = validarNombre(nombre);
  if (String(cantidad).trim() === "") {
    throw new ErrorValidacion(`Falta la cantidad de «${nombreOk}».`, "cantidad");
  }
  return [nombreOk, validarCantidad(cantidad), validarUnidad(unidad)];
}

// Quita la numeración o viñeta que el usuario escriba al inicio («1. », «2) », «- », «• »), porque la
// pantalla ya numera los pasos. «2 huevos» o «1.5 tazas» NO se tocan.
const PREFIJO_PASO = /^\s*(?:[0-9]+\s*[.)]|[-*•])\s+/;
const SALTOS_DE_LINEA = /\r\n|[\n\r\v\f\x1c-\x1e\x85\u2028\u2029]/;

/** Convierte el texto de preparación (un paso por línea) en una lista de pasos limpios. */
export function validarPasos(pasos) {
  const lineas = typeof pasos === "string" ? pasos.split(SALTOS_DE_LINEA) : [...pasos];
  const limpios = lineas.map((l) => String(l).replace(PREFIJO_PASO, "").trim()).filter(Boolean);
  if (!limpios.length) throw new ErrorValidacion("Escribe al menos un paso de preparación.", "pasos");
  if (limpios.length > MAX_PASOS) {
    throw new ErrorValidacion(`Hay demasiados pasos (máximo ${MAX_PASOS}).`, "pasos");
  }
  limpios.forEach((paso, i) => {
    if (largo(paso) > LARGO_MAX_PASO) {
      throw new ErrorValidacion(`El paso ${i + 1} es demasiado largo (máximo ${LARGO_MAX_PASO} caracteres).`, "pasos");
    }
    if (!tieneLetra(paso)) throw new ErrorValidacion(`El paso ${i + 1} debe contener texto.`, "pasos");
  });
  return limpios;
}

const mismoIngrediente = (a, b) => coincideIngrediente(a, b) && coincideIngrediente(b, a);

/**
 * Valida todo y devuelve la receta lista para guardar.
 * `ingredientes`: filas [nombre, cantidad, unidad]. `nombresExistentes`: nombres de las demás recetas,
 * para no repetir ninguno (se ignoran mayúsculas y acentos).
 */
export function crearReceta(nombre, ingredientes, pasos, nombresExistentes = [], id = null) {
  const nombreOk = validarNombreReceta(nombre);
  if (nombresExistentes.some((otro) => normalizar(otro) === normalizar(nombreOk))) {
    throw new ErrorValidacion(`Ya existe una receta llamada «${nombreOk}». Elige otro nombre.`, "nombre");
  }
  const filas = [...ingredientes];
  if (!filas.length) throw new ErrorValidacion("Agrega al menos un ingrediente a la receta.", "ingredientes");
  if (filas.length > MAX_INGREDIENTES) {
    throw new ErrorValidacion(`Hay demasiados ingredientes (máximo ${MAX_INGREDIENTES}).`, "ingredientes");
  }
  const validados = [];
  for (const fila of filas) {
    const ingrediente = validarIngredienteReceta(...fila);
    if (validados.some((anterior) => mismoIngrediente(ingrediente[0], anterior[0]))) {
      throw new ErrorValidacion(`«${ingrediente[0]}» está repetido en la receta.`, "ingredientes");
    }
    validados.push(ingrediente);
  }
  return {
    nombre: nombreOk,
    ingredientes: validados.map((f) => f[0]),
    instrucciones: validarPasos(pasos),
    cantidades: validados.map((f) => [f[1], f[2]]),
    propia: true,
    id: id || nuevoId(),
  };
}

// --------------------------------------------------------------------------- //
// Forma guardada (la misma que usa el Python: recetas_propias.json)
// --------------------------------------------------------------------------- //
export function recetaADatos(receta) {
  return {
    id: receta.id,
    nombre: receta.nombre,
    ingredientes: receta.ingredientes.map((nombre, i) => ({
      nombre, cantidad: receta.cantidades[i][0], unidad: receta.cantidades[i][1],
    })),
    instrucciones: [...receta.instrucciones],
  };
}

/** Reconstruye una receta guardada revalidándola entera (por si los datos se dañaron o se editaron a mano). */
export function recetaDesdeDatos(datos) {
  const filas = datos.ingredientes.map((f) => [f.nombre, f.cantidad, f.unidad]);
  return crearReceta(datos.nombre, filas, datos.instrucciones, [], datos.id);
}
