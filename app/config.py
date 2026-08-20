"""Configuración centralizada y segura por entorno."""

import os
import secrets


def _as_bool(name, default):
    value = os.environ.get(name)
    return default if not value else value.strip().lower() in {"1", "true", "si", "sí", "yes", "on"}


class Config:
    DEBUG = _as_bool("FLASK_DEBUG", True)
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
