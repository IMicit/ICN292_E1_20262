# Proceso de negocio: *as-is* y *to-be*

Proyecto IMELSE · ICN-292 Sistemas de Información para la Gestión · UTFSM 2026-2

Diagramas en BPMN 2.0, modelados en Bizagi Modeler:

| Diagrama | Archivo editable | Imagen |
|---|---|---|
| Proceso actual (*as-is*) | [`assets/bpmn-as-is-imelse.bpm`](../assets/bpmn-as-is-imelse.bpm) | [`assets/bpmn-as-is-imelse.png`](../assets/bpmn-as-is-imelse.png) |
| Proceso rediseñado (*to-be*) | [`assets/bpmn-to-be-imelse.bpm`](../assets/bpmn-to-be-imelse.bpm) | [`assets/bpmn-to-be-imelse.png`](../assets/bpmn-to-be-imelse.png) |

---

## 1. El proceso actual (*as-is*)

Cuatro carriles: **Cliente**, **Gerencia**, **IMELSE SpA** (la cuadrilla en
terreno) y **Administración**.

### Tiempos medidos en el levantamiento

Los tiempos provienen de la entrevista al gerente de operaciones y de la
observación de visitas. Las celdas marcadas **«no medido»** son actividades que
el levantamiento no alcanzó a cronometrar. Se declaran como tales en vez de
estimarlas: un número inventado en esta tabla contaminaría el caso de negocio
completo, porque de acá sale la línea base contra la que se compara el sistema.

| Actividad | Trabajo | Espera | Rol |
|---|---|---|---|
| Recibir solicitud de hora | 5 min | no medido | Administración |
| Agendar hora | no medido | no medido | Administración |
| Dirigirse al local | 30 min | — | Cuadrilla |
| Ejecutar la mantención | 9 h | — | Cuadrilla |
| Rellenar el informe en papel | 20 min | **15 h** | Cuadrilla |
| Volver a local IMELSE con el informe | — | 30 min | Cuadrilla |
| Recibir los informes del día anterior | no medido | no medido | Administración |
| Digitalizar el informe | no medido | no medido | Administración |
| Enviar el informe al cliente | no medido | no medido | Administración |

### Las tres cosas que el diagrama *as-is* deja ver

**1. La latencia está dibujada.** Después de «Enviar informe a Administración»
hay un **evento intermedio de temporizador rotulado «16 a 24 horas»**. No es una
estimación nuestra puesta en el informe: es un elemento del modelo. Esa espera
es la manifestación P1 del diagnóstico, y no es ineficiencia de las personas
sino una propiedad del instrumento: un papel no puede estar en dos lugares a la
vez.

**2. El pendiente no existe como dato.** La compuerta «¿Algún pendiente?»
conduce, por la rama *Sí*, a una actividad llamada literalmente **«Pendiente sin
registro formal»**, con una anotación adjunta que dice: *«El pendiente se
comunica verbalmente si es que se pregunta, no queda registrado ni corregido»*.
Ésa es la manifestación P3 —cobertura incierta— escrita en el propio diagrama
del proceso actual.

**3. Un tablero no es una unidad del proceso.** La actividad central se llama
«Realizar mantenimiento general agendado con toma de pruebas fotográficas
**(20 – 40 tableros eléctricos)**»: una sola caja para entre veinte y cuarenta
tableros. Mientras el proceso no distinga tablero por tablero, no existe
denominador posible para medir cobertura, y por eso hoy IMELSE no puede
calcularla.

El *as-is* incluye además un ciclo de corrección que el *to-be* elimina:
«Solicitar detalles faltantes» → «Volver al local y tomar pruebas solicitadas»
→ «Enviar pruebas fotográficas». Es decir, **volver al local porque la
evidencia llegó incompleta**.

---

## 2. El proceso rediseñado (*to-be*)

Cinco carriles. Al *as-is* se le agrega **SIG**, que concentra las tareas de
servicio que antes eran trabajo manual de una persona.

| Carril | Qué hace en el *to-be* |
|---|---|
| Cliente | Solicita servicio y recibe el informe |
| SIG | Valida cobertura, cierra la visita, genera el informe y lo envía |
| Gerencia | Programa el ciclo y consulta el panel |
| IMELSE SpA (cuadrilla) | Ejecuta la visita y genera el registro mientras trabaja |
| Administración | Atiende el retiro de materiales y mantiene el stock de bodega |

### El tramo de materiales

El *to-be* modela lo que ocurre cuando la cuadrilla no tiene con qué trabajar:

1. «Evaluar materiales necesarios» → compuerta **«¿Tiene lo necesario para el
   trabajo?»**
2. Rama *No*: «Rellenar formulario "Retiro de materiales y herramientas"» →
   «Enviar formulario a Administración» → **evento intermedio de temporizador**
   (la espera del despacho) → Administración «Entregar materiales solicitados»
   → «Actualizar stock de bodega» (almacén de datos *Stock de bodega*).
3. «Entregar materiales solicitados» dispara un **evento intermedio de mensaje**
   rotulado **«Materiales entregados»**, que la cuadrilla recibe en
   «Recepcionar y confirmar materiales».
