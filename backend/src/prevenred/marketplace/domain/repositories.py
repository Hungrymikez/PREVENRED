from abc import ABC, abstractmethod

from prevenred.shared.domain.ids import EntityId

from .material import Material, MaterialCategory, OfferType


class MaterialRepository(ABC):
    @abstractmethod
    async def save(self, material: Material) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, material_id: EntityId) -> Material | None:
        pass

    @abstractmethod
    async def search_nearby(
        self,
        longitude: float,
        latitude: float,
        max_distance_meters: float = 10000.0,
        category: MaterialCategory | None = None,
        offer_type: OfferType | None = None,
        limit: int = 50,
    ) -> list[Material]:
        pass
