"""
paleta.py
---------
Colores compartidos entre las tres exportaciones (Excel, PDF, PNG) para que
las tres tengan la misma estética: encabezado en color, filas alternadas y
bordes prolijos. Si el día de mañana se quiere cambiar el color, alcanza con
tocar este archivo.
"""

# Hex sin "#", tal como los espera openpyxl.
HEADER_HEX = "F4B183"          # naranja/durazno suave para el encabezado
FILA_PAR_HEX = "FBEEE6"        # banda muy tenue para alternar filas
BORDE_HEX = "BFBFBF"           # gris para los bordes de las celdas
TEXTO_OSCURO_HEX = "3B2A1A"    # texto del encabezado y títulos


def hex_a_rgb(hex_color):
    """Convierte 'RRGGBB' a una tupla (R, G, B) de 0-255, para usar con Pillow."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
