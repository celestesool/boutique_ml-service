"""
Endpoints para extracción de embeddings y búsqueda por similitud.
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Header
from typing import List, Optional
import numpy as np

from app.schemas.embeddings import (
    EmbeddingRequest,
    EmbeddingResponse,
    SimilarityRequest,
    SimilarityResponse,
    BatchEmbeddingResponse,
    FindSimilarRequest,
    FindSimilarResponse,
    SimilarImageResult
)
from app.services.embedding_service import embedding_service
from app.services.faiss_service import faiss_service
from app.database.mongodb import get_database
from app.config import settings
from app.utils.logger import logger

router = APIRouter()


async def verify_api_key(x_api_key: str = Header(...)):
    """Verifica la API key en el header."""
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="API Key inválida")
    return x_api_key


@router.post("/embeddings/extract", response_model=EmbeddingResponse)
async def extract_embedding(
    file: UploadFile = File(..., description="Imagen para extraer embedding"),
    image_id: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Extrae el embedding (vector de características) de una imagen.
    
    - **file**: Imagen en formato JPG, PNG, etc.
    - **image_id**: ID opcional para identificar la imagen
    
    Retorna un vector de 1280 dimensiones que representa las características visuales.
    """
    try:
        logger.info(f"Extrayendo embedding de imagen: {file.filename}")
        
        # Leer bytes de la imagen
        image_bytes = await file.read()
        
        # Extraer embedding
        embedding = embedding_service.extract_embedding(image_bytes)
        
        # Guardar en MongoDB si se proporcionó image_id
        if image_id:
            db = await get_database()
            await db.embeddings.update_one(
                {"image_id": image_id},
                {
                    "$set": {
                        "image_id": image_id,
                        "embedding": embedding.tolist(),
                        "embedding_size": len(embedding),
                        "filename": file.filename
                    }
                },
                upsert=True
            )
            logger.info(f"✅ Embedding guardado en BD para image_id: {image_id}")
            
            # Añadir al índice FAISS para búsqueda rápida
            try:
                faiss_service.add_embeddings(
                    embeddings=embedding.reshape(1, -1),
                    image_ids=[image_id],
                    metadata=[{"filename": file.filename}]
                )
                logger.info(f"✅ Embedding añadido al índice FAISS")
            except Exception as e:
                logger.warning(f"No se pudo añadir al FAISS: {str(e)}")
        
        return EmbeddingResponse(
            success=True,
            embedding=embedding.tolist(),
            embedding_size=len(embedding),
            image_id=image_id
        )
        
    except Exception as e:
        logger.error(f"Error al extraer embedding: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al extraer embedding: {str(e)}")


@router.post("/embeddings/similarity", response_model=SimilarityResponse)
async def calculate_similarity(
    file1: UploadFile = File(..., description="Primera imagen"),
    file2: UploadFile = File(..., description="Segunda imagen"),
    api_key: str = Depends(verify_api_key)
):
    """
    Calcula la similitud visual entre dos imágenes.
    
    - **file1**: Primera imagen
    - **file2**: Segunda imagen
    
    Retorna similitud coseno (0-1), donde 1 significa imágenes idénticas.
    """
    try:
        logger.info(f"Calculando similitud entre {file1.filename} y {file2.filename}")
        
        # Leer imágenes
        image1_bytes = await file1.read()
        image2_bytes = await file2.read()
        
        # Extraer embeddings
        embedding1 = embedding_service.extract_embedding(image1_bytes)
        embedding2 = embedding_service.extract_embedding(image2_bytes)
        
        # Calcular similitud
        similarity = embedding_service.compute_similarity(embedding1, embedding2)
        
        # Interpretar similitud
        if similarity >= 0.9:
            interpretation = "Muy similar (casi idénticas)"
        elif similarity >= 0.7:
            interpretation = "Similar"
        elif similarity >= 0.5:
            interpretation = "Moderadamente similar"
        else:
            interpretation = "Poco similar (diferentes)"
        
        logger.info(f"✅ Similitud calculada: {similarity:.4f} - {interpretation}")
        
        return SimilarityResponse(
            success=True,
            similarity=similarity,
            image_id_1=file1.filename,
            image_id_2=file2.filename,
            interpretation=interpretation
        )
        
    except Exception as e:
        logger.error(f"Error al calcular similitud: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al calcular similitud: {str(e)}")


