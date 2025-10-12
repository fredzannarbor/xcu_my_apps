"""
Token usage tracking for LLM calls.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Token usage information for a single LLM call."""
    model: str
    prompt_name: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    response_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    cost: Optional[float] = None


class TokenUsageTracker:
    """Tracks token usage across LLM calls."""
    
    def __init__(self):
        """Initialize token usage tracker."""
        self.usage_records: list[TokenUsage] = []
        self.total_tokens = 0
        self.total_cost = 0.0
    
    def record_usage(
        self,
        model: str,
        prompt_name: str,
        response: Any,
        response_time: float = 0.0
    ) -> None:
        """
        Record token usage from an LLM response.
        
        Args:
            model: Model name used
            prompt_name: Name/identifier of the prompt
            response: LLM response object
            response_time: Response time in seconds
        """
        try:
            # Extract token usage from response
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            
            if hasattr(response, 'usage'):
                usage = response.usage
                prompt_tokens = getattr(usage, 'prompt_tokens', 0)
                completion_tokens = getattr(usage, 'completion_tokens', 0)
                total_tokens = getattr(usage, 'total_tokens', 0)
            
            # Create usage record
            usage_record = TokenUsage(
                model=model,
                prompt_name=prompt_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                response_time=response_time
            )
            
            # Add to records
            self.usage_records.append(usage_record)
            self.total_tokens += total_tokens
            
            logger.debug(f"Recorded token usage: {total_tokens} tokens for {model} ({prompt_name})")
            
        except Exception as e:
            logger.warning(f"Failed to record token usage: {e}")
    
    def get_total_usage(self) -> Dict[str, Any]:
        """Get total usage statistics."""
        return {
            "total_calls": len(self.usage_records),
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "models_used": list(set(record.model for record in self.usage_records)),
            "prompts_used": list(set(record.prompt_name for record in self.usage_records))
        }
    
    def get_usage_by_model(self) -> Dict[str, Dict[str, Any]]:
        """Get usage statistics by model."""
        model_stats = {}
        
        for record in self.usage_records:
            if record.model not in model_stats:
                model_stats[record.model] = {
                    "calls": 0,
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_response_time": 0.0
                }
            
            stats = model_stats[record.model]
            stats["calls"] += 1
            stats["total_tokens"] += record.total_tokens
            stats["prompt_tokens"] += record.prompt_tokens
            stats["completion_tokens"] += record.completion_tokens
            stats["total_response_time"] += record.response_time
        
        return model_stats
    
    def clear(self) -> None:
        """Clear all usage records."""
        self.usage_records.clear()
        self.total_tokens = 0
        self.total_cost = 0.0
        logger.info("Token usage tracker cleared")