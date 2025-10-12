#!/usr/bin/env python3
"""
Enhanced Habit Promotion System
Extends the existing promotion system with behavior counters and metrics integration
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import sys
import os

# Import existing system
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from habits.habit_tracker import HabitPromotionSystem
from behavior_counter_manager import BehaviorCounterManager
from habit_metrics_manager import HabitMetricsManager


class EnhancedPromotionSystem(HabitPromotionSystem):
    """Enhanced habit promotion system with behavior counters and metrics integration"""
    
    def __init__(self, db_path='daily_engine.db'):
        super().__init__(db_path)
        self.behavior_manager = BehaviorCounterManager(db_path)
        self.metrics_manager = HabitMetricsManager(db_path)
        
        # Enhanced criteria thresholds
        self.ENHANCED_CRITERIA = {
            # Behavior influence weights
            'positive_behavior_weight': 0.3,  # 30% influence from positive behaviors
            'negative_behavior_weight': 0.2,  # 20% penalty from negative behaviors
            'metrics_consistency_weight': 0.2,  # 20% influence from metrics consistency
            
            # Behavior thresholds
            'positive_behavior_threshold': 5,  # Weekly positive behavior count for bonus
            'negative_behavior_penalty_threshold': 3,  # Weekly negative behavior count for penalty
            'negative_streak_demotion_threshold': 7,  # Consecutive days of negative behavior
            
            # Metrics consistency thresholds
            'metrics_logging_consistency': 0.8,  # 80% of days should have metrics logged
            'metrics_improvement_bonus': 0.1,  # Bonus for improving metrics trends
        }
    
    def analyze_habit_performance(self, habit_name: str) -> Dict:
        """Enhanced habit analysis including behavior counters and metrics"""
        # Get base analysis from parent class
        base_analysis = super().analyze_habit_performance(habit_name)
        
        if base_analysis['recommendation'] == 'insufficient_data':
            return base_analysis
        
        # Add enhanced analysis
        behavior_influence = self.calculate_behavior_influence(habit_name)
        metrics_influence = self.calculate_metrics_influence(habit_name)
        negative_behavior_analysis = self.analyze_negative_behavior_patterns(habit_name)
        
        # Combine all factors for enhanced recommendation
        enhanced_recommendation = self._generate_enhanced_recommendation(
            base_analysis, behavior_influence, metrics_influence, negative_behavior_analysis
        )
        
        # Add enhanced data to analysis
        base_analysis.update({
            'behavior_influence': behavior_influence,
            'metrics_influence': metrics_influence,
            'negative_behavior_analysis': negative_behavior_analysis,
            'enhanced_recommendation': enhanced_recommendation,
            'enhancement_factors': self._calculate_enhancement_factors(
                behavior_influence, metrics_influence, negative_behavior_analysis
            )
        })
        
        return base_analysis
    
    def calculate_behavior_influence(self, habit_name: str) -> Dict:
        """Calculate influence of behavior counters on habit promotion"""
        analysis_end = datetime.now()
        analysis_start = analysis_end - timedelta(days=30)  # 30-day analysis window
        
        # Get related behavior counters (those that might influence this habit)
        related_counters = self._identify_related_counters(habit_name)
        
        if not related_counters:
            return {
                'positive_influence': 0.0,
                'negative_influence': 0.0,
                'overall_influence': 0.0,
                'related_counters': []
            }
        
        positive_influence = 0.0
        negative_influence = 0.0
        counter_details = []
        
        for counter_name, counter_type in related_counters:
            stats = self.behavior_manager.get_counter_statistics(counter_name, 30)
            
            if 'error' in stats:
                continue
            
            counter_detail = {
                'counter_name': counter_name,
                'counter_type': counter_type,
                'total_count': stats['total_count'],
                'average_daily': stats['average_daily'],
                'current_streak': stats['current_streak'],
                'trend_direction': stats['trend_direction']
            }
            
            if counter_type == 'positive':
                # Positive behaviors boost promotion chances
                weekly_average = stats['total_count'] / 4.3  # ~30 days / 7 days per week
                if weekly_average >= self.ENHANCED_CRITERIA['positive_behavior_threshold']:
                    influence = min(0.5, weekly_average / 10)  # Cap at 0.5
                    positive_influence += influence
                    counter_detail['influence'] = influence
                else:
                    counter_detail['influence'] = 0.0
            
            else:  # negative
                # Negative behaviors reduce promotion chances
                weekly_average = stats['total_count'] / 4.3
                if weekly_average >= self.ENHANCED_CRITERIA['negative_behavior_penalty_threshold']:
                    penalty = min(0.4, weekly_average / 15)  # Cap penalty at 0.4
                    negative_influence += penalty
                    counter_detail['influence'] = -penalty
                else:
                    counter_detail['influence'] = 0.0
            
            counter_details.append(counter_detail)
        
        overall_influence = (positive_influence * self.ENHANCED_CRITERIA['positive_behavior_weight'] - 
                           negative_influence * self.ENHANCED_CRITERIA['negative_behavior_weight'])
        
        return {
            'positive_influence': positive_influence,
            'negative_influence': negative_influence,
            'overall_influence': overall_influence,
            'related_counters': counter_details
        }
    
    def calculate_metrics_influence(self, habit_name: str) -> Dict:
        """Calculate influence of habit metrics on promotion"""
        # Get metrics definitions for this habit
        metric_definitions = self.metrics_manager.get_habit_metric_definitions(habit_name)
        
        if not metric_definitions:
            return {
                'consistency_score': 0.0,
                'improvement_score': 0.0,
                'overall_influence': 0.0,
                'metrics_analyzed': []
            }
        
        total_consistency = 0.0
        total_improvement = 0.0
        metrics_analyzed = []
        
        for metric_def in metric_definitions:
            metric_name = metric_def['metric_name']
            
            # Get metric history
            history = self.metrics_manager.get_metric_history(habit_name, metric_name, 30)
            
            if not history:
                continue
            
            # Calculate consistency (how often metrics are logged)
            days_with_data = len(set(entry['date'] for entry in history))
            consistency = days_with_data / 30.0  # 30-day window
            
            # Calculate improvement (for numerical metrics)
            improvement = 0.0
            if metric_def['data_type'] in ['int', 'float']:
                stats = self.metrics_manager.get_metric_statistics(habit_name, metric_name, 30)
                if 'trend' in stats:
                    if stats['trend'] == 'increasing':
                        improvement = 0.3
                    elif stats['trend'] == 'stable':
                        improvement = 0.1
                    # decreasing = 0.0 (no bonus)
            
            metrics_analyzed.append({
                'metric_name': metric_name,
                'consistency': consistency,
                'improvement': improvement,
                'data_points': len(history)
            })
            
            total_consistency += consistency
            total_improvement += improvement
        
        # Average across all metrics
        num_metrics = len(metrics_analyzed)
        if num_metrics > 0:
            avg_consistency = total_consistency / num_metrics
            avg_improvement = total_improvement / num_metrics
        else:
            avg_consistency = 0.0
            avg_improvement = 0.0
        
        # Calculate overall influence
        consistency_influence = (avg_consistency * self.ENHANCED_CRITERIA['metrics_consistency_weight'] 
                               if avg_consistency >= self.ENHANCED_CRITERIA['metrics_logging_consistency'] else 0.0)
        improvement_influence = avg_improvement * self.ENHANCED_CRITERIA['metrics_improvement_bonus']
        
        overall_influence = consistency_influence + improvement_influence
        
        return {
            'consistency_score': avg_consistency,
            'improvement_score': avg_improvement,
            'overall_influence': overall_influence,
            'metrics_analyzed': metrics_analyzed
        }
    
    def analyze_negative_behavior_patterns(self, habit_name: str) -> Dict:
        """Analyze negative behavior patterns that might affect habit promotion"""
        # Get related negative behavior counters
        related_counters = self._identify_related_counters(habit_name)
        negative_counters = [c for c in related_counters if c[1] == 'negative']
        
        if not negative_counters:
            return {
                'has_concerning_patterns': False,
                'streak_analysis': {},
                'demotion_risk': 0.0
            }
        
        concerning_patterns = False
        streak_analysis = {}
        total_demotion_risk = 0.0
        
        for counter_name, _ in negative_counters:
            stats = self.behavior_manager.get_counter_statistics(counter_name, 30)
            
            if 'error' in stats:
                continue
            
            # Analyze negative behavior streaks
            current_negative_streak = self._calculate_negative_behavior_streak(counter_name)
            
            streak_info = {
                'current_negative_streak': current_negative_streak,
                'total_count_30_days': stats['total_count'],
                'trend': stats['trend_direction']
            }
            
            # Check for concerning patterns
            if (current_negative_streak >= self.ENHANCED_CRITERIA['negative_streak_demotion_threshold'] or
                stats['trend_direction'] == 'increasing'):
                concerning_patterns = True
                
                # Calculate demotion risk
                streak_risk = min(0.5, current_negative_streak / 14)  # Max 0.5 for 2-week streak
                trend_risk = 0.2 if stats['trend_direction'] == 'increasing' else 0.0
                total_demotion_risk += streak_risk + trend_risk
            
            streak_analysis[counter_name] = streak_info
        
        return {
            'has_concerning_patterns': concerning_patterns,
            'streak_analysis': streak_analysis,
            'demotion_risk': min(1.0, total_demotion_risk)  # Cap at 1.0
        }
    
    def _identify_related_counters(self, habit_name: str) -> List[Tuple[str, str]]:
        """Identify behavior counters related to a specific habit"""
        # Get all counter definitions
        all_counters = self.behavior_manager.get_counter_definitions()
        
        # Simple keyword matching for now - could be enhanced with ML or user configuration
        habit_keywords = habit_name.lower().split('_')
        related_counters = []
        
        for counter in all_counters:
            counter_name = counter['counter_name'].lower()
            counter_type = counter['counter_type']
            
            # Check for keyword matches
            for keyword in habit_keywords:
                if keyword in counter_name or any(kw in counter_name for kw in ['eating', 'exercise', 'sleep', 'work']):
                    related_counters.append((counter['counter_name'], counter_type))
                    break
        
        return related_counters
    
    def _calculate_negative_behavior_streak(self, counter_name: str) -> int:
        """Calculate consecutive days with negative behavior occurrences"""
        trend_data = self.behavior_manager.get_counter_trends(counter_name, 30)
        
        if not trend_data:
            return 0
        
        # Sort by date (most recent first)
        sorted_data = sorted(trend_data, key=lambda x: x['date'], reverse=True)
        
        current_streak = 0
        for entry in sorted_data:
            if entry['count'] > 0:  # Negative behavior occurred
                current_streak += 1
            else:
                break  # Streak broken
        
        return current_streak
    
    def _generate_enhanced_recommendation(self, base_analysis: Dict, behavior_influence: Dict, 
                                        metrics_influence: Dict, negative_behavior_analysis: Dict) -> str:
        """Generate enhanced recommendation considering all factors"""
        base_recommendation = base_analysis['recommendation']
        
        # Calculate enhancement score
        behavior_score = behavior_influence['overall_influence']
        metrics_score = metrics_influence['overall_influence']
        negative_penalty = negative_behavior_analysis['demotion_risk']
        
        total_enhancement = behavior_score + metrics_score - negative_penalty
        
        # Modify base recommendation based on enhancement
        if base_recommendation == 'promote_to_consistent':
            if total_enhancement >= 0.3:
                return 'strongly_promote_to_consistent'
            elif total_enhancement < -0.2:
                return 'consider_promotion'  # Downgrade due to negative factors
            else:
                return base_recommendation
        
        elif base_recommendation == 'consider_promotion':
            if total_enhancement >= 0.4:
                return 'promote_to_consistent'  # Upgrade due to positive factors
            elif total_enhancement < -0.3:
                return 'maintain_intermittent'
            else:
                return base_recommendation
        
        elif base_recommendation == 'maintain_consistent':
            if total_enhancement < -0.4:
                return 'consider_demotion'  # Negative factors suggest problems
            else:
                return base_recommendation
        
        elif base_recommendation == 'consider_demotion':
            if total_enhancement >= 0.2:
                return 'maintain_consistent'  # Positive factors suggest recovery
            elif total_enhancement < -0.3:
                return 'demote_to_intermittent'  # Strong negative factors
            else:
                return base_recommendation
        
        elif base_recommendation == 'demote_to_intermittent':
            if total_enhancement >= 0.3:
                return 'consider_demotion'  # Some positive factors present
            else:
                return base_recommendation
        
        else:  # maintain_intermittent
            if total_enhancement >= 0.5:
                return 'consider_promotion'  # Strong positive factors
            else:
                return base_recommendation
    
    def _calculate_enhancement_factors(self, behavior_influence: Dict, metrics_influence: Dict, 
                                     negative_behavior_analysis: Dict) -> Dict:
        """Calculate detailed enhancement factors for reporting"""
        return {
            'behavior_boost': behavior_influence['overall_influence'],
            'metrics_boost': metrics_influence['overall_influence'],
            'negative_penalty': negative_behavior_analysis['demotion_risk'],
            'net_enhancement': (behavior_influence['overall_influence'] + 
                              metrics_influence['overall_influence'] - 
                              negative_behavior_analysis['demotion_risk']),
            'primary_factors': self._identify_primary_factors(behavior_influence, metrics_influence, negative_behavior_analysis)
        }
    
    def _identify_primary_factors(self, behavior_influence: Dict, metrics_influence: Dict, 
                                negative_behavior_analysis: Dict) -> List[str]:
        """Identify the primary factors influencing the recommendation"""
        factors = []
        
        if behavior_influence['positive_influence'] > 0.2:
            factors.append('strong_positive_behaviors')
        
        if behavior_influence['negative_influence'] > 0.2:
            factors.append('concerning_negative_behaviors')
        
        if metrics_influence['consistency_score'] > 0.8:
            factors.append('consistent_metrics_logging')
        
        if metrics_influence['improvement_score'] > 0.2:
            factors.append('improving_metrics_trends')
        
        if negative_behavior_analysis['demotion_risk'] > 0.3:
            factors.append('negative_behavior_patterns')
        
        return factors
    
    def generate_enhanced_promotion_report(self) -> str:
        """Generate comprehensive enhanced promotion report"""
        base_report = super().generate_promotion_report()
        
        # Add enhanced analysis section
        enhanced_section = """
