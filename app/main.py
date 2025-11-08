"""
ML Service - Main FastAPI Application
Microservicio de Machine Learning para Boutique E-commerce
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.config import settings
from app.api.routes import health, classification, similarity, search, training, supervision, embeddings, recommendations, metrics
from app.database.mongodb import connect_to_mongo, close_mongo_connection
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for FastAPI application"""
    # Startup
    logger.info("🚀 Starting ML Service...")
    await connect_to_mongo()
    logger.info("✅ ML Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down ML Service...")
    await close_mongo_connection()
    logger.info("✅ ML Service shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="ML Service - Boutique",
    description="Microservicio de Machine Learning para clasificación y búsqueda de productos",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(classification.router, prefix="/api/ml", tags=["Classification"])
app.include_router(similarity.router, prefix="/api/ml", tags=["Similarity"])
app.include_router(search.router, prefix="/api/ml", tags=["Search"])
app.include_router(training.router, prefix="/api/ml", tags=["Training"])
app.include_router(supervision.router, prefix="/api/ml", tags=["Supervision"])
app.include_router(embeddings.router, prefix="/api/ml", tags=["Embeddings"])
app.include_router(recommendations.router, prefix="/api/ml", tags=["Recommendations (ML No Supervisado)"])
app.include_router(metrics.router, prefix="/api/ml", tags=["Metrics & KPIs"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ML Service - Boutique",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.ML_SERVICE_HOST,
        port=settings.ML_SERVICE_PORT,
        reload=settings.ML_SERVICE_ENV == "development"
    )
