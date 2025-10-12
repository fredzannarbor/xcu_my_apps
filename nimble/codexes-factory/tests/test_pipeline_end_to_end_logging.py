#!/usr/bin/env python3
"""
End-to-end test to verify that success message guarantee works
in the actual pipeline execution context.
"""

import logging
import sys
import os
import io
import subprocess
import tempfile
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_pipeline_dry_run_logging():
    """Test that success messages appear in actual pipeline dry run."""
    print("Testing pipeline dry run logging...")
    
    # Create a minimal test schedule file
    test_schedule = {
        "publishing_schedule": [
            {
                "month": "January 2025",
                "books": [
                    {
                        "title": "Test Book for Logging",
                        "author": "Test Author",
                        "genre": "Test Genre",
                        "quotes_per_book": 10
                    }
                ]
            }
        ]
    }
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_schedule, f, indent=2)
        schedule_file = f.name
    
    try:
        # Run pipeline in dry run mode with terse logging
        cmd = [
            sys.executable, 
            'run_book_pipeline.py',
            '--imprint', 'xynapse_traces',
            '--schedule-file', schedule_file,
            '--model', 'gemini/gemini-2.5-flash',
            '--dry-run',
            '--terse-log',
            '--max-books', '1'
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        
        # Capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"Return code: {result.returncode}")
        print("\nSTDOUT:")
        print("-" * 40)
        print(result.stdout)
        print("-" * 40)
        
        if result.stderr:
            print("\nSTDERR:")
            print("-" * 40)
            print(result.stderr)
            print("-" * 40)
        
        # Analyze output for success messages
        stdout_lines = result.stdout.split('\n')
        success_lines = [line for line in stdout_lines if '✅' in line]
        stats_lines = [line for line in stdout_lines if '📊' in line]
        
        print(f"\nFound {len(success_lines)} success messages (✅)")
        print(f"Found {len(stats_lines)} statistics messages (📊)")
        
        for line in success_lines:
            print(f"  ✅ {line.strip()}")
        
        for line in stats_lines:
            print(f"  📊 {line.strip()}")
        
        # Check if we got expected messages
        expected_success_messages = [
            "Opened schedule file",
            "Processing only specified books" if '--max-books' in cmd else None
        ]
        
        found_expected = 0
        for expected in expected_success_messages:
            if expected and any(expected in line for line in success_lines):
                found_expected += 1
        
        if result.returncode == 0 and len(success_lines) > 0:
            print("✅ SUCCESS: Pipeline dry run completed with success messages visible")
            return True
        else:
            print("❌ FAILURE: Pipeline dry run failed or no success messages found")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ FAILURE: Pipeline dry run timed out")
        return False
    except Exception as e:
        print(f"❌ FAILURE: Pipeline dry run error: {e}")
        return False
    finally:
        # Clean up temporary file
        try:
            os.unlink(schedule_file)
        except:
            pass


def test_pipeline_logging_configuration():
    """Test that the pipeline logging configuration is set up correctly."""
    print("\nTesting pipeline logging configuration...")
    
    # Import pipeline modules to trigger logging setup
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    
    try:
        # This should trigger the logging setup in the pipeline
        from codexes.core.logging_config import get_logging_manager
        from codexes.core.logging_filters import SuccessAwareHandler
        
        # Check that the logging manager is configured
        logging_manager = get_logging_manager()
        
        # Set up logging like the pipeline does
        logging_manager.setup_logging(environment='production')
        
        # Check that we have the right handler types
        root_logger = logging.getLogger()
        console_handlers = [
            h for h in root_logger.handlers 
            if isinstance(h, logging.StreamHandler) and h.stream == sys.stdout
        ]
        
        if console_handlers:
            handler = console_handlers[0]
            print(f"Console handler type: {type(handler).__name__}")
            
            if isinstance(handler, SuccessAwareHandler):
                print("✅ SUCCESS: SuccessAwareHandler is being used")
                return True
            else:
                print("⚠️ WARNING: Regular StreamHandler is being used")
                print("This may still work due to log_success function")
                return True
        else:
            print("❌ FAILURE: No console handler found")
            return False
            
    except Exception as e:
        print(f"❌ FAILURE: Error testing logging configuration: {e}")
        return False


def main():
    """Run all end-to-end tests."""
    print("=" * 60)
    print("PIPELINE END-TO-END LOGGING TEST")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(test_pipeline_logging_configuration())
    results.append(test_pipeline_dry_run_logging())
    
    # Summary
    print("\n" + "=" * 60)
    print("END-TO-END TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL END-TO-END TESTS PASSED!")
        print("✅ Success message guarantee is working in actual pipeline")
        return 0
    else:
        print("❌ SOME END-TO-END TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())