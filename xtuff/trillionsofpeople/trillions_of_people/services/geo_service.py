"""Geographic data service for location information."""

import logging
import random
import requests
from typing import Tuple, Dict, Optional

from ..core.exceptions import APIError

logger = logging.getLogger(__name__)


class GeoService:
    """Service for geographic data and location information."""
    
    def __init__(self, timeout: int = 10):
        """Initialize geographic service."""
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'trillions-of-people/1.0 (https://trillionsofpeople.info)'
        })
        
        # Fallback coordinates for major countries
        self.country_fallbacks = {
            'US': (39.8283, -98.5795, 'United States'),
            'CA': (56.1304, -106.3468, 'Canada'),
            'GB': (55.3781, -3.4360, 'United Kingdom'),
            'FR': (46.2276, 2.2137, 'France'),
            'DE': (51.1657, 10.4515, 'Germany'),
            'IT': (41.8719, 12.5674, 'Italy'),
            'ES': (40.4637, -3.7492, 'Spain'),
            'JP': (36.2048, 138.2529, 'Japan'),
            'CN': (35.8617, 104.1954, 'China'),
            'IN': (20.5937, 78.9629, 'India'),
            'BR': (-14.2350, -51.9253, 'Brazil'),
            'AU': (-25.2744, 133.7751, 'Australia'),
            'RU': (61.5240, 105.3188, 'Russia'),
            'Random': (0.0, 0.0, 'Unknown Location')
        }
        
        logger.info("GeoService initialized")
    
    def get_random_location(self, country_code: str, max_retries: int = 2) -> Tuple[float, float, str]:
        """Get random coordinates and nearest city for a country."""
        # Handle special case for "Random" country
        if country_code == "Random":
            return self._get_random_global_location()
        
        # Try API first
        for attempt in range(max_retries):
            try:
                return self._get_location_from_api(country_code)
            except APIError as e:
                logger.warning(f"API attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    break
        
        # Fall back to predefined coordinates
        logger.info(f"Using fallback coordinates for {country_code}")
        return self._get_fallback_location(country_code)
    
    def _get_location_from_api(self, country_code: str) -> Tuple[float, float, str]:
        """Get location from 3geonames API."""
        try:
            # Use 3geonames API as in the original code
            url = f"https://api.3geonames.org/?randomland={country_code}&json=1"
            
            logger.debug(f"Requesting location from API: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if 'nearest' in data:
                nearest = data['nearest']
                city = nearest.get('name', 'Unknown City')
                lat = float(nearest.get('latt', 0.0))
                lon = float(nearest.get('longt', 0.0))
                
                logger.debug(f"Got location from API: {city} ({lat}, {lon})")
                return lat, lon, city
            else:
                raise APIError(f"Invalid response format from geo API: {data}")
                
        except requests.exceptions.Timeout as e:
            raise APIError(f"Geo API request timed out: {e}")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Geo API request failed: {e}")
        except (ValueError, KeyError) as e:
            raise APIError(f"Failed to parse geo API response: {e}")
        except Exception as e:
            raise APIError(f"Unexpected error in geo API: {e}")
    
    def _get_fallback_location(self, country_code: str) -> Tuple[float, float, str]:
        """Get fallback coordinates for a country."""
        # Try exact match first
        if country_code in self.country_fallbacks:
            lat, lon, city = self.country_fallbacks[country_code]
            return lat, lon, city
        
        # Try case-insensitive match
        for code, (lat, lon, city) in self.country_fallbacks.items():
            if code.lower() == country_code.lower():
                return lat, lon, city
        
        # Default fallback
        logger.warning(f"No fallback coordinates for {country_code}, using default")
        return self.country_fallbacks['Random']
    
    def _get_random_global_location(self) -> Tuple[float, float, str]:
        """Get a random location from available fallbacks."""
        # Exclude 'Random' from the choices to avoid infinite recursion
        available_countries = [k for k in self.country_fallbacks.keys() if k != 'Random']
        country_code = random.choice(available_countries)
        lat, lon, city = self.country_fallbacks[country_code]
        
        # Add some randomness to the coordinates
        lat += random.uniform(-2.0, 2.0)
        lon += random.uniform(-2.0, 2.0)
        
        # Ensure coordinates stay within valid ranges
        lat = max(-90.0, min(90.0, lat))
        lon = max(-180.0, min(180.0, lon))
        
        return lat, lon, f"Near {city}"
    
    def add_country_fallback(self, country_code: str, latitude: float, longitude: float, city: str):
        """Add a new country fallback location."""
        self.country_fallbacks[country_code] = (latitude, longitude, city)
        logger.info(f"Added fallback location for {country_code}: {city}")
    
    def is_available(self) -> bool:
        """Check if the geo service is available."""
        try:
            # Test with a simple request
            response = self.session.get("https://api.3geonames.org/", timeout=5)
            return response.status_code == 200
        except Exception:
            return False