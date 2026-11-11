/**
 * Guardado en el dispositivo (versión web / Android) con localStorage.
 *
 * Funciona igual dentro de la app de Android (el WebView conserva los datos), en el navegador y en la
 * app instalada desde el navegador. Cada «almacén» se guarda como JSON {version, <lista>} bajo una clave.
 * Si lo guardado está dañado no se pierde en silencio: se copia a una clave «.corrupto» y la app
 * arranca con la lista vacía avisando al usuario. Los datos son los mismos que usa la versión de
 * escritorio, así que se pueden llevar de una a otra.
 *
 * `almacen` es cualquier objeto con getItem / setItem / removeItem (localStorage, o uno falso en las pruebas).
 */
import { ingredienteDesdeDatos } from "./modelo.js";
import { recetaADatos, recetaDesdeDatos } from "./recetasUsuario.js";

export const CLAVE_INGREDIENTES = "foodsaver.ingredientes";
export const CLAVE_RECETAS = "foodsaver.recetas";
const VERSION = 1;

/** No se pudo guardar (almacenamiento lleno, bloqueado o desactivado). */
export class ErrorAlmacenamiento extends Error {
  constructor(mensaje) {
    super(mensaje);
    this.name = "ErrorAlmacenamiento";
  }
}

/** El almacén del navegador, o null si no se puede usar (modo privado estricto, bloqueado…). */
export function almacenDelNavegador() {
  try {
    const prueba = "foodsaver.prueba";
    globalThis.localStorage.setItem(prueba, "1");
    globalThis.localStorage.removeItem(prueba);
    return globalThis.localStorage;
  } catch {
    return null;
  }
}

function guardarJson(almacen, clave, contenido) {
  try {
    almacen.setItem(clave, JSON.stringify(contenido));
  } catch (error) {
    throw new ErrorAlmacenamiento(
      `No se pudieron guardar los datos en este dispositivo (${error?.message ?? "error desconocido"}).`);
  }
}

/** Lee `lista` de un almacén. Devuelve { elementos, aviso }; nunca lanza por datos malos. */
function cargarLista(almacen, clave, nombreLista, aElemento, textoDanado, textoOmitidos) {
  const crudo = almacen.getItem(clave);
  if (crudo === null) return { elementos: [], aviso: null };

  let entradas;
  try {
    entradas = JSON.parse(crudo)?.[nombreLista];
    if (!Array.isArray(entradas)) throw new TypeError(`'${nombreLista}' debe ser una lista`);
  } catch {
    try {
      almacen.setItem(`${clave}.corrupto`, crudo);
      almacen.removeItem(clave);
    } catch { /* si ni siquiera se puede respaldar, se sigue igual */ }
    return { elementos: [], aviso: textoDanado };
  }

  const elementos = [];
  let omitidos = 0;
  for (const entrada of entradas) {
    try { elementos.push(aElemento(entrada)); } catch { omitidos += 1; }
  }
  return { elementos, aviso: omitidos ? textoOmitidos(omitidos) : null };
}

/** Ingredientes guardados: { ingredientes, aviso }. */
export function cargarIngredientes(almacen) {
  const { elementos, aviso } = cargarLista(
    almacen, CLAVE_INGREDIENTES, "ingredientes", ingredienteDesdeDatos,
    "Los datos guardados estaban dañados y la app arrancó vacía. Se conservó una copia de respaldo en este dispositivo.",
    (n) => `Se omitieron ${n} ingrediente(s) con datos inválidos en lo guardado.`);
  return { ingredientes: elementos, aviso };
}

export function guardarIngredientes(almacen, ingredientes) {
  guardarJson(almacen, CLAVE_INGREDIENTES, { version: VERSION, ingredientes });
}

/** Recetas propias guardadas: { recetas, aviso }. */
export function cargarRecetas(almacen) {
  const { elementos, aviso } = cargarLista(
    almacen, CLAVE_RECETAS, "recetas", recetaDesdeDatos,
    "Tus recetas guardadas estaban dañadas y se empezó con la lista vacía. Se conservó una copia de respaldo en este dispositivo.",
    (n) => `Se omitieron ${n} receta(s) con datos inválidos en lo guardado.`);
  return { recetas: elementos, aviso };
}

export function guardarRecetas(almacen, recetas) {
  guardarJson(almacen, CLAVE_RECETAS, { version: VERSION, recetas: recetas.map(recetaADatos) });
}
