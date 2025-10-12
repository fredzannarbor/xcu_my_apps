#!/usr/bin/env python3
"""
App Management API Examples
Demonstrates various ways to use the programmatic API for managing Streamlit apps
"""

import time
import sys
import os

# Add the parent directory to the path so we can import the API
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_management_api import AppAPI


def example_basic_operations():
    """Example: Basic app operations"""
    print("=" * 60)
    print("EXAMPLE 1: Basic App Operations")
    print("=" * 60)
    
    # Initialize the API
    api = AppAPI()
    
    # List all configured apps
    apps = api.list_apps()
    print(f"Configured apps: {', '.join(apps)}")
    
    # Get current status of all apps
    print("\nCurrent status:")
    statuses = api.status()
    for app_name, status in statuses.items():
        print(f"  {app_name}: {status.status}" + 
              (f" (port {status.port})" if status.port else ""))
    
    # Example: Start an app (if not already running)
    app_to_test = 'daily_engine'  # Change this to an app you want to test
    
    if app_to_test in apps:
        current_status = api.status(app_to_test)
        if app_to_test in current_status:
            status = current_status[app_to_test]
            
            if not status.is_running:
                print(f"\nStarting {app_to_test}...")
                result = api.start(app_to_test)
                if result.success:
                    print(f"✅ Started {app_to_test} on {result.url}")
                else:
                    print(f"❌ Failed to start {app_to_test}: {result.error}")
            else:
                print(f"\n{app_to_test} is already running on port {status.port}")
    
    print()


def example_health_monitoring():
    """Example: Health monitoring and automatic recovery"""
    print("=" * 60)
    print("EXAMPLE 2: Health Monitoring")
    print("=" * 60)
    
    api = AppAPI()
    
    # Get running apps
    running_apps = api.get_running_apps()
    print(f"Running apps: {', '.join(running_apps) if running_apps else 'None'}")
    
    if running_apps:
        print("\nPerforming health checks...")
        health_results = api.health_check()
        
        for app_name, health in health_results.items():
            if health.healthy:
                print(f"✅ {app_name}: Healthy" + 
                      (f" (HTTP {health.status_code})" if health.status_code else ""))
            else:
                print(f"❌ {app_name}: Unhealthy - {health.reason}")
                
                # Example: Automatic recovery
                print(f"   Attempting to restart {app_name}...")
                result = api.restart(app_name)
                if result.success:
                    print(f"   ✅ Successfully restarted {app_name}")
                else:
                    print(f"   ❌ Failed to restart {app_name}: {result.error}")
    else:
        print("No running apps to check")
    
    print()


def example_batch_operations():
    """Example: Batch operations on multiple apps"""
    print("=" * 60)
    print("EXAMPLE 3: Batch Operations")
    print("=" * 60)
    
    api = AppAPI()
    
    # Get all configured apps
    apps = api.list_apps()
    print(f"Found {len(apps)} configured apps")
    
    # Example: Start all enabled apps
    print("\nStarting all enabled apps...")
    results = api.start_all_enabled()
    
    success_count = 0
    for app_name, result in results.items():
        if result.success:
            print(f"✅ {app_name}: Started on {result.url}")
            success_count += 1
        else:
            print(f"❌ {app_name}: {result.error}")
    
    print(f"\nSuccessfully started {success_count}/{len(results)} apps")
    
    # Wait a moment for apps to fully start
    if success_count > 0:
        print("\nWaiting for apps to fully initialize...")
        time.sleep(3)
        
        # Perform health checks on all apps
        print("Performing health checks...")
        health_results = api.health_check()
        
        healthy_count = 0
        for app_name, health in health_results.items():
            if health.healthy:
                healthy_count += 1
        
        print(f"Health check results: {healthy_count}/{len(health_results)} apps healthy")
    
    print()


def example_port_management():
    """Example: Port management and assignments"""
    print("=" * 60)
    print("EXAMPLE 4: Port Management")
    print("=" * 60)
    
    api = AppAPI()
    
    # Get available ports
    available_ports = api.get_available_ports()
    print(f"Available ports: {available_ports}")
    
    # Get current port assignments
    assignments = api.get_port_assignments()
    print(f"\nCurrent port assignments:")
    for app_name, port in assignments.items():
        print(f"  {app_name}: port {port}")
    
    # Show port usage summary
    all_ports = list(range(8501, 8511))  # Default range
    used_ports = list(assignments.values())
    
    print(f"\nPort usage summary:")
    print(f"  Total ports in range: {len(all_ports)}")
    print(f"  Assigned ports: {len(used_ports)}")
    print(f"  Available ports: {len(available_ports)}")
    
    print()


