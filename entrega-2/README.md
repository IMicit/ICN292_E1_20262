# SIG de trazabilidad de mantención preventiva — IMELSE SpA

**ICN-292 Sistemas de Información para la Gestión** · Universidad Técnica
Federico Santa María · Campus Vitacura · 2026-2 · **Paralelo 100 · Grupo 5** ·
Entrega 2

Sistema de información para la trazabilidad de la mantención preventiva de
tableros eléctricos en locales de retail. Reemplaza el checklist en papel por
un registro digital, guiado y evidenciado, que se genera durante la ejecución
de la visita.

---

## Prueba de oro: de cero a las consultas corriendo

Estos son todos los pasos. Si alguno falla en un entorno limpio, es un defecto
nuestro y no del lector.

**Requisito único: PostgreSQL 16.**

```bash
git clone https://github.com/IMicit/ICN292_E1_20262.git
cd ICN292_E1_20262/entrega-2

createdb sig_imelse
psql -d sig_imelse -f db/schema.sql
psql -d sig_imelse -f db/seed.sql

psql -d sig_imelse -f db/consultas/01-cobertura-por-local-y-ciclo.sql
```

Si ese último comando devuelve 24 filas con la cobertura por local y ciclo, el
entorno está correcto.

### Las seis consultas de negocio

```bash
for f in db/consultas/*.sql; do psql -d sig_imelse -f "$f"; done
```

| Archivo | Pregunta que responde |
|---|---|
| `01-cobertura-por-local-y-ciclo.sql` | De los tableros que había que revisar, ¿cuántos se revisaron? |
| `02-tableros-sin-intervencion.sql` | ¿Qué tableros llevan más tiempo sin que nadie los revise, y por qué? |
| `03-latencia-del-registro.sql` | ¿Cuánto demora en llegar a la oficina lo que se hizo en terreno? |
| `04-motivos-de-pendiente.sql` | ¿Qué impide completar las visitas? |
| `05-items-que-mas-fallan.sql` | ¿Qué componentes fallan más seguido y dónde? |
| `06-materiales-por-comprar.sql` | ¿Qué hay que comprar, para qué local, y qué tablero está detenido? |

Los resultados están interpretados en
[`docs/04-sql-consultas.md`](docs/04-sql-consultas.md).

---

## Levantar también la aplicación (opcional)

La misma base sirve para las dos cosas. El esquema incluye un apéndice con las
tablas de infraestructura que el framework necesita, de modo que no hace falta
crear una segunda base.

```bash
cd app
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL="postgresql://usuario:clave@localhost:5432/sig_imelse"
python manage.py runserver
```

Abrir <http://127.0.0.1:8000/>. Usuarios de prueba, todos con la contraseña
`imelse2026`:

| Usuario | Perfil | Qué muestra |
|---|---|---|
| `tecnico` | Técnico | El registro en terreno: pauta, fotos, pendientes, cierre |
| `dual` | Técnico | El estudiante dual anexando observaciones sin tocar lo sellado |
| `admin` | Administración | Informes, evidencia y catálogo |
| `gerencia` | Gerencia | Panel de cumplimiento, planilla anual y consultas SQL |

La ruta `/consultas/` ejecuta **los mismos archivos de `db/consultas/`** contra
la base y muestra el resultado junto a su interpretación. No hay una copia del
SQL dentro del código.

Para levantar la aplicación sin PostgreSQL, usando SQLite, basta con no definir
`DATABASE_URL` y correr `python manage.py migrate && python manage.py cargar_demo`.
La guía de instalación completa, pensada para alguien que nunca ha programado,
está en [`docs/06-instalacion.md`](docs/06-instalacion.md).

---

## Documentación

