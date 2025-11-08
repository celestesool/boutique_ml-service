"""
Schemas package initialization
"""

from app.schemas.classification import (
    ClassificationRequest,
    ClassificationResponse,
    ProductLabelsResponse
)
from app.schemas.similarity import (
    SimilarityRequest,
    SimilarityResponse,
    SimilarProduct
)
from app.schemas.search import (
    SearchByImageRequest,
    SearchByImageResponse,
    ProductMatch
)
from app.schemas.training import (
    TrainingRequest,
    TrainingResponse,
    TrainingStatusResponse
)

__all__ = [
    "ClassificationRequest",
    "ClassificationResponse",
    "ProductLabelsResponse",
    "SimilarityRequest",
    "SimilarityResponse",
    "SimilarProduct",
    "SearchByImageRequest",
    "SearchByImageResponse",
    "ProductMatch",
    "TrainingRequest",
    "TrainingResponse",
    "TrainingStatusResponse",
]