## 🔬 Enhanced Analysis with Behavior Counters & Metrics

### Behavior Counter Integration
This analysis incorporates positive and negative behavior counters that influence habit automaticity:

"""
        
        # Analyze all habits with enhanced system
        from config.settings import config
        current_habits = config.get_habits()
        all_habits = current_habits['consistent'] + current_habits['intermittent']
        
        for habit in all_habits:
            enhanced_analysis = self.analyze_habit_performance(habit)
            
            if 'behavior_influence' in enhanced_analysis:
                behavior_inf = enhanced_analysis['behavior_influence']
                metrics_inf = enhanced_analysis['metrics_influence']
                negative_analysis = enhanced_analysis['negative_behavior_analysis']
                
                enhanced_section += f"""
**{habit.replace('_', ' ').title()}**
- Base Recommendation: {enhanced_analysis['recommendation']}
- Enhanced Recommendation: {enhanced_analysis.get('enhanced_recommendation', 'N/A')}
- Behavior Influence: {behavior_inf['overall_influence']:.2f}
- Metrics Influence: {metrics_inf['overall_influence']:.2f}
- Negative Behavior Risk: {negative_analysis['demotion_risk']:.2f}
- Primary Factors: {', '.join(enhanced_analysis['enhancement_factors']['primary_factors'])}
"""
                
                if behavior_inf['related_counters']:
                    enhanced_section += "  - Related Counters:\n"
                    for counter in behavior_inf['related_counters']:
                        enhanced_section += f"    - {counter['counter_name']} ({counter['counter_type']}): {counter['influence']:.2f}\n"
                
                if metrics_inf['metrics_analyzed']:
                    enhanced_section += "  - Metrics Analysis:\n"
                    for metric in metrics_inf['metrics_analyzed']:
                        enhanced_section += f"    - {metric['metric_name']}: {metric['consistency']:.1%} consistency\n"
        
        enhanced_section += """
