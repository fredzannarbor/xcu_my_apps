"""
Automation engine for ideation workflows.
Provides job scheduling and automated processing capabilities.
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from threading import Thread, Event

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Status of automation jobs."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(Enum):
    """Priority levels for jobs."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class AutomationJob:
    """Represents an automation job."""
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_name: str = ""
    job_function: Optional[Callable] = None
    job_args: List[Any] = field(default_factory=list)
    job_kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: JobPriority = JobPriority.NORMAL
    scheduled_time: Optional[datetime] = None
    max_retries: int = 3
    retry_delay: float = 60.0
    timeout_seconds: int = 3600
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Any = None
    retry_count: int = 0


class JobScheduler:
    """Schedules and manages automation jobs."""
    
    def __init__(self, max_concurrent_jobs: int = 4):
        """Initialize the job scheduler."""
        self.max_concurrent_jobs = max_concurrent_jobs
        self.pending_jobs: List[AutomationJob] = []
        self.running_jobs: Dict[str, AutomationJob] = {}
        self.completed_jobs: List[AutomationJob] = []
        self.scheduler_thread: Optional[Thread] = None
        self.stop_event = Event()
        self.running = False
        logger.info("JobScheduler initialized")
    
    def start(self):
        """Start the job scheduler."""
        if not self.running:
            self.running = True
            self.stop_event.clear()
            self.scheduler_thread = Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            logger.info("Job scheduler started")
    
    def stop(self):
        """Stop the job scheduler."""
        if self.running:
            self.running = False
            self.stop_event.set()
            if self.scheduler_thread:
                self.scheduler_thread.join(timeout=5)
            logger.info("Job scheduler stopped")
    
    def schedule_job(self, job: AutomationJob) -> str:
        """Schedule a job for execution."""
        self.pending_jobs.append(job)
        self.pending_jobs.sort(key=lambda j: (j.priority.value, j.created_at), reverse=True)
        logger.info(f"Scheduled job: {job.job_name} ({job.job_id})")
        return job.job_id
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running job."""
        # Check pending jobs
        for i, job in enumerate(self.pending_jobs):
            if job.job_id == job_id:
                job.status = JobStatus.CANCELLED
                self.completed_jobs.append(self.pending_jobs.pop(i))
                logger.info(f"Cancelled pending job: {job_id}")
                return True
        
        # Check running jobs
        if job_id in self.running_jobs:
            job = self.running_jobs[job_id]
            job.status = JobStatus.CANCELLED
            logger.info(f"Marked running job for cancellation: {job_id}")
            return True
        
        return False
    
    def get_job_status(self, job_id: str) -> Optional[AutomationJob]:
        """Get the status of a job."""
        # Check running jobs
        if job_id in self.running_jobs:
            return self.running_jobs[job_id]
        
        # Check pending jobs
        for job in self.pending_jobs:
            if job.job_id == job_id:
                return job
        
        # Check completed jobs
        for job in self.completed_jobs:
            if job.job_id == job_id:
                return job
        
        return None
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.running and not self.stop_event.is_set():
            try:
                self._process_pending_jobs()
                self._check_running_jobs()
                time.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
    
    def _process_pending_jobs(self):
        """Process pending jobs."""
        current_time = datetime.now()
        
        while (len(self.running_jobs) < self.max_concurrent_jobs and 
               self.pending_jobs and self.running):
            
            job = self.pending_jobs[0]
            
            # Check if job is scheduled for future execution
            if job.scheduled_time and job.scheduled_time > current_time:
                break
            
            # Start the job
            job = self.pending_jobs.pop(0)
            self._start_job(job)
    
    def _start_job(self, job: AutomationJob):
        """Start executing a job."""
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        self.running_jobs[job.job_id] = job
        
        # Start job in separate thread
        job_thread = Thread(target=self._execute_job, args=(job,), daemon=True)
        job_thread.start()
        
        logger.info(f"Started job: {job.job_name} ({job.job_id})")
    
    def _execute_job(self, job: AutomationJob):
        """Execute a job."""
        try:
            if job.job_function:
                result = job.job_function(*job.job_args, **job.job_kwargs)
                job.result = result
                job.status = JobStatus.COMPLETED
                logger.info(f"Job completed successfully: {job.job_id}")
            else:
                raise ValueError("No job function specified")
                
        except Exception as e:
            job.error_message = str(e)
            job.retry_count += 1
            
            if job.retry_count <= job.max_retries:
                # Schedule for retry
                job.status = JobStatus.PENDING
                job.scheduled_time = datetime.now() + timedelta(seconds=job.retry_delay)
                self.pending_jobs.append(job)
                logger.warning(f"Job failed, scheduling retry {job.retry_count}/{job.max_retries}: {job.job_id}")
            else:
                job.status = JobStatus.FAILED
                logger.error(f"Job failed permanently: {job.job_id} - {str(e)}")
        
        finally:
            job.completed_at = datetime.now()
            if job.job_id in self.running_jobs:
                del self.running_jobs[job.job_id]
            self.completed_jobs.append(job)
    
    def _check_running_jobs(self):
        """Check for timed out running jobs."""
        current_time = datetime.now()
        timed_out_jobs = []
        
        for job_id, job in self.running_jobs.items():
            if job.started_at:
                elapsed = (current_time - job.started_at).total_seconds()
                if elapsed > job.timeout_seconds:
                    timed_out_jobs.append(job_id)
        
        for job_id in timed_out_jobs:
            job = self.running_jobs[job_id]
            job.status = JobStatus.FAILED
            job.error_message = "Job timed out"
            job.completed_at = current_time
            del self.running_jobs[job_id]
            self.completed_jobs.append(job)
            logger.error(f"Job timed out: {job_id}")


class AutomationEngine:
    """Main automation engine for ideation workflows."""
    
    def __init__(self):
        """Initialize the automation engine."""
        self.scheduler = JobScheduler()
        self.job_templates: Dict[str, Dict[str, Any]] = {}
        logger.info("AutomationEngine initialized")
    
    def start(self):
        """Start the automation engine."""
        self.scheduler.start()
        logger.info("Automation engine started")
    
    def stop(self):
        """Stop the automation engine."""
        self.scheduler.stop()
        logger.info("Automation engine stopped")
    
    def register_job_template(self, template_name: str, job_function: Callable,
                            default_args: List[Any] = None,
                            default_kwargs: Dict[str, Any] = None,
                            default_priority: JobPriority = JobPriority.NORMAL):
        """Register a job template for easy scheduling."""
        self.job_templates[template_name] = {
            "function": job_function,
            "default_args": default_args or [],
            "default_kwargs": default_kwargs or {},
            "default_priority": default_priority
        }
        logger.info(f"Registered job template: {template_name}")
    
    def schedule_job_from_template(self, template_name: str, job_name: str,
                                 args: List[Any] = None, kwargs: Dict[str, Any] = None,
                                 priority: Optional[JobPriority] = None,
                                 scheduled_time: Optional[datetime] = None) -> str:
        """Schedule a job using a registered template."""
        if template_name not in self.job_templates:
            raise ValueError(f"Unknown job template: {template_name}")
        
        template = self.job_templates[template_name]
        
        job = AutomationJob(
            job_name=job_name,
            job_function=template["function"],
            job_args=args or template["default_args"],
            job_kwargs=kwargs or template["default_kwargs"],
            priority=priority or template["default_priority"],
            scheduled_time=scheduled_time
        )
        
        return self.scheduler.schedule_job(job)
    
    def schedule_custom_job(self, job_name: str, job_function: Callable,
                          args: List[Any] = None, kwargs: Dict[str, Any] = None,
                          priority: JobPriority = JobPriority.NORMAL,
                          scheduled_time: Optional[datetime] = None) -> str:
        """Schedule a custom job."""
        job = AutomationJob(
            job_name=job_name,
            job_function=job_function,
            job_args=args or [],
            job_kwargs=kwargs or {},
            priority=priority,
            scheduled_time=scheduled_time
        )
        
        return self.scheduler.schedule_job(job)
    
    def get_engine_statistics(self) -> Dict[str, Any]:
        """Get automation engine statistics."""
        return {
            "pending_jobs": len(self.scheduler.pending_jobs),
            "running_jobs": len(self.scheduler.running_jobs),
            "completed_jobs": len(self.scheduler.completed_jobs),
            "registered_templates": len(self.job_templates),
            "scheduler_running": self.scheduler.running
        }