"""Fábrica de la aplicación y composición de sus controladores HTTP."""

from flask import Flask

from .config import Config


def create_app(config_object=Config):
    """Crea una instancia Flask aislada y registra sus Blueprints."""
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_object)

    # Importar aquí evita dependencias circulares durante la creación.
    from .blueprints.registros import bp as registros_bp
    from .blueprints.responsables import bp as responsables_bp
    from .blueprints.territorios import bp as territorios_bp

    app.register_blueprint(territorios_bp)
    app.register_blueprint(responsables_bp)
    app.register_blueprint(registros_bp)
    return app
