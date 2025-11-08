"""
Servicio de Métricas del Modelo ML.
Calcula y almacena métricas de performance del modelo.
"""
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict
import time

from app.utils.logger import logger


class MetricsService:
    """Servicio para calcular y almacenar métricas del modelo."""
    
    def __init__(self):
        """Inicializa el servicio de métricas."""
        # Almacenamiento de predicciones y tiempos
        self.predictions_history: List[Dict] = []
        self.inference_times: List[float] = []
        
        # Contadores por clase
        self.class_counts: Dict[int, int] = defaultdict(int)
        
        # Métricas de validación (cuando tengamos el modelo entrenado)
        self.validation_metrics: Optional[Dict] = None
        
    def record_prediction(
        self,
        predicted_class: int,
        confidence: float,
        inference_time_ms: float,
        true_label: Optional[int] = None
    ):
        """
        Registra una predicción para calcular métricas.
        
        Args:
            predicted_class: Clase predicha
            confidence: Confianza de la predicción
            inference_time_ms: Tiempo de inferencia en milisegundos
            true_label: Etiqueta verdadera (si está disponible)
        """
        try:
            prediction = {
                'predicted_class': predicted_class,
                'confidence': confidence,
                'inference_time_ms': inference_time_ms,
                'true_label': true_label,
                'timestamp': datetime.now()
            }
            
            self.predictions_history.append(prediction)
            self.inference_times.append(inference_time_ms)
            self.class_counts[predicted_class] += 1
            
            # Mantener solo últimas 10000 predicciones
            if len(self.predictions_history) > 10000:
                self.predictions_history = self.predictions_history[-10000:]
                self.inference_times = self.inference_times[-10000:]
            
        except Exception as e:
            logger.error(f"Error al registrar predicción: {str(e)}")
    
    def get_inference_stats(self) -> Dict:
        """Obtiene estadísticas de inferencia."""
        if not self.inference_times:
            return {
                'total_inferences': 0,
                'average_time_ms': 0,
                'min_time_ms': 0,
                'max_time_ms': 0,
                'inferences_per_second': 0
            }
        
        avg_time = np.mean(self.inference_times)
        
        return {
            'total_inferences': len(self.inference_times),
            'average_time_ms': float(avg_time),
            'min_time_ms': float(np.min(self.inference_times)),
            'max_time_ms': float(np.max(self.inference_times)),
            'inferences_per_second': float(1000 / avg_time) if avg_time > 0 else 0
        }
    
    def calculate_accuracy(self) -> float:
        """Calcula accuracy basado en predicciones con ground truth."""
        predictions_with_truth = [
            p for p in self.predictions_history 
            if p['true_label'] is not None
        ]
        
        if not predictions_with_truth:
            return 0.0
        
        correct = sum(
            1 for p in predictions_with_truth 
            if p['predicted_class'] == p['true_label']
        )
        
        return correct / len(predictions_with_truth)
    
    def get_confusion_matrix(self, num_classes: int = 10) -> np.ndarray:
        """
        Calcula matriz de confusión.
        
        Args:
            num_classes: Número de clases
            
        Returns:
            Matriz de confusión NxN
        """
        predictions_with_truth = [
            p for p in self.predictions_history 
            if p['true_label'] is not None
        ]
        
        if not predictions_with_truth:
            return np.zeros((num_classes, num_classes), dtype=int)
        
        matrix = np.zeros((num_classes, num_classes), dtype=int)
        
        for p in predictions_with_truth:
            true_label = p['true_label']
            predicted = p['predicted_class']
            if true_label < num_classes and predicted < num_classes:
                matrix[true_label][predicted] += 1
        
        return matrix
    
    def calculate_per_class_metrics(self, num_classes: int = 10) -> List[Dict]:
        """
        Calcula precision, recall, f1-score por clase.
        
        Returns:
            Lista de métricas por clase
        """
        confusion_matrix = self.get_confusion_matrix(num_classes)
        
        class_names = [
            "T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
            "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"
        ]
        
        metrics = []
        
        for i in range(num_classes):
            # True Positives: diagonal
            tp = confusion_matrix[i][i]
            
            # False Positives: suma de columna i - TP
            fp = np.sum(confusion_matrix[:, i]) - tp
            
            # False Negatives: suma de fila i - TP
            fn = np.sum(confusion_matrix[i, :]) - tp
            
            # Precision
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            
            # Recall
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            
            # F1-Score
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            # Support (total de muestras reales de esta clase)
            support = int(np.sum(confusion_matrix[i, :]))
            
            metrics.append({
                'class_name': class_names[i] if i < len(class_names) else f"Class {i}",
                'class_id': i,
                'precision': float(precision),
                'recall': float(recall),
                'f1_score': float(f1),
                'support': support
            })
        
        return metrics
    
    def get_overall_metrics(self) -> Dict:
        """Obtiene métricas generales del modelo."""
        per_class = self.calculate_per_class_metrics()
        
        # Promedios (macro average)
        if per_class:
            avg_precision = np.mean([m['precision'] for m in per_class])
            avg_recall = np.mean([m['recall'] for m in per_class])
            avg_f1 = np.mean([m['f1_score'] for m in per_class])
        else:
            avg_precision = avg_recall = avg_f1 = 0.0
        
        inference_stats = self.get_inference_stats()
        
        return {
            'accuracy': float(self.calculate_accuracy()),
            'precision': float(avg_precision),
            'recall': float(avg_recall),
            'f1_score': float(avg_f1),
            'total_predictions': len(self.predictions_history),
            'average_inference_time': inference_stats['average_time_ms']
        }
    
    def load_validation_metrics(self, metrics_dict: Dict):
        """
        Carga métricas de validación desde el entrenamiento.
        
        Args:
            metrics_dict: Diccionario con métricas del modelo entrenado
        """
        self.validation_metrics = metrics_dict
        logger.info("✅ Métricas de validación cargadas")
    
    def get_training_history(self) -> Optional[Dict]:
        """
        Obtiene historial de entrenamiento si está disponible.
        
        Returns:
            Diccionario con history de entrenamiento
        """
        # TODO: Cargar desde archivo de training history
        # Por ahora retornamos datos mock
        return {
            'epochs': [1, 2, 3, 4, 5],
            'train_accuracy': [0.7, 0.8, 0.85, 0.88, 0.9],
            'val_accuracy': [0.68, 0.78, 0.83, 0.86, 0.88],
            'train_loss': [0.8, 0.6, 0.5, 0.4, 0.35],
            'val_loss': [0.85, 0.65, 0.55, 0.45, 0.4]
        }
    
    def get_class_distribution(self) -> Dict[str, int]:
        """Obtiene distribución de predicciones por clase."""
        class_names = [
            "T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
            "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"
        ]
        
        return {
            class_names[class_id] if class_id < len(class_names) else f"Class {class_id}": count
            for class_id, count in self.class_counts.items()
        }


# Instancia global del servicio (singleton)
metrics_service = MetricsService()
