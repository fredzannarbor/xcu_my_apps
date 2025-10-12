"""
Section generation system for arxiv paper generation.

This module provides functionality for generating individual paper sections
using LLM providers and template rendering.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import time

from .exceptions import GenerationError, ValidationError, TemplateError, LLMError
from .models import Section, SectionConfig, ValidationResult
from ..templates.manager import TemplateManager
from ..templates.models import PromptTemplate, RenderedPrompt, ValidationCriteria
from ..llm.caller import call_model_with_prompt
from ..llm.models import LLMConfig, LLMResponse

logger = logging.getLogger(__name__)


class SectionGenerator:
    """
    Generates individual paper sections using LLM providers and templates.
    
    This class handles the generation of paper sections by:
    - Loading and rendering prompt templates with context data
    - Calling LLM providers to generate content
    - Validating generated content against criteria
    - Returning structured section results
    """
    
    def __init__(self, llm_config: LLMConfig, template_manager: TemplateManager):
        """
        Initialize section generator.
        
        Args:
            llm_config: Configuration for LLM calls
            template_manager: Template manager for loading and rendering templates
        """
        self.llm_config = llm_config
        self.template_manager = template_manager
        
        logger.info("SectionGenerator initialized")
    
    def generate_section(
        self,
        section_config: SectionConfig,
        context: Dict[str, Any],
        model_override: Optional[str] = None
    ) -> Section:
        """
        Generate a single paper section.
        
        Args:
            section_config: Configuration for the section to generate
            context: Context data for template rendering
            model_override: Optional model override for this section
            
        Returns:
            Generated Section object
            
        Raises:
            GenerationError: If section generation fails
            TemplateError: If template rendering fails
            LLMError: If LLM call fails
        """
        logger.info(f"Generating section: {section_config.name}")
        start_time = time.time()
        
        try:
            # Get and validate template
            template = self._get_template(section_config.template_key)
            
            # Render template with context
            rendered_prompt = self._render_template(template, context)
            
            # Generate content using LLM
            model = model_override or getattr(self.llm_config, 'model', None) or getattr(self.llm_config, 'default_model', 'gpt-4')
            content = self._generate_content(rendered_prompt, model, section_config)
            
            # Validate generated content
            validation_result = self._validate_content(content, section_config, template.validation_criteria)
            
            # Create section object
            generation_time = time.time() - start_time
            section = Section(
                name=section_config.name,
                title=section_config.title,
                content=content,
                word_count=len(content.split()),
                generated_at=datetime.now(),
                llm_model=model,
                generation_time=generation_time
            )
            
            logger.info(f"Successfully generated section '{section_config.name}' "
                       f"({section.word_count} words, {generation_time:.2f}s)")
            
            return section
            
        except Exception as e:
            logger.error(f"Failed to generate section '{section_config.name}': {e}")
            raise GenerationError(f"Section generation failed: {e}") from e
    
    def generate_multiple_sections(
        self,
        section_configs: List[SectionConfig],
        context: Dict[str, Any],
        model_override: Optional[str] = None,
        continue_on_error: bool = False
    ) -> Dict[str, Union[Section, Exception]]:
        """
        Generate multiple paper sections.
        
        Args:
            section_configs: List of section configurations
            context: Context data for template rendering
            model_override: Optional model override for all sections
            continue_on_error: Whether to continue if individual sections fail
            
        Returns:
            Dictionary mapping section names to Section objects or exceptions
        """
        logger.info(f"Generating {len(section_configs)} sections")
        results = {}
        
        for section_config in section_configs:
            try:
                section = self.generate_section(section_config, context, model_override)
                results[section_config.name] = section
            except Exception as e:
                logger.error(f"Failed to generate section '{section_config.name}': {e}")
                if continue_on_error:
                    results[section_config.name] = e
                else:
                    raise
        
        successful_sections = len([r for r in results.values() if isinstance(r, Section)])
        logger.info(f"Generated {successful_sections}/{len(section_configs)} sections successfully")
        
        return results
    
    def _get_template(self, template_key: str) -> PromptTemplate:
        """
        Get template by key.
        
        Args:
            template_key: Template identifier
            
        Returns:
            PromptTemplate object
            
        Raises:
            TemplateError: If template not found
        """
        template = self.template_manager.get_prompt_template(template_key)
        
        if template is None:
            raise TemplateError(f"Template '{template_key}' not found")
        
        return template
    
    def _render_template(self, template: PromptTemplate, context: Dict[str, Any]) -> RenderedPrompt:
        """
        Render template with context data.
        
        Args:
            template: Template to render
            context: Context data
            
        Returns:
            RenderedPrompt object
            
        Raises:
            TemplateError: If template rendering fails
        """
        try:
            # Validate context has required variables
            missing_vars = template.validate_context(context)
            if missing_vars:
                logger.warning(f"Missing context variables for template '{template.name}': {missing_vars}")
                # Add empty values for missing variables to prevent rendering errors
                for var in missing_vars:
                    context[var] = f"[Missing: {var}]"
            
            # Render template
            rendered = self.template_manager.render_template(template.name, context)
            
            if isinstance(rendered, RenderedPrompt):
                return rendered
            else:
                # If renderer returns something else, create RenderedPrompt
                return RenderedPrompt(
                    template_name=template.name,
                    system_prompt=rendered.get('system_prompt', ''),
                    user_prompt=rendered.get('user_prompt', ''),
                    context_used=context
                )
                
        except Exception as e:
            raise TemplateError(f"Failed to render template '{template.name}': {e}") from e
    
    def _generate_content(
        self,
        rendered_prompt: RenderedPrompt,
        model: str,
        section_config: SectionConfig
    ) -> str:
        """
        Generate content using LLM.
        
        Args:
            rendered_prompt: Rendered prompt to send to LLM
            model: Model to use for generation
            section_config: Section configuration
            
        Returns:
            Generated content string
            
        Raises:
            LLMError: If LLM call fails
        """
        try:
            # Prepare messages for LLM call
            messages = []
            
            if rendered_prompt.system_prompt.strip():
                messages.append({
                    "role": "system",
                    "content": rendered_prompt.system_prompt
                })
            
            messages.append({
                "role": "user", 
                "content": rendered_prompt.user_prompt
            })
            
            # Prepare model parameters - only include valid LLM API parameters
            valid_params = ['temperature', 'max_tokens', 'top_p', 'frequency_penalty', 'presence_penalty', 'timeout']
            model_params = {}
            for param in valid_params:
                if hasattr(self.llm_config, param):
                    value = getattr(self.llm_config, param)
                    if value is not None:
                        model_params[param] = value
            
            # Add section-specific constraints
            if section_config.max_words > 0:
                # Estimate tokens (rough approximation: 1 word ≈ 1.3 tokens)
                estimated_tokens = int(section_config.max_words * 1.3)
                current_max_tokens = model_params.get('max_tokens', 0) or 0
                if current_max_tokens == 0 or current_max_tokens > estimated_tokens:
                    model_params['max_tokens'] = estimated_tokens
            
            # Prepare prompt config for LLM caller
            prompt_config = {
                "messages": messages,
                "params": model_params
            }
            
            # Call LLM
            logger.debug(f"Calling LLM {model} for section '{section_config.name}'")
            response = call_model_with_prompt(
                model_name=model,
                prompt_config=prompt_config,
                response_format_type="text",
                prompt_name=f"section_{section_config.name}"
            )
            
            # Extract content from response
            if isinstance(response, dict):
                content = response.get("parsed_content", "")
                if isinstance(content, dict):
                    # If parsed_content is a dict, try to extract text
                    content = content.get("content", str(content))
                
                # Fallback to raw content if parsed content is empty
                if not content or content.strip() == "":
                    content = response.get("raw_content", "")
            else:
                content = str(response)
            
            if not content or content.strip() == "":
                raise LLMError(f"Empty response from LLM for section '{section_config.name}'")
            
            logger.debug(f"Generated {len(content.split())} words for section '{section_config.name}'")
            return content.strip()
            
        except Exception as e:
            raise LLMError(f"LLM call failed for section '{section_config.name}': {e}") from e
    
    def _validate_content(
        self,
        content: str,
        section_config: SectionConfig,
        validation_criteria: Optional[ValidationCriteria]
    ) -> ValidationResult:
        """
        Validate generated content against criteria.
        
        Args:
            content: Generated content to validate
            section_config: Section configuration with validation rules
            validation_criteria: Template validation criteria
            
        Returns:
            ValidationResult object
        """
        errors = []
        warnings = []
        metrics = {}
        
        # Basic content validation
        if not content or not content.strip():
            errors.append("Content is empty")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                metrics=metrics
            )
        
        word_count = len(content.split())
        metrics["word_count"] = word_count
        metrics["character_count"] = len(content)
        
        # Word count validation from section config
        if section_config.min_words > 0 and word_count < section_config.min_words:
            errors.append(f"Content too short: {word_count} words (minimum: {section_config.min_words})")
        
        if section_config.max_words > 0 and word_count > section_config.max_words:
            errors.append(f"Content too long: {word_count} words (maximum: {section_config.max_words})")
        
        # Template validation criteria
        if validation_criteria:
            # Required opening validation
            if validation_criteria.required_opening:
                if not content.strip().startswith(validation_criteria.required_opening):
                    warnings.append(f"Content should start with: '{validation_criteria.required_opening}'")
            
            # Word count range validation
            if validation_criteria.word_count_range:
                min_words, max_words = validation_criteria.word_count_range
                if word_count < min_words:
                    errors.append(f"Content below word count range: {word_count} < {min_words}")
                elif word_count > max_words:
                    warnings.append(f"Content above word count range: {word_count} > {max_words}")
            
            # Required terms validation
            content_lower = content.lower()
            for term in validation_criteria.must_include_terms:
                if term.lower() not in content_lower:
                    warnings.append(f"Content should include term: '{term}'")
            
            # Forbidden terms validation
            for term in validation_criteria.forbidden_terms:
                if term.lower() in content_lower:
                    errors.append(f"Content contains forbidden term: '{term}'")
            
            # Length validation
            if validation_criteria.min_length and len(content) < validation_criteria.min_length:
                errors.append(f"Content too short: {len(content)} characters (minimum: {validation_criteria.min_length})")
            
            if validation_criteria.max_length and len(content) > validation_criteria.max_length:
                errors.append(f"Content too long: {len(content)} characters (maximum: {validation_criteria.max_length})")
        
        # Content quality checks
        sentences = content.split('.')
        metrics["sentence_count"] = len([s for s in sentences if s.strip()])
        
        if word_count > 0:
            metrics["avg_words_per_sentence"] = word_count / max(1, metrics["sentence_count"])
        
        # Check for very short sentences (potential quality issue)
        short_sentences = [s for s in sentences if s.strip() and len(s.split()) < 3]
        if len(short_sentences) > metrics["sentence_count"] * 0.3:  # More than 30% short sentences
            warnings.append("Content has many very short sentences")
        
        # Check for repetitive content (basic check)
        words = content.lower().split()
        unique_words = set(words)
        if len(words) > 10 and len(unique_words) / len(words) < 0.3:  # Less than 30% unique words
            warnings.append("Content may be repetitive")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metrics=metrics
        )
    
    def validate_section(self, section: Section, criteria: Optional[ValidationCriteria] = None) -> ValidationResult:
        """
        Validate a section against criteria.
        
        Args:
            section: Section to validate
            criteria: Optional validation criteria (uses template criteria if not provided)
            
        Returns:
            ValidationResult object
        """
        # Create a minimal section config for validation
        section_config = SectionConfig(
            name=section.name,
            title=section.title,
            template_key="",  # Not needed for validation
            min_words=0,  # Use criteria instead
            max_words=0   # Use criteria instead
        )
        
        return self._validate_content(section.content, section_config, criteria)
    
    def regenerate_section(
        self,
        section: Section,
        section_config: SectionConfig,
        context: Dict[str, Any],
        feedback: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> Section:
        """
        Regenerate a section with optional feedback.
        
        Args:
            section: Original section to regenerate
            section_config: Section configuration
            context: Context data for template rendering
            feedback: Optional feedback to incorporate
            model_override: Optional model override
            
        Returns:
            Regenerated Section object
        """
        logger.info(f"Regenerating section: {section.name}")
        
        # Add feedback to context if provided
        if feedback:
            context = context.copy()
            context["regeneration_feedback"] = feedback
            context["previous_content"] = section.content
        
        # Generate new section
        new_section = self.generate_section(section_config, context, model_override)
        
        # Preserve some metadata from original
        new_section.name = section.name
        new_section.title = section.title
        
        return new_section
    
    def get_section_statistics(self, sections: List[Section]) -> Dict[str, Any]:
        """
        Get statistics for a list of sections.
        
        Args:
            sections: List of sections to analyze
            
        Returns:
            Dictionary with section statistics
        """
        if not sections:
            return {"total_sections": 0}
        
        total_words = sum(s.word_count for s in sections)
        total_time = sum(s.generation_time for s in sections)
        
        stats = {
            "total_sections": len(sections),
            "total_words": total_words,
            "total_generation_time": total_time,
            "average_words_per_section": total_words / len(sections),
            "average_generation_time": total_time / len(sections),
            "sections_by_name": {s.name: s.word_count for s in sections},
            "models_used": list(set(s.llm_model for s in sections if s.llm_model)),
            "generation_dates": [s.generated_at for s in sections if s.generated_at]
        }
        
        # Word count distribution
        word_counts = [s.word_count for s in sections]
        if word_counts:
            stats["word_count_stats"] = {
                "min": min(word_counts),
                "max": max(word_counts),
                "median": sorted(word_counts)[len(word_counts) // 2]
            }
        
        return stats


# Utility functions for common section generation patterns

def create_standard_section_configs() -> List[SectionConfig]:
    """
    Create standard academic paper section configurations.
    
    Returns:
        List of standard SectionConfig objects
    """
    return [
        SectionConfig(
            name="abstract",
            title="Abstract",
            template_key="abstract",
            required=True,
            min_words=100,
            max_words=300
        ),
        SectionConfig(
            name="introduction",
            title="Introduction",
            template_key="introduction",
            required=True,
            min_words=300,
            max_words=800
        ),
        SectionConfig(
            name="related_work",
            title="Related Work",
            template_key="related_work",
            required=False,
            min_words=200,
            max_words=600,
            dependencies=["introduction"]
        ),
        SectionConfig(
            name="methodology",
            title="Methodology",
            template_key="methodology",
            required=True,
            min_words=400,
            max_words=1000,
            dependencies=["introduction"]
        ),
        SectionConfig(
            name="results",
            title="Results",
            template_key="results",
            required=True,
            min_words=300,
            max_words=800,
            dependencies=["methodology"]
        ),
        SectionConfig(
            name="discussion",
            title="Discussion",
            template_key="discussion",
            required=True,
            min_words=200,
            max_words=600,
            dependencies=["results"]
        ),
        SectionConfig(
            name="conclusion",
            title="Conclusion",
            template_key="conclusion",
            required=True,
            min_words=150,
            max_words=400,
            dependencies=["discussion"]
        )
    ]


def validate_section_dependencies(section_configs: List[SectionConfig]) -> List[str]:
    """
    Validate that section dependencies are satisfied.
    
    Args:
        section_configs: List of section configurations
        
    Returns:
        List of dependency validation errors
    """
    errors = []
    section_names = {config.name for config in section_configs}
    
    for config in section_configs:
        for dependency in config.dependencies:
            if dependency not in section_names:
                errors.append(f"Section '{config.name}' depends on missing section '{dependency}'")
    
    return errors