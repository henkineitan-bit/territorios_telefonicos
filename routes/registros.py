"""
routes/registros.py
-------------------
Rutas para la gestión y exportación de registros telefónicos:
- Actualización inline de registros (observaciones, no llamar, funcionan)
- Importación masiva desde Excel de registros
- Importación masiva de historial de asignaciones
- Exportación a Excel, PDF y PNG
"""

from datetime import datetime
from flask import render_template, request, abort, redirect, url_for, flash, send_file
from database import get_connection
from exports import (
    importar_excel,
    generar_excel,
    generar_pdf,
    generar_png,
    importar_historial,
)


def register_registros(app):
    @app.route("/territorio/<int:territorio_id>/actualizar-registro", methods=["POST"])
    def actualizar_registro(territorio_id):
        """
        Guarda los cambios editables de UN registro telefónico:
        dirección, teléfono, observaciones, no_llamar, funcionan, notas_internas.
        """
        registro_id = request.form.get("registro_id")
        if not registro_id:
            abort(400)

        direccion = request.form.get("direccion", "").strip() or None
        telefono = request.form.get("telefono", "").strip()

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
        registro = conn.execute(
            "SELECT * FROM registros WHERE id = ? AND territorio_id = ?",
            (registro_id, territorio_id),
        ).fetchone()
        if registro is None:
            conn.close()
            abort(404)

        if not telefono:
            telefono = registro["telefono"]

        conn.execute(
            """
            UPDATE registros
            SET direccion = ?, telefono = ?, observaciones = ?, no_llamar = ?, funcionan = ?, notas_internas = ?
            WHERE id = ?
            """,
            (direccion, telefono, observaciones, no_llamar, funcionan, notas_internas, registro_id),
        )

        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            """
            INSERT INTO actividad (territorio_id, registro_id, tipo, descripcion, fecha)
            VALUES (?, ?, 'EDICION', ?, ?)
            """,
            (territorio_id, registro_id, f"Registro {telefono} actualizado", ahora),
        )

        conn.commit()
        conn.close()

        flash(f"Registro {telefono} actualizado correctamente.", "success")
        return redirect(url_for("territorio_detalle", territorio_id=territorio_id))

    @app.route("/territorio/<int:territorio_id>/nuevo-registro", methods=["POST"])
    def nuevo_registro(territorio_id):
        """
        Agrega un nuevo registro telefónico al territorio.
        """
        telefono = request.form.get("telefono", "").strip()
        if not telefono:
            flash("El número de teléfono es obligatorio.", "error")
            return redirect(url_for("territorio_detalle", territorio_id=territorio_id))

        direccion = request.form.get("direccion", "").strip() or None
        observaciones = request.form.get("observaciones", "").strip() or None
        notas_internas = request.form.get("notas_internas", "").strip() or None
        no_llamar = 1 if request.form.get("no_llamar") else 0

        funcionan_raw = request.form.get("funcionan", "")
        if funcionan_raw == "1":
            funcionan = 1
        elif funcionan_raw == "0":
            funcionan = 0
        else:
            funcionan = None

        conn = get_connection()
        cur = conn.execute(
            """
            INSERT INTO registros (territorio_id, direccion, telefono, observaciones, no_llamar, funcionan, notas_internas)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (territorio_id, direccion, telefono, observaciones, no_llamar, funcionan, notas_internas),
        )
        nuevo_id = cur.lastrowid
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            """
            INSERT INTO actividad (territorio_id, registro_id, tipo, descripcion, fecha)
            VALUES (?, ?, 'CREACION', ?, ?)
            """,
            (territorio_id, nuevo_id, f"Registro {telefono} agregado", ahora),
        )
        conn.commit()
        conn.close()

        flash(f"Registro {telefono} agregado exitosamente.", "success")
        return redirect(url_for("territorio_detalle", territorio_id=territorio_id))

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

