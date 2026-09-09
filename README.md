# SIG para IMELSE — ICN-292, Entrega 1

**Universidad Técnica Federico Santa Maria — Departamento de Industrias**
Sistemas de Información para la Gestion · Paralelo 100 · 2026-2
Profesores: Jose Miguel Gonzalez Paul · Jose Luis Saez Tamayo

## 1. Qué PYME y qué problema

**IMELSE** es una empresa de servicios de mantenimiento eléctrico industrial
ubicada en Av. General Saavedra 1217, Independencia, Región Metropolitana.
Presta servicios de mantención preventiva y correctiva a tableros eléctricos,
termografáa, bancos de condensadores, sistemas fotovoltaicos y mediciones de
calidad de energia, a clientes del retail como Unimarc, Santa Isabel y Mall Vivo.

**Problema:** Cerca de un 17% de las mantenciones preventivas resultan incompletas sin la detección de potenciales problemas de forma oportuna, ya que el cumplimiento se declara en un checklist en hojas de papel sin evidencia verificable por el tablero que luego llegan a la oficina dentro de 16 a 24 horas en promedio. El resultado de esto es que las fallas por no mantención aumentan y la empresa debe llevar a cabo visitas de emergencia que deben ser cubiertas por la misma. Dentro de los principales artículos donde ocurre es en los tableros eléctricos que pueden pasar uno o más ciclos bimensuales sin revisión, ocasionando una falla eléctrica que debe ser cubierta por un contrato que cuenta con un seguro de 27.500 UF.

**Objetivo del SIG:** Reemplazar el registro en papel por un registro digital, guiado y evidenciado que se genera durante la ejecución, de modo que la gerencia pueda verificar la cobertura de tableros de cada visita antes de su cierre junto a las debidas y necesarias pruebas que respalden esto.

Detalle completo y evidencia en [`docs/00-caso-pyme.md`](docs/00-caso-pyme.md).

## 2. Contenido del repositorio

| Ruta | Contenido |
|---|---|
| [`docs/00-caso-pyme.md`](docs/00-caso-pyme.md) | Identificacion de IMELSE, evidencia verificable y problema medible |
| [`docs/01-requerimientos.md`](docs/01-requerimientos.md) | Actores, alcance in/out, RF y RNF priorizados con MoSCoW y trazabilidad |
| [`docs/02-bpmn.md`](docs/02-bpmn.md) | Procesos as-is y to-be en BPMN 2.0 y explicacion de mejoras |
| [`docs/03-er-preliminar.md`](docs/03-er-preliminar.md) | Modelo entidad-relacion y trazabilidad proceso-datos |
| [`assets/`](assets/) | Diagramas exportados y evidencia fotografica numerada |
| [`informe/`](informe/) | Informe en PDF y Word/LaTeX |

## 3. Relacion con la Entrega 2

En la Entrega 2 se implementará un prototipo funcional en **localhost** con el
stack [POR DEFINIR], que operará sobre el modelo de datos descrito en
`docs/03-er-preliminar.md` y medira los KPI definidos en `docs/00-caso-pyme.md`.
Este mismo repositorio continuara siendo el unico del proyecto.

## 4. Integrantes y roles

| Nombre | RUT | Rol |
|---|---|---|
| Javier Bravo | 21330540-9 | 202360638-3 |
| Benjamín Eliz | 21803009-2 | 202360632-4 |
| Cristóbal Muñoz | 21657535-0 | 202360603-0 |
| Nicolás Oyarzún | 21762466-5 | 202404599-7 |
| Nicolás Soto | 22083026-8 | 202460585-2 |

## 5. Entrega

- Informe en PDF y Word/LaTeX: carpeta [`informe/`](informe/)
- Los mismos archivos fueron subidos a Aula USM junto a `ENLACE_GITHUB.txt`
- Cierre: sabado 12 de septiembre de 2026, 12:30
