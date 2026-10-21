from abc import ABC, abstractmethod

from .audit_log import AuditLog


class AuditRepository(ABC):
    @abstractmethod
    async def save(self, log: AuditLog) -> None:
        pass

    @abstractmethod
    async def list_recent(
        self,
        resource: str | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        pass
