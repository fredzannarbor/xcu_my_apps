"""Main people generation logic."""

import logging
import random
from typing import List, Optional

from .models import Person, Config, Species, Timeline, Realness
from .exceptions import ValidationError, APIError
from ..services.llm_service import LLMService
from ..services.geo_service import GeoService
from ..services.image_service import ImageService
from ..utils.formatters import create_shortname, fourwordsname

logger = logging.getLogger(__name__)


class PeopleGenerator:
    """Main class for generating synthetic people."""
    
    def __init__(self, config: Config):
        """Initialize the people generator with configuration."""
        self.config = config
        
        # Set up logging
        from .config import ConfigManager
        config_manager = ConfigManager()
        config_manager.setup_logging(config)
        
        # Initialize services
        self.llm_service = LLMService(config.openai_api_key)
        self.geo_service = GeoService()
        self.image_service = ImageService()
        
        logger.info("PeopleGenerator initialized with config")
        
    def generate_people(
        self, 
        count: int, 
        year: int, 
        country: str,
        **kwargs
    ) -> List[Person]:
        """Generate multiple synthetic people based on parameters."""
        if count <= 0:
            raise ValidationError("Count must be positive")
        if count > self.config.max_people_per_request:
            raise ValidationError(f"Count cannot exceed {self.config.max_people_per_request}")
            
        logger.info(f"Generating {count} people for year {year} in {country}")
        
        people = []
        for i in range(count):
            try:
                person = self.generate_single_person(year, country, **kwargs)
                people.append(person)
                logger.debug(f"Generated person {i+1}/{count}: {person.name}")
            except Exception as e:
                logger.error(f"Failed to generate person {i+1}/{count}: {e}")
                # Continue with other people generation
                continue
                
        logger.info(f"Successfully generated {len(people)} out of {count} requested people")
        return people
    
    def generate_single_person(
        self, 
        year: int, 
        country: str,
        species: Optional[Species] = None,
        timeline: Optional[Timeline] = None,
        gender: Optional[str] = None,
        **kwargs
    ) -> Person:
        """Generate a single synthetic person."""
        try:
            # Set defaults
            species = species or Species.SAPIENS
            timeline = timeline or Timeline.OURS
            gender = gender or random.choice(['male', 'female'])
            
            # Generate basic attributes
            name = create_shortname(species.value)
            four_words_name = fourwordsname()
            
            # Get location data with fallback
            try:
                latitude, longitude, nearest_city = self.geo_service.get_random_location(country)
            except APIError as e:
                logger.warning(f"Geo service failed, using fallback: {e}")
                latitude, longitude, nearest_city = 0.0, 0.0, "Unknown City"
            
            # Generate backstory with fallback
            backstory = ""
            try:
                prompt = self._create_backstory_prompt(name, year, country, gender)
                backstory = self.llm_service.generate_backstory(prompt)
            except APIError as e:
                logger.warning(f"LLM service failed, using fallback: {e}")
                backstory = f"A {gender} person from {country} born in {year}."
            
            # Generate image URL with fallback
            image_url = None
            try:
                if self.config.enable_image_generation:
                    image_url = self.image_service.get_face_image_url(gender, (20, 70))
            except APIError as e:
                logger.warning(f"Image service failed: {e}")
                # image_url remains None
            
            person = Person(
                name=name,
                birth_year=year,
                gender=gender,
                species=species,
                timeline=timeline,
                realness=Realness.SYNTHETIC,
                latitude=latitude,
                longitude=longitude,
                nearest_city=nearest_city,
                country=country,
                backstory=backstory,
                four_words_name=four_words_name,
                image_url=image_url,
                source="trillions_of_people",
                status="active"
            )
            
            logger.debug(f"Generated person: {person.name} from {country}")
            return person
            
        except Exception as e:
            logger.error(f"Failed to generate person: {e}")
            raise ValidationError(f"Person generation failed: {e}")
    
    def _create_backstory_prompt(self, name: str, year: int, country: str, gender: str) -> str:
        """Create a prompt for backstory generation."""
        if year < 0:
            time_desc = f"{name} was born {abs(year)} years ago in the area now known as {country}."
        elif year == 0:
            time_desc = f"{name} was born in the area now known as {country}."
        else:
            time_desc = f"{name} will be born in the area now known as {country}."
        
        return f"{time_desc} Generate a brief biographical backstory for this {gender} person."