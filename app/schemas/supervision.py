"""
Pydantic schemas for supervision endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class PendingReview(BaseModel):
    """Image pending manual review"""
    image_id: str
    product_id: str
    image_url: Optional[str] = None
    predicted_labels: Dict[str, Dict[str, float]]  # {label_type: {label: confidence}}
    confidence_avg: float
    classified_at: datetime
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "image_id": "507f1f77bcf86cd799439011",
                "product_id": "123e4567-e89b-12d3-a456-426614174000",
                "predicted_labels": {
                    "tipo_prenda": {"label": "camisa", "confidence": 0.94},
                    "color_principal": {"label": "azul", "confidence": 0.88}
                },
                "confidence_avg": 0.82,
                "classified_at": "2025-11-08T10:00:00Z"
            }
        }
    }


class ApproveRequest(BaseModel):
    """Request to approve predictions"""
    image_id: str
    reviewed_by: str = Field(..., description="ID del usuario/admin que revisa")
    notes: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "image_id": "507f1f77bcf86cd799439011",
                "reviewed_by": "admin_001",
                "notes": "Etiquetas correctas"
            }
        }
    }


class RejectRequest(BaseModel):
    """Request to reject and correct predictions"""
    image_id: str
    reviewed_by: str
    corrected_labels: Dict[str, str]  # {label_type: corrected_value}
    notes: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "image_id": "507f1f77bcf86cd799439011",
                "reviewed_by": "admin_001",
                "corrected_labels": {
                    "tipo_prenda": "camisa",
                    "color_principal": "azul marino",
                    "estilo": "formal"
                },
                "notes": "Color corregido de azul a azul marino"
            }
        }
    }


class SupervisionResponse(BaseModel):
    """Response from supervision action"""
    success: bool
    message: str
    image_id: str
    status: str  # "approved", "rejected", "pending"
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Prediction approved successfully",
                "image_id": "507f1f77bcf86cd799439011",
                "status": "approved"
            }
        }
    }


class ReviewHistoryItem(BaseModel):
    """Single review history item"""
    image_id: str
    product_id: str
    status: str
    reviewed_by: str
    reviewed_at: datetime
    confidence_avg: float
    corrections_made: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "image_id": "507f1f77bcf86cd799439011",
                "product_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "approved",
                "reviewed_by": "admin_001",
                "reviewed_at": "2025-11-08T10:30:00Z",
                "confidence_avg": 0.87,
                "corrections_made": 0
            }
        }
    }


class SupervisionMetrics(BaseModel):
    """Supervision system metrics"""
    total_pending: int
    total_approved: int
    total_rejected: int
    avg_confidence_approved: float
    avg_confidence_rejected: float
    total_corrections: int
    approval_rate: float
    ready_for_retraining: bool
    images_for_retraining: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_pending": 45,
                "total_approved": 320,
                "total_rejected": 28,
                "avg_confidence_approved": 0.89,
                "avg_confidence_rejected": 0.64,
                "total_corrections": 35,
                "approval_rate": 0.92,
                "ready_for_retraining": True,
                "images_for_retraining": 500
            }
        }
    }


class RetrainingTriggerRequest(BaseModel):
    """Request to trigger retraining"""
    triggered_by: str
    min_images: int = Field(100, description="Minimum approved images required")
    reason: str = "manual"
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "triggered_by": "admin_001",
                "min_images": 500,
                "reason": "Accumulated 500 approved images"
            }
        }
    }
