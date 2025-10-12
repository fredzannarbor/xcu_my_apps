"""
Data models for arxiv-writer.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class LLMConfig:
    """Configuration for LLM integration."""
    default_model: str = "gemini/gemini-2.5-flash"
    available_models: List[str] = field(default_factory=lambda: ["gemini/gemini-2.5-flash", "gemini/gemini-2.5-pro"])
    model_parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    provider: str = "gemini"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 60
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class TemplateConfig:
    """Configuration for templates."""
    template_file: str = "templates/default_prompts.json"
    section_order: List[str] = field(default_factory=lambda: ["abstract", "introduction", "conclusion"])
    custom_templates: Dict[str, str] = field(default_factory=dict)
    default_prompts: Dict[str, Any] = field(default_factory=dict)
    prompts_file: str = "templates/default_prompts.json"  # backward compatibility
    latex_template: Optional[str] = None


@dataclass
class OutputConfig:
    """Configuration for output generation."""
    format: str = "latex"
    compile_pdf: bool = False
    output_dir: str = "output"
    filename_template: str = "{title}_{timestamp}"


@dataclass
class ValidationConfig:
    """Configuration for content validation."""
    enabled: bool = True
    strict_mode: bool = False
    quality_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "min_word_count": 100,
        "max_word_count": 50000
    })
    min_word_count: int = 100  # backward compatibility
    max_word_count: int = 50000  # backward compatibility
    required_sections: List[str] = field(default_factory=lambda: ["abstract", "introduction", "conclusion"])
    citation_format: str = "bibtex"


@dataclass
class PaperConfig:
    """Main configuration for paper generation."""
    output_directory: str = "output"
    llm_config: LLMConfig = field(default_factory=LLMConfig)
    template_config: TemplateConfig = field(default_factory=TemplateConfig)
    validation_config: ValidationConfig = field(default_factory=ValidationConfig)
    
    # Backward compatibility
    llm: LLMConfig = field(default_factory=LLMConfig)
    templates: TemplateConfig = field(default_factory=TemplateConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    
    # Additional settings
    paper_title: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    abstract: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Ensure backward compatibility by syncing old and new field names."""
        # Sync new format with old format for backward compatibility
        # Only sync if the old format was explicitly set (not default)
        if self.llm_config != LLMConfig() and self.llm == LLMConfig():
            self.llm = self.llm_config
        elif self.llm != LLMConfig() and self.llm_config == LLMConfig():
            self.llm_config = self.llm
            
        if self.template_config != TemplateConfig() and self.templates == TemplateConfig():
            self.templates = self.template_config
        elif self.templates != TemplateConfig() and self.template_config == TemplateConfig():
            self.template_config = self.templates
            
        if self.validation_config != ValidationConfig() and self.validation == ValidationConfig():
            self.validation = self.validation_config
        elif self.validation != ValidationConfig() and self.validation_config == ValidationConfig():
            self.validation_config = self.validation
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> 'PaperConfig':
        """Load configuration from file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            if config_path.suffix.lower() == '.json':
                data = json.load(f)
            else:
                import yaml
                data = yaml.safe_load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaperConfig':
        """Create configuration from dictionary."""
        # Extract nested configurations
        llm_config = LLMConfig(**data.get('llm', {}))
        template_config = TemplateConfig(**data.get('templates', {}))
        output_config = OutputConfig(**data.get('output', {}))
        validation_config = ValidationConfig(**data.get('validation', {}))
        
        # Create main config
        config_data = {k: v for k, v in data.items() 
                      if k not in ['llm', 'templates', 'output', 'validation']}
        
        return cls(
            llm=llm_config,
            templates=template_config,
            output=output_config,
            validation=validation_config,
            **config_data
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "output_directory": self.output_directory,
            "llm_config": {
                "default_model": self.llm_config.default_model,
                "available_models": self.llm_config.available_models,
                "model_parameters": self.llm_config.model_parameters,
                "provider": self.llm_config.provider,
                "temperature": self.llm_config.temperature,
                "max_tokens": self.llm_config.max_tokens,
                "timeout": self.llm_config.timeout,
                "retry_attempts": self.llm_config.retry_attempts,
                "retry_delay": self.llm_config.retry_delay
            },
            "template_config": {
                "template_file": self.template_config.template_file,
                "section_order": self.template_config.section_order,
                "custom_templates": self.template_config.custom_templates,
                "default_prompts": self.template_config.default_prompts
            },
            "validation_config": {
                "enabled": self.validation_config.enabled,
                "strict_mode": self.validation_config.strict_mode,
                "quality_thresholds": self.validation_config.quality_thresholds,
                "required_sections": self.validation_config.required_sections,
                "citation_format": self.validation_config.citation_format
            },
            "paper_title": self.paper_title,
            "authors": self.authors,
            "abstract": self.abstract,
            "keywords": self.keywords
        }
    
    @property
    def output_dir(self) -> str:
        """Get output directory."""
        return self.output.output_dir if hasattr(self.output, 'output_dir') else self.output_directory


@dataclass
class Section:
    """Represents a paper section."""
    name: str
    content: str
    word_count: int = 0
    generated_at: Optional[Any] = None  # Can be datetime or string
    model_used: Optional[str] = None
    validation_status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Backward compatibility
    title: str = ""
    llm_model: Optional[str] = None
    generation_time: float = 0.0
    
    def __post_init__(self):
        """Ensure backward compatibility."""
        if self.llm_model and not self.model_used:
            self.model_used = self.llm_model
        if not self.title:
            self.title = self.name.replace('_', ' ').title()


@dataclass
class ValidationResult:
    """Result of content validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationSummary:
    """Summary of the generation process."""
    total_sections: int
    successful_sections: int
    failed_sections: int
    total_time: float
    total_word_count: int
    llm_calls: int
    errors: List[str] = field(default_factory=list)


