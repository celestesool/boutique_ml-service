"""
Search by image endpoints
"""

from fastapi import APIRouter, HTTPException, Header
from app.schemas.search import SearchByImageRequest, SearchByImageResponse, ProductMatch
from app.config import settings
from app.utils.logger import logger
import time

router = APIRouter()


@router.post("/search-by-image", response_model=SearchByImageResponse)
async def search_by_image(
    request: SearchByImageRequest,
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Search for products using an uploaded image
    
    - **image_base64**: Base64 encoded image to search
    - **limit**: Maximum number of results
    - **filters**: Optional filters (category, price range, etc.)
    """
    
    # Verify API key
    if api_key != settings.ML_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    start_time = time.time()
    
    try:
        logger.info(f"Searching products by image with limit: {request.limit}")
        
        # TODO: Implement actual image search using FAISS embeddings
        # For now, return mock data
        
        mock_matches = [
            ProductMatch(
                product_id="123e4567-e89b-12d3-a456-426614174000",
                similarity_score=0.89,
                product_name="Camisa Azul Casual"
            ),
            ProductMatch(
                product_id="234e5678-e89b-12d3-a456-426614174001",
                similarity_score=0.85,
                product_name="Camisa Navy Formal"
            ),
            ProductMatch(
                product_id="345e6789-e89b-12d3-a456-426614174002",
                similarity_score=0.81,
                product_name="Camisa Celeste Casual"
            )
        ]
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return SearchByImageResponse(
            success=True,
            matches=mock_matches[:request.limit],
            total_matches=len(mock_matches),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error searching by image: {e}")
        raise HTTPException(status_code=500, detail=str(e))
