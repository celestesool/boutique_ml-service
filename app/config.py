"""
Configuration settings for ML Service
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    ML_SERVICE_HOST: str = "0.0.0.0"
    ML_SERVICE_PORT: int = 8000
    ML_SERVICE_ENV: str = "development"
    
    # API Security
    ML_API_KEY: str = "ml_secret_key_boutique_2025"
    # Backwards-compatible environment variable name (some setups use API_KEY)
    API_KEY: str | None = Field(None, env="API_KEY")
    SHARED_SECRET_NESTJS: str = "tu_secreto_super_secreto_aqui_2024"
    
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "ml_boutique_db"
    
    # FAISS Configuration
    FAISS_INDEX_PATH: str = "./models/faiss_index.bin"
    EMBEDDING_DIMENSION: int = 512
    
    # Model Paths
    MODEL_CLASSIFIER_PATH: str = "./models/classifier_v1.h5"
    MODEL_EMBEDDINGS_PATH: str = "./models/embeddings_v1.pkl"
    
    # NestJS Backend
    NESTJS_GRAPHQL_URL: str = "http://localhost:3001/graphql"
    NESTJS_JWT_SECRET: str = "tu_secreto_super_secreto_aqui_2024"
    
    # Training Configuration
    BATCH_SIZE: int = 32
    EPOCHS: int = 50
    LEARNING_RATE: float = 0.001
    MIN_CONFIDENCE_THRESHOLD: float = 0.70
    
    # Image Processing
    MAX_IMAGE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,webp"
    IMAGE_RESIZE_WIDTH: int = 224
    IMAGE_RESIZE_HEIGHT: int = 224
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "./logs/ml_service.log"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Frontend React
        "http://localhost:3001",  # Backend NestJS
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()


# Create directories if they don't exist
def create_directories():
    """Create necessary directories"""
    directories = [
        Path(settings.LOG_FILE_PATH).parent,
        Path(settings.MODEL_CLASSIFIER_PATH).parent,
        Path("./data/train"),
        Path("./data/validation"),
        Path("./data/test"),
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


create_directories()
