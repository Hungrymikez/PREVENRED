"""Esquemas HTTP del contexto incidents."""

from datetime import datetime

from pydantic import BaseModel, Field

from prevenred.incidents.domain.incident import (
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)


class ReportIncidentRequest(BaseModel):
    """Cuerpo de POST /incidents."""

    incident_type: IncidentType
    severity: IncidentSeverity = IncidentSeverity.MEDIA
    description: str = Field(..., min_length=5)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    media_urls: list[str] = Field(default_factory=list)


class UpdateIncidentStatusRequest(BaseModel):
    """Cuerpo de PATCH /incidents/{id}/status."""

    new_status: IncidentStatus
    notes: str = Field(default="", max_length=500)


class IncidentResponse(BaseModel):
    """Representación pública de un incidente."""

    id: str
    case_number: str
    incident_type: IncidentType
    severity: IncidentSeverity
    status: IncidentStatus
    description: str
    longitude: float
    latitude: float
    reported_by: str
    media_urls: list[str]
    created_at: datetime
