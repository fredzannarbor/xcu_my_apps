#!/usr/bin/env python3
"""
Database Extensions for Enhanced Habit Tracking
Extends the existing database schema with new tables for metrics and behavior tracking
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional


class DatabaseExtensions:
    """Manages database schema extensions for enhanced habit tracking"""
    
    def __init__(self, db_path='daily_engine.db'):
        self.db_path = db_path
        self.init_extended_schema()
    
    def init_extended_schema(self):
        """Initialize extended database schema with migration support"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create habit_metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habit_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_name TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                data_type TEXT NOT NULL CHECK (data_type IN ('int', 'float', 'string')),
                value TEXT NOT NULL,
                date TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(habit_name, metric_name, date)
            )
        ''')
        
        # Create behavior_counters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS behavior_counters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                counter_name TEXT NOT NULL,
                counter_type TEXT NOT NULL CHECK (counter_type IN ('positive', 'negative')),
                description TEXT,
                date TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(counter_name, date)
            )
        ''')
        
        # Create streamlit_app_status table (if not exists from app manager)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streamlit_app_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT NOT NULL UNIQUE,
                port INTEGER NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('running', 'stopped', 'error')),
                pid INTEGER,
                start_time TEXT,
                last_health_check TEXT,
                restart_count INTEGER DEFAULT 0,
                error_message TEXT
            )
        ''')
        
        # Create habit_metric_definitions table for metadata
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habit_metric_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_name TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                data_type TEXT NOT NULL CHECK (data_type IN ('int', 'float', 'string')),
                description TEXT,
                unit TEXT,
                min_value REAL,
                max_value REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(habit_name, metric_name)
            )
        ''')
        
        # Create behavior_counter_definitions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS behavior_counter_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                counter_name TEXT NOT NULL UNIQUE,
                counter_type TEXT NOT NULL CHECK (counter_type IN ('positive', 'negative')),
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create micro_tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS micro_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0,
                priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
                estimated_minutes INTEGER DEFAULT 15,
                completed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_habit_metrics_date ON habit_metrics(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_habit_metrics_habit ON habit_metrics(habit_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_behavior_counters_date ON behavior_counters(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_behavior_counters_name ON behavior_counters(counter_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_micro_tasks_date ON micro_tasks(date)')

        conn.commit()
        conn.close()
    
    def migrate_existing_data(self):
        """Migrate existing habit data to preserve compatibility"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if habit_tracking table exists and has data
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='habit_tracking'")
            if cursor.fetchone():
                # Ensure existing habit_tracking table has all required columns
                cursor.execute("PRAGMA table_info(habit_tracking)")
                columns = [column[1] for column in cursor.fetchall()]
                
                # Add missing columns if needed
                if 'notes' not in columns:
                    cursor.execute('ALTER TABLE habit_tracking ADD COLUMN notes TEXT')
                
                print("Existing habit tracking data preserved")
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Migration warning: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def add_habit_metric_definition(self, habit_name: str, metric_name: str, data_type: str, 
                                  description: str = None, unit: str = None, 
                                  min_value: float = None, max_value: float = None) -> bool:
        """Add a metric definition for a habit"""
        if data_type not in ['int', 'float', 'string']:
            raise ValueError("data_type must be 'int', 'float', or 'string'")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO habit_metric_definitions 
                (habit_name, metric_name, data_type, description, unit, min_value, max_value)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (habit_name, metric_name, data_type, description, unit, min_value, max_value))
            
            conn.commit()
            return True
            
        except sqlite3.IntegrityError:
            # Metric already exists, update it
            cursor.execute('''
                UPDATE habit_metric_definitions 
                SET data_type = ?, description = ?, unit = ?, min_value = ?, max_value = ?
                WHERE habit_name = ? AND metric_name = ?
            ''', (data_type, description, unit, min_value, max_value, habit_name, metric_name))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Error adding metric definition: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def add_behavior_counter_definition(self, counter_name: str, counter_type: str, description: str = None) -> bool:
        """Add a behavior counter definition"""
        if counter_type not in ['positive', 'negative']:
            raise ValueError("counter_type must be 'positive' or 'negative'")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO behavior_counter_definitions (counter_name, counter_type, description)
                VALUES (?, ?, ?)
            ''', (counter_name, counter_type, description))
            
            conn.commit()
            return True
            
        except sqlite3.IntegrityError:
            # Counter already exists, update it
            cursor.execute('''
                UPDATE behavior_counter_definitions 
                SET counter_type = ?, description = ?
                WHERE counter_name = ?
            ''', (counter_type, description, counter_name))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Error adding counter definition: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_habit_metric_definitions(self, habit_name: str = None) -> List[Dict]:
        """Get metric definitions for habits"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if habit_name:
                cursor.execute('''
                    SELECT habit_name, metric_name, data_type, description, unit, min_value, max_value
                    FROM habit_metric_definitions WHERE habit_name = ?
                ''', (habit_name,))
            else:
                cursor.execute('''
                    SELECT habit_name, metric_name, data_type, description, unit, min_value, max_value
                    FROM habit_metric_definitions
                ''')
            
            results = cursor.fetchall()
            return [
                {
                    'habit_name': row[0],
                    'metric_name': row[1],
                    'data_type': row[2],
                    'description': row[3],
                    'unit': row[4],
                    'min_value': row[5],
                    'max_value': row[6]
                }
                for row in results
            ]
            
        except sqlite3.Error as e:
            print(f"Error getting metric definitions: {e}")
            return []
        finally:
            conn.close()
    
    def get_behavior_counter_definitions(self) -> List[Dict]:
        """Get all behavior counter definitions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT counter_name, counter_type, description, created_at
                FROM behavior_counter_definitions
                ORDER BY counter_type, counter_name
            ''')
            
            results = cursor.fetchall()
            return [
                {
                    'counter_name': row[0],
                    'counter_type': row[1],
                    'description': row[2],
                    'created_at': row[3]
                }
                for row in results
            ]
            
        except sqlite3.Error as e:
            print(f"Error getting counter definitions: {e}")
            return []
        finally:
            conn.close()
    
    def validate_metric_value(self, habit_name: str, metric_name: str, value: Any) -> tuple[bool, str]:
        """Validate a metric value against its definition"""
        definitions = self.get_habit_metric_definitions(habit_name)
        metric_def = next((d for d in definitions if d['metric_name'] == metric_name), None)
        
        if not metric_def:
            return False, f"Metric '{metric_name}' not defined for habit '{habit_name}'"
        
        data_type = metric_def['data_type']
        
        try:
            if data_type == 'int':
                int_value = int(value)
                if metric_def['min_value'] is not None and int_value < metric_def['min_value']:
                    return False, f"Value {int_value} is below minimum {metric_def['min_value']}"
                if metric_def['max_value'] is not None and int_value > metric_def['max_value']:
                    return False, f"Value {int_value} is above maximum {metric_def['max_value']}"
                return True, str(int_value)
                
            elif data_type == 'float':
                float_value = float(value)
                if metric_def['min_value'] is not None and float_value < metric_def['min_value']:
                    return False, f"Value {float_value} is below minimum {metric_def['min_value']}"
                if metric_def['max_value'] is not None and float_value > metric_def['max_value']:
                    return False, f"Value {float_value} is above maximum {metric_def['max_value']}"
                return True, str(float_value)
                
            elif data_type == 'string':
                return True, str(value)
                
        except (ValueError, TypeError):
            return False, f"Cannot convert '{value}' to {data_type}"
        
        return False, "Unknown validation error"
    
    def log_habit_metric(self, habit_name: str, metric_name: str, value: Any, date: str = None) -> bool:
        """Log a metric value for a habit"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Validate the value
        is_valid, validated_value = self.validate_metric_value(habit_name, metric_name, value)
        if not is_valid:
            print(f"Validation error: {validated_value}")
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO habit_metrics 
                (habit_name, metric_name, data_type, value, date)
                SELECT ?, ?, data_type, ?, ?
                FROM habit_metric_definitions 
                WHERE habit_name = ? AND metric_name = ?
            ''', (habit_name, metric_name, validated_value, date, habit_name, metric_name))
            
            if cursor.rowcount == 0:
                print(f"Metric definition not found for {habit_name}.{metric_name}")
                return False
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Error logging metric: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_habit_metrics(self, habit_name: str, metric_name: str = None, days: int = 30) -> List[Dict]:
        """Get habit metric history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if metric_name:
                cursor.execute('''
                    SELECT date, value, data_type, timestamp
                    FROM habit_metrics 
                    WHERE habit_name = ? AND metric_name = ?
                    ORDER BY date DESC
                    LIMIT ?
                ''', (habit_name, metric_name, days))
            else:
                cursor.execute('''
                    SELECT metric_name, date, value, data_type, timestamp
                    FROM habit_metrics 
                    WHERE habit_name = ?
                    ORDER BY date DESC, metric_name
                    LIMIT ?
                ''', (habit_name, days * 10))  # Rough estimate for multiple metrics
            
            results = cursor.fetchall()
            
            if metric_name:
                return [
                    {
                        'date': row[0],
                        'value': row[1],
                        'data_type': row[2],
                        'timestamp': row[3]
                    }
                    for row in results
                ]
            else:
                return [
                    {
                        'metric_name': row[0],
                        'date': row[1],
                        'value': row[2],
                        'data_type': row[3],
                        'timestamp': row[4]
                    }
                    for row in results
                ]
            
        except sqlite3.Error as e:
            print(f"Error getting metrics: {e}")
            return []
        finally:
            conn.close()
    
    def set_behavior_counter(self, counter_name: str, value: float, date: str = None) -> bool:
        """Set a behavior counter to an absolute value (for metrics like weight)"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Check if counter definition exists
            cursor.execute('SELECT counter_type FROM behavior_counter_definitions WHERE counter_name = ?',
                         (counter_name,))
            counter_def = cursor.fetchone()

            if not counter_def:
                print(f"Counter '{counter_name}' not defined")
                return False

            counter_type = counter_def[0]

            # Insert or replace counter value for the date
            cursor.execute('''
                INSERT INTO behavior_counters (counter_name, counter_type, date, count)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(counter_name, date) DO UPDATE SET
                count = ?
            ''', (counter_name, counter_type, date, value, value))

            conn.commit()
            return True

        except sqlite3.Error as e:
            print(f"Error setting counter: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def increment_behavior_counter(self, counter_name: str, amount: int = 1, date: str = None) -> bool:
        """Increment a behavior counter"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Check if counter definition exists
            cursor.execute('SELECT counter_type FROM behavior_counter_definitions WHERE counter_name = ?',
                         (counter_name,))
            counter_def = cursor.fetchone()

            if not counter_def:
                print(f"Counter '{counter_name}' not defined")
                return False

            counter_type = counter_def[0]

            # Insert or update counter for the date
            cursor.execute('''
                INSERT INTO behavior_counters (counter_name, counter_type, date, count)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(counter_name, date) DO UPDATE SET
                count = count + ?
            ''', (counter_name, counter_type, date, amount, amount))

            conn.commit()
            return True

        except sqlite3.Error as e:
            print(f"Error incrementing counter: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_behavior_counter_data(self, counter_name: str = None, days: int = 30) -> List[Dict]:
        """Get behavior counter data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if counter_name:
                cursor.execute('''
                    SELECT date, count, timestamp
                    FROM behavior_counters 
                    WHERE counter_name = ?
                    ORDER BY date DESC
                    LIMIT ?
                ''', (counter_name, days))
            else:
                cursor.execute('''
                    SELECT counter_name, counter_type, date, count, timestamp
                    FROM behavior_counters 
                    ORDER BY date DESC, counter_name
                    LIMIT ?
                ''', (days * 20))  # Rough estimate for multiple counters
            
            results = cursor.fetchall()
            
            if counter_name:
                return [
                    {
                        'date': row[0],
                        'count': row[1],
                        'timestamp': row[2]
                    }
                    for row in results
                ]
            else:
                return [
                    {
                        'counter_name': row[0],
                        'counter_type': row[1],
                        'date': row[2],
                        'count': row[3],
                        'timestamp': row[4]
                    }
                    for row in results
                ]
            
        except sqlite3.Error as e:
            print(f"Error getting counter data: {e}")
            return []
        finally:
            conn.close()
    
    def get_daily_summary(self, date: str = None) -> Dict:
        """Get daily summary of all metrics and counters"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get metrics for the date
            cursor.execute('''
                SELECT habit_name, metric_name, value, data_type
                FROM habit_metrics
                WHERE date = ?
            ''', (date,))
            metrics = cursor.fetchall()

            # Get counters for the date
            cursor.execute('''
                SELECT counter_name, counter_type, count
                FROM behavior_counters
                WHERE date = ?
            ''', (date,))
            counters = cursor.fetchall()

            return {
                'date': date,
                'metrics': [
                    {
                        'habit_name': row[0],
                        'metric_name': row[1],
                        'value': row[2],
                        'data_type': row[3]
                    }
                    for row in metrics
                ],
                'counters': [
                    {
                        'counter_name': row[0],
                        'counter_type': row[1],
                        'count': row[2]
                    }
                    for row in counters
                ]
            }

        except sqlite3.Error as e:
            print(f"Error getting daily summary: {e}")
            return {'date': date, 'metrics': [], 'counters': []}
        finally:
            conn.close()

    def add_micro_task(self, task_name: str, description: str = None, priority: str = 'medium',
                      estimated_minutes: int = 15, date: str = None) -> bool:
        """Add a new micro-task"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        if priority not in ['low', 'medium', 'high']:
            raise ValueError("priority must be 'low', 'medium', or 'high'")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO micro_tasks (task_name, description, date, priority, estimated_minutes)
                VALUES (?, ?, ?, ?, ?)
            ''', (task_name, description, date, priority, estimated_minutes))

            conn.commit()
            return True

        except sqlite3.Error as e:
            print(f"Error adding micro-task: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def complete_micro_task(self, task_id: int) -> bool:
        """Mark a micro-task as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                UPDATE micro_tasks
                SET completed = 1, completed_at = ?
                WHERE id = ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), task_id))

            conn.commit()
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            print(f"Error completing micro-task: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_micro_tasks(self, date: str = None, completed: bool = None) -> List[Dict]:
        """Get micro-tasks for a specific date"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            query = '''
                SELECT id, task_name, description, completed, priority, estimated_minutes, completed_at, created_at
                FROM micro_tasks
                WHERE date = ?
            '''
            params = [date]

            if completed is not None:
                query += ' AND completed = ?'
                params.append(1 if completed else 0)

            query += ' ORDER BY priority DESC, created_at ASC'

            cursor.execute(query, params)
            results = cursor.fetchall()

            return [
                {
                    'id': row[0],
                    'task_name': row[1],
                    'description': row[2],
                    'completed': bool(row[3]),
                    'priority': row[4],
                    'estimated_minutes': row[5],
                    'completed_at': row[6],
                    'created_at': row[7]
                }
                for row in results
            ]

        except sqlite3.Error as e:
            print(f"Error getting micro-tasks: {e}")
            return []
        finally:
            conn.close()

    def delete_micro_task(self, task_id: int) -> bool:
        """Delete a micro-task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('DELETE FROM micro_tasks WHERE id = ?', (task_id,))
            conn.commit()
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            print(f"Error deleting micro-task: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()


# Global instance for easy access
db_extensions = DatabaseExtensions()


# Convenience functions
def add_habit_metric_definition(habit_name: str, metric_name: str, data_type: str, **kwargs) -> bool:
    """Add a habit metric definition"""
    return db_extensions.add_habit_metric_definition(habit_name, metric_name, data_type, **kwargs)


def add_behavior_counter_definition(counter_name: str, counter_type: str, description: str = None) -> bool:
    """Add a behavior counter definition"""
    return db_extensions.add_behavior_counter_definition(counter_name, counter_type, description)


def log_habit_metric(habit_name: str, metric_name: str, value: Any, date: str = None) -> bool:
    """Log a habit metric value"""
    return db_extensions.log_habit_metric(habit_name, metric_name, value, date)


def set_behavior_counter(counter_name: str, value: float, date: str = None) -> bool:
    """Set a behavior counter to an absolute value"""
    return db_extensions.set_behavior_counter(counter_name, value, date)


def increment_behavior_counter(counter_name: str, amount: int = 1, date: str = None) -> bool:
    """Increment a behavior counter"""
    return db_extensions.increment_behavior_counter(counter_name, amount, date)


def get_daily_summary(date: str = None) -> Dict:
    """Get daily summary of metrics and counters"""
    return db_extensions.get_daily_summary(date)


def add_micro_task(task_name: str, description: str = None, priority: str = 'medium',
                  estimated_minutes: int = 15, date: str = None) -> bool:
    """Add a new micro-task"""
    return db_extensions.add_micro_task(task_name, description, priority, estimated_minutes, date)


def complete_micro_task(task_id: int) -> bool:
    """Mark a micro-task as completed"""
    return db_extensions.complete_micro_task(task_id)


def get_micro_tasks(date: str = None, completed: bool = None) -> List[Dict]:
    """Get micro-tasks for a specific date"""
    return db_extensions.get_micro_tasks(date, completed)


def delete_micro_task(task_id: int) -> bool:
    """Delete a micro-task"""
    return db_extensions.delete_micro_task(task_id)


if __name__ == "__main__":
    # Test the database extensions
    print("Initializing database extensions...")
    db_ext = DatabaseExtensions()
    
    # Test adding metric definitions
    db_ext.add_habit_metric_definition('exercise', 'weight', 'float', 'Body weight in kg', 'kg', 40.0, 200.0)
    db_ext.add_habit_metric_definition('sleep', 'hours', 'float', 'Hours of sleep', 'hours', 0.0, 24.0)
    
    # Test adding counter definitions
    db_ext.add_behavior_counter_definition('healthy_eating', 'positive', 'Healthy eating choices')
    db_ext.add_behavior_counter_definition('binge_eating', 'negative', 'Binge eating episodes')
    
    print("Database extensions initialized successfully!")