# Prototipo SIG IMELSE — Entrega 2

Sistema de información para la trazabilidad de la mantención preventiva de
tableros eléctricos. Reemplaza el checklist en papel por un registro digital,
guiado y evidenciado, que se genera durante la ejecución de la visita.

ICN-292 Sistemas de Información para la Gestión · UTFSM · 2026-2

---

## 1. Stack y versiones exactas

| Componente | Versión | Nota |
|---|---|---|
| Python | 3.12 o superior | probado en 3.13 |
| Django | 5.2.6 | framework web y ORM |
| Pillow | 11.3.0 | compresión y estampado de fotografías (RNF-08) |
| reportlab | 5.0.1 | informe de visita en PDF (RF-13) |
| openpyxl | 3.1.5 | planilla anual de control en Excel (RF-12) |
| **PostgreSQL** | **16** (verificado sobre 16.15) | **motor de base de datos de producción** |
| SQLite | 3.45 o superior | motor del prototipo en localhost (RNF-09) |

El prototipo arranca sobre SQLite para que cualquier integrante pueda
reproducirlo sin instalar un servidor de base de datos. El motor declarado
para la operación real es **PostgreSQL 16**, y el cambio entre ambos es una
variable de entorno, no una modificación de código:

```bash
export DATABASE_URL=postgresql://usuario:clave@localhost:5432/sig_imelse
```

## 2. Puesta en marcha

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py cargar_demo                        # datos ficticios de demostración
python manage.py runserver
```

Abrir <http://127.0.0.1:8000/>.

### Desde el teléfono del técnico

El computador hace de servidor y el teléfono entra por la red local. Ambos en
la misma Wi-Fi:

```bash
python manage.py runserver 0.0.0.0:8000     # el 0.0.0.0 lo abre a la red
ipconfig          # Windows: buscar «Dirección IPv4»
ipconfig getifaddr en0   # macOS
```

En el teléfono: `http://<esa IP>:8000/`. Windows pedirá permiso del Firewall la
primera vez; hay que autorizarlo en redes privadas. Desde Chrome puede agregarse
a la pantalla principal y queda como aplicación (hay `manifest.json`).

La captura sin conexión funciona sobre `http://` de red local. Lo que no se
activa ahí es el service worker que guarda el armazón de las pantallas, porque
los navegadores lo reservan para orígenes seguros: en `127.0.0.1` y en
producción bajo HTTPS sí se registra.

### Usuarios de prueba

Todos con la contraseña `imelse2026`.

| Usuario | Perfil | Qué puede hacer |
|---|---|---|
| `tecnico` | Técnico | Registrar la visita, responder la pauta, capturar evidencia, declarar pendientes, cerrar |
| `tecnico2` | Técnico | Igual, otra cuadrilla |
| `dual` | Técnico | El estudiante dual: entra con la cuadrilla y anexa observaciones |
| `admin` | Administración | Revisar informes y evidencia, administrar el catálogo |
| `gerencia` | Gerencia | Consultar el panel de cumplimiento y el historial; no edita nada |
| `super` | Gerencia | Además, acceso a `/admin/` de Django |

## 3. La pauta no es inventada

Los 25 ítems del checklist son la transcripción literal de la ficha
**«LISTA DE CHEQUEO MANTENIMIENTO PREVENTIVO ELECTRICO N° 002190»** de IMELSE,
levantada en terreno (`assets/ev-05-ficha-checklist.pdf` de este repositorio).

Están en `core/management/commands/cargar_pauta.py`. La única adición del
rediseño es el campo `ambito`, que distingue los 10 ítems que se responden una
vez por visita de los **15 que deben responderse tablero por tablero**: ésa es
exactamente la trazabilidad que el formato en papel no permitía, y la causa de
que hoy un tablero pueda pasar ciclos sin revisión.

## 4. Cómo se cumple cada requisito

