from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import DomainValidationError
from prevenred.shared.domain.ids import EntityId


class MaterialCategory(StrEnum):
    MADERA = "MADERA"
    METAL = "METAL"
    ELECTRICO = "ELECTRICO"
    HERRAMIENTAS = "HERRAMIENTAS"
    PLOMERIA = "PLOMERIA"
    CONSTRUCCION = "CONSTRUCCION"
    OTROS = "OTROS"


class OfferType(StrEnum):
    DONACION = "DONACION"
    VENTA = "VENTA"
    ALQUILER = "ALQUILER"


class MaterialCondition(StrEnum):
    NUEVO = "NUEVO"
    BUENO = "BUENO"
    USADO = "USADO"


@dataclass
class Material(Entity):
    title: str
    description: str
    category: MaterialCategory
    offer_type: OfferType
    condition: MaterialCondition
    quantity: float
    unit: str
    price: float | None
    longitude: float
    latitude: float
    owner_id: EntityId
    media_urls: list[str]
    is_active: bool
    created_at: datetime

    @classmethod
    def create(
        cls,
        title: str,
        description: str,
        category: MaterialCategory,
        offer_type: OfferType,
        condition: MaterialCondition,
        quantity: float,
        unit: str,
        longitude: float,
        latitude: float,
        owner_id: EntityId,
        price: float | None = None,
        media_urls: list[str] | None = None,
    ) -> "Material":
        clean_title = title.strip() if title else ""
        if len(clean_title) < 3:
            raise DomainValidationError("El título debe tener al menos 3 caracteres.")
        if quantity <= 0:
            raise DomainValidationError("La cantidad debe ser mayor a 0.")
        if offer_type in (OfferType.VENTA, OfferType.ALQUILER) and (price is None or price < 0):
            raise DomainValidationError(
                "Para venta o alquiler se requiere un precio válido mayor o igual a 0."
            )
        if not (-180.0 <= longitude <= 180.0 and -90.0 <= latitude <= 90.0):
            raise DomainValidationError("Coordenadas geográficas inválidas.")

        return cls(
            id=EntityId.generate(),
            title=clean_title,
            description=description.strip() if description else "",
            category=category,
            offer_type=offer_type,
            condition=condition,
            quantity=quantity,
            unit=unit.strip().lower(),
            price=price if offer_type != OfferType.DONACION else 0.0,
            longitude=longitude,
            latitude=latitude,
            owner_id=owner_id,
            media_urls=media_urls or [],
            is_active=True,
            created_at=datetime.now(UTC),
        )
