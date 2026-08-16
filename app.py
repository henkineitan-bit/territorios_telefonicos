"""
app.py
------
Punto de entrada de la aplicación Flask.
Por ahora solo tiene la ruta "/" para verificar que todo funciona.
Las rutas del mapa de endpoints (territorio/<id>, asignar, etc.)
las iremos agregando en los próximos pasos.
"""

from flask import (
    Flask, render_template, request, abort, redirect, url_for,
    send_file, flash,
)
from datetime import datetime
from database import get_connection
from exports import importar_excel, generar_excel, generar_pdf, generar_png, importar_historial

app = Flask(__name__)
app.secret_key = "dev-secret-key-cambiar-en-produccion"  # necesario para usar flash()


@app.route("/")
def index():
    """
    Lista de territorios con filtros: búsqueda por número (q), estado,
    responsable asignado (responsable_id) y orden (numero / antiguos / recientes).
    """
    q = request.args.get("q", "").strip()
    estado = request.args.get("estado", "").strip()
    responsable_id = request.args.get("responsable_id", "").strip()
    orden = request.args.get("orden", "numero")

    conn = get_connection()

    # LEFT JOIN con asignaciones "abiertas" (fecha_finalizacion IS NULL)
    # para saber quién tiene el territorio en este momento, si alguien lo tiene,
    # y desde cuándo (a.fecha_asignado).
    sql = """
        SELECT
            t.id,
            t.numero,
            t.estado,
            r.nombre AS responsable,
            a.fecha_asignado
        FROM territorios t
        LEFT JOIN asignaciones a
            ON a.territorio_id = t.id AND a.fecha_finalizacion IS NULL
        LEFT JOIN responsables r
            ON r.id = a.responsable_id
        WHERE t.numero LIKE ?
    """
    parametros = [f"%{q}%"]

    if estado in ("Disponible", "En trabajo"):
        sql += " AND t.estado = ?"
        parametros.append(estado)

    if responsable_id:
        sql += " AND a.responsable_id = ?"
        parametros.append(responsable_id)

    if orden == "antiguos":
        # Los que tienen fecha_asignado más vieja van primero.
        # Los territorios sin asignación activa (fecha_asignado NULL) quedan al final.
        sql += " ORDER BY (a.fecha_asignado IS NULL), a.fecha_asignado ASC"
    elif orden == "recientes":
        # Igual que "antiguos" pero al revés: asignados más recientemente primero.
        sql += " ORDER BY (a.fecha_asignado IS NULL), a.fecha_asignado DESC"
    else:
        orden = "numero"  # normalizamos cualquier valor raro que venga por la URL
        sql += " ORDER BY CAST(t.numero AS INTEGER)"

    filas = conn.execute(sql, parametros).fetchall()

    # Responsables para el <select> del filtro (todos, activos primero)
    responsables = conn.execute(
        "SELECT id, nombre FROM responsables ORDER BY activo DESC, nombre"
    ).fetchall()

    conn.close()

    # Armamos el texto de "Asignado el" acá en Python, en formato DD/MM/YYYY
    # y sumando cuántos días lleva en trabajo (solo si está 'En trabajo').
    ahora = datetime.now()
    territorios = []
    for fila in filas:
        t = dict(fila)
        if t["estado"] == "En trabajo" and t["fecha_asignado"]:
            fecha_dt = datetime.strptime(t["fecha_asignado"], "%Y-%m-%d %H:%M:%S")
            dias = (ahora - fecha_dt).days
            plural = "" if dias == 1 else "s"
            t["asignado_texto"] = f"{fecha_dt.strftime('%d/%m/%Y')} ({dias} día{plural})"
        else:
            t["asignado_texto"] = "—"
        territorios.append(t)

    return render_template(
        "index.html",
        territorios=territorios,
        q=q,
        estado=estado,
        responsable_id=responsable_id,
        orden=orden,
        responsables=responsables,
    )


