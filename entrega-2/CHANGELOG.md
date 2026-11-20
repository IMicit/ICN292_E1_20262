# Registro de cambios

Proyecto IMELSE · ICN-292 · UTFSM 2026-2

---

## [v1.0-e2] — Entrega 2

### Correcciones pedidas en la retroalimentación de la Entrega 1

La Entrega 1 obtuvo 92 puntos, con tres observaciones. Las tres están
resueltas:

- **Tipificación de eventos intermedios del BPMN.** Corregida en el diagrama
  *to-be*. Detalle en `docs/02-bpmn.md`.
- **Métricas de los requisitos no funcionales.** Reescritas con número y
  unidad, y además declaradas en `app/config/settings.py`, de modo que sean
  verificables en el código y no sólo en el informe. La latencia máxima en
  operación sin conexión quedó en 8 horas de captura local y 60 segundos de
  sincronización.
- **Versión exacta del motor de base de datos.** Precisada como **PostgreSQL
  16** en el README, en el informe y en `db/schema.sql`. El sistema se verificó
  corriendo sobre ese motor.

### Agregado

- **Esquema SQL ejecutable** (`db/schema.sql`): 20 entidades de negocio, 92
  restricciones, con las reglas del negocio declaradas como `CHECK` y `UNIQUE`
  y comentarios `COMMENT ON` en cada tabla.
- **Datos de demostración** (`db/seed.sql`): un año completo de operación, seis
  ciclos bimensuales, 24 visitas, 1.805 respuestas de la pauta y 382
  evidencias.
- **Seis consultas de negocio** (`db/consultas/`) con su interpretación
  escrita en `docs/04-sql-consultas.md`. La sexta responde qué materiales hay
  que comprar y detecta los que faltan una y otra vez en el mismo local, que
  no son un olvido sino un error de stock permanente.
- **Pantalla de consultas en la aplicación** (`/consultas/`): ejecuta los
  mismos archivos `.sql` del repositorio contra la base y muestra el resultado,
  la interpretación y el texto de la consulta. No existe una copia del SQL
  dentro del código.
- **Modelo entidad-relación en 3FN** (`docs/03-modelo-datos.md`), generado por
  introspección de la base real, con diccionario de datos completo y
  justificación de las anomalías evitadas.
- **Automatización con n8n** (`docs/n8n/flujo-despacho-informe.json`): despacho
  del informe al cliente y aviso a gerencia ante pendientes críticos, trazado a
  la tarea «Enviar informe al cliente» del BPMN *to-be*.
- **API de integración** (`app/core/api.py`): dos rutas autenticadas por token
  para que la automatización obtenga el informe y registre su despacho.
- **Operación sin conexión** (RNF-01): captura local en IndexedDB y
  sincronización automática al recuperar señal. **Estaba declarado fuera del
  alcance en la Entrega 1** y se implementó.
- **Mediciones eléctricas** (RF-17): digitalización de la hoja N° 002214, con
  detección automática de lecturas fuera de rango contra 400 V entre fases y
  230 V fase-neutro.
- **Informe de visita en PDF** (RF-13): generado en el servidor al cerrar la
  visita y archivado como registro inmutable con su propia huella SHA-256.
- **Planilla anual de control en Excel**: una hoja por mes, más hojas de
  pendientes y de seguimiento por tablero. Se regenera al cerrar cada visita.
- **Generación de visitas desde el calendario del ciclo** (RF-02, *Must*):
  la vista `/ciclos/` crea una visita por local del contrato, con las fechas
  repartidas dentro de la ventana del ciclo. Hasta esta entrega las visitas se
  creaban a mano desde el administrador de Django, que es una herramienta de
  desarrollo y no de operación.
- **Registro de materiales faltantes** (RF-11, *Should*): el técnico declara en
  terreno qué faltó y la vista `/materiales/` lo agrupa por local para
  abastecimiento. **Era el único requisito que atacaba la manifestación P6** del
  diagnóstico —re-trabajo en abastecimiento— y había quedado sin implementar.
- **Dos indicadores más en el panel**: latencia del registro y pendientes
  críticos. La latencia usa la misma definición y el mismo estadístico que
  `03-latencia-del-registro.sql`, para que el panel y la consulta no puedan dar
  números distintos.

### Cambiado

- **Las tablas se renombraron a nombres de negocio.** `core_tablero` pasó a ser
  `tablero`, `core_registro_item` a `registro_item`. El esquema se lee como un
  modelo de negocio y no como un volcado técnico, y el ER calza uno a uno con
  él.
- **La evidencia fotográfica pasó a ser obligatoria por ítem**, no por tablero.
  RF-03 dice que el sistema no debe permitir marcar un ítem como ejecutado sin
  registrar su evidencia asociada, y la implementación anterior lo cumplía sólo
  parcialmente. Una misma fotografía puede respaldar varios ítems, de modo que
  la regla no obliga a repetir quince capturas casi idénticas del mismo
  tablero.
- **La relación entre fotografía e ítems pasó de 1:N a N:M**, como consecuencia
  de lo anterior.
- **Las fotografías llevan la fecha, la hora y el tablero estampados dentro de
  la imagen**, no sólo en los metadatos, porque los metadatos se pierden al
  reenviar una imagen por mensajería.
- **Se agregó la exigencia de justificación** para los ítems marcados «No» o
  «No aplica», por simetría con la exigencia de evidencia para los marcados
  «Sí».
- **Los informes pasaron de generarse al vuelo a archivarse con versión.**
  Regenerar crea una versión nueva y las anteriores se conservan.
- **Los motivos de pendiente considerados críticos se declaran una sola vez**,
  en `Pendiente.MOTIVOS_CRITICOS`. Antes estaban escritos por separado en el
  flujo de automatización y en el panel, de modo que podían divergir sin que
  nadie lo notara.

### Corregido

- **El registro de una fotografía devolvía error 500.** `core/forms.py` usaba
  `django.utils.timezone.utc`, que Django eliminó en la versión 5.0, de modo que
  la validación de antigüedad de la evidencia reventaba al enviar el formulario.
  El defecto no se había detectado antes porque las 382 evidencias de los datos
  de demostración se crean por el ORM y nunca pasan por el formulario. Apareció
  al grabar la demostración del prototipo, manejando la aplicación como lo haría
  un técnico. Corregido usando el UTC de la biblioteca estándar.

### Quitado

- **El botón «marcar todo conforme».** Permitía completar los quince ítems de
  un tablero con un solo toque, lo que abría la puerta a declarar cumplimiento
  sin haberlo verificado. Ver la nota sobre RNF-03 más abajo.

### Limitación conocida

Al quitar el marcado en bloque y exigir evidencia por ítem, el registro de un
tablero pasó a requerir más de las **cinco interacciones** que declara el
RNF-03, que está priorizado como *Must*. Es un conflicto real entre dos
requisitos propios: la verificabilidad de RF-03 y la velocidad de RNF-03.

Se optó por privilegiar la verificabilidad, porque un registro rápido que no
prueba nada reproduce el problema que el sistema existe para resolver. La
discusión completa está en el informe, en la sección de limitaciones.

---

## [v1.0-e1] — Entrega 1

- Levantamiento en terreno de la PYME y caracterización del problema con seis
  manifestaciones medidas.
- Proceso *as-is* y rediseño *to-be* en BPMN 2.0.
- 18 requisitos funcionales y 10 no funcionales, priorizados con MoSCoW y
  trazados a las manifestaciones del problema.
- Modelo entidad-relación preliminar de 12 entidades.
