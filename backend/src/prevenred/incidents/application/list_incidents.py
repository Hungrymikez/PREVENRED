"""Listado de incidentes recientes (dashboard / mapa / mis casos)."""

from prevenred.auth.application.ports import TokenPayload
from prevenred.auth.domain.role import Role
from prevenred.shared.domain.errors import NotFoundError

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
        assigned_to_me: bool = False,
    ) -> list[Incident]:
        reported_by = None if requester.role in STAFF_ROLES else requester.user_id
        # "Asignados a mí": solo tiene sentido para el personal de atención.
        assigned_to = (
            requester.user_id if assigned_to_me and requester.role in STAFF_ROLES else None
        )
        return self._repository.list_recent(
            status=status, limit=limit, reported_by=reported_by, assigned_to=assigned_to
        )


class GetIncidentByCaseNumber:
    """CU-32: consulta un caso por su número. El personal ve cualquiera; los demás roles, solo
    los suyos. Si no es suyo responde igual que si no existiera (E1: no revela casos ajenos)."""

    def __init__(self, repository: IncidentRepository) -> None:
        self._repository = repository

    def execute(self, requester: TokenPayload, case_number: str) -> Incident:
        incident = self._repository.get_by_case_number(case_number.strip().upper())
        visible = incident is not None and (
            requester.role in STAFF_ROLES or incident.reported_by == requester.user_id
        )
        if not visible:
            raise NotFoundError("No encontramos ese número entre tus casos.")
        return incident
