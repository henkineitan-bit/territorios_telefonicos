"""
exports
-------
Paquete con las funciones auxiliares para importar y exportar datos del
Gestor de Territorios Telefónicos, dividido en un módulo por
responsabilidad:

- celdas.py                 -> helpers para interpretar celdas de Excel
- paleta.py                 -> colores compartidos por las 3 exportaciones
- importacion_excel.py      -> importar_excel()      (Excel de números)
- importacion_historial.py  -> importar_historial()  (Excel de historial)
- exportacion_excel.py      -> generar_excel()
- exportacion_pdf.py        -> generar_pdf()
- exportacion_png.py        -> generar_png()

Se re-exportan acá las 5 funciones públicas para que el resto de la app
(routes/, etc.) las siga importando exactamente igual que antes, sin
tener que cambiar nada:

    from exports import generar_pdf, generar_png, generar_excel
    from exports import importar_excel, importar_historial
"""

from .importacion_excel import importar_excel
from .importacion_historial import importar_historial
from .exportacion_excel import generar_excel
from .exportacion_pdf import generar_pdf
from .exportacion_png import generar_png

__all__ = [
    "importar_excel",
    "importar_historial",
    "generar_excel",
    "generar_pdf",
    "generar_png",
]
