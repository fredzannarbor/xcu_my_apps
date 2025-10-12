"""
Unit tests for IdeationLLMService.
"""

import pytest
from unittest.mock import Mock, patch

from codexes.modules.ideation.llm.ideation_llm_service import (
    IdeationLLMService, IdeationLLMRequest, IdeationLLMResponse
)
from codexes.modules.ideation.core.codex_object import (
    CodexObject, CodexObjectType, DevelopmentStage
)


class TestIdeationLLMService:
    """Test cases for IdeationLLMService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.llm_service = IdeationLLMService()
    
    def test_service_initialization(self):
        """Test service initialization."""
        assert self.llm_service.llm_caller is not None
        assert self.llm_service.prompt_manager is not None
        assert self.llm_service.response_parser is not None
    
    def test_ideation_llm_request_creation(self):
        """Test IdeationLLMRequest dataclass."""
        request = IdeationLLMRequest(
            operation_type="generate_ideas",
            model="gpt-4o-mini",
            temperature=0.8,
            context_data={"genre": "Fantasy"},
            prompt_config={"type": "basic"}
        )
        
        assert request.operation_type == "generate_ideas"
        assert request.model == "gpt-4o-mini"
        assert request.temperature == 0.8
        assert request.context_data["genre"] == "Fantasy"
        assert request.prompt_config["type"] == "basic"
    
    def test_ideation_llm_response_creation(self):
        """Test IdeationLLMResponse dataclass."""
        response = IdeationLLMResponse(
            success=True,
            content="Generated content",
            parsed_data={"ideas": []},
            operation_type="generate_ideas",
            model_used="gpt-4o-mini"
        )
        
        assert response.success is True
        assert response.content == "Generated content"
        assert response.parsed_data == {"ideas": []}
        assert response.operation_type == "generate_ideas"
        assert response.model_used == "gpt-4o-mini"
    
    @patch('codexes.modules.ideation.llm.ideation_llm_service.enhanced_llm_caller')
    def test_generate_ideas_success(self, mock_llm_caller):
        """Test successful idea generation."""
        # Mock LLM response
        mock_llm_response = {
            'content': '''[
                {
                    "title": "The Time Gardener",
                    "logline": "A botanist discovers plants that grow through time instead of space.",
                    "description": "When Dr. Sarah Chen inherits her grandmother's greenhouse, she discovers that the plants inside don't grow upward—they grow through time, showing glimpses of past and future events.",
                    "themes": ["time", "nature", "inheritance"],
                    "genre": "Science Fiction"
                }
            ]''',
            'usage': {'total_tokens': 150},
            'attempts': 1
        }
        
        mock_llm_caller.call_llm_with_retry.return_value = mock_llm_response
        
        # Create request
        request = IdeationLLMRequest(
            operation_type="generate_ideas",
            context_data={"genre": "Science Fiction", "count": 1}
        )
        
        # Call service
        response = self.llm_service.generate_ideas(request)
        
        # Verify response
        assert response.success is True
        assert response.operation_type == "generate_ideas"
        assert response.parsed_data is not None
        assert "ideas" in response.parsed_data
        assert len(response.parsed_data["ideas"]) == 1
        assert response.parsed_data["ideas"][0]["title"] == "The Time Gardener"
    
    @patch('codexes.modules.ideation.llm.ideation_llm_service.enhanced_llm_caller')
    def test_generate_ideas_failure(self, mock_llm_caller):
        """Test idea generation failure."""
        # Mock LLM failure
        mock_llm_caller.call_llm_with_retry.return_value = None
        
        request = IdeationLLMRequest(operation_type="generate_ideas")
        response = self.llm_service.generate_ideas(request)
        
        assert response.success is False
        assert "LLM failed" in response.error_message
    
    @patch('codexes.modules.ideation.llm.ideation_llm_service.enhanced_llm_caller')
    def test_evaluate_tournament_match_success(self, mock_llm_caller):
        """Test successful tournament match evaluation."""
        # Mock LLM response
        mock_llm_response = {
            "winner": "A",
            "reasoning": "Concept A has stronger character development and more original premise.",
            "scores": {
                "concept_a": {
                    "originality": 8,
                    "marketability": 7,
                    "execution_potential": 8,
                    "emotional_impact": 7,
                    "total": 30
                },
                "concept_b": {
                    "originality": 6,
                    "marketability": 8,
                    "execution_potential": 6,
                    "emotional_impact": 6,
                    "total": 26
                }
            },
            "strengths_a": ["Original premise", "Strong characters"],
            "strengths_b": ["Market appeal", "Clear genre"],
            "weaknesses_a": ["Complex execution"],
            "weaknesses_b": ["Less original", "Predictable plot"]
        }
        
        mock_llm_caller.call_llm_json_with_retry.return_value = mock_llm_response
        
        # Create test objects
        obj1 = CodexObject(
            title="The Time Gardener",
            content="A story about time-traveling plants",
            object_type=CodexObjectType.IDEA
        )
        
        obj2 = CodexObject(
            title="Space Detective",
            content="A detective solves crimes in space",
            object_type=CodexObjectType.IDEA
        )
        
        # Call service
        response = self.llm_service.evaluate_tournament_match(obj1, obj2)
        
        # Verify response
        assert response.success is True
        assert response.operation_type == "tournament_evaluation"
        assert response.parsed_data["winner_uuid"] == obj1.uuid
        assert response.parsed_data["winner_choice"] == "A"
        assert "stronger character development" in response.parsed_data["reasoning"]
    
    @patch('codexes.modules.ideation.llm.ideation_llm_service.enhanced_llm_caller')
    def test_simulate_reader_evaluation_success(self, mock_llm_caller):
        """Test successful reader evaluation simulation."""
        # Mock LLM response
        mock_llm_response = {
            "rating": 4,
            "would_read": True,
            "interest_level": "high",
            "feedback": "This concept really appeals to me as a sci-fi fan. The idea of time-traveling plants is unique and intriguing.",
            "appeal_factors": ["Unique premise", "Science fiction elements", "Nature theme"],
            "concerns": ["Might be too complex", "Execution challenges"],
            "demographic_fit": "Perfect match for sci-fi enthusiasts",
            "recommendation_likelihood": 4
        }
        
        mock_llm_caller.call_llm_json_with_retry.return_value = mock_llm_response
        
        # Create test object and reader persona
        obj = CodexObject(
            title="The Time Gardener",
            content="A botanist discovers plants that grow through time",
            object_type=CodexObjectType.SYNOPSIS,
            genre="Science Fiction"
        )
        
        reader_persona = {
            "id": "reader_001",
            "demographics": "Female, 25-35, college educated",
            "preferences": "Science fiction, fantasy, nature themes",
            "experience_level": "Avid reader",
            "reading_goals": "Entertainment and escapism"
        }
        
        # Call service
        response = self.llm_service.simulate_reader_evaluation(obj, reader_persona)
        
        # Verify response
        assert response.success is True
        assert response.operation_type == "reader_evaluation"
        assert response.parsed_data["rating"] == 4
        assert response.parsed_data["would_read"] is True
        assert response.parsed_data["interest_level"] == "high"
        assert response.parsed_data["reader_id"] == "reader_001"
    
    @patch('codexes.modules.ideation.llm.ideation_llm_service.enhanced_llm_caller')
    def test_extract_story_elements_success(self, mock_llm_caller):
        """Test successful story element extraction."""
        # Mock LLM response
        mock_llm_response = {
            "elements": {
                "characters": [
                    {
                        "name": "Dr. Sarah Chen",
                        "role": "Protagonist",
                        "description": "A botanist who inherits her grandmother's greenhouse",
                        "extraction_confidence": 0.9
                    }
                ],
                "settings": [
                    {
                        "name": "The Greenhouse",
                        "description": "A mysterious greenhouse with time-traveling plants",
                        "importance": "Primary",
                        "extraction_confidence": 0.8
                    }
                ],
                "themes": [
                    {
                        "theme": "Time and Memory",
                        "description": "Exploration of how past and future connect",
                        "prominence": "Major",
                        "extraction_confidence": 0.7
                    }
                ]
            },
            "overall_analysis": "Rich story with clear characters and unique premise",
            "extraction_quality": "High quality extraction with clear elements"
        }
        
        mock_llm_caller.call_llm_json_with_retry.return_value = mock_llm_response
        
        # Create test object
        obj = CodexObject(
            title="The Time Gardener",
            content="Dr. Sarah Chen inherits her grandmother's greenhouse and discovers plants that grow through time, showing glimpses of past and future events.",
            object_type=CodexObjectType.SYNOPSIS
        )
        
        # Call service
        response = self.llm_service.extract_story_elements(obj, ["characters", "settings", "themes"])
        
        # Verify response
        assert response.success is True
        assert response.operation_type == "element_extraction"
        assert "characters" in response.parsed_data["elements"]
        assert "settings" in response.parsed_data["elements"]
        assert "themes" in response.parsed_data["elements"]
        assert response.parsed_data["total_elements"] == 3
        assert response.parsed_data["average_confidence"] > 0.7
    
    def test_get_service_stats(self):
        """Test getting service statistics."""
        stats = self.llm_service.get_service_stats()
        
        assert "service_name" in stats
        assert "available_operations" in stats
        assert "default_model" in stats
        assert stats["service_name"] == "IdeationLLMService"
        assert "generate_ideas" in stats["available_operations"]
        assert "evaluate_tournament_match" in stats["available_operations"]
    
    @patch('codexes.modules.ideation.llm.ideation_llm_service.enhanced_llm_caller')
    def test_batch_process_objects(self, mock_llm_caller):
        """Test batch processing of objects."""
        # Mock LLM response for enhancement
        mock_llm_response = {
            'content': 'Enhanced content with more detail and better structure.',
            'usage': {'total_tokens': 100},
            'attempts': 1
        }
        
        mock_llm_caller.call_llm_with_retry.return_value = mock_llm_response
        
        # Create test objects
        objects = [
            CodexObject(title="Idea 1", content="Basic idea content", object_type=CodexObjectType.IDEA),
            CodexObject(title="Idea 2", content="Another basic idea", object_type=CodexObjectType.IDEA)
        ]
        
        # Call batch processing
        responses = self.llm_service.batch_process_objects(
            objects, 
            "enhance", 
            {"enhancement_type": "general"}
        )
        
        # Verify responses
        assert len(responses) == 2
        assert all(response.success for response in responses)
        assert all(response.operation_type == "content_enhancement" for response in responses)


class TestIdeationLLMDataClasses:
    """Test cases for ideation LLM data classes."""
    
    def test_ideation_llm_request_defaults(self):
        """Test IdeationLLMRequest with default values."""
        request = IdeationLLMRequest(operation_type="test")
        
        assert request.operation_type == "test"
        assert request.model == "gpt-4o-mini"
        assert request.temperature == 0.7
        assert request.max_tokens is None
        assert request.context_data == {}
        assert request.prompt_config == {}
    
    def test_ideation_llm_response_defaults(self):
        """Test IdeationLLMResponse with default values."""
        response = IdeationLLMResponse(
            success=True,
            content="test content",
            parsed_data={"test": "data"},
            operation_type="test",
            model_used="gpt-4o-mini"
        )
        
        assert response.success is True
        assert response.content == "test content"
        assert response.parsed_data == {"test": "data"}
        assert response.operation_type == "test"
        assert response.model_used == "gpt-4o-mini"
        assert response.error_message == ""
        assert response.metadata == {}


class TestIdeationLLMIntegration:
    """Integration tests for ideation LLM service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.llm_service = IdeationLLMService()
    
    def test_service_component_integration(self):
        """Test that all service components work together."""
        # Test that prompt manager can generate prompts
        prompt = self.llm_service.prompt_manager.get_idea_generation_prompt(
            {"genre": "Fantasy", "count": 1},
            {"type": "basic"}
        )
        assert "Fantasy" in prompt
        assert "1" in prompt
        
        # Test that response parser can handle basic parsing
        test_response = '[{"title": "Test Idea", "description": "Test description", "logline": "A test logline", "themes": ["test"], "elements": ["element1"]}]'
        parsed = self.llm_service.response_parser.parse_idea_generation_response(test_response)
        assert parsed["parsing_success"] is True
        assert len(parsed["ideas"]) == 1
    
    def test_error_handling_integration(self):
        """Test error handling across service components."""
        # Test with invalid JSON response
        invalid_response = "This is not valid JSON"
        parsed = self.llm_service.response_parser.parse_idea_generation_response(invalid_response)
        
        # Should handle gracefully
        assert parsed["parsing_success"] is False or parsed["format"] == "text_extracted"
        assert "ideas" in parsed