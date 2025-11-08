"""
Servicio FAISS para búsqueda vectorial ultrarrápida de imágenes similares.
FAISS (Facebook AI Similarity Search) permite buscar en millones de vectores en milisegundos.
"""
import faiss
import numpy as np
import pickle
import os
from typing import List, Tuple, Optional, Dict
from pathlib import Path

from app.utils.logger import logger
from app.config import settings


class FAISSService:
    """
    Servicio para gestionar índice FAISS de embeddings.
    Permite búsqueda de k-vecinos más cercanos (k-NN) ultrarrápida.
    """
    
    def __init__(self, embedding_size: int = 1280):
        """
        Inicializa el servicio FAISS.
        
        Args:
            embedding_size: Dimensión de los embeddings (1280 para EfficientNetB0)
        """
        self.embedding_size = embedding_size
        self.index: Optional[faiss.Index] = None
        self.id_mapping: Dict[int, str] = {}  # Mapeo de índice FAISS -> image_id
        self.metadata: Dict[str, Dict] = {}   # Metadata de cada imagen
        self.index_path = Path("models/faiss_index")
        self.index_path.mkdir(parents=True, exist_ok=True)
        
    def create_index(self, index_type: str = "L2"):
        """
        Crea un nuevo índice FAISS.
        
        Args:
            index_type: Tipo de índice
                - "L2": Distancia euclidiana (por defecto)
                - "Cosine": Similitud coseno (mejor para embeddings normalizados)
                - "IVF": Inverted File (más rápido para grandes datasets)
        """
        try:
            logger.info(f"Creando índice FAISS tipo {index_type}, dimensión {self.embedding_size}")
            
            if index_type == "L2":
                # Índice básico con distancia L2 (euclidiana)
                self.index = faiss.IndexFlatL2(self.embedding_size)
                
            elif index_type == "Cosine":
                # Índice con producto interno (similitud coseno para vectores normalizados)
                self.index = faiss.IndexFlatIP(self.embedding_size)
                
            elif index_type == "IVF":
                # Índice con cuantización para datasets grandes (100k+ embeddings)
                # Usa 100 clusters (ajustar según tamaño del dataset)
                quantizer = faiss.IndexFlatL2(self.embedding_size)
                self.index = faiss.IndexIVFFlat(quantizer, self.embedding_size, 100)
                logger.info("⚠️  IVF requiere entrenamiento antes de añadir vectores")
            else:
                raise ValueError(f"Tipo de índice no soportado: {index_type}")
            
            logger.info(f"✅ Índice FAISS creado exitosamente")
            
        except Exception as e:
            logger.error(f"Error al crear índice FAISS: {str(e)}")
            raise
    
    def add_embeddings(
        self, 
        embeddings: np.ndarray, 
        image_ids: List[str],
        metadata: Optional[List[Dict]] = None
    ):
        """
        Añade embeddings al índice FAISS.
        
        Args:
            embeddings: Array numpy con embeddings (shape: [n, embedding_size])
            image_ids: Lista de IDs de imágenes
            metadata: Lista opcional de metadata para cada imagen
        """
        try:
            if self.index is None:
                logger.warning("Índice no creado, creando índice L2 por defecto")
                self.create_index("L2")
            
            # Validar dimensiones
            if embeddings.shape[1] != self.embedding_size:
                raise ValueError(
                    f"Dimensión de embeddings ({embeddings.shape[1]}) "
                    f"no coincide con índice ({self.embedding_size})"
                )
            
            if len(embeddings) != len(image_ids):
                raise ValueError("Número de embeddings y IDs no coincide")
            
            # Convertir a float32 (requerido por FAISS)
            embeddings = embeddings.astype('float32')
            
            # Obtener el índice actual antes de añadir
            current_size = self.index.ntotal
            
            # Añadir embeddings al índice
            self.index.add(embeddings)
            
            # Actualizar mapeo de IDs
            for i, image_id in enumerate(image_ids):
                faiss_idx = current_size + i
                self.id_mapping[faiss_idx] = image_id
                
                # Guardar metadata si se proporcionó
                if metadata and i < len(metadata):
                    self.metadata[image_id] = metadata[i]
            
            logger.info(f"✅ Añadidos {len(embeddings)} embeddings al índice FAISS")
            logger.info(f"   Total en índice: {self.index.ntotal}")
            
        except Exception as e:
            logger.error(f"Error al añadir embeddings: {str(e)}")
            raise
    
    def search(
        self, 
        query_embedding: np.ndarray, 
        k: int = 10,
        return_distances: bool = True
    ) -> List[Tuple[str, float]]:
        """
        Busca los k vecinos más cercanos de un embedding.
        
        Args:
            query_embedding: Embedding de consulta (shape: [embedding_size])
            k: Número de vecinos más cercanos a retornar
            return_distances: Si retornar las distancias/similitudes
            
        Returns:
            Lista de tuplas (image_id, distance/similarity)
        """
        try:
            if self.index is None or self.index.ntotal == 0:
                logger.warning("Índice vacío, retornando lista vacía")
                return []
            
            # Validar dimensión
            if query_embedding.shape[0] != self.embedding_size:
                raise ValueError(
                    f"Dimensión del query ({query_embedding.shape[0]}) "
                    f"no coincide con índice ({self.embedding_size})"
                )
            
            # Convertir a float32 y expandir dimensiones para batch
            query = query_embedding.astype('float32').reshape(1, -1)
            
            # Ajustar k si hay menos embeddings
            k = min(k, self.index.ntotal)
            
            # Buscar k vecinos más cercanos
            distances, indices = self.index.search(query, k)
            
            # Convertir índices a image_ids
            results = []
            for i in range(len(indices[0])):
                faiss_idx = int(indices[0][i])
                distance = float(distances[0][i])
                
                if faiss_idx in self.id_mapping:
                    image_id = self.id_mapping[faiss_idx]
                    
                    if return_distances:
                        # Convertir distancia L2 a similitud (0-1)
                        # Similitud más alta = más cercano
                        similarity = 1 / (1 + distance)
                        results.append((image_id, similarity))
                    else:
                        results.append((image_id, distance))
            
            logger.info(f"✅ Búsqueda completada: {len(results)} resultados encontrados")
            
            return results
            
        except Exception as e:
            logger.error(f"Error en búsqueda FAISS: {str(e)}")
            raise
    
    def batch_search(
        self,
        query_embeddings: np.ndarray,
        k: int = 10
    ) -> List[List[Tuple[str, float]]]:
        """
        Busca vecinos para múltiples queries en batch (más eficiente).
        
        Args:
            query_embeddings: Array de embeddings (shape: [n_queries, embedding_size])
            k: Número de vecinos por query
            
        Returns:
            Lista de listas con resultados para cada query
        """
        try:
            if self.index is None or self.index.ntotal == 0:
                return [[] for _ in range(len(query_embeddings))]
            
            # Convertir a float32
            queries = query_embeddings.astype('float32')
            
            # Ajustar k
            k = min(k, self.index.ntotal)
            
            # Búsqueda en batch
            distances, indices = self.index.search(queries, k)
            
            # Procesar resultados
            all_results = []
            for i in range(len(queries)):
                results = []
                for j in range(k):
                    faiss_idx = int(indices[i][j])
                    distance = float(distances[i][j])
                    
                    if faiss_idx in self.id_mapping:
                        image_id = self.id_mapping[faiss_idx]
                        similarity = 1 / (1 + distance)
                        results.append((image_id, similarity))
                
                all_results.append(results)
            
            logger.info(f"✅ Batch search completado: {len(queries)} queries procesadas")
            
            return all_results
            
        except Exception as e:
            logger.error(f"Error en batch search: {str(e)}")
            raise
    
    def save_index(self, filename: str = "faiss_index.index"):
        """
        Guarda el índice FAISS y metadata en disco.
        
        Args:
            filename: Nombre del archivo de índice
        """
        try:
            if self.index is None:
                logger.warning("No hay índice para guardar")
                return
            
            index_file = self.index_path / filename
            metadata_file = self.index_path / f"{filename}.metadata"
            
            # Guardar índice FAISS
            faiss.write_index(self.index, str(index_file))
            
            # Guardar mapeo y metadata
            with open(metadata_file, 'wb') as f:
                pickle.dump({
                    'id_mapping': self.id_mapping,
                    'metadata': self.metadata,
                    'embedding_size': self.embedding_size
                }, f)
            
            logger.info(f"✅ Índice FAISS guardado en {index_file}")
            logger.info(f"   Total embeddings: {self.index.ntotal}")
            
        except Exception as e:
            logger.error(f"Error al guardar índice: {str(e)}")
            raise
    
    def load_index(self, filename: str = "faiss_index.index"):
        """
        Carga el índice FAISS y metadata desde disco.
        
        Args:
            filename: Nombre del archivo de índice
            
        Returns:
            True si se cargó exitosamente, False si no existe
        """
        try:
            index_file = self.index_path / filename
            metadata_file = self.index_path / f"{filename}.metadata"
            
            if not index_file.exists():
                logger.warning(f"Archivo de índice no encontrado: {index_file}")
                return False
            
            # Cargar índice FAISS
            self.index = faiss.read_index(str(index_file))
            
            # Cargar mapeo y metadata
            if metadata_file.exists():
                with open(metadata_file, 'rb') as f:
                    data = pickle.load(f)
                    self.id_mapping = data['id_mapping']
                    self.metadata = data['metadata']
                    self.embedding_size = data['embedding_size']
            
            logger.info(f"✅ Índice FAISS cargado desde {index_file}")
            logger.info(f"   Total embeddings: {self.index.ntotal}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error al cargar índice: {str(e)}")
            raise
    
    def remove_embeddings(self, image_ids: List[str]):
        """
        Elimina embeddings del índice.
        Nota: FAISS no soporta eliminación directa, hay que reconstruir el índice.
        
        Args:
            image_ids: Lista de IDs de imágenes a eliminar
        """
        try:
            logger.warning("Eliminación de embeddings requiere reconstruir el índice")
            
            # Filtrar IDs a mantener
            faiss_indices_to_remove = set()
            for faiss_idx, img_id in self.id_mapping.items():
                if img_id in image_ids:
                    faiss_indices_to_remove.add(faiss_idx)
            
            logger.info(f"Se eliminarán {len(faiss_indices_to_remove)} embeddings")
            logger.info("Reconstruir índice manualmente si es necesario")
            
        except Exception as e:
            logger.error(f"Error al eliminar embeddings: {str(e)}")
            raise
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del índice FAISS.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            "total_embeddings": self.index.ntotal if self.index else 0,
            "embedding_size": self.embedding_size,
            "index_type": type(self.index).__name__ if self.index else None,
            "total_metadata": len(self.metadata),
            "index_loaded": self.index is not None
        }


# Instancia global del servicio (singleton)
faiss_service = FAISSService(embedding_size=1280)
