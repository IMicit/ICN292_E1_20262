"""Generación del informe de mantención en PDF (RF-13).

El informe se arma en el servidor a partir de los registros sellados y se
archiva en la base de datos como un `InformeVisita` con su propio hash. Eso
importa: el documento que llega al cliente es un objeto del sistema, no un
archivo que alguien compone a mano y puede retocar antes de enviarlo.
"""

import io
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image as RLImage,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .models import InformeVisita, RegistroItem

AZUL = colors.HexColor("#123a6b")
GRIS = colors.HexColor("#5b6672")
LINEA = colors.HexColor("#d4dae1")
VERDE = colors.HexColor("#1b6e3c")
ROJO = colors.HexColor("#b32828")
AMBAR = colors.HexColor("#b26a00")

FUENTES = Path(settings.BASE_DIR) / "core" / "static" / "core" / "fuentes"
_registradas = False


def _registrar_fuentes():
    """DejaVu viene con el proyecto: las fuentes base de reportlab no cubren
    bien los acentos del castellano en todas las plataformas."""
    global _registradas
    if _registradas:
        return "DejaVu", "DejaVu-Bold"
    try:
        pdfmetrics.registerFont(TTFont("DejaVu", str(FUENTES / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(FUENTES / "DejaVuSans-Bold.ttf")))
        _registradas = True
        return "DejaVu", "DejaVu-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


def _estilos():
    base, negrita = _registrar_fuentes()
    hoja = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("t", parent=hoja["Title"], fontName=negrita,
                                 fontSize=17, leading=21, textColor=AZUL,
                                 alignment=TA_LEFT, spaceAfter=2),
        "subtitulo": ParagraphStyle("st", fontName=base, fontSize=9.5, leading=14,
                                    textColor=GRIS, spaceAfter=10),
        "h2": ParagraphStyle("h2", fontName=negrita, fontSize=11.5, leading=15,
                             textColor=AZUL, spaceBefore=12, spaceAfter=5),
        "h3": ParagraphStyle("h3", fontName=negrita, fontSize=9.5, leading=13,
                             textColor=colors.HexColor("#17212b"),
                             spaceBefore=7, spaceAfter=3),
        "p": ParagraphStyle("p", fontName=base, fontSize=9, leading=12.5),
        "celda": ParagraphStyle("c", fontName=base, fontSize=7.8, leading=10),
        "celda_b": ParagraphStyle("cb", fontName=negrita, fontSize=7.8, leading=10),
        "pie": ParagraphStyle("pie", fontName=base, fontSize=7.2, leading=9.5, textColor=GRIS),
        "base": base, "negrita": negrita,
    }


def _encabezado_pie(visita, est):
    def dibujar(lienzo, doc):
        lienzo.saveState()
        ancho, alto = A4
        lienzo.setFillColor(AZUL)
        lienzo.rect(0, alto - 16 * mm, ancho, 16 * mm, stroke=0, fill=1)
        lienzo.setFillColor(colors.white)
        lienzo.setFont(est["negrita"], 10)
        lienzo.drawString(18 * mm, alto - 10.5 * mm, "IMELSE SpA · Informe de mantención preventiva")
        lienzo.setFont(est["base"], 7.5)
        lienzo.setFillColor(colors.HexColor("#aebfd4"))
        lienzo.drawRightString(ancho - 18 * mm, alto - 10.5 * mm,
                               f"{visita.local.nombre} · {visita.fecha:%d-%m-%Y}")
        lienzo.setStrokeColor(LINEA)
        lienzo.setLineWidth(0.5)
        lienzo.line(18 * mm, 14 * mm, ancho - 18 * mm, 14 * mm)
        lienzo.setFillColor(GRIS)
        lienzo.setFont(est["base"], 7)
        lienzo.drawString(18 * mm, 10 * mm,
                          "Documento generado por el SIG de IMELSE. Prototipo académico, datos ficticios.")
        lienzo.drawRightString(ancho - 18 * mm, 10 * mm, f"Página {doc.page}")
        lienzo.restoreState()
    return dibujar


