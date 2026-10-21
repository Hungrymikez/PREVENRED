from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    actor_id: str
    action: str
    resource: str
    resource_id: str
    details: dict[str, Any]
    created_at: datetime
