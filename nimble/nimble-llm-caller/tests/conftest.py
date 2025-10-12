"""
Pytest configuration and fixtures for nimble-llm-caller tests.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock

from nimble_llm_caller import LLMContentGenerator, LLMCaller, PromptManager
from nimble_llm_caller.models.request import LLMRequest, ResponseFormat
from nimble_llm_caller.models.response import LLMResponse, ResponseStatus


@pytest.fixture
def sample_prompts():
    """Sample prompts for testing."""
    return {
        "simple_prompt": {
            "messages": [
                {"role": "user", "content": "Say hello to {name}"}
            ],
            "params": {
                "temperature": 0.7,
                "max_tokens": 100
            }
        },
        "complex_prompt": {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Analyze {topic} and provide {detail_level} details."}
            ],
            "params": {
                "temperature": 0.3,
                "max_tokens": 500
            }
        },
        "json_prompt": {
            "messages": [
                {"role": "user", "content": "Extract metadata from: {content}"}
            ],
            "params": {
                "temperature": 0.1,
                "max_tokens": 200
            }
        }
    }


@pytest.fixture
def temp_prompts_file(sample_prompts):
    """Create a temporary prompts file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_prompts, f, indent=2)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def mock_litellm_response():
    """Mock LiteLLM response."""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "Test response content"
    mock_response.usage = Mock()
    mock_response.usage.dict.return_value = {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30
    }
    mock_response.model = "gpt-4o"
    return mock_response


@pytest.fixture
def mock_llm_caller():
    """Mock LLM caller for testing."""
    caller = Mock(spec=LLMCaller)
    
    # Mock successful response
    success_response = LLMResponse(
        prompt_key="test_prompt",
        model="gpt-4o",
        status=ResponseStatus.SUCCESS,
        content="Test response content",
        parsed_content={"result": "test"},
        execution_time=1.5,
        attempts=1,
        tokens_used={"total_tokens": 30}
    )
    
    caller.call.return_value = success_response
    caller.get_statistics.return_value = {
        "total_calls": 1,
        "successful_calls": 1,
        "failed_calls": 0,
        "success_rate": 100.0
    }
    
    return caller


@pytest.fixture
def sample_llm_request():
    """Sample LLM request for testing."""
    return LLMRequest(
        prompt_key="test_prompt",
        model="gpt-4o",
        substitutions={"name": "World"},
        response_format=ResponseFormat.TEXT,
        model_params={"temperature": 0.7}
    )


@pytest.fixture
def sample_llm_response():
    """Sample LLM response for testing."""
    return LLMResponse(
        prompt_key="test_prompt",
        model="gpt-4o",
        status=ResponseStatus.SUCCESS,
        content="Hello World!",
        parsed_content=None,
        execution_time=1.2,
        attempts=1,
        tokens_used={"total_tokens": 25}
    )


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def content_generator(temp_prompts_file, temp_output_dir):
    """Content generator with temporary files."""
    return LLMContentGenerator(
        prompt_file_path=temp_prompts_file,
        output_dir=temp_output_dir,
        default_model="gpt-4o"
    )


@pytest.fixture
def prompt_manager(temp_prompts_file):
    """Prompt manager with temporary prompts file."""
    return PromptManager(temp_prompts_file)


# Environment variable fixtures
@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for API keys."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")


# JSON test data
@pytest.fixture
def sample_json_responses():
    """Sample JSON responses for testing parsing."""
    return {
        "valid_json": '{"title": "Test Title", "summary": "Test summary"}',
        "json_with_markdown": '```json\n{"title": "Test Title", "summary": "Test summary"}\n```',
        "malformed_json": '{"title": "Test Title", "summary": "Test summary"',  # Missing closing brace
        "conversational_response": "The title is 'Test Title' and the summary is 'Test summary'.",
        "empty_response": "",
        "none_response": None
    }


@pytest.fixture
def sample_batch_responses():
    """Sample batch responses for testing."""
    return [
        LLMResponse(
            prompt_key="prompt_1",
            model="gpt-4o",
            status=ResponseStatus.SUCCESS,
            content="Response 1",
            execution_time=1.0
        ),
        LLMResponse(
            prompt_key="prompt_2", 
            model="claude-3-sonnet",
            status=ResponseStatus.SUCCESS,
            content="Response 2",
            execution_time=1.5
        ),
        LLMResponse(
            prompt_key="prompt_3",
            model="gpt-4o",
            status=ResponseStatus.ERROR,
            error_message="Test error",
            execution_time=0.5
        )
    ]