| Documento | Contenido |
|---|---|
| [`docs/00-caso-pyme.md`](docs/00-caso-pyme.md) | La PYME, el problema y sus manifestaciones medidas |
| [`docs/01-requerimientos.md`](docs/01-requerimientos.md) | 18 RF y 10 RNF priorizados con MoSCoW |
| [`docs/02-bpmn.md`](docs/02-bpmn.md) | Proceso *as-is* y *to-be*, con los cambios respecto de la E1 |
| [`docs/03-modelo-datos.md`](docs/03-modelo-datos.md) | ER en 3FN, diccionario de datos y anomalías evitadas |
| [`docs/04-sql-consultas.md`](docs/04-sql-consultas.md) | Las seis consultas con sus resultados interpretados |
| [`docs/05-automatizacion-n8n.md`](docs/05-automatizacion-n8n.md) | El flujo de automatización y su trazabilidad al BPMN |
| [`docs/DECLARACION_IA.md`](docs/DECLARACION_IA.md) | Uso de inteligencia artificial en el desarrollo |
| [`CHANGELOG.md`](CHANGELOG.md) | Qué cambió entre la Entrega 1 y la Entrega 2 |

---

## Estructura del repositorio

```
db/
   schema.sql              Esquema PostgreSQL 16, 20 entidades, 92 restricciones
   seed.sql                Un año de operación: 24 visitas, 1.805 respuestas
   consultas/              Las seis consultas de negocio
docs/
   diagramas/              ER generado desde la base real (PNG, SVG, PDF)
   n8n/                    Flujo de automatización exportado
app/                       Prototipo Django 5 sobre PostgreSQL 16
informe/                   Informe de la Entrega 2 en PDF y LaTeX
presentacion/              Diapositivas de la defensa (PPTX o PDF)
assets/
   demo/                   Grabaciones del prototipo real corriendo (GIF)
   (resto)                 Diagramas BPMN y evidencia del levantamiento
```

---

## Stack y versiones exactas

| Componente | Versión |
|---|---|
| **PostgreSQL** | **16** |
| Python | 3.12 o superior |
| Django | 5.2.6 |
| Pillow | 11.3.0 |
| reportlab | 5.0.1 |
| openpyxl | 3.1.5 |
	n8n · 1.x, se levanta con npx n8n

---

## Qué hace el sistema

- **Checklist guiado tablero por tablero**, con los 25 ítems reales de la pauta
  de IMELSE transcritos de la ficha N° 002190 levantada en terreno: **15 de
  ámbito tablero**, que se responden una vez por cada tablero, y **10 de ámbito
  visita**, que se responden una vez para el local completo.
- **Ningún ítem se declara ejecutado sin fotografía vinculada.** La foto se
  toma con la cámara, no se adjunta desde la galería, y lleva el tablero, la
  fecha y la hora estampados dentro de la imagen.
- **Ningún registro cerrado se modifica ni se elimina**, por nadie. Las
  correcciones se encadenan al original y ambas quedan visibles.
- **Una visita no se cierra** mientras quede un tablero sin registro ni
  pendiente declarado con su motivo.
- **Opera sin conexión** durante la visita y sincroniza sola al recuperar
  señal.
- **Genera el informe en PDF y actualiza la planilla anual** al cerrar la
  visita, y la automatización lo despacha al cliente.
- **Registra lo que faltó en terreno** y lo agrupa por local, de modo que
  abastecimiento compre antes de que la cuadrilla vuelva sin el repuesto.

---

## Equipo

| Integrante | Responsabilidad en la Entrega 2 |
|---|---|
| Javier Bravo Campos | Modelo de datos y documentación técnica |
| Benjamín Eliz | Diseño SQL y consultas de negocio |
| Nicolás Oyarzún | BPMN final y automatización |
| Nicolás Soto | Presentación y coordinación |
| Cristóbal Muñoz | Informe y documentación |

---

## Datos personales

El prototipo opera **exclusivamente con datos ficticios**, en cumplimiento del
compromiso declarado respecto de la Ley 21.719, que entra en vigor el 1 de
diciembre de 2026. No contiene nombres reales de trabajadores de IMELSE, ni
códigos o direcciones reales de locales del cliente, ni fotografías tomadas en
instalaciones reales.

La única excepción es un dato verdadero y deliberado: los 25 ítems de la pauta,
transcritos literalmente de la ficha de chequeo que la empresa usa hoy en
papel. El sistema no inventó la pauta, la digitalizó.
