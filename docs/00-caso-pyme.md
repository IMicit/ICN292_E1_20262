# Caso: IMELSE — Mantenimiento eléctrico para retail

**ICN-292 Sistemas de Información para la Gestión · Entrega 1 · 2026-2**
Universidad Técnica Federico Santa María — Departamento de Industrias

---

## 1. Identificación de la PYME

| Campo | Dato |
|---|---|
| Nombre de fantasía | IMELSE |
| Razón social | [POR CONFIRMAR] |
| RUT | [POR CONFIRMAR] |
| Rubro | Servicios de mantenimiento eléctrico industrial, con foco en retail y supermercados |
| Ubicación | Av. General Saavedra 1217, Independencia, Región Metropolitana |
| Contacto | (56-2) 27323122 · contacto@imelse.cl |
| Sitio web | https://imelse.cl |
| Gerente General | Yuri Rojas |
| Constitución | Opera desde el año 2000 como persona natural; sociedad limitada desde 2009 |
| Dotación | 24 personas: 14 de planilla fija y 10 estudiantes en formación dual |
| Distribución | 4 personas en oficina, 20 en terreno |

### Justificación del alcance PYME

Con 24 personas y una estructura administrativa de 4 personas, IMELSE se encuentra dentro del
rango de pequeña empresa. El proyecto se acota además al **proceso de mantención preventiva
bajo contrato con la unidad de negocio SMU (Unimarc)**, que constituye la operación recurrente
y contractualmente comprometida de la empresa.

### Programa de formación dual

IMELSE participa en un convenio de educación dual asociado a la SOFOFA, que se trata de que
10 estudiantes de enseñanza media técnica asisten dos días por semana como ayudantes de
los técnicos (cinco de tercero medio los jueves y viernes, cinco de cuarto medio los lunes y martes).
Este dato es relevante para el diseño del sistema ya que una fracción del personal en terreno
es rotativa y de baja permanencia, lo que refuerza la necesidad de que el procedimiento
quede guiado por el sistema y no dependa de la experiencia acumulada del técnico.

---

## 2. Servicios y clientes

### Líneas de servicio

- Mantención preventiva de salas y tableros eléctricos (contrato)
- Servicios correctivos y de emergencia (24/7)
- Proyectos y mejoras de infraestructura eléctrica
- Termografía, mediciones de calidad de energía, reapriete de automáticos
- Bancos de condensadores, iluminación de emergencia, sistemas fotovoltaicos

### Clientes

| Grupo | Marcas atendidas | Modalidad |
|---|---|---|
| SMU | Unimarc | Contrato de mantención bimensual (~60–70 locales) |
| SMU | Alvi, Mayorista 10 | Servicios puntuales a solicitud |
| Cencosud | Jumbo, Santa Isabel | Correctivos y proyectos |
| Falabella | Tottus, Sodimac | Correctivos |

Trayectoria: la empresa se adjudicó 33 locales de Santa Isabel (Cencosud) hasta 2011,
posteriormente ingresó a Falabella con Tottus, y hace cuatro años se adjudicó el contrato
de Unimarc, que partió con cerca de 50 locales y hoy bordea los 70.

### Cobertura geográfica

Contrato acotado a la Región Metropolitana: Tiltil por el norte, Linderos por el sur,
Talagante por el poniente, incluyendo el sector oriente (Las Condes, La Dehesa).
Servicios puntuales se han extendido a la Quinta Región y, excepcionalmente, a proyectos
fuera de la zona central.

### Alcance técnico

La responsabilidad de IMELSE llega **hasta el punto eléctrico**. Los equipos de frío,
murales e islas de congelado son responsabilidad de un contrato de mantención distinto.
Esta frontera es relevante para el modelo de datos: un servicio se cierra en el punto de
conexión, no en el equipo del cliente.

---

## 3. Volúmenes de operación

