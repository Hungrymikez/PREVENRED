from datetime import datetime

from pydantic import BaseModel, Field

from ..domain.aid import AidCategory, AidPriority, AidStatus


class RequestAidPayload(BaseModel):
    title: str = Field(..., min_length=3)
    category: AidCategory
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1)
    priority: AidPriority = AidPriority.MEDIA
    longitude: float = Field(..., ge=-180.0, le=180.0)
    latitude: float = Field(..., ge=-90.0, le=90.0)


class OfferAidPayload(BaseModel):
    title: str = Field(..., min_length=3)
    category: AidCategory
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    source_material_id: str | None = None


class AidNeedResponse(BaseModel):
    id: str
    title: str
    category: AidCategory
    quantity: float
    unit: str
    priority: AidPriority
    requester_id: str
    longitude: float
    latitude: float
    status: AidStatus
    created_at: datetime


class AidOfferResponse(BaseModel):
    id: str
    title: str
    category: AidCategory
    quantity: float
    unit: str
    donor_id: str
    longitude: float
    latitude: float
    status: AidStatus
    created_at: datetime
    source_material_id: str | None = None


class DonationMatchResponse(BaseModel):
    id: str
    need_id: str
    offer_id: str
    matched_quantity: float
    distance_meters: float
    matched_by: str
    matched_at: datetime
    is_confirmed: bool
