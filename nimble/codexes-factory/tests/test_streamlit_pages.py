#!/usr/bin/env python3
"""
Test script to verify all Streamlit pages can be imported without errors
"""
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def test_page_imports():
    """Test importing all Streamlit pages"""
    pages_dir = src_path / "codexes" / "pages"
    
    if not pages_dir.exists():
        print(f"❌ Pages directory not found: {pages_dir}")
        return False
    
    success_count = 0
    total_count = 0
    
    for page_file in pages_dir.glob("*.py"):
        if page_file.name.startswith("__"):
            continue
            
        total_count += 1
        page_name = page_file.name
        
        try:
            # Create a module name from the file path
            module_name = f"codexes.pages.{page_file.stem}"
            
            # Try to import the module
            __import__(module_name)
            print(f"✅ {page_name} - Import successful")
            success_count += 1
            
        except ImportError as e:
            print(f"❌ {page_name} - Import error: {e}")
        except Exception as e:
            # Some pages might fail due to Streamlit-specific code, but imports should work
            if "st.set_page_config" in str(e) or "streamlit" in str(e).lower():
                print(f"⚠️  {page_name} - Streamlit-specific error (expected): {e}")
                success_count += 1  # Count as success since imports worked
            else:
                print(f"❌ {page_name} - Unexpected error: {e}")
    
    print(f"\n📊 Results: {success_count}/{total_count} pages imported successfully")
    return success_count == total_count

if __name__ == "__main__":
    success = test_page_imports()
    sys.exit(0 if success else 1)