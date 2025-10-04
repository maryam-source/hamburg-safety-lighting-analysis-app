# backend/models/lighting.py
from pydantic import BaseModel, Field
from typing import Dict, Any

class PolygonInput(BaseModel):
    """
    Model for receiving polygon input in GeoJSON format.
    """
    geojson: Dict[str, Any] = Field(
        ...,
        description="Polygon or MultiPolygon in valid GeoJSON format"
    )
