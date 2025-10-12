"""
Progress tracking system for batch operations.
Provides detailed progress monitoring and reporting.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProgressReport:
    """Report of progress for a batch operation."""
    operation_id: str
    operation_name: str
    total_items: int
    completed_items: int
    failed_items: int
    progress_percentage: float
    elapsed_time: float
    estimated_remaining_time: Optional[float]
    current_status: str
    error_messages: List[str] = field(default_factory=list)
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    last_update: str = field(default_factory=lambda: datetime.now().isoformat())


class ProgressTracker:
    """Tracks progress of batch operations."""
    
    def __init__(self):
        """Initialize the progress tracker."""
        self.tracked_operations: Dict[str, Dict[str, Any]] = {}
        logger.info("ProgressTracker initialized")
    
    def start_tracking(self, operation_id: str, operation_name: str, 
                      total_items: int) -> None:
        """Start tracking a new operation."""
        self.tracked_operations[operation_id] = {
            "operation_name": operation_name,
            "total_items": total_items,
            "completed_items": 0,
            "failed_items": 0,
            "start_time": time.time(),
            "last_update": time.time(),
            "status": "running",
            "error_messages": []
        }
        logger.info(f"Started tracking operation: {operation_name} ({operation_id})")
    
    def update_progress(self, operation_id: str, completed_items: int, 
                       failed_items: int = 0, status: str = "running",
                       error_message: Optional[str] = None) -> None:
        """Update progress for an operation."""
        if operation_id not in self.tracked_operations:
            logger.warning(f"Operation {operation_id} not found for progress update")
            return
        
        operation = self.tracked_operations[operation_id]
        operation["completed_items"] = completed_items
        operation["failed_items"] = failed_items
        operation["status"] = status
        operation["last_update"] = time.time()
        
        if error_message:
            operation["error_messages"].append(error_message)
        
        logger.debug(f"Updated progress for {operation_id}: {completed_items}/{operation['total_items']}")
    
    def complete_operation(self, operation_id: str, final_status: str = "completed") -> None:
        """Mark an operation as completed."""
        if operation_id in self.tracked_operations:
            self.tracked_operations[operation_id]["status"] = final_status
            self.tracked_operations[operation_id]["last_update"] = time.time()
            logger.info(f"Operation {operation_id} marked as {final_status}")
    
    def get_progress_report(self, operation_id: str) -> Optional[ProgressReport]:
        """Get a progress report for an operation."""
        if operation_id not in self.tracked_operations:
            return None
        
        operation = self.tracked_operations[operation_id]
        current_time = time.time()
        elapsed_time = current_time - operation["start_time"]
        
        # Calculate progress percentage
        total_processed = operation["completed_items"] + operation["failed_items"]
        progress_percentage = (total_processed / operation["total_items"]) * 100 if operation["total_items"] > 0 else 0
        
        # Estimate remaining time
        estimated_remaining_time = None
        if progress_percentage > 0 and operation["status"] == "running":
            estimated_total_time = elapsed_time / (progress_percentage / 100)
            estimated_remaining_time = estimated_total_time - elapsed_time
        
        return ProgressReport(
            operation_id=operation_id,
            operation_name=operation["operation_name"],
            total_items=operation["total_items"],
            completed_items=operation["completed_items"],
            failed_items=operation["failed_items"],
            progress_percentage=progress_percentage,
            elapsed_time=elapsed_time,
            estimated_remaining_time=estimated_remaining_time,
            current_status=operation["status"],
            error_messages=operation["error_messages"].copy(),
            start_time=datetime.fromtimestamp(operation["start_time"]).isoformat(),
            last_update=datetime.fromtimestamp(operation["last_update"]).isoformat()
        )
    
    def get_all_operations(self) -> List[ProgressReport]:
        """Get progress reports for all tracked operations."""
        reports = []
        for operation_id in self.tracked_operations:
            report = self.get_progress_report(operation_id)
            if report:
                reports.append(report)
        return reports
    
    def cleanup_completed_operations(self, max_age_hours: int = 24) -> int:
        """Clean up old completed operations."""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        operations_to_remove = []
        for operation_id, operation in self.tracked_operations.items():
            if (operation["status"] in ["completed", "failed", "cancelled"] and
                current_time - operation["last_update"] > max_age_seconds):
                operations_to_remove.append(operation_id)
        
        for operation_id in operations_to_remove:
            del self.tracked_operations[operation_id]
        
        logger.info(f"Cleaned up {len(operations_to_remove)} old operations")
        return len(operations_to_remove)
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics for all operations."""
        if not self.tracked_operations:
            return {
                "total_operations": 0,
                "running_operations": 0,
                "completed_operations": 0,
                "failed_operations": 0
            }
        
        stats = {
            "total_operations": len(self.tracked_operations),
            "running_operations": 0,
            "completed_operations": 0,
            "failed_operations": 0,
            "cancelled_operations": 0
        }
        
        for operation in self.tracked_operations.values():
            status = operation["status"]
            if status == "running":
                stats["running_operations"] += 1
            elif status == "completed":
                stats["completed_operations"] += 1
            elif status == "failed":
                stats["failed_operations"] += 1
            elif status == "cancelled":
                stats["cancelled_operations"] += 1
        
        return stats