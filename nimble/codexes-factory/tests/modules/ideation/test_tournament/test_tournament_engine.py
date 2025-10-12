"""
Unit tests for TournamentEngine.
"""

import pytest
import tempfile
from unittest.mock import Mock, patch

from codexes.modules.ideation.tournament.tournament_engine import (
    TournamentEngine, Tournament, TournamentMatch, TournamentType, TournamentStatus
)
from codexes.modules.ideation.tournament.evaluation_engine import MatchEvaluation
from codexes.modules.ideation.core.codex_object import CodexObject, CodexObjectType
from codexes.modules.ideation.storage.database_manager import DatabaseManager, IdeationDatabase


class TestTournamentEngine:
    """Test cases for TournamentEngine class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary database
        self.temp_dir = tempfile.mkdtemp()
        db_path = f"{self.temp_dir}/test_tournament.db"
        self.db_manager = DatabaseManager(db_path)
        self.database = IdeationDatabase(self.db_manager)
        self.tournament_engine = TournamentEngine(self.database)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_tournament_engine_initialization(self):
        """Test tournament engine initialization."""
        assert self.tournament_engine.database is not None
        assert self.tournament_engine.bracket_generator is not None
        assert self.tournament_engine.evaluation_engine is not None
    
    def test_create_tournament_basic(self):
        """Test basic tournament creation."""
        # Create test participants
        participants = [
            CodexObject(title="Idea 1", content="First test idea", object_type=CodexObjectType.IDEA),
            CodexObject(title="Idea 2", content="Second test idea", object_type=CodexObjectType.IDEA),
            CodexObject(title="Idea 3", content="Third test idea", object_type=CodexObjectType.IDEA),
            CodexObject(title="Idea 4", content="Fourth test idea", object_type=CodexObjectType.IDEA)
        ]
        
        # Create tournament
        tournament = self.tournament_engine.create_tournament(
            name="Test Tournament",
            participants=participants,
            tournament_type=TournamentType.SINGLE_ELIMINATION
        )
        
        # Verify tournament properties
        assert tournament.name == "Test Tournament"
        assert tournament.tournament_type == TournamentType.SINGLE_ELIMINATION
        assert tournament.status == TournamentStatus.CREATED
        assert tournament.participant_count == 4
        assert len(tournament.participant_uuids) == 4
        assert tournament.bracket is not None
        assert len(tournament.matches) > 0
    
    def test_create_tournament_insufficient_participants(self):
        """Test tournament creation with insufficient participants."""
        participants = [
            CodexObject(title="Only One", content="Single participant", object_type=CodexObjectType.IDEA)
        ]
        
        with pytest.raises(ValueError, match="at least 2 participants"):
            self.tournament_engine.create_tournament("Invalid Tournament", participants)
    
    def test_start_tournament(self):
        """Test starting a tournament."""
        participants = [
            CodexObject(title="Idea 1", content="First idea", object_type=CodexObjectType.IDEA),
            CodexObject(title="Idea 2", content="Second idea", object_type=CodexObjectType.IDEA)
        ]
        
        tournament = self.tournament_engine.create_tournament("Start Test", participants)
        
        # Start tournament
        success = self.tournament_engine.start_tournament(tournament)
        
        assert success is True
        assert tournament.status == TournamentStatus.STARTED
        assert tournament.started_timestamp is not None
    
    def test_start_tournament_invalid_status(self):
        """Test starting tournament with invalid status."""
        participants = [
            CodexObject(title="Idea 1", content="First idea", object_type=CodexObjectType.IDEA),
            CodexObject(title="Idea 2", content="Second idea", object_type=CodexObjectType.IDEA)
        ]
        
        tournament = self.tournament_engine.create_tournament("Status Test", participants)
        tournament.status = TournamentStatus.COMPLETED  # Invalid status for starting
        
        success = self.tournament_engine.start_tournament(tournament)
        assert success is False
    
    @patch('codexes.modules.ideation.tournament.evaluation_engine.EvaluationEngine.evaluate_match')
    def test_run_tournament_success(self, mock_evaluate):
        """Test successful tournament execution."""
        # Create test participants
        participants = [
            CodexObject(title="Idea 1", content="First idea", object_type=CodexObjectType.IDEA),
            CodexObject(title="Idea 2", content="Second idea", object_type=CodexObjectType.IDEA),
            CodexObject(title="Idea 3", content="Third idea", object_type=CodexObjectType.IDEA),
            CodexObject(title="Idea 4", content="Fourth idea", object_type=CodexObjectType.IDEA)
        ]
        
        # Mock evaluation results
        def mock_evaluation_side_effect(obj1, obj2, criteria):
            # Always return obj1 as winner for predictable results
            return MatchEvaluation(
                winner_uuid=obj1.uuid,
                loser_uuid=obj2.uuid,
                reasoning="Mock evaluation - obj1 wins",
                scores={
                    obj1.uuid: {"originality": 8, "marketability": 7, "total": 15},
                    obj2.uuid: {"originality": 6, "marketability": 6, "total": 12}
                }
            )
        
        mock_evaluate.side_effect = mock_evaluation_side_effect
        
        # Create and run tournament
        tournament = self.tournament_engine.create_tournament("Run Test", participants)
        completed_tournament = self.tournament_engine.run_tournament(tournament, participants)
        
        # Verify tournament completion
        assert completed_tournament.status == TournamentStatus.COMPLETED
        assert completed_tournament.completed_timestamp is not None
        assert completed_tournament.get_winner() is not None
        
        # Verify all matches were completed
        completed_matches = completed_tournament.get_completed_matches()
        assert len(completed_matches) == len(completed_tournament.matches)
    
    def test_get_tournament_results_incomplete(self):
        """Test getting results for incomplete tournament."""
        participants = [
            CodexObject(title="Idea 1", content="First idea", object_type=CodexObjectType.IDEA),
            CodexObject(title="Idea 2", content="Second idea", object_type=CodexObjectType.IDEA)
        ]
        
        tournament = self.tournament_engine.create_tournament("Incomplete Test", participants)
        results = self.tournament_engine.get_tournament_results(tournament)
        
        assert results["completed"] is False
        assert "not yet completed" in results["message"]
    
    @patch('codexes.modules.ideation.tournament.evaluation_engine.EvaluationEngine.evaluate_match')
    def test_get_tournament_results_complete(self, mock_evaluate):
        """Test getting results for completed tournament."""
        participants = [
            CodexObject(title="Winner", content="Winning idea", object_type=CodexObjectType.IDEA),
            CodexObject(title="Runner-up", content="Second place idea", object_type=CodexObjectType.IDEA)
        ]
        
        # Mock evaluation
        mock_evaluate.return_value = MatchEvaluation(
            winner_uuid=participants[0].uuid,
            loser_uuid=participants[1].uuid,
            reasoning="Winner has better concept",
            scores={
                participants[0].uuid: {"originality": 9, "total": 18},
                participants[1].uuid: {"originality": 7, "total": 14}
            }
        )
        
        # Create and run tournament
        tournament = self.tournament_engine.create_tournament("Results Test", participants)
        completed_tournament = self.tournament_engine.run_tournament(tournament, participants)
        
        # Get results
        results = self.tournament_engine.get_tournament_results(completed_tournament)
        
        assert results["completed"] is True
        assert results["winner"] == participants[0].uuid
        assert results["tournament_name"] == "Results Test"
        assert "bracket_summary" in results
        assert "match_results" in results
        assert "rankings" in results


class TestTournamentMatch:
    """Test cases for TournamentMatch class."""
    
    def test_tournament_match_creation(self):
        """Test tournament match creation."""
        match = TournamentMatch(
            tournament_uuid="tournament-123",
            round_number=1,
            match_number=1,
            object1_uuid="obj1",
            object2_uuid="obj2"
        )
        
        assert match.tournament_uuid == "tournament-123"
        assert match.round_number == 1
        assert match.match_number == 1
        assert match.object1_uuid == "obj1"
        assert match.object2_uuid == "obj2"
        assert match.is_completed is False
    
    def test_complete_match(self):
        """Test completing a match."""
        match = TournamentMatch(
            object1_uuid="obj1",
            object2_uuid="obj2"
        )
        
        evaluation = MatchEvaluation(
            winner_uuid="obj1",
            loser_uuid="obj2",
            reasoning="obj1 is better"
        )
        
        match.complete_match("obj1", evaluation)
        
        assert match.is_completed is True
        assert match.winner_uuid == "obj1"
        assert match.evaluation == evaluation
        assert match.completed_timestamp is not None


class TestTournament:
    """Test cases for Tournament class."""
    
    def test_tournament_creation(self):
        """Test tournament creation."""
        tournament = Tournament(
            name="Test Tournament",
            tournament_type=TournamentType.SINGLE_ELIMINATION,
            participant_uuids=["obj1", "obj2", "obj3", "obj4"]
        )
        
        assert tournament.name == "Test Tournament"
        assert tournament.tournament_type == TournamentType.SINGLE_ELIMINATION
        assert tournament.status == TournamentStatus.CREATED
        assert tournament.participant_count == 4
        assert tournament.is_completed is False
    
    def test_get_matches_by_round(self):
        """Test getting matches by round."""
        tournament = Tournament()
        
        # Add test matches
        match1 = TournamentMatch(round_number=1, match_number=1)
        match2 = TournamentMatch(round_number=1, match_number=2)
        match3 = TournamentMatch(round_number=2, match_number=1)
        
        tournament.matches = [match1, match2, match3]
        
        round1_matches = tournament.get_matches_by_round(1)
        round2_matches = tournament.get_matches_by_round(2)
        
        assert len(round1_matches) == 2
        assert len(round2_matches) == 1
        assert round1_matches[0].round_number == 1
        assert round2_matches[0].round_number == 2
    
    def test_get_completed_matches(self):
        """Test getting completed matches."""
        tournament = Tournament()
        
        # Create matches with different completion status
        completed_match = TournamentMatch(object1_uuid="obj1", object2_uuid="obj2")
        completed_match.complete_match("obj1", MatchEvaluation("obj1", "obj2", "test"))
        
        pending_match = TournamentMatch(object1_uuid="obj3", object2_uuid="obj4")
        
        tournament.matches = [completed_match, pending_match]
        
        completed_matches = tournament.get_completed_matches()
        pending_matches = tournament.get_pending_matches()
        
        assert len(completed_matches) == 1
        assert len(pending_matches) == 1
        assert completed_matches[0].is_completed is True
        assert pending_matches[0].is_completed is False
    
    def test_get_winner(self):
        """Test getting tournament winner."""
        tournament = Tournament()
        
        # Tournament not completed
        assert tournament.get_winner() is None
        
        # Complete tournament with winner
        tournament.status = TournamentStatus.COMPLETED
        tournament.results = {"winner_uuid": "winner-123"}
        
        assert tournament.get_winner() == "winner-123"


class TestTournamentIntegration:
    """Integration tests for tournament system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        db_path = f"{self.temp_dir}/test_integration.db"
        self.db_manager = DatabaseManager(db_path)
        self.database = IdeationDatabase(self.db_manager)
        self.tournament_engine = TournamentEngine(self.database)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_tournament_persistence(self):
        """Test tournament persistence in database."""
        participants = [
            CodexObject(title="Persistent 1", content="First persistent idea", object_type=CodexObjectType.IDEA),
            CodexObject(title="Persistent 2", content="Second persistent idea", object_type=CodexObjectType.IDEA)
        ]
        
        # Create tournament
        tournament = self.tournament_engine.create_tournament("Persistence Test", participants)
        original_uuid = tournament.uuid
        
        # Load tournament from database
        loaded_tournament = self.tournament_engine.load_tournament(original_uuid)
        
        assert loaded_tournament is not None
        assert loaded_tournament.uuid == original_uuid
        assert loaded_tournament.name == "Persistence Test"
        assert loaded_tournament.tournament_type == TournamentType.SINGLE_ELIMINATION
    
    @patch('codexes.modules.ideation.tournament.evaluation_engine.EvaluationEngine.evaluate_match')
    def test_full_tournament_workflow(self, mock_evaluate):
        """Test complete tournament workflow."""
        # Create diverse participants
        participants = [
            CodexObject(title="Fantasy Epic", content="A grand fantasy adventure", object_type=CodexObjectType.SYNOPSIS, genre="Fantasy"),
            CodexObject(title="Sci-Fi Thriller", content="A thrilling space adventure", object_type=CodexObjectType.SYNOPSIS, genre="Science Fiction"),
            CodexObject(title="Mystery Novel", content="A complex murder mystery", object_type=CodexObjectType.SYNOPSIS, genre="Mystery"),
            CodexObject(title="Romance Story", content="A heartwarming love story", object_type=CodexObjectType.SYNOPSIS, genre="Romance")
        ]
        
        # Mock evaluations with varying results
        evaluation_results = [
            (participants[0].uuid, participants[1].uuid),  # Fantasy beats Sci-Fi
            (participants[2].uuid, participants[3].uuid),  # Mystery beats Romance
            (participants[0].uuid, participants[2].uuid)   # Fantasy beats Mystery (final)
        ]
        
        call_count = 0
        def mock_evaluation_side_effect(obj1, obj2, criteria):
            nonlocal call_count
            winner_uuid, loser_uuid = evaluation_results[call_count]
            call_count += 1
            
            return MatchEvaluation(
                winner_uuid=winner_uuid,
                loser_uuid=loser_uuid,
                reasoning=f"Mock evaluation {call_count}",
                scores={
                    winner_uuid: {"originality": 8, "marketability": 8, "total": 16},
                    loser_uuid: {"originality": 6, "marketability": 6, "total": 12}
                }
            )
        
        mock_evaluate.side_effect = mock_evaluation_side_effect
        
        # Run complete tournament
        tournament = self.tournament_engine.create_tournament(
            "Full Workflow Test", 
            participants,
            config={"evaluation_criteria": {"originality": 0.5, "marketability": 0.5}}
        )
        
        completed_tournament = self.tournament_engine.run_tournament(tournament, participants)
        results = self.tournament_engine.get_tournament_results(completed_tournament)
        
        # Verify complete workflow
        assert completed_tournament.status == TournamentStatus.COMPLETED
        assert results["completed"] is True
        assert results["winner"] == participants[0].uuid  # Fantasy Epic should win
        assert results["participant_count"] == 4
        assert len(results["match_results"]) == 3  # 3 matches total
        assert len(results["rankings"]) == 4  # All participants ranked