"""
Pydantic schemas for training endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime


class TrainingRequest(BaseModel):
    """Request to start training"""
    dataset_version: str = Field(..., description="Version identifier for the dataset")
    images_count: int = Field(..., ge=1)
    labels_updated: list[str] = Field(..., description="List of label types to update")
    trigger: str = Field("manual", description="Training trigger: manual or scheduled")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "dataset_version": "v2",
                "images_count": 500,
                "labels_updated": ["tipo_prenda", "color"],
                "trigger": "manual"
            }
        }
    }


class TrainingResponse(BaseModel):
    """Response from training start"""
    success: bool
    training_job_id: str
    status: str
    estimated_time_minutes: int
    started_at: datetime
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "training_job_id": "job-123-abc",
                "status": "in_progress",
                "estimated_time_minutes": 45,
                "started_at": "2025-11-08T10:00:00Z"
            }
        }
    }


class TrainingStatusResponse(BaseModel):
    """Response for training status"""
    job_id: str
    status: str
    metrics: Optional[Dict[str, float]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": "job-123-abc",
                "status": "completed",
                "metrics": {
                    "accuracy": 0.94,
                    "loss": 0.12,
                    "epochs_completed": 50
                },
                "started_at": "2025-11-08T10:00:00Z",
                "completed_at": "2025-11-08T10:45:00Z"
            }
        }
    }
