"""
Unit tests for ContentTransformer.
"""

import pytest
from unittest.mock import Mock, patch

from codexes.modules.ideation.core.transformation import (
    ContentTransformer, TransformationResult, TransformationType
)
from codexes.modules.ideation.core.codex_object import (
    CodexObject, CodexObjectType, DevelopmentStage
)


class TestContentTransformer:
    """Test cases for ContentTransformer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = ContentTransformer()
    
    def test_transformer_initialization(self):
        """Test transformer initialization."""
        assert self.transformer.llm_caller is not None
        assert self.transformer.transformation_prompts is not None
        assert len(self.transformer.transformation_paths) > 0
    
    def test_is_valid_transformation(self):
        """Test transformation validation."""
        # Valid transformations
        assert self.transformer._is_valid_transformation(
            CodexObjectType.IDEA, CodexObjectType.SYNOPSIS
        )
        assert self.transformer._is_valid_transformation(
            CodexObjectType.SYNOPSIS, CodexObjectType.OUTLINE
        )
        
        # Same type (enhancement)
        assert self.transformer._is_valid_transformation(
            CodexObjectType.IDEA, CodexObjectType.IDEA
        )
        
        # Invalid transformation (not in paths)
        assert not self.transformer._is_valid_transformation(
            CodexObjectType.MANUSCRIPT, CodexObjectType.IDEA
        )
    
    def test_determine_transformation_type(self):
        """Test transformation type determination."""
        # Expansion
        assert self.transformer._determine_transformation_type(
            CodexObjectType.IDEA, CodexObjectType.SYNOPSIS
        ) == TransformationType.EXPAND
        
        # Condensation
        assert self.transformer._determine_transformation_type(
            CodexObjectType.SYNOPSIS, CodexObjectType.SUMMARY
        ) == TransformationType.CONDENSE
        
        # Enhancement (same type)
        assert self.transformer._determine_transformation_type(
            CodexObjectType.IDEA, CodexObjectType.IDEA
        ) == TransformationType.ENHANCE
    
    @patch('src.codexes.modules.ideation.core.transformation.enhanced_llm_caller')
    def test_expand_content_success(self, mock_llm_caller):
        """Test successful content expansion."""
        # Mock LLM response
        mock_llm_caller.call_llm_with_retry.return_value = {
            'content': """
            Detective Sarah Chen has always been able to see things others cannot. When a series of 
            mysterious deaths plague Victorian London, she discovers that the victims were all 
            connected to an ancient artifact. As she investigates deeper, she realizes that the 
            artifact is a gateway between the world of the living and the dead.
            """
        }
        
        source_object = CodexObject(
            title="Detective Story",
            content="A detective who can see ghosts solves supernatural mysteries in Victorian London.",
            object_type=CodexObjectType.IDEA,
            genre="Mystery"
        )
        
        result = self.transformer._expand_content(
            source_object, CodexObjectType.SYNOPSIS, {}
        )
        
        assert result.success is True
        assert result.transformed_object is not None
        assert result.transformed_object.object_type == CodexObjectType.SYNOPSIS
        assert result.transformed_object.parent_uuid == source_object.uuid
        assert result.transformed_object.word_count > source_object.word_count
    
    @patch('src.codexes.modules.ideation.core.transformation.enhanced_llm_caller')
    def test_expand_content_failure(self, mock_llm_caller):
        """Test content expansion failure."""
        # Mock LLM failure
        mock_llm_caller.call_llm_with_retry.return_value = None
        
        source_object = CodexObject(
            title="Test",
            content="Test content",
            object_type=CodexObjectType.IDEA
        )
        
        result = self.transformer._expand_content(
            source_object, CodexObjectType.SYNOPSIS, {}
        )
        
        assert result.success is False
        assert result.transformed_object is None
        assert "LLM failed" in result.error_message
    
    @patch('src.codexes.modules.ideation.core.transformation.enhanced_llm_caller')
    def test_condense_content_success(self, mock_llm_caller):
        """Test successful content condensation."""
        # Mock LLM response
        mock_llm_caller.call_llm_with_retry.return_value = {
            'content': "A detective with supernatural abilities solves mysteries in Victorian London."
        }
        
        source_object = CodexObject(
            title="Detective Story",
            content="""
            Detective Sarah Chen has always been able to see things others cannot. When a series of 
            mysterious deaths plague Victorian London, she discovers that the victims were all 
            connected to an ancient artifact. As she investigates deeper, she realizes that the 
            artifact is a gateway between the world of the living and the dead. With the help of 
            her ghostly informants, Sarah must solve the case before more innocent people die.
            """ * 3,  # Make it longer
            object_type=CodexObjectType.SYNOPSIS,
            genre="Mystery"
        )
        
        result = self.transformer._condense_content(
            source_object, CodexObjectType.SUMMARY, {}
        )
        
        assert result.success is True
        assert result.transformed_object is not None
        assert result.transformed_object.object_type == CodexObjectType.SUMMARY
        assert result.transformed_object.word_count < source_object.word_count
    
    @patch('src.codexes.modules.ideation.core.transformation.enhanced_llm_caller')
    def test_enhance_content_success(self, mock_llm_caller):
        """Test successful content enhancement."""
        # Mock LLM response
        mock_llm_caller.call_llm_with_retry.return_value = {
            'content': """
            Detective Sarah Chen possesses an extraordinary gift—the ability to perceive and 
            communicate with spirits from beyond the veil. When a series of inexplicable deaths 
            begins to terrorize Victorian London, she uncovers a sinister connection linking all 
            the victims to a mysterious ancient artifact of immense power.
            """
        }
        
        source_object = CodexObject(
            title="Detective Story",
            content="A detective who can see ghosts solves supernatural mysteries in Victorian London.",
            object_type=CodexObjectType.IDEA,
            genre="Mystery"
        )
        
        result = self.transformer._enhance_content(source_object, {})
        
        assert result.success is True
        assert result.transformed_object is not None
        assert result.transformed_object.object_type == CodexObjectType.IDEA  # Same type
        assert result.transformed_object.development_stage == DevelopmentStage.REVISION
        assert len(result.transformed_object.content) > len(source_object.content)
    
    def test_transform_content_invalid_transformation(self):
        """Test transformation with invalid type combination."""
        source_object = CodexObject(
            title="Test",
            content="Test content",
            object_type=CodexObjectType.MANUSCRIPT
        )
        
        result = self.transformer.transform_content(
            source_object, CodexObjectType.IDEA
        )
        
        assert result.success is False
        assert "Invalid transformation" in result.error_message
    
    @patch('src.codexes.modules.ideation.core.transformation.enhanced_llm_caller')
    def test_transform_content_expansion_success(self, mock_llm_caller):
        """Test successful transformation via expansion."""
        # Mock LLM response
        mock_llm_caller.call_llm_with_retry.return_value = {
            'content': """
            In the fog-shrouded streets of Victorian London, Detective Sarah Chen walks a path 
            between two worlds. Born with the rare gift of supernatural sight, she can perceive 
            the restless spirits that linger in the shadows of the living world. When a series 
            of mysterious deaths begins to plague the city, each victim found in circumstances 
            that defy rational explanation, Sarah discovers a chilling truth: all the deceased 
            were connected to an ancient artifact of immense and terrible power.
            """
        }
        
        source_object = CodexObject(
            title="The Ghost Detective",
            content="A detective who can see ghosts solves supernatural mysteries in Victorian London.",
            object_type=CodexObjectType.IDEA,
            genre="Supernatural Mystery"
        )
        
        result = self.transformer.transform_content(
            source_object, CodexObjectType.SYNOPSIS
        )
        
        assert result.success is True
        assert result.transformed_object.object_type == CodexObjectType.SYNOPSIS
        assert result.transformed_object.parent_uuid == source_object.uuid
        assert "transformation_type" in result.transformed_object.generation_metadata
        assert result.transformed_object.generation_metadata["transformation_type"] == "expand"
    
    def test_get_valid_transformations(self):
        """Test getting valid transformation targets."""
        valid_targets = self.transformer.get_valid_transformations(CodexObjectType.IDEA)
        
        assert CodexObjectType.LOGLINE in valid_targets
        assert CodexObjectType.SUMMARY in valid_targets
        assert CodexObjectType.SYNOPSIS in valid_targets
    
    def test_suggest_next_development_stage(self):
        """Test suggesting next development stage."""
        idea_object = CodexObject(
            title="Test Idea",
            content="A story about time travel",
            object_type=CodexObjectType.IDEA
        )
        
        next_stage = self.transformer.suggest_next_development_stage(idea_object)
        
        # Should suggest logline as next step for idea
        assert next_stage == CodexObjectType.LOGLINE
    
    def test_suggest_next_development_stage_no_valid(self):
        """Test suggesting next stage when no valid transformations exist."""
        # Create object with type that has no valid transformations
        unknown_object = CodexObject(
            title="Unknown Type",
            content="Unknown content",
            object_type=CodexObjectType.UNKNOWN
        )
        
        next_stage = self.transformer.suggest_next_development_stage(unknown_object)
        
        assert next_stage is None
    
    @patch('src.codexes.modules.ideation.core.transformation.enhanced_llm_caller')
    def test_batch_transform_success(self, mock_llm_caller):
        """Test successful batch transformation."""
        # Mock LLM responses
        mock_llm_caller.call_llm_with_retry.return_value = {
            'content': "Expanded content for synopsis"
        }
        
        source_objects = [
            CodexObject(
                title="Idea 1",
                content="First story idea",
                object_type=CodexObjectType.IDEA
            ),
            CodexObject(
                title="Idea 2", 
                content="Second story idea",
                object_type=CodexObjectType.IDEA
            )
        ]
        
        results = self.transformer.batch_transform(
            source_objects, CodexObjectType.SYNOPSIS
        )
        
        assert len(results) == 2
        assert all(result.success for result in results)
        assert all(result.transformed_object.object_type == CodexObjectType.SYNOPSIS 
                  for result in results)
    
    @patch('src.codexes.modules.ideation.core.transformation.enhanced_llm_caller')
    def test_batch_transform_mixed_results(self, mock_llm_caller):
        """Test batch transformation with mixed success/failure."""
        # Mock LLM responses - first succeeds, second fails
        mock_responses = [
            {'content': "Successful expansion"},
            None  # Failure
        ]
        mock_llm_caller.call_llm_with_retry.side_effect = mock_responses
        
        source_objects = [
            CodexObject(
                title="Idea 1",
                content="First story idea",
                object_type=CodexObjectType.IDEA
            ),
            CodexObject(
                title="Idea 2",
                content="Second story idea", 
                object_type=CodexObjectType.IDEA
            )
        ]
        
        results = self.transformer.batch_transform(
            source_objects, CodexObjectType.SYNOPSIS
        )
        
        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False


class TestTransformationResult:
    """Test cases for TransformationResult dataclass."""
    
    def test_transformation_result_creation(self):
        """Test TransformationResult creation."""
        transformed_object = CodexObject(
            title="Transformed",
            content="Transformed content",
            object_type=CodexObjectType.SYNOPSIS
        )
        
        result = TransformationResult(
            success=True,
            transformed_object=transformed_object,
            error_message="",
            transformation_metadata={"method": "expansion"}
        )
        
        assert result.success is True
        assert result.transformed_object == transformed_object
        assert result.error_message == ""
        assert result.transformation_metadata["method"] == "expansion"
    
    def test_transformation_result_failure(self):
        """Test TransformationResult for failure case."""
        result = TransformationResult(
            success=False,
            transformed_object=None,
            error_message="Transformation failed",
            transformation_metadata={"error": "LLM timeout"}
        )
        
        assert result.success is False
        assert result.transformed_object is None
        assert result.error_message == "Transformation failed"
        assert result.transformation_metadata["error"] == "LLM timeout"


class TestTransformationIntegration:
    """Integration tests for transformation system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = ContentTransformer()
    
    @patch('src.codexes.modules.ideation.core.transformation.enhanced_llm_caller')
    def test_full_transformation_workflow(self, mock_llm_caller):
        """Test complete transformation workflow from idea to synopsis."""
        # Mock LLM response for expansion
        mock_llm_caller.call_llm_with_retry.return_value = {
            'content': """
            Dr. Elena Vasquez, a brilliant quantum physicist, discovers that her experimental 
            time machine has created a paradox that threatens to unravel the fabric of reality 
            itself. As she attempts to fix the timeline, she realizes that every correction 
            creates new problems, and she must choose between saving her own future or 
            preserving the natural order of time. The story explores the consequences of 
            scientific ambition and the weight of impossible choices.
            """
        }
        
        # Create initial idea
        idea = CodexObject(
            title="Time Paradox",
            content="A scientist creates a time machine but accidentally creates a paradox.",
            object_type=CodexObjectType.IDEA,
            genre="Science Fiction"
        )
        
        # Transform to synopsis
        result = self.transformer.transform_content(idea, CodexObjectType.SYNOPSIS)
        
        assert result.success is True
        synopsis = result.transformed_object
        
        # Verify transformation
        assert synopsis.object_type == CodexObjectType.SYNOPSIS
        assert synopsis.parent_uuid == idea.uuid
        assert synopsis.title == idea.title
        assert synopsis.genre == idea.genre
        assert synopsis.word_count > idea.word_count
        assert synopsis.development_stage == DevelopmentStage.DEVELOPMENT
        
        # Verify processing history
        assert len(synopsis.processing_history) >= 2  # created + transformed
        transform_entry = synopsis.processing_history[-1]
        assert transform_entry["action"] == "transformed"
        assert transform_entry["details"]["source_type"] == "idea"
        assert transform_entry["details"]["target_type"] == "synopsis"
        
        # Verify generation metadata
        assert "transformation_type" in synopsis.generation_metadata
        assert synopsis.generation_metadata["transformation_type"] == "expand"
    
    @patch('src.codexes.modules.ideation.core.transformation.enhanced_llm_caller')
    def test_multi_stage_transformation(self, mock_llm_caller):
        """Test multiple transformation stages: idea -> synopsis -> outline."""
        # Mock LLM responses
        synopsis_content = """
        Dr. Elena Vasquez discovers her time machine creates paradoxes. She must choose 
        between fixing her timeline or preserving reality's natural order.
        """
        
        outline_content = """
        Chapter 1: The Discovery
        - Elena completes her time machine
        - First test reveals unexpected results
        - Paradox begins to manifest
        
        Chapter 2: The Consequences
        - Timeline starts to fracture
        - Elena realizes the scope of the problem
        - Attempts first correction
        
        Chapter 3: The Choice
        - Multiple timelines converge
        - Elena must make the ultimate decision
        - Resolution and consequences
        """
        
        mock_llm_caller.call_llm_with_retry.side_effect = [
            {'content': synopsis_content},
            {'content': outline_content}
        ]
        
        # Start with idea
        idea = CodexObject(
            title="Time Paradox",
            content="A scientist creates a time machine but accidentally creates a paradox.",
            object_type=CodexObjectType.IDEA,
            genre="Science Fiction"
        )
        
        # Transform to synopsis
        synopsis_result = self.transformer.transform_content(idea, CodexObjectType.SYNOPSIS)
        assert synopsis_result.success is True
        synopsis = synopsis_result.transformed_object
        
        # Transform synopsis to outline
        outline_result = self.transformer.transform_content(synopsis, CodexObjectType.OUTLINE)
        assert outline_result.success is True
        outline = outline_result.transformed_object
        
        # Verify final outline
        assert outline.object_type == CodexObjectType.OUTLINE
        assert outline.parent_uuid == synopsis.uuid
        assert idea.uuid in outline.derived_from
        assert synopsis.uuid in outline.derived_from
        assert "Chapter" in outline.content
    
    def test_transformation_path_validation(self):
        """Test that transformation paths are properly defined."""
        # Check that all object types have some transformation paths
        for object_type in CodexObjectType:
            if object_type != CodexObjectType.UNKNOWN:
                paths = self.transformer.get_valid_transformations(object_type)
                # Most types should have at least one valid transformation
                # (except maybe MANUSCRIPT which might only condense)
                if object_type not in [CodexObjectType.MANUSCRIPT, CodexObjectType.SERIES]:
                    assert len(paths) > 0, f"{object_type} should have valid transformations"
    
    def test_transformation_metadata_preservation(self):
        """Test that transformation preserves important metadata."""
        with patch('src.codexes.modules.ideation.core.transformation.enhanced_llm_caller') as mock_llm:
            mock_llm.call_llm_with_retry.return_value = {
                'content': "Enhanced content with more detail and better structure."
            }
            
            # Create source object with metadata
            source = CodexObject(
                title="Original Title",
                content="Original content",
                object_type=CodexObjectType.IDEA,
                genre="Fantasy",
                target_audience="Young Adult",
                tags=["magic", "adventure"]
            )
            
            # Add some evaluation data
            source.add_evaluation_score("test_judge", 7.5)
            source.tournament_performance = {"wins": 2, "losses": 1}
            
            # Transform
            result = self.transformer.transform_content(source, CodexObjectType.SYNOPSIS)
            transformed = result.transformed_object
            
            # Verify metadata preservation
            assert transformed.title == source.title
            assert transformed.genre == source.genre
            assert transformed.target_audience == source.target_audience
            assert transformed.tags == source.tags
            
            # Verify relationship tracking
            assert transformed.parent_uuid == source.uuid
            assert source.uuid in transformed.derived_from
            
            # Original object's data should be preserved
            assert source.evaluation_scores["test_judge"] == 7.5
            assert source.tournament_performance == {"wins": 2, "losses": 1}