4. Las dos ramas convergen antes de la compuerta «¿Es mantenimiento preventivo
   o correctivo?».

**Estos dos son los eventos intermedios del *to-be*, y están tipificados**: uno
de temporizador y uno de mensaje. El *as-is* tenía seis eventos intermedios y
el *to-be* tiene dos; la reducción es consecuencia de haber eliminado las
esperas, no de haber simplificado el dibujo.

### El tramo de ejecución y cierre

- Compuerta **«¿Es mantenimiento preventivo o correctivo?»**
  - *Preventivo* → **subproceso multi-instancia «Realizar mantenimiento por
    tablero»**. Éste es el cambio estructural respecto del *as-is*: lo que era
    una caja para 20–40 tableros pasa a ser un subproceso que se instancia
    **una vez por tablero**. De ahí sale el denominador de la cobertura.
  - *Correctivo* → «Realizar correctivos» → «Tomar muestras fotográficas» →
    «Completar formulario "Hoja de servicio"».
- «Anotar observaciones en sistema» → «Solicitar cierre de proceso».
- [SIG] «Validar cobertura de tableros» → compuerta **«¿Cobertura completa?»**
  - *Sí* → «Cerrar visita».
  - *No* → **«Declarar pendiente»**, y desde ahí al cierre. Es la única salida:
    el flujo no tiene un camino que permita cerrar y no decir nada. Compárese
    con «Pendiente sin registro formal» del *as-is*.
- «Cerrar visita» → «Generar informe» → **«Enviar informe a Cliente»** → evento
  de fin «Proceso completo y guardado en base de datos».
- [Gerencia] evento de inicio de temporizador «Necesidad de revisión de caso» →
  «Consultar panel» → fin «Informe de proceso en poder de la gerencia».

### Qué actividades desaparecen

| Actividad del *as-is* | Qué pasa en el *to-be* |
|---|---|
| Rellenar informe en papel (20 min + 15 h de espera) | Reemplazada por el registro tablero por tablero, durante la ejecución |
| Volver a local IMELSE con el informe (30 min) | **Eliminada.** No hay nada que transportar |
| Digitalizar el informe | **Eliminada.** El dato nace digital |
| Evento «16 a 24 horas» | **Eliminado.** El cierre publica la evidencia en el acto |
| «Pendiente sin registro formal» | Reemplazada por «Declarar pendiente», con motivo, autor y fecha |
| «Volver al local y tomar pruebas solicitadas» | **Eliminada.** La visita no cierra con evidencia incompleta |

---

## 3. Qué se automatizó, y su trazabilidad

La automatización construida en n8n corresponde a **una tarea concreta del
diagrama**: **«Enviar informe a Cliente», en el carril SIG**. No es un paso
nuevo inventado para la entrega, sino uno que el *to-be* ya declaraba y que se
sacó de las manos de una persona.

El detalle del flujo, nodo por nodo, con la correspondencia entre cada nodo y
su elemento del BPMN, está en
[`05-automatizacion-n8n.md`](05-automatizacion-n8n.md).

---

## 4. Trazabilidad entre el proceso y el modelo de datos

Cada actividad del *to-be* que produce información tiene una entidad que la
guarda. La correspondencia completa está en
[`03-modelo-datos.md`](03-modelo-datos.md), sección 7.

| Actividad del *to-be* | Entidad |
|---|---|
| Confirmar programación del ciclo | `ciclo`, `visita` |
| Realizar mantenimiento por tablero | `registro_tablero`, `registro_item` |
| Tomar muestras fotográficas | `evidencia`, `evidencia_item` |
| Declarar pendiente | `pendiente` |
| Evaluar materiales necesarios / retiro de materiales | `material_faltante` |
| Completar formulario «Hoja de servicio» | `medicion_electrica` |
| Anotar observaciones en sistema | `observacion`, `hallazgo` |
| Cerrar visita | `visita.estado`, `visita.ts_cierre` |
| Generar informe | `informe_visita` |
| Enviar informe a Cliente | `informe_visita.ts_despacho`, escrito por la automatización |
| Consultar panel | Vista `/panel/`, sin entidad propia: es lectura |

---

## 5. Lo que el prototipo no implementa del *to-be*

Conviene decirlo antes de que lo pregunten, porque el diagrama es más amplio
que el sistema construido.

**El flujo de bodega.** El *to-be* modela el retiro de materiales con
formulario, despacho desde Administración y actualización del stock. El
prototipo **no** gestiona bodega ni stock. Lo que sí implementa es el registro
de lo que faltó en terreno (RF-11, entidad `material_faltante`) y la consulta
que agrupa esos faltantes por local para abastecimiento. Es la parte del tramo
que ataca la manifestación P6; el inventario en sí queda fuera del alcance.

**El tramo comercial.** Cotización, evaluación de proyectos y los servicios
correctivos de emergencia están en el diagrama porque forman parte del negocio,
pero el sistema cubre la mantención preventiva programada.

**El arrastre de pendientes al ciclo siguiente** (RF-15) y **la firma del
encargado del local** (RF-16) están priorizados como *Could have* desde la
Entrega 1 y siguen pendientes. La consulta 2 muestra por qué el primero
importa: hay tableros que acumulan cinco ciclos consecutivos fuera.
