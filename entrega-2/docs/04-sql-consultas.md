# Consultas de negocio

Proyecto IMELSE · ICN-292 Sistemas de Información para la Gestión · UTFSM 2026-2

Motor: **PostgreSQL 16**. Los archivos están en
[`db/consultas/`](../db/consultas/) y se ejecutan tal cual, sin modificación.

---

## Cómo reproducir estos resultados

Desde un clon limpio del repositorio, con PostgreSQL 16 instalado:

```bash
createdb sig_imelse
psql -d sig_imelse -f db/schema.sql
psql -d sig_imelse -f db/seed.sql

psql -d sig_imelse -f db/consultas/01-cobertura-por-local-y-ciclo.sql
psql -d sig_imelse -f db/consultas/02-tableros-sin-intervencion.sql
psql -d sig_imelse -f db/consultas/03-latencia-del-registro.sql
psql -d sig_imelse -f db/consultas/04-motivos-de-pendiente.sql
psql -d sig_imelse -f db/consultas/05-items-que-mas-fallan.sql
psql -d sig_imelse -f db/consultas/06-materiales-por-comprar.sql
```

Los resultados de este documento se obtuvieron exactamente así.

**Las mismas consultas se ejecutan dentro de la aplicación**, en la ruta
`/consultas/`. La pantalla lee estos archivos del repositorio: no existe una
copia del SQL dentro del código, de modo que editar un `.sql` cambia lo que la
aplicación muestra. Es la forma más corta de demostrar que ningún número de
este informe se inventó.

**Volumen de la base:** 24 visitas en 6 ciclos, 22 tableros en 4 locales, 1.805
respuestas de la pauta, 382 evidencias, 105 registros de tablero sellados y 15
materiales faltantes declarados en terreno.

---

## 1 · Cobertura de mantención por local y ciclo

**¿De los tableros que había que revisar en cada local, cuántos se revisaron de
verdad?**

Resumido por ciclo:

| Ciclo | Tableros esperados | Registrados | Cobertura |
|---|---|---|---|
| 1 | 22 | 19 | 86,4 % |
| 2 | 22 | 20 | 90,9 % |
| 3 | 22 | 19 | 86,4 % |
| 4 | 22 | 19 | 86,4 % |
| 5 | 22 | 19 | 86,4 % |
| 6 *(en ejecución)* | 22 | 9 | 40,9 % |

La consulta completa devuelve 24 filas, una por local y ciclo.

### Interpretación

Éste es el indicador central del proyecto, y **hoy IMELSE no puede
calcularlo**. El checklist en papel se llena una vez por visita y no dice a
cuántos tableros se refiere: una hoja marcada «sí» en todos los puntos puede
corresponder a ocho tableros o a cinco, y no hay forma de distinguirlo.

Acá el denominador sale del catálogo y el numerador de los registros sellados,
así que el porcentaje es verificable y no declarado.

La cobertura se estabiliza en torno al 86 %, lo que es consistente con el
diagnóstico de la Entrega 1, que estimaba cerca de un 17 % de mantenciones
incompletas. La diferencia es que ahora el número se mide en vez de estimarse.

Una fila con cobertura bajo el 100 % y la visita ya cerrada no es un error del
sistema: significa que los tableros faltantes quedaron declarados como
pendientes con su motivo, que es la única salida que el sistema permite. El
ciclo 6 aparece en 40,9 % porque está en ejecución.

---

## 2 · Tableros que acumulan ciclos sin intervención

**¿Qué tableros llevan más tiempo sin que nadie los revise, y por qué?**

| Local | Tablero | Ubicación | Veces intervenido | Ciclos pendiente | Motivo recurrente |
|---|---|---|---|---|---|
| Sucursal Oriente | TD-0205 | Sala de máquinas | **0** | 5 | Sala sin acceso |
| Sucursal Centro | TD-0407 | Entrepiso | **0** | 5 | Equipo en operación |
| Sucursal Oriente | TD-0204 | Pasillo de cámaras | 4 | 1 | Tiempo insuficiente |
| Sucursal Poniente | TD-0304 | Pasillo de cámaras | 4 | 1 | Tiempo insuficiente |
| Sucursal Centro | TD-0406 | Andén de carga | 4 | 1 | Tiempo insuficiente |
| Sucursal Norte | TD-0106 | Andén de carga | 5 | 1 | Tiempo insuficiente |

### Interpretación

**Ésta es la consulta que justifica el proyecto completo.**

El diagnóstico de la Entrega 1 afirmaba que hay tableros que pasan ciclos
bimensuales enteros sin revisión y que nadie se entera hasta que fallan. Con el
papel esa afirmación no se podía comprobar. Acá se ve, con nombre y apellido.

**TD-0205 y TD-0407 tienen cero intervenciones en todo el año.** Cinco ciclos
bimensuales consecutivos declarados como pendientes significa **diez meses
descubiertos**. Cuando uno de esos tableros falle, la visita de emergencia la
paga IMELSE por contrato, y el seguro comprometido es de 27.500 UF.

