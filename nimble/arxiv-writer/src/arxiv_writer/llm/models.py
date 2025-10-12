"""
LLM-related data models.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LLMConfig:
    """Configuration for LLM calls."""
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 60
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class LLMResponse:
    """Response from LLM call."""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    response_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMError(Exception):
    """Exception raised for LLM-related errors."""
    pass