def example_configuration_inspection():
    """Example: Inspecting app configurations"""
    print("=" * 60)
    print("EXAMPLE 5: Configuration Inspection")
    print("=" * 60)
    
    api = AppAPI()
    
    # Get all configured apps
    apps = api.list_apps()
    
    for app_name in apps:
        config = api.get_app_config(app_name)
        if config:
            print(f"\n📱 {config.get('name', app_name)}")
            print(f"   Path: {config['path']}")
            print(f"   Enabled: {config.get('enabled', True)}")
            print(f"   Auto-start: {config.get('auto_start', False)}")
            print(f"   Restart on failure: {config.get('restart_on_failure', True)}")
            print(f"   Default port: {config.get('port', 'Auto-assigned')}")
            
            # Get current runtime status
            status_dict = api.status(app_name)
            if app_name in status_dict:
                status = status_dict[app_name]
                print(f"   Current status: {status.status}")
                if status.is_running:
                    print(f"   Running on port: {status.port}")
                    print(f"   Process ID: {status.pid}")
                    if status.restart_count > 0:
                        print(f"   Restart count: {status.restart_count}")
    
    print()


def example_error_handling():
    """Example: Proper error handling"""
    print("=" * 60)
    print("EXAMPLE 6: Error Handling")
    print("=" * 60)
    
    api = AppAPI()
    
    # Example 1: Try to start a non-existent app
    print("Attempting to start non-existent app...")
    result = api.start('nonexistent_app', app_path='nonexistent_path.py')
    if result.success:
        print(f"✅ Unexpected success: {result.message}")
    else:
        print(f"❌ Expected failure: {result.error}")
    
    # Example 2: Try to stop an app that's not running
    print("\nAttempting to stop non-running app...")
    result = api.stop('nonexistent_app')
    if result.success:
        print(f"✅ Unexpected success: {result.message}")
    else:
        print(f"❌ Expected failure: {result.error}")
    
    # Example 3: Get status of non-existent app
    print("\nGetting status of non-existent app...")
    status_dict = api.status('nonexistent_app')
    if 'nonexistent_app' in status_dict:
        status = status_dict['nonexistent_app']
        print(f"Status: {status.status}")
    else:
        print("App not found in status results")
    
    # Example 4: Using result objects in boolean context
    print("\nDemonstrating boolean context usage...")
    result = api.start('another_nonexistent_app')
    if result:  # This uses the __bool__ method
        print("This shouldn't print")
    else:
        print(f"Boolean context correctly identified failure: {result.error}")
    
    print()


def example_monitoring_script():
    """Example: Simple monitoring script"""
    print("=" * 60)
    print("EXAMPLE 7: Simple Monitoring Script")
    print("=" * 60)
    
    api = AppAPI()
    
    print("Starting monitoring cycle...")
    
    # This would normally run in a loop, but we'll just do one iteration
    for iteration in range(1):
        print(f"\nMonitoring iteration {iteration + 1}")
        
        # Get all app statuses
        statuses = api.status()
        
        # Check each app
        issues_found = 0
        for app_name, status in statuses.items():
            config = api.get_app_config(app_name)
            
            if config and config.get('enabled', True):
                if status.is_running:
                    # App is running, check health
                    health = api.health_check(app_name)
                    if app_name in health:
                        if health[app_name].healthy:
                            print(f"✅ {app_name}: Running and healthy")
                        else:
                            print(f"⚠️  {app_name}: Running but unhealthy - {health[app_name].reason}")
                            issues_found += 1
                    else:
                        print(f"❓ {app_name}: Running but health check failed")
                        issues_found += 1
                
                elif config.get('auto_start', False):
                    # App should be running but isn't
                    print(f"🔄 {app_name}: Should be auto-started, attempting start...")
                    result = api.start(app_name)
                    if result.success:
                        print(f"✅ {app_name}: Successfully started")
                    else:
                        print(f"❌ {app_name}: Failed to start - {result.error}")
                        issues_found += 1
                
                else:
                    print(f"⏸️  {app_name}: Stopped (auto-start disabled)")
            
            else:
                print(f"⏹️  {app_name}: Disabled")
        
        print(f"\nMonitoring summary: {issues_found} issues found")
    
    print()


def main():
    """Run all examples"""
    print("App Management API Examples")
    print("This script demonstrates various ways to use the programmatic API")
    print()
    
    try:
        # Run all examples
        example_basic_operations()
        example_health_monitoring()
        example_batch_operations()
        example_port_management()
        example_configuration_inspection()
        example_error_handling()
        example_monitoring_script()
        
        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()