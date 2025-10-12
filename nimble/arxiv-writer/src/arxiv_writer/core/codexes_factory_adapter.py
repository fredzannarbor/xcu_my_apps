"""
Codexes Factory compatibility layer for arxiv-writer package.

This module provides seamless integration with existing Codexes Factory
configurations and workflows, allowing drop-in replacement of the current
arxiv paper generation functionality.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
import json
from datetime import datetime

from .context_collector import ContextCollector, ContextConfig, create_codexes_factory_context_collector
from .generator import ArxivPaperGenerator
from .models import PaperConfig, LLMConfig, ValidationConfig, TemplateConfig, SectionConfig
from .exceptions import ConfigurationError, ValidationError

logger = logging.getLogger(__name__)


@dataclass
class CodexesFactoryConfig:
    """Configuration structure matching Codexes Factory format."""
    workspace_root: str = "."
    imprint_name: str = "xynapse_traces"
    output_directory: str = "output"
    
    # LLM configuration
    default_model: str = "anthropic/claude-3-5-sonnet-20241022"
    available_models: List[str] = field(default_factory=lambda: [
        "anthropic/claude-3-5-sonnet-20241022",
        "google/gemini-pro-1.5",
        "openai/gpt-4-turbo",
        "xai/grok-beta"
    ])
    
    # Template configuration
    template_file: str = "templates/default_prompts.json"
    section_order: List[str] = field(default_factory=lambda: [
        "abstract",
        "introduction", 
        "related_work",
        "methodology",
        "results",
        "discussion",
        "conclusion",
        "references"
    ])
    
    # Validation settings
    validation_enabled: bool = True
    strict_mode: bool = False
    quality_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "min_word_count": 500,
        "max_word_count": 8000,
        "readability_score": 0.7,
        "coherence_score": 0.8
    })
    
    # Context collection settings
    collect_book_catalog: bool = True
    collect_imprint_config: bool = True
    collect_technical_architecture: bool = True
    collect_performance_metrics: bool = True
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> 'CodexesFactoryConfig':
        """Load configuration from Codexes Factory format file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return cls.from_dict(data)
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration from {config_path}: {e}")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodexesFactoryConfig':
        """Create configuration from dictionary."""
        # Extract relevant fields from Codexes Factory format
        config = cls()
        
        # Basic settings
        config.workspace_root = data.get("workspace_root", ".")
        config.imprint_name = data.get("imprint", "xynapse_traces")
        config.output_directory = data.get("output_directory", "output")
        
        # LLM settings - handle invalid nested config gracefully
        llm_config = data.get("llm_config", {})
        if isinstance(llm_config, dict):
            config.default_model = llm_config.get("default_model", config.default_model)
            config.available_models = llm_config.get("available_models", config.available_models)
        else:
            logger.warning(f"Invalid llm_config format: {type(llm_config)}, using defaults")
        
        # Template settings - handle invalid nested config gracefully
        template_config = data.get("template_config", {})
        if isinstance(template_config, dict):
            config.template_file = template_config.get("template_file", config.template_file)
            config.section_order = template_config.get("section_order", config.section_order)
        else:
            logger.warning(f"Invalid template_config format: {type(template_config)}, using defaults")
        
        # Validation settings - handle invalid nested config gracefully
        validation_config = data.get("validation_config", {})
        if isinstance(validation_config, dict):
            config.validation_enabled = validation_config.get("enabled", config.validation_enabled)
            config.strict_mode = validation_config.get("strict_mode", config.strict_mode)
            quality_thresholds = validation_config.get("quality_thresholds", {})
            if isinstance(quality_thresholds, dict):
                config.quality_thresholds.update(quality_thresholds)
        else:
            logger.warning(f"Invalid validation_config format: {type(validation_config)}, using defaults")
        
        # Context collection settings - handle invalid nested config gracefully
        context_config = data.get("context_config", {})
        if isinstance(context_config, dict):
            config.collect_book_catalog = context_config.get("collect_book_catalog", config.collect_book_catalog)
            config.collect_imprint_config = context_config.get("collect_imprint_config", config.collect_imprint_config)
            config.collect_technical_architecture = context_config.get("collect_technical_architecture", config.collect_technical_architecture)
            config.collect_performance_metrics = context_config.get("collect_performance_metrics", config.collect_performance_metrics)
        else:
            logger.warning(f"Invalid context_config format: {type(context_config)}, using defaults")
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "workspace_root": self.workspace_root,
            "imprint": self.imprint_name,
            "output_directory": self.output_directory,
            "llm_config": {
                "default_model": self.default_model,
                "available_models": self.available_models
            },
            "template_config": {
                "template_file": self.template_file,
                "section_order": self.section_order
            },
            "validation_config": {
                "enabled": self.validation_enabled,
                "strict_mode": self.strict_mode,
                "quality_thresholds": self.quality_thresholds
            },
            "context_config": {
                "collect_book_catalog": self.collect_book_catalog,
                "collect_imprint_config": self.collect_imprint_config,
                "collect_technical_architecture": self.collect_technical_architecture,
                "collect_performance_metrics": self.collect_performance_metrics
            }
        }


