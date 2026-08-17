"""
exportacion_png.py
-------------------
Genera una imagen PNG de un territorio para compartir rápido (ej. WhatsApp)
sin necesidad de abrir un PDF, con la misma estética que el Excel y el PDF.
"""

import io

from PIL import Image, ImageDraw, ImageFont

from .paleta import HEADER_HEX, FILA_PAR_HEX, BORDE_HEX, TEXTO_OSCURO_HEX, hex_a_rgb


def generar_png(territorio, registros):
    """
    Genera una imagen PNG con una tabla del territorio, pensada para
    compartir rápido (ej. por WhatsApp) sin necesidad de abrir un PDF.

    Misma estética que el Excel/PDF exportados: encabezado en color y grilla
    de bordes prolija. 'No llamar' y 'Funciona' quedan en blanco cuando no
    hay un dato cargado, en vez de escribir "No" / "Sin verificar".
    """
    ancho_img = 900
    margen_izq = 20
    margen_der = ancho_img - 20
    fila_alto = 32
    alto_titulo = 78
    alto_encabezado_tabla = 34
    alto_img = alto_titulo + alto_encabezado_tabla + fila_alto * max(len(registros), 1) + 20

    img = Image.new("RGB", (ancho_img, alto_img), color="white")
    draw = ImageDraw.Draw(img)

    try:
        fuente_titulo = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20
        )
        fuente_normal = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14
        )
        fuente_negrita = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14
        )
    except OSError:
        # Intentar con fuentes de Windows
        try:
            fuente_titulo = ImageFont.truetype("arial.ttf", 20)
            fuente_normal = ImageFont.truetype("arial.ttf", 14)
            fuente_negrita = ImageFont.truetype("arialbd.ttf", 14)
        except OSError:
            # Último recurso: fuente por defecto de Pillow
            fuente_titulo = ImageFont.load_default()
            fuente_normal = ImageFont.load_default()
            fuente_negrita = ImageFont.load_default()

    color_header = hex_a_rgb(HEADER_HEX)
    color_fila_par = hex_a_rgb(FILA_PAR_HEX)
    color_borde = hex_a_rgb(BORDE_HEX)
    color_texto_header = hex_a_rgb(TEXTO_OSCURO_HEX)

    y = 20
    draw.text((margen_izq, y), f"Territorio {territorio['numero']}", fill="black", font=fuente_titulo)
    y += 30
    draw.text((margen_izq, y), f"Estado: {territorio['estado']}", fill="black", font=fuente_normal)
    y += 34

    columnas = ["Dirección", "Teléfono", "No llamar", "Funciona"]
    anchos_col = [340, 200, 150, 170]
    x_bordes = [margen_izq]
    for ancho_col in anchos_col:
        x_bordes.append(x_bordes[-1] + ancho_col)

    y_tabla_inicio = y

    # Encabezado con fondo de color
    draw.rectangle([margen_izq, y, x_bordes[-1], y + alto_encabezado_tabla], fill=color_header)
    for texto, x_izq in zip(columnas, x_bordes[:-1]):
        draw.text((x_izq + 8, y + 9), texto, fill=color_texto_header, font=fuente_negrita)
    y += alto_encabezado_tabla

    for idx, reg in enumerate(registros):
        if idx % 2 == 1:
            draw.rectangle([margen_izq, y, x_bordes[-1], y + fila_alto], fill=color_fila_par)

        # En blanco si no hay dato cargado, para no escribir "No" o
        # "Sin verificar" en cada fila y que sea fácil completar a mano.
        no_llamar_txt = "Sí" if reg["no_llamar"] else ""
        if reg["funcionan"] is None:
            funciona_txt = ""
        else:
            funciona_txt = "Sí" if reg["funcionan"] else "No"

        valores = [
            (reg["direccion"] or "—")[:45],
            reg["telefono"] or "",
            no_llamar_txt,
            funciona_txt,
        ]
        for texto, x_izq in zip(valores, x_bordes[:-1]):
            draw.text((x_izq + 8, y + 9), str(texto), fill="black", font=fuente_normal)
        y += fila_alto

    y_tabla_fin = y

    # Grilla: líneas verticales entre columnas + horizontales entre filas
    for x in x_bordes:
        draw.line([(x, y_tabla_inicio), (x, y_tabla_fin)], fill=color_borde, width=1)
    y_linea = y_tabla_inicio
    draw.line([(margen_izq, y_linea), (x_bordes[-1], y_linea)], fill=color_borde, width=1)
    y_linea += alto_encabezado_tabla
    draw.line([(margen_izq, y_linea), (x_bordes[-1], y_linea)], fill=color_borde, width=1)
    for _ in registros:
        y_linea += fila_alto
        draw.line([(margen_izq, y_linea), (x_bordes[-1], y_linea)], fill=color_borde, width=1)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
