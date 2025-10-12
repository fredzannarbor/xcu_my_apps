"""
AI Interaction Logger - Comprehensive logging for model prompts, responses, and verifications

This module provides structured logging for all AI model interactions including:
- Prompt generation and formatting
- Model calls and responses
- Post verification attempts
- Performance metrics and timing
- Error tracking and debugging information
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import time

# Import paths utility
from .paths import get_data_path


class InteractionType(Enum):
    """Types of AI interactions to log."""
    POST_GENERATION = "post_generation"
    POST_VERIFICATION = "post_verification"
    POST_CORRECTION = "post_correction"
    BATCH_VERIFICATION = "batch_verification"
    PERSONA_OPTIMIZATION = "persona_optimization"


class LogLevel(Enum):
    """Log levels for different types of events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ModelCall:
    """Details of a single model call."""
    model_name: str
    prompt: str
    response: str
    token_usage: Optional[Dict[str, int]] = None
    latency_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class VerificationAttempt:
    """Details of a post verification attempt."""
    post_content: str
    verification_prompt: str
    verification_response: str
    is_valid: bool
    quality_score: float
    issues_found: List[str]
    needs_revision: bool
    corrected_content: Optional[str] = None


@dataclass
class InteractionLog:
    """Complete log entry for an AI interaction."""
    interaction_id: str
    timestamp: datetime
    interaction_type: InteractionType
    persona_id: Optional[str]
    user_id: Optional[str]

    # Model interaction details
    model_calls: List[ModelCall]

    # Verification details (if applicable)
    verification_attempts: List[VerificationAttempt]

    # Context and metadata
    context: Dict[str, Any]
    performance_metrics: Dict[str, float]

    # Final outcome
    success: bool
    final_result: Optional[str]
    error_details: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['interaction_type'] = self.interaction_type.value
        return data


