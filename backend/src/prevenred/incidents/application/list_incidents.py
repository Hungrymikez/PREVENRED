"""Listado de incidentes recientes (dashboard / mapa)."""

from ..domain.incident import Incident, IncidentStatus
from ..domain.repositories import IncidentRepository


class ListIncidents:
    """Consulta reportes recientes, con filtro opcional por estado."""

    def __init__(self, repository: IncidentRepository) -> None:
        self._repository = repository

    def execute(
        self,
        status: IncidentStatus | None = None,
        limit: int = 50,
    ) -> list[Incident]:
        return self._repository.list_recent(status=status, limit=limit)
