"""
Error Recovery Module

This module provides comprehensive error recovery mechanisms for the LSI CSV generation pipeline.
It implements various recovery strategies to handle different types of errors gracefully.
"""

import json
import logging
import threading
import traceback
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from functools import wraps

logger = logging.getLogger(__name__)


class RecoveryStrategy(Enum):
    """Available error recovery strategies."""
    RETRY = "retry"
    FALLBACK_VALUE = "fallback_value"
    USE_DEFAULT = "use_default"
    SKIP_FIELD = "skip_field"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class ErrorContext:
    """Context information about an error."""
    operation: str
    error_type: str
    error_message: str
    timestamp: datetime = field(default_factory=datetime.now)
    book_id: Optional[str] = None
    field_name: Optional[str] = None
    batch_id: Optional[str] = None
    stack_trace: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class RecoveryAction:
    """Defines a recovery action to take for an error."""
    strategy: RecoveryStrategy
    max_retries: int = 3
    retry_delay: float = 1.0
    fallback_value: Any = None
    description: str = ""


@dataclass
class ErrorRecoveryResult:
    """Result of an error recovery attempt."""
    success: bool
    recovered_value: Any = None
    strategy_used: Optional[RecoveryStrategy] = None
    attempts_made: int = 0
    fallback_used: bool = False
    error_message: Optional[str] = None


