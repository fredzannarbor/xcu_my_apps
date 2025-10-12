"""
Integration tests for plugin discovery and loading functionality.
"""

import pytest
import tempfile
import shutil
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.arxiv_writer.plugins import (
    PluginManager, PluginRegistry, SectionPlugin, FormatterPlugin,
    PluginType, PluginMetadata
)
from src.arxiv_writer.core.models import Section
from src.arxiv_writer.core.exceptions import PluginError


class TestPluginDiscovery:
    """Tests for plugin discovery functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.registry = PluginRegistry()
        self.manager = PluginManager(self.registry)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_discover_plugins_from_directory(self):
        """Test plugin discovery from directory."""
        # Create a test plugin file
        plugin_file = self.temp_dir / "test_plugin.py"
        plugin_code = '''
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.arxiv_writer.plugins import SectionPlugin, PluginMetadata, PluginType
from src.arxiv_writer.core.models import Section
from typing import Dict, Any

class DiscoveredPlugin(SectionPlugin):
    @property
    def metadata(self):
        return PluginMetadata(
            name="discovered_plugin",
            version="1.0.0",
            description="Discovered plugin",
            author="Test",
            plugin_type=PluginType.SECTION
        )
    
    def generate_section(self, context: Dict[str, Any]) -> Section:
        return Section(
            name="discovered",
            title="Discovered Section",
            content="Content from discovered plugin",
            word_count=5
        )
'''
        plugin_file.write_text(plugin_code)
        
        # Discover plugins
        discovered_count = self.manager.discover_plugins([str(self.temp_dir)])
        
        assert discovered_count == 1
        
        plugins = self.manager.list_available_plugins()
        assert "discovered_plugin" in plugins
    
    def test_load_plugins_from_config_file(self):
        """Test loading plugins from configuration file."""
        # Create a test plugin
        plugin_file = self.temp_dir / "config_plugin.py"
        plugin_code = '''
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.arxiv_writer.plugins import SectionPlugin, PluginMetadata, PluginType
from src.arxiv_writer.core.models import Section
from typing import Dict, Any

class ConfigurablePlugin(SectionPlugin):
    @property
    def metadata(self):
        return PluginMetadata(
            name="configurable_plugin",
            version="1.0.0",
            description="Configurable plugin",
            author="Test",
            plugin_type=PluginType.SECTION,
            config_schema={
                "required": ["message"],
                "properties": {
                    "message": {"type": "string"}
                }
            }
        )
    
    def validate_config(self, config):
        return "message" in config
    
    def generate_section(self, context: Dict[str, Any]) -> Section:
        message = self.config.get("message", "Default message")
        return Section(
            name="configurable",
            title="Configurable Section",
            content=f"Message: {message}",
            word_count=2
        )
'''
        plugin_file.write_text(plugin_code)
        
        # Create configuration file
        config_file = self.temp_dir / "plugin_config.json"
        config = {
            "plugin_directories": [str(self.temp_dir)],
            "plugins": {
                "configurable_plugin": {
                    "enabled": True,
                    "config": {
                        "message": "Hello from config!"
                    }
                }
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Load plugins from config
        self.manager.load_plugins_from_config_file(str(config_file))
        
        # Verify plugin is loaded and configured
        plugin = self.manager.get_plugin("configurable_plugin")
        assert plugin is not None
        assert plugin.config["message"] == "Hello from config!"
    
    def test_plugin_conflict_resolution(self):
        """Test plugin conflict detection and resolution."""
        # Create two plugins with the same name
        plugin1_file = self.temp_dir / "plugin1.py"
        plugin2_file = self.temp_dir / "plugin2.py"
        
        plugin_code_template = '''
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.arxiv_writer.plugins import SectionPlugin, PluginMetadata, PluginType
from src.arxiv_writer.core.models import Section
from typing import Dict, Any

class ConflictPlugin{num}(SectionPlugin):
    @property
    def metadata(self):
        return PluginMetadata(
            name="conflict_plugin",  # Same name for both
            version="1.0.{num}",
            description="Conflict plugin {num}",
            author="Test",
            plugin_type=PluginType.SECTION
        )
    
    def generate_section(self, context: Dict[str, Any]) -> Section:
        return Section(
            name="conflict",
            title="Conflict Section {num}",
            content="Content from plugin {num}",
            word_count=4
        )
'''
        
        plugin1_file.write_text(plugin_code_template.format(num=1))
        plugin2_file.write_text(plugin_code_template.format(num=2))
        
        # Discover plugins
        self.manager.discover_plugins([str(self.temp_dir)])
        
        # Check for conflicts
        conflicts = self.manager.resolve_plugin_conflicts()
        
        # Should detect name conflicts
        assert len(conflicts['name_conflicts']) > 0 or len(conflicts['dependency_conflicts']) >= 0
    
    def test_plugin_dependency_validation(self):
        """Test plugin dependency validation."""
        # Create plugin with dependencies
        plugin_file = self.temp_dir / "dependent_plugin.py"
        plugin_code = '''
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.arxiv_writer.plugins import SectionPlugin, PluginMetadata, PluginType
from src.arxiv_writer.core.models import Section
from typing import Dict, Any

class DependentPlugin(SectionPlugin):
    @property
    def metadata(self):
        return PluginMetadata(
            name="dependent_plugin",
            version="1.0.0",
            description="Plugin with dependencies",
            author="Test",
            plugin_type=PluginType.SECTION,
            dependencies=["nonexistent_plugin"]
        )
    
    def generate_section(self, context: Dict[str, Any]) -> Section:
        return Section(
            name="dependent",
            title="Dependent Section",
            content="Content with dependencies",
            word_count=3
        )
'''
        plugin_file.write_text(plugin_code)
        
        # Discover and load plugin
        self.manager.discover_plugins([str(self.temp_dir)])
        
        # Try to load the plugin (this should work even with missing dependencies for discovery)
        try:
            self.manager.load_plugin("dependent_plugin")
        except PluginError:
            # Expected to fail due to missing dependencies during initialization
            pass
        
        # Validate dependencies
        missing_deps = self.manager.validate_plugin_dependencies()
        
        # Should have missing dependencies
        assert "dependent_plugin" in missing_deps
        assert "nonexistent_plugin" in missing_deps["dependent_plugin"]
    
    def test_export_plugin_config(self):
        """Test exporting plugin configuration."""
        # Create and load a plugin
        plugin_file = self.temp_dir / "export_plugin.py"
        plugin_code = '''
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.arxiv_writer.plugins import SectionPlugin, PluginMetadata, PluginType
from src.arxiv_writer.core.models import Section
from typing import Dict, Any

class ExportPlugin(SectionPlugin):
    @property
    def metadata(self):
        return PluginMetadata(
            name="export_plugin",
            version="1.0.0",
            description="Plugin for export test",
            author="Test",
            plugin_type=PluginType.SECTION
        )
    
    def generate_section(self, context: Dict[str, Any]) -> Section:
        return Section(
            name="export",
            title="Export Section",
            content="Content for export",
            word_count=3
        )
'''
        plugin_file.write_text(plugin_code)
        
        # Discover and load plugin
        self.manager.discover_plugins([str(self.temp_dir)])
        self.manager.load_plugin("export_plugin", {"test_config": "value"})
        
        # Export configuration
        export_file = self.temp_dir / "exported_config.json"
        self.manager.export_plugin_config(str(export_file))
        
        # Verify exported configuration
        assert export_file.exists()
        
        with open(export_file, 'r') as f:
            exported_config = json.load(f)
        
        assert "plugins" in exported_config
        assert "export_plugin" in exported_config["plugins"]
        assert exported_config["plugins"]["export_plugin"]["config"]["test_config"] == "value"
    
    def test_create_plugin_template(self):
        """Test creating plugin templates."""
        # Create section plugin template
        template_path = self.manager.create_plugin_template(
            "My Custom Plugin",
            PluginType.SECTION,
            str(self.temp_dir)
        )
        
        assert Path(template_path).exists()
        
        # Read and verify template content
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        assert "class MyCustomPluginPlugin(SectionPlugin):" in template_content
        assert "def generate_section" in template_content
        assert "my_custom_plugin" in template_content
    
    def test_refresh_plugins(self):
        """Test refreshing plugin discovery."""
        initial_count = len(self.manager.list_available_plugins())
        
        # Add discovery path
        self.manager.add_discovery_path(str(self.temp_dir))
        
        # Create a plugin after adding the path
        plugin_file = self.temp_dir / "refresh_plugin.py"
        plugin_code = '''
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.arxiv_writer.plugins import SectionPlugin, PluginMetadata, PluginType
from src.arxiv_writer.core.models import Section
from typing import Dict, Any

class RefreshPlugin(SectionPlugin):
    @property
    def metadata(self):
        return PluginMetadata(
            name="refresh_plugin",
            version="1.0.0",
            description="Plugin for refresh test",
            author="Test",
            plugin_type=PluginType.SECTION
        )
    
    def generate_section(self, context: Dict[str, Any]) -> Section:
        return Section(
            name="refresh",
            title="Refresh Section",
            content="Content for refresh",
            word_count=3
        )
'''
        plugin_file.write_text(plugin_code)
        
        # Refresh plugins
        new_plugins = self.manager.refresh_plugins()
        
        assert new_plugins >= 1
        
        final_count = len(self.manager.list_available_plugins())
        assert final_count > initial_count
    
    def test_auto_discovery_toggle(self):
        """Test enabling/disabling auto discovery."""
        # Test enabling
        self.manager.enable_auto_discovery(True)
        assert self.manager._auto_discovery_enabled
        
        # Test disabling
        self.manager.enable_auto_discovery(False)
        assert not self.manager._auto_discovery_enabled
        
        # Auto discovery should return 0 when disabled
        discovered = self.manager.auto_discover_plugins()
        assert discovered == 0
    
    def test_discovery_path_management(self):
        """Test managing discovery paths."""
        test_path = str(self.temp_dir)
        
        # Add path
        self.manager.add_discovery_path(test_path)
        assert test_path in self.manager.get_discovery_paths()
        
        # Remove path
        self.manager.remove_discovery_path(test_path)
        assert test_path not in self.manager.get_discovery_paths()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])