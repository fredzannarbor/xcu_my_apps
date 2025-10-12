#!/usr/bin/env python3
"""
Test script to verify the dropdown manager fix for publisher -> imprint mapping
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codexes.modules.ui.dropdown_manager import DropdownManager

def test_dropdown_fix():
    """Test that the dropdown manager can now find imprints for nimble_books"""
    
    print("🧪 Testing Dropdown Manager Fix")
    print("=" * 50)
    
    # Create dropdown manager
    manager = DropdownManager()
    
    # Test publisher -> imprint mapping
    publisher = "nimble_books"
    print(f"📋 Testing publisher: {publisher}")
    
    # Get publisher name
    publisher_name = manager._get_publisher_name(publisher)
    print(f"📝 Publisher name from config: {publisher_name}")
    
    # Get imprints
    imprints = manager.get_imprints_for_publisher(publisher)
    print(f"🏢 Found imprints: {imprints}")
    
    # Test specific imprint
    if "xynapse_traces" in imprints:
        print("✅ SUCCESS: xynapse_traces found for nimble_books")
        
        # Test tranche lookup
        tranches = manager.get_tranches_for_imprint("xynapse_traces")
        print(f"📦 Found tranches for xynapse_traces: {tranches}")
        
        return True
    else:
        print("❌ FAILED: xynapse_traces not found for nimble_books")
        return False

if __name__ == "__main__":
    success = test_dropdown_fix()
    if success:
        print("\n🎉 Dropdown fix test PASSED!")
        sys.exit(0)
    else:
        print("\n💥 Dropdown fix test FAILED!")
        sys.exit(1)