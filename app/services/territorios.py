"""Casos de uso de asignación y finalización de territorios."""

from datetime import datetime
from app.repositories.responsables import ResponsablesRepository
from app.repositories.territorios import TerritoriosRepository


class DomainError(ValueError):
    """Error esperado de una regla de negocio."""


def assign(connection, territorio_id, responsable_id, details=None):
    territorios = TerritoriosRepository(connection)
    responsables = ResponsablesRepository(connection)
    territorio = territorios.get(territorio_id)
    if territorio is None:
        raise LookupError("Territorio inexistente")
    responsable = responsables.get_active(responsable_id)
    if responsable is None:
        raise DomainError("El responsable no existe o está inactivo")
    if territorio["estado"] != "Disponible" or territorios.mark_assigned(territorio_id).rowcount == 0:
        raise DomainError("El territorio ya no está disponible")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    territorios.add_assignment(territorio_id, responsable_id, now, details)
    territorios.add_activity(territorio_id, responsable_id, "ASIGNACION", f"Territorio {territorio['numero']} asignado a {responsable['nombre']}", now)


def finish(connection, territorio_id):
    territorios = TerritoriosRepository(connection)
    territorio = territorios.get(territorio_id)
    if territorio is None:
        raise LookupError("Territorio inexistente")
    assignment = territorios.get_active_assignment(territorio_id)
    if assignment is None:
        return False
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    territorios.close_assignment(assignment["id"], now)
    territorios.set_status(territorio_id, "Disponible")
    territorios.add_activity(territorio_id, assignment["responsable_id"], "FINALIZACION", f"Territorio {territorio['numero']} finalizado", now)
    return True
