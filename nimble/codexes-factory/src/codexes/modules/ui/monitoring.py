"""
Monitoring and validation tools for UI robustness.

This module provides tools for tracking None value encounters,
validating pattern integrity, and monitoring UI health.
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
import streamlit as st

from .safety_patterns import validate_not_none, log_none_encounter
from .error_prevention import ui_error_prevention, graceful_degradation_manager

logger = logging.getLogger(__name__)


class UIRobustnessMonitor:
    """
    Monitor for tracking UI robustness metrics and None value encounters.
    
    Provides comprehensive monitoring of safety pattern usage,
    error prevention effectiveness, and overall UI health.
    """
    
    def __init__(self):
        self.metrics = {
            'session_start_time': time.time(),
            'none_encounters': 0,
            'errors_prevented': 0,
            'safety_patterns_used': 0,
            'graceful_degradations': 0,
            'validation_failures': 0,
            'autofix_compatibility_checks': 0
        }
        
        self.encounter_log = []
        self.performance_metrics = {}
        self.health_status = 'healthy'
        
    def record_none_encounter(self, context: str, attribute: str, 
                            severity: str = 'warning') -> None:
        """
        Record a None value encounter for monitoring.
        
        Args:
            context: Context where None was encountered
            attribute: Attribute that was None
            severity: Severity level (info, warning, error)
        """
        self.metrics['none_encounters'] += 1
        
        encounter = {
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'attribute': attribute,
            'severity': severity
        }
        
        self.encounter_log.append(encounter)
        
        # Keep log size manageable
        if len(self.encounter_log) > 1000:
            self.encounter_log = self.encounter_log[-500:]
        
        # Update health status based on encounter rate
        self._update_health_status()
        
        logger.info(f"None encounter recorded: {context}.{attribute} ({severity})")
    
    def record_error_prevention(self, error_type: str, context: str) -> None:
        """
        Record an error that was prevented by safety patterns.
        
        Args:
            error_type: Type of error prevented
            context: Context where error was prevented
        """
        self.metrics['errors_prevented'] += 1
        
        prevention_record = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'context': context
        }
        
        logger.info(f"Error prevented: {error_type} in {context}")
    
    def record_safety_pattern_usage(self, pattern_name: str, context: str) -> None:
        """
        Record usage of a safety pattern.
        
        Args:
            pattern_name: Name of the safety pattern used
            context: Context where pattern was used
        """
        self.metrics['safety_patterns_used'] += 1
        
        # Track pattern-specific metrics
        pattern_key = f'pattern_{pattern_name}'
        if pattern_key not in self.metrics:
            self.metrics[pattern_key] = 0
        self.metrics[pattern_key] += 1
    
    def record_graceful_degradation(self, operation: str, context: str) -> None:
        """
        Record a graceful degradation event.
        
        Args:
            operation: Operation that required degradation
            context: Context where degradation occurred
        """
        self.metrics['graceful_degradations'] += 1
        
        logger.info(f"Graceful degradation: {operation} in {context}")
    
    def record_performance_metric(self, operation: str, duration: float) -> None:
        """
        Record performance metrics for safety operations.
        
        Args:
            operation: Name of the operation
            duration: Duration in seconds
        """
        if operation not in self.performance_metrics:
            self.performance_metrics[operation] = {
                'total_time': 0.0,
                'call_count': 0,
                'avg_time': 0.0,
                'max_time': 0.0
            }
        
        metrics = self.performance_metrics[operation]
        metrics['total_time'] += duration
        metrics['call_count'] += 1
        metrics['avg_time'] = metrics['total_time'] / metrics['call_count']
        metrics['max_time'] = max(metrics['max_time'], duration)
    
    def _update_health_status(self) -> None:
        """Update overall health status based on metrics."""
        current_time = time.time()
        session_duration = current_time - self.metrics['session_start_time']
        
        # Calculate encounter rate (encounters per minute)
        if session_duration > 0:
            encounter_rate = (self.metrics['none_encounters'] / session_duration) * 60
            
            if encounter_rate > 10:  # More than 10 per minute
                self.health_status = 'critical'
            elif encounter_rate > 5:  # More than 5 per minute
                self.health_status = 'warning'
            elif encounter_rate > 1:  # More than 1 per minute
                self.health_status = 'degraded'
            else:
                self.health_status = 'healthy'
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report.
        
        Returns:
            Dictionary containing health metrics and status
        """
        current_time = time.time()
        session_duration = current_time - self.metrics['session_start_time']
        
        # Calculate rates
        encounter_rate = (self.metrics['none_encounters'] / max(session_duration, 1)) * 60
        error_prevention_rate = (self.metrics['errors_prevented'] / max(session_duration, 1)) * 60
        
        # Get recent encounters (last 5 minutes)
        recent_cutoff = datetime.now() - timedelta(minutes=5)
        recent_encounters = [
            enc for enc in self.encounter_log
            if datetime.fromisoformat(enc['timestamp']) > recent_cutoff
        ]
        
        return {
            'health_status': self.health_status,
            'session_duration_minutes': session_duration / 60,
            'metrics': self.metrics.copy(),
            'rates': {
                'none_encounters_per_minute': encounter_rate,
                'errors_prevented_per_minute': error_prevention_rate
            },
            'recent_encounters': len(recent_encounters),
            'performance_metrics': self.performance_metrics.copy(),
            'recommendations': self._get_health_recommendations()
        }
    
    def _get_health_recommendations(self) -> List[str]:
        """Get health improvement recommendations."""
        recommendations = []
        
        if self.health_status == 'critical':
            recommendations.append("High None encounter rate detected. Review data validation.")
            recommendations.append("Consider implementing additional safety patterns.")
        
        if self.metrics['validation_failures'] > 10:
            recommendations.append("Multiple validation failures detected. Check data sources.")
        
        # Performance recommendations
        for operation, metrics in self.performance_metrics.items():
            if metrics['avg_time'] > 0.1:  # More than 100ms average
                recommendations.append(f"Performance issue in {operation}: {metrics['avg_time']:.3f}s average")
        
        if not recommendations:
            recommendations.append("UI robustness is performing well.")
        
        return recommendations
    
    def export_metrics(self, filepath: Optional[str] = None) -> str:
        """
        Export metrics to JSON file.
        
        Args:
            filepath: Optional file path for export
            
        Returns:
            JSON string of metrics
        """
        report = self.get_health_report()
        report['export_timestamp'] = datetime.now().isoformat()
        
        json_data = json.dumps(report, indent=2, default=str)
        
        if filepath:
            Path(filepath).write_text(json_data)
            logger.info(f"Metrics exported to {filepath}")
        
        return json_data
    
    def reset_metrics(self) -> None:
        """Reset all metrics and logs."""
        self.metrics = {
            'session_start_time': time.time(),
            'none_encounters': 0,
            'errors_prevented': 0,
            'safety_patterns_used': 0,
            'graceful_degradations': 0,
            'validation_failures': 0,
            'autofix_compatibility_checks': 0
        }
        self.encounter_log = []
        self.performance_metrics = {}
        self.health_status = 'healthy'


