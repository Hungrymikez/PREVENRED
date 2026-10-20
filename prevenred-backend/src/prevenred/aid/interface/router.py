from typing import Annotated

from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from prevenred.identity.domain.user import User
from prevenred.identity.interface.dependencies import get_current_user
from prevenred.shared.infrastructure.mongo import get_database

from ..application.manage_aid import (
    ExecuteMatchingCommand,
    ManageAidUseCase,
    OfferAidCommand,
    RequestAidCommand,
)
from ..infrastructure.mongo_aid_repository import MongoAidRepository
from .schemas import (
    AidNeedResponse,
    AidOfferResponse,
    DonationMatchResponse,
    OfferAidPayload,
    RequestAidPayload,
)

router = APIRouter(prefix="/aid", tags=["Aid & Donation Matching"])


@router.post("/needs", response_model=AidNeedResponse, status_code=status.HTTP_201_CREATED)
async def request_aid(
    payload: RequestAidPayload,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> AidNeedResponse:
    repo = MongoAidRepository(db)
    use_case = ManageAidUseCase(repo)

    cmd = RequestAidCommand(
        title=payload.title,
        category=payload.category,
        quantity=payload.quantity,
        unit=payload.unit,
        priority=payload.priority,
        longitude=payload.longitude,
        latitude=payload.latitude,
        requester=current_user,
    )
    res = await use_case.request_aid(cmd)
    return AidNeedResponse(
        id=res.id.value,
        title=res.title,
        category=res.category,
        quantity=res.quantity,
        unit=res.unit,
        priority=res.priority,
        requester_id=res.requester_id.value,
        longitude=res.longitude,
        latitude=res.latitude,
        status=res.status,
        created_at=res.created_at,
    )


@router.post("/offers", response_model=AidOfferResponse, status_code=status.HTTP_201_CREATED)
async def offer_aid(
    payload: OfferAidPayload,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> AidOfferResponse:
    repo = MongoAidRepository(db)
    use_case = ManageAidUseCase(repo)

    cmd = OfferAidCommand(
        title=payload.title,
        category=payload.category,
        quantity=payload.quantity,
        unit=payload.unit,
        longitude=payload.longitude,
        latitude=payload.latitude,
        donor=current_user,
        source_material_id=payload.source_material_id,
    )
    res = await use_case.offer_aid(cmd)
    return AidOfferResponse(
        id=res.id.value,
        title=res.title,
        category=res.category,
        quantity=res.quantity,
        unit=res.unit,
        donor_id=res.donor_id.value,
        longitude=res.longitude,
        latitude=res.latitude,
        status=res.status,
        created_at=res.created_at,
        source_material_id=res.source_material_id.value if res.source_material_id else None,
    )


@router.post("/matching/run", response_model=list[DonationMatchResponse])
async def trigger_matching(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> list[DonationMatchResponse]:
    repo = MongoAidRepository(db)
    use_case = ManageAidUseCase(repo)

    matches = await use_case.run_matching(ExecuteMatchingCommand(admin_user=current_user))
    return [
        DonationMatchResponse(
            id=m.id.value,
            need_id=m.need_id.value,
            offer_id=m.offer_id.value,
            matched_quantity=m.matched_quantity,
            distance_meters=m.distance_meters,
            matched_by=m.matched_by.value,
            matched_at=m.matched_at,
            is_confirmed=m.is_confirmed,
        )
        for m in matches
    ]
