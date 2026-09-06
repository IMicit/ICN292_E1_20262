# Requerimientos — SIG de trazabilidad de mantención preventiva

**ICN-292 Sistemas de Información para la Gestión · Entrega 1 · 2026-2**
Caso: IMELSE · Ver [`00-caso-pyme.md`](00-caso-pyme.md)

---

## 1. Actores y roles

### Actores humanos

| Actor | Rol en el proceso | Interacción con el sistema |
|---|---|---|
| **Gerente de Operaciones** | Planifica el calendario, asigna cuadrillas, controla el cumplimiento | Consulta cumplimiento, revisa evidencia, gestiona el levantamiento de tableros |
| **Técnico** | Ejecuta la mantención y es el responsable del registro | Ejecuta el checklist guiado, captura evidencia, declara pendientes |
| **Ayudante** | Apoya la ejecución en terreno | Sin acceso propio; opera bajo la sesión del técnico |
| **Estudiante dual** | Apoyo en formación, rotativo | Sin acceso propio |
| **Administrativo (digitalización)** | Consolida y envía los informes al cliente | Genera y despacha el informe desde el sistema |
| **Encargado del local** | Levanta requerimientos al inicio de la visita y valida presencia | Firma o valida la visita (opcional) |

### Actores externos

| Actor | Naturaleza | Relación |
|---|---|---|
| **Cliente corporativo (SMU / Unimarc)** | Organización | Recibe el calendario anual y los informes de mantención |
| **Canal de mensajería actual (WhatsApp)** | Sistema externo | Sistema a reemplazar como canal de evidencia |
| **Correo electrónico** | Sistema externo | Canal de despacho del informe al cliente |

---

## 2. Alcance

### Dentro del alcance (in)

- Proceso de **mantención preventiva bajo contrato** con la unidad de negocio SMU (Unimarc)
- Registro maestro de locales y de los tableros de cada local (levantamiento)
- Ejecución guiada del checklist en terreno, con captura de evidencia
- Validación de cobertura de tableros por visita
- Declaración estructurada de trabajos pendientes
- Consulta de historial por tablero y por local
- Generación y despacho del informe de mantención al cliente
- Panel de control de cumplimiento para la gerencia

### Fuera del alcance (out)

| Excluido | Justificación |
|---|---|
| Servicios correctivos y de emergencia | Proceso distinto, sin calendario ni checklist estandarizado; se abordaría en una fase posterior |
| Integración con sistemas del cliente corporativo | Requiere acuerdo entre empresas, fuera del control de IMELSE |
| Gestión de inventario y bodega | El sistema registra el material faltante, no administra stock |
| Facturación y cobro de servicios | No forma parte del problema de trazabilidad declarado |
| Gestión de remuneraciones y turnos | Sin relación con el problema |
| Mantención de equipos de frío | Fuera del alcance técnico contractual de IMELSE |
| Aplicación para el cliente final | El cliente recibe informes; no opera el sistema |

---

## 3. Requisitos funcionales

Prioridad según MoSCoW: **M** = Must have, **S** = Should have, **C** = Could have, **W** = Won't have (esta versión).

Columna *Origen*: manifestación del problema en `00-caso-pyme.md` §5 que el requisito ataca.

| ID | Requisito | Actor | Prioridad | Origen |
|---|---|---|---|---|
| RF-01 | El sistema debe mantener un registro maestro de locales y de los tableros de cada local, con identificador y ubicación física, proveniente del levantamiento existente | Gerente | M | P3 |
| RF-02 | El sistema debe generar la visita de mantención a partir del calendario del ciclo, asociándola a un local, una fecha y una cuadrilla responsable | Gerente | M | P1 |
| RF-03 | El sistema debe presentar al técnico un checklist guiado por tablero, que no permite marcar un ítem como ejecutado sin registrar su evidencia asociada | Técnico | M | P2 |
| RF-04 | El sistema debe exigir la captura de al menos una fotografía por tablero intervenido, vinculada al ítem del checklist que la origina | Técnico | M | P2, P4 |
| RF-05 | El sistema debe registrar automáticamente fecha, hora y usuario en cada captura de evidencia, sin intervención del operador | Sistema | M | P2 |
| RF-06 | El sistema debe impedir el cierre de una visita mientras existan tableros del levantamiento sin registro, salvo declaración explícita de pendiente | Técnico | M | P3 |
| RF-07 | El sistema debe permitir declarar un tablero como pendiente indicando el motivo desde una lista predefinida y un comentario libre | Técnico | M | P3 |
| RF-08 | El sistema debe poner la evidencia de la visita a disposición de la oficina al momento del cierre de la visita, sin transferencia manual | Sistema | M | P1 |
| RF-09 | El sistema debe permitir consultar el historial completo de intervenciones de un tablero específico, ordenado cronológicamente | Gerente | M | P5 |
| RF-10 | El sistema debe registrar los hallazgos detectados durante la visita, clasificados por nivel de criticidad | Técnico | S | P5 |
| RF-11 | El sistema debe registrar los materiales o repuestos faltantes detectados en terreno, asociados al local y a la visita | Técnico | S | P6 |
| RF-12 | El sistema debe entregar a la gerencia un panel con el porcentaje de cobertura de tableros y de visitas completas por local y por ciclo | Gerente | S | P3, P5 |
| RF-13 | El sistema debe generar el informe de mantención en formato exportable, con la evidencia asociada, para su envío al cliente | Administrativo | S | P4 |
| RF-14 | El sistema debe administrar usuarios y perfiles de acceso diferenciados para técnico, gerencia y administración | Gerente | S | — |
| RF-15 | El sistema debe arrastrar automáticamente los pendientes declarados de un ciclo a la planificación del ciclo siguiente | Gerente | C | P3 |
| RF-16 | El sistema debe permitir al encargado del local validar la presencia de la cuadrilla mediante firma en el dispositivo | Encargado | C | — |
| RF-17 | El sistema debe registrar las mediciones numéricas de termografía asociadas a cada tablero | Técnico | C | P5 |
| RF-18 | El sistema debe notificar automáticamente a la gerencia cuando una visita se cierra con pendientes críticos | Sistema | C | P5 |
| RF-19 | Integración automática con los sistemas del cliente corporativo | — | W | Fuera de alcance |
| RF-20 | Gestión de inventario y control de stock de bodega | — | W | Fuera de alcance |