| Requisito | Dónde se cumple |
|---|---|
| RF-01 Registro maestro de locales y tableros | `Local`, `Tablero`; vista `/locales/` y admin |
| RF-02 Visita desde el calendario del ciclo | `Ciclo.generar_visitas()`; vista `/ciclos/`. Idempotente: la restricción única (local, ciclo) impide duplicar |
| RF-03 Checklist guiado por tablero | `RegistroTablero.items_sin_evidencia()`: un ítem marcado «Sí» sin fotografía vinculada impide sellar |
| RF-04 Al menos una foto por tablero | `RegistroTablero.sellar()` lo exige |
| RF-05 Fecha, hora y usuario automáticos | `Evidencia.ts` y `.usuario` no editables, y estampados **dentro del píxel** de la imagen |
| RF-17 Mediciones eléctricas | `MedicionElectrica`, con lectura de anomalías contra 400/230 V |
| RF-06 No cerrar con cobertura incompleta | `Visita.cerrar()` y `tableros_sin_resolver()` |
| RF-07 Declaración de pendiente con motivo | `Pendiente` con lista cerrada de motivos |
| RF-08 Evidencia disponible al cierre | El cierre publica; no hay transferencia manual |
| RF-09 Historial por tablero | `/tablero/<id>/historial/` |
| RF-10 Hallazgos por criticidad | `Hallazgo` |
| RF-11 Materiales faltantes en terreno | `MaterialFaltante`; el técnico declara en `/visitas/<id>/materiales/` y oficina compra desde `/materiales/` |
| RF-12 Panel de cobertura | `/panel/` |
| RF-13 Informe exportable con evidencia | `core/informes.py`: PDF generado en servidor y archivado como `InformeVisita` inmutable |
| RF-12 Planilla anual de control | `core/libro_anual.py`: Excel con una hoja por mes, regenerado al cerrar cada visita |
| RNF-01 Operación sin conexión | `core/static/core/offline.js` + `sw.js`: cola en IndexedDB y reenvío automático |
| RF-14 Perfiles diferenciados | `Usuario.rol` y el decorador `solo_roles` |
| **RNF-02 Inmutabilidad** | `AppendOnlyModel`: bloquea `save()` y `delete()` en el ORM |
| RNF-03 ≤5 interacciones por tablero | **No se cumple, y está declarado.** Se quitó «marcar todo conforme» para sostener el RF-03. Ver la limitación conocida en el `CHANGELOG.md` y la sección de limitaciones del informe |
| RNF-05 Acceso por perfil y atribución | `solo_roles`; todo registro lleva su `usuario` |
| RNF-08 Compresión de fotografías | `core/forms.py:comprimir()` |
| RNF-09 Reproducible en localhost | Esta sección 2 |

### Métricas de los RNF (con número y unidad)

Declaradas en `config/settings.py`, no sólo en el informe:

- **RNF-01 · Operación sin conexión:** hasta **8 horas** de captura local y
  sincronización en **≤ 60 segundos** al recuperar señal, sin pérdida de evidencia.
  Implementado: las acciones se encolan en IndexedDB y se reenvían en orden al
  volver la red. La validación de frescura de la fotografía descuenta el tiempo
  que la acción estuvo en cola, para que una visita sincronizada al salir del
  subterráneo no se rechace entera.
- **RNF-03 · Usabilidad:** **≤ 5 interacciones** por tablero conforme; controles
  táctiles de **≥ 48 px** de alto, operables con guantes. La métrica de
  interacciones **no se cumple** en la implementación entregada: exigir
  evidencia por ítem (RF-03) y permitir cerrar un tablero en cinco toques son
  requisitos incompatibles, y se optó por la verificabilidad. El tamaño de los
  controles sí se cumple.
- **RNF-04 · Volumen:** **30 visitas/mes × 20 tableros**, con al menos
  1 fotografía por tablero ≈ **600 imágenes/mes**.
- **RNF-08 · Compresión:** lado largo **1.600 px**, calidad JPEG **80**,
  máximo **500 KB** por fotografía.

## 4 bis. Planilla anual de control

`/planilla/` entrega un archivo `.xlsx` por año con quince hojas:

- **Resumen** — los doce meses en una tabla, con totales del año. El nombre de
  cada mes enlaza a su hoja.
