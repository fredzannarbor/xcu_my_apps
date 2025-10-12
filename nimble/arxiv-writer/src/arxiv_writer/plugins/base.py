"""
Base plugin classes for the arxiv-writer plugin system.

This module defines the base classes that all plugins must inherit from,
providing a consistent interface for plugin development and management.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from ..core.models import Section, ValidationResult


class PluginType(Enum):
    """Types of plugins supported by the system."""
    SECTION = "section"
    FORMATTER = "formatter"
    VALIDATOR = "validator"
    CONTEXT_PROCESSOR = "context_processor"


@dataclass
class PluginMetadata:
    """Metadata for plugin registration and management."""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = None
    config_schema: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.config_schema is None:
            self.config_schema = {}


class BasePlugin(ABC):
    """
    Base class for all arxiv-writer plugins.
    
    All plugins must inherit from this class and implement the required methods.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize plugin with configuration.
        
        Args:
            config: Plugin-specific configuration dictionary
        """
        self.config = config or {}
        self._initialized = False
        self._metadata = None
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass
    
    def initialize(self) -> None:
        """
        Initialize plugin resources.
        
        This method is called once when the plugin is loaded.
        Override to perform any setup operations.
        """
        self._initialized = True
    
    def cleanup(self) -> None:
        """
        Cleanup plugin resources.
        
        This method is called when the plugin is unloaded.
        Override to perform any cleanup operations.
        """
        self._initialized = False
    
    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._initialized
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate plugin configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        # Basic validation - can be overridden by subclasses
        if not self.metadata.config_schema:
            return True
        
        # Simple schema validation - in a real implementation,
        # you might use jsonschema or similar
        required_keys = self.metadata.config_schema.get('required', [])
        return all(key in config for key in required_keys)


class SectionPlugin(BasePlugin):
    """
    Base class for plugins that generate custom paper sections.
    
    Section plugins can generate new types of sections or modify
    the generation process for existing sections.
    """
    
    @property
    def metadata(self) -> PluginMetadata:
        """Return section plugin metadata."""
        if self._metadata is None:
            self._metadata = PluginMetadata(
                name=self.__class__.__name__,
                version="1.0.0",
                description="Custom section plugin",
                author="Unknown",
                plugin_type=PluginType.SECTION
            )
        return self._metadata
    
    @abstractmethod
    def generate_section(self, context: Dict[str, Any]) -> Section:
        """
        Generate custom section content.
        
        Args:
            context: Context data for section generation
            
        Returns:
            Generated section
        """
        pass
    
    def validate_section(self, section: Section) -> ValidationResult:
        """
        Validate custom section content.
        
        Args:
            section: Section to validate
            
        Returns:
            Validation result
        """
        # Default validation - can be overridden
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            metrics={"score": 1.0}
        )
    
    def get_supported_sections(self) -> List[str]:
        """
        Get list of section names this plugin can generate.
        
        Returns:
            List of supported section names
        """
        return []


class FormatterPlugin(BasePlugin):
    """
    Base class for plugins that format paper output.
    
    Formatter plugins can modify how the final paper is assembled
    and formatted, supporting different output formats or styles.
    """
    
    @property
    def metadata(self) -> PluginMetadata:
        """Return formatter plugin metadata."""
        if self._metadata is None:
            self._metadata = PluginMetadata(
                name=self.__class__.__name__,
                version="1.0.0",
                description="Custom formatter plugin",
                author="Unknown",
                plugin_type=PluginType.FORMATTER
            )
        return self._metadata
    
    @abstractmethod
    def format_paper(self, sections: List[Section]) -> str:
        """
        Format paper sections into final output.
        
        Args:
            sections: List of paper sections to format
            
        Returns:
            Formatted paper content
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Return list of supported output formats.
        
        Returns:
            List of supported format names (e.g., ['latex', 'markdown'])
        """
        pass
    
    def format_section(self, section: Section) -> str:
        """
        Format individual section.
        
        Args:
            section: Section to format
            
        Returns:
            Formatted section content
        """
        return section.content


class ValidatorPlugin(BasePlugin):
    """
    Base class for plugins that validate paper content.
    
    Validator plugins can implement custom validation rules
    for paper quality, academic standards, or specific requirements.
    """
    
    @property
    def metadata(self) -> PluginMetadata:
        """Return validator plugin metadata."""
        if self._metadata is None:
            self._metadata = PluginMetadata(
                name=self.__class__.__name__,
                version="1.0.0",
                description="Custom validator plugin",
                author="Unknown",
                plugin_type=PluginType.VALIDATOR
            )
        return self._metadata
    
    @abstractmethod
    def validate_content(self, content: str, context: Dict[str, Any] = None) -> ValidationResult:
        """
        Validate content against plugin-specific criteria.
        
        Args:
            content: Content to validate
            context: Optional context for validation
            
        Returns:
            Validation result
        """
        pass
    
    def get_validation_criteria(self) -> Dict[str, Any]:
        """
        Get validation criteria used by this plugin.
        
        Returns:
            Dictionary describing validation criteria
        """
        return {}


class ContextProcessorPlugin(BasePlugin):
    """
    Base class for plugins that process context data.
    
    Context processor plugins can modify or enhance the context
    data used for paper generation.
    """
    
    @property
    def metadata(self) -> PluginMetadata:
        """Return context processor plugin metadata."""
        if self._metadata is None:
            self._metadata = PluginMetadata(
                name=self.__class__.__name__,
                version="1.0.0",
                description="Custom context processor plugin",
                author="Unknown",
                plugin_type=PluginType.CONTEXT_PROCESSOR
            )
        return self._metadata
    
    @abstractmethod
    def process_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and modify context data.
        
        Args:
            context: Original context data
            
        Returns:
            Processed context data
        """
        pass
    
    def get_required_context_keys(self) -> List[str]:
        """
        Get list of required context keys for this processor.
        
        Returns:
            List of required context keys
        """
        return []