"""
Field Mapping Registry Module

This module provides a registry for field mapping strategies that integrates
the enhanced LLM completion strategy.
"""

import logging
from typing import Dict, Any, Optional, List

from ..metadata.metadata_models import CodexMetadata
from .field_mapping import (
    MappingStrategy, DirectMappingStrategy, ComputedMappingStrategy,
    DefaultMappingStrategy, ConditionalMappingStrategy, FieldMappingRegistry,
    MappingContext
)
from .enhanced_llm_completion_strategy import EnhancedLLMCompletionStrategy
from .enhanced_field_mappings import create_comprehensive_lsi_registry

logger = logging.getLogger(__name__)


def create_enhanced_lsi_registry(config=None, llm_field_completer=None) -> FieldMappingRegistry:
    """
    Create a field mapping registry with enhanced LLM completion strategies.
    
    Args:
        config: Optional LSIConfiguration instance for default values
        llm_field_completer: Optional LLMFieldCompleter for intelligent field completion
        
    Returns:
        FieldMappingRegistry with enhanced strategies
    """
    
    # Create the base registry using the comprehensive field mappings
    registry = create_comprehensive_lsi_registry(config, llm_field_completer)
    
    # If no LLM field completer is provided, return the base registry
    if not llm_field_completer:
        logger.warning("No LLM field completer provided, using standard mapping strategies")
        return registry
    
    # Replace standard strategies with enhanced LLM completion strategies for key fields
    _enhance_contributor_fields(registry, llm_field_completer)
    _enhance_classification_fields(registry, llm_field_completer)
    _enhance_marketing_fields(registry, llm_field_completer)
    _enhance_audience_fields(registry, llm_field_completer)
    
    logger.info(f"Created enhanced LSI registry with {len(registry.get_registered_fields())} field strategies")
    return registry


def _enhance_contributor_fields(registry: FieldMappingRegistry, llm_field_completer) -> None:
    """
    Enhance contributor-related fields with LLM completion strategies.
    
    Args:
        registry: FieldMappingRegistry to enhance
        llm_field_completer: LLMFieldCompleter instance
    """
    # Contributor bio
    registry.register_strategy(
        "Contributor One BIO",
        EnhancedLLMCompletionStrategy(
            field_completer=llm_field_completer,
            metadata_field="contributor_one_bio",
            prompt_key="generate_contributor_bio"
        )
    )
    
    # Contributor affiliations
    registry.register_strategy(
        "Contributor One Affiliations",
        EnhancedLLMCompletionStrategy(
            field_completer=llm_field_completer,
            metadata_field="contributor_one_affiliations",
            prompt_key="extract_lsi_contributor_info"
        )
    )
    
    # Contributor professional position
    registry.register_strategy(
        "Contributor One Professional Position",
        EnhancedLLMCompletionStrategy(
            field_completer=llm_field_completer,
            metadata_field="contributor_one_professional_position",
            prompt_key="extract_lsi_contributor_info"
        )
    )
    
    # Contributor location
    registry.register_strategy(
        "Contributor One Location",
        EnhancedLLMCompletionStrategy(
            field_completer=llm_field_completer,
            metadata_field="contributor_one_location",
            prompt_key="extract_lsi_contributor_info"
        )
    )
    
    # Contributor prior work
    registry.register_strategy(
        "Contributor One Prior Work",
        EnhancedLLMCompletionStrategy(
            field_completer=llm_field_completer,
            metadata_field="contributor_one_prior_work",
            prompt_key="extract_lsi_contributor_info"
        )
    )


def _enhance_classification_fields(registry: FieldMappingRegistry, llm_field_completer) -> None:
    """
    Enhance classification-related fields with LLM completion strategies.
    
    Args:
        registry: FieldMappingRegistry to enhance
        llm_field_completer: LLMFieldCompleter instance
    """
    # BISAC categories
    registry.register_strategy(
        "BISAC Category 2",
        EnhancedLLMCompletionStrategy(
            field_completer=llm_field_completer,
            metadata_field="bisac_category_2",
            prompt_key="suggest_bisac_codes"
        )
    )
    
    registry.register_strategy(
        "BISAC Category 3",
        EnhancedLLMCompletionStrategy(
            field_completer=llm_field_completer,
            metadata_field="bisac_category_3",
            prompt_key="suggest_bisac_codes"
        )
    )
    
    # Thema subjects
    registry.register_strategy(
        "Thema Subject 1",
        EnhancedLLMCompletionStrategy(
            field_completer=llm_field_completer,
            metadata_field="thema_subject_1",
            prompt_key="suggest_thema_subjects"
        )
    )
    
    registry.register_strategy(
        "Thema Subject 2",
        EnhancedLLMCompletionStrategy(
            field_completer=llm_field_completer,
            metadata_field="thema_subject_2",
            prompt_key="suggest_thema_subjects"
        )
    )
    
    registry.register_strategy(
        "Thema Subject 3",
        EnhancedLLMCompletionStrategy(
            field_completer=llm_field_completer,
            metadata_field="thema_subject_3",
            prompt_key="suggest_thema_subjects"
        )
    )
    
    # Keywords
    registry.register_strategy(
        "Keywords",
        EnhancedLLMCompletionStrategy(
            field_completer=llm_field_completer,
            metadata_field="keywords",
            prompt_key="generate_keywords"
        )
    )


def _enhance_marketing_fields(registry: FieldMappingRegistry, llm_field_completer) -> None:
    """
    Enhance marketing-related fields with LLM completion strategies.
    
    Args:
        registry: FieldMappingRegistry to enhance
        llm_field_completer: LLMFieldCompleter instance
    """
    # Short description
    registry.register_strategy(
        "Short Description",
        EnhancedLLMCompletionStrategy(
            field_completer=llm_field_completer,
            metadata_field="summary_short",
            prompt_key="create_short_description"
        )
    )
    
    # Series information
    registry.register_strategy(
        "Series Name",
        EnhancedLLMCompletionStrategy(
            field_completer=llm_field_completer,
            metadata_field="series_name",
            prompt_key="suggest_series_info"
        )
    )
    
    registry.register_strategy(
        "# in Series",
        EnhancedLLMCompletionStrategy(
            field_completer=llm_field_completer,
            metadata_field="series_number",
            prompt_key="suggest_series_info"
        )
    )


def _enhance_audience_fields(registry: FieldMappingRegistry, llm_field_completer) -> None:
    """
    Enhance audience-related fields with LLM completion strategies.
    
    Args:
        registry: FieldMappingRegistry to enhance
        llm_field_completer: LLMFieldCompleter instance
    """
    # Audience
    registry.register_strategy(
        "Audience",
        EnhancedLLMCompletionStrategy(
            field_completer=llm_field_completer,
            metadata_field="audience",
            prompt_key="determine_audience"
        )
    )
    
    # Age range
    registry.register_strategy(
        "Min Age",
        EnhancedLLMCompletionStrategy(
            field_completer=llm_field_completer,
            metadata_field="min_age",
            prompt_key="determine_age_range"
        )
    )
    
    registry.register_strategy(
        "Max Age",
        EnhancedLLMCompletionStrategy(
            field_completer=llm_field_completer,
            metadata_field="max_age",
            prompt_key="determine_age_range"
        )
    )