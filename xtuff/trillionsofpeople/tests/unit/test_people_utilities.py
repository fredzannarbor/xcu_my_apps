"""
Unit tests for people utilities module.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import json

from trillions_of_people.modules.people_utilities import PeopleManager


class TestPeopleManager:
    """Test cases for PeopleManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def people_manager(self, temp_dir):
        """Create PeopleManager instance with temporary directory."""
        return PeopleManager(data_dir=temp_dir)

    def test_init_creates_data_dir(self, temp_dir):
        """Test that initialization creates data directory."""
        data_path = Path(temp_dir) / "test_data"
        manager = PeopleManager(data_dir=str(data_path))
        assert data_path.exists()

    def test_load_countries_with_file(self, people_manager, temp_dir):
        """Test loading countries from CSV file."""
        # Create test countries file
        countries_file = Path(temp_dir) / "country.csv"
        countries_data = "United States,US\nCanada,CA\nGermany,DE"
        countries_file.write_text(countries_data)

        countries = people_manager.load_countries()
        assert "United States" in countries
        assert countries["United States"] == "US"
        assert countries["Canada"] == "CA"

    def test_load_countries_without_file(self, people_manager):
        """Test loading countries when file doesn't exist."""
        countries = people_manager.load_countries()
        assert isinstance(countries, dict)
        assert "United States" in countries
        assert "Random" in countries

    def test_browse_people_empty(self, people_manager):
        """Test browsing people when no data exists."""
        df = people_manager.browse_people()
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_browse_people_with_data(self, people_manager, temp_dir):
        """Test browsing people with existing data."""
        # Create test people file
        people_file = Path(temp_dir) / "people.csv"
        test_data = "name,age,country\nJohn Doe,30,US\nJane Smith,25,CA"
        people_file.write_text(test_data)

        df = people_manager.browse_people()
        assert not df.empty
        assert len(df) == 2
        assert "John Doe" in df["name"].values

    def test_browse_people_with_limit(self, people_manager, temp_dir):
        """Test browsing people with limit."""
        # Create test people file with multiple records
        people_file = Path(temp_dir) / "people.csv"
        test_data = "name,age\nPerson1,20\nPerson2,30\nPerson3,40\nPerson4,50"
        people_file.write_text(test_data)

        df = people_manager.browse_people(limit=2)
        assert len(df) == 2

    @patch('trillions_of_people.modules.people_utilities.TrillionsLLMCaller')
    def test_create_new_people_success(self, mock_llm_caller, people_manager):
        """Test successful people generation."""
        # Mock LLM response
        mock_instance = Mock()
        mock_llm_caller.return_value = mock_instance
        mock_instance.generate_personas.return_value = [
            {
                "name": "Test Person",
                "age": 30,
                "gender": "Female",
                "occupation": "Teacher",
                "country": "US",
                "family_situation": "Single",
                "education": "Bachelor's",
                "economic_status": "Middle class",
                "personality_traits": ["Kind", "Patient"],
                "life_challenges": ["Work stress"],
                "cultural_background": "American",
                "notable_events": ["Graduated college"]
            }
        ]

        people_df, card_df = people_manager.create_new_people(
            country="United States",
            country_code="US",
            count=1,
            target_year=2024,
            api_key="test-key"
        )

        assert not people_df.empty
        assert not card_df.empty
        assert people_df.iloc[0]["name"] == "Test Person"
        assert "Attributes" in card_df.columns
        assert "Values" in card_df.columns

    @patch('trillions_of_people.modules.people_utilities.TrillionsLLMCaller')
    def test_create_new_people_llm_error(self, mock_llm_caller, people_manager):
        """Test people generation with LLM error."""
        # Mock LLM to raise error
        mock_instance = Mock()
        mock_llm_caller.return_value = mock_instance
        mock_instance.generate_personas.side_effect = Exception("API Error")

        people_df, card_df = people_manager.create_new_people(
            country="United States",
            country_code="US",
            count=1,
            target_year=2024,
            api_key="test-key"
        )

        assert people_df.empty
        assert card_df.empty

    def test_calculate_birth_year(self, people_manager):
        """Test birth year calculation."""
        assert people_manager._calculate_birth_year(30, 2024) == 1994
        assert people_manager._calculate_birth_year("invalid", 2024) == 1994  # Default

    def test_format_traits(self, people_manager):
        """Test trait formatting."""
        assert people_manager._format_traits(["Kind", "Smart"]) == "Kind, Smart"
        assert people_manager._format_traits("Single trait") == "Single trait"
        assert people_manager._format_traits([]) == ""
        assert people_manager._format_traits(None) == "Unknown"

    def test_save_people(self, people_manager, temp_dir):
        """Test saving people data."""
        test_df = pd.DataFrame({
            "name": ["Test Person"],
            "age": [30],
            "country": ["US"]
        })

        success = people_manager.save_people(test_df, backup=False)
        assert success

        # Check file was created
        people_file = Path(temp_dir) / "people.csv"
        assert people_file.exists()

        # Check content
        saved_df = pd.read_csv(people_file)
        assert len(saved_df) == 1
        assert saved_df.iloc[0]["name"] == "Test Person"

    def test_create_display_card_empty_df(self, people_manager):
        """Test creating display card with empty DataFrame."""
        empty_df = pd.DataFrame()
        card_df = people_manager._create_display_card(empty_df)
        assert card_df.empty

    def test_personas_to_dataframe_with_error(self, people_manager):
        """Test persona to DataFrame conversion with error data."""
        personas_with_error = [
            {"error": "Parsing failed", "raw_content": "Invalid JSON"},
            {"name": "Valid Person", "age": 25}
        ]

        df = people_manager._personas_to_dataframe(personas_with_error, "US", 2024)
        assert len(df) == 1  # Only valid persona should be processed
        assert df.iloc[0]["name"] == "Valid Person"


@pytest.fixture
def mock_countries():
    """Mock countries data for testing."""
    return {
        "United States": "US",
        "Canada": "CA",
        "Random": "RANDOM"
    }


class TestPeopleManagerIntegration:
    """Integration tests for PeopleManager."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary directory with test data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sample countries file
            countries_file = Path(tmpdir) / "country.csv"
            countries_file.write_text("United States,US\nCanada,CA\nGermany,DE")

            # Create sample people file
            people_file = Path(tmpdir) / "people.csv"
            people_data = """name,age,gender,born,country,occupation
John Doe,30,Male,1994,US,Engineer
Jane Smith,25,Female,1999,CA,Teacher"""
            people_file.write_text(people_data)

            yield tmpdir

    def test_full_workflow(self, temp_data_dir):
        """Test complete workflow from loading to saving."""
        manager = PeopleManager(data_dir=temp_data_dir)

        # Test loading
        countries = manager.load_countries()
        assert len(countries) == 3

        people_df = manager.browse_people()
        assert len(people_df) == 2

        # Test creating display card
        card_df = manager._create_display_card(people_df)
        assert not card_df.empty
        assert "Attributes" in card_df.columns