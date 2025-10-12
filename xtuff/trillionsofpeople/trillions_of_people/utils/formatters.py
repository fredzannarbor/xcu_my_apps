"""Output formatting utilities."""

import csv
import json
import random
from io import StringIO
from typing import List, Dict, Any
from ..core.models import Person

try:
    import gibberish as gib
    gib_generator = gib.Gibberish()
except ImportError:
    gib_generator = None

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def format_person_csv(people: List[Person]) -> str:
    """Format list of Person objects as CSV string."""
    if not people:
        return ""
    
    output = StringIO()
    fieldnames = [
        'name', 'birth_year', 'gender', 'species', 'timeline', 'realness',
        'latitude', 'longitude', 'nearest_city', 'country', 'backstory',
        'four_words_name', 'image_url', 'source', 'status'
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for person in people:
        row = {
            'name': person.name,
            'birth_year': person.birth_year,
            'gender': person.gender,
            'species': person.species.value if hasattr(person.species, 'value') else person.species,
            'timeline': person.timeline.value if hasattr(person.timeline, 'value') else person.timeline,
            'realness': person.realness.value if hasattr(person.realness, 'value') else person.realness,
            'latitude': person.latitude,
            'longitude': person.longitude,
            'nearest_city': person.nearest_city,
            'country': person.country,
            'backstory': person.backstory,
            'four_words_name': person.four_words_name,
            'image_url': person.image_url,
            'source': person.source,
            'status': person.status,
        }
        writer.writerow(row)
    
    return output.getvalue()


def format_person_json(people: List[Person]) -> str:
    """Format list of Person objects as JSON string."""
    data = []
    for person in people:
        person_dict = {
            'name': person.name,
            'birth_year': person.birth_year,
            'gender': person.gender,
            'species': person.species.value if hasattr(person.species, 'value') else person.species,
            'timeline': person.timeline.value if hasattr(person.timeline, 'value') else person.timeline,
            'realness': person.realness.value if hasattr(person.realness, 'value') else person.realness,
            'latitude': person.latitude,
            'longitude': person.longitude,
            'nearest_city': person.nearest_city,
            'country': person.country,
            'backstory': person.backstory,
            'four_words_name': person.four_words_name,
            'image_url': person.image_url,
            'ocean_tuple': person.ocean_tuple,
            'source': person.source,
            'status': person.status,
        }
        data.append(person_dict)
    
    return json.dumps(data, indent=2, ensure_ascii=False)


def create_shortname(species: str) -> str:
    """Create a short name based on species."""
    if gib_generator:
        if species == 'sapiens':
            shortname = gib_generator.generate_word()
        elif species == 'neanderthalensis':
            shortname = gib_generator.generate_word(start_vowel=False)
        else:
            shortname = gib_generator.generate_word()
        return shortname.title()
    else:
        # Fallback when gibberish is not available
        fallback_names = [
            'Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Avery', 'Quinn',
            'Sage', 'River', 'Phoenix', 'Rowan', 'Skyler', 'Cameron', 'Dakota', 'Emery'
        ]
        return random.choice(fallback_names)


def fourwordsname() -> str:
    """Generate a four-words name in the format adjective-noun-verb-adverb."""
    try:
        # Try to read word lists from the original location
        import os
        base_path = 'app/utilities/moby_pos'
        
        if os.path.exists(f'{base_path}/adjectives_clean.txt'):
            with open(f'{base_path}/adjectives_clean.txt') as f:
                adjectives = [line.strip() for line in f.readlines()]
            with open(f'{base_path}/nouns_clean.txt') as f:
                nouns = [line.strip() for line in f.readlines()]
            with open(f'{base_path}/verbs_clean.txt') as f:
                verbs = [line.strip() for line in f.readlines()]
            with open(f'{base_path}/adverbs_clean.txt') as f:
                adverbs = [line.strip() for line in f.readlines()]
            
            # Filter for reasonable length words
            short_adjectives = [word for word in adjectives if 4 < len(word) < 9]
            
            adjective = random.choice(short_adjectives) if short_adjectives else random.choice(adjectives)
            noun = random.choice(nouns)
            verb = random.choice(verbs)
            adverb = random.choice(adverbs)
            
            return f"{adjective}-{noun}-{verb}-{adverb}"
            
    except (FileNotFoundError, IOError):
        pass
    
    # Fallback word lists when files are not available
    adjectives = ['bright', 'clever', 'gentle', 'swift', 'bold', 'wise', 'kind', 'brave']
    nouns = ['river', 'mountain', 'forest', 'ocean', 'star', 'moon', 'sun', 'wind']
    verbs = ['dancing', 'singing', 'running', 'flying', 'swimming', 'climbing', 'jumping', 'walking']
    adverbs = ['gracefully', 'quietly', 'swiftly', 'boldly', 'gently', 'proudly', 'calmly', 'freely']
    
    adjective = random.choice(adjectives)
    noun = random.choice(nouns)
    verb = random.choice(verbs)
    adverb = random.choice(adverbs)
    
    return f"{adjective}-{noun}-{verb}-{adverb}"


def format_person_parquet(people: List[Person], output_path: str) -> None:
    """Format list of Person objects as Parquet file."""
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required for Parquet export. Install with: pip install pandas[parquet]")
    
    if not people:
        # Create empty DataFrame with correct schema
        df = pd.DataFrame(columns=[
            'name', 'birth_year', 'gender', 'species', 'timeline', 'realness',
            'latitude', 'longitude', 'nearest_city', 'country', 'backstory',
            'four_words_name', 'image_url', 'source', 'status'
        ])
    else:
        data = []
        for person in people:
            row = {
                'name': person.name,
                'birth_year': person.birth_year,
                'gender': person.gender,
                'species': person.species.value if hasattr(person.species, 'value') else person.species,
                'timeline': person.timeline.value if hasattr(person.timeline, 'value') else person.timeline,
                'realness': person.realness.value if hasattr(person.realness, 'value') else person.realness,
                'latitude': person.latitude,
                'longitude': person.longitude,
                'nearest_city': person.nearest_city,
                'country': person.country,
                'backstory': person.backstory,
                'four_words_name': person.four_words_name,
                'image_url': person.image_url,
                'source': person.source,
                'status': person.status,
            }
            data.append(row)
        
        df = pd.DataFrame(data)
    
    df.to_parquet(output_path, index=False)


def load_people_from_csv(file_path: str) -> List[Person]:
    """Load people data from CSV file."""
    from ..core.models import Person, Species, Timeline, Realness
    
    people = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle enum fields
            species = Species(row.get('species', 'sapiens'))
            timeline = Timeline(row.get('timeline', 'ours'))
            realness = Realness(row.get('realness', 'synthetic'))
            
            # Handle numeric fields
            birth_year = int(row.get('birth_year', 2100))
            latitude = float(row['latitude']) if row.get('latitude') and row['latitude'].strip() else None
            longitude = float(row['longitude']) if row.get('longitude') and row['longitude'].strip() else None
            
            person = Person(
                name=row.get('name', ''),
                birth_year=birth_year,
                gender=row.get('gender', ''),
                species=species,
                timeline=timeline,
                realness=realness,
                latitude=latitude,
                longitude=longitude,
                nearest_city=row.get('nearest_city', ''),
                country=row.get('country', ''),
                backstory=row.get('backstory', ''),
                four_words_name=row.get('four_words_name', ''),
                image_url=row.get('image_url', ''),
                source=row.get('source', 'trillions_of_people'),
                status=row.get('status', 'active'),
            )
            people.append(person)
    
    return people


def load_people_from_json(file_path: str) -> List[Person]:
    """Load people data from JSON file."""
    from ..core.models import Person, Species, Timeline, Realness
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    people = []
    for item in data:
        # Handle enum fields
        species = Species(item.get('species', 'sapiens'))
        timeline = Timeline(item.get('timeline', 'ours'))
        realness = Realness(item.get('realness', 'synthetic'))
        
        person = Person(
            name=item.get('name', ''),
            birth_year=item.get('birth_year', 2100),
            gender=item.get('gender', ''),
            species=species,
            timeline=timeline,
            realness=realness,
            latitude=item.get('latitude'),
            longitude=item.get('longitude'),
            nearest_city=item.get('nearest_city', ''),
            country=item.get('country', ''),
            backstory=item.get('backstory', ''),
            four_words_name=item.get('four_words_name', ''),
            image_url=item.get('image_url', ''),
            source=item.get('source', 'trillions_of_people'),
            status=item.get('status', 'active'),
        )
        people.append(person)
    
    return people