"""
Token usage tracking system for LLM calls.

This module provides functionality to track token usage and calculate costs
using LiteLLM's built-in pricing information and cost calculation features.
"""

import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import litellm

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    """Record of a single LLM call's usage statistics."""
    model: str
    prompt_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: Optional[float]
    timestamp: datetime
    response_time: Optional[float] = None
    
    @property
    def cost_per_token(self) -> Optional[float]:
        """Calculate cost per token if cost is available."""
        if self.cost is not None and self.total_tokens > 0:
            return self.cost / self.total_tokens
        return None


@dataclass
class ModelStats:
    """Aggregated statistics for a specific model."""
    model: str
    call_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost: Optional[float] = None
    average_response_time: Optional[float] = None
    
    def add_record(self, record: UsageRecord) -> None:
        """Add a usage record to this model's statistics."""
        self.call_count += 1
        self.total_input_tokens += record.input_tokens
        self.total_output_tokens += record.output_tokens
        self.total_tokens += record.total_tokens
        
        # Add cost if available
        if record.cost is not None:
            if self.total_cost is None:
                self.total_cost = 0.0
            self.total_cost += record.cost
        
        # Update average response time
        if record.response_time is not None:
            if self.average_response_time is None:
                self.average_response_time = record.response_time
            else:
                # Calculate running average
                self.average_response_time = (
                    (self.average_response_time * (self.call_count - 1) + record.response_time) 
                    / self.call_count
                )


@dataclass
class PromptStats:
    """Aggregated statistics for a specific prompt type."""
    prompt_name: str
    call_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost: Optional[float] = None
    models_used: Dict[str, int] = field(default_factory=dict)
    
    def add_record(self, record: UsageRecord) -> None:
        """Add a usage record to this prompt's statistics."""
        self.call_count += 1
        self.total_input_tokens += record.input_tokens
        self.total_output_tokens += record.output_tokens
        self.total_tokens += record.total_tokens
        
        # Add cost if available
        if record.cost is not None:
            if self.total_cost is None:
                self.total_cost = 0.0
            self.total_cost += record.cost
        
        # Track models used
        if record.model in self.models_used:
            self.models_used[record.model] += 1
        else:
            self.models_used[record.model] = 1