| Indicador | Valor |
|---|---|
| Locales bajo contrato de mantención | ~60–70 (Unimarc) |
| Frecuencia del contrato | Bimensual: mitad de los locales un mes, mitad el siguiente |
| Mantenciones preventivas por mes | ~30 |
| Mantenciones simultáneas por día | 2 locales |
| Servicios correctivos por mes | ~80 (mínimo 1–2 diarios) |
| Tableros por local (Unimarc) | ~20 |
| Tableros por local (formato mayor, ej. Jumbo) | 40–60 |
| Duración de una mantención preventiva | Jornada completa (09:30 a 17:30) |
| Duración de un correctivo | 2 horas a 2 días según complejidad |
| Composición de cuadrilla | Técnico + ayudante + dual (mínimo 2 personas por seguridad) |
| Horario de operación | 09:00 a 18:00; correctivos fuera de horario con recargo |

### Estacionalidad

- **Invierno:** filtraciones de agua en los locales generan cortes y fallas.
- **Verano:** el aumento de consumo por equipos de frío y la conexión no autorizada de
  equipos adicionales por parte de proveedores satura los circuitos.

---

## 4. Evidencia de existencia y del caso

| N° | Evidencia | Fecha | Ubicación en github |
|---|---|---|---|
| 1 | Captura del sitio web imelse.cl (identificación, servicios, clientes) | [01/09/2026] | `assets/ev-01-sitio.png` |
| 2 | Acta de entrevista firmada por el Gerente de Operaciones | [03/09/2026] | `assets/ev-02-acta.pdf` |
| 3 | Ficha de checklist de mantención en uso | [03/09/2026] | `assets/ev-03-ficha-checklist.png` |
| 4 | Hoja de registro de tableros con termografía | [03/09/2026] | `assets/ev-04-registro-tableros.png` |
| 5 | Transcripción completa de la entrevista | [05/09/2026] | `docs/04-transcripción-entrevista.pdf.pdf` |
| 6 | Registro fotográfico de la visita | [06/09/2026] | `assets/ev-06-visita.pdf` |

**Entrevista.** Realizada en dependencias de la empresa el [03/09/2026], con el Gerente general [Yuri Rojas] 
junto al Gerente de Operaciones, [Francisco Meza], quien firmó el acta autorizando el uso del nombre
de la organización con fines académicos.


---

## 5. Problema de negocio

 En el proceso de mantención preventiva de tableros eléctricos, **entre 15 y 20 de cada 100
 mantenciones quedan incompletas** sin que la oficina lo detecte oportunamente, porque el
 cumplimiento del procedimiento se registra en checklists de papel que el técnico completa
 sin evidencia verificable por tablero y que llegan a oficina al día siguiente. Esto genera
 re-visitas absorbidas por la empresa, tableros que pasan ciclos completos sin revisión, y
 exposición a falla eléctrica bajo un contrato con seguro comprometido de 27.500 UF.

### Manifestaciones concretas (declaradas en entrevista)

1. **Traspaso de información diferido.** Los técnicos están en terreno toda la jornada y
   entregan la información al final del día o a la mañana siguiente. La revisión en oficina
   ocurre, en la práctica, al día siguiente del servicio.

2. **Registro no verificable.** El checklist en papel permite declarar la ejecución sin
   respaldo. En palabras del entrevistado, el técnico puede consignar lo que quiera y la
   gerencia debe conformarse con esa declaración.

3. **Cobertura de tableros incierta.** Se han detectado tableros no intervenidos y
   justificados como desconocidos o no ubicados, pese a que existe un levantamiento previo
   de las instalaciones en el 80–90 % de los locales con contrato.

4. **Pérdida de evidencia.** Las fotografías y los informes circulan por WhatsApp y correo;
   al solicitarlos posteriormente, en ocasiones no se encuentran.

5. **Detección tardía y reactiva.** El incumplimiento se descubre cuando otra persona visita
   el local y encuentra un tablero evidentemente sin intervenir, lo que obliga a reconstruir
   a posteriori quién pasó y cuándo.

6. **Re-trabajo en abastecimiento.** La información incompleta sobre materiales faltantes
   provoca compras erradas y desplazamientos adicionales al local.

### Impacto

| Dimensión | Efecto |
|---|---|
| Servicio | Mantenciones incompletas que se arrastran al ciclo siguiente (bimensual) |
| Costo | Re-visitas absorbidas por la empresa; compras erradas y viajes repetidos |
| Tiempo | Latencia de ~16 a 24 horas entre la ejecución y la disponibilidad del registro |
| Riesgo | Falla de tableros no intervenidos, con responsabilidad contractual y seguro de 27.500 UF comprometido |
| Control | Imposibilidad de auditar cobertura de tableros por local y por ciclo |

