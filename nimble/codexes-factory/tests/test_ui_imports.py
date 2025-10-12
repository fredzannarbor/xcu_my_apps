#!/usr/bin/env python3
"""
Test script to verify UI component imports work correctly
"""
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def test_imports():
    """Test all UI component imports"""
    try:
        print("Testing UI component imports...")
        
        from codexes.modules.ui.streamlit_components import ConfigurationUI
        print("✅ ConfigurationUI import successful")
        
        from codexes.modules.ui.command_builder import CommandBuilder
        print("✅ CommandBuilder import successful")
        
        from codexes.modules.ui.parameter_groups import ParameterGroupManager
        print("✅ ParameterGroupManager import successful")
        
        from codexes.modules.ui.configuration_manager import EnhancedConfigurationManager
        print("✅ EnhancedConfigurationManager import successful")
        
        from codexes.modules.ui.config_validator import ConfigurationValidator
        print("✅ ConfigurationValidator import successful")
        
        from codexes.modules.ui.dynamic_config_loader import DynamicConfigurationLoader
        print("✅ DynamicConfigurationLoader import successful")
        
        print("\n🎉 All UI component imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)