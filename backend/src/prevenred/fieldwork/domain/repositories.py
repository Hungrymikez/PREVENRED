"""Puerto del repositorio de inspecciones de campo."""

from abc import ABC, abstractmethod

from prevenred.shared.domain.ids import EntityId

from .inspection import PropertyInspection


class FieldworkRepository(ABC):
    """Persistencia de inspecciones de inmuebles."""

    @abstractmethod
    def save(self, inspection: PropertyInspection) -> None:
        """Guarda una inspección."""

    @abstractmethod
    def get_by_id(self, inspection_id: EntityId) -> PropertyInspection | None:
        """Busca por identificador."""

    @abstractmethod
    def list_by_inspector(self, inspector_id: EntityId) -> list[PropertyInspection]:
        """Lista inspecciones de un evaluador."""
