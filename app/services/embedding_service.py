"""
Servicio para extraer embeddings (vectores de características) de imágenes.
Utiliza EfficientNetB0 pre-entrenado como extractor de características.
"""
import numpy as np
from typing import List, Optional
from PIL import Image
import io
import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.applications.efficientnet import preprocess_input
from tensorflow.keras.models import Model

from app.utils.logger import logger


class EmbeddingService:
    """Servicio para generar embeddings de imágenes."""
    
    def __init__(self):
        """Inicializa el modelo extractor de embeddings."""
        self.model: Optional[Model] = None
        self.embedding_size = 1280  # EfficientNetB0 output size
        self.input_size = (224, 224)
        
    def load_model(self):
        """
        Carga EfficientNetB0 pre-entrenado y crea un modelo extractor.
        Usa la última capa antes de la clasificación para obtener embeddings.
        """
        try:
            logger.info("Cargando modelo EfficientNetB0 para extracción de embeddings...")
            
            # Cargar EfficientNetB0 pre-entrenado (sin top layer de clasificación)
            base_model = EfficientNetB0(
                weights='imagenet',
                include_top=False,  # Sin capa de clasificación
                pooling='avg',      # Global Average Pooling
                input_shape=(224, 224, 3)
            )
            
            # El modelo base ya genera embeddings de 1280 dimensiones
            self.model = base_model
            
            logger.info(f"✅ Modelo cargado exitosamente. Embedding size: {self.embedding_size}")
            logger.info(f"   Input shape: {self.input_size}")
            
        except Exception as e:
            logger.error(f"❌ Error al cargar modelo de embeddings: {str(e)}")
            raise
    
    def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """
        Preprocesa una imagen para el modelo.
        
        Args:
            image_bytes: Bytes de la imagen
            
        Returns:
            Array numpy con la imagen preprocesada
        """
        try:
            # Cargar imagen desde bytes
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convertir a RGB si es necesario
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Redimensionar
            image = image.resize(self.input_size)
            
            # Convertir a array numpy
            img_array = np.array(image)
            
            # Expandir dimensiones para batch
            img_array = np.expand_dims(img_array, axis=0)
            
            # Preprocesar según EfficientNet
            img_array = preprocess_input(img_array)
            
            return img_array
            
        except Exception as e:
            logger.error(f"Error al preprocesar imagen: {str(e)}")
            raise
    
    def extract_embedding(self, image_bytes: bytes) -> np.ndarray:
        """
        Extrae embedding de una imagen.
        
        Args:
            image_bytes: Bytes de la imagen
            
        Returns:
            Vector de embeddings (1280 dimensiones)
        """
        try:
            # Cargar modelo si no está cargado
            if self.model is None:
                self.load_model()
            
            # Preprocesar imagen
            processed_image = self.preprocess_image(image_bytes)
            
            # Extraer embedding
            embedding = self.model.predict(processed_image, verbose=0)
            
            # Normalizar el embedding (útil para similitud coseno)
            embedding = embedding / np.linalg.norm(embedding)
            
            # Retornar como vector 1D
            return embedding.flatten()
            
        except Exception as e:
            logger.error(f"Error al extraer embedding: {str(e)}")
            raise
    
    def extract_embeddings_batch(self, images_bytes: List[bytes]) -> np.ndarray:
        """
        Extrae embeddings de múltiples imágenes en batch (más eficiente).
        
        Args:
            images_bytes: Lista de bytes de imágenes
            
        Returns:
            Array numpy con embeddings (shape: [n_images, 1280])
        """
        try:
            # Cargar modelo si no está cargado
            if self.model is None:
                self.load_model()
            
            # Preprocesar todas las imágenes
            processed_images = []
            for img_bytes in images_bytes:
                processed_img = self.preprocess_image(img_bytes)
                processed_images.append(processed_img)
            
            # Concatenar en un solo batch
            batch = np.vstack(processed_images)
            
            # Extraer embeddings en batch
            embeddings = self.model.predict(batch, verbose=0)
            
            # Normalizar todos los embeddings
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / norms
            
            logger.info(f"✅ Extraídos {len(images_bytes)} embeddings en batch")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error al extraer embeddings en batch: {str(e)}")
            raise
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calcula similitud coseno entre dos embeddings.
        
        Args:
            embedding1: Primer embedding
            embedding2: Segundo embedding
            
        Returns:
            Similitud coseno (0-1, donde 1 es idéntico)
        """
        # Similitud coseno (ya que los embeddings están normalizados, es solo el producto punto)
        similarity = np.dot(embedding1, embedding2)
        return float(similarity)
    
    def find_most_similar(
        self, 
        query_embedding: np.ndarray, 
        database_embeddings: np.ndarray,
        top_k: int = 10
    ) -> List[tuple]:
        """
        Encuentra los embeddings más similares en una base de datos.
        
        Args:
            query_embedding: Embedding de consulta
            database_embeddings: Array de embeddings en la BD (shape: [n, 1280])
            top_k: Número de resultados más similares
            
        Returns:
            Lista de tuplas (índice, similitud) ordenadas por similitud
        """
        try:
            # Calcular similitudes con todos los embeddings
            similarities = np.dot(database_embeddings, query_embedding)
            
            # Obtener índices de los top-k más similares
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            # Crear lista de resultados
            results = [
                (int(idx), float(similarities[idx])) 
                for idx in top_indices
            ]
            
            return results
            
        except Exception as e:
            logger.error(f"Error al buscar similares: {str(e)}")
            raise


# Instancia global del servicio (singleton)
embedding_service = EmbeddingService()
