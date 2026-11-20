# Automatización del proceso con n8n

Proyecto IMELSE · ICN-292 Sistemas de Información para la Gestión · UTFSM 2026-2

Flujo exportado: [`docs/n8n/flujo-despacho-informe.json`](n8n/flujo-despacho-informe.json)

---

## 1. Qué se automatizó y por qué ésa tarea

Se automatizó el **despacho del informe de mantención al cliente**, que ocurre
cuando el técnico cierra una visita en terreno.

La elección no fue arbitraria. Hay cuatro razones concretas:

**Es una tarea que ya existe en el proceso rediseñado.** Está dibujada en el
BPMN *to-be*, en el carril SIG, con el nombre «Enviar informe a Cliente». La
automatización no inventa un paso nuevo: toma uno que el diagrama ya declaraba
y lo saca de las manos de una persona.

**Es exactamente lo que habíamos declarado fuera del alcance.** El informe de
la Entrega 1 dice que el prototipo generaría y archivaría el PDF, pero que el
envío quedaría en manos de una persona. La automatización cierra ese hueco, de
modo que es una mejora real y verificable sobre la entrega anterior.

**El punto de conexión ya estaba construido.** El modelo `InformeVisita` tiene
el método `marcar_despachado`, que registra a quién y cuándo se envió sin
alterar el documento ni su huella. No hubo que rediseñar nada para conectar la
automatización.

**De paso implementa un requisito pendiente.** El RF-18, «notificar a gerencia
cuando una visita se cierra con pendientes críticos», estaba priorizado como
*Could have* y no se había implementado. La rama condicional del flujo lo
resuelve.

---

## 2. Trazabilidad con el BPMN

| Elemento del flujo | Elemento del BPMN *to-be* |
|---|---|
| Disparador del webhook | Tarea «Cerrar visita», carril SIG |
| Descarga del PDF | Tarea «Generar informe», carril SIG |
| Rama de pendientes críticos | Compuerta «¿Cobertura completa?» y la rama «Declarar pendiente» |
| Envío al cliente | **Tarea «Enviar informe a Cliente», carril SIG** |
| Aviso a gerencia | Tarea nueva. Alimenta «Consultar panel», carril Gerencia (RF-18) |
| Registro del despacho | Escritura en el almacén de datos «Sistema de registro SIG» |

La tarea que la automatización reemplaza es la cuarta fila. Las demás son el
contexto que la hace posible.

---

## 3. El flujo, nodo por nodo

### Nodo 1 · «Visita cerrada» — Webhook

Queda escuchando en `POST /webhook/visita-cerrada`. El SIG le envía un aviso en
el momento en que el técnico cierra la visita, con esta estructura:

```json
{
  "evento": "visita.cerrada",
  "visita":    { "id": 17, "fecha": "2026-09-18", "ciclo": "Ciclo 5/2026",
                 "local": "Sucursal Centro", "cerrada_por": "Camila Soto" },
  "cobertura": { "tableros_esperados": 7, "tableros_registrados": 6,
                 "porcentaje": 86 },
  "pendientes":{ "total": 1, "criticos": 1,
                 "detalle": [ { "tablero": "TD-0407", "ubicacion": "Entrepiso",
                                "motivo": "Equipo en operación, no se pudo desenergizar",
                                "comentario": "..." } ] },
  "informe":   { "id": 31, "version": 1, "hash_sha256": "...",
                 "url_descarga": "http://…/api/informe/31/pdf/",
                 "url_despacho": "http://…/api/informe/31/despacho/" },
  "destinatario": "contacto@cliente-demo.cl",
  "destinatario_gerencia": "gerencia@imelse-demo.cl"
}
```

El aviso lo emite `core/integraciones.py`. Vale la pena señalar una decisión de
diseño: **si n8n está caído, el cierre de la visita se completa igual**. El
envío tiene un tiempo de espera de 5 segundos y cualquier fallo se registra en
la bitácora sin propagarse. Un técnico en terreno no puede quedar bloqueado
porque un servidor de correo no responde.

### Nodo 2 · «Obtener informe PDF» — HTTP Request

Descarga el PDF desde `url_descarga`, autenticándose con la cabecera
`X-SIG-Token`. El documento **no se arma en n8n**: se toma el que el SIG ya
generó y archivó con su huella SHA-256 al cerrar la visita. La respuesta
incluye la cabecera `X-SIG-Hash`, que permite verificar que se recibió el
archivo correcto.

### Nodo 3 · «¿Hay pendientes críticos?» — IF

