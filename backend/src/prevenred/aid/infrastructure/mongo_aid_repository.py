from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import GEOSPHERE

from prevenred.shared.domain.ids import EntityId

from ..domain.aid import (
    AidCategory,
    AidNeed,
    AidOffer,
    AidPriority,
    AidStatus,
    DonationMatch,
)
from ..domain.repositories import AidRepository


class MongoAidRepository(AidRepository):
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._offers = database["aid_inventory"]
        self._needs = database["aid_needs"]
        self._matches = database["donation_matches"]

    async def create_indexes(self) -> None:
        await self._offers.create_index([("location", GEOSPHERE)])
        await self._offers.create_index("status")
        await self._offers.create_index("category")
        await self._needs.create_index([("location", GEOSPHERE)])
        await self._needs.create_index("status")
        await self._needs.create_index("category")
        await self._matches.create_index("need_id")
        await self._matches.create_index("offer_id")

    def _offer_to_doc(self, o: AidOffer) -> dict[str, Any]:
        return {
            "_id": o.id.value,
            "title": o.title,
            "category": o.category.value,
            "quantity": o.quantity,
            "unit": o.unit,
            "donor_id": o.donor_id.value,
            "location": {"type": "Point", "coordinates": [o.longitude, o.latitude]},
            "status": o.status.value,
            "created_at": o.created_at,
            "source_material_id": o.source_material_id.value if o.source_material_id else None,
        }

    def _doc_to_offer(self, d: dict[str, Any]) -> AidOffer:
        coords = d["location"]["coordinates"]
        source_id = EntityId(d["source_material_id"]) if d.get("source_material_id") else None
        return AidOffer(
            id=EntityId(str(d["_id"])),
            title=d["title"],
            category=AidCategory(d["category"]),
            quantity=float(d["quantity"]),
            unit=d["unit"],
            donor_id=EntityId(str(d["donor_id"])),
            longitude=float(coords[0]),
            latitude=float(coords[1]),
            status=AidStatus(d["status"]),
            created_at=d["created_at"],
            source_material_id=source_id,
        )

    def _need_to_doc(self, n: AidNeed) -> dict[str, Any]:
        return {
            "_id": n.id.value,
            "title": n.title,
            "category": n.category.value,
            "quantity": n.quantity,
            "unit": n.unit,
            "priority": n.priority.value,
            "requester_id": n.requester_id.value,
            "location": {"type": "Point", "coordinates": [n.longitude, n.latitude]},
            "status": n.status.value,
            "created_at": n.created_at,
        }

    def _doc_to_need(self, d: dict[str, Any]) -> AidNeed:
        coords = d["location"]["coordinates"]
        return AidNeed(
            id=EntityId(str(d["_id"])),
            title=d["title"],
            category=AidCategory(d["category"]),
            quantity=float(d["quantity"]),
            unit=d["unit"],
            priority=AidPriority(d["priority"]),
            requester_id=EntityId(str(d["requester_id"])),
            longitude=float(coords[0]),
            latitude=float(coords[1]),
            status=AidStatus(d["status"]),
            created_at=d["created_at"],
        )

    async def save_offer(self, offer: AidOffer) -> None:
        await self._offers.replace_one(
            {"_id": offer.id.value}, self._offer_to_doc(offer), upsert=True
        )

    async def list_pending_offers(self, category: AidCategory | None = None) -> list[AidOffer]:
        q: dict[str, Any] = {"status": AidStatus.PENDIENTE.value}
        if category:
            q["category"] = category.value
        docs = await self._offers.find(q).to_list(length=100)
        return [self._doc_to_offer(d) for d in docs]

    async def save_need(self, need: AidNeed) -> None:
        await self._needs.replace_one({"_id": need.id.value}, self._need_to_doc(need), upsert=True)

    async def list_pending_needs(self, category: AidCategory | None = None) -> list[AidNeed]:
        q: dict[str, Any] = {"status": AidStatus.PENDIENTE.value}
        if category:
            q["category"] = category.value
        docs = await self._needs.find(q).to_list(length=100)
        return [self._doc_to_need(d) for d in docs]

    async def save_match(self, match: DonationMatch) -> None:
        doc = {
            "_id": match.id.value,
            "need_id": match.need_id.value,
            "offer_id": match.offer_id.value,
            "matched_quantity": match.matched_quantity,
            "distance_meters": match.distance_meters,
            "matched_by": match.matched_by.value,
            "matched_at": match.matched_at,
            "is_confirmed": match.is_confirmed,
        }
        await self._matches.replace_one({"_id": match.id.value}, doc, upsert=True)
