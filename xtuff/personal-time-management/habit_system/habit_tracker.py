#!/usr/bin/env python3
"""
Habit Promotion System
Research-based automatic promotion/demotion of habits between intermittent and consistent categories
Based on peer-reviewed studies on habit formation and automaticity

Research Foundation:
- Lally et al. (2010): "How are habits formed: Modelling habit formation in the real world"
- Gardner et al. (2012): "Make health habitual: the psychology of 'habit-formation' and general practice"
- Wood & Neal (2007): "A new look at habits and the habit-goal interface"
- Verplanken & Aarts (1999): "Habit, attitude, and planned behaviour"
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import sys
import os

# Add config to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config.settings import config


class HabitPromotionSystem:
    def __init__(self, db_path='daily_engine.db'):
        self.db_path = db_path

        # Research-based criteria thresholds
        self.PROMOTION_CRITERIA = {
            # Lally et al. (2010): Average 66 days to automaticity, range 18-254 days
            'min_tracking_days': 21,  # Minimum observation period
            'promotion_threshold_days': 66,  # Optimal automaticity period
            'consistency_rate_promotion': 0.80,  # 80% consistency for promotion
            'streak_stability_promotion': 14,  # Sustained 2-week streaks

            # Demotion criteria - Gardner et al. (2012): automaticity decay
            'demotion_threshold_days': 30,  # Period to assess decline
            'consistency_rate_demotion': 0.40,  # Below 40% suggests lost automaticity
            'streak_decline_demotion': 7,  # Max streak under 1 week indicates decline
        }

    def log_habit_completion(self, habit_name: str, completed: bool):
        """Log habit completion to database with improved streak calculation"""
        today = datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if entry exists
        cursor.execute('SELECT id FROM habit_tracking WHERE habit_name = ? AND date = ?', (habit_name, today))
        existing = cursor.fetchone()

        if existing:
            # Update existing entry
            cursor.execute('''
                UPDATE habit_tracking 
                SET completed = ?
                WHERE habit_name = ? AND date = ?
            ''', (completed, habit_name, today))
        else:
            # Calculate proper streak count
            current_streak = self._calculate_current_streak_for_logging(habit_name, completed)

            # Create new entry
            cursor.execute('''
                INSERT INTO habit_tracking (habit_name, date, completed, streak_count)
                VALUES (?, ?, ?, ?)
            ''', (habit_name, today, completed, current_streak))

        conn.commit()
        conn.close()

    def _calculate_current_streak_for_logging(self, habit_name: str, completed_today: bool) -> int:
        """Calculate current streak for logging purposes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get recent records excluding today
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT date, completed FROM habit_tracking 
            WHERE habit_name = ? AND date <= ?
            ORDER BY date DESC
            LIMIT 30
        ''', (habit_name, yesterday))

        records = cursor.fetchall()
        conn.close()

        if not completed_today:
            return 0

        # Count consecutive completed days working backwards
        streak = 1  # Today counts as 1
        for date_str, completed in records:
            if completed:
                streak += 1
            else:
                break

        return streak

    def analyze_habit_performance(self, habit_name: str) -> Dict:
        """
        Analyze habit performance using research-based metrics
        Returns comprehensive habit analysis including promotion/demotion recommendation

        Based on:
        - Lally et al. (2010): Automaticity development timeline
        - Gardner et al. (2012): Self-report habit index validation
        - Wood & Neal (2007): Context-dependent automaticity
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get habit tracking data for analysis period
        analysis_end = datetime.now()
        analysis_start = analysis_end - timedelta(days=self.PROMOTION_CRITERIA['promotion_threshold_days'])

        cursor.execute('''
            SELECT date, completed, streak_count 
            FROM habit_tracking 
            WHERE habit_name = ? AND date >= ? AND date <= ?
            ORDER BY date ASC
        ''', (habit_name, analysis_start.strftime('%Y-%m-%d'), analysis_end.strftime('%Y-%m-%d')))

        records = cursor.fetchall()
        conn.close()

        if not records:
            return {'recommendation': 'insufficient_data', 'metrics': {}}

        # Calculate research-based metrics
        metrics = self._calculate_habit_metrics(records)

        # Determine current category
        current_habits = config.get_habits()
        current_category = 'consistent' if habit_name in current_habits['consistent'] else 'intermittent'

        # Generate recommendation based on research criteria
        recommendation = self._generate_recommendation(metrics, current_category)

        return {
            'habit_name': habit_name,
            'current_category': current_category,
            'recommendation': recommendation,
            'metrics': metrics,
            'confidence_score': self._calculate_confidence_score(metrics),
            'research_basis': self._get_research_explanation(recommendation, metrics)
        }

    def _calculate_habit_metrics(self, records: List[Tuple]) -> Dict:
        """Calculate research-based habit strength metrics"""
        if not records:
            return {}

        total_days = len(records)
        completed_days = sum(1 for _, completed, _ in records if completed)
        consistency_rate = completed_days / total_days if total_days > 0 else 0

        # Calculate streak metrics
        streaks = self._extract_streaks(records)
        max_streak = max(streaks) if streaks else 0
        avg_streak = sum(streaks) / len(streaks) if streaks else 0

        # Calculate stability (consistency over time periods)
        stability_score = self._calculate_stability(records)

        # Calculate automaticity indicators
        recent_performance = self._calculate_recent_performance(records, days=14)
        trend_score = self._calculate_trend(records)

        return {
            'total_tracking_days': total_days,
            'completed_days': completed_days,
            'consistency_rate': consistency_rate,
            'max_streak': max_streak,
            'average_streak': avg_streak,
            'stability_score': stability_score,
            'recent_performance': recent_performance,
            'trend_score': trend_score,
            'streak_count': len(streaks)
        }

    def _extract_streaks(self, records: List[Tuple]) -> List[int]:
        """Extract all streaks from habit records"""
        streaks = []
        current_streak = 0

        for _, completed, _ in records:
            if completed:
                current_streak += 1
            else:
                if current_streak > 0:
                    streaks.append(current_streak)
                current_streak = 0

        # Don't forget the final streak if it ends with completion
        if current_streak > 0:
            streaks.append(current_streak)

        return streaks

    def _calculate_stability(self, records: List[Tuple]) -> float:
        """
        Calculate stability score based on consistent performance across time periods
        Research: Wood & Neal (2007) - stable context-behavior associations
        """
        if len(records) < 14:
            return 0.0

        # Divide into weekly chunks and calculate consistency within each
        weekly_performances = []
        for i in range(0, len(records), 7):
            week_records = records[i:i + 7]
            week_completed = sum(1 for _, completed, _ in week_records if completed)
            week_consistency = week_completed / len(week_records)
            weekly_performances.append(week_consistency)

        if len(weekly_performances) < 2:
            return 0.0

        # Calculate standard deviation (lower = more stable)
        mean_performance = sum(weekly_performances) / len(weekly_performances)
        variance = sum((x - mean_performance) ** 2 for x in weekly_performances) / len(weekly_performances)
        std_dev = variance ** 0.5

        # Convert to stability score (0-1, higher = more stable)
        stability_score = max(0, 1 - (std_dev * 2))  # Scale standard deviation
        return stability_score

    def _calculate_recent_performance(self, records: List[Tuple], days: int = 14) -> float:
        """Calculate performance in recent period (automaticity indicator)"""
        if len(records) < days:
            return 0.0

        recent_records = records[-days:]
        completed = sum(1 for _, completed, _ in recent_records if completed)
        return completed / len(recent_records)

    def _calculate_trend(self, records: List[Tuple]) -> float:
        """
        Calculate performance trend (improving, stable, declining)
        Returns: 1.0 (improving), 0.0 (stable), -1.0 (declining)
        """
        if len(records) < 14:
            return 0.0

        mid_point = len(records) // 2
        first_half = records[:mid_point]
        second_half = records[mid_point:]

        first_rate = sum(1 for _, completed, _ in first_half if completed) / len(first_half)
        second_rate = sum(1 for _, completed, _ in second_half if completed) / len(second_half)

        difference = second_rate - first_rate

        # Normalize to -1 to 1 scale
        if abs(difference) < 0.1:  # Stable (less than 10% change)
            return 0.0
        elif difference > 0:
            return min(1.0, difference * 2)  # Improving
        else:
            return max(-1.0, difference * 2)  # Declining

    def _generate_recommendation(self, metrics: Dict, current_category: str) -> str:
        """Generate promotion/demotion recommendation based on research criteria"""
        if metrics['total_tracking_days'] < self.PROMOTION_CRITERIA['min_tracking_days']:
            return 'insufficient_data'

        consistency_rate = metrics['consistency_rate']
        max_streak = metrics['max_streak']
        stability_score = metrics['stability_score']
        recent_performance = metrics['recent_performance']
        trend_score = metrics['trend_score']

        if current_category == 'intermittent':
            # Check for promotion to consistent
            promotion_indicators = [
                metrics['total_tracking_days'] >= self.PROMOTION_CRITERIA['promotion_threshold_days'],
                consistency_rate >= self.PROMOTION_CRITERIA['consistency_rate_promotion'],
                max_streak >= self.PROMOTION_CRITERIA['streak_stability_promotion'],
                stability_score >= 0.7,  # High stability
                recent_performance >= 0.75,  # Strong recent performance
                trend_score >= 0.0  # Not declining
            ]

            # Research: Gardner et al. (2012) - multiple indicators needed for automaticity
            if sum(promotion_indicators) >= 4:  # Most criteria met
                return 'promote_to_consistent'
            elif sum(promotion_indicators) >= 3:
                return 'consider_promotion'
            else:
                return 'maintain_intermittent'

        else:  # current_category == 'consistent'
            # Check for demotion to intermittent
            demotion_indicators = [
                consistency_rate < self.PROMOTION_CRITERIA['consistency_rate_demotion'],
                max_streak < self.PROMOTION_CRITERIA['streak_decline_demotion'],
                stability_score < 0.3,  # Low stability
                recent_performance < 0.5,  # Poor recent performance
                trend_score < -0.3  # Declining trend
            ]

            # Research: Wood & Neal (2007) - habits can decay without regular practice
            if sum(demotion_indicators) >= 3:  # Multiple decay indicators
                return 'demote_to_intermittent'
            elif sum(demotion_indicators) >= 2:
                return 'consider_demotion'
            else:
                return 'maintain_consistent'

    def _calculate_confidence_score(self, metrics: Dict) -> float:
        """Calculate confidence in recommendation based on data quality"""
        if not metrics:
            return 0.0

        # Factors affecting confidence
        data_sufficiency = min(1.0, metrics['total_tracking_days'] / 66)  # More data = higher confidence
        consistency_clarity = abs(metrics['consistency_rate'] - 0.5) * 2  # Clear high/low performance
        stability_factor = metrics.get('stability_score', 0)

        confidence = (data_sufficiency + consistency_clarity + stability_factor) / 3
        return min(1.0, confidence)

    def _get_research_explanation(self, recommendation: str, metrics: Dict) -> str:
        """Provide research-based explanation for recommendation"""
        explanations = {
            'promote_to_consistent': f"Research indicates automaticity development: {metrics['consistency_rate']:.1%} consistency over {metrics['total_tracking_days']} days exceeds Lally et al. (2010) thresholds for habit formation.",

            'consider_promotion': f"Approaching automaticity criteria from Gardner et al. (2012): Strong consistency ({metrics['consistency_rate']:.1%}) but may benefit from longer observation period.",

            'maintain_intermittent': f"Performance below automaticity thresholds: {metrics['consistency_rate']:.1%} consistency suggests behavior not yet automatic per habit formation research.",

            'demote_to_intermittent': f"Wood & Neal (2007) habit decay indicators present: {metrics['consistency_rate']:.1%} recent consistency suggests lost automaticity.",

            'consider_demotion': f"Some decline indicators present but not conclusive. Monitor for continued performance decrease per habit maintenance research.",

            'maintain_consistent': f"Stable automatic behavior: {metrics['consistency_rate']:.1%} consistency and {metrics.get('stability_score', 0):.1%} stability support continued consistent categorization.",

            'insufficient_data': f"Requires minimum {self.PROMOTION_CRITERIA['min_tracking_days']} days tracking for reliable habit analysis per research protocols."
        }

        return explanations.get(recommendation, "Research-based analysis inconclusive.")

    def execute_habit_promotion(self, habit_name: str, force: bool = False) -> Dict:
        """Execute habit promotion/demotion with config file update"""
        analysis = self.analyze_habit_performance(habit_name)
        recommendation = analysis['recommendation']

        if not force and recommendation not in ['promote_to_consistent', 'demote_to_intermittent']:
            return {
                'executed': False,
                'reason': f"Recommendation '{recommendation}' does not warrant automatic change",
                'analysis': analysis
            }

        try:
            # Load current config
            current_habits = config.get_habits()

            if recommendation == 'promote_to_consistent':
                # Move from intermittent to consistent
                if habit_name in current_habits['intermittent']:
                    current_habits['intermittent'].remove(habit_name)
                    current_habits['consistent'].append(habit_name)

                    # Update config
                    config.set('habits.consistent', current_habits['consistent'])
                    config.set('habits.intermittent', current_habits['intermittent'])

                    return {
                        'executed': True,
                        'action': 'promoted_to_consistent',
                        'habit': habit_name,
                        'analysis': analysis
                    }

            elif recommendation == 'demote_to_intermittent':
                # Move from consistent to intermittent
                if habit_name in current_habits['consistent']:
                    current_habits['consistent'].remove(habit_name)
                    current_habits['intermittent'].append(habit_name)

                    # Update config
                    config.set('habits.consistent', current_habits['consistent'])
                    config.set('habits.intermittent', current_habits['intermittent'])

                    return {
                        'executed': True,
                        'action': 'demoted_to_intermittent',
                        'habit': habit_name,
                        'analysis': analysis
                    }

        except Exception as e:
            return {
                'executed': False,
                'error': str(e),
                'analysis': analysis
            }

        return {
            'executed': False,
            'reason': 'No action taken',
            'analysis': analysis
        }

    def analyze_all_habits(self) -> Dict[str, Dict]:
        """Analyze all habits and return recommendations"""
        current_habits = config.get_habits()
        all_habits = current_habits['consistent'] + current_habits['intermittent']

        analyses = {}
        for habit in all_habits:
            analyses[habit] = self.analyze_habit_performance(habit)

        return analyses

    def execute_all_promotions(self, auto_execute: bool = False) -> Dict:
        """Analyze all habits and execute promotions/demotions"""
        analyses = self.analyze_all_habits()
        results = {
            'executed_changes': [],
            'recommended_changes': [],
            'no_changes': [],
            'insufficient_data': []
        }

        for habit_name, analysis in analyses.items():
            recommendation = analysis['recommendation']

            if recommendation in ['promote_to_consistent', 'demote_to_intermittent']:
                if auto_execute:
                    result = self.execute_habit_promotion(habit_name)
                    if result['executed']:
                        results['executed_changes'].append(result)
                    else:
                        results['recommended_changes'].append({
                            'habit': habit_name,
                            'recommendation': recommendation,
                            'analysis': analysis
                        })
                else:
                    results['recommended_changes'].append({
                        'habit': habit_name,
                        'recommendation': recommendation,
                        'analysis': analysis
                    })

            elif recommendation == 'insufficient_data':
                results['insufficient_data'].append(habit_name)

            else:
                results['no_changes'].append(habit_name)

        return results

    def generate_promotion_report(self) -> str:
        """Generate a comprehensive habit promotion analysis report"""
        results = self.execute_all_promotions(auto_execute=False)

        report = f"""
# 🧠 Habit Promotion Analysis Report
*Based on peer-reviewed research on habit formation and automaticity*

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Research Foundation
This analysis uses criteria from:
- **Lally et al. (2010)**: Average 66 days to automaticity
- **Gardner et al. (2012)**: Self-report habit index validation
- **Wood & Neal (2007)**: Context-dependent automaticity
- **Verplanken & Aarts (1999)**: Habit measurement and characteristics

## Promotion Recommendations

### 🔥 Ready for Promotion to Consistent
"""

        promotion_candidates = [r for r in results['recommended_changes']
                                if r['recommendation'] == 'promote_to_consistent']

        if promotion_candidates:
            for candidate in promotion_candidates:
                habit = candidate['habit']
                metrics = candidate['analysis']['metrics']
                confidence = candidate['analysis']['confidence_score']

                report += f"""
**{habit.replace('_', ' ').title()}**
- Consistency Rate: {metrics['consistency_rate']:.1%}
- Max Streak: {metrics['max_streak']} days
- Stability Score: {metrics.get('stability_score', 0):.1%}
- Recent Performance: {metrics['recent_performance']:.1%}
- Confidence: {confidence:.1%}
- Research Basis: {candidate['analysis']['research_basis']}
"""
        else:
            report += "\nNo habits currently meet promotion criteria.\n"

        report += """
### ⚠️ Consider Demotion to Intermittent
"""

        demotion_candidates = [r for r in results['recommended_changes']
                               if r['recommendation'] == 'demote_to_intermittent']

        if demotion_candidates:
            for candidate in demotion_candidates:
                habit = candidate['habit']
                metrics = candidate['analysis']['metrics']
                confidence = candidate['analysis']['confidence_score']

                report += f"""
**{habit.replace('_', ' ').title()}**
- Consistency Rate: {metrics['consistency_rate']:.1%}
- Recent Performance: {metrics['recent_performance']:.1%}
- Trend: {'Declining' if metrics['trend_score'] < -0.1 else 'Stable' if metrics['trend_score'] < 0.1 else 'Improving'}
- Max Streak: {metrics['max_streak']} days
- Confidence: {confidence:.1%}
- Research Basis: {candidate['analysis']['research_basis']}
"""
        else:
            report += "\nNo consistent habits show decline requiring demotion.\n"

        report += f"""
### 📊 Habits Under Consideration
"""
        consideration_habits = [r for r in results['recommended_changes']
                                if r['recommendation'] in ['consider_promotion', 'consider_demotion']]

        if consideration_habits:
            for candidate in consideration_habits:
                habit = candidate['habit']
                recommendation = candidate['recommendation']
                metrics = candidate['analysis']['metrics']

                action = "promotion" if "promotion" in recommendation else "demotion"
                report += f"""
**{habit.replace('_', ' ').title()}** (Consider {action})
- Consistency: {metrics['consistency_rate']:.1%}
- Trend: {'📈' if metrics['trend_score'] > 0.1 else '📉' if metrics['trend_score'] < -0.1 else '➡️'}
- Note: {candidate['analysis']['research_basis']}
"""

        report += f"""
## Summary Statistics
- **Total habits analyzed**: {len(results['executed_changes']) + len(results['recommended_changes']) + len(results['no_changes']) + len(results['insufficient_data'])}
- **Promotion candidates**: {len(promotion_candidates)}
- **Demotion candidates**: {len(demotion_candidates)}
- **Under consideration**: {len(consideration_habits)}
- **Stable habits**: {len(results['no_changes'])}
- **Insufficient data**: {len(results['insufficient_data'])}

## Implementation Guidelines

### For Promotions
1. **Execute immediately**: Habits meeting all research criteria
2. **Monitor closely**: Habits under consideration for promotion
3. **Continue tracking**: Habits with insufficient data

### For Demotions
1. **Review context**: Consider external factors affecting performance
2. **Implement gradually**: Allow transition period for habit re-establishment
3. **Set reminders**: Increase environmental cues and support

### Research Notes
- **Automaticity timeline**: Most habits require 66+ days for full automation
- **Individual variation**: Range can be 18-254 days depending on complexity
- **Context dependency**: Environmental consistency crucial for maintenance
- **Decay patterns**: Habits can lose automaticity without regular practice

## Next Steps
1. Review promotion/demotion recommendations above
2. Execute changes using the habit promotion system
3. Continue tracking for habits with insufficient data
4. Monitor demoted habits for re-promotion opportunities
5. Schedule monthly reviews for ongoing optimization

---
*This analysis follows evidence-based criteria from peer-reviewed habit formation research.*
"""

        return report


# Global instance for easy access
habit_system = HabitPromotionSystem()


# Convenience functions for external use
def log_habit_completion(habit_name: str, completed: bool):
    """Log habit completion to database"""
    return habit_system.log_habit_completion(habit_name, completed)


def analyze_habit_promotions() -> Dict:
    """Analyze all habits for promotion/demotion opportunities"""
    return habit_system.execute_all_promotions(auto_execute=False)


def execute_habit_promotion(habit_name: str, force: bool = False) -> Dict:
    """Execute habit promotion/demotion for a specific habit"""
    return habit_system.execute_habit_promotion(habit_name, force)


def generate_habit_promotion_report() -> str:
    """Generate comprehensive habit promotion analysis report"""
    return habit_system.generate_promotion_report()


def get_habit_analysis(habit_name: str) -> Dict:
    """Get detailed analysis for a specific habit"""
    return habit_system.analyze_habit_performance(habit_name)


def test_habit_promotion_system():
    """Test function for the habit promotion system"""
    print("Testing Habit Promotion System...")

    # Test individual habit analysis
    print("\n1. Testing individual habit analysis...")
    current_habits = config.get_habits()
    if current_habits['intermittent']:
        test_habit = current_habits['intermittent'][0]
        analysis = get_habit_analysis(test_habit)
        print(f"Analysis for '{test_habit}': {analysis['recommendation']}")
        print(f"Confidence: {analysis['confidence_score']:.1%}")

    # Test all habits analysis
    print("\n2. Testing all habits analysis...")
    results = analyze_habit_promotions()
    print(f"Promotion candidates: {len(results['recommended_changes'])}")
    print(f"Stable habits: {len(results['no_changes'])}")

    # Test report generation
    print("\n3. Testing report generation...")
    report = generate_habit_promotion_report()
    print(f"Report generated: {len(report)} characters")

    print("\nHabit Promotion System test completed!")


if __name__ == "__main__":
    test_habit_promotion_system()