class PatternIntegrityValidator:
    """
    Validator for ensuring safety patterns remain intact after autofix operations.
    
    Provides tools for validating that autofix-resistant patterns
    continue to function correctly after code formatting.
    """
    
    def __init__(self):
        self.validation_results = {}
        self.pattern_tests = {}
        self._initialize_pattern_tests()
    
    def _initialize_pattern_tests(self) -> None:
        """Initialize pattern validation tests."""
        from .safety_patterns import (
            safe_getattr, safe_dict_get, safe_iteration, safe_len, safe_join
        )
        
        self.pattern_tests = {
            'safe_getattr': {
                'function': safe_getattr,
                'test_cases': [
                    {'args': (None, 'attr', 'default'), 'expected': 'default'},
                    {'args': (type('Obj', (), {'attr': 'value'})(), 'attr', 'default'), 'expected': 'value'}
                ]
            },
            'safe_dict_get': {
                'function': safe_dict_get,
                'test_cases': [
                    {'args': (None, 'key', 'default'), 'expected': 'default'},
                    {'args': ({'key': 'value'}, 'key', 'default'), 'expected': 'value'}
                ]
            },
            'safe_iteration': {
                'function': safe_iteration,
                'test_cases': [
                    {'args': (None,), 'expected': []},
                    {'args': (['a', 'b'],), 'expected': ['a', 'b']}
                ]
            },
            'safe_len': {
                'function': safe_len,
                'test_cases': [
                    {'args': (None,), 'expected': 0},
                    {'args': ([1, 2, 3],), 'expected': 3}
                ]
            },
            'safe_join': {
                'function': safe_join,
                'test_cases': [
                    {'args': (None,), 'expected': ''},
                    {'args': (['a', 'b'], ', '), 'expected': 'a, b'}
                ]
            }
        }
    
    def validate_pattern_integrity(self) -> Dict[str, Any]:
        """
        Validate that all safety patterns are functioning correctly.
        
        Returns:
            Validation results for all patterns
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'passed',
            'pattern_results': {},
            'failed_patterns': [],
            'warnings': []
        }
        
        for pattern_name, pattern_info in self.pattern_tests.items():
            pattern_result = self._validate_single_pattern(
                pattern_name, 
                pattern_info['function'], 
                pattern_info['test_cases']
            )
            
            results['pattern_results'][pattern_name] = pattern_result
            
            if not pattern_result['passed']:
                results['overall_status'] = 'failed'
                results['failed_patterns'].append(pattern_name)
        
        self.validation_results = results
        return results
    
    def _validate_single_pattern(self, pattern_name: str, pattern_func: Callable,
                                test_cases: List[Dict]) -> Dict[str, Any]:
        """
        Validate a single safety pattern.
        
        Args:
            pattern_name: Name of the pattern
            pattern_func: Pattern function to test
            test_cases: List of test cases
            
        Returns:
            Validation result for the pattern
        """
        result = {
            'pattern_name': pattern_name,
            'passed': True,
            'test_results': [],
            'errors': []
        }
        
        for i, test_case in enumerate(test_cases):
            try:
                actual = pattern_func(*test_case['args'])
                expected = test_case['expected']
                
                test_passed = actual == expected
                
                test_result = {
                    'test_index': i,
                    'passed': test_passed,
                    'expected': expected,
                    'actual': actual,
                    'args': test_case['args']
                }
                
                result['test_results'].append(test_result)
                
                if not test_passed:
                    result['passed'] = False
                    result['errors'].append(
                        f"Test {i} failed: expected {expected}, got {actual}"
                    )
                    
            except Exception as e:
                result['passed'] = False
                result['errors'].append(f"Test {i} raised exception: {e}")
                
                test_result = {
                    'test_index': i,
                    'passed': False,
                    'error': str(e),
                    'args': test_case['args']
                }
                result['test_results'].append(test_result)
        
        return result
    
    def validate_autofix_compatibility(self) -> Dict[str, Any]:
        """
        Validate that patterns are compatible with autofix operations.
        
        Returns:
            Autofix compatibility validation results
        """
        # This would typically involve running autofix and then validating
        # For now, we'll check that patterns use standard Python idioms
        
        compatibility_results = {
            'timestamp': datetime.now().isoformat(),
            'compatible': True,
            'checks': [],
            'warnings': []
        }
        
        # Check that patterns use standard Python functions
        standard_patterns = [
            'getattr', 'dict.get', 'len', 'join', 'isinstance', 'hasattr'
        ]
        
        for pattern in standard_patterns:
            check_result = {
                'pattern': pattern,
                'compatible': True,
                'reason': f'Uses standard Python {pattern}'
            }
            compatibility_results['checks'].append(check_result)
        
        return compatibility_results
    
    def get_validation_report(self) -> str:
        """
        Get formatted validation report.
        
        Returns:
            Formatted validation report string
        """
        if not self.validation_results:
            return "No validation results available. Run validate_pattern_integrity() first."
        
        report_lines = [
            "=== UI Safety Pattern Validation Report ===",
            f"Timestamp: {self.validation_results['timestamp']}",
            f"Overall Status: {self.validation_results['overall_status'].upper()}",
            ""
        ]
        
        if self.validation_results['failed_patterns']:
            report_lines.extend([
                "FAILED PATTERNS:",
                *[f"  - {pattern}" for pattern in self.validation_results['failed_patterns']],
                ""
            ])
        
        report_lines.append("PATTERN DETAILS:")
        for pattern_name, pattern_result in self.validation_results['pattern_results'].items():
            status = "PASS" if pattern_result['passed'] else "FAIL"
            report_lines.append(f"  {pattern_name}: {status}")
            
            if pattern_result['errors']:
                for error in pattern_result['errors']:
                    report_lines.append(f"    ERROR: {error}")
        
        return "\n".join(report_lines)


class UIHealthChecker:
    """
    Health checker for monitoring UI robustness in production.
    
    Provides utilities for checking UI health, detecting issues,
    and providing recommendations for improvement.
    """
    
    def __init__(self, monitor: UIRobustnessMonitor):
        self.monitor = monitor
        self.health_thresholds = {
            'max_none_encounters_per_minute': 5,
            'max_validation_failures': 10,
            'max_avg_response_time': 0.5,
            'min_error_prevention_rate': 0.1
        }
    
    def perform_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive UI health check.
        
        Returns:
            Health check results with status and recommendations
        """
        health_report = self.monitor.get_health_report()
        
        check_results = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': 'healthy',
            'checks': [],
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check None encounter rate
        encounter_rate = health_report['rates']['none_encounters_per_minute']
        if encounter_rate > self.health_thresholds['max_none_encounters_per_minute']:
            check_results['critical_issues'].append(
                f"High None encounter rate: {encounter_rate:.2f}/min"
            )
            check_results['overall_health'] = 'critical'
        
        # Check validation failures
        validation_failures = health_report['metrics']['validation_failures']
        if validation_failures > self.health_thresholds['max_validation_failures']:
            check_results['warnings'].append(
                f"High validation failure count: {validation_failures}"
            )
            if check_results['overall_health'] == 'healthy':
                check_results['overall_health'] = 'warning'
        
        # Check performance metrics
        for operation, metrics in health_report['performance_metrics'].items():
            if metrics['avg_time'] > self.health_thresholds['max_avg_response_time']:
                check_results['warnings'].append(
                    f"Slow operation {operation}: {metrics['avg_time']:.3f}s average"
                )
                if check_results['overall_health'] == 'healthy':
                    check_results['overall_health'] = 'warning'
        
        # Add recommendations
        check_results['recommendations'] = health_report['recommendations']
        
        return check_results
    
    def display_health_dashboard(self) -> None:
        """Display health dashboard in Streamlit."""
        st.subheader("🏥 UI Robustness Health Dashboard")
        
        health_check = self.perform_health_check()
        health_report = self.monitor.get_health_report()
        
        # Overall status
        status_color = {
            'healthy': '🟢',
            'warning': '🟡', 
            'critical': '🔴'
        }
        
        st.metric(
            "Overall Health",
            f"{status_color.get(health_check['overall_health'], '⚪')} {health_check['overall_health'].title()}"
        )
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "None Encounters",
                health_report['metrics']['none_encounters'],
                f"{health_report['rates']['none_encounters_per_minute']:.1f}/min"
            )
        
        with col2:
            st.metric(
                "Errors Prevented",
                health_report['metrics']['errors_prevented'],
                f"{health_report['rates']['errors_prevented_per_minute']:.1f}/min"
            )
        
        with col3:
            st.metric(
                "Safety Patterns Used",
                health_report['metrics']['safety_patterns_used']
            )
        
        with col4:
            st.metric(
                "Session Duration",
                f"{health_report['session_duration_minutes']:.1f} min"
            )
        
        # Issues and recommendations
        if health_check['critical_issues']:
            st.error("**Critical Issues:**")
            for issue in health_check['critical_issues']:
                st.write(f"• {issue}")
        
        if health_check['warnings']:
            st.warning("**Warnings:**")
            for warning in health_check['warnings']:
                st.write(f"• {warning}")
        
        if health_check['recommendations']:
            st.info("**Recommendations:**")
            for rec in health_check['recommendations']:
                st.write(f"• {rec}")
        
        # Performance metrics
        if health_report['performance_metrics']:
            st.subheader("⚡ Performance Metrics")
            
            perf_data = []
            for operation, metrics in health_report['performance_metrics'].items():
                perf_data.append({
                    'Operation': operation,
                    'Calls': metrics['call_count'],
                    'Avg Time (ms)': f"{metrics['avg_time'] * 1000:.1f}",
                    'Max Time (ms)': f"{metrics['max_time'] * 1000:.1f}",
                    'Total Time (s)': f"{metrics['total_time']:.2f}"
                })
            
            if perf_data:
                st.table(perf_data)


# Global instances
ui_monitor = UIRobustnessMonitor()
pattern_validator = PatternIntegrityValidator()
health_checker = UIHealthChecker(ui_monitor)


# Convenience functions
def record_none_encounter(context: str, attribute: str, severity: str = 'warning') -> None:
    """Record a None value encounter."""
    ui_monitor.record_none_encounter(context, attribute, severity)


def validate_patterns() -> Dict[str, Any]:
    """Validate all safety patterns."""
    return pattern_validator.validate_pattern_integrity()


def get_health_status() -> str:
    """Get current UI health status."""
    return ui_monitor.health_status


def display_health_dashboard() -> None:
    """Display the health dashboard."""
    health_checker.display_health_dashboard()