class CodexesFactoryAdapter:
    """
    Adapter class for seamless integration with Codexes Factory workflows.
    
    This class provides a compatibility layer that allows the arxiv-writer package
    to be used as a drop-in replacement for the existing Codexes Factory arxiv
    paper generation functionality.
    """
    
    def __init__(self, config: Union[CodexesFactoryConfig, Dict[str, Any], str, Path]):
        """
        Initialize the adapter with Codexes Factory configuration.
        
        Args:
            config: Configuration in Codexes Factory format
        """
        if isinstance(config, (str, Path)):
            # Load from file - check if it's a migrated config with metadata
            config_path = Path(config)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                
                # Check if this is a migrated config with Codexes Factory metadata
                if "codexes_factory_metadata" in file_data:
                    # Use the original Codexes Factory config from metadata
                    original_config = file_data["codexes_factory_metadata"]["original_config"]
                    self.codexes_config = CodexesFactoryConfig.from_dict(original_config)
                else:
                    # Regular Codexes Factory config file
                    self.codexes_config = CodexesFactoryConfig.from_file(config)
            else:
                raise ConfigurationError(f"Configuration file not found: {config}")
        elif isinstance(config, dict):
            # Check if this is a migrated config dict with metadata
            if "codexes_factory_metadata" in config:
                original_config = config["codexes_factory_metadata"]["original_config"]
                self.codexes_config = CodexesFactoryConfig.from_dict(original_config)
            else:
                self.codexes_config = CodexesFactoryConfig.from_dict(config)
        elif isinstance(config, CodexesFactoryConfig):
            self.codexes_config = config
        else:
            raise ConfigurationError(f"Invalid configuration type: {type(config)}")
        
        # Convert to arxiv-writer format
        self.paper_config = self._convert_to_paper_config()
        
        # Initialize components
        self.context_collector = self._create_context_collector()
        self.paper_generator = ArxivPaperGenerator(self.paper_config)
        
        logger.info(f"CodexesFactoryAdapter initialized for imprint: {self.codexes_config.imprint_name}")
    
    def _convert_to_paper_config(self) -> PaperConfig:
        """Convert Codexes Factory configuration to arxiv-writer PaperConfig."""
        # Create LLM configuration
        llm_config = LLMConfig(
            default_model=self.codexes_config.default_model,
            available_models=self.codexes_config.available_models,
            model_parameters={
                model: {
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "top_p": 0.9
                } for model in self.codexes_config.available_models
            }
        )
        
        # Create validation configuration
        validation_config = ValidationConfig(
            enabled=self.codexes_config.validation_enabled,
            strict_mode=self.codexes_config.strict_mode,
            quality_thresholds=self.codexes_config.quality_thresholds
        )
        
        # Create template configuration
        template_config = TemplateConfig(
            template_file=self.codexes_config.template_file,
            section_order=self.codexes_config.section_order,
            custom_templates={},
            default_prompts={}
        )
        
        # Create main paper configuration
        paper_config = PaperConfig(
            output_directory=self.codexes_config.output_directory,
            llm_config=llm_config,
            validation_config=validation_config,
            template_config=template_config,
            # Set backward compatibility fields to match
            llm=llm_config,
            templates=template_config,
            validation=validation_config
        )
        
        return paper_config
    
    def _create_context_collector(self) -> ContextCollector:
        """Create context collector configured for Codexes Factory data patterns."""
        collection_types = []
        
        if self.codexes_config.collect_book_catalog:
            collection_types.append("book_catalog")
        if self.codexes_config.collect_imprint_config:
            collection_types.append("imprint_config")
        if self.codexes_config.collect_technical_architecture:
            collection_types.append("technical_architecture")
        if self.codexes_config.collect_performance_metrics:
            collection_types.append("performance_metrics")
        
        # If all are enabled, use the comprehensive xynapse_traces collection
        if len(collection_types) == 4:
            collection_types = ["xynapse_traces"]
        
        return create_codexes_factory_context_collector(
            workspace_root=self.codexes_config.workspace_root,
            collection_types=collection_types,
            validation_enabled=self.codexes_config.validation_enabled
        )
    
    def generate_paper(self, additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate academic paper using Codexes Factory workflow.
        
        Args:
            additional_context: Optional additional context data
            
        Returns:
            Dictionary containing generation results in Codexes Factory format
        """
        logger.info("Starting paper generation with Codexes Factory compatibility mode")
        
        try:
            # Collect context data
            logger.info("Collecting context data...")
            context_data = self.context_collector.collect_context()
            
            # Add additional context if provided
            if additional_context:
                context_data.update(additional_context)
            
            # Prepare context for paper generation
            prepared_context = self.context_collector.prepare_context(context_data)
            
            # Generate paper
            logger.info("Generating paper sections...")
            paper_result = self.paper_generator.generate_paper(prepared_context)
            
            # Convert result to Codexes Factory format
            codexes_result = self._convert_result_to_codexes_format(paper_result, context_data)
            
            logger.info("Paper generation completed successfully")
            return codexes_result
            
        except Exception as e:
            logger.error(f"Paper generation failed: {e}")
            raise
    
    def generate_section(self, section_name: str, additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate individual paper section using Codexes Factory workflow.
        
        Args:
            section_name: Name of the section to generate
            additional_context: Optional additional context data
            
        Returns:
            Dictionary containing section generation results
        """
        logger.info(f"Generating section: {section_name}")
        
        try:
            # Collect context data
            context_data = self.context_collector.collect_context()
            
            # Add additional context if provided
            if additional_context:
                context_data.update(additional_context)
                
                # Extract nested context variables to top level for template compatibility
                if "imprint_data" in additional_context:
                    for source_name, source_data in additional_context["imprint_data"].items():
                        if isinstance(source_data, dict):
                            # Flatten important variables to top level
                            for key, value in source_data.items():
                                if key in ["total_books", "publication_date_range", "book_catalog_summary", 
                                          "imprint_config_summary", "config_hierarchy_summary", "technical_innovations"]:
                                    context_data[key] = value
            
            # Add missing template variables with defaults
            context_data.setdefault("key_technologies", ["LLM orchestration", "Multi-level configuration", "LaTeX integration"])
            context_data.setdefault("ai_models_used", ["anthropic/claude-3-5-sonnet-20241022", "google/gemini-pro-1.5", "openai/gpt-4-turbo"])
            context_data.setdefault("technical_innovations", ["AI-assisted content generation", "Automated publishing pipeline", "Multi-language support"])
            context_data.setdefault("config_hierarchy_summary", "Five-tier hierarchy: Global → Publisher → Imprint → Tranche → Book")
            
            # Prepare context for section generation
            prepared_context = self.context_collector.prepare_context(context_data)
            
            # Ensure template variables are available at top level after preparation
            if "imprint_data" in context_data:
                for source_name, source_data in context_data["imprint_data"].items():
                    if isinstance(source_data, dict):
                        # Add important variables to prepared context
                        for key, value in source_data.items():
                            if key in ["total_books", "publication_date_range", "book_catalog_summary", 
                                      "imprint_config_summary", "config_hierarchy_summary", "technical_innovations"]:
                                prepared_context[key] = value
            
            # Ensure all required template variables are present
            prepared_context.setdefault("total_books", context_data.get("total_books", 10))
            prepared_context.setdefault("publication_date_range", context_data.get("publication_date_range", "September 2023 to April 2024"))
            prepared_context.setdefault("key_technologies", ["LLM orchestration", "Multi-level configuration", "LaTeX integration"])
            prepared_context.setdefault("ai_models_used", ["anthropic/claude-3-5-sonnet-20241022", "google/gemini-pro-1.5", "openai/gpt-4-turbo"])
            prepared_context.setdefault("technical_innovations", ["AI-assisted content generation", "Automated publishing pipeline", "Multi-language support"])
            prepared_context.setdefault("config_hierarchy_summary", "Five-tier hierarchy: Global → Publisher → Imprint → Tranche → Book")
            
            # Generate section
            from .models import SectionConfig
            section_config = SectionConfig(
                name=section_name,
                title=section_name.title(),
                template_key=section_name,
                required=True,
                min_words=100,
                max_words=1000
            )
            section_result = self.paper_generator.generate_section(section_config, prepared_context)
            
            # Convert result to Codexes Factory format
            codexes_result = {
                "section_name": section_name,
                "content": section_result.content,
                "word_count": section_result.word_count,
                "generated_at": section_result.generated_at.isoformat(),
                "model_used": section_result.model_used,
                "validation_status": section_result.validation_status,
                "metadata": section_result.metadata,
                "context_summary": {
                    "sources_used": list(context_data.get("sources", {}).keys()),
                    "total_context_size": len(str(context_data))
                }
            }
            
            logger.info(f"Section '{section_name}' generated successfully")
            return codexes_result
            
        except Exception as e:
            logger.error(f"Section generation failed: {e}")
            raise
    
    def _convert_result_to_codexes_format(self, paper_result, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert arxiv-writer result to Codexes Factory format."""
        return {
            "paper_content": paper_result.complete_paper,
            "sections": {
                name: {
                    "content": section.content,
                    "word_count": section.word_count,
                    "generated_at": section.generated_at.isoformat(),
                    "model_used": section.model_used,
                    "validation_status": section.validation_status,
                    "metadata": section.metadata
                }
                for name, section in paper_result.sections.items()
            },
            "generation_summary": {
                "total_sections": len(paper_result.sections),
                "total_word_count": sum(section.word_count for section in paper_result.sections.values()),
                "generation_time": paper_result.generation_summary.total_time if hasattr(paper_result.generation_summary, 'total_time') else None,
                "models_used": list(set(section.model_used for section in paper_result.sections.values())),
                "quality_score": paper_result.get_quality_score() if hasattr(paper_result, 'get_quality_score') else None
            },
            "context_summary": {
                "sources_collected": list(context_data.get("sources", {}).keys()),
                "collection_timestamp": context_data.get("collection_metadata", {}).get("timestamp"),
                "total_context_size": len(str(context_data))
            },
            "output_files": paper_result.output_files,
            "imprint_info": {
                "imprint_name": self.codexes_config.imprint_name,
                "workspace_root": self.codexes_config.workspace_root,
                "configuration_used": self.codexes_config.to_dict()
            }
        }
    
    def validate_paper(self, paper_content: str) -> Dict[str, Any]:
        """
        Validate paper content using Codexes Factory standards.
        
        Args:
            paper_content: Paper content to validate
            
        Returns:
            Validation results in Codexes Factory format
        """
        logger.info("Validating paper content")
        
        try:
            validation_result = self.paper_generator.validate_paper(paper_content)
            
            # Convert to Codexes Factory format
            codexes_validation = {
                "is_valid": validation_result.is_valid,
                "validation_score": validation_result.score if hasattr(validation_result, 'score') else None,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "quality_metrics": validation_result.metrics,
                "recommendations": validation_result.recommendations if hasattr(validation_result, 'recommendations') else [],
                "arxiv_compliance": {
                    "meets_standards": validation_result.is_valid,
                    "submission_ready": validation_result.is_valid and len(validation_result.errors) == 0
                }
            }
            
            logger.info(f"Paper validation completed. Valid: {validation_result.is_valid}")
            return codexes_validation
            
        except Exception as e:
            logger.error(f"Paper validation failed: {e}")
            raise
    
    def get_context_data(self) -> Dict[str, Any]:
        """
        Get collected context data in Codexes Factory format.
        
        Returns:
            Context data formatted for Codexes Factory compatibility
        """
        logger.info("Collecting context data")
        
        try:
            context_data = self.context_collector.collect_context()
            
            # Format for Codexes Factory compatibility
            codexes_context = {
                "imprint_data": context_data.get("sources", {}),
                "collection_metadata": context_data.get("collection_metadata", {}),
                "validation_results": context_data.get("validation_results", {}),
                "summary": {
                    "total_sources": len(context_data.get("sources", {})),
                    "successful_collections": len([
                        s for s in context_data.get("sources", {}).values() 
                        if isinstance(s, dict) and "error" not in s
                    ]),
                    "failed_collections": len([
                        s for s in context_data.get("sources", {}).values() 
                        if isinstance(s, dict) and "error" in s
                    ])
                }
            }
            
            logger.info("Context data collection completed")
            return codexes_context
            
        except Exception as e:
            logger.error(f"Context data collection failed: {e}")
            raise


def migrate_from_codexes_factory(
    codexes_config_path: Union[str, Path],
    output_config_path: Union[str, Path]
) -> PaperConfig:
    """
    Migrate Codexes Factory configuration to arxiv-writer format.
    
    Args:
        codexes_config_path: Path to existing Codexes Factory configuration
        output_config_path: Path where to save the converted configuration
        
    Returns:
        Converted PaperConfig instance
    """
    return migrate_codexes_factory_config(codexes_config_path, output_config_path)


def migrate_codexes_factory_config(
    codexes_config_path: Union[str, Path],
    output_config_path: Union[str, Path]
) -> PaperConfig:
    """
    Migrate Codexes Factory configuration to arxiv-writer format.
    
    Args:
        codexes_config_path: Path to existing Codexes Factory configuration
        output_config_path: Path where to save the converted configuration
        
    Returns:
        Converted PaperConfig instance
    """
    logger.info(f"Migrating configuration from {codexes_config_path} to {output_config_path}")
    
    try:
        # Load Codexes Factory configuration
        codexes_config = CodexesFactoryConfig.from_file(codexes_config_path)
        
        # Create adapter to perform conversion
        adapter = CodexesFactoryAdapter(codexes_config)
        paper_config = adapter.paper_config
        
        # Save converted configuration with Codexes Factory metadata preserved
        output_path = Path(output_config_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create enhanced config dict that preserves Codexes Factory information
        config_dict = paper_config.to_dict()
        config_dict["codexes_factory_metadata"] = {
            "imprint_name": codexes_config.imprint_name,
            "workspace_root": codexes_config.workspace_root,
            "original_config": codexes_config.to_dict()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, default=str)
        
        logger.info(f"Configuration migration completed. Saved to {output_path}")
        return paper_config
        
    except Exception as e:
        logger.error(f"Configuration migration failed: {e}")
        raise ConfigurationError(f"Failed to migrate configuration: {e}")


def create_codexes_compatibility_config(
    workspace_root: Union[str, Path] = ".",
    imprint_name: str = "xynapse_traces"
) -> CodexesFactoryConfig:
    """
    Create a configuration that replicates Codexes Factory behavior.
    
    Args:
        workspace_root: Root directory of the Codexes Factory workspace
        imprint_name: Name of the imprint to configure for
        
    Returns:
        CodexesFactoryConfig instance configured for compatibility
    """
    logger.info(f"Creating Codexes Factory compatibility configuration for {imprint_name}")
    
    config = CodexesFactoryConfig(
        workspace_root=str(workspace_root),
        imprint_name=imprint_name,
        output_directory="output/arxiv_papers",
        
        # Use the same models as Codexes Factory
        default_model="anthropic/claude-3-5-sonnet-20241022",
        available_models=[
            "anthropic/claude-3-5-sonnet-20241022",
            "google/gemini-pro-1.5",
            "openai/gpt-4-turbo",
            "xai/grok-beta"
        ],
        
        # Use Codexes Factory template structure
        template_file="templates/default_prompts.json",
        section_order=[
            "abstract",
            "introduction",
            "related_work", 
            "methodology",
            "results",
            "discussion",
            "conclusion",
            "references"
        ],
        
        # Enable all context collection for full compatibility
        collect_book_catalog=True,
        collect_imprint_config=True,
        collect_technical_architecture=True,
        collect_performance_metrics=True,
        
        # Use Codexes Factory validation standards
        validation_enabled=True,
        strict_mode=False,
        quality_thresholds={
            "min_word_count": 500,
            "max_word_count": 8000,
            "readability_score": 0.7,
            "coherence_score": 0.8,
            "citation_count": 10,
            "section_balance": 0.6
        }
    )
    
    logger.info("Codexes Factory compatibility configuration created")
    return config


# Convenience function for backward compatibility
def create_codexes_factory_paper_generator(
    config_path: Optional[Union[str, Path]] = None,
    workspace_root: Union[str, Path] = ".",
    imprint_name: str = "xynapse_traces"
) -> CodexesFactoryAdapter:
    """
    Create a paper generator configured for Codexes Factory compatibility.
    
    Args:
        config_path: Optional path to existing Codexes Factory configuration
        workspace_root: Root directory of the Codexes Factory workspace
        imprint_name: Name of the imprint
        
    Returns:
        CodexesFactoryAdapter instance ready for paper generation
    """
    if config_path:
        config = CodexesFactoryConfig.from_file(config_path)
    else:
        config = create_codexes_compatibility_config(workspace_root, imprint_name)
    
    return CodexesFactoryAdapter(config)