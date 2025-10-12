#!/usr/bin/env python3
"""
Unit tests for countable-task functionality (behavior counters)
Tests the countable task system including counter creation, incrementing, and tracking
"""

import unittest
import sys
import os
import tempfile
import sqlite3
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_extensions import DatabaseExtensions
from behavior_counter_manager import BehaviorCounterManager


class TestCountableTasks(unittest.TestCase):
    """Test cases for countable task functionality (behavior counters)"""
    
    def setUp(self):
        """Set up test fixtures with temporary database"""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Initialize database extensions with temp database
        self.db_ext = DatabaseExtensions(self.temp_db.name)
        self.counter_manager = BehaviorCounterManager(self.temp_db.name)
        
        # Initialize the database schema
        self._init_test_database()
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Remove temporary database file
        os.unlink(self.temp_db.name)
    
    def _init_test_database(self):
        """Initialize test database with required schema"""
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Create behavior_counter_definitions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS behavior_counter_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                counter_name TEXT UNIQUE NOT NULL,
                counter_type TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create behavior_counters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS behavior_counters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                counter_name TEXT NOT NULL,
                date TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(counter_name, date)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def test_create_positive_counter(self):
        """Test creating a positive behavior counter"""
        result = self.counter_manager.create_positive_counter(
            "exercise_sessions", 
            "Number of exercise sessions completed"
        )
        
        self.assertTrue(result)
        
        # Verify counter was created
        definitions = self.db_ext.get_behavior_counter_definitions()
        self.assertEqual(len(definitions), 1)
        
        definition = definitions[0]
        self.assertEqual(definition['counter_name'], "exercise_sessions")
        self.assertEqual(definition['counter_type'], "positive")
        self.assertEqual(definition['description'], "Number of exercise sessions completed")
    
    def test_create_negative_counter(self):
        """Test creating a negative behavior counter"""
        result = self.counter_manager.create_negative_counter(
            "procrastination", 
            "Times procrastinated on important tasks"
        )
        
        self.assertTrue(result)
        
        # Verify counter was created
        definitions = self.db_ext.get_behavior_counter_definitions()
        self.assertEqual(len(definitions), 1)
        
        definition = definitions[0]
        self.assertEqual(definition['counter_name'], "procrastination")
        self.assertEqual(definition['counter_type'], "negative")
        self.assertEqual(definition['description'], "Times procrastinated on important tasks")
    
    def test_increment_counter_basic(self):
        """Test basic counter incrementing"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Create a counter first
        self.counter_manager.create_positive_counter("water_glasses", "Glasses of water consumed")
        
        # Increment the counter
        result = self.counter_manager.increment_counter("water_glasses", 1, today)
        self.assertTrue(result)
        
        # Verify the count
        daily_counts = self.counter_manager.get_daily_counts(today)
        self.assertIn("water_glasses", daily_counts["positive"])
        self.assertEqual(daily_counts["positive"]["water_glasses"]["count"], 1)
    
    def test_increment_counter_multiple_times(self):
        """Test incrementing a counter multiple times in the same day"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Create a counter
        self.counter_manager.create_positive_counter("healthy_meals", "Healthy meals eaten")
        
        # Increment multiple times
        self.counter_manager.increment_counter("healthy_meals", 1, today)
        self.counter_manager.increment_counter("healthy_meals", 2, today)
        self.counter_manager.increment_counter("healthy_meals", 1, today)
        
        # Verify the total count
        daily_counts = self.counter_manager.get_daily_counts(today)
        self.assertEqual(daily_counts["positive"]["healthy_meals"]["count"], 4)
    
    def test_increment_counter_different_days(self):
        """Test incrementing counters on different days"""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Create a counter
        self.counter_manager.create_positive_counter("reading_minutes", "Minutes spent reading")
        
        # Increment on different days
        self.counter_manager.increment_counter("reading_minutes", 30, today)
        self.counter_manager.increment_counter("reading_minutes", 45, yesterday)
        
        # Verify counts for each day
        today_counts = self.counter_manager.get_daily_counts(today)
        yesterday_counts = self.counter_manager.get_daily_counts(yesterday)
        
        self.assertEqual(today_counts["positive"]["reading_minutes"]["count"], 30)
        self.assertEqual(yesterday_counts["positive"]["reading_minutes"]["count"], 45)
    
    def test_increment_nonexistent_counter(self):
        """Test incrementing a counter that doesn't exist"""
        result = self.counter_manager.increment_counter("nonexistent_counter", 1)
        self.assertFalse(result)
    
    def test_get_daily_counts_empty(self):
        """Test getting daily counts when no counters exist"""
        today = datetime.now().strftime('%Y-%m-%d')
        daily_counts = self.counter_manager.get_daily_counts(today)
        self.assertEqual(len(daily_counts["positive"]), 0)
        self.assertEqual(len(daily_counts["negative"]), 0)
    
    def test_get_daily_counts_multiple_counters(self):
        """Test getting daily counts with multiple counters"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Create multiple counters
        self.counter_manager.create_positive_counter("steps", "Steps taken")
        self.counter_manager.create_positive_counter("calories", "Calories burned")
        self.counter_manager.create_negative_counter("junk_food", "Junk food consumed")
        
        # Increment counters
        self.counter_manager.increment_counter("steps", 5000, today)
        self.counter_manager.increment_counter("calories", 300, today)
        self.counter_manager.increment_counter("junk_food", 1, today)
        
        # Get daily counts
        daily_counts = self.counter_manager.get_daily_counts(today)
        
        self.assertEqual(len(daily_counts["positive"]), 2)  # steps and calories
        self.assertEqual(len(daily_counts["negative"]), 1)  # junk_food
        self.assertEqual(daily_counts["positive"]["steps"]["count"], 5000)
        self.assertEqual(daily_counts["positive"]["calories"]["count"], 300)
        self.assertEqual(daily_counts["negative"]["junk_food"]["count"], 1)
    
    def test_bulk_increment_counters(self):
        """Test bulk incrementing multiple counters"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Create counters
        self.counter_manager.create_positive_counter("pushups", "Push-ups completed")
        self.counter_manager.create_positive_counter("situps", "Sit-ups completed")
        self.counter_manager.create_positive_counter("squats", "Squats completed")
        
        # Bulk increment
        increments = {
            "pushups": 20,
            "situps": 30,
            "squats": 25
        }
        
        results = self.counter_manager.bulk_increment_counters(increments, today)
        
        # Verify all increments succeeded
        for counter_name, success in results.items():
            self.assertTrue(success, f"Failed to increment {counter_name}")
        
        # Verify counts
        daily_counts = self.counter_manager.get_daily_counts(today)
        self.assertEqual(daily_counts["positive"]["pushups"]["count"], 20)
        self.assertEqual(daily_counts["positive"]["situps"]["count"], 30)
        self.assertEqual(daily_counts["positive"]["squats"]["count"], 25)
    
    def test_counter_type_validation(self):
        """Test that counter types are properly validated"""
        # Create both positive and negative counters
        self.counter_manager.create_positive_counter("good_habit", "A good habit")
        self.counter_manager.create_negative_counter("bad_habit", "A bad habit")
        
        definitions = self.db_ext.get_behavior_counter_definitions()
        self.assertEqual(len(definitions), 2)
        
        # Find each counter and verify type
        good_habit = next(d for d in definitions if d['counter_name'] == 'good_habit')
        bad_habit = next(d for d in definitions if d['counter_name'] == 'bad_habit')
        
        self.assertEqual(good_habit['counter_type'], 'positive')
        self.assertEqual(bad_habit['counter_type'], 'negative')
    
    def test_duplicate_counter_creation(self):
        """Test that duplicate counter names are handled properly"""
        # Create a counter
        result1 = self.counter_manager.create_positive_counter("duplicate_test", "First attempt")
        self.assertTrue(result1)
        
        # Try to create the same counter again - this might succeed in the current implementation
        # so we'll just verify that only one definition exists
        result2 = self.counter_manager.create_positive_counter("duplicate_test", "Second attempt")
        
        # Verify only one counter exists (regardless of return value)
        definitions = self.db_ext.get_behavior_counter_definitions()
        duplicate_counters = [d for d in definitions if d['counter_name'] == 'duplicate_test']
        self.assertEqual(len(duplicate_counters), 1)
    
    def test_counter_data_persistence(self):
        """Test that counter data persists correctly across multiple days"""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Create a counter and add data
        self.counter_manager.create_positive_counter("meditation", "Minutes of meditation")
        
        self.counter_manager.increment_counter("meditation", 20, yesterday)
        self.counter_manager.increment_counter("meditation", 25, today)
        
        # Verify data for each day
        today_counts = self.counter_manager.get_daily_counts(today)
        yesterday_counts = self.counter_manager.get_daily_counts(yesterday)
        
        self.assertEqual(today_counts["positive"]["meditation"]["count"], 25)
        self.assertEqual(yesterday_counts["positive"]["meditation"]["count"], 20)


