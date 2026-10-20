"""Puerto del repositorio de incidentes."""

from abc import ABC, abstractmethod

from prevenred.shared.domain.ids import EntityId

from .incident import Incident, IncidentStatus


class IncidentRepository(ABC):
    """Persistencia de reportes de emergencia."""

    @abstractmethod
    def save(self, incident: Incident) -> None:
        """Crea o actualiza un incidente."""

    @abstractmethod
    def get_by_id(self, incident_id: EntityId) -> Incident | None:
        """Busca por identificador."""

    @abstractmethod
    def list_recent(
        self,
        status: IncidentStatus | None = None,
        limit: int = 50,
    ) -> list[Incident]:
        """Lista recientes, opcionalmente filtrados por estado."""
