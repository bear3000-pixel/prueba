/** Pruebas del guardado en el dispositivo (localStorage) y de las fechas. */
import test from "node:test";
import assert from "node:assert/strict";

import {
  CLAVE_INGREDIENTES, CLAVE_RECETAS, ErrorAlmacenamiento, cargarIngredientes, cargarRecetas,
  guardarIngredientes, guardarRecetas,
} from "../js/almacenamiento.js";
import {
  crearIngrediente, diasEntre, fechaIso, hoyIso, nuevoId, sumarDias, estaPorVencer, estaVencido,
} from "../js/modelo.js";
import { crearReceta } from "../js/recetasUsuario.js";

/** Un localStorage falso, sin navegador. */
function almacenFalso({ limite = Infinity } = {}) {
  const datos = new Map();
  return {
    datos,
    getItem: (k) => (datos.has(k) ? datos.get(k) : null),
    setItem(k, v) {
      if (String(v).length > limite) throw new Error("QuotaExceededError");
      datos.set(k, String(v));
    },
    removeItem: (k) => datos.delete(k),
  };
}

const leche = () => crearIngrediente("Leche", "1,5", "L", "20/06/2026", "id1");
const pan = () => crearReceta("Pan casero", [["Harina", "500", "g"]], "Mezclar\nHornear", [], "r1");

test("sin nada guardado, empieza vacío y sin avisos", () => {
  const a = almacenFalso();
  assert.deepEqual(cargarIngredientes(a), { ingredientes: [], aviso: null });
  assert.deepEqual(cargarRecetas(a), { recetas: [], aviso: null });
});

test("guardar y cargar conserva los ingredientes", () => {
  const a = almacenFalso();
  guardarIngredientes(a, [leche(), crearIngrediente("Piña", 2, "unidades", "2026-07-01", "id2")]);
  const { ingredientes, aviso } = cargarIngredientes(a);
  assert.equal(aviso, null);
  assert.deepEqual(ingredientes.map((i) => [i.nombre, i.cantidad, i.unidad, i.vencimiento]),
    [["Leche", 1.5, "L", "2026-06-20"], ["Piña", 2, "unidades", "2026-07-01"]]);
});

test("guardar y cargar conserva las recetas propias", () => {
  const a = almacenFalso();
  guardarRecetas(a, [pan()]);
  const { recetas, aviso } = cargarRecetas(a);
  assert.equal(aviso, null);
  assert.deepEqual(recetas, [pan()]);
});

test("el formato guardado es el mismo que usa la versión de escritorio", () => {
  const a = almacenFalso();
  guardarIngredientes(a, [leche()]);
  guardarRecetas(a, [pan()]);
  assert.deepEqual(JSON.parse(a.getItem(CLAVE_INGREDIENTES)), {
    version: 1,
    ingredientes: [{ id: "id1", nombre: "Leche", cantidad: 1.5, unidad: "L", vencimiento: "2026-06-20" }],
  });
  assert.deepEqual(JSON.parse(a.getItem(CLAVE_RECETAS)), {
    version: 1,
    recetas: [{
      id: "r1", nombre: "Pan casero",
      ingredientes: [{ nombre: "Harina", cantidad: 500, unidad: "g" }],
      instrucciones: ["Mezclar", "Hornear"],
    }],
  });
});

test("datos dañados: no se cae, avisa y deja una copia de respaldo", () => {
  for (const [clave, cargar] of [[CLAVE_INGREDIENTES, cargarIngredientes], [CLAVE_RECETAS, cargarRecetas]]) {
    for (const malo of ["{esto no es json", "[]", '{"otra": 1}', '{"ingredientes": 5, "recetas": 5}', ""]) {
      const a = almacenFalso();
      a.setItem(clave, malo);
      const resultado = cargar(a);
      assert.deepEqual(Object.values(resultado)[0], []);
      assert.match(resultado.aviso, /dañad/);
      assert.equal(a.getItem(`${clave}.corrupto`), malo, "se conserva la copia");
      assert.equal(a.getItem(clave), null, "lo dañado se retira para no volver a fallar");
    }
  }
});

