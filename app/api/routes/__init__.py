"""
Routes package initialization
"""

from app.api.routes import health, classification, similarity, search, training

__all__ = ["health", "classification", "similarity", "search", "training"]
