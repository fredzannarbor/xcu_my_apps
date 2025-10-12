#!/usr/bin/env python3
"""
Test suite for App Management API
Basic tests to verify the API functionality
"""

import unittest
import sys
import os
import tempfile
import json

# Add the parent directory to the path so we can import the API
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_management_api import AppAPI, AppResult, AppStatus, HealthResult


class TestAppManagementAPI(unittest.TestCase):
    """Test cases for the App Management API"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary config file for testing
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        
        test_config = {
            "apps": {
                "test_app": {
                    "name": "Test App",
                    "path": "test_app.py",
                    "port": 8501,
                    "enabled": True,
                    "auto_start": False,
                    "restart_on_failure": True,
                    "health_check_url": "/health",
                    "environment": {}
                },
                "disabled_app": {
                    "name": "Disabled App",
                    "path": "disabled_app.py",
                    "port": 8502,
                    "enabled": False,
                    "auto_start": False,
                    "restart_on_failure": True,
                    "health_check_url": "/health",
                    "environment": {}
                }
            },
            "daemon_config": {
                "check_interval": 30,
                "restart_delay": 5,
                "max_restart_attempts": 3,
                "log_level": "INFO"
            }
        }
        
        json.dump(test_config, self.temp_config)
        self.temp_config.close()
        
        # Initialize API with test config
        self.api = AppAPI(config_path=self.temp_config.name)
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Remove temporary config file
        os.unlink(self.temp_config.name)
    
    def test_api_initialization(self):
        """Test API initialization"""
        self.assertIsInstance(self.api, AppAPI)
        self.assertIsNotNone(self.api.manager)
    
    def test_list_apps(self):
        """Test listing configured apps"""
        apps = self.api.list_apps()
        self.assertIsInstance(apps, list)
        self.assertIn('test_app', apps)
        self.assertIn('disabled_app', apps)
    
    def test_get_app_config(self):
        """Test getting app configuration"""
        config = self.api.get_app_config('test_app')
        self.assertIsInstance(config, dict)
        self.assertEqual(config['name'], 'Test App')
        self.assertEqual(config['path'], 'test_app.py')
        self.assertTrue(config['enabled'])
        
        # Test non-existent app
        config = self.api.get_app_config('nonexistent_app')
        self.assertIsNone(config)
    
    def test_status_method(self):
        """Test status method"""
        # Test getting all statuses
        statuses = self.api.status()
        self.assertIsInstance(statuses, dict)
        
        # Test getting specific app status
        status_dict = self.api.status('test_app')
        self.assertIsInstance(status_dict, dict)
        
        if 'test_app' in status_dict:
            status = status_dict['test_app']
            self.assertIsInstance(status, AppStatus)
            self.assertEqual(status.app_name, 'test_app')
    
    def test_start_nonexistent_app(self):
        """Test starting a non-existent app"""
        result = self.api.start('nonexistent_app', app_path='nonexistent.py')
        self.assertIsInstance(result, AppResult)
        self.assertFalse(result.success)
        # Should contain some indication of failure
        self.assertTrue(len(result.error) > 0)
    
    def test_stop_nonrunning_app(self):
        """Test stopping a non-running app"""
        result = self.api.stop('test_app')
        self.assertIsInstance(result, AppResult)
        # This should fail because the app is not running
        self.assertFalse(result.success)
    
    def test_restart_nonrunning_app(self):
        """Test restarting a non-running app"""
        result = self.api.restart('test_app')
        self.assertIsInstance(result, AppResult)
        # This should fail because the app file doesn't exist
        self.assertFalse(result.success)
    
    def test_health_check_nonrunning_app(self):
        """Test health check on non-running app"""
        health_results = self.api.health_check('test_app')
        self.assertIsInstance(health_results, dict)
        
        if 'test_app' in health_results:
            health = health_results['test_app']
            self.assertIsInstance(health, HealthResult)
            self.assertFalse(health.healthy)
    
    def test_get_running_apps(self):
        """Test getting running apps"""
        running = self.api.get_running_apps()
        self.assertIsInstance(running, list)
        # Should be empty since no apps are actually running in tests
        self.assertEqual(len(running), 0)
    
    def test_get_available_ports(self):
        """Test getting available ports"""
        ports = self.api.get_available_ports()
        self.assertIsInstance(ports, list)
        # Should have some available ports (or empty list if permission issues)
        self.assertGreaterEqual(len(ports), 0)
    
    def test_get_port_assignments(self):
        """Test getting port assignments"""
        assignments = self.api.get_port_assignments()
        self.assertIsInstance(assignments, dict)
    
    def test_start_disabled_app(self):
        """Test starting a disabled app"""
        result = self.api.start('disabled_app')
        self.assertIsInstance(result, AppResult)
        self.assertFalse(result.success)
        self.assertIn('disabled', result.error.lower())
    
    def test_app_result_boolean_context(self):
        """Test AppResult boolean context"""
        # Test successful result
        success_result = AppResult(success=True, app_name='test')
        self.assertTrue(bool(success_result))
        self.assertTrue(success_result)  # Direct boolean evaluation
        
        # Test failed result
        fail_result = AppResult(success=False, app_name='test', error='Test error')
        self.assertFalse(bool(fail_result))
        self.assertFalse(fail_result)  # Direct boolean evaluation
    
    def test_app_status_properties(self):
        """Test AppStatus properties"""
        # Test running status
        running_status = AppStatus(
            app_name='test',
            status='running',
            port=8501,
            last_health_check='2023-01-01T12:00:00'
        )
        self.assertTrue(running_status.is_running)
        self.assertFalse(running_status.is_stopped)
        self.assertTrue(running_status.is_healthy)
        
        # Test stopped status
        stopped_status = AppStatus(app_name='test', status='stopped')
        self.assertFalse(stopped_status.is_running)
        self.assertTrue(stopped_status.is_stopped)
        self.assertFalse(stopped_status.is_healthy)
    
    def test_start_all_enabled(self):
        """Test starting all enabled apps"""
        results = self.api.start_all_enabled()
        self.assertIsInstance(results, dict)
        
        # Should have results for enabled apps
        self.assertIn('test_app', results)
        self.assertIsInstance(results['test_app'], AppResult)
        
        # Should have result for disabled app (but marked as disabled)
        self.assertIn('disabled_app', results)
        self.assertFalse(results['disabled_app'].success)
        self.assertIn('disabled', results['disabled_app'].error.lower())
    
    def test_stop_all(self):
        """Test stopping all apps"""
        results = self.api.stop_all()
        self.assertIsInstance(results, dict)
        # Should be empty since no apps are running
        self.assertEqual(len(results), 0)


class TestConvenienceFunctions(unittest.TestCase):
    """Test the convenience functions"""
    
    def test_convenience_functions_exist(self):
        """Test that convenience functions exist and are callable"""
        from app_management_api import start_app, stop_app, restart_app, get_app_status, health_check
        
        # Test that functions exist
        self.assertTrue(callable(start_app))
        self.assertTrue(callable(stop_app))
        self.assertTrue(callable(restart_app))
        self.assertTrue(callable(get_app_status))
        self.assertTrue(callable(health_check))
    
    def test_convenience_function_return_types(self):
        """Test that convenience functions return expected types"""
        from app_management_api import get_app_status, health_check
        
        # Test get_app_status
        status = get_app_status()
        self.assertIsInstance(status, dict)
        
        # Test health_check
        health = health_check()
        self.assertIsInstance(health, dict)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestAppManagementAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestConvenienceFunctions))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running App Management API Tests")
    print("=" * 50)
    
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)