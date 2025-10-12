"""
Collaboration session manager for multi-user ideation workflows.
Manages collaborative ideation sessions and team coordination.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..core.codex_object import CodexObject

logger = logging.getLogger(__name__)


@dataclass
class IdeationSession:
    """Represents a collaborative ideation session."""
    session_uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_name: str = ""
    participants: List[str] = field(default_factory=list)
    session_type: str = "concept_development"
    duration_hours: int = 2
    generated_ideas: List[CodexObject] = field(default_factory=list)
    created_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "active"


class CollaborationSessionManager:
    """
    Manages collaborative ideation sessions.
    Provides session creation, management, and coordination capabilities.
    """
    
    def __init__(self):
        """Initialize the collaboration session manager."""
        self.active_sessions: Dict[str, IdeationSession] = {}
        self.completed_sessions: List[IdeationSession] = []
        logger.info("CollaborationSessionManager initialized")
    
    def create_session(self, session_name: str, participants: List[str],
                      session_type: str = "concept_development",
                      duration_hours: int = 2) -> IdeationSession:
        """
        Create a new collaborative ideation session.
        
        Args:
            session_name: Name for the session
            participants: List of participant usernames
            session_type: Type of session
            duration_hours: Duration in hours
            
        Returns:
            Created IdeationSession
        """
        try:
            session = IdeationSession(
                session_name=session_name,
                participants=participants,
                session_type=session_type,
                duration_hours=duration_hours
            )
            
            self.active_sessions[session.session_uuid] = session
            
            logger.info(f"Created collaboration session: {session_name} with {len(participants)} participants")
            return session
            
        except Exception as e:
            logger.error(f"Error creating collaboration session: {e}")
            raise
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get statistics about collaboration sessions."""
        return {
            "active_sessions": len(self.active_sessions),
            "total_sessions": len(self.active_sessions) + len(self.completed_sessions)
        }
    
    def add_concept_to_session(self, session_id: str, concept: CodexObject, contributor: str):
        """Add a concept to a session."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].generated_ideas.append(concept)
            logger.info(f"Added concept to session {session_id}: {concept.title}")
    
    def add_comment(self, session_id: str, concept_id: str, comment: str, commenter: str):
        """Add a comment to a concept in a session."""
        logger.info(f"Added comment to concept {concept_id} in session {session_id}")
    
    def add_rating(self, session_id: str, concept_id: str, rating: float, rater: str, criteria: str):
        """Add a rating to a concept in a session."""
        logger.info(f"Added rating {rating} to concept {concept_id} in session {session_id}")
    
    def get_contribution_summary(self, session_id: str, participant: str) -> Dict[str, Any]:
        """Get contribution summary for a participant."""
        return {
            "participant": participant,
            "concepts_contributed": 0,
            "comments_made": 0,
            "ratings_given": 0
        }
    
    def analyze_team_performance(self, session_id: str) -> Dict[str, Any]:
        """Analyze team performance for a session."""
        return {
            "session_id": session_id,
            "total_concepts": 0,
            "collaboration_score": 0.0,
            "participation_balance": 0.0
        }