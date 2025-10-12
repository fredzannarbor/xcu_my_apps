
'''
Classes for Scenario Operation
'''
import pandas as pd
import random
import logging
from typing import Tuple, Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_scenario_personas(scenario: str, n: int, target_year: int, country: str, 
                           peopledf_columns: List[str], countries: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create synthetic personas for a given scenario.
    
    Args:
        scenario: Scenario identifier
        n: Number of personas to generate
        target_year: Birth year for personas
        country: Country for geographic placement
        peopledf_columns: List of DataFrame column names
        countries: Dictionary containing country data
        
    Returns:
        Tuple of (scenario_personas_df, card_df)
    """
    # Set pandas option once, outside the loop
    pd.set_option('display.max_colwidth', 70)
    
    scenario_personas_data = []
    card_columns = ['Attributes']
    card_df = pd.DataFrame(columns=card_columns)
    card_df['Attributes'] = peopledf_columns
    
    # Store the last persona's values for the card_df
    last_persona_values = []
    
    for person in range(n):
        try:
            values = []
            
            # Check if country exists in countries dictionary
            if country not in countries:
                logger.warning(f"Country {country} not found in countries data. Using default location.")
                latitude, longitude, nearest_city = 0.0, 0.0, "Unknown City"
            else:
                latitude, longitude, nearest_city = random_spot(countries[country])
            
            species = 'sapiens'
            gender = random.choice(['male', 'female'])
            shortname = create_shortname(species)
            year_of_birth_in_CE = target_year
            thisperson4name = fourwordsname()
            timeline = 'ours'
            realness = 'synthetic'  # ['synthetic', 'authenticated', 'fictional']
            backstory = ""
            
            # Generate backstory with error handling
            try:
                prompt = f'Biographical details: {gender}: {country}'
                backstory_response = gpt3complete(scenario, prompt, 'trillions')
                if backstory_response and len(backstory_response) > 0 and 'choices' in backstory_response[0]:
                    backstory = backstory_response[0]['choices'][0]['text']
                else:
                    backstory = f"A {gender} person from {country} born in {target_year}."
            except Exception as e:
                logger.error(f"Failed to generate backstory for persona {person}: {e}")
                backstory = f"A {gender} person from {country} born in {target_year}."
            
            # Generate image with error handling
            try:
                image_uri = f'<img src="{fetch_fake_face_api(gender)}" height=90>'
            except Exception as e:
                logger.error(f"Failed to generate image for persona {person}: {e}")
                image_uri = f'<img src="placeholder_{gender}.jpg" height=90>'
            
            source = scenario
            comments = ""
            status = 'Register | Edit | Claim '
            
            values = [shortname, image_uri, year_of_birth_in_CE, gender, species, timeline, realness, 
                     latitude, longitude, nearest_city, country, backstory, thisperson4name, source, 
                     comments, status]
            
            # Ensure values list matches the length of peopledf_columns
            if len(values) != len(peopledf_columns):
                logger.warning(f"Values length ({len(values)}) doesn't match columns length ({len(peopledf_columns)})")
                # Pad or truncate values to match columns
                if len(values) < len(peopledf_columns):
                    values.extend([''] * (len(peopledf_columns) - len(values)))
                else:
                    values = values[:len(peopledf_columns)]
            
            scenario_personas_dict = dict(zip(peopledf_columns, values))
            scenario_personas_data.append(scenario_personas_dict)
            
            # Store the last persona's values for card_df
            last_persona_values = values
            
        except Exception as e:
            logger.error(f"Failed to generate persona {person}: {e}")
            continue
    
    # Set the card_df values to the last generated persona (or empty if none generated)
    if last_persona_values:
        card_df["Values"] = last_persona_values
    else:
        card_df["Values"] = [''] * len(peopledf_columns)
    
    scenario_personas_df = pd.DataFrame(scenario_personas_data, columns=peopledf_columns)
    
    return scenario_personas_df, card_df


def create_scenario_personas_safe(scenario: str, n: int, target_year: int, country: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Safe wrapper for create_scenario_personas that handles missing dependencies.
    This function should be called from the main application where peopledf_columns and countries are available.
    """
    try:
        # These should be imported or passed from the calling module
        from trillionsofpeople import peopledf_columns, countries
        return create_scenario_personas(scenario, n, target_year, country, peopledf_columns, countries)
    except ImportError as e:
        logger.error(f"Missing required dependencies: {e}")
        # Return empty DataFrames as fallback
        empty_df = pd.DataFrame()
        return empty_df, empty_df
    except Exception as e:
        logger.error(f"Unexpected error in create_scenario_personas_safe: {e}")
        empty_df = pd.DataFrame()
        return empty_df, empty_df
