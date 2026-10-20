from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from prevenred.identity.domain.user import User
from prevenred.identity.interface.dependencies import get_current_user
from prevenred.shared.domain.errors import NotFoundError
from prevenred.shared.domain.ids import EntityId
from prevenred.shared.infrastructure.mongo import get_database

from ..application.manage_technician import (
    RegisterTechnicianProfileCommand,
    RegisterTechnicianProfileUseCase,
    VerifyTechnicianCommand,
    VerifyTechnicianUseCase,
)
from ..domain.technician import Specialty
from ..infrastructure.mongo_technician_repository import MongoTechnicianRepository
from .schemas import (
    RegisterTechnicianRequest,
    TechnicianResponse,
    VerifyTechnicianRequest,
    WhatsAppContactResponse,
)

router = APIRouter(prefix="/services", tags=["Services - OficiosYa"])


@router.post(
    "/technicians/profile",
    response_model=TechnicianResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_technician_profile(
    payload: RegisterTechnicianRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> TechnicianResponse:
    repo = MongoTechnicianRepository(db)
    use_case = RegisterTechnicianProfileUseCase(repo)

    cmd = RegisterTechnicianProfileCommand(
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        specialties=payload.specialties,
        experience_years=payload.experience_years,
        bio=payload.bio,
        longitude=payload.longitude,
        latitude=payload.latitude,
        user=current_user,
    )
    res = await use_case.execute(cmd)
    return TechnicianResponse(
        id=res.id.value,
        user_id=res.user_id.value,
        full_name=res.full_name,
        phone_number=res.phone_number,
        specialties=res.specialties,
        experience_years=res.experience_years,
        bio=res.bio,
        verification_status=res.verification_status,
        rating_average=res.rating_average,
        reviews_count=res.reviews_count,
        longitude=res.longitude,
        latitude=res.latitude,
        created_at=res.created_at,
    )


@router.patch("/technicians/{technician_id}/verify", response_model=TechnicianResponse)
async def verify_technician(
    technician_id: str,
    payload: VerifyTechnicianRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> TechnicianResponse:
    repo = MongoTechnicianRepository(db)
    use_case = VerifyTechnicianUseCase(repo)

    cmd = VerifyTechnicianCommand(
        technician_id=technician_id,
        approve=payload.approve,
        admin_user=current_user,
    )
    res = await use_case.execute(cmd)
    return TechnicianResponse(
        id=res.id.value,
        user_id=res.user_id.value,
        full_name=res.full_name,
        phone_number=res.phone_number,
        specialties=res.specialties,
        experience_years=res.experience_years,
        bio=res.bio,
        verification_status=res.verification_status,
        rating_average=res.rating_average,
        reviews_count=res.reviews_count,
        longitude=res.longitude,
        latitude=res.latitude,
        created_at=res.created_at,
    )


@router.get("/technicians/search", response_model=list[TechnicianResponse])
async def search_technicians(
    longitude: float = Query(..., ge=-180.0, le=180.0),
    latitude: float = Query(..., ge=-90.0, le=90.0),
    radius_meters: float = Query(15000.0, ge=100.0, le=50000.0),
    specialty: Specialty | None = Query(None),
    only_verified: bool = Query(True),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> list[TechnicianResponse]:
    repo = MongoTechnicianRepository(db)
    items = await repo.search_nearby(
        longitude=longitude,
        latitude=latitude,
        max_distance_meters=radius_meters,
        specialty=specialty,
        only_verified=only_verified,
        limit=limit,
    )
    return [
        TechnicianResponse(
            id=t.id.value,
            user_id=t.user_id.value,
            full_name=t.full_name,
            phone_number=t.phone_number,
            specialties=t.specialties,
            experience_years=t.experience_years,
            bio=t.bio,
            verification_status=t.verification_status,
            rating_average=t.rating_average,
            reviews_count=t.reviews_count,
            longitude=t.longitude,
            latitude=t.latitude,
            created_at=t.created_at,
        )
        for t in items
    ]


@router.get("/technicians/{technician_id}/whatsapp", response_model=WhatsAppContactResponse)
async def get_technician_whatsapp_link(
    technician_id: str,
    message: str = Query("Hola, te contacto desde PrevenRed para una cotización."),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> WhatsAppContactResponse:
    repo = MongoTechnicianRepository(db)
    profile = await repo.get_by_id(EntityId(technician_id))
    if not profile:
        raise NotFoundError(f"Técnico con ID '{technician_id}' no encontrado.")

    wa_url = profile.generate_whatsapp_link(message=message)
    return WhatsAppContactResponse(
        technician_name=profile.full_name,
        whatsapp_url=wa_url,
    )
