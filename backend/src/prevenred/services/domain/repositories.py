from abc import ABC, abstractmethod

from prevenred.shared.domain.ids import EntityId

from .technician import Specialty, TechnicianProfile, VerificationStatus


class TechnicianRepository(ABC):
    @abstractmethod
    async def save(self, profile: TechnicianProfile) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, profile_id: EntityId) -> TechnicianProfile | None:
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: EntityId) -> TechnicianProfile | None:
        pass

    @abstractmethod
    async def search_nearby(
        self,
        longitude: float,
        latitude: float,
        max_distance_meters: float = 15000.0,
        specialty: Specialty | None = None,
        only_verified: bool = True,
        limit: int = 50,
    ) -> list[TechnicianProfile]:
        pass

    @abstractmethod
    async def list_by_status(
        self, status: VerificationStatus, limit: int = 100
    ) -> list[TechnicianProfile]:
        """Perfiles en un estado de verificación, los más antiguos primero (CU-18)."""
