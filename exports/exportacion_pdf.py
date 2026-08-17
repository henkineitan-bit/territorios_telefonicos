"""
exportacion_pdf.py
-------------------
Genera el PDF imprimible de un territorio: título, estado y tabla de
registros, con la misma estética que el Excel exportado.
"""

import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph

from .paleta import HEADER_HEX, FILA_PAR_HEX, BORDE_HEX, TEXTO_OSCURO_HEX


def generar_pdf(territorio, registros):
    """
    Genera un PDF prolijo e imprimible con los datos del territorio y su
    tabla de registros telefónicos: encabezado en color, bordes en toda la
    tabla y filas alternadas (misma estética que el Excel exportado).

    'No llamar' y 'Funciona' quedan en blanco cuando no hay un dato cargado
    (en vez de escribir "No" / "Sin verificar"), para no confundir y para
    que sea cómodo completarlas a mano si se imprime la planilla.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )

    color_header = colors.HexColor(f"#{HEADER_HEX}")
    color_fila_par = colors.HexColor(f"#{FILA_PAR_HEX}")
    color_borde = colors.HexColor(f"#{BORDE_HEX}")
    color_texto_oscuro = colors.HexColor(f"#{TEXTO_OSCURO_HEX}")

    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "TituloTerritorio", parent=estilos["Heading1"],
        fontSize=18, spaceAfter=2, textColor=color_texto_oscuro,
    )
    estilo_subtitulo = ParagraphStyle(
        "Subtitulo", parent=estilos["Normal"],
        fontSize=11, textColor=colors.HexColor("#555555"), spaceAfter=14,
    )
    estilo_celda = ParagraphStyle("Celda", parent=estilos["Normal"], fontSize=9, leading=11)
    estilo_celda_centro = ParagraphStyle("CeldaCentro", parent=estilo_celda, alignment=TA_CENTER)
    estilo_encabezado_celda = ParagraphStyle(
        "EncabezadoCelda", parent=estilos["Normal"], fontSize=9.5, leading=12,
        textColor=color_texto_oscuro, alignment=TA_CENTER, fontName="Helvetica-Bold",
    )

    elementos = [
        Paragraph(f"Territorio N.° {territorio['numero']}", estilo_titulo),
        Paragraph(f"Estado: {territorio['estado']}", estilo_subtitulo),
    ]

    encabezados = ["Dirección", "Teléfono", "Observaciones", "No llamar", "Funciona"]
    filas = [[Paragraph(h, estilo_encabezado_celda) for h in encabezados]]

    for reg in registros:
        # En blanco si no hay dato cargado, para no escribir "No" o
        # "Sin verificar" en cada fila y que sea fácil completar a mano.
        no_llamar_txt = "Sí" if reg["no_llamar"] else ""
        if reg["funcionan"] is None:
            funciona_txt = ""
        else:
            funciona_txt = "Sí" if reg["funcionan"] else "No"

        filas.append([
            Paragraph(reg["direccion"] or "—", estilo_celda),
            Paragraph(reg["telefono"] or "", estilo_celda),
            Paragraph(reg["observaciones"] or "", estilo_celda),
            Paragraph(no_llamar_txt, estilo_celda_centro),
            Paragraph(funciona_txt, estilo_celda_centro),
        ])

    anchos_col = [5.3 * cm, 2.8 * cm, 5.4 * cm, 2.3 * cm, 2.3 * cm]
    tabla = Table(filas, colWidths=anchos_col, repeatRows=1)

    estilo_tabla = [
        ("BACKGROUND", (0, 0), (-1, 0), color_header),
        ("GRID", (0, 0), (-1, -1), 0.6, color_borde),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    for i in range(1, len(filas)):
        if i % 2 == 0:
            estilo_tabla.append(("BACKGROUND", (0, i), (-1, i), color_fila_par))
    tabla.setStyle(TableStyle(estilo_tabla))

    elementos.append(tabla)
    doc.build(elementos)
    buffer.seek(0)
    return buffer
