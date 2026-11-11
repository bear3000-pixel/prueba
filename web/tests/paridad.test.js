/**
 * Paridad Python ↔ JavaScript.
 *
 * web/tests/referencia.json lo genera el código PYTHON (generar_referencia.py). Aquí se ejecuta el
 * JavaScript con exactamente los mismos casos y se exige el MISMO resultado: mismos valores, mismos
 * mensajes de error y mismo orden. Si alguien cambia una regla en un lado y no en el otro, falla.
 *
 * Ejecutar:  node --test web/tests/
 */
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import {
  ErrorValidacion, autoformatearFecha, convertirCantidad, describirVencimiento, formatearCantidad,
  formatearFecha, normalizar, parsearFecha, textoCantidad, validarCantidad, validarNombre, validarUnidad,
  UNIDADES,
} from "../js/modelo.js";
import {
  clasificar, coincideIngrediente, esCompleta, ordenarPorVencimiento, sugerirRecetas, totalIngredientes,
} from "../js/logica.js";
import { RECETAS } from "../js/recetas.js";
import { crearReceta, recetaADatos, recetaDesdeDatos, validarPasos } from "../js/recetasUsuario.js";
import { ingredientesDeEjemplo } from "../js/ejemplos.js";

const ref = JSON.parse(readFileSync(new URL("./referencia.json", import.meta.url), "utf8"));

/** {ok: valor} o {error, campo}: la misma forma que usa el generador de Python. */
function resultado(funcion) {
  try {
    return { ok: funcion() };
  } catch (error) {
    if (error instanceof ErrorValidacion) return { error: error.message, campo: error.campo };
    throw error;
  }
}

/** Compara cada caso por separado para que el mensaje de fallo diga cuál fue. */
function porCaso(nombre, casos, calcular, esperado = (c) => c.salida) {
  test(nombre, () => {
    assert.ok(casos.length > 0, "la referencia no trae casos");
    for (const caso of casos) {
      assert.deepEqual(calcular(caso), esperado(caso), `caso: ${JSON.stringify(caso).slice(0, 300)}`);
    }
  });
}

const sinEntrada = ({ entrada, ...resto }) => resto;

test("las unidades son las mismas", () => assert.deepEqual(UNIDADES, ref.unidades));

porCaso("autoformato de fecha (lo que se escribe en «Vence»)", ref.autoformato,
  (c) => autoformatearFecha(c.entrada, c.escribiendo));
porCaso("parsear fecha: valores y mensajes de error", ref.fechas,
  (c) => resultado(() => parsearFecha(c.entrada)), sinEntrada);
porCaso("validar cantidad: valores y mensajes de error", ref.cantidades,
  (c) => resultado(() => validarCantidad(c.entrada)), sinEntrada);
porCaso("validar nombre", ref.nombres, (c) => resultado(() => validarNombre(c.entrada)), sinEntrada);
porCaso("validar unidad", ref.unidadesValidas, (c) => resultado(() => validarUnidad(c.entrada)), sinEntrada);
porCaso("convertir cantidades (kg↔g, L↔ml)", ref.conversiones, (c) => convertirCantidad(c.cantidad, c.de, c.a));
porCaso("formato de cantidad", ref.formatoCantidad, (c) => formatearCantidad(c.entrada));
porCaso("cantidad con su unidad en singular o plural", ref.textoCantidad, (c) => textoCantidad(c.cantidad, c.unidad));
porCaso("descripción del vencimiento", ref.describirVencimiento, (c) => describirVencimiento(c.dias));
porCaso("fecha DD/MM/AAAA", ref.formatoFecha, (c) => formatearFecha(c.entrada));
porCaso("normalizar nombres", ref.normalizar, (c) => normalizar(c.entrada));
porCaso("coincidencia de nombres (plurales, acentos…)", ref.coincidencias,
  (c) => coincideIngrediente(c.requerido, c.disponible));
porCaso("pasos de preparación", ref.pasos, (c) => resultado(() => validarPasos(c.entrada)), sinEntrada);

test("crear recetas propias: valores y mensajes de error", () => {
  const nombresExistentes = RECETAS.map((r) => r.nombre);
  for (const caso of ref.recetasNuevas) {
    const c = caso.caso;
    const obtenido = resultado(() => crearReceta(c.nombre, c.filas, c.pasos, nombresExistentes, "r0"));
    const { caso: _omitido, ...esperado } = caso;
    assert.deepEqual(obtenido, esperado, `receta: ${JSON.stringify(c).slice(0, 200)}`);
  }
});

test("las 17 recetas predefinidas son las mismas que en Python", () => {
  assert.equal(RECETAS.length, 17);
  assert.ok(RECETAS.every((r) => r.cantidades.length === 0 && r.propia === false && r.id === ""));
});

const propias = ref.recetasPropiasEspec.map((e) => crearReceta(e.nombre, e.filas, e.pasos, [], e.id));

test("las recetas propias de referencia se construyen igual", () => {
  assert.deepEqual(propias, ref.recetasPropias);
});

test("la forma guardada de las recetas es la misma (y se puede volver a leer)", () => {
  assert.deepEqual(propias.map(recetaADatos), ref.datosGuardadosDeRecetas);
  assert.deepEqual(ref.datosGuardadosDeRecetas.map(recetaDesdeDatos), propias);
});

const aIngrediente = ([nombre, cantidad, unidad, vencimiento], i) =>
  ({ id: `i${i}`, nombre, cantidad, unidad, vencimiento });

test("los ingredientes de ejemplo son los mismos", () => {
  const obtenido = ingredientesDeEjemplo(ref.hoy).map((i) => [i.nombre, i.cantidad, i.unidad, i.vencimiento]);
  assert.deepEqual(obtenido, ref.ejemplos);
});

test("orden por vencimiento y separación de vencidos", () => {
  const despensa = ref.orden.despensa.map(([nombre, cantidad, unidad, vencimiento, id]) =>
    ({ id, nombre, cantidad, unidad, vencimiento }));
  const [vigentes, vencidos] = clasificar(despensa, ref.hoy);
  assert.deepEqual(ordenarPorVencimiento(despensa).map((i) => i.id), ref.orden.ordenados);
  assert.deepEqual(vigentes.map((i) => i.id), ref.orden.vigentes);
  assert.deepEqual(vencidos.map((i) => i.id), ref.orden.vencidos);
});

/** Misma forma resumida que genera Python (_resumen). */
function resumen(sugerencias) {
  return sugerencias.map((s) => ({
    receta: s.receta.nombre,
    usados: s.usados.map((u) => [u.requerido, u.lote.nombre, u.dias, u.necesita]),
    faltantes: s.faltantes,
    descartados: s.descartadosPorVencidos,
    insuficientes: s.insuficientes.map((i) => [i.requerido, i.lote.nombre, i.dias, i.necesita, i.tienes]),
    puntaje: s.puntaje,
    diasMasUrgente: s.diasMasUrgente,
    completa: esCompleta(s),
    total: totalIngredientes(s),
  }));
}

for (const escenario of ref.sugerencias) {
  test(`sugerencias de recetas: ${escenario.caso}`, () => {
    const despensa = escenario.despensa.map(aIngrediente);
    const recetas = escenario.recetas === "predefinidas" ? RECETAS : [...RECETAS, ...propias];
    const obtenido = resumen(sugerirRecetas(despensa, recetas, ref.hoy, escenario.soloCompletas));
    assert.deepEqual(obtenido, escenario.resultado);
  });
}
