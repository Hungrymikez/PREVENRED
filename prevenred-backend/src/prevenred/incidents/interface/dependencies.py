"""Cableado del contexto incidents (inyección de dependencias)."""

from fastapi import Depends
from pymongo.database import Database

from prevenred.identity.application.ports import TokenPayload
from prevenred.identity.domain.role import Role
from prevenred.identity.interface.dependencies import get_current_token, require_roles
from prevenred.incidents.application.list_incidents import ListIncidents
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


require_authenticated = get_current_token
require_incident_staff = require_roles(Role.ADMINISTRADOR, Role.INSPECTOR)


def get_staff_token(
    token: TokenPayload = Depends(require_incident_staff),
) -> TokenPayload:
    return token
