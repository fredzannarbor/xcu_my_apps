"""
Reader persona system for synthetic reader evaluation.
Creates and manages diverse reader profiles with demographic attributes and preferences.
"""

import logging
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AgeGroup(Enum):
    """Age group classifications for readers."""
    CHILD = "child"
    TEENAGER = "teenager"
    YOUNG_ADULT = "young_adult"
    ADULT = "adult"
    ELDER = "elder"


class Gender(Enum):
    """Gender classifications for readers."""
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class ReadingLevel(Enum):
    """Reading experience levels."""
    BEGINNER = "beginner"
    CASUAL = "casual"
    MODERATE = "moderate"
    AVID = "avid"
    EXPERT = "expert"


class IncomeLevel(Enum):
    """Income level classifications."""
    LOW = "low"
    LOWER_MIDDLE = "lower_middle"
    MIDDLE = "middle"
    UPPER_MIDDLE = "upper_middle"
    HIGH = "high"


@dataclass
class ReaderPersona:
    """
    Represents a synthetic reader with demographic attributes and preferences.
    Implements Requirements 5.1, 5.2, 5.6 for reader persona simulation.
    """
    
    # Core identifiers
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    
    # Demographics
    age_group: AgeGroup = AgeGroup.ADULT
    gender: Gender = Gender.PREFER_NOT_TO_SAY
    location: str = "United States"
    income_level: IncomeLevel = IncomeLevel.MIDDLE
    education_level: str = "College"
    
    # Reading characteristics
    reading_level: ReadingLevel = ReadingLevel.MODERATE
    books_per_year: int = 12
    preferred_genres: List[str] = field(default_factory=list)
    disliked_genres: List[str] = field(default_factory=list)
    preferred_length: str = "medium"  # short, medium, long
    
    # Preferences and traits
    reading_goals: List[str] = field(default_factory=lambda: ["entertainment"])
    personality_traits: List[str] = field(default_factory=list)
    content_sensitivities: List[str] = field(default_factory=list)
    format_preferences: List[str] = field(default_factory=lambda: ["physical", "digital"])
    
    # Behavioral patterns
    discovery_methods: List[str] = field(default_factory=lambda: ["recommendations", "browsing"])
    review_behavior: str = "occasional"  # never, rare, occasional, frequent, always
    social_sharing: bool = True
    price_sensitivity: str = "moderate"  # low, moderate, high
    
    # Reading history and context
    recent_reads: List[str] = field(default_factory=list)
    favorite_authors: List[str] = field(default_factory=list)
    reading_mood: str = "neutral"  # adventurous, comfort, challenging, neutral
    current_life_stage: str = "stable"  # student, career_building, family_focused, stable, retirement
    
    # Evaluation consistency
    consistency_score: float = 0.8  # How consistent this reader is in evaluations
    reliability_score: float = 0.8  # How reliable this reader's feedback is
    
    # Metadata
    created_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: Optional[str] = None
    usage_count: int = 0
    
    def get_description(self) -> str:
        """Get a natural language description of this reader persona."""
        desc_parts = []
        
        # Basic demographics
        desc_parts.append(f"{self.gender.value.replace('_', ' ').title()} {self.age_group.value.replace('_', ' ')}")
        desc_parts.append(f"from {self.location}")
        desc_parts.append(f"with {self.education_level.lower()} education")
        
        # Reading characteristics
        desc_parts.append(f"reads {self.books_per_year} books per year")
        desc_parts.append(f"at a {self.reading_level.value} level")
        
        # Preferences
        if self.preferred_genres:
            genres_str = ", ".join(self.preferred_genres[:3])
            desc_parts.append(f"enjoys {genres_str}")
        
        # Goals
        if self.reading_goals:
            goals_str = ", ".join(self.reading_goals[:2])
            desc_parts.append(f"reads for {goals_str}")
        
        return "; ".join(desc_parts)
    
    def get_evaluation_context(self) -> Dict[str, Any]:
        """Get context data for LLM evaluation."""
        return {
            "demographics": f"{self.gender.value.title()} {self.age_group.value.replace('_', ' ')}, {self.location}",
            "reading_level": self.reading_level.value,
            "books_per_year": self.books_per_year,
            "preferred_genres": self.preferred_genres,
            "disliked_genres": self.disliked_genres,
            "reading_goals": self.reading_goals,
            "personality_traits": self.personality_traits,
            "content_sensitivities": self.content_sensitivities,
            "current_mood": self.reading_mood,
            "life_stage": self.current_life_stage,
            "recent_reads": self.recent_reads[:3],  # Limit for context
            "consistency_score": self.consistency_score
        }
    
    def update_usage(self):
        """Update usage statistics."""
        self.usage_count += 1
        self.last_used = datetime.now().isoformat()
    
    def calculate_genre_affinity(self, genre: str) -> float:
        """Calculate affinity score for a specific genre."""
        if genre.lower() in [g.lower() for g in self.preferred_genres]:
            return 0.8 + random.uniform(0, 0.2)
        elif genre.lower() in [g.lower() for g in self.disliked_genres]:
            return 0.1 + random.uniform(0, 0.2)
        else:
            return 0.4 + random.uniform(0, 0.4)
    
    def simulate_reading_time(self, word_count: int) -> Dict[str, Any]:
        """Simulate how long this reader would take to read content."""
        # Base reading speeds by level (words per minute)
        reading_speeds = {
            ReadingLevel.BEGINNER: 150,
            ReadingLevel.CASUAL: 200,
            ReadingLevel.MODERATE: 250,
            ReadingLevel.AVID: 300,
            ReadingLevel.EXPERT: 350
        }
        
        base_speed = reading_speeds[self.reading_level]
        # Add some variation based on personality
        speed_variation = random.uniform(0.8, 1.2)
        actual_speed = base_speed * speed_variation
        
        reading_time_minutes = word_count / actual_speed
        
        return {
            "estimated_reading_time_minutes": reading_time_minutes,
            "reading_speed_wpm": actual_speed,
            "would_finish": reading_time_minutes <= self._get_attention_span()
        }
    
    def _get_attention_span(self) -> float:
        """Get attention span in minutes based on reader characteristics."""
        base_spans = {
            AgeGroup.CHILD: 15,
            AgeGroup.TEENAGER: 30,
            AgeGroup.YOUNG_ADULT: 45,
            AgeGroup.ADULT: 60,
            AgeGroup.ELDER: 45
        }
        
        base_span = base_spans[self.age_group]
        
        # Adjust based on reading level
        level_multipliers = {
            ReadingLevel.BEGINNER: 0.7,
            ReadingLevel.CASUAL: 0.8,
            ReadingLevel.MODERATE: 1.0,
            ReadingLevel.AVID: 1.3,
            ReadingLevel.EXPERT: 1.5
        }
        
        return base_span * level_multipliers[self.reading_level]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert persona to dictionary format."""
        return {
            "uuid": self.uuid,
            "name": self.name,
            "age_group": self.age_group.value,
            "gender": self.gender.value,
            "location": self.location,
            "income_level": self.income_level.value,
            "education_level": self.education_level,
            "reading_level": self.reading_level.value,
            "books_per_year": self.books_per_year,
            "preferred_genres": self.preferred_genres,
            "disliked_genres": self.disliked_genres,
            "preferred_length": self.preferred_length,
            "reading_goals": self.reading_goals,
            "personality_traits": self.personality_traits,
            "content_sensitivities": self.content_sensitivities,
            "format_preferences": self.format_preferences,
            "discovery_methods": self.discovery_methods,
            "review_behavior": self.review_behavior,
            "social_sharing": self.social_sharing,
            "price_sensitivity": self.price_sensitivity,
            "recent_reads": self.recent_reads,
            "favorite_authors": self.favorite_authors,
            "reading_mood": self.reading_mood,
            "current_life_stage": self.current_life_stage,
            "consistency_score": self.consistency_score,
            "reliability_score": self.reliability_score,
            "created_timestamp": self.created_timestamp,
            "last_used": self.last_used,
            "usage_count": self.usage_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReaderPersona':
        """Create persona from dictionary format."""
        return cls(
            uuid=data.get("uuid", str(uuid.uuid4())),
            name=data.get("name", ""),
            age_group=AgeGroup(data.get("age_group", "adult")),
            gender=Gender(data.get("gender", "prefer_not_to_say")),
            location=data.get("location", "United States"),
            income_level=IncomeLevel(data.get("income_level", "middle")),
            education_level=data.get("education_level", "College"),
            reading_level=ReadingLevel(data.get("reading_level", "moderate")),
            books_per_year=data.get("books_per_year", 12),
            preferred_genres=data.get("preferred_genres", []),
            disliked_genres=data.get("disliked_genres", []),
            preferred_length=data.get("preferred_length", "medium"),
            reading_goals=data.get("reading_goals", ["entertainment"]),
            personality_traits=data.get("personality_traits", []),
            content_sensitivities=data.get("content_sensitivities", []),
            format_preferences=data.get("format_preferences", ["physical", "digital"]),
            discovery_methods=data.get("discovery_methods", ["recommendations", "browsing"]),
            review_behavior=data.get("review_behavior", "occasional"),
            social_sharing=data.get("social_sharing", True),
            price_sensitivity=data.get("price_sensitivity", "moderate"),
            recent_reads=data.get("recent_reads", []),
            favorite_authors=data.get("favorite_authors", []),
            reading_mood=data.get("reading_mood", "neutral"),
            current_life_stage=data.get("current_life_stage", "stable"),
            consistency_score=data.get("consistency_score", 0.8),
            reliability_score=data.get("reliability_score", 0.8),
            created_timestamp=data.get("created_timestamp", datetime.now().isoformat()),
            last_used=data.get("last_used"),
            usage_count=data.get("usage_count", 0)
        )


class ReaderPersonaFactory:
    """
    Factory for creating diverse reader personas.
    Implements Requirements 5.1 and 5.2 for generating diverse reader profiles.
    """
    
    def __init__(self):
        """Initialize the persona factory."""
        self.genre_preferences = self._load_genre_preferences()
        self.name_lists = self._load_name_lists()
        self.location_data = self._load_location_data()
        logger.info("ReaderPersonaFactory initialized")
    
    def create_random_persona(self) -> ReaderPersona:
        """Create a random reader persona with realistic characteristics."""
        # Generate basic demographics
        age_group = random.choice(list(AgeGroup))
        gender = random.choice(list(Gender))
        location = random.choice(self.location_data["locations"])
        income_level = random.choice(list(IncomeLevel))
        education_level = random.choice(self.location_data["education_levels"])
        
        # Generate reading characteristics
        reading_level = self._generate_reading_level(age_group, education_level)
        books_per_year = self._generate_books_per_year(reading_level, age_group)
        
        # Generate preferences
        preferred_genres = self._generate_genre_preferences(age_group, gender)
        disliked_genres = self._generate_genre_dislikes(preferred_genres)
        
        # Generate personality and goals
        reading_goals = self._generate_reading_goals(age_group)
        personality_traits = self._generate_personality_traits()
        content_sensitivities = self._generate_content_sensitivities(age_group)
        
        # Generate behavioral patterns
        discovery_methods = self._generate_discovery_methods(age_group)
        review_behavior = self._generate_review_behavior(personality_traits)
        
        # Generate name
        name = self._generate_name(gender)
        
        # Create persona
        persona = ReaderPersona(
            name=name,
            age_group=age_group,
            gender=gender,
            location=location,
            income_level=income_level,
            education_level=education_level,
            reading_level=reading_level,
            books_per_year=books_per_year,
            preferred_genres=preferred_genres,
            disliked_genres=disliked_genres,
            preferred_length=random.choice(["short", "medium", "long"]),
            reading_goals=reading_goals,
            personality_traits=personality_traits,
            content_sensitivities=content_sensitivities,
            format_preferences=self._generate_format_preferences(age_group),
            discovery_methods=discovery_methods,
            review_behavior=review_behavior,
            social_sharing=random.choice([True, False]),
            price_sensitivity=random.choice(["low", "moderate", "high"]),
            recent_reads=self._generate_recent_reads(preferred_genres),
            favorite_authors=self._generate_favorite_authors(preferred_genres),
            reading_mood=random.choice(["adventurous", "comfort", "challenging", "neutral"]),
            current_life_stage=self._generate_life_stage(age_group),
            consistency_score=random.uniform(0.6, 0.95),
            reliability_score=random.uniform(0.7, 0.95)
        )
        
        return persona
    
    def create_targeted_persona(self, target_demographics: Dict[str, Any]) -> ReaderPersona:
        """Create a persona targeting specific demographics."""
        # Start with random persona
        persona = self.create_random_persona()
        
        # Override with targeted characteristics
        if "age_group" in target_demographics:
            persona.age_group = AgeGroup(target_demographics["age_group"])
        
        if "gender" in target_demographics:
            persona.gender = Gender(target_demographics["gender"])
        
        if "location" in target_demographics:
            persona.location = target_demographics["location"]
        
        if "reading_level" in target_demographics:
            persona.reading_level = ReadingLevel(target_demographics["reading_level"])
        
        if "preferred_genres" in target_demographics:
            persona.preferred_genres = target_demographics["preferred_genres"]
        
        if "reading_goals" in target_demographics:
            persona.reading_goals = target_demographics["reading_goals"]
        
        # Regenerate name if gender changed
        if "gender" in target_demographics:
            persona.name = self._generate_name(persona.gender)
        
        return persona
    
    def create_diverse_panel(self, panel_size: int, 
                           diversity_config: Optional[Dict[str, Any]] = None) -> List[ReaderPersona]:
        """
        Create a diverse panel of reader personas.
        
        Args:
            panel_size: Number of personas to create
            diversity_config: Configuration for ensuring diversity
            
        Returns:
            List of diverse reader personas
        """
        if diversity_config is None:
            diversity_config = {
                "age_distribution": "balanced",
                "gender_distribution": "balanced", 
                "reading_level_distribution": "balanced",
                "genre_diversity": "high"
            }
        
        personas = []
        
        # Ensure diversity in key dimensions
        age_groups = list(AgeGroup)
        genders = list(Gender)
        reading_levels = list(ReadingLevel)
        
        for i in range(panel_size):
            if diversity_config.get("age_distribution") == "balanced":
                target_age = age_groups[i % len(age_groups)]
            else:
                target_age = random.choice(age_groups)
            
            if diversity_config.get("gender_distribution") == "balanced":
                target_gender = genders[i % len(genders)]
            else:
                target_gender = random.choice(genders)
            
            if diversity_config.get("reading_level_distribution") == "balanced":
                target_reading_level = reading_levels[i % len(reading_levels)]
            else:
                target_reading_level = random.choice(reading_levels)
            
            # Create targeted persona
            persona = self.create_targeted_persona({
                "age_group": target_age.value,
                "gender": target_gender.value,
                "reading_level": target_reading_level.value
            })
            
            personas.append(persona)
        
        # Ensure genre diversity if requested
        if diversity_config.get("genre_diversity") == "high":
            self._ensure_genre_diversity(personas)
        
        return personas
    
    def _load_genre_preferences(self) -> Dict[str, Any]:
        """Load genre preference data."""
        return {
            "popular_genres": [
                "Fiction", "Mystery", "Romance", "Science Fiction", "Fantasy",
                "Thriller", "Historical Fiction", "Literary Fiction", "Biography",
                "Self-Help", "Business", "Health", "Travel", "Cooking"
            ],
            "age_preferences": {
                AgeGroup.CHILD: ["Children's", "Picture Books", "Adventure"],
                AgeGroup.TEENAGER: ["Young Adult", "Fantasy", "Romance", "Adventure"],
                AgeGroup.YOUNG_ADULT: ["Romance", "Fantasy", "Mystery", "Self-Help"],
                AgeGroup.ADULT: ["Fiction", "Mystery", "Biography", "Business"],
                AgeGroup.ELDER: ["Historical Fiction", "Biography", "Literary Fiction"]
            },
            "gender_preferences": {
                Gender.FEMALE: ["Romance", "Mystery", "Historical Fiction", "Biography"],
                Gender.MALE: ["Thriller", "Science Fiction", "Business", "History"],
                Gender.NON_BINARY: ["Fantasy", "Science Fiction", "Literary Fiction"],
                Gender.PREFER_NOT_TO_SAY: ["Fiction", "Mystery", "Biography"]
            }
        }
    
    def _load_name_lists(self) -> Dict[str, List[str]]:
        """Load name lists for persona generation."""
        return {
            "female_names": [
                "Emma", "Olivia", "Ava", "Isabella", "Sophia", "Charlotte", "Mia", "Amelia",
                "Harper", "Evelyn", "Abigail", "Emily", "Elizabeth", "Mila", "Ella", "Avery"
            ],
            "male_names": [
                "Liam", "Noah", "Oliver", "Elijah", "William", "James", "Benjamin", "Lucas",
                "Henry", "Alexander", "Mason", "Michael", "Ethan", "Daniel", "Jacob", "Logan"
            ],
            "neutral_names": [
                "Alex", "Jordan", "Taylor", "Casey", "Riley", "Avery", "Quinn", "Sage",
                "River", "Phoenix", "Rowan", "Blake", "Cameron", "Drew", "Finley", "Hayden"
            ]
        }
    
    def _load_location_data(self) -> Dict[str, Any]:
        """Load location and demographic data."""
        return {
            "locations": [
                "United States", "Canada", "United Kingdom", "Australia", "Germany",
                "France", "Japan", "South Korea", "Brazil", "India", "Mexico", "Spain"
            ],
            "education_levels": [
                "High School", "Some College", "College", "Graduate Degree", "Professional Degree"
            ]
        }
    
    def _generate_reading_level(self, age_group: AgeGroup, education_level: str) -> ReadingLevel:
        """Generate reading level based on demographics."""
        # Base level on education
        education_mapping = {
            "High School": [ReadingLevel.BEGINNER, ReadingLevel.CASUAL],
            "Some College": [ReadingLevel.CASUAL, ReadingLevel.MODERATE],
            "College": [ReadingLevel.MODERATE, ReadingLevel.AVID],
            "Graduate Degree": [ReadingLevel.AVID, ReadingLevel.EXPERT],
            "Professional Degree": [ReadingLevel.AVID, ReadingLevel.EXPERT]
        }
        
        possible_levels = education_mapping.get(education_level, [ReadingLevel.MODERATE])
        return random.choice(possible_levels)
    
    def _generate_books_per_year(self, reading_level: ReadingLevel, age_group: AgeGroup) -> int:
        """Generate realistic books per year based on reading level and age."""
        base_ranges = {
            ReadingLevel.BEGINNER: (3, 8),
            ReadingLevel.CASUAL: (6, 15),
            ReadingLevel.MODERATE: (12, 25),
            ReadingLevel.AVID: (20, 40),
            ReadingLevel.EXPERT: (30, 60)
        }
        
        min_books, max_books = base_ranges[reading_level]
        
        # Adjust for age group
        if age_group in [AgeGroup.CHILD, AgeGroup.TEENAGER]:
            min_books = max(1, min_books - 5)
            max_books = max(min_books + 1, max_books - 10)
        elif age_group == AgeGroup.ELDER:
            min_books += 5
            max_books += 10
        
        return random.randint(min_books, max_books)
    
    def _generate_genre_preferences(self, age_group: AgeGroup, gender: Gender) -> List[str]:
        """Generate genre preferences based on demographics."""
        age_prefs = self.genre_preferences["age_preferences"].get(age_group, [])
        gender_prefs = self.genre_preferences["gender_preferences"].get(gender, [])
        popular_genres = self.genre_preferences["popular_genres"]
        
        # Combine preferences with some randomness
        candidate_genres = list(set(age_prefs + gender_prefs + popular_genres))
        
        # Select 2-5 preferred genres
        num_preferences = random.randint(2, 5)
        return random.sample(candidate_genres, min(num_preferences, len(candidate_genres)))
    
    def _generate_genre_dislikes(self, preferred_genres: List[str]) -> List[str]:
        """Generate genre dislikes that don't conflict with preferences."""
        all_genres = self.genre_preferences["popular_genres"]
        available_dislikes = [g for g in all_genres if g not in preferred_genres]
        
        # Select 0-2 disliked genres
        num_dislikes = random.randint(0, 2)
        if num_dislikes > 0 and available_dislikes:
            return random.sample(available_dislikes, min(num_dislikes, len(available_dislikes)))
        return []
    
    def _generate_reading_goals(self, age_group: AgeGroup) -> List[str]:
        """Generate reading goals based on age group."""
        all_goals = [
            "entertainment", "education", "escapism", "personal_growth",
            "professional_development", "relaxation", "social_connection"
        ]
        
        age_specific_goals = {
            AgeGroup.CHILD: ["entertainment", "education"],
            AgeGroup.TEENAGER: ["entertainment", "escapism", "social_connection"],
            AgeGroup.YOUNG_ADULT: ["entertainment", "personal_growth", "escapism"],
            AgeGroup.ADULT: ["entertainment", "professional_development", "relaxation"],
            AgeGroup.ELDER: ["entertainment", "relaxation", "education"]
        }
        
        preferred_goals = age_specific_goals.get(age_group, all_goals)
        num_goals = random.randint(1, 3)
        return random.sample(preferred_goals, min(num_goals, len(preferred_goals)))
    
    def _generate_personality_traits(self) -> List[str]:
        """Generate personality traits."""
        traits = [
            "analytical", "creative", "social", "introverted", "adventurous",
            "practical", "emotional", "logical", "optimistic", "critical"
        ]
        
        num_traits = random.randint(2, 4)
        return random.sample(traits, num_traits)
    
    def _generate_content_sensitivities(self, age_group: AgeGroup) -> List[str]:
        """Generate content sensitivities based on age."""
        all_sensitivities = [
            "violence", "sexual_content", "profanity", "religious_themes",
            "political_themes", "dark_themes", "substance_abuse"
        ]
        
        if age_group in [AgeGroup.CHILD, AgeGroup.TEENAGER]:
            # Younger readers more likely to have sensitivities
            num_sensitivities = random.randint(2, 4)
        else:
            num_sensitivities = random.randint(0, 2)
        
        if num_sensitivities > 0:
            return random.sample(all_sensitivities, min(num_sensitivities, len(all_sensitivities)))
        return []
    
    def _generate_format_preferences(self, age_group: AgeGroup) -> List[str]:
        """Generate format preferences based on age."""
        if age_group in [AgeGroup.CHILD, AgeGroup.ELDER]:
            return ["physical"]
        elif age_group in [AgeGroup.TEENAGER, AgeGroup.YOUNG_ADULT]:
            return random.choice([["digital"], ["physical"], ["physical", "digital"]])
        else:
            return random.choice([["physical"], ["digital"], ["physical", "digital"], ["audio"]])
    
    def _generate_discovery_methods(self, age_group: AgeGroup) -> List[str]:
        """Generate content discovery methods."""
        all_methods = [
            "recommendations", "browsing", "reviews", "social_media",
            "bestseller_lists", "author_following", "bookstore_staff"
        ]
        
        if age_group in [AgeGroup.TEENAGER, AgeGroup.YOUNG_ADULT]:
            preferred_methods = ["social_media", "recommendations", "reviews"]
        else:
            preferred_methods = ["recommendations", "browsing", "reviews"]
        
        # Add some random methods
        additional_methods = random.sample(
            [m for m in all_methods if m not in preferred_methods], 
            random.randint(0, 2)
        )
        
        return preferred_methods + additional_methods
    
    def _generate_review_behavior(self, personality_traits: List[str]) -> str:
        """Generate review behavior based on personality."""
        if "social" in personality_traits:
            return random.choice(["frequent", "always"])
        elif "introverted" in personality_traits:
            return random.choice(["never", "rare"])
        else:
            return random.choice(["rare", "occasional", "frequent"])
    
    def _generate_recent_reads(self, preferred_genres: List[str]) -> List[str]:
        """Generate recent reading history."""
        # Simplified - would use actual book titles in real implementation
        recent_reads = []
        for genre in preferred_genres[:3]:
            recent_reads.append(f"Recent {genre} book")
        return recent_reads
    
    def _generate_favorite_authors(self, preferred_genres: List[str]) -> List[str]:
        """Generate favorite authors based on genres."""
        # Simplified - would use actual author names in real implementation
        authors = []
        for genre in preferred_genres[:2]:
            authors.append(f"Popular {genre} author")
        return authors
    
    def _generate_life_stage(self, age_group: AgeGroup) -> str:
        """Generate life stage based on age group."""
        stage_mapping = {
            AgeGroup.CHILD: "student",
            AgeGroup.TEENAGER: "student",
            AgeGroup.YOUNG_ADULT: random.choice(["student", "career_building"]),
            AgeGroup.ADULT: random.choice(["career_building", "family_focused", "stable"]),
            AgeGroup.ELDER: random.choice(["stable", "retirement"])
        }
        
        return stage_mapping.get(age_group, "stable")
    
    def _generate_name(self, gender: Gender) -> str:
        """Generate a name based on gender."""
        if gender == Gender.FEMALE:
            return random.choice(self.name_lists["female_names"])
        elif gender == Gender.MALE:
            return random.choice(self.name_lists["male_names"])
        else:
            return random.choice(self.name_lists["neutral_names"])
    
    def _ensure_genre_diversity(self, personas: List[ReaderPersona]):
        """Ensure genre diversity across the panel."""
        all_genres = self.genre_preferences["popular_genres"]
        
        # Track genre coverage
        covered_genres = set()
        for persona in personas:
            covered_genres.update(persona.preferred_genres)
        
        # Add missing genres to personas that could reasonably like them
        missing_genres = set(all_genres) - covered_genres
        
        for genre in missing_genres:
            # Find a persona that could reasonably like this genre
            suitable_personas = [p for p in personas if len(p.preferred_genres) < 5]
            if suitable_personas:
                chosen_persona = random.choice(suitable_personas)
                chosen_persona.preferred_genres.append(genre)