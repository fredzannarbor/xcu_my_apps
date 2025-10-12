"""
Accurate reporting system for tracking prompt success and quote retrieval statistics.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class ProcessingStatistics:
    """Comprehensive processing statistics"""
    total_prompts: int = 0
    successful_prompts: int = 0
    failed_prompts: int = 0
    total_quotes_requested: int = 0
    total_quotes_retrieved: int = 0
    processing_time: float = 0.0
    error_details: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class PromptExecution:
    """Individual prompt execution record"""
    prompt_name: str
    success: bool
    execution_time: float
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class QuoteRetrievalRecord:
    """Quote retrieval tracking record"""
    book_id: str
    quotes_requested: int
    quotes_retrieved: int
    success_rate: float
    timestamp: datetime
    source: str = "unknown"
    retrieval_time: float = 0.0


class AccurateReportingSystem:
    """Accurate tracking and reporting of prompt success and quote retrieval"""
    
    def __init__(self):
        self.prompt_stats: Dict[str, List[PromptExecution]] = {}
        self.quote_stats: Dict[str, List[QuoteRetrievalRecord]] = {}
        self.processing_stats = ProcessingStatistics()
        self.session_start = datetime.now()
    
    def track_prompt_execution(self, prompt_name: str, success: bool, details: Dict[str, Any]) -> None:
        """Track individual prompt execution results"""
        try:
            execution_time = details.get('execution_time', 0.0)
            error_message = details.get('error_message') if not success else None
            
            execution = PromptExecution(
                prompt_name=prompt_name,
                success=success,
                execution_time=execution_time,
                timestamp=datetime.now(),
                details=details,
                error_message=error_message
            )
            
            if prompt_name not in self.prompt_stats:
                self.prompt_stats[prompt_name] = []
            
            self.prompt_stats[prompt_name].append(execution)
            
            # Update overall statistics
            self.processing_stats.total_prompts += 1
            if success:
                self.processing_stats.successful_prompts += 1
            else:
                self.processing_stats.failed_prompts += 1
                if error_message:
                    self.processing_stats.error_details.append(f"{prompt_name}: {error_message}")
            
            self.processing_stats.processing_time += execution_time
            
            logger.info(f"Tracked prompt execution: {prompt_name} - {'SUCCESS' if success else 'FAILED'}")
            
        except Exception as e:
            logger.error(f"Error tracking prompt execution: {e}")
    
    def track_quote_retrieval(self, book_id: str, quotes_retrieved: int, quotes_requested: int, source: str = "unknown", retrieval_time: float = 0.0) -> None:
        """Track quote retrieval statistics accurately"""
        try:
            success_rate = (quotes_retrieved / quotes_requested) if quotes_requested > 0 else 0.0
            
            record = QuoteRetrievalRecord(
                book_id=book_id,
                quotes_requested=quotes_requested,
                quotes_retrieved=quotes_retrieved,
                success_rate=success_rate,
                timestamp=datetime.now(),
                source=source,
                retrieval_time=retrieval_time
            )
            
            if book_id not in self.quote_stats:
                self.quote_stats[book_id] = []
            
            self.quote_stats[book_id].append(record)
            
            # Update overall statistics
            self.processing_stats.total_quotes_requested += quotes_requested
            self.processing_stats.total_quotes_retrieved += quotes_retrieved
            
            logger.info(f"Tracked quote retrieval: {book_id} - {quotes_retrieved}/{quotes_requested} quotes")
            
        except Exception as e:
            logger.error(f"Error tracking quote retrieval: {e}")
    
    def generate_accurate_report(self) -> Dict[str, Any]:
        """Generate report with accurate statistics matching actual results"""
        try:
            current_time = datetime.now()
            session_duration = (current_time - self.session_start).total_seconds()
            
            # Calculate prompt success rates by type
            prompt_summary = {}
            for prompt_name, executions in self.prompt_stats.items():
                total = len(executions)
                successful = sum(1 for e in executions if e.success)
                failed = total - successful
                avg_time = sum(e.execution_time for e in executions) / total if total > 0 else 0
                
                prompt_summary[prompt_name] = {
                    'total_executions': total,
                    'successful': successful,
                    'failed': failed,
                    'success_rate': (successful / total) if total > 0 else 0,
                    'average_execution_time': avg_time,
                    'recent_errors': [e.error_message for e in executions[-5:] if e.error_message]
                }
            
            # Calculate quote retrieval summary
            quote_summary = {}
            total_books_processed = len(self.quote_stats)
            overall_quotes_requested = 0
            overall_quotes_retrieved = 0
            
            for book_id, records in self.quote_stats.items():
                latest_record = records[-1] if records else None
                if latest_record:
                    quote_summary[book_id] = {
                        'quotes_requested': latest_record.quotes_requested,
                        'quotes_retrieved': latest_record.quotes_retrieved,
                        'success_rate': latest_record.success_rate,
                        'source': latest_record.source,
                        'timestamp': latest_record.timestamp.isoformat()
                    }
                    overall_quotes_requested += latest_record.quotes_requested
                    overall_quotes_retrieved += latest_record.quotes_retrieved
            
            # Overall success rates
            overall_prompt_success_rate = (
                self.processing_stats.successful_prompts / self.processing_stats.total_prompts
                if self.processing_stats.total_prompts > 0 else 0
            )
            
            overall_quote_success_rate = (
                overall_quotes_retrieved / overall_quotes_requested
                if overall_quotes_requested > 0 else 0
            )
            
            report = {
                'report_timestamp': current_time.isoformat(),
                'session_duration_seconds': session_duration,
                'overall_statistics': {
                    'total_prompts_executed': self.processing_stats.total_prompts,
                    'successful_prompts': self.processing_stats.successful_prompts,
                    'failed_prompts': self.processing_stats.failed_prompts,
                    'prompt_success_rate': overall_prompt_success_rate,
                    'total_quotes_requested': overall_quotes_requested,
                    'total_quotes_retrieved': overall_quotes_retrieved,
                    'quote_retrieval_rate': overall_quote_success_rate,
                    'books_processed': total_books_processed,
                    'total_processing_time': self.processing_stats.processing_time
                },
                'prompt_details': prompt_summary,
                'quote_details': quote_summary,
                'error_summary': {
                    'total_errors': len(self.processing_stats.error_details),
                    'recent_errors': self.processing_stats.error_details[-10:]  # Last 10 errors
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating accurate report: {e}")
            return {'error': f'Report generation failed: {e}'}
    
    def validate_reporting_accuracy(self, expected_results: Dict[str, Any]) -> bool:
        """Validate that reported statistics match actual execution results"""
        try:
            report = self.generate_accurate_report()
            overall_stats = report.get('overall_statistics', {})
            
            # Validate key metrics
            validations = []
            
            if 'expected_quotes_retrieved' in expected_results:
                actual = overall_stats.get('total_quotes_retrieved', 0)
                expected = expected_results['expected_quotes_retrieved']
                validations.append(actual == expected)
                if actual != expected:
                    logger.warning(f"Quote count mismatch: expected {expected}, got {actual}")
            
            if 'expected_prompt_success_rate' in expected_results:
                actual = overall_stats.get('prompt_success_rate', 0)
                expected = expected_results['expected_prompt_success_rate']
                # Allow small floating point differences
                validations.append(abs(actual - expected) < 0.01)
                if abs(actual - expected) >= 0.01:
                    logger.warning(f"Success rate mismatch: expected {expected}, got {actual}")
            
            if 'expected_books_processed' in expected_results:
                actual = overall_stats.get('books_processed', 0)
                expected = expected_results['expected_books_processed']
                validations.append(actual == expected)
                if actual != expected:
                    logger.warning(f"Books processed mismatch: expected {expected}, got {actual}")
            
            return all(validations) if validations else True
            
        except Exception as e:
            logger.error(f"Error validating reporting accuracy: {e}")
            return False
    
    def get_prompt_statistics(self, prompt_name: str) -> Dict[str, Any]:
        """Get detailed statistics for a specific prompt"""
        try:
            if prompt_name not in self.prompt_stats:
                return {'error': f'No statistics found for prompt: {prompt_name}'}
            
            executions = self.prompt_stats[prompt_name]
            total = len(executions)
            successful = sum(1 for e in executions if e.success)
            failed = total - successful
            
            return {
                'prompt_name': prompt_name,
                'total_executions': total,
                'successful': successful,
                'failed': failed,
                'success_rate': (successful / total) if total > 0 else 0,
                'average_execution_time': sum(e.execution_time for e in executions) / total if total > 0 else 0,
                'recent_executions': [
                    {
                        'success': e.success,
                        'timestamp': e.timestamp.isoformat(),
                        'execution_time': e.execution_time,
                        'error': e.error_message
                    }
                    for e in executions[-5:]  # Last 5 executions
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting prompt statistics: {e}")
            return {'error': f'Failed to get statistics: {e}'}
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get statistics for the current session"""
        try:
            report = self.generate_accurate_report()
            return report.get('overall_statistics', {})
        except Exception as e:
            logger.error(f"Error getting session statistics: {e}")
            return {}
    
    def reset_statistics(self):
        """Reset all statistics for a new session"""
        try:
            self.prompt_stats.clear()
            self.quote_stats.clear()
            self.processing_stats = ProcessingStatistics()
            self.session_start = datetime.now()
            logger.info("Statistics reset for new session")
        except Exception as e:
            logger.error(f"Error resetting statistics: {e}")
    
    def export_statistics(self, filepath: str) -> bool:
        """Export statistics to JSON file"""
        try:
            report = self.generate_accurate_report()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Statistics exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting statistics: {e}")
            return False