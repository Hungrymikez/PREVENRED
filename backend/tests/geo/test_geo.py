from typing import Any

import pytest

from prevenred.auth.domain.role import Role
from prevenred.auth.domain.user import User
from prevenred.auth.domain.value_objects import Email
from prevenred.auth.infrastructure.argon2_password_hasher import Argon2PasswordHasher
from prevenred.geo.domain.layer import LayerCategory, MapLayer
from prevenred.geo.domain.repositories import GeoRepository
from prevenred.shared.domain.errors import DomainValidationError


class InMemoryGeoRepository(GeoRepository):
    def __init__(self) -> None:
        self.layers: dict[str, MapLayer] = {}

    async def save_layer(self, layer: MapLayer) -> None:
        self.layers[layer.id.value] = layer

    async def list_active_layers(self, category: LayerCategory | None = None) -> list[MapLayer]:
        layers = [layer for layer in self.layers.values() if layer.is_active]
        if category:
            layers = [layer for layer in layers if layer.category == category]
        return layers


@pytest.fixture
def admin_user() -> User:
    return User.register(
        email=Email("admin.geo@pereira.gov.co"),
        raw_password="AdminGeoPass2026*",
        name="Cartógrafo DIGER",
        role=Role.ADMIN,
        hasher=Argon2PasswordHasher(),
    )


@pytest.fixture
def citizen_user() -> User:
    return User.register(
        email=Email("vecino.geo@pereira.gov.co"),
        raw_password="CitizenPass2026*",
        name="Vecino",
        role=Role.CIUDADANO,
        hasher=Argon2PasswordHasher(),
    )


def test_layer_domain_validations() -> None:
    valid_geojson: dict[str, Any] = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-75.69, 4.81]},
                "properties": {"name": "Punto crítico"},
            }
        ],
    }

    # Nombre corto
    with pytest.raises(DomainValidationError, match="al menos 3 caracteres"):
        MapLayer.create(name="ab", category=LayerCategory.ZONAS_RIESGO, geojson_data=valid_geojson)

    # GeoJSON inválido sin 'features'
    with pytest.raises(DomainValidationError, match="FeatureCollection"):
        MapLayer.create(name="Zonas Riesgo", category=LayerCategory.ZONAS_RIESGO, geojson_data={})


@pytest.mark.asyncio
async def test_create_and_list_layers() -> None:
    repo = InMemoryGeoRepository()
    layer = MapLayer.create(
        name="Vías principales Pereira",
        category=LayerCategory.RED_VIAL,
        geojson_data={"type": "FeatureCollection", "features": []},
    )
    await repo.save_layer(layer)

    active = await repo.list_active_layers()
    assert len(active) == 1
    assert active[0].name == "Vías principales Pereira"

    filtered = await repo.list_active_layers(category=LayerCategory.CUENCAS_HIDRICAS)
    assert len(filtered) == 0
