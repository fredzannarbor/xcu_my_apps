"""
Batch operations module for processing multiple imprints at once.

This module provides batch processing capabilities for:
- Completing and validating imprint configurations
- Bulk revising configurations based on prompts
- Creating ideation tournaments for multiple imprints
"""

from .models import (
    BatchOperationResult,
    ConfigDiff,
    ValidationError,
    ValidationSeverity,
    IdeationBatchResult,
    BatchRevisionResult,
    TournamentConfig
)

from .config_operations import (
    complete_and_validate_configs,
    revise_configs_batch
)

from .ideation_integration import create_ideation_tournaments

from .path_selector import (
    render_path_selector,
    get_predefined_paths,
    get_configs_from_paths,
    render_config_selector
)

from .config_loader import BatchConfigLoader

from .validation import BatchValidator

from .backup import BackupManager

__all__ = [
    'BatchOperationResult',
    'ConfigDiff',
    'ValidationError',
    'ValidationSeverity',
    'IdeationBatchResult',
    'BatchRevisionResult',
    'TournamentConfig',
    'complete_and_validate_configs',
    'revise_configs_batch',
    'create_ideation_tournaments',
    'render_path_selector',
    'get_predefined_paths',
    'get_configs_from_paths',
    'render_config_selector',
    'BatchConfigLoader',
    'BatchValidator',
    'BackupManager',
]
