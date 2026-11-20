# Cómo se instala el SIG de IMELSE, explicado

**Versión 1 · 24 de octubre de 2026**

Esta versión corresponde a un proyecto que necesita cuatro bibliotecas: Django,
Pillow, reportlab y openpyxl.

> Si el sistema incorpora bibliotecas nuevas o cambian los comandos de carga,
> este documento queda desactualizado y hay que regenerarlo antes de producir
> el video final.

Este documento explica el proceso de instalación del prototipo del sistema de
información de IMELSE. No es una lista de comandos: es una explicación de qué
hace cada paso, por qué hace falta, y cómo darse cuenta de que salió bien.

Está escrito para alguien que nunca ha programado. Los comandos aparecen, pero
siempre acompañados de qué significan.

---

## 1. Qué vamos a hacer, en términos generales

El sistema es una aplicación web. Eso quiere decir que no se instala en cada
teléfono ni en cada computador de la oficina. Se instala **una sola vez en un
computador**, que pasa a hacer de servidor, y todos los demás entran con su
navegador escribiendo una dirección.

Instalarlo consiste en cuatro cosas, en este orden:

**Primero**, instalar el lenguaje en que el sistema está escrito, que se llama
Python. Es el único programa que hay que descargar.

**Segundo**, poner la carpeta del proyecto en algún lugar del computador y
situarse ahí con una herramienta llamada terminal.

**Tercero**, descargar las cuatro bibliotecas que el sistema necesita y crear la
base de datos, que son unos pocos comandos.

**Cuarto**, encender el sistema y comprobar que se ve, primero desde el mismo
computador y después desde un teléfono.

La primera vez toma unos veinte minutos. De la segunda en adelante, encenderlo
son dos líneas y cinco segundos.

Nada de esto modifica el computador de forma permanente ni instala cosas
repartidas por todos lados. Salvo Python, que es un programa normal, todo lo
demás vive dentro de la carpeta del proyecto. Borrar esa carpeta deja el
computador como estaba.

---

## 2. Los cuatro conceptos que conviene entender antes

Casi todos los problemas de instalación vienen de no tener claros estos cuatro
conceptos. Vale la pena detenerse.

### Qué es Python y qué es el PATH

Python es el lenguaje en que está escrito el sistema. Instalarlo es como
instalar cualquier programa: se descarga y se ejecuta el instalador.

Hay un detalle que causa más problemas que todos los demás juntos. Durante la
instalación en Windows aparece, abajo del todo de la primera pantalla, una
casilla pequeña que dice **"Add python.exe to PATH"**. El PATH es la lista de
lugares donde el computador busca los programas cuando uno escribe su nombre.
Si esa casilla no se marca, Python queda instalado pero el computador no sabe
dónde encontrarlo, y todo lo que sigue falla con un mensaje que dice que
"python no se reconoce como un comando".

Si se olvidó, no hay que desinstalar nada: se abre el mismo instalador otra
vez, se elige la opción "Modify" y se marca ahí.

### Qué es la terminal y por qué importa dónde está parada

La terminal es una ventana donde se escriben órdenes en texto en lugar de hacer
clic. Se ve austera, pero no tiene nada de misterioso.

Lo esencial es entender que **la terminal siempre está parada dentro de una
carpeta**, y que las órdenes que uno escribe actúan sobre esa carpeta. Si la
terminal está parada en el escritorio y uno pide abrir un archivo que está en
otro lugar, no lo va a encontrar.

La terminal dice dónde está parada en el texto que aparece a la izquierda,
antes de donde uno escribe. Si ese texto dice `C:\>` está parada en la raíz del
disco, que es el lugar equivocado. Si dice
`C:\Users\nombre\Desktop\sig-imelse>` está dentro del proyecto, que es el lugar
correcto.

Este es el error más común de toda la instalación: correr los comandos sin
estar parado en la carpeta del proyecto. Y es traicionero, porque algunos
comandos no dan error de inmediato: simplemente crean las cosas en el lugar
equivocado y el problema aparece tres pasos después.

Hay un truco en Windows que evita el problema por completo. Se abre la carpeta
del proyecto en el explorador normal, se hace clic en la barra de direcciones de
arriba donde aparece la ruta, se escribe `cmd` encima y se aprieta Enter. Se
abre una terminal ya parada exactamente ahí, sin escribir ninguna ruta a mano.
En macOS el equivalente es escribir `cd`, un espacio, y arrastrar la carpeta
encima de la ventana de la Terminal.