@app.route("/territorio/<int:territorio_id>")
def territorio_detalle(territorio_id):
    """
    Detalle de un territorio: sus datos y la tabla de registros telefónicos.
    """
    conn = get_connection()

    territorio = conn.execute(
        "SELECT * FROM territorios WHERE id = ?", (territorio_id,)
    ).fetchone()

    if territorio is None:
        conn.close()
        abort(404)

    registros = conn.execute(
        "SELECT * FROM registros WHERE territorio_id = ? ORDER BY id",
        (territorio_id,),
    ).fetchall()

    # Si el territorio está "En trabajo", acá está el responsable actual
    # (la asignación que todavía no tiene fecha_finalizacion)
    asignacion_activa = conn.execute(
        """
        SELECT a.*, r.nombre AS responsable_nombre
        FROM asignaciones a
        JOIN responsables r ON r.id = a.responsable_id
        WHERE a.territorio_id = ? AND a.fecha_finalizacion IS NULL
        """,
        (territorio_id,),
    ).fetchone()

    # Responsables activos, para llenar el <select> del formulario "Asignar"
    responsables = conn.execute(
        "SELECT * FROM responsables WHERE activo = 1 ORDER BY nombre"
    ).fetchall()

    conn.close()

    return render_template(
        "territorio.html",
        territorio=territorio,
        registros=registros,
        asignacion_activa=asignacion_activa,
        responsables=responsables,
    )


@app.route("/territorio/<int:territorio_id>/historial")
def territorio_historial(territorio_id):
    """
    Cronología del territorio: todas sus asignaciones pasadas/actual,
    y todos los eventos de 'actividad' (asignación, finalización, ediciones).
    """
    conn = get_connection()

    territorio = conn.execute(
        "SELECT * FROM territorios WHERE id = ?", (territorio_id,)
    ).fetchone()
    if territorio is None:
        conn.close()
        abort(404)

    asignaciones = conn.execute(
        """
        SELECT a.*, r.nombre AS responsable_nombre
        FROM asignaciones a
        JOIN responsables r ON r.id = a.responsable_id
        WHERE a.territorio_id = ?
        ORDER BY a.fecha_asignado DESC
        """,
        (territorio_id,),
    ).fetchall()

    actividad = conn.execute(
        """
        SELECT * FROM actividad
        WHERE territorio_id = ?
        ORDER BY fecha DESC, id DESC
        """,
        (territorio_id,),
    ).fetchall()

    conn.close()

    return render_template(
        "historial.html",
        territorio=territorio,
        asignaciones=asignaciones,
        actividad=actividad,
    )


@app.route("/territorio/<int:territorio_id>/asignar", methods=["POST"])
def territorio_asignar(territorio_id):
    """
    Asigna el territorio a un responsable: crea una fila en 'asignaciones'
    y pasa el territorio a estado 'En trabajo'.
    """
    responsable_id = request.form.get("responsable_id")
    detalles = request.form.get("detalles", "").strip() or None

    if not responsable_id:
        abort(400)  # falta el dato obligatorio

    conn = get_connection()

    territorio = conn.execute(
        "SELECT * FROM territorios WHERE id = ?", (territorio_id,)
    ).fetchone()
    if territorio is None:
        conn.close()
        abort(404)

    # Regla de negocio del MVP (sección 14 del doc): un territorio "En trabajo"
    # no puede recibir otra asignación simultánea.
    if territorio["estado"] != "Disponible":
        conn.close()
        flash(
            f"El territorio {territorio['numero']} ya está en trabajo, "
            "no se puede asignar de nuevo hasta que se finalice.",
            "error",
        )
        return redirect(url_for("territorio_detalle", territorio_id=territorio_id))

    responsable = conn.execute(
        "SELECT * FROM responsables WHERE id = ? AND activo = 1", (responsable_id,)
    ).fetchone()
    if responsable is None:
        conn.close()
        abort(400)  # el responsable no existe o está inactivo

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # El WHERE estado = 'Disponible' es la segunda barrera de seguridad:
    # si dos peticiones llegaran casi al mismo tiempo (ej. doble clic muy rápido),
    # la primera cambia el estado y la segunda ya no encuentra la fila para
    # actualizar (rowcount = 0), así que la frenamos acá también.
    cur = conn.execute(
        "UPDATE territorios SET estado = 'En trabajo' WHERE id = ? AND estado = 'Disponible'",
        (territorio_id,),
    )
    if cur.rowcount == 0:
        conn.close()
        flash(
            f"El territorio {territorio['numero']} ya no estaba disponible "
            "(alguien más lo asignó justo antes). Refrescá la página.",
            "error",
        )
        return redirect(url_for("territorio_detalle", territorio_id=territorio_id))

    conn.execute(
        """
        INSERT INTO asignaciones (territorio_id, responsable_id, fecha_asignado, detalles)
        VALUES (?, ?, ?, ?)
        """,
        (territorio_id, responsable_id, ahora, detalles),
    )
    conn.execute(
        """
        INSERT INTO actividad (territorio_id, responsable_id, tipo, descripcion, fecha)
        VALUES (?, ?, 'ASIGNACION', ?, ?)
        """,
        (
            territorio_id,
            responsable_id,
            f"Territorio {territorio['numero']} asignado a {responsable['nombre']}",
            ahora,
        ),
    )

    conn.commit()
    conn.close()

    return redirect(url_for("territorio_detalle", territorio_id=territorio_id))