**Cobertura:** los seis puntos de dolor declarados en la entrevista quedan cubiertos por al menos un requisito *Must*. Ningún requisito *Must* carece de origen trazable.

---

## 4. Requisitos no funcionales

| ID | Requisito | Categoría | Prioridad | Origen |
|---|---|---|---|---|
| RNF-01 | El sistema debe operar sin conexión a internet durante la ejecución de la visita y sincronizar al recuperar señal, sin pérdida de evidencia | Disponibilidad | M | Las salas de tableros suelen ubicarse en subterráneos o bodegas sin cobertura celular *(por confirmar con la empresa)* |
| RNF-02 | Un registro de evidencia cerrado no debe poder modificarse ni eliminarse retroactivamente; toda corrección debe quedar como un registro nuevo con su autor y fecha | Integridad | M | El problema central es la falta de certeza sobre lo declarado; un registro editable reproduce el problema del papel |
| RNF-03 | El registro de un tablero completo no debe requerir más de 5 interacciones del operador, y la interfaz debe ser operable con una mano y con guantes | Usabilidad | M | El técnico opera en terreno; el 40 % del personal de apoyo son estudiantes duales rotativos sin experiencia acumulada |
| RNF-04 | El sistema debe soportar el volumen de evidencia del ciclo: aproximadamente 30 visitas mensuales con ~20 tableros cada una, con al menos una fotografía por tablero | Rendimiento | M | Volúmenes declarados en `00-caso-pyme.md` §3 |
| RNF-05 | El acceso debe estar controlado por perfil, y cada acción sobre un registro debe quedar atribuida a un usuario identificado | Seguridad | M | La atribución de responsabilidad es el objetivo del sistema |
| RNF-06 | El tratamiento de datos personales de trabajadores y de terceros debe ajustarse a la Ley 21.719, con minimización de datos y finalidad declarada | Cumplimiento | M | Anticipación normativa exigida por el enunciado |
| RNF-07 | El sistema debe ejecutarse en dispositivos móviles Android de gama media, sin requerir hardware especializado | Compatibilidad | S | La empresa no dispone hoy de tablets asignadas *(por confirmar)* |
| RNF-08 | Las fotografías deben comprimirse antes de la sincronización, sin perder legibilidad de la identificación del tablero ni de las conexiones | Rendimiento | S | Deriva de RNF-01 y RNF-04: sincronización sobre red móvil |
| RNF-09 | El prototipo de la Entrega 2 debe ser reproducible en localhost a partir del repositorio, con instrucciones en el README | Mantenibilidad | M | Requisito del curso |
| RNF-10 | El sistema debe conservar la evidencia por al menos el período de vigencia del contrato de mantención | Cumplimiento | S | El seguro comprometido es de 27.500 UF; la evidencia tiene valor probatorio ante siniestro |

---

## 5. Trazabilidad problema → requisito

| Manifestación del problema (§5 del caso) | Requisitos que la atacan |
|---|---|
| P1 · Traspaso de información diferido (16–24 h) | RF-02, RF-08, RNF-01 |
| P2 · Registro no verificable | RF-03, RF-04, RF-05, RNF-02 |
| P3 · Cobertura de tableros incierta | RF-01, RF-06, RF-07, RF-12, RF-15 |
| P4 · Pérdida de evidencia | RF-04, RF-13, RNF-02 |
| P5 · Detección tardía y reactiva | RF-09, RF-10, RF-12, RF-17, RF-18 |
| P6 · Re-trabajo en abastecimiento | RF-11 |

---

## 6. Supuestos y decisiones pendientes

| N° | Supuesto adoptado | Qué cambia si es falso |
|---|---|---|
| 1 | No hay señal celular confiable en las salas de tableros, por lo que RNF-01 (operación offline) es obligatorio | Si hay señal estable, RNF-01 baja a *Should* y el stack se simplifica de forma significativa: desaparece la capa de sincronización y el almacenamiento local |
| 2 | El levantamiento de tableros existente (80–90 % de los locales con contrato) es utilizable como carga inicial de RF-01 | Si el levantamiento está sólo en papel, se agrega un requisito de digitalización inicial y una etapa previa al despliegue |
| 3 | Los técnicos disponen de un dispositivo móvil apto | Si la empresa debe adquirir equipos, aparece un costo de implementación y RNF-07 se vuelve restrictivo |
| 4 | El envío del informe al cliente mantiene el correo como canal | Si el cliente exige un portal o formato propio, RF-13 crece en alcance |

Estos supuestos fueron consultados a la empresa por correo y durante la entrevista y se
actualizarán en cuanto haya respuesta.