### Qué es un entorno virtual y por qué hay que activarlo

Un entorno virtual es una carpeta donde viven las bibliotecas de un proyecto y
de ningún otro. Sirve para que instalar este sistema no interfiera con
cualquier otra cosa que use Python en el mismo computador.

Se crea una sola vez, con un comando. Pero hay que **activarlo cada vez que se
abre una terminal nueva**. Activarlo es decirle a esa ventana concreta que use
las bibliotecas de esta carpeta.

La señal de que está activado es que la línea de la terminal pasa a empezar con
`(.venv)` entre paréntesis. Ese paréntesis es el único indicador: el comando de
activación no dice nada más.

Este es el segundo error más frecuente. Si se saltó la activación, el comando
siguiente responde que "pip no se reconoce", lo que parece un problema distinto
pero es exactamente éste disfrazado.

### Qué significa que el servidor "esté corriendo"

Cuando se enciende el sistema, la terminal muestra unas líneas que terminan en
"Starting development server" y **deja de devolver la línea de comandos**. Se
queda ahí, aparentemente pegada.

Eso es lo correcto, no un error. Significa que el servidor está vivo y
escuchando. Esa ventana tiene que quedarse abierta mientras se use el sistema.
Si se cierra o se aprieta Control más C, el sistema se apaga y nadie puede
entrar.

Mucha gente, al ver que la terminal "no responde", aprieta Control más C
creyendo que se colgó, y apaga justo lo que acaba de encender.

---

## 3. Las cinco etapas, explicadas

### Etapa uno: instalar Python

Se descarga desde el sitio oficial de Python y se ejecuta el instalador. En
Windows, marcando la casilla del PATH antes de continuar. En macOS, con las
opciones por defecto, y después haciendo doble clic en el archivo de
certificados que el instalador deja en una carpeta, porque sin eso la descarga
de bibliotecas de la etapa tres falla.

Para comprobar que quedó bien, se abre una terminal y se escribe
`python --version` en Windows, o `python3 --version` en macOS. Tiene que
responder con un número que empiece en tres punto doce o superior.

Si responde con el número de versión, se puede seguir. Si dice que no reconoce
el comando, Python no quedó en el PATH y no tiene sentido continuar hasta
arreglarlo.

### Etapa dos: poner el proyecto en su lugar

Se descomprime el archivo del proyecto y se deja la carpeta resultante en un
lugar simple, por ejemplo el escritorio.

Conviene abrir la carpeta y confirmar con los ojos que adentro hay un archivo
llamado `manage.py` y una carpeta llamada `core`. En Windows a veces la
descompresión deja una carpeta dentro de otra con el mismo nombre; la que
importa es la que contiene `manage.py`.

Después se abre la terminal dentro de esa carpeta, con el truco descrito más
arriba, y se confirma escribiendo `dir` en Windows o `ls` en macOS. En la lista
que aparece tiene que estar `manage.py`. Si en cambio aparecen cosas como
"Program Files" o "Windows", la terminal está en la raíz del disco y hay que
volver atrás.

Esta comprobación parece trivial y es la que evita el error más común.

### Etapa tres: crear el entorno e instalar las bibliotecas

Son tres comandos seguidos.

El primero crea el entorno virtual. En Windows se escribe
`python -m venv .venv`, en macOS `python3 -m venv .venv`. Demora unos segundos
y no dice nada al terminar: simplemente devuelve la línea. Eso es correcto.

El segundo lo activa. En Windows es `.venv\Scripts\activate`, en macOS
`source .venv/bin/activate`. Tampoco dice nada, pero la línea pasa a empezar con
`(.venv)`. **Si ese paréntesis no aparece, no hay que seguir.**

El tercero descarga las bibliotecas: `pip install -r requirements.txt`. Este
necesita internet y demora entre veinte segundos y un minuto. Tiene que
terminar con un mensaje que diga "Successfully installed" seguido de los
nombres. Son cuatro: Django, que es el marco de trabajo web; Pillow, que
procesa las fotografías; reportlab, que arma el informe en PDF; y openpyxl, que
genera la planilla anual de Excel.

