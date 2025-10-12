"""
Comprehensive test suite for the streamlined imprint builder.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

# Import the modules to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from codexes.modules.imprint_builder.imprint_concept import ImprintConcept, ImprintConceptParser
from codexes.modules.imprint_builder.imprint_expander import ImprintExpander, ExpandedImprint
from codexes.modules.imprint_builder.unified_editor import ImprintEditor, EditingSession
from codexes.modules.imprint_builder.artifact_generator import ImprintArtifactGenerator
from codexes.modules.imprint_builder.schedule_generator import ImprintScheduleGenerator
from codexes.modules.imprint_builder.validation import ImprintValidator, ValidationResult
from codexes.modules.imprint_builder.pipeline_integration import PipelineIntegrator
from codexes.core.llm_integration import LLMCaller


class TestImprintConcept:
    """Test the ImprintConcept data model."""
    
    def test_concept_creation(self):
        """Test basic concept creation."""
        concept = ImprintConcept(
            raw_input="A literary imprint for contemporary fiction",
            extracted_themes=["literary fiction", "contemporary"],
            target_audience="adult readers",
            confidence_score=0.8
        )
        
        assert concept.raw_input == "A literary imprint for contemporary fiction"
        assert "literary fiction" in concept.extracted_themes
        assert concept.target_audience == "adult readers"
        assert concept.confidence_score == 0.8
    
    def test_concept_serialization(self):
        """Test concept to/from dict conversion."""
        concept = ImprintConcept(
            raw_input="Test imprint",
            extracted_themes=["test"],
            target_audience="testers"
        )
        
        # Test to_dict
        concept_dict = concept.to_dict()
        assert isinstance(concept_dict, dict)
        assert concept_dict['raw_input'] == "Test imprint"
        
        # Test from_dict
        restored_concept = ImprintConcept.from_dict(concept_dict)
        assert restored_concept.raw_input == concept.raw_input
        assert restored_concept.extracted_themes == concept.extracted_themes


class TestImprintConceptParser:
    """Test the ImprintConceptParser."""
    
    @pytest.fixture
    def mock_llm_caller(self):
        """Mock LLM caller for testing."""
        mock_caller = Mock(spec=LLMCaller)
        mock_caller.call_model_with_prompt.return_value = {
            'content': json.dumps({
                'themes': ['fiction', 'literary'],
                'target_audience': 'adult readers',
                'publishing_focus': ['novels', 'short stories'],
                'design_style': 'elegant',
                'special_requirements': [],
                'market_positioning': 'premium literary',
                'brand_personality': 'sophisticated'
            })
        }
        return mock_caller
    
    @pytest.fixture
    def parser(self, mock_llm_caller):
        """Create parser with mocked LLM caller."""
        return ImprintConceptParser(mock_llm_caller)
    
    def test_parse_simple_concept(self, parser):
        """Test parsing a simple concept."""
        concept_text = "A literary imprint focused on contemporary fiction for adult readers"
        concept = parser.parse_concept(concept_text)
        
        assert concept.raw_input == concept_text
        assert concept.confidence_score > 0
        assert len(concept.extracted_themes) > 0
    
    def test_parse_detailed_concept(self, parser):
        """Test parsing a detailed concept."""
        concept_text = """
        A premium literary imprint specializing in contemporary fiction and literary non-fiction 
        for educated adult readers aged 25-55. We focus on diverse voices and innovative storytelling, 
        with a sophisticated brand identity that appeals to book clubs and literary enthusiasts.
        """
        concept = parser.parse_concept(concept_text)
        
        assert concept.confidence_score > 0.5
        assert concept.target_audience
        assert len(concept.extracted_themes) > 1
    
    def test_validation_and_suggestions(self, parser):
        """Test concept validation and suggestions."""
        concept_text = "Books"  # Very minimal input
        concept = parser.parse_concept(concept_text)
        
        validation = parser.validate_concept(concept)
        assert not validation['is_valid'] or len(validation['suggestions']) > 0
        
        suggestions = parser.suggest_improvements(concept)
        assert len(suggestions) > 0


class TestImprintExpander:
    """Test the ImprintExpander."""
    
    @pytest.fixture
    def mock_llm_caller(self):
        """Mock LLM caller for testing."""
        mock_caller = Mock(spec=LLMCaller)
        mock_caller.call_model_with_prompt.return_value = {
            'content': json.dumps({
                'imprint_name': 'Literary Voices',
                'tagline': 'Diverse stories, universal truths',
                'mission_statement': 'Publishing exceptional literary fiction',
                'brand_values': ['Quality', 'Diversity', 'Innovation'],
                'unique_selling_proposition': 'Curated literary excellence',
                'brand_voice': 'Sophisticated yet accessible'
            })
        }
        return mock_caller
    
    @pytest.fixture
    def expander(self, mock_llm_caller):
        """Create expander with mocked LLM caller."""
        return ImprintExpander(mock_llm_caller)
    
    @pytest.fixture
    def sample_concept(self):
        """Create a sample concept for testing."""
        return ImprintConcept(
            raw_input="A literary imprint for contemporary fiction",
            extracted_themes=["literary fiction", "contemporary"],
            target_audience="adult readers",
            publishing_focus=["fiction"],
            confidence_score=0.8
        )
    
    def test_expand_concept(self, expander, sample_concept):
        """Test concept expansion."""
        expanded = expander.expand_concept(sample_concept)
        
        assert isinstance(expanded, ExpandedImprint)
        assert expanded.branding.imprint_name
        assert expanded.design.color_palette
        assert expanded.publishing.primary_genres
        assert expanded.production.workflow_stages
    
    def test_fallback_expansion(self, sample_concept):
        """Test fallback expansion when LLM fails."""
        # Create expander with failing LLM
        mock_caller = Mock(spec=LLMCaller)
        mock_caller.call_model_with_prompt.side_effect = Exception("LLM failed")
        
        expander = ImprintExpander(mock_caller)
        expanded = expander.expand_concept(sample_concept)
        
        # Should still create a valid expanded imprint with fallbacks
        assert isinstance(expanded, ExpandedImprint)
        assert expanded.expansion_metadata['expansion_method'] == 'fallback'


class TestImprintEditor:
    """Test the ImprintEditor."""
    
    @pytest.fixture
    def mock_llm_caller(self):
        """Mock LLM caller for testing."""
        return Mock(spec=LLMCaller)
    
    @pytest.fixture
    def editor(self, mock_llm_caller):
        """Create editor with mocked LLM caller."""
        return ImprintEditor(mock_llm_caller)
    
    @pytest.fixture
    def sample_imprint(self):
        """Create a sample expanded imprint."""
        concept = ImprintConcept(raw_input="Test imprint")
        expanded = ExpandedImprint(concept=concept)
        expanded.branding.imprint_name = "Test Imprint"
        expanded.branding.mission_statement = "Test mission"
        return expanded
    
    def test_create_editing_session(self, editor, sample_imprint):
        """Test creating an editing session."""
        session = editor.create_editing_session(sample_imprint)
        
        assert isinstance(session, EditingSession)
        assert session.imprint.branding.imprint_name == "Test Imprint"
        assert len(session.change_history) == 0
        assert not session.is_dirty
    
    def test_update_field(self, editor, sample_imprint):
        """Test updating a field with change tracking."""
        session = editor.create_editing_session(sample_imprint)
        
        # Update imprint name
        success = editor.update_field(session, 'branding', 'imprint_name', 'New Name')
        
        assert success
        assert session.imprint.branding.imprint_name == 'New Name'
        assert len(session.change_history) == 1
        assert session.is_dirty
    
    def test_undo_redo(self, editor, sample_imprint):
        """Test undo/redo functionality."""
        session = editor.create_editing_session(sample_imprint)
        original_name = session.imprint.branding.imprint_name
        
        # Make a change
        editor.update_field(session, 'branding', 'imprint_name', 'New Name')
        assert session.imprint.branding.imprint_name == 'New Name'
        
        # Undo the change
        success = editor.undo_change(session)
        assert success
        assert session.imprint.branding.imprint_name == original_name
        
        # Redo the change
        success = editor.redo_change(session)
        assert success
        assert session.imprint.branding.imprint_name == 'New Name'
    
    def test_validation(self, editor, sample_imprint):
        """Test imprint validation."""
        session = editor.create_editing_session(sample_imprint)
        
        validation = editor.validate_imprint(session)
        assert isinstance(validation, ValidationResult)
        assert hasattr(validation, 'is_valid')
        assert hasattr(validation, 'completeness_score')


class TestArtifactGenerator:
    """Test the ImprintArtifactGenerator."""
    
    @pytest.fixture
    def mock_llm_caller(self):
        """Mock LLM caller for testing."""
        return Mock(spec=LLMCaller)
    
    @pytest.fixture
    def generator(self, mock_llm_caller):
        """Create generator with mocked LLM caller."""
        return ImprintArtifactGenerator(mock_llm_caller)
    
    @pytest.fixture
    def sample_imprint(self):
        """Create a sample expanded imprint."""
        concept = ImprintConcept(raw_input="Test imprint")
        expanded = ExpandedImprint(concept=concept)
        expanded.branding.imprint_name = "Test Imprint"
        expanded.branding.mission_statement = "Test mission"
        expanded.design.color_palette = {'primary_color': '#2C3E50'}
        expanded.design.typography = {'primary_font': 'Arial'}
        expanded.publishing.primary_genres = ['Fiction']
        return expanded
    
    def test_generate_latex_templates(self, generator, sample_imprint):
        """Test LaTeX template generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = generator.generate_latex_templates(sample_imprint, temp_dir)
            
            assert result['status'] == 'success'
            assert 'files_generated' in result
            
            # Check if files were created
            template_path = Path(temp_dir)
            assert (template_path / 'template.tex').exists()
    
    def test_generate_llm_prompts(self, generator, sample_imprint):
        """Test LLM prompt generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            prompts_file = Path(temp_dir) / 'prompts.json'
            result = generator.generate_llm_prompts(sample_imprint, str(prompts_file))
            
            assert result['status'] == 'success'
            assert prompts_file.exists()
            
            # Validate prompts file
            with open(prompts_file, 'r') as f:
                prompts = json.load(f)
            
            assert 'content_generation' in prompts
            assert 'editing' in prompts
    
    def test_generate_all_artifacts(self, generator, sample_imprint):
        """Test generating all artifacts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            results = generator.generate_all_artifacts(sample_imprint, temp_dir)
            
            assert 'artifacts' in results
            assert 'templates' in results['artifacts']
            assert 'prompts' in results['artifacts']
            assert 'configs' in results['artifacts']


