"""
Puertos del marketplace de herramientas (CU-13, CU-14, CU-15).

`list_blocking_between` existe para responder "¿estas fechas están libres?" con
UNA consulta al índice `toolId+startDate+endDate`, en lugar de traer todas las
reservas de la herramienta y filtrarlas en memoria.
"""
from abc import ABC, abstractmethod
from datetime import datetime

from prevenred.marketplace.domain.entities import Reservation, ToolTransaction


class ReservationRepository(ABC):
    """Puerto de las reservas de herramientas."""

    @abstractmethod
    def get_by_id(self, reservation_id: str) -> Reservation | None:
        """Busca una reserva por id."""

    @abstractmethod
    def add(self, reservation: Reservation) -> None:
        """Registra una solicitud de reserva."""

    @abstractmethod
    def update(self, reservation: Reservation) -> None:
        """Guarda el cambio de estado (aprobada, entregada, devuelta...)."""

    @abstractmethod
    def list_by_requester(self, user_id: str, *, limit: int = 100) -> list[Reservation]:
        """'Mis reservas' como solicitante (CU-14)."""

    @abstractmethod
    def list_by_owner(self, user_id: str, *, limit: int = 100) -> list[Reservation]:
        """Solicitudes recibidas por el dueño de la herramienta (CU-13/CU-14)."""

    @abstractmethod
    def list_blocking_between(
        self, tool_id: str, start: datetime, end: datetime
    ) -> list[Reservation]:
        """Reservas que ocupan la herramienta en ese rango (choques de fechas)."""


class TransactionRepository(ABC):
    """Puerto de las operaciones completadas (CU-15)."""

    @abstractmethod
    def get_by_id(self, transaction_id: str) -> ToolTransaction | None:
        """Busca una operación por id."""

    @abstractmethod
    def add(self, transaction: ToolTransaction) -> None:
        """Registra una operación."""

    @abstractmethod
    def update(self, transaction: ToolTransaction) -> None:
        """Guarda el cambio de estado o la finalización."""

    @abstractmethod
    def list_by_participant(self, user_id: str, *, limit: int = 100) -> list[ToolTransaction]:
        """Operaciones en las que la persona fue compradora o vendedora."""
