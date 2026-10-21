from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from prevenred.auth.domain.role import Role
from prevenred.auth.domain.user import User
from prevenred.auth.interface.dependencies import get_current_user
from prevenred.shared.domain.errors import AuthorizationError
from prevenred.shared.infrastructure.mongo import get_database

from ..domain.layer import LayerCategory, MapLayer
from ..infrastructure.mongo_geo_repository import MongoGeoRepository
from .schemas import CreateLayerRequest, MapLayerResponse

router = APIRouter(prefix="/geo", tags=["Geo & Map Layers"])


@router.post("/layers", response_model=MapLayerResponse, status_code=status.HTTP_201_CREATED)
async def create_layer(
    payload: CreateLayerRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> MapLayerResponse:
    if current_user.role != Role.ADMIN:
        raise AuthorizationError(
            "Solo administradores pueden crear o actualizar capas cartográficas."
        )

    repo = MongoGeoRepository(db)
    layer = MapLayer.create(
        name=payload.name, category=payload.category, geojson_data=payload.geojson_data
    )
    await repo.save_layer(layer)
    return MapLayerResponse(
        id=layer.id.value,
        name=layer.name,
        category=layer.category,
        geojson_data=layer.geojson_data,
        is_active=layer.is_active,
        created_at=layer.created_at,
    )


@router.get("/layers", response_model=list[MapLayerResponse])
async def list_layers(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    category: LayerCategory | None = Query(None),
) -> list[MapLayerResponse]:
    repo = MongoGeoRepository(db)
    layers = await repo.list_active_layers(category=category)
    return [
        MapLayerResponse(
            id=layer.id.value,
            name=layer.name,
            category=layer.category,
            geojson_data=layer.geojson_data,
            is_active=layer.is_active,
            created_at=layer.created_at,
        )
        for layer in layers
    ]
