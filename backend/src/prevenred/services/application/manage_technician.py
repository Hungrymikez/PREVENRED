from dataclasses import dataclass

from prevenred.auth.domain.role import Role
from prevenred.auth.domain.user import User
from prevenred.shared.domain.errors import AuthorizationError, NotFoundError
from prevenred.shared.domain.ids import EntityId

from ..domain.repositories import TechnicianRepository
from ..domain.technician import Specialty, TechnicianProfile, VerificationStatus


@dataclass(frozen=True)
class RegisterTechnicianProfileCommand:
    full_name: str
    phone_number: str
    specialties: list[Specialty]
    experience_years: int
    bio: str
    longitude: float
    latitude: float
    user: User


class RegisterTechnicianProfileUseCase:
    def __init__(self, repository: TechnicianRepository) -> None:
        self._repository = repository

    async def execute(self, command: RegisterTechnicianProfileCommand) -> TechnicianProfile:
        user_id = EntityId(command.user.id)
        existing = await self._repository.get_by_user_id(user_id)
        if existing:
            existing.full_name = command.full_name
            existing.phone_number = command.phone_number
            existing.specialties = command.specialties
            existing.experience_years = command.experience_years
            existing.bio = command.bio
            existing.longitude = command.longitude
            existing.latitude = command.latitude
            await self._repository.save(existing)
            return existing

        profile = TechnicianProfile.create(
            user_id=user_id,
            full_name=command.full_name,
            phone_number=command.phone_number,
            specialties=command.specialties,
            experience_years=command.experience_years,
            bio=command.bio,
            longitude=command.longitude,
            latitude=command.latitude,
        )
        await self._repository.save(profile)
        return profile


@dataclass(frozen=True)
class VerifyTechnicianCommand:
    technician_id: str
    approve: bool
    admin_user: User


class VerifyTechnicianUseCase:
    def __init__(self, repository: TechnicianRepository) -> None:
        self._repository = repository

    async def execute(self, command: VerifyTechnicianCommand) -> TechnicianProfile:
        if command.admin_user.role != Role.ADMIN:
            raise AuthorizationError("Solo administradores pueden verificar perfiles técnicos.")

        profile = await self._repository.get_by_id(EntityId(command.technician_id))
        if not profile:
            raise NotFoundError(f"Técnico con ID '{command.technician_id}' no encontrado.")

        admin_id = EntityId(command.admin_user.id)
        if command.approve:
            profile.verify(admin_id)
        else:
            profile.reject(admin_id)

        await self._repository.save(profile)
        return profile


class GetMyTechnicianProfileUseCase:
    """CU-17: el técnico consulta su propio perfil (y su estado de verificación)."""

    def __init__(self, repository: TechnicianRepository) -> None:
        self._repository = repository

    async def execute(self, user: User) -> TechnicianProfile:
        profile = await self._repository.get_by_user_id(EntityId(user.id))
        if not profile:
            raise NotFoundError("Aún no has registrado tu perfil de técnico.")
        return profile


class GetTechnicianProfileUseCase:
    """CU-19: detalle de un técnico. RN-05: solo el Administrador (o el dueño del perfil)
    ve perfiles no verificados; para los demás se responde 404."""

    def __init__(self, repository: TechnicianRepository) -> None:
        self._repository = repository

    async def execute(self, technician_id: str, viewer: User) -> TechnicianProfile:
        profile = await self._repository.get_by_id(EntityId(technician_id))
        if profile is None or not (
            profile.verification_status == VerificationStatus.VERIFIED
            or viewer.role == Role.ADMIN
            or profile.user_id == EntityId(viewer.id)
        ):
            raise NotFoundError(f"Técnico con ID '{technician_id}' no encontrado.")
        return profile


class ListPendingTechniciansUseCase:
    """CU-18: el Administrador revisa los perfiles que esperan verificación."""

    def __init__(self, repository: TechnicianRepository) -> None:
        self._repository = repository

    async def execute(self, admin_user: User, limit: int = 100) -> list[TechnicianProfile]:
        if admin_user.role != Role.ADMIN:
            raise AuthorizationError("Solo administradores pueden revisar perfiles técnicos.")
        return await self._repository.list_by_status(VerificationStatus.PENDING, limit=limit)
