from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from prevenred.shared.domain.entity import Entity
from prevenred.shared.domain.errors import DomainValidationError
from prevenred.shared.domain.ids import EntityId


@dataclass
class AuditLog(Entity):
    actor_id: EntityId
    action: str
    resource: str
    resource_id: str
    details: dict[str, Any]
    created_at: datetime

    @classmethod
    def create(
        cls,
        actor_id: EntityId,
        action: str,
        resource: str,
        resource_id: str,
        details: dict[str, Any] | None = None,
    ) -> "AuditLog":
        if not action or len(action.strip()) < 3:
            raise DomainValidationError("La acción a auditar debe tener al menos 3 caracteres.")
        if not resource or len(resource.strip()) < 2:
            raise DomainValidationError("El recurso auditado debe tener al menos 2 caracteres.")

        return cls(
            id=EntityId.generate(),
            actor_id=actor_id,
            action=action.strip().upper(),
            resource=resource.strip().lower(),
            resource_id=resource_id.strip(),
            details=details or {},
            created_at=datetime.now(UTC),
        )
