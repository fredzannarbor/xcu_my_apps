#!/usr/bin/env python3
"""
Critical message filtering validation script.

This script validates that the LiteLLM filter never blocks critical error messages
and provides comprehensive testing of filter behavior with real-world scenarios.
"""

import logging
import sys
import os
from typing import List, Dict, Any, Tuple
import json
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codexes.core.logging_filters import LiteLLMFilter


class CriticalMessageValidator:
    """Validates that critical messages are never filtered out."""
    
    def __init__(self):
        """Initialize the validator."""
        self.filter = LiteLLMFilter(debug_mode=False)
        self.test_results = []
        self.validation_errors = []
    
    def validate_critical_error_messages(self) -> bool:
        """Validate that critical error messages always pass through."""
        print("🔍 Validating Critical Error Messages")
        print("=" * 50)
        
        critical_error_messages = [
            # Authentication errors
            ('litellm.main', logging.ERROR, 'Authentication failed for API key'),
            ('litellm.main', logging.ERROR, 'Invalid API key provided'),
            ('litellm.main', logging.ERROR, 'API key expired'),
            ('litellm.main', logging.ERROR, 'Unauthorized access attempt'),
            
            # Connection errors
            ('litellm.main', logging.ERROR, 'Connection timeout occurred'),
            ('litellm.main', logging.ERROR, 'Connection refused by server'),
            ('litellm.main', logging.ERROR, 'Network connection failed'),
            ('litellm.main', logging.ERROR, 'SSL connection error'),
            
            # Server errors
            ('litellm.main', logging.ERROR, 'Internal server error from provider'),
            ('litellm.main', logging.ERROR, 'Service unavailable'),
            ('litellm.main', logging.ERROR, 'Bad gateway response'),
            ('litellm.main', logging.ERROR, 'Gateway timeout'),
            
            # Rate limiting errors
            ('litellm.main', logging.ERROR, 'Rate limit exceeded'),
            ('litellm.main', logging.ERROR, 'Quota exceeded for model'),
            ('litellm.main', logging.ERROR, 'Too many requests'),
            
            # Model errors
            ('litellm.main', logging.ERROR, 'Model not found'),
            ('litellm.main', logging.ERROR, 'Model overloaded'),
            ('litellm.main', logging.ERROR, 'Model request failed'),
        ]
        
        all_passed = True
        
        for logger_name, level, message in critical_error_messages:
            record = logging.LogRecord(
                name=logger_name,
                level=level,
                pathname='test.py',
                lineno=1,
                msg=message,
                args=(),
                exc_info=None
            )
            
            passed = self.filter.filter(record)
            
            if not passed:
                self.validation_errors.append(f"CRITICAL ERROR BLOCKED: {message}")
                all_passed = False
                print(f"❌ BLOCKED: {message}")
            else:
                print(f"✅ PASSED: {message}")
            
            self.test_results.append({
                'type': 'critical_error',
                'logger': logger_name,
                'level': level,
                'message': message,
                'passed': passed,
                'expected': True
            })
        
        print(f"\n📊 Critical Error Messages: {len([r for r in self.test_results if r['type'] == 'critical_error' and r['passed']])}/{len(critical_error_messages)} passed")
        return all_passed
    
    def validate_critical_warning_messages(self) -> bool:
        """Validate that critical warning messages pass through."""
        print("\n🔍 Validating Critical Warning Messages")
        print("=" * 50)
        
        critical_warning_messages = [
            # Rate limiting warnings
            ('litellm.main', logging.WARNING, 'Rate limit warning - approaching limit'),
            ('litellm.main', logging.WARNING, 'Quota warning - 90% used'),
            ('litellm.main', logging.WARNING, 'Rate limit exceeded, retrying'),
            
            # Authentication warnings
            ('litellm.main', logging.WARNING, 'Authentication warning detected'),
            ('litellm.main', logging.WARNING, 'API key will expire soon'),
            
            # Service warnings
            ('litellm.main', logging.WARNING, 'Service degraded performance'),
            ('litellm.main', logging.WARNING, 'Service unavailable, using fallback'),
            ('litellm.main', logging.WARNING, 'Timeout warning - request taking long'),
            
            # Model warnings
            ('litellm.main', logging.WARNING, 'Model performance degraded'),
            ('litellm.main', logging.WARNING, 'Model fallback activated'),
        ]
        
        all_passed = True
        
        for logger_name, level, message in critical_warning_messages:
            record = logging.LogRecord(
                name=logger_name,
                level=level,
                pathname='test.py',
                lineno=1,
                msg=message,
                args=(),
                exc_info=None
            )
            
            passed = self.filter.filter(record)
            
            if not passed:
                self.validation_errors.append(f"CRITICAL WARNING BLOCKED: {message}")
                all_passed = False
                print(f"❌ BLOCKED: {message}")
            else:
                print(f"✅ PASSED: {message}")
            
            self.test_results.append({
                'type': 'critical_warning',
                'logger': logger_name,
                'level': level,
                'message': message,
                'passed': passed,
                'expected': True
            })
        
        print(f"\n📊 Critical Warning Messages: {len([r for r in self.test_results if r['type'] == 'critical_warning' and r['passed']])}/{len(critical_warning_messages)} passed")
        return all_passed
    
    def validate_info_level_critical_patterns(self) -> bool:
        """Validate that INFO level messages with critical patterns pass through."""
        print("\n🔍 Validating INFO Level Critical Patterns")
        print("=" * 50)
        
        info_critical_messages = [
            # These should pass due to critical patterns, even at INFO level
            ('litellm.main', logging.INFO, 'Request failed due to authentication error'),
            ('litellm.main', logging.INFO, 'Connection timeout detected in request'),
            ('litellm.main', logging.INFO, 'Service returned internal server error'),
            ('litellm.main', logging.INFO, 'Rate limit exceeded for current request'),
            ('litellm.main', logging.INFO, 'Quota exceeded notification received'),
            ('litellm.main', logging.INFO, 'Authentication failed for this request'),
            ('litellm.main', logging.INFO, 'Request failed with timeout'),
            ('litellm.main', logging.INFO, 'Service unavailable response received'),
            # Success messages should always pass through
            ('litellm.main', logging.INFO, 'Request completed successfully'),
            ('litellm.main', logging.INFO, '✅ Operation completed successfully'),
            ('litellm.main', logging.INFO, 'LLM call success with response'),
            ('litellm.main', logging.INFO, 'Wrapper: Completed Call, calling success_handler'),
        ]
        
        all_passed = True
        
        for logger_name, level, message in info_critical_messages:
            record = logging.LogRecord(
                name=logger_name,
                level=level,
                pathname='test.py',
                lineno=1,
                msg=message,
                args=(),
                exc_info=None
            )
            
            passed = self.filter.filter(record)
            
            if not passed:
                self.validation_errors.append(f"INFO CRITICAL PATTERN BLOCKED: {message}")
                all_passed = False
                print(f"❌ BLOCKED: {message}")
            else:
                print(f"✅ PASSED: {message}")
            
            self.test_results.append({
                'type': 'info_critical',
                'logger': logger_name,
                'level': level,
                'message': message,
                'passed': passed,
                'expected': True
            })
        
        print(f"\n📊 INFO Critical Patterns: {len([r for r in self.test_results if r['type'] == 'info_critical' and r['passed']])}/{len(info_critical_messages)} passed")
        return all_passed
    
    def validate_non_critical_filtering(self) -> bool:
        """Validate that non-critical messages are properly filtered."""
        print("\n🔍 Validating Non-Critical Message Filtering")
        print("=" * 50)
        
        non_critical_messages = [
            # Cost calculation messages (should be filtered)
            ('litellm.main', logging.INFO, 'Cost calculation completed for request'),
            ('litellm.main', logging.INFO, 'Calculating cost for completion'),
            ('litellm.main', logging.DEBUG, 'Token cost analysis in progress'),
            ('litellm.utils', logging.INFO, 'Pricing calculation started'),
            
            # Completion wrapper messages (should be filtered)
            ('litellm.completion', logging.INFO, 'Completion wrapper initialized'),
            ('litellm.completion', logging.DEBUG, 'Wrapper function called'),
            ('litellm.main', logging.INFO, 'LiteLLM completion processing'),
            
            # Utility messages (should be filtered)
            ('litellm.utils', logging.INFO, 'Token counting in progress'),
            ('litellm.utils', logging.DEBUG, 'Model mapping configured'),
            ('litellm.main', logging.INFO, 'Provider mapping updated'),
            ('litellm.main', logging.DEBUG, 'API key validation passed'),
            
            # Operational messages (should be filtered)
            ('litellm.main', logging.INFO, 'Making request to OpenAI'),
            ('litellm.main', logging.INFO, 'Received response from provider'),
            ('litellm.main', logging.DEBUG, 'Processing request headers'),
            ('litellm.main', logging.DEBUG, 'Response headers processed'),
            
            # Configuration messages (should be filtered)
            ('litellm.main', logging.INFO, 'Setting model configuration'),
            ('litellm.router', logging.INFO, 'Configuring provider settings'),
            ('litellm.main', logging.DEBUG, 'Loading configuration file'),
            ('litellm.proxy', logging.INFO, 'Initializing proxy client'),
        ]
        
        all_passed = True
        
        for logger_name, level, message in non_critical_messages:
            record = logging.LogRecord(
                name=logger_name,
                level=level,
                pathname='test.py',
                lineno=1,
                msg=message,
                args=(),
                exc_info=None
            )
            
            passed = self.filter.filter(record)
            
            if passed:
                self.validation_errors.append(f"NON-CRITICAL MESSAGE NOT FILTERED: {message}")
                all_passed = False
                print(f"❌ NOT FILTERED: {message}")
            else:
                print(f"✅ FILTERED: {message}")
            
            self.test_results.append({
                'type': 'non_critical',
                'logger': logger_name,
                'level': level,
                'message': message,
                'passed': passed,
                'expected': False
            })
        
        filtered_count = len([r for r in self.test_results if r['type'] == 'non_critical' and not r['passed']])
        print(f"\n📊 Non-Critical Messages: {filtered_count}/{len(non_critical_messages)} properly filtered")
        return all_passed
    
    def validate_non_litellm_messages(self) -> bool:
        """Validate that non-LiteLLM messages always pass through."""
        print("\n🔍 Validating Non-LiteLLM Message Handling")
        print("=" * 50)
        
        non_litellm_messages = [
            # Application messages (should always pass)
            ('myapp.main', logging.INFO, 'Application started successfully'),
            ('myapp.processor', logging.DEBUG, 'Processing user request'),
            ('myapp.database', logging.WARNING, 'Database connection slow'),
            ('myapp.api', logging.ERROR, 'API endpoint failed'),
            
            # Other library messages (should always pass)
            ('requests', logging.INFO, 'Making HTTP request'),
            ('urllib3', logging.DEBUG, 'Connection pool created'),
            ('openai', logging.INFO, 'OpenAI client initialized'),
            ('anthropic', logging.WARNING, 'Rate limit warning'),
            
            # System messages (should always pass)
            ('root', logging.INFO, 'System message'),
            ('__main__', logging.DEBUG, 'Main module debug'),
        ]
        
        all_passed = True
        
        for logger_name, level, message in non_litellm_messages:
            record = logging.LogRecord(
                name=logger_name,
                level=level,
                pathname='test.py',
                lineno=1,
                msg=message,
                args=(),
                exc_info=None
            )
            
            passed = self.filter.filter(record)
            
            if not passed:
                self.validation_errors.append(f"NON-LITELLM MESSAGE BLOCKED: {logger_name} - {message}")
                all_passed = False
                print(f"❌ BLOCKED: {logger_name} - {message}")
            else:
                print(f"✅ PASSED: {logger_name} - {message}")
            
            self.test_results.append({
                'type': 'non_litellm',
                'logger': logger_name,
                'level': level,
                'message': message,
                'passed': passed,
                'expected': True
            })
        
        print(f"\n📊 Non-LiteLLM Messages: {len([r for r in self.test_results if r['type'] == 'non_litellm' and r['passed']])}/{len(non_litellm_messages)} passed")
        return all_passed
    
    def validate_debug_mode_behavior(self) -> bool:
        """Validate that debug mode allows all messages through."""
        print("\n🔍 Validating Debug Mode Behavior")
        print("=" * 50)
        
        debug_filter = LiteLLMFilter(debug_mode=True)
        
        test_messages = [
            ('litellm.main', logging.DEBUG, 'Debug cost calculation message'),
            ('litellm.utils', logging.INFO, 'Token counting debug info'),
            ('litellm.completion', logging.DEBUG, 'Completion wrapper debug'),
            ('litellm.main', logging.INFO, 'Verbose operational message'),
        ]
        
        all_passed = True
        
        for logger_name, level, message in test_messages:
            record = logging.LogRecord(
                name=logger_name,
                level=level,
                pathname='test.py',
                lineno=1,
                msg=message,
                args=(),
                exc_info=None
            )
            
            passed = debug_filter.filter(record)
            
            if not passed:
                self.validation_errors.append(f"DEBUG MODE BLOCKED MESSAGE: {message}")
                all_passed = False
                print(f"❌ BLOCKED IN DEBUG: {message}")
            else:
                print(f"✅ PASSED IN DEBUG: {message}")
            
            self.test_results.append({
                'type': 'debug_mode',
                'logger': logger_name,
                'level': level,
                'message': message,
                'passed': passed,
                'expected': True
            })
        
        print(f"\n📊 Debug Mode Messages: {len([r for r in self.test_results if r['type'] == 'debug_mode' and r['passed']])}/{len(test_messages)} passed")
        return all_passed
    
    def validate_edge_cases(self) -> bool:
        """Validate edge cases and unusual scenarios."""
        print("\n🔍 Validating Edge Cases")
        print("=" * 50)
        
        edge_cases = [
            # Empty messages
            ('litellm.main', logging.INFO, ''),
            ('litellm.main', logging.ERROR, ''),
            
            # Very long messages
            ('litellm.main', logging.INFO, 'Cost calculation ' + 'x' * 1000),
            ('litellm.main', logging.ERROR, 'Authentication failed ' + 'y' * 1000),
            
            # Messages with special characters
            ('litellm.main', logging.INFO, 'Cost calculation with unicode: 🔥💰'),
            ('litellm.main', logging.ERROR, 'Error with special chars: @#$%^&*()'),
            
            # Mixed case patterns
            ('litellm.main', logging.INFO, 'COST CALCULATION in uppercase'),
            ('litellm.main', logging.ERROR, 'authentication FAILED mixed case'),
            
            # Partial pattern matches
            ('litellm.main', logging.INFO, 'This mentions cost but not calculation'),
            ('litellm.main', logging.ERROR, 'This has error but should pass'),
        ]
        
        all_passed = True
        
        for logger_name, level, message in edge_cases:
            record = logging.LogRecord(
                name=logger_name,
                level=level,
                pathname='test.py',
                lineno=1,
                msg=message,
                args=(),
                exc_info=None
            )
            
            try:
                passed = self.filter.filter(record)
                
                # Determine expected behavior
                if level >= logging.ERROR:
                    expected = True  # Errors should always pass
                elif any(pattern in message.lower() for pattern in ['error', 'failed', 'authentication']):
                    expected = True  # Critical patterns should pass
                elif any(pattern in message.lower() for pattern in ['cost calculation', 'token counting']):
                    expected = False  # Non-critical patterns should be filtered
                else:
                    expected = True  # Default to pass for edge cases
                
                if passed != expected:
                    self.validation_errors.append(f"EDGE CASE UNEXPECTED: {message} (got {passed}, expected {expected})")
                    all_passed = False
                    print(f"❌ UNEXPECTED: {message[:50]}... (got {passed}, expected {expected})")
                else:
                    print(f"✅ EXPECTED: {message[:50]}... ({passed})")
                
                self.test_results.append({
                    'type': 'edge_case',
                    'logger': logger_name,
                    'level': level,
                    'message': message[:100],  # Truncate for storage
                    'passed': passed,
                    'expected': expected
                })
                
            except Exception as e:
                self.validation_errors.append(f"EDGE CASE EXCEPTION: {message[:50]}... - {e}")
                all_passed = False
                print(f"❌ EXCEPTION: {message[:50]}... - {e}")
        
        edge_case_results = [r for r in self.test_results if r['type'] == 'edge_case']
        correct_count = len([r for r in edge_case_results if r['passed'] == r['expected']])
        print(f"\n📊 Edge Cases: {correct_count}/{len(edge_cases)} handled correctly")
        return all_passed
    
    def run_comprehensive_validation(self) -> bool:
        """Run comprehensive validation of critical message filtering."""
        print("🚀 Starting Comprehensive Critical Message Validation")
        print("=" * 80)
        
        validation_start = datetime.now()
        
        # Run all validation tests
        results = {
            'critical_errors': self.validate_critical_error_messages(),
            'critical_warnings': self.validate_critical_warning_messages(),
            'info_critical_patterns': self.validate_info_level_critical_patterns(),
            'non_critical_filtering': self.validate_non_critical_filtering(),
            'non_litellm_messages': self.validate_non_litellm_messages(),
            'debug_mode': self.validate_debug_mode_behavior(),
            'edge_cases': self.validate_edge_cases()
        }
        
        validation_end = datetime.now()
        validation_time = (validation_end - validation_start).total_seconds()
        
        # Generate summary
        all_passed = all(results.values())
        
        print("\n" + "=" * 80)
        print("📋 VALIDATION SUMMARY")
        print("=" * 80)
        
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"   {test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\n📊 Overall Statistics:")
        print(f"   • Total Tests: {len(self.test_results)}")
        print(f"   • Validation Time: {validation_time:.3f} seconds")
        print(f"   • Validation Errors: {len(self.validation_errors)}")
        
        # Test type breakdown
        test_types = {}
        for result in self.test_results:
            test_type = result['type']
            if test_type not in test_types:
                test_types[test_type] = {'total': 0, 'correct': 0}
            test_types[test_type]['total'] += 1
            if result['passed'] == result['expected']:
                test_types[test_type]['correct'] += 1
        
        print(f"\n📈 Test Type Breakdown:")
        for test_type, stats in test_types.items():
            accuracy = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
            print(f"   • {test_type.replace('_', ' ').title()}: {stats['correct']}/{stats['total']} ({accuracy:.1f}%)")
        
        # Show validation errors if any
        if self.validation_errors:
            print(f"\n❌ VALIDATION ERRORS ({len(self.validation_errors)}):")
            for i, error in enumerate(self.validation_errors[:10], 1):  # Show first 10
                print(f"   {i}. {error}")
            if len(self.validation_errors) > 10:
                print(f"   ... and {len(self.validation_errors) - 10} more errors")
        
        # Final result
        if all_passed:
            print(f"\n✅ ALL VALIDATIONS PASSED - Critical message filtering is working correctly!")
        else:
            print(f"\n❌ VALIDATION FAILED - Critical message filtering has issues!")
        
        return all_passed
    
    def save_validation_report(self, filename: str = None) -> str:
        """Save validation report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/critical_message_validation_{timestamp}.json"
        
        # Ensure logs directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': len(self.test_results),
                'validation_errors': len(self.validation_errors),
                'overall_passed': len(self.validation_errors) == 0
            },
            'test_results': self.test_results,
            'validation_errors': self.validation_errors,
            'filter_configuration': {
                'debug_mode': self.filter.debug_mode,
                'filtered_patterns_count': len(self.filter.get_filtered_patterns()),
                'critical_patterns_count': len(self.filter.get_critical_patterns())
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return filename


def main():
    """Main function to run critical message validation."""
    validator = CriticalMessageValidator()
    
    try:
        # Run comprehensive validation
        success = validator.run_comprehensive_validation()
        
        # Save report
        report_file = validator.save_validation_report()
        print(f"\n📁 Validation report saved to: {report_file}")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())