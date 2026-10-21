from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ..domain.layer import LayerCategory


class CreateLayerRequest(BaseModel):
    name: str = Field(..., min_length=3)
    category: LayerCategory
    geojson_data: dict[str, Any] = Field(..., description="GeoJSON FeatureCollection")


class MapLayerResponse(BaseModel):
    id: str
    name: str
    category: LayerCategory
    geojson_data: dict[str, Any]
    is_active: bool
    created_at: datetime
