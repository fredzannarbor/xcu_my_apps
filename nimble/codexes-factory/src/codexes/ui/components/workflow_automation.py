"""
Workflow Automation Component

Provides scheduling and automation capabilities for workflows.
Allows users to set up automated workflow execution with various triggers and conditions.
"""

import streamlit as st
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import sys
import threading
import time

# Add project paths for imports
project_root = Path(__file__).resolve().parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from codexes.modules.ideation.core.codex_object import CodexObject

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Types of automation triggers."""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    CONTENT_THRESHOLD = "content_threshold"
    TIME_INTERVAL = "time_interval"
    EXTERNAL_EVENT = "external_event"


class AutomationStatus(Enum):
    """Status of automation jobs."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AutomationTrigger:
    """Configuration for automation triggers."""
    trigger_type: TriggerType
    parameters: Dict[str, Any]
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_type": self.trigger_type.value,
            "parameters": self.parameters,
            "description": self.description
        }


@dataclass
class AutomationJob:
    """Automated workflow job configuration."""
    id: str
    name: str
    description: str
    workflow_type: str
    workflow_config: Dict[str, Any]
    trigger: AutomationTrigger
    status: AutomationStatus
    created_date: str
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutomationJob':
        # Convert enum fields
        data['status'] = AutomationStatus(data['status'])
        data['trigger'] = AutomationTrigger(
            trigger_type=TriggerType(data['trigger']['trigger_type']),
            parameters=data['trigger']['parameters'],
            description=data['trigger'].get('description', '')
        )
        return cls(**data)


