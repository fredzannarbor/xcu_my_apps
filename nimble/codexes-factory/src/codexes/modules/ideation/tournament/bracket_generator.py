"""
Bracket generation for tournaments.
Creates tournament brackets and match pairings.
"""

import logging
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any
from enum import Enum

from ..core.codex_object import CodexObject

logger = logging.getLogger(__name__)


@dataclass
class TournamentBracket:
    """Represents a tournament bracket structure."""
    tournament_type: str
    participant_count: int
    rounds: List[List[Tuple[str, str]]] = field(default_factory=list)
    seeding: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BracketGenerator:
    """
    Generates tournament brackets and match pairings.
    Supports multiple tournament formats.
    """
    
    def __init__(self):
        """Initialize bracket generator."""
        logger.info("BracketGenerator initialized")
    
    def generate_single_elimination_bracket(self, participants: List[CodexObject]) -> TournamentBracket:
        """Generate a single elimination tournament bracket."""
        try:
            participant_count = len(participants)
            
            # Ensure power of 2 participants
            next_power_of_2 = 1
            while next_power_of_2 < participant_count:
                next_power_of_2 *= 2
            
            # Create seeding
            seeding = {}
            for i, participant in enumerate(participants):
                seeding[participant.uuid] = i + 1
            
            # Generate bracket rounds
            rounds = []
            current_participants = [p.uuid for p in participants]
            
            # Add byes if needed
            while len(current_participants) < next_power_of_2:
                current_participants.append("BYE")
            
            # Generate rounds
            while len(current_participants) > 1:
                round_matches = []
                next_round_participants = []
                
                for i in range(0, len(current_participants), 2):
                    participant_a = current_participants[i]
                    participant_b = current_participants[i + 1] if i + 1 < len(current_participants) else "BYE"
                    
                    round_matches.append((participant_a, participant_b))
                    
                    # Winner advances (for now, just pick first participant)
                    if participant_a != "BYE":
                        next_round_participants.append(participant_a)
                    else:
                        next_round_participants.append(participant_b)
                
                rounds.append(round_matches)
                current_participants = next_round_participants
            
            bracket = TournamentBracket(
                tournament_type="single_elimination",
                participant_count=participant_count,
                rounds=rounds,
                seeding=seeding,
                metadata={
                    "total_rounds": len(rounds),
                    "total_matches": sum(len(round_matches) for round_matches in rounds)
                }
            )
            
            logger.info(f"Generated single elimination bracket with {participant_count} participants")
            return bracket
            
        except Exception as e:
            logger.error(f"Error generating single elimination bracket: {e}")
            raise
    
    def generate_round_robin_bracket(self, participants: List[CodexObject]) -> TournamentBracket:
        """Generate a round robin tournament bracket."""
        try:
            participant_count = len(participants)
            participant_uuids = [p.uuid for p in participants]
            
            rounds = []
            
            # Generate all possible pairings
            for i in range(participant_count):
                for j in range(i + 1, participant_count):
                    rounds.append([(participant_uuids[i], participant_uuids[j])])
            
            # Create seeding (all equal in round robin)
            seeding = {p.uuid: i + 1 for i, p in enumerate(participants)}
            
            bracket = TournamentBracket(
                tournament_type="round_robin",
                participant_count=participant_count,
                rounds=rounds,
                seeding=seeding,
                metadata={
                    "total_rounds": len(rounds),
                    "total_matches": len(rounds)
                }
            )
            
            logger.info(f"Generated round robin bracket with {participant_count} participants")
            return bracket
            
        except Exception as e:
            logger.error(f"Error generating round robin bracket: {e}")
            raise
    
    def generate_swiss_bracket(self, participants: List[CodexObject], rounds: int = 3) -> TournamentBracket:
        """Generate a Swiss system tournament bracket."""
        try:
            participant_count = len(participants)
            participant_uuids = [p.uuid for p in participants]
            
            # Initial random pairing for first round
            shuffled_participants = participant_uuids.copy()
            random.shuffle(shuffled_participants)
            
            bracket_rounds = []
            
            # Generate first round
            first_round = []
            for i in range(0, len(shuffled_participants), 2):
                if i + 1 < len(shuffled_participants):
                    first_round.append((shuffled_participants[i], shuffled_participants[i + 1]))
            
            bracket_rounds.append(first_round)
            
            # Subsequent rounds would be generated based on results
            # For now, just create placeholder rounds
            for round_num in range(1, rounds):
                round_matches = []
                # In a real implementation, this would pair based on standings
                for i in range(0, len(participant_uuids), 2):
                    if i + 1 < len(participant_uuids):
                        round_matches.append((participant_uuids[i], participant_uuids[i + 1]))
                bracket_rounds.append(round_matches)
            
            seeding = {p.uuid: i + 1 for i, p in enumerate(participants)}
            
            bracket = TournamentBracket(
                tournament_type="swiss",
                participant_count=participant_count,
                rounds=bracket_rounds,
                seeding=seeding,
                metadata={
                    "total_rounds": rounds,
                    "total_matches": sum(len(round_matches) for round_matches in bracket_rounds)
                }
            )
            
            logger.info(f"Generated Swiss bracket with {participant_count} participants, {rounds} rounds")
            return bracket
            
        except Exception as e:
            logger.error(f"Error generating Swiss bracket: {e}")
            raise
    
    def update_bracket_with_results(self, bracket: TournamentBracket, 
                                   round_number: int, match_results: List[str]) -> TournamentBracket:
        """Update bracket with match results."""
        try:
            if round_number >= len(bracket.rounds):
                logger.warning(f"Round {round_number} does not exist in bracket")
                return bracket
            
            current_round = bracket.rounds[round_number]
            
            if len(match_results) != len(current_round):
                logger.warning(f"Match results count ({len(match_results)}) doesn't match round matches ({len(current_round)})")
                return bracket
            
            # Update bracket metadata with results
            if "results" not in bracket.metadata:
                bracket.metadata["results"] = {}
            
            bracket.metadata["results"][f"round_{round_number}"] = match_results
            
            logger.info(f"Updated bracket with results for round {round_number}")
            return bracket
            
        except Exception as e:
            logger.error(f"Error updating bracket with results: {e}")
            return bracket
    
    def get_bracket_summary(self, bracket: TournamentBracket) -> Dict[str, Any]:
        """Get a summary of the tournament bracket."""
        try:
            summary = {
                "tournament_type": bracket.tournament_type,
                "participant_count": bracket.participant_count,
                "total_rounds": len(bracket.rounds),
                "total_matches": sum(len(round_matches) for round_matches in bracket.rounds),
                "seeding_count": len(bracket.seeding),
                "metadata": bracket.metadata
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting bracket summary: {e}")
            return {"error": str(e)}