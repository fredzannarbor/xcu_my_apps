#!/usr/bin/env python3
"""
Unit tests for Quick Stats functionality
Tests the quick stats rendering and data fetching logic
"""

import unittest
import sys
import os
import tempfile
import sqlite3
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utilities_daily_engine import get_today_session, update_energy_level
from database_extensions import DatabaseExtensions


class TestQuickStats(unittest.TestCase):
    """Test cases for Quick Stats functionality"""
    
    def setUp(self):
        """Set up test fixtures with temporary database"""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
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
        
        # Create daily_sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                energy_level INTEGER,
                energy_comment TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create habits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                completed_at TEXT,
                UNIQUE(name, date)
            )
        ''')
        
        # Create revenue_activities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS revenue_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL DEFAULT 0.0,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create creative_activities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS creative_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                area TEXT NOT NULL,
                active BOOLEAN DEFAULT TRUE,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    @patch('utilities_daily_engine.sqlite3.connect')
    def test_get_today_session_existing(self, mock_connect):
        """Test getting today's session when it exists"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock existing session data
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'date': today,
            'energy_level': 8,
            'energy_comment': 'Feeling great!',
            'created_at': '2023-01-01 10:00:00',
            'updated_at': '2023-01-01 10:30:00'
        }
        
        # Test getting today's session
        session = get_today_session()
        
        # Verify the session data
        self.assertIsNotNone(session)
        self.assertEqual(session['energy_level'], 8)
        self.assertEqual(session['energy_comment'], 'Feeling great!')
        
        # Verify database calls
        mock_cursor.execute.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch('utilities_daily_engine.sqlite3.connect')
    def test_get_today_session_new(self, mock_connect):
        """Test getting today's session when it doesn't exist (creates new)"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock no existing session (first call returns None, second returns new session)
        mock_cursor.fetchone.side_effect = [
            None,  # First call - no existing session
            {      # Second call - newly created session
                'id': 1,
                'date': today,
                'energy_level': None,
                'energy_comment': None,
                'created_at': '2023-01-01 10:00:00',
                'updated_at': '2023-01-01 10:00:00'
            }
        ]
        
        # Test getting today's session
        session = get_today_session()
        
        # Verify the session was created
        self.assertIsNotNone(session)
        self.assertEqual(session['date'], today)
        self.assertIsNone(session['energy_level'])
        
        # Verify database calls (should have at least INSERT and SELECT)
        self.assertGreaterEqual(mock_cursor.execute.call_count, 2)
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch('utilities_daily_engine.sqlite3.connect')
    def test_update_energy_level(self, mock_connect):
        """Test updating energy level"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Test updating energy level
        result = update_energy_level(7)
        
        # The function doesn't return a value, so we can't test the result
        # Instead, we'll verify the database call was made
        
        # Verify database calls
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
        
        # Verify the SQL query includes the energy level
        call_args = mock_cursor.execute.call_args[0]
        self.assertIn('energy_level', call_args[0])
        self.assertIn(7, call_args[1])
    
    def test_quick_stats_data_integration(self):
        """Test integration of quick stats data fetching"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Use real database for integration test
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Insert test data
        # Daily session with energy level
        cursor.execute('''
            INSERT INTO daily_sessions (date, energy_level, energy_comment)
            VALUES (?, ?, ?)
        ''', (today, 8, 'Great energy today!'))
        
        # Habits data
        cursor.execute('''
            INSERT INTO habits (name, date, completed)
            VALUES (?, ?, ?)
        ''', ('Exercise', today, True))
        
        cursor.execute('''
            INSERT INTO habits (name, date, completed)
            VALUES (?, ?, ?)
        ''', ('Read', today, False))
        
        cursor.execute('''
            INSERT INTO habits (name, date, completed)
            VALUES (?, ?, ?)
        ''', ('Meditate', today, True))
        
        # Revenue data
        cursor.execute('''
            INSERT INTO revenue_activities (date, amount, description)
            VALUES (?, ?, ?)
        ''', (today, 150.50, 'Freelance work'))
        
        cursor.execute('''
            INSERT INTO revenue_activities (date, amount, description)
            VALUES (?, ?, ?)
        ''', (today, 75.25, 'Side project'))
        
        # Creative activities data
        cursor.execute('''
            INSERT INTO creative_activities (date, area, active)
            VALUES (?, ?, ?)
        ''', (today, 'Writing', True))
        
        cursor.execute('''
            INSERT INTO creative_activities (date, area, active)
            VALUES (?, ?, ?)
        ''', (today, 'Music', True))
        
        cursor.execute('''
            INSERT INTO creative_activities (date, area, active)
            VALUES (?, ?, ?)
        ''', (today, 'Art', False))
        
        conn.commit()
        
        # Test fetching quick stats data
        # Energy level
        cursor.execute('SELECT energy_level, updated_at FROM daily_sessions WHERE date = ?', (today,))
        energy_data = cursor.fetchone()
        self.assertIsNotNone(energy_data)
        self.assertEqual(energy_data[0], 8)
        
        # Habits completion
        cursor.execute('SELECT COUNT(*) FROM habits WHERE date = ? AND completed = 1', (today,))
        completed_habits = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM habits WHERE date = ?', (today,))
        total_habits = cursor.fetchone()[0]
        
        self.assertEqual(completed_habits, 2)
        self.assertEqual(total_habits, 3)
        
        # Revenue total
        cursor.execute('SELECT SUM(amount) FROM revenue_activities WHERE date = ?', (today,))
        total_revenue = cursor.fetchone()[0]
        self.assertEqual(total_revenue, 225.75)
        
        # Active creative areas
        cursor.execute('SELECT COUNT(DISTINCT area) FROM creative_activities WHERE date = ? AND active = 1', (today,))
        active_areas = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(DISTINCT area) FROM creative_activities WHERE date = ?', (today,))
        total_areas = cursor.fetchone()[0]
        
        self.assertEqual(active_areas, 2)
        self.assertEqual(total_areas, 3)
        
        conn.close()
    
    def test_quick_stats_empty_data(self):
        """Test quick stats with no data"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Test with empty database
        # Energy level (should be None)
        cursor.execute('SELECT energy_level, updated_at FROM daily_sessions WHERE date = ?', (today,))
        energy_data = cursor.fetchone()
        self.assertIsNone(energy_data)
        
        # Habits (should be 0/0)
        cursor.execute('SELECT COUNT(*) FROM habits WHERE date = ? AND completed = 1', (today,))
        completed_habits = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM habits WHERE date = ?', (today,))
        total_habits = cursor.fetchone()[0]
        
        self.assertEqual(completed_habits, 0)
        self.assertEqual(total_habits, 0)
        
        # Revenue (should be 0 or None)
        cursor.execute('SELECT SUM(amount) FROM revenue_activities WHERE date = ?', (today,))
        total_revenue = cursor.fetchone()[0]
        self.assertIsNone(total_revenue)  # SUM returns None for empty result
        
        # Creative areas (should be 0/0)
        cursor.execute('SELECT COUNT(DISTINCT area) FROM creative_activities WHERE date = ? AND active = 1', (today,))
        active_areas = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(DISTINCT area) FROM creative_activities WHERE date = ?', (today,))
        total_areas = cursor.fetchone()[0]
        
        self.assertEqual(active_areas, 0)
        self.assertEqual(total_areas, 0)
        
        conn.close()
    
    def test_quick_stats_data_formatting(self):
        """Test that quick stats data is properly formatted for display"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Insert test data with edge cases
        cursor.execute('''
            INSERT INTO daily_sessions (date, energy_level, updated_at)
            VALUES (?, ?, ?)
        ''', (today, 10, '2023-01-01 14:30:45'))
        
        cursor.execute('''
            INSERT INTO revenue_activities (date, amount)
            VALUES (?, ?)
        ''', (today, 1234.56))
        
        conn.commit()
        
        # Test data formatting
        cursor.execute('SELECT energy_level, updated_at FROM daily_sessions WHERE date = ?', (today,))
        energy_data = cursor.fetchone()
        
        # Energy level should be an integer
        self.assertIsInstance(energy_data[0], int)
        self.assertEqual(energy_data[0], 10)
        
        # Timestamp should be a string
        self.assertIsInstance(energy_data[1], str)
        
        # Revenue should handle decimal places
        cursor.execute('SELECT SUM(amount) FROM revenue_activities WHERE date = ?', (today,))
        total_revenue = cursor.fetchone()[0]
        self.assertAlmostEqual(total_revenue, 1234.56, places=2)
        
        conn.close()


def run_tests():
    """Run all quick stats tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestQuickStats))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running Quick Stats Tests")
    print("=" * 50)
    
    success = run_tests()
    
    if success:
        print("\n✅ All quick stats tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some quick stats tests failed!")
        sys.exit(1)