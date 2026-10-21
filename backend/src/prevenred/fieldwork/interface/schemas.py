"""Esquemas HTTP del contexto fieldwork."""

from datetime import datetime

from pydantic import BaseModel, Field

from prevenred.fieldwork.domain.inspection import DamageLevel, HabitabilityStatus


class SubmitInspectionRequest(BaseModel):
    """Cuerpo de POST /fieldwork/inspections."""

    property_address: str = Field(..., min_length=5)
    neighborhood: str = Field(..., min_length=2)
    residents_count: int = Field(..., ge=0)
    damage_level: DamageLevel
    habitability: HabitabilityStatus
    technical_notes: str = Field(default="")
    longitude: float = Field(..., ge=-180.0, le=180.0)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    photos: list[str] = Field(default_factory=list)


class PropertyInspectionResponse(BaseModel):
    """Representación pública de una inspección."""

    id: str
    property_address: str
    neighborhood: str
    residents_count: int
    damage_level: DamageLevel
    habitability: HabitabilityStatus
    technical_notes: str
    longitude: float
    latitude: float
    inspector_id: str
    photos: list[str]
    created_at: datetime
