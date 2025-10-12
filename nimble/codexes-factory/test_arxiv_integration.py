#!/usr/bin/env python3
"""
Test script for the fixed arxiv-writer integration.

This script tests the fixed bridge module and integration with the
arxiv-writer package to ensure proper API usage.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_bridge_import():
    """Test importing the fixed arxiv bridge module."""
    try:
        from codexes.modules.arxiv_bridge import (
            generate_arxiv_paper,
            create_paper_generation_config,
            ARXIV_WRITER_AVAILABLE
        )
        print("✅ Successfully imported arxiv_bridge module")
        print(f"   ArXiv-writer available: {ARXIV_WRITER_AVAILABLE}")
        return True, generate_arxiv_paper, create_paper_generation_config
    except Exception as e:
        print(f"❌ Failed to import arxiv_bridge: {e}")
        return False, None, None

def test_paper_generation():
    """Test paper generation with the fixed integration."""
    success, generate_fn, config_fn = test_bridge_import()
    if not success:
        return False

    try:
        # Create test context data
        context_data = {
            "imprint_name": "Xynapse Traces",
            "specialization": "Cutting-edge research and emerging technologies",
            "focus_areas": [
                "AI-assisted imprint development",
                "Technology-focused publishing",
                "Emerging technology documentation"
            ],
            "configuration_complexity": {
                "complexity_level": "high",
                "complexity_score": 185,
                "total_config_sections": 28,
                "has_workflow_automation": True
            }
        }

        print("🔄 Testing paper generation with fixed integration...")
        result = generate_fn(
            context_data=context_data,
            output_dir="output/test_papers",
            working_directory=str(project_root)
        )

        if result.get("success"):
            print("✅ Paper generation succeeded!")
            print(f"   Method: {result.get('generation_method')}")
            print(f"   Output: {result.get('output_directory')}")
            return True
        else:
            print(f"❌ Paper generation failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Exception during paper generation: {e}")
        return False

def test_academic_paper_integration():
    """Test the full academic paper integration."""
    try:
        from codexes.modules.imprints.academic_paper_integration import generate_paper_for_new_imprint
        print("✅ Successfully imported academic_paper_integration")

        print("🔄 Testing full integration with xynapse_traces...")
        result = generate_paper_for_new_imprint('xynapse_traces')

        if result and result.get('success'):
            print("✅ Full integration test succeeded!")
            print(f"   Imprint: {result.get('imprint_name')}")
            print(f"   Output: {result.get('output_directory')}")
            return True
        else:
            print(f"❌ Full integration test failed: {result.get('error') if result else 'No result'}")
            return False

    except Exception as e:
        print(f"❌ Exception during full integration test: {e}")
        return False

def main():
    """Run all integration tests."""
    print("🚀 Testing Fixed ArXiv-Writer Integration")
    print("=" * 50)

    # Test 1: Bridge module import
    print("\n1. Testing bridge module import...")
    bridge_success, _, _ = test_bridge_import()

    # Test 2: Direct paper generation
    print("\n2. Testing direct paper generation...")
    generation_success = test_paper_generation()

    # Test 3: Full academic paper integration
    print("\n3. Testing full academic paper integration...")
    integration_success = test_academic_paper_integration()

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print(f"   Bridge Import: {'✅ PASS' if bridge_success else '❌ FAIL'}")
    print(f"   Paper Generation: {'✅ PASS' if generation_success else '❌ FAIL'}")
    print(f"   Full Integration: {'✅ PASS' if integration_success else '❌ FAIL'}")

    if all([bridge_success, generation_success, integration_success]):
        print("\n🎉 All tests passed! Integration is working correctly.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)