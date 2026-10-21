from dataclasses import dataclass
from typing import Any

from prevenred.auth.domain.role import Role
from prevenred.auth.domain.user import User
from prevenred.shared.domain.errors import AuthorizationError
from prevenred.shared.domain.ids import EntityId

from ..domain.audit_log import AuditLog
from ..domain.repositories import AuditRepository


@dataclass(frozen=True)
class RecordAuditCommand:
    actor_id: str
    action: str
    resource: str
    resource_id: str
    details: dict[str, Any]


class AuditUseCase:
    def __init__(self, repository: AuditRepository) -> None:
        self._repository = repository

    async def record_event(self, command: RecordAuditCommand) -> AuditLog:
        log = AuditLog.create(
            actor_id=EntityId(command.actor_id),
            action=command.action,
            resource=command.resource,
            resource_id=command.resource_id,
            details=command.details,
        )
        await self._repository.save(log)
        return log

    async def list_logs(
        self, user: User, resource: str | None = None, limit: int = 100
    ) -> list[AuditLog]:
        if user.role != Role.ADMIN:
            raise AuthorizationError(
                "Solo administradores pueden consultar registros de auditoría."
            )
        return await self._repository.list_recent(resource=resource, limit=limit)
