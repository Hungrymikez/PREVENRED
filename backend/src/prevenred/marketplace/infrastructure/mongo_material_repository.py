from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import GEOSPHERE

from prevenred.shared.domain.ids import EntityId

from ..domain.material import (
    Material,
    MaterialCategory,
    MaterialCondition,
    OfferType,
)
from ..domain.repositories import MaterialRepository


class MongoMaterialRepository(MaterialRepository):
    COLLECTION_NAME = "materials"

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._collection = database[self.COLLECTION_NAME]

    async def create_indexes(self) -> None:
        await self._collection.create_index([("location", GEOSPHERE)])
        await self._collection.create_index("category")
        await self._collection.create_index("offer_type")
        await self._collection.create_index("is_active")

    def _to_doc(self, material: Material) -> dict[str, Any]:
        return {
            "_id": material.id.value,
            "title": material.title,
            "description": material.description,
            "category": material.category.value,
            "offer_type": material.offer_type.value,
            "condition": material.condition.value,
            "quantity": material.quantity,
            "unit": material.unit,
            "price": material.price,
            "location": {
                "type": "Point",
                "coordinates": [material.longitude, material.latitude],
            },
            "owner_id": material.owner_id.value,
            "media_urls": material.media_urls,
            "is_active": material.is_active,
            "created_at": material.created_at,
        }

    def _to_entity(self, doc: dict[str, Any]) -> Material:
        coords = doc["location"]["coordinates"]
        return Material(
            id=EntityId(str(doc["_id"])),
            title=doc["title"],
            description=doc.get("description", ""),
            category=MaterialCategory(doc["category"]),
            offer_type=OfferType(doc["offer_type"]),
            condition=MaterialCondition(doc["condition"]),
            quantity=float(doc["quantity"]),
            unit=doc["unit"],
            price=float(doc["price"]) if doc.get("price") is not None else None,
            longitude=float(coords[0]),
            latitude=float(coords[1]),
            owner_id=EntityId(str(doc["owner_id"])),
            media_urls=doc.get("media_urls", []),
            is_active=bool(doc.get("is_active", True)),
            created_at=doc["created_at"],
        )

    async def save(self, material: Material) -> None:
        doc = self._to_doc(material)
        await self._collection.replace_one({"_id": material.id.value}, doc, upsert=True)

    async def get_by_id(self, material_id: EntityId) -> Material | None:
        doc = await self._collection.find_one({"_id": material_id.value})
        return self._to_entity(doc) if doc else None

    async def search_nearby(
        self,
        longitude: float,
        latitude: float,
        max_distance_meters: float = 10000.0,
        category: MaterialCategory | None = None,
        offer_type: OfferType | None = None,
        limit: int = 50,
    ) -> list[Material]:
        filter_query: dict[str, Any] = {
            "is_active": True,
            "location": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [longitude, latitude],
                    },
                    "$maxDistance": max_distance_meters,
                }
            },
        }
        if category:
            filter_query["category"] = category.value
        if offer_type:
            filter_query["offer_type"] = offer_type.value

        cursor = self._collection.find(filter_query).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._to_entity(d) for d in docs]
