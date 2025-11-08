"""
Endpoints para Métricas y Reportes del Modelo ML.
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List

from app.schemas.metrics import (
    ModelMetrics,
    ClassMetrics,
    ConfusionMatrixData,
    ModelReport,
    TrainingHistory,
    InferenceStats
)
from app.services.metrics_service import metrics_service
from app.config import settings
from app.utils.logger import logger

router = APIRouter()


async def verify_api_key(x_api_key: str = Header(...)):
    """Verifica la API key en el header."""
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="API Key inválida")
    return x_api_key


@router.get("/metrics/overall", response_model=ModelMetrics)
async def get_overall_metrics(api_key: str = Depends(verify_api_key)):
    """
    Obtiene métricas generales del modelo.
    
    **Métricas incluidas:**
    - Accuracy: Precisión general
    - Precision: Promedio de precision por clase
    - Recall: Promedio de recall por clase
    - F1-Score: Promedio de F1 por clase
    - Total de predicciones realizadas
    - Tiempo promedio de inferencia
    
    **Uso:** Dashboard principal, monitoreo de performance.
    """
    try:
        logger.info("Obteniendo métricas generales del modelo")
        
        metrics = metrics_service.get_overall_metrics()
        
        return ModelMetrics(**metrics)
        
    except Exception as e:
        logger.error(f"Error al obtener métricas: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener métricas: {str(e)}"
        )


@router.get("/metrics/per-class", response_model=List[ClassMetrics])
async def get_per_class_metrics(api_key: str = Depends(verify_api_key)):
    """
    Obtiene métricas detalladas por clase.
    
    **Para cada clase retorna:**
    - Precision: Qué tan preciso es para esa clase
    - Recall: Qué tan completo es (detecta todos los casos)
    - F1-Score: Balance entre precision y recall
    - Support: Cuántas muestras hay de esa clase
    
    **Uso:** Identificar clases problemáticas, balance del dataset.
    """
    try:
        logger.info("Obteniendo métricas por clase")
        
        per_class = metrics_service.calculate_per_class_metrics()
        
        return [ClassMetrics(**m) for m in per_class]
        
    except Exception as e:
        logger.error(f"Error al obtener métricas por clase: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener métricas por clase: {str(e)}"
        )


@router.get("/metrics/confusion-matrix", response_model=ConfusionMatrixData)
async def get_confusion_matrix(api_key: str = Depends(verify_api_key)):
    """
    Obtiene la matriz de confusión del modelo.
    
    **Matriz de Confusión:**
    - Muestra qué clases se confunden entre sí
    - Diagonal = predicciones correctas
    - Fuera de diagonal = errores
    
    **Uso:** Visualizar errores del modelo, identificar pares de clases problemáticos.
    """
    try:
        logger.info("Obteniendo matriz de confusión")
        
        matrix = metrics_service.get_confusion_matrix(num_classes=10)
        
        class_labels = [
            "T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
            "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"
        ]
        
        return ConfusionMatrixData(
            matrix=matrix.tolist(),
            class_labels=class_labels
        )
        
    except Exception as e:
        logger.error(f"Error al obtener matriz de confusión: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener matriz de confusión: {str(e)}"
        )


@router.get("/metrics/inference-stats", response_model=InferenceStats)
async def get_inference_stats(api_key: str = Depends(verify_api_key)):
    """
    Obtiene estadísticas de rendimiento de inferencia.
    
    **Estadísticas:**
    - Total de inferencias realizadas
    - Tiempo promedio, mínimo, máximo
    - Throughput (inferencias por segundo)
    
    **Uso:** Monitoreo de performance, optimización, SLA.
    """
    try:
        logger.info("Obteniendo estadísticas de inferencia")
        
        stats = metrics_service.get_inference_stats()
        
        return InferenceStats(**stats)
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.get("/metrics/training-history", response_model=TrainingHistory)
async def get_training_history(api_key: str = Depends(verify_api_key)):
    """
    Obtiene historial de entrenamiento del modelo.
    
    **Datos incluidos:**
    - Accuracy por epoch (train y validation)
    - Loss por epoch (train y validation)
    - Detecta overfitting (si val_loss sube mientras train_loss baja)
    
    **Uso:** Visualizar curvas de aprendizaje, diagnosticar problemas de entrenamiento.
    """
    try:
        logger.info("Obteniendo historial de entrenamiento")
        
        history = metrics_service.get_training_history()
        
        if not history:
            raise HTTPException(
                status_code=404,
                detail="No hay historial de entrenamiento disponible"
            )
        
        return TrainingHistory(**history)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener historial: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener historial: {str(e)}"
        )


@router.get("/metrics/report", response_model=ModelReport)
async def get_model_report(api_key: str = Depends(verify_api_key)):
    """
    Genera reporte completo del modelo.
    
    **Reporte incluye:**
    - Información del modelo (nombre, versión, fecha)
    - Métricas generales
    - Métricas por clase
    - Matriz de confusión
    
    **Uso:** Reporte ejecutivo, documentación, auditoría.
    """
    try:
        logger.info("Generando reporte completo del modelo")
        
        overall = metrics_service.get_overall_metrics()
        per_class = metrics_service.calculate_per_class_metrics()
        matrix = metrics_service.get_confusion_matrix(num_classes=10)
        
        class_labels = [
            "T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
            "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"
        ]
        
        report = ModelReport(
            model_name="EfficientNetB0 Fashion Classifier",
            model_version="v1.0",
            training_date=None,  # TODO: Cargar desde metadata del modelo
            overall_metrics=ModelMetrics(**overall),
            per_class_metrics=[ClassMetrics(**m) for m in per_class],
            confusion_matrix=ConfusionMatrixData(
                matrix=matrix.tolist(),
                class_labels=class_labels
            )
        )
        
        logger.info("✅ Reporte generado exitosamente")
        
        return report
        
    except Exception as e:
        logger.error(f"Error al generar reporte: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar reporte: {str(e)}"
        )


@router.get("/metrics/class-distribution")
async def get_class_distribution(api_key: str = Depends(verify_api_key)):
    """
    Obtiene distribución de predicciones por clase.
    
    **Retorna:** Diccionario con conteo de predicciones por clase.
    
    **Uso:** Detectar desbalance, analizar patrones de uso.
    """
    try:
        logger.info("Obteniendo distribución de clases")
        
        distribution = metrics_service.get_class_distribution()
        
        return {
            "success": True,
            "distribution": distribution,
            "total_predictions": sum(distribution.values())
        }
        
    except Exception as e:
        logger.error(f"Error al obtener distribución: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener distribución: {str(e)}"
        )
