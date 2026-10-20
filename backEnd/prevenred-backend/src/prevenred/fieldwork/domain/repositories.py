"""
Puertos de persistencia del censo (fieldwork). El dominio dice QUÉ necesita.

El `client_id` aparece en las lecturas porque la sincronización offline (CU-37)
necesita saber "¿ya llegó este registro?" sin descargar la colección.
"""
from abc import ABC, abstractmethod

from prevenred.fieldwork.domain.entities import Inspection, Property


class PropertyRepository(ABC):
    """Puerto de persistencia de inmuebles (CU-34)."""

    @abstractmethod
    def get_by_id(self, property_id: str) -> Property | None:
        """Busca un inmueble por id; None si no existe."""

    @abstractmethod
    def get_by_client_id(self, client_id: str) -> Property | None:
        """Busca por el id del celular (evita duplicados al sincronizar, CU-37)."""

    @abstractmethod
    def add(self, property: Property) -> None:
        """Guarda un inmueble nuevo."""

    @abstractmethod
    def update(self, property: Property) -> None:
        """Guarda los cambios del inmueble (estado, fotos, número de caso)."""

    @abstractmethod
    def list_by_inspector(self, inspector_id: str, *, limit: int = 100) -> list[Property]:
        """Inmuebles censados por una persona, del más reciente al más antiguo."""


class InspectionRepository(ABC):
    """Puerto de persistencia de inspecciones (CU-35)."""

    @abstractmethod
    def get_by_id(self, inspection_id: str) -> Inspection | None:
        """Busca una inspección por id."""

    @abstractmethod
    def get_by_client_id(self, client_id: str) -> Inspection | None:
        """Busca por el id del celular (idempotencia offline, CU-37)."""

    @abstractmethod
    def add(self, inspection: Inspection) -> None:
        """Guarda una inspección nueva."""

    @abstractmethod
    def update(self, inspection: Inspection) -> None:
        """Guarda cambios (segunda revisión)."""

    @abstractmethod
    def list_by_property(self, property_id: str) -> list[Inspection]:
        """Historial de inspecciones de un inmueble, de la más antigua a la más nueva."""

    @abstractmethod
    def list_pending_second_review(self, *, limit: int = 100) -> list[Inspection]:
        """Casos críticos que aún esperan la segunda revisión (O-11)."""
