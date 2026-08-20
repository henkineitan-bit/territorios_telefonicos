"""Consultas de persistencia de responsables."""


class ResponsablesRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_active(self, responsable_id):
        return self.connection.execute("SELECT * FROM responsables WHERE id = ? AND activo = 1", (responsable_id,)).fetchone()
