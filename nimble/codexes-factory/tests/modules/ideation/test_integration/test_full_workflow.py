#!/usr/bin/env python3
"""
Integration tests for complete ideation workflows.
Tests end-to-end functionality across all ideation modules.
"""

import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch
from pathlib import Path

from src.codexes.modules.ideation.core.codex_object import CodexObject
from src.codexes.modules.ideation.tournament.tournament_engine import TournamentEngine
from src.codexes.modules.ideation.synthetic_readers.reader_panel import SyntheticReaderPanel
from src.codexes.modules.ideation.series.series_generator import SeriesGenerator
from src.codexes.modules.ideation.elements.element_extractor import ElementExtractor
from src.codexes.modules.ideation.batch.batch_processor import BatchProcessor
from src.codexes.modules.ideation.performance.cache_manager import CacheManager
from src.codexes.modules.ideation.storage.database_manager import DatabaseManager


class TestFullIdeationWorkflow:
    """Test complete ideation workflow integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_ideation.db"
        
        # Initialize components
        self.db_manager = DatabaseManager(str(self.db_path))
        self.cache_manager = CacheManager()
        self.tournament_engine = TournamentEngine()
        self.reader_panel = SyntheticReaderPanel()
        self.series_generator = SeriesGenerator()
        self.element_extractor = ElementExtractor()
        self.batch_processor = BatchProcessor()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.codexes.modules.ideation.llm.ideation_llm_service.IdeationLLMService')
    def test_complete_tournament_workflow(self, mock_llm_service):
        """Test complete tournament workflow from creation to results."""
        # Mock LLM responses
        mock_llm_service.return_value.evaluate_tournament_match.return_value.success = True
        mock_llm_service.return_value.evaluate_tournament_match.return_value.parsed_data = {
            "winner": "concept_1",
            "reasoning": "Better plot structure",
            "confidence": 0.8
        }
        
        # Create test concepts
        concepts = []
        for i in range(4):
            concept = CodexObject(
                title=f"Test Concept {i+1}",
                premise=f"Premise for concept {i+1}",
                genre="fantasy",
                setting=f"Setting {i+1}",
                themes=[f"theme_{i+1}"],
                tone="adventurous"
            )
            concepts.append(concept)
        
        # Create and run tournament
        tournament = self.tournament_engine.create_tournament(
            concepts=concepts,
            tournament_name="Integration Test Tournament"
        )
        
        assert tournament is not None
        assert len(tournament.concepts) == 4
        
        # Execute tournament
        with patch('time.sleep'):  # Skip delays
            results = self.tournament_engine.execute_tournament(tournament.tournament_id)
        
        assert results is not None
        assert "winner" in results
        assert "bracket_results" in results
        assert len(results["bracket_results"]) > 0
    
    @patch('src.codexes.modules.ideation.llm.ideation_llm_service.IdeationLLMService')
    def test_synthetic_reader_evaluation_workflow(self, mock_llm_service):
        """Test synthetic reader panel evaluation workflow."""
        # Mock LLM responses for reader evaluation
        mock_llm_service.return_value.evaluate_with_reader_persona.return_value.success = True
        mock_llm_service.return_value.evaluate_with_reader_persona.return_value.parsed_data = {
            "appeal_score": 0.8,
            "reasoning": "Engaging plot and characters",
            "market_appeal": 0.7,
            "demographic_fit": 0.9
        }
        
        # Create test concept
        concept = CodexObject(
            title="Reader Test Concept",
            premise="A story designed for reader evaluation",
            genre="young adult",
            setting="Modern high school",
            themes=["coming of age", "friendship"],
            tone="optimistic"
        )
        
        # Create reader panel
        panel = self.reader_panel.create_diverse_panel(panel_size=6)
        assert len(panel) == 6
        
        # Evaluate concept with panel
        with patch('time.sleep'):  # Skip delays
            evaluation_results = self.reader_panel.evaluate_concept(concept, panel)
        
        assert evaluation_results is not None
        assert "overall_appeal" in evaluation_results
        assert "demographic_breakdown" in evaluation_results
        assert "consensus_patterns" in evaluation_results
        assert len(evaluation_results["individual_evaluations"]) == 6
    
    @patch('src.codexes.modules.ideation.llm.ideation_llm_service.IdeationLLMService')
    def test_series_generation_workflow(self, mock_llm_service):
        """Test series generation workflow."""
        # Mock LLM responses
        mock_llm_service.return_value.generate_series_name.return_value.success = True
        mock_llm_service.return_value.generate_series_name.return_value.parsed_data = {
            "series_name": "Integration Test Series"
        }
        
        mock_llm_service.return_value.generate_series_entry.return_value.success = True
        mock_llm_service.return_value.generate_series_entry.return_value.parsed_data = {
            "title": "Series Book",
            "premise": "Book in the series",
            "genre": "fantasy",
            "setting": "Fantasy world",
            "themes": ["adventure"]
        }
        
        # Create base concept
        base_concept = CodexObject(
            title="Series Base Concept",
            premise="Foundation for a book series",
            genre="fantasy",
            setting="Magical realm",
            themes=["heroic journey", "magic"],
            tone="epic"
        )
        
        # Generate series
        from src.codexes.modules.ideation.series.series_generator import SeriesConfiguration
        config = SeriesConfiguration(target_book_count=3, formulaicness_level=0.7)
        
        with patch('time.sleep'):  # Skip delays
            series_entries = self.series_generator.generate_complete_series(base_concept, config)
        
        assert len(series_entries) == 3
        for i, entry in enumerate(series_entries, 1):
            assert entry.metadata["entry_number"] == i
            assert entry.metadata["series_uuid"] is not None
    
    @patch('src.codexes.modules.ideation.llm.ideation_llm_service.IdeationLLMService')
    def test_element_extraction_and_recombination(self, mock_llm_service):
        """Test element extraction and recombination workflow."""
        # Mock LLM responses for element extraction
        mock_llm_service.return_value.extract_story_elements.return_value.success = True
        mock_llm_service.return_value.extract_story_elements.return_value.parsed_data = {
            "characters": [{"name": "Hero", "type": "protagonist", "description": "Brave warrior"}],
            "settings": [{"name": "Castle", "type": "location", "description": "Ancient fortress"}],
            "themes": [{"name": "Good vs Evil", "type": "theme", "description": "Classic conflict"}],
            "plot_devices": [{"name": "Quest", "type": "structure", "description": "Journey narrative"}]
        }
        
        # Mock recombination response
        mock_llm_service.return_value.recombine_elements.return_value.success = True
        mock_llm_service.return_value.recombine_elements.return_value.parsed_data = {
            "title": "Recombined Concept",
            "premise": "New story from combined elements",
            "genre": "fantasy",
            "setting": "Combined setting",
            "themes": ["combined themes"]
        }
        
        # Create source concepts
        source_concepts = [
            CodexObject(
                title="Source Concept 1",
                premise="First source story",
                genre="fantasy",
                setting="Medieval castle",
                themes=["heroism", "magic"]
            ),
            CodexObject(
                title="Source Concept 2", 
                premise="Second source story",
                genre="adventure",
                setting="Ancient ruins",
                themes=["discovery", "treasure"]
            )
        ]
        
        # Extract elements
        extracted_elements = self.element_extractor.extract_elements_from_concepts(source_concepts)
        
        assert extracted_elements is not None
        assert len(extracted_elements) > 0
        
        # Recombine elements
        selected_elements = extracted_elements[:3]  # Select first 3 elements
        recombined_concept = self.element_extractor.recombine_elements(selected_elements)
        
        assert recombined_concept is not None
        assert recombined_concept.title == "Recombined Concept"
    
    @patch('src.codexes.modules.ideation.llm.ideation_llm_service.IdeationLLMService')
    def test_batch_processing_workflow(self, mock_llm_service):
        """Test batch processing workflow."""
        # Mock LLM responses
        mock_llm_service.return_value.enhance_codex_object.return_value.success = True
        mock_llm_service.return_value.enhance_codex_object.return_value.parsed_data = {
            "enhanced_premise": "Enhanced premise",
            "additional_themes": ["new theme"],
            "character_suggestions": ["new character"]
        }
        
        # Create batch of concepts
        concepts = []
        for i in range(10):
            concept = CodexObject(
                title=f"Batch Concept {i+1}",
                premise=f"Premise for batch concept {i+1}",
                genre="science fiction",
                setting=f"Future setting {i+1}",
                themes=[f"theme_{i+1}"]
            )
            concepts.append(concept)
        
        # Process batch
        def mock_enhancement_function(concept):
            # Simulate enhancement
            concept.premise = f"Enhanced: {concept.premise}"
            return concept
        
        with patch('time.sleep'):  # Skip delays
            results = self.batch_processor.process_batch(
                concepts,
                mock_enhancement_function,
                batch_name="Integration Test Batch"
            )
        
        assert results is not None
        assert results["success_count"] == 10
        assert results["failure_count"] == 0
        assert len(results["processed_objects"]) == 10
        
        # Verify enhancements were applied
        for processed_concept in results["processed_objects"]:
            assert processed_concept.premise.startswith("Enhanced:")
    
    def test_caching_integration(self):
        """Test caching integration across workflows."""
        # Test cache key generation for different operations
        tournament_key = self.cache_manager.generate_cache_key("tournament_result", {
            "tournament_id": "test_123",
            "round": 1
        })
        
        reader_key = self.cache_manager.generate_cache_key("reader_evaluation", {
            "concept_id": "concept_456",
            "reader_id": "reader_789"
        })
        
        series_key = self.cache_manager.generate_cache_key("series_entry", {
            "series_id": "series_abc",
            "entry_number": 2
        })
        
        # Verify keys are unique
        assert tournament_key != reader_key
        assert reader_key != series_key
        assert tournament_key != series_key
        
        # Test caching and retrieval
        test_data = {"result": "cached_data"}
        
        self.cache_manager.set(tournament_key, test_data)
        retrieved_data = self.cache_manager.get(tournament_key)
        
        assert retrieved_data == test_data
        assert self.cache_manager.cache_stats["hits"] == 1
    
    def test_database_integration(self):
        """Test database integration across workflows."""
        # Test storing different types of objects
        concept = CodexObject(
            title="Database Test Concept",
            premise="Testing database storage",
            genre="mystery",
            setting="Detective office",
            themes=["investigation", "justice"]
        )
        
        # Store concept
        concept_id = self.db_manager.store_codex_object(concept)
        assert concept_id is not None
        
        # Retrieve concept
        retrieved_concept = self.db_manager.get_codex_object(concept_id)
        assert retrieved_concept is not None
        assert retrieved_concept.title == concept.title
        assert retrieved_concept.premise == concept.premise
        
        # Test querying
        fantasy_concepts = self.db_manager.query_codex_objects({"genre": "mystery"})
        assert len(fantasy_concepts) >= 1
        assert any(c.title == "Database Test Concept" for c in fantasy_concepts)
    
    def test_error_handling_integration(self):
        """Test error handling across integrated workflows."""
        # Test with invalid concept data
        invalid_concept = CodexObject(title="", premise="")  # Invalid empty data
        
        # Should handle gracefully without crashing
        try:
            concept_id = self.db_manager.store_codex_object(invalid_concept)
            # If storage succeeds, retrieval should work
            if concept_id:
                retrieved = self.db_manager.get_codex_object(concept_id)
                assert retrieved is not None
        except Exception as e:
            # Should be a handled exception with meaningful message
            assert isinstance(e, (ValueError, TypeError))
            assert len(str(e)) > 0
        
        # Test cache with invalid keys
        try:
            result = self.cache_manager.get("")  # Empty key
            assert result is None  # Should return None, not crash
        except Exception as e:
            # Should handle gracefully
            assert isinstance(e, (ValueError, KeyError))


if __name__ == "__main__":
    pytest.main([__file__])