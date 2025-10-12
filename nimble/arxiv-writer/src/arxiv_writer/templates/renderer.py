"""
Template rendering system with Jinja2 context injection.
"""

import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging

try:
    from jinja2 import Environment, BaseLoader, Template as Jinja2Template, TemplateError as Jinja2TemplateError
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

from .models import (
    Template, 
    PromptTemplate, 
    LatexTemplate, 
    RenderedPrompt,
    ValidationCriteria
)
from ..core.exceptions import TemplateError, ValidationError


logger = logging.getLogger(__name__)


class TemplateRenderer:
    """Renders templates with context data injection using Jinja2."""
    
    def __init__(self, enable_jinja2: bool = True):
        """
        Initialize template renderer.
        
        Args:
            enable_jinja2: Whether to use Jinja2 for advanced templating
        """
        self.enable_jinja2 = enable_jinja2 and JINJA2_AVAILABLE
        
        if self.enable_jinja2:
            self.jinja_env = Environment(
                loader=BaseLoader(),
                autoescape=False,  # Don't escape for text templates
                trim_blocks=True,
                lstrip_blocks=True
            )
            
            # Add custom filters
            self.jinja_env.filters['word_count'] = self._word_count_filter
            self.jinja_env.filters['truncate_words'] = self._truncate_words_filter
            self.jinja_env.filters['capitalize_first'] = self._capitalize_first_filter
            
        else:
            self.jinja_env = None
            if enable_jinja2:
                logger.warning("Jinja2 not available, falling back to simple string substitution")
    
    def render(self, template: Template, context: Dict[str, Any]) -> Union[str, RenderedPrompt]:
        """
        Render template with context data.
        
        Args:
            template: Template to render
            context: Context data for rendering
            
        Returns:
            Rendered content (string for basic templates, RenderedPrompt for prompt templates)
            
        Raises:
            TemplateError: If rendering fails
        """
        if isinstance(template, PromptTemplate):
            return self._render_prompt_template(template, context)
        else:
            return self._render_basic_template(template, context)
    
    def _render_prompt_template(self, template: PromptTemplate, context: Dict[str, Any]) -> RenderedPrompt:
        """
        Render a prompt template.
        
        Args:
            template: PromptTemplate to render
            context: Context data
            
        Returns:
            RenderedPrompt with rendered system and user prompts
            
        Raises:
            TemplateError: If rendering fails
        """
        # Validate required context variables
        missing_vars = template.validate_context(context)
        if missing_vars:
            raise TemplateError(f"Missing required context variables for template '{template.name}': {missing_vars}")
        
        try:
            # Render system prompt
            system_prompt = self._render_string(template.system_prompt, context)
            
            # Render user prompt
            user_prompt = self._render_string(template.user_prompt, context)
            
            # Create rendered prompt
            rendered = RenderedPrompt(
                template_name=template.name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                context_used=context.copy()
            )
            
            # Validate rendered content if criteria provided
            if template.validation_criteria:
                self._validate_rendered_content(rendered, template.validation_criteria)
            
            return rendered
            
        except Exception as e:
            raise TemplateError(f"Failed to render prompt template '{template.name}': {e}")
    
    def _render_basic_template(self, template: Template, context: Dict[str, Any]) -> str:
        """
        Render a basic template.
        
        Args:
            template: Template to render
            context: Context data
            
        Returns:
            Rendered content as string
            
        Raises:
            TemplateError: If rendering fails
        """
        try:
            # Use LaTeX-specific rendering for LaTeX templates
            if hasattr(template, 'template_type') and template.template_type == 'latex':
                return self._render_latex_template(template.content, context)
            else:
                return self._render_string(template.content, context)
        except Exception as e:
            raise TemplateError(f"Failed to render template '{template.name}': {e}")
    
    def _render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Render a template string with context.
        
        Args:
            template_string: Template string to render
            context: Context data
            
        Returns:
            Rendered string
            
        Raises:
            TemplateError: If rendering fails
        """
        if not template_string:
            return ""
        
        if self.enable_jinja2:
            return self._render_with_jinja2(template_string, context)
        else:
            return self._render_with_simple_substitution(template_string, context)
    
    def _render_with_jinja2(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Render template string using Jinja2.
        
        Args:
            template_string: Template string
            context: Context data
            
        Returns:
            Rendered string
            
        Raises:
            TemplateError: If Jinja2 rendering fails
        """
        try:
            # Convert {variable} format to {{variable}} for Jinja2
            # But preserve existing {{variable}} format
            import re
            
            # First, protect existing Jinja2 variables
            protected = {}
            jinja_pattern = r'\{\{([^}]+)\}\}'
            matches = re.finditer(jinja_pattern, template_string)
            for i, match in enumerate(matches):
                placeholder = f"__JINJA_PROTECTED_{i}__"
                protected[placeholder] = match.group(0)
                template_string = template_string.replace(match.group(0), placeholder)
            
            # Convert simple {variable} to {{variable}}
            simple_pattern = r'\{([^{}]+)\}'
            template_string = re.sub(simple_pattern, r'{{\1}}', template_string)
            
            # Restore protected Jinja2 variables
            for placeholder, original in protected.items():
                template_string = template_string.replace(placeholder, original)
            
            template = self.jinja_env.from_string(template_string)
            return template.render(**context)
        except Jinja2TemplateError as e:
            raise TemplateError(f"Jinja2 template error: {e}")
        except Exception as e:
            raise TemplateError(f"Template rendering error: {e}")
    
    def _render_latex_template(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Render LaTeX template string with special handling for braces.
        
        Args:
            template_string: LaTeX template string
            context: Context data
            
        Returns:
            Rendered string with LaTeX braces preserved
        """
        try:
            # For LaTeX templates, we need to preserve braces around substituted values
            # Only replace variables that are actually in the context
            import re
            
            def replace_var(match):
                var_name = match.group(1)
                if var_name in context:
                    return f"{{{context[var_name]}}}"
                else:
                    # Return the original match if not a context variable
                    return match.group(0)
            
            # Replace {variable} with {value} only for variables in context
            pattern = r'\{([^{}]+)\}'
            result = re.sub(pattern, replace_var, template_string)
            return result
            
        except Exception as e:
            raise TemplateError(f"LaTeX template rendering error: {e}")
    
    def _render_with_simple_substitution(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Render template string using simple variable substitution.
        
        Args:
            template_string: Template string with {variable} placeholders
            context: Context data
            
        Returns:
            Rendered string
            
        Raises:
            TemplateError: If substitution fails
        """
        try:
            # Simple string formatting with context
            return template_string.format(**context)
        except KeyError as e:
            raise TemplateError(f"Missing context variable: {e}")
        except Exception as e:
            raise TemplateError(f"String substitution error: {e}")
    
    def extract_variables(self, template_string: str) -> List[str]:
        """
        Extract variable names from template string.
        
        Args:
            template_string: Template string to analyze
            
        Returns:
            List of variable names found in template
        """
        if not template_string:
            return []
        
        variables = set()
        
        # Extract simple {variable} patterns
        simple_pattern = r'\{([^{}]+)\}'
        simple_matches = re.findall(simple_pattern, template_string)
        for match in simple_matches:
            # Handle format specifiers like {var:format}
            var_name = match.split(':')[0].strip()
            if var_name and var_name.isidentifier():
                variables.add(var_name)
        
        # If Jinja2 is available, also extract Jinja2 variables
        if self.enable_jinja2:
            jinja_pattern = r'\{\{\s*([^{}]+?)\s*\}\}'
            jinja_matches = re.findall(jinja_pattern, template_string)
            for match in jinja_matches:
                # Extract variable name (handle filters and operations)
                var_name = match.split('|')[0].split('.')[0].strip()
                if var_name and var_name.isidentifier():
                    variables.add(var_name)
        
        return sorted(list(variables))
    
    def _validate_rendered_content(self, rendered: RenderedPrompt, criteria: ValidationCriteria) -> None:
        """
        Validate rendered content against criteria.
        
        Args:
            rendered: Rendered prompt to validate
            criteria: Validation criteria
            
        Raises:
            ValidationError: If validation fails
        """
        errors = []
        
        # Combine system and user prompts for validation
        full_content = f"{rendered.system_prompt}\n\n{rendered.user_prompt}"
        
        # Note: required_opening validation should be applied to LLM response, not prompt template
        # Skipping required_opening validation for prompt templates - this will be validated on the response
        
        # Check word count range
        if criteria.word_count_range:
            word_count = len(full_content.split())
            min_words, max_words = criteria.word_count_range
            if word_count < min_words:
                errors.append(f"Content too short: {word_count} words (minimum: {min_words})")
            elif word_count > max_words:
                errors.append(f"Content too long: {word_count} words (maximum: {max_words})")
        
        # Check minimum length
        if criteria.min_length and len(full_content) < criteria.min_length:
            errors.append(f"Content too short: {len(full_content)} characters (minimum: {criteria.min_length})")
        
        # Check maximum length
        if criteria.max_length and len(full_content) > criteria.max_length:
            errors.append(f"Content too long: {len(full_content)} characters (maximum: {criteria.max_length})")
        
        # Check required terms
        content_lower = full_content.lower()
        for term in criteria.must_include_terms:
            if term.lower() not in content_lower:
                errors.append(f"Required term missing: '{term}'")
        
        # Check forbidden terms
        for term in criteria.forbidden_terms:
            if term.lower() in content_lower:
                errors.append(f"Forbidden term found: '{term}'")
        
        if errors:
            raise ValidationError(f"Content validation failed: {'; '.join(errors)}")
    
    # Custom Jinja2 filters
    def _word_count_filter(self, text: str) -> int:
        """Count words in text."""
        return len(str(text).split())
    
    def _truncate_words_filter(self, text: str, count: int) -> str:
        """Truncate text to specified word count."""
        words = str(text).split()
        if len(words) <= count:
            return text
        return ' '.join(words[:count]) + '...'
    
    def _capitalize_first_filter(self, text: str) -> str:
        """Capitalize first letter of text."""
        text = str(text)
        return text[0].upper() + text[1:] if text else text
    
    def test_template(self, template_string: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test template rendering with given context.
        
        Args:
            template_string: Template string to test
            context: Context data
            
        Returns:
            Dictionary with test results
        """
        result = {
            'success': False,
            'rendered_content': None,
            'error': None,
            'variables_found': [],
            'variables_used': [],
            'variables_missing': []
        }
        
        try:
            # Extract variables
            variables_found = self.extract_variables(template_string)
            result['variables_found'] = variables_found
            
            # Check which variables are available in context
            variables_used = [var for var in variables_found if var in context]
            variables_missing = [var for var in variables_found if var not in context]
            
            result['variables_used'] = variables_used
            result['variables_missing'] = variables_missing
            
            # Try to render - if there are missing variables, this should fail
            if variables_missing:
                result['error'] = f"Missing variables: {variables_missing}"
                result['success'] = False
            else:
                rendered_content = self._render_string(template_string, context)
                result['rendered_content'] = rendered_content
                result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
        
        return result