class InteractionLogger:
    """
    Centralized logger for all AI model interactions.

    Provides structured logging with JSON output, performance tracking,
    and comprehensive debugging information.
    """

    def __init__(self, log_file_path: Optional[Path] = None, enable_console_log: bool = True):
        self.log_file_path = log_file_path or get_data_path("ai_interactions.jsonl")
        self.enable_console_log = enable_console_log

        # Ensure log directory exists
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Set up dual logging (console + file)
        self.console_logger = logging.getLogger("ai_interactions")
        self.console_logger.setLevel(logging.INFO)

        # Clear any existing handlers to avoid duplicates
        self.console_logger.handlers.clear()

        # Add console handler
        if self.enable_console_log:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - AI_INTERACTION - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.console_logger.addHandler(console_handler)

        # Add file handler for structured text logs
        log_txt_path = self.log_file_path.with_suffix('.log')
        file_handler = logging.FileHandler(log_txt_path)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.console_logger.addHandler(file_handler)

    def start_interaction(self,
                         interaction_type: InteractionType,
                         persona_id: Optional[str] = None,
                         user_id: Optional[str] = None,
                         context: Optional[Dict[str, Any]] = None) -> str:
        """
        Start tracking a new AI interaction.
        Returns interaction_id for subsequent logging.
        """
        interaction_id = str(uuid.uuid4())

        # Store interaction start time for performance tracking
        self._interaction_starts = getattr(self, '_interaction_starts', {})
        self._interaction_starts[interaction_id] = time.time()

        # Initialize interaction context
        self._active_interactions = getattr(self, '_active_interactions', {})
        self._active_interactions[interaction_id] = {
            'interaction_type': interaction_type,
            'persona_id': persona_id,
            'user_id': user_id,
            'context': context or {},
            'model_calls': [],
            'verification_attempts': [],
            'start_time': time.time()
        }

        if self.enable_console_log:
            self.console_logger.info(f"Started {interaction_type.value} interaction: {interaction_id}")

        return interaction_id

    def log_model_call(self,
                      interaction_id: str,
                      model_name: str,
                      prompt: str,
                      response: str,
                      token_usage: Optional[Dict[str, int]] = None,
                      latency_ms: Optional[float] = None,
                      success: bool = True,
                      error_message: Optional[str] = None):
        """Log a model call within an interaction."""
        if not hasattr(self, '_active_interactions') or interaction_id not in self._active_interactions:
            self.console_logger.warning(f"Attempted to log model call for unknown interaction: {interaction_id}")
            return

        model_call = ModelCall(
            model_name=model_name,
            prompt=prompt,
            response=response,
            token_usage=token_usage,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message
        )

        self._active_interactions[interaction_id]['model_calls'].append(model_call)

        if self.enable_console_log:
            status = "SUCCESS" if success else "ERROR"
            response_len = len(response) if response else 0
            self.console_logger.info(f"Model call [{model_name}] {status} - {response_len} chars response")

    def log_verification_attempt(self,
                                interaction_id: str,
                                post_content: str,
                                verification_prompt: str,
                                verification_response: str,
                                is_valid: bool,
                                quality_score: float,
                                issues_found: List[str],
                                needs_revision: bool = False,
                                corrected_content: Optional[str] = None):
        """Log a post verification attempt."""
        if not hasattr(self, '_active_interactions') or interaction_id not in self._active_interactions:
            self.console_logger.warning(f"Attempted to log verification for unknown interaction: {interaction_id}")
            return

        verification = VerificationAttempt(
            post_content=post_content,
            verification_prompt=verification_prompt,
            verification_response=verification_response,
            is_valid=is_valid,
            quality_score=quality_score,
            issues_found=issues_found,
            needs_revision=needs_revision,
            corrected_content=corrected_content
        )

        self._active_interactions[interaction_id]['verification_attempts'].append(verification)

        if self.enable_console_log:
            status = "VALID" if is_valid else "INVALID"
            self.console_logger.info(f"Verification {status} - Quality: {quality_score:.2f} - Issues: {len(issues_found)}")

    def end_interaction(self,
                       interaction_id: str,
                       success: bool,
                       final_result: Optional[str] = None,
                       error_details: Optional[str] = None,
                       additional_metrics: Optional[Dict[str, float]] = None):
        """Complete and save an interaction log."""
        if not hasattr(self, '_active_interactions') or interaction_id not in self._active_interactions:
            self.console_logger.warning(f"Attempted to end unknown interaction: {interaction_id}")
            return

        interaction_data = self._active_interactions[interaction_id]

        # Calculate performance metrics
        total_time = time.time() - interaction_data['start_time']
        performance_metrics = {
            'total_duration_ms': total_time * 1000,
            'model_calls_count': len(interaction_data['model_calls']),
            'verification_attempts_count': len(interaction_data['verification_attempts']),
        }

        # Add model-specific metrics
        if interaction_data['model_calls']:
            total_latency = sum(call.latency_ms or 0 for call in interaction_data['model_calls'])
            performance_metrics['total_model_latency_ms'] = total_latency
            performance_metrics['avg_model_latency_ms'] = total_latency / len(interaction_data['model_calls'])

        # Add any additional metrics
        if additional_metrics:
            performance_metrics.update(additional_metrics)

        # Create complete log entry
        log_entry = InteractionLog(
            interaction_id=interaction_id,
            timestamp=datetime.now(),
            interaction_type=interaction_data['interaction_type'],
            persona_id=interaction_data['persona_id'],
            user_id=interaction_data['user_id'],
            model_calls=interaction_data['model_calls'],
            verification_attempts=interaction_data['verification_attempts'],
            context=interaction_data['context'],
            performance_metrics=performance_metrics,
            success=success,
            final_result=final_result,
            error_details=error_details
        )

        # Save to file
        self._save_log_entry(log_entry)

        # Clean up
        del self._active_interactions[interaction_id]
        if hasattr(self, '_interaction_starts') and interaction_id in self._interaction_starts:
            del self._interaction_starts[interaction_id]

        if self.enable_console_log:
            status = "SUCCESS" if success else "FAILED"
            self.console_logger.info(f"Completed interaction {status} - Duration: {total_time*1000:.1f}ms")

    def _save_log_entry(self, log_entry: InteractionLog):
        """Save log entry to JSONL file and log summary to console."""
        try:
            # Save structured JSON to file
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry.to_dict(), ensure_ascii=False) + '\n')

            # Log summary to console and file
            summary = (f"INTERACTION_COMPLETE [{log_entry.interaction_type.value}] "
                      f"Persona: {log_entry.persona_id or 'N/A'} | "
                      f"Duration: {log_entry.performance_metrics.get('total_duration_ms', 0):.1f}ms | "
                      f"Model calls: {log_entry.performance_metrics.get('model_calls_count', 0)} | "
                      f"Verifications: {log_entry.performance_metrics.get('verification_attempts_count', 0)} | "
                      f"Success: {log_entry.success}")

            self.console_logger.info(summary)

        except Exception as e:
            self.console_logger.error(f"Failed to save log entry: {e}")

    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent log entries."""
        logs = []
        try:
            if self.log_file_path.exists():
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-limit:]:
                        if line.strip():
                            logs.append(json.loads(line))
        except Exception as e:
            if self.enable_console_log:
                self.console_logger.error(f"Failed to read log file: {e}")

        return logs

    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours."""
        logs = self.get_recent_logs(limit=1000)  # Get more logs for analysis

        # Filter by time
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        recent_logs = [
            log for log in logs
            if datetime.fromisoformat(log['timestamp']).timestamp() > cutoff_time
        ]

        if not recent_logs:
            return {"message": "No recent interactions found"}

        # Calculate summary statistics
        total_interactions = len(recent_logs)
        successful_interactions = sum(1 for log in recent_logs if log['success'])

        avg_duration = sum(log['performance_metrics']['total_duration_ms'] for log in recent_logs) / total_interactions

        model_calls_total = sum(log['performance_metrics']['model_calls_count'] for log in recent_logs)
        verification_attempts_total = sum(log['performance_metrics']['verification_attempts_count'] for log in recent_logs)

        # Group by interaction type
        by_type = {}
        for log in recent_logs:
            interaction_type = log['interaction_type']
            if interaction_type not in by_type:
                by_type[interaction_type] = {'count': 0, 'success_rate': 0}
            by_type[interaction_type]['count'] += 1
            if log['success']:
                by_type[interaction_type]['success_rate'] += 1

        # Calculate success rates
        for type_data in by_type.values():
            type_data['success_rate'] = type_data['success_rate'] / type_data['count']

        return {
            'time_period_hours': hours,
            'total_interactions': total_interactions,
            'success_rate': successful_interactions / total_interactions,
            'avg_duration_ms': avg_duration,
            'total_model_calls': model_calls_total,
            'total_verification_attempts': verification_attempts_total,
            'by_interaction_type': by_type
        }