class TestScheduleGenerator:
    """Test the ImprintScheduleGenerator."""
    
    @pytest.fixture
    def mock_llm_caller(self):
        """Mock LLM caller for testing."""
        mock_caller = Mock(spec=LLMCaller)
        mock_caller.call_model_with_prompt.return_value = {
            'content': json.dumps({
                'book_ideas': [
                    {
                        'title': 'Test Book 1',
                        'author': 'Test Author 1',
                        'genre': 'Fiction',
                        'description': 'A test book',
                        'estimated_word_count': 80000,
                        'target_audience': 'Adult readers',
                        'market_appeal': 'medium'
                    }
                ]
            })
        }
        return mock_caller
    
    @pytest.fixture
    def generator(self, mock_llm_caller):
        """Create generator with mocked LLM caller."""
        return ImprintScheduleGenerator(mock_llm_caller)
    
    @pytest.fixture
    def sample_imprint(self):
        """Create a sample expanded imprint."""
        concept = ImprintConcept(raw_input="Test imprint")
        expanded = ExpandedImprint(concept=concept)
        expanded.branding.imprint_name = "Test Imprint"
        expanded.publishing.primary_genres = ['Fiction']
        expanded.publishing.target_audience = 'Adult readers'
        expanded.production.workflow_stages = ['Edit', 'Design', 'Produce']
        return expanded
    
    def test_generate_initial_schedule(self, generator, sample_imprint):
        """Test initial schedule generation."""
        schedules = generator.generate_initial_schedule(sample_imprint, num_books=3)
        
        assert len(schedules) > 0
        assert all(hasattr(schedule, 'title') for schedule in schedules)
        assert all(hasattr(schedule, 'publication_date') for schedule in schedules)
    
    def test_generate_workflow_config(self, generator, sample_imprint):
        """Test workflow configuration generation."""
        config = generator.generate_workflow_config(sample_imprint)
        
        assert 'workflow_stages' in config
        assert 'quality_gates' in config
        assert 'resource_requirements' in config
    
    def test_suggest_codex_types(self, generator, sample_imprint):
        """Test codex type suggestions."""
        codex_types = generator.suggest_codex_types(sample_imprint)
        
        assert isinstance(codex_types, list)
        assert len(codex_types) > 0


