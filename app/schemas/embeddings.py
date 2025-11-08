"""
Schemas Pydantic para endpoints de embeddings.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class EmbeddingRequest(BaseModel):
    """Request para extraer embedding de una imagen."""
    image_id: Optional[str] = Field(None, description="ID opcional de la imagen para referencia")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "image_id": "product_12345"
            }
        }
    }


class EmbeddingResponse(BaseModel):
    """Response con el embedding extraído."""
    success: bool = Field(..., description="Si la extracción fue exitosa")
    embedding: List[float] = Field(..., description="Vector de características (1280 dimensiones)")
    embedding_size: int = Field(..., description="Tamaño del embedding")
    image_id: Optional[str] = Field(None, description="ID de la imagen si se proporcionó")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "embedding": [0.123, -0.456, 0.789, "..."],
                "embedding_size": 1280,
                "image_id": "product_12345"
            }
        }
    }


class SimilarityRequest(BaseModel):
    """Request para calcular similitud entre dos imágenes."""
    image_id_1: Optional[str] = Field(None, description="ID de la primera imagen")
    image_id_2: Optional[str] = Field(None, description="ID de la segunda imagen")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "image_id_1": "product_001",
                "image_id_2": "product_002"
            }
        }
    }


class SimilarityResponse(BaseModel):
    """Response con la similitud calculada."""
    success: bool = Field(..., description="Si el cálculo fue exitoso")
    similarity: float = Field(..., description="Similitud coseno (0-1)")
    image_id_1: Optional[str] = None
    image_id_2: Optional[str] = None
    interpretation: str = Field(..., description="Interpretación de la similitud")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "similarity": 0.87,
                "image_id_1": "product_001",
                "image_id_2": "product_002",
                "interpretation": "Muy similar"
            }
        }
    }


class BatchEmbeddingResponse(BaseModel):
    """Response para extracción de múltiples embeddings."""
    success: bool = Field(..., description="Si la extracción fue exitosa")
    embeddings: List[List[float]] = Field(..., description="Lista de embeddings")
    count: int = Field(..., description="Número de embeddings extraídos")
    embedding_size: int = Field(..., description="Tamaño de cada embedding")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "embeddings": [[0.1, 0.2, "..."], [0.3, 0.4, "..."]],
                "count": 2,
                "embedding_size": 1280
            }
        }
    }


class FindSimilarRequest(BaseModel):
    """Request para buscar imágenes similares."""
    top_k: int = Field(10, description="Número de resultados similares", ge=1, le=100)
    threshold: float = Field(0.5, description="Umbral mínimo de similitud", ge=0, le=1)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "top_k": 10,
                "threshold": 0.7
            }
        }
    }


class SimilarImageResult(BaseModel):
    """Resultado de una imagen similar."""
    image_id: str = Field(..., description="ID de la imagen similar")
    similarity: float = Field(..., description="Similitud con la imagen de consulta")
    product_id: Optional[str] = Field(None, description="ID del producto asociado")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "image_id": "img_98765",
                "similarity": 0.92,
                "product_id": "prod_456"
            }
        }
    }


class FindSimilarResponse(BaseModel):
    """Response con imágenes similares encontradas."""
    success: bool = Field(..., description="Si la búsqueda fue exitosa")
    query_image_id: Optional[str] = None
    similar_images: List[SimilarImageResult] = Field(..., description="Lista de imágenes similares")
    count: int = Field(..., description="Número de imágenes encontradas")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "query_image_id": "img_12345",
                "similar_images": [
                    {"image_id": "img_98765", "similarity": 0.92, "product_id": "prod_456"},
                    {"image_id": "img_11111", "similarity": 0.88, "product_id": "prod_789"}
                ],
                "count": 2
            }
        }
    }
