"""
Data models for batch operations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """Represents a validation error or warning."""
    field: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    config_name: Optional[str] = None
    suggested_fix: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
            "config_name": self.config_name,
            "suggested_fix": self.suggested_fix
        }


@dataclass
class ConfigDiff:
    """Represents a difference between old and new config."""
    field: str
    old_value: Any
    new_value: Any
    config_name: str
    change_type: str = "modified"  # modified, added, removed

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "field": self.field,
            "old_value": str(self.old_value) if self.old_value is not None else None,
            "new_value": str(self.new_value) if self.new_value is not None else None,
            "config_name": self.config_name,
            "change_type": self.change_type
        }


@dataclass
class BatchOperationResult:
    """Result of a batch operation."""
    operation_type: str
    configs_processed: int = 0
    configs_fixed: int = 0
    configs_failed: int = 0
    validation_errors: List[ValidationError] = field(default_factory=list)
    updated_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    operation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_seconds: float = 0.0
    backup_path: Optional[Path] = None

    def add_error(self, error: ValidationError):
        """Add a validation error."""
        self.validation_errors.append(error)

    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of errors by severity."""
        summary = {"error": 0, "warning": 0, "info": 0}
        for error in self.validation_errors:
            summary[error.severity.value] += 1
        return summary

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_type": self.operation_type,
            "configs_processed": self.configs_processed,
            "configs_fixed": self.configs_fixed,
            "configs_failed": self.configs_failed,
            "validation_errors": [e.to_dict() for e in self.validation_errors],
            "error_summary": self.get_error_summary(),
            "operation_timestamp": self.operation_timestamp,
            "duration_seconds": self.duration_seconds,
            "backup_path": str(self.backup_path) if self.backup_path else None
        }


@dataclass
class BatchRevisionResult:
    """Result of a batch revision operation."""
    operation_type: str = "batch_revision"
    configs_modified: int = 0
    configs_failed: int = 0
    changes_preview: Dict[str, List[ConfigDiff]] = field(default_factory=dict)
    validation_status: Dict[str, bool] = field(default_factory=dict)
    revision_prompt: str = ""
    operation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_seconds: float = 0.0
    backup_path: Optional[Path] = None

    def add_change(self, config_name: str, diff: ConfigDiff):
        """Add a change to the preview."""
        if config_name not in self.changes_preview:
            self.changes_preview[config_name] = []
        self.changes_preview[config_name].append(diff)

    def get_total_changes(self) -> int:
        """Get total number of changes."""
        return sum(len(changes) for changes in self.changes_preview.values())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_type": self.operation_type,
            "configs_modified": self.configs_modified,
            "configs_failed": self.configs_failed,
            "total_changes": self.get_total_changes(),
            "changes_by_config": {
                name: [d.to_dict() for d in diffs]
                for name, diffs in self.changes_preview.items()
            },
            "validation_status": self.validation_status,
            "revision_prompt": self.revision_prompt,
            "operation_timestamp": self.operation_timestamp,
            "duration_seconds": self.duration_seconds,
            "backup_path": str(self.backup_path) if self.backup_path else None
        }


@dataclass
class TournamentRecord:
    """Record of a created tournament."""
    tournament_id: str
    imprint_name: str
    ideas_generated: int
    tournament_status: str  # created, running, completed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    winner: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tournament_id": self.tournament_id,
            "imprint_name": self.imprint_name,
            "ideas_generated": self.ideas_generated,
            "tournament_status": self.tournament_status,
            "created_at": self.created_at,
            "winner": self.winner
        }


@dataclass
class IdeationBatchResult:
    """Result of batch ideation tournament creation."""
    operation_type: str = "batch_ideation"
    tournaments_created: List[TournamentRecord] = field(default_factory=list)
    ideas_generated: Dict[str, int] = field(default_factory=dict)
    failed_imprints: List[str] = field(default_factory=list)
    operation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_seconds: float = 0.0
    dashboard_export_path: Optional[Path] = None

    def add_tournament(self, record: TournamentRecord):
        """Add a tournament record."""
        self.tournaments_created.append(record)
        self.ideas_generated[record.imprint_name] = record.ideas_generated

    def get_total_ideas(self) -> int:
        """Get total ideas generated."""
        return sum(self.ideas_generated.values())

    def get_success_rate(self) -> float:
        """Get success rate percentage."""
        total = len(self.tournaments_created) + len(self.failed_imprints)
        if total == 0:
            return 0.0
        return (len(self.tournaments_created) / total) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_type": self.operation_type,
            "tournaments_created": [t.to_dict() for t in self.tournaments_created],
            "total_tournaments": len(self.tournaments_created),
            "total_ideas": self.get_total_ideas(),
            "ideas_by_imprint": self.ideas_generated,
            "failed_imprints": self.failed_imprints,
            "success_rate": self.get_success_rate(),
            "operation_timestamp": self.operation_timestamp,
            "duration_seconds": self.duration_seconds,
            "dashboard_export_path": str(self.dashboard_export_path) if self.dashboard_export_path else None
        }


@dataclass
class TournamentConfig:
    """Configuration for tournament creation."""
    ideas_per_imprint: int = 10
    tournament_type: str = "multi-round"  # single, multi-round, continuous
    llm_model: str = "anthropic/claude-sonnet-4-5-20250929"
    evaluation_criteria: List[str] = field(default_factory=lambda: [
        "imprint_alignment",
        "market_viability",
        "originality",
        "execution_feasibility"
    ])
    integration_mode: str = "full"  # ideas_only, generate_and_run, full
    auto_run: bool = True
    save_results: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ideas_per_imprint": self.ideas_per_imprint,
            "tournament_type": self.tournament_type,
            "llm_model": self.llm_model,
            "evaluation_criteria": self.evaluation_criteria,
            "integration_mode": self.integration_mode,
            "auto_run": self.auto_run,
            "save_results": self.save_results
        }
