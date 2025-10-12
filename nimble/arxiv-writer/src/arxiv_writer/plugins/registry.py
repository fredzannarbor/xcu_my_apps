"""
Plugin registry for managing plugin discovery and registration.

This module provides the PluginRegistry class that handles plugin
registration, discovery, and lifecycle management.
"""

import importlib
import importlib.util
import inspect
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type, Any, Set
from collections import defaultdict

from .base import BasePlugin, PluginType, PluginMetadata
from ..core.exceptions import PluginError


logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Registry for managing plugins in the arxiv-writer system.
    
    The registry handles plugin discovery, registration, initialization,
    and lifecycle management.
    """
    
    def __init__(self):
        """Initialize empty plugin registry."""
        self._plugins: Dict[str, BasePlugin] = {}
        self._plugin_classes: Dict[str, Type[BasePlugin]] = {}
        self._plugins_by_type: Dict[PluginType, List[str]] = defaultdict(list)
        self._plugin_dependencies: Dict[str, Set[str]] = {}
        self._initialized_plugins: Set[str] = set()
    
    def register_plugin_class(self, plugin_class: Type[BasePlugin]) -> None:
        """
        Register a plugin class.
        
        Args:
            plugin_class: Plugin class to register
            
        Raises:
            PluginError: If plugin registration fails
        """
        if not issubclass(plugin_class, BasePlugin):
            raise PluginError(f"Plugin class {plugin_class.__name__} must inherit from BasePlugin")
        
        # Create temporary instance to get metadata
        try:
            temp_instance = plugin_class()
            metadata = temp_instance.metadata
        except Exception as e:
            raise PluginError(f"Failed to get metadata for plugin {plugin_class.__name__}: {e}")
        
        plugin_name = metadata.name
        
        if plugin_name in self._plugin_classes:
            logger.warning(f"Plugin {plugin_name} is already registered, overwriting")
        
        self._plugin_classes[plugin_name] = plugin_class
        self._plugins_by_type[metadata.plugin_type].append(plugin_name)
        self._plugin_dependencies[plugin_name] = set(metadata.dependencies)
        
        logger.info(f"Registered plugin class: {plugin_name} (type: {metadata.plugin_type.value})")
    
    def create_plugin_instance(self, plugin_name: str, config: Dict[str, Any] = None) -> BasePlugin:
        """
        Create an instance of a registered plugin.
        
        Args:
            plugin_name: Name of the plugin to instantiate
            config: Configuration for the plugin
            
        Returns:
            Plugin instance
            
        Raises:
            PluginError: If plugin creation fails
        """
        if plugin_name not in self._plugin_classes:
            raise PluginError(f"Plugin {plugin_name} is not registered")
        
        plugin_class = self._plugin_classes[plugin_name]
        
        try:
            plugin_instance = plugin_class(config or {})
            
            # Validate configuration
            if not plugin_instance.validate_config(config or {}):
                raise PluginError(f"Invalid configuration for plugin {plugin_name}")
            
            return plugin_instance
        except Exception as e:
            raise PluginError(f"Failed to create instance of plugin {plugin_name}: {e}")
    
    def register_plugin_instance(self, plugin_instance: BasePlugin) -> None:
        """
        Register a plugin instance.
        
        Args:
            plugin_instance: Plugin instance to register
            
        Raises:
            PluginError: If plugin registration fails
        """
        metadata = plugin_instance.metadata
        plugin_name = metadata.name
        
        if plugin_name in self._plugins:
            logger.warning(f"Plugin instance {plugin_name} is already registered, overwriting")
        
        self._plugins[plugin_name] = plugin_instance
        
        # Also register the class if not already registered
        if plugin_name not in self._plugin_classes:
            self._plugin_classes[plugin_name] = plugin_instance.__class__
            self._plugins_by_type[metadata.plugin_type].append(plugin_name)
            self._plugin_dependencies[plugin_name] = set(metadata.dependencies)
        
        logger.info(f"Registered plugin instance: {plugin_name}")
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        Get a registered plugin instance.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin instance or None if not found
        """
        return self._plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[BasePlugin]:
        """
        Get all registered plugin instances of a specific type.
        
        Args:
            plugin_type: Type of plugins to retrieve
            
        Returns:
            List of plugin instances
        """
        plugin_names = self._plugins_by_type.get(plugin_type, [])
        return [self._plugins[name] for name in plugin_names if name in self._plugins]
    
    def list_registered_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        List all registered plugins with their metadata.
        
        Returns:
            Dictionary mapping plugin names to their metadata
        """
        result = {}
        for plugin_name, plugin_class in self._plugin_classes.items():
            try:
                temp_instance = plugin_class()
                metadata = temp_instance.metadata
                result[plugin_name] = {
                    'name': metadata.name,
                    'version': metadata.version,
                    'description': metadata.description,
                    'author': metadata.author,
                    'type': metadata.plugin_type.value,
                    'dependencies': metadata.dependencies,
                    'initialized': plugin_name in self._initialized_plugins,
                    'instance_registered': plugin_name in self._plugins
                }
            except Exception as e:
                result[plugin_name] = {
                    'name': plugin_name,
                    'error': str(e)
                }
        return result
    
    def initialize_plugin(self, plugin_name: str) -> None:
        """
        Initialize a registered plugin.
        
        Args:
            plugin_name: Name of the plugin to initialize
            
        Raises:
            PluginError: If plugin initialization fails
        """
        if plugin_name not in self._plugins:
            raise PluginError(f"Plugin {plugin_name} is not registered")
        
        if plugin_name in self._initialized_plugins:
            logger.debug(f"Plugin {plugin_name} is already initialized")
            return
        
        plugin = self._plugins[plugin_name]
        
        # Initialize dependencies first
        dependencies = self._plugin_dependencies.get(plugin_name, set())
        for dep_name in dependencies:
            if dep_name not in self._plugins:
                raise PluginError(f"Plugin {plugin_name} depends on {dep_name} which is not registered")
            self.initialize_plugin(dep_name)
        
        try:
            plugin.initialize()
            self._initialized_plugins.add(plugin_name)
            logger.info(f"Initialized plugin: {plugin_name}")
        except Exception as e:
            raise PluginError(f"Failed to initialize plugin {plugin_name}: {e}")
    
    def initialize_all_plugins(self) -> None:
        """
        Initialize all registered plugins in dependency order.
        
        Raises:
            PluginError: If any plugin initialization fails
        """
        # Topological sort to handle dependencies
        initialization_order = self._get_initialization_order()
        
        for plugin_name in initialization_order:
            if plugin_name in self._plugins:
                self.initialize_plugin(plugin_name)
    
    def cleanup_plugin(self, plugin_name: str) -> None:
        """
        Cleanup a plugin.
        
        Args:
            plugin_name: Name of the plugin to cleanup
        """
        if plugin_name not in self._plugins:
            logger.warning(f"Plugin {plugin_name} is not registered")
            return
        
        if plugin_name not in self._initialized_plugins:
            logger.debug(f"Plugin {plugin_name} is not initialized")
            return
        
        plugin = self._plugins[plugin_name]
        
        try:
            plugin.cleanup()
            self._initialized_plugins.discard(plugin_name)
            logger.info(f"Cleaned up plugin: {plugin_name}")
        except Exception as e:
            logger.error(f"Failed to cleanup plugin {plugin_name}: {e}")
    
    def cleanup_all_plugins(self) -> None:
        """Cleanup all initialized plugins."""
        for plugin_name in list(self._initialized_plugins):
            self.cleanup_plugin(plugin_name)
    
    def unregister_plugin(self, plugin_name: str) -> None:
        """
        Unregister a plugin.
        
        Args:
            plugin_name: Name of the plugin to unregister
        """
        # Cleanup first if initialized
        if plugin_name in self._initialized_plugins:
            self.cleanup_plugin(plugin_name)
        
        # Remove from all registries
        if plugin_name in self._plugins:
            del self._plugins[plugin_name]
        
        if plugin_name in self._plugin_classes:
            plugin_class = self._plugin_classes[plugin_name]
            temp_instance = plugin_class()
            plugin_type = temp_instance.metadata.plugin_type
            
            del self._plugin_classes[plugin_name]
            
            if plugin_name in self._plugins_by_type[plugin_type]:
                self._plugins_by_type[plugin_type].remove(plugin_name)
        
        if plugin_name in self._plugin_dependencies:
            del self._plugin_dependencies[plugin_name]
        
        logger.info(f"Unregistered plugin: {plugin_name}")
    
    def discover_plugins(self, plugin_directories: List[str]) -> int:
        """
        Discover and register plugins from directories.
        
        Args:
            plugin_directories: List of directories to search for plugins
            
        Returns:
            Number of plugins discovered and registered
        """
        discovered_count = 0
        
        for directory in plugin_directories:
            path = Path(directory)
            if not path.exists() or not path.is_dir():
                logger.warning(f"Plugin directory does not exist: {directory}")
                continue
            
            discovered_count += self._discover_plugins_in_directory(path)
        
        return discovered_count
    
    def _discover_plugins_in_directory(self, directory: Path) -> int:
        """
        Discover plugins in a specific directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            Number of plugins discovered
        """
        discovered_count = 0
        
        # Look for Python files
        for py_file in directory.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            try:
                discovered_count += self._load_plugins_from_file(py_file)
            except Exception as e:
                logger.error(f"Failed to load plugins from {py_file}: {e}")
        
        # Recursively search subdirectories
        for subdir in directory.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("__"):
                discovered_count += self._discover_plugins_in_directory(subdir)
        
        return discovered_count
    
    def _load_plugins_from_file(self, file_path: Path) -> int:
        """
        Load plugins from a Python file.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Number of plugins loaded
        """
        # Convert file path to module name
        module_name = file_path.stem
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            loaded_count = 0
            
            # Find all BasePlugin subclasses in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, BasePlugin) and 
                    obj is not BasePlugin and 
                    obj.__module__ == module.__name__):
                    
                    try:
                        self.register_plugin_class(obj)
                        loaded_count += 1
                    except Exception as e:
                        logger.error(f"Failed to register plugin class {name}: {e}")
            
            return loaded_count
            
        except Exception as e:
            logger.error(f"Failed to load module from {file_path}: {e}")
            return 0
    
    def _get_initialization_order(self) -> List[str]:
        """
        Get plugin initialization order based on dependencies.
        
        Returns:
            List of plugin names in initialization order
        """
        # Simple topological sort
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(plugin_name: str):
            if plugin_name in temp_visited:
                raise PluginError(f"Circular dependency detected involving plugin {plugin_name}")
            
            if plugin_name in visited:
                return
            
            temp_visited.add(plugin_name)
            
            # Visit dependencies first
            dependencies = self._plugin_dependencies.get(plugin_name, set())
            for dep_name in dependencies:
                if dep_name in self._plugin_classes:
                    visit(dep_name)
            
            temp_visited.remove(plugin_name)
            visited.add(plugin_name)
            order.append(plugin_name)
        
        # Visit all plugins
        for plugin_name in self._plugin_classes:
            if plugin_name not in visited:
                visit(plugin_name)
        
        return order


# Global plugin registry instance
_global_registry = None


def get_global_registry() -> PluginRegistry:
    """
    Get the global plugin registry instance.
    
    Returns:
        Global plugin registry
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = PluginRegistry()
    return _global_registry


def register_plugin(plugin_class: Type[BasePlugin]) -> None:
    """
    Register a plugin class with the global registry.
    
    Args:
        plugin_class: Plugin class to register
    """
    registry = get_global_registry()
    registry.register_plugin_class(plugin_class)