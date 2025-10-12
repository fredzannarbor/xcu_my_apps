#!/usr/bin/env python3
"""
Example usage of the refactored people generation services.

This example demonstrates how to use the new service-based architecture
for generating synthetic people data.
"""

import os
import sys

# Add the package to the path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from trillions_of_people import PeopleGenerator, Config, ConfigManager


def main():
    """Demonstrate service usage."""
    print("TrillionsOfPeople Service Usage Example")
    print("=" * 40)
    
    # Create configuration
    config = Config(
        openai_api_key=os.getenv('OPENAI_API_KEY'),  # Optional
        default_country="US",
        default_year=2024,
        max_people_per_request=10,
        enable_image_generation=True,
        log_level="INFO"
    )
    
    # Initialize the people generator
    generator = PeopleGenerator(config)
    
    print(f"\n1. Generating a single person from {config.default_country}:")
    person = generator.generate_single_person(2024, "US", gender="female")
    print(f"   Name: {person.name}")
    print(f"   Birth Year: {person.birth_year}")
    print(f"   Gender: {person.gender}")
    print(f"   Location: {person.nearest_city} ({person.latitude}, {person.longitude})")
    print(f"   Backstory: {person.backstory[:100]}...")
    
    print(f"\n2. Generating multiple people from different countries:")
    countries = ["CA", "GB", "FR", "JP"]
    for country in countries:
        try:
            people = generator.generate_people(2, 2025, country)
            print(f"   {country}: Generated {len(people)} people")
            for p in people:
                print(f"     - {p.name} from {p.nearest_city}")
        except Exception as e:
            print(f"   {country}: Error - {e}")
    
    print(f"\n3. Testing service availability:")
    print(f"   LLM Service: {'✓' if generator.llm_service.is_available() else '✗'}")
    print(f"   Geo Service: {'✓' if generator.geo_service.is_available() else '✗'}")
    print(f"   Image Service: {'✓' if generator.image_service.is_available() else '✗'}")
    
    print(f"\n4. Generating historical and future people:")
    # Historical person (BCE)
    historical = generator.generate_single_person(-500, "IT", gender="male")
    print(f"   Historical: {historical.name} from ancient {historical.country}")
    
    # Future person
    future = generator.generate_single_person(2100, "Random", gender="female")
    print(f"   Future: {future.name} from {future.nearest_city} in 2100")
    
    print("\n✓ Example completed successfully!")


if __name__ == "__main__":
    main()