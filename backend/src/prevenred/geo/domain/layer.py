from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import DomainValidationError
from prevenred.shared.domain.ids import EntityId


class LayerCategory(StrEnum):
    INFRAESTRUCTURA_CRITICA = "INFRAESTRUCTURA_CRITICA"
    ZONAS_RIESGO = "ZONAS_RIESGO"
    RED_VIAL = "RED_VIAL"
    CUENCAS_HIDRICAS = "CUENCAS_HIDRICAS"


@dataclass
class MapLayer(Entity):
    name: str
    category: LayerCategory
    geojson_data: dict[str, Any]
    is_active: bool
    created_at: datetime

    @classmethod
    def create(
        cls,
        name: str,
        category: LayerCategory,
        geojson_data: dict[str, Any],
    ) -> "MapLayer":
        if not name or len(name.strip()) < 3:
            raise DomainValidationError("El nombre de la capa debe tener al menos 3 caracteres.")
        if not geojson_data or "features" not in geojson_data:
            raise DomainValidationError("El GeoJSON debe ser una FeatureCollection válida.")

        return cls(
            id=EntityId.generate(),
            name=name.strip(),
            category=category,
            geojson_data=geojson_data,
            is_active=True,
            created_at=datetime.now(UTC),
        )
