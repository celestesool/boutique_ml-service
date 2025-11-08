"""
Pydantic schemas for similarity endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class SimilarityRequest(BaseModel):
    """Request for similar products"""
    product_id: Optional[str] = Field(None, description="Product ID to find similar products")
    image_base64: Optional[str] = Field(None, description="Base64 image to find similar products")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of similar products")
    min_similarity: float = Field(0.70, ge=0.0, le=1.0, description="Minimum similarity score")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": "123e4567-e89b-12d3-a456-426614174000",
                "limit": 10,
                "min_similarity": 0.75
            }
        }
    }


class SimilarProduct(BaseModel):
    """Single similar product"""
    product_id: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    matched_attributes: List[str] = []
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": "987e6543-e21b-12d3-a456-426614174999",
                "similarity_score": 0.92,
                "matched_attributes": ["color", "tipo_prenda", "patron"]
            }
        }
    }


class SimilarityResponse(BaseModel):
    """Response from similarity endpoint"""
    success: bool
    query_product_id: Optional[str] = None
    similar_products: List[SimilarProduct]
    total_found: int
    processing_time_ms: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "query_product_id": "123e4567-e89b-12d3-a456-426614174000",
                "similar_products": [
                    {
                        "product_id": "987e6543-e21b-12d3-a456-426614174999",
                        "similarity_score": 0.92,
                        "matched_attributes": ["color", "tipo_prenda"]
                    }
                ],
                "total_found": 10,
                "processing_time_ms": 145
            }
        }
    }
