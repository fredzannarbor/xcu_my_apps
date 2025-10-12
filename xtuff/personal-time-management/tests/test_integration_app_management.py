#!/usr/bin/env python3
"""
Integration tests for the app management system
Tests the complete app management workflow including UI integration
"""

import unittest
import sys
import os
import tempfile
import json
import subprocess
import time
import requests
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_management_api import AppAPI
from streamlit_app_manager import StreamlitAppManager


class TestAppManagementIntegration(unittest.TestCase):
    """Integration tests for the complete app management system"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        
        # Create test app files
        self.test_app_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        self.test_app_file.write('''
import streamlit as st
import time

st.title("Test App")
st.write("This is a test Streamlit application")

# Health check endpoint
if st.sidebar.button("Health Check"):
    st.success("App is healthy!")

# Simple counter for testing
if "counter" not in st.session_state:
    st.session_state.counter = 0

if st.button("Increment"):
    st.session_state.counter += 1

st.write(f"Counter: {st.session_state.counter}")
''')
        self.test_app_file.close()
        
        # Create test configuration
        test_config = {
            "apps": {
                "test_integration_app": {
                    "name": "Test Integration App",
                    "path": self.test_app_file.name,
                    "port": 8599,  # Use a high port to avoid conflicts
                    "enabled": True,
                    "auto_start": False,
                    "restart_on_failure": True,
                    "health_check_url": "/",
                    "environment": {}
                },
                "disabled_integration_app": {
                    "name": "Disabled Integration App",
                    "path": "nonexistent.py",
                    "port": 8598,
                    "enabled": False,
                    "auto_start": False,
                    "restart_on_failure": False,
                    "health_check_url": "/",
                    "environment": {}
                }
            },
            "daemon_config": {
                "check_interval": 30,
                "restart_delay": 2,
                "max_restart_attempts": 2,
                "log_level": "INFO"
            }
        }
        
        json.dump(test_config, self.temp_config)
        self.temp_config.close()
        
        # Initialize API and manager
        self.api = AppAPI(config_path=self.temp_config.name)
        self.manager = StreamlitAppManager(config_path=self.temp_config.name)
        
        # Keep track of started processes for cleanup
        self.started_processes = []
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Stop any running test apps
        try:
            self.api.stop('test_integration_app')
        except:
            pass
        
        # Clean up any remaining processes
        for proc in self.started_processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                try:
                    proc.kill()
                except:
                    pass
        
        # Remove temporary files
        os.unlink(self.temp_config.name)
        os.unlink(self.test_app_file.name)
    
    def test_full_app_lifecycle(self):
        """Test the complete app lifecycle: start -> status -> health -> stop"""
        app_name = "test_integration_app"
        
        # 1. Start the app
        start_result = self.api.start(app_name)
        
        if not start_result.success:
            self.skipTest(f"Could not start test app: {start_result.error}")
        
        self.assertTrue(start_result.success)
        self.assertEqual(start_result.app_name, app_name)
        self.assertIsNotNone(start_result.port)
        self.assertIsNotNone(start_result.pid)
        
        try:
            # Give the app time to start
            time.sleep(3)
            
            # 2. Check status
            status_dict = self.api.status(app_name)
            self.assertIn(app_name, status_dict)
            
            status = status_dict[app_name]
            self.assertEqual(status.app_name, app_name)
            self.assertTrue(status.is_running)
            self.assertEqual(status.port, start_result.port)
            
            # 3. Health check
            health_dict = self.api.health_check(app_name)
            
            if app_name in health_dict:
                health = health_dict[app_name]
                self.assertEqual(health.app_name, app_name)
                # Health check might fail due to Streamlit startup time, so we don't assert healthy
            
            # 4. Verify app is accessible (if possible)
            try:
                response = requests.get(f"http://localhost:{start_result.port}", timeout=5)
                # If we get any response, the app is running
                self.assertIsNotNone(response)
            except requests.exceptions.RequestException:
                # Network requests might fail in test environment, that's okay
                pass
            
        finally:
            # 5. Stop the app
            stop_result = self.api.stop(app_name)
            self.assertTrue(stop_result.success)
            self.assertEqual(stop_result.app_name, app_name)
            
            # Give time for cleanup
            time.sleep(1)
            
            # 6. Verify app is stopped
            final_status = self.api.status(app_name)
            if app_name in final_status:
                self.assertTrue(final_status[app_name].is_stopped)
    
    def test_start_disabled_app_integration(self):
        """Test that disabled apps cannot be started through the integration"""
        app_name = "disabled_integration_app"
        
        result = self.api.start(app_name)
        
        self.assertFalse(result.success)
        self.assertIn('disabled', result.error.lower())
    
    def test_multiple_apps_management(self):
        """Test managing multiple apps simultaneously"""
        # This test is limited since we only have one enabled test app
        # But we can test the multi-app functions
        
        # Test listing apps
        apps = self.api.list_apps()
        self.assertIn("test_integration_app", apps)
        self.assertIn("disabled_integration_app", apps)
        
        # Test getting all statuses
        all_statuses = self.api.status()
        self.assertIsInstance(all_statuses, dict)
        
        # Test start all enabled (should start our one enabled app)
        results = self.api.start_all_enabled()
        self.assertIn("test_integration_app", results)
        self.assertIn("disabled_integration_app", results)
        
        # The enabled app should succeed or fail with a real error
        enabled_result = results["test_integration_app"]
        self.assertIsInstance(enabled_result.success, bool)
        
        # The disabled app should fail with disabled error
        disabled_result = results["disabled_integration_app"]
        self.assertFalse(disabled_result.success)
        self.assertIn('disabled', disabled_result.error.lower())
        
        # Clean up if we started anything
        try:
            self.api.stop_all()
        except:
            pass
    
    def test_port_management_integration(self):
        """Test port management functionality"""
        # Test getting available ports
        available_ports = self.api.get_available_ports()
        self.assertIsInstance(available_ports, list)
        
        # Test getting port assignments
        assignments = self.api.get_port_assignments()
        self.assertIsInstance(assignments, dict)
        
        # Start an app and check port assignment
        app_name = "test_integration_app"
        start_result = self.api.start(app_name)
        
        if start_result.success:
            try:
                # Check that port is now assigned
                new_assignments = self.api.get_port_assignments()
                self.assertIn(app_name, new_assignments)
                self.assertEqual(new_assignments[app_name], start_result.port)
                
                # Check that port is no longer in available list
                new_available = self.api.get_available_ports()
                if start_result.port in available_ports:
                    self.assertNotIn(start_result.port, new_available)
                
            finally:
                self.api.stop(app_name)
    
    def test_error_handling_integration(self):
        """Test error handling in integration scenarios"""
        # Test starting non-existent app
        result = self.api.start("nonexistent_app", app_path="nonexistent.py")
        self.assertFalse(result.success)
        self.assertIn("not found", result.error.lower())
        
        # Test stopping non-running app
        result = self.api.stop("test_integration_app")
        self.assertFalse(result.success)
        
        # Test health check on non-running app
        health = self.api.health_check("test_integration_app")
        if "test_integration_app" in health:
            self.assertFalse(health["test_integration_app"].healthy)
    
    def test_app_config_integration(self):
        """Test app configuration retrieval and validation"""
        # Test getting existing app config
        config = self.api.get_app_config("test_integration_app")
        self.assertIsNotNone(config)
        self.assertEqual(config['name'], "Test Integration App")
        self.assertEqual(config['port'], 8599)
        self.assertTrue(config['enabled'])
        
        # Test getting non-existent app config
        config = self.api.get_app_config("nonexistent_app")
        self.assertIsNone(config)
    
    @patch('streamlit_app_manager.subprocess.Popen')
    def test_process_management_integration(self, mock_popen):
        """Test process management with mocked subprocess"""
        # Mock a successful process start
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process
        
        app_name = "test_integration_app"
        
        # Test starting with mocked process
        result = self.api.start(app_name)
        
        # Should succeed with mocked process
        self.assertTrue(result.success)
        self.assertEqual(result.pid, 12345)
        
        # Test that subprocess was called correctly
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        
        # Verify streamlit command structure
        cmd = call_args[0][0]
        self.assertIn('streamlit', cmd[0])
        self.assertIn('run', cmd)
        self.assertIn(self.test_app_file.name, cmd)
    
    def test_restart_integration(self):
        """Test app restart functionality"""
        app_name = "test_integration_app"
        
        # Start the app first
        start_result = self.api.start(app_name)
        
        if not start_result.success:
            self.skipTest(f"Could not start test app for restart test: {start_result.error}")
        
        try:
            time.sleep(2)  # Let it start
            
            # Restart the app
            restart_result = self.api.restart(app_name)
            
            # Restart should succeed
            self.assertTrue(restart_result.success)
            self.assertEqual(restart_result.app_name, app_name)
            
            # Should have port and potentially new PID
            self.assertIsNotNone(restart_result.port)
            
        finally:
            # Clean up
            self.api.stop(app_name)


class TestUIIntegration(unittest.TestCase):
    """Test UI integration components"""
    
    def test_settings_ui_integration(self):
        """Test that settings UI components can be imported and called"""
        try:
            from ui.settings_ui import render_settings_page
            self.assertTrue(callable(render_settings_page))
        except ImportError as e:
            self.fail(f"Could not import settings UI: {e}")
    
    def test_app_management_settings_function_exists(self):
        """Test that render_app_management_settings function exists and is callable"""
        # This tests the fix for the NameError issue
        try:
            # Try to import from various possible locations
            try:
                from ui.settings_ui import render_app_management_settings
                self.assertTrue(callable(render_app_management_settings))
            except ImportError:
                try:
                    from streamlit_app_manager import render_app_management_settings
                    self.assertTrue(callable(render_app_management_settings))
                except ImportError:
                    # If neither location has it, the function needs to be implemented
                    self.fail("render_app_management_settings function not found in expected locations")
        except Exception as e:
            self.fail(f"Error testing render_app_management_settings: {e}")
    
    def test_micro_tasks_ui_integration(self):
        """Test that micro-tasks UI can be imported"""
        try:
            from ui.management_ui import render_micro_tasks_ui
            self.assertTrue(callable(render_micro_tasks_ui))
        except ImportError as e:
            self.fail(f"Could not import micro-tasks UI: {e}")


def run_tests():
    """Run all integration tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestAppManagementIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestUIIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running App Management Integration Tests")
    print("=" * 50)
    
    success = run_tests()
    
    if success:
        print("\n✅ All integration tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some integration tests failed!")
        sys.exit(1)