@dataclass
class PaperResult:
    """Result of paper generation."""
    sections: Dict[str, Section] = field(default_factory=dict)
    complete_paper: str = ""
    generation_summary: Optional[GenerationSummary] = None
    output_files: List[str] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)
    
    # Backward compatibility
    success: bool = True
    output_path: Optional[str] = None
    pdf_path: Optional[str] = None
    sections_generated: List[str] = field(default_factory=list)
    generation_time: float = 0.0
    word_count: int = 0
    validation_results: Dict[str, ValidationResult] = field(default_factory=dict)
    summary: Optional[GenerationSummary] = None
    errors: List[str] = field(default_factory=list)
    
    def get_quality_score(self) -> float:
        """Calculate overall quality score."""
        if not self.sections:
            return 0.0
        
        # Simple quality score based on word count and validation status
        total_score = 0.0
        for section in self.sections.values():
            section_score = min(section.word_count / 500, 1.0)  # Normalize by expected word count
            if section.validation_status == "valid":
                section_score *= 1.0
            elif section.validation_status == "warning":
                section_score *= 0.8
            else:
                section_score *= 0.5
            total_score += section_score
        
        return total_score / len(self.sections) if self.sections else 0.0
    
    def save_to_directory(self, output_dir: str) -> None:
        """Save all results to directory."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save complete paper
        paper_file = output_path / "paper.tex"
        with open(paper_file, 'w', encoding='utf-8') as f:
            f.write(self.complete_paper)
        
        # Save individual sections
        sections_dir = output_path / "sections"
        sections_dir.mkdir(exist_ok=True)
        
        for name, section in self.sections.items():
            section_file = sections_dir / f"{name}.tex"
            with open(section_file, 'w', encoding='utf-8') as f:
                f.write(section.content)
        
        # Update output files list
        self.output_files = [str(paper_file)] + [
            str(sections_dir / f"{name}.tex") for name in self.sections.keys()
        ]


@dataclass
class SectionConfig:
    """Configuration for individual sections."""
    name: str
    title: str
    template_key: str
    required: bool = True
    min_words: int = 50
    max_words: int = 5000
    dependencies: List[str] = field(default_factory=list)
