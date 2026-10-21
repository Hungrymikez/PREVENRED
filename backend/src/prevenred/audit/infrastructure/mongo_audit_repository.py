from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from prevenred.shared.domain.ids import EntityId

from ..domain.audit_log import AuditLog
from ..domain.repositories import AuditRepository


class MongoAuditRepository(AuditRepository):
    COLLECTION_NAME = "audit_logs"

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._collection = database[self.COLLECTION_NAME]

    async def create_indexes(self) -> None:
        await self._collection.create_index("created_at")
        await self._collection.create_index("resource")
        await self._collection.create_index("actor_id")

    async def save(self, log: AuditLog) -> None:
        doc = {
            "_id": log.id.value,
            "actor_id": log.actor_id.value,
            "action": log.action,
            "resource": log.resource,
            "resource_id": log.resource_id,
            "details": log.details,
            "created_at": log.created_at,
        }
        await self._collection.insert_one(doc)

    async def list_recent(
        self,
        resource: str | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        query: dict[str, Any] = {}
        if resource:
            query["resource"] = resource.lower()

        docs = (
            await self._collection.find(query)
            .sort("created_at", -1)
            .limit(limit)
            .to_list(length=limit)
        )
        return [
            AuditLog(
                id=EntityId(str(d["_id"])),
                actor_id=EntityId(str(d["actor_id"])),
                action=d["action"],
                resource=d["resource"],
                resource_id=d["resource_id"],
                details=d.get("details", {}),
                created_at=d["created_at"],
            )
            for d in docs
        ]
