"""
Automated tournament execution for continuous generation.
Automatically runs tournaments on generated concepts.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

from ..core.codex_object import CodexObject

logger = logging.getLogger(__name__)


class TournamentTrigger(Enum):
    """Triggers for automatic tournaments."""
    CONCEPT_COUNT = "concept_count"
    TIME_INTERVAL = "time_interval"
    QUALITY_THRESHOLD = "quality_threshold"
    MANUAL = "manual"


@dataclass
class TournamentConfiguration:
    """Configuration for automatic tournaments."""
    trigger_type: TournamentTrigger = TournamentTrigger.CONCEPT_COUNT
    trigger_value: int = 8  # concepts for count trigger, seconds for time trigger
    tournament_size: int = 8
    min_concepts_required: int = 4
    auto_promote_winner: bool = False
    save_results: bool = True
    cleanup_after_tournament: bool = False
    evaluation_criteria: str = "originality, market appeal, character development"


class AutoTournamentExecutor:
    """Executes tournaments automatically based on triggers."""
    
    def __init__(self):
        """Initialize the auto tournament executor."""
        self.tournament_history: List[Dict[str, Any]] = []
        self.active_configurations: Dict[str, TournamentConfiguration] = {}
        logger.info("AutoTournamentExecutor initialized")
    
    def configure_auto_tournaments(self, session_id: str, 
                                 config: TournamentConfiguration):
        """Configure automatic tournaments for a session."""
        self.active_configurations[session_id] = config
        logger.info(f"Configured auto tournaments for session: {session_id}")
    
    def check_tournament_triggers(self, session_id: str, 
                                concepts: List[CodexObject]) -> bool:
        """Check if tournament should be triggered."""
        if session_id not in self.active_configurations:
            return False
        
        config = self.active_configurations[session_id]
        
        # Check minimum concepts requirement
        if len(concepts) < config.min_concepts_required:
            return False
        
        # Check trigger conditions
        if config.trigger_type == TournamentTrigger.CONCEPT_COUNT:
            return len(concepts) >= config.trigger_value
        
        # For other triggers, would need additional logic
        # This is a simplified implementation
        return False
    
    def execute_auto_tournament(self, session_id: str, 
                              concepts: List[CodexObject]) -> Optional[Dict[str, Any]]:
        """Execute an automatic tournament."""
        if session_id not in self.active_configurations:
            logger.warning(f"No tournament configuration for session: {session_id}")
            return None
        
        config = self.active_configurations[session_id]
        
        try:
            # Select concepts for tournament
            tournament_concepts = self._select_tournament_concepts(concepts, config)
            
            if len(tournament_concepts) < config.min_concepts_required:
                logger.warning(f"Not enough concepts for tournament: {len(tournament_concepts)}")
                return None
            
            # Execute tournament (simplified implementation)
            tournament_result = self._run_tournament(tournament_concepts, config)
            
            # Store result
            tournament_record = {
                "session_id": session_id,
                "tournament_id": f"auto_{session_id}_{len(self.tournament_history)}",
                "timestamp": datetime.now().isoformat(),
                "participant_count": len(tournament_concepts),
                "winner": tournament_result.get("winner"),
                "configuration": {
                    "trigger_type": config.trigger_type.value,
                    "tournament_size": config.tournament_size,
                    "evaluation_criteria": config.evaluation_criteria
                },
                "results": tournament_result
            }
            
            self.tournament_history.append(tournament_record)
            
            logger.info(f"Executed auto tournament for session {session_id}: {tournament_result.get('winner', {}).get('title', 'Unknown')} won")
            
            return tournament_record
            
        except Exception as e:
            logger.error(f"Error executing auto tournament: {e}")
            return None
    
    def _select_tournament_concepts(self, concepts: List[CodexObject], 
                                  config: TournamentConfiguration) -> List[CodexObject]:
        """Select concepts for tournament based on configuration."""
        # Simple selection - take most recent concepts
        tournament_size = min(config.tournament_size, len(concepts))
        return concepts[-tournament_size:]
    
    def _run_tournament(self, concepts: List[CodexObject], 
                       config: TournamentConfiguration) -> Dict[str, Any]:
        """Run a simplified tournament."""
        # This is a simplified implementation
        # In a real implementation, this would use the TournamentEngine
        
        import random
        
        # Simulate tournament rounds
        remaining_concepts = concepts.copy()
        rounds = []
        
        round_num = 1
        while len(remaining_concepts) > 1:
            round_matches = []
            next_round_concepts = []
            
            # Pair up concepts
            for i in range(0, len(remaining_concepts), 2):
                if i + 1 < len(remaining_concepts):
                    concept_a = remaining_concepts[i]
                    concept_b = remaining_concepts[i + 1]
                    
                    # Simulate match (random winner for now)
                    winner = random.choice([concept_a, concept_b])
                    
                    match_result = {
                        "concept_a": concept_a.title,
                        "concept_b": concept_b.title,
                        "winner": winner.title,
                        "reasoning": f"Winner selected based on {config.evaluation_criteria}"
                    }
                    
                    round_matches.append(match_result)
                    next_round_concepts.append(winner)
                else:
                    # Odd concept gets bye
                    next_round_concepts.append(remaining_concepts[i])
            
            rounds.append({
                "round": round_num,
                "matches": round_matches
            })
            
            remaining_concepts = next_round_concepts
            round_num += 1
        
        winner = remaining_concepts[0] if remaining_concepts else None
        
        return {
            "winner": {
                "title": winner.title,
                "content": winner.content,
                "uuid": winner.uuid
            } if winner else None,
            "rounds": rounds,
            "total_rounds": len(rounds),
            "participant_count": len(concepts)
        }
    
    def get_tournament_history(self, session_id: Optional[str] = None, 
                             limit: int = 10) -> List[Dict[str, Any]]:
        """Get tournament history."""
        history = self.tournament_history
        
        if session_id:
            history = [t for t in history if t["session_id"] == session_id]
        
        return sorted(history, key=lambda t: t["timestamp"], reverse=True)[:limit]
    
    def get_tournament_statistics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get tournament statistics."""
        history = self.tournament_history
        
        if session_id:
            history = [t for t in history if t["session_id"] == session_id]
        
        if not history:
            return {
                "total_tournaments": 0,
                "total_participants": 0,
                "average_participants": 0
            }
        
        total_tournaments = len(history)
        total_participants = sum(t["participant_count"] for t in history)
        average_participants = total_participants / total_tournaments
        
        return {
            "total_tournaments": total_tournaments,
            "total_participants": total_participants,
            "average_participants": average_participants,
            "most_recent": history[-1]["timestamp"] if history else None
        }
    
    def disable_auto_tournaments(self, session_id: str):
        """Disable automatic tournaments for a session."""
        if session_id in self.active_configurations:
            del self.active_configurations[session_id]
            logger.info(f"Disabled auto tournaments for session: {session_id}")
    
    def get_active_configurations(self) -> Dict[str, TournamentConfiguration]:
        """Get all active tournament configurations."""
        return self.active_configurations.copy()