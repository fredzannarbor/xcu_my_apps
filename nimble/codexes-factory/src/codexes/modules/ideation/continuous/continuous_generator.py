"""
Continuous generation engine for ideation workflows.
Provides automated, continuous concept generation with monitoring.
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import Thread, Event
from typing import Dict, Any, List, Optional, Callable

from ..core.codex_object import CodexObject
from .spending_control import SpendingTracker, SpendingEntry, estimate_request_cost

logger = logging.getLogger(__name__)


class GenerationStatus(Enum):
    """Status of continuous generation."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class GenerationConfiguration:
    """Configuration for continuous generation."""
    generation_interval: int = 3600  # seconds between generations
    concepts_per_batch: int = 5
    max_stored_concepts: int = 1000
    auto_cleanup: bool = True
    cleanup_threshold: int = 1200
    quality_threshold: float = 0.6
    enable_tournaments: bool = False
    tournament_frequency: int = 10  # every N generations
    notification_callback: Optional[Callable] = None
    
    # Spending control settings
    enable_spending_control: bool = True
    daily_spending_limit: float = 25.0  # USD per day for continuous generation
    hourly_spending_limit: float = 5.0   # USD per hour
    spending_data_dir: str = "data/spending"


@dataclass
class GenerationSession:
    """Represents a continuous generation session."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_name: str = ""
    config: GenerationConfiguration = field(default_factory=GenerationConfiguration)
    status: GenerationStatus = GenerationStatus.STOPPED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    last_generation: Optional[datetime] = None
    total_generations: int = 0
    successful_generations: int = 0
    failed_generations: int = 0
    generated_concepts: List[CodexObject] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)


class ContinuousGenerationEngine:
    """Engine for continuous concept generation."""
    
    def __init__(self):
        """Initialize the continuous generation engine."""
        self.active_sessions: Dict[str, GenerationSession] = {}
        self.completed_sessions: List[GenerationSession] = []
        self.generation_threads: Dict[str, Thread] = {}
        self.stop_events: Dict[str, Event] = {}
        
        # Initialize spending control
        self.spending_tracker = SpendingTracker()
        
        logger.info("ContinuousGenerationEngine initialized with spending controls")
    
    def create_session(self, session_name: str, 
                      config: Optional[GenerationConfiguration] = None) -> str:
        """Create a new continuous generation session."""
        session = GenerationSession(
            session_name=session_name,
            config=config or GenerationConfiguration()
        )
        
        self.active_sessions[session.session_id] = session
        logger.info(f"Created generation session: {session_name} ({session.session_id})")
        return session.session_id
    
    def start_session(self, session_id: str) -> bool:
        """Start a continuous generation session."""
        if session_id not in self.active_sessions:
            logger.error(f"Session not found: {session_id}")
            return False
        
        session = self.active_sessions[session_id]
        if session.status == GenerationStatus.RUNNING:
            logger.warning(f"Session already running: {session_id}")
            return True
        
        # Create stop event and thread
        stop_event = Event()
        self.stop_events[session_id] = stop_event
        
        generation_thread = Thread(
            target=self._generation_loop,
            args=(session, stop_event),
            daemon=True
        )
        
        self.generation_threads[session_id] = generation_thread
        
        # Start the session
        session.status = GenerationStatus.RUNNING
        session.started_at = datetime.now()
        generation_thread.start()
        
        logger.info(f"Started generation session: {session_id}")
        return True
    
    def stop_session(self, session_id: str) -> bool:
        """Stop a continuous generation session."""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        # Signal stop
        if session_id in self.stop_events:
            self.stop_events[session_id].set()
        
        # Wait for thread to finish
        if session_id in self.generation_threads:
            thread = self.generation_threads[session_id]
            thread.join(timeout=5)
            del self.generation_threads[session_id]
        
        # Clean up
        if session_id in self.stop_events:
            del self.stop_events[session_id]
        
        session.status = GenerationStatus.STOPPED
        logger.info(f"Stopped generation session: {session_id}")
        return True
    
    def pause_session(self, session_id: str) -> bool:
        """Pause a continuous generation session."""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        session.status = GenerationStatus.PAUSED
        logger.info(f"Paused generation session: {session_id}")
        return True
    
    def resume_session(self, session_id: str) -> bool:
        """Resume a paused generation session."""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        if session.status == GenerationStatus.PAUSED:
            session.status = GenerationStatus.RUNNING
            logger.info(f"Resumed generation session: {session_id}")
            return True
        
        return False
    
    def _generation_loop(self, session: GenerationSession, stop_event: Event):
        """Main generation loop for a session."""
        logger.info(f"Starting generation loop for session: {session.session_id}")
        
        while not stop_event.is_set():
            try:
                if session.status == GenerationStatus.RUNNING:
                    self._perform_generation(session)
                    session.last_generation = datetime.now()
                
                # Wait for next generation interval
                for _ in range(session.config.generation_interval):
                    if stop_event.is_set():
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in generation loop: {e}")
                session.status = GenerationStatus.ERROR
                session.error_messages.append(str(e))
                break
        
        logger.info(f"Generation loop ended for session: {session.session_id}")
    
    def _perform_generation(self, session: GenerationSession):
        """Perform a single generation cycle."""
        try:
            # Generate concepts (simplified implementation)
            new_concepts = []
            
            for i in range(session.config.concepts_per_batch):
                concept = CodexObject(
                    title=f"Generated Concept {session.total_generations + i + 1}",
                    content=f"Automatically generated concept from session {session.session_name}",
                    genre="Generated Fiction",
                    target_audience="General"
                )
                new_concepts.append(concept)
            
            # Filter by quality if threshold is set
            if session.config.quality_threshold > 0:
                # Simplified quality check - in real implementation would use LLM
                filtered_concepts = [c for c in new_concepts if len(c.content) > 20]
                new_concepts = filtered_concepts
            
            # Add to session
            session.generated_concepts.extend(new_concepts)
            session.total_generations += 1
            session.successful_generations += 1
            
            # Cleanup if needed
            if (session.config.auto_cleanup and 
                len(session.generated_concepts) > session.config.cleanup_threshold):
                self._cleanup_concepts(session)
            
            # Notify if callback is set
            if session.config.notification_callback:
                session.config.notification_callback(session.session_id, len(new_concepts))
            
            logger.debug(f"Generated {len(new_concepts)} concepts for session {session.session_id}")
            
        except Exception as e:
            session.failed_generations += 1
            session.error_messages.append(str(e))
            logger.error(f"Error in generation cycle: {e}")
    
    def _cleanup_concepts(self, session: GenerationSession):
        """Clean up old concepts to maintain storage limits."""
        if len(session.generated_concepts) > session.config.max_stored_concepts:
            # Remove oldest concepts
            excess_count = len(session.generated_concepts) - session.config.max_stored_concepts
            session.generated_concepts = session.generated_concepts[excess_count:]
            logger.debug(f"Cleaned up {excess_count} old concepts from session {session.session_id}")
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status information for a session."""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        # Calculate runtime
        runtime = None
        if session.started_at:
            runtime = (datetime.now() - session.started_at).total_seconds()
        
        # Calculate next generation time
        next_generation = None
        if session.last_generation and session.status == GenerationStatus.RUNNING:
            next_generation = session.last_generation + timedelta(seconds=session.config.generation_interval)
        
        return {
            "session_id": session.session_id,
            "session_name": session.session_name,
            "status": session.status.value,
            "total_generations": session.total_generations,
            "successful_generations": session.successful_generations,
            "failed_generations": session.failed_generations,
            "concepts_generated": len(session.generated_concepts),
            "runtime_seconds": runtime,
            "last_generation": session.last_generation.isoformat() if session.last_generation else None,
            "next_generation": next_generation.isoformat() if next_generation else None,
            "error_count": len(session.error_messages)
        }
    
    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get overall generation statistics."""
        total_sessions = len(self.active_sessions) + len(self.completed_sessions)
        active_sessions = len(self.active_sessions)
        
        total_concepts = sum(len(session.generated_concepts) for session in self.active_sessions.values())
        total_generations = sum(session.total_generations for session in self.active_sessions.values())
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "completed_sessions": len(self.completed_sessions),
            "total_concepts_generated": total_concepts,
            "total_generation_cycles": total_generations,
            "overall_statistics": {
                "total_ideas_generated": total_concepts,
                "average_ideas_per_session": total_concepts / total_sessions if total_sessions > 0 else 0
            }
        }
    
    def get_session_concepts(self, session_id: str, limit: Optional[int] = None) -> List[CodexObject]:
        """Get concepts generated by a session."""
        if session_id not in self.active_sessions:
            return []
        
        session = self.active_sessions[session_id]
        concepts = session.generated_concepts
        
        if limit:
            concepts = concepts[-limit:]  # Get most recent
        
        return concepts
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its data."""
        # Stop if running
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if session.status == GenerationStatus.RUNNING:
                self.stop_session(session_id)
            
            # Move to completed sessions
            self.completed_sessions.append(session)
            del self.active_sessions[session_id]
            
            logger.info(f"Deleted session: {session_id}")
            return True
        
        return False
    
    def get_completed_sessions(self, limit: int = 10) -> List[GenerationSession]:
        """Get completed sessions."""
        return self.completed_sessions[-limit:] if self.completed_sessions else []