@router.post("/embeddings/find-similar", response_model=FindSimilarResponse)
async def find_similar_images(
    file: UploadFile = File(..., description="Imagen de consulta"),
    request: FindSimilarRequest = Depends(),
    api_key: str = Depends(verify_api_key)
):
    """
    Busca imágenes similares en la base de datos usando FAISS (ultrarrápido).
    
    - **file**: Imagen de consulta
    - **top_k**: Número de resultados (máximo 100)
    - **threshold**: Umbral mínimo de similitud (0-1)
    
    Retorna las imágenes más similares encontradas en la BD.
    """
    try:
        logger.info(f"Buscando imágenes similares a {file.filename} con FAISS")
        
        # Extraer embedding de la imagen de consulta
        image_bytes = await file.read()
        query_embedding = embedding_service.extract_embedding(image_bytes)
        
        # Buscar usando FAISS (mucho más rápido)
        faiss_results = faiss_service.search(
            query_embedding=query_embedding,
            k=request.top_k,
            return_distances=True
        )
        
        if not faiss_results:
            logger.warning("No hay embeddings en el índice FAISS")
            return FindSimilarResponse(
                success=True,
                query_image_id=file.filename,
                similar_images=[],
                count=0
            )
        
        # Filtrar por threshold y crear respuesta
        similar_images = []
        for image_id, similarity in faiss_results:
            if similarity >= request.threshold:
                # Obtener metadata de MongoDB si existe
                db = await get_database()
                doc = await db.embeddings.find_one({"image_id": image_id})
                product_id = doc.get("product_id") if doc else None
                
                similar_images.append(
                    SimilarImageResult(
                        image_id=image_id,
                        similarity=similarity,
                        product_id=product_id
                    )
                )
        
        logger.info(f"✅ Encontradas {len(similar_images)} imágenes similares con FAISS (threshold: {request.threshold})")
        
        return FindSimilarResponse(
            success=True,
            query_image_id=file.filename,
            similar_images=similar_images,
            count=len(similar_images)
        )
        
    except Exception as e:
        logger.error(f"Error al buscar imágenes similares: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al buscar similares: {str(e)}")


@router.get("/embeddings/stats")
async def get_embedding_stats(api_key: str = Depends(verify_api_key)):
    """
    Obtiene estadísticas sobre embeddings almacenados en MongoDB y FAISS.
    
    Retorna información sobre cuántos embeddings hay en BD y en el índice FAISS.
    """
    try:
        db = await get_database()
        
        total_embeddings = await db.embeddings.count_documents({})
        
        # Obtener ejemplo de embedding
        sample = await db.embeddings.find_one({})
        embedding_size = sample.get("embedding_size", 1280) if sample else 1280
        
        # Estadísticas de FAISS
        faiss_stats = faiss_service.get_stats()
        
        return {
            "success": True,
            "mongodb": {
                "total_embeddings": total_embeddings,
                "embedding_size": embedding_size,
                "status": "ready" if total_embeddings > 0 else "empty"
            },
            "faiss": faiss_stats,
            "model": "EfficientNetB0"
        }
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener stats: {str(e)}")


@router.post("/embeddings/index/build")
async def build_faiss_index(api_key: str = Depends(verify_api_key)):
    """
    Construye el índice FAISS desde todos los embeddings en MongoDB.
    
    Útil para reconstruir el índice después de añadir muchos embeddings.
    """
    try:
        logger.info("Construyendo índice FAISS desde MongoDB...")
        
        db = await get_database()
        
        # Obtener todos los embeddings de MongoDB
        cursor = db.embeddings.find({}, {"image_id": 1, "embedding": 1, "filename": 1})
        
        embeddings_list = []
        image_ids = []
        metadata_list = []
        
        async for doc in cursor:
            if "embedding" in doc:
                embeddings_list.append(doc["embedding"])
                image_ids.append(doc["image_id"])
                metadata_list.append({"filename": doc.get("filename", "unknown")})
        
        if not embeddings_list:
            return {
                "success": False,
                "message": "No hay embeddings en MongoDB para construir el índice",
                "total_embeddings": 0
            }
        
        # Convertir a numpy array
        embeddings_array = np.array(embeddings_list, dtype='float32')
        
        # Crear nuevo índice FAISS
        faiss_service.create_index("L2")
        
        # Añadir todos los embeddings
        faiss_service.add_embeddings(
            embeddings=embeddings_array,
            image_ids=image_ids,
            metadata=metadata_list
        )
        
        # Guardar índice en disco
        faiss_service.save_index()
        
        logger.info(f"✅ Índice FAISS construido con {len(embeddings_list)} embeddings")
        
        return {
            "success": True,
            "message": "Índice FAISS construido exitosamente",
            "total_embeddings": len(embeddings_list),
            "index_saved": True
        }
        
    except Exception as e:
        logger.error(f"Error al construir índice FAISS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al construir índice: {str(e)}")


@router.post("/embeddings/index/load")
async def load_faiss_index(api_key: str = Depends(verify_api_key)):
    """
    Carga el índice FAISS desde disco.
    
    Útil para cargar un índice previamente guardado al iniciar el servicio.
    """
    try:
        logger.info("Cargando índice FAISS desde disco...")
        
        success = faiss_service.load_index()
        
        if success:
            stats = faiss_service.get_stats()
            return {
                "success": True,
                "message": "Índice FAISS cargado exitosamente",
                "stats": stats
            }
        else:
            return {
                "success": False,
                "message": "No se encontró índice FAISS guardado. Usa /embeddings/index/build para crear uno.",
                "stats": faiss_service.get_stats()
            }
        
    except Exception as e:
        logger.error(f"Error al cargar índice FAISS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al cargar índice: {str(e)}")
