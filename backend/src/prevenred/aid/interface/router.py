from typing import Annotated

from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from prevenred.auth.domain.user import User
from prevenred.auth.interface.dependencies import get_current_user
from prevenred.shared.domain.ids import EntityId
from prevenred.shared.infrastructure.mongo import get_database

from ..application.manage_aid import (
    ExecuteMatchingCommand,
    ManageAidUseCase,
    OfferAidCommand,
    RequestAidCommand,
)
from ..domain.aid import AidNeed, AidOffer, DonationMatch
from ..infrastructure.mongo_aid_repository import MongoAidRepository
from .schemas import (
    AidNeedResponse,
    AidOfferResponse,
    DonationMatchResponse,
    OfferAidPayload,
    RequestAidPayload,
)

router = APIRouter(prefix="/aid", tags=["Aid & Donation Matching"])


def _need_response(n: AidNeed) -> AidNeedResponse:
    return AidNeedResponse(
        id=n.id.value,
        title=n.title,
        category=n.category,
        quantity=n.quantity,
        unit=n.unit,
        priority=n.priority,
        requester_id=n.requester_id.value,
        longitude=n.longitude,
        latitude=n.latitude,
        status=n.status,
        created_at=n.created_at,
        remaining_quantity=n.remaining_quantity,
    )


def _offer_response(o: AidOffer) -> AidOfferResponse:
    return AidOfferResponse(
        id=o.id.value,
        title=o.title,
        category=o.category,
        quantity=o.quantity,
        unit=o.unit,
        donor_id=o.donor_id.value,
        longitude=o.longitude,
        latitude=o.latitude,
        status=o.status,
        created_at=o.created_at,
        source_material_id=o.source_material_id.value if o.source_material_id else None,
        available_quantity=o.available_quantity,
    )


def _match_response(m: DonationMatch) -> DonationMatchResponse:
    return DonationMatchResponse(
        id=m.id.value,
        need_id=m.need_id.value,
        offer_id=m.offer_id.value,
        matched_quantity=m.matched_quantity,
        distance_meters=m.distance_meters,
        matched_by=m.matched_by.value,
        matched_at=m.matched_at,
        is_confirmed=m.is_confirmed,
    )


@router.post("/needs", response_model=AidNeedResponse, status_code=status.HTTP_201_CREATED)
async def request_aid(
    payload: RequestAidPayload,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> AidNeedResponse:
    use_case = ManageAidUseCase(MongoAidRepository(db))
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
    return _need_response(await use_case.request_aid(cmd))


@router.get("/needs/mine", response_model=list[AidNeedResponse])
async def my_aid_needs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> list[AidNeedResponse]:
    """CU-32: solicitudes de ayuda de la persona con sesión (no ve las de otros)."""
    needs = await MongoAidRepository(db).list_needs_by_requester(EntityId(current_user.id))
    return [_need_response(n) for n in needs]


@router.get("/needs/pending", response_model=list[AidNeedResponse])
async def pending_aid_needs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> list[AidNeedResponse]:
    """CU-42: necesidades aún sin cubrir (solo administración)."""
    use_case = ManageAidUseCase(MongoAidRepository(db))
    return [_need_response(n) for n in await use_case.list_pending_needs(current_user)]


@router.post("/offers", response_model=AidOfferResponse, status_code=status.HTTP_201_CREATED)
async def offer_aid(
    payload: OfferAidPayload,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> AidOfferResponse:
    use_case = ManageAidUseCase(MongoAidRepository(db))
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
    return _offer_response(await use_case.offer_aid(cmd))


@router.get("/offers/mine", response_model=list[AidOfferResponse])
async def my_aid_offers(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> list[AidOfferResponse]:
    """CU-33: ofertas de ayuda de la persona con sesión."""
    use_case = ManageAidUseCase(MongoAidRepository(db))
    return [_offer_response(o) for o in await use_case.list_my_offers(current_user)]


@router.get("/offers/pending", response_model=list[AidOfferResponse])
async def pending_aid_offers(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> list[AidOfferResponse]:
    """CU-41: ofertas con cantidad disponible (solo administración)."""
    use_case = ManageAidUseCase(MongoAidRepository(db))
    return [_offer_response(o) for o in await use_case.list_pending_offers(current_user)]


@router.post("/matching/run", response_model=list[DonationMatchResponse])
async def trigger_matching(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> list[DonationMatchResponse]:
    use_case = ManageAidUseCase(MongoAidRepository(db))
    matches = await use_case.run_matching(ExecuteMatchingCommand(admin_user=current_user))
    return [_match_response(m) for m in matches]
