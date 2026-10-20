"""Casos de uso para registro y gestión operativa de voluntarios."""

from dataclasses import dataclass

from prevenred.identity.domain.role import Role
from prevenred.identity.domain.user import User
from prevenred.shared.domain.errors import AuthorizationError, NotFoundError
from prevenred.shared.domain.ids import EntityId

from ..domain.repositories import VolunteerRepository
from ..domain.volunteer import (
    VolunteerAssignment,
    VolunteerProfile,
    VolunteerSkill,
)


@dataclass(frozen=True)
class RegisterVolunteerCommand:
    full_name: str
    phone_number: str
    skills: list[VolunteerSkill]
    longitude: float
    latitude: float
    user: User


@dataclass(frozen=True)
class AssignVolunteerCommand:
    volunteer_id: str
    incident_id: str
    task_description: str
    coordinator: User


class ManageVolunteeringUseCase:
    def __init__(self, repository: VolunteerRepository) -> None:
        self._repository = repository

    async def register_volunteer(self, command: RegisterVolunteerCommand) -> VolunteerProfile:
        user_id = EntityId(command.user.id)
        existing = await self._repository.get_by_user_id(user_id)
        if existing:
            existing.full_name = command.full_name
            existing.phone_number = command.phone_number
            existing.skills = command.skills
            existing.longitude = command.longitude
            existing.latitude = command.latitude
            await self._repository.save_profile(existing)
            return existing

        profile = VolunteerProfile.create(
            user_id=user_id,
            full_name=command.full_name,
            phone_number=command.phone_number,
            skills=command.skills,
            longitude=command.longitude,
            latitude=command.latitude,
        )
        await self._repository.save_profile(profile)
        return profile

    async def assign_volunteer(self, command: AssignVolunteerCommand) -> VolunteerAssignment:
        if command.coordinator.role not in (Role.ADMIN, Role.INSPECTOR):
            raise AuthorizationError("Solo coordinadores pueden asignar misiones de voluntariado.")

        profile = await self._repository.get_by_id(EntityId(command.volunteer_id))
        if not profile:
            raise NotFoundError(f"Voluntario '{command.volunteer_id}' no encontrado.")

        coordinator_id = EntityId(command.coordinator.id)
        assignment = VolunteerAssignment.create(
            volunteer_id=profile.id,
            incident_id=EntityId(command.incident_id),
            task_description=command.task_description,
            assigned_by=coordinator_id,
        )
        await self._repository.save_assignment(assignment)
        return assignment