Si en el camino aparece un aviso amarillo sugiriendo actualizar pip, es un
aviso y no un error. Se ignora.

### Etapa cuatro: crear la base de datos y cargar la demostración

Son dos comandos.

El primero, `python manage.py migrate`, crea las tablas de la base de datos. No
hay que instalar ninguna base de datos aparte: el prototipo usa una que vive
dentro de un solo archivo y que viene incluida en Python. Van a salir unas
veinticinco líneas, todas terminadas en "OK".

El segundo, `python manage.py cargar_demo`, deja el sistema con contenido para
mostrar en lugar de vacío. Carga los veinticinco ítems reales de la pauta de
IMELSE, más cuatro locales ficticios con sus tableros, ocho visitas en
distintos estados de avance, y fotografías de ejemplo generadas
automáticamente. Al terminar imprime la lista de usuarios de prueba, que
conviene anotar.

Si en algún momento se quiere empezar de cero, se borra el archivo de base de
datos y la carpeta de imágenes, y se repiten estos dos comandos. El código no
se toca.

### Etapa cinco: encender y comprobar

El comando para encender es
`python manage.py runserver 0.0.0.0:8000`.

Esa parte final, los ceros y el número ocho mil, no es opcional y conviene
entender por qué. Sin ella, el sistema sólo se deja ver desde el mismo
computador donde corre, y los teléfonos nunca van a poder entrar aunque todo lo
demás esté perfecto. Los ceros son los que lo abren a la red local.

Lo primero que hay que probar es desde el mismo computador, en la dirección
`http://127.0.0.1:8000`. Esa dirección significa "este mismo equipo".

Esta prueba importa por una razón de método: **separa el problema en dos
mitades**. Si esa dirección carga, el sistema está bien instalado, y cualquier
cosa que falle después es un asunto de red o de cortafuegos, no de instalación.
Si no carga, el problema está en los pasos anteriores. Saber en cuál de las dos
mitades está el problema reduce a la mitad lo que hay que revisar.

---

## 4. Cómo entrar desde el teléfono

Esta parte merece explicación porque es la que más confusión genera.

El computador hace de servidor y el teléfono se conecta a él. Para eso tienen
que **estar los dos en la misma red Wi-Fi**. Los datos móviles no sirven: el
teléfono estaría en otra red y no tendría forma de llegar.

Cada equipo conectado a una red tiene un número que lo identifica dentro de
ella, parecido a un número de casa dentro de una calle. Hay que averiguar el del
computador, lo que se hace escribiendo `ipconfig` en Windows en una terminal
aparte, o `ipconfig getifaddr en0` en macOS. El número tiene la forma de cuatro
grupos separados por puntos, algo como ciento noventa y dos punto ciento sesenta
y ocho punto tres punto sesenta y dos.

En el teléfono se escribe ese número en el navegador, precedido de `http://` y
seguido de dos puntos y el ocho mil. Las dos cosas son necesarias: sin el
`http://` el navegador puede interpretarlo como una búsqueda, y sin el ocho mil
va a buscar en otro lugar donde no hay nada escuchando, lo que produce un error
de conexión rechazada.

La primera vez, Windows va a mostrar una ventana del cortafuegos pidiendo
permiso para que Python acepte conexiones. Hay que **autorizarlo en redes
privadas**. Si esa ventana se cierra o se rechaza, el teléfono nunca va a poder
conectarse, y además el aviso no vuelve a aparecer, de modo que hay que
habilitarlo a mano en la configuración.

Una vez que la página carga en el teléfono, se puede guardar en la pantalla de
inicio para que quede con su propio ícono y abra a pantalla completa. En Chrome
es el menú de tres puntos y la opción de agregar a pantalla principal; en
iPhone, el botón de compartir y la opción de agregar a inicio. No se descarga
nada de ninguna tienda de aplicaciones: es la misma página guardada como acceso
directo.

Un detalle sobre el número del computador: lo asigna el router y puede cambiar
si el equipo se reinicia o se conecta a otra red. Si un día los teléfonos dejan
de entrar, lo primero es volver a averiguarlo. Para fijarlo de forma permanente
se reserva en la configuración del router, pero para probar no hace falta.

---

## 5. Los errores habituales y qué significan de verdad

