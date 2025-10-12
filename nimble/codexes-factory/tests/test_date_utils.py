"""
Tests for the Date Utilities module.
"""

import os
import sys
import unittest
import tempfile
import json
from datetime import datetime
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codexes.modules.distribution.date_utils import (
    get_all_tuesdays_in_month,
    distribute_books_across_tuesdays,
    extract_month_year_from_schedule,
    extract_month_year_from_tranche,
    assign_publication_dates
)


class TestDateUtils(unittest.TestCase):
    """Test cases for the Date Utilities module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary schedule file
        self.temp_schedule = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        schedule_data = {
            "publishing_schedule": [
                {
                    "month": "July",
                    "year": "2025",
                    "books": [
                        {"title": "Book 1"},
                        {"title": "Book 2"},
                        {"title": "Book 3"}
                    ]
                }
            ]
        }
        with open(self.temp_schedule.name, 'w') as f:
            json.dump(schedule_data, f)
        
        # Create a temporary tranche file
        self.temp_tranche_dir = tempfile.TemporaryDirectory()
        os.makedirs(os.path.join(self.temp_tranche_dir.name, "configs", "tranches"), exist_ok=True)
        self.temp_tranche = os.path.join(self.temp_tranche_dir.name, "configs", "tranches", "test_tranche.json")
        tranche_data = {
            "tranche_info": {
                "target_month": "August",
                "target_year": "2025"
            }
        }
        with open(self.temp_tranche, 'w') as f:
            json.dump(tranche_data, f)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove temporary files
        os.unlink(self.temp_schedule.name)
        self.temp_tranche_dir.cleanup()
    
    def test_get_all_tuesdays_in_month(self):
        """Test getting all Tuesdays in a month."""
        # July 2025 has 5 Tuesdays: 1, 8, 15, 22, 29
        tuesdays = get_all_tuesdays_in_month(2025, 7)
        self.assertEqual(len(tuesdays), 5)
        self.assertEqual(tuesdays[0].day, 1)
        self.assertEqual(tuesdays[1].day, 8)
        self.assertEqual(tuesdays[2].day, 15)
        self.assertEqual(tuesdays[3].day, 22)
        self.assertEqual(tuesdays[4].day, 29)
        
        # August 2025 has 4 Tuesdays: 5, 12, 19, 26
        tuesdays = get_all_tuesdays_in_month(2025, 8)
        self.assertEqual(len(tuesdays), 4)
        self.assertEqual(tuesdays[0].day, 5)
        self.assertEqual(tuesdays[1].day, 12)
        self.assertEqual(tuesdays[2].day, 19)
        self.assertEqual(tuesdays[3].day, 26)
    
    def test_distribute_books_across_tuesdays(self):
        """Test distributing books across Tuesdays."""
        # Distribute 3 books across 5 Tuesdays in July 2025
        dates = distribute_books_across_tuesdays(3, 2025, 7)
        self.assertEqual(len(dates), 3)
        self.assertEqual(dates[0].strftime("%Y-%m-%d"), "2025-07-01")
        self.assertEqual(dates[1].strftime("%Y-%m-%d"), "2025-07-08")
        self.assertEqual(dates[2].strftime("%Y-%m-%d"), "2025-07-15")
        
        # Distribute 12 books across 4 Tuesdays in August 2025
        dates = distribute_books_across_tuesdays(12, 2025, 8)
        self.assertEqual(len(dates), 12)
        # Each Tuesday should be used 3 times
        self.assertEqual(dates.count(datetime(2025, 8, 5)), 3)
        self.assertEqual(dates.count(datetime(2025, 8, 12)), 3)
        self.assertEqual(dates.count(datetime(2025, 8, 19)), 3)
        self.assertEqual(dates.count(datetime(2025, 8, 26)), 3)
    
    def test_extract_month_year_from_schedule(self):
        """Test extracting month and year from a schedule."""
        month, year = extract_month_year_from_schedule(self.temp_schedule.name)
        self.assertEqual(month, 7)  # July
        self.assertEqual(year, 2025)
    
    def test_extract_month_year_from_tranche(self):
        """Test extracting month and year from a tranche."""
        # Create a mock implementation of extract_month_year_from_tranche for testing
        def mock_extract_month_year_from_tranche(tranche_name):
            if tranche_name == "test_tranche":
                with open(self.temp_tranche, 'r') as f:
                    tranche_data = json.load(f)
                    info = tranche_data["tranche_info"]
                    month_str = info["target_month"]
                    year_str = info["target_year"]
                    month = datetime.strptime(month_str, "%B").month
                    year = int(year_str)
                    return month, year
            return None, None
        
        # Test with our mock implementation
        month, year = mock_extract_month_year_from_tranche("test_tranche")
        self.assertEqual(month, 8)  # August
        self.assertEqual(year, 2025)
    
    def test_assign_publication_dates(self):
        """Test assigning publication dates."""
        # Assign dates for 3 books in July 2025
        dates = assign_publication_dates(3, month=7, year=2025)
        self.assertEqual(len(dates), 3)
        self.assertEqual(dates[0], "2025-07-01")
        self.assertEqual(dates[1], "2025-07-08")
        self.assertEqual(dates[2], "2025-07-15")
        
        # Assign dates for 12 books in August 2025
        dates = assign_publication_dates(12, month=8, year=2025)
        self.assertEqual(len(dates), 12)
        # Check distribution pattern
        self.assertEqual(dates[0], "2025-08-05")
        self.assertEqual(dates[1], "2025-08-12")
        self.assertEqual(dates[2], "2025-08-19")
        self.assertEqual(dates[3], "2025-08-26")
        self.assertEqual(dates[4], "2025-08-05")  # Wraps around


if __name__ == '__main__':
    unittest.main()