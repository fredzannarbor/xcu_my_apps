"""
Tournament engine for CodexObject competitions.
Manages tournament creation, execution, and results tracking.
"""

import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple

from ..core.codex_object import CodexObject
from ..storage.database_manager import IdeationDatabase
from .bracket_generator import BracketGenerator, TournamentBracket
from .evaluation_engine import EvaluationEngine, MatchEvaluation

logger = logging.getLogger(__name__)


class TournamentStatus(Enum):
    """Tournament status enumeration."""
    CREATED = "created"
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TournamentType(Enum):
    """Tournament type enumeration."""
    SINGLE_ELIMINATION = "single_elimination"
    DOUBLE_ELIMINATION = "double_elimination"
    ROUND_ROBIN = "round_robin"
    SWISS = "swiss"


@dataclass
class TournamentMatch:
    """Represents a single match in a tournament."""
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    tournament_uuid: str = ""
    round_number: int = 0
    match_number: int = 0
    object1_uuid: str = ""
    object2_uuid: str = ""
    winner_uuid: Optional[str] = None
    evaluation: Optional[MatchEvaluation] = None
    created_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_timestamp: Optional[str] = None
    
    @property
    def is_completed(self) -> bool:
        """Check if match is completed."""
        return self.winner_uuid is not None and self.completed_timestamp is not None
    
    def complete_match(self, winner_uuid: str, evaluation: MatchEvaluation):
        """Complete the match with winner and evaluation."""
        self.winner_uuid = winner_uuid
        self.evaluation = evaluation
        self.completed_timestamp = datetime.now().isoformat()


@dataclass
class Tournament:
    """Represents a tournament of CodexObjects."""
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    tournament_type: TournamentType = TournamentType.SINGLE_ELIMINATION
    status: TournamentStatus = TournamentStatus.CREATED
    participant_uuids: List[str] = field(default_factory=list)
    matches: List[TournamentMatch] = field(default_factory=list)
    bracket: Optional[TournamentBracket] = None
    config: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    created_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    started_timestamp: Optional[str] = None
    completed_timestamp: Optional[str] = None
    
    @property
    def participant_count(self) -> int:
        """Get number of participants."""
        return len(self.participant_uuids)
    
    @property
    def round_count(self) -> int:
        """Get number of rounds in tournament."""
        if not self.matches:
            return 0
        return max(match.round_number for match in self.matches)
    
    @property
    def is_completed(self) -> bool:
        """Check if tournament is completed."""
        return self.status == TournamentStatus.COMPLETED
    
    def get_matches_by_round(self, round_number: int) -> List[TournamentMatch]:
        """Get all matches for a specific round."""
        return [match for match in self.matches if match.round_number == round_number]
    
    def get_completed_matches(self) -> List[TournamentMatch]:
        """Get all completed matches."""
        return [match for match in self.matches if match.is_completed]
    
    def get_pending_matches(self) -> List[TournamentMatch]:
        """Get all pending matches."""
        return [match for match in self.matches if not match.is_completed]
    
    def get_winner(self) -> Optional[str]:
        """Get tournament winner UUID."""
        if not self.is_completed:
            return None
        return self.results.get("winner_uuid")


