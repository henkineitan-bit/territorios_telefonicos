"""Conexiones SQLite y migraciones numeradas de la aplicación."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "territorios.db"
SCHEMA_PATH = PROJECT_ROOT / "schema.sql"
MIGRATIONS = (
    (1, "Agregar teléfono a responsables", "ALTER TABLE responsables ADD COLUMN telefono TEXT DEFAULT NULL"),
    (2, "Agregar email a responsables", "ALTER TABLE responsables ADD COLUMN email TEXT DEFAULT NULL"),
    (3, "Agregar fecha de alta a responsables", "ALTER TABLE responsables ADD COLUMN fecha_alta TEXT DEFAULT NULL"),
)


def get_connection():
    """Devuelve una conexión con filas direccionables por nombre."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def transaction():
    """Agrupa una operación de negocio en una transacción atómica."""
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def apply_migrations(connection):
    connection.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    applied = {row["version"] for row in connection.execute("SELECT version FROM schema_migrations")}
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(responsables)")}
    for version, name, sql in MIGRATIONS:
        if version not in applied:
            column = sql.split(" ADD COLUMN ", 1)[1].split()[0]
            if column not in columns:
                connection.execute(sql)
            connection.execute("INSERT INTO schema_migrations (version, name) VALUES (?, ?)", (version, name))


def init_db():
    """Crea el esquema base y aplica migraciones pendientes sin perder datos."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with transaction() as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        apply_migrations(connection)
