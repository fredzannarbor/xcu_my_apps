"""
Plugin system for extending arxiv-writer functionality.

This module provides a plugin architecture that allows users to extend
the paper generation process with custom components.
"""

from .base import (
    BasePlugin, 
    SectionPlugin, 
    FormatterPlugin, 
    ValidatorPlugin,
    ContextProcessorPlugin,
    PluginType,
    PluginMetadata
)
from .manager import PluginManager, get_global_manager
from .registry import PluginRegistry, get_global_registry, register_plugin

__all__ = [
    "BasePlugin",
    "SectionPlugin", 
    "FormatterPlugin", 
    "ValidatorPlugin",
    "ContextProcessorPlugin",
    "PluginType",
    "PluginMetadata",
    "PluginManager",
    "PluginRegistry",
    "get_global_manager",
    "get_global_registry",
    "register_plugin"
]
