"""
routes/territorios.py
---------------------
Rutas para la gestión y visualización de territorios y sus asignaciones:
- Listado principal (index) con filtros y ordenamiento
- Vista de detalle de territorio
- Historial de asignaciones y actividades
- Asignación y finalización de trabajo en territorios
"""

from datetime import datetime
from flask import render_template, request, abort, redirect, url_for, flash
from database import get_connection


def register_territorios(app):
    @app.route("/")
    def index():
        """
        Lista de territorios con filtros: búsqueda por número (q), estado,
        responsable asignado (responsable_id) y orden (numero / antiguos / recientes).
        Calcula métricas globales para las tarjetas KPI superiores.
        """
        q = request.args.get("q", "").strip()
        estado = request.args.get("estado", "").strip()
        responsable_id = request.args.get("responsable_id", "").strip()
        orden = request.args.get("orden", "numero")

        conn = get_connection()

        # Métricas globales para los KPI cards
        total_territorios = conn.execute("SELECT COUNT(*) FROM territorios").fetchone()[0]
        total_en_trabajo = conn.execute(
            "SELECT COUNT(*) FROM territorios WHERE estado = 'En trabajo'"
        ).fetchone()[0]
        total_disponibles = conn.execute(
            "SELECT COUNT(*) FROM territorios WHERE estado = 'Disponible'"
        ).fetchone()[0]
        total_lineas = conn.execute("SELECT COUNT(*) FROM registros").fetchone()[0]

        # LEFT JOIN con asignaciones activas y registros para conteo de líneas
        sql = """
            SELECT
                t.id,
                t.numero,
                t.estado,
                r.id AS responsable_id,
                r.nombre AS responsable,
                a.fecha_asignado,
                COUNT(DISTINCT reg.id) AS total_lineas_territorio
            FROM territorios t
            LEFT JOIN asignaciones a
                ON a.territorio_id = t.id AND a.fecha_finalizacion IS NULL
            LEFT JOIN responsables r
                ON r.id = a.responsable_id
            LEFT JOIN registros reg
                ON reg.territorio_id = t.id
            WHERE (t.numero LIKE ? OR r.nombre LIKE ?)
        """
        param_q = f"%{q}%"
        parametros = [param_q, param_q]

        if estado in ("Disponible", "En trabajo"):
            sql += " AND t.estado = ?"
            parametros.append(estado)

        if responsable_id:
            sql += " AND a.responsable_id = ?"
            parametros.append(responsable_id)

        sql += " GROUP BY t.id"

        if orden == "antiguos":
            sql += " ORDER BY (a.fecha_asignado IS NULL), a.fecha_asignado ASC"
        elif orden == "recientes":
            sql += " ORDER BY (a.fecha_asignado IS NULL), a.fecha_asignado DESC"
        elif orden == "lineas":
            sql += " ORDER BY total_lineas_territorio DESC"
        else:
            orden = "numero"
            sql += " ORDER BY CAST(t.numero AS INTEGER), t.numero ASC"

        if orden == "disponibles":
            # Ordenar por más tiempo disponible requiere la fecha en la que
            # cada territorio quedó libre, que se calcula más abajo (no es
            # una columna directa de la tabla). Por eso acá dejamos el orden
            # por número como base y reordenamos en Python al final.
            sql += " ORDER BY CAST(t.numero AS INTEGER), t.numero ASC"

        filas = conn.execute(sql, parametros).fetchall()

        # Responsables para el select del filtro
        responsables = conn.execute(
            "SELECT id, nombre FROM responsables ORDER BY activo DESC, nombre"
        ).fetchall()

        # Fecha en la que cada territorio quedó disponible por última vez:
        # la fecha_finalizacion de su asignación cerrada más reciente. Si el
        # territorio nunca fue asignado, se usa su fecha de creación (evento
        # 'CREACION' en la tabla de actividad) como aproximación razonable.
        mapa_ultima_finalizacion = {
            fila["territorio_id"]: fila["fecha"]
            for fila in conn.execute(
                """
                SELECT territorio_id, MAX(fecha_finalizacion) AS fecha
                FROM asignaciones
                WHERE fecha_finalizacion IS NOT NULL
                GROUP BY territorio_id
                """
            ).fetchall()
        }
        mapa_fecha_creacion = {
            fila["territorio_id"]: fila["fecha"]
            for fila in conn.execute(
                """
                SELECT territorio_id, MIN(fecha) AS fecha
                FROM actividad
                WHERE tipo = 'CREACION'
                GROUP BY territorio_id
                """
            ).fetchall()
        }

        conn.close()

        ahora = datetime.now()
        territorios = []
        for fila in filas:
            t = dict(fila)
            if t["estado"] == "En trabajo" and t["fecha_asignado"]:
                try:
                    fecha_dt = datetime.strptime(t["fecha_asignado"], "%Y-%m-%d %H:%M:%S")
                    dias = (ahora - fecha_dt).days
                    plural = "" if dias == 1 else "s"
                    t["asignado_texto"] = f"{fecha_dt.strftime('%d/%m/%Y')} ({dias} día{plural})"
                    t["asignado_dias"] = dias
                except Exception:
                    t["asignado_texto"] = str(t["fecha_asignado"])
                    t["asignado_dias"] = 0
            else:
                t["asignado_texto"] = "—"
                t["asignado_dias"] = -1

            # Columna "Disponible hace": solo tiene sentido para territorios
            # que están libres ahora mismo.
            t["disponible_texto"] = "—"
            t["disponible_dias"] = -1
            if t["estado"] == "Disponible":
                fecha_disp = mapa_ultima_finalizacion.get(t["id"]) or mapa_fecha_creacion.get(t["id"])
                if fecha_disp:
                    try:
                        fecha_dt = datetime.strptime(fecha_disp, "%Y-%m-%d %H:%M:%S")
                        dias = (ahora - fecha_dt).days
                        plural = "" if dias == 1 else "s"
                        t["disponible_texto"] = f"{fecha_dt.strftime('%d/%m/%Y')} ({dias} día{plural})"
                        t["disponible_dias"] = dias
                    except Exception:
                        pass

            territorios.append(t)

        if orden == "disponibles":
            # Más tiempo disponible primero; los que no están disponibles
            # (dias == -1) van al final.
            territorios.sort(
                key=lambda t: (t["disponible_dias"] == -1, -t["disponible_dias"])
            )

        return render_template(
            "index.html",
            territorios=territorios,
            q=q,
            estado=estado,
            responsable_id=responsable_id,
            orden=orden,
            responsables=responsables,
            total_territorios=total_territorios,
            total_en_trabajo=total_en_trabajo,
            total_disponibles=total_disponibles,
            total_lineas=total_lineas,
        )

    @app.route("/territorios/nuevo", methods=["POST"])
    def nuevo_territorio():
        """
        Crea un nuevo territorio rápidamente.
        """
        numero = request.form.get("numero", "").strip()
        if not numero:
            flash("El número de territorio es obligatorio.", "error")
            return redirect(url_for("index"))

        conn = get_connection()
        existente = conn.execute(
            "SELECT id FROM territorios WHERE numero = ?", (numero,)
        ).fetchone()

        if existente:
            conn.close()
            flash(f"El territorio N.° {numero} ya existe.", "error")
            return redirect(url_for("index"))

        cur = conn.execute(
            "INSERT INTO territorios (numero, estado) VALUES (?, 'Disponible')",
            (numero,)
        )
        nuevo_id = cur.lastrowid
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO actividad (territorio_id, tipo, descripcion, fecha) VALUES (?, 'CREACION', ?, ?)",
            (nuevo_id, f"Territorio {numero} creado", ahora)
        )
        conn.commit()
        conn.close()

        flash(f"Territorio N.° {numero} creado exitosamente.", "success")
        return redirect(url_for("territorio_detalle", territorio_id=nuevo_id))


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


    @app.route("/territorio/<int:territorio_id>/eliminar", methods=["POST"])
    def territorio_eliminar(territorio_id):
        """
        Elimina definitivamente un territorio junto con sus registros,
        asignaciones e historial de actividad asociados.
        """
        conn = get_connection()

        territorio = conn.execute(
            "SELECT * FROM territorios WHERE id = ?", (territorio_id,)
        ).fetchone()

        if territorio is None:
            conn.close()
            abort(404)

        numero = territorio["numero"]

        conn.execute("DELETE FROM actividad WHERE territorio_id = ?", (territorio_id,))
        conn.execute("DELETE FROM asignaciones WHERE territorio_id = ?", (territorio_id,))
        conn.execute("DELETE FROM registros WHERE territorio_id = ?", (territorio_id,))
        conn.execute("DELETE FROM territorios WHERE id = ?", (territorio_id,))
        conn.commit()
        conn.close()

        flash(f"Territorio N.° {numero} eliminado definitivamente.", "success")
        return redirect(url_for("index"))


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

        # No asumimos que queda "Disponible": recalculamos el estado mirando
        # si queda alguna OTRA asignación abierta para este territorio. En
        # uso normal no debería quedar ninguna (el índice único de la base
        # ya impide que existan dos a la vez), pero si la base tuviera datos
        # importados de otra forma, esto evita dejar el territorio marcado
        # como libre cuando en realidad sigue con trabajo abierto.
        sigue_abierta = conn.execute(
            "SELECT 1 FROM asignaciones WHERE territorio_id = ? AND fecha_finalizacion IS NULL",
            (territorio_id,),
        ).fetchone()
        nuevo_estado = "En trabajo" if sigue_abierta else "Disponible"
        conn.execute(
            "UPDATE territorios SET estado = ? WHERE id = ?",
            (nuevo_estado, territorio_id),
        )
        if sigue_abierta:
            flash(
                f"Se finalizó esa asignación, pero el territorio {territorio['numero']} "
                "sigue 'En trabajo' porque tiene otra asignación abierta.",
                "warning",
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


