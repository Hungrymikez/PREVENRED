"""Entidad PropertyInspection: censo e inspección de habitabilidad (CU-34, CU-36)."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import ValidationError
from prevenred.shared.domain.events import utcnow
from prevenred.shared.domain.ids import EntityId, new_id


class DamageLevel(StrEnum):
    """Nivel de daño del inmueble (catálogo M10)."""

    LEVE = "LEVE"
    MODERADO = "MODERADO"
    SEVERO = "SEVERO"
    DESTRUIDO = "DESTRUIDO"


class HabitabilityStatus(StrEnum):
    """Resultado de habitabilidad tras la inspección."""

    HABITABLE = "HABITABLE"
    RESTRINGIDO = "RESTRINGIDO"
    EVACUACION = "EVACUACION"


@dataclass(kw_only=True, eq=False)
class PropertyInspection(Entity):
    """Resultado de inspección de campo sobre un inmueble."""

    property_address: str
    neighborhood: str
    residents_count: int
    damage_level: DamageLevel
    habitability: HabitabilityStatus
    technical_notes: str
    longitude: float
    latitude: float
    inspector_id: EntityId
    photos: list[str]
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        property_address: str,
        neighborhood: str,
        residents_count: int,
        damage_level: DamageLevel,
        habitability: HabitabilityStatus,
        technical_notes: str,
        longitude: float,
        latitude: float,
        inspector_id: EntityId,
        photos: list[str] | None = None,
    ) -> "PropertyInspection":
        """Crea una inspección válida (CU-36)."""
        if not property_address or len(property_address.strip()) < 5:
            raise ValidationError("La dirección del inmueble debe contener al menos 5 caracteres.")
        if not neighborhood or len(neighborhood.strip()) < 2:
            raise ValidationError("Indica el barrio o comuna del inmueble.")
        if residents_count < 0:
            raise ValidationError("El número de residentes no puede ser negativo.")
        if not (-180.0 <= longitude <= 180.0 and -90.0 <= latitude <= 90.0):
            raise ValidationError("Coordenadas geográficas inválidas.")

        return cls(
            id=new_id(),
            property_address=property_address.strip(),
            neighborhood=neighborhood.strip(),
            residents_count=residents_count,
            damage_level=damage_level,
            habitability=habitability,
            technical_notes=(technical_notes or "").strip(),
            longitude=longitude,
            latitude=latitude,
            inspector_id=inspector_id,
            photos=list(photos or []),
            created_at=utcnow(),
        )
