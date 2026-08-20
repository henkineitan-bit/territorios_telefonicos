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
    _register_legacy_endpoint_aliases(app)
    return app


def _register_legacy_endpoint_aliases(app):
    """Mantiene compatibles los ``url_for`` de las plantillas existentes.

    Los Blueprints califican los endpoints como ``territorios.index``. Las
    plantillas anteriores usaban ``index``; durante esta transición ambos
    nombres deben construir la misma URL.
    """
    prefixes = ("territorios.", "responsables.", "registros.")
    for rule in list(app.url_map.iter_rules()):
        prefix = next((item for item in prefixes if rule.endpoint.startswith(item)), None)
        if prefix is None:
            continue
        legacy_endpoint = rule.endpoint.removeprefix(prefix)
        app.add_url_rule(
            rule.rule,
            endpoint=legacy_endpoint,
            view_func=app.view_functions[rule.endpoint],
            methods=rule.methods,
            defaults=rule.defaults,
            strict_slashes=rule.strict_slashes,
            provide_automatic_options=False,
        )
