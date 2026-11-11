/**
 * Lógica de Food Saver (versión web / Android): clasificar ingredientes y sugerir recetas.
 *
 * Mismo comportamiento que food_saver/logica.py. Son funciones puras: la fecha de «hoy» entra
 * como parámetro y no tocan la pantalla ni el almacenamiento, por eso se prueban fácilmente.
 */
import {
  DIAS_POR_VENCER, convertirCantidad, diasParaVencer, estaVencido, normalizar,
} from "./modelo.js";

// Puntos que aporta a una receta cada ingrediente que SÍ tienes, según qué tan cerca esté de vencer.
export const PUNTOS_URGENTE = 5; // vence en DIAS_POR_VENCER días o menos
export const PUNTOS_PRONTO = 3; // vence en 7 días o menos
export const PUNTOS_NORMAL = 1; // el resto
export const DIAS_PRONTO = 7;

const comparar = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

// --------------------------------------------------------------------------- //
// Ordenar y separar vencidos
// --------------------------------------------------------------------------- //
/** Del que vence primero al que vence último; empata por nombre. */
export function ordenarPorVencimiento(ingredientes) {
  return [...ingredientes].sort((a, b) =>
    comparar(a.vencimiento, b.vencimiento) || comparar(normalizar(a.nombre), normalizar(b.nombre)));
}

/** Devuelve [vigentes, vencidos], cada lista ordenada por fecha de vencimiento. */
export function clasificar(ingredientes, hoy) {
  const lista = [...ingredientes];
  return [
    ordenarPorVencimiento(lista.filter((i) => !estaVencido(i, hoy))),
    ordenarPorVencimiento(lista.filter((i) => estaVencido(i, hoy))),
  ];
}

// --------------------------------------------------------------------------- //
// Coincidencia de nombres
// --------------------------------------------------------------------------- //
/** Formas singulares posibles: «tomates»->«tomate», «limones»->«limon», «frijoles»->«frijol». */
function variantes(palabra) {
  const v = new Set([palabra]);
  if (palabra.length > 3 && palabra.endsWith("es")) v.add(palabra.slice(0, -2));
  if (palabra.length > 2 && palabra.endsWith("s")) v.add(palabra.slice(0, -1));
  return v;
}

/** ¿El ingrediente que pide la receta («tomate») es el que tiene el usuario («Tomates cherry»)?
 *  Ignora mayúsculas, acentos y plurales; cada palabra de la receta debe aparecer en el nombre del usuario. */
export function coincideIngrediente(requerido, disponible) {
  const disponibles = normalizar(disponible).split(" ").filter(Boolean).map(variantes);
  for (const palabra of normalizar(requerido).split(" ").filter(Boolean)) {
    const propias = variantes(palabra);
    if (!disponibles.some((v) => [...propias].some((x) => v.has(x)))) return false;
  }
  return true;
}

// --------------------------------------------------------------------------- //
// Sugerencia de recetas
// --------------------------------------------------------------------------- //
const puntos = (dias) => (dias <= DIAS_POR_VENCER ? PUNTOS_URGENTE : dias <= DIAS_PRONTO ? PUNTOS_PRONTO : PUNTOS_NORMAL);

/** Suma lo que hay de un ingrediente expresado en `unidad` (convierte kg↔g y L↔ml); null si no es comparable. */
function cantidadTotal(lotes, unidad) {
  let total = 0;
  let comparable = false;
  for (const lote of lotes) {
    const c = convertirCantidad(lote.cantidad, lote.unidad, unidad);
    if (c !== null) { total += c; comparable = true; }
  }
  return comparable ? total : null;
}

/** El lote que vence primero (el primero de la lista si empatan). */
function loteQueVenceAntes(lotes) {
  let mejor = lotes[0];
  for (const lote of lotes.slice(1)) {
    if (comparar([lote.vencimiento, normalizar(lote.nombre)].join("\u0000"),
                 [mejor.vencimiento, normalizar(mejor.nombre)].join("\u0000")) < 0) mejor = lote;
  }
  return mejor;
}

/** Una sugerencia es completa si no falta ni es insuficiente ningún ingrediente. */
export const esCompleta = (s) => s.faltantes.length === 0 && s.insuficientes.length === 0;
export const totalIngredientes = (s) => s.usados.length + s.insuficientes.length + s.faltantes.length;
/** El ingrediente (suficiente o no) cuyo lote vence primero. Tiene .lote y .dias. */
export const usoMasUrgente = (s) =>
  [...s.usados, ...s.insuficientes].reduce((a, b) => (b.dias < a.dias ? b : a));

/**
 * Recetas que se pueden armar (total o parcialmente) con ingredientes NO vencidos.
 *  - Los vencidos se excluyen; si una receta los pide, se listan como faltantes avisando que están vencidos.
 *  - Con varios lotes del mismo ingrediente se usa el que vence primero.
 *  - Solo se sugieren recetas donde tengas al menos un ingrediente.
 *  - Si la receta indica cantidades (las recetas propias) se compara con lo que hay, sumando los lotes
 *    vigentes. Si las unidades no se pueden comparar (p. ej. «2 unidades» contra «500 g») se da por disponible.
 *  - Orden: más puntaje primero, luego las que menos ingredientes faltan, luego alfabético.
 */
export function sugerirRecetas(ingredientes, recetas, hoy, soloCompletas = false) {
  const lista = [...ingredientes];
  const vigentes = lista.filter((i) => !estaVencido(i, hoy));
  const vencidos = lista.filter((i) => estaVencido(i, hoy));
  const sugerencias = [];

  for (const receta of recetas) {
    const usados = [];
    const insuficientes = [];
    const faltantes = [];
    const descartados = [];

    receta.ingredientes.forEach((requerido, indice) => {
      const necesita = receta.cantidades?.[indice] ?? null;
      const lotes = vigentes.filter((i) => coincideIngrediente(requerido, i.nombre));
      if (lotes.length) {
        const lote = loteQueVenceAntes(lotes);
        const dias = diasParaVencer(lote, hoy);
        if (necesita) {
          const tiene = cantidadTotal(lotes, necesita[1]);
          if (tiene !== null && tiene + 1e-9 < necesita[0]) {
            insuficientes.push({ requerido, lote, dias, necesita, tienes: [tiene, necesita[1]] });
            return;
          }
        }
        usados.push({ requerido, lote, dias, necesita });
      } else {
        faltantes.push(requerido);
        if (vencidos.some((i) => coincideIngrediente(requerido, i.nombre))) descartados.push(requerido);
      }
    });

    if (!usados.length && !insuficientes.length) continue; // no tienes nada para esta receta
    if (soloCompletas && (faltantes.length || insuficientes.length)) continue;

    const aprovechados = [...usados, ...insuficientes]; // los dos usarían algo de la despensa
    sugerencias.push({
      receta, usados, faltantes, descartadosPorVencidos: descartados, insuficientes,
      puntaje: aprovechados.reduce((suma, u) => suma + puntos(u.dias), 0),
      diasMasUrgente: Math.min(...aprovechados.map((u) => u.dias)),
    });
  }

  sugerencias.sort((a, b) =>
    (b.puntaje - a.puntaje)
    || ((a.faltantes.length + a.insuficientes.length) - (b.faltantes.length + b.insuficientes.length))
    || comparar(normalizar(a.receta.nombre), normalizar(b.receta.nombre)));
  return sugerencias;
}
