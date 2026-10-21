from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from prevenred.shared.domain.ids import EntityId

from ..domain.layer import LayerCategory, MapLayer
from ..domain.repositories import GeoRepository


class MongoGeoRepository(GeoRepository):
    COLLECTION_NAME = "map_layers"

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._collection = database[self.COLLECTION_NAME]

    async def save_layer(self, layer: MapLayer) -> None:
        doc = {
            "_id": layer.id.value,
            "name": layer.name,
            "category": layer.category.value,
            "geojson_data": layer.geojson_data,
            "is_active": layer.is_active,
            "created_at": layer.created_at,
        }
        await self._collection.replace_one({"_id": layer.id.value}, doc, upsert=True)

    async def list_active_layers(self, category: LayerCategory | None = None) -> list[MapLayer]:
        query: dict[str, Any] = {"is_active": True}
        if category:
            query["category"] = category.value
        docs = await self._collection.find(query).to_list(length=50)
        return [
            MapLayer(
                id=EntityId(str(d["_id"])),
                name=d["name"],
                category=LayerCategory(d["category"]),
                geojson_data=d["geojson_data"],
                is_active=bool(d["is_active"]),
                created_at=d["created_at"],
            )
            for d in docs
        ]
