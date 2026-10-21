from typing import Annotated

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from prevenred.auth.domain.user import User
from prevenred.auth.interface.dependencies import get_current_user
from prevenred.shared.infrastructure.mongo import get_database

from ..application.record_audit import AuditUseCase
from ..infrastructure.mongo_audit_repository import MongoAuditRepository
from .schemas import AuditLogResponse

router = APIRouter(prefix="/audit", tags=["Audit & Governance"])


@router.get("/logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    resource: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> list[AuditLogResponse]:
    repo = MongoAuditRepository(db)
    use_case = AuditUseCase(repo)
    logs = await use_case.list_logs(user=current_user, resource=resource, limit=limit)
    return [
        AuditLogResponse(
            id=log.id.value,
            actor_id=log.actor_id.value,
            action=log.action,
            resource=log.resource,
            resource_id=log.resource_id,
            details=log.details,
            created_at=log.created_at,
        )
        for log in logs
    ]
