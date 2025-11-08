"""
Pydantic schemas for search endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class SearchByImageRequest(BaseModel):
    """Request for image search"""
    image_base64: str = Field(..., description="Base64 encoded image")
    limit: int = Field(20, ge=1, le=100)
    filters: Optional[Dict[str, Any]] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
                "limit": 20,
                "filters": {
                    "categoria": "camisas",
                    "precio_max": 100
                }
            }
        }
    }


class ProductMatch(BaseModel):
    """Single product match from search"""
    product_id: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    product_name: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": "123e4567-e89b-12d3-a456-426614174000",
                "similarity_score": 0.89,
                "product_name": "Camisa Azul Casual"
            }
        }
    }


class SearchByImageResponse(BaseModel):
    """Response from image search"""
    success: bool
    matches: List[ProductMatch]
    total_matches: int
    processing_time_ms: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "matches": [
                    {
                        "product_id": "123e4567-e89b-12d3-a456-426614174000",
                        "similarity_score": 0.89,
                        "product_name": "Camisa Azul Casual"
                    }
                ],
                "total_matches": 20,
                "processing_time_ms": 312
            }
        }
    }
