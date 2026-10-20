"""Cableado del contexto fieldwork (inyección de dependencias)."""

from fastapi import Depends
from pymongo.database import Database

from prevenred.fieldwork.application.submit_inspection import SubmitInspection
from prevenred.fieldwork.domain.repositories import FieldworkRepository
from prevenred.fieldwork.infrastructure.mongo_fieldwork_repository import (
    MongoFieldworkRepository,
)
from prevenred.identity.application.ports import TokenPayload
from prevenred.identity.domain.role import Role
from prevenred.identity.interface.dependencies import require_roles
from prevenred.shared.application.event_bus import EventBus
from prevenred.shared.infrastructure.event_bus import event_bus
from prevenred.shared.infrastructure.mongo import get_db


def get_fieldwork_repository(db: Database = Depends(get_db)) -> FieldworkRepository:
    return MongoFieldworkRepository(db)


def get_event_bus() -> EventBus:
    return event_bus


def get_submit_inspection(
    repo: FieldworkRepository = Depends(get_fieldwork_repository),
    events: EventBus = Depends(get_event_bus),
) -> SubmitInspection:
    return SubmitInspection(repo, events)


require_field_staff = require_roles(Role.INSPECTOR, Role.ADMINISTRADOR)


def get_field_token(
    token: TokenPayload = Depends(require_field_staff),
) -> TokenPayload:
    return token
