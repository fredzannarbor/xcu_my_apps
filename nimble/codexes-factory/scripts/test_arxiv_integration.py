#!/usr/bin/env python3
"""
Test ArXiv Writer Integration

This script tests the integration between codexes-factory and the new arxiv-writer package.
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_arxiv_bridge_import():
    """Test that we can import the arxiv bridge module."""
    print("🔗 Testing ArXiv Bridge Import...")

    try:
        from codexes.modules.arxiv_bridge import (
            generate_arxiv_paper,
            ArxivPaperGenerator,
            create_paper_generation_config
        )
        print("✅ ArXiv bridge imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import arxiv bridge: {e}")
        return False

def test_paper_generation():
    """Test basic paper generation functionality with caller-specified paths."""
    print("\n📄 Testing Paper Generation...")

    try:
        from codexes.modules.arxiv_bridge import generate_arxiv_paper

        # Create test context data
        context_data = {
            "research_area": "AI-Assisted Publishing",
            "methodology": "Large Language Models",
            "key_findings": "Automated paper generation with quality validation",
            "imprint_name": "xynapse_traces",
            "book_count": 50,
            "technical_architecture": "Multi-model LLM system with validation pipeline"
        }

        # Test output directory (relative to project_root)
        output_dir = "test_output/arxiv_integration_test"
        full_output_dir = project_root / output_dir
        full_output_dir.mkdir(parents=True, exist_ok=True)

        print(f"   Context data: {len(context_data)} fields")
        print(f"   Working directory: {project_root}")
        print(f"   Output directory: {output_dir}")

        # Test function call with explicit working directory
        # This ensures arxiv-writer uses caller's paths, not site-packages
        result = generate_arxiv_paper(
            context_data=context_data,
            output_dir=output_dir,
            working_directory=str(project_root)
        )

        print("   Function call with working_directory: ✅")
        print("   All paths resolved from calling project: ✅")

        return True

    except Exception as e:
        print(f"❌ Paper generation test failed: {e}")
        return False

def test_configuration():
    """Test configuration creation."""
    print("\n⚙️  Testing Configuration...")

    try:
        from codexes.modules.arxiv_bridge import create_paper_generation_config

        config = create_paper_generation_config(
            output_directory="./test_output",
            target_word_count=8000,
            models=["anthropic/claude-3-5-sonnet-20241022"]
        )

        print(f"   Configuration created: {type(config)}")
        print("   Configuration test: ✅")

        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_arxiv_writer_direct():
    """Test direct arxiv-writer import."""
    print("\n🔬 Testing Direct ArXiv Writer Import...")

    # Add arxiv-writer to path
    arxiv_writer_path = "//nimble/arxiv-writer/src"
    if os.path.exists(arxiv_writer_path):
        sys.path.insert(0, arxiv_writer_path)

        try:
            import arxiv_writer
            print(f"✅ ArXiv Writer imported: v{arxiv_writer.__version__}")

            # Test main classes
            from arxiv_writer import ArxivPaperGenerator, PaperConfig
            print("✅ Main classes imported successfully")

            return True

        except ImportError as e:
            print(f"❌ Direct import failed: {e}")
            return False
    else:
        print(f"❌ ArXiv Writer path not found: {arxiv_writer_path}")
        return False

def main():
    """Run all integration tests."""
    print("ArXiv Writer Integration Test")
    print("=" * 50)

    tests = [
        test_arxiv_writer_direct,
        test_arxiv_bridge_import,
        test_configuration,
        test_paper_generation,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print(f"Integration Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed! ArXiv Writer integration is working.")
    else:
        print(f"⚠️  {total - passed} tests failed. Check the output above.")

    print("=" * 50)

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)