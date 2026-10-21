from datetime import datetime

from pydantic import BaseModel, Field

from ..domain.technician import Specialty, VerificationStatus


class RegisterTechnicianRequest(BaseModel):
    full_name: str = Field(..., min_length=3)
    phone_number: str = Field(..., min_length=7)
    specialties: list[Specialty] = Field(..., min_length=1)
    experience_years: int = Field(..., ge=0)
    bio: str = Field(default="")
    longitude: float = Field(..., ge=-180.0, le=180.0)
    latitude: float = Field(..., ge=-90.0, le=90.0)


class VerifyTechnicianRequest(BaseModel):
    approve: bool = Field(..., description="True para verificar, False para rechazar")


class TechnicianResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    phone_number: str
    specialties: list[Specialty]
    experience_years: int
    bio: str
    verification_status: VerificationStatus
    rating_average: float
    reviews_count: int
    longitude: float
    latitude: float
    created_at: datetime


class WhatsAppContactResponse(BaseModel):
    technician_name: str
    whatsapp_url: str