### Intentos previos de solución

La empresa ha ensayado dos mecanismos, ambos con resultados parciales. Esto evidencia que
el problema es estructural y no atribuible a falta de voluntad de la gerencia:

| Intento | Mecanismo | Resultado |
|---|---|---|
| 1 | Etiqueta adhesiva en la puerta del tablero con fecha, técnico y próxima pasada | Fallido: los técnicos dejaban de instalarla ante cualquier faltante operativo menor, para no comprometer responsabilidad. Sin etiqueta, tampoco había registro |
| 2 | Hoja de registro con termografía, mediciones y fotografía del tablero abierto (vigente hace ~1,5 meses) | Parcialmente efectivo: aumentó la detección de hallazgos, pero mantiene la latencia de un día y no garantiza cobertura completa de tableros |

El segundo intento es especialmente relevante como línea base: al exigir fotografía por
tablero, la empresa reporta que aparecen considerablemente más hallazgos que antes, lo que
sugiere que el subregistro previo era mayor al percibido.

---

## 6. Objetivo del SIG propuesto

Dotar a la gerencia de **certeza verificable y oportuna** de que cada tablero comprometido en
un local fue efectivamente intervenido, por quién y con qué resultado, sustituyendo la
declaración en papel por un registro guiado y evidenciado que se genera en el momento de la
ejecución.

### Decisiones que el sistema debe habilitar

- Determinar, antes de cerrar una visita, qué tableros del levantamiento quedaron sin registro.
- Verificar el cumplimiento del procedimiento sin depender de un interrogatorio posterior.
- Consultar el historial de intervenciones de un tablero específico para discriminar si un
  hallazgo es preexistente o sobrevenido.
- Priorizar la programación del ciclo siguiente con los pendientes declarados del ciclo actual.

---

## 7. KPI propuestos para la Entrega 2

| KPI | Definición | Línea base | Meta preliminar |
|---|---|---|---|
| Tasa de mantención completa | Mantenciones con checklist cerrado y evidencia por tablero / mantenciones ejecutadas | 80–85 % | ≥ 95 % |
| Cobertura de tableros | Tableros con registro en el ciclo / tableros del levantamiento del local | No medible hoy | ≥ 98 % |
| Latencia del registro | Tiempo entre cierre del servicio en terreno y disponibilidad del registro en oficina | ~16–24 h | < 1 h |
| Tasa de re-visita | Servicios que requieren retorno por trabajo no completado / servicios ejecutados | [POR CONFIRMAR] | Reducción del 50 % |

Los dos primeros atacan directamente el problema declarado. El tercero es consecuencia
estructural del cambio de soporte. El cuarto traduce el problema a costo y requiere
confirmación de dato con la empresa.

---

## 8. Datos pendientes de confirmación

Solicitados a la empresa por correo con fecha [07/09/2026]:

- [ ] Razón social completa y RUT
- [ ] Promedio de tableros por local con contrato
- [ ] **Disponibilidad de señal celular en salas de tableros** (define si el sistema requiere
      operación offline con sincronización posterior — RNF crítico)
- [ ] Si los técnicos utilizan equipo propio o provisto por la empresa
- [ ] Formato actual del levantamiento de tableros (digital o papel)
- [ ] Número estimado de re-visitas mensuales y su costo aproximado
- [ ] Tiempo de digitalización y envío del informe al cliente

---

## 9. Trazabilidad

| Sección de este documento | Alimenta a |
|---|---|
| §3 Volúmenes | Dimensionamiento y KPI (`03-er-preliminar.md`, E2) |
| §5 Problema y manifestaciones | Requisitos funcionales (`01-requerimientos.md`) |
| §5.1 Traspaso diferido | BPMN as-is, espera entre ejecución y revisión (`02-bpmn.md`) |
| §5.3 Cobertura incierta | Entidad `Tablero` y relación con `Visita` (`03-er-preliminar.md`) |
| §6 Objetivo | Alcance in/out (`01-requerimientos.md`) |
| §7 KPI | Entrega 2 |