- **01 Enero … 12 Diciembre** — una fila por visita: fecha, local, comuna,
  ciclo, estado, cuadrilla, cobertura y si el informe ya se emitió.
- **Pendientes** — los tableros no intervenidos del año con su motivo.
- **Tableros** — cuántas veces se intervino cada tablero y cuándo fue la
  última. Los que nunca se tocaron quedan marcados en rojo: es el dato que el
  papel no permitía obtener.

Las celdas de cobertura y los totales van como **fórmulas de Excel**, no como
números calculados en Python, para que la planilla se pueda trabajar.

La planilla **se regenera completa** cada vez que se cierra una visita, en
lugar de irse parchando. La razón está en el encabezado de `libro_anual.py`:
no es evidencia, es una vista derivada. Si se editara a mano, el archivo y el
sistema dirían cosas distintas y volveríamos al problema de las dos fuentes de
verdad. Por eso `LibroAnual` es el único modelo de salida que **no** es
append-only, a diferencia de `InformeVisita`.

## 5. Inmutabilidad (RNF-02)

Es la regla central del sistema y la razón por la que no reproduce el problema
del papel:

1. `RegistroItem`, `Evidencia`, `Observacion` y `Hallazgo` heredan de
   `AppendOnlyModel`, que lanza `PermissionDenied` en `save()` sobre una fila
   existente y en `delete()`.
2. La restricción vive en el **modelo**, no en la interfaz, de modo que ningún
   camino del código —vista, admin de Django o shell— pueda saltársela.
3. El admin de Django registra estos modelos en **sólo lectura**.
4. Una corrección **no sobrescribe**: crea una fila nueva con `corrige_a`
   apuntando a la original. Ambas quedan visibles, con su autor y su fecha.
5. Una vez sellado el registro, el único aporte posible es una `Observacion`
   anexada: el registro original queda intacto y el comentario queda a su lado.
6. Cada fotografía guarda su **hash SHA-256**, calculado al momento de subirla,
   lo que permite comprobar después que la imagen exhibida es la capturada.
7. El informe en PDF se archiva como `InformeVisita` con su propio hash.
   Regenerarlo crea una versión nueva; las anteriores no se borran. Lo único que
   admite añadirse después es a quién y cuándo se despachó, que no toca el
   documento ni su huella.

### Sobre la evidencia fotográfica

- La foto se captura con la cámara (`capture="environment"`), no desde la galería.
- El servidor **rechaza** imágenes cuyo archivo tenga más de 15 minutos
  (`EVIDENCIA_MAX_ANTIGUEDAD_S`), descontando el tiempo en cola offline.
- La fecha, la hora, el tablero y el autor quedan estampados **sobre el píxel**,
  no sólo en los metadatos EXIF, que se pierden al reenviar una imagen.
- Un ítem marcado «Sí» sin fotografía vinculada impide sellar el tablero. Una
  misma captura puede respaldar varios ítems, de modo que la regla no obligue a
  repetir quince fotos casi idénticas del mismo tablero abierto.

## 6. Datos personales (Ley 21.719)

El prototipo opera **exclusivamente con datos ficticios**: no hay nombres reales
de trabajadores de IMELSE, ni códigos o direcciones reales de locales del
cliente, ni fotografías tomadas en instalaciones reales. Las imágenes de
evidencia de la demostración se generan sintéticamente en
`core/management/commands/cargar_demo.py`.

El control de acceso por perfil está implementado desde el inicio, no añadido
después.

## 7. Estructura

```
config/     settings, urls, wsgi
core/
  models.py           modelo de datos y reglas de inmutabilidad
  views.py            vistas y control de acceso por perfil
  forms.py            formularios y compresión de fotografías
  admin.py            catálogo editable, registros en sólo lectura
  templates/core/     interfaz (móvil para terreno, escritorio para oficina)
  management/commands/
    cargar_pauta.py   los 25 ítems de la ficha N° 002190
    cargar_demo.py    escenario de demostración con datos ficticios
```
