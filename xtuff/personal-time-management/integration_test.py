#!/usr/bin/env python3
"""
End-to-End Integration Test for Daily Engine
Tests the complete system integration and final wiring
"""

import sys
import os
import sqlite3
import json
from datetime import datetime
import tempfile
import shutil

# Add modules to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all major components
from app_management_api import AppAPI
from database_extensions import db_extensions
from utilities_daily_engine import init_database, get_today_session
from config.settings import config
from streamlit_app_manager import StreamlitAppManager

def test_database_integration():
    """Test that all database components are properly integrated"""
    print("Testing database integration...")
    
    # Initialize database
    init_database()
    
    # Test session creation
    session = get_today_session()
    assert session is not None, "Failed to create/get today's session"
    print("✓ Database session management working")
    
    # Test micro-tasks integration
    from database_extensions import add_micro_task, get_micro_tasks, complete_micro_task
    
    success = add_micro_task("Integration test task", "Testing integration", "high", 15)
    assert success, "Failed to add micro-task"
    
    # Get the task ID from the database
    tasks = get_micro_tasks(completed=False)
    task_id = None
    for task in tasks:
        if task['task_name'] == "Integration test task":
            task_id = task['id']
            break
    assert task_id is not None, "Failed to find added micro-task"
    
    tasks = get_micro_tasks(completed=False)
    assert any(task['id'] == task_id for task in tasks), "Failed to retrieve micro-task"
    
    success = complete_micro_task(task_id)
    assert success, "Failed to complete micro-task"
    print("✓ Micro-tasks integration working")
    
    # Test countable tasks integration
    counter_name = "integration_test_counter"
    success = db_extensions.add_behavior_counter_definition(
        counter_name, 'positive', 'Integration test counter'
    )
    assert success, "Failed to add behavior counter definition"
    
    success = db_extensions.increment_behavior_counter(counter_name, 1)
    assert success, "Failed to increment behavior counter"
    
    data = db_extensions.get_behavior_counter_data(counter_name, days=1)
    assert len(data) > 0, "Failed to retrieve behavior counter data"
    print("✓ Countable tasks integration working")

def test_app_management_integration():
    """Test that app management is properly integrated"""
    print("Testing app management integration...")
    
    # Test API initialization
    api = AppAPI()
    assert api is not None, "Failed to initialize App Management API"
    
    # Test configuration loading
    apps = api.list_apps()
    assert isinstance(apps, list), "Failed to list configured apps"
    print(f"✓ Found {len(apps)} configured apps: {', '.join(apps)}")
    
    # Test status retrieval
    statuses = api.status()
    assert isinstance(statuses, dict), "Failed to get app statuses"
    print("✓ App status retrieval working")
    
    # Test port management
    ports = api.get_available_ports()
    assert isinstance(ports, list), "Failed to get available ports"
    print(f"✓ Port management working, {len(ports)} ports available")

def test_config_integration():
    """Test that configuration system is properly integrated"""
    print("Testing configuration integration...")
    
    # Test habit configuration
    habits = config.get_habits()
    assert 'consistent' in habits, "Failed to get consistent habits"
    assert 'intermittent' in habits, "Failed to get intermittent habits"
    print("✓ Habit configuration working")
    
    # Test project configuration
    projects = config.get_projects()
    assert isinstance(projects, dict), "Failed to get projects configuration"
    print("✓ Project configuration working")
    
    # Test micro-tasks configuration
    micro_tasks = config.get_micro_tasks()
    assert isinstance(micro_tasks, list), "Failed to get micro-tasks configuration"
    print("✓ Micro-tasks configuration working")

def test_ui_component_integration():
    """Test that UI components can be imported and are properly integrated"""
    print("Testing UI component integration...")
    
    # Test main UI components
    try:
        from ui.management_ui import render_management_ui, render_daily_management_only
        from ui.settings_ui import render_settings_page, render_app_management_settings
        from ui.habit_ui import render_habit_ui
        from ui.revenue_ui import render_revenue_ui
        from ui.creative_ui import render_creative_ui
        from ui.project_ui import render_projects_ui
        from ui.persistent_agents_ui import render_persistent_agents_panel
        print("✓ All UI components can be imported")
    except ImportError as e:
        assert False, f"Failed to import UI component: {e}"
    
    # Test that render_app_management_settings exists and is callable
    assert callable(render_app_management_settings), "render_app_management_settings is not callable"
    print("✓ App management settings UI is properly integrated")

def test_quick_stats_integration():
    """Test that quick stats functionality is properly integrated"""
    print("Testing quick stats integration...")
    
    from utilities_daily_engine import update_energy_level, get_energy_comment, save_energy_comment
    
    # Test energy level functionality
    update_energy_level('high')
    session = get_today_session()
    assert session[4] == 'high', "Failed to update energy level"
    print("✓ Energy level management working")
    
    # Test energy comments
    test_comment = "Integration test comment"
    save_energy_comment(test_comment)
    retrieved_comment = get_energy_comment()
    assert retrieved_comment == test_comment, "Failed to save/retrieve energy comment"
    print("✓ Energy comments working")

