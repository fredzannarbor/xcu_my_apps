#!/usr/bin/env python3
"""
Test configuration and utilities
Provides common test setup and configuration for all test modules
"""

import os
import tempfile
import sqlite3
import json
from datetime import datetime


class TestDatabaseSetup:
    """Helper class for setting up test databases"""
    
    @staticmethod
    def create_temp_database():
        """Create a temporary database file"""
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        return temp_db.name
    
    @staticmethod
    def init_full_schema(db_path):
        """Initialize a database with the full application schema"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Daily sessions table
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
        
        # Micro-tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS micro_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'medium',
                estimated_minutes INTEGER DEFAULT 15,
                date TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                completed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Behavior counter definitions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS behavior_counter_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                counter_name TEXT UNIQUE NOT NULL,
                counter_type TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Behavior counters table
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
        
        # Streamlit app status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streamlit_app_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL,
                port INTEGER,
                pid INTEGER,
                start_time TEXT,
                last_health_check TEXT,
                restart_count INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Habits table
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
        
        # Revenue activities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS revenue_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL DEFAULT 0.0,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Creative activities table
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


class TestAppConfig:
    """Helper class for creating test app configurations"""
    
    @staticmethod
    def create_test_config(config_path, test_app_path=None):
        """Create a test configuration file"""
        if test_app_path is None:
            # Create a minimal test app
            test_app_path = TestAppConfig.create_test_app()
        
        config = {
            "apps": {
                "test_app": {
                    "name": "Test App",
                    "path": test_app_path,
                    "port": 8501,
                    "enabled": True,
                    "auto_start": False,
                    "restart_on_failure": True,
                    "health_check_url": "/health",
                    "environment": {}
                },
                "disabled_app": {
                    "name": "Disabled App",
                    "path": "disabled_app.py",
                    "port": 8502,
                    "enabled": False,
                    "auto_start": False,
                    "restart_on_failure": True,
                    "health_check_url": "/health",
                    "environment": {}
                }
            },
            "daemon_config": {
                "check_interval": 30,
                "restart_delay": 5,
                "max_restart_attempts": 3,
                "log_level": "INFO"
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config_path
    
    @staticmethod
    def create_test_app():
        """Create a minimal test Streamlit app"""
        test_app = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        test_app.write('''
import streamlit as st

st.title("Test Streamlit App")
st.write("This is a test application for unit testing")

# Health check
if st.sidebar.button("Health Check"):
    st.success("App is healthy!")

# Simple functionality
if "counter" not in st.session_state:
    st.session_state.counter = 0

if st.button("Click me"):
    st.session_state.counter += 1
    st.write(f"Clicked {st.session_state.counter} times")
''')
        test_app.close()
        return test_app.name


class TestDataGenerator:
    """Helper class for generating test data"""
    
    @staticmethod
    def create_sample_micro_tasks(db_path, date=None):
        """Create sample micro-tasks for testing"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        sample_tasks = [
            ("Review emails", "Check and respond to important emails", "high", 15),
            ("Update documentation", "Update project README file", "medium", 30),
            ("Quick code review", "Review pull request #123", "high", 20),
            ("Organize desk", "Clean and organize workspace", "low", 10),
            ("Plan tomorrow", "Create task list for tomorrow", "medium", 15)
        ]
        
        for task_name, description, priority, minutes in sample_tasks:
            cursor.execute('''
                INSERT INTO micro_tasks (task_name, description, priority, estimated_minutes, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (task_name, description, priority, minutes, date))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def create_sample_counters(db_path, date=None):
        """Create sample behavior counters for testing"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create counter definitions
        counter_definitions = [
            ("water_glasses", "positive", "Glasses of water consumed"),
            ("exercise_minutes", "positive", "Minutes of exercise"),
            ("healthy_meals", "positive", "Healthy meals eaten"),
            ("procrastination", "negative", "Times procrastinated"),
            ("junk_food", "negative", "Junk food items consumed")
        ]
        
        for counter_name, counter_type, description in counter_definitions:
            cursor.execute('''
                INSERT OR IGNORE INTO behavior_counter_definitions 
                (counter_name, counter_type, description)
                VALUES (?, ?, ?)
            ''', (counter_name, counter_type, description))
        
        # Create some sample counts
        sample_counts = [
            ("water_glasses", 8),
            ("exercise_minutes", 45),
            ("healthy_meals", 3),
            ("procrastination", 2),
            ("junk_food", 1)
        ]
        
        for counter_name, count in sample_counts:
            cursor.execute('''
                INSERT OR REPLACE INTO behavior_counters 
                (counter_name, date, count)
                VALUES (?, ?, ?)
            ''', (counter_name, date, count))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def create_sample_daily_session(db_path, date=None):
        """Create a sample daily session for testing"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO daily_sessions 
            (date, energy_level, energy_comment)
            VALUES (?, ?, ?)
        ''', (date, 8, "Feeling great today!"))
        
        conn.commit()
        conn.close()


def cleanup_temp_files(*file_paths):
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception:
            pass  # Ignore cleanup errors


# Test constants
TEST_PORTS = [8599, 8598, 8597, 8596, 8595]  # High ports to avoid conflicts
TEST_DATE = "2023-01-01"
TEST_TIMEOUT = 10  # seconds