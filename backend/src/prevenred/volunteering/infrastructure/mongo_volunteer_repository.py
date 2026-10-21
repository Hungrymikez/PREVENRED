"""Implementación MongoDB del repositorio de voluntarios y asignaciones operativas."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import GEOSPHERE

from prevenred.shared.domain.ids import EntityId

from ..domain.repositories import VolunteerRepository
from ..domain.volunteer import (
    AssignmentStatus,
    VolunteerAssignment,
    VolunteerProfile,
    VolunteerSkill,
)


class MongoVolunteerRepository(VolunteerRepository):
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._volunteers = database["volunteers"]
        self._assignments = database["assignments"]

    async def create_indexes(self) -> None:
        await self._volunteers.create_index([("location", GEOSPHERE)])
        await self._volunteers.create_index("user_id", unique=True)
        await self._volunteers.create_index("is_available")
        await self._assignments.create_index("volunteer_id")
        await self._assignments.create_index("incident_id")

    def _vol_to_doc(self, p: VolunteerProfile) -> dict[str, Any]:
        return {
            "_id": p.id.value,
            "user_id": p.user_id.value,
            "full_name": p.full_name,
            "phone_number": p.phone_number,
            "skills": [s.value for s in p.skills],
            "is_available": p.is_available,
            "location": {"type": "Point", "coordinates": [p.longitude, p.latitude]},
            "created_at": p.created_at,
        }

    def _doc_to_vol(self, d: dict[str, Any]) -> VolunteerProfile:
        coords = d["location"]["coordinates"]
        return VolunteerProfile(
            id=EntityId(str(d["_id"])),
            user_id=EntityId(str(d["user_id"])),
            full_name=d["full_name"],
            phone_number=d["phone_number"],
            skills=[VolunteerSkill(s) for s in d["skills"]],
            is_available=bool(d["is_available"]),
            longitude=float(coords[0]),
            latitude=float(coords[1]),
            created_at=d["created_at"],
        )

    async def save_profile(self, profile: VolunteerProfile) -> None:
        await self._volunteers.replace_one(
            {"_id": profile.id.value}, self._vol_to_doc(profile), upsert=True
        )

    async def get_by_user_id(self, user_id: EntityId) -> VolunteerProfile | None:
        d = await self._volunteers.find_one({"user_id": user_id.value})
        return self._doc_to_vol(d) if d else None

    async def get_by_id(self, volunteer_id: EntityId) -> VolunteerProfile | None:
        d = await self._volunteers.find_one({"_id": volunteer_id.value})
        return self._doc_to_vol(d) if d else None

    async def save_assignment(self, assignment: VolunteerAssignment) -> None:
        doc = {
            "_id": assignment.id.value,
            "volunteer_id": assignment.volunteer_id.value,
            "incident_id": assignment.incident_id.value,
            "task_description": assignment.task_description,
            "status": assignment.status.value,
            "assigned_by": assignment.assigned_by.value,
            "created_at": assignment.created_at,
        }
        await self._assignments.replace_one({"_id": assignment.id.value}, doc, upsert=True)

    async def list_assignments_by_volunteer(
        self, volunteer_id: EntityId
    ) -> list[VolunteerAssignment]:
        docs = (
            await self._assignments.find({"volunteer_id": volunteer_id.value})
            .sort("created_at", -1)
            .to_list(length=50)
        )
        return [
            VolunteerAssignment(
                id=EntityId(str(d["_id"])),
                volunteer_id=EntityId(str(d["volunteer_id"])),
                incident_id=EntityId(str(d["incident_id"])),
                task_description=d["task_description"],
                status=AssignmentStatus(d["status"]),
                assigned_by=EntityId(str(d["assigned_by"])),
                created_at=d["created_at"],
            )
            for d in docs
        ]
