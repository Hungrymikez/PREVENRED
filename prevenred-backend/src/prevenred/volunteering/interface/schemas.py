"""Esquemas Pydantic para el API de voluntariado."""

from datetime import datetime

from pydantic import BaseModel, Field

from ..domain.volunteer import AssignmentStatus, VolunteerSkill


class RegisterVolunteerRequest(BaseModel):
    full_name: str = Field(..., min_length=3)
    phone_number: str = Field(..., min_length=7)
    skills: list[VolunteerSkill] = Field(..., min_length=1)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    latitude: float = Field(..., ge=-90.0, le=90.0)


class AssignVolunteerRequest(BaseModel):
    volunteer_id: str
    incident_id: str
    task_description: str = Field(..., min_length=5)


class VolunteerProfileResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    phone_number: str
    skills: list[VolunteerSkill]
    is_available: bool
    longitude: float
    latitude: float
    created_at: datetime


class AssignmentResponse(BaseModel):
    id: str
    volunteer_id: str
    incident_id: str
    task_description: str
    status: AssignmentStatus
    assigned_by: str
    created_at: datetime
