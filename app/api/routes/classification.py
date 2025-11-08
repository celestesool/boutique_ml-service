"""
Classification endpoints
"""

from fastapi import APIRouter, HTTPException, Header
from app.schemas.classification import ClassificationRequest, ClassificationResponse
from app.config import settings
from app.utils.logger import logger
import time

router = APIRouter()


def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from header"""
    if x_api_key != settings.ML_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key


@router.post("/classify-image", response_model=ClassificationResponse)
async def classify_image(
    request: ClassificationRequest,
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Classify product image and return ML labels
    
    - **product_id**: UUID of the product
    - **image_base64**: Base64 encoded image (required if image_url not provided)
    - **image_url**: URL of the image (alternative to image_base64)
    """
    
    # Verify API key
    if api_key != settings.ML_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    start_time = time.time()
    
    try:
        # Validate input
        if not request.image_base64 and not request.image_url:
            raise HTTPException(
                status_code=400,
                detail="Either image_base64 or image_url must be provided"
            )
        
        logger.info(f"Classifying image for product: {request.product_id}")
        
        # TODO: Implement actual classification logic
        # For now, return mock data
        
        from app.schemas.classification import PredictionLabel, ClassificationPredictions
        
        mock_predictions = ClassificationPredictions(
            tipo_prenda=PredictionLabel(label="camisa", confidence=0.94),
            color_principal=PredictionLabel(label="azul", confidence=0.88),
            estilo=PredictionLabel(label="casual", confidence=0.79),
            patron=PredictionLabel(label="liso", confidence=0.91),
            tipo_cuello=PredictionLabel(label="cuello_v", confidence=0.85),
            tipo_manga=PredictionLabel(label="manga_larga", confidence=0.87)
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return ClassificationResponse(
            success=True,
            product_id=request.product_id,
            predictions=mock_predictions,
            processing_time_ms=processing_time,
            model_version="v1.0.0"
        )
        
    except Exception as e:
        logger.error(f"Error classifying image: {e}")
        raise HTTPException(status_code=500, detail=str(e))
