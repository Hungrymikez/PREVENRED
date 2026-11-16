"""Listado de incidentes recientes (dashboard / mapa / mis casos)."""

from prevenred.auth.application.ports import TokenPayload
from prevenred.auth.domain.role import Role

from ..domain.incident import Incident, IncidentStatus
from ..domain.repositories import IncidentRepository

# Roles que pueden ver todos los reportes (operación y seguimiento de la emergencia).
STAFF_ROLES = frozenset({Role.ADMINISTRADOR, Role.INSPECTOR})


class ListIncidents:
    """Consulta reportes recientes, con filtro opcional por estado.

    Los reportes contienen datos personales (quién reportó, descripción y
    ubicación exacta), así que solo el personal (administrador e inspector) ve
    todos; cualquier otro rol ve únicamente los suyos ("mis casos", CU-32).
    """

    def __init__(self, repository: IncidentRepository) -> None:
        self._repository = repository

    def execute(
        self,
        requester: TokenPayload,
        status: IncidentStatus | None = None,
        limit: int = 50,
    ) -> list[Incident]:
        reported_by = None if requester.role in STAFF_ROLES else requester.user_id
        return self._repository.list_recent(status=status, limit=limit, reported_by=reported_by)
