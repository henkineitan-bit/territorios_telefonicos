"""
app.py
------
Punto de entrada de la aplicación Flask.
Las rutas están divididas lógicamente en la carpeta `routes/`.
"""

from flask import Flask
from routes.territorios import register_territorios
from routes.responsables import register_responsables
from routes.registros import register_registros

app = Flask(__name__)
app.secret_key = "dev-secret-key-cambiar-en-produccion"  # necesario para usar flash()

# Registrar todas las rutas de los distintos módulos
register_territorios(app)
register_responsables(app)
register_registros(app)

if __name__ == "__main__":
    # debug=True: reinicia el servidor solo al guardar cambios,
    # y muestra errores detallados en el navegador. Muy útil mientras aprendés.
    app.run(debug=True, port=5000)