Se bifurca según `pendientes.criticos > 0`. Se consideran críticos los motivos
`SIN_ACCESO`, `EN_OPERACION` y `NO_EXISTE`: son los que no se resuelven solos
en el ciclo siguiente, a diferencia de «tiempo insuficiente», que es ruido
operativo normal.

### Nodo 4a · «Avisar a gerencia» — Send Email

Rama verdadera. Envía a gerencia el detalle de los tableros que quedaron fuera,
con su motivo y su ubicación. Es el RF-18.

El valor está en el momento: hoy gerencia se entera de un tablero sin
intervenir **cuando falla**. Con esto se entera el mismo día, y los datos de la
consulta 2 muestran por qué importa: hay tableros que acumulan cinco ciclos
consecutivos sin que nadie levante la mano.

### Nodo 4b · «Enviar informe al cliente» — Send Email

Rama falsa, y también continuación de la rama verdadera: el cliente recibe su
informe en los dos casos. Adjunta el PDF descargado en el nodo 2 y redacta el
cuerpo con los datos de cobertura de la visita.

### Nodo 5 · «Registrar despacho en el SIG» — HTTP Request

Hace `POST` a `url_despacho` con el correo del destinatario. El SIG registra a
quién y cuándo se envió.

Este nodo es importante para la defensa del diseño: **el flujo no termina en el
aire**. El registro del despacho queda en la base de datos del sistema, no en
el historial de ejecuciones de n8n. Si mañana se cambia de herramienta de
automatización, el dato sigue estando donde corresponde.

Y no altera el documento ni su huella: `marcar_despachado` sólo añade el
destinatario y la marca de tiempo, que es el único dato que un informe admite
después de generado.

---

## 4. Lo que el SIG expone, y lo que deliberadamente no expone

La integración necesitó dos rutas nuevas, en `core/api.py`:

| Ruta | Método | Qué hace |
|---|---|---|
| `/api/informe/<id>/pdf/` | GET | Entrega el PDF archivado |
| `/api/informe/<id>/despacho/` | POST | Registra el destinatario y la hora |

No hay ninguna ruta que permita **modificar un registro de terreno**. La
inmutabilidad vale también para los sistemas que se conectan desde afuera, no
sólo para las personas que usan la interfaz. Un sistema que cierra la puerta de
adelante y deja abierta la de atrás no protege nada.

La autenticación es un token compartido comparado en tiempo constante. Es
suficiente para una integración entre dos servicios de la misma red, y se
documenta como tal: para exposición a internet correspondería OAuth, que está
fuera del alcance de esta entrega.

---

## 5. Cómo ejecutarlo

### Levantar n8n

```bash
npx n8n
```

Queda disponible en `http://localhost:5678`. No instala nada permanente.

### Importar el flujo

En el lienzo de n8n, menú de los tres puntos → **Import from File** → elegir
`docs/n8n/flujo-despacho-informe.json`.

### Conectar el SIG con el flujo

n8n muestra la URL del webhook al abrir el primer nodo. Esa URL se le pasa al
SIG por variable de entorno:

```bash
export N8N_WEBHOOK_URL="http://localhost:5678/webhook/visita-cerrada"
export SIG_BASE_URL="http://127.0.0.1:8000"
python manage.py runserver
```

Sin esa variable el sistema funciona igual, simplemente no avisa hacia afuera.

### Probarlo

Cerrar una visita desde la aplicación como usuario `tecnico`. El flujo se
ejecuta y en el lienzo de n8n se ve avanzar nodo por nodo.

---

## 6. Limitaciones declaradas

**El envío de correo necesita credenciales SMTP.** Para la demostración se usó
[indicar cuál: cuenta de Gmail con contraseña de aplicación, o el nodo de
correo simulado de n8n]. Si se usó el simulado, el correo no sale realmente del
equipo y corresponde decirlo.

**El token es compartido y está en el archivo del flujo.** En operación real
iría en las credenciales de n8n, que las cifra, y no en el JSON exportado.

**El flujo corre en localhost.** En producción, n8n y el SIG estarían en el
mismo servidor o en una red privada entre ambos.

---

## 7. Qué cambiaría en la operación real de IMELSE

Hoy, cerrada la visita, alguien en oficina tiene que acordarse de armar el
informe, adjuntarlo y mandarlo. Esa persona existe, tiene otras cosas que
hacer, y entre la visita y el correo pasan horas o días.

Con el flujo andando, el informe sale **en el momento en que el técnico cierra
la visita en el local**, antes de que la cuadrilla se suba a la camioneta. Y si
quedaron tableros críticos sin intervenir, gerencia lo sabe ese mismo día en
vez de enterarse cuando el tablero falla.

Las dos cosas apuntan al mismo problema del diagnóstico: la información existía
pero llegaba tarde.