@app.route("/territorio/<int:territorio_id>/finalizar", methods=["POST"])
def territorio_finalizar(territorio_id):
    """
    Cierra la asignación activa del territorio y lo vuelve a 'Disponible'.
    """
    conn = get_connection()

    territorio = conn.execute(
        "SELECT * FROM territorios WHERE id = ?", (territorio_id,)
    ).fetchone()
    if territorio is None:
        conn.close()
        abort(404)

    asignacion_activa = conn.execute(
        "SELECT * FROM asignaciones WHERE territorio_id = ? AND fecha_finalizacion IS NULL",
        (territorio_id,),
    ).fetchone()

    if asignacion_activa is None:
        # No había nada que finalizar (por ejemplo, doble clic). No rompemos nada,
        # simplemente volvemos al detalle sin hacer cambios.
        conn.close()
        return redirect(url_for("territorio_detalle", territorio_id=territorio_id))

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn.execute(
        "UPDATE asignaciones SET fecha_finalizacion = ? WHERE id = ?",
        (ahora, asignacion_activa["id"]),
    )
    conn.execute(
        "UPDATE territorios SET estado = 'Disponible' WHERE id = ?",
        (territorio_id,),
    )
    conn.execute(
        """
        INSERT INTO actividad (territorio_id, responsable_id, tipo, descripcion, fecha)
        VALUES (?, ?, 'FINALIZACION', ?, ?)
        """,
        (
            territorio_id,
            asignacion_activa["responsable_id"],
            f"Territorio {territorio['numero']} finalizado",
            ahora,
        ),
    )

    conn.commit()
    conn.close()

    return redirect(url_for("territorio_detalle", territorio_id=territorio_id))


@app.route("/territorio/<int:territorio_id>/actualizar-registro", methods=["POST"])
def actualizar_registro(territorio_id):
    """
    Guarda los cambios editables de UN registro telefónico:
    observaciones, no_llamar, funcionan, notas_internas.
    """
    registro_id = request.form.get("registro_id")
    if not registro_id:
        abort(400)

    # Checkbox: si no viene en el form es que estaba destildado
    no_llamar = 1 if request.form.get("no_llamar") else 0

    # Select con 3 valores posibles: "" (sin verificar), "1" (sí), "0" (no)
    funcionan_raw = request.form.get("funcionan", "")
    if funcionan_raw == "1":
        funcionan = 1
    elif funcionan_raw == "0":
        funcionan = 0
    else:
        funcionan = None

    observaciones = request.form.get("observaciones", "").strip() or None
    notas_internas = request.form.get("notas_internas", "").strip() or None

    conn = get_connection()

    # Verificamos que el registro exista Y pertenezca a este territorio
    # (evita que alguien edite un registro de otro territorio cambiando la URL)
    registro = conn.execute(
        "SELECT * FROM registros WHERE id = ? AND territorio_id = ?",
        (registro_id, territorio_id),
    ).fetchone()
    if registro is None:
        conn.close()
        abort(404)

    conn.execute(
        """
        UPDATE registros
        SET observaciones = ?, no_llamar = ?, funcionan = ?, notas_internas = ?
        WHERE id = ?
        """,
        (observaciones, no_llamar, funcionan, notas_internas, registro_id),
    )

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """
        INSERT INTO actividad (territorio_id, registro_id, tipo, descripcion, fecha)
        VALUES (?, ?, 'EDICION', ?, ?)
        """,
        (territorio_id, registro_id, f"Registro {registro['telefono']} actualizado", ahora),
    )

    conn.commit()
    conn.close()

    return redirect(url_for("territorio_detalle", territorio_id=territorio_id))


import math


