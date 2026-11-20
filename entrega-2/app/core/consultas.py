"""Ejecución de las consultas de negocio desde la aplicación.

Los archivos de `db/consultas/` son los mismos que el docente corre con psql:
no hay una copia dentro del código que pueda quedar desincronizada. Editar el
.sql cambia lo que esta pantalla muestra, y al revés, lo que se ve acá es
exactamente lo que devuelve el motor.

Eso importa para la defensa. El enunciado prohíbe «inventar resultados que la
base no pueda reproducir», y la forma más corta de demostrar que no se inventó
nada es ejecutar la consulta delante de quien pregunta.
"""

import re
from pathlib import Path

from django.conf import settings
from django.db import connection

def _carpeta_consultas():
    """Dónde están los .sql que esta pantalla ejecuta.

    Dentro del repositorio la aplicación vive en `app/` y las consultas están en
    `db/consultas/` de la raíz, una carpeta más arriba. Fuera del repositorio,
    con la aplicación suelta, están en su propio `db/consultas/`.

    Se busca primero la de la raíz para que no existan dos copias del SQL. El
    README afirma que la pantalla ejecuta los mismos archivos que se entregan, y
    eso tiene que ser literalmente cierto: si hubiera una copia dentro de la
    aplicación, editar una consulta del repositorio no cambiaría lo que la
    pantalla muestra, y la afirmación sería falsa sin que nadie lo notara.
    """
    base = Path(settings.BASE_DIR)
    for candidata in (base.parent / "db" / "consultas", base / "db" / "consultas"):
        if candidata.is_dir():
            return candidata
    return base / "db" / "consultas"


CARPETA = _carpeta_consultas()

# Sólo lectura. Los archivos son nuestros, pero una pantalla que ejecuta SQL
# tiene que negarse a ejecutar cualquier cosa que no sea una consulta, aunque
# el archivo venga de donde venga.
PERMITIDO = re.compile(r"^\s*(WITH|SELECT)\b", re.IGNORECASE)
PROHIBIDO = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|GRANT|REVOKE|CREATE|COPY)\b",
    re.IGNORECASE,
)


def _sin_comentarios(sql):
    return re.sub(r"--[^\n]*", "", sql)


def leer_consultas():
    """Devuelve las consultas disponibles, con su encabezado interpretado."""
    consultas = []
    if not CARPETA.is_dir():
        return consultas

    for ruta in sorted(CARPETA.glob("*.sql")):
        texto = ruta.read_text(encoding="utf-8")
        consultas.append({
            "slug": ruta.stem,
            "archivo": f"db/consultas/{ruta.name}",
            "titulo": _campo(texto, "titulo") or ruta.stem,
            "pregunta": _campo(texto, "pregunta"),
            "interpretacion": _campo(texto, "interpretacion", multilinea=True),
            "sql": _cuerpo(texto),
        })
    return consultas


def _campo(texto, nombre, multilinea=False):
    """Lee una anotación `-- @nombre: ...` del encabezado del archivo."""
    patron = rf"--\s*@{nombre}:\s*(.*)"
    m = re.search(patron, texto)
    if not m:
        return ""
    valor = m.group(1).strip()
    if not multilinea:
        return valor
    # Las líneas siguientes que empiezan con "--" y van indentadas continúan.
    lineas = [valor]
    for linea in texto[m.end():].split("\n"):
        cont = re.match(r"--\s{2,}(\S.*)", linea)
        if not cont:
            break
        lineas.append(cont.group(1).strip())
    return " ".join(lineas)


def _cuerpo(texto):
    """El SQL sin el encabezado de anotaciones."""
    lineas = [l for l in texto.split("\n") if not l.strip().startswith("--")]
    return "\n".join(lineas).strip()


def ejecutar(consulta, limite=200):
    """Corre la consulta y devuelve (columnas, filas, error)."""
    sql = consulta["sql"]
    cuerpo = _sin_comentarios(sql)
    if not PERMITIDO.match(cuerpo) or PROHIBIDO.search(cuerpo):
        return [], [], "La consulta no es de sólo lectura y no se ejecutó."

    try:
        with connection.cursor() as cur:
            cur.execute(sql.rstrip().rstrip(";"))
            columnas = [c[0] for c in cur.description]
            filas = cur.fetchmany(limite)
    except Exception as e:  # el motor explica mejor que nosotros qué pasó
        return [], [], str(e).strip().split("\n")[0]
    return columnas, [list(f) for f in filas], None
