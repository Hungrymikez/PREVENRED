from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from prevenred.auth.domain.role import Role
from prevenred.auth.domain.user import User
from prevenred.auth.interface.dependencies import get_current_user
from prevenred.shared.domain.errors import NotFoundError
from prevenred.shared.domain.ids import EntityId
from prevenred.shared.infrastructure.mongo import get_database

from ..application.manage_technician import (
    GetMyTechnicianProfileUseCase,
    GetTechnicianProfileUseCase,
    ListPendingTechniciansUseCase,
    RegisterTechnicianProfileCommand,
    RegisterTechnicianProfileUseCase,
    VerifyTechnicianCommand,
    VerifyTechnicianUseCase,
)
from ..domain.technician import Specialty, TechnicianProfile, VerificationStatus
from ..infrastructure.mongo_technician_repository import MongoTechnicianRepository
from .schemas import (
    RegisterTechnicianRequest,
    TechnicianResponse,
    VerifyTechnicianRequest,
    WhatsAppContactResponse,
)

router = APIRouter(prefix="/services", tags=["Services - OficiosYa"])


def _to_response(profile: TechnicianProfile) -> TechnicianResponse:
    return TechnicianResponse(
        id=profile.id.value,
        user_id=profile.user_id.value,
        full_name=profile.full_name,
        phone_number=profile.phone_number,
        specialties=profile.specialties,
        experience_years=profile.experience_years,
        bio=profile.bio,
        verification_status=profile.verification_status,
        rating_average=profile.rating_average,
        reviews_count=profile.reviews_count,
        longitude=profile.longitude,
        latitude=profile.latitude,
        created_at=profile.created_at,
    )


# Las rutas fijas (/me, /pending, /search) van antes de /technicians/{technician_id}.
@router.get("/technicians/me", response_model=TechnicianResponse)
async def get_my_technician_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> TechnicianResponse:
    """CU-17: perfil propio del técnico con su estado de verificación (404 si no existe)."""
    use_case = GetMyTechnicianProfileUseCase(MongoTechnicianRepository(db))
    return _to_response(await use_case.execute(current_user))


@router.get("/technicians/pending", response_model=list[TechnicianResponse])
async def list_pending_technicians(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    limit: int = Query(100, ge=1, le=200),
) -> list[TechnicianResponse]:
    """CU-18: perfiles pendientes de verificación (solo Administrador)."""
    use_case = ListPendingTechniciansUseCase(MongoTechnicianRepository(db))
    items = await use_case.execute(current_user, limit=limit)
    return [_to_response(t) for t in items]


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
    return _to_response(res)


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
    return _to_response(res)


@router.get("/technicians/search", response_model=list[TechnicianResponse])
async def search_technicians(
    longitude: float = Query(..., ge=-180.0, le=180.0),
    latitude: float = Query(..., ge=-90.0, le=90.0),
    radius_meters: float = Query(15000.0, ge=100.0, le=50000.0),
    specialty: Specialty | None = Query(None),
    only_verified: bool = Query(True),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> list[TechnicianResponse]:
    """CU-19: técnicos cercanos. Exige sesión; solo el Administrador ve los no verificados
    (incluye su teléfono y ubicación, RN-05)."""
    if current_user.role != Role.ADMIN:
        only_verified = True
    repo = MongoTechnicianRepository(db)
    items = await repo.search_nearby(
        longitude=longitude,
        latitude=latitude,
        max_distance_meters=radius_meters,
        specialty=specialty,
        only_verified=only_verified,
        limit=limit,
    )
    return [_to_response(t) for t in items]


@router.get("/technicians/{technician_id}/whatsapp", response_model=WhatsAppContactResponse)
async def get_technician_whatsapp_link(
    technician_id: str,
    message: str = Query("Hola, te contacto desde PrevenRed para una cotización."),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> WhatsAppContactResponse:
    """CU-22. RN-05: el número de un técnico sin verificar no se entrega (solo al
    Administrador o al propio técnico); para los demás responde como si no existiera."""
    repo = MongoTechnicianRepository(db)
    profile = await repo.get_by_id(EntityId(technician_id))
    visible = profile is not None and (
        profile.verification_status == VerificationStatus.VERIFIED
        or current_user.role == Role.ADMIN
        or profile.user_id.value == str(getattr(current_user.id, "value", current_user.id))
    )
    if not visible:
        raise NotFoundError(f"Técnico con ID '{technician_id}' no encontrado.")

    wa_url = profile.generate_whatsapp_link(message=message)
    return WhatsAppContactResponse(
        technician_name=profile.full_name,
        whatsapp_url=wa_url,
    )


@router.get("/technicians/{technician_id}", response_model=TechnicianResponse)
async def get_technician(
    technician_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> TechnicianResponse:
    """CU-19: detalle de un técnico; los no verificados solo los ve el Administrador o su dueño."""
    use_case = GetTechnicianProfileUseCase(MongoTechnicianRepository(db))
    return _to_response(await use_case.execute(technician_id, current_user))
