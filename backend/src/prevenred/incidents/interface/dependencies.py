"""Cableado del contexto incidents (inyección de dependencias)."""

from fastapi import Depends
from pymongo.database import Database

from prevenred.auth.application.ports import TokenPayload
from prevenred.auth.domain.repositories import UserRepository
from prevenred.auth.domain.role import Role
from prevenred.auth.interface.dependencies import (
    get_current_token,
    get_user_repository,
    require_roles,
)
from prevenred.incidents.application.assign_incident import AssignIncident
from prevenred.incidents.application.list_incidents import (
    GetIncidentByCaseNumber,
    ListIncidents,
)
from prevenred.incidents.application.report_incident import ReportIncident
from prevenred.incidents.application.update_incident_status import UpdateIncidentStatus
from prevenred.incidents.domain.repositories import IncidentRepository
from prevenred.incidents.infrastructure.mongo_incident_repository import (
    MongoIncidentRepository,
)
from prevenred.shared.application.event_bus import EventBus
from prevenred.shared.infrastructure.event_bus import event_bus
from prevenred.shared.infrastructure.mongo import get_db


def get_incident_repository(db: Database = Depends(get_db)) -> IncidentRepository:
    return MongoIncidentRepository(db)


def get_event_bus() -> EventBus:
    return event_bus


def get_report_incident(
    repo: IncidentRepository = Depends(get_incident_repository),
    events: EventBus = Depends(get_event_bus),
) -> ReportIncident:
    return ReportIncident(repo, events)


def get_update_incident_status(
    repo: IncidentRepository = Depends(get_incident_repository),
    events: EventBus = Depends(get_event_bus),
) -> UpdateIncidentStatus:
    return UpdateIncidentStatus(repo, events)


def get_list_incidents(
    repo: IncidentRepository = Depends(get_incident_repository),
) -> ListIncidents:
    return ListIncidents(repo)


def get_incident_by_case_number(
    repo: IncidentRepository = Depends(get_incident_repository),
) -> GetIncidentByCaseNumber:
    return GetIncidentByCaseNumber(repo)


def get_assign_incident(
    repo: IncidentRepository = Depends(get_incident_repository),
) -> AssignIncident:
    return AssignIncident(repo)


def get_user_role_lookup(users: UserRepository = Depends(get_user_repository)):
    """Devuelve una función id -> rol de la cuenta activa (None si no existe o está inactiva).
    Vive en el cableado para que incidents no dependa del interior de identity."""

    def lookup(user_id: str) -> Role | None:
        user = users.get_by_id(user_id)
        return user.role if user is not None and user.is_active else None

    return lookup


require_authenticated = get_current_token
require_incident_staff = require_roles(Role.ADMINISTRADOR, Role.INSPECTOR)


def get_staff_token(
    token: TokenPayload = Depends(require_incident_staff),
) -> TokenPayload:
    return token
