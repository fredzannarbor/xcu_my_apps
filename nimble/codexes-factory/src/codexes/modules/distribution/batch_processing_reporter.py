
"""
Enhanced Batch Processing Reporter

This module provides comprehensive reporting for batch processing operations.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class BookProcessingResult:
    """Result of processing a single book."""
    book_id: str
    title: str
    status: str  # "success", "failed", "skipped"
    processing_time: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    fields_populated: int = 0
    total_fields: int = 0
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class BatchProcessingReport:
    """Comprehensive batch processing report."""
    batch_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_books: int = 0
    successful_books: int = 0
    failed_books: int = 0
    skipped_books: int = 0
    book_results: List[BookProcessingResult] = field(default_factory=list)
    overall_errors: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


class BatchProcessingReporter:
    """Enhanced batch processing reporter with detailed error tracking."""
    
    def __init__(self, report_dir: str = "logs/batch_reports"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.current_report: Optional[BatchProcessingReport] = None
    
    def start_batch_report(self, batch_id: str, total_books: int) -> BatchProcessingReport:
        """Start a new batch processing report."""
        self.current_report = BatchProcessingReport(
            batch_id=batch_id,
            start_time=datetime.now(),
            total_books=total_books
        )
        
        logger.info(f"Started batch processing report: {batch_id} ({total_books} books)")
        return self.current_report
    
    def add_book_result(self, result: BookProcessingResult):
        """Add a book processing result to the current report."""
        if not self.current_report:
            logger.error("No active batch report to add book result to")
            return
        
        self.current_report.book_results.append(result)
        
        # Update counters
        if result.status == "success":
            self.current_report.successful_books += 1
        elif result.status == "failed":
            self.current_report.failed_books += 1
        elif result.status == "skipped":
            self.current_report.skipped_books += 1
        
        logger.info(f"Added book result: {result.title} - {result.status}")
    
    def add_overall_error(self, error: str):
        """Add an overall batch processing error."""
        if not self.current_report:
            logger.error("No active batch report to add error to")
            return
        
        self.current_report.overall_errors.append(error)
        logger.error(f"Added batch error: {error}")
    
    def complete_batch_report(self) -> Optional[BatchProcessingReport]:
        """Complete the current batch report and save it."""
        if not self.current_report:
            logger.error("No active batch report to complete")
            return None
        
        self.current_report.end_time = datetime.now()
        
        # Calculate performance metrics
        total_time = (self.current_report.end_time - self.current_report.start_time).total_seconds()
        self.current_report.performance_metrics = {
            "total_processing_time": total_time,
            "average_time_per_book": total_time / max(1, self.current_report.total_books),
            "success_rate": self.current_report.successful_books / max(1, self.current_report.total_books),
            "error_rate": self.current_report.failed_books / max(1, self.current_report.total_books)
        }
        
        # Save report to file
        report_file = self.report_dir / f"batch_report_{self.current_report.batch_id}.json"
        self._save_report_to_file(self.current_report, report_file)
        
        # Generate summary
        self._log_batch_summary(self.current_report)
        
        completed_report = self.current_report
        self.current_report = None
        
        return completed_report
    
    def create_book_result(self, book_id: str, title: str, status: str, 
                          processing_time: float) -> BookProcessingResult:
        """Create a new book processing result."""
        return BookProcessingResult(
            book_id=book_id,
            title=title,
            status=status,
            processing_time=processing_time
        )
    
    def _save_report_to_file(self, report: BatchProcessingReport, file_path: Path):
        """Save batch report to JSON file."""
        try:
            report_data = {
                "batch_id": report.batch_id,
                "start_time": report.start_time.isoformat(),
                "end_time": report.end_time.isoformat() if report.end_time else None,
                "summary": {
                    "total_books": report.total_books,
                    "successful_books": report.successful_books,
                    "failed_books": report.failed_books,
                    "skipped_books": report.skipped_books
                },
                "performance_metrics": report.performance_metrics,
                "overall_errors": report.overall_errors,
                "book_results": [
                    {
                        "book_id": result.book_id,
                        "title": result.title,
                        "status": result.status,
                        "processing_time": result.processing_time,
                        "errors": result.errors,
                        "warnings": result.warnings,
                        "fields_populated": result.fields_populated,
                        "total_fields": result.total_fields,
                        "validation_errors": result.validation_errors
                    }
                    for result in report.book_results
                ]
            }
            
            with open(file_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.info(f"Saved batch report to: {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving batch report: {e}")
    
    def _log_batch_summary(self, report: BatchProcessingReport):
        """Log a summary of the batch processing results."""
        logger.info("=" * 60)
        logger.info(f"BATCH PROCESSING SUMMARY - {report.batch_id}")
        logger.info("=" * 60)
        logger.info(f"Total Books: {report.total_books}")
        logger.info(f"Successful: {report.successful_books} ({report.performance_metrics['success_rate']:.1%})")
        logger.info(f"Failed: {report.failed_books} ({report.performance_metrics['error_rate']:.1%})")
        logger.info(f"Skipped: {report.skipped_books}")
        logger.info(f"Total Time: {report.performance_metrics['total_processing_time']:.2f}s")
        logger.info(f"Avg Time/Book: {report.performance_metrics['average_time_per_book']:.2f}s")
        
        if report.overall_errors:
            logger.info(f"Overall Errors: {len(report.overall_errors)}")
            for error in report.overall_errors[:5]:  # Show first 5 errors
                logger.info(f"  - {error}")
            if len(report.overall_errors) > 5:
                logger.info(f"  ... and {len(report.overall_errors) - 5} more errors")
        
        logger.info("=" * 60)
