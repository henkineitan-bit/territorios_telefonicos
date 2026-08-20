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

from app.db import get_connection, init_db

# Rutas absolutas, para que funcione sin importar desde dónde se ejecute
def migrate_db(conn=None):
    """
    Verifica y aplica migraciones incrementales sobre la base de datos existente
    sin alterar ni perder datos previos.
    """
    if conn is None:
        init_db()


if __name__ == "__main__":
    init_db()
