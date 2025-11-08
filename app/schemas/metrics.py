"""
Schemas Pydantic para métricas y reportes del modelo ML.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional
from datetime import datetime


class ModelMetrics(BaseModel):
    """Métricas del modelo de clasificación."""
    accuracy: float = Field(..., description="Precisión general del modelo (0-1)")
    precision: float = Field(..., description="Precision promedio")
    recall: float = Field(..., description="Recall promedio")
    f1_score: float = Field(..., description="F1-Score promedio")
    total_predictions: int = Field(..., description="Total de predicciones realizadas")
    average_inference_time: float = Field(..., description="Tiempo promedio de inferencia (ms)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "accuracy": 0.92,
                "precision": 0.89,
                "recall": 0.91,
                "f1_score": 0.90,
                "total_predictions": 1500,
                "average_inference_time": 45.5
            }
        }
    }


class ClassMetrics(BaseModel):
    """Métricas por clase."""
    class_name: str = Field(..., description="Nombre de la clase")
    class_id: int = Field(..., description="ID de la clase")
    precision: float = Field(..., description="Precision para esta clase")
    recall: float = Field(..., description="Recall para esta clase")
    f1_score: float = Field(..., description="F1-Score para esta clase")
    support: int = Field(..., description="Número de muestras en el dataset")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "class_name": "T-shirt",
                "class_id": 0,
                "precision": 0.95,
                "recall": 0.92,
                "f1_score": 0.93,
                "support": 1000
            }
        }
    }


class ConfusionMatrixData(BaseModel):
    """Datos de la matriz de confusión."""
    matrix: List[List[int]] = Field(..., description="Matriz de confusión NxN")
    class_labels: List[str] = Field(..., description="Etiquetas de las clases")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "matrix": [[950, 30, 20], [15, 980, 5], [10, 10, 980]],
                "class_labels": ["T-shirt", "Trouser", "Pullover"]
            }
        }
    }


class ModelReport(BaseModel):
    """Reporte completo del modelo."""
    model_name: str = Field(..., description="Nombre del modelo")
    model_version: str = Field(..., description="Versión del modelo")
    training_date: Optional[datetime] = Field(None, description="Fecha de entrenamiento")
    overall_metrics: ModelMetrics = Field(..., description="Métricas generales")
    per_class_metrics: List[ClassMetrics] = Field(..., description="Métricas por clase")
    confusion_matrix: ConfusionMatrixData = Field(..., description="Matriz de confusión")
    
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "model_name": "EfficientNetB0 Classifier",
                "model_version": "v1.0",
                "training_date": "2025-11-08T14:00:00",
                "overall_metrics": {
                    "accuracy": 0.92,
                    "precision": 0.89,
                    "recall": 0.91,
                    "f1_score": 0.90,
                    "total_predictions": 1500,
                    "average_inference_time": 45.5
                },
                "per_class_metrics": [],
                "confusion_matrix": {
                    "matrix": [],
                    "class_labels": []
                }
            }
        }
    )


class TrainingHistory(BaseModel):
    """Historial de entrenamiento."""
    epochs: List[int] = Field(..., description="Números de epoch")
    train_accuracy: List[float] = Field(..., description="Accuracy en entrenamiento")
    val_accuracy: List[float] = Field(..., description="Accuracy en validación")
    train_loss: List[float] = Field(..., description="Loss en entrenamiento")
    val_loss: List[float] = Field(..., description="Loss en validación")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "epochs": [1, 2, 3, 4, 5],
                "train_accuracy": [0.7, 0.8, 0.85, 0.88, 0.9],
                "val_accuracy": [0.68, 0.78, 0.83, 0.86, 0.88],
                "train_loss": [0.8, 0.6, 0.5, 0.4, 0.35],
                "val_loss": [0.85, 0.65, 0.55, 0.45, 0.4]
            }
        }
    }


class InferenceStats(BaseModel):
    """Estadísticas de inferencia en tiempo real."""
    total_inferences: int = Field(..., description="Total de inferencias realizadas")
    average_time_ms: float = Field(..., description="Tiempo promedio en milisegundos")
    min_time_ms: float = Field(..., description="Tiempo mínimo")
    max_time_ms: float = Field(..., description="Tiempo máximo")
    inferences_per_second: float = Field(..., description="Throughput (inferencias/segundo)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_inferences": 5000,
                "average_time_ms": 45.5,
                "min_time_ms": 30.2,
                "max_time_ms": 120.5,
                "inferences_per_second": 22.0
            }
        }
    }