test("las entradas inválidas se omiten y las buenas se conservan", () => {
  const a = almacenFalso();
  a.setItem(CLAVE_INGREDIENTES, JSON.stringify({
    version: 1,
    ingredientes: [
      { nombre: "Leche", cantidad: 1, unidad: "L", vencimiento: "2026-06-20" },
      { nombre: "Malo", cantidad: -5, unidad: "L", vencimiento: "2026-06-20" },
      { nombre: "SinFecha", cantidad: 1, unidad: "L" },
      "no soy un objeto",
      null,
    ],
  }));
  const { ingredientes, aviso } = cargarIngredientes(a);
  assert.deepEqual(ingredientes.map((i) => i.nombre), ["Leche"]);
  assert.match(aviso, /4 ingrediente/);

  a.setItem(CLAVE_RECETAS, JSON.stringify({
    version: 1,
    recetas: [
      { id: "a", nombre: "Buena", ingredientes: [{ nombre: "Harina", cantidad: 1, unidad: "g" }], instrucciones: ["Cocinar"] },
      { id: "b", nombre: "Cantidad mala", ingredientes: [{ nombre: "Harina", cantidad: -4, unidad: "g" }], instrucciones: ["Cocinar"] },
      { id: "c", nombre: "Sin pasos", ingredientes: [{ nombre: "Harina", cantidad: 1, unidad: "g" }], instrucciones: [] },
    ],
  }));
  const { recetas, aviso: avisoRecetas } = cargarRecetas(a);
  assert.deepEqual(recetas.map((r) => r.nombre), ["Buena"]);
  assert.match(avisoRecetas, /2 receta/);
});

test("si no hay espacio para guardar, lanza un error claro (no se pierde en silencio)", () => {
  const a = almacenFalso({ limite: 10 });
  assert.throws(() => guardarIngredientes(a, [leche()]), ErrorAlmacenamiento);
  assert.throws(() => guardarRecetas(a, [pan()]), (e) => e instanceof ErrorAlmacenamiento && /No se pudieron guardar/.test(e.message));
});

test("fechas: días entre fechas, meses y años bisiestos", () => {
  assert.equal(diasEntre("2026-06-15", "2026-06-17"), 2);
  assert.equal(diasEntre("2026-06-15", "2026-06-14"), -1);
  assert.equal(diasEntre("2026-12-31", "2027-01-01"), 1);
  assert.equal(diasEntre("2028-02-28", "2028-03-01"), 2); // 2028 es bisiesto
  assert.equal(diasEntre("2026-02-28", "2026-03-01"), 1);
  assert.equal(sumarDias("2026-12-30", 3), "2027-01-02");
  assert.equal(sumarDias("2026-03-01", -1), "2026-02-28");
  assert.equal(sumarDias("2026-06-15", 200), "2027-01-01");
});

test("fechas: hoy según el reloj del dispositivo (hora local, no UTC)", () => {
  assert.equal(hoyIso(new Date(2026, 10, 11, 23, 59)), "2026-11-11");
  assert.equal(hoyIso(new Date(2026, 0, 5, 0, 1)), "2026-01-05");
  assert.equal(fechaIso(2026, 1, 5), "2026-01-05");
});

test("estado de un ingrediente según hoy", () => {
  const hoy = "2026-06-15";
  const con = (dias) => ({ vencimiento: sumarDias(hoy, dias) });
  assert.ok(estaVencido(con(-1), hoy));
  assert.ok(!estaVencido(con(0), hoy)); // vence hoy: todavía sirve
  assert.ok(estaPorVencer(con(0), hoy) && estaPorVencer(con(3), hoy));
  assert.ok(!estaPorVencer(con(4), hoy) && !estaPorVencer(con(-1), hoy));
});

test("los ids nuevos no se repiten", () => {
  assert.equal(new Set(Array.from({ length: 500 }, nuevoId)).size, 500);
});