# Global logger instance
_global_logger: Optional[InteractionLogger] = None

def get_interaction_logger() -> InteractionLogger:
    """Get the global interaction logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = InteractionLogger()
    return _global_logger


# Convenience functions for common logging patterns
def log_post_generation(persona_id: str, prompt: str, response: str, model_name: str,
                       success: bool = True, verification_result: Optional[Dict] = None) -> str:
    """Convenience function to log a complete post generation interaction."""
    logger = get_interaction_logger()

    interaction_id = logger.start_interaction(
        InteractionType.POST_GENERATION,
        persona_id=persona_id,
        context={'post_type': 'social_media_post'}
    )

    logger.log_model_call(
        interaction_id=interaction_id,
        model_name=model_name,
        prompt=prompt,
        response=response,
        success=success
    )

    if verification_result:
        logger.log_verification_attempt(
            interaction_id=interaction_id,
            post_content=response,
            verification_prompt=verification_result.get('verification_prompt', ''),
            verification_response=verification_result.get('verification_response', ''),
            is_valid=verification_result.get('is_valid', False),
            quality_score=verification_result.get('quality_score', 0.0),
            issues_found=verification_result.get('issues_found', []),
            needs_revision=verification_result.get('needs_revision', False),
            corrected_content=verification_result.get('corrected_content')
        )

    logger.end_interaction(
        interaction_id=interaction_id,
        success=success,
        final_result=response if success else None
    )

    return interaction_id


if __name__ == "__main__":
    # Example usage
    logger = InteractionLogger()

    # Test logging
    interaction_id = logger.start_interaction(
        InteractionType.POST_GENERATION,
        persona_id="test_persona",
        context={"test": True}
    )

    logger.log_model_call(
        interaction_id=interaction_id,
        model_name="gpt-4",
        prompt="Generate a test post",
        response="This is a test post",
        success=True
    )

    logger.end_interaction(
        interaction_id=interaction_id,
        success=True,
        final_result="Test completed"
    )

    print("✅ Test logging completed")

    # Show performance summary
    summary = logger.get_performance_summary(hours=1)
    print(f"📊 Performance summary: {summary}")