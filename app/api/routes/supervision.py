"""
Supervision endpoints for manual validation
"""

from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional
from app.schemas.supervision import (
    PendingReview,
    ApproveRequest,
    RejectRequest,
    SupervisionResponse,
    ReviewHistoryItem,
    SupervisionMetrics,
    RetrainingTriggerRequest
)
from app.services.supervision_service import supervision_service
from app.config import settings
from app.utils.logger import logger

router = APIRouter()


@router.get("/supervision/pending", response_model=list[PendingReview])
async def get_pending_reviews(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    max_confidence: float = Query(1.0, ge=0.0, le=1.0, description="Maximum confidence threshold"),
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Get images pending manual review
    
    Returns images that have been classified but not yet reviewed by a human.
    Can filter by confidence level to prioritize low-confidence predictions.
    """
    
    # Verify API key
    if api_key != settings.ML_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    try:
        pending = await supervision_service.get_pending_reviews(limit, min_confidence, max_confidence)
        return pending
        
    except Exception as e:
        logger.error(f"Error getting pending reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/supervision/approve", response_model=SupervisionResponse)
async def approve_prediction(
    request: ApproveRequest,
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Approve ML prediction
    
    Marks the prediction as approved and ready for use in retraining.
    """
    
    # Verify API key
    if api_key != settings.ML_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    try:
        result = await supervision_service.approve_prediction(
            request.image_id,
            request.reviewed_by,
            request.notes
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error approving prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/supervision/reject", response_model=SupervisionResponse)
async def reject_and_correct(
    request: RejectRequest,
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Reject prediction and provide corrections
    
    Marks the prediction as incorrect and saves the corrected labels
    for future model improvement.
    """
    
    # Verify API key
    if api_key != settings.ML_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    try:
        result = await supervision_service.reject_and_correct(
            request.image_id,
            request.reviewed_by,
            request.corrected_labels,
            request.notes
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error rejecting prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supervision/history", response_model=list[ReviewHistoryItem])
async def get_review_history(
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = Query(None, description="Filter by status: approved, rejected"),
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Get review history
    
    Returns the history of all manual reviews performed.
    """
    
    # Verify API key
    if api_key != settings.ML_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    try:
        history = await supervision_service.get_review_history(limit, status)
        return history
        
    except Exception as e:
        logger.error(f"Error getting review history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supervision/metrics", response_model=SupervisionMetrics)
async def get_supervision_metrics(
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Get supervision system metrics
    
    Returns statistics about the supervision process including:
    - Total pending, approved, and rejected reviews
    - Average confidence scores
    - Approval rate
    - Readiness for retraining
    """
    
    # Verify API key
    if api_key != settings.ML_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    try:
        metrics = await supervision_service.get_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting supervision metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/supervision/trigger-retraining")
async def trigger_retraining(
    request: RetrainingTriggerRequest,
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Trigger model retraining with approved images
    
    Initiates a new training job using all approved and corrected images.
    """
    
    # Verify API key
    if api_key != settings.ML_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    try:
        # Get approved images
        approved_images = await supervision_service.get_approved_for_training(request.min_images)
        
        if len(approved_images) < request.min_images:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough approved images. Found {len(approved_images)}, need {request.min_images}"
            )
        
        # TODO: Implement actual retraining logic
        # For now, just mark as used and return success
        
        logger.info(f"Retraining triggered by {request.triggered_by} with {len(approved_images)} images")
        
        return {
            "success": True,
            "message": f"Retraining initiated with {len(approved_images)} images",
            "triggered_by": request.triggered_by,
            "images_count": len(approved_images),
            "status": "queued"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering retraining: {e}")
        raise HTTPException(status_code=500, detail=str(e))
