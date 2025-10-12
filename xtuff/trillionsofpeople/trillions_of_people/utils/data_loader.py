"""Data loading utilities."""

import csv
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from functools import lru_cache

from ..core.models import Country, Person
from ..core.exceptions import DataError, ValidationError
from .validators import validate_country_data, validate_person_data


class DataLoader:
    """Utility class for loading and caching data files."""
    
    def __init__(self, data_directory: str = "data"):
        """Initialize data loader with data directory."""
        self.data_directory = Path(data_directory)
        if not self.data_directory.exists():
            self.data_directory.mkdir(parents=True, exist_ok=True)
    
    @lru_cache(maxsize=1)
    def load_countries(self) -> Dict[str, Country]:
        """
        Load country data from CSV file with caching.
        
        Returns:
            Dict[str, Country]: Dictionary mapping country names to Country objects
            
        Raises:
            DataError: If loading fails
        """
        try:
            countries = {}
            country_file = self.data_directory / "countries.csv"
            
            if not country_file.exists():
                # Create default countries file if it doesn't exist
                self._create_default_countries_file(country_file)
            
            with open(country_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for line_num, row in enumerate(reader, 1):
                    if len(row) >= 2:
                        name = row[0].strip()
                        code = row[1].strip()
                        
                        if name and code:  # Skip empty rows
                            try:
                                country = validate_country_data({
                                    'name': name,
                                    'code': code
                                })
                                countries[name] = country
                            except ValidationError as e:
                                # Log warning but continue processing
                                print(f"Warning: Invalid country data at line {line_num}: {e}")
                                continue
            
            return countries
        except Exception as e:
            raise DataError(f"Failed to load countries data: {e}")
    
    def get_country_by_name(self, name: str) -> Optional[Country]:
        """
        Get country by name.
        
        Args:
            name: Country name to search for
            
        Returns:
            Optional[Country]: Country object if found, None otherwise
        """
        countries = self.load_countries()
        return countries.get(name)
    
    def get_country_by_code(self, code: str) -> Optional[Country]:
        """
        Get country by ISO code.
        
        Args:
            code: ISO country code to search for
            
        Returns:
            Optional[Country]: Country object if found, None otherwise
        """
        countries = self.load_countries()
        for country in countries.values():
            if country.code == code.upper():
                return country
        return None
    
    def get_all_country_names(self) -> List[str]:
        """
        Get list of all country names.
        
        Returns:
            List[str]: List of country names
        """
        countries = self.load_countries()
        return list(countries.keys())
    
    def get_all_country_codes(self) -> List[str]:
        """
        Get list of all country codes.
        
        Returns:
            List[str]: List of country codes
        """
        countries = self.load_countries()
        return [country.code for country in countries.values()]
    
    def load_json_data(self, filename: str) -> Dict[str, Any]:
        """
        Load JSON data from file.
        
        Args:
            filename: Name of JSON file to load
            
        Returns:
            Dict[str, Any]: Loaded JSON data
            
        Raises:
            DataError: If loading fails
        """
        try:
            file_path = self.data_directory / filename
            if not file_path.exists():
                raise DataError(f"File not found: {filename}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise DataError(f"Invalid JSON in {filename}: {e}")
        except Exception as e:
            raise DataError(f"Failed to load {filename}: {e}")
    
    def save_json_data(self, data: Dict[str, Any], filename: str) -> None:
        """
        Save data to JSON file.
        
        Args:
            data: Data to save
            filename: Name of JSON file to save to
            
        Raises:
            DataError: If saving fails
        """
        try:
            file_path = self.data_directory / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise DataError(f"Failed to save {filename}: {e}")
    
    def load_people_from_csv(self, filename: str) -> List[Person]:
        """
        Load people data from CSV file.
        
        Args:
            filename: Name of CSV file to load
            
        Returns:
            List[Person]: List of validated Person objects
            
        Raises:
            DataError: If loading fails
        """
        try:
            file_path = self.data_directory / filename
            if not file_path.exists():
                raise DataError(f"File not found: {filename}")
            
            people = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for line_num, row in enumerate(reader, 2):  # Start at 2 for header
                    try:
                        # Convert string values to appropriate types
                        processed_row = self._process_csv_row(row)
                        person = validate_person_data(processed_row)
                        people.append(person)
                    except ValidationError as e:
                        print(f"Warning: Invalid person data at line {line_num}: {e}")
                        continue
            
            return people
        except Exception as e:
            raise DataError(f"Failed to load people from {filename}: {e}")
    
    def save_people_to_csv(self, people: List[Person], filename: str) -> None:
        """
        Save people data to CSV file.
        
        Args:
            people: List of Person objects to save
            filename: Name of CSV file to save to
            
        Raises:
            DataError: If saving fails
        """
        try:
            file_path = self.data_directory / filename
            
            if not people:
                raise DataError("No people data to save")
            
            # Get all field names from the first person
            fieldnames = list(people[0].dict().keys())
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for person in people:
                    # Convert Person object to dictionary
                    row = person.dict()
                    # Handle tuple fields
                    if row.get('ocean_tuple'):
                        row['ocean_tuple'] = str(row['ocean_tuple'])
                    writer.writerow(row)
                    
        except Exception as e:
            raise DataError(f"Failed to save people to {filename}: {e}")
    
    def _process_csv_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """
        Process CSV row data, converting string values to appropriate types.
        
        Args:
            row: Raw CSV row data
            
        Returns:
            Dict[str, Any]: Processed row data
        """
        processed = {}
        
        for key, value in row.items():
            if not value or value.strip() == '':
                processed[key] = None
                continue
                
            # Convert specific fields to appropriate types
            if key == 'birth_year':
                try:
                    processed[key] = int(value)
                except ValueError:
                    processed[key] = None
            elif key in ['latitude', 'longitude']:
                try:
                    processed[key] = float(value)
                except ValueError:
                    processed[key] = None
            elif key == 'ocean_tuple':
                try:
                    # Parse tuple string representation
                    if value.startswith('(') and value.endswith(')'):
                        tuple_str = value[1:-1]  # Remove parentheses
                        if tuple_str:
                            processed[key] = tuple(float(x.strip()) for x in tuple_str.split(','))
                        else:
                            processed[key] = None
                    else:
                        processed[key] = None
                except ValueError:
                    processed[key] = None
            else:
                processed[key] = value.strip()
        
        return processed
    
    def _create_default_countries_file(self, file_path: Path) -> None:
        """
        Create a default countries.csv file with basic country data.
        
        Args:
            file_path: Path where to create the file
        """
        default_countries = [
            ("Random", "RD"),
            ("United States of America", "US"),
            ("United Kingdom", "GB"),
            ("Germany", "DE"),
            ("France", "FR"),
            ("Japan", "JP"),
            ("China", "CN"),
            ("India", "IN"),
            ("Brazil", "BR"),
            ("Canada", "CA"),
            ("Australia", "AU"),
        ]
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for name, code in default_countries:
                writer.writerow([name, code])
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self.load_countries.cache_clear()