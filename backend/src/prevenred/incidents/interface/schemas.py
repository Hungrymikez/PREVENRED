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
    client_id: str | None = Field(
        default=None,
        max_length=64,
        description="Id generado por el celular; al reintentar se devuelve el mismo caso (CU-37).",
    )
    reported_at: datetime | None = Field(
        default=None, description="Hora real del reporte si se hizo sin conexión."
    )


class UpdateIncidentStatusRequest(BaseModel):
    """Cuerpo de PATCH /incidents/{id}/status."""

    new_status: IncidentStatus
    notes: str = Field(default="", max_length=500)


class AssignIncidentRequest(BaseModel):
    """Cuerpo de PATCH /incidents/{id}/assign."""

    assignee_id: str = Field(..., min_length=1, description="Id de la cuenta del inspector")
    notes: str = Field(default="", max_length=500)


class IncidentHistoryEntry(BaseModel):
    """Cambio de estado del caso (RF-24)."""

    from_status: IncidentStatus
    to_status: IncidentStatus
    changed_at: datetime
    notes: str


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
    reported_at: datetime
    assigned_to: str | None = None
    history: list[IncidentHistoryEntry] = Field(default_factory=list)
