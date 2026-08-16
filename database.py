"""
database.py
------------
Se encarga de dos cosas:
1. Crear (o conectar con) el archivo territorios.db
2. Ejecutar el esquema (schema.sql) para crear las tablas si no existen

Cómo usarlo:
    python database.py
Esto crea el archivo territorios.db en la misma carpeta, con las 5 tablas
definidas en schema.sql.
"""

import sqlite3
import os

# Rutas absolutas, para que funcione sin importar desde dónde se ejecute
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "data", "territorios.db")
SCHEMA = os.path.join(BASE_DIR, "schema.sql")


def migrate_db(conn=None):
    """
    Verifica y aplica migraciones incrementales sobre la base de datos existente
    sin alterar ni perder datos previos.
    """
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    cursor = conn.cursor()
    # Obtenemos las columnas actuales de 'responsables'
    cursor.execute("PRAGMA table_info(responsables)")
    columnas = [col["name"] for col in cursor.fetchall()]

    if "telefono" not in columnas:
        cursor.execute("ALTER TABLE responsables ADD COLUMN telefono TEXT DEFAULT NULL")
    if "email" not in columnas:
        cursor.execute("ALTER TABLE responsables ADD COLUMN email TEXT DEFAULT NULL")
    if "fecha_alta" not in columnas:
        cursor.execute("ALTER TABLE responsables ADD COLUMN fecha_alta TEXT DEFAULT NULL")
        # Asignamos la fecha de hoy como fecha de alta a los registros previos que no tengan
        cursor.execute("UPDATE responsables SET fecha_alta = date('now') WHERE fecha_alta IS NULL")

    conn.commit()
    if should_close:
        conn.close()


def get_connection():
    """
    Devuelve una conexión a la base de datos.
    row_factory = sqlite3.Row permite acceder a las columnas por nombre,
    por ejemplo: fila["numero"] en lugar de fila[0]
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    # Activa las claves foráneas (SQLite las trae desactivadas por defecto)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    Lee schema.sql y ejecuta todas las sentencias CREATE TABLE.
    Como usan "IF NOT EXISTS", se puede correr varias veces sin problema:
    no borra datos existentes.
    """
    conn = get_connection()
    with open(SCHEMA, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    migrate_db(conn)
    conn.commit()
    conn.close()
    print(f"Base de datos inicializada correctamente en: {DATABASE}")


if __name__ == "__main__":
    init_db()