@app.route("/responsables", methods=["GET", "POST"])
def responsables():
    """
    GET: lista responsables con búsqueda, filtros por estado, ordenamiento
    y paginación.
    POST: crea un nuevo responsable con nombre, teléfono y email opcionales.
    """
    conn = get_connection()

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip() or None
        email = request.form.get("email", "").strip() or None

        if not nombre:
            conn.close()
            flash("El nombre del responsable es obligatorio.", "error")
            return redirect(url_for("responsables"))

        fecha_alta = datetime.now().strftime("%Y-%m-%d")

        conn.execute(
            """
            INSERT INTO responsables (nombre, activo, telefono, email, fecha_alta)
            VALUES (?, 1, ?, ?, ?)
            """,
            (nombre, telefono, email, fecha_alta),
        )
        conn.commit()
        conn.close()

        flash(f"Responsable '{nombre}' agregado exitosamente.", "success")
        return redirect(url_for("responsables"))

    # --- GET: Filtros, Búsqueda, Orden y Paginación ---
    q = request.args.get("q", "").strip()
    estado = request.args.get("estado", "").strip()
    orden = request.args.get("orden", "nombre_asc")
    
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    per_page_raw = request.args.get("per_page", "10")
    if per_page_raw == "todos":
        per_page = 999999
    else:
        try:
            per_page = max(5, int(per_page_raw))
        except (ValueError, TypeError):
            per_page = 10

    sql = """
        SELECT
            r.id,
            r.nombre,
            r.activo,
            r.telefono,
            r.email,
            r.fecha_alta,
            (
                SELECT COUNT(*)
                FROM asignaciones a
                WHERE a.responsable_id = r.id AND a.fecha_finalizacion IS NULL
            ) AS territorios_asignados
        FROM responsables r
        WHERE 1=1
    """
    parametros = []

    if q:
        sql += " AND (r.nombre LIKE ? OR r.telefono LIKE ? OR r.email LIKE ?)"
        term = f"%{q}%"
        parametros.extend([term, term, term])

    if estado in ("0", "1"):
        sql += " AND r.activo = ?"
        parametros.append(int(estado))

    # Ordenamiento
    if orden == "nombre_desc":
        sql += " ORDER BY r.nombre COLLATE NOCASE DESC"
    elif orden == "territorios_desc":
        sql += " ORDER BY territorios_asignados DESC, r.nombre COLLATE NOCASE ASC"
    elif orden == "fecha_desc":
        sql += " ORDER BY (r.fecha_alta IS NULL), r.fecha_alta DESC, r.id DESC"
    elif orden == "fecha_asc":
        sql += " ORDER BY (r.fecha_alta IS NULL), r.fecha_alta ASC, r.id ASC"
    else:
        orden = "nombre_asc"
        sql += " ORDER BY r.activo DESC, r.nombre COLLATE NOCASE ASC"

    filas = conn.execute(sql, parametros).fetchall()
    conn.close()

    total_items = len(filas)
    total_pages = max(1, math.ceil(total_items / per_page)) if per_page_raw != "todos" else 1
    if page > total_pages:
        page = total_pages

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    items_paginados = filas[start_idx:end_idx]

    start_item = (start_idx + 1) if total_items > 0 else 0
    end_item = min(end_idx, total_items)

    return render_template(
        "responsables.html",
        responsables=items_paginados,
        total_items=total_items,
        total_pages=total_pages,
        page=page,
        per_page=per_page_raw,
        start_item=start_item,
        end_item=end_item,
        q=q,
        estado=estado,
        orden=orden,
    )


@app.route("/responsables/<int:responsable_id>/editar", methods=["POST"])
def responsable_editar(responsable_id):
    """Edita los datos (nombre, teléfono, email) de un responsable existente."""
    nombre = request.form.get("nombre", "").strip()
    telefono = request.form.get("telefono", "").strip() or None
    email = request.form.get("email", "").strip() or None

    if not nombre:
        flash("El nombre no puede estar vacío.", "error")
        return redirect(url_for("responsables", **request.args))

    conn = get_connection()
    resp = conn.execute("SELECT id FROM responsables WHERE id = ?", (responsable_id,)).fetchone()
    if resp is None:
        conn.close()
        abort(404)

    conn.execute(
        "UPDATE responsables SET nombre = ?, telefono = ?, email = ? WHERE id = ?",
        (nombre, telefono, email, responsable_id),
    )
    conn.commit()
    conn.close()

    flash(f"Responsable '{nombre}' actualizado correctamente.", "success")
    return redirect(url_for("responsables", **request.args))


