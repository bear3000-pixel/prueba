/**
 * Modelo de datos y validaciones de Food Saver (versión web / Android).
 *
 * Es el MISMO conjunto de reglas que food_saver/modelo.py (la versión de escritorio): los mismos
 * mensajes en español y los mismos límites. web/tests/ compara este archivo con el Python usando
 * casos de referencia generados desde el propio Python, para que las dos versiones no se separen.
 *
 * Las fechas se manejan como texto ISO «AAAA-MM-DD» (así se guardan, igual que en el Python).
 */

export const UNIDADES = ["unidades", "kg", "g", "L", "ml", "tazas", "paquetes", "latas"];
export const DIAS_POR_VENCER = 3; // «por vencer» = faltan 3 días o menos
export const CANTIDAD_MAXIMA = 1_000_000;
export const LARGO_MAXIMO_NOMBRE = 50;

/** Dato inválido. `campo` indica qué campo corregir (opcional). */
export class ErrorValidacion extends Error {
  constructor(mensaje, campo = null) {
    super(mensaje);
    this.name = "ErrorValidacion";
    this.campo = campo;
  }
}

const tieneLetra = (texto) => /\p{L}/u.test(texto);
const largo = (texto) => [...texto].length; // cuenta caracteres, no unidades UTF-16

// --------------------------------------------------------------------------- //
// Validaciones de texto -> valores
// --------------------------------------------------------------------------- //
export function validarNombre(texto) {
  const nombre = String(texto ?? "").split(/\s+/).filter(Boolean).join(" ");
  if (!nombre) throw new ErrorValidacion("Escribe el nombre del ingrediente.", "nombre");
  if (largo(nombre) > LARGO_MAXIMO_NOMBRE) {
    throw new ErrorValidacion(
      `El nombre es demasiado largo (máximo ${LARGO_MAXIMO_NOMBRE} caracteres).`, "nombre");
  }
  if (!tieneLetra(nombre)) throw new ErrorValidacion("El nombre debe contener letras.", "nombre");
  return nombre;
}

/** Acepta coma o punto decimal ("1,5" o "1.5"). Rechaza vacío, letras, negativos, cero,
 *  notación científica, "nan"/"inf" y valores absurdamente grandes. */
export function validarCantidad(texto) {
  const crudo = String(texto).trim().replace(/,/g, ".");
  if (crudo === "") throw new ErrorValidacion("Escribe la cantidad.", "cantidad");
  if (crudo.startsWith("-")) {
    throw new ErrorValidacion("La cantidad debe ser mayor que cero.", "cantidad");
  }
  // Solo dígitos con un punto decimal opcional: deja fuera "nan", "inf", "1e5" y "1_000".
  if (!/^(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)$/.test(crudo)) {
    throw new ErrorValidacion("La cantidad debe ser un número (por ejemplo 2 o 1,5).", "cantidad");
  }
  const valor = Number(parseFloat(crudo).toFixed(3));
  if (valor <= 0) throw new ErrorValidacion("La cantidad debe ser mayor que cero.", "cantidad");
  if (valor > CANTIDAD_MAXIMA) {
    throw new ErrorValidacion("La cantidad es demasiado grande (máximo 1.000.000).", "cantidad");
  }
  return valor;
}

export function validarUnidad(texto) {
  const unidad = String(texto ?? "").trim();
  if (!UNIDADES.includes(unidad)) throw new ErrorValidacion("Elige una unidad de la lista.", "unidad");
  return unidad;
}

// --------------------------------------------------------------------------- //
// Fechas (texto ISO «AAAA-MM-DD»)
// --------------------------------------------------------------------------- //
const dosDigitos = (n) => String(n).padStart(2, "0");
const esBisiesto = (a) => (a % 4 === 0 && a % 100 !== 0) || a % 400 === 0;
const diasDelMes = (a, m) => [31, esBisiesto(a) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1];

export function fechaIso(anio, mes, dia) {
  return `${String(anio).padStart(4, "0")}-${dosDigitos(mes)}-${dosDigitos(dia)}`;
}

