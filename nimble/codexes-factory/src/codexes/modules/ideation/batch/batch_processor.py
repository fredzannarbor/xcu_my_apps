"""
Batch processing system for ideation operations.
Handles large-scale processing of concepts with progress tracking.
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.codex_object import CodexObject

logger = logging.getLogger(__name__)


@dataclass
class BatchConfiguration:
    """Configuration for batch processing."""
    batch_size: int = 10
    max_workers: int = 4
    retry_attempts: int = 3
    retry_delay: float = 1.0
    timeout_seconds: int = 300
    progress_callback: Optional[Callable] = None


@dataclass
class BatchResult:
    """Result of batch processing operation."""
    batch_id: str
    total_items: int
    processed_items: int
    successful_items: int
    failed_items: int
    processing_time: float
    success_rate: float
    errors: List[str] = field(default_factory=list)
    processed_objects: List[Any] = field(default_factory=list)


class BatchProcessor:
    """Processes large batches of concepts with progress tracking."""
    
    def __init__(self):
        """Initialize the batch processor."""
        self.active_batches: Dict[str, Dict[str, Any]] = {}
        self.completed_batches: List[BatchResult] = []
        logger.info("BatchProcessor initialized")
    
    def process_batch(self, items: List[Any], processing_function: Callable,
                     config: Optional[BatchConfiguration] = None,
                     batch_name: str = "Unnamed Batch") -> BatchResult:
        """
        Process a batch of items with the given function.
        
        Args:
            items: List of items to process
            processing_function: Function to apply to each item
            config: Batch processing configuration
            batch_name: Name for the batch operation
            
        Returns:
            BatchResult with processing statistics
        """
        if config is None:
            config = BatchConfiguration()
        
        batch_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Initialize batch tracking
            self.active_batches[batch_id] = {
                "name": batch_name,
                "total_items": len(items),
                "processed_items": 0,
                "start_time": start_time,
                "status": "processing"
            }
            
            processed_objects = []
            errors = []
            successful_count = 0
            
            # Process items in batches
            for i in range(0, len(items), config.batch_size):
                batch_items = items[i:i + config.batch_size]
                
                # Process batch with threading
                batch_results = self._process_batch_chunk(
                    batch_items, processing_function, config
                )
                
                # Collect results
                for result in batch_results:
                    if result["success"]:
                        processed_objects.append(result["object"])
                        successful_count += 1
                    else:
                        errors.append(result["error"])
                
                # Update progress
                self.active_batches[batch_id]["processed_items"] = len(processed_objects) + len(errors)
                
                # Call progress callback if provided
                if config.progress_callback:
                    progress = (len(processed_objects) + len(errors)) / len(items)
                    config.progress_callback(batch_id, progress)
            
            # Calculate final results
            processing_time = time.time() - start_time
            success_rate = successful_count / len(items) if items else 0
            
            result = BatchResult(
                batch_id=batch_id,
                total_items=len(items),
                processed_items=len(processed_objects) + len(errors),
                successful_items=successful_count,
                failed_items=len(errors),
                processing_time=processing_time,
                success_rate=success_rate,
                errors=errors,
                processed_objects=processed_objects
            )
            
            # Clean up and store result
            del self.active_batches[batch_id]
            self.completed_batches.append(result)
            
            logger.info(f"Batch processing completed: {batch_name} ({successful_count}/{len(items)} successful)")
            return result
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            # Clean up on error
            if batch_id in self.active_batches:
                del self.active_batches[batch_id]
            
            # Return error result
            return BatchResult(
                batch_id=batch_id,
                total_items=len(items),
                processed_items=0,
                successful_items=0,
                failed_items=len(items),
                processing_time=time.time() - start_time,
                success_rate=0.0,
                errors=[str(e)]
            )
    
    def _process_batch_chunk(self, items: List[Any], processing_function: Callable,
                           config: BatchConfiguration) -> List[Dict[str, Any]]:
        """Process a chunk of items with threading."""
        results = []
        
        with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(self._process_single_item, item, processing_function, config): item
                for item in items
            }
            
            # Collect results
            for future in as_completed(future_to_item, timeout=config.timeout_seconds):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    item = future_to_item[future]
                    results.append({
                        "success": False,
                        "object": item,
                        "error": str(e)
                    })
        
        return results
    
    def _process_single_item(self, item: Any, processing_function: Callable,
                           config: BatchConfiguration) -> Dict[str, Any]:
        """Process a single item with retry logic."""
        last_error = None
        
        for attempt in range(config.retry_attempts):
            try:
                processed_item = processing_function(item)
                return {
                    "success": True,
                    "object": processed_item,
                    "error": None
                }
            except Exception as e:
                last_error = e
                if attempt < config.retry_attempts - 1:
                    time.sleep(config.retry_delay * (attempt + 1))
        
        return {
            "success": False,
            "object": item,
            "error": str(last_error)
        }
    
    def get_batch_progress(self, batch_id: str) -> Dict[str, Any]:
        """Get progress information for an active batch."""
        if batch_id not in self.active_batches:
            return {"error": "Batch not found"}
        
        batch_info = self.active_batches[batch_id]
        elapsed_time = time.time() - batch_info["start_time"]
        
        progress = batch_info["processed_items"] / batch_info["total_items"] if batch_info["total_items"] > 0 else 0
        
        # Estimate completion time
        if progress > 0:
            estimated_total_time = elapsed_time / progress
            estimated_remaining_time = estimated_total_time - elapsed_time
        else:
            estimated_remaining_time = None
        
        return {
            "batch_id": batch_id,
            "name": batch_info["name"],
            "progress": progress,
            "processed_items": batch_info["processed_items"],
            "total_items": batch_info["total_items"],
            "elapsed_time": elapsed_time,
            "estimated_remaining_time": estimated_remaining_time,
            "status": batch_info["status"]
        }
    
    def get_batch_statistics(self) -> Dict[str, Any]:
        """Get overall batch processing statistics."""
        if not self.completed_batches:
            return {
                "total_batches": 0,
                "total_items_processed": 0,
                "average_success_rate": 0.0,
                "average_processing_time": 0.0
            }
        
        total_items = sum(batch.total_items for batch in self.completed_batches)
        total_successful = sum(batch.successful_items for batch in self.completed_batches)
        total_time = sum(batch.processing_time for batch in self.completed_batches)
        
        return {
            "total_batches": len(self.completed_batches),
            "total_items_processed": total_items,
            "total_successful_items": total_successful,
            "average_success_rate": total_successful / total_items if total_items > 0 else 0,
            "average_processing_time": total_time / len(self.completed_batches),
            "active_batches": len(self.active_batches)
        }
    
    def cancel_batch(self, batch_id: str) -> bool:
        """Cancel an active batch operation."""
        if batch_id in self.active_batches:
            self.active_batches[batch_id]["status"] = "cancelled"
            logger.info(f"Batch {batch_id} marked for cancellation")
            return True
        return False