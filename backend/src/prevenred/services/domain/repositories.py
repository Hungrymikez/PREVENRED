from abc import ABC, abstractmethod

from prevenred.shared.domain.ids import EntityId

from .technician import Specialty, TechnicianProfile


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
