/* Operación sin conexión (RNF-01).
 *
 * Las salas de tableros suelen estar en subterráneos o bodegas sin cobertura.
 * Esta capa hace que el técnico no se entere: si no hay red, la acción se
 * guarda en el dispositivo (IndexedDB, que sí admite la fotografía completa) y
 * se reenvía sola al recuperar señal.
 *
 * Métricas declaradas: hasta 8 h de captura local, sincronización en ≤ 60 s.
 */
(function () {
  "use strict";

  var BD = "sig-imelse-cola";
  var ALMACEN = "pendientes";
  var bd = null;

  function abrir() {
    return new Promise(function (resolver, rechazar) {
      if (bd) return resolver(bd);
      var peticion = indexedDB.open(BD, 1);
      peticion.onupgradeneeded = function (e) {
        var base = e.target.result;
        if (!base.objectStoreNames.contains(ALMACEN)) {
          base.createObjectStore(ALMACEN, { keyPath: "id", autoIncrement: true });
        }
      };
      peticion.onsuccess = function (e) { bd = e.target.result; resolver(bd); };
      peticion.onerror = function () { rechazar(peticion.error); };
    });
  }

  function transaccion(modo) {
    return abrir().then(function (base) {
      return base.transaction(ALMACEN, modo).objectStore(ALMACEN);
    });
  }

  function encolar(registro) {
    return transaccion("readwrite").then(function (almacen) {
      return new Promise(function (resolver, rechazar) {
        var p = almacen.add(registro);
        p.onsuccess = function () { resolver(p.result); };
        p.onerror = function () { rechazar(p.error); };
      });
    });
  }

  function listar() {
    return transaccion("readonly").then(function (almacen) {
      return new Promise(function (resolver, rechazar) {
        var p = almacen.getAll();
        p.onsuccess = function () { resolver(p.result || []); };
        p.onerror = function () { rechazar(p.error); };
      });
    });
  }

  function borrar(id) {
    return transaccion("readwrite").then(function (almacen) {
      return new Promise(function (resolver) {
        var p = almacen.delete(id);
        p.onsuccess = resolver; p.onerror = resolver;
      });
    });
  }

  /* ---------------------------------------------------------------- Aviso */

  var aviso = null;
  function pintarAviso(texto, clase) {
    if (!aviso) {
      aviso = document.createElement("div");
      aviso.className = "aviso-red";
      document.body.appendChild(aviso);
    }
    aviso.textContent = texto;
    aviso.dataset.estado = clase;
    aviso.hidden = !texto;
  }

  function refrescarAviso() {
    listar().then(function (cola) {
      if (!navigator.onLine) {
        pintarAviso(
          cola.length
            ? "Sin conexión · " + cola.length + " acción(es) guardadas en el equipo"
            : "Sin conexión · la captura sigue funcionando",
          "offline"
        );
      } else if (cola.length) {
        pintarAviso("Sincronizando " + cola.length + " acción(es)…", "sincronizando");
      } else {
        pintarAviso("", "ok");
      }
    });
  }

  /* ----------------------------------------------------------- Sincronizar */

  var sincronizando = false;

  function sincronizar() {
    if (sincronizando || !navigator.onLine) return Promise.resolve();
    sincronizando = true;
    var inicio = Date.now();

    var habiaCola = false;

    return listar().then(function (cola) {
      if (!cola.length) return;
      habiaCola = true;

      // En serie y en orden: las acciones de un mismo tablero dependen unas de
      // otras (primero las respuestas, después la foto, al final el sellado).
      return cola.reduce(function (cadena, item) {
        return cadena.then(function () {
          var datos = new FormData();
          item.campos.forEach(function (par) { datos.append(par[0], par[1]); });
          if (item.archivo) {
            datos.append(item.campoArchivo, item.archivo, item.nombreArchivo);
            // El servidor exige que la foto sea reciente respecto de su captura,
            // no respecto del momento en que logra subirse. Sin este desfase,
            // una visita sincronizada al salir del subterráneo se rechazaría
            // entera por "fotografía antigua".
            datos.append("desfase_cola", String(Date.now() - item.encoladaEn));
          }
          return fetch(item.url, {
            method: "POST", body: datos, credentials: "same-origin",
            headers: { "X-Sincronizacion-Diferida": "1" }
          }).then(function (respuesta) {
            if (respuesta.ok || respuesta.redirected) return borrar(item.id);
            if (respuesta.status >= 400 && respuesta.status < 500) {
              // El servidor rechazó el contenido: reintentar no lo arregla.
              return borrar(item.id).then(function () {
                pintarAviso("Una acción fue rechazada por el servidor. Revísela.", "error");
              });
            }
          }).catch(function () { /* sigue sin red: queda en la cola */ });
        });
      }, Promise.resolve());
    }).then(function () {
      sincronizando = false;
      if (!habiaCola) { refrescarAviso(); return; }

      return listar().then(function (resto) {
        if (resto.length) { refrescarAviso(); return; }
        // Sólo se recarga cuando de verdad se envió algo: la pantalla tiene que
        // pasar a mostrar lo que el servidor ya recibió.
        var seg = ((Date.now() - inicio) / 1000).toFixed(1);
        pintarAviso("Sincronizado en " + seg + " s", "ok");
        setTimeout(function () { location.reload(); }, 1200);
      });
    });
  }

  /* -------------------------------------------------- Intercepción de envíos */

  function interceptar(formulario) {
    formulario.addEventListener("submit", function (evento) {
      if (navigator.onLine) return;          // con red, el envío es el normal
      evento.preventDefault();

      var datos = new FormData(formulario);
      var campos = [], archivo = null, campoArchivo = null, nombreArchivo = null;

      datos.forEach(function (valor, clave) {
        if (valor instanceof File) {
          if (valor.size) { archivo = valor; campoArchivo = clave; nombreArchivo = valor.name; }
        } else {
          campos.push([clave, valor]);
        }
      });

      encolar({
        url: formulario.action || location.pathname,
        campos: campos,
        archivo: archivo,
        campoArchivo: campoArchivo,
        nombreArchivo: nombreArchivo,
        encoladaEn: Date.now()
      }).then(function () {
        formulario.reset();
        refrescarAviso();
        pintarAviso("Guardado en el equipo. Se enviará solo al recuperar señal.", "guardado");
        setTimeout(refrescarAviso, 2500);
      }).catch(function () {
        pintarAviso("No se pudo guardar localmente. Anote el dato en papel.", "error");
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("form[method=post]").forEach(interceptar);
    refrescarAviso();
    if (navigator.onLine) sincronizar();
  });

  window.addEventListener("online", sincronizar);
  window.addEventListener("offline", refrescarAviso);

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(function () {});
  }
})();
