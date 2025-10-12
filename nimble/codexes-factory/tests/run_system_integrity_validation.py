#!/usr/bin/env python3
"""
Test runner for system integrity validation.

This script runs the comprehensive system integrity validation test
and provides a simple interface for executing the validation.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the tests directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from test_system_integrity_validation import SystemIntegrityValidator


def main():
    """Main function to run the system integrity validation."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive system integrity validation for cleanup operations"
    )
    parser.add_argument(
        "--root-path",
        default=".",
        help="Root path of the project (default: current directory)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run validation
    validator = SystemIntegrityValidator(args.root_path)
    results = validator.run_comprehensive_validation()
    
    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Tests Run: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['failed_tests']}")
    print(f"Warnings: {results['warnings']}")
    
    if results['overall_success']:
        print("\n✅ SYSTEM INTEGRITY VALIDATION PASSED")
        print("All critical functionality is preserved.")
        return 0
    else:
        print("\n❌ SYSTEM INTEGRITY VALIDATION FAILED")
        print("Some critical functionality may be broken.")
        print("Please review the detailed output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())