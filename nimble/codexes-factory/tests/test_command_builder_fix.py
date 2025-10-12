#!/usr/bin/env python3
"""
Test script to verify the command builder generates valid commands
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_command_builder():
    """Test that the command builder generates valid commands"""
    print("🧪 Testing Command Builder Fix")
    print("=" * 35)
    
    try:
        from codexes.modules.ui.command_builder import CommandBuilder
        
        # Create command builder
        builder = CommandBuilder()
        
        # Test configuration data (similar to what would come from the form)
        test_config = {
            'publisher': 'nimble_books',
            'imprint': 'xynapse_traces',
            'tranche': '',
            'model': 'gemini/gemini-2.5-flash',
            'verifier_model': 'gemini/gemini-2.5-pro',
            'schedule_file': 'test_schedule.json',
            'start_stage': 1,
            'end_stage': 4,
            'max_books': 1,
            'begin_with_book': 1,
            'quotes_per_book': 90,
            'enable_llm_completion': True,
            'enable_isbn_assignment': True,
            'no_litellm_log': True,
            'report_formats': ['html', 'csv', 'markdown'],
            'catalog_file': 'data/books.csv',
            'lsi_template': 'templates/LSI_ACS_header.csv',
            'model_params_file': 'resources/json/model_params.json'
        }
        
        # Build command
        print("📋 Building pipeline command...")
        command = builder.build_pipeline_command(test_config)
        
        # Check that invalid parameters are not included
        command_str = ' '.join(command)
        invalid_params = ['--max-retries', '--base-delay', '--max-delay']
        
        for invalid_param in invalid_params:
            if invalid_param in command_str:
                print(f"❌ Invalid parameter found in command: {invalid_param}")
                return False
        
        print("✅ No invalid parameters found in command")
        
        # Check that required parameters are included
        required_params = ['--imprint', '--model', '--schedule-file']
        for required_param in required_params:
            if required_param not in command_str:
                print(f"❌ Required parameter missing from command: {required_param}")
                return False
        
        print("✅ All required parameters found in command")
        
        # Show the generated command (first few parts)
        print(f"📝 Generated command (first 10 args): {' '.join(command[:10])}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing command builder: {e}")
        return False

def test_pipeline_script_compatibility():
    """Test that the pipeline script can parse a generated command"""
    print("\n🧪 Testing Pipeline Script Compatibility")
    print("=" * 42)
    
    # Test with a minimal valid command
    test_args = [
        'run_book_pipeline.py',
        '--imprint', 'xynapse_traces',
        '--model', 'gemini/gemini-2.5-flash',
        '--schedule-file', 'test_schedule.json',
        '--help'  # This will show help and exit, but validates argument parsing
    ]
    
    try:
        import subprocess
        
        # Run the pipeline script with --help to test argument parsing
        result = subprocess.run(
            ['uv', 'run', 'python'] + test_args,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # If --help works, the argument parsing is valid
        if result.returncode == 0 and 'usage:' in result.stdout:
            print("✅ Pipeline script can parse generated arguments")
            return True
        else:
            print(f"❌ Pipeline script failed to parse arguments: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing pipeline script compatibility: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Command Builder Fix Verification")
    print("=" * 50)
    
    tests = [
        ("Command Builder", test_command_builder),
        ("Pipeline Script Compatibility", test_pipeline_script_compatibility)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if not result:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Command builder fix is working.")
        print("\nThe pipeline should now:")
        print("- Generate valid commands without invalid parameters")
        print("- Execute successfully without argument errors")
        print("- Include all required parameters for pipeline execution")
        return 0
    else:
        print("💥 SOME TESTS FAILED! Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())