class TournamentEngine:
    """
    Manages tournament creation, execution, and results.
    Implements Requirements 1.1, 1.2, 1.3, 1.4 for tournament functionality.
    """
    
    def __init__(self, database: IdeationDatabase):
        """
        Initialize tournament engine.
        
        Args:
            database: Database interface for storing tournament data
        """
        self.database = database
        self.bracket_generator = BracketGenerator()
        self.evaluation_engine = EvaluationEngine()
        
        logger.info("TournamentEngine initialized")
    
    def create_tournament(self, name: str, participants: List[CodexObject],
                         tournament_type: TournamentType = TournamentType.SINGLE_ELIMINATION,
                         config: Dict[str, Any] = None) -> Tournament:
        """
        Create a new tournament.
        Implements Requirement 1.1 and 1.2.
        
        Args:
            name: Tournament name
            participants: List of CodexObjects to compete
            tournament_type: Type of tournament
            config: Tournament configuration
            
        Returns:
            Created tournament
        """
        try:
            if len(participants) < 2:
                raise ValueError("Tournament requires at least 2 participants")
            
            # Create tournament
            tournament = Tournament(
                name=name,
                tournament_type=tournament_type,
                participant_uuids=[obj.uuid for obj in participants],
                config=config or {}
            )
            
            # Generate bracket and matches
            bracket = self.bracket_generator.generate_bracket(participants, tournament_type)
            tournament.bracket = bracket
            tournament.matches = self._create_matches_from_bracket(tournament, bracket)
            
            # Save to database
            tournament_data = self._tournament_to_dict(tournament)
            success = self.database.save_tournament(tournament_data)
            
            if not success:
                raise RuntimeError("Failed to save tournament to database")
            
            logger.info(f"Created tournament '{name}' with {len(participants)} participants")
            return tournament
            
        except Exception as e:
            logger.error(f"Error creating tournament: {e}")
            raise
    
    def start_tournament(self, tournament: Tournament) -> bool:
        """
        Start a tournament.
        
        Args:
            tournament: Tournament to start
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if tournament.status != TournamentStatus.CREATED:
                logger.warning(f"Tournament {tournament.uuid} is not in CREATED status")
                return False
            
            tournament.status = TournamentStatus.STARTED
            tournament.started_timestamp = datetime.now().isoformat()
            
            # Save updated tournament
            tournament_data = self._tournament_to_dict(tournament)
            success = self.database.save_tournament(tournament_data)
            
            if success:
                logger.info(f"Started tournament {tournament.name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error starting tournament: {e}")
            return False
    
    def run_tournament(self, tournament: Tournament, 
                      participants: List[CodexObject]) -> Tournament:
        """
        Execute tournament matches and determine winners.
        Implements Requirement 1.3 and 1.4.
        
        Args:
            tournament: Tournament to run
            participants: List of participant CodexObjects
            
        Returns:
            Updated tournament with results
        """
        try:
            if tournament.status not in [TournamentStatus.CREATED, TournamentStatus.STARTED]:
                logger.warning(f"Tournament {tournament.uuid} cannot be run in status {tournament.status}")
                return tournament
            
            # Start tournament if not already started
            if tournament.status == TournamentStatus.CREATED:
                self.start_tournament(tournament)
            
            tournament.status = TournamentStatus.IN_PROGRESS
            
            # Create participant lookup
            participant_lookup = {obj.uuid: obj for obj in participants}
            
            # Run matches round by round
            current_round = 1
            max_rounds = tournament.round_count
            
            while current_round <= max_rounds:
                round_matches = tournament.get_matches_by_round(current_round)
                
                if not round_matches:
                    break
                
                logger.info(f"Running round {current_round} with {len(round_matches)} matches")
                
                # Execute all matches in this round
                for match in round_matches:
                    if not match.is_completed:
                        self._execute_match(match, participant_lookup, tournament)
                
                # Check if all matches in round are completed
                completed_matches = [m for m in round_matches if m.is_completed]
                if len(completed_matches) != len(round_matches):
                    logger.error(f"Not all matches in round {current_round} completed")
                    break
                
                current_round += 1
            
            # Complete tournament
            self._complete_tournament(tournament, participant_lookup)
            
            # Save final tournament state
            tournament_data = self._tournament_to_dict(tournament)
            self.database.save_tournament(tournament_data)
            
            logger.info(f"Tournament {tournament.name} completed")
            return tournament
            
        except Exception as e:
            logger.error(f"Error running tournament: {e}")
            tournament.status = TournamentStatus.CANCELLED
            return tournament
    
    def get_tournament_results(self, tournament: Tournament) -> Dict[str, Any]:
        """
        Get formatted tournament results.
        Implements Requirement 1.5 and 1.6.
        
        Args:
            tournament: Tournament to get results for
            
        Returns:
            Formatted results dictionary
        """
        try:
            if not tournament.is_completed:
                return {
                    "tournament_uuid": tournament.uuid,
                    "tournament_name": tournament.name,
                    "status": tournament.status.value,
                    "completed": False,
                    "message": "Tournament not yet completed"
                }
            
            # Generate bracket summary with round names
            bracket_summary = self._generate_bracket_summary(tournament)
            
            # Compile match results
            match_results = []
            for match in tournament.matches:
                if match.evaluation:
                    match_results.append({
                        "round": match.round_number,
                        "match": match.match_number,
                        "participants": [match.object1_uuid, match.object2_uuid],
                        "winner": match.winner_uuid,
                        "evaluation": match.evaluation.to_dict() if hasattr(match.evaluation, 'to_dict') else str(match.evaluation)
                    })
            
            # Generate rankings
            rankings = self._generate_rankings(tournament)
            
            return {
                "tournament_uuid": tournament.uuid,
                "tournament_name": tournament.name,
                "tournament_type": tournament.tournament_type.value,
                "status": tournament.status.value,
                "completed": True,
                "participant_count": tournament.participant_count,
                "round_count": tournament.round_count,
                "winner": tournament.get_winner(),
                "bracket_summary": bracket_summary,
                "match_results": match_results,
                "rankings": rankings,
                "started_at": tournament.started_timestamp,
                "completed_at": tournament.completed_timestamp
            }
            
        except Exception as e:
            logger.error(f"Error getting tournament results: {e}")
            return {
                "tournament_uuid": tournament.uuid,
                "error": str(e)
            }
    
    def _create_matches_from_bracket(self, tournament: Tournament, 
                                   bracket: TournamentBracket) -> List[TournamentMatch]:
        """Create tournament matches from bracket structure."""
        matches = []
        
        for round_num, round_matches in enumerate(bracket.rounds, 1):
            for match_num, (obj1_uuid, obj2_uuid) in enumerate(round_matches, 1):
                match = TournamentMatch(
                    tournament_uuid=tournament.uuid,
                    round_number=round_num,
                    match_number=match_num,
                    object1_uuid=obj1_uuid,
                    object2_uuid=obj2_uuid
                )
                matches.append(match)
        
        return matches
    
    def _execute_match(self, match: TournamentMatch, 
                      participant_lookup: Dict[str, CodexObject],
                      tournament: Tournament):
        """Execute a single tournament match."""
        try:
            obj1 = participant_lookup.get(match.object1_uuid)
            obj2 = participant_lookup.get(match.object2_uuid)
            
            if not obj1 or not obj2:
                logger.error(f"Missing participants for match {match.uuid}")
                return
            
            # Get evaluation criteria from tournament config
            evaluation_criteria = tournament.config.get("evaluation_criteria", {
                "originality": 0.3,
                "marketability": 0.3,
                "execution_potential": 0.2,
                "emotional_impact": 0.2
            })
            
            # Evaluate match
            evaluation = self.evaluation_engine.evaluate_match(obj1, obj2, evaluation_criteria)
            
            if evaluation and evaluation.winner_uuid:
                match.complete_match(evaluation.winner_uuid, evaluation)
                logger.info(f"Match completed: {match.uuid}, winner: {evaluation.winner_uuid}")
            else:
                logger.error(f"Failed to evaluate match {match.uuid}")
                
        except Exception as e:
            logger.error(f"Error executing match {match.uuid}: {e}")
    
    def _complete_tournament(self, tournament: Tournament, 
                           participant_lookup: Dict[str, CodexObject]):
        """Complete tournament and determine final results."""
        try:
            tournament.status = TournamentStatus.COMPLETED
            tournament.completed_timestamp = datetime.now().isoformat()
            
            # Determine winner (winner of final match)
            if tournament.tournament_type == TournamentType.SINGLE_ELIMINATION:
                final_matches = tournament.get_matches_by_round(tournament.round_count)
                if final_matches and final_matches[0].is_completed:
                    winner_uuid = final_matches[0].winner_uuid
                    tournament.results["winner_uuid"] = winner_uuid
                    
                    # Get winner object for additional info
                    winner_obj = participant_lookup.get(winner_uuid)
                    if winner_obj:
                        tournament.results["winner_title"] = winner_obj.title
                        tournament.results["winner_type"] = winner_obj.object_type.value
            
            # Calculate additional statistics
            tournament.results["total_matches"] = len(tournament.matches)
            tournament.results["completed_matches"] = len(tournament.get_completed_matches())
            tournament.results["tournament_duration"] = self._calculate_duration(
                tournament.started_timestamp, tournament.completed_timestamp
            )
            
        except Exception as e:
            logger.error(f"Error completing tournament: {e}")
    
    def _generate_bracket_summary(self, tournament: Tournament) -> Dict[str, Any]:
        """Generate readable bracket summary with round names."""
        try:
            round_names = self._get_round_names(tournament.round_count, tournament.participant_count)
            
            bracket_summary = {
                "rounds": {},
                "round_names": round_names
            }
            
            for round_num in range(1, tournament.round_count + 1):
                round_matches = tournament.get_matches_by_round(round_num)
                round_name = round_names.get(round_num, f"Round {round_num}")
                
                bracket_summary["rounds"][round_name] = []
                
                for match in round_matches:
                    match_info = {
                        "match_number": match.match_number,
                        "participants": [match.object1_uuid, match.object2_uuid],
                        "winner": match.winner_uuid,
                        "completed": match.is_completed
                    }
                    bracket_summary["rounds"][round_name].append(match_info)
            
            return bracket_summary
            
        except Exception as e:
            logger.error(f"Error generating bracket summary: {e}")
            return {}
    
    def _get_round_names(self, round_count: int, participant_count: int) -> Dict[int, str]:
        """Get appropriate round names based on tournament size."""
        if round_count <= 1:
            return {1: "Final"}
        elif round_count == 2:
            return {1: "Semifinal", 2: "Final"}
        elif round_count == 3:
            return {1: "Quarterfinal", 2: "Semifinal", 3: "Final"}
        elif round_count == 4:
            return {1: "Round of 16", 2: "Quarterfinal", 3: "Semifinal", 4: "Final"}
        elif round_count == 5:
            return {1: "Round of 32", 2: "Round of 16", 3: "Quarterfinal", 4: "Semifinal", 5: "Final"}
        else:
            # Generic naming for larger tournaments
            names = {}
            for i in range(1, round_count + 1):
                if i == round_count:
                    names[i] = "Final"
                elif i == round_count - 1:
                    names[i] = "Semifinal"
                elif i == round_count - 2:
                    names[i] = "Quarterfinal"
                else:
                    names[i] = f"Round {i}"
            return names
    
    def _generate_rankings(self, tournament: Tournament) -> List[Dict[str, Any]]:
        """Generate participant rankings based on tournament performance."""
        try:
            # For single elimination, ranking is based on how far each participant got
            participant_performance = {}
            
            # Initialize all participants
            for uuid in tournament.participant_uuids:
                participant_performance[uuid] = {
                    "uuid": uuid,
                    "wins": 0,
                    "losses": 0,
                    "rounds_reached": 0,
                    "eliminated_in_round": 0
                }
            
            # Analyze matches to determine performance
            for match in tournament.get_completed_matches():
                winner_uuid = match.winner_uuid
                loser_uuid = match.object2_uuid if winner_uuid == match.object1_uuid else match.object1_uuid
                
                if winner_uuid in participant_performance:
                    participant_performance[winner_uuid]["wins"] += 1
                    participant_performance[winner_uuid]["rounds_reached"] = max(
                        participant_performance[winner_uuid]["rounds_reached"], 
                        match.round_number
                    )
                
                if loser_uuid in participant_performance:
                    participant_performance[loser_uuid]["losses"] += 1
                    if participant_performance[loser_uuid]["eliminated_in_round"] == 0:
                        participant_performance[loser_uuid]["eliminated_in_round"] = match.round_number
            
            # Sort by performance (rounds reached, then wins, then losses)
            rankings = sorted(
                participant_performance.values(),
                key=lambda x: (x["rounds_reached"], x["wins"], -x["losses"]),
                reverse=True
            )
            
            # Add ranking positions
            for i, participant in enumerate(rankings, 1):
                participant["rank"] = i
            
            return rankings
            
        except Exception as e:
            logger.error(f"Error generating rankings: {e}")
            return []
    
    def _calculate_duration(self, start_time: Optional[str], end_time: Optional[str]) -> Optional[str]:
        """Calculate tournament duration."""
        try:
            if not start_time or not end_time:
                return None
            
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            duration = end_dt - start_dt
            
            return str(duration)
            
        except Exception as e:
            logger.error(f"Error calculating duration: {e}")
            return None
    
    def _tournament_to_dict(self, tournament: Tournament) -> Dict[str, Any]:
        """Convert Tournament to dictionary for database storage."""
        return {
            "uuid": tournament.uuid,
            "name": tournament.name,
            "tournament_type": tournament.tournament_type.value,
            "status": tournament.status.value,
            "config": tournament.config,
            "results": tournament.results,
            "created_timestamp": tournament.created_timestamp,
            "started_timestamp": tournament.started_timestamp,
            "completed_timestamp": tournament.completed_timestamp,
            "participant_count": tournament.participant_count,
            "round_count": tournament.round_count
        }
    
    def get_active_tournaments(self) -> Dict[str, Tournament]:
        """Get all active tournaments."""
        try:
            # Query database for active tournaments
            query = """
            SELECT * FROM tournaments 
            WHERE status IN ('created', 'started', 'in_progress')
            ORDER BY created_timestamp DESC
            """
            
            with self.database.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                
                active_tournaments = {}
                for row in rows:
                    tournament_data = dict(row)
                    tournament = self._dict_to_tournament(tournament_data)
                    if tournament:
                        active_tournaments[tournament.uuid] = tournament
                
                return active_tournaments
                
        except Exception as e:
            logger.error(f"Error getting active tournaments: {e}")
            return {}
    
    def get_tournament_history(self) -> List[Dict[str, Any]]:
        """Get tournament history."""
        try:
            # Query database for completed tournaments
            query = """
            SELECT * FROM tournaments 
            WHERE status = 'completed'
            ORDER BY completed_timestamp DESC
            LIMIT 50
            """
            
            with self.database.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                
                history = []
                for row in rows:
                    tournament_data = dict(row)
                    history.append({
                        'tournament_id': tournament_data.get('uuid'),
                        'name': tournament_data.get('name'),
                        'total_participants': tournament_data.get('participant_count', 0),
                        'winner': tournament_data.get('winner_uuid'),
                        'completed_timestamp': tournament_data.get('completed_timestamp'),
                        'duration': tournament_data.get('duration')
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Error getting tournament history: {e}")
            return []

    def load_tournament(self, tournament_uuid: str) -> Optional[Tournament]:
        """Load tournament from database."""
        try:
            tournament_data = self.database.load_tournament(tournament_uuid)
            if not tournament_data:
                return None
            
            # Convert back to Tournament object
            tournament = Tournament(
                uuid=tournament_data["uuid"],
                name=tournament_data["name"],
                tournament_type=TournamentType(tournament_data["tournament_type"]),
                status=TournamentStatus(tournament_data["status"]),
                config=tournament_data.get("config", {}),
                results=tournament_data.get("results", {}),
                created_timestamp=tournament_data["created_timestamp"],
                started_timestamp=tournament_data.get("started_timestamp"),
                completed_timestamp=tournament_data.get("completed_timestamp")
            )
            
            # Note: This is a simplified load - in a full implementation,
            # we would also load matches and bracket data
            
            return tournament
            
        except Exception as e:
            logger.error(f"Error loading tournament {tournament_uuid}: {e}")
            return None
    
    def _dict_to_tournament(self, tournament_data: Dict[str, Any]) -> Optional[Tournament]:
        """Convert dictionary data to Tournament object."""
        try:
            tournament = Tournament(
                uuid=tournament_data["uuid"],
                name=tournament_data["name"],
                tournament_type=TournamentType(tournament_data["tournament_type"]),
                status=TournamentStatus(tournament_data["status"]),
                config=tournament_data.get("config", {}),
                results=tournament_data.get("results", {}),
                created_timestamp=tournament_data["created_timestamp"],
                started_timestamp=tournament_data.get("started_timestamp"),
                completed_timestamp=tournament_data.get("completed_timestamp")
            )
            return tournament
        except Exception as e:
            logger.error(f"Error converting dict to tournament: {e}")
            return None
    
    def execute_tournament(self, tournament_uuid: str) -> Dict[str, Any]:
        """Execute a tournament by UUID and return results."""
        try:
            # Load tournament
            tournament = self.load_tournament(tournament_uuid)
            if not tournament:
                logger.error(f"Tournament {tournament_uuid} not found")
                return {}
            
            # For now, return mock results since we need participants
            # In a full implementation, we would load participants and run the tournament
            results = {
                'tournament_id': tournament_uuid,
                'status': 'completed',
                'winner': None,
                'participants': [],
                'rounds': []
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing tournament {tournament_uuid}: {e}")
            return {}
    
    def get_tournament_statistics(self) -> Dict[str, Any]:
        """Get tournament statistics for dashboard display."""
        try:
            stats = {
                "active_tournaments": 0,
                "completed_tournaments": 0,
                "total_tournaments": 0,
                "total_participants": 0
            }
            
            # Query for tournament counts
            with self.database.db.get_connection() as conn:
                # Count active tournaments
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM tournaments 
                    WHERE status IN ('created', 'started', 'in_progress')
                """)
                stats["active_tournaments"] = cursor.fetchone()[0]
                
                # Count completed tournaments
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM tournaments 
                    WHERE status = 'completed'
                """)
                stats["completed_tournaments"] = cursor.fetchone()[0]
                
                # Count total tournaments
                cursor = conn.execute("SELECT COUNT(*) FROM tournaments")
                stats["total_tournaments"] = cursor.fetchone()[0]
                
                # Sum total participants
                cursor = conn.execute("SELECT SUM(participant_count) FROM tournaments")
                result = cursor.fetchone()[0]
                stats["total_participants"] = result if result else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting tournament statistics: {e}")
            return {
                "active_tournaments": 0,
                "completed_tournaments": 0,
                "total_tournaments": 0,
                "total_participants": 0
            }
    
    def get_completed_tournaments(self, limit: int = 10) -> List[Tournament]:
        """Get recently completed tournaments."""
        try:
            with self.database.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM tournaments 
                    WHERE status = 'completed'
                    ORDER BY completed_timestamp DESC
                    LIMIT ?
                """, (limit,))
                
                tournaments = []
                for row in cursor.fetchall():
                    tournament_data = dict(row)
                    tournament = self._dict_to_tournament(tournament_data)
                    if tournament:
                        tournaments.append(tournament)
                
                return tournaments
                
        except Exception as e:
            logger.error(f"Error getting completed tournaments: {e}")
            return []