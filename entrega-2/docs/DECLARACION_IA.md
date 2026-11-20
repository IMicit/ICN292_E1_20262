# Declaración de uso de inteligencia artificial

Proyecto IMELSE · ICN-292 Sistemas de Información para la Gestión · UTFSM 2026-2

---

## Alcance

El equipo usó asistentes de inteligencia artificial durante el desarrollo de la
Entrega 2, con autorización expresa del profesor del ramo para este proyecto en
particular, dada su naturaleza.

Esta declaración describe en qué se usó y en qué no.

---

## Dónde se usó

**Desarrollo del prototipo.** La implementación en Django del sistema —modelos,
vistas, plantillas, la capa de operación sin conexión, la generación del
informe en PDF y de la planilla anual— se construyó con asistencia de IA a
partir de los requisitos que el equipo había levantado y especificado en la
Entrega 1.

**Diseño del esquema SQL.** El archivo `db/schema.sql` se redactó con
asistencia, partiendo del modelo de datos que el equipo definió. Las decisiones
de diseño —claves subrogadas, tablas append-only, qué reglas del negocio
declarar como restricciones— se discutieron y se adoptaron por el equipo.

**Consultas de negocio.** Las seis consultas de `db/consultas/` se escribieron
con asistencia. Las preguntas que responden las definió el equipo a partir del
diagnóstico de la Entrega 1.

**Flujo de automatización.** El archivo de n8n se generó con asistencia. La
elección de qué tarea automatizar la hizo el equipo, por su trazabilidad con el
BPMN *to-be*.

**Redacción de la documentación.** Los documentos de `docs/`, el README y este
informe se redactaron con asistencia, sobre el contenido técnico y las
decisiones del equipo.

**Datos de demostración.** El contenido de `db/seed.sql` es sintético y se
generó programáticamente, salvo los 25 ítems de la pauta, que son transcripción
literal de la ficha N° 002190 levantada en terreno por el equipo.

---

## Dónde no se usó

**El levantamiento en terreno.** La entrevista al gerente de operaciones de
IMELSE, la observación del proceso, la recolección de las fichas en papel y la
medición de las manifestaciones del problema son trabajo de campo del equipo.

**La caracterización del problema.** Las seis manifestaciones, sus cifras y su
priorización salieron del levantamiento, no de un modelo.

**La especificación de requisitos.** Los 18 requisitos funcionales y los 10 no
funcionales, con su priorización MoSCoW, se definieron en la Entrega 1 a partir
del trabajo de campo.

**El modelado del proceso.** Los diagramas BPMN *as-is* y *to-be* los construyó
el equipo en Bizagi Modeler.

**Las decisiones de diseño.** Qué automatizar, qué dejar fuera del alcance, qué
motor de base de datos adoptar y cómo resolver el conflicto entre RF-03 y
RNF-03 son decisiones del equipo, tomadas y discutidas por sus integrantes.

---

## Verificación

El equipo ejecutó y verificó todo el código que entrega. En particular:

- El esquema y los datos se cargaron en una base PostgreSQL 16 limpia y se
  comprobó que ambos archivos corren sin error.
- Las seis consultas se ejecutaron contra esa base y sus resultados son los
  que aparecen en `docs/04-sql-consultas.md`.
- La aplicación se levantó y se recorrió completa en los tres perfiles de
  usuario.
- El flujo de n8n se importó y se ejecutó.

---

## Texto para el informe

> El equipo utilizó asistentes de inteligencia artificial en el desarrollo del
> prototipo, el diseño del esquema SQL y las consultas de negocio, la
> construcción del flujo de automatización y la redacción de la documentación,
> partiendo en todos los casos del levantamiento en terreno, la
> caracterización del problema, la especificación de requisitos y el modelado
> de procesos elaborados por el equipo en la Entrega 1. Las decisiones de
> diseño —qué automatizar, qué dejar fuera del alcance, qué motor de base de
> datos adoptar y cómo resolver el conflicto detectado entre los requisitos
> RF-03 y RNF-03— fueron tomadas y discutidas por los integrantes. Todo el
> código entregado fue ejecutado y verificado por el equipo.
