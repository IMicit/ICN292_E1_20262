"""Libro anual de control en Excel, con una hoja por mes (RF-12 ampliado).

Por qué se regenera en lugar de irse editando
---------------------------------------------
El libro **no es un registro**: es una vista derivada de lo que ya está en la
base de datos. Por eso se regenera completo cada vez en lugar de irse
modificando fila por fila. Si se editara a mano, el archivo y el sistema
dirían cosas distintas y volveríamos justo al problema del papel: dos fuentes
de verdad y ninguna confiable.

La distinción con el informe de visita es deliberada:

- `InformeVisita` (PDF) **es** evidencia: inmutable, versionado, con hash. Es
  el documento que se le mandó al cliente y tiene que poder recuperarse igual
  meses después.
- `LibroAnual` (Excel) es una **fotografía del estado actual**: se rehace
  entera cuando los datos cambian, y siempre refleja lo que el sistema sabe
  hoy.

Las celdas de cobertura y los totales van como **fórmulas**, no como números
calculados aquí, para que la gerencia pueda trabajar el archivo como una
planilla de verdad.
"""

from collections import defaultdict
from datetime import date

from django.core.files.base import ContentFile
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from .models import LibroAnual, RegistroTablero, Tablero, Visita

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

AZUL = "FF123A6B"
AZUL_CLARO = "FFE3ECF8"
GRIS = "FFEAEEF3"
VERDE = "FFE2F3E8"
AMBAR = "FFFDF0DC"
ROJO = "FFFBE3E3"

TITULO = Font(name="Calibri", size=14, bold=True, color=AZUL)
SUBTITULO = Font(name="Calibri", size=9, color="FF5B6672")
CABECERA = Font(name="Calibri", size=9, bold=True, color="FFFFFFFF")
NEGRITA = Font(name="Calibri", size=10, bold=True)
NORMAL = Font(name="Calibri", size=10)

RELLENO_CABECERA = PatternFill("solid", fgColor=AZUL)
RELLENO_TOTAL = PatternFill("solid", fgColor=GRIS)

BORDE = Border(*[Side(style="thin", color="FFD4DAE1")] * 4)
CENTRO = Alignment(horizontal="center", vertical="center")
IZQ = Alignment(horizontal="left", vertical="center", wrap_text=False)


def _cabecera(hoja, fila, columnas):
    """Escribe la fila de títulos y devuelve la fila siguiente."""
    for i, (titulo, ancho) in enumerate(columnas, start=1):
        celda = hoja.cell(row=fila, column=i, value=titulo)
        celda.font = CABECERA
        celda.fill = RELLENO_CABECERA
        celda.alignment = CENTRO
        celda.border = BORDE
        hoja.column_dimensions[get_column_letter(i)].width = ancho
    hoja.row_dimensions[fila].height = 26
    return fila + 1


def _titulo(hoja, texto, subtexto, ancho_cols):
    hoja["A1"] = texto
    hoja["A1"].font = TITULO
    hoja["A2"] = subtexto
    hoja["A2"].font = SUBTITULO
    hoja.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ancho_cols)
    hoja.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ancho_cols)
    hoja.row_dimensions[1].height = 22


def _semaforo(hoja, rango):
    """Pinta la columna de cobertura: verde al 100 %, ámbar parcial, rojo en cero."""
    hoja.conditional_formatting.add(rango, CellIsRule(
        operator="equal", formula=["1"], fill=PatternFill("solid", bgColor=VERDE)))
    # Un mes sin visitas programadas no es 0 % de cobertura: es "no aplica", y
    # la fórmula deja la celda vacía. Sólo se pinta de rojo un 0 % real.
    hoja.conditional_formatting.add(rango, CellIsRule(
        operator="equal", formula=["0"], fill=PatternFill("solid", bgColor=ROJO)))
    hoja.conditional_formatting.add(rango, CellIsRule(
        operator="between", formula=["0.0001", "0.9999"],
        fill=PatternFill("solid", bgColor=AMBAR)))


# ---------------------------------------------------------------------------
# Hojas
# ---------------------------------------------------------------------------

