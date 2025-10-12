#!/usr/bin/env python3
"""
Enhanced BISAC Category Generator

This module provides intelligent BISAC category generation with LLM assistance,
tranche configuration overrides, and category diversity optimization.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .bisac_validator import get_bisac_validator, BISACValidationResult
from .field_mapping import MappingContext
from ..metadata.metadata_models import CodexMetadata

logger = logging.getLogger(__name__)


@dataclass
class BISACCategoryResult:
    """Result of BISAC category generation."""
    categories: List[str]  # Full category names
    primary_category: str  # Most relevant category (may be tranche override)
    confidence_scores: List[float]  # Confidence for each category
    validation_results: List[BISACValidationResult]
    top_level_categories: List[str]  # Top-level prefixes (BUS, SEL, COM, etc.)
    diversity_score: float  # Measure of category diversity
    tranche_override_used: bool = False
    fallback_used: bool = False


class BISACCategoryGenerator:
    """
    Generates multiple BISAC categories using LLM assistance and validation.
    Supports tranche overrides and ensures diversity across top-level categories.
    """
    
    def __init__(self, llm_completer=None):
        """
        Initialize the BISAC category generator.
        
        Args:
            llm_completer: LLM field completer for category generation
        """
        self.llm_completer = llm_completer
        self.bisac_validator = get_bisac_validator()
        self._category_cache = {}  # Cache to avoid regenerating for same metadata
        
        # Safe fallback categories from different top-levels
        self.fallback_categories = [
            "GENERAL",
            "BUSINESS & ECONOMICS / General", 
            "REFERENCE / General"
        ]
    
    def generate_categories(self, metadata: CodexMetadata, context: MappingContext, max_categories: int = 3) -> BISACCategoryResult:
        """
        Generate BISAC categories with tranche overrides and diversity optimization.
        
        Args:
            metadata: Book metadata
            context: Mapping context with configuration
            max_categories: Maximum number of categories to generate
            
        Returns:
            BISACCategoryResult with generated categories and metadata
        """
        # Create cache key
        cache_key = self._create_cache_key(metadata, context)
        if cache_key in self._category_cache:
            logger.debug(f"Using cached BISAC categories for {cache_key}")
            return self._category_cache[cache_key]
        
        logger.info(f"Generating BISAC categories for: {getattr(metadata, 'title', 'Unknown')}")
        
        categories = []
        confidence_scores = []
        validation_results = []
        tranche_override_used = False
        fallback_used = False
        
        # Step 1: Check for tranche override
        tranche_override = self.apply_tranche_override(context)
        if tranche_override:
            logger.info(f"Applying tranche BISAC override: {tranche_override}")
            categories.append(tranche_override)
            confidence_scores.append(1.0)  # Override has highest confidence
            tranche_override_used = True
            
            # Validate the override
            validation_result = self.bisac_validator.validate_bisac_code(tranche_override)
            if not validation_result.is_valid:
                # Try to validate as category name
                validation_result = self._validate_category_name(tranche_override)
            validation_results.append(validation_result)
        
        # Step 2: Generate additional categories using LLM
        remaining_slots = max_categories - len(categories)
        if remaining_slots > 0:
            try:
                llm_categories = self._generate_with_llm(metadata, context, remaining_slots, tranche_override)
                for category, confidence in llm_categories:
                    formatted_category = self.validate_and_format_category(category)
                    if formatted_category:
                        categories.append(formatted_category)
                        confidence_scores.append(confidence)
                        
                        # Validate the category
                        validation_result = self._validate_category_name(formatted_category)
                        validation_results.append(validation_result)
            except Exception as e:
                logger.warning(f"LLM category generation failed: {e}")
                fallback_used = True
        
        # Step 3: Fill remaining slots with fallbacks if needed
        if len(categories) < max_categories:
            fallback_used = True
            self._add_fallback_categories(categories, confidence_scores, validation_results, max_categories)
        
        # Step 4: Ensure category diversity
        categories = self.ensure_category_diversity(categories)
        
        # Step 5: Calculate diversity score
        top_level_categories = [self._extract_top_level_category(cat) for cat in categories]
        diversity_score = len(set(top_level_categories)) / len(categories) if categories else 0.0
        
        # Create result
        result = BISACCategoryResult(
            categories=categories[:max_categories],
            primary_category=categories[0] if categories else self.fallback_categories[0],
            confidence_scores=confidence_scores[:max_categories],
            validation_results=validation_results[:max_categories],
            top_level_categories=top_level_categories[:max_categories],
            diversity_score=diversity_score,
            tranche_override_used=tranche_override_used,
            fallback_used=fallback_used
        )
        
        # Cache the result
        self._category_cache[cache_key] = result
        
        logger.info(f"Generated {len(result.categories)} BISAC categories with diversity score: {diversity_score:.2f}")
        return result
    
    def apply_tranche_override(self, context: MappingContext) -> Optional[str]:
        """
        Check tranche config for BISAC category override.
        
        Args:
            context: Mapping context with configuration
            
        Returns:
            Override category if valid, None otherwise
        """
        if not context or not hasattr(context, 'config') or not context.config:
            return None
        
        # Check for various override field names
        override_fields = [
            'required_bisac_subject',
            'tranche_bisac_subject', 
            'bisac_override',
            'primary_bisac_category'
        ]
        
        for field in override_fields:
            override_value = context.config.get(field)
            if override_value:
                logger.debug(f"Found tranche BISAC override in {field}: {override_value}")
                
                # Clean up the override value
                cleaned_override = self._clean_tranche_override(override_value)
                if cleaned_override:
                    return cleaned_override
        
        return None
    
    def _clean_tranche_override(self, override_value: str) -> Optional[str]:
        """
        Clean and validate tranche override value.
        
        Args:
            override_value: Raw override value from config
            
        Returns:
            Cleaned category name or None if invalid
        """
        if not override_value:
            return None
        
        # Handle cases like "SOC052000SELF-HELP / Journaling"
        # Extract the category name part after the code
        code_pattern = r'^[A-Z]{3}\d{6}'
        if re.match(code_pattern, override_value):
            # Remove the code prefix
            category_name = re.sub(code_pattern, '', override_value).strip()
            if category_name:
                return category_name
        
        # Return as-is if it looks like a category name
        return override_value.strip()
    
    def ensure_category_diversity(self, categories: List[str]) -> List[str]:
        """
        Reorder categories to maximize diversity across top-level categories.
        
        Args:
            categories: List of category names
            
        Returns:
            Reordered categories with maximum diversity
        """
        if len(categories) <= 1:
            return categories
        
        # Group categories by top-level
        top_level_groups = {}
        for category in categories:
            top_level = self._extract_top_level_category(category)
            if top_level not in top_level_groups:
                top_level_groups[top_level] = []
            top_level_groups[top_level].append(category)
        
        # Reorder to maximize diversity
        diverse_categories = []
        used_top_levels = set()
        
        # First pass: one from each top-level
        for category in categories:
            top_level = self._extract_top_level_category(category)
            if top_level not in used_top_levels:
                diverse_categories.append(category)
                used_top_levels.add(top_level)
        
        # Second pass: fill remaining slots
        for category in categories:
            if category not in diverse_categories:
                diverse_categories.append(category)
        
        logger.debug(f"Diversity optimization: {len(used_top_levels)} unique top-levels from {len(categories)} categories")
        return diverse_categories
    
    def _extract_top_level_category(self, category: str) -> str:
        """
        Extract top-level category from full category name.
        
        Args:
            category: Full category name
            
        Returns:
            Top-level category (e.g., "BUSINESS & ECONOMICS")
        """
        if not category:
            return "UNKNOWN"
        
        # Split on " / " and take the first part
        parts = category.split(" / ")
        return parts[0].strip().upper()
    
    def validate_and_format_category(self, category: str) -> Optional[str]:
        """
        Validate category against BISAC standards and format properly.
        
        Args:
            category: Category name or code
            
        Returns:
            Formatted category name if valid, None otherwise
        """
        if not category:
            return None
        
        category = category.strip()
        
        # If it looks like a BISAC code, convert to name
        if re.match(r'^[A-Z]{3}\d{6}$', category):
            validation_result = self.bisac_validator.validate_bisac_code(category)
            if validation_result.is_valid and validation_result.category_name:
                return validation_result.category_name
            return None
        
        # Validate as category name
        validation_result = self._validate_category_name(category)
        if validation_result.is_valid:
            return category
        
        # Try to find similar category
        suggestions = self.bisac_validator.suggest_bisac_codes([category], max_suggestions=1)
        if suggestions:
            code, name, confidence = suggestions[0]
            if confidence > 0.7:
                logger.debug(f"Using suggested category '{name}' for '{category}' (confidence: {confidence})")
                return name
        
        return None
    
    def _validate_category_name(self, category_name: str) -> BISACValidationResult:
        """
        Validate a category name against BISAC standards.
        
        Args:
            category_name: Category name to validate
            
        Returns:
            Validation result
        """
        # Check if the category name exists in our validator's database
        for code, name in self.bisac_validator.valid_codes.items():
            if name.lower() == category_name.lower():
                return BISACValidationResult(
                    is_valid=True,
                    message="Valid BISAC category name",
                    category_name=name
                )
        
        # If not found, it might still be valid but not in our database
        return BISACValidationResult(
            is_valid=True,  # Assume valid for now
            message="Category name not in database but may be valid",
            category_name=category_name
        )
    
    def _generate_with_llm(self, metadata: CodexMetadata, context: MappingContext, 
                          count: int, existing_category: Optional[str] = None) -> List[Tuple[str, float]]:
        """
        Generate categories using LLM assistance.
        
        Args:
            metadata: Book metadata
            context: Mapping context
            count: Number of categories to generate
            existing_category: Already selected category to avoid duplicates
            
        Returns:
            List of (category_name, confidence) tuples
        """
        if not self.llm_completer:
            logger.warning("No LLM completer available for BISAC category generation")
            return []
        
        try:
            # Prepare context for LLM
            book_info = {
                'title': getattr(metadata, 'title', ''),
                'subtitle': getattr(metadata, 'subtitle', ''),
                'description': getattr(metadata, 'summary_long', '') or getattr(metadata, 'summary_short', ''),
                'keywords': getattr(metadata, 'keywords', ''),
                'existing_category': existing_category or ''
            }
            
            logger.debug(f"Generating {count} BISAC categories with LLM for: {book_info['title']}")
            
            # Use the specialized BISAC category generation prompt
            prompt_key = "generate_bisac_categories"
            
            # Call LLM with the prepared context
            response = self.llm_completer.complete_field(
                field_name="bisac_categories",
                metadata=metadata,
                context=context,
                prompt_key=prompt_key,
                prompt_params=book_info
            )
            
            if not response:
                logger.warning("LLM returned empty response for BISAC categories")
                return []
            
            # Parse the response (categories separated by semicolons)
            categories = [cat.strip() for cat in response.split(';') if cat.strip()]
            
            # Return with confidence scores (higher for first categories)
            results = []
            for i, category in enumerate(categories[:count]):
                confidence = max(0.5, 0.9 - (i * 0.1))  # Decreasing confidence
                results.append((category, confidence))
            
            logger.info(f"LLM generated {len(results)} BISAC categories: {[cat for cat, _ in results]}")
            return results
            
        except Exception as e:
            logger.error(f"LLM category generation failed: {e}")
            return []
    
    def _add_fallback_categories(self, categories: List[str], confidence_scores: List[float], 
                               validation_results: List[BISACValidationResult], max_categories: int):
        """
        Add fallback categories to fill remaining slots.
        
        Args:
            categories: Current categories list (modified in place)
            confidence_scores: Current confidence scores (modified in place)
            validation_results: Current validation results (modified in place)
            max_categories: Maximum number of categories needed
        """
        for fallback in self.fallback_categories:
            if len(categories) >= max_categories:
                break
            
            if fallback not in categories:
                categories.append(fallback)
                confidence_scores.append(0.5)  # Low confidence for fallbacks
                
                validation_result = BISACValidationResult(
                    is_valid=True,
                    message="Fallback category",
                    category_name=fallback
                )
                validation_results.append(validation_result)
                
                logger.debug(f"Added fallback BISAC category: {fallback}")
    
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
        return f"{title}_{config_hash}"


# Global generator instance
_bisac_generator = None

def get_bisac_category_generator(llm_completer=None) -> BISACCategoryGenerator:
    """Get the global BISAC category generator instance."""
    global _bisac_generator
    if _bisac_generator is None:
        _bisac_generator = BISACCategoryGenerator(llm_completer)
    return _bisac_generator