"""
importacion_historial.py
-------------------------
Importa el Excel de Historial de Asignaciones y sincroniza el estado de
cada territorio afectado.
"""

import pandas as pd

from .celdas import _celda_pandas_a_texto, _parsear_fecha_excel

# Columnas obligatorias del Excel de Historial (nombres exactos, sensibles a
# mayúsculas porque así vienen del Excel original).
COLUMNAS_HISTORIAL = ["Territorio", "Responsable", "Fecha asignado", "Fecha completado", "Detalles"]


def importar_historial(archivo, conn):
    """
    Lee el Excel de Historial de Asignaciones (columnas: Territorio,
    Responsable, Fecha asignado, Fecha completado, Detalles) y:

    1. Crea los responsables que no existan todavía (activo = 1).
    2. Crea los territorios que no existan todavía (por 'numero').
    3. Normaliza las fechas de cada fila.
    4. Hace upsert en 'asignaciones': la clave natural para no duplicar si el
       mismo Excel se sube dos veces es (territorio_id, responsable_id,
       fecha_asignado). Si ya existe esa asignación, se actualizan
       'fecha_finalizacion' y 'detalles' en vez de crear una fila nueva.
    5. Al final, sincroniza 'territorios.estado': queda 'En trabajo' si el
       territorio tiene alguna asignación sin fecha_finalizacion, o
       'Disponible' si no tiene ninguna abierta.

    Devuelve un diccionario con contadores para mostrarle un resumen al usuario.
    """
    try:
        df = pd.read_excel(archivo)
    except Exception as e:
        raise ValueError(f"No se pudo leer el Excel: {e}")

    faltantes = [c for c in COLUMNAS_HISTORIAL if c not in df.columns]
    if faltantes:
        raise ValueError(
            "El Excel debe tener las columnas: "
            f"{', '.join(COLUMNAS_HISTORIAL)}. Faltan: {', '.join(faltantes)}."
        )

    resumen = {
        "responsables_creados": 0,
        "territorios_creados": 0,
        "asignaciones_insertadas": 0,
        "asignaciones_actualizadas": 0,
        "errores": 0,
        "detalle_errores": [],
    }

    # Cachés en memoria para no repetir SELECTs por cada fila del Excel.
    cache_responsables = {}
    cache_territorios = {}
    territorios_afectados = set()

    for pos, fila in df.iterrows():
        num_fila_excel = pos + 2  # +2: índice 0-based de pandas + fila de encabezado

        numero = _celda_pandas_a_texto(fila["Territorio"])
        nombre_resp = _celda_pandas_a_texto(fila["Responsable"])
        fecha_asignado = _parsear_fecha_excel(fila["Fecha asignado"])
        fecha_completado = _parsear_fecha_excel(fila["Fecha completado"])
        detalles = _celda_pandas_a_texto(fila["Detalles"])

        if not numero or not nombre_resp or not fecha_asignado:
            resumen["errores"] += 1
            resumen["detalle_errores"].append(
                f"Fila {num_fila_excel}: faltan datos obligatorios "
                "(Territorio, Responsable o Fecha asignado válida), se saltea."
            )
            continue

        # --- Responsable: auto-crear si no existe ---
        responsable_id = cache_responsables.get(nombre_resp)
        if responsable_id is None:
            fila_resp = conn.execute(
                "SELECT id FROM responsables WHERE nombre = ?", (nombre_resp,)
            ).fetchone()
            if fila_resp is None:
                cur = conn.execute(
                    "INSERT INTO responsables (nombre, activo) VALUES (?, 1)",
                    (nombre_resp,),
                )
                responsable_id = cur.lastrowid
                resumen["responsables_creados"] += 1
            else:
                responsable_id = fila_resp["id"]
            cache_responsables[nombre_resp] = responsable_id

        # --- Territorio: auto-crear si no existe ---
        territorio_id = cache_territorios.get(numero)
        if territorio_id is None:
            fila_terr = conn.execute(
                "SELECT id FROM territorios WHERE numero = ?", (numero,)
            ).fetchone()
            if fila_terr is None:
                cur = conn.execute(
                    "INSERT INTO territorios (numero, estado) VALUES (?, 'Disponible')",
                    (numero,),
                )
                territorio_id = cur.lastrowid
                resumen["territorios_creados"] += 1
            else:
                territorio_id = fila_terr["id"]
            cache_territorios[numero] = territorio_id

        territorios_afectados.add(territorio_id)

        # --- Upsert de la asignación ---
        # Misma clave natural (territorio + responsable + fecha_asignado) =
        # se considera la misma asignación, aunque se reimporte el archivo.
        existente = conn.execute(
            """
            SELECT id FROM asignaciones
            WHERE territorio_id = ? AND responsable_id = ? AND fecha_asignado = ?
            """,
            (territorio_id, responsable_id, fecha_asignado),
        ).fetchone()

        if existente is None:
            conn.execute(
                """
                INSERT INTO asignaciones
                    (territorio_id, responsable_id, fecha_asignado, fecha_finalizacion, detalles)
                VALUES (?, ?, ?, ?, ?)
                """,
                (territorio_id, responsable_id, fecha_asignado, fecha_completado, detalles),
            )
            resumen["asignaciones_insertadas"] += 1
        else:
            conn.execute(
                "UPDATE asignaciones SET fecha_finalizacion = ?, detalles = ? WHERE id = ?",
                (fecha_completado, detalles, existente["id"]),
            )
            resumen["asignaciones_actualizadas"] += 1

    # --- Sincronizamos el estado de cada territorio que tocamos ---
    for territorio_id in territorios_afectados:
        abierta = conn.execute(
            "SELECT 1 FROM asignaciones WHERE territorio_id = ? AND fecha_finalizacion IS NULL",
            (territorio_id,),
        ).fetchone()
        nuevo_estado = "En trabajo" if abierta else "Disponible"
        conn.execute(
            "UPDATE territorios SET estado = ? WHERE id = ?",
            (nuevo_estado, territorio_id),
        )

    conn.commit()
    return resumen
