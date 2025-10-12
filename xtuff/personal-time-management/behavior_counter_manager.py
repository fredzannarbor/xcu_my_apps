#!/usr/bin/env python3
"""
Behavior Counter Manager
Manages positive and negative behavior counters with trend analysis
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from database_extensions import DatabaseExtensions


class BehaviorCounterManager:
    """Manages positive and negative behavior counters"""
    
    def __init__(self, db_path='daily_engine.db'):
        self.db_path = db_path
        self.db_extensions = DatabaseExtensions(db_path)
    
    def create_positive_counter(self, name: str, description: str = None) -> bool:
        """Create a positive behavior counter"""
        return self.db_extensions.add_behavior_counter_definition(name, 'positive', description)
    
    def create_negative_counter(self, name: str, description: str = None) -> bool:
        """Create a negative behavior counter"""
        return self.db_extensions.add_behavior_counter_definition(name, 'negative', description)
    
    def increment_counter(self, counter_name: str, amount: int = 1, date: str = None) -> bool:
        """Increment a behavior counter"""
        return self.db_extensions.increment_behavior_counter(counter_name, amount, date)
    
    def get_daily_counts(self, date: str = None) -> Dict[str, Dict]:
        """Get daily counts for all counters"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT bc.counter_name, bc.counter_type, bc.count, bcd.description
                FROM behavior_counters bc
                LEFT JOIN behavior_counter_definitions bcd 
                ON bc.counter_name = bcd.counter_name
                WHERE bc.date = ?
                ORDER BY bc.counter_type, bc.counter_name
            ''', (date,))
            
            results = cursor.fetchall()
            
            daily_counts = {
                'positive': {},
                'negative': {},
                'date': date,
                'total_positive': 0,
                'total_negative': 0
            }
            
            for row in results:
                counter_name = row[0]
                counter_type = row[1]
                count = row[2]
                description = row[3]
                
                daily_counts[counter_type][counter_name] = {
                    'count': count,
                    'description': description
                }
                
                if counter_type == 'positive':
                    daily_counts['total_positive'] += count
                else:
                    daily_counts['total_negative'] += count
            
            return daily_counts
            
        except sqlite3.Error as e:
            print(f"Error getting daily counts: {e}")
            return {'positive': {}, 'negative': {}, 'date': date, 'total_positive': 0, 'total_negative': 0}
        finally:
            conn.close()
    
    def get_counter_trends(self, counter_name: str, days: int = 30) -> List[Dict]:
        """Get trend data for a specific counter"""
        return self.db_extensions.get_behavior_counter_data(counter_name, days)
    
    def get_all_counter_trends(self, days: int = 30) -> Dict[str, List[Dict]]:
        """Get trend data for all counters"""
        all_data = self.db_extensions.get_behavior_counter_data(None, days)
        
        # Group by counter name
        trends = {}
        for entry in all_data:
            counter_name = entry['counter_name']
            if counter_name not in trends:
                trends[counter_name] = []
            trends[counter_name].append(entry)
        
        return trends
    
    def get_counter_statistics(self, counter_name: str, days: int = 30) -> Dict:
        """Get statistical analysis of a counter"""
        trend_data = self.get_counter_trends(counter_name, days)
        
        if not trend_data:
            return {'error': 'No data available'}
        
        # Get counter definition
        definitions = self.db_extensions.get_behavior_counter_definitions()
        counter_def = next((d for d in definitions if d['counter_name'] == counter_name), None)
        
        if not counter_def:
            return {'error': 'Counter definition not found'}
        
        counts = [entry['count'] for entry in trend_data]
        dates = [entry['date'] for entry in trend_data]
        
        total_count = sum(counts)
        avg_daily = total_count / len(counts) if counts else 0
        max_daily = max(counts) if counts else 0
        min_daily = min(counts) if counts else 0
        
        # Calculate streaks
        streaks = self._calculate_streaks(trend_data)
        
        # Calculate trend
        trend_direction = self._calculate_counter_trend(counts)
        
        return {
            'counter_name': counter_name,
            'counter_type': counter_def['counter_type'],
            'description': counter_def['description'],
            'days_analyzed': len(counts),
            'total_count': total_count,
            'average_daily': round(avg_daily, 2),
            'max_daily': max_daily,
            'min_daily': min_daily,
            'current_streak': streaks['current_streak'],
            'longest_streak': streaks['longest_streak'],
            'streak_type': streaks['streak_type'],
            'trend_direction': trend_direction,
            'latest_count': counts[0] if counts else 0,  # Most recent first
            'latest_date': dates[0] if dates else None
        }
    
    def _calculate_streaks(self, trend_data: List[Dict]) -> Dict:
        """Calculate streak information for counter data"""
        if not trend_data:
            return {'current_streak': 0, 'longest_streak': 0, 'streak_type': 'none'}
        
        # Sort by date (most recent first)
        sorted_data = sorted(trend_data, key=lambda x: x['date'], reverse=True)
        
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        streak_type = 'none'
        
        # Determine streak type based on counter type
        definitions = self.db_extensions.get_behavior_counter_definitions()
        counter_name = sorted_data[0]['counter_name']
        counter_def = next((d for d in definitions if d['counter_name'] == counter_name), None)
        
        if not counter_def:
            return {'current_streak': 0, 'longest_streak': 0, 'streak_type': 'none'}
        
        counter_type = counter_def['counter_type']
        
        # For positive counters, streak = consecutive days with count > 0
        # For negative counters, streak = consecutive days with count = 0 (good streak)
        for i, entry in enumerate(sorted_data):
            count = entry['count']
            
            if counter_type == 'positive':
                # Positive behavior: streak when count > 0
                if count > 0:
                    temp_streak += 1
                    if i == 0:  # Current streak
                        current_streak = temp_streak
                else:
                    if i == 0:  # Current streak broken
                        current_streak = 0
                    longest_streak = max(longest_streak, temp_streak)
                    temp_streak = 0
                    streak_type = 'positive_behavior'
            else:
                # Negative behavior: streak when count = 0 (avoiding negative behavior)
                if count == 0:
                    temp_streak += 1
                    if i == 0:  # Current streak
                        current_streak = temp_streak
                else:
                    if i == 0:  # Current streak broken
                        current_streak = 0
                    longest_streak = max(longest_streak, temp_streak)
                    temp_streak = 0
                    streak_type = 'avoidance'
        
        # Don't forget the final streak
        longest_streak = max(longest_streak, temp_streak)
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'streak_type': streak_type
        }
    
    def _calculate_counter_trend(self, counts: List[int]) -> str:
        """Calculate trend direction for counter data"""
        if len(counts) < 3:
            return 'insufficient_data'
        
        # Use first and last third of data
        n = len(counts)
        first_third = counts[-n//3:] if n >= 3 else counts[-1:]  # Older data (end of list)
        last_third = counts[:n//3] if n >= 3 else counts[:1]     # Recent data (start of list)
        
        if not first_third or not last_third:
            return 'insufficient_data'
        
        first_avg = sum(first_third) / len(first_third)
        last_avg = sum(last_third) / len(last_third)
        
        if first_avg == 0 and last_avg == 0:
            return 'stable'
        
        if first_avg == 0:
            return 'increasing'
        
        change_percent = ((last_avg - first_avg) / first_avg) * 100
        
        if change_percent > 20:
            return 'increasing'
        elif change_percent < -20:
            return 'decreasing'
        else:
            return 'stable'
    
    def get_weekly_summary(self, start_date: str = None) -> Dict:
        """Get weekly summary of all counters"""
        if start_date is None:
            # Get current week (Monday to Sunday)
            today = datetime.now()
            days_since_monday = today.weekday()
            monday = today - timedelta(days=days_since_monday)
            start_date = monday.strftime('%Y-%m-%d')
        
        end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT bc.counter_name, bc.counter_type, bc.date, bc.count
                FROM behavior_counters bc
                LEFT JOIN behavior_counter_definitions bcd 
                ON bc.counter_name = bcd.counter_name
                WHERE bc.date >= ? AND bc.date <= ?
                ORDER BY bc.counter_name, bc.date
            ''', (start_date, end_date))
            
            results = cursor.fetchall()
            
            # Group by counter
            weekly_data = {}
            for row in results:
                counter_name = row[0]
                counter_type = row[1]
                date = row[2]
                count = row[3]
                
                if counter_name not in weekly_data:
                    weekly_data[counter_name] = {
                        'counter_type': counter_type,
                        'daily_counts': {},
                        'total_count': 0,
                        'days_active': 0
                    }
                
                weekly_data[counter_name]['daily_counts'][date] = count
                weekly_data[counter_name]['total_count'] += count
                if count > 0:
                    weekly_data[counter_name]['days_active'] += 1
            
            return {
                'week_start': start_date,
                'week_end': end_date,
                'counters': weekly_data,
                'summary': self._generate_weekly_insights(weekly_data)
            }
            
        except sqlite3.Error as e:
            print(f"Error getting weekly summary: {e}")
            return {'week_start': start_date, 'week_end': end_date, 'counters': {}, 'summary': {}}
        finally:
            conn.close()
    
    def _generate_weekly_insights(self, weekly_data: Dict) -> Dict:
        """Generate insights from weekly data"""
        insights = {
            'total_positive_behaviors': 0,
            'total_negative_behaviors': 0,
            'most_active_positive': None,
            'most_active_negative': None,
            'best_avoidance': None,  # Negative behavior with lowest count
            'consistency_score': 0
        }
        
        positive_counters = []
        negative_counters = []
        
        for counter_name, data in weekly_data.items():
            if data['counter_type'] == 'positive':
                insights['total_positive_behaviors'] += data['total_count']
                positive_counters.append((counter_name, data['total_count'], data['days_active']))
            else:
                insights['total_negative_behaviors'] += data['total_count']
                negative_counters.append((counter_name, data['total_count'], data['days_active']))
        
        # Find most active counters
        if positive_counters:
            insights['most_active_positive'] = max(positive_counters, key=lambda x: x[1])
        
        if negative_counters:
            insights['most_active_negative'] = max(negative_counters, key=lambda x: x[1])
            insights['best_avoidance'] = min(negative_counters, key=lambda x: x[1])
        
        # Calculate consistency score (0-100)
        if weekly_data:
            total_possible_days = len(weekly_data) * 7  # 7 days per week
            total_active_days = sum(data['days_active'] for data in weekly_data.values())
            insights['consistency_score'] = round((total_active_days / total_possible_days) * 100, 1) if total_possible_days > 0 else 0
        
        return insights
    
    def bulk_increment_counters(self, counter_increments: Dict[str, int], date: str = None) -> Dict[str, bool]:
        """Increment multiple counters at once"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        results = {}
        for counter_name, amount in counter_increments.items():
            success = self.increment_counter(counter_name, amount, date)
            results[counter_name] = success
        
        return results
    
    def get_counter_definitions(self) -> List[Dict]:
        """Get all counter definitions"""
        return self.db_extensions.get_behavior_counter_definitions()
    
    def remove_counter_definition(self, counter_name: str) -> bool:
        """Remove a counter definition"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Remove definition
            cursor.execute('''
                DELETE FROM behavior_counter_definitions 
                WHERE counter_name = ?
            ''', (counter_name,))
            
            # Optionally remove historical data (commented out to preserve data)
            # cursor.execute('''
            #     DELETE FROM behavior_counters 
            #     WHERE counter_name = ?
            # ''', (counter_name,))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"Error removing counter definition: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def export_counter_data(self, counter_name: str = None, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Export counter data for analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT bc.counter_name, bc.counter_type, bc.date, bc.count, bc.timestamp,
                       bcd.description
                FROM behavior_counters bc
                LEFT JOIN behavior_counter_definitions bcd 
                ON bc.counter_name = bcd.counter_name
                WHERE 1=1
            '''
            params = []
            
            if counter_name:
                query += ' AND bc.counter_name = ?'
                params.append(counter_name)
            
            if start_date:
                query += ' AND bc.date >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND bc.date <= ?'
                params.append(end_date)
            
            query += ' ORDER BY bc.counter_name, bc.date'
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            return [
                {
                    'counter_name': row[0],
                    'counter_type': row[1],
                    'date': row[2],
                    'count': row[3],
                    'timestamp': row[4],
                    'description': row[5]
                }
                for row in results
            ]
            
        except sqlite3.Error as e:
            print(f"Error exporting counter data: {e}")
            return []
        finally:
            conn.close()


# Global instance for easy access
behavior_counter_manager = BehaviorCounterManager()


# Convenience functions
def create_positive_counter(name: str, description: str = None) -> bool:
    """Create a positive behavior counter"""
    return behavior_counter_manager.create_positive_counter(name, description)


def create_negative_counter(name: str, description: str = None) -> bool:
    """Create a negative behavior counter"""
    return behavior_counter_manager.create_negative_counter(name, description)


def increment_counter(counter_name: str, amount: int = 1, date: str = None) -> bool:
    """Increment a behavior counter"""
    return behavior_counter_manager.increment_counter(counter_name, amount, date)


def get_daily_counts(date: str = None) -> Dict[str, Dict]:
    """Get daily counts for all counters"""
    return behavior_counter_manager.get_daily_counts(date)


def get_counter_statistics(counter_name: str, days: int = 30) -> Dict:
    """Get counter statistics"""
    return behavior_counter_manager.get_counter_statistics(counter_name, days)


def get_weekly_summary(start_date: str = None) -> Dict:
    """Get weekly summary"""
    return behavior_counter_manager.get_weekly_summary(start_date)


def bulk_increment_counters(counter_increments: Dict[str, int], date: str = None) -> Dict[str, bool]:
    """Bulk increment counters"""
    return behavior_counter_manager.bulk_increment_counters(counter_increments, date)


if __name__ == "__main__":
    # Test the behavior counter manager
    print("Testing Behavior Counter Manager...")
    
    manager = BehaviorCounterManager()
    
    # Create test counters
    manager.create_positive_counter('healthy_eating', 'Healthy eating choices made')
    manager.create_positive_counter('exercise_sessions', 'Exercise sessions completed')
    manager.create_negative_counter('binge_eating', 'Binge eating episodes')
    manager.create_negative_counter('procrastination', 'Times procrastinated on important tasks')
    
    # Increment some counters
    manager.increment_counter('healthy_eating', 3)
    manager.increment_counter('exercise_sessions', 1)
    manager.increment_counter('binge_eating', 1)
    
    # Get daily counts
    daily = manager.get_daily_counts()
    print(f"Daily counts: {daily}")
    
    # Get statistics
    stats = manager.get_counter_statistics('healthy_eating')
    print(f"Healthy eating stats: {stats}")
    
    # Get weekly summary
    weekly = manager.get_weekly_summary()
    print(f"Weekly summary: {weekly}")
    
    print("Behavior Counter Manager test completed!")