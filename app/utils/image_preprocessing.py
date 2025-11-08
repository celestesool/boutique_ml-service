"""
Image preprocessing utilities
"""

import base64
import io
import numpy as np
from PIL import Image
import cv2
from typing import Tuple, Optional
from app.config import settings
from app.utils.logger import logger


class ImagePreprocessor:
    """Image preprocessing for ML models"""
    
    def __init__(
        self,
        target_size: Tuple[int, int] = (settings.IMAGE_RESIZE_WIDTH, settings.IMAGE_RESIZE_HEIGHT)
    ):
        self.target_size = target_size
    
    def base64_to_image(self, base64_string: str) -> Image.Image:
        """Convert base64 string to PIL Image"""
        try:
            # Remove data URI scheme if present
            if "base64," in base64_string:
                base64_string = base64_string.split("base64,")[1]
            
            # Decode base64
            image_data = base64.b64decode(base64_string)
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
        except Exception as e:
            logger.error(f"Error converting base64 to image: {e}")
            raise ValueError(f"Invalid base64 image data: {e}")
    
    def image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        try:
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
        except Exception as e:
            logger.error(f"Error converting image to base64: {e}")
            raise ValueError(f"Error encoding image: {e}")
    
    def resize_image(self, image: Image.Image) -> Image.Image:
        """Resize image to target size"""
        return image.resize(self.target_size, Image.Resampling.LANCZOS)
    
    def preprocess_for_model(self, image: Image.Image) -> np.ndarray:
        """Preprocess image for ML model (normalized numpy array)"""
        # Resize
        image = self.resize_image(image)
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Normalize to [0, 1]
        img_array = img_array.astype('float32') / 255.0
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    
    def validate_image_size(self, base64_string: str) -> bool:
        """Validate image size in MB"""
        try:
            # Calculate size in MB
            size_mb = len(base64_string) * 3 / 4 / (1024 * 1024)
            
            if size_mb > settings.MAX_IMAGE_SIZE_MB:
                logger.warning(f"Image size {size_mb:.2f}MB exceeds limit {settings.MAX_IMAGE_SIZE_MB}MB")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating image size: {e}")
            return False
    
    def extract_dominant_colors(self, image: Image.Image, k: int = 5) -> list:
        """Extract dominant colors using K-means clustering"""
        try:
            # Convert to OpenCV format
            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            img_cv = cv2.resize(img_cv, (150, 150))
            
            # Reshape to list of pixels
            pixels = img_cv.reshape((-1, 3))
            pixels = np.float32(pixels)
            
            # K-means clustering
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
            _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Convert to list of RGB tuples
            centers = centers.astype(int)
            dominant_colors = [tuple(reversed(color)) for color in centers.tolist()]
            
            return dominant_colors
        except Exception as e:
            logger.error(f"Error extracting dominant colors: {e}")
            return []


# Create singleton instance
image_preprocessor = ImagePreprocessor()
