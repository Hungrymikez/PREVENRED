from dataclasses import dataclass

from ..domain.material import Material, MaterialCategory, OfferType
from ..domain.repositories import MaterialRepository


@dataclass(frozen=True)
class SearchMaterialsQuery:
    longitude: float
    latitude: float
    max_distance_meters: float = 10000.0
    category: MaterialCategory | None = None
    offer_type: OfferType | None = None
    limit: int = 50


class SearchMaterialsUseCase:
    def __init__(self, repository: MaterialRepository) -> None:
        self._repository = repository

    async def execute(self, query: SearchMaterialsQuery) -> list[Material]:
        return await self._repository.search_nearby(
            longitude=query.longitude,
            latitude=query.latitude,
            max_distance_meters=query.max_distance_meters,
            category=query.category,
            offer_type=query.offer_type,
            limit=query.limit,
        )
