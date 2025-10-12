"""
Unit tests for TournamentResultsManager.
"""

import pytest
import tempfile
from unittest.mock import Mock, patch

from codexes.modules.ideation.tournament.results_manager import TournamentResultsManager
from codexes.modules.ideation.tournament.tournament_engine import (
    Tournament, TournamentMatch, TournamentType, TournamentStatus
)
from codexes.modules.ideation.tournament.evaluation_engine import MatchEvaluation
from codexes.modules.ideation.core.codex_object import CodexObject, CodexObjectType
from codexes.modules.ideation.storage.database_manager import DatabaseManager, IdeationDatabase
from codexes.modules.ideation.storage.file_manager import IdeationFileManager


class TestTournamentResultsManager:
    """Test cases for TournamentResultsManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary database and file manager
        self.temp_dir = tempfile.mkdtemp()
        db_path = f"{self.temp_dir}/test_results.db"
        self.db_manager = DatabaseManager(db_path)
        self.database = IdeationDatabase(self.db_manager)
        self.file_manager = IdeationFileManager(f"{self.temp_dir}/files")
        self.results_manager = TournamentResultsManager(self.database, self.file_manager)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_results_manager_initialization(self):
        """Test results manager initialization."""
        assert self.results_manager.database is not None
        assert self.results_manager.file_manager is not None
    
    def test_save_tournament_results_incomplete(self):
        """Test saving results for incomplete tournament."""
        tournament = Tournament(
            name="Incomplete Tournament",
            status=TournamentStatus.IN_PROGRESS
        )
        
        participants = [
            CodexObject(title="Test 1", object_type=CodexObjectType.IDEA),
            CodexObject(title="Test 2", object_type=CodexObjectType.IDEA)
        ]
        
        success = self.results_manager.save_tournament_results(tournament, participants)
        assert success is False
    
    def test_save_tournament_results_complete(self):
        """Test saving results for completed tournament."""
        # Create completed tournament
        tournament = Tournament(
            name="Complete Tournament",
            tournament_type=TournamentType.SINGLE_ELIMINATION,
            status=TournamentStatus.COMPLETED,
            participant_uuids=["uuid1", "uuid2"]
        )
        
        # Add completed match
        match = TournamentMatch(
            tournament_uuid=tournament.uuid,
            round_number=1,
            match_number=1,
            object1_uuid="uuid1",
            object2_uuid="uuid2"
        )
        
        evaluation = MatchEvaluation(
            winner_uuid="uuid1",
            loser_uuid="uuid2",
            reasoning="Test evaluation"
        )
        
        match.complete_match("uuid1", evaluation)
        tournament.matches = [match]
        tournament.results = {"winner_uuid": "uuid1"}
        
        participants = [
            CodexObject(uuid="uuid1", title="Winner", object_type=CodexObjectType.IDEA),
            CodexObject(uuid="uuid2", title="Runner-up", object_type=CodexObjectType.IDEA)
        ]
        
        success = self.results_manager.save_tournament_results(tournament, participants)
        assert success is True
    
    def test_load_tournament_results(self):
        """Test loading tournament results."""
        # First save a tournament
        tournament = Tournament(
            name="Load Test Tournament",
            tournament_type=TournamentType.SINGLE_ELIMINATION,
            status=TournamentStatus.COMPLETED
        )
        
        participants = [
            CodexObject(title="Test 1", object_type=CodexObjectType.IDEA),
            CodexObject(title="Test 2", object_type=CodexObjectType.IDEA)
        ]
        
        self.results_manager.save_tournament_results(tournament, participants)
        
        # Load the results
        loaded_results = self.results_manager.load_tournament_results(tournament.uuid)
        
        assert loaded_results is not None
        assert loaded_results["name"] == "Load Test Tournament"
        assert loaded_results["tournament_type"] == "single_elimination"
    
    def test_load_tournament_results_not_found(self):
        """Test loading results for non-existent tournament."""
        results = self.results_manager.load_tournament_results("non-existent-uuid")
        assert results is None
    
    def test_export_results_json(self):
        """Test exporting results to JSON."""
        # Create and save tournament
        tournament = Tournament(
            name="JSON Export Test",
            tournament_type=TournamentType.SINGLE_ELIMINATION,
            status=TournamentStatus.COMPLETED
        )
        
        participants = [
            CodexObject(title="JSON Test 1", object_type=CodexObjectType.IDEA),
            CodexObject(title="JSON Test 2", object_type=CodexObjectType.IDEA)
        ]
        
        self.results_manager.save_tournament_results(tournament, participants)
        
        # Export to JSON
        export_path = self.results_manager.export_results_json(tournament.uuid)
        
        assert export_path is not None
        assert export_path.endswith('.json')
        
        # Verify file exists
        from pathlib import Path
        assert Path(export_path).exists()
    
    def test_export_results_csv(self):
        """Test exporting results to CSV."""
        # Create and save tournament
        tournament = Tournament(
            name="CSV Export Test",
            tournament_type=TournamentType.SINGLE_ELIMINATION,
            status=TournamentStatus.COMPLETED
        )
        
        participants = [
            CodexObject(title="CSV Test 1", object_type=CodexObjectType.IDEA),
            CodexObject(title="CSV Test 2", object_type=CodexObjectType.IDEA)
        ]
        
        self.results_manager.save_tournament_results(tournament, participants)
        
        # Export to CSV
        export_path = self.results_manager.export_results_csv(tournament.uuid)
        
        assert export_path is not None
        assert export_path.endswith('.csv')
        
        # Verify file exists
        from pathlib import Path
        assert Path(export_path).exists()
    
    def test_generate_bracket_summary(self):
        """Test generating bracket summary."""
        # Create tournament with matches
        tournament = Tournament(
            name="Bracket Summary Test",
            tournament_type=TournamentType.SINGLE_ELIMINATION,
            status=TournamentStatus.COMPLETED,
            participant_uuids=["uuid1", "uuid2", "uuid3", "uuid4"]
        )
        
        # Add matches
        match1 = TournamentMatch(
            tournament_uuid=tournament.uuid,
            round_number=1,
            match_number=1,
            object1_uuid="uuid1",
            object2_uuid="uuid2"
        )
        match1.complete_match("uuid1", MatchEvaluation("uuid1", "uuid2", "Test"))
        
        match2 = TournamentMatch(
            tournament_uuid=tournament.uuid,
            round_number=1,
            match_number=2,
            object1_uuid="uuid3",
            object2_uuid="uuid4"
        )
        match2.complete_match("uuid3", MatchEvaluation("uuid3", "uuid4", "Test"))
        
        final_match = TournamentMatch(
            tournament_uuid=tournament.uuid,
            round_number=2,
            match_number=1,
            object1_uuid="uuid1",
            object2_uuid="uuid3"
        )
        final_match.complete_match("uuid1", MatchEvaluation("uuid1", "uuid3", "Final"))
        
        tournament.matches = [match1, match2, final_match]
        tournament.results = {"winner_uuid": "uuid1"}
        
        participants = [
            CodexObject(uuid="uuid1", title="Winner", object_type=CodexObjectType.IDEA),
            CodexObject(uuid="uuid2", title="Semi 1", object_type=CodexObjectType.IDEA),
            CodexObject(uuid="uuid3", title="Semi 2", object_type=CodexObjectType.IDEA),
            CodexObject(uuid="uuid4", title="Quarter", object_type=CodexObjectType.IDEA)
        ]
        
        # Save tournament
        self.results_manager.save_tournament_results(tournament, participants)
        
        # Generate bracket summary
        bracket_summary = self.results_manager.generate_bracket_summary(tournament.uuid)
        
        assert bracket_summary is not None
        assert bracket_summary["tournament_name"] == "Bracket Summary Test"
        assert bracket_summary["winner"] == "uuid1"
        assert "rounds" in bracket_summary
        assert "round_names" in bracket_summary
        assert bracket_summary["round_count"] == 2
    
    def test_get_tournament_statistics(self):
        """Test getting tournament statistics."""
        # Create tournament with data
        tournament = Tournament(
            name="Statistics Test",
            tournament_type=TournamentType.SINGLE_ELIMINATION,
            status=TournamentStatus.COMPLETED,
            participant_uuids=["uuid1", "uuid2"]
        )
        
        participants = [
            CodexObject(uuid="uuid1", title="Stats 1", object_type=CodexObjectType.IDEA),
            CodexObject(uuid="uuid2", title="Stats 2", object_type=CodexObjectType.IDEA)
        ]
        
        self.results_manager.save_tournament_results(tournament, participants)
        
        # Get statistics
        stats = self.results_manager.get_tournament_statistics(tournament.uuid)
        
        assert stats is not None
        assert "tournament_info" in stats
        assert "match_statistics" in stats
        assert "participant_statistics" in stats
        assert "evaluation_statistics" in stats
        assert stats["tournament_info"]["name"] == "Statistics Test"
    
    def test_compare_tournaments(self):
        """Test comparing multiple tournaments."""
        # Create two tournaments
        tournament1 = Tournament(
            name="Compare Test 1",
            tournament_type=TournamentType.SINGLE_ELIMINATION,
            status=TournamentStatus.COMPLETED,
            participant_uuids=["uuid1", "uuid2"]
        )
        
        tournament2 = Tournament(
            name="Compare Test 2",
            tournament_type=TournamentType.ROUND_ROBIN,
            status=TournamentStatus.COMPLETED,
            participant_uuids=["uuid3", "uuid4", "uuid5"]
        )
        
        participants1 = [
            CodexObject(uuid="uuid1", title="T1 P1", object_type=CodexObjectType.IDEA),
            CodexObject(uuid="uuid2", title="T1 P2", object_type=CodexObjectType.IDEA)
        ]
        
        participants2 = [
            CodexObject(uuid="uuid3", title="T2 P1", object_type=CodexObjectType.IDEA),
            CodexObject(uuid="uuid4", title="T2 P2", object_type=CodexObjectType.IDEA),
            CodexObject(uuid="uuid5", title="T2 P3", object_type=CodexObjectType.IDEA)
        ]
        
        # Save tournaments
        self.results_manager.save_tournament_results(tournament1, participants1)
        self.results_manager.save_tournament_results(tournament2, participants2)
        
        # Compare tournaments
        comparison = self.results_manager.compare_tournaments([tournament1.uuid, tournament2.uuid])
        
        assert "tournaments" in comparison
        assert "comparison_metrics" in comparison
        assert len(comparison["tournaments"]) == 2
        assert comparison["comparison_metrics"]["total_tournaments"] == 2
        assert comparison["comparison_metrics"]["average_participant_count"] == 2.5  # (2+3)/2


class TestResultsManagerIntegration:
    """Integration tests for results manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        db_path = f"{self.temp_dir}/test_integration.db"
        self.db_manager = DatabaseManager(db_path)
        self.database = IdeationDatabase(self.db_manager)
        self.file_manager = IdeationFileManager(f"{self.temp_dir}/files")
        self.results_manager = TournamentResultsManager(self.database, self.file_manager)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_full_results_workflow(self):
        """Test complete results management workflow."""
        # Create comprehensive tournament
        tournament = Tournament(
            name="Full Workflow Test",
            tournament_type=TournamentType.SINGLE_ELIMINATION,
            status=TournamentStatus.COMPLETED,
            participant_uuids=["uuid1", "uuid2", "uuid3", "uuid4"]
        )
        
        # Create detailed matches with evaluations
        matches = []
        
        # Semifinal 1
        match1 = TournamentMatch(
            tournament_uuid=tournament.uuid,
            round_number=1,
            match_number=1,
            object1_uuid="uuid1",
            object2_uuid="uuid2"
        )
        evaluation1 = MatchEvaluation(
            winner_uuid="uuid1",
            loser_uuid="uuid2",
            reasoning="Strong concept and execution",
            scores={
                "uuid1": {"originality": 8, "marketability": 7, "total": 15},
                "uuid2": {"originality": 6, "marketability": 8, "total": 14}
            },
            confidence_score=0.85
        )
        match1.complete_match("uuid1", evaluation1)
        matches.append(match1)
        
        # Semifinal 2
        match2 = TournamentMatch(
            tournament_uuid=tournament.uuid,
            round_number=1,
            match_number=2,
            object1_uuid="uuid3",
            object2_uuid="uuid4"
        )
        evaluation2 = MatchEvaluation(
            winner_uuid="uuid3",
            loser_uuid="uuid4",
            reasoning="Better market appeal",
            scores={
                "uuid3": {"originality": 7, "marketability": 9, "total": 16},
                "uuid4": {"originality": 9, "marketability": 5, "total": 14}
            },
            confidence_score=0.75
        )
        match2.complete_match("uuid3", evaluation2)
        matches.append(match2)
        
        # Final
        final_match = TournamentMatch(
            tournament_uuid=tournament.uuid,
            round_number=2,
            match_number=1,
            object1_uuid="uuid1",
            object2_uuid="uuid3"
        )
        final_evaluation = MatchEvaluation(
            winner_uuid="uuid1",
            loser_uuid="uuid3",
            reasoning="Overall superior concept",
            scores={
                "uuid1": {"originality": 9, "marketability": 8, "total": 17},
                "uuid3": {"originality": 7, "marketability": 8, "total": 15}
            },
            confidence_score=0.9
        )
        final_match.complete_match("uuid1", final_evaluation)
        matches.append(final_match)
        
        tournament.matches = matches
        tournament.results = {"winner_uuid": "uuid1"}
        
        # Create participants
        participants = [
            CodexObject(uuid="uuid1", title="Champion Idea", object_type=CodexObjectType.SYNOPSIS, genre="Fantasy"),
            CodexObject(uuid="uuid2", title="Runner-up Idea", object_type=CodexObjectType.SYNOPSIS, genre="Mystery"),
            CodexObject(uuid="uuid3", title="Third Place Idea", object_type=CodexObjectType.SYNOPSIS, genre="Romance"),
            CodexObject(uuid="uuid4", title="Fourth Place Idea", object_type=CodexObjectType.SYNOPSIS, genre="Sci-Fi")
        ]
        
        # Execute full workflow
        
        # 1. Save results
        save_success = self.results_manager.save_tournament_results(tournament, participants)
        assert save_success is True
        
        # 2. Load results
        loaded_results = self.results_manager.load_tournament_results(tournament.uuid)
        assert loaded_results is not None
        assert loaded_results["name"] == "Full Workflow Test"
        
        # 3. Generate bracket summary
        bracket_summary = self.results_manager.generate_bracket_summary(tournament.uuid)
        assert bracket_summary is not None
        assert bracket_summary["winner"] == "uuid1"
        assert "Semifinal" in bracket_summary["round_names"].values()
        assert "Final" in bracket_summary["round_names"].values()
        
        # 4. Get statistics
        stats = self.results_manager.get_tournament_statistics(tournament.uuid)
        assert stats is not None
        assert stats["tournament_info"]["total_matches"] == 3
        assert stats["tournament_info"]["participant_count"] == 4
        
        # 5. Export to JSON
        json_path = self.results_manager.export_results_json(tournament.uuid, include_detailed_scores=True)
        assert json_path is not None
        
        # Verify JSON content
        import json
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        
        assert json_data["tournament_info"]["name"] == "Full Workflow Test"
        assert json_data["results"]["winner"] == "uuid1"
        assert len(json_data["results"]["match_results"]) == 3
        
        # 6. Export to CSV
        csv_path = self.results_manager.export_results_csv(tournament.uuid)
        assert csv_path is not None
        
        # Verify CSV content
        import csv
        with open(csv_path, 'r') as f:
            csv_reader = csv.DictReader(f)
            rows = list(csv_reader)
        
        assert len(rows) > 0
        tournament_info_row = next((row for row in rows if row["Type"] == "Tournament Info"), None)
        assert tournament_info_row is not None
        assert tournament_info_row["Name"] == "Full Workflow Test"