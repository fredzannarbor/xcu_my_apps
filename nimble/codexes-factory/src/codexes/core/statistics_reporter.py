"""
Statistics reporter for end-of-pipeline summaries.

This module provides functionality to generate comprehensive reports of token usage
and cost statistics collected during pipeline execution.
"""

import logging
from typing import Dict, Any, Optional
from datetime import timedelta

from .token_usage_tracker import TokenUsageTracker, ModelStats, PromptStats
from .logging_filters import log_success

logger = logging.getLogger(__name__)


class StatisticsReporter:
    """
    Reports token usage and cost statistics in a readable format.
    
    This class takes data from TokenUsageTracker and formats it into
    comprehensive reports suitable for logging or display.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the statistics reporter.
        
        Args:
            config: Optional configuration dictionary for reporting behavior.
                   If None, will attempt to load from logging configuration.
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration, attempting to load from logging config."""
        try:
            from .logging_config import get_statistics_config
            return get_statistics_config()
        except ImportError:
            # Fallback to default configuration if logging_config is not available
            return {
                "enabled": True,
                "detail_level": "standard",
                "include_model_breakdown": True,
                "include_prompt_breakdown": True,
                "include_cost_analysis": True,
                "include_timing_analysis": False,
                "include_performance_metrics": False
            }
    
    def report_pipeline_statistics(self, tracker: TokenUsageTracker) -> None:
        """
        Generate and log a comprehensive pipeline statistics report.
        
        Args:
            tracker: TokenUsageTracker instance with collected statistics
        """
        # Check if statistics reporting is enabled
        if not self.config.get("enabled", True):
            return
        
        try:
            # Get overall statistics
            total_stats = tracker.get_total_statistics()
            
            if total_stats['total_calls'] == 0:
                log_success(self.logger, "📊 Pipeline Statistics: No LLM calls recorded")
                return
            
            # Generate the main report based on detail level
            detail_level = self.config.get("detail_level", "standard")
            
            if detail_level == "minimal":
                self._log_minimal_summary(total_stats)
            elif detail_level == "summary":
                self._log_summary_report(total_stats, tracker)
            elif detail_level == "detailed":
                self._log_detailed_report(total_stats, tracker)
            else:  # standard
                self._log_standard_report(total_stats, tracker)
            
        except Exception as e:
            self.logger.error(f"Error generating pipeline statistics report: {e}", exc_info=True)
    
    def _log_minimal_summary(self, stats: Dict[str, Any]) -> None:
        """Log minimal statistics summary."""
        log_success(self.logger, "📊 Pipeline Statistics:")
        self.logger.info(f"   • {stats['total_calls']:,} LLM calls, {stats['total_tokens']:,} tokens")
        if stats['total_cost'] is not None:
            self.logger.info(f"   • Total cost: ${stats['total_cost']:.4f}")
    
    def _log_summary_report(self, stats: Dict[str, Any], tracker: TokenUsageTracker) -> None:
        """Log summary statistics report."""
        self.logger.info("=" * 50)
        log_success(self.logger, "📊 PIPELINE STATISTICS")
        self.logger.info("=" * 50)
        
        # Overall summary
        self._log_overall_summary(stats)
        
        # Model breakdown if enabled
        if self.config.get("include_model_breakdown", True):
            model_breakdown = tracker.get_model_breakdown()
            if model_breakdown:
                self._log_model_breakdown(model_breakdown)
        
        # Cost summary if enabled
        if self.config.get("include_cost_analysis", True):
            model_breakdown = tracker.get_model_breakdown()
            self._log_cost_summary(stats, model_breakdown)
        
        self.logger.info("=" * 50)
    
    def _log_standard_report(self, stats: Dict[str, Any], tracker: TokenUsageTracker) -> None:
        """Log standard statistics report."""
        self.logger.info("=" * 60)
        log_success(self.logger, "📊 PIPELINE STATISTICS SUMMARY")
        self.logger.info("=" * 60)
        
        # Overall summary
        self._log_overall_summary(stats)
        
        # Model breakdown if enabled
        if self.config.get("include_model_breakdown", True):
            model_breakdown = tracker.get_model_breakdown()
            if model_breakdown:
                self._log_model_breakdown(model_breakdown)
        
        # Prompt breakdown if enabled
        if self.config.get("include_prompt_breakdown", True):
            prompt_breakdown = tracker.get_prompt_breakdown()
            if prompt_breakdown:
                self._log_prompt_breakdown(prompt_breakdown)
        
        # Cost summary if enabled
        if self.config.get("include_cost_analysis", True):
            model_breakdown = tracker.get_model_breakdown()
            self._log_cost_summary(stats, model_breakdown)
        
        self.logger.info("=" * 60)
    
    def _log_detailed_report(self, stats: Dict[str, Any], tracker: TokenUsageTracker) -> None:
        """Log detailed statistics report with timing and performance metrics."""
        self.logger.info("=" * 70)
        log_success(self.logger, "📊 DETAILED PIPELINE STATISTICS")
        self.logger.info("=" * 70)
        
        # Overall summary
        self._log_overall_summary(stats)
        
        # Performance metrics if enabled
        if self.config.get("include_performance_metrics", False):
            self._log_performance_metrics(stats)
        
        # Model breakdown if enabled
        if self.config.get("include_model_breakdown", True):
            model_breakdown = tracker.get_model_breakdown()
            if model_breakdown:
                self._log_model_breakdown(model_breakdown)
        
        # Prompt breakdown if enabled
        if self.config.get("include_prompt_breakdown", True):
            prompt_breakdown = tracker.get_prompt_breakdown()
            if prompt_breakdown:
                self._log_prompt_breakdown(prompt_breakdown)
        
        # Timing analysis if enabled
        if self.config.get("include_timing_analysis", False):
            self._log_timing_analysis(tracker)
        
        # Cost summary if enabled
        if self.config.get("include_cost_analysis", True):
            model_breakdown = tracker.get_model_breakdown()
            self._log_cost_summary(stats, model_breakdown)
        
        self.logger.info("=" * 70)
    
    def _log_performance_metrics(self, stats: Dict[str, Any]) -> None:
        """Log performance metrics."""
        self.logger.info("⚡ Performance Metrics:")
        self.logger.info(f"   • Tokens per Second: {stats['tokens_per_second']:.1f}")
        
        if stats['total_calls'] > 0 and stats['duration_seconds'] > 0:
            calls_per_second = stats['total_calls'] / stats['duration_seconds']
            self.logger.info(f"   • Calls per Second: {calls_per_second:.2f}")
            
            avg_tokens_per_call = stats['total_tokens'] / stats['total_calls']
            self.logger.info(f"   • Average Tokens per Call: {avg_tokens_per_call:.1f}")
        
        self.logger.info("")
    
    def _log_timing_analysis(self, tracker: TokenUsageTracker) -> None:
        """Log timing analysis."""
        model_breakdown = tracker.get_model_breakdown()
        
        self.logger.info("⏱️ Timing Analysis:")
        
        for model_name, stats in model_breakdown.items():
            if stats.average_response_time is not None:
                self.logger.info(f"   📱 {model_name}:")
                self.logger.info(f"      • Avg Response Time: {stats.average_response_time:.2f}s")
                
                if stats.call_count > 0:
                    tokens_per_second = stats.total_tokens / (stats.average_response_time * stats.call_count)
                    self.logger.info(f"      • Tokens per Second: {tokens_per_second:.1f}")
        
        self.logger.info("")
    
    def _log_overall_summary(self, stats: Dict[str, Any]) -> None:
        """Log the overall pipeline summary."""
        duration = timedelta(seconds=int(stats['duration_seconds']))
        
        self.logger.info("📈 Overall Summary:")
        self.logger.info(f"   • Total LLM Calls: {stats['total_calls']:,}")
        self.logger.info(f"   • Total Tokens: {stats['total_tokens']:,}")
        self.logger.info(f"     - Input Tokens: {stats['total_input_tokens']:,}")
        self.logger.info(f"     - Output Tokens: {stats['total_output_tokens']:,}")
        self.logger.info(f"   • Pipeline Duration: {duration}")
        self.logger.info(f"   • Processing Rate: {stats['tokens_per_second']:.1f} tokens/second")
        
        if stats['total_cost'] is not None:
            self.logger.info(f"   • Total Cost: ${stats['total_cost']:.4f}")
            if stats['average_cost_per_call']:
                self.logger.info(f"   • Average Cost/Call: ${stats['average_cost_per_call']:.4f}")
        else:
            self.logger.info("   • Cost: Not available")
        
        self.logger.info("")
    
    def _log_model_breakdown(self, model_stats: Dict[str, ModelStats]) -> None:
        """Log statistics broken down by model."""
        self.logger.info("🤖 Model Breakdown:")
        
        # Sort models by total tokens (descending)
        sorted_models = sorted(
            model_stats.items(),
            key=lambda x: x[1].total_tokens,
            reverse=True
        )
        
        for model_name, stats in sorted_models:
            self.logger.info(f"   📱 {model_name}:")
            self.logger.info(f"      • Calls: {stats.call_count:,}")
            self.logger.info(f"      • Tokens: {stats.total_tokens:,} "
                           f"({stats.total_input_tokens:,} in, {stats.total_output_tokens:,} out)")
            
            if stats.total_cost is not None:
                avg_cost = stats.total_cost / stats.call_count if stats.call_count > 0 else 0
                self.logger.info(f"      • Cost: ${stats.total_cost:.4f} (avg: ${avg_cost:.4f}/call)")
            
            if stats.average_response_time is not None:
                self.logger.info(f"      • Avg Response Time: {stats.average_response_time:.2f}s")
        
        self.logger.info("")
    
    def _log_prompt_breakdown(self, prompt_stats: Dict[str, PromptStats]) -> None:
        """Log statistics broken down by prompt type."""
        self.logger.info("📝 Prompt Breakdown:")
        
        # Sort prompts by total tokens (descending)
        sorted_prompts = sorted(
            prompt_stats.items(),
            key=lambda x: x[1].total_tokens,
            reverse=True
        )
        
        for prompt_name, stats in sorted_prompts:
            self.logger.info(f"   📄 {prompt_name}:")
            self.logger.info(f"      • Calls: {stats.call_count:,}")
            self.logger.info(f"      • Tokens: {stats.total_tokens:,} "
                           f"({stats.total_input_tokens:,} in, {stats.total_output_tokens:,} out)")
            
            if stats.total_cost is not None:
                avg_cost = stats.total_cost / stats.call_count if stats.call_count > 0 else 0
                self.logger.info(f"      • Cost: ${stats.total_cost:.4f} (avg: ${avg_cost:.4f}/call)")
            
            # Show models used for this prompt
            if stats.models_used:
                models_list = [f"{model}({count})" for model, count in stats.models_used.items()]
                self.logger.info(f"      • Models: {', '.join(models_list)}")
        
        self.logger.info("")
    
    def _log_cost_summary(self, total_stats: Dict[str, Any], model_stats: Dict[str, ModelStats]) -> None:
        """Log a detailed cost summary."""
        self.logger.info("💰 Cost Analysis:")
        
        if total_stats['total_cost'] is not None:
            # Overall cost metrics
            cost_per_token = total_stats['total_cost'] / total_stats['total_tokens'] if total_stats['total_tokens'] > 0 else 0
            cost_per_input_token = None
            cost_per_output_token = None
            
            # Calculate cost per token type if we have model breakdowns
            total_input_cost = 0
            total_output_cost = 0
            models_with_cost = 0
            
            for stats in model_stats.values():
                if stats.total_cost is not None:
                    models_with_cost += 1
                    # Rough estimation - this would be more accurate with per-model pricing
                    if stats.total_tokens > 0:
                        model_cost_per_token = stats.total_cost / stats.total_tokens
                        total_input_cost += model_cost_per_token * stats.total_input_tokens
                        total_output_cost += model_cost_per_token * stats.total_output_tokens
            
            if total_stats['total_input_tokens'] > 0:
                cost_per_input_token = total_input_cost / total_stats['total_input_tokens']
            if total_stats['total_output_tokens'] > 0:
                cost_per_output_token = total_output_cost / total_stats['total_output_tokens']
            
            self.logger.info(f"✅    • Total Cost: ${total_stats['total_cost']:.4f}")
            self.logger.info(f"✅   • Cost per Token: ${cost_per_token:.6f}")
            
            if cost_per_input_token is not None:
                self.logger.info(f"✅   • Est. Cost per Input Token: ${cost_per_input_token:.6f}")
            if cost_per_output_token is not None:
                self.logger.info(f"✅   • Est. Cost per Output Token: ${cost_per_output_token:.6f}")
            
            # Cost efficiency metrics
            if total_stats['duration_seconds'] > 0:
                cost_per_second = total_stats['total_cost'] / total_stats['duration_seconds']
                self.logger.info(f"✅   • Cost per Second: ${cost_per_second:.6f}")
            
            # Show cost coverage
            cost_coverage = (total_stats['cost_available_calls'] / total_stats['total_calls']) * 100
            self.logger.info(f"✅   • Cost Data Coverage: {cost_coverage:.1f}% "
                           f"({total_stats['cost_available_calls']}/{total_stats['total_calls']} calls)")
            
        else:
            self.logger.warning("   • Cost data not available for this pipeline run")
            self.logger.warning("   • This may be due to:")
            self.logger.warning("     - Using models not in LiteLLM's pricing database")
            self.logger.warning("     - Local/custom model endpoints")
            self.logger.warning("     - API response format differences")
    
    def format_cost_summary(self, stats: Dict[str, Any]) -> str:
        """
        Format a cost summary as a string for programmatic use.
        
        Args:
            stats: Statistics dictionary from TokenUsageTracker
            
        Returns:
            Formatted cost summary string
        """
        if stats['total_cost'] is not None:
            return (
                f"Pipeline completed: {stats['total_calls']} calls, "
                f"{stats['total_tokens']:,} tokens, ${stats['total_cost']:.4f}"
            )
        else:
            return (
                f"Pipeline completed: {stats['total_calls']} calls, "
                f"{stats['total_tokens']:,} tokens, cost data unavailable"
            )
    
    def log_model_breakdown(self, model_stats: Dict[str, ModelStats]) -> None:
        """
        Log just the model breakdown section.
        
        Args:
            model_stats: Dictionary of model statistics
        """
        if not model_stats:
            self.logger.info("No model statistics available")
            return
        
        self._log_model_breakdown(model_stats)
    
    def log_prompt_breakdown(self, prompt_stats: Dict[str, PromptStats]) -> None:
        """
        Log just the prompt breakdown section.
        
        Args:
            prompt_stats: Dictionary of prompt statistics
        """
        if not prompt_stats:
            self.logger.info("No prompt statistics available")
            return
        
        self._log_prompt_breakdown(prompt_stats)
    
    def generate_summary_report(self, tracker: TokenUsageTracker) -> str:
        """
        Generate a summary report as a string.
        
        Args:
            tracker: TokenUsageTracker instance with collected statistics
            
        Returns:
            Formatted summary report string
        """
        try:
            total_stats = tracker.get_total_statistics()
            
            if total_stats['total_calls'] == 0:
                return "Pipeline Statistics: No LLM calls recorded"
            
            duration = timedelta(seconds=int(total_stats['duration_seconds']))
            
            lines = [
                "Pipeline Statistics Summary:",
                f"• {total_stats['total_calls']:,} LLM calls",
                f"• {total_stats['total_tokens']:,} total tokens",
                f"• {duration} duration",
            ]
            
            if total_stats['total_cost'] is not None:
                lines.append(f"• ${total_stats['total_cost']:.4f} total cost")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
            return "Error generating pipeline statistics summary"