/**
 * Datos de ejemplo para la demostración (botón «Cargar ejemplo»).
 * Los vencimientos se calculan RELATIVOS a hoy, así la demo siempre muestra ingredientes por vencer y
 * vencidos sin importar qué día se presente. Todos los datos son ficticios (igual que food_saver/ejemplos.py).
 */
import { crearIngrediente, sumarDias } from "./modelo.js";

// [nombre, cantidad, unidad, días hasta vencer; negativo = ya vencido]
const EJEMPLOS = [
  ["Pan de molde", 1, "paquetes", 2],
  ["Leche", 1, "L", 2],
  ["Espinaca", 1, "paquetes", 1],
  ["Tomates", 4, "unidades", 3],
  ["Huevos", 6, "unidades", 5],
  ["Zanahorias", 4, "unidades", 6],
  ["Queso", 200, "g", 10],
  ["Cebolla", 3, "unidades", 12],
  ["Papas", 5, "unidades", 15],
  ["Arroz", 1, "kg", 200],
  ["Pollo", 500, "g", -1], // vencido
  ["Yogur", 2, "unidades", -3], // vencido
];

export function ingredientesDeEjemplo(hoy) {
  return EJEMPLOS.map(([nombre, cantidad, unidad, dias]) =>
    crearIngrediente(nombre, cantidad, unidad, sumarDias(hoy, dias)));
}