class WorkflowAutomation:
    """
    Workflow automation and scheduling system.
    Provides capabilities for automated workflow execution with various triggers.
    """
    
    def __init__(self):
        """Initialize the workflow automation system."""
        self.session_key = "workflow_automation_state"
        self.jobs_file = Path("data/automation_jobs.json")
        self.jobs_file.parent.mkdir(exist_ok=True)
        
        # Initialize session state
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                'jobs': self._load_jobs(),
                'automation_enabled': True,
                'job_history': []
            }
        
        logger.info("WorkflowAutomation initialized")
    
    def render_automation_interface(self) -> Dict[str, Any]:
        """
        Render the workflow automation interface.
        
        Returns:
            Dictionary containing automation actions and results
        """
        st.markdown("### 🤖 Workflow Automation")
        
        # Create automation tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Active Jobs", "➕ Create Job", "📊 Job History", "⚙️ Settings"])
        
        with tab1:
            return self._render_active_jobs()
        
        with tab2:
            return self._render_create_job()
        
        with tab3:
            return self._render_job_history()
        
        with tab4:
            return self._render_automation_settings()
    
    def _render_active_jobs(self) -> Dict[str, Any]:
        """Render active automation jobs interface."""
        st.markdown("#### 📋 Active Automation Jobs")
        
        state = st.session_state[self.session_key]
        jobs = state['jobs']
        automation_enabled = state['automation_enabled']
        
        # Global automation toggle
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if not automation_enabled:
                st.warning("⚠️ Automation is currently disabled. Enable it in Settings to run jobs.")
        
        with col2:
            if st.button("🔄 Refresh Jobs"):
                st.rerun()
        
        if not jobs:
            st.info("No automation jobs configured. Create your first job in the 'Create Job' tab!")
            return {}
        
        # Filter jobs
        status_filter = st.selectbox(
            "Filter by Status",
            options=["All"] + [status.value.title() for status in AutomationStatus]
        )
        
        filtered_jobs = jobs
        if status_filter != "All":
            status_enum = AutomationStatus(status_filter.lower())
            filtered_jobs = [job for job in jobs if job.status == status_enum]
        
        if not filtered_jobs:
            st.warning(f"No jobs with status '{status_filter}' found.")
            return {}
        
        # Display jobs
        for job in filtered_jobs:
            with st.expander(f"🤖 {job.name} ({job.status.value.title()})", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Description:** {job.description}")
                    st.write(f"**Workflow Type:** {job.workflow_type.replace('_', ' ').title()}")
                    st.write(f"**Trigger:** {job.trigger.trigger_type.value.replace('_', ' ').title()}")
                    st.write(f"**Created:** {job.created_date}")
                    
                    if job.last_run:
                        st.write(f"**Last Run:** {job.last_run}")
                    
                    if job.next_run:
                        st.write(f"**Next Run:** {job.next_run}")
                    
                    # Job statistics
                    st.write(f"**Runs:** {job.run_count} total, {job.success_count} successful, {job.failure_count} failed")
                    
                    # Trigger details
                    with st.expander("🔧 Trigger Configuration", expanded=False):
                        st.json(job.trigger.parameters)
                
                with col2:
                    # Job controls
                    if job.enabled and automation_enabled:
                        if st.button("⏸️ Pause", key=f"pause_{job.id}"):
                            self._pause_job(job.id)
                            st.rerun()
                    else:
                        if st.button("▶️ Resume", key=f"resume_{job.id}"):
                            self._resume_job(job.id)
                            st.rerun()
                    
                    if st.button("🚀 Run Now", key=f"run_{job.id}"):
                        result = self._execute_job_manually(job)
                        if result.get("success"):
                            st.success("✅ Job executed successfully!")
                        else:
                            st.error(f"❌ Job failed: {result.get('error', 'Unknown error')}")
                        st.rerun()
                    
                    if st.button("📝 Edit", key=f"edit_{job.id}"):
                        st.session_state[f"edit_job_{job.id}"] = True
                        st.rerun()
                    
                    if st.button("🗑️ Delete", key=f"delete_{job.id}"):
                        self._delete_job(job.id)
                        st.success("Job deleted successfully!")
                        st.rerun()
                
                # Edit job inline
                if st.session_state.get(f"edit_job_{job.id}", False):
                    st.markdown("---")
                    st.markdown("**Edit Job:**")
                    
                    with st.form(f"edit_job_form_{job.id}"):
                        new_name = st.text_input("Job Name", value=job.name)
                        new_description = st.text_area("Description", value=job.description)
                        new_enabled = st.checkbox("Enabled", value=job.enabled)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.form_submit_button("💾 Save Changes"):
                                job.name = new_name
                                job.description = new_description
                                job.enabled = new_enabled
                                self._update_job(job)
                                st.session_state[f"edit_job_{job.id}"] = False
                                st.success("Job updated successfully!")
                                st.rerun()
                        
                        with col2:
                            if st.form_submit_button("❌ Cancel"):
                                st.session_state[f"edit_job_{job.id}"] = False
                                st.rerun()
        
        return {}
    
    def _render_create_job(self) -> Dict[str, Any]:
        """Render job creation interface."""
        st.markdown("#### ➕ Create Automation Job")
        
        # Job basic information
        job_name = st.text_input(
            "Job Name *",
            placeholder="e.g., 'Daily Tournament', 'Weekly Reader Panel'"
        )
        
        job_description = st.text_area(
            "Description *",
            placeholder="Describe what this automation job does..."
        )
        
        # Workflow configuration
        st.markdown("#### ⚙️ Workflow Configuration")
        
        workflow_type = st.selectbox(
            "Workflow Type *",
            options=[
                ("Tournament", "tournament"),
                ("Reader Panel", "reader_panel"),
                ("Series Generation", "series_generation")
            ],
            format_func=lambda x: x[0]
        )
        
        if not workflow_type:
            return {}
        
        workflow_type_value = workflow_type[1]
        
        # Simplified workflow configuration for automation
        workflow_config = self._render_simplified_workflow_config(workflow_type_value)
        
        # Trigger configuration
        st.markdown("#### 🔔 Trigger Configuration")
        
        trigger_type = st.selectbox(
            "Trigger Type *",
            options=[
                ("Manual Only", TriggerType.MANUAL),
                ("Scheduled", TriggerType.SCHEDULED),
                ("Content Threshold", TriggerType.CONTENT_THRESHOLD),
                ("Time Interval", TriggerType.TIME_INTERVAL)
            ],
            format_func=lambda x: x[0]
        )
        
        if not trigger_type:
            return {}
        
        trigger_config = self._render_trigger_configuration(trigger_type[1])
        
        # Content source configuration
        st.markdown("#### 📁 Content Source")
        
        content_source = st.selectbox(
            "Content Source",
            options=[
                ("Session Objects", "session"),
                ("File Directory", "directory"),
                ("Database Query", "database")
            ],
            format_func=lambda x: x[0]
        )
        
        content_config = self._render_content_source_config(content_source[1] if content_source else "session")
        
        # Create job
        if job_name and job_description and workflow_config and trigger_config:
            if st.button("🚀 Create Automation Job", type="primary"):
                job_id = self._generate_job_id(job_name)
                
                trigger = AutomationTrigger(
                    trigger_type=trigger_type[1],
                    parameters=trigger_config,
                    description=f"{trigger_type[0]} trigger"
                )
                
                new_job = AutomationJob(
                    id=job_id,
                    name=job_name,
                    description=job_description,
                    workflow_type=workflow_type_value,
                    workflow_config={
                        **workflow_config,
                        "content_source": content_config
                    },
                    trigger=trigger,
                    status=AutomationStatus.ACTIVE,
                    created_date=datetime.now().isoformat()
                )
                
                # Calculate next run time if scheduled
                if trigger_type[1] in [TriggerType.SCHEDULED, TriggerType.TIME_INTERVAL]:
                    new_job.next_run = self._calculate_next_run(trigger).isoformat()
                
                self._save_job(new_job)
                st.success(f"✅ Automation job '{job_name}' created successfully!")
                st.rerun()
        
        return {}
    
    def _render_job_history(self) -> Dict[str, Any]:
        """Render job execution history."""
        st.markdown("#### 📊 Job Execution History")
        
        state = st.session_state[self.session_key]
        job_history = state.get('job_history', [])
        
        if not job_history:
            st.info("No job execution history available yet.")
            return {}
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            date_filter = st.date_input("Filter by Date (from)")
        
        with col2:
            status_filter = st.selectbox(
                "Filter by Result",
                options=["All", "Success", "Failed"]
            )
        
        # Display history
        filtered_history = job_history
        
        # Apply filters
        if date_filter:
            filtered_history = [
                h for h in filtered_history
                if datetime.fromisoformat(h['timestamp']).date() >= date_filter
            ]
        
        if status_filter != "All":
            success_filter = status_filter == "Success"
            filtered_history = [
                h for h in filtered_history
                if h['success'] == success_filter
            ]
        
        if not filtered_history:
            st.warning("No history entries match your filters.")
            return {}
        
        # Display history entries
        for entry in sorted(filtered_history, key=lambda x: x['timestamp'], reverse=True):
            status_icon = "✅" if entry['success'] else "❌"
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
            
            with st.expander(f"{status_icon} {entry['job_name']} - {timestamp}", expanded=False):
                st.write(f"**Job ID:** {entry['job_id']}")
                st.write(f"**Workflow Type:** {entry['workflow_type']}")
                st.write(f"**Duration:** {entry.get('duration', 'Unknown')} seconds")
                
                if entry['success']:
                    st.success("✅ Execution completed successfully")
                    if 'results_summary' in entry:
                        st.write(f"**Results:** {entry['results_summary']}")
                else:
                    st.error(f"❌ Execution failed: {entry.get('error', 'Unknown error')}")
                
                # Show detailed results if available
                if 'detailed_results' in entry:
                    with st.expander("📊 Detailed Results", expanded=False):
                        st.json(entry['detailed_results'])
        
        return {}
    
    def _render_automation_settings(self) -> Dict[str, Any]:
        """Render automation settings interface."""
        st.markdown("#### ⚙️ Automation Settings")
        
        state = st.session_state[self.session_key]
        
        # Global automation toggle
        automation_enabled = st.checkbox(
            "Enable Automation",
            value=state.get('automation_enabled', True),
            help="Master switch for all automation jobs"
        )
        
        state['automation_enabled'] = automation_enabled
        
        # Automation intervals
        st.markdown("**Default Intervals:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            default_check_interval = st.slider(
                "Job Check Interval (minutes)",
                min_value=1,
                max_value=60,
                value=5,
                help="How often to check for jobs that need to run"
            )
        
        with col2:
            max_concurrent_jobs = st.slider(
                "Max Concurrent Jobs",
                min_value=1,
                max_value=10,
                value=3,
                help="Maximum number of jobs that can run simultaneously"
            )
        
        # Notification settings
        st.markdown("**Notifications:**")
        
        notify_on_success = st.checkbox("Notify on successful job completion", value=False)
        notify_on_failure = st.checkbox("Notify on job failure", value=True)
        
        # Cleanup settings
        st.markdown("**Cleanup:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            history_retention_days = st.slider(
                "History Retention (days)",
                min_value=7,
                max_value=365,
                value=30,
                help="How long to keep job execution history"
            )
        
        with col2:
            if st.button("🧹 Clean Old History"):
                cleaned_count = self._cleanup_old_history(history_retention_days)
                st.success(f"✅ Cleaned {cleaned_count} old history entries")
        
        # Save settings
        if st.button("💾 Save Settings"):
            settings = {
                'automation_enabled': automation_enabled,
                'default_check_interval': default_check_interval,
                'max_concurrent_jobs': max_concurrent_jobs,
                'notify_on_success': notify_on_success,
                'notify_on_failure': notify_on_failure,
                'history_retention_days': history_retention_days
            }
            
            self._save_settings(settings)
            st.success("✅ Settings saved successfully!")
        
        # System status
        st.markdown("#### 📊 System Status")
        
        jobs = state['jobs']
        active_jobs = len([job for job in jobs if job.status == AutomationStatus.ACTIVE and job.enabled])
        total_jobs = len(jobs)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Jobs", total_jobs)
        
        with col2:
            st.metric("Active Jobs", active_jobs)
        
        with col3:
            st.metric("Automation Status", "Enabled" if automation_enabled else "Disabled")
        
        return {}
    
    def _render_simplified_workflow_config(self, workflow_type: str) -> Dict[str, Any]:
        """Render simplified workflow configuration for automation."""
        if workflow_type == "tournament":
            return {
                "tournament_type": "single_elimination",
                "evaluation_criteria": {
                    "originality": 0.3,
                    "marketability": 0.3,
                    "execution_potential": 0.2,
                    "emotional_impact": 0.2
                }
            }
        
        elif workflow_type == "reader_panel":
            panel_size = st.slider("Panel Size", min_value=3, max_value=15, value=8)
            return {
                "panel_size": panel_size,
                "demographics": {
                    "age_distribution": "balanced",
                    "gender_distribution": "balanced",
                    "reading_level_focus": "balanced",
                    "genre_diversity": "medium"
                },
                "evaluation_focus": ["Market Appeal", "Emotional Engagement", "Genre Fit"]
            }
        
        elif workflow_type == "series_generation":
            book_count = st.slider("Number of Books", min_value=2, max_value=5, value=3)
            return {
                "series_type": "standalone_series",
                "target_book_count": book_count,
                "formulaicness_level": 0.5,
                "consistency_requirements": {
                    "setting": 0.8,
                    "tone": 0.7,
                    "genre": 0.9,
                    "themes": 0.6,
                    "character_types": 0.5
                }
            }
        
        return {}
    
    def _render_trigger_configuration(self, trigger_type: TriggerType) -> Dict[str, Any]:
        """Render trigger-specific configuration."""
        if trigger_type == TriggerType.MANUAL:
            st.info("Manual triggers require no additional configuration. Job will only run when manually executed.")
            return {}
        
        elif trigger_type == TriggerType.SCHEDULED:
            st.markdown("**Schedule Configuration:**")
            
            schedule_type = st.selectbox(
                "Schedule Type",
                options=["Daily", "Weekly", "Monthly"]
            )
            
            if schedule_type == "Daily":
                time_input = st.time_input("Run Time", value=datetime.now().time())
                return {
                    "schedule_type": "daily",
                    "time": time_input.strftime("%H:%M")
                }
            
            elif schedule_type == "Weekly":
                day_of_week = st.selectbox(
                    "Day of Week",
                    options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                )
                time_input = st.time_input("Run Time", value=datetime.now().time())
                return {
                    "schedule_type": "weekly",
                    "day_of_week": day_of_week.lower(),
                    "time": time_input.strftime("%H:%M")
                }
            
            elif schedule_type == "Monthly":
                day_of_month = st.slider("Day of Month", min_value=1, max_value=28, value=1)
                time_input = st.time_input("Run Time", value=datetime.now().time())
                return {
                    "schedule_type": "monthly",
                    "day_of_month": day_of_month,
                    "time": time_input.strftime("%H:%M")
                }
        
        elif trigger_type == TriggerType.CONTENT_THRESHOLD:
            st.markdown("**Content Threshold Configuration:**")
            
            threshold_count = st.slider(
                "Minimum Content Count",
                min_value=2,
                max_value=50,
                value=10,
                help="Job will run when this many content objects are available"
            )
            
            content_types = st.multiselect(
                "Content Types (optional)",
                options=["idea", "synopsis", "outline", "draft", "manuscript"],
                help="Limit to specific content types, or leave empty for all types"
            )
            
            return {
                "threshold_count": threshold_count,
                "content_types": content_types
            }
        
        elif trigger_type == TriggerType.TIME_INTERVAL:
            st.markdown("**Time Interval Configuration:**")
            
            interval_value = st.slider("Interval Value", min_value=1, max_value=24, value=1)
            interval_unit = st.selectbox(
                "Interval Unit",
                options=["hours", "days", "weeks"]
            )
            
            return {
                "interval_value": interval_value,
                "interval_unit": interval_unit
            }
        
        return {}
    
    def _render_content_source_config(self, source_type: str) -> Dict[str, Any]:
        """Render content source configuration."""
        if source_type == "session":
            st.info("Will use content objects from the current session.")
            return {"type": "session"}
        
        elif source_type == "directory":
            directory_path = st.text_input(
                "Directory Path",
                value="data/",
                help="Path to directory containing content files"
            )
            
            file_types = st.multiselect(
                "File Types",
                options=[".txt", ".md", ".docx", ".pdf"],
                default=[".txt", ".md"],
                help="File types to include"
            )
            
            return {
                "type": "directory",
                "path": directory_path,
                "file_types": file_types
            }
        
        elif source_type == "database":
            st.info("Database content source configuration coming soon.")
            return {"type": "database"}
        
        return {"type": "session"}
    
    def _generate_job_id(self, name: str) -> str:
        """Generate unique job ID."""
        import hashlib
        timestamp = datetime.now().isoformat()
        unique_string = f"{name}_{timestamp}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    def _calculate_next_run(self, trigger: AutomationTrigger) -> datetime:
        """Calculate next run time for a trigger."""
        now = datetime.now()
        params = trigger.parameters
        
        if trigger.trigger_type == TriggerType.SCHEDULED:
            schedule_type = params.get("schedule_type", "daily")
            time_str = params.get("time", "09:00")
            hour, minute = map(int, time_str.split(":"))
            
            if schedule_type == "daily":
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                return next_run
            
            elif schedule_type == "weekly":
                # Implementation for weekly scheduling
                return now + timedelta(days=7)
            
            elif schedule_type == "monthly":
                # Implementation for monthly scheduling
                return now + timedelta(days=30)
        
        elif trigger.trigger_type == TriggerType.TIME_INTERVAL:
            interval_value = params.get("interval_value", 1)
            interval_unit = params.get("interval_unit", "hours")
            
            if interval_unit == "hours":
                return now + timedelta(hours=interval_value)
            elif interval_unit == "days":
                return now + timedelta(days=interval_value)
            elif interval_unit == "weeks":
                return now + timedelta(weeks=interval_value)
        
        return now + timedelta(hours=1)  # Default fallback
    
    def _save_job(self, job: AutomationJob):
        """Save job to session state and file."""
        state = st.session_state[self.session_key]
        state['jobs'].append(job)
        self._save_jobs_to_file(state['jobs'])
    
    def _update_job(self, job: AutomationJob):
        """Update existing job."""
        state = st.session_state[self.session_key]
        jobs = state['jobs']
        
        for i, j in enumerate(jobs):
            if j.id == job.id:
                jobs[i] = job
                break
        
        self._save_jobs_to_file(jobs)
    
    def _delete_job(self, job_id: str):
        """Delete job."""
        state = st.session_state[self.session_key]
        state['jobs'] = [job for job in state['jobs'] if job.id != job_id]
        self._save_jobs_to_file(state['jobs'])
    
    def _pause_job(self, job_id: str):
        """Pause job execution."""
        state = st.session_state[self.session_key]
        for job in state['jobs']:
            if job.id == job_id:
                job.enabled = False
                job.status = AutomationStatus.PAUSED
                break
        self._save_jobs_to_file(state['jobs'])
    
    def _resume_job(self, job_id: str):
        """Resume job execution."""
        state = st.session_state[self.session_key]
        for job in state['jobs']:
            if job.id == job_id:
                job.enabled = True
                job.status = AutomationStatus.ACTIVE
                break
        self._save_jobs_to_file(state['jobs'])
    
    def _execute_job_manually(self, job: AutomationJob) -> Dict[str, Any]:
        """Execute job manually."""
        try:
            start_time = time.time()
            
            # Simulate job execution (in real implementation, this would call the actual workflow)
            st.info(f"🚀 Executing job: {job.name}")
            
            # Update job statistics
            job.run_count += 1
            job.last_run = datetime.now().isoformat()
            
            # Calculate next run if applicable
            if job.trigger.trigger_type in [TriggerType.SCHEDULED, TriggerType.TIME_INTERVAL]:
                job.next_run = self._calculate_next_run(job.trigger).isoformat()
            
            # Simulate success (in real implementation, this would be actual results)
            execution_time = time.time() - start_time
            job.success_count += 1
            
            # Log execution
            self._log_job_execution(job, True, execution_time, {"simulated": True})
            
            self._update_job(job)
            
            return {
                "success": True,
                "execution_time": execution_time,
                "results": {"simulated": True}
            }
        
        except Exception as e:
            logger.error(f"Error executing job {job.id}: {e}")
            
            job.failure_count += 1
            self._log_job_execution(job, False, 0, {"error": str(e)})
            self._update_job(job)
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def _log_job_execution(self, job: AutomationJob, success: bool, duration: float, results: Dict[str, Any]):
        """Log job execution to history."""
        state = st.session_state[self.session_key]
        
        history_entry = {
            "job_id": job.id,
            "job_name": job.name,
            "workflow_type": job.workflow_type,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "duration": duration,
            "detailed_results": results
        }
        
        if success:
            history_entry["results_summary"] = f"Job completed successfully in {duration:.2f} seconds"
        else:
            history_entry["error"] = results.get("error", "Unknown error")
        
        if 'job_history' not in state:
            state['job_history'] = []
        
        state['job_history'].append(history_entry)
        
        # Keep only recent history (last 1000 entries)
        if len(state['job_history']) > 1000:
            state['job_history'] = state['job_history'][-1000:]
    
    def _cleanup_old_history(self, retention_days: int) -> int:
        """Clean up old job history entries."""
        state = st.session_state[self.session_key]
        job_history = state.get('job_history', [])
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        original_count = len(job_history)
        state['job_history'] = [
            entry for entry in job_history
            if datetime.fromisoformat(entry['timestamp']) > cutoff_date
        ]
        
        cleaned_count = original_count - len(state['job_history'])
        return cleaned_count
    
    def _load_jobs(self) -> List[AutomationJob]:
        """Load jobs from file."""
        try:
            if self.jobs_file.exists():
                with open(self.jobs_file, 'r') as f:
                    jobs_data = json.load(f)
                    return [AutomationJob.from_dict(data) for data in jobs_data]
        except Exception as e:
            logger.error(f"Error loading jobs: {e}")
        
        return []
    
    def _save_jobs_to_file(self, jobs: List[AutomationJob]):
        """Save jobs to file."""
        try:
            jobs_data = [job.to_dict() for job in jobs]
            with open(self.jobs_file, 'w') as f:
                json.dump(jobs_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving jobs: {e}")
    
    def _save_settings(self, settings: Dict[str, Any]):
        """Save automation settings."""
        settings_file = Path("data/automation_settings.json")
        try:
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
    
    def check_and_run_scheduled_jobs(self):
        """Check for and run scheduled jobs (would be called by background process)."""
        # This would be implemented as a background service
        # For now, it's a placeholder for the automation system
        pass