"""
importacion_historial.py
-------------------------
Importa el Excel de Historial de Asignaciones y sincroniza el estado de
cada territorio afectado.
"""

import difflib
import sqlite3
import pandas as pd

from .celdas import _celda_pandas_a_texto, _parsear_fecha_excel, _normalizar_nombre

# A partir de qué % de similitud (0-1) avisamos que un nombre nuevo se
# parece sospechosamente a uno que ya existe, para que se revise a mano.
# Por debajo de esto se considera un nombre distinto y no se avisa.
UMBRAL_AVISO_SIMILITUD = 0.82

# Columnas obligatorias del Excel de Historial (nombres exactos, sensibles a
# mayúsculas porque así vienen del Excel original).
COLUMNAS_HISTORIAL = ["Territorio", "Responsable", "Fecha asignado", "Fecha completado", "Detalles"]


def importar_historial(archivo, conn):
    """
    Lee el Excel de Historial de Asignaciones (columnas: Territorio,
    Responsable, Fecha asignado, Fecha completado, Detalles) y:

    1. Crea los responsables que no existan todavía (activo = 1). La
       búsqueda de "¿ya existe?" ignora tildes, mayúsculas y espacios de
       más, para no crear un responsable duplicado por variaciones de
       escritura del mismo nombre (ver `_normalizar_nombre`). Si un nombre
       nuevo se parece mucho a uno existente pero no es igual ni siquiera
       normalizado (posible typo real), no se bloquea la importación: se
       crea igual y se avisa en el resumen para que se revise a mano.
    2. Antes de tocar la base, valida que el archivo no deje a ningún
       territorio con más de una asignación abierta (sin 'Fecha completado')
       a la vez. Si eso pasa, no se importa NADA y se informa con un error
       claro qué territorios y filas están en conflicto.
    3. Crea los territorios que no existan todavía (por 'numero').
    4. Normaliza las fechas de cada fila.
    5. Hace upsert en 'asignaciones': la clave natural para no duplicar si el
       mismo Excel se sube dos veces es (territorio_id, responsable_id,
       fecha_asignado). Si ya existe esa asignación, se actualizan
       'fecha_finalizacion' y 'detalles' en vez de crear una fila nueva.
    6. Al final, sincroniza 'territorios.estado': queda 'En trabajo' si el
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
        "avisos_nombres_parecidos": [],
    }

    # Cachés en memoria para no repetir SELECTs por cada fila del Excel.
    # cache_responsables: nombre normalizado -> (id, nombre_original_en_bd)
    cache_responsables = {}
    for fila_resp in conn.execute("SELECT id, nombre FROM responsables"):
        cache_responsables[_normalizar_nombre(fila_resp["nombre"])] = (
            fila_resp["id"],
            fila_resp["nombre"],
        )
    nombres_normalizados_existentes = list(cache_responsables.keys())

    cache_territorios = {}
    territorios_afectados = set()

    # --- Validación previa: ¿el archivo dejaría más de una asignación
    # abierta para el mismo territorio? ---
    # No escribimos nada en la base todavía. Simulamos en memoria el estado
    # final de "¿está abierta?" por cada combinación (territorio, responsable,
    # fecha_asignado) que aparece en el archivo, partiendo de lo que ya está
    # abierto en la base para esos territorios. Si al terminar algún
    # territorio queda con 2 o más claves distintas abiertas, se rechaza
    # TODA la importación con un error claro, en vez de dejar la base a
    # medio actualizar.
    estado_por_territorio = {}  # numero -> { clave_natural: (abierta, fila_excel) }
    for pos, fila in df.iterrows():
        num_fila_excel = pos + 2
        numero = _celda_pandas_a_texto(fila["Territorio"])
        nombre_resp = _celda_pandas_a_texto(fila["Responsable"])
        fecha_asignado = _parsear_fecha_excel(fila["Fecha asignado"])
        fecha_completado = _parsear_fecha_excel(fila["Fecha completado"])

        if not numero or not nombre_resp or not fecha_asignado:
            continue  # esta fila ya se va a reportar como error en la pasada real

        if numero not in estado_por_territorio:
            # Sembramos con lo que YA está abierto hoy en la base para este
            # territorio (si existe), usando el nombre del responsable como
            # parte de la clave para poder comparar contra el Excel.
            estado_por_territorio[numero] = {}
            fila_terr_existente = conn.execute(
                "SELECT id FROM territorios WHERE numero = ?", (numero,)
            ).fetchone()
            if fila_terr_existente is not None:
                for a in conn.execute(
                    """
                    SELECT a.responsable_id, a.fecha_asignado, r.nombre AS responsable_nombre
                    FROM asignaciones a
                    JOIN responsables r ON r.id = a.responsable_id
                    WHERE a.territorio_id = ? AND a.fecha_finalizacion IS NULL
                    """,
                    (fila_terr_existente["id"],),
                ):
                    clave_previa = (
                        _normalizar_nombre(a["responsable_nombre"]),
                        a["fecha_asignado"],
                    )
                    estado_por_territorio[numero][clave_previa] = (True, "(ya existente en la base)")

        clave = (_normalizar_nombre(nombre_resp), fecha_asignado)
        esta_abierta = not fecha_completado
        estado_por_territorio[numero][clave] = (esta_abierta, num_fila_excel)

    conflictos = []
    for numero, claves in estado_por_territorio.items():
        abiertas = [(clave, origen) for clave, (abierta, origen) in claves.items() if abierta]
        if len(abiertas) > 1:
            filas_conflicto = ", ".join(str(origen) for _clave, origen in abiertas)
            conflictos.append(
                f"Territorio {numero}: quedaría con {len(abiertas)} asignaciones abiertas "
                f"a la vez (filas: {filas_conflicto}). Un territorio solo puede tener una."
            )

    if conflictos:
        raise ValueError(
            "No se importó nada porque el archivo dejaría más de una asignación abierta "
            "para el mismo territorio en estos casos:\n- " + "\n- ".join(conflictos) +
            "\nCorregí el Excel (dejando una sola fila sin 'Fecha completado' por territorio) "
            "y volvé a intentar."
        )

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

        # --- Responsable: auto-crear si no existe (comparando sin tildes/mayúsculas) ---
        clave_normalizada = _normalizar_nombre(nombre_resp)
        entrada_cache = cache_responsables.get(clave_normalizada)
        if entrada_cache is None:
            # No hay match ni siquiera normalizado: es un nombre nuevo de verdad.
            # Antes de crearlo, avisamos si se parece mucho a uno que ya existe
            # (posible typo real, ej. "Papatanasi" vs "Papatanassi"), pero no
            # bloqueamos la importación por esto.
            parecidos = difflib.get_close_matches(
                clave_normalizada, nombres_normalizados_existentes,
                n=1, cutoff=UMBRAL_AVISO_SIMILITUD,
            )
            if parecidos:
                nombre_parecido = cache_responsables[parecidos[0]][1]
                resumen["avisos_nombres_parecidos"].append(
                    f"Fila {num_fila_excel}: \"{nombre_resp}\" se creó como responsable "
                    f"nuevo pero se parece a \"{nombre_parecido}\" (ya existente). "
                    "Revisar si es la misma persona escrita distinto."
                )

            cur = conn.execute(
                "INSERT INTO responsables (nombre, activo) VALUES (?, 1)",
                (nombre_resp,),
            )
            responsable_id = cur.lastrowid
            resumen["responsables_creados"] += 1
            cache_responsables[clave_normalizada] = (responsable_id, nombre_resp)
            nombres_normalizados_existentes.append(clave_normalizada)
        else:
            responsable_id, _ = entrada_cache

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
            try:
                conn.execute(
                    """
                    INSERT INTO asignaciones
                        (territorio_id, responsable_id, fecha_asignado, fecha_finalizacion, detalles)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (territorio_id, responsable_id, fecha_asignado, fecha_completado, detalles),
                )
            except sqlite3.IntegrityError:
                # Backstop: no debería pasar (ya lo validamos antes), pero si
                # algo dejó a este territorio con otra asignación abierta
                # justo en este momento, no lo dejamos pasar en silencio.
                raise ValueError(
                    f"Fila {num_fila_excel}: el territorio {numero} ya tiene otra "
                    "asignación abierta en la base. No se importó nada."
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
