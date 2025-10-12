"""
Unit tests for LLM caller module.
"""

import pytest
from unittest.mock import Mock, patch
import json

from trillions_of_people.core.llm_caller import (
    TrillionsLLMCaller,
    PersonaGenerationRequest
)


class TestPersonaGenerationRequest:
    """Test cases for PersonaGenerationRequest dataclass."""

    def test_basic_request(self):
        """Test basic request creation."""
        request = PersonaGenerationRequest(
            country="United States",
            year=2024,
            count=1
        )
        assert request.country == "United States"
        assert request.year == 2024
        assert request.count == 1
        assert request.additional_context is None

    def test_request_with_context(self):
        """Test request with additional context."""
        request = PersonaGenerationRequest(
            country="France",
            year=1789,
            count=2,
            additional_context="French Revolution period"
        )
        assert request.additional_context == "French Revolution period"


class TestTrillionsLLMCaller:
    """Test cases for TrillionsLLMCaller class."""

    @patch('trillions_of_people.core.llm_caller.LLMCaller')
    def test_init_with_api_key(self, mock_llm_caller):
        """Test initialization with API key."""
        caller = TrillionsLLMCaller(api_key="test-key")
        assert caller.api_key == "test-key"
        mock_llm_caller.assert_called_once()

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'env-key'})
    @patch('trillions_of_people.core.llm_caller.LLMCaller')
    def test_init_with_env_key(self, mock_llm_caller):
        """Test initialization with environment variable."""
        caller = TrillionsLLMCaller()
        assert caller.api_key == "env-key"

    def test_init_without_key_raises_error(self):
        """Test that initialization without API key raises error."""
        with pytest.raises(ValueError, match="No API key provided"):
            TrillionsLLMCaller()

    @patch('trillions_of_people.core.llm_caller.LLMCaller')
    def test_generate_personas_success(self, mock_llm_caller):
        """Test successful persona generation."""
        # Setup mock
        mock_instance = Mock()
        mock_llm_caller.return_value = mock_instance
        mock_response = Mock()
        mock_response.content = json.dumps([
            {
                "name": "Marie Dubois",
                "age": 25,
                "gender": "Female",
                "occupation": "Seamstress",
                "country": "France"
            }
        ])
        mock_instance.call.return_value = mock_response

        # Test
        caller = TrillionsLLMCaller(api_key="test-key")
        request = PersonaGenerationRequest(
            country="France",
            year=1850,
            count=1
        )

        personas = caller.generate_personas(request)

        assert len(personas) == 1
        assert personas[0]["name"] == "Marie Dubois"
        assert personas[0]["occupation"] == "Seamstress"

    @patch('trillions_of_people.core.llm_caller.LLMCaller')
    def test_generate_personas_llm_error(self, mock_llm_caller):
        """Test persona generation with LLM error."""
        # Setup mock to raise error
        mock_instance = Mock()
        mock_llm_caller.return_value = mock_instance
        mock_instance.call.side_effect = Exception("API Error")

        # Test
        caller = TrillionsLLMCaller(api_key="test-key")
        request = PersonaGenerationRequest(
            country="France",
            year=1850,
            count=1
        )

        with pytest.raises(Exception, match="API Error"):
            caller.generate_personas(request)

    def test_build_system_prompt(self):
        """Test system prompt building."""
        caller = TrillionsLLMCaller(api_key="test-key")
        prompt = caller._build_system_prompt()

        assert "historical demographer" in prompt.lower()
        assert "synthetic personas" in prompt.lower()
        assert "json" in prompt.lower()

    def test_build_persona_prompt(self):
        """Test persona prompt building."""
        caller = TrillionsLLMCaller(api_key="test-key")
        request = PersonaGenerationRequest(
            country="Japan",
            year=1600,
            count=2,
            additional_context="Edo period beginning"
        )

        prompt = caller._build_persona_prompt(request)

        assert "Japan" in prompt
        assert "1600" in prompt
        assert "2" in prompt
        assert "Edo period beginning" in prompt

    def test_get_era_description_ancient(self):
        """Test era description for ancient times."""
        caller = TrillionsLLMCaller(api_key="test-key")

        desc_bce = caller._get_era_description(-500)
        assert "500 BCE" in desc_bce
        assert "ancient times" in desc_bce

        desc_early_ce = caller._get_era_description(300)
        assert "300 CE" in desc_early_ce
        assert "classical" in desc_early_ce.lower()

    def test_get_era_description_medieval(self):
        """Test era description for medieval times."""
        caller = TrillionsLLMCaller(api_key="test-key")

        desc = caller._get_era_description(1200)
        assert "1200 CE" in desc
        assert "medieval" in desc.lower()

    def test_get_era_description_modern(self):
        """Test era description for modern times."""
        caller = TrillionsLLMCaller(api_key="test-key")

        desc_industrial = caller._get_era_description(1850)
        assert "1850 CE" in desc_industrial
        assert "industrial" in desc_industrial.lower()

        desc_20th = caller._get_era_description(1950)
        assert "1950 CE" in desc_20th
        assert "20th century" in desc_20th

    def test_get_era_description_future(self):
        """Test era description for future dates."""
        caller = TrillionsLLMCaller(api_key="test-key")

        desc = caller._get_era_description(2100)
        assert "2100 CE" in desc
        assert "future" in desc.lower()
        assert "trends" in desc.lower()

    def test_parse_persona_response_valid_json(self):
        """Test parsing valid JSON response."""
        caller = TrillionsLLMCaller(api_key="test-key")

        json_response = '[{"name": "Test Person", "age": 30}]'
        result = caller._parse_persona_response(json_response)

        assert len(result) == 1
        assert result[0]["name"] == "Test Person"
        assert result[0]["age"] == 30

    def test_parse_persona_response_markdown_json(self):
        """Test parsing JSON in markdown code blocks."""
        caller = TrillionsLLMCaller(api_key="test-key")

        markdown_response = '''Here are the personas:

```json
[{"name": "Test Person", "age": 30}]
```

Hope this helps!'''

        result = caller._parse_persona_response(markdown_response)

        assert len(result) == 1
        assert result[0]["name"] == "Test Person"

    def test_parse_persona_response_invalid_json(self):
        """Test parsing invalid JSON response."""
        caller = TrillionsLLMCaller(api_key="test-key")

        invalid_response = "This is not valid JSON at all"
        result = caller._parse_persona_response(invalid_response)

        assert len(result) == 1
        assert "description" in result[0]
        assert result[0]["parsing_failed"] is True

    def test_parse_persona_response_exception(self):
        """Test parsing response with exception."""
        caller = TrillionsLLMCaller(api_key="test-key")

        # This should trigger the exception handler
        with patch('json.loads', side_effect=Exception("JSON Error")):
            result = caller._parse_persona_response('{"invalid": json}')

            assert len(result) == 1
            assert "error" in result[0]
            assert "raw_content" in result[0]