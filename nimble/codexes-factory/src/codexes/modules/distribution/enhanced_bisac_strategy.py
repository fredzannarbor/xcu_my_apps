#!/usr/bin/env python3
"""
Enhanced BISAC Category Mapping Strategy

This module provides a unified strategy for mapping BISAC categories with
tranche overrides, LLM generation, and diversity optimization.
"""

import logging
from typing import Dict, Optional

from .field_mapping import MappingStrategy, MappingContext
from .bisac_category_generator import get_bisac_category_generator, BISACCategoryResult
from ..metadata.metadata_models import CodexMetadata

logger = logging.getLogger(__name__)


class EnhancedBISACCategoryStrategy(MappingStrategy):
    """
    Unified strategy for generating and validating BISAC categories.
    Generates up to 3 relevant categories using LLM assistance with tranche overrides.
    """
    
    def __init__(self, category_number: int, llm_completer=None):
        """
        Initialize the enhanced BISAC category strategy.
        
        Args:
            category_number: Which category to return (1, 2, or 3)
            llm_completer: LLM field completer for category generation
        """
        self.category_number = category_number
        self.llm_completer = llm_completer
        self.bisac_generator = get_bisac_category_generator(llm_completer)
        
        # Shared cache across all instances to avoid regenerating categories
        self._shared_cache = {}
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Map the metadata to a BISAC category using intelligent generation.
        
        Args:
            metadata: The metadata object to map from
            context: Mapping context with configuration
            
        Returns:
            The BISAC category name for the requested category number
        """
        try:
            # Create cache key for this metadata/context combination
            cache_key = self._create_cache_key(metadata, context)
            
            # Check if we already generated categories for this book
            if cache_key not in self._shared_cache:
                logger.info(f"Generating BISAC categories for category {self.category_number}")
                
                # Generate all categories at once
                result = self.bisac_generator.generate_categories(metadata, context, max_categories=3)
                
                # Cache the result for all category numbers
                self._shared_cache[cache_key] = result
                
                # Log the generation results
                self._log_generation_results(result, metadata)
            else:
                logger.debug(f"Using cached BISAC categories for category {self.category_number}")
            
            # Get the cached result
            result: BISACCategoryResult = self._shared_cache[cache_key]
            
            # Return the requested category number
            if self.category_number <= len(result.categories):
                category = result.categories[self.category_number - 1]
                logger.debug(f"Returning BISAC category {self.category_number}: {category}")
                return category
            else:
                logger.warning(f"Requested category {self.category_number} but only {len(result.categories)} available")
                return ""
                
        except Exception as e:
            logger.error(f"BISAC category mapping failed for category {self.category_number}: {e}")
            
            # Return fallback category
            fallback_categories = [
                "GENERAL",
                "BUSINESS & ECONOMICS / General",
                "REFERENCE / General"
            ]
            
            if self.category_number <= len(fallback_categories):
                fallback = fallback_categories[self.category_number - 1]
                logger.warning(f"Using fallback BISAC category {self.category_number}: {fallback}")
                return fallback
            
            return ""
    
    def _create_cache_key(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Create a cache key for the metadata and context.
        
        Args:
            metadata: Book metadata
            context: Mapping context
            
        Returns:
            Cache key string
        """
        title = getattr(metadata, 'title', 'unknown')
        config_hash = hash(str(context.config)) if context and context.config else 0
        return f"bisac_{title}_{config_hash}"
    
    def _log_generation_results(self, result: BISACCategoryResult, metadata: CodexMetadata):
        """
        Log the results of BISAC category generation.
        
        Args:
            result: Generation result
            metadata: Book metadata
        """
        title = getattr(metadata, 'title', 'Unknown')
        
        logger.info(f"BISAC category generation complete for '{title}':")
        logger.info(f"  Generated {len(result.categories)} categories")
        logger.info(f"  Primary category: {result.primary_category}")
        logger.info(f"  Diversity score: {result.diversity_score:.2f}")
        logger.info(f"  Tranche override used: {result.tranche_override_used}")
        logger.info(f"  Fallback used: {result.fallback_used}")
        
        for i, category in enumerate(result.categories, 1):
            confidence = result.confidence_scores[i-1] if i-1 < len(result.confidence_scores) else 0.0
            top_level = result.top_level_categories[i-1] if i-1 < len(result.top_level_categories) else "UNKNOWN"
            logger.info(f"  Category {i}: {category} (confidence: {confidence:.2f}, top-level: {top_level})")
        
        # Log validation results
        for i, validation in enumerate(result.validation_results, 1):
            if not validation.is_valid:
                logger.warning(f"  Category {i} validation: {validation.message}")


class BISACCategoryMappingStrategy(MappingStrategy):
    """
    Legacy BISAC category mapping strategy for backward compatibility.
    Delegates to EnhancedBISACCategoryStrategy.
    """
    
    def __init__(self, metadata_field: str, default_value: str = "", is_primary: bool = False):
        """
        Initialize the legacy BISAC category mapping strategy.
        
        Args:
            metadata_field: The field in the metadata to map from (ignored)
            default_value: Default value to use if the field is not found (ignored)
            is_primary: Whether this is the primary BISAC category
        """
        self.metadata_field = metadata_field
        self.default_value = default_value
        self.is_primary = is_primary
        
        # Determine category number based on primary flag and field name
        if is_primary or "category" not in metadata_field.lower():
            self.category_number = 1
        elif "2" in metadata_field:
            self.category_number = 2
        elif "3" in metadata_field:
            self.category_number = 3
        else:
            self.category_number = 1
        
        # Create enhanced strategy instance
        self.enhanced_strategy = EnhancedBISACCategoryStrategy(self.category_number)
    
    def map_field(self, metadata: CodexMetadata, context: MappingContext) -> str:
        """
        Map the metadata field to a BISAC category using enhanced strategy.
        
        Args:
            metadata: The metadata object to map from
            context: Mapping context
            
        Returns:
            The BISAC category without the code
        """
        return self.enhanced_strategy.map_field(metadata, context)