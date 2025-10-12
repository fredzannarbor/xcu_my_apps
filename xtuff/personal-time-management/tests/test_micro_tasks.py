#!/usr/bin/env python3
"""
Unit tests for micro-task functionality
Tests the micro-task management system including creation, completion, and retrieval
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


class TestMicroTasks(unittest.TestCase):
    """Test cases for micro-task functionality"""
    
    def setUp(self):
        """Set up test fixtures with temporary database"""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Initialize database extensions with temp database
        self.db_ext = DatabaseExtensions(self.temp_db.name)
        
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
        
        # Create micro_tasks table
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
        
        conn.commit()
        conn.close()
    
    def test_add_micro_task_basic(self):
        """Test adding a basic micro-task"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        result = self.db_ext.add_micro_task(
            task_name="Test task",
            description="Test description",
            priority="high",
            estimated_minutes=30,
            date=today
        )
        
        self.assertTrue(result)
        
        # Verify task was added
        tasks = self.db_ext.get_micro_tasks(date=today)
        self.assertEqual(len(tasks), 1)
        
        task = tasks[0]
        self.assertEqual(task['task_name'], "Test task")
        self.assertEqual(task['description'], "Test description")
        self.assertEqual(task['priority'], "high")
        self.assertEqual(task['estimated_minutes'], 30)
        self.assertFalse(task['completed'])
    
    def test_add_micro_task_minimal(self):
        """Test adding a micro-task with minimal parameters"""
        result = self.db_ext.add_micro_task(task_name="Minimal task")
        
        self.assertTrue(result)
        
        # Verify task was added with defaults
        tasks = self.db_ext.get_micro_tasks()
        self.assertEqual(len(tasks), 1)
        
        task = tasks[0]
        self.assertEqual(task['task_name'], "Minimal task")
        self.assertEqual(task['priority'], "medium")
        self.assertEqual(task['estimated_minutes'], 15)
        self.assertFalse(task['completed'])
    
    def test_complete_micro_task(self):
        """Test completing a micro-task"""
        # Add a task first
        self.db_ext.add_micro_task(task_name="Task to complete")
        tasks = self.db_ext.get_micro_tasks()
        task_id = tasks[0]['id']
        
        # Complete the task
        result = self.db_ext.complete_micro_task(task_id)
        self.assertTrue(result)
        
        # Verify task is completed
        tasks = self.db_ext.get_micro_tasks()
        task = tasks[0]
        self.assertTrue(task['completed'])
        self.assertIsNotNone(task['completed_at'])
    
    def test_complete_nonexistent_task(self):
        """Test completing a non-existent task"""
        result = self.db_ext.complete_micro_task(999)
        self.assertFalse(result)
    
    def test_get_micro_tasks_by_date(self):
        """Test retrieving micro-tasks by specific date"""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Add tasks for different dates
        self.db_ext.add_micro_task("Today's task", date=today)
        self.db_ext.add_micro_task("Yesterday's task", date=yesterday)
        
        # Get today's tasks
        today_tasks = self.db_ext.get_micro_tasks(date=today)
        self.assertEqual(len(today_tasks), 1)
        self.assertEqual(today_tasks[0]['task_name'], "Today's task")
        
        # Get yesterday's tasks
        yesterday_tasks = self.db_ext.get_micro_tasks(date=yesterday)
        self.assertEqual(len(yesterday_tasks), 1)
        self.assertEqual(yesterday_tasks[0]['task_name'], "Yesterday's task")
    
    def test_get_micro_tasks_by_completion_status(self):
        """Test retrieving micro-tasks by completion status"""
        # Add completed and incomplete tasks
        self.db_ext.add_micro_task("Incomplete task")
        self.db_ext.add_micro_task("Task to complete")
        
        tasks = self.db_ext.get_micro_tasks()
        task_id = tasks[1]['id']
        self.db_ext.complete_micro_task(task_id)
        
        # Get only incomplete tasks
        incomplete_tasks = self.db_ext.get_micro_tasks(completed=False)
        self.assertEqual(len(incomplete_tasks), 1)
        self.assertEqual(incomplete_tasks[0]['task_name'], "Incomplete task")
        
        # Get only completed tasks
        completed_tasks = self.db_ext.get_micro_tasks(completed=True)
        self.assertEqual(len(completed_tasks), 1)
        self.assertEqual(completed_tasks[0]['task_name'], "Task to complete")
    
    def test_delete_micro_task(self):
        """Test deleting a micro-task"""
        # Add a task
        self.db_ext.add_micro_task("Task to delete")
        tasks = self.db_ext.get_micro_tasks()
        task_id = tasks[0]['id']
        
        # Delete the task
        result = self.db_ext.delete_micro_task(task_id)
        self.assertTrue(result)
        
        # Verify task is deleted
        tasks = self.db_ext.get_micro_tasks()
        self.assertEqual(len(tasks), 0)
    
    def test_delete_nonexistent_task(self):
        """Test deleting a non-existent task"""
        result = self.db_ext.delete_micro_task(999)
        self.assertFalse(result)
    
    def test_multiple_tasks_same_date(self):
        """Test handling multiple tasks on the same date"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Add multiple tasks
        self.db_ext.add_micro_task("Task 1", priority="high", date=today)
        self.db_ext.add_micro_task("Task 2", priority="low", date=today)
        self.db_ext.add_micro_task("Task 3", priority="medium", date=today)
        
        # Retrieve all tasks
        tasks = self.db_ext.get_micro_tasks(date=today)
        self.assertEqual(len(tasks), 3)
        
        # Verify all tasks are present
        task_names = [task['task_name'] for task in tasks]
        self.assertIn("Task 1", task_names)
        self.assertIn("Task 2", task_names)
        self.assertIn("Task 3", task_names)
    
    def test_task_priorities(self):
        """Test different task priorities"""
        priorities = ["low", "medium", "high"]
        
        for priority in priorities:
            self.db_ext.add_micro_task(f"Task {priority}", priority=priority)
        
        tasks = self.db_ext.get_micro_tasks()
        self.assertEqual(len(tasks), 3)
        
        # Verify priorities are stored correctly
        stored_priorities = [task['priority'] for task in tasks]
        for priority in priorities:
            self.assertIn(priority, stored_priorities)
    
    def test_estimated_minutes_validation(self):
        """Test estimated minutes handling"""
        # Test various time estimates
        time_estimates = [5, 15, 30, 60, 120]
        
        for minutes in time_estimates:
            self.db_ext.add_micro_task(f"Task {minutes}min", estimated_minutes=minutes)
        
        tasks = self.db_ext.get_micro_tasks()
        self.assertEqual(len(tasks), 5)
        
        # Verify time estimates are stored correctly
        stored_times = [task['estimated_minutes'] for task in tasks]
        for minutes in time_estimates:
            self.assertIn(minutes, stored_times)


class TestMicroTaskConvenienceFunctions(unittest.TestCase):
    """Test the convenience functions for micro-tasks"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Patch the database path in database_extensions
        import database_extensions
        self.original_db_path = database_extensions.db_extensions.db_path
        database_extensions.db_extensions.db_path = self.temp_db.name
        
        # Initialize the database schema
        self._init_test_database()
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Restore original database path
        import database_extensions
        database_extensions.db_extensions.db_path = self.original_db_path
        
        # Remove temporary database file
        os.unlink(self.temp_db.name)
    
    def _init_test_database(self):
        """Initialize test database with required schema"""
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Create micro_tasks table
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
        
        conn.commit()
        conn.close()
    
    def test_convenience_functions_exist(self):
        """Test that convenience functions exist and are callable"""
        from database_extensions import add_micro_task, complete_micro_task, get_micro_tasks, delete_micro_task
        
        # Test that functions exist
        self.assertTrue(callable(add_micro_task))
        self.assertTrue(callable(complete_micro_task))
        self.assertTrue(callable(get_micro_tasks))
        self.assertTrue(callable(delete_micro_task))
    
    def test_convenience_add_micro_task(self):
        """Test the convenience function for adding micro-tasks"""
        from database_extensions import add_micro_task, get_micro_tasks
        
        result = add_micro_task("Convenience test task", "Test description")
        self.assertTrue(result)
        
        tasks = get_micro_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['task_name'], "Convenience test task")
    
    def test_convenience_complete_micro_task(self):
        """Test the convenience function for completing micro-tasks"""
        from database_extensions import add_micro_task, complete_micro_task, get_micro_tasks
        
        # Add a task
        add_micro_task("Task to complete")
        tasks = get_micro_tasks()
        task_id = tasks[0]['id']
        
        # Complete using convenience function
        result = complete_micro_task(task_id)
        self.assertTrue(result)
        
        # Verify completion
        tasks = get_micro_tasks()
        self.assertTrue(tasks[0]['completed'])


def run_tests():
    """Run all micro-task tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestMicroTasks))
    suite.addTests(loader.loadTestsFromTestCase(TestMicroTaskConvenienceFunctions))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running Micro-Task Tests")
    print("=" * 50)
    
    success = run_tests()
    
    if success:
        print("\n✅ All micro-task tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some micro-task tests failed!")
        sys.exit(1)