Más útil que la receta es entender la causa, porque la misma causa aparece
disfrazada de distintas formas.

**"pip no se reconoce como un comando."** El entorno virtual no está activado.
Se reconoce porque la línea de la terminal no empieza con `(.venv)`. Es, con
diferencia, el error más frecuente de toda la instalación.

**"python no se reconoce como un comando."** Python no quedó en el PATH al
instalarse. Se arregla volviendo a abrir el instalador y eligiendo modificar la
instalación. Después hay que cerrar y volver a abrir la terminal, porque el
cambio no afecta a las ventanas que ya estaban abiertas.

**"No such file or directory: manage.py."** La terminal no está parada en la
carpeta del proyecto. Es el error de ubicación, y se confirma listando el
contenido de la carpeta.

**"La ejecución de scripts está deshabilitada en este sistema."** Aparece sólo
al activar el entorno desde PowerShell, que es una terminal distinta y más
restrictiva. Lo más simple es usar la terminal clásica en lugar de PowerShell.

**"No module named django."** Otra vez el entorno sin activar, o la descarga de
bibliotecas que no llegó a terminar.

**"That port is already in use."** Quedó otro servidor corriendo en otra
ventana. O se cierra esa ventana, o se usa otro número de puerto.

**"ERR_CONNECTION_REFUSED" en el navegador.** Significa que algo respondió
"aquí no hay nada" en esa dirección. Tres causas en orden de probabilidad: falta
el `:8000` al final de la dirección, la terminal del servidor se cerró, o se
encendió sin la parte de los ceros que lo abre a la red.

**Funciona en el computador pero el teléfono no entra.** El sistema está bien:
el problema es de red. Hay que revisar que se haya encendido con los ceros, que
el teléfono esté en la misma Wi-Fi y no en datos móviles, que se haya aceptado
el permiso del cortafuegos, y que el número del computador siga siendo el mismo.
Algunas redes de invitados aíslan los equipos entre sí y en ese caso no hay
forma de que funcione: hay que usar otra red.

**El sistema rechaza una fotografía diciendo que es muy antigua.** Esto no es un
error de instalación: es el sistema funcionando como debe. No acepta imágenes
con más de quince minutos para que la evidencia sea del momento y no se adjunte
después desde la galería.

---

## 6. Qué pasa después de la primera vez

Las etapas tres y cuatro no se repiten nunca más, salvo que se quiera empezar de
cero. Para encender el sistema en los días siguientes bastan dos líneas: activar
el entorno y levantar el servidor, siempre con la terminal parada dentro de la
carpeta del proyecto.

Vale la pena mencionar dos cosas opcionales.

La primera es que existe la posibilidad de obtener una dirección pública y
segura mediante lo que se llama un túnel, que permite entrar al sistema desde
cualquier parte sin estar en la misma red. Es útil para probar con datos
móviles, para compartir el acceso con otras personas, o para presentar en una
sala cuya red aísle los equipos. Tiene además la ventaja de que, al ser una
conexión segura, se activa el guardado de pantallas sin conexión que los
navegadores reservan para ese tipo de direcciones.

La segunda es el cambio de motor de base de datos. El prototipo corre sobre
SQLite para poder reproducirse sin instalar nada, pero el motor declarado para
la operación real es PostgreSQL en su versión dieciséis punto cuatro. El cambio
se hace con una variable de configuración, sin tocar el código: es
deliberadamente así de simple porque el sistema está construido sobre una capa
que traduce entre el código y la base de datos, de modo que el mismo programa
funciona sobre cualquiera de los dos motores.

---

## 7. Resumen de los comandos

Para referencia, la secuencia completa en Windows, con la terminal ya parada
dentro de la carpeta del proyecto:

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py cargar_demo
python manage.py runserver 0.0.0.0:8000
```

En macOS, los mismos con dos diferencias: `python3` en lugar de `python`, y
`source .venv/bin/activate` en lugar de la segunda línea.

Y para los días siguientes, sólo las dos últimas:

```
.venv\Scripts\activate
python manage.py runserver 0.0.0.0:8000
```

Los usuarios de prueba son `tecnico`, `admin`, `gerencia` y `dual`, todos con
la misma contraseña, que el comando de carga de demostración imprime al
terminar.
