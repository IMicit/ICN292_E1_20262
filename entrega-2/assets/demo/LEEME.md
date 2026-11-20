# Demostración del prototipo en imágenes

Proyecto IMELSE · ICN-292 · UTFSM 2026-2 · Paralelo 100 · Grupo 5

Todo lo que hay en esta carpeta es **el prototipo real corriendo**, grabado
manejando la aplicación igual que lo haría un técnico. No hay animaciones ni
recreaciones: lo que se ve en pantalla es lo que la aplicación respondió. Si en
la defensa preguntan «¿esto es el sistema o una maqueta?», la respuesta es que
es el sistema, y se puede levantar en el momento.

Los archivos son GIF, de modo que se reproducen solos en PowerPoint, en Google
Slides y en cualquier navegador, sin controles ni clics.

---

## Qué muestra cada archivo

| Archivo | Qué se ve | Dónde usarlo |
|---|---|---|
| `0-antes-ficha-en-papel.jpg` | La lista de chequeo N° 002190 de IMELSE, en papel | El «antes». Es la hoja que el orador sostiene |
| `1-no-sella-sin-evidencia.gif` | El técnico responde los 15 ítems de la pauta y el botón de sellar **sigue deshabilitado**, con el aviso «Falta registrar al menos una fotografía (RF-04)» | **El más importante.** Va junto a la hoja de papel |
| `2-registrar-la-fotografia.gif` | Se adjunta la fotografía, se vincula a los ítems y queda registrada con su autor, su tamaño y su hash SHA-256 | Si hay tiempo, después del anterior |
| `3-estampado-dentro-de-la-imagen.jpg` | La evidencia a tamaño completo, con el tablero, la fecha y la hora **grabados sobre el píxel** | Para la pregunta «¿y cómo saben cuándo se tomó?» |
| `4-sellar-y-queda-inmutable.gif` | El botón se habilita, se sella, y el registro pasa a sólo lectura | Refuerza la inmutabilidad |
| `5-panel-de-cumplimiento.gif` | El panel de gerencia con cobertura, visitas completas, latencia y pendientes críticos | La mitad de oficina de la historia |
| `6-materiales-por-comprar.gif` | La lista de faltantes agrupada por local, con los que bloquean un tablero | Para el RF-11 y la manifestación P6 |
| `7-consultas-sql-en-vivo.gif` | La pantalla de consultas ejecutando `06-materiales-por-comprar.sql` **contra la base real** | El argumento más fuerte del bloque SQL |

---

## Cómo se grabaron

La aplicación se levantó sobre PostgreSQL 16 con los datos de demostración del
repositorio, y un guion de Playwright la manejó paso a paso en un navegador con
viewport de teléfono (390 × 844) y de escritorio (1280 × 800). Cada fotograma es
una captura real de la página.

El tablero que aparece es **TD-0405 de Sucursal Centro**, en el ciclo 6 de 2026,
que es una visita en ejecución de los datos de demostración.

La fotografía que se sube es una imagen sintética, generada para la grabación.
No es una fotografía de una instalación real, en coherencia con lo declarado en
el README sobre datos ficticios.

---

## Un aviso antes de proyectar

`0-antes-ficha-en-papel.jpg` es el escaneo de la ficha real de IMELSE y lleva en
el membrete el **RUT, la dirección, el teléfono y el correo de la empresa**. Está
en el repositorio del proyecto desde la Entrega 1 como evidencia del
levantamiento. Si prefieren no proyectar esos datos, hay que difuminar el
membrete antes de la defensa.

---

## Cómo usarlos en la presentación

Dos ya están puestos en el PPT: la ficha de papel y
`1-no-sella-sin-evidencia.gif` comparten la diapositiva 4, y
`5-panel-de-cumplimiento.gif` está en la 7.

Para agregar otro en PowerPoint: Insertar → Imágenes → elegir el `.gif`. Se
anima solo al pasar a modo presentación, no en la vista de edición. Conviene
probarlo una vez en el computador con que van a presentar, porque algunas
versiones antiguas de PowerPoint muestran sólo el primer fotograma.
