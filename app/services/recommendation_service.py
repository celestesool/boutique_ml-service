"""
Servicio de Recomendaciones - ML No Supervisado
Combina similitud coseno (visual) con co-ocurrencia (comportamiento)
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter
from datetime import datetime

from app.utils.logger import logger
from app.services.embedding_service import embedding_service
from app.services.faiss_service import faiss_service


class RecommendationService:
    """
    Servicio de recomendaciones usando ML No Supervisado.
    
    Estrategias:
    1. Visual: Similitud coseno de embeddings (productos visualment similares)
    2. Collaborative: Co-ocurrencia (productos vistos/comprados juntos)
    3. Hybrid: Combinación de ambas
    """
    
    def __init__(self):
        """Inicializa el servicio de recomendaciones."""
        # Matriz de co-ocurrencia: {product_id: {other_product_id: count}}
        self.co_occurrence_matrix: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Interacciones por usuario: {user_id: [(product_id, timestamp)]}
        self.user_interactions: Dict[str, List[Tuple[str, datetime]]] = defaultdict(list)
        
        # Contador de popularidad
        self.product_popularity: Counter = Counter()
        
    def register_interaction(
        self,
        user_id: str,
        product_id: str,
        interaction_type: str = "view"
    ):
        """
        Registra una interacción usuario-producto.
        Actualiza la matriz de co-ocurrencia.
        
        Args:
            user_id: ID del usuario
            product_id: ID del producto
            interaction_type: Tipo de interacción (view, purchase, like)
        """
        try:
            timestamp = datetime.now()
            
            # Registrar interacción
            self.user_interactions[user_id].append((product_id, timestamp))
            self.product_popularity[product_id] += 1
            
            # Actualizar co-ocurrencia con productos recientes del usuario
            # (últimas 10 interacciones)
            recent_products = [
                p for p, t in self.user_interactions[user_id][-11:-1]
            ]
            
            for other_product in recent_products:
                if other_product != product_id:
                    # Incrementar co-ocurrencia bidireccional
                    self.co_occurrence_matrix[product_id][other_product] += 1
                    self.co_occurrence_matrix[other_product][product_id] += 1
            
            logger.info(
                f"✅ Interacción registrada: user={user_id}, "
                f"product={product_id}, type={interaction_type}"
            )
            
            return len(self.user_interactions[user_id])
            
        except Exception as e:
            logger.error(f"Error al registrar interacción: {str(e)}")
            raise
    
    def get_visual_recommendations(
        self,
        product_id: str,
        n: int = 5
    ) -> List[Tuple[str, float, str]]:
        """
        Recomendaciones basadas en similitud visual (embeddings).
        
        Args:
            product_id: ID del producto base
            n: Número de recomendaciones
            
        Returns:
            Lista de tuplas (product_id, score, reason)
        """
        try:
            logger.info(f"Buscando recomendaciones visuales para {product_id}")
            
            # Buscar similares usando FAISS
            # Nota: Aquí necesitarías el embedding del product_id
            # Por ahora retornamos mock data
            
            recommendations = []
            # TODO: Implementar búsqueda real cuando tengamos embeddings en BD
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error en recomendaciones visuales: {str(e)}")
            return []
    
    def get_collaborative_recommendations(
        self,
        product_id: str,
        n: int = 5
    ) -> List[Tuple[str, float, str]]:
        """
        Recomendaciones basadas en co-ocurrencia (filtrado colaborativo).
        "Los que vieron esto también vieron..."
        
        Args:
            product_id: ID del producto base
            n: Número de recomendaciones
            
        Returns:
            Lista de tuplas (product_id, score, reason)
        """
        try:
            logger.info(f"Buscando recomendaciones colaborativas para {product_id}")
            
            if product_id not in self.co_occurrence_matrix:
                logger.warning(f"Producto {product_id} sin co-ocurrencias")
                return []
            
            # Obtener productos co-ocurrentes ordenados por frecuencia
            co_occurrences = self.co_occurrence_matrix[product_id]
            
            if not co_occurrences:
                return []
            
            # Ordenar por frecuencia de co-ocurrencia
            sorted_products = sorted(
                co_occurrences.items(),
                key=lambda x: x[1],
                reverse=True
            )[:n]
            
            # Normalizar scores (0-1)
            max_count = max(co_occurrences.values()) if co_occurrences else 1
            
            recommendations = [
                (
                    other_product,
                    count / max_count,  # Score normalizado
                    f"Visto junto {count} veces"
                )
                for other_product, count in sorted_products
            ]
            
            logger.info(f"✅ Encontradas {len(recommendations)} recomendaciones colaborativas")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error en recomendaciones colaborativas: {str(e)}")
            return []
    
    def get_hybrid_recommendations(
        self,
        product_id: str,
        n: int = 5,
        visual_weight: float = 0.5,
        collaborative_weight: float = 0.5
    ) -> List[Tuple[str, float, str]]:
        """
        Recomendaciones híbridas (visual + colaborativo).
        
        Args:
            product_id: ID del producto base
            n: Número de recomendaciones
            visual_weight: Peso de similitud visual
            collaborative_weight: Peso de co-ocurrencia
            
        Returns:
            Lista de tuplas (product_id, score, reason)
        """
        try:
            logger.info(f"Generando recomendaciones híbridas para {product_id}")
            
            # Obtener ambos tipos de recomendaciones
            visual_recs = self.get_visual_recommendations(product_id, n * 2)
            collab_recs = self.get_collaborative_recommendations(product_id, n * 2)
            
            # Combinar scores
            combined_scores: Dict[str, Dict] = {}
            
            # Añadir recomendaciones visuales
            for prod_id, score, reason in visual_recs:
                combined_scores[prod_id] = {
                    'visual_score': score * visual_weight,
                    'collab_score': 0,
                    'reasons': [reason]
                }
            
            # Añadir recomendaciones colaborativas
            for prod_id, score, reason in collab_recs:
                if prod_id in combined_scores:
                    combined_scores[prod_id]['collab_score'] = score * collaborative_weight
                    combined_scores[prod_id]['reasons'].append(reason)
                else:
                    combined_scores[prod_id] = {
                        'visual_score': 0,
                        'collab_score': score * collaborative_weight,
                        'reasons': [reason]
                    }
            
            # Calcular score final y ordenar
            final_recommendations = []
            for prod_id, scores in combined_scores.items():
                total_score = scores['visual_score'] + scores['collab_score']
                reason = " + ".join(scores['reasons'])
                final_recommendations.append((prod_id, total_score, reason))
            
            # Ordenar por score y tomar top N
            final_recommendations.sort(key=lambda x: x[1], reverse=True)
            final_recommendations = final_recommendations[:n]
            
            logger.info(f"✅ Generadas {len(final_recommendations)} recomendaciones híbridas")
            
            return final_recommendations
            
        except Exception as e:
            logger.error(f"Error en recomendaciones híbridas: {str(e)}")
            return []
    
    def get_recommendations(
        self,
        product_id: Optional[str] = None,
        user_id: Optional[str] = None,
        n: int = 5,
        strategy: str = "hybrid"
    ) -> List[Tuple[str, float, str]]:
        """
        Obtiene recomendaciones según la estrategia especificada.
        
        Args:
            product_id: ID del producto base (opcional)
            user_id: ID del usuario (opcional)
            n: Número de recomendaciones
            strategy: 'visual', 'collaborative', o 'hybrid'
            
        Returns:
            Lista de tuplas (product_id, score, reason)
        """
        try:
            # Si se proporciona user_id pero no product_id,
            # usar el último producto visto por el usuario
            if user_id and not product_id:
                if user_id in self.user_interactions and self.user_interactions[user_id]:
                    product_id = self.user_interactions[user_id][-1][0]
                    logger.info(f"Usando último producto visto por {user_id}: {product_id}")
            
            if not product_id:
                logger.warning("No se proporcionó product_id ni user_id válido")
                # Retornar productos más populares
                return self._get_popular_products(n)
            
            # Seleccionar estrategia
            if strategy == "visual":
                return self.get_visual_recommendations(product_id, n)
            elif strategy == "collaborative":
                return self.get_collaborative_recommendations(product_id, n)
            else:  # hybrid
                return self.get_hybrid_recommendations(product_id, n)
                
        except Exception as e:
            logger.error(f"Error al obtener recomendaciones: {str(e)}")
            return []
    
    def _get_popular_products(self, n: int) -> List[Tuple[str, float, str]]:
        """Retorna los productos más populares."""
        most_common = self.product_popularity.most_common(n)
        max_count = most_common[0][1] if most_common else 1
        
        return [
            (prod_id, count / max_count, "Producto popular")
            for prod_id, count in most_common
        ]
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del sistema de recomendaciones."""
        total_interactions = sum(len(interactions) for interactions in self.user_interactions.values())
        
        # Top pares de productos co-ocurrentes
        all_pairs = []
        for prod_a, co_prods in self.co_occurrence_matrix.items():
            for prod_b, count in co_prods.items():
                if prod_a < prod_b:  # Evitar duplicados
                    all_pairs.append((prod_a, prod_b, count))
        
        top_pairs = sorted(all_pairs, key=lambda x: x[2], reverse=True)[:10]
        
        return {
            "total_interactions": total_interactions,
            "unique_users": len(self.user_interactions),
            "unique_products": len(self.product_popularity),
            "products_with_cooccurrence": len(self.co_occurrence_matrix),
            "top_pairs": [
                {
                    "product_a": pa,
                    "product_b": pb,
                    "count": count
                }
                for pa, pb, count in top_pairs
            ]
        }


# Instancia global del servicio (singleton)
recommendation_service = RecommendationService()
