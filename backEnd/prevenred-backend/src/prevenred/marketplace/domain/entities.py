"""
Entidades del marketplace de herramientas: `Reservation` y `ToolTransaction`.

Por qué:
  - Una reserva es un COMPROMISO de fechas: solo se acepta si las fechas no se
    cruzan con otra reserva activa de la misma herramienta (CU-13). Por eso la
    regla es `overlaps()` y no una simple comparación de estados.
  - La transacción (CU-15) deja rastro del intercambio con un estado explícito:
    si una entrega no se devuelve, el dueño lo ve en la plataforma.
"""
from dataclasses import dataclass, field
from datetime import datetime

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import ValidationError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.domain.guards import require_one_of, require_text, require_utc

#: Estados de una reserva.
RESERVATION_STATUSES = ("SOLICITADA", "APROBADA", "RECHAZADA", "ENTREGADA", "DEVUELTA", "CANCELADA")

#: Estados que ocupan la herramienta en el calendario.
BLOCKING_STATUSES = ("SOLICITADA", "APROBADA", "ENTREGADA")

#: Estados de la operación (CU-15). `DEVUELTA` aplica a alquileres devueltos.
TRANSACTION_STATUSES = ("SOLICITADA", "APROBADA", "DEVUELTA", "CANCELADA")

#: Tipos de operación.
TRANSACTION_TYPES = ("ALQUILER", "VENTA", "INTERCAMBIO")


@dataclass(kw_only=True, eq=False)
class Reservation(Entity):
    """Solicitud de alquiler de una herramienta para un rango de fechas (CU-13)."""
    tool_id: str
    requester_id: str
    owner_id: str                 # copiado: "mis reservas" sin cruzar colecciones (CU-14)
    start_date: datetime
    end_date: datetime
    cost: float = 0.0
    status: str = "SOLICITADA"
    returned_at: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        """Valida fechas y costo: una reserva de fin anterior al inicio no existe."""
        require_text(self.tool_id, "tool_id", max_length=64)
        require_text(self.requester_id, "requester_id", max_length=64)
        require_text(self.owner_id, "owner_id", max_length=64)
        require_one_of(self.status, RESERVATION_STATUSES, "status")
        self.start_date = require_utc(self.start_date, "start_date")
        self.end_date = require_utc(self.end_date, "end_date")
        if self.end_date <= self.start_date:
            raise ValidationError("La fecha final debe ser posterior a la inicial.")
        if self.cost < 0:
            raise ValidationError("El costo no puede ser negativo.")

    def overlaps(self, other_start: datetime, other_end: datetime) -> bool:
        """True si el rango pedido choca con esta reserva.

        Los bordes no cuentan como choque: entregar el sábado y recibir el sábado
        siguiente no es un conflicto.
        """
        return other_start < self.end_date and other_end > self.start_date

    @property
    def blocks_calendar(self) -> bool:
        """True si esta reserva impide aprobar otras en las mismas fechas."""
        return self.status in BLOCKING_STATUSES

    def approve(self) -> None:
        """El dueño acepta la solicitud (CU-13)."""
        if self.status != "SOLICITADA":
            raise ValidationError("Solo se puede aprobar una reserva solicitada.")
        self.status = "APROBADA"

    def reject(self) -> None:
        """El dueño rechaza; las fechas quedan libres."""
        if self.status != "SOLICITADA":
            raise ValidationError("Solo se puede rechazar una reserva solicitada.")
        self.status = "RECHAZADA"

    def mark_delivered(self) -> None:
        """El dueño entrega la herramienta (CU-15)."""
        if self.status != "APROBADA":
            raise ValidationError("Primero hay que aprobar la reserva.")
        self.status = "ENTREGADA"

    def mark_returned(self, at: datetime) -> None:
        """Se devuelve la herramienta: la reserva termina bien (CU-14)."""
        if self.status != "ENTREGADA":
            raise ValidationError("Solo se puede devolver una herramienta entregada.")
        self.returned_at = require_utc(at, "returned_at")
        self.status = "DEVUELTA"

    def cancel(self) -> None:
        """El solicitante cancela antes de la entrega."""
        if self.status not in ("SOLICITADA", "APROBADA"):
            raise ValidationError("Ya no se puede cancelar esta reserva.")
        self.status = "CANCELADA"


@dataclass(kw_only=True, eq=False)
class ToolTransaction(Entity):
    """Operación completada entre dos personas (CU-15)."""
    buyer_id: str
    seller_id: str
    item_id: str
    type: str
    amount: float
    status: str = "SOLICITADA"
    completed_at: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        """Valida la operación: nadie compra ni vende a sí mismo."""
        require_text(self.buyer_id, "buyer_id", max_length=64)
        require_text(self.seller_id, "seller_id", max_length=64)
        require_text(self.item_id, "item_id", max_length=64)
        require_one_of(self.type, TRANSACTION_TYPES, "type")
        require_one_of(self.status, TRANSACTION_STATUSES, "status")
        if self.buyer_id == self.seller_id:
            raise ValidationError("No puedes operar contigo mismo.")
        if self.amount < 0:
            raise ValidationError("El monto no puede ser negativo.")

    def approve(self) -> None:
        """Se aprueba la operación (CU-15)."""
        if self.status != "SOLICITADA":
            raise ValidationError("Solo se aprueba una operación solicitada.")
        self.status = "APROBADA"

    def complete(self, at: datetime) -> None:
        """Cierra la operación cuando la herramienta cambió de manos."""
        if self.status != "APROBADA":
            raise ValidationError("Solo se completa una operación aprobada.")
        self.completed_at = require_utc(at, "completed_at")
        self.status = "DEVUELTA"

    def cancel(self) -> None:
        """Anula una operación que no se concretó."""
        if self.status == "DEVUELTA":
            raise ValidationError("Una operación ya completada no se puede anular.")
        self.status = "CANCELADA"