### Enhancement Methodology
- **Behavior Counters**: Positive behaviors boost promotion, negative behaviors create penalties
- **Metrics Consistency**: Regular metric logging indicates engagement and awareness
- **Negative Behavior Patterns**: Consecutive negative behavior days trigger demotion risk
- **Weighted Scoring**: All factors are weighted and combined with base habit analysis

### Recommendation Confidence
Enhanced recommendations have higher confidence due to multiple data sources:
- Traditional habit streak analysis (base system)
- Behavioral pattern recognition (counters)
- Quantitative progress tracking (metrics)
- Negative pattern detection (risk assessment)
"""
        
        return base_report + enhanced_section


# Global enhanced system instance
enhanced_promotion_system = EnhancedPromotionSystem()


# Enhanced convenience functions
def analyze_enhanced_habit_promotions() -> Dict:
    """Analyze all habits with enhanced system"""
    return enhanced_promotion_system.execute_all_promotions(auto_execute=False)


def get_enhanced_habit_analysis(habit_name: str) -> Dict:
    """Get enhanced analysis for a specific habit"""
    return enhanced_promotion_system.analyze_habit_performance(habit_name)


def generate_enhanced_promotion_report() -> str:
    """Generate enhanced promotion report"""
    return enhanced_promotion_system.generate_enhanced_promotion_report()


def calculate_behavior_influence_for_habit(habit_name: str) -> Dict:
    """Calculate behavior influence for a habit"""
    return enhanced_promotion_system.calculate_behavior_influence(habit_name)


if __name__ == "__main__":
    # Test the enhanced promotion system
    print("Testing Enhanced Promotion System...")
    
    system = EnhancedPromotionSystem()
    
    # Test enhanced analysis
    from config.settings import config
    current_habits = config.get_habits()
    
    if current_habits['intermittent']:
        test_habit = current_habits['intermittent'][0]
        enhanced_analysis = system.analyze_habit_performance(test_habit)
        
        print(f"\nEnhanced analysis for '{test_habit}':")
        print(f"Base recommendation: {enhanced_analysis['recommendation']}")
        print(f"Enhanced recommendation: {enhanced_analysis.get('enhanced_recommendation', 'N/A')}")
        print(f"Behavior influence: {enhanced_analysis.get('behavior_influence', {}).get('overall_influence', 0):.2f}")
        print(f"Metrics influence: {enhanced_analysis.get('metrics_influence', {}).get('overall_influence', 0):.2f}")
    
    print("\nEnhanced Promotion System test completed!")