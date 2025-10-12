"""
Modernized people utilities for generating and managing synthetic personas.
Replaces the legacy classes/SyntheticPeople/PeopleUtilities.py module.
"""

import csv
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

from ..core.llm_caller import TrillionsLLMCaller, PersonaGenerationRequest
from ..core.logging_config import get_logger

logger = get_logger(__name__)


class PeopleManager:
    """Modern people management with improved data handling."""

    def __init__(self, data_dir: str = "people_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.people_file = self.data_dir / "people.csv"
        self.countries_file = self.data_dir / "country.csv"

    def load_countries(self) -> Dict[str, str]:
        """Load available countries from CSV file."""
        try:
            if self.countries_file.exists():
                countries_df = pd.read_csv(
                    self.countries_file,
                    names=['country_name', 'code'],
                    index_col=0
                )
                return countries_df.to_dict()['code']
            else:
                logger.warning(f"Countries file {self.countries_file} not found")
                return self._get_default_countries()
        except Exception as e:
            logger.error(f"Error loading countries data: {e}")
            return self._get_default_countries()

    def _get_default_countries(self) -> Dict[str, str]:
        """Return default country list if file is not available."""
        return {
            "United States": "US",
            "United Kingdom": "GB",
            "Canada": "CA",
            "Australia": "AU",
            "Germany": "DE",
            "France": "FR",
            "Japan": "JP",
            "China": "CN",
            "India": "IN",
            "Brazil": "BR",
            "Random": "RANDOM"
        }

    def browse_people(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Load and return people data as DataFrame."""
        try:
            if self.people_file.exists():
                df = pd.read_csv(self.people_file)
                if limit:
                    df = df.head(limit)
                logger.info(f"Loaded {len(df)} people from database")
                return df
            else:
                logger.warning("People file not found, returning empty DataFrame")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading people data: {e}")
            return pd.DataFrame()

    def create_new_people(
        self,
        country: str,
        country_code: str,
        count: int,
        target_year: int,
        latitude: float = 0.0,
        longitude: float = 0.0,
        nearest_city: str = "Unknown",
        birth_year: Optional[int] = None,
        api_key: Optional[str] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate new synthetic people using modern LLM integration.

        Returns:
            Tuple of (people_dataframe, display_card_dataframe)
        """
        try:
            # Initialize LLM caller
            llm_caller = TrillionsLLMCaller(api_key=api_key)

            # Create generation request
            request = PersonaGenerationRequest(
                country=country,
                year=birth_year or target_year,
                count=count,
                additional_context=f"Coordinates: {latitude}, {longitude}. Nearest city: {nearest_city}"
            )

            # Generate personas
            personas = llm_caller.generate_personas(request)

            # Convert to DataFrame format
            people_df = self._personas_to_dataframe(personas, country_code, target_year)

            # Create display card
            card_df = self._create_display_card(people_df)

            logger.info(f"Successfully generated {len(people_df)} people")
            return people_df, card_df

        except Exception as e:
            logger.error(f"Error creating new people: {e}")
            # Return empty DataFrames on error
            return pd.DataFrame(), pd.DataFrame()

    def _personas_to_dataframe(
        self,
        personas: List[Dict[str, Any]],
        country_code: str,
        target_year: int
    ) -> pd.DataFrame:
        """Convert LLM-generated personas to standardized DataFrame format."""

        standardized_records = []

        for persona in personas:
            # Handle potential parsing errors
            if "error" in persona or "parsing_failed" in persona:
                logger.warning(f"Skipping malformed persona: {persona}")
                continue

            record = {
                "name": persona.get("name", "Unknown"),
                "age": persona.get("age", 30),
                "gender": persona.get("gender", "Unknown"),
                "born": self._calculate_birth_year(persona.get("age", 30), target_year),
                "country": persona.get("country", country_code),
                "occupation": persona.get("occupation", "Unknown"),
                "family_situation": persona.get("family_situation", "Unknown"),
                "education": persona.get("education", "Unknown"),
                "economic_status": persona.get("economic_status", "Unknown"),
                "personality_traits": self._format_traits(persona.get("personality_traits", [])),
                "life_challenges": self._format_challenges(persona.get("life_challenges", [])),
                "cultural_background": persona.get("cultural_background", "Unknown"),
                "notable_events": self._format_events(persona.get("notable_events", [])),
                "generated_year": target_year,
                "invisible_comments": json.dumps(persona)  # Store full data for reference
            }

            standardized_records.append(record)

        return pd.DataFrame(standardized_records)

    def _calculate_birth_year(self, age: int, current_year: int) -> int:
        """Calculate birth year from age and current year."""
        try:
            return current_year - int(age)
        except (ValueError, TypeError):
            return current_year - 30  # Default age

    def _format_traits(self, traits) -> str:
        """Format personality traits as comma-separated string."""
        if isinstance(traits, list):
            return ", ".join(str(trait) for trait in traits)
        return str(traits) if traits else "Unknown"

    def _format_challenges(self, challenges) -> str:
        """Format life challenges as comma-separated string."""
        if isinstance(challenges, list):
            return ", ".join(str(challenge) for challenge in challenges)
        return str(challenges) if challenges else "None specified"

    def _format_events(self, events) -> str:
        """Format notable events as comma-separated string."""
        if isinstance(events, list):
            return ", ".join(str(event) for event in events)
        return str(events) if events else "None specified"

    def _create_display_card(self, people_df: pd.DataFrame) -> pd.DataFrame:
        """Create a display card DataFrame from people data."""
        if people_df.empty:
            return pd.DataFrame()

        # Select first person for display
        person = people_df.iloc[0]

        # Create card format
        attributes = []
        values = []

        display_fields = [
            ("Name", "name"),
            ("Age", "age"),
            ("Gender", "gender"),
            ("Born", "born"),
            ("Country", "country"),
            ("Occupation", "occupation"),
            ("Family", "family_situation"),
            ("Education", "education"),
            ("Economic Status", "economic_status"),
            ("Personality", "personality_traits"),
            ("Life Challenges", "life_challenges"),
            ("Cultural Background", "cultural_background"),
            ("Notable Events", "notable_events")
        ]

        for label, field in display_fields:
            attributes.append(label)
            values.append(person.get(field, "Unknown"))

        return pd.DataFrame({
            "Attributes": attributes,
            "Values": values
        })

    def save_people(self, people_df: pd.DataFrame, backup: bool = True) -> bool:
        """Save people DataFrame to CSV file."""
        try:
            if backup and self.people_file.exists():
                backup_file = self.people_file.with_suffix('.backup.csv')
                self.people_file.rename(backup_file)
                logger.info(f"Created backup at {backup_file}")

            people_df.to_csv(
                self.people_file,
                mode='a' if self.people_file.exists() else 'w',
                header=not self.people_file.exists(),
                index=False,
                quoting=csv.QUOTE_ALL
            )

            logger.info(f"Saved {len(people_df)} people to {self.people_file}")
            return True

        except Exception as e:
            logger.error(f"Error saving people data: {e}")
            return False