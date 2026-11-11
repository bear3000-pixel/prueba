/**
 * Pruebas de extremo a extremo de la versión web / Android, con Playwright.
 *
 * Abren la app en un navegador real (Chromium) emulando un Pixel 7 y la usan como una persona:
 * escriben en los campos, tocan botones, recargan la página, cortan la conexión... La fecha de «hoy» se
 * fija en el 11/11/2026 para que los resultados sean siempre los mismos.
 *
 * No son parte de `npm test` porque necesitan Playwright (npm i -D playwright). Para ejecutarlas:
 *     node web/tests/e2e/movil.e2e.cjs            # imprime ✔/✘ y termina con error si algo falla
 *     CAPTURAS=/ruta/carpeta node web/tests/e2e/movil.e2e.cjs   # además guarda capturas de pantalla
 */
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const { chromium, devices } = require("playwright");

const RAIZ = path.resolve(__dirname, "..", "..");
const CAPTURAS = process.env.CAPTURAS || "";
const TIPOS = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
  ".json": "application/json", ".webmanifest": "application/manifest+json", ".png": "image/png",
};

function servidor() {
  return new Promise((resolver) => {
    const s = http.createServer((req, res) => {
      const ruta = path.join(RAIZ, decodeURIComponent(new URL(req.url, "http://x").pathname).replace(/\/$/, "/index.html"));
      if (!ruta.startsWith(RAIZ) || !fs.existsSync(ruta) || fs.statSync(ruta).isDirectory()) { res.writeHead(404).end(); return; }
      res.writeHead(200, { "Content-Type": TIPOS[path.extname(ruta)] || "application/octet-stream" });
      fs.createReadStream(ruta).pipe(res);
    }).listen(0, "127.0.0.1", () => resolver({ s, url: `http://127.0.0.1:${s.address().port}/` }));
  });
}

const HOY = new Date(2026, 10, 11, 12, 0, 0); // 11/11/2026
const fecha = (dias) => {
  const f = new Date(2026, 10, 11 + dias);
  return [f.getDate(), f.getMonth() + 1, f.getFullYear()].map((n, i) => String(n).padStart(i === 2 ? 4 : 2, "0")).join("/");
};

const resultados = [];
async function caso(nombre, funcion) {
  try { await funcion(); resultados.push([true, nombre]); console.log("  ✔", nombre); }
  catch (error) { resultados.push([false, nombre, error]); console.log("  ✘", nombre, "\n     ", String(error.message).split("\n").slice(0, 6).join("\n      ")); }
}

