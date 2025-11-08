"""
Schemas Pydantic para sistema de recomendaciones (ML No Supervisado).
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ProductInteraction(BaseModel):
    """Interacción de usuario con producto."""
    user_id: str = Field(..., description="ID del usuario")
    product_id: str = Field(..., description="ID del producto")
    interaction_type: str = Field(..., description="Tipo: 'view', 'purchase', 'like'")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "user_123",
                "product_id": "prod_456",
                "interaction_type": "view"
            }
        }
    }


class RecommendationRequest(BaseModel):
    """Request para obtener recomendaciones."""
    product_id: Optional[str] = Field(None, description="ID del producto base")
    user_id: Optional[str] = Field(None, description="ID del usuario")
    n_recommendations: int = Field(5, description="Número de recomendaciones", ge=1, le=50)
    strategy: str = Field("hybrid", description="Estrategia: 'visual', 'collaborative', 'hybrid'")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": "prod_123",
                "user_id": "user_456",
                "n_recommendations": 10,
                "strategy": "hybrid"
            }
        }
    }


class RecommendedProduct(BaseModel):
    """Producto recomendado."""
    product_id: str = Field(..., description="ID del producto")
    score: float = Field(..., description="Score de recomendación (0-1)")
    reason: str = Field(..., description="Razón de la recomendación")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": "prod_789",
                "score": 0.92,
                "reason": "Visualmente similar + Comprado frecuentemente junto"
            }
        }
    }


class RecommendationResponse(BaseModel):
    """Response con recomendaciones."""
    success: bool = Field(..., description="Si la operación fue exitosa")
    recommendations: List[RecommendedProduct] = Field(..., description="Lista de productos recomendados")
    strategy_used: str = Field(..., description="Estrategia utilizada")
    count: int = Field(..., description="Número de recomendaciones")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "recommendations": [
                    {
                        "product_id": "prod_789",
                        "score": 0.92,
                        "reason": "Visualmente similar"
                    }
                ],
                "strategy_used": "hybrid",
                "count": 5
            }
        }
    }


class CoOccurrenceStats(BaseModel):
    """Estadísticas de co-ocurrencia."""
    total_interactions: int = Field(..., description="Total de interacciones registradas")
    unique_users: int = Field(..., description="Usuarios únicos")
    unique_products: int = Field(..., description="Productos únicos")
    top_pairs: List[dict] = Field(..., description="Pares de productos más co-ocurrentes")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_interactions": 1500,
                "unique_users": 250,
                "unique_products": 100,
                "top_pairs": [
                    {
                        "product_a": "prod_1",
                        "product_b": "prod_2",
                        "count": 45
                    }
                ]
            }
        }
    }


class InteractionResponse(BaseModel):
    """Response al registrar interacción."""
    success: bool = Field(..., description="Si se registró correctamente")
    message: str = Field(..., description="Mensaje de confirmación")
    interaction_count: int = Field(..., description="Total de interacciones del usuario")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Interacción registrada exitosamente",
                "interaction_count": 15
            }
        }
    }
