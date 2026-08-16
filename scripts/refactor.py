import os

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def extract_funcs(lines, funcs_to_extract):
    out = []
    in_func = False
    for i, line in enumerate(lines):
        if line.startswith('@app.route('):
            nxt = lines[i+1]
            if nxt.startswith('def '):
                name = nxt.split('(')[0][4:].strip()
                if name in funcs_to_extract:
                    in_func = True
        
        if in_func:
            out.append(line)
            if i > 0 and i+1 < len(lines):
                # We also need to ignore 'import math' which is between routes
                if lines[i+1].startswith('@app.route') or lines[i+1].startswith('import ') or (lines[i+1].startswith('def ') and not lines[i+1].startswith('    ')) or lines[i+1].startswith('if __name__'):
                    in_func = False
    return "".join(out)


territorios_funcs = ['index', 'territorio_detalle', 'territorio_historial', 'territorio_asignar', 'territorio_finalizar']
responsables_funcs = ['responsables', 'responsable_editar', 'responsable_desactivar', 'responsable_activar', 'responsables_lote']
registros_funcs = ['actualizar_registro', 'importar_excel_view', 'importar_historial_view', 'exportar_excel', 'territorio_exportar_pdf', 'territorio_exportar_png']

header_territorios = """from flask import render_template, request, abort, redirect, url_for, flash
from datetime import datetime
from database import get_connection

def register_territorios(app):
"""

header_responsables = """from flask import render_template, request, abort, redirect, url_for, flash
from datetime import datetime
from database import get_connection
import math

def register_responsables(app):
"""

header_registros = """from flask import render_template, request, abort, redirect, url_for, flash, send_file
from datetime import datetime
from database import get_connection
from exports import importar_excel, generar_excel, generar_pdf, generar_png, importar_historial

def register_registros(app):
"""

def process_file(header, funcs, output_path):
    code = extract_funcs(lines, funcs)
    indented_code = ""
    for line in code.split('\n'):
        if line:
            indented_code += "    " + line + "\n"
        else:
            indented_code += "\n"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header + indented_code)

process_file(header_territorios, territorios_funcs, 'routes/territorios.py')
process_file(header_responsables, responsables_funcs, 'routes/responsables.py')
process_file(header_registros, registros_funcs, 'routes/registros.py')

app_code = """\"\"\"
app.py
------
Punto de entrada de la aplicación Flask.
\"\"\"
from flask import Flask
from routes.territorios import register_territorios
from routes.responsables import register_responsables
from routes.registros import register_registros

app = Flask(__name__)
app.secret_key = "dev-secret-key-cambiar-en-produccion"

register_territorios(app)
register_responsables(app)
register_registros(app)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
"""

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)

print("Refactor completed successfully")
