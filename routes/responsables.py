"""
routes/responsables.py
----------------------
Rutas para la gestión de responsables/publicadores:
- Listado con filtros, ordenamiento y paginación
- Creación de nuevo responsable
- Edición de datos de contacto
- Activación/desactivación individual
- Acciones masivas en lote
"""

from datetime import datetime
from flask import Blueprint, render_template, request, abort, redirect, url_for, flash
from database import get_connection


bp = Blueprint("responsables", __name__)


def register_responsables(app):
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

        # Con este volumen de datos (decenas de responsables) filtrar/ordenar
        # en el servidor y paginar de vuelta era más complejo que el beneficio
        # que aportaba, y era la causa de un bug real: al cambiar el filtro o
        # el orden en el cliente, solo se recalculaba sobre las filas de la
        # página ya cargada, no sobre el total. Ahora el servidor entrega
        # siempre la lista completa y static/js/responsables.js resuelve
        # búsqueda, filtro, orden y paginación 100% en el cliente sobre el
        # total real (ver docs/Plan_de_Refactorización_y_Arquitectura.pdf,
        # sección 1.4, criterio "volumen bajo").
        #
        # `page` y `per_page` se siguen aceptando y devolviendo solo para
        # poder pre-seleccionar los controles de paginación al cargar la
        # página (por ejemplo, un link compartido con ?per_page=20&page=2) y
        # para preservarlos en los redirects de las acciones de abajo.
        try:
            page = max(1, int(request.args.get("page", 1)))
        except (ValueError, TypeError):
            page = 1
        per_page_raw = request.args.get("per_page", "10")

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
        """

        # Ordenamiento (el filtrado por q/estado ahora es exclusivamente
        # client-side; el orden se mantiene en el servidor para que la
        # tabla ya aparezca ordenada en el primer render, sin parpadeo).
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

        responsables_todos = conn.execute(sql).fetchall()
        conn.close()

        return render_template(
            "responsables.html",
            responsables=responsables_todos,
            total_items=len(responsables_todos),
            page=page,
            per_page=per_page_raw,
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


register_responsables(bp)