def _tabla(datos, anchos, est, cabecera=True):
    t = Table(datos, colWidths=anchos, repeatRows=1 if cabecera else 0)
    estilo = [
        ("GRID", (0, 0), (-1, -1), 0.4, LINEA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    if cabecera:
        estilo += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaeef3"))]
    t.setStyle(TableStyle(estilo))
    return t


def _color_resultado(resultado):
    return {"SI": VERDE, "NO": ROJO}.get(resultado, GRIS)


def construir_pdf(visita):
    """Devuelve los bytes del informe de la visita."""
    est = _estilos()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=22 * mm, bottomMargin=18 * mm,
        title=f"Informe de mantención — {visita.local.nombre}",
        author="SIG IMELSE",
    )
    E, P = [], est
    ancho = doc.width

    # --- Portada ---------------------------------------------------------
    E.append(Paragraph("Informe de mantención preventiva", P["titulo"]))
    E.append(Paragraph(
        f"{visita.local.cliente.razon_social} · {visita.local.nombre}<br/>"
        f"{visita.local.direccion}, {visita.local.comuna}<br/>"
        f"{visita.ciclo} · Visita del {visita.fecha:%d de %B de %Y}",
        P["subtitulo"]))

    cuadrilla = ", ".join(
        u.get_full_name() or u.username for u in visita.cuadrilla.all()
    ) or "—"
    cierre = (
        f"{visita.ts_cierre:%d-%m-%Y %H:%M} por "
        f"{visita.cerrada_por.get_full_name() or visita.cerrada_por.username}"
        if visita.ts_cierre else "Visita no cerrada"
    )
    E.append(_tabla([
        [Paragraph("Tableros intervenidos", P["celda_b"]),
         Paragraph("Cobertura", P["celda_b"]),
         Paragraph("Pendientes", P["celda_b"]),
         Paragraph("Cierre", P["celda_b"])],
        [Paragraph(f"{visita.total_registrados} de {visita.total_tableros}", P["celda"]),
         Paragraph(f"{visita.porcentaje_cobertura} %", P["celda"]),
         Paragraph(str(visita.pendientes.count()), P["celda"]),
         Paragraph(cierre, P["celda"])],
    ], [ancho * .22, ancho * .15, ancho * .15, ancho * .48], P))
    E.append(Spacer(1, 4))
    E.append(Paragraph(f"<b>Cuadrilla:</b> {cuadrilla}", P["p"]))

    # --- Pauta de ámbito visita ------------------------------------------
    vigentes_visita = {}
    for r in visita.items.filter(registro_tablero__isnull=True).select_related(
            "item", "item__seccion", "usuario").order_by("ts_captura", "id"):
        vigentes_visita[r.item_id] = r

    if vigentes_visita:
        E.append(Paragraph("Pauta general de la visita", P["h2"]))
        filas = [[Paragraph("Ítem", P["celda_b"]), Paragraph("Resultado", P["celda_b"]),
                  Paragraph("Motivo", P["celda_b"]), Paragraph("Hora", P["celda_b"])]]
        marcas = []
        for i, r in enumerate(sorted(vigentes_visita.values(),
                                     key=lambda x: (x.item.seccion.numero, x.item.orden)), start=1):
            filas.append([
                Paragraph(f"{r.item.codigo} {r.item.descripcion}", P["celda"]),
                Paragraph(r.get_resultado_display(), P["celda_b"]),
                Paragraph(r.justificacion or "—", P["celda"]),
                Paragraph(f"{timezone.localtime(r.ts_captura):%H:%M}", P["celda"]),
            ])
            marcas.append(("TEXTCOLOR", (1, i), (1, i), _color_resultado(r.resultado)))
        t = _tabla(filas, [ancho * .52, ancho * .13, ancho * .25, ancho * .10], P)
        t.setStyle(TableStyle(marcas))
        E.append(t)

    # --- Detalle por tablero ---------------------------------------------
    registros = (visita.registros_tablero.select_related("tablero", "usuario")
                 .prefetch_related("evidencias__items", "observaciones__autor",
                                   "hallazgos", "items__item__seccion", "medicion")
                 .order_by("tablero__codigo"))

    for reg in registros:
        E.append(PageBreak())
        E.append(Paragraph(
            f"Tablero {reg.tablero.codigo} — {reg.tablero.ubicacion}", P["h2"]))
        sello = (f"Sellado el {timezone.localtime(reg.ts_cierre):%d-%m-%Y %H:%M}"
                 if reg.ts_cierre else "Sin sellar")
        E.append(Paragraph(
            f"{reg.tablero.get_tipo_display()} · "
            f"{reg.usuario.get_full_name() or reg.usuario.username} · {sello}",
            P["subtitulo"]))

        vigentes = reg.respuestas_vigentes()
        con_foto = set()
        for ev in reg.evidencias.all():
            con_foto.update(i.id for i in ev.items.all())

        filas = [[Paragraph("Ítem de la pauta", P["celda_b"]),
                  Paragraph("Resultado", P["celda_b"]),
                  Paragraph("Motivo", P["celda_b"]),
                  Paragraph("Foto", P["celda_b"]),
                  Paragraph("Hora", P["celda_b"])]]
        marcas = []
        for i, r in enumerate(sorted(vigentes.values(),
                                     key=lambda x: (x.item.seccion.numero, x.item.orden)), start=1):
            filas.append([
                Paragraph(f"{r.item.codigo} {r.item.descripcion}", P["celda"]),
                Paragraph(r.get_resultado_display(), P["celda_b"]),
                Paragraph(r.justificacion or "—", P["celda"]),
                Paragraph("Sí" if r.item_id in con_foto else "—", P["celda"]),
                Paragraph(f"{timezone.localtime(r.ts_captura):%H:%M}", P["celda"]),
            ])
            marcas.append(("TEXTCOLOR", (1, i), (1, i), _color_resultado(r.resultado)))
        t = _tabla(filas, [ancho * .46, ancho * .12, ancho * .24, ancho * .08, ancho * .10], P)
        t.setStyle(TableStyle(marcas))
        E.append(t)

        # Mediciones eléctricas
        medicion = getattr(reg, "medicion", None)
        if medicion:
            E.append(Paragraph("Mediciones eléctricas", P["h3"]))
            def v(x):
                return "—" if x is None else f"{x}"
            filas = [
                [Paragraph("Entre fases (V)", P["celda_b"]),
                 Paragraph(f"L1-L2 {v(medicion.v_l1_l2)}", P["celda"]),
                 Paragraph(f"L2-L3 {v(medicion.v_l2_l3)}", P["celda"]),
                 Paragraph(f"L3-L1 {v(medicion.v_l3_l1)}", P["celda"])],
                [Paragraph("Línea-neutro (V)", P["celda_b"]),
                 Paragraph(f"L1-N {v(medicion.v_l1_n)}", P["celda"]),
                 Paragraph(f"L2-N {v(medicion.v_l2_n)}", P["celda"]),
                 Paragraph(f"L3-N {v(medicion.v_l3_n)}", P["celda"])],
                [Paragraph("Línea-tierra (V)", P["celda_b"]),
                 Paragraph(f"L1-T {v(medicion.v_l1_t)}", P["celda"]),
                 Paragraph(f"L2-T {v(medicion.v_l2_t)}", P["celda"]),
                 Paragraph(f"L3-T {v(medicion.v_l3_t)}", P["celda"])],
                [Paragraph("Corriente (A)", P["celda_b"]),
                 Paragraph(f"L1 {v(medicion.i_l1)}", P["celda"]),
                 Paragraph(f"L2 {v(medicion.i_l2)}", P["celda"]),
                 Paragraph(f"L3 {v(medicion.i_l3)}", P["celda"])],
                [Paragraph("Tierra-neutro / COS-FI", P["celda_b"]),
                 Paragraph(f"T-N {v(medicion.v_t_n)} V", P["celda"]),
                 Paragraph(f"COS-FI {v(medicion.cos_fi)}", P["celda"]),
                 Paragraph("", P["celda"])],
            ]
            E.append(_tabla(filas, [ancho * .28, ancho * .24, ancho * .24, ancho * .24],
                            P, cabecera=False))
            for aviso in medicion.anomalias():
                E.append(Paragraph(
                    f'<font color="#b32828"><b>Fuera de rango:</b> {aviso}</font>', P["p"]))

        # Hallazgos
        hallazgos = list(reg.hallazgos.all())
        if hallazgos:
            E.append(Paragraph("Hallazgos", P["h3"]))
            for h in hallazgos:
                color = ROJO if h.criticidad in ("ALTA", "CRITICA") else AMBAR
                E.append(Paragraph(
                    f'<font color="#{color.hexval()[2:]}"><b>[{h.get_criticidad_display()}]</b></font> '
                    f"{h.descripcion}", P["p"]))

        # Evidencia
        evidencias = list(reg.evidencias.all())
        if evidencias:
            E.append(Paragraph("Evidencia fotográfica", P["h3"]))
            fila, pies = [], []
            for ev in evidencias:
                try:
                    img = RLImage(ev.archivo.path, width=ancho / 3.25, height=ancho / 4.35)
                except Exception:
                    continue
                codigos = ", ".join(i.codigo for i in ev.items.all()) or "general"
                fila.append(img)
                pies.append(Paragraph(
                    f"{codigos}<br/>{timezone.localtime(ev.ts):%d-%m %H:%M} · "
                    f"sha256 {ev.hash_corto}…", P["pie"]))
                if len(fila) == 3:
                    E.append(KeepTogether([
                        _tabla([fila, pies], [ancho / 3.1] * 3, P, cabecera=False)]))
                    fila, pies = [], []
            if fila:
                while len(fila) < 3:
                    fila.append(""); pies.append("")
                E.append(_tabla([fila, pies], [ancho / 3.1] * 3, P, cabecera=False))

        # Observaciones
        observaciones = list(reg.observaciones.all())
        if observaciones:
            E.append(Paragraph("Observaciones anexadas", P["h3"]))
            for o in observaciones:
                E.append(Paragraph(
                    f"<b>{o.autor.get_full_name() or o.autor.username}</b> "
                    f"({o.autor.get_rol_display()}, "
                    f"{timezone.localtime(o.ts):%d-%m-%Y %H:%M}): {o.texto}", P["p"]))

    # --- Pendientes -------------------------------------------------------
    pendientes = list(visita.pendientes.select_related("tablero", "usuario"))
    if pendientes:
        E.append(PageBreak())
        E.append(Paragraph("Tableros no intervenidos", P["h2"]))
        E.append(Paragraph(
            "Cada tablero no intervenido quedó declarado con su motivo, autor y hora. "
            "Ninguno quedó simplemente en blanco.", P["subtitulo"]))
        filas = [[Paragraph("Tablero", P["celda_b"]), Paragraph("Motivo", P["celda_b"]),
                  Paragraph("Detalle", P["celda_b"]), Paragraph("Declaró", P["celda_b"]),
                  Paragraph("Fecha", P["celda_b"])]]
        for p in pendientes:
            filas.append([
                Paragraph(f"{p.tablero.codigo}<br/>{p.tablero.ubicacion}", P["celda"]),
                Paragraph(p.get_motivo_display(), P["celda"]),
                Paragraph(p.comentario or "—", P["celda"]),
                Paragraph(p.usuario.get_full_name() or p.usuario.username, P["celda"]),
                Paragraph(f"{timezone.localtime(p.ts):%d-%m-%Y %H:%M}", P["celda"]),
            ])
        E.append(_tabla(filas, [ancho * .20, ancho * .22, ancho * .26, ancho * .18, ancho * .14], P))

    # --- Nota de integridad ----------------------------------------------
    E.append(Spacer(1, 14))
    E.append(Paragraph(
        "Las fotografías llevan estampados dentro de la imagen el tablero, la fecha y la hora "
        "de captura, y cada una guarda su huella SHA-256 calculada en el momento de recibirla. "
        "Ningún registro de este informe fue modificado después de su cierre: el sistema no lo "
        "permite (RNF-02).", P["pie"]))

    doc.build(E, onFirstPage=_encabezado_pie(visita, P),
              onLaterPages=_encabezado_pie(visita, P))
    return buffer.getvalue()


def generar_informe(visita, usuario):
    """Construye el PDF y lo archiva como `InformeVisita` inmutable."""
    datos = construir_pdf(visita)
    version = visita.informes.count() + 1
    informe = InformeVisita(
        visita=visita,
        version=version,
        archivo=ContentFile(
            datos,
            name=f"informe-{visita.local.nombre[:20].replace(' ', '-')}"
                 f"-{visita.fecha:%Y%m%d}-v{version}.pdf",
        ),
        generado_por=usuario,
        ts=timezone.now(),
    )
    informe.save()
    return informe
