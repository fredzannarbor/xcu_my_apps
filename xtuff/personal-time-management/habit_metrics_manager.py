#!/usr/bin/env python3
"""
Habit Metrics Manager
Manages quantitative metrics for habit tracking with validation and history
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from database_extensions import DatabaseExtensions


class HabitMetricsManager:
    """Manages quantitative metrics for habits"""
    
    def __init__(self, db_path='daily_engine.db'):
        self.db_path = db_path
        self.db_extensions = DatabaseExtensions(db_path)
    
    def add_metric_to_habit(self, habit_name: str, metric_name: str, data_type: str, 
                           description: str = None, unit: str = None, 
                           min_value: float = None, max_value: float = None) -> bool:
        """Add a metric definition to a habit"""
        if data_type not in ['int', 'float', 'string']:
            raise ValueError("data_type must be 'int', 'float', or 'string'")
        
        return self.db_extensions.add_habit_metric_definition(
            habit_name, metric_name, data_type, description, unit, min_value, max_value
        )
    
    def log_metric_value(self, habit_name: str, metric_name: str, value: Any, date: str = None) -> bool:
        """Log a metric value for a habit"""
        return self.db_extensions.log_habit_metric(habit_name, metric_name, value, date)
    
    def get_metric_history(self, habit_name: str, metric_name: str, days: int = 30) -> List[Dict]:
        """Get metric history for a specific habit and metric"""
        return self.db_extensions.get_habit_metrics(habit_name, metric_name, days)
    
    def get_all_habit_metrics(self, habit_name: str, days: int = 30) -> List[Dict]:
        """Get all metrics for a specific habit"""
        return self.db_extensions.get_habit_metrics(habit_name, None, days)
    
    def validate_metric_value(self, habit_name: str, metric_name: str, value: Any) -> Tuple[bool, str]:
        """Validate a metric value against its definition"""
        return self.db_extensions.validate_metric_value(habit_name, metric_name, value)
    
    def get_habit_metric_definitions(self, habit_name: str = None) -> List[Dict]:
        """Get metric definitions for habits"""
        return self.db_extensions.get_habit_metric_definitions(habit_name)
    
    def remove_metric_definition(self, habit_name: str, metric_name: str) -> bool:
        """Remove a metric definition"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Remove definition
            cursor.execute('''
                DELETE FROM habit_metric_definitions 
                WHERE habit_name = ? AND metric_name = ?
            ''', (habit_name, metric_name))
            
            # Optionally remove historical data (commented out to preserve data)
            # cursor.execute('''
            #     DELETE FROM habit_metrics 
            #     WHERE habit_name = ? AND metric_name = ?
            # ''', (habit_name, metric_name))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"Error removing metric definition: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_metric_statistics(self, habit_name: str, metric_name: str, days: int = 30) -> Dict:
        """Get statistical analysis of a metric"""
        history = self.get_metric_history(habit_name, metric_name, days)
        
        if not history:
            return {'error': 'No data available'}
        
        # Get metric definition for data type
        definitions = self.get_habit_metric_definitions(habit_name)
        metric_def = next((d for d in definitions if d['metric_name'] == metric_name), None)
        
        if not metric_def:
            return {'error': 'Metric definition not found'}
        
        data_type = metric_def['data_type']
        
        if data_type in ['int', 'float']:
            # Numerical statistics
            values = []
            for entry in history:
                try:
                    if data_type == 'int':
                        values.append(int(entry['value']))
                    else:
                        values.append(float(entry['value']))
                except (ValueError, TypeError):
                    continue
            
            if not values:
                return {'error': 'No valid numerical values'}
            
            values.sort()
            n = len(values)
            
            stats = {
                'count': n,
                'min': min(values),
                'max': max(values),
                'mean': sum(values) / n,
                'median': values[n // 2] if n % 2 == 1 else (values[n // 2 - 1] + values[n // 2]) / 2,
                'data_type': data_type,
                'unit': metric_def.get('unit'),
                'latest_value': values[-1] if values else None,
                'trend': self._calculate_trend(values)
            }
            
            # Calculate standard deviation
            mean = stats['mean']
            variance = sum((x - mean) ** 2 for x in values) / n
            stats['std_dev'] = variance ** 0.5
            
            return stats
        
        else:
            # String statistics
            values = [entry['value'] for entry in history]
            unique_values = list(set(values))
            
            return {
                'count': len(values),
                'unique_values': len(unique_values),
                'most_common': max(unique_values, key=values.count) if unique_values else None,
                'data_type': data_type,
                'latest_value': values[0] if values else None  # Most recent first
            }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for numerical values"""
        if len(values) < 2:
            return 'insufficient_data'
        
        # Simple trend calculation using first and last quartiles
        n = len(values)
        first_quarter = values[:n//4] if n >= 4 else values[:1]
        last_quarter = values[-n//4:] if n >= 4 else values[-1:]
        
        if not first_quarter or not last_quarter:
            return 'insufficient_data'
        
        first_avg = sum(first_quarter) / len(first_quarter)
        last_avg = sum(last_quarter) / len(last_quarter)
        
        diff_percent = ((last_avg - first_avg) / first_avg * 100) if first_avg != 0 else 0
        
        if diff_percent > 5:
            return 'increasing'
        elif diff_percent < -5:
            return 'decreasing'
        else:
            return 'stable'
    
    def get_metrics_for_date(self, date: str = None) -> Dict[str, List[Dict]]:
        """Get all metrics logged for a specific date"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT habit_name, metric_name, value, data_type
                FROM habit_metrics 
                WHERE date = ?
                ORDER BY habit_name, metric_name
            ''', (date,))
            
            results = cursor.fetchall()
            
            # Group by habit
            metrics_by_habit = {}
            for row in results:
                habit_name = row[0]
                if habit_name not in metrics_by_habit:
                    metrics_by_habit[habit_name] = []
                
                metrics_by_habit[habit_name].append({
                    'metric_name': row[1],
                    'value': row[2],
                    'data_type': row[3]
                })
            
            return metrics_by_habit
            
        except sqlite3.Error as e:
            print(f"Error getting metrics for date: {e}")
            return {}
        finally:
            conn.close()
    
    def get_missing_metrics_for_date(self, date: str = None) -> Dict[str, List[str]]:
        """Get metrics that are defined but not logged for a date"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Get all defined metrics
        all_definitions = self.get_habit_metric_definitions()
        
        # Get logged metrics for the date
        logged_metrics = self.get_metrics_for_date(date)
        
        missing = {}
        for definition in all_definitions:
            habit_name = definition['habit_name']
            metric_name = definition['metric_name']
            
            # Check if this metric was logged
            habit_logged = logged_metrics.get(habit_name, [])
            logged_metric_names = [m['metric_name'] for m in habit_logged]
            
            if metric_name not in logged_metric_names:
                if habit_name not in missing:
                    missing[habit_name] = []
                missing[habit_name].append(metric_name)
        
        return missing
    
    def bulk_log_metrics(self, metrics_data: Dict[str, Dict[str, Any]], date: str = None) -> Dict[str, bool]:
        """Log multiple metrics at once"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        results = {}
        
        for habit_name, metrics in metrics_data.items():
            for metric_name, value in metrics.items():
                success = self.log_metric_value(habit_name, metric_name, value, date)
                results[f"{habit_name}.{metric_name}"] = success
        
        return results
    
    def export_metrics_data(self, habit_name: str = None, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Export metrics data for analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT hm.habit_name, hm.metric_name, hm.value, hm.data_type, hm.date, hm.timestamp,
                       hmd.description, hmd.unit, hmd.min_value, hmd.max_value
                FROM habit_metrics hm
                LEFT JOIN habit_metric_definitions hmd 
                ON hm.habit_name = hmd.habit_name AND hm.metric_name = hmd.metric_name
                WHERE 1=1
            '''
            params = []
            
            if habit_name:
                query += ' AND hm.habit_name = ?'
                params.append(habit_name)
            
            if start_date:
                query += ' AND hm.date >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND hm.date <= ?'
                params.append(end_date)
            
            query += ' ORDER BY hm.habit_name, hm.metric_name, hm.date'
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            return [
                {
                    'habit_name': row[0],
                    'metric_name': row[1],
                    'value': row[2],
                    'data_type': row[3],
                    'date': row[4],
                    'timestamp': row[5],
                    'description': row[6],
                    'unit': row[7],
                    'min_value': row[8],
                    'max_value': row[9]
                }
                for row in results
            ]
            
        except sqlite3.Error as e:
            print(f"Error exporting metrics data: {e}")
            return []
        finally:
            conn.close()
    
    def get_metric_correlation(self, habit1: str, metric1: str, habit2: str, metric2: str, days: int = 30) -> Dict:
        """Calculate correlation between two metrics"""
        history1 = self.get_metric_history(habit1, metric1, days)
        history2 = self.get_metric_history(habit2, metric2, days)
        
        if not history1 or not history2:
            return {'error': 'Insufficient data for correlation'}
        
        # Create date-indexed dictionaries
        data1 = {entry['date']: entry['value'] for entry in history1}
        data2 = {entry['date']: entry['value'] for entry in history2}
        
        # Find common dates
        common_dates = set(data1.keys()) & set(data2.keys())
        
        if len(common_dates) < 3:
            return {'error': 'Insufficient overlapping data points'}
        
        # Extract values for common dates
        try:
            values1 = [float(data1[date]) for date in common_dates]
            values2 = [float(data2[date]) for date in common_dates]
        except (ValueError, TypeError):
            return {'error': 'Non-numeric data cannot be correlated'}
        
        # Calculate Pearson correlation coefficient
        n = len(values1)
        sum1 = sum(values1)
        sum2 = sum(values2)
        sum1_sq = sum(x * x for x in values1)
        sum2_sq = sum(x * x for x in values2)
        sum_products = sum(x * y for x, y in zip(values1, values2))
        
        numerator = n * sum_products - sum1 * sum2
        denominator = ((n * sum1_sq - sum1 * sum1) * (n * sum2_sq - sum2 * sum2)) ** 0.5
        
        if denominator == 0:
            correlation = 0
        else:
            correlation = numerator / denominator
        
        # Interpret correlation strength
        abs_corr = abs(correlation)
        if abs_corr >= 0.7:
            strength = 'strong'
        elif abs_corr >= 0.3:
            strength = 'moderate'
        elif abs_corr >= 0.1:
            strength = 'weak'
        else:
            strength = 'negligible'
        
        direction = 'positive' if correlation > 0 else 'negative' if correlation < 0 else 'none'
        
        return {
            'correlation': correlation,
            'strength': strength,
            'direction': direction,
            'data_points': n,
            'metric1': f"{habit1}.{metric1}",
            'metric2': f"{habit2}.{metric2}"
        }


# Global instance for easy access
habit_metrics_manager = HabitMetricsManager()


# Convenience functions
def add_metric_to_habit(habit_name: str, metric_name: str, data_type: str, **kwargs) -> bool:
    """Add a metric to a habit"""
    return habit_metrics_manager.add_metric_to_habit(habit_name, metric_name, data_type, **kwargs)


def log_metric_value(habit_name: str, metric_name: str, value: Any, date: str = None) -> bool:
    """Log a metric value"""
    return habit_metrics_manager.log_metric_value(habit_name, metric_name, value, date)


def get_metric_history(habit_name: str, metric_name: str, days: int = 30) -> List[Dict]:
    """Get metric history"""
    return habit_metrics_manager.get_metric_history(habit_name, metric_name, days)


def get_metric_statistics(habit_name: str, metric_name: str, days: int = 30) -> Dict:
    """Get metric statistics"""
    return habit_metrics_manager.get_metric_statistics(habit_name, metric_name, days)


def get_missing_metrics_for_today() -> Dict[str, List[str]]:
    """Get missing metrics for today"""
    return habit_metrics_manager.get_missing_metrics_for_date()


def bulk_log_metrics(metrics_data: Dict[str, Dict[str, Any]], date: str = None) -> Dict[str, bool]:
    """Bulk log metrics"""
    return habit_metrics_manager.bulk_log_metrics(metrics_data, date)


if __name__ == "__main__":
    # Test the habit metrics manager
    print("Testing Habit Metrics Manager...")
    
    manager = HabitMetricsManager()
    
    # Add some test metrics
    manager.add_metric_to_habit('exercise', 'weight', 'float', 'Body weight', 'kg', 40.0, 200.0)
    manager.add_metric_to_habit('exercise', 'duration', 'int', 'Exercise duration', 'minutes', 0, 300)
    manager.add_metric_to_habit('sleep', 'hours', 'float', 'Sleep duration', 'hours', 0.0, 24.0)
    manager.add_metric_to_habit('mood', 'rating', 'int', 'Mood rating', 'scale', 1, 10)
    
    # Log some test values
    manager.log_metric_value('exercise', 'weight', 75.5)
    manager.log_metric_value('exercise', 'duration', 45)
    manager.log_metric_value('sleep', 'hours', 7.5)
    manager.log_metric_value('mood', 'rating', 8)
    
    # Get statistics
    weight_stats = manager.get_metric_statistics('exercise', 'weight')
    print(f"Weight statistics: {weight_stats}")
    
    # Get missing metrics
    missing = manager.get_missing_metrics_for_date()
    print(f"Missing metrics: {missing}")
    
    print("Habit Metrics Manager test completed!")