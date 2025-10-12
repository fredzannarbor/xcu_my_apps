"""Image generation service for face images."""

import logging
import random
import requests
from typing import Tuple, Optional

from ..core.exceptions import APIError

logger = logging.getLogger(__name__)


class ImageService:
    """Service for generating face images."""
    
    def __init__(self, timeout: int = 10):
        """Initialize image service."""
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'trillions-of-people/1.0 (https://trillionsofpeople.info)'
        })
        
        # Fallback placeholder images
        self.placeholder_images = {
            'male': 'https://via.placeholder.com/150x150/4A90E2/FFFFFF?text=Male',
            'female': 'https://via.placeholder.com/150x150/E24A90/FFFFFF?text=Female',
            'default': 'https://via.placeholder.com/150x150/50C878/FFFFFF?text=Person'
        }
        
        logger.info("ImageService initialized")
    
    def get_face_image_url(self, gender: str, age_range: Tuple[int, int] = (20, 70), max_retries: int = 2) -> Optional[str]:
        """Get URL for generated face image."""
        # Normalize gender
        gender = gender.lower() if gender else 'default'
        
        # Try face generation API first
        for attempt in range(max_retries):
            try:
                return self._get_face_from_api(gender, age_range)
            except APIError as e:
                logger.warning(f"Face API attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    break
        
        # Fall back to placeholder
        logger.info(f"Using placeholder image for {gender}")
        return self._get_placeholder_image(gender)
    
    def _get_face_from_api(self, gender: str, age_range: Tuple[int, int]) -> str:
        """Get face image from FakeFace API."""
        try:
            # Use the FakeFace API as in the original code
            base_uri = "https://fakeface.rest/thumb/view?"
            noise = str(random.randint(1, 99))
            
            # Map gender for API
            api_gender = gender if gender in ['male', 'female'] else 'male'
            
            face_url = f"{base_uri}{noise}/{api_gender}"
            
            logger.debug(f"Requesting face image: {face_url}")
            
            # Test if the URL is accessible
            response = self.session.head(face_url, timeout=self.timeout)
            response.raise_for_status()
            
            logger.debug(f"Got face image URL: {face_url}")
            return face_url
            
        except requests.exceptions.Timeout as e:
            raise APIError(f"Face API request timed out: {e}")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Face API request failed: {e}")
        except Exception as e:
            raise APIError(f"Failed to generate face image: {e}")
    
    def _get_placeholder_image(self, gender: str) -> str:
        """Get placeholder image URL."""
        if gender in self.placeholder_images:
            return self.placeholder_images[gender]
        return self.placeholder_images['default']
    
    def get_face_image_html(self, gender: str, age_range: Tuple[int, int] = (20, 70), height: int = 90) -> str:
        """Get HTML img tag for face image (for compatibility with existing code)."""
        try:
            image_url = self.get_face_image_url(gender, age_range)
            if image_url:
                return f'<img src="{image_url}" height="{height}">'
            else:
                return f'<img src="{self._get_placeholder_image(gender)}" height="{height}">'
        except Exception as e:
            logger.error(f"Failed to generate image HTML: {e}")
            return f'<img src="{self._get_placeholder_image("default")}" height="{height}">'
    
    def is_available(self) -> bool:
        """Check if the image service is available."""
        try:
            # Test with a simple request to the face API
            test_url = "https://fakeface.rest/thumb/view?1/male"
            response = self.session.head(test_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def add_placeholder_image(self, gender: str, url: str):
        """Add a custom placeholder image for a gender."""
        self.placeholder_images[gender] = url
        logger.info(f"Added placeholder image for {gender}: {url}")