@app.route("/responsables/<int:responsable_id>/desactivar", methods=["POST"])
def responsable_desactivar(responsable_id):
    """
    Desactiva un responsable (no lo borra: activo = 0).
    Así se conserva el historial de asignaciones pasadas donde participó.
    """
    conn = get_connection()
    responsable = conn.execute(
        "SELECT * FROM responsables WHERE id = ?", (responsable_id,)
    ).fetchone()
    if responsable is None:
        conn.close()
        abort(404)

    conn.execute("UPDATE responsables SET activo = 0 WHERE id = ?", (responsable_id,))
    conn.commit()
    conn.close()

    flash(f"Responsable '{responsable['nombre']}' desactivado.", "warning")
    return redirect(url_for("responsables", **request.args))


@app.route("/responsables/<int:responsable_id>/activar", methods=["POST"])
def responsable_activar(responsable_id):
    """Reactiva un responsable que estaba desactivado."""
    conn = get_connection()
    responsable = conn.execute(
        "SELECT * FROM responsables WHERE id = ?", (responsable_id,)
    ).fetchone()
    if responsable is None:
        conn.close()
        abort(404)

    conn.execute("UPDATE responsables SET activo = 1 WHERE id = ?", (responsable_id,))
    conn.commit()
    conn.close()

    flash(f"Responsable '{responsable['nombre']}' reactivado.", "success")
    return redirect(url_for("responsables", **request.args))


@app.route("/responsables/lote", methods=["POST"])
def responsables_lote():
    """Ejecuta acciones masivas (desactivar / activar) sobre múltiples responsables seleccionados."""
    accion = request.form.get("accion")
    ids = request.form.getlist("responsables_ids")

    if not ids:
        flash("No seleccionaste ningún responsable para la acción en lote.", "warning")
        return redirect(url_for("responsables", **request.args))

    if accion not in ("desactivar", "activar"):
        flash("Acción en lote no reconocida.", "error")
        return redirect(url_for("responsables", **request.args))

    nuevo_estado = 0 if accion == "desactivar" else 1
    placeholders = ",".join("?" for _ in ids)

    conn = get_connection()
    conn.execute(
        f"UPDATE responsables SET activo = ? WHERE id IN ({placeholders})",
        [nuevo_estado] + [int(i) for i in ids],
    )
    conn.commit()
    conn.close()

    verbo = "desactivaron" if accion == "desactivar" else "reactivaron"
    flash(f"Se {verbo} {len(ids)} responsable(s) en lote exitosamente.", "success")
    return redirect(url_for("responsables", **request.args))


@app.route("/importar-excel", methods=["GET", "POST"])
def importar_excel_view():
    """
    GET: muestra el formulario para subir el archivo.
    POST: procesa el Excel y hace upsert en territorios/registros.
    """
    if request.method == "GET":
        return render_template("importar_excel.html")

    archivo = request.files.get("archivo")
    if archivo is None or archivo.filename == "":
        flash("Tenés que elegir un archivo .xlsx primero.", "error")
        return redirect(url_for("importar_excel_view"))

    if not archivo.filename.lower().endswith((".xlsx", ".xlsm")):
        flash("El archivo tiene que ser un Excel (.xlsx).", "error")
        return redirect(url_for("importar_excel_view"))

    conn = get_connection()
    try:
        resumen = importar_excel(archivo, conn)
    except ValueError as e:
        conn.rollback()
        flash(str(e), "error")
        return redirect(url_for("importar_excel_view"))
    except Exception as e:
        conn.rollback()
        flash(f"Error inesperado durante la importación: {e}", "error")
        return redirect(url_for("importar_excel_view"))
    finally:
        conn.close()

    mensaje = (
        f"Importación terminada: {resumen['territorios_creados']} territorios creados, "
        f"{resumen['registros_insertados']} registros nuevos, "
        f"{resumen['registros_actualizados']} registros actualizados, "
        f"{resumen['errores']} filas con errores."
    )
    flash(mensaje, "success" if resumen["errores"] == 0 else "warning")

    if resumen["detalle_errores"]:
        for err in resumen["detalle_errores"][:10]:  # no inundamos la pantalla
            flash(err, "error")

    return redirect(url_for("importar_excel_view"))


