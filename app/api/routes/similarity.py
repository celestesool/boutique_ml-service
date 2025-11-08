"""
Similarity search endpoints
"""

from fastapi import APIRouter, HTTPException, Header
from app.schemas.similarity import SimilarityRequest, SimilarityResponse, SimilarProduct
from app.config import settings
from app.utils.logger import logger
import time

router = APIRouter()


@router.post("/similar-products", response_model=SimilarityResponse)
async def find_similar_products(
    request: SimilarityRequest,
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Find similar products based on product ID or image
    
    - **product_id**: Product ID to find similar products (optional)
    - **image_base64**: Base64 image to find similar products (optional)
    - **limit**: Maximum number of similar products to return
    - **min_similarity**: Minimum similarity score threshold
    """
    
    # Verify API key
    if api_key != settings.ML_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    start_time = time.time()
    
    try:
        # Validate input
        if not request.product_id and not request.image_base64:
            raise HTTPException(
                status_code=400,
                detail="Either product_id or image_base64 must be provided"
            )
        
        logger.info(f"Finding similar products for: {request.product_id or 'uploaded image'}")
        
        # TODO: Implement actual similarity search using FAISS
        # For now, return mock data
        
        mock_similar_products = [
            SimilarProduct(
                product_id="987e6543-e21b-12d3-a456-426614174999",
                similarity_score=0.92,
                matched_attributes=["color", "tipo_prenda", "patron"]
            ),
            SimilarProduct(
                product_id="456e7890-e21b-12d3-a456-426614175000",
                similarity_score=0.87,
                matched_attributes=["tipo_prenda", "estilo"]
            ),
            SimilarProduct(
                product_id="789e0123-e21b-12d3-a456-426614175001",
                similarity_score=0.82,
                matched_attributes=["color", "estilo"]
            )
        ]
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return SimilarityResponse(
            success=True,
            query_product_id=request.product_id,
            similar_products=mock_similar_products[:request.limit],
            total_found=len(mock_similar_products),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error finding similar products: {e}")
        raise HTTPException(status_code=500, detail=str(e))
