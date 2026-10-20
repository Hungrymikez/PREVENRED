"""
Entidades de ayuda: `AidNeed` (lo que se pide) e `AidInventoryItem` (lo que hay).

Por qué:
  - Lo que se pide y lo que hay se registran por SEPARADO: así el coordinador ve
    el déficit (pedido - disponible) sin cruzar colecciones.
  - `AidInventoryItem.reserve()` es el punto delicado: si dos entregas toman el
    mismo recurso a la vez, se despacharía más de lo que existe. La comprobación
    de aquí es la regla; el repositorio la aplica con un filtro condicional
    atómico para que valga también con peticiones simultáneas.
"""
from dataclasses import dataclass, field
from datetime import datetime

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import ValidationError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.domain.guards import require_one_of, require_text, require_utc

#: Origen del recurso (CU-41).
SOURCE_TYPES = ("MATERIAL", "HERRAMIENTA", "DONACION")

#: Estado del recurso en inventario.
INVENTORY_STATUSES = ("DISPONIBLE", "AGOTADO", "RESERVADO", "BAJA")

#: Estados de una necesidad.
NEED_STATUSES = ("ABIERTA", "PARCIAL", "CUBIERTA", "CANCELADA")

#: Prioridad de atención.
PRIORITIES = ("BAJA", "MEDIA", "ALTA", "CRITICA")


@dataclass(kw_only=True, eq=False)
class AidNeed(Entity):
    """Necesidad de ayuda solicitada (CU-31; seguimiento en CU-32/CU-42)."""
    type: str
    description: str
    requested_by: str
    quantity: int = 1
    latitude: float | None = None
    longitude: float | None = None
    priority: str = "MEDIA"
    status: str = "ABIERTA"
    case_id: str | None = None
    incident_id: str | None = None      # reporte que la originó, si existe
    covered_quantity: int = 0           # ya entregado
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        """Valida la petición: sin cantidad no hay nada que cubrir."""
        require_text(self.type, "type", max_length=60)
        require_text(self.description, "description", max_length=1000)
        require_text(self.requested_by, "requested_by", max_length=64)
        require_one_of(self.priority, PRIORITIES, "priority")
        require_one_of(self.status, NEED_STATUSES, "status")
        if self.quantity <= 0:
            raise ValidationError("La cantidad solicitada debe ser mayor que cero.")
        if self.covered_quantity < 0 or self.covered_quantity > self.quantity:
            raise ValidationError("La cantidad cubierta no puede exceder lo solicitado.")
        if self.latitude is not None and not -90 <= self.latitude <= 90:
            raise ValidationError("La latitud debe estar entre -90 y 90.")
        if self.longitude is not None and not -180 <= self.longitude <= 180:
            raise ValidationError("La longitud debe estar entre -180 y 180.")

    @property
    def pending_quantity(self) -> int:
        """Falta por cubrir."""
        return self.quantity - self.covered_quantity

    def add_covered(self, amount: int) -> None:
        """Suma lo entregado y actualiza el estado (ABIERTA -> PARCIAL -> CUBIERTA)."""
        if amount <= 0:
            raise ValidationError("La cantidad entregada debe ser mayor que cero.")
        if amount > self.pending_quantity:
            raise ValidationError("Se entregarían más unidades de las solicitadas.")
        self.covered_quantity += amount
        self.status = "CUBIERTA" if self.covered_quantity == self.quantity else "PARCIAL"

    def cancel(self) -> None:
        """Cancela la necesidad (p. ej. la familia ya la resolvió)."""
        if self.status == "CUBIERTA":
            raise ValidationError("Una necesidad ya cubierta no se puede cancelar.")
        self.status = "CANCELADA"

    @property
    def is_open(self) -> bool:
        """True si todavía se puede atender."""
        return self.status in ("ABIERTA", "PARCIAL")


@dataclass(kw_only=True, eq=False)
class AidInventoryItem(Entity):
    """Recurso disponible en bodega (CU-41), con su trazabilidad."""
    source_id: str
    source_type: str
    type: str
    quantity: int
    origin_trace: str                     # de dónde salió (donante, compra, campaña)
    available_quantity: int | None = None  # None = aún no se calcula; = quantity
    status: str = "DISPONIBLE"
    updated_at: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        """Normaliza el disponible y valida que no se supere el total."""
        require_text(self.source_id, "source_id", max_length=64)
        require_one_of(self.source_type, SOURCE_TYPES, "source_type")
        require_text(self.type, "type", max_length=60)
        require_text(self.origin_trace, "origin_trace", max_length=500)
        require_one_of(self.status, INVENTORY_STATUSES, "status")
        if self.quantity <= 0:
            raise ValidationError("La cantidad total debe ser mayor que cero.")
        if self.available_quantity is None:
            self.available_quantity = self.quantity
        if not 0 <= self.available_quantity <= self.quantity:
            raise ValidationError("El disponible no puede ser negativo ni superar el total.")
        if self.updated_at is not None:
            self.updated_at = require_utc(self.updated_at, "updated_at")

    @staticmethod
    def check_reservation(available_quantity: int, status: str, amount: int) -> None:
        """Regla de reserva sin tocar el objeto.

        La usa el repositorio para SU filtro condicional: el mismo criterio que
        aquí se valida antes, se aplica luego dentro de la escritura atómica.
        """
        if amount <= 0:
            raise ValidationError("La cantidad a reservar debe ser mayor que cero.")
        if status != "DISPONIBLE":
            raise ValidationError("Este recurso no está disponible para asignar.")
        if amount > available_quantity:
            raise ValidationError(
                f"Solo hay {available_quantity} unidades disponibles de este recurso."
            )

    def reserve(self, amount: int) -> None:
        """Compromete unidades para una entrega (CU-42).

        Fallar aquí es lo que impide prometer ayuda que no existe.
        """
        available = self.available_quantity or 0
        self.check_reservation(available, self.status, amount)
        self.available_quantity = available - amount
        self.status = "AGOTADO" if self.available_quantity == 0 else "DISPONIBLE"
        self.updated_at = utcnow()

    def receive(self, amount: int) -> None:
        """Entra una donación o compra nueva al inventario (CU-41)."""
        if amount <= 0:
            raise ValidationError("La cantidad recibida debe ser mayor que cero.")
        self.quantity += amount
        self.available_quantity = (self.available_quantity or 0) + amount
        if self.status == "AGOTADO":
            self.status = "DISPONIBLE"
        self.updated_at = utcnow()