class TestCountableTaskConvenienceFunctions(unittest.TestCase):
    """Test the convenience functions for countable tasks"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Patch the database path in behavior_counter_manager
        import behavior_counter_manager
        self.original_manager = behavior_counter_manager.behavior_counter_manager
        behavior_counter_manager.behavior_counter_manager = BehaviorCounterManager(self.temp_db.name)
        
        # Initialize the database schema
        self._init_test_database()
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Restore original manager
        import behavior_counter_manager
        behavior_counter_manager.behavior_counter_manager = self.original_manager
        
        # Remove temporary database file
        os.unlink(self.temp_db.name)
    
    def _init_test_database(self):
        """Initialize test database with required schema"""
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Create behavior_counter_definitions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS behavior_counter_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                counter_name TEXT UNIQUE NOT NULL,
                counter_type TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create behavior_counters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS behavior_counters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                counter_name TEXT NOT NULL,
                date TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(counter_name, date)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def test_convenience_functions_exist(self):
        """Test that convenience functions exist and are callable"""
        from behavior_counter_manager import (
            create_positive_counter, create_negative_counter, 
            increment_counter, get_daily_counts, bulk_increment_counters
        )
        
        # Test that functions exist
        self.assertTrue(callable(create_positive_counter))
        self.assertTrue(callable(create_negative_counter))
        self.assertTrue(callable(increment_counter))
        self.assertTrue(callable(get_daily_counts))
        self.assertTrue(callable(bulk_increment_counters))
    
    def test_convenience_create_and_increment(self):
        """Test the convenience functions for creating and incrementing counters"""
        from behavior_counter_manager import create_positive_counter, increment_counter, get_daily_counts
        
        # Create counter using convenience function
        result = create_positive_counter("test_counter", "Test counter description")
        self.assertTrue(result)
        
        # Increment using convenience function
        result = increment_counter("test_counter", 5)
        self.assertTrue(result)
        
        # Verify using convenience function
        today = datetime.now().strftime('%Y-%m-%d')
        daily_counts = get_daily_counts(today)
        self.assertIn("test_counter", daily_counts["positive"])
        self.assertEqual(daily_counts["positive"]["test_counter"]["count"], 5)


def run_tests():
    """Run all countable task tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestCountableTasks))
    suite.addTests(loader.loadTestsFromTestCase(TestCountableTaskConvenienceFunctions))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running Countable Task Tests")
    print("=" * 50)
    
    success = run_tests()
    
    if success:
        print("\n✅ All countable task tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some countable task tests failed!")
        sys.exit(1)