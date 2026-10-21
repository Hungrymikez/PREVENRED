"""Esquemas Pydantic para el API de bienestar emocional."""

from datetime import datetime

from pydantic import BaseModel, Field


class GrantConsentRequest(BaseModel):
    terms_version: str = Field(default="v1.0")


class ConsentResponse(BaseModel):
    user_id: str
    terms_version: str
    consented_at: datetime
    is_revoked: bool


class SubmitSurveyRequest(BaseModel):
    neighborhood: str = Field(..., min_length=2, description="Comuna o Barrio de Pereira")
    mood_score: int = Field(..., ge=1, le=5, description="1: Muy mal, 5: Muy bien")
    text: str | None = Field(default="", max_length=1000)


class SurveySubmissionResponse(BaseModel):
    survey_id: str
    neighborhood: str
    mood_score: int
    crisis_detected: bool
    crisis_support_message: str | None = None


class CommunityIndicatorResponse(BaseModel):
    neighborhood: str
    sample_count: int
    average_mood: float
    crisis_alerts: int


class CrisisHelplineResponse(BaseModel):
    city: str
    helplines: list[dict[str, str]]
