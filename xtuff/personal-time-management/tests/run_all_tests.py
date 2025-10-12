#!/usr/bin/env python3
"""
Comprehensive test runner for all new functionality
Runs unit tests and integration tests for the fixes and new features
"""

import unittest
import sys
import os
import time
from io import StringIO

# Add the parent directory to the path so we can import test modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all test modules
from tests.test_app_management_api import TestAppManagementAPI, TestConvenienceFunctions
from tests.test_micro_tasks import TestMicroTasks, TestMicroTaskConvenienceFunctions
from tests.test_countable_tasks import TestCountableTasks, TestCountableTaskConvenienceFunctions
from tests.test_quick_stats import TestQuickStats
from tests.test_integration_app_management import TestAppManagementIntegration, TestUIIntegration


class TestResults:
    """Class to track and display test results"""
    
    def __init__(self):
        self.results = {}
        self.total_tests = 0
        self.total_failures = 0
        self.total_errors = 0
        self.total_skipped = 0
    
    def add_result(self, test_name, result):
        """Add a test result"""
        self.results[test_name] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped),
            'success': result.wasSuccessful(),
            'failure_details': result.failures,
            'error_details': result.errors
        }
        
        self.total_tests += result.testsRun
        self.total_failures += len(result.failures)
        self.total_errors += len(result.errors)
        self.total_skipped += len(result.skipped)
    
    def print_summary(self):
        """Print a comprehensive test summary"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        # Print results for each test suite
        for test_name, result in self.results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"\n{status} {test_name}")
            print(f"  Tests run: {result['tests_run']}")
            
            if result['failures'] > 0:
                print(f"  Failures: {result['failures']}")
            if result['errors'] > 0:
                print(f"  Errors: {result['errors']}")
            if result['skipped'] > 0:
                print(f"  Skipped: {result['skipped']}")
        
        # Print overall summary
        print("\n" + "-" * 80)
        print("OVERALL SUMMARY")
        print("-" * 80)
        print(f"Total test suites: {len(self.results)}")
        print(f"Total tests run: {self.total_tests}")
        print(f"Total failures: {self.total_failures}")
        print(f"Total errors: {self.total_errors}")
        print(f"Total skipped: {self.total_skipped}")
        
        success_rate = ((self.total_tests - self.total_failures - self.total_errors) / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
        
        overall_success = self.total_failures == 0 and self.total_errors == 0
        status = "✅ ALL TESTS PASSED" if overall_success else "❌ SOME TESTS FAILED"
        print(f"\n{status}")
        
        # Print failure details if any
        if self.total_failures > 0 or self.total_errors > 0:
            print("\n" + "=" * 80)
            print("FAILURE AND ERROR DETAILS")
            print("=" * 80)
            
            for test_name, result in self.results.items():
                if result['failures'] or result['errors']:
                    print(f"\n{test_name}:")
                    
                    for failure in result['failure_details']:
                        print(f"  FAILURE: {failure[0]}")
                        print(f"    {failure[1]}")
                    
                    for error in result['error_details']:
                        print(f"  ERROR: {error[0]}")
                        print(f"    {error[1]}")
        
        return overall_success


def run_test_suite(test_classes, suite_name):
    """Run a test suite and return results"""
    print(f"\n{'='*60}")
    print(f"Running {suite_name}")
    print(f"{'='*60}")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    # Capture output
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    
    # Run tests
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Print results
    output = stream.getvalue()
    print(output)
    
    print(f"\n{suite_name} completed in {end_time - start_time:.2f} seconds")
    
    return result


def main():
    """Main test runner function"""
    print("Comprehensive Test Suite for Daily Engine Fixes")
    print("Testing: Micro-tasks, Countable-tasks, Quick Stats, App Management")
    print("=" * 80)
    
    results = TestResults()
    
    # Define test suites
    test_suites = [
        {
            'name': 'App Management API Tests',
            'classes': [TestAppManagementAPI, TestConvenienceFunctions]
        },
        {
            'name': 'Micro-Tasks Tests',
            'classes': [TestMicroTasks, TestMicroTaskConvenienceFunctions]
        },
        {
            'name': 'Countable Tasks Tests',
            'classes': [TestCountableTasks, TestCountableTaskConvenienceFunctions]
        },
        {
            'name': 'Quick Stats Tests',
            'classes': [TestQuickStats]
        },
        {
            'name': 'Integration Tests',
            'classes': [TestAppManagementIntegration, TestUIIntegration]
        }
    ]
    
    # Run each test suite
    for suite_info in test_suites:
        try:
            result = run_test_suite(suite_info['classes'], suite_info['name'])
            results.add_result(suite_info['name'], result)
        except Exception as e:
            print(f"❌ Error running {suite_info['name']}: {e}")
            # Create a mock result for failed suite
            mock_result = type('MockResult', (), {
                'testsRun': 0,
                'failures': [('Suite Error', str(e))],
                'errors': [],
                'skipped': [],
                'wasSuccessful': lambda: False
            })()
            results.add_result(suite_info['name'], mock_result)
    
    # Print comprehensive summary
    overall_success = results.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()