/** La fecha de hoy según el reloj del dispositivo, como «AAAA-MM-DD». */
export function hoyIso(ahora = new Date()) {
  return fechaIso(ahora.getFullYear(), ahora.getMonth() + 1, ahora.getDate());
}

function aUtc(iso) {
  const [a, m, d] = iso.split("-").map(Number);
  return Date.UTC(a, m - 1, d);
}

export function diasEntre(desdeIso, hastaIso) {
  return Math.round((aUtc(hastaIso) - aUtc(desdeIso)) / 86_400_000);
}

export function sumarDias(iso, dias) {
  const f = new Date(aUtc(iso) + dias * 86_400_000);
  return fechaIso(f.getUTCFullYear(), f.getUTCMonth() + 1, f.getUTCDate());
}

const FORMATOS_FECHA = [
  { re: /^([0-9]{1,2})\/([0-9]{1,2})\/([0-9]{4})$/, orden: "dma" },
  { re: /^([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})$/, orden: "amd" },
  { re: /^([0-9]{1,2})-([0-9]{1,2})-([0-9]{4})$/, orden: "dma" },
];

/** Acepta DD/MM/AAAA, AAAA-MM-DD o DD-MM-AAAA. Rechaza fechas que no existen. Devuelve «AAAA-MM-DD». */
export function parsearFecha(texto) {
  const crudo = String(texto ?? "").trim();
  if (!crudo) {
    throw new ErrorValidacion("Escribe la fecha de vencimiento (DD/MM/AAAA).", "vencimiento");
  }
  for (const { re, orden } of FORMATOS_FECHA) {
    const m = re.exec(crudo);
    if (!m) continue;
    const [dia, mes, anio] = (orden === "dma" ? [m[1], m[2], m[3]] : [m[3], m[2], m[1]]).map(Number);
    if (anio < 1 || mes < 1 || mes > 12 || dia < 1 || dia > diasDelMes(anio, mes)) continue; // no existe
    // Filtra errores de dedo típicos como 25/12/0226 o 25/12/2926.
    if (anio < 2000 || anio > 2100) {
      throw new ErrorValidacion("El año del vencimiento debe estar entre 2000 y 2100.", "vencimiento");
    }
    return fechaIso(anio, mes, dia);
  }
  throw new ErrorValidacion(
    "Fecha no válida. Usa DD/MM/AAAA (por ejemplo 25/12/2026) y verifica que el día exista.",
    "vencimiento");
}

const DIGITOS = "0123456789";
const SEPARADORES = "/-.";

/** Da formato DD/MM/AAAA MIENTRAS se escribe: «02112026» -> «02/11/2026».
 *  Solo acepta dígitos; con `agregarBarra` (se está escribiendo, no borrando) pone la barra apenas se
 *  completa el día o el mes; «2/» -> «02/»; un AAAA-MM-DD pegado se convierte; máximo 8 dígitos.
 *  Solo cambia la FORMA: que la fecha exista lo decide parsearFecha. */
export function autoformatearFecha(texto, agregarBarra = false) {
  texto = String(texto ?? "");
  const iso = /^\s*([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})\s*$/.exec(texto);
  if (iso) return `${dosDigitos(Number(iso[3]))}/${dosDigitos(Number(iso[2]))}/${iso[1]}`;

  const maximos = [2, 2, 4]; // largo de día, mes y año
  const campos = [""];
  for (const caracter of texto) {
    let actual = campos.length - 1;
    if (DIGITOS.includes(caracter)) {
      if (campos[actual].length === maximos[actual]) {
        if (actual === 2) break; // el año está completo: lo demás sobra
        campos.push(""); // el campo se llenó: el dígito pasa al siguiente
        actual += 1;
      }
      campos[actual] += caracter;
    } else if (SEPARADORES.includes(caracter)) {
      if (campos[actual] === "") continue; // sin barras al comienzo ni dobles
      if (actual === 2) break;
      if (campos[actual].length === 1) campos[actual] = "0" + campos[actual];
      campos.push("");
    }
    // cualquier otro carácter (letras, espacios) se descarta
  }
  let resultado = campos.join("/");
  const ultimo = campos.length - 1;
  if (agregarBarra && ultimo < 2 && campos[ultimo].length === maximos[ultimo]) resultado += "/";
  return resultado;
}

