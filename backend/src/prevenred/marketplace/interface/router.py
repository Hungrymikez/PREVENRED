from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from prevenred.auth.domain.user import User
from prevenred.auth.interface.dependencies import get_current_user
from prevenred.shared.domain.errors import NotFoundError
from prevenred.shared.domain.ids import EntityId
from prevenred.shared.infrastructure.mongo import get_database

from ..application.publish_material import PublishMaterialCommand, PublishMaterialUseCase
from ..application.search_materials import SearchMaterialsQuery, SearchMaterialsUseCase
from ..domain.material import MaterialCategory, OfferType
from ..infrastructure.mongo_material_repository import MongoMaterialRepository
from .schemas import MaterialResponse, PublishMaterialRequest

router = APIRouter(prefix="/marketplace", tags=["Marketplace - SegundaVida"])


@router.post("/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def publish_material(
    payload: PublishMaterialRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> MaterialResponse:
    repo = MongoMaterialRepository(db)
    use_case = PublishMaterialUseCase(repo)

    cmd = PublishMaterialCommand(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        offer_type=payload.offer_type,
        condition=payload.condition,
        quantity=payload.quantity,
        unit=payload.unit,
        longitude=payload.longitude,
        latitude=payload.latitude,
        owner=current_user,
        price=payload.price,
        media_urls=payload.media_urls,
    )
    res = await use_case.execute(cmd)
    return MaterialResponse(
        id=res.id.value,
        title=res.title,
        description=res.description,
        category=res.category,
        offer_type=res.offer_type,
        condition=res.condition,
        quantity=res.quantity,
        unit=res.unit,
        price=res.price,
        longitude=res.longitude,
        latitude=res.latitude,
        owner_id=res.owner_id.value,
        media_urls=res.media_urls,
        is_active=res.is_active,
        created_at=res.created_at,
    )


@router.get("/materials/search", response_model=list[MaterialResponse])
async def search_materials(
    longitude: float = Query(..., ge=-180.0, le=180.0),
    latitude: float = Query(..., ge=-90.0, le=90.0),
    radius_meters: float = Query(10000.0, ge=100.0, le=50000.0),
    category: MaterialCategory | None = Query(None),
    offer_type: OfferType | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> list[MaterialResponse]:
    repo = MongoMaterialRepository(db)
    use_case = SearchMaterialsUseCase(repo)

    query = SearchMaterialsQuery(
        longitude=longitude,
        latitude=latitude,
        max_distance_meters=radius_meters,
        category=category,
        offer_type=offer_type,
        limit=limit,
    )
    items = await use_case.execute(query)
    return [
        MaterialResponse(
            id=m.id.value,
            title=m.title,
            description=m.description,
            category=m.category,
            offer_type=m.offer_type,
            condition=m.condition,
            quantity=m.quantity,
            unit=m.unit,
            price=m.price,
            longitude=m.longitude,
            latitude=m.latitude,
            owner_id=m.owner_id.value,
            media_urls=m.media_urls,
            is_active=m.is_active,
            created_at=m.created_at,
        )
        for m in items
    ]


@router.get("/materials/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> MaterialResponse:
    repo = MongoMaterialRepository(db)
    m = await repo.get_by_id(EntityId(material_id))
    if not m:
        raise NotFoundError(f"Material '{material_id}' no encontrado.")
    return MaterialResponse(
        id=m.id.value,
        title=m.title,
        description=m.description,
        category=m.category,
        offer_type=m.offer_type,
        condition=m.condition,
        quantity=m.quantity,
        unit=m.unit,
        price=m.price,
        longitude=m.longitude,
        latitude=m.latitude,
        owner_id=m.owner_id.value,
        media_urls=m.media_urls,
        is_active=m.is_active,
        created_at=m.created_at,
    )
