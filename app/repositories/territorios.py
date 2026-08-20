"""Consultas de persistencia de territorios y asignaciones."""


class TerritoriosRepository:
    def __init__(self, connection):
        self.connection = connection

    def get(self, territorio_id):
        return self.connection.execute("SELECT * FROM territorios WHERE id = ?", (territorio_id,)).fetchone()

    def get_active_assignment(self, territorio_id):
        return self.connection.execute("SELECT * FROM asignaciones WHERE territorio_id = ? AND fecha_finalizacion IS NULL", (territorio_id,)).fetchone()

    def mark_assigned(self, territorio_id):
        return self.connection.execute("UPDATE territorios SET estado = 'En trabajo' WHERE id = ? AND estado = 'Disponible'", (territorio_id,))

    def close_assignment(self, assignment_id, finished_at):
        self.connection.execute("UPDATE asignaciones SET fecha_finalizacion = ? WHERE id = ?", (finished_at, assignment_id))

    def set_status(self, territorio_id, status):
        self.connection.execute("UPDATE territorios SET estado = ? WHERE id = ?", (status, territorio_id))

    def add_assignment(self, territorio_id, responsable_id, assigned_at, details):
        self.connection.execute("INSERT INTO asignaciones (territorio_id, responsable_id, fecha_asignado, detalles) VALUES (?, ?, ?, ?)", (territorio_id, responsable_id, assigned_at, details))

    def add_activity(self, territorio_id, responsable_id, activity_type, description, occurred_at):
        self.connection.execute("INSERT INTO actividad (territorio_id, responsable_id, tipo, descripcion, fecha) VALUES (?, ?, ?, ?, ?)", (territorio_id, responsable_id, activity_type, description, occurred_at))
