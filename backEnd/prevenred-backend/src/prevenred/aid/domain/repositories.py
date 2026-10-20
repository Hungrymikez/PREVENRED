"""
Puertos de persistencia de ayuda (CU-31, CU-41, CU-42).

`reserve_stock` devuelve bool en lugar de lanzar: el caso de uso traduce ese
False a un mensaje ("ya no hay suficientes"), porque la carrera se detecta en
la escritura atómica, no en la comprobación previa.
"""
from abc import ABC, abstractmethod

from prevenred.aid.domain.entities import AidInventoryItem, AidNeed


class AidNeedRepository(ABC):
    """Puerto de las necesidades de ayuda."""

    @abstractmethod
    def get_by_id(self, need_id: str) -> AidNeed | None:
        """Busca una necesidad por id."""

    @abstractmethod
    def add(self, need: AidNeed) -> None:
        """Registra una necesidad nueva."""

    @abstractmethod
    def update(self, need: AidNeed) -> None:
        """Guarda el avance de la entrega y el estado."""

    @abstractmethod
    def list_by_requester(self, user_id: str, *, limit: int = 100) -> list[AidNeed]:
        """Necesidades de una persona (CU-32 'mis casos')."""

    @abstractmethod
    def list_open(self, *, limit: int = 200) -> list[AidNeed]:
        """Necesidades sin cubrir, prioridad primero (tablero CU-42)."""


class AidInventoryRepository(ABC):
    """Puerto del inventario de recursos."""

    @abstractmethod
    def get_by_id(self, item_id: str) -> AidInventoryItem | None:
        """Busca un recurso por id."""

    @abstractmethod
    def add(self, item: AidInventoryItem) -> None:
        """Registra un recurso nuevo."""

    @abstractmethod
    def update(self, item: AidInventoryItem) -> None:
        """Guarda cambios administrativos (cantidad total, estado, trazabilidad)."""

    @abstractmethod
    def reserve_stock(self, item_id: str, amount: int) -> bool:
        """Reserva unidades de forma ATÓMICA.

        True si se pudo; False si ya no alcanzaba (otra entrega se adelantó).
        """

    @abstractmethod
    def list_available(
        self, *, type: str | None = None, limit: int = 200
    ) -> list[AidInventoryItem]:
        """Recursos con existencias disponibles (CU-41)."""
