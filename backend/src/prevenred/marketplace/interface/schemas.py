from datetime import datetime

from pydantic import BaseModel, Field

from ..domain.material import MaterialCategory, MaterialCondition, OfferType


class PublishMaterialRequest(BaseModel):
    title: str = Field(..., min_length=3)
    description: str = Field(default="")
    category: MaterialCategory
    offer_type: OfferType
    condition: MaterialCondition
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1)
    price: float | None = Field(default=None, ge=0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    media_urls: list[str] | None = Field(default_factory=list)


class MaterialResponse(BaseModel):
    id: str
    title: str
    description: str
    category: MaterialCategory
    offer_type: OfferType
    condition: MaterialCondition
    quantity: float
    unit: str
    price: float | None
    longitude: float
    latitude: float
    owner_id: str
    media_urls: list[str]
    is_active: bool
    created_at: datetime
