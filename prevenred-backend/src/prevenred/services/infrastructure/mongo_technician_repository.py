from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import GEOSPHERE

from prevenred.shared.domain.ids import EntityId

from ..domain.repositories import TechnicianRepository
from ..domain.technician import Specialty, TechnicianProfile, VerificationStatus


class MongoTechnicianRepository(TechnicianRepository):
    COLLECTION_NAME = "technicians"

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._collection = database[self.COLLECTION_NAME]

    async def create_indexes(self) -> None:
        await self._collection.create_index([("location", GEOSPHERE)])
        await self._collection.create_index("user_id", unique=True)
        await self._collection.create_index("verification_status")
        await self._collection.create_index("specialties")

    def _to_doc(self, profile: TechnicianProfile) -> dict[str, Any]:
        return {
            "_id": profile.id.value,
            "user_id": profile.user_id.value,
            "full_name": profile.full_name,
            "phone_number": profile.phone_number,
            "specialties": [s.value for s in profile.specialties],
            "experience_years": profile.experience_years,
            "bio": profile.bio,
            "verification_status": profile.verification_status.value,
            "rating_average": profile.rating_average,
            "reviews_count": profile.reviews_count,
            "location": {
                "type": "Point",
                "coordinates": [profile.longitude, profile.latitude],
            },
            "created_at": profile.created_at,
            "verified_by": profile.verified_by.value if profile.verified_by else None,
        }

    def _to_entity(self, doc: dict[str, Any]) -> TechnicianProfile:
        coords = doc["location"]["coordinates"]
        verified_by = EntityId(doc["verified_by"]) if doc.get("verified_by") else None
        return TechnicianProfile(
            id=EntityId(str(doc["_id"])),
            user_id=EntityId(str(doc["user_id"])),
            full_name=doc["full_name"],
            phone_number=doc["phone_number"],
            specialties=[Specialty(s) for s in doc["specialties"]],
            experience_years=int(doc["experience_years"]),
            bio=doc.get("bio", ""),
            verification_status=VerificationStatus(doc["verification_status"]),
            rating_average=float(doc.get("rating_average", 0.0)),
            reviews_count=int(doc.get("reviews_count", 0)),
            longitude=float(coords[0]),
            latitude=float(coords[1]),
            created_at=doc["created_at"],
            verified_by=verified_by,
        )

    async def save(self, profile: TechnicianProfile) -> None:
        doc = self._to_doc(profile)
        await self._collection.replace_one({"_id": profile.id.value}, doc, upsert=True)

    async def get_by_id(self, profile_id: EntityId) -> TechnicianProfile | None:
        doc = await self._collection.find_one({"_id": profile_id.value})
        return self._to_entity(doc) if doc else None

    async def get_by_user_id(self, user_id: EntityId) -> TechnicianProfile | None:
        doc = await self._collection.find_one({"user_id": user_id.value})
        return self._to_entity(doc) if doc else None

    async def search_nearby(
        self,
        longitude: float,
        latitude: float,
        max_distance_meters: float = 15000.0,
        specialty: Specialty | None = None,
        only_verified: bool = True,
        limit: int = 50,
    ) -> list[TechnicianProfile]:
        filter_query: dict[str, Any] = {
            "location": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [longitude, latitude],
                    },
                    "$maxDistance": max_distance_meters,
                }
            }
        }
        if only_verified:
            filter_query["verification_status"] = VerificationStatus.VERIFIED.value
        if specialty:
            filter_query["specialties"] = specialty.value

        cursor = self._collection.find(filter_query).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._to_entity(d) for d in docs]
