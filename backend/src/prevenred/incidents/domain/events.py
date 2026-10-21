"""Eventos que publica el contexto incidents."""

from dataclasses import dataclass

from prevenred.shared.domain.events import DomainEvent
from prevenred.shared.domain.ids import EntityId

from .incident import IncidentStatus, IncidentType


@dataclass(frozen=True, kw_only=True)
class IncidentReportedEvent(DomainEvent):
    """Publicado al crear un reporte (CU-29)."""

    incident_id: EntityId
    case_number: str
    incident_type: IncidentType
    reported_by: EntityId


@dataclass(frozen=True, kw_only=True)
class IncidentStatusChangedEvent(DomainEvent):
    """Publicado al cambiar el estado (CU-39)."""

    incident_id: EntityId
    previous_status: IncidentStatus
    new_status: IncidentStatus
    changed_by: EntityId
