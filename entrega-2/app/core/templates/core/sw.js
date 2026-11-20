/* Service worker del SIG IMELSE (RNF-01).
 *
 * Guarda el armazón de la aplicación para que las pantallas de terreno se
 * abran sin red. No cachea evidencia: la fotografía recién capturada vive en
 * la cola de IndexedDB hasta que se sincroniza.
 */
var CACHE = "sig-imelse-v1";
var BASE = ["/visitas/", "/static/core/offline.js"];

self.addEventListener("install", function (evento) {
  evento.waitUntil(
    caches.open(CACHE).then(function (c) {
      return c.addAll(BASE).catch(function () {});
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (evento) {
  evento.waitUntil(
    caches.keys().then(function (claves) {
      return Promise.all(claves.map(function (k) {
        if (k !== CACHE) return caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (evento) {
  var peticion = evento.request;

  // Los envíos no se cachean nunca: la cola de IndexedDB se encarga de ellos.
  if (peticion.method !== "GET") return;
  if (peticion.url.indexOf("/admin/") !== -1) return;

  // Red primero, caché como respaldo: en terreno conviene el dato fresco
  // cuando hay señal, y el armazón guardado cuando no la hay.
  evento.respondWith(
    fetch(peticion).then(function (respuesta) {
      if (respuesta && respuesta.status === 200 && respuesta.type === "basic") {
        var copia = respuesta.clone();
        caches.open(CACHE).then(function (c) { c.put(peticion, copia); });
      }
      return respuesta;
    }).catch(function () {
      return caches.match(peticion).then(function (guardada) {
        return guardada || caches.match("/visitas/");
      });
    })
  );
});
