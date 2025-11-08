"""
Endpoints para Sistema de Recomendaciones (ML No Supervisado)
Basado en Similitud Coseno + Co-ocurrencia
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List

from app.schemas.recommendations import (
    ProductInteraction,
    RecommendationRequest,
    RecommendedProduct,
    RecommendationResponse,
    CoOccurrenceStats,
    InteractionResponse
)
from app.services.recommendation_service import recommendation_service
from app.config import settings
from app.utils.logger import logger

router = APIRouter()


async def verify_api_key(x_api_key: str = Header(...)):
    """Verifica la API key en el header."""
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="API Key inválida")
    return x_api_key


@router.post("/recommendations/interaction", response_model=InteractionResponse)
async def register_interaction(
    interaction: ProductInteraction,
    api_key: str = Depends(verify_api_key)
):
    """
    Registra una interacción usuario-producto.
    
    **ML No Supervisado**: Construye matriz de co-ocurrencia automáticamente.
    
    - **user_id**: ID del usuario
    - **product_id**: ID del producto
    - **interaction_type**: 'view', 'purchase', 'like'
    
    Esta data se usa para identificar productos que se ven/compran juntos.
    """
    try:
        logger.info(
            f"Registrando interacción: user={interaction.user_id}, "
            f"product={interaction.product_id}, type={interaction.interaction_type}"
        )
        
        interaction_count = recommendation_service.register_interaction(
            user_id=interaction.user_id,
            product_id=interaction.product_id,
            interaction_type=interaction.interaction_type
        )
        
        return InteractionResponse(
            success=True,
            message="Interacción registrada exitosamente",
            interaction_count=interaction_count
        )
        
    except Exception as e:
        logger.error(f"Error al registrar interacción: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar interacción: {str(e)}"
        )


@router.post("/recommendations/get", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Obtiene recomendaciones de productos usando ML No Supervisado.
    
    **Estrategias disponibles:**
    - **visual**: Similitud coseno de embeddings (productos visualmente similares)
    - **collaborative**: Co-ocurrencia (productos vistos/comprados juntos)
    - **hybrid**: Combinación de ambas estrategias
    
    **Ejemplo de uso:**
    - Dado product_id: "Encuentra productos similares"
    - Dado user_id: "Recomendaciones personalizadas basadas en historial"
    """
    try:
        logger.info(
            f"Generando recomendaciones: product={request.product_id}, "
            f"user={request.user_id}, strategy={request.strategy}"
        )
        
        # Obtener recomendaciones
        recommendations = recommendation_service.get_recommendations(
            product_id=request.product_id,
            user_id=request.user_id,
            n=request.n_recommendations,
            strategy=request.strategy
        )
        
        # Convertir a schema
        recommended_products = [
            RecommendedProduct(
                product_id=prod_id,
                score=score,
                reason=reason
            )
            for prod_id, score, reason in recommendations
        ]
        
        logger.info(f"✅ Generadas {len(recommended_products)} recomendaciones")
        
        return RecommendationResponse(
            success=True,
            recommendations=recommended_products,
            strategy_used=request.strategy,
            count=len(recommended_products)
        )
        
    except Exception as e:
        logger.error(f"Error al generar recomendaciones: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar recomendaciones: {str(e)}"
        )


@router.get("/recommendations/stats", response_model=CoOccurrenceStats)
async def get_recommendation_stats(api_key: str = Depends(verify_api_key)):
    """
    Obtiene estadísticas del sistema de recomendaciones.
    
    **Retorna:**
    - Total de interacciones registradas
    - Usuarios y productos únicos
    - Pares de productos más co-ocurrentes
    
    **Uso:** Validar que el sistema de recomendaciones está aprendiendo patrones.
    """
    try:
        logger.info("Obteniendo estadísticas de recomendaciones")
        
        stats = recommendation_service.get_stats()
        
        return CoOccurrenceStats(
            total_interactions=stats["total_interactions"],
            unique_users=stats["unique_users"],
            unique_products=stats["unique_products"],
            top_pairs=stats["top_pairs"]
        )
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.post("/recommendations/batch-interactions")
async def register_batch_interactions(
    interactions: List[ProductInteraction],
    api_key: str = Depends(verify_api_key)
):
    """
    Registra múltiples interacciones en batch (útil para importar datos históricos).
    
    **Uso:** Cargar interacciones históricas para entrenar el sistema de recomendaciones.
    """
    try:
        logger.info(f"Registrando {len(interactions)} interacciones en batch")
        
        for interaction in interactions:
            recommendation_service.register_interaction(
                user_id=interaction.user_id,
                product_id=interaction.product_id,
                interaction_type=interaction.interaction_type
            )
        
        logger.info(f"✅ Registradas {len(interactions)} interacciones")
        
        return {
            "success": True,
            "message": f"Registradas {len(interactions)} interacciones exitosamente",
            "total_interactions": len(interactions)
        }
        
    except Exception as e:
        logger.error(f"Error al registrar batch: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar batch: {str(e)}"
        )