class ErrorRecoveryManager:
    """Manages error recovery strategies and execution."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.recovery_strategies: Dict[str, List[RecoveryAction]] = {}
        self.fallback_values: Dict[str, Any] = {}
        self.recovery_stats: Dict[str, Dict[str, Any]] = {}
        self.error_history: List[ErrorContext] = []
        self._lock = threading.Lock()
        
        # Initialize default strategies
        self._initialize_default_strategies()
        
        # Load configuration if provided
        if config_file and Path(config_file).exists():
            self._load_config(config_file)
    
    def register_recovery_strategy(self, error_type: str, strategies: List[RecoveryAction]):
        """Register recovery strategies for a specific error type."""
        self.recovery_strategies[error_type] = strategies
        logger.debug(f"Registered {len(strategies)} recovery strategies for error type: {error_type}")
    
    def recover_from_error(self, error_context: ErrorContext, 
                          original_function: Optional[Callable] = None,
                          *args, **kwargs) -> ErrorRecoveryResult:
        """Attempt to recover from an error using registered strategies."""
        with self._lock:
            self.error_history.append(error_context)
        
        logger.info(f"Attempting error recovery for: {error_context.operation} - {error_context.error_type}")
        
        # Find matching recovery strategies
        matching_strategies = self._find_matching_strategies(error_context)
        
        if not matching_strategies:
            logger.warning(f"No recovery strategies found for error type: {error_context.error_type}")
            return ErrorRecoveryResult(
                success=False,
                error_message="No recovery strategies available"
            )
        
        # Try each strategy group
        for strategy_group in matching_strategies:
            for action in strategy_group:
                try:
                    logger.debug(f"Trying recovery strategy: {action.strategy.value}")
                    
                    result = self._execute_recovery_action(action, error_context, 
                                                         original_function, *args, **kwargs)
                    
                    # Update statistics
                    self._update_recovery_stats(error_context.error_type, action.strategy, result.success)
                    
                    if result.success:
                        logger.info(f"Successfully recovered using strategy: {action.strategy.value}")
                        return result
                    else:
                        logger.debug(f"Recovery strategy failed: {action.strategy.value} - {result.error_message}")
                
                except Exception as e:
                    logger.error(f"Error executing recovery strategy {action.strategy.value}: {e}")
                    continue
        
        # All strategies failed
        logger.error(f"All recovery strategies failed for: {error_context.operation}")
        return ErrorRecoveryResult(
            success=False,
            error_message="All recovery strategies failed"
        )
    
    def _execute_recovery_action(self, action: RecoveryAction, error_context: ErrorContext,
                               original_function: Optional[Callable] = None,
                               *args, **kwargs) -> ErrorRecoveryResult:
        """Execute a specific recovery action."""
        if action.strategy == RecoveryStrategy.RETRY:
            return self._execute_retry_strategy(action, error_context, original_function, *args, **kwargs)
        elif action.strategy == RecoveryStrategy.FALLBACK_VALUE:
            return self._execute_fallback_value_strategy(action, error_context)
        elif action.strategy == RecoveryStrategy.USE_DEFAULT:
            return self._execute_default_value_strategy(action, error_context)
        elif action.strategy == RecoveryStrategy.SKIP_FIELD:
            return self._execute_skip_field_strategy(action, error_context)
        elif action.strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
            return self._execute_graceful_degradation_strategy(action, error_context)
        elif action.strategy == RecoveryStrategy.MANUAL_INTERVENTION:
            return self._execute_manual_intervention_strategy(action, error_context)
        else:
            return ErrorRecoveryResult(
                success=False,
                error_message=f"Unknown recovery strategy: {action.strategy}"
            )
    
    def _execute_retry_strategy(self, action: RecoveryAction, error_context: ErrorContext,
                              original_function: Optional[Callable] = None,
                              *args, **kwargs) -> ErrorRecoveryResult:
        """Execute retry recovery strategy."""
        if not original_function:
            return ErrorRecoveryResult(
                success=False,
                error_message="Cannot retry without original function"
            )
        
        import time
        last_error = None
        
        for attempts in range(1, action.max_retries + 1):
            try:
                logger.debug(f"Retry attempt {attempts}/{action.max_retries}")
                
                if attempts > 1:
                    time.sleep(action.retry_delay * (attempts - 1))  # Exponential backoff
                
                result = original_function(*args, **kwargs)
                
                return ErrorRecoveryResult(
                    success=True,
                    recovered_value=result,
                    strategy_used=RecoveryStrategy.RETRY,
                    attempts_made=attempts
                )
            
            except Exception as e:
                last_error = str(e)
                logger.debug(f"Retry attempt {attempts} failed: {e}")
                continue
        
        return ErrorRecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.RETRY,
            attempts_made=attempts,
            error_message=f"All {action.max_retries} retry attempts failed. Last error: {last_error}"
        )
    
    def _execute_fallback_value_strategy(self, action: RecoveryAction, 
                                       error_context: ErrorContext) -> ErrorRecoveryResult:
        """Execute fallback value recovery strategy."""
        fallback_value = None
        
        # Try action-specific fallback value first
        if action.fallback_value is not None:
            fallback_value = action.fallback_value
        
        # Try field-specific fallback value
        elif error_context.field_name and error_context.field_name in self.fallback_values:
            fallback_value = self.fallback_values[error_context.field_name]
        
        # Try operation-specific fallback value
        elif error_context.operation in self.fallback_values:
            fallback_value = self.fallback_values[error_context.operation]
        
        # Generate intelligent fallback based on field type
        else:
            fallback_value = self._generate_intelligent_fallback(error_context)
        
        if fallback_value is not None:
            logger.info(f"Using fallback value for {error_context.field_name}: {fallback_value}")
            return ErrorRecoveryResult(
                success=True,
                recovered_value=fallback_value,
                strategy_used=RecoveryStrategy.FALLBACK_VALUE,
                fallback_used=True
            )
        
        return ErrorRecoveryResult(
            success=False,
            error_message="No fallback value available"
        )
    
    def _execute_default_value_strategy(self, action: RecoveryAction, 
                                      error_context: ErrorContext) -> ErrorRecoveryResult:
        """Execute default value recovery strategy."""
        default_values = {
            # Common LSI field defaults
            'Binding Type': 'Paperback',
            'Interior Color': 'BW',
            'Paper Color': 'White',
            'Language': 'en',
            'Country of Publication': 'US',
            'Currency': 'USD',
            'Territory Rights': 'Worldwide',
            'Return Policy': 'Standard',
            'Age Range From': '',
            'Age Range To': '',
            'Series Title': '',
            'Volume Number': '',
            'Edition': '1',
            'Copyright Year': str(datetime.now().year)
        }
        
        field_name = error_context.field_name
        if field_name and field_name in default_values:
            default_value = default_values[field_name]
            logger.info(f"Using default value for {field_name}: {default_value}")
            
            return ErrorRecoveryResult(
                success=True,
                recovered_value=default_value,
                strategy_used=RecoveryStrategy.USE_DEFAULT,
                fallback_used=True
            )
        
        return ErrorRecoveryResult(
            success=False,
            error_message=f"No default value available for field: {field_name}"
        )
    
    def _execute_skip_field_strategy(self, action: RecoveryAction, 
                                   error_context: ErrorContext) -> ErrorRecoveryResult:
        """Execute skip field recovery strategy."""
        logger.info(f"Skipping field due to error: {error_context.field_name}")
        
        return ErrorRecoveryResult(
            success=True,
            recovered_value=None,  # Empty value
            strategy_used=RecoveryStrategy.SKIP_FIELD
        )
    
    def _execute_graceful_degradation_strategy(self, action: RecoveryAction, 
                                             error_context: ErrorContext) -> ErrorRecoveryResult:
        """Execute graceful degradation recovery strategy."""
        # Implement graceful degradation based on field importance
        field_importance = {
            'Title': 'critical',
            'ISBN': 'critical',
            'Author': 'high',
            'List Price': 'high',
            'Page Count': 'high',
            'Short Description': 'medium',
            'Long Description': 'medium',
            'BISAC Category': 'medium',
            'Keywords': 'low',
            'Series Title': 'low'
        }
        
        field_name = error_context.field_name
        importance = field_importance.get(field_name, 'low')
        
        if importance == 'critical':
            # Critical fields cannot be degraded
            return ErrorRecoveryResult(
                success=False,
                error_message=f"Cannot degrade critical field: {field_name}"
            )
        
        elif importance == 'high':
            # Try to provide a minimal acceptable value
            minimal_value = self._get_minimal_acceptable_value(field_name)
            if minimal_value:
                logger.warning(f"Using minimal value for high-importance field {field_name}: {minimal_value}")
                return ErrorRecoveryResult(
                    success=True,
                    recovered_value=minimal_value,
                    strategy_used=RecoveryStrategy.GRACEFUL_DEGRADATION,
                    fallback_used=True
                )
        
        else:
            # Medium/low importance fields can be left empty
            logger.info(f"Gracefully degrading field {field_name} (importance: {importance})")
            return ErrorRecoveryResult(
                success=True,
                recovered_value='',
                strategy_used=RecoveryStrategy.GRACEFUL_DEGRADATION
            )
        
        return ErrorRecoveryResult(
            success=False,
            error_message="Graceful degradation not possible"
        )
    
    def _execute_manual_intervention_strategy(self, action: RecoveryAction, 
                                            error_context: ErrorContext) -> ErrorRecoveryResult:
        """Execute manual intervention recovery strategy."""
        # Log the error for manual review
        manual_review_data = {
            'timestamp': error_context.timestamp.isoformat(),
            'operation': error_context.operation,
            'error_type': error_context.error_type,
            'error_message': error_context.error_message,
            'book_id': error_context.book_id,
            'field_name': error_context.field_name,
            'batch_id': error_context.batch_id,
            'additional_data': error_context.additional_data
        }
        
        # Save to manual review queue
        self._save_for_manual_review(manual_review_data)
        
        logger.warning(f"Error requires manual intervention: {error_context.operation}")
        
        # For now, return a placeholder value to allow processing to continue
        placeholder_value = self._get_placeholder_value(error_context.field_name)
        
        return ErrorRecoveryResult(
            success=True,
            recovered_value=placeholder_value,
            strategy_used=RecoveryStrategy.MANUAL_INTERVENTION,
            fallback_used=True
        )
    
    def _generate_intelligent_fallback(self, error_context: ErrorContext) -> Any:
        """Generate intelligent fallback values based on context."""
        field_name = error_context.field_name
        if not field_name:
            return None
        
        field_lower = field_name.lower()
        
        # Price fields
        if 'price' in field_lower:
            return '0.00'
        
        # Date fields
        elif 'date' in field_lower:
            return datetime.now().strftime('%Y-%m-%d')
        
        # Boolean fields
        elif any(term in field_lower for term in ['active', 'available', 'enabled']):
            return 'true'
        
        # Numeric fields
        elif any(term in field_lower for term in ['count', 'number', 'quantity', 'age']):
            return '0'
        
        # Description fields
        elif 'description' in field_lower:
            return 'Description not available'
        
        # Category/classification fields
        elif any(term in field_lower for term in ['category', 'genre', 'subject']):
            return 'General'
        
        # Default to empty string
        else:
            return ''
    
    def _get_minimal_acceptable_value(self, field_name: str) -> Optional[str]:
        """Get minimal acceptable value for high-importance fields."""
        minimal_values = {
            'Author': 'Unknown Author',
            'List Price': '0.00',
            'Page Count': '1',
            'Short Description': 'No description available',
            'Publisher': 'Independent Publisher',
            'Publication Date': datetime.now().strftime('%Y-%m-%d')
        }
        
        return minimal_values.get(field_name)
    
    def _get_placeholder_value(self, field_name: str) -> str:
        """Get placeholder value for manual intervention cases."""
        if not field_name:
            return '[MANUAL_REVIEW_REQUIRED]'
        
        return f'[MANUAL_REVIEW_REQUIRED_{field_name.upper().replace(" ", "_")}]'
    
    def _save_for_manual_review(self, review_data: Dict[str, Any]):
        """Save error data for manual review."""
        review_dir = Path("logs/manual_review")
        review_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"manual_review_{timestamp}.json"
        
        try:
            with open(review_dir / filename, 'w') as f:
                json.dump(review_data, f, indent=2, default=str)
            
            logger.info(f"Saved error for manual review: {filename}")
        except Exception as e:
            logger.error(f"Failed to save manual review data: {e}")
    
    def _find_matching_strategies(self, error_context: ErrorContext) -> List[List[RecoveryAction]]:
        """Find recovery strategies that match the error context."""
        matching_strategies = []
        
        # Check for exact error type match
        if error_context.error_type in self.recovery_strategies:
            matching_strategies.append(self.recovery_strategies[error_context.error_type])
        
        # Check for pattern matches
        for pattern, strategies in self.recovery_strategies.items():
            if pattern != error_context.error_type:
                # Simple pattern matching (could be enhanced with regex)
                if (pattern.lower() in error_context.error_message.lower() or 
                    pattern.lower() in error_context.operation.lower()):
                    matching_strategies.append(strategies)
        
        # Add default strategies if no specific matches found
        if not matching_strategies and 'default' in self.recovery_strategies:
            matching_strategies.append(self.recovery_strategies['default'])
        
        return matching_strategies
    
    def _update_recovery_stats(self, error_type: str, strategy: RecoveryStrategy, success: bool):
        """Update recovery statistics."""
        with self._lock:
            if error_type not in self.recovery_stats:
                self.recovery_stats[error_type] = {
                    'total_attempts': 0,
                    'successful_recoveries': 0,
                    'strategy_success': {}
                }
            
            stats = self.recovery_stats[error_type]
            stats['total_attempts'] += 1
            
            if success:
                stats['successful_recoveries'] += 1
            
            strategy_name = strategy.value
            if strategy_name not in stats['strategy_success']:
                stats['strategy_success'][strategy_name] = {'attempts': 0, 'successes': 0}
            
            stats['strategy_success'][strategy_name]['attempts'] += 1
            if success:
                stats['strategy_success'][strategy_name]['successes'] += 1
    
    def _initialize_default_strategies(self):
        """Initialize default recovery strategies."""
        # JSON parsing errors
        json_strategies = [
            RecoveryAction(
                strategy=RecoveryStrategy.RETRY,
                max_retries=2,
                retry_delay=0.5,
                description="Retry JSON parsing with delay"
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK_VALUE,
                fallback_value={},
                description="Use empty JSON object as fallback"
            )
        ]
        self.register_recovery_strategy("JSONDecodeError", json_strategies)
        
        # LLM API errors
        llm_strategies = [
            RecoveryAction(
                strategy=RecoveryStrategy.RETRY,
                max_retries=3,
                retry_delay=2.0,
                description="Retry LLM API call with exponential backoff"
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.FALLBACK_VALUE,
                description="Use cached or default response"
            )
        ]
        self.register_recovery_strategy("llm_api_error", llm_strategies)
        
        # Validation errors
        validation_strategies = [
            RecoveryAction(
                strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
                description="Degrade field quality gracefully"
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.USE_DEFAULT,
                description="Use field default value"
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.SKIP_FIELD,
                description="Skip field if not critical"
            )
        ]
        self.register_recovery_strategy("validation_error", validation_strategies)
        
        # Configuration errors
        config_strategies = [
            RecoveryAction(
                strategy=RecoveryStrategy.USE_DEFAULT,
                description="Use default configuration values"
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.MANUAL_INTERVENTION,
                description="Require manual configuration fix"
            )
        ]
        self.register_recovery_strategy("configuration_error", config_strategies)
        
        # Default fallback strategies
        default_strategies = [
            RecoveryAction(
                strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
                description="Default graceful degradation"
            ),
            RecoveryAction(
                strategy=RecoveryStrategy.MANUAL_INTERVENTION,
                description="Default manual intervention"
            )
        ]
        self.register_recovery_strategy("default", default_strategies)
    
    def _load_config(self, config_file: str):
        """Load recovery configuration from file."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Load fallback values
            if 'fallback_values' in config:
                self.fallback_values.update(config['fallback_values'])
            
            # Load recovery strategies (simplified loading)
            if 'recovery_strategies' in config:
                for error_type, strategies_config in config['recovery_strategies'].items():
                    strategies = []
                    for strategy_config in strategies_config:
                        strategy = RecoveryAction(
                            strategy=RecoveryStrategy(strategy_config['strategy']),
                            max_retries=strategy_config.get('max_retries', 3),
                            retry_delay=strategy_config.get('retry_delay', 1.0),
                            fallback_value=strategy_config.get('fallback_value'),
                            description=strategy_config.get('description', '')
                        )
                        strategies.append(strategy)
                    
                    self.register_recovery_strategy(error_type, strategies)
            
            logger.info(f"Loaded error recovery configuration from {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to load recovery configuration: {e}")
            self._initialize_default_strategies()
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery statistics."""
        with self._lock:
            return {
                'total_errors': len(self.error_history),
                'error_types': list(self.recovery_stats.keys()),
                'recovery_stats': dict(self.recovery_stats),
                'recent_errors': [
                    {
                        'timestamp': error.timestamp.isoformat(),
                        'operation': error.operation,
                        'error_type': error.error_type,
                        'field_name': error.field_name
                    }
                    for error in self.error_history[-10:]  # Last 10 errors
                ]
            }
    
    def clear_error_history(self, older_than_days: int = 30):
        """Clear old error history."""
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        with self._lock:
            original_count = len(self.error_history)
            self.error_history = [
                error for error in self.error_history 
                if error.timestamp > cutoff_date
            ]
            
            cleared_count = original_count - len(self.error_history)
            if cleared_count > 0:
                logger.info(f"Cleared {cleared_count} old error records")


# Global error recovery manager
_error_recovery_manager = None
_lock = threading.Lock()


def get_error_recovery_manager() -> ErrorRecoveryManager:
    """Get the global error recovery manager instance."""
    global _error_recovery_manager
    with _lock:
        if _error_recovery_manager is None:
            _error_recovery_manager = ErrorRecoveryManager()
        return _error_recovery_manager


def with_error_recovery(error_type: str = None, operation: str = None):
    """Decorator to add error recovery to functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_context = ErrorContext(
                    operation=operation or func.__name__,
                    error_type=error_type or type(e).__name__,
                    error_message=str(e),
                    stack_trace=traceback.format_exc()
                )
                
                recovery_manager = get_error_recovery_manager()
                recovery_result = recovery_manager.recover_from_error(
                    error_context, func, *args, **kwargs
                )
                
                if recovery_result.success:
                    return recovery_result.recovered_value
                else:
                    # Re-raise original exception if recovery failed
                    raise
        
        return wrapper
    return decorator


# Convenience functions for common recovery scenarios
def recover_json_parsing(json_string: str, default_value: Any = None) -> Any:
    """Recover from JSON parsing errors."""
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        error_context = ErrorContext(
            operation="json_parsing",
            error_type="JSONDecodeError",
            error_message=str(e)
        )
        
        recovery_manager = get_error_recovery_manager()
        recovery_result = recovery_manager.recover_from_error(error_context)
        
        if recovery_result.success:
            return recovery_result.recovered_value
        else:
            return default_value or {}


def recover_field_value(field_name: str, error_message: str, 
                       book_id: str = None) -> Any:
    """Recover a field value when processing fails."""
    error_context = ErrorContext(
        operation="field_processing",
        error_type="field_processing_error",
        error_message=error_message,
        field_name=field_name,
        book_id=book_id
    )
    
    recovery_manager = get_error_recovery_manager()
    recovery_result = recovery_manager.recover_from_error(error_context)
    
    if recovery_result.success:
        return recovery_result.recovered_value
    else:
        return None