/** DD/MM/AAAA a partir de «AAAA-MM-DD». */
export function formatearFecha(iso) {
  const [a, m, d] = iso.split("-");
  return `${d}/${m}/${a}`;
}

// --------------------------------------------------------------------------- //
// Cantidades y unidades
// --------------------------------------------------------------------------- //
const BASE = { g: ["masa", 1], kg: ["masa", 1000], ml: ["volumen", 1], L: ["volumen", 1000] };

/** Convierte entre kg↔g y L↔ml. Devuelve null si no se pueden comparar («unidades» con «g»). */
export function convertirCantidad(cantidad, de, a) {
  if (de === a) return Number(cantidad);
  if (de in BASE && a in BASE && BASE[de][0] === BASE[a][0]) return (cantidad * BASE[de][1]) / BASE[a][1];
  return null;
}

/** 2 -> «2»; 1.5 -> «1,5»; 0.25 -> «0,25» (coma decimal, como se escribe en español). */
export function formatearCantidad(cantidad) {
  if (Number.isInteger(cantidad)) return String(cantidad);
  return cantidad.toFixed(3).replace(/0+$/, "").replace(/\.$/, "").replace(".", ",");
}

const SINGULAR = { unidades: "unidad", paquetes: "paquete", tazas: "taza", latas: "lata" };

/** «1 paquete», «2 paquetes», «1,5 L»: concuerda la unidad con la cantidad. */
export function textoCantidad(cantidad, unidad) {
  if (cantidad === 1) unidad = SINGULAR[unidad] ?? unidad;
  return `${formatearCantidad(cantidad)} ${unidad}`;
}

/** Minúsculas, sin acentos y con espacios simples: «Limón  » -> «limon». */
export function normalizar(texto) {
  return String(texto).normalize("NFD").replace(/\p{Mn}/gu, "").toLowerCase()
    .split(/\s+/).filter(Boolean).join(" ");
}

// --------------------------------------------------------------------------- //
// Ingrediente: { id, nombre, cantidad, unidad, vencimiento: «AAAA-MM-DD» }
// --------------------------------------------------------------------------- //
export function nuevoId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID().replaceAll("-", "");
  return Date.now().toString(16) + Math.random().toString(16).slice(2, 12);
}

/** Valida los cuatro campos (en el orden del formulario) y devuelve el ingrediente. */
export function crearIngrediente(nombre, cantidad, unidad, vencimiento, id = null) {
  return {
    id: id || nuevoId(),
    nombre: validarNombre(nombre),
    cantidad: validarCantidad(cantidad),
    unidad: validarUnidad(unidad),
    vencimiento: parsearFecha(vencimiento),
  };
}

/** Reconstruye un ingrediente guardado, revalidándolo todo (por si los datos se dañaron). */
export function ingredienteDesdeDatos(datos) {
  return crearIngrediente(datos.nombre, datos.cantidad, datos.unidad, datos.vencimiento, datos.id);
}

// --------------------------------------------------------------------------- //
// Estado respecto a la fecha de hoy
// --------------------------------------------------------------------------- //
/** Días que faltan para vencer. 0 = vence hoy; negativo = ya venció. */
export const diasParaVencer = (ingrediente, hoy) => diasEntre(hoy, ingrediente.vencimiento);
/** Vencido = su fecha es ANTERIOR a hoy. Lo que vence hoy aún se puede usar. */
export const estaVencido = (ingrediente, hoy) => diasParaVencer(ingrediente, hoy) < 0;
export const estaPorVencer = (ingrediente, hoy) => {
  const dias = diasParaVencer(ingrediente, hoy);
  return dias >= 0 && dias <= DIAS_POR_VENCER;
};

/** «vence hoy», «vence mañana», «vence en 5 días», «vencido hace 2 días». */
export function describirVencimiento(dias) {
  if (dias < 0) return dias === -1 ? "vencido hace 1 día" : `vencido hace ${-dias} días`;
  if (dias === 0) return "vence hoy";
  if (dias === 1) return "vence mañana";
  return `vence en ${dias} días`;
}