La columna del motivo recurrente separa dos problemas distintos que exigen dos
decisiones distintas:

- TD-0205 queda fuera por **sala sin acceso**, cinco veces seguidas. Es un
  problema de coordinación con el local y se resuelve con una llamada previa.
- TD-0407 queda fuera por **equipo en operación**, cinco veces seguidas. Es un
  problema contractual: hay que negociar con el cliente una ventana de
  desenergización.

Las otras cuatro filas son pendientes aislados por tiempo insuficiente, que es
ruido operativo normal y no requiere acción.

Sin esta consulta, los seis casos se ven igual. Con ella, dos son urgentes y
cuatro no.

---

## 3 · Latencia entre la ejecución en terreno y la disponibilidad en oficina

**¿Cuánto demora en llegar a la oficina lo que el técnico hizo en el local?**

| Visitas medidas | Promedio | Mínimo | Máximo |
|---|---|---|---|
| 21 | **6,8 minutos** | 3 min | 11 min |

Línea base del proceso en papel, según el levantamiento de la Entrega 1:
**16 a 24 horas**.

### Interpretación

El papel viaja físicamente con la cuadrilla, alguien lo transcribe en oficina y
recién entonces se arma el informe. Durante esas 16 a 24 horas, la gerencia no
tiene forma de saber qué pasó en terreno.

El sistema mide lo mismo en **minutos**, y la razón de fondo vale la pena
decirla con precisión: no se optimizó el paso de traspaso, **el paso dejó de
existir**. Al cerrar la visita, la evidencia ya está en la base. Los 6,8
minutos promedio son el tiempo entre sellar el último tablero y apretar el
botón de cerrar.

Son unos **950 minutos ahorrados por visita**, cerca de 16 horas. Con 30
visitas mensuales, eso equivale a alrededor de 475 horas al mes de información
que antes estaba en tránsito y ahora está disponible.

La consulta devuelve además `minutos_de_ejecucion`, que mide cuánto dura una
visita en terreno: entre 89 y 141 minutos. Ese dato hoy tampoco existe y sirve
para planificar las rutas con algo más que una estimación.

---

## 4 · Motivos por los que un tablero queda sin intervenir

**¿Qué impide completar las visitas, y es un problema del local o de la
planificación?**

| Local | Motivo | Veces | Ciclos afectados | % del local |
|---|---|---|---|---|
| Sucursal Centro | Equipo en operación | 5 | 5 | 83,3 % |
| Sucursal Centro | Tiempo insuficiente | 1 | 1 | 16,7 % |
| Sucursal Oriente | Sala sin acceso | 5 | 5 | 83,3 % |
| Sucursal Oriente | Tiempo insuficiente | 1 | 1 | 16,7 % |
| Sucursal Norte | Tiempo insuficiente | 1 | 1 | 100 % |
| Sucursal Poniente | Tiempo insuficiente | 1 | 1 | 100 % |

### Interpretación

Con el papel, un tablero no intervenido simplemente no aparecía: quedaba un
casillero en blanco que nadie podía interpretar después. El sistema obliga a
declarar el motivo desde una lista cerrada, y eso convierte el silencio en
información que se puede agregar.

La lectura es directa y cada motivo apunta a una decisión distinta:

- **Sala sin acceso** concentrado en un local es un problema de coordinación.
  Se resuelve avisando al encargado antes de ir.
- **Equipo en operación** concentrado en un local es un problema contractual.
  Se resuelve negociando una ventana de desenergización.
- **Tiempo insuficiente** repartido entre locales es un problema de
  planificación de rutas. Se resuelve asignando menos locales por jornada.
- **Falta de material** sería un problema de bodega, y conecta con la
  manifestación P6 del diagnóstico. No aparece en este período.

En estos datos, el 83 % de los pendientes de Centro y de Oriente se explican
por una sola causa cada uno, y esa causa es la misma todos los ciclos. Son dos
conversaciones puntuales con el cliente, no un problema sistémico de la
cuadrilla.

---

## 5 · Puntos de la pauta que más veces resultan no conformes

**¿Qué componentes fallan más seguido, y en qué locales se concentran?**

| Código | Ítem | No conformes | % | Locales afectados |
|---|---|---|---|---|
| 2.2 | Se realiza limpieza de sala eléctrica | 3 | 13,0 % | 3 |
| 4.6 | Se realiza reapriete de borneras | 11 | 10,5 % | 4 |
| 3.3 | Se revisa estado de interruptores tripolares | 11 | 10,5 % | 4 |
| 5.1 | Se realiza medición de baterías | 2 | 8,7 % | 2 |
| 5.5 | Se revisa TTA del grupo operativo | 2 | 8,7 % | 1 |

La consulta completa devuelve 23 filas.

### Interpretación

