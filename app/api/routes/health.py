"""
Health check endpoint
"""

from fastapi import APIRouter
from app.database.mongodb import get_database
from app.config import settings
import os

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    Returns the status of the service and its dependencies
    """
    
    # Check MongoDB connection
    try:
        db = get_database()
        await db.command('ping')
        mongodb_status = "connected"
    except Exception:
        mongodb_status = "disconnected"
    
    # Check if FAISS index exists
    faiss_status = "loaded" if os.path.exists(settings.FAISS_INDEX_PATH) else "not_loaded"
    
    # Check if ML model exists
    model_status = "ready" if os.path.exists(settings.MODEL_CLASSIFIER_PATH) else "not_ready"
    
    # Overall status
    overall_status = "healthy" if mongodb_status == "connected" else "degraded"
    
    return {
        "status": overall_status,
        "service": "ML Service - Boutique",
        "version": "1.0.0",
        "dependencies": {
            "mongodb": mongodb_status,
            "faiss_index": faiss_status,
            "ml_model": model_status
        }
    }
