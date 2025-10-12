"""
Integration tests for the Universal Workflow Interface.
Tests the complete workflow from content creation to workflow execution.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
project_root = Path(__file__).resolve().parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from codexes.modules.ideation.core.codex_object import CodexObject, CodexObjectType
from codexes.ui.components.workflow_selector import WorkflowSelector, WorkflowType, WorkflowConfiguration
from codexes.ui.adapters.workflow_adapter import WorkflowAdapter, MixedTypeHandling


class TestWorkflowInterface:
    """Test suite for the Universal Workflow Interface."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_objects = [
            CodexObject(
                title="Time Travel Adventure",
                content="A scientist discovers a way to travel through time but must prevent a catastrophic timeline.",
                object_type=CodexObjectType.IDEA,
                genre="Science Fiction"
            ),
            CodexObject(
                title="Dragon's Quest Synopsis",
                content="In a medieval fantasy world, a young knight must find and tame a legendary dragon to save the kingdom from an ancient evil.",
                object_type=CodexObjectType.SYNOPSIS,
                genre="Fantasy"
            ),
            CodexObject(
                title="Mystery Novel Outline",
                content="Chapter 1: The Murder\nChapter 2: Investigation\nChapter 3: Resolution",
                object_type=CodexObjectType.OUTLINE,
                genre="Mystery"
            )
        ]
    
    def test_workflow_adapter_content_analysis(self):
        """Test WorkflowAdapter content analysis functionality."""
        adapter = WorkflowAdapter()
        
        # Test with mixed content types
        analysis = adapter.analyze_content_mix(self.test_objects)
        
        assert analysis["total_objects"] == 3
        assert analysis["unique_types"] == 3
        assert analysis["is_mixed"] is True
        assert analysis["mixing_complexity"] in ["low", "medium", "high"]
        assert analysis["recommended_strategy"] in ["adaptive", "normalize", "type_aware"]
        
        # Test with single content type
        single_type_objects = [self.test_objects[0]]
        single_analysis = adapter.analyze_content_mix(single_type_objects)
        
        assert single_analysis["total_objects"] == 1
        assert single_analysis["unique_types"] == 1
        assert single_analysis["is_mixed"] is False
        assert single_analysis["dominant_type"] == "idea"
    
    def test_workflow_adaptation_creation(self):
        """Test creation of workflow adaptations."""
        adapter = WorkflowAdapter()
        
        # Test tournament adaptation
        tournament_adaptation = adapter.create_workflow_adaptation(
            self.test_objects, 
            "tournament"
        )
        
        assert isinstance(tournament_adaptation.handling_strategy, MixedTypeHandling)
        assert len(tournament_adaptation.type_weights) > 0
        assert tournament_adaptation.comparison_method in [
            "adaptive_scoring", "normalized_scoring", "type_weighted_scoring", "standard_scoring"
        ]
        
        # Test reader panel adaptation
        reader_panel_adaptation = adapter.create_workflow_adaptation(
            self.test_objects,
            "reader_panel"
        )
        
        assert isinstance(reader_panel_adaptation.handling_strategy, MixedTypeHandling)
        assert len(reader_panel_adaptation.evaluation_adjustments) > 0
    
    def test_tournament_evaluation_adaptation(self):
        """Test tournament evaluation adaptation for mixed types."""
        adapter = WorkflowAdapter()
        
        adaptation = adapter.create_workflow_adaptation(self.test_objects, "tournament")
        
        base_criteria = {
            "originality": 0.3,
            "marketability": 0.3,
            "execution_potential": 0.2,
            "emotional_impact": 0.2
        }
        
        # Test adaptive evaluation
        evaluation_config = adapter.adapt_tournament_evaluation(
            self.test_objects[0],  # idea
            self.test_objects[1],  # synopsis
            base_criteria,
            adaptation
        )
        
        assert "criteria" in evaluation_config
        assert "method" in evaluation_config
        assert evaluation_config["method"] in ["adaptive", "normalized", "type_aware", "standard"]
    
    def test_reader_panel_adaptation(self):
        """Test reader panel adaptation for mixed types."""
        adapter = WorkflowAdapter()
        
        adaptation = adapter.create_workflow_adaptation(self.test_objects, "reader_panel")
        
        base_config = {
            "panel_size": 8,
            "demographics": {
                "age_distribution": "balanced",
                "gender_distribution": "balanced"
            }
        }
        
        adapted_config = adapter.adapt_reader_panel_evaluation(
            self.test_objects,
            base_config,
            adaptation
        )
        
        assert "evaluation_instructions" in adapted_config
        assert "mixed_type_handling" in adapted_config
        assert "type_weights" in adapted_config
        assert adapted_config["panel_size"] == 8
    
    def test_series_generation_adaptation(self):
        """Test series generation adaptation."""
        adapter = WorkflowAdapter()
        
        adaptation = adapter.create_workflow_adaptation([self.test_objects[0]], "series_generation")
        
        base_config = {
            "series_type": "standalone_series",
            "target_book_count": 3,
            "consistency_requirements": {
                "setting": 0.8,
                "tone": 0.7,
                "genre": 0.9
            }
        }
        
        adapted_config = adapter.adapt_series_generation(
            self.test_objects[0],
            base_config,
            adaptation
        )
        
        assert "base_type" in adapted_config
        assert "type_specific_instructions" in adapted_config
        assert adapted_config["target_book_count"] == 3
        assert "consistency_requirements" in adapted_config
    
    @patch('codexes.ui.components.workflow_selector.DatabaseManager')
    def test_workflow_selector_initialization(self, mock_db_manager):
        """Test WorkflowSelector initialization."""
        # Mock the database manager
        mock_db_instance = Mock()
        mock_db_manager.return_value = mock_db_instance
        
        selector = WorkflowSelector()
        
        assert selector.session_key == "workflow_selector_state"
        assert selector.tournament_engine is not None
        assert selector.reader_panel is not None
        assert selector.series_generator is not None
    
    def test_workflow_configuration_creation(self):
        """Test creation of workflow configurations."""
        # Test tournament configuration
        tournament_config = WorkflowConfiguration(
            workflow_type=WorkflowType.TOURNAMENT,
            name="Test Tournament",
            description="Test tournament with mixed types",
            parameters={
                "tournament_type": "single_elimination",
                "evaluation_criteria": {
                    "originality": 0.3,
                    "marketability": 0.3,
                    "execution_potential": 0.2,
                    "emotional_impact": 0.2
                }
            }
        )
        
        config_dict = tournament_config.to_dict()
        
        assert config_dict["workflow_type"] == "tournament"
        assert config_dict["name"] == "Test Tournament"
        assert "parameters" in config_dict
        assert "evaluation_criteria" in config_dict["parameters"]
        
        # Test reader panel configuration
        reader_panel_config = WorkflowConfiguration(
            workflow_type=WorkflowType.READER_PANEL,
            name="Test Reader Panel",
            parameters={
                "panel_size": 10,
                "demographics": {
                    "age_distribution": "young_adult",
                    "gender_distribution": "balanced"
                }
            }
        )
        
        panel_dict = reader_panel_config.to_dict()
        
        assert panel_dict["workflow_type"] == "reader_panel"
        assert panel_dict["parameters"]["panel_size"] == 10
        
        # Test series generation configuration
        series_config = WorkflowConfiguration(
            workflow_type=WorkflowType.SERIES_GENERATION,
            name="Test Series",
            parameters={
                "series_type": "character_series",
                "target_book_count": 5,
                "formulaicness_level": 0.7
            }
        )
        
        series_dict = series_config.to_dict()
        
        assert series_dict["workflow_type"] == "series_generation"
        assert series_dict["parameters"]["target_book_count"] == 5
    
    def test_mixed_type_handling_strategies(self):
        """Test different mixed-type handling strategies."""
        adapter = WorkflowAdapter()
        
        # Test each handling strategy
        strategies = [
            MixedTypeHandling.ADAPTIVE,
            MixedTypeHandling.NORMALIZE,
            MixedTypeHandling.TYPE_AWARE,
            MixedTypeHandling.SEPARATE
        ]
        
        for strategy in strategies:
            # Create adaptation with specific strategy
            adaptation = adapter.create_workflow_adaptation(self.test_objects, "tournament")
            adaptation.handling_strategy = strategy
            
            # Test tournament evaluation with this strategy
            base_criteria = {
                "originality": 0.25,
                "marketability": 0.25,
                "execution_potential": 0.25,
                "emotional_impact": 0.25
            }
            
            evaluation_config = adapter.adapt_tournament_evaluation(
                self.test_objects[0],
                self.test_objects[1],
                base_criteria,
                adaptation
            )
            
            assert "criteria" in evaluation_config
            assert "method" in evaluation_config
    
    def test_type_specific_evaluation_instructions(self):
        """Test type-specific evaluation instructions."""
        adapter = WorkflowAdapter()
        
        # Test instructions for different content types
        content_types = ["idea", "synopsis", "outline", "draft", "manuscript"]
        
        for content_type in content_types:
            instructions = adapter._get_type_specific_evaluation_instructions(content_type)
            
            assert "focus" in instructions
            assert "criteria" in instructions
            assert "considerations" in instructions
            assert isinstance(instructions["focus"], str)
            assert len(instructions["focus"]) > 0
    
    def test_series_generation_instructions(self):
        """Test series generation instructions for different types."""
        adapter = WorkflowAdapter()
        
        content_types = ["idea", "synopsis", "outline"]
        
        for content_type in content_types:
            instructions = adapter._get_series_generation_instructions(content_type)
            
            assert "expansion_focus" in instructions
            assert "consistency_elements" in instructions
            assert "variation_approach" in instructions
            assert isinstance(instructions["expansion_focus"], str)
            assert len(instructions["expansion_focus"]) > 0


if __name__ == "__main__":
    # Run tests if executed directly
    test_suite = TestWorkflowInterface()
    test_suite.setup_method()
    
    print("🧪 Running Workflow Interface Integration Tests...")
    
    try:
        test_suite.test_workflow_adapter_content_analysis()
        print("✅ Content analysis test passed")
        
        test_suite.test_workflow_adaptation_creation()
        print("✅ Workflow adaptation creation test passed")
        
        test_suite.test_tournament_evaluation_adaptation()
        print("✅ Tournament evaluation adaptation test passed")
        
        test_suite.test_reader_panel_adaptation()
        print("✅ Reader panel adaptation test passed")
        
        test_suite.test_series_generation_adaptation()
        print("✅ Series generation adaptation test passed")
        
        test_suite.test_workflow_configuration_creation()
        print("✅ Workflow configuration creation test passed")
        
        test_suite.test_mixed_type_handling_strategies()
        print("✅ Mixed-type handling strategies test passed")
        
        test_suite.test_type_specific_evaluation_instructions()
        print("✅ Type-specific evaluation instructions test passed")
        
        test_suite.test_series_generation_instructions()
        print("✅ Series generation instructions test passed")
        
        print("\n🎉 All integration tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)