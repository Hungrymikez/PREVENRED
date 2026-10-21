"""Interfaces de repositorio para perfiles y asignaciones de voluntariado."""

from abc import ABC, abstractmethod

from prevenred.shared.domain.ids import EntityId

from .volunteer import VolunteerAssignment, VolunteerProfile


class VolunteerRepository(ABC):
    @abstractmethod
    async def save_profile(self, profile: VolunteerProfile) -> None:
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: EntityId) -> VolunteerProfile | None:
        pass

    @abstractmethod
    async def get_by_id(self, volunteer_id: EntityId) -> VolunteerProfile | None:
        pass

    @abstractmethod
    async def save_assignment(self, assignment: VolunteerAssignment) -> None:
        pass

    @abstractmethod
    async def list_assignments_by_volunteer(
        self, volunteer_id: EntityId
    ) -> list[VolunteerAssignment]:
        pass
