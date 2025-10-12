"""
Plugin manager for high-level plugin operations.

This module provides the PluginManager class that offers a convenient
interface for plugin loading, configuration, and lifecycle management.
"""

import logging
import importlib
import importlib.metadata
from pathlib import Path
from typing import Dict, List, Optional, Any, Type, Set
import json
import yaml

from .base import BasePlugin, PluginType
from .registry import PluginRegistry, get_global_registry
from ..core.exceptions import PluginError


logger = logging.getLogger(__name__)


class PluginManager:
    """
    High-level manager for plugin operations.
    
    The PluginManager provides a convenient interface for loading,
    configuring, and managing plugins in the arxiv-writer system.
    """
    
    def __init__(self, registry: Optional[PluginRegistry] = None):
        """
        Initialize plugin manager.
        
        Args:
            registry: Plugin registry to use (defaults to global registry)
        """
        self.registry = registry or get_global_registry()
        self._plugin_configs: Dict[str, Dict[str, Any]] = {}
        self._discovery_paths: Set[str] = set()
        self._auto_discovery_enabled: bool = True
    
    def load_plugins_from_config(self, config: Dict[str, Any]) -> None:
        """
        Load and configure plugins from configuration.
        
        Args:
            config: Plugin configuration dictionary
            
        Expected config format:
        {
            "plugin_directories": ["path/to/plugins"],
            "plugins": {
                "plugin_name": {
                    "enabled": true,
                    "config": {...}
                }
            }
        }
        """
        # Discover plugins from directories
        plugin_directories = config.get("plugin_directories", [])
        if plugin_directories:
            discovered = self.registry.discover_plugins(plugin_directories)
            logger.info(f"Discovered {discovered} plugins from directories")
        
        # Configure and instantiate plugins
        plugins_config = config.get("plugins", {})
        for plugin_name, plugin_config in plugins_config.items():
            if not plugin_config.get("enabled", True):
                logger.debug(f"Plugin {plugin_name} is disabled, skipping")
                continue
            
            try:
                self.load_plugin(plugin_name, plugin_config.get("config", {}))
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")
    
    def load_plugin(self, plugin_name: str, config: Dict[str, Any] = None) -> BasePlugin:
        """
        Load and configure a specific plugin.
        
        Args:
            plugin_name: Name of the plugin to load
            config: Plugin configuration
            
        Returns:
            Loaded plugin instance
            
        Raises:
            PluginError: If plugin loading fails
        """
        # Store configuration
        self._plugin_configs[plugin_name] = config or {}
        
        # Create plugin instance
        plugin_instance = self.registry.create_plugin_instance(plugin_name, config)
        
        # Register instance
        self.registry.register_plugin_instance(plugin_instance)
        
        # Initialize plugin
        self.registry.initialize_plugin(plugin_name)
        
        logger.info(f"Loaded and initialized plugin: {plugin_name}")
        return plugin_instance
    
    def unload_plugin(self, plugin_name: str) -> None:
        """
        Unload a plugin.
        
        Args:
            plugin_name: Name of the plugin to unload
        """
        self.registry.unregister_plugin(plugin_name)
        if plugin_name in self._plugin_configs:
            del self._plugin_configs[plugin_name]
        logger.info(f"Unloaded plugin: {plugin_name}")
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        Get a loaded plugin instance.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin instance or None if not found
        """
        return self.registry.get_plugin(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[BasePlugin]:
        """
        Get all loaded plugins of a specific type.
        
        Args:
            plugin_type: Type of plugins to retrieve
            
        Returns:
            List of plugin instances
        """
        return self.registry.get_plugins_by_type(plugin_type)
    
    def list_available_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        List all available plugins.
        
        Returns:
            Dictionary of plugin information
        """
        return self.registry.list_registered_plugins()
    
    def reload_plugin(self, plugin_name: str) -> BasePlugin:
        """
        Reload a plugin with its current configuration.
        
        Args:
            plugin_name: Name of the plugin to reload
            
        Returns:
            Reloaded plugin instance
        """
        config = self._plugin_configs.get(plugin_name, {})
        self.unload_plugin(plugin_name)
        return self.load_plugin(plugin_name, config)
    
    def initialize_all_plugins(self) -> None:
        """Initialize all loaded plugins."""
        self.registry.initialize_all_plugins()
    
    def cleanup_all_plugins(self) -> None:
        """Cleanup all loaded plugins."""
        self.registry.cleanup_all_plugins()
    
    def register_plugin_class(self, plugin_class: Type[BasePlugin]) -> None:
        """
        Register a plugin class.
        
        Args:
            plugin_class: Plugin class to register
        """
        self.registry.register_plugin_class(plugin_class)
    
    def discover_plugins(self, directories: List[str]) -> int:
        """
        Discover plugins in directories.
        
        Args:
            directories: List of directories to search
            
        Returns:
            Number of plugins discovered
        """
        discovered = self.registry.discover_plugins(directories)
        self._discovery_paths.update(directories)
        return discovered
    
    def discover_plugins_from_entry_points(self, group: str = "arxiv_writer.plugins") -> int:
        """
        Discover plugins from setuptools entry points.
        
        Args:
            group: Entry point group name
            
        Returns:
            Number of plugins discovered
        """
        discovered_count = 0
        
        try:
            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, 'select'):
                # Python 3.10+
                plugin_entries = entry_points.select(group=group)
            else:
                # Python 3.8-3.9
                plugin_entries = entry_points.get(group, [])
            
            for entry_point in plugin_entries:
                try:
                    plugin_class = entry_point.load()
                    if issubclass(plugin_class, BasePlugin):
                        self.registry.register_plugin_class(plugin_class)
                        discovered_count += 1
                        logger.info(f"Discovered plugin from entry point: {entry_point.name}")
                    else:
                        logger.warning(f"Entry point {entry_point.name} does not point to a BasePlugin subclass")
                except Exception as e:
                    logger.error(f"Failed to load plugin from entry point {entry_point.name}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to discover plugins from entry points: {e}")
        
        return discovered_count
    
    def discover_plugins_from_packages(self, package_names: List[str]) -> int:
        """
        Discover plugins from installed packages.
        
        Args:
            package_names: List of package names to search
            
        Returns:
            Number of plugins discovered
        """
        discovered_count = 0
        
        for package_name in package_names:
            try:
                package = importlib.import_module(package_name)
                discovered_count += self._discover_plugins_in_package(package)
            except ImportError:
                logger.warning(f"Package {package_name} not found")
            except Exception as e:
                logger.error(f"Failed to discover plugins in package {package_name}: {e}")
        
        return discovered_count
    
    def auto_discover_plugins(self) -> int:
        """
        Automatically discover plugins from common locations.
        
        Returns:
            Number of plugins discovered
        """
        if not self._auto_discovery_enabled:
            return 0
        
        discovered_count = 0
        
        # Discover from entry points
        discovered_count += self.discover_plugins_from_entry_points()
        
        # Discover from common plugin directories
        common_paths = [
            "plugins",
            "arxiv_writer_plugins",
            str(Path.home() / ".arxiv_writer" / "plugins"),
            "/usr/local/share/arxiv_writer/plugins",
        ]
        
        existing_paths = [path for path in common_paths if Path(path).exists()]
        if existing_paths:
            discovered_count += self.discover_plugins(existing_paths)
        
        return discovered_count
    
    def load_plugins_from_config_file(self, config_file: str) -> None:
        """
        Load plugins from a configuration file.
        
        Args:
            config_file: Path to configuration file (JSON or YAML)
        """
        config_path = Path(config_file)
        if not config_path.exists():
            raise PluginError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() == '.json':
                    config = json.load(f)
                elif config_path.suffix.lower() in ['.yml', '.yaml']:
                    config = yaml.safe_load(f)
                else:
                    raise PluginError(f"Unsupported configuration file format: {config_path.suffix}")
            
            self.load_plugins_from_config(config)
            
        except Exception as e:
            raise PluginError(f"Failed to load plugin configuration from {config_file}: {e}")
    
    def _discover_plugins_in_package(self, package) -> int:
        """
        Discover plugins in a Python package.
        
        Args:
            package: Python package to search
            
        Returns:
            Number of plugins discovered
        """
        discovered_count = 0
        
        if hasattr(package, '__path__'):
            # Package has submodules
            import pkgutil
            
            for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
                try:
                    module = importlib.import_module(modname)
                    discovered_count += self._discover_plugins_in_module(module)
                except Exception as e:
                    logger.error(f"Failed to import module {modname}: {e}")
        else:
            # Single module
            discovered_count += self._discover_plugins_in_module(package)
        
        return discovered_count
    
    def _discover_plugins_in_module(self, module) -> int:
        """
        Discover plugins in a Python module.
        
        Args:
            module: Python module to search
            
        Returns:
            Number of plugins discovered
        """
        import inspect
        discovered_count = 0
        
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (issubclass(obj, BasePlugin) and 
                obj is not BasePlugin and 
                obj.__module__ == module.__name__):
                
                try:
                    self.registry.register_plugin_class(obj)
                    discovered_count += 1
                    logger.info(f"Discovered plugin class: {name}")
                except Exception as e:
                    logger.error(f"Failed to register plugin class {name}: {e}")
        
        return discovered_count
    
    def validate_plugin_dependencies(self) -> Dict[str, List[str]]:
        """
        Validate plugin dependencies.
        
        Returns:
            Dictionary mapping plugin names to lists of missing dependencies
        """
        missing_deps = {}
        
        for plugin_name, plugin in self.registry._plugins.items():
            metadata = plugin.metadata
            missing = []
            
            for dep_name in metadata.dependencies:
                if dep_name not in self.registry._plugins:
                    missing.append(dep_name)
            
            if missing:
                missing_deps[plugin_name] = missing
        
        return missing_deps
    
    def get_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status information for all plugins.
        
        Returns:
            Dictionary with plugin status information
        """
        status = {}
        plugin_info = self.list_available_plugins()
        
        for plugin_name, info in plugin_info.items():
            status[plugin_name] = {
                **info,
                'config': self._plugin_configs.get(plugin_name, {}),
                'dependencies_satisfied': plugin_name not in self.validate_plugin_dependencies()
            }
        
        return status
    
    def resolve_plugin_conflicts(self) -> Dict[str, List[str]]:
        """
        Identify and resolve plugin conflicts.
        
        Returns:
            Dictionary mapping conflict types to lists of affected plugins
        """
        conflicts = {
            'name_conflicts': [],
            'type_conflicts': [],
            'dependency_conflicts': []
        }
        
        # Check for name conflicts
        plugin_names = {}
        for plugin_name, plugin in self.registry._plugins.items():
            metadata = plugin.metadata
            if metadata.name in plugin_names:
                conflicts['name_conflicts'].extend([plugin_names[metadata.name], plugin_name])
            else:
                plugin_names[metadata.name] = plugin_name
        
        # Check for type conflicts (multiple plugins of same type with conflicting functionality)
        type_groups = {}
        for plugin_name, plugin in self.registry._plugins.items():
            metadata = plugin.metadata
            plugin_type = metadata.plugin_type
            if plugin_type not in type_groups:
                type_groups[plugin_type] = []
            type_groups[plugin_type].append(plugin_name)
        
        # For now, just log type groups with multiple plugins
        for plugin_type, plugins in type_groups.items():
            if len(plugins) > 1:
                logger.info(f"Multiple plugins of type {plugin_type}: {plugins}")
        
        # Check for dependency conflicts
        missing_deps = self.validate_plugin_dependencies()
        conflicts['dependency_conflicts'] = list(missing_deps.keys())
        
        return conflicts
    
    def enable_auto_discovery(self, enabled: bool = True) -> None:
        """
        Enable or disable automatic plugin discovery.
        
        Args:
            enabled: Whether to enable auto discovery
        """
        self._auto_discovery_enabled = enabled
    
    def add_discovery_path(self, path: str) -> None:
        """
        Add a path for plugin discovery.
        
        Args:
            path: Directory path to add
        """
        self._discovery_paths.add(path)
    
    def remove_discovery_path(self, path: str) -> None:
        """
        Remove a path from plugin discovery.
        
        Args:
            path: Directory path to remove
        """
        self._discovery_paths.discard(path)
    
    def get_discovery_paths(self) -> List[str]:
        """
        Get list of plugin discovery paths.
        
        Returns:
            List of discovery paths
        """
        return list(self._discovery_paths)
    
    def refresh_plugins(self) -> int:
        """
        Refresh plugin discovery from all configured paths.
        
        Returns:
            Number of new plugins discovered
        """
        initial_count = len(self.registry._plugin_classes)
        
        # Re-discover from all paths
        if self._discovery_paths:
            self.discover_plugins(list(self._discovery_paths))
        
        # Auto-discover if enabled
        if self._auto_discovery_enabled:
            self.auto_discover_plugins()
        
        final_count = len(self.registry._plugin_classes)
        return final_count - initial_count
    
    def export_plugin_config(self, output_file: str) -> None:
        """
        Export current plugin configuration to a file.
        
        Args:
            output_file: Path to output file
        """
        config = {
            "plugin_directories": list(self._discovery_paths),
            "auto_discovery": self._auto_discovery_enabled,
            "plugins": {}
        }
        
        for plugin_name, plugin_config in self._plugin_configs.items():
            plugin = self.get_plugin(plugin_name)
            if plugin:
                config["plugins"][plugin_name] = {
                    "enabled": True,
                    "config": plugin_config,
                    "metadata": {
                        "name": plugin.metadata.name,
                        "version": plugin.metadata.version,
                        "description": plugin.metadata.description,
                        "type": plugin.metadata.plugin_type.value
                    }
                }
        
        output_path = Path(output_file)
        try:
            with open(output_path, 'w') as f:
                if output_path.suffix.lower() == '.json':
                    json.dump(config, f, indent=2)
                elif output_path.suffix.lower() in ['.yml', '.yaml']:
                    yaml.dump(config, f, default_flow_style=False)
                else:
                    # Default to JSON
                    json.dump(config, f, indent=2)
            
            logger.info(f"Plugin configuration exported to {output_file}")
            
        except Exception as e:
            raise PluginError(f"Failed to export plugin configuration: {e}")
    
    def create_plugin_template(self, plugin_name: str, plugin_type: PluginType, output_dir: str) -> str:
        """
        Create a template for a new plugin.
        
        Args:
            plugin_name: Name of the plugin
            plugin_type: Type of plugin to create
            output_dir: Directory to create the template in
            
        Returns:
            Path to the created template file
        """
        template_content = self._generate_plugin_template(plugin_name, plugin_type)
        
        output_path = Path(output_dir) / f"{plugin_name.lower().replace(' ', '_')}_plugin.py"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(template_content)
        
        logger.info(f"Plugin template created at {output_path}")
        return str(output_path)
    
    def _generate_plugin_template(self, plugin_name: str, plugin_type: PluginType) -> str:
        """
        Generate plugin template code.
        
        Args:
            plugin_name: Name of the plugin
            plugin_type: Type of plugin
            
        Returns:
            Template code as string
        """
        class_name = f"{plugin_name.replace(' ', '').replace('_', '')}Plugin"
        
        if plugin_type == PluginType.SECTION:
            base_class = "SectionPlugin"
            abstract_methods = """
    def generate_section(self, context: Dict[str, Any]) -> Section:
        \"\"\"Generate section content.\"\"\"
        return Section(
            name=self.metadata.name,
            title=f"{plugin_name} Section",
            content="Generated content goes here",
            word_count=0
        )"""
        elif plugin_type == PluginType.FORMATTER:
            base_class = "FormatterPlugin"
            abstract_methods = """
    def format_paper(self, sections: List[Section]) -> str:
        \"\"\"Format paper sections.\"\"\"
        return "\\n\\n".join([f"# {section.title}\\n{section.content}" for section in sections])
    
    def get_supported_formats(self) -> List[str]:
        \"\"\"Return supported formats.\"\"\"
        return ["custom_format"]"""
        elif plugin_type == PluginType.VALIDATOR:
            base_class = "ValidatorPlugin"
            abstract_methods = """
    def validate_content(self, content: str, context: Dict[str, Any] = None) -> ValidationResult:
        \"\"\"Validate content.\"\"\"
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            metrics={}
        )"""
        else:
            base_class = "ContextProcessorPlugin"
            abstract_methods = """
    def process_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Process context data.\"\"\"
        processed = context.copy()
        processed["processed_by"] = self.metadata.name
        return processed"""
        
        template = f'''"""
{plugin_name} plugin for arxiv-writer.

This plugin was generated automatically. Customize it according to your needs.
"""

from typing import Dict, Any, List
from arxiv_writer.plugins import {base_class}, PluginMetadata, PluginType
from arxiv_writer.core.models import Section, ValidationResult


class {class_name}({base_class}):
    """
    {plugin_name} plugin implementation.
    
    TODO: Add plugin description and usage instructions.
    """
    
    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="{plugin_name.lower().replace(' ', '_')}",
            version="1.0.0",
            description="{plugin_name} plugin",
            author="Your Name",
            plugin_type=PluginType.{plugin_type.name}
        )
{abstract_methods}
'''
        
        return template


# Global plugin manager instance
_global_manager = None


def get_global_manager() -> PluginManager:
    """
    Get the global plugin manager instance.
    
    Returns:
        Global plugin manager
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = PluginManager()
    return _global_manager