(async () => {
  const { s, url } = await servidor();
  const navegador = await chromium.launch();

  async function nuevaPagina(opciones = {}) {
    const contexto = await navegador.newContext({ ...devices["Pixel 7"], locale: "es-CO", timezoneId: "America/Bogota", ...opciones });
    const pagina = await contexto.newPage();
    pagina.errores = [];
    pagina.on("console", (m) => { if (["error", "warning"].includes(m.type())) pagina.errores.push(m.text()); });
    pagina.on("pageerror", (e) => pagina.errores.push("pageerror: " + e.message));
    await pagina.clock.install({ time: HOY });
    await pagina.goto(url);
    return pagina;
  }
  const foto = async (pagina, nombre, opciones = {}) => { if (CAPTURAS) await pagina.screenshot({ path: path.join(CAPTURAS, nombre + ".png"), ...opciones }); };

  const agregar = async (p, nombre, cantidad, unidad, vence) => {
    await p.fill("#nombre", nombre); await p.fill("#cantidad", cantidad); await p.selectOption("#unidad", unidad);
    await p.fill("#vence", ""); await p.locator("#vence").pressSequentially(vence);
    await p.click("#boton-guardar");
  };
  const textos = (p, selector) => p.locator(selector).allInnerTexts();
  const mensaje = (p) => p.locator("#mensaje").innerText();

  console.log("\nCelular Android (Pixel 7)");

  await caso("abre sin errores, vacío y con la guía de inicio", async () => {
    const p = await nuevaPagina();
    assert.equal(await p.title(), "Food Saver");
    assert.deepEqual(await textos(p, ".chip"), ["0 vigentes", "0 por vencer", "0 vencidos"]);
    assert.match(await p.locator("#vacio-vigentes").innerText(), /Todavía no hay ingredientes/);
    await foto(p, "01-vacio");
    assert.deepEqual(p.errores, []);
  });

  await caso("rechaza datos inválidos con mensaje y no agrega nada", async () => {
    const p = await nuevaPagina();
    const casos = [
      ["Leche", "0", "L", "13/11/2026", "La cantidad debe ser mayor que cero."],
      ["Leche", "-3", "L", "13/11/2026", "La cantidad debe ser mayor que cero."],
      ["Leche", "abc", "L", "13/11/2026", "La cantidad debe ser un número (por ejemplo 2 o 1,5)."],
      ["Leche", "", "L", "13/11/2026", "Escribe la cantidad."],
      ["Leche", "1e3", "L", "13/11/2026", "La cantidad debe ser un número (por ejemplo 2 o 1,5)."],
      ["Leche", "5000000", "L", "13/11/2026", "La cantidad es demasiado grande (máximo 1.000.000)."],
      ["", "1", "L", "13/11/2026", "Escribe el nombre del ingrediente."],
      ["123", "1", "L", "13/11/2026", "El nombre debe contener letras."],
      ["Leche", "1", "L", "", "Escribe la fecha de vencimiento (DD/MM/AAAA)."],
      ["Leche", "1", "L", "31022026", "Fecha no válida. Usa DD/MM/AAAA (por ejemplo 25/12/2026) y verifica que el día exista."],
      ["Leche", "1", "L", "25120226", "El año del vencimiento debe estar entre 2000 y 2100."],
      ["Leche", "1", "L", "021126", "Fecha no válida. Usa DD/MM/AAAA (por ejemplo 25/12/2026) y verifica que el día exista."],
    ];
    for (const [n, c, u, v, esperado] of casos) {
      await agregar(p, n, c, u, v);
      assert.equal(await mensaje(p), esperado, `caso ${n}/${c}/${v}`);
      assert.equal(await p.locator("#mensaje").getAttribute("class"), "mensaje error");
      assert.equal((await textos(p, "#lista-vigentes .ing, #lista-vencidos .ing")).length, 0, `no debe agregar (${c})`);
    }
    await foto(p, "02-error");
    assert.deepEqual(p.errores, []);
  });

  await caso("fecha con barras automáticas: 02112026 -> 02/11/2026", async () => {
    const p = await nuevaPagina();
    const vence = p.locator("#vence");
    const secuencia = [];
    for (const d of "02112026") { await vence.pressSequentially(d); secuencia.push(await vence.inputValue()); }
    assert.deepEqual(secuencia, ["0", "02/", "02/1", "02/11/", "02/11/2", "02/11/20", "02/11/202", "02/11/2026"]);
    await vence.fill(""); await vence.pressSequentially("2/11/2026");
    assert.equal(await vence.inputValue(), "02/11/2026");
    await vence.fill(""); await vence.pressSequentially("mañana");
    assert.equal(await vence.inputValue(), "");
    await vence.pressSequentially("0211202699");
    assert.equal(await vence.inputValue(), "02/11/2026");
    // Retroceso: las barras no reaparecen solas
    await vence.fill(""); await vence.pressSequentially("0211");
    const borrado = [await vence.inputValue()];
    for (let i = 0; i < 5; i++) { await vence.press("Backspace"); borrado.push(await vence.inputValue()); }
    assert.deepEqual(borrado, ["02/11/", "02/11", "02/1", "02/", "02", "0"]);
    assert.equal(await vence.getAttribute("inputmode"), "numeric"); // teclado numérico en el celular
  });

  await caso("avisa en vivo si la fecha no existe y el aviso se quita al corregirla", async () => {
    const p = await nuevaPagina();
    await p.locator("#vence").pressSequentially("31022026");
    assert.equal(await p.locator("#vence").inputValue(), "31/02/2026");
    assert.match(await mensaje(p), /^Fecha no válida/);
    await p.locator("#vence").fill(""); await p.locator("#vence").pressSequentially("28022026");
    assert.equal(await p.locator("#mensaje").isHidden(), true);
    await p.locator("#vence").fill("");
    await p.evaluate(() => {}); // (la caja se oculta sin mensaje)
  });

  await caso("agrega ingredientes: orden por vencimiento, por vencer y vencidos aparte", async () => {
    const p = await nuevaPagina();
    for (const [n, c, u, d] of [["Arroz", "1", "kg", 200], ["Pollo", "500", "g", -1], ["Leche", "1", "L", 2],
      ["Yogur", "2", "unidades", 0], ["Queso", "200", "g", 3], ["Pan", "1", "paquetes", 4]]) {
      await agregar(p, n, c, u, fecha(d).replaceAll("/", ""));
    }
    assert.deepEqual(await textos(p, ".chip"), ["5 vigentes", "3 por vencer", "1 vencido"]);
    const filas = await p.locator("#lista-vigentes .ing").evaluateAll((els) => els.map((e) => ({
      nombre: e.querySelector(".nombre").textContent, estado: e.querySelector(".estado").textContent,
      detalle: e.querySelector(".detalle").textContent, clase: e.className.replace(/\s+/g, " ").trim(),
    })));
    assert.deepEqual(filas.map((f) => [f.nombre, f.estado]), [
      ["Yogur", "⚠ Vence hoy"], ["Leche", "⚠ Vence en 2 días"], ["Queso", "⚠ Vence en 3 días"],
      ["Pan", "Vence en 4 días"], ["Arroz", "Vence en 200 días"]]);
    assert.deepEqual(filas.map((f) => f.clase.includes("por-vencer")), [true, true, true, false, false]);
    assert.equal(filas[3].detalle, "1 paquete · vence 15/11/2026"); // singular y fecha DD/MM/AAAA
    assert.deepEqual(await textos(p, "#lista-vencidos .nombre"), ["Pollo"]);
    assert.equal(await p.locator("#lista-vencidos .estado").innerText(), "Vencido hace 1 día");
    assert.equal(await p.locator("#titulo-vigentes").innerText(), "Ingredientes vigentes (5) — el que vence primero, arriba");
    await foto(p, "03-despensa", { fullPage: true });
    assert.deepEqual(p.errores, []);
  });

  await caso("editar actualiza sin duplicar; eliminar y borrar todo piden confirmación", async () => {
    const p = await nuevaPagina();
    await agregar(p, "Leche", "1", "L", fecha(2).replaceAll("/", ""));
    await agregar(p, "Huevos", "6", "unidades", fecha(5).replaceAll("/", ""));
    await p.click('#lista-vigentes [data-accion="editar"] >> nth=0');
    assert.equal(await p.locator("#nombre").inputValue(), "Leche");
    assert.equal(await p.locator("#vence").inputValue(), fecha(2));
    assert.equal(await p.locator("#titulo-formulario").innerText(), "Editando «Leche»");
    assert.equal(await p.locator("#boton-guardar").innerText(), "Guardar cambios");
    await p.fill("#cantidad", "0"); await p.click("#boton-guardar");
    assert.equal(await mensaje(p), "La cantidad debe ser mayor que cero.");
    await p.fill("#cantidad", "3"); await p.locator("#vence").fill(""); await p.locator("#vence").pressSequentially(fecha(-1).replaceAll("/", ""));
    await p.click("#boton-guardar");
    assert.equal(await mensaje(p), "«Leche» actualizado.");
    assert.deepEqual(await textos(p, "#lista-vencidos .nombre"), ["Leche"]); // pasó a Vencidos, no se duplicó
    assert.equal(await p.locator("#boton-guardar").innerText(), "Agregar");
    // Eliminar: primero «No», luego «Sí»
    await p.click('#lista-vigentes [data-accion="eliminar"] >> nth=0');
    assert.equal(await p.locator("#confirmar-texto").innerText(), "¿Eliminar «Huevos»?");
    await p.click("#confirmar-no");
    assert.deepEqual(await textos(p, "#lista-vigentes .nombre"), ["Huevos"]);
    await p.click('#lista-vigentes [data-accion="eliminar"] >> nth=0');
    await p.click("#confirmar-si");
    assert.equal(await mensaje(p), "«Huevos» eliminado.");
    await p.click("#boton-borrar-todo");
    assert.equal(await p.locator("#confirmar-texto").innerText(), "¿Borrar el ingrediente guardado?");
    await p.click("#confirmar-si");
    assert.equal(await mensaje(p), "Se borraron todos los ingredientes.");
    assert.deepEqual(await textos(p, ".chip"), ["0 vigentes", "0 por vencer", "0 vencidos"]);
  });

  await caso("cargar ejemplo: resumen, primeras recetas y receta abierta", async () => {
    const p = await nuevaPagina();
    await p.click("#boton-ejemplo");
    assert.equal(await mensaje(p), "Se agregaron 12 ingredientes de ejemplo.");
    assert.deepEqual(await textos(p, ".chip"), ["10 vigentes", "4 por vencer", "2 vencidos"]);
    assert.deepEqual(await textos(p, "#lista-vigentes .nombre"),
      ["Espinaca", "Leche", "Pan de molde", "Tomates", "Huevos", "Zanahorias", "Queso", "Cebolla", "Papas", "Arroz"]);
    assert.deepEqual(await textos(p, "#lista-vencidos .nombre"), ["Yogur", "Pollo"]);
    await p.click("#pestana-recetas");
    const primeras = await p.locator("#lista-recetas > li").evaluateAll((els) => els.slice(0, 3).map((e) => [
      e.querySelector(".receta-titulo").textContent, e.querySelector(".receta-meta").textContent]));
    assert.deepEqual(primeras, [
      ["Tostadas francesas", "Tienes 3 de 3 · Aprovecha: Pan de molde (en 2 días)"],
      ["Huevos revueltos con espinaca", "Tienes 3 de 3 · Aprovecha: Espinaca (mañana)"],
      ["Omelette de queso y tomate", "Tienes 3 de 3 · Aprovecha: Tomates (en 3 días)"]]);
    // La primera receta viene abierta, con su detalle
    const detalle = await p.locator(".receta-detalle").first().innerText();
    assert.match(detalle, /Tienes todos los ingredientes: puedes cocinarla ya/);
    assert.match(detalle, /Pan de molde \(1 paquete\) — vence en 2 días/);
    assert.match(detalle, /Preparación\s+Bate el huevo/); // (los números de la lista los dibuja el navegador)
    await foto(p, "04-recetas");
    // El filtro «solo las que puedo cocinar ya»
    await p.check("#solo-completas");
    assert.deepEqual(await textos(p, "#lista-recetas .receta-titulo"),
      ["Tostadas francesas", "Huevos revueltos con espinaca", "Omelette de queso y tomate", "Arroz frito con huevo"]);
    assert.deepEqual(p.errores, []);
  });

  await caso("los vencidos no se usan en las recetas y se avisa", async () => {
    const p = await nuevaPagina();
    for (const [n, c, u, d] of [["Pollo", "500", "g", -1], ["Arroz", "1", "kg", 30], ["Zanahorias", "4", "unidades", 3], ["Cebolla", "3", "unidades", 10]]) {
      await agregar(p, n, c, u, fecha(d).replaceAll("/", ""));
    }
    await p.click("#pestana-recetas");
    const primera = await p.locator("#lista-recetas > li").first().innerText();
    assert.match(primera, /Arroz con pollo y verduras/);
    assert.match(primera, /Tienes 3 de 4 · Aprovecha: Zanahorias \(en 3 días\)/);
    const detalle = await p.locator(".receta-detalle").first().innerText();
    assert.match(detalle, /Pollo \(lo tienes, pero está vencido\)/);
    await p.check("#solo-completas");
    assert.match(await p.locator("#vacio-recetas").innerText(), /Ninguna receta se puede cocinar completa/);
  });

  await caso("recetas propias: validaciones del cuadro (cantidades negativas, nulas, etc.)", async () => {
    const p = await nuevaPagina();
    await p.click("#pestana-recetas"); await p.click("#boton-crear-receta");
    assert.equal(await p.locator("#titulo-dialogo-receta").innerText(), "Crear mi receta");
    const aviso = () => p.locator("#receta-mensaje").innerText();
    const agregarIng = async (n, c, u = "g") => {
      await p.fill("#receta-ingrediente", n); await p.fill("#receta-cantidad", c);
      await p.selectOption("#receta-unidad", u); await p.click("#receta-agregar");
    };
    for (const [c, esperado] of [["", "Falta la cantidad de «Harina»."], ["0", "La cantidad debe ser mayor que cero."],
      ["-5", "La cantidad debe ser mayor que cero."], ["abc", "La cantidad debe ser un número (por ejemplo 2 o 1,5)."],
      ["1e3", "La cantidad debe ser un número (por ejemplo 2 o 1,5)."], ["5000000", "La cantidad es demasiado grande (máximo 1.000.000)."],
      ["0,0001", "La cantidad debe ser mayor que cero."]]) {
      await agregarIng("Harina", c);
      assert.equal(await aviso(), esperado, `cantidad ${JSON.stringify(c)}`);
      assert.equal(await p.locator("#receta-lista .ing").count(), 0);
    }
    await agregarIng("", "5"); assert.equal(await aviso(), "Escribe el nombre del ingrediente.");
    await agregarIng("123", "5"); assert.equal(await aviso(), "El nombre debe contener letras.");
    await agregarIng("Harina", "500"); assert.equal(await aviso(), "«Harina» agregado a la receta.");
    await agregarIng("HARINAS", "2"); assert.equal(await aviso(), "«HARINAS» ya está en la lista de ingredientes.");
    await agregarIng("Azúcar", "1,5", "tazas");
    assert.deepEqual(await textos(p, "#receta-lista .detalle"), ["500 g", "1,5 tazas"]);
    // Guardar: cada falta tiene su aviso
    await p.click("#receta-guardar"); assert.equal(await aviso(), "Escribe el nombre de la receta.");
    await p.fill("#receta-nombre", "omelette de queso y tomate"); await p.fill("#receta-pasos", "Mezclar");
    await p.click("#receta-guardar"); assert.equal(await aviso(), "Ya existe una receta llamada «omelette de queso y tomate». Elige otro nombre.");
    await p.fill("#receta-nombre", "Mi receta"); await p.fill("#receta-pasos", "");
    await p.click("#receta-guardar"); assert.equal(await aviso(), "Escribe al menos un paso de preparación.");
    await p.fill("#receta-pasos", "123\n456");
    await p.click("#receta-guardar"); assert.equal(await aviso(), "El paso 1 debe contener texto.");
    await p.fill("#receta-pasos", "Mezclar"); await p.fill("#receta-ingrediente", "Sal"); await p.fill("#receta-cantidad", "2");
    await p.click("#receta-guardar");
    assert.equal(await aviso(), "Tienes un ingrediente escrito que no has agregado. Pulsa «Agregar ingrediente» o borra lo escrito.");
    assert.equal(await p.evaluate(() => document.getElementById("dialogo-receta").open), true, "sigue abierto");
    await foto(p, "05-crear-receta-error");
    assert.deepEqual(p.errores, []);
  });

  await caso("recetas propias: crear, ver con ★ y cantidades, editar, eliminar y conservar", async () => {
    const p = await nuevaPagina();
    await agregar(p, "Harina", "1", "kg", fecha(2).replaceAll("/", ""));
    await agregar(p, "Agua", "1", "L", fecha(30).replaceAll("/", ""));
    await p.click("#pestana-recetas"); await p.click("#boton-crear-receta");
    await p.fill("#receta-nombre", "Pan casero");
    for (const [n, c, u] of [["Harina", "500", "g"], ["Agua", "300", "ml"]]) {
      await p.fill("#receta-ingrediente", n); await p.fill("#receta-cantidad", c);
      await p.selectOption("#receta-unidad", u); await p.click("#receta-agregar");
    }
    await p.fill("#receta-pasos", "1. Mezclar todo\n2) Amasar\n- Hornear 30 minutos");
    await foto(p, "06-crear-receta");
    await p.click("#receta-guardar");
    assert.equal(await p.evaluate(() => document.getElementById("dialogo-receta").open), false);
    assert.equal(await p.locator("#mensaje-recetas").innerText(), "Receta «Pan casero» guardada. Ya aparece en las recetas sugeridas.");
    const primera = p.locator("#lista-recetas > li").first();
    assert.equal(await primera.locator(".receta-titulo").innerText(), "★ Pan casero");
    assert.match(await primera.locator(".receta-meta").innerText(), /Tienes 2 de 2 · Aprovecha: Harina \(en 2 días\)/);
    const detalle = await primera.locator(".receta-detalle").innerText();
    assert.match(detalle, /Receta creada por ti/);
    assert.match(detalle, /Harina \(1 kg\) — vence en 2 días — la receta pide 500 g/);
    assert.match(detalle, /Agua \(1 L\) — vence en 30 días — la receta pide 300 ml/);
    assert.deepEqual(await primera.locator("ol li").allInnerTexts(), ["Mezclar todo", "Amasar", "Hornear 30 minutos"]);
    await foto(p, "07-receta-propia", { fullPage: true });

    // Se conserva al recargar la página
    await p.reload();
    await p.click("#pestana-recetas");
    assert.equal(await p.locator("#lista-recetas .receta-titulo").first().innerText(), "★ Pan casero");

    // Mis recetas: lista, editar (con cantidad nueva) y eliminar
    await p.click("#boton-mis-recetas");
    assert.deepEqual(await textos(p, "#mis-recetas-lista .nombre"), ["Pan casero"]);
    assert.equal(await p.locator("#mis-recetas-lista .detalle").innerText(), "2 ingredientes · 3 pasos");
    await p.click('#mis-recetas-lista [data-accion="mis-editar"]');
    assert.equal(await p.locator("#receta-nombre").inputValue(), "Pan casero");
    assert.equal(await p.locator("#receta-pasos").inputValue(), "Mezclar todo\nAmasar\nHornear 30 minutos");
    await p.click('#receta-lista [data-accion="receta-editar-fila"] >> nth=0');
    assert.equal(await p.locator("#receta-cantidad").inputValue(), "500");
    await p.fill("#receta-cantidad", "2000"); await p.click("#receta-agregar"); // pide 2000 g: tienes 1 kg
    await p.click("#receta-guardar");
    assert.equal(await p.locator("#mensaje-recetas").innerText(), "Receta «Pan casero» actualizada. Ya aparece en las recetas sugeridas.");
    assert.equal((await p.locator("#lista-recetas .receta-titulo").allInnerTexts()).filter((t) => t.includes("Pan casero")).length, 1, "no se duplicó");
    const detalle2 = await p.locator(".receta-detalle").first().innerText();
    assert.match(detalle2, /Harina: pide 2000 g, tienes 1000 g \(te faltan 1000 g\)/);
    assert.match(detalle2, /Te faltan 1 ingrediente\(s\)\./);
    await p.click("#cerrar-mis-recetas"); // «Mis recetas» es un cuadro modal: se cierra para volver a la lista
    await p.check("#solo-completas"); // ya no se puede cocinar completa
    assert.ok(!(await textos(p, "#lista-recetas .receta-titulo")).includes("★ Pan casero"));
    await p.uncheck("#solo-completas");
    await p.click("#boton-mis-recetas");
    await p.click('#mis-recetas-lista [data-accion="mis-eliminar"]');
    assert.equal(await p.locator("#confirmar-texto").innerText(), "¿Eliminar tu receta «Pan casero»?");
    await p.click("#confirmar-si");
    assert.equal(await p.locator("#mensaje-recetas").innerText(), "Receta «Pan casero» eliminada.");
    assert.match(await p.locator("#mis-recetas-vacio").innerText(), /Todavía no has creado ninguna receta/);
    assert.deepEqual(p.errores, []);
  });

  await caso("cerrar la receta con cambios sin guardar pide confirmación", async () => {
    const p = await nuevaPagina();
    await p.click("#pestana-recetas"); await p.click("#boton-crear-receta");
    await p.click("#receta-cancelar"); // sin escribir nada: se cierra sin preguntar
    assert.equal(await p.evaluate(() => document.getElementById("dialogo-receta").open), false);
    await p.click("#boton-crear-receta");
    await p.fill("#receta-nombre", "A medias");
    await p.keyboard.press("Escape"); // Esc o el botón «atrás» de Android
    assert.match(await p.locator("#confirmar-texto").innerText(), /Tienes cambios sin guardar en esta receta/);
    await p.click("#confirmar-no");
    assert.equal(await p.evaluate(() => document.getElementById("dialogo-receta").open), true);
    await p.click("#cerrar-receta"); await p.click("#confirmar-si");
    assert.equal(await p.evaluate(() => document.getElementById("dialogo-receta").open), false);
    assert.equal(await p.locator("#lista-recetas > li").count(), 0);
  });

  await caso("los datos se conservan al recargar y un dato dañado no impide abrir la app", async () => {
    const p = await nuevaPagina();
    await agregar(p, "Leche", "1", "L", fecha(2).replaceAll("/", ""));
    await p.reload();
    assert.deepEqual(await textos(p, "#lista-vigentes .nombre"), ["Leche"]);
    await p.evaluate(() => localStorage.setItem("foodsaver.ingredientes", "{esto no es json"));
    await p.reload();
    assert.match(await p.locator("#aviso-general").innerText(), /datos guardados estaban dañados/);
    assert.deepEqual(await textos(p, ".chip"), ["0 vigentes", "0 por vencer", "0 vencidos"]);
    assert.equal(await p.evaluate(() => localStorage.getItem("foodsaver.ingredientes.corrupto")), "{esto no es json");
  });

  await caso("funciona SIN INTERNET (service worker) y se puede instalar (manifiesto)", async () => {
    const p = await nuevaPagina();
    await p.evaluate(() => navigator.serviceWorker.ready);
    await p.reload(); // ya con el service worker controlando la página
    await p.waitForFunction(() => navigator.serviceWorker.controller !== null);
    await p.context().setOffline(true);
    await p.reload();
    assert.equal(await p.locator("h1").innerText(), "Food Saver");
    await agregar(p, "Leche", "1", "L", fecha(2).replaceAll("/", ""));
    assert.deepEqual(await textos(p, "#lista-vigentes .nombre"), ["Leche"]); // todo funciona offline
    await p.context().setOffline(false);
    const manifiesto = await p.evaluate(async () => (await fetch(document.querySelector('link[rel="manifest"]').href)).json());
    assert.equal(manifiesto.display, "standalone");
    assert.ok(manifiesto.icons.some((i) => i.sizes === "512x512" && i.purpose === "maskable"));
    for (const icono of manifiesto.icons) {
      const estado = await p.evaluate(async (src) => (await fetch(src)).status, new URL(icono.src, url).href);
      assert.equal(estado, 200, icono.src);
    }
  });

  await caso("accesibilidad básica: etiquetas, nombres de botones, objetivos táctiles de 44 px", async () => {
    const p = await nuevaPagina();
    await p.click("#boton-ejemplo");
    const sinEtiqueta = await p.evaluate(() => [...document.querySelectorAll("input:not([type=checkbox]), select, textarea")]
      .filter((c) => !document.querySelector(`label[for="${c.id}"]`) && !c.getAttribute("aria-label")).map((c) => c.id));
    assert.deepEqual(sinEtiqueta, []);
    const botonesSinNombre = await p.evaluate(() => [...document.querySelectorAll("button")]
      .filter((b) => !(b.textContent.trim() || b.getAttribute("aria-label"))).length);
    assert.equal(botonesSinNombre, 0);
    assert.equal(await p.locator("html").getAttribute("lang"), "es");
    const chicos = await p.evaluate(() => [...document.querySelectorAll("button, input[type=text], select")]
      .filter((e) => e.offsetParent !== null && e.getBoundingClientRect().height < 40)
      .map((e) => `${e.tagName}#${e.id || e.textContent.trim().slice(0, 20)} ${Math.round(e.getBoundingClientRect().height)}px`));
    assert.deepEqual(chicos, [], "objetivos táctiles menores de 40 px");
    const desborda = await p.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
    assert.equal(desborda, false, "no debe haber desplazamiento horizontal en el celular");
  });

  await caso("modo oscuro", async () => {
    const p = await nuevaPagina({ colorScheme: "dark" });
    await p.click("#boton-ejemplo");
    const fondo = await p.evaluate(() => getComputedStyle(document.body).backgroundColor);
    assert.equal(fondo, "rgb(15, 23, 19)");
    await foto(p, "08-oscuro", { fullPage: false });
    await p.click("#pestana-recetas");
    await foto(p, "09-oscuro-recetas", { fullPage: false });
  });

  console.log("\nComputador (pantalla ancha)");
  await caso("dos columnas a la vez, sin pestañas", async () => {
    const p = await nuevaPagina({ ...devices["Desktop Chrome"], viewport: { width: 1280, height: 900 }, hasTouch: false, isMobile: false });
    await p.click("#boton-ejemplo");
    assert.equal(await p.locator(".pestanas").isVisible(), false);
    assert.equal(await p.locator("#vista-despensa").isVisible(), true);
    assert.equal(await p.locator("#vista-recetas").isVisible(), true);
    const [a, b] = await Promise.all([p.locator("#vista-despensa").boundingBox(), p.locator("#vista-recetas").boundingBox()]);
    assert.ok(b.x > a.x + a.width - 2, "recetas queda a la derecha de la despensa");
    await foto(p, "10-escritorio", { fullPage: true });
    assert.deepEqual(p.errores, []);
  });

  await navegador.close();
  s.close();
  const fallos = resultados.filter(([ok]) => !ok);
  console.log(`\n${resultados.length - fallos.length}/${resultados.length} casos pasaron.`);
  process.exit(fallos.length ? 1 : 0);
})();
