"""
Template data models for arxiv-writer.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class ValidationCriteria:
    """Validation criteria for template content."""
    required_opening: Optional[str] = None
    word_count_range: Optional[List[int]] = None
    must_include_terms: List[str] = field(default_factory=list)
    forbidden_terms: List[str] = field(default_factory=list)
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'required_opening': self.required_opening,
            'word_count_range': self.word_count_range,
            'must_include_terms': self.must_include_terms,
            'forbidden_terms': self.forbidden_terms,
            'max_length': self.max_length,
            'min_length': self.min_length
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationCriteria':
        """Create from dictionary."""
        return cls(
            required_opening=data.get('required_opening'),
            word_count_range=data.get('word_count_range'),
            must_include_terms=data.get('must_include_terms', []),
            forbidden_terms=data.get('forbidden_terms', []),
            max_length=data.get('max_length'),
            min_length=data.get('min_length')
        )


@dataclass
class PromptTemplate:
    """Template for LLM prompts with context injection."""
    name: str
    system_prompt: str
    user_prompt: str
    context_variables: List[str] = field(default_factory=list)
    validation_criteria: Optional[ValidationCriteria] = None
    model_parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation."""
        if self.validation_criteria is None:
            self.validation_criteria = ValidationCriteria()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'system_prompt': self.system_prompt,
            'user_prompt': self.user_prompt,
            'context_variables': self.context_variables,
            'validation_criteria': self.validation_criteria.to_dict() if self.validation_criteria else None,
            'model_parameters': self.model_parameters,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> 'PromptTemplate':
        """Create from dictionary."""
        validation_data = data.get('validation_criteria', {})
        validation_criteria = ValidationCriteria.from_dict(validation_data) if validation_data else None
        
        return cls(
            name=name,
            system_prompt=data.get('system_prompt', ''),
            user_prompt=data.get('user_prompt', ''),
            context_variables=data.get('context_variables', []),
            validation_criteria=validation_criteria,
            model_parameters=data.get('model_parameters', {}),
            metadata=data.get('metadata', {})
        )
    
    def get_required_variables(self) -> List[str]:
        """Get list of required context variables."""
        return self.context_variables.copy()
    
    def validate_context(self, context: Dict[str, Any]) -> List[str]:
        """Validate that required context variables are present."""
        missing_vars = []
        for var in self.context_variables:
            if var not in context:
                missing_vars.append(var)
        return missing_vars


@dataclass
class RenderedPrompt:
    """Rendered prompt with context data injected."""
    template_name: str
    system_prompt: str
    user_prompt: str
    context_used: Dict[str, Any]
    rendered_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'template_name': self.template_name,
            'system_prompt': self.system_prompt,
            'user_prompt': self.user_prompt,
            'context_used': self.context_used,
            'rendered_at': self.rendered_at.isoformat()
        }


@dataclass
class Template:
    """Base template class."""
    name: str
    content: str
    template_type: str
    variables: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'content': self.content,
            'template_type': self.template_type,
            'variables': self.variables,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Template':
        """Create from dictionary."""
        created_at = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
        updated_at = datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat()))
        
        return cls(
            name=data['name'],
            content=data['content'],
            template_type=data['template_type'],
            variables=data.get('variables', []),
            metadata=data.get('metadata', {}),
            created_at=created_at,
            updated_at=updated_at
        )


@dataclass
class LatexTemplate(Template):
    """LaTeX template for document formatting."""
    document_class: str = "article"
    packages: List[str] = field(default_factory=list)
    custom_commands: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization."""
        self.template_type = "latex"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'document_class': self.document_class,
            'packages': self.packages,
            'custom_commands': self.custom_commands
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LatexTemplate':
        """Create from dictionary."""
        base_template = super().from_dict(data)
        return cls(
            name=base_template.name,
            content=base_template.content,
            template_type=base_template.template_type,
            variables=base_template.variables,
            metadata=base_template.metadata,
            created_at=base_template.created_at,
            updated_at=base_template.updated_at,
            document_class=data.get('document_class', 'article'),
            packages=data.get('packages', []),
            custom_commands=data.get('custom_commands', {})
        )


@dataclass
class TemplateValidationResult:
    """Result of template validation."""
    is_valid: bool
    template_name: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_variables: List[str] = field(default_factory=list)
    unused_variables: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'is_valid': self.is_valid,
            'template_name': self.template_name,
            'errors': self.errors,
            'warnings': self.warnings,
            'missing_variables': self.missing_variables,
            'unused_variables': self.unused_variables
        }