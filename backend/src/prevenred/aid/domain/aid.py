from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import DomainValidationError
from prevenred.shared.domain.ids import EntityId


class AidCategory(StrEnum):
    ALIMENTOS = "ALIMENTOS"
    AGUA = "AGUA"
    HERRAMIENTAS = "HERRAMIENTAS"
    REFUGIO = "REFUGIO"
    ROPA = "ROPA"
    PRIMEROS_AUXILIOS = "PRIMEROS_AUXILIOS"
    OTROS = "OTROS"


class AidPriority(StrEnum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    URGENTE = "URGENTE"


class AidStatus(StrEnum):
    PENDIENTE = "PENDIENTE"
    EMPAREJADO = "EMPAREJADO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"


@dataclass
class AidOffer(Entity):
    title: str
    category: AidCategory
    quantity: float
    unit: str
    donor_id: EntityId
    longitude: float
    latitude: float
    status: AidStatus
    created_at: datetime
    source_material_id: EntityId | None = None
    # CU-41: cantidad que aún no se ha comprometido en un emparejamiento.
    available_quantity: float | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.available_quantity is None:
            self.available_quantity = self.quantity if self.status == AidStatus.PENDIENTE else 0.0

    def allocate(self, amount: float) -> None:
        """CU-42: compromete parte de la oferta; solo queda EMPAREJADA cuando se agota."""
        if amount <= 0 or amount > (self.available_quantity or 0):
            raise DomainValidationError("La cantidad a comprometer excede lo disponible.")
        self.available_quantity = round((self.available_quantity or 0) - amount, 6)
        if self.available_quantity <= 0:
            self.available_quantity = 0.0
            self.status = AidStatus.EMPAREJADO

    @classmethod
    def create(
        cls,
        title: str,
        category: AidCategory,
        quantity: float,
        unit: str,
        donor_id: EntityId,
        longitude: float,
        latitude: float,
        source_material_id: EntityId | None = None,
    ) -> "AidOffer":
        if not title or len(title.strip()) < 3:
            raise DomainValidationError("El título del recurso debe tener al menos 3 caracteres.")
        if quantity <= 0:
            raise DomainValidationError("La cantidad disponible debe ser superior a 0.")
        if not (-180.0 <= longitude <= 180.0 and -90.0 <= latitude <= 90.0):
            raise DomainValidationError("Coordenadas geográficas inválidas.")

        return cls(
            id=EntityId.generate(),
            title=title.strip(),
            category=category,
            quantity=quantity,
            unit=unit.strip().lower(),
            donor_id=donor_id,
            longitude=longitude,
            latitude=latitude,
            status=AidStatus.PENDIENTE,
            created_at=datetime.now(UTC),
            source_material_id=source_material_id,
        )


@dataclass
class AidNeed(Entity):
    title: str
    category: AidCategory
    quantity: float
    unit: str
    priority: AidPriority
    requester_id: EntityId
    longitude: float
    latitude: float
    status: AidStatus
    created_at: datetime
    # CU-42: cantidad que todavía falta por cubrir con donaciones.
    remaining_quantity: float | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.remaining_quantity is None:
            self.remaining_quantity = self.quantity if self.status == AidStatus.PENDIENTE else 0.0

    def fulfil(self, amount: float) -> None:
        """CU-42: cubre parte de la necesidad; solo queda EMPAREJADA cuando se cubre toda."""
        if amount <= 0 or amount > (self.remaining_quantity or 0):
            raise DomainValidationError("La cantidad a cubrir excede lo pendiente.")
        self.remaining_quantity = round((self.remaining_quantity or 0) - amount, 6)
        if self.remaining_quantity <= 0:
            self.remaining_quantity = 0.0
            self.status = AidStatus.EMPAREJADO

    @classmethod
    def create(
        cls,
        title: str,
        category: AidCategory,
        quantity: float,
        unit: str,
        priority: AidPriority,
        requester_id: EntityId,
        longitude: float,
        latitude: float,
    ) -> "AidNeed":
        if not title or len(title.strip()) < 3:
            raise DomainValidationError(
                "El título de la necesidad debe tener al menos 3 caracteres."
            )
        if quantity <= 0:
            raise DomainValidationError("La cantidad solicitada debe ser mayor a 0.")
        if not (-180.0 <= longitude <= 180.0 and -90.0 <= latitude <= 90.0):
            raise DomainValidationError("Coordenadas geográficas inválidas.")

        return cls(
            id=EntityId.generate(),
            title=title.strip(),
            category=category,
            quantity=quantity,
            unit=unit.strip().lower(),
            priority=priority,
            requester_id=requester_id,
            longitude=longitude,
            latitude=latitude,
            status=AidStatus.PENDIENTE,
            created_at=datetime.now(UTC),
        )


@dataclass
class DonationMatch(Entity):
    need_id: EntityId
    offer_id: EntityId
    matched_quantity: float
    distance_meters: float
    matched_by: EntityId
    matched_at: datetime
    is_confirmed: bool

    @classmethod
    def create(
        cls,
        need_id: EntityId,
        offer_id: EntityId,
        matched_quantity: float,
        distance_meters: float,
        matched_by: EntityId,
    ) -> "DonationMatch":
        if matched_quantity <= 0:
            raise DomainValidationError("La cantidad emparejada debe ser positiva.")
        return cls(
            id=EntityId.generate(),
            need_id=need_id,
            offer_id=offer_id,
            matched_quantity=matched_quantity,
            distance_meters=distance_meters,
            matched_by=matched_by,
            matched_at=datetime.now(UTC),
            is_confirmed=True,
        )
