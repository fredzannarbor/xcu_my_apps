"""
Comprehensive error handling system for final fix components.
"""

import logging
import traceback
from typing import Dict, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class FixComponentType(Enum):
    """Types of fix components"""
    BARCODE_GENERATOR = "barcode_generator"
    DOTGRID_LAYOUT = "dotgrid_layout"
    ISBN_FORMATTER = "isbn_formatter"
    SUBTITLE_VALIDATOR = "subtitle_validator"
    SPINE_WIDTH_CALCULATOR = "spine_width_calculator"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FixError:
    """Represents an error in a fix component"""
    component: FixComponentType
    severity: ErrorSeverity
    message: str
    exception: Optional[Exception] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class FixErrorHandler:
    """Comprehensive error handler for all fix components"""
    
    def __init__(self, log_dir: str = "logs/fixes"):
        """Initialize error handler with logging directory"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Error counters
        self.error_counts = {component: 0 for component in FixComponentType}
        self.total_errors = 0
        
        # Fallback strategies
        self.fallback_strategies = {
            FixComponentType.BARCODE_GENERATOR: self._barcode_fallback,
            FixComponentType.DOTGRID_LAYOUT: self._dotgrid_fallback,
            FixComponentType.ISBN_FORMATTER: self._isbn_fallback,
            FixComponentType.SUBTITLE_VALIDATOR: self._subtitle_fallback,
            FixComponentType.SPINE_WIDTH_CALCULATOR: self._spine_width_fallback,
        }
    
    def handle_error(self, 
                    component: FixComponentType, 
                    error: Exception, 
                    context: Dict[str, Any] = None,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> Any:
        """Handle error with appropriate fallback strategy"""
        try:
            # Create error record
            fix_error = FixError(
                component=component,
                severity=severity,
                message=str(error),
                exception=error,
                context=context or {}
            )
            
            # Log error
            self._log_error(fix_error)
            
            # Update counters
            self.error_counts[component] += 1
            self.total_errors += 1
            
            # Apply fallback strategy
            fallback_result = self._apply_fallback(fix_error)
            
            logger.info(f"Applied fallback strategy for {component.value}: {type(fallback_result)}")
            return fallback_result
            
        except Exception as handler_error:
            logger.critical(f"Error handler itself failed: {handler_error}")
            return self._emergency_fallback(component, context)
    
    def _log_error(self, fix_error: FixError) -> None:
        """Log error to file and console"""
        try:
            # Console logging
            log_level = self._get_log_level(fix_error.severity)
            logger.log(log_level, f"{fix_error.component.value}: {fix_error.message}")
            
            if fix_error.exception:
                logger.debug(f"Exception details: {traceback.format_exc()}")
            
            # File logging
            log_file = self.log_dir / f"{fix_error.component.value}_errors.log"
            
            error_record = {
                'timestamp': fix_error.timestamp.isoformat(),
                'component': fix_error.component.value,
                'severity': fix_error.severity.value,
                'message': fix_error.message,
                'context': fix_error.context,
                'traceback': traceback.format_exc() if fix_error.exception else None
            }
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_record) + '\n')
                
        except Exception as log_error:
            logger.critical(f"Failed to log error: {log_error}")
    
    def _get_log_level(self, severity: ErrorSeverity) -> int:
        """Get logging level for severity"""
        severity_map = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        return severity_map.get(severity, logging.WARNING)
    
    def _apply_fallback(self, fix_error: FixError) -> Any:
        """Apply appropriate fallback strategy"""
        try:
            fallback_func = self.fallback_strategies.get(fix_error.component)
            if fallback_func:
                return fallback_func(fix_error)
            else:
                logger.error(f"No fallback strategy for {fix_error.component.value}")
                return None
                
        except Exception as fallback_error:
            logger.error(f"Fallback strategy failed for {fix_error.component.value}: {fallback_error}")
            return self._emergency_fallback(fix_error.component, fix_error.context)
    
    def _barcode_fallback(self, fix_error: FixError) -> Dict[str, Any]:
        """Fallback strategy for barcode generation errors"""
        try:
            context = fix_error.context or {}
            isbn = context.get('isbn', 'Unknown')
            
            # Create placeholder barcode result
            from src.codexes.modules.distribution.isbn_barcode_generator import (
                BarcodeResult, Position, SafetySpaces
            )
            
            fallback_result = BarcodeResult(
                barcode_data=b"PLACEHOLDER_BARCODE",
                position=Position(x=10.0, y=0.5),
                safety_spaces=SafetySpaces(top=0.125, bottom=0.125, left=0.125, right=0.125),
                format_type="UPC-A"
            )
            
            logger.info(f"Generated placeholder barcode for ISBN: {isbn}")
            return fallback_result
            
        except Exception as e:
            logger.error(f"Barcode fallback failed: {e}")
            return None
    
    def _dotgrid_fallback(self, fix_error: FixError) -> Dict[str, Any]:
        """Fallback strategy for dotgrid layout errors"""
        try:
            context = fix_error.context or {}
            
            # Use safe default positioning
            from src.codexes.modules.prepress.dotgrid_layout_manager import Position
            
            fallback_position = Position(x=2.75, y=2.0)  # Safe center position
            
            logger.info("Applied safe default dotgrid positioning")
            return {
                'position': fallback_position,
                'spacing_valid': True,
                'fallback_applied': True
            }
            
        except Exception as e:
            logger.error(f"Dotgrid fallback failed: {e}")
            return {'position': None, 'spacing_valid': False, 'fallback_applied': True}
    
    def _isbn_fallback(self, fix_error: FixError) -> str:
        """Fallback strategy for ISBN formatting errors"""
        try:
            context = fix_error.context or {}
            original_isbn = context.get('isbn', 'Unknown')
            
            # Basic ISBN formatting fallback
            if original_isbn and original_isbn != 'Unknown':
                # Simple hyphenation for display
                clean_isbn = original_isbn.replace('-', '').replace(' ', '')
                if len(clean_isbn) == 13:
                    formatted = f"ISBN {clean_isbn[:3]}-{clean_isbn[3]}-{clean_isbn[4:10]}-{clean_isbn[10:12]}-{clean_isbn[12]}"
                    logger.info(f"Applied basic ISBN formatting: {formatted}")
                    return formatted
            
            logger.info(f"Using original ISBN as fallback: {original_isbn}")
            return f"ISBN {original_isbn}"
            
        except Exception as e:
            logger.error(f"ISBN fallback failed: {e}")
            return "ISBN Unknown"
    
    def _subtitle_fallback(self, fix_error: FixError) -> str:
        """Fallback strategy for subtitle validation errors"""
        try:
            context = fix_error.context or {}
            original_subtitle = context.get('subtitle', '')
            char_limit = context.get('char_limit', 38)
            
            if not original_subtitle:
                return ''
            
            # Simple truncation fallback
            if len(original_subtitle) > char_limit:
                # Truncate at word boundary if possible
                truncated = original_subtitle[:char_limit]
                last_space = truncated.rfind(' ')
                
                if last_space > char_limit * 0.7:
                    result = truncated[:last_space].rstrip('.,;:')
                else:
                    result = truncated[:char_limit-3] + "..." if char_limit > 3 else truncated[:char_limit]
                
                logger.info(f"Applied subtitle truncation fallback: '{result}'")
                return result
            
            return original_subtitle
            
        except Exception as e:
            logger.error(f"Subtitle fallback failed: {e}")
            return context.get('subtitle', '') if context else ''
    
    def _spine_width_fallback(self, fix_error: FixError) -> float:
        """Fallback strategy for spine width calculation errors"""
        try:
            context = fix_error.context or {}
            page_count = context.get('page_count', 200)
            
            # Simple spine width estimation based on page count
            # Rough estimate: 0.002 inches per page
            estimated_width = max(0.125, min(2.0, page_count * 0.002))
            
            logger.info(f"Applied spine width estimation fallback: {estimated_width} for {page_count} pages")
            return estimated_width
            
        except Exception as e:
            logger.error(f"Spine width fallback failed: {e}")
            return 0.25  # Safe default
    
    def _emergency_fallback(self, component: FixComponentType, context: Dict[str, Any] = None) -> Any:
        """Emergency fallback when all else fails"""
        logger.critical(f"Emergency fallback activated for {component.value}")
        
        emergency_defaults = {
            FixComponentType.BARCODE_GENERATOR: None,
            FixComponentType.DOTGRID_LAYOUT: {'position': None, 'fallback_applied': True},
            FixComponentType.ISBN_FORMATTER: "ISBN Unknown",
            FixComponentType.SUBTITLE_VALIDATOR: "",
            FixComponentType.SPINE_WIDTH_CALCULATOR: 0.25,
        }
        
        return emergency_defaults.get(component)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors encountered"""
        return {
            'total_errors': self.total_errors,
            'errors_by_component': dict(self.error_counts),
            'most_problematic_component': max(self.error_counts, key=self.error_counts.get).value if self.total_errors > 0 else None
        }
    
    def reset_counters(self) -> None:
        """Reset error counters"""
        self.error_counts = {component: 0 for component in FixComponentType}
        self.total_errors = 0
        logger.info("Error counters reset")
    
    def create_error_report(self) -> str:
        """Create comprehensive error report"""
        try:
            report_path = self.log_dir / f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'summary': self.get_error_summary(),
                'log_directory': str(self.log_dir),
                'available_logs': [f.name for f in self.log_dir.glob('*.log')]
            }
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Error report created: {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"Failed to create error report: {e}")
            return ""


# Global error handler instance
_global_error_handler = None


def get_error_handler() -> FixErrorHandler:
    """Get global error handler instance"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = FixErrorHandler()
    return _global_error_handler


def handle_fix_error(component: FixComponentType, 
                    error: Exception, 
                    context: Dict[str, Any] = None,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> Any:
    """Convenience function to handle fix errors"""
    return get_error_handler().handle_error(component, error, context, severity)