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
        reported_by: str | None = None,
        assigned_to: str | None = None,
    ) -> list[Incident]:
        """Lista recientes, opcionalmente filtrados por estado y por quién reportó."""

    @abstractmethod
    def get_by_client_id(self, reported_by: EntityId, client_id: str) -> Incident | None:
        """Busca el reporte que esa persona envió con ese clientId (idempotencia, CU-37)."""

    @abstractmethod
    def get_by_case_number(self, case_number: str) -> Incident | None:
        """Busca por número de caso (CU-32)."""
