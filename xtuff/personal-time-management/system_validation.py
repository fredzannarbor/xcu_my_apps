#!/usr/bin/env python3
"""
System Validation Script
Final validation that all components are properly integrated and working
"""

import sys
import os
import json
from datetime import datetime

# Add modules to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def validate_main_application():
    """Validate that the main application can be imported and initialized"""
    print("Validating main application...")
    
    try:
        # Test that daily_engine can be imported without errors
        import daily_engine
        print("✓ Main application imports successfully")
        
        # Test database initialization
        from utilities_daily_engine import init_database
        init_database()
        print("✓ Database initialization works")
        
        return True
    except Exception as e:
        print(f"❌ Main application validation failed: {e}")
        return False

def validate_app_management():
    """Validate app management functionality"""
    print("Validating app management...")
    
    try:
        from app_management_api import AppAPI
        api = AppAPI()
        
        # Test basic operations
        apps = api.list_apps()
        statuses = api.status()
        ports = api.get_available_ports()
        
        print(f"✓ App management working - {len(apps)} apps configured")
        return True
    except Exception as e:
        print(f"❌ App management validation failed: {e}")
        return False

def validate_task_systems():
    """Validate micro-tasks and countable tasks"""
    print("Validating task systems...")
    
    try:
        from database_extensions import (
            add_micro_task, get_micro_tasks, complete_micro_task,
            add_behavior_counter_definition, increment_behavior_counter,
            db_extensions
        )
        
        # Test micro-tasks
        success = add_micro_task("Validation test", "System validation", "low", 5)
        if not success:
            raise Exception("Failed to add micro-task")
        
        tasks = get_micro_tasks(completed=False)
        validation_task = None
        for task in tasks:
            if task['task_name'] == "Validation test":
                validation_task = task
                break
        
        if not validation_task:
            raise Exception("Failed to retrieve micro-task")
        
        success = complete_micro_task(validation_task['id'])
        if not success:
            raise Exception("Failed to complete micro-task")
        
        # Test countable tasks
        counter_name = "validation_counter"
        success = add_behavior_counter_definition(counter_name, 'positive', 'Validation counter')
        if not success:
            raise Exception("Failed to add counter definition")
        
        success = increment_behavior_counter(counter_name, 1)
        if not success:
            raise Exception("Failed to increment counter")
        
        data = db_extensions.get_behavior_counter_data(counter_name, days=1)
        if not data:
            raise Exception("Failed to retrieve counter data")
        
        print("✓ Task systems working correctly")
        return True
    except Exception as e:
        print(f"❌ Task systems validation failed: {e}")
        return False

def validate_ui_components():
    """Validate that all UI components can be imported"""
    print("Validating UI components...")
    
    try:
        from ui.settings_ui import render_settings_page, render_app_management_settings
        from ui.management_ui import render_management_ui
        from ui.habit_ui import render_habit_ui
        from ui.revenue_ui import render_revenue_ui
        from ui.creative_ui import render_creative_ui
        from ui.project_ui import render_projects_ui
        from ui.persistent_agents_ui import render_persistent_agents_panel
        
        # Verify critical functions exist
        assert callable(render_app_management_settings), "render_app_management_settings not callable"
        
        print("✓ All UI components available")
        return True
    except Exception as e:
        print(f"❌ UI components validation failed: {e}")
        return False

def validate_configuration():
    """Validate configuration system"""
    print("Validating configuration...")
    
    try:
        from config.settings import config
        
        # Test configuration access
        habits = config.get_habits()
        projects = config.get_projects()
        micro_tasks = config.get_micro_tasks()
        
        assert isinstance(habits, dict), "Habits config not a dict"
        assert isinstance(projects, dict), "Projects config not a dict"
        assert isinstance(micro_tasks, list), "Micro-tasks config not a list"
        
        print("✓ Configuration system working")
        return True
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

def validate_persistent_agents():
    """Validate persistent agents system"""
    print("Validating persistent agents...")
    
    try:
        from persistent_agents.base_agent import PersistentAgent, Alert, FamilyMember
        from persistent_agents.social_security_agent import SocialSecurityAgent
        from persistent_agents.real_property_agent import RealPropertyAgent
        
        # Test agent initialization
        ss_agent = SocialSecurityAgent()
        rp_agent = RealPropertyAgent()
        
        # Test basic functionality
        alerts = ss_agent.get_active_alerts()
        members = ss_agent.get_family_members()
        
        print("✓ Persistent agents system working")
        return True
    except Exception as e:
        print(f"❌ Persistent agents validation failed: {e}")
        return False

def validate_quick_stats():
    """Validate quick stats functionality"""
    print("Validating quick stats...")
    
    try:
        from utilities_daily_engine import (
            get_today_session, update_energy_level, 
            save_energy_comment, get_energy_comment
        )
        
        # Test session management
        session = get_today_session()
        assert session is not None, "Failed to get today's session"
        
        # Test energy level
        update_energy_level('medium')
        updated_session = get_today_session()
        assert updated_session[4] == 'medium', "Energy level not updated"
        
        # Test energy comments
        test_comment = "Validation test comment"
        save_energy_comment(test_comment)
        retrieved_comment = get_energy_comment()
        assert retrieved_comment == test_comment, "Energy comment not saved/retrieved"
        
        print("✓ Quick stats functionality working")
        return True
    except Exception as e:
        print(f"❌ Quick stats validation failed: {e}")
        return False

def cleanup_validation_data():
    """Clean up validation test data"""
    try:
        import sqlite3
        conn = sqlite3.connect('daily_engine.db')
        cursor = conn.cursor()
        
        # Clean up validation data
        cursor.execute("DELETE FROM micro_tasks WHERE task_name = 'Validation test'")
        cursor.execute("DELETE FROM behavior_counter_definitions WHERE counter_name = 'validation_counter'")
        cursor.execute("DELETE FROM behavior_counters WHERE counter_name = 'validation_counter'")
        
        conn.commit()
        conn.close()
        
        print("✓ Validation data cleaned up")
    except Exception as e:
        print(f"Warning: Cleanup failed: {e}")

def main():
    """Run system validation"""
    print("=" * 60)
    print("DAILY ENGINE - SYSTEM VALIDATION")
    print("=" * 60)
    print(f"Validation started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    validations = [
        ("Main Application", validate_main_application),
        ("App Management", validate_app_management),
        ("Task Systems", validate_task_systems),
        ("UI Components", validate_ui_components),
        ("Configuration", validate_configuration),
        ("Persistent Agents", validate_persistent_agents),
        ("Quick Stats", validate_quick_stats)
    ]
    
    passed = 0
    failed = 0
    
    for name, validation_func in validations:
        print(f"\n{name}:")
        try:
            if validation_func():
                passed += 1
                print(f"✅ {name} VALIDATED")
            else:
                failed += 1
                print(f"❌ {name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {name} FAILED: {e}")
    
    print("\n" + "=" * 60)
    print("SYSTEM VALIDATION RESULTS")
    print("=" * 60)
    print(f"Total validations: {len(validations)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(passed/len(validations)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 SYSTEM VALIDATION SUCCESSFUL!")
        print("All components are properly integrated and working.")
        print("\nThe Daily Engine system is ready for use:")
        print("• Run with: streamlit run daily_engine.py")
        print("• Access settings via the Settings tab")
        print("• Manage apps via Settings → App Management")
        print("• All task systems are operational")
        print("• Persistent agents are active")
    else:
        print(f"\n⚠️  {failed} validation(s) failed.")
        print("System may not function correctly.")
    
    # Clean up validation data
    cleanup_validation_data()
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)