def _hoja_mes(libro, anio, mes, visitas):
    hoja = libro.create_sheet(f"{mes:02d} {MESES[mes - 1]}")
    columnas = [
        ("Fecha", 11), ("Local", 24), ("Comuna", 16), ("Ciclo", 10),
        ("Estado", 14), ("Cuadrilla", 28), ("Tableros", 10),
        ("Registrados", 12), ("Pendientes", 12), ("Cobertura", 11),
        ("Hallazgos", 11), ("Informe", 10),
    ]
    _titulo(hoja, f"{MESES[mes - 1]} {anio}",
            "Visitas de mantención preventiva del mes. La cobertura se calcula sola.",
            len(columnas))
    fila = _cabecera(hoja, 4, columnas)
    primera = fila

    for v in visitas:
        esperados = v.total_tableros
        registrados = v.total_registrados
        pendientes = v.pendientes.count()
        hallazgos = sum(r.hallazgos.count() for r in v.registros_tablero.all())
        cuadrilla = ", ".join(
            u.get_full_name() or u.username for u in v.cuadrilla.all()
        ) or "—"

        datos = [
            v.fecha, v.local.nombre, v.local.comuna, str(v.ciclo),
            v.get_estado_display(), cuadrilla, esperados, registrados, pendientes,
            None, hallazgos, "Sí" if v.informes.exists() else "—",
        ]
        for i, valor in enumerate(datos, start=1):
            celda = hoja.cell(row=fila, column=i, value=valor)
            celda.font = NORMAL
            celda.border = BORDE
            celda.alignment = CENTRO if i not in (2, 3, 6) else IZQ
        hoja.cell(row=fila, column=1).number_format = "DD-MM-YYYY"
        # Cobertura como fórmula: el archivo sigue siendo una planilla viva.
        cob = hoja.cell(row=fila, column=10,
                        value=f'=IF(G{fila}=0,"",H{fila}/G{fila})')
        cob.number_format = "0%"
        cob.font = NEGRITA
        cob.border = BORDE
        cob.alignment = CENTRO
        fila += 1

    if fila == primera:
        hoja.cell(row=fila, column=1, value="Sin visitas registradas en este mes.").font = SUBTITULO
        fila += 1
    else:
        ultima = fila - 1
        total = hoja.cell(row=fila, column=1, value="Total del mes")
        total.font = NEGRITA
        hoja.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=6)
        for col, letra in ((7, "G"), (8, "H"), (9, "I"), (11, "K")):
            c = hoja.cell(row=fila, column=col,
                          value=f"=SUM({letra}{primera}:{letra}{ultima})")
            c.font = NEGRITA
            c.alignment = CENTRO
        c = hoja.cell(row=fila, column=10, value=f'=IF(G{fila}=0,"",H{fila}/G{fila})')
        c.number_format = "0%"
        c.font = NEGRITA
        c.alignment = CENTRO
        for col in range(1, len(columnas) + 1):
            hoja.cell(row=fila, column=col).fill = RELLENO_TOTAL
            hoja.cell(row=fila, column=col).border = BORDE
        _semaforo(hoja, f"J{primera}:J{ultima}")

    hoja.freeze_panes = f"A{primera}"
    return hoja


