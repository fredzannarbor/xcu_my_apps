#!/usr/bin/env python3
"""
Overnight Automation Runner
Runs automated tasks for all SaaS projects during off-hours
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automation.saas_automation import SaaSAutomation
from habits.habit_tracker import HabitTracker
import json
from datetime import datetime

# Project paths
PROJECT_PATHS = {
    'nimble_books': '/Users/fred/xcu_my_apps/nimble/codexes-factory',
    'xtuff': '/Users/fred/xcu_my_apps/xtuff',
    'altdoge': '/Users/fred/my-organizations/altDOGE',
    'trillions': '/Users/fred/my-organizations/trillionsofpeople'
}

def run_overnight_automation():
    """Run all overnight automation tasks"""
    print(f"🌙 Starting overnight automation at {datetime.now()}")
    
    # Initialize automation
    automation = SaaSAutomation(PROJECT_PATHS)
    
    # Run all SaaS automations
    print("🚀 Running SaaS project automations...")
    results = automation.run_all_automations()
    
    # Print summary
    print("\n📊 Automation Summary:")
    print(automation.get_summary())
    
    # Save results to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"automation_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to {results_file}")
    
    # Initialize habit tracker for tomorrow's scheduling
    habit_tracker = HabitTracker()
    daily_summary = habit_tracker.get_daily_summary()
    
    print(f"\n🎯 Today's Habit Summary:")
    print(f"Consistent habits: {daily_summary['consistent_habits']['completed']}/{daily_summary['consistent_habits']['total']}")
    print(f"Intermittent habits: {daily_summary['intermittent_habits']['completed']}/{daily_summary['intermittent_habits']['total']}")
    print(f"Overall score: {daily_summary['overall_score']}%")
    
    print(f"\n✅ Overnight automation complete at {datetime.now()}")
    
    return results

if __name__ == "__main__":
    run_overnight_automation()