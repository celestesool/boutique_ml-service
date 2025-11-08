"""
Pydantic schemas for classification endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class PredictionLabel(BaseModel):
    """Single prediction label with confidence"""
    label: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class ClassificationRequest(BaseModel):
    """Request for image classification"""
    product_id: str = Field(..., description="UUID of the product")
    image_base64: Optional[str] = Field(None, description="Base64 encoded image")
    image_url: Optional[str] = Field(None, description="URL of the image")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": "123e4567-e89b-12d3-a456-426614174000",
                "image_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
            }
        }
    }


class ClassificationPredictions(BaseModel):
    """Predictions from classification model"""
    tipo_prenda: PredictionLabel
    tipo_cuello: Optional[PredictionLabel] = None
    tipo_manga: Optional[PredictionLabel] = None
    patron: Optional[PredictionLabel] = None
    color_principal: PredictionLabel
    estilo: PredictionLabel


class ClassificationResponse(BaseModel):
    """Response from classification endpoint"""
    success: bool
    product_id: str
    predictions: ClassificationPredictions
    embedding_vector: Optional[List[float]] = None
    processing_time_ms: int
    model_version: str = "v1.0.0"
    
    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "success": True,
                "product_id": "123e4567-e89b-12d3-a456-426614174000",
                "predictions": {
                    "tipo_prenda": {"label": "camisa", "confidence": 0.94},
                    "color_principal": {"label": "azul", "confidence": 0.88},
                    "estilo": {"label": "casual", "confidence": 0.79}
                },
                "processing_time_ms": 234,
                "model_version": "v1.0.0"
            }
        }
    }


class ProductLabelsResponse(BaseModel):
    """Response for product labels"""
    product_id: str
    labels: Dict[str, str]
    confidence_avg: float
    last_updated: datetime
    approved: bool
