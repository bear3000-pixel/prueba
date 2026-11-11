/* Service worker de Food Saver: hace que la app funcione SIN INTERNET.
 *
 * Estrategia «primero la red, si no hay red la copia guardada»: con conexión siempre se ve la versión
 * más nueva; sin conexión se usa lo último que se descargó. Para forzar que todos descarguen de nuevo
 * después de un cambio, basta con subir el número de VERSION. */
const VERSION = "foodsaver-v1";
const ARCHIVOS = [
  "./", "index.html", "manifest.webmanifest", "css/estilos.css",
  "js/app.js", "js/modelo.js", "js/logica.js", "js/recetas.js", "js/recetasUsuario.js",
  "js/almacenamiento.js", "js/ejemplos.js",
  "iconos/icono-192.png", "iconos/icono-512.png", "iconos/icono-maskable-512.png",
  "iconos/apple-touch-icon.png", "iconos/favicon.png",
];

self.addEventListener("install", (evento) => {
  evento.waitUntil(caches.open(VERSION).then((cache) => cache.addAll(ARCHIVOS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches.keys()
      .then((claves) => Promise.all(claves.filter((c) => c !== VERSION).map((c) => caches.delete(c))))
      .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (evento) => {
  const { request } = evento;
  if (request.method !== "GET" || new URL(request.url).origin !== self.location.origin) return;
  evento.respondWith(
    fetch(request)
      .then((respuesta) => {
        if (respuesta.ok) {
          const copia = respuesta.clone();
          caches.open(VERSION).then((cache) => cache.put(request, copia));
        }
        return respuesta;
      })
      .catch(() => caches.match(request).then((guardada) => guardada || caches.match("index.html"))));
});