def test_persistent_agents_integration():
    """Test that persistent agents are properly integrated"""
    print("Testing persistent agents integration...")
    
    try:
        from persistent_agents.base_agent import PersistentAgent, Alert, FamilyMember
        from persistent_agents.social_security_agent import SocialSecurityAgent
        from persistent_agents.real_property_agent import RealPropertyAgent
        print("✓ Persistent agents can be imported")
    except ImportError as e:
        assert False, f"Failed to import persistent agent: {e}"
    
    # Test agent initialization
    try:
        ss_agent = SocialSecurityAgent()
        rp_agent = RealPropertyAgent()
        print("✓ Persistent agents can be initialized")
    except Exception as e:
        print(f"⚠ Warning: Agent initialization failed: {e}")

def test_file_structure_integrity():
    """Test that all required files exist and are accessible"""
    print("Testing file structure integrity...")
    
    required_files = [
        'daily_engine.py',
        'app_management_api.py',
        'streamlit_app_manager.py',
        'database_extensions.py',
        'utilities_daily_engine.py',
        'config/settings.py',
        'ui/settings_ui.py',
        'ui/management_ui.py',
        'ui/habit_ui.py',
        'ui/revenue_ui.py',
        'ui/creative_ui.py',
        'ui/project_ui.py',
        'ui/persistent_agents_ui.py',
        'persistent_agents/base_agent.py',
        'persistent_agents/social_security_agent.py',
        'persistent_agents/real_property_agent.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    assert len(missing_files) == 0, f"Missing required files: {missing_files}"
    print(f"✓ All {len(required_files)} required files exist")

def test_database_schema_integrity():
    """Test that database schema is complete and consistent"""
    print("Testing database schema integrity...")
    
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    required_tables = [
        'daily_sessions',
        'micro_tasks',
        'behavior_counter_definitions',
        'behavior_counters',
        'streamlit_app_status'
    ]
    
    missing_tables = [table for table in required_tables if table not in tables]
    assert len(missing_tables) == 0, f"Missing database tables: {missing_tables}"
    print(f"✓ All {len(required_tables)} required database tables exist")
    
    conn.close()

def test_end_to_end_workflow():
    """Test a complete end-to-end workflow"""
    print("Testing end-to-end workflow...")
    
    # 1. Create a session
    session = get_today_session()
    assert session is not None
    
    # 2. Add and complete a micro-task
    from database_extensions import add_micro_task, complete_micro_task, get_micro_tasks
    success = add_micro_task("E2E test task", "End-to-end test", "medium", 10)
    assert success
    
    # Get the task ID
    tasks = get_micro_tasks(completed=False)
    task_id = None
    for task in tasks:
        if task['task_name'] == "E2E test task":
            task_id = task['id']
            break
    assert task_id is not None
    
    success = complete_micro_task(task_id)
    assert success
    
    # 3. Increment a countable task
    counter_name = "e2e_test_counter"
    db_extensions.add_behavior_counter_definition(counter_name, 'positive', 'E2E test')
    success = db_extensions.increment_behavior_counter(counter_name, 1)
    assert success
    
    # 4. Update energy level
    from utilities_daily_engine import update_energy_level
    update_energy_level('peak')
    
    # 5. Test app management
    api = AppAPI()
    statuses = api.status()
    assert isinstance(statuses, dict)
    
    print("✓ End-to-end workflow completed successfully")

def cleanup_test_data():
    """Clean up test data"""
    print("Cleaning up test data...")
    
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()
    
    # Clean up test micro-tasks
    cursor.execute("DELETE FROM micro_tasks WHERE task_name LIKE '%test%'")
    
    # Clean up test counters
    cursor.execute("DELETE FROM behavior_counter_definitions WHERE counter_name LIKE '%test%'")
    cursor.execute("DELETE FROM behavior_counters WHERE counter_name LIKE '%test%'")
    
    conn.commit()
    conn.close()
    
    print("✓ Test data cleaned up")

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("DAILY ENGINE - SYSTEM INTEGRATION TEST")
    print("=" * 60)
    
    tests = [
        test_file_structure_integrity,
        test_database_schema_integrity,
        test_database_integration,
        test_config_integration,
        test_app_management_integration,
        test_ui_component_integration,
        test_quick_stats_integration,
        test_persistent_agents_integration,
        test_end_to_end_workflow
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"\n{test.__name__.replace('_', ' ').title()}:")
            test()
            passed += 1
            print(f"✅ PASSED")
        except Exception as e:
            failed += 1
            print(f"❌ FAILED: {e}")
    
    print("\n" + "=" * 60)
    print("INTEGRATION TEST RESULTS")
    print("=" * 60)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("System integration and final wiring is complete.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. System integration needs attention.")
    
    # Clean up regardless of test results
    try:
        cleanup_test_data()
    except Exception as e:
        print(f"Warning: Cleanup failed: {e}")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)