class TokenUsageTracker:
    """
    Tracks token usage and costs for LLM calls using LiteLLM's built-in features.
    
    This class collects usage data from LiteLLM responses and calculates costs
    using LiteLLM's completion_cost function, which has built-in pricing information
    for various models.
    """
    
    def __init__(self):
        """Initialize the token usage tracker."""
        self.records: List[UsageRecord] = []
        self.model_stats: Dict[str, ModelStats] = {}
        self.prompt_stats: Dict[str, PromptStats] = {}
        self.start_time = datetime.now()
        logger.debug("TokenUsageTracker initialized")
    
    def record_usage(
        self,
        model: str,
        prompt_name: str,
        response: Any,
        response_time: Optional[float] = None
    ) -> None:
        """
        Record token usage from a LiteLLM response.
        
        Args:
            model: The model name used for the call
            prompt_name: Name/identifier of the prompt used
            response: LiteLLM response object containing usage data
            response_time: Optional response time in seconds
        """
        try:
            # Extract usage data from LiteLLM response
            usage_data = self._extract_usage_from_response(response)
            if not usage_data:
                logger.warning(f"No usage data found in response for {model}/{prompt_name}")
                return
            
            # Calculate cost using LiteLLM's built-in cost calculation
            cost = self._calculate_cost(response, model)
            
            # Create usage record
            record = UsageRecord(
                model=model,
                prompt_name=prompt_name,
                input_tokens=usage_data.get('prompt_tokens', 0),
                output_tokens=usage_data.get('completion_tokens', 0),
                total_tokens=usage_data.get('total_tokens', 0),
                cost=cost,
                timestamp=datetime.now(),
                response_time=response_time
            )
            
            # Store the record
            self.records.append(record)
            
            # Update aggregated statistics
            self._update_model_stats(record)
            self._update_prompt_stats(record)
            
            logger.debug(
                f"Recorded usage for {model}/{prompt_name}: "
                f"{record.total_tokens} tokens, ${cost:.4f}" if cost else f"{record.total_tokens} tokens"
            )
            
        except Exception as e:
            logger.error(f"Error recording usage for {model}/{prompt_name}: {e}", exc_info=True)
    
    def _extract_usage_from_response(self, response: Any) -> Optional[Dict[str, int]]:
        """
        Extract usage data from LiteLLM response object.
        
        Args:
            response: LiteLLM response object
            
        Returns:
            Dictionary with token usage data or None if not available
        """
        try:
            # LiteLLM response objects have a usage attribute
            if hasattr(response, 'usage') and response.usage:
                usage = response.usage
                return {
                    'prompt_tokens': getattr(usage, 'prompt_tokens', 0),
                    'completion_tokens': getattr(usage, 'completion_tokens', 0),
                    'total_tokens': getattr(usage, 'total_tokens', 0)
                }
            
            # Fallback: check if response is a dict with usage data
            if isinstance(response, dict) and 'usage' in response:
                usage = response['usage']
                return {
                    'prompt_tokens': usage.get('prompt_tokens', 0),
                    'completion_tokens': usage.get('completion_tokens', 0),
                    'total_tokens': usage.get('total_tokens', 0)
                }
            
            logger.debug("No usage data found in response object")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting usage data: {e}")
            return None
    
    def _calculate_cost(self, response: Any, model: str) -> Optional[float]:
        """
        Calculate cost using LiteLLM's built-in cost calculation.
        
        Args:
            response: LiteLLM response object
            model: Model name for fallback cost calculation
            
        Returns:
            Cost in USD or None if calculation fails
        """
        try:
            # Use LiteLLM's built-in cost calculation
            cost = litellm.completion_cost(completion_response=response)
            if cost is not None and cost > 0:
                return float(cost)
            
            # Fallback: try with model parameter if direct calculation fails
            if hasattr(response, 'usage') and response.usage:
                cost = litellm.completion_cost(
                    completion_response=response,
                    model=model
                )
                if cost is not None and cost > 0:
                    return float(cost)
            
            logger.debug(f"Cost calculation returned None or 0 for model {model}")
            return None
            
        except Exception as e:
            logger.warning(f"Error calculating cost for model {model}: {e}")
            return None
    
    def _update_model_stats(self, record: UsageRecord) -> None:
        """Update aggregated statistics for the model."""
        if record.model not in self.model_stats:
            self.model_stats[record.model] = ModelStats(model=record.model)
        
        self.model_stats[record.model].add_record(record)
    
    def _update_prompt_stats(self, record: UsageRecord) -> None:
        """Update aggregated statistics for the prompt."""
        if record.prompt_name not in self.prompt_stats:
            self.prompt_stats[record.prompt_name] = PromptStats(prompt_name=record.prompt_name)
        
        self.prompt_stats[record.prompt_name].add_record(record)
    
    def get_total_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive usage statistics.
        
        Returns:
            Dictionary containing total usage statistics
        """
        total_input_tokens = sum(record.input_tokens for record in self.records)
        total_output_tokens = sum(record.output_tokens for record in self.records)
        total_tokens = sum(record.total_tokens for record in self.records)
        
        # Calculate total cost (only from records that have cost data)
        costs = [record.cost for record in self.records if record.cost is not None]
        total_cost = sum(costs) if costs else None
        
        # Calculate duration
        duration = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'total_calls': len(self.records),
            'total_input_tokens': total_input_tokens,
            'total_output_tokens': total_output_tokens,
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'duration_seconds': duration,
            'models_used': list(self.model_stats.keys()),
            'prompts_used': list(self.prompt_stats.keys()),
            'cost_available_calls': len(costs),
            'average_cost_per_call': total_cost / len(costs) if costs else None,
            'tokens_per_second': total_tokens / duration if duration > 0 else 0
        }
    
    def get_model_breakdown(self) -> Dict[str, ModelStats]:
        """Get statistics broken down by model."""
        return self.model_stats.copy()
    
    def get_prompt_breakdown(self) -> Dict[str, PromptStats]:
        """Get statistics broken down by prompt type."""
        return self.prompt_stats.copy()
    
    def reset(self) -> None:
        """Reset all tracking data."""
        self.records.clear()
        self.model_stats.clear()
        self.prompt_stats.clear()
        self.start_time = datetime.now()
        logger.debug("TokenUsageTracker reset")
    
    def get_recent_records(self, limit: int = 10) -> List[UsageRecord]:
        """
        Get the most recent usage records.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of recent usage records
        """
        return self.records[-limit:] if self.records else []