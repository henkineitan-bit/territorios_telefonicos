"""
app.py
------
Punto de entrada de la aplicación Flask.
Las rutas están divididas lógicamente en la carpeta `routes/`.

Configuración por variables de entorno (todas opcionales para el uso local
de siempre: si no se define ninguna, la app arranca exactamente igual que
antes, sin pedir nada extra):

- FLASK_DEBUG: "true" o "false" (default: "true"). Con debug activado el
  servidor se reinicia solo al guardar cambios y muestra el depurador de
  Flask en el navegador ante un error. Es cómodo para uso local, pero NO
  debe quedar activado si la app se va a compartir en la red con otras PCs.

- FLASK_SECRET_KEY: clave secreta usada para firmar la sesión (la necesita
  flash() para mostrar los mensajes de éxito/error). Con FLASK_DEBUG activado
  (el default) no hace falta configurarla: se genera una automáticamente en
  cada arranque. Si se desactiva el debug (FLASK_DEBUG=false), esta variable
  pasa a ser OBLIGATORIA — la app no arranca sin ella, para no quedar nunca
  con una clave fija y conocida en una instalación compartida.

- FLASK_HOST: host de escucha (default: "127.0.0.1", o sea solo esta PC).
  Poné "0.0.0.0" únicamente si vas a compartir la app en tu red local, y
  después de haber desactivado el modo debug.

- FLASK_PORT: puerto de escucha (default: 5000).
"""

import os
import secrets

from flask import Flask
from routes.territorios import register_territorios
from routes.responsables import register_responsables
from routes.registros import register_registros


def _leer_bool_env(nombre, default):
    """Lee una variable de entorno tipo 'true'/'false' de forma tolerante."""
    valor = os.environ.get(nombre)
    if valor is None or valor.strip() == "":
        return default
    return valor.strip().lower() in ("1", "true", "si", "sí", "yes", "on")


DEBUG = _leer_bool_env("FLASK_DEBUG", default=True)

secret_key = os.environ.get("FLASK_SECRET_KEY")
if not secret_key:
    if DEBUG:
        # Uso local de siempre: no hace falta configurar nada a mano.
        # Se genera una clave aleatoria en cada arranque; como la app no
        # tiene login ni datos sensibles en la sesión, alcanza y sobra.
        secret_key = secrets.token_hex(32)
    else:
        raise RuntimeError(
            "Falta la variable de entorno FLASK_SECRET_KEY. Es obligatoria "
            "cuando FLASK_DEBUG está desactivado (por ejemplo, para compartir "
            "la app en la red local con otras PCs). Definila antes de iniciar "
            "la aplicación y volvé a intentar."
        )

app = Flask(__name__)
app.secret_key = secret_key

# Registrar todas las rutas de los distintos módulos
register_territorios(app)
register_responsables(app)
register_registros(app)

if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    app.run(debug=DEBUG, host=host, port=port)
