"""
Fallback LLM implementation for development when nimble-llm-caller is not available.
This is a minimal implementation to maintain compatibility.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMRequest:
    """Simple LLM request structure."""
    messages: List[Dict[str, str]]
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000


@dataclass
class LLMResponse:
    """Simple LLM response structure."""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None


class LLMCaller:
    """Fallback LLM caller that provides mock responses."""

    def call(self, request: LLMRequest, api_key: Optional[str] = None) -> LLMResponse:
        """
        Fallback implementation - returns mock persona data.
        In production, use nimble-llm-caller.
        """
        logger.warning("Using fallback LLM implementation - install nimble-llm-caller for full functionality")

        # Mock response for persona generation
        mock_persona = {
            "name": "Elena Rodriguez",
            "age": 32,
            "gender": "Female",
            "occupation": "Teacher",
            "country": "Spain",
            "year": 2023,
            "family_situation": "Married with two children",
            "education": "University degree in Education",
            "economic_status": "Middle class",
            "personality_traits": ["Kind", "Patient", "Creative"],
            "life_challenges": ["Work-life balance", "Supporting aging parents"],
            "cultural_background": "Spanish Catholic",
            "notable_events": ["Graduated university in 2013", "Started teaching career in 2014"]
        }

        mock_response = f'[{mock_persona}]'

        return LLMResponse(
            content=mock_response,
            model=request.model,
            usage={"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300}
        )