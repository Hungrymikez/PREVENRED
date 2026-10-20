from dataclasses import dataclass

from prevenred.identity.domain.user import User
from prevenred.shared.domain.ids import EntityId

from ..domain.material import Material, MaterialCategory, MaterialCondition, OfferType
from ..domain.repositories import MaterialRepository


@dataclass(frozen=True)
class PublishMaterialCommand:
    title: str
    description: str
    category: MaterialCategory
    offer_type: OfferType
    condition: MaterialCondition
    quantity: float
    unit: str
    longitude: float
    latitude: float
    owner: User
    price: float | None = None
    media_urls: list[str] | None = None


class PublishMaterialUseCase:
    def __init__(self, repository: MaterialRepository) -> None:
        self._repository = repository

    async def execute(self, command: PublishMaterialCommand) -> Material:
        owner_id = EntityId(command.owner.id)
        material = Material.create(
            title=command.title,
            description=command.description,
            category=command.category,
            offer_type=command.offer_type,
            condition=command.condition,
            quantity=command.quantity,
            unit=command.unit,
            longitude=command.longitude,
            latitude=command.latitude,
            owner_id=owner_id,
            price=command.price,
            media_urls=command.media_urls,
        )
        await self._repository.save(material)
        return material