El sistema no registra solamente que la pauta se cumplió: registra el resultado
de **cada punto por separado**, y eso permite agregar algo que el papel nunca
permitió.

Los dos ítems con más no conformidades —reapriete de borneras y estado de
interruptores tripolares— aparecen en los cuatro locales. Que el problema esté
repartido y no concentrado sugiere desgaste normal de componentes y no una
falla puntual de instalación. Si en cambio el mismo ítem se concentrara en un
local, eso no sería un problema de la cuadrilla sino de la instalación de ese
local, y convendría plantearlo al cliente **antes** de que algo falle. Esa
distinción es la que habilita la detección temprana de la manifestación P5 del
diagnóstico.

### El control de calidad del propio registro

La consulta devuelve además la columna `sin_evidencia`: ítems declarados como
ejecutados que no tienen fotografía vinculada.

**El resultado es cero en los 25 ítems, sobre 1.805 respuestas.**

Eso no es casualidad ni buena voluntad de los técnicos: el sistema no permite
sellar un tablero con ítems marcados «Sí» sin evidencia que los respalde
(RF-03). Esta columna es la verificación de que la regla se sostiene sobre
todos los datos, y no sólo en el caso que se muestra en la demostración. Si
alguna vez diera distinta de cero, significaría que la regla se rompió por
algún camino y habría que buscar por dónde.

---

## 6 · Materiales por comprar antes de la próxima visita

**¿Qué hay que comprar, para qué local, y qué está deteniendo un tablero?**

| Local | Material | Cant. | Veces pedido | Bloquea | Acción |
|---|---|---|---|---|---|
| Sucursal Centro | Barra de tierra de cobre 1 m | 1 | 1 | 1 | Comprar ahora: hay un tablero detenido (TD-0406) |
| Sucursal Norte | Automático diferencial 2x25A | 1 | 1 | 1 | Comprar ahora: hay un tablero detenido (TD-0103) |
| Sucursal Oriente | Automático diferencial 2x25A | 1 | 1 | 1 | Comprar ahora: hay un tablero detenido (TD-0202) |
| Sucursal Poniente | Automático diferencial 2x25A | 1 | 1 | 1 | Comprar ahora: hay un tablero detenido (TD-0301) |
| **Sucursal Oriente** | **Prensaestopa PG-16** | **12** | **3** | 0 | **Se repite: subir al stock permanente de la camioneta** |
| Sucursal Centro | Cinta aislante de goma autofundente | 4 | 2 | 0 | Se repite: subir al stock permanente de la camioneta |
| … | | | | | |

La consulta completa devuelve 12 filas.

### Interpretación

Ésta es la consulta que convierte el RF-11 en algo útil. Que el técnico
registre el faltante no evita por sí solo el re-trabajo: lo evita que
abastecimiento vea la lista agrupada **antes** de volver al local.

La columna `accion` tiene tres valores y cada uno pide una decisión distinta.

**«Comprar ahora»** es un material que dejó un tablero sin poder mantenerse. La
cobertura del ciclo siguiente depende de esa compra, de modo que no es una
reposición de rutina sino una condición para cumplir el contrato. Son cuatro, y
cada una tiene nombre de tablero.

**«Se repite»** es el hallazgo que el checklist en papel nunca pudo mostrar,
porque cada hoja se miraba sola. La prensaestopa PG-16 faltó **tres veces en
Sucursal Oriente**, en los ciclos 1, 3 y 5. Eso no es un olvido puntual: es un
error de stock permanente de la camioneta. La decisión correcta no es comprarla
una cuarta vez, es subirla al inventario base. Un sistema que sólo listara
faltantes diría «comprar 4 prensaestopas» otra vez; agrupar por local y contar
las veces es lo que convierte el registro en una decisión.

**«Reponer antes del próximo ciclo»** es consumo corriente y no necesita que
nadie decida nada.

### Relación con la consulta 2

Es directa, y conviene decirla en la defensa. La consulta 2 dice **qué tablero
está detenido**; ésta dice **qué hay que comprar para soltarlo**. Un tablero
que acumula ciclos sin intervención por falta de material aparece acá con
nombre, cantidad y unidad, listo para una orden de compra.

Ésa es la manifestación P6 del diagnóstico —re-trabajo en abastecimiento— y el
RF-11 era el único requisito que la atacaba.

---

## Nota sobre respuestas corregidas

La consulta 5 considera sólo las **respuestas vigentes**: una respuesta
corregida sigue en la tabla, encadenada a la original por `corrige_a_id`, pero
no se cuenta dos veces. El filtro es:

```sql
WHERE NOT EXISTS (
    SELECT 1 FROM registro_item c WHERE c.corrige_a_id = ri.id
)
```

Que el historial completo siga disponible **y** que los indicadores no se
distorsionen por él es justamente lo que permite el diseño append-only descrito
en [`03-modelo-datos.md`](03-modelo-datos.md).