@app.route("/importar-historial", methods=["GET", "POST"])
def importar_historial_view():
    """
    GET: muestra el formulario para subir el Excel de Historial de Asignaciones
    (columnas: Territorio, Responsable, Fecha asignado, Fecha completado, Detalles).
    POST: lo procesa y hace upsert en responsables/territorios/asignaciones.
    """
    if request.method == "GET":
        return render_template("importar_historial.html")

    archivo = request.files.get("archivo")
    if archivo is None or archivo.filename == "":
        flash("Tenés que elegir un archivo .xlsx primero.", "error")
        return redirect(url_for("importar_historial_view"))

    if not archivo.filename.lower().endswith((".xlsx", ".xlsm")):
        flash("El archivo tiene que ser un Excel (.xlsx).", "error")
        return redirect(url_for("importar_historial_view"))

    conn = get_connection()
    try:
        resumen = importar_historial(archivo, conn)
    except ValueError as e:
        conn.rollback()
        flash(str(e), "error")
        return redirect(url_for("importar_historial_view"))
    except Exception as e:
        conn.rollback()
        flash(f"Error inesperado durante la importación: {e}", "error")
        return redirect(url_for("importar_historial_view"))
    finally:
        conn.close()

    mensaje = (
        f"Importación de historial terminada: {resumen['responsables_creados']} responsables creados, "
        f"{resumen['territorios_creados']} territorios creados, "
        f"{resumen['asignaciones_insertadas']} asignaciones nuevas, "
        f"{resumen['asignaciones_actualizadas']} asignaciones actualizadas, "
        f"{resumen['errores']} filas con errores."
    )
    flash(mensaje, "success" if resumen["errores"] == 0 else "warning")

    if resumen["detalle_errores"]:
        for err in resumen["detalle_errores"][:10]:  # no inundamos la pantalla
            flash(err, "error")

    return redirect(url_for("importar_historial_view"))


@app.route("/exportar/excel")
def exportar_excel():
    """
    Descarga un Excel con todos los registros, o filtrado por
    ?territorio_id=X si viene ese parámetro.
    """
    territorio_id = request.args.get("territorio_id")

    conn = get_connection()

    sql = """
        SELECT
            reg.*,
            t.numero AS numero_territorio
        FROM registros reg
        JOIN territorios t ON t.id = reg.territorio_id
    """
    parametros = ()
    if territorio_id:
        sql += " WHERE reg.territorio_id = ?"
        parametros = (territorio_id,)
    sql += " ORDER BY CAST(t.numero AS INTEGER), reg.id"

    registros = conn.execute(sql, parametros).fetchall()
    conn.close()

    buffer = generar_excel(registros)

    nombre_archivo = (
        f"territorio_{territorio_id}.xlsx" if territorio_id else "registros_completos.xlsx"
    )

    return send_file(
        buffer,
        as_attachment=True,
        download_name=nombre_archivo,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/territorio/<int:territorio_id>/exportar/pdf")
def territorio_exportar_pdf(territorio_id):
    """Genera y descarga el PDF imprimible del territorio."""
    conn = get_connection()

    territorio = conn.execute(
        "SELECT * FROM territorios WHERE id = ?", (territorio_id,)
    ).fetchone()
    if territorio is None:
        conn.close()
        abort(404)

    registros = conn.execute(
        "SELECT * FROM registros WHERE territorio_id = ? ORDER BY id",
        (territorio_id,),
    ).fetchall()
    conn.close()

    buffer = generar_pdf(territorio, registros)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"territorio_{territorio['numero']}.pdf",
        mimetype="application/pdf",
    )


@app.route("/territorio/<int:territorio_id>/exportar/png")
def territorio_exportar_png(territorio_id):
    """Genera y descarga una imagen PNG rápida del territorio."""
    conn = get_connection()

    territorio = conn.execute(
        "SELECT * FROM territorios WHERE id = ?", (territorio_id,)
    ).fetchone()
    if territorio is None:
        conn.close()
        abort(404)

    registros = conn.execute(
        "SELECT * FROM registros WHERE territorio_id = ? ORDER BY id",
        (territorio_id,),
    ).fetchall()
    conn.close()

    buffer = generar_png(territorio, registros)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"territorio_{territorio['numero']}.png",
        mimetype="image/png",
    )


if __name__ == "__main__":
    # debug=True: reinicia el servidor solo al guardar cambios,
    # y muestra errores detallados en el navegador. Muy útil mientras aprendés.
    app.run(debug=True, port=5000)
