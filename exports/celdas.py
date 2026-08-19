"""
celdas.py
---------
Helpers para interpretar celdas de Excel de forma flexible. Los usan tanto
importacion_excel.py (vía openpyxl) como importacion_historial.py (vía
pandas), por eso están centralizados acá en vez de repetidos en cada uno.
"""

from datetime import datetime
import unicodedata
import pandas as pd


def _normalizar_nombre(nombre):
    """
    Devuelve una versión 'canónica' de un nombre para poder comparar
    responsables sin que tildes, mayúsculas o espacios de más generen
    duplicados (ej: "José Espósito", "jose esposito " y "JOSÉ  ESPÓSITO"
    deben matchear el mismo responsable).

    No se usa para mostrar en pantalla ni para guardar en la base: solo
    como clave de comparación interna.
    """
    if nombre is None:
        return ""
    # Separa cada letra de su tilde/diacrítico y se queda solo con la letra
    descompuesto = unicodedata.normalize("NFKD", nombre)
    sin_tildes = "".join(c for c in descompuesto if not unicodedata.combining(c))
    # Colapsa espacios múltiples y pasa todo a minúsculas
    return " ".join(sin_tildes.lower().split())


def _celda_a_texto(valor):
    """Convierte una celda de Excel a texto limpio, o None si está vacía."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _celda_a_bool01(valor):
    """
    Convierte una celda a 0 o 1, aceptando varias formas de escribir "sí/no":
    1, 0, "si", "sí", "no", "true", "false", vacío (-> 0).
    """
    if valor is None:
        return 0
    texto = str(valor).strip().lower()
    if texto in ("1", "si", "sí", "true", "x"):
        return 1
    return 0


def _celda_a_funcionan(valor):
    """
    Convierte una celda al valor de 'funcionan': None (sin verificar), 1 o 0.
    Deja en None cualquier celda vacía o que no se entienda con claridad.
    """
    if valor is None:
        return None
    texto = str(valor).strip().lower()
    if texto in ("1", "si", "sí", "true"):
        return 1
    if texto in ("0", "no", "false"):
        return 0
    return None


def _celda_pandas_a_texto(valor):
    """
    Como _celda_a_texto, pero para valores que vienen de un DataFrame de pandas.
    Cubre dos casos típicos de leer Excel con pandas:
    - Celdas vacías, que pandas representa como NaN (float), no como None.
    - Columnas de números (como 'Territorio') que, si tienen alguna celda
      vacía en el medio, pandas infiere como float: 404 llega como 404.0.
    """
    if valor is None or pd.isna(valor):
        return None
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    texto = str(valor).strip()
    return texto or None


def _parsear_fecha_excel(texto):
    """
    Convierte el texto de una celda de fecha a 'YYYY-MM-DD HH:MM:SS'
    (el mismo formato que usa el resto de la app), o None si la celda
    está vacía (incluyendo NaN de pandas) o no se pudo interpretar.

    Acepta 'YYYY-MM-DD' y 'DD/MM/YYYY', con o sin hora incluida (esto último
    pasa seguido porque Excel suele guardar las fechas como fecha+hora aunque
    la celda solo muestre el día).
    """
    if texto is None or pd.isna(texto):
        return None
    texto = str(texto).strip()
    if not texto:
        return None

    formatos = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y")
    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

    return None  # formato no reconocido; se trata como fecha vacía
