"""
Template management system for arxiv-writer.
"""

import json
import yaml
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import logging
from datetime import datetime

from .models import (
    PromptTemplate, 
    Template, 
    LatexTemplate, 
    TemplateValidationResult,
    ValidationCriteria
)
from .renderer import TemplateRenderer
from ..core.exceptions import TemplateError, ValidationError


logger = logging.getLogger(__name__)


class TemplateManager:
    """Manages loading, validation, and access to templates."""
    
    def __init__(self, template_config: Optional[Dict[str, Any]] = None):
        """
        Initialize template manager.
        
        Args:
            template_config: Configuration dictionary for templates
        """
        self.config = template_config or {}
        self.prompt_templates: Dict[str, PromptTemplate] = {}
        self.latex_templates: Dict[str, LatexTemplate] = {}
        self.custom_templates: Dict[str, Template] = {}
        self.renderer = TemplateRenderer()
        
        # Load default templates if specified and file exists
        default_prompts_file = self.config.get('prompts_file', 'templates/default_prompts.json')
        if default_prompts_file and Path(default_prompts_file).exists():
            try:
                self.load_prompt_templates(default_prompts_file)
            except Exception as e:
                logger.warning(f"Failed to load default templates: {e}")
    
    def load_prompt_templates(self, file_path: Union[str, Path]) -> None:
        """
        Load prompt templates from file.
        
        Args:
            file_path: Path to template file (JSON or YAML)
            
        Raises:
            TemplateError: If file cannot be loaded or parsed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise TemplateError(f"Template file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() == '.json':
                    data = json.load(f)
                elif file_path.suffix.lower() in ['.yml', '.yaml']:
                    data = yaml.safe_load(f)
                else:
                    raise TemplateError(f"Unsupported template file format: {file_path.suffix}")
            
            # Extract paper sections templates
            paper_sections = data.get('paper_sections', {})
            for section_name, section_data in paper_sections.items():
                try:
                    template = PromptTemplate.from_dict(section_name, section_data)
                    self.prompt_templates[section_name] = template
                    logger.debug(f"Loaded prompt template: {section_name}")
                except Exception as e:
                    logger.warning(f"Failed to load template {section_name}: {e}")
            
            # Extract technical documentation templates
            tech_docs = data.get('technical_documentation', {})
            for doc_name, doc_data in tech_docs.items():
                try:
                    template = PromptTemplate.from_dict(doc_name, doc_data)
                    self.prompt_templates[doc_name] = template
                    logger.debug(f"Loaded technical documentation template: {doc_name}")
                except Exception as e:
                    logger.warning(f"Failed to load technical template {doc_name}: {e}")
            
            # Extract data analysis templates
            data_analysis = data.get('data_analysis', {})
            for analysis_name, analysis_data in data_analysis.items():
                try:
                    template = PromptTemplate.from_dict(analysis_name, analysis_data)
                    self.prompt_templates[analysis_name] = template
                    logger.debug(f"Loaded data analysis template: {analysis_name}")
                except Exception as e:
                    logger.warning(f"Failed to load analysis template {analysis_name}: {e}")
            
            # Extract literature review templates
            lit_review = data.get('literature_review', {})
            for review_name, review_data in lit_review.items():
                try:
                    template = PromptTemplate.from_dict(review_name, review_data)
                    self.prompt_templates[review_name] = template
                    logger.debug(f"Loaded literature review template: {review_name}")
                except Exception as e:
                    logger.warning(f"Failed to load literature review template {review_name}: {e}")
            
            # Extract supplemental documentation templates
            supplemental = data.get('supplemental_documentation', {})
            for supp_name, supp_data in supplemental.items():
                try:
                    template = PromptTemplate.from_dict(supp_name, supp_data)
                    self.prompt_templates[supp_name] = template
                    logger.debug(f"Loaded supplemental template: {supp_name}")
                except Exception as e:
                    logger.warning(f"Failed to load supplemental template {supp_name}: {e}")
            
            logger.info(f"Loaded {len(self.prompt_templates)} prompt templates from {file_path}")
            
        except json.JSONDecodeError as e:
            raise TemplateError(f"Invalid JSON in template file {file_path}: {e}")
        except yaml.YAMLError as e:
            raise TemplateError(f"Invalid YAML in template file {file_path}: {e}")
        except Exception as e:
            raise TemplateError(f"Failed to load template file {file_path}: {e}")
    
    def load_latex_template(self, name: str, file_path: Union[str, Path]) -> None:
        """
        Load LaTeX template from file.
        
        Args:
            name: Template name
            file_path: Path to LaTeX template file
            
        Raises:
            TemplateError: If file cannot be loaded
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise TemplateError(f"LaTeX template file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract variables from template content
            variables = self.renderer.extract_variables(content)
            
            template = LatexTemplate(
                name=name,
                content=content,
                template_type="latex",
                variables=variables,
                metadata={'file_path': str(file_path)}
            )
            
            self.latex_templates[name] = template
            logger.info(f"Loaded LaTeX template: {name}")
            
        except Exception as e:
            raise TemplateError(f"Failed to load LaTeX template {file_path}: {e}")
    
    def add_custom_template(self, template: Template) -> None:
        """
        Add a custom template.
        
        Args:
            template: Template to add
        """
        if isinstance(template, PromptTemplate):
            self.prompt_templates[template.name] = template
        elif isinstance(template, LatexTemplate):
            self.latex_templates[template.name] = template
        else:
            self.custom_templates[template.name] = template
        
        logger.info(f"Added custom template: {template.name}")
    
    def get_prompt_template(self, name: str) -> Optional[PromptTemplate]:
        """
        Get prompt template by name.
        
        Args:
            name: Template name
            
        Returns:
            PromptTemplate if found, None otherwise
        """
        return self.prompt_templates.get(name)
    
    def get_latex_template(self, name: str) -> Optional[LatexTemplate]:
        """
        Get LaTeX template by name.
        
        Args:
            name: Template name
            
        Returns:
            LatexTemplate if found, None otherwise
        """
        return self.latex_templates.get(name)
    
    def get_template(self, name: str) -> Optional[Template]:
        """
        Get any template by name.
        
        Args:
            name: Template name
            
        Returns:
            Template if found, None otherwise
        """
        # Check prompt templates first
        if name in self.prompt_templates:
            return self.prompt_templates[name]
        
        # Check LaTeX templates
        if name in self.latex_templates:
            return self.latex_templates[name]
        
        # Check custom templates
        return self.custom_templates.get(name)
    
    def list_templates(self, template_type: Optional[str] = None) -> List[str]:
        """
        List available templates.
        
        Args:
            template_type: Filter by template type ('prompt', 'latex', 'custom')
            
        Returns:
            List of template names
        """
        templates = []
        
        if template_type is None or template_type == 'prompt':
            templates.extend(self.prompt_templates.keys())
        
        if template_type is None or template_type == 'latex':
            templates.extend(self.latex_templates.keys())
        
        if template_type is None or template_type == 'custom':
            templates.extend(self.custom_templates.keys())
        
        return sorted(templates)
    
    def validate_template(self, name: str) -> TemplateValidationResult:
        """
        Validate a template.
        
        Args:
            name: Template name
            
        Returns:
            TemplateValidationResult with validation details
        """
        template = self.get_template(name)
        
        if template is None:
            return TemplateValidationResult(
                is_valid=False,
                template_name=name,
                errors=[f"Template '{name}' not found"]
            )
        
        errors = []
        warnings = []
        missing_variables = []
        unused_variables = []
        
        try:
            # For prompt templates, validate structure
            if isinstance(template, PromptTemplate):
                if not template.system_prompt.strip():
                    warnings.append("System prompt is empty")
                
                if not template.user_prompt.strip():
                    errors.append("User prompt is empty")
                
                # Check for context variables in prompts
                system_vars = self.renderer.extract_variables(template.system_prompt)
                user_vars = self.renderer.extract_variables(template.user_prompt)
                all_vars = set(system_vars + user_vars)
                
                # Check for missing variable declarations
                declared_vars = set(template.context_variables)
                missing_variables = list(all_vars - declared_vars)
                unused_variables = list(declared_vars - all_vars)
                
                if missing_variables:
                    warnings.extend([f"Variable '{var}' used but not declared" for var in missing_variables])
                
                if unused_variables:
                    warnings.extend([f"Variable '{var}' declared but not used" for var in unused_variables])
            
            # For LaTeX templates, basic syntax check
            elif isinstance(template, LatexTemplate):
                content = template.content
                
                # Basic validation
                if not content.strip():
                    errors.append("Template content is empty")
                
                # Check for basic LaTeX structure
                if '\\documentclass' not in content:
                    warnings.append("No \\documentclass found in LaTeX template")
                
                if '\\begin{document}' not in content:
                    warnings.append("No \\begin{document} found in LaTeX template")
                
                if '\\end{document}' not in content:
                    warnings.append("No \\end{document} found in LaTeX template")
                
                # Check for balanced braces (basic check)
                open_braces = content.count('{')
                close_braces = content.count('}')
                if open_braces != close_braces:
                    errors.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")
            
            # For other templates, basic content validation
            else:
                if not template.content.strip():
                    errors.append("Template content is empty")
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        is_valid = len(errors) == 0
        
        return TemplateValidationResult(
            is_valid=is_valid,
            template_name=name,
            errors=errors,
            warnings=warnings,
            missing_variables=missing_variables,
            unused_variables=unused_variables
        )
    
    def validate_all_templates(self) -> Dict[str, TemplateValidationResult]:
        """
        Validate all loaded templates.
        
        Returns:
            Dictionary mapping template names to validation results
        """
        results = {}
        
        for template_name in self.list_templates():
            results[template_name] = self.validate_template(template_name)
        
        return results
    
    def render_template(self, name: str, context: Dict[str, Any]) -> Any:
        """
        Render a template with context data.
        
        Args:
            name: Template name
            context: Context data for rendering
            
        Returns:
            Rendered template (type depends on template type)
            
        Raises:
            TemplateError: If template not found or rendering fails
        """
        template = self.get_template(name)
        
        if template is None:
            raise TemplateError(f"Template '{name}' not found")
        
        return self.renderer.render(template, context)
    
    def get_template_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a template.
        
        Args:
            name: Template name
            
        Returns:
            Template information dictionary or None if not found
        """
        template = self.get_template(name)
        
        if template is None:
            return None
        
        info = {
            'name': template.name,
            'type': template.__class__.__name__,
            'variables': getattr(template, 'variables', []),
            'created_at': getattr(template, 'created_at', None),
            'updated_at': getattr(template, 'updated_at', None),
            'metadata': getattr(template, 'metadata', {})
        }
        
        # Add specific info for prompt templates
        if isinstance(template, PromptTemplate):
            info.update({
                'context_variables': template.context_variables,
                'validation_criteria': template.validation_criteria.to_dict() if template.validation_criteria else None,
                'model_parameters': template.model_parameters
            })
        
        # Add specific info for LaTeX templates
        elif isinstance(template, LatexTemplate):
            info.update({
                'document_class': template.document_class,
                'packages': template.packages,
                'custom_commands': template.custom_commands
            })
        
        return info
    
    def list_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        List all available templates with their information.
        
        Returns:
            Dictionary mapping template names to their information
        """
        templates = {}
        
        # Add prompt templates
        for name, template in self.prompt_templates.items():
            templates[name] = {
                'type': 'prompt',
                'description': getattr(template, 'description', 'Prompt template'),
                'variables': template.context_variables,
                'created_at': getattr(template, 'created_at', None)
            }
        
        # Add LaTeX templates
        for name, template in self.latex_templates.items():
            templates[name] = {
                'type': 'latex',
                'description': getattr(template, 'description', 'LaTeX template'),
                'variables': template.variables,
                'created_at': getattr(template, 'created_at', None)
            }
        
        # Add custom templates
        for name, template in self.custom_templates.items():
            templates[name] = {
                'type': 'custom',
                'description': getattr(template, 'description', 'Custom template'),
                'variables': getattr(template, 'variables', []),
                'created_at': getattr(template, 'created_at', None)
            }
        
        return templates

    def export_templates(self, output_path: Union[str, Path], template_type: Optional[str] = None) -> None:
        """
        Export templates to file.
        
        Args:
            output_path: Output file path
            template_type: Filter by template type ('prompt', 'latex', 'custom')
        """
        output_path = Path(output_path)
        
        export_data = {
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'template_count': len(self.list_templates(template_type))
            },
            'templates': {}
        }
        
        # Export prompt templates
        if template_type is None or template_type == 'prompt':
            export_data['templates']['prompt'] = {
                name: template.to_dict() 
                for name, template in self.prompt_templates.items()
            }
        
        # Export LaTeX templates
        if template_type is None or template_type == 'latex':
            export_data['templates']['latex'] = {
                name: template.to_dict() 
                for name, template in self.latex_templates.items()
            }
        
        # Export custom templates
        if template_type is None or template_type == 'custom':
            export_data['templates']['custom'] = {
                name: template.to_dict() 
                for name, template in self.custom_templates.items()
            }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                if output_path.suffix.lower() == '.json':
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                elif output_path.suffix.lower() in ['.yml', '.yaml']:
                    yaml.dump(export_data, f, default_flow_style=False, allow_unicode=True)
                else:
                    raise TemplateError(f"Unsupported export format: {output_path.suffix}")
            
            logger.info(f"Exported templates to {output_path}")
            
        except Exception as e:
            raise TemplateError(f"Failed to export templates: {e}")