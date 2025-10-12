"""
Test script to verify Streamlit imports work correctly
"""

import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from codexes.ui.components.universal_input import UniversalContentInput
    from codexes.ui.config.model_config import ModelConfigManager
    print("✅ Streamlit imports successful!")
    
    # Test basic functionality
    input_component = UniversalContentInput()
    model_config = ModelConfigManager()
    
    print("✅ Components initialized successfully!")
    print(f"✅ Model config has {len(model_config.get_available_models())} models")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()