def _hoja_resumen(libro, anio, por_mes):
    hoja = libro.create_sheet("Resumen", 0)
    columnas = [
        ("Mes", 14), ("Visitas", 10), ("Cerradas", 10), ("Tableros", 11),
        ("Registrados", 12), ("Pendientes", 12), ("Cobertura", 12),
        ("Visitas completas", 16), ("Hallazgos", 11),
    ]
    _titulo(hoja, f"Control de mantención preventiva {anio}",
            "IMELSE SpA · Resumen anual por mes. Cada mes tiene su propia hoja con el detalle.",
            len(columnas))
    fila = _cabecera(hoja, 4, columnas)
    primera = fila

    for mes in range(1, 13):
        visitas = por_mes.get(mes, [])
        esperados = sum(v.total_tableros for v in visitas)
        registrados = sum(v.total_registrados for v in visitas)
        pendientes = sum(v.pendientes.count() for v in visitas)
        cerradas = sum(1 for v in visitas if v.estado == Visita.Estado.CERRADA)
        completas = sum(
            1 for v in visitas if v.total_tableros and v.total_registrados == v.total_tableros
        )
        hallazgos = sum(
            r.hallazgos.count() for v in visitas for r in v.registros_tablero.all()
        )

        datos = [MESES[mes - 1], len(visitas), cerradas, esperados, registrados,
                 pendientes, None, completas, hallazgos]
        for i, valor in enumerate(datos, start=1):
            celda = hoja.cell(row=fila, column=i, value=valor)
            celda.font = NORMAL
            celda.border = BORDE
            celda.alignment = IZQ if i == 1 else CENTRO
        cob = hoja.cell(row=fila, column=7, value=f'=IF(D{fila}=0,"",E{fila}/D{fila})')
        cob.number_format = "0%"
        cob.font = NEGRITA
        cob.border = BORDE
        cob.alignment = CENTRO
        if visitas:
            hoja.cell(row=fila, column=1).hyperlink = f"#'{mes:02d} {MESES[mes - 1]}'!A4"
            hoja.cell(row=fila, column=1).font = Font(
                name="Calibri", size=10, color="FF1B5DA8", underline="single")
        fila += 1

    ultima = fila - 1
    hoja.cell(row=fila, column=1, value=f"Año {anio}").font = NEGRITA
    for col, letra in ((2, "B"), (3, "C"), (4, "D"), (5, "E"), (6, "F"), (8, "H"), (9, "I")):
        c = hoja.cell(row=fila, column=col, value=f"=SUM({letra}{primera}:{letra}{ultima})")
        c.font = NEGRITA
        c.alignment = CENTRO
    c = hoja.cell(row=fila, column=7, value=f'=IF(D{fila}=0,"",E{fila}/D{fila})')
    c.number_format = "0%"
    c.font = NEGRITA
    c.alignment = CENTRO
    for col in range(1, len(columnas) + 1):
        hoja.cell(row=fila, column=col).fill = RELLENO_TOTAL
        hoja.cell(row=fila, column=col).border = BORDE

    _semaforo(hoja, f"G{primera}:G{ultima}")
    hoja.freeze_panes = f"A{primera}"

    nota = fila + 2
    hoja.cell(row=nota, column=1,
              value="Cobertura = tableros con registro sellado ÷ tableros del levantamiento.").font = SUBTITULO
    hoja.cell(row=nota + 1, column=1,
              value="Una visita completa es aquella en que se intervino el 100 % de los tableros del local.").font = SUBTITULO
    hoja.merge_cells(start_row=nota, start_column=1, end_row=nota, end_column=9)
    hoja.merge_cells(start_row=nota + 1, start_column=1, end_row=nota + 1, end_column=9)
    return hoja


def _hoja_pendientes(libro, anio, visitas):
    hoja = libro.create_sheet("Pendientes")
    columnas = [
        ("Fecha", 11), ("Local", 24), ("Tablero", 13), ("Ubicación", 26),
        ("Motivo", 30), ("Detalle", 42), ("Declaró", 20),
    ]
    _titulo(hoja, f"Tableros no intervenidos · {anio}",
            "Cada uno con su motivo declarado. Esta es la lista que hay que arrastrar al ciclo siguiente.",
            len(columnas))
    fila = _cabecera(hoja, 4, columnas)
    primera = fila

    for v in visitas:
        for p in v.pendientes.select_related("tablero", "usuario"):
            datos = [v.fecha, v.local.nombre, p.tablero.codigo, p.tablero.ubicacion,
                     p.get_motivo_display(), p.comentario or "—",
                     p.usuario.get_full_name() or p.usuario.username]
            for i, valor in enumerate(datos, start=1):
                celda = hoja.cell(row=fila, column=i, value=valor)
                celda.font = NORMAL
                celda.border = BORDE
                celda.alignment = CENTRO if i in (1, 3) else IZQ
            hoja.cell(row=fila, column=1).number_format = "DD-MM-YYYY"
            fila += 1

    if fila == primera:
        hoja.cell(row=fila, column=1,
                  value="Ningún tablero quedó pendiente en el año.").font = SUBTITULO
    hoja.freeze_panes = f"A{primera}"
    hoja.auto_filter.ref = f"A{primera - 1}:G{max(fila - 1, primera)}"
    return hoja


def _hoja_tableros(libro, anio, visitas):
    """El control que hoy no existe: qué tablero pasó ciclos sin revisión."""
    hoja = libro.create_sheet("Tableros")
    columnas = [
        ("Local", 24), ("Tablero", 13), ("Ubicación", 26), ("Tipo", 20),
        ("Veces intervenido", 17), ("Última intervención", 18),
        ("Ciclos pendiente", 16), ("Estado", 24),
    ]
    _titulo(hoja, f"Seguimiento por tablero · {anio}",
            "Cuántas veces se intervino cada tablero en el año. Es el dato que el papel no permitía obtener.",
            len(columnas))
    fila = _cabecera(hoja, 4, columnas)
    primera = fila

    ids_visitas = [v.id for v in visitas]
    intervenciones = defaultdict(list)
    for r in (RegistroTablero.objects
              .filter(visita_id__in=ids_visitas, cerrado=True)
              .select_related("visita")):
        intervenciones[r.tablero_id].append(r.visita.fecha)

    pendientes_por_tablero = defaultdict(int)
    for v in visitas:
        for p in v.pendientes.all():
            pendientes_por_tablero[p.tablero_id] += 1

    for t in Tablero.objects.filter(activo=True).select_related("local").order_by(
            "local__nombre", "codigo"):
        fechas = sorted(intervenciones.get(t.id, []))
        n_pend = pendientes_por_tablero.get(t.id, 0)
        if not fechas and n_pend:
            estado = "Nunca intervenido en el año"
        elif not fechas:
            estado = "Sin visitas en el año"
        elif n_pend:
            estado = f"Intervenido, con {n_pend} ciclo(s) pendiente(s)"
        else:
            estado = "Al día"

        datos = [t.local.nombre, t.codigo, t.ubicacion, t.get_tipo_display(),
                 len(fechas), fechas[-1] if fechas else None, n_pend, estado]
        for i, valor in enumerate(datos, start=1):
            celda = hoja.cell(row=fila, column=i, value=valor)
            celda.font = NORMAL
            celda.border = BORDE
            celda.alignment = CENTRO if i in (2, 5, 6, 7) else IZQ
        hoja.cell(row=fila, column=6).number_format = "DD-MM-YYYY"
        if not fechas or n_pend:
            relleno = PatternFill("solid", fgColor=ROJO if not fechas else AMBAR)
            for i in range(1, len(columnas) + 1):
                hoja.cell(row=fila, column=i).fill = relleno
        fila += 1

    hoja.freeze_panes = f"A{primera}"
    if fila > primera:
        hoja.auto_filter.ref = f"A{primera - 1}:H{fila - 1}"
    return hoja


# ---------------------------------------------------------------------------
# Construcción y archivo
# ---------------------------------------------------------------------------

def construir_libro(anio):
    """Devuelve los bytes del archivo .xlsx del año."""
    visitas = list(
        Visita.objects.filter(fecha__year=anio)
        .select_related("local", "ciclo")
        .prefetch_related("cuadrilla", "pendientes__tablero", "pendientes__usuario",
                          "registros_tablero__hallazgos", "informes")
        .order_by("fecha")
    )
    por_mes = defaultdict(list)
    for v in visitas:
        por_mes[v.fecha.month].append(v)

    libro = Workbook()
    libro.remove(libro.active)

    for mes in range(1, 13):
        _hoja_mes(libro, anio, mes, por_mes.get(mes, []))
    _hoja_pendientes(libro, anio, visitas)
    _hoja_tableros(libro, anio, visitas)
    _hoja_resumen(libro, anio, por_mes)  # se inserta primera

    libro.active = 0
    libro.properties.title = f"Control de mantención preventiva {anio}"
    libro.properties.creator = "SIG IMELSE"

    from io import BytesIO
    buffer = BytesIO()
    libro.save(buffer)
    return buffer.getvalue(), len(visitas)


def actualizar_libro(anio, usuario=None):
    """Regenera el libro del año y lo deja guardado.

    Es la operación que corre sola al cerrar una visita, y también la que
    dispara el botón «Actualizar» de la pantalla de gerencia.
    """
    datos, n_visitas = construir_libro(anio)
    nombre = f"control-mantencion-{anio}.xlsx"

    libro, _ = LibroAnual.objects.get_or_create(anio=anio)
    if libro.archivo:
        libro.archivo.delete(save=False)  # el libro es una vista, no un registro
    libro.archivo.save(nombre, ContentFile(datos), save=False)
    libro.n_visitas = n_visitas
    libro.bytes = len(datos)
    libro.ts_actualizacion = timezone.now()
    libro.actualizado_por = usuario
    libro.save()
    return libro