class TestImprintValidator:
    """Test the ImprintValidator."""
    
    @pytest.fixture
    def validator(self):
        """Create validator."""
        return ImprintValidator()
    
    @pytest.fixture
    def sample_concept(self):
        """Create a sample concept."""
        return ImprintConcept(
            raw_input="A literary imprint for contemporary fiction",
            extracted_themes=["literary fiction"],
            target_audience="adult readers",
            confidence_score=0.8
        )
    
    @pytest.fixture
    def sample_imprint(self):
        """Create a sample expanded imprint."""
        concept = ImprintConcept(raw_input="Test imprint")
        expanded = ExpandedImprint(concept=concept)
        expanded.branding.imprint_name = "Test Imprint"
        expanded.publishing.primary_genres = ['Fiction']
        return expanded
    
    def test_validate_concept(self, validator, sample_concept):
        """Test concept validation."""
        result = validator.validate_concept(sample_concept)
        
        assert isinstance(result, ValidationResult)
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'overall_score')
        assert hasattr(result, 'issues')
    
    def test_validate_expanded_imprint(self, validator, sample_imprint):
        """Test expanded imprint validation."""
        result = validator.validate_expanded_imprint(sample_imprint)
        
        assert isinstance(result, ValidationResult)
        assert result.overall_score >= 0.0
        assert result.overall_score <= 1.0
    
    def test_template_validation(self, validator):
        """Test template validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple template file
            template_path = Path(temp_dir)
            template_file = template_path / 'template.tex'
            
            with open(template_file, 'w') as f:
                f.write('\\documentclass{memoir}\n\\begin{document}\nTest\n\\end{document}')
            
            result = validator.validate_template_compilation(str(template_path))
            
            assert isinstance(result, ValidationResult)
    
    def test_auto_fix_issues(self, validator, sample_imprint):
        """Test automatic issue fixing."""
        # Create an imprint with fixable issues
        sample_imprint.branding.imprint_name = ""  # Missing name
        sample_imprint.publishing.primary_genres = []  # Missing genres
        
        validation_result = validator.validate_expanded_imprint(sample_imprint)
        fix_results = validator.auto_fix_issues(sample_imprint, validation_result)
        
        assert 'fixes_applied' in fix_results
        assert 'fixes_failed' in fix_results


class TestPipelineIntegration:
    """Test the PipelineIntegrator."""
    
    @pytest.fixture
    def mock_llm_caller(self):
        """Mock LLM caller for testing."""
        return Mock(spec=LLMCaller)
    
    @pytest.fixture
    def integrator(self, mock_llm_caller):
        """Create integrator with mocked LLM caller."""
        return PipelineIntegrator(mock_llm_caller)
    
    @pytest.fixture
    def sample_imprint(self):
        """Create a sample expanded imprint."""
        concept = ImprintConcept(raw_input="Test imprint")
        expanded = ExpandedImprint(concept=concept)
        expanded.branding.imprint_name = "Test Imprint"
        expanded.publishing.primary_genres = ['Fiction']
        return expanded
    
    def test_check_compatibility(self, integrator, sample_imprint):
        """Test compatibility checking."""
        compatibility = integrator.check_compatibility(sample_imprint)
        
        assert 'overall_compatible' in compatibility
        assert 'issues' in compatibility
        assert 'recommendations' in compatibility
    
    def test_create_migration_plan(self, integrator):
        """Test migration plan creation."""
        existing_imprints = ['imprint1', 'imprint2']
        new_definitions = []  # Empty for testing
        
        plan = integrator.create_migration_plan(existing_imprints, new_definitions)
        
        assert 'migration_phases' in plan
        assert 'estimated_duration_hours' in plan
        assert 'risks' in plan


class TestIntegrationScenarios:
    """Test complete integration scenarios."""
    
    @pytest.fixture
    def mock_llm_caller(self):
        """Mock LLM caller for integration tests."""
        mock_caller = Mock(spec=LLMCaller)
        
        # Mock concept parsing response
        mock_caller.call_model_with_prompt.return_value = {
            'content': json.dumps({
                'themes': ['fiction', 'literary'],
                'target_audience': 'adult readers',
                'publishing_focus': ['novels'],
                'design_style': 'elegant',
                'special_requirements': [],
                'market_positioning': 'premium',
                'brand_personality': 'sophisticated',
                'imprint_name': 'Literary Voices',
                'tagline': 'Exceptional stories',
                'mission_statement': 'Publishing quality literature',
                'brand_values': ['Quality', 'Diversity'],
                'unique_selling_proposition': 'Curated excellence'
            })
        }
        return mock_caller
    
    def test_complete_imprint_creation_workflow(self, mock_llm_caller):
        """Test the complete workflow from concept to artifacts."""
        # Step 1: Parse concept
        parser = ImprintConceptParser(mock_llm_caller)
        concept = parser.parse_concept("A literary imprint for contemporary fiction")
        
        assert concept.raw_input
        assert concept.confidence_score > 0
        
        # Step 2: Expand concept
        expander = ImprintExpander(mock_llm_caller)
        expanded_imprint = expander.expand_concept(concept)
        
        assert expanded_imprint.branding.imprint_name
        assert expanded_imprint.publishing.primary_genres
        
        # Step 3: Validate imprint
        validator = ImprintValidator()
        validation_result = validator.validate_expanded_imprint(expanded_imprint)
        
        assert isinstance(validation_result, ValidationResult)
        
        # Step 4: Generate artifacts
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = ImprintArtifactGenerator(mock_llm_caller)
            artifact_results = generator.generate_all_artifacts(expanded_imprint, temp_dir)
            
            assert 'artifacts' in artifact_results
            assert len(artifact_results.get('errors', [])) == 0
        
        # Step 5: Generate schedule
        schedule_generator = ImprintScheduleGenerator(mock_llm_caller)
        schedules = schedule_generator.generate_initial_schedule(expanded_imprint, num_books=3)
        
        assert len(schedules) == 3
        assert all(schedule.imprint_name == expanded_imprint.branding.imprint_name for schedule in schedules)
    
    def test_editing_workflow(self, mock_llm_caller):
        """Test the editing workflow."""
        # Create initial imprint
        concept = ImprintConcept(raw_input="Test imprint")
        expanded_imprint = ExpandedImprint(concept=concept)
        expanded_imprint.branding.imprint_name = "Original Name"
        
        # Create editing session
        editor = ImprintEditor(mock_llm_caller)
        session = editor.create_editing_session(expanded_imprint)
        
        # Make several changes
        editor.update_field(session, 'branding', 'imprint_name', 'New Name')
        editor.update_field(session, 'branding', 'tagline', 'New Tagline')
        
        assert len(session.change_history) == 2
        assert session.is_dirty
        
        # Validate changes
        validation = editor.validate_imprint(session)
        assert isinstance(validation, ValidationResult)
        
        # Test undo/redo
        editor.undo_change(session)
        assert session.imprint.branding.tagline == ''
        
        editor.redo_change(session)
        assert session.imprint.branding.tagline == 'New Tagline'
    
    def test_error_handling_and_recovery(self, mock_llm_caller):
        """Test error handling and recovery scenarios."""
        # Test with failing LLM
        failing_llm = Mock(spec=LLMCaller)
        failing_llm.call_model_with_prompt.side_effect = Exception("LLM Error")
        
        # Should still work with fallbacks
        parser = ImprintConceptParser(failing_llm)
        concept = parser.parse_concept("Test concept")
        
        assert concept.raw_input == "Test concept"
        assert concept.confidence_score >= 0  # Should have some fallback score
        
        # Test expansion with failing LLM
        expander = ImprintExpander(failing_llm)
        expanded = expander.expand_concept(concept)
        
        assert isinstance(expanded, ExpandedImprint)
        assert expanded.expansion_metadata['expansion_method'] == 'fallback'


# Performance and stress tests
class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.fixture
    def mock_llm_caller(self):
        """Fast mock LLM caller for performance tests."""
        mock_caller = Mock(spec=LLMCaller)
        mock_caller.call_model_with_prompt.return_value = {
            'content': json.dumps({'test': 'response'})
        }
        return mock_caller
    
    def test_large_batch_processing(self, mock_llm_caller):
        """Test processing multiple imprints efficiently."""
        parser = ImprintConceptParser(mock_llm_caller)
        
        # Process multiple concepts
        concepts = []
        for i in range(10):
            concept_text = f"Test imprint {i} for testing batch processing"
            concept = parser.parse_concept(concept_text)
            concepts.append(concept)
        
        assert len(concepts) == 10
        assert all(concept.raw_input for concept in concepts)
    
    def test_memory_usage(self, mock_llm_caller):
        """Test memory usage with large imprints."""
        # Create a large imprint with many components
        concept = ImprintConcept(
            raw_input="Large test imprint" * 100,
            extracted_themes=["theme"] * 50,
            special_requirements=["requirement"] * 100
        )
        
        expander = ImprintExpander(mock_llm_caller)
        expanded = expander.expand_concept(concept)
        
        # Should handle large data without issues
        assert isinstance(expanded, ExpandedImprint)


# User acceptance tests
class TestUserAcceptanceScenarios:
    """Test real-world user scenarios."""
    
    @pytest.fixture
    def mock_llm_caller(self):
        """Mock LLM caller with realistic responses."""
        mock_caller = Mock(spec=LLMCaller)
        mock_caller.call_model_with_prompt.return_value = {
            'content': json.dumps({
                'imprint_name': 'Realistic Imprint',
                'themes': ['realistic', 'practical'],
                'target_audience': 'real users'
            })
        }
        return mock_caller
    
    def test_literary_fiction_imprint(self, mock_llm_caller):
        """Test creating a literary fiction imprint."""
        concept_text = """
        A premium literary imprint specializing in contemporary fiction and literary non-fiction 
        for educated adult readers aged 25-55. We focus on diverse voices and innovative storytelling, 
        with a sophisticated brand identity that appeals to book clubs and literary enthusiasts.
        Our mission is to publish books that challenge, inspire, and endure.
        """
        
        # Full workflow
        parser = ImprintConceptParser(mock_llm_caller)
        concept = parser.parse_concept(concept_text)
        
        expander = ImprintExpander(mock_llm_caller)
        expanded = expander.expand_concept(concept)
        
        validator = ImprintValidator()
        validation = validator.validate_expanded_imprint(expanded)
        
        # Should be high quality
        assert concept.confidence_score > 0.6
        assert validation.overall_score > 0.7
        assert expanded.branding.imprint_name
    
    def test_young_adult_fantasy_imprint(self, mock_llm_caller):
        """Test creating a YA fantasy imprint."""
        concept_text = """
        A young adult fantasy imprint targeting readers aged 13-18 with epic fantasy, 
        urban fantasy, and magical realism. Modern, exciting brand that connects with 
        teens through social media. Focus on diverse characters and contemporary themes.
        """
        
        parser = ImprintConceptParser(mock_llm_caller)
        concept = parser.parse_concept(concept_text)
        
        expander = ImprintExpander(mock_llm_caller)
        expanded = expander.expand_concept(concept)
        
        # Should identify YA characteristics
        assert 'young adult' in concept.target_audience.lower() or 'teen' in concept.target_audience.lower()
        assert any('fantasy' in genre.lower() for genre in expanded.publishing.primary_genres)
    
    def test_business_book_imprint(self, mock_llm_caller):
        """Test creating a business book imprint."""
        concept_text = """
        Professional business book imprint targeting entrepreneurs and business leaders. 
        Focus on practical guides, leadership, innovation, and startup advice. 
        Clean, professional brand identity that conveys authority and expertise.
        """
        
        parser = ImprintConceptParser(mock_llm_caller)
        concept = parser.parse_concept(concept_text)
        
        expander = ImprintExpander(mock_llm_caller)
        expanded = expander.expand_concept(concept)
        
        # Should identify business characteristics
        assert 'business' in concept.target_audience.lower() or 'entrepreneur' in concept.target_audience.lower()
        assert any('business' in genre.lower() for genre in expanded.publishing.primary_genres)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])