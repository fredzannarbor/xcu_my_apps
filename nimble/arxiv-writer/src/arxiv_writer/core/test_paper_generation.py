#!/usr/bin/env python3
"""
Test script for ArXiv paper generation system.

This script tests the paper generation functionality with a minimal
configuration to ensure the system is working correctly.
"""

import logging
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Also add the current directory for relative imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    # Try absolute import first
    from src.codexes.modules.arxiv_paper.paper_generator import (
        ContextDataCollector,
        PaperSectionGenerator,
        create_paper_generation_config
    )
except ImportError:
    try:
        # Try relative import
        from paper_generator import (
            ContextDataCollector,
            PaperSectionGenerator,
            create_paper_generation_config
        )
    except ImportError as e:
        print(f"Import error: {e}")
        print(f"Project root: {project_root}")
        print(f"Current working directory: {Path.cwd()}")
        print("Please run from project root or ensure PYTHONPATH is set correctly")
        sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_context_data_collection():
    """Test context data collection functionality."""
    logger.info("Testing context data collection...")
    
    try:
        collector = ContextDataCollector()
        context_data = collector.collect_xynapse_traces_data()
        
        # Check if key data was collected
        required_keys = ["total_books", "imprint_config_summary", "key_technologies"]
        missing_keys = [key for key in required_keys if key not in context_data]
        
        if missing_keys:
            logger.warning(f"Missing context keys: {missing_keys}")
        else:
            logger.info("✅ Context data collection successful")
        
        # Print summary
        print(f"\n📊 Context Data Summary:")
        print(f"Total books: {context_data.get('total_books', 'N/A')}")
        print(f"Publication range: {context_data.get('publication_date_range', 'N/A')}")
        print(f"Key technologies: {len(context_data.get('key_technologies', []))}")
        
        return context_data
        
    except Exception as e:
        logger.error(f"Context data collection failed: {e}")
        return None


def test_prompt_template_loading():
    """Test prompt template loading."""
    logger.info("Testing prompt template loading...")
    
    try:
        try:
            from src.codexes.modules.arxiv_paper.paper_generator import ArxivPaperGenerator
        except ImportError:
            from paper_generator import ArxivPaperGenerator
        
        config = create_paper_generation_config()
        generator = ArxivPaperGenerator(config)
        
        # Check if templates were loaded
        templates = generator.prompt_templates
        
        if "paper_sections" not in templates:
            logger.error("No paper_sections found in templates")
            return False
        
        sections = templates["paper_sections"]
        logger.info(f"✅ Loaded {len(sections)} section templates")
        
        # Check key sections
        key_sections = ["abstract", "introduction", "methodology"]
        missing_sections = [section for section in key_sections if section not in sections]
        
        if missing_sections:
            logger.warning(f"Missing key sections: {missing_sections}")
        else:
            logger.info("✅ All key sections present")
        
        return True
        
    except Exception as e:
        logger.error(f"Prompt template loading failed: {e}")
        return False


def test_section_generation():
    """Test individual section generation."""
    logger.info("Testing section generation...")
    
    try:
        # Load templates and context
        try:
            from src.codexes.modules.arxiv_paper.paper_generator import ArxivPaperGenerator
        except ImportError:
            from paper_generator import ArxivPaperGenerator
        
        config = create_paper_generation_config()
        generator = ArxivPaperGenerator(config)
        
        # Collect context data
        context_data = generator.context_collector.collect_xynapse_traces_data()
        
        # Initialize section generator
        section_generator = PaperSectionGenerator(generator.prompt_templates, context_data)
        
        # Test generating abstract (shortest section)
        logger.info("Generating test abstract section...")
        
        # Use a simple model for testing (you may need to adjust this)
        test_model = "anthropic/claude-3-5-sonnet-20241022"
        
        abstract_section = section_generator.generate_section("abstract", model=test_model)
        
        if abstract_section:
            logger.info(f"✅ Abstract generation successful")
            print(f"\n📝 Generated Abstract ({abstract_section.word_count} words):")
            print(f"{'='*60}")
            print(abstract_section.content[:300] + "..." if len(abstract_section.content) > 300 else abstract_section.content)
            print(f"{'='*60}")
            
            return True
        else:
            logger.error("❌ Abstract generation failed")
            return False
            
    except Exception as e:
        logger.error(f"Section generation test failed: {e}")
        return False


def test_validation_system():
    """Test the validation system."""
    logger.info("Testing validation system...")
    
    try:
        try:
            from src.codexes.modules.arxiv_paper.paper_validator import ContentValidator
        except ImportError:
            from paper_validator import ContentValidator
        
        validator = ContentValidator()
        
        # Test with sample abstract
        sample_abstract = """
        The AI Lab for Book-Lovers demonstrates the use of AI in creating a new publishing imprint 
        with a 35-title list releasing from September 2025 to December 2026. The imprint is a 
        fundamental unit of publishing business activity that encompasses branding, editorial focus, 
        and production workflows. This paper presents the first comprehensive case study of fully 
        AI-assisted imprint creation, documenting the technical implementation within the 
        Codexes-Factory platform. Our approach leverages multi-level configuration inheritance, 
        LLM orchestration for content generation, and automated production pipelines to achieve 
        unprecedented efficiency in publishing workflows. The system demonstrates 87.5% efficiency 
        improvement over traditional methods while maintaining quality standards. Results show 
        successful production of 35 books with consistent metadata, automated LSI integration, 
        and Korean language processing capabilities. This work contributes to the intersection 
        of AI and digital humanities, providing a replicable framework for AI-assisted publishing 
        automation. The implications extend beyond publishing to any domain requiring systematic 
        content creation and workflow automation.
        """
        
        result = validator.validate_abstract(sample_abstract)
        
        logger.info(f"✅ Validation system working")
        print(f"\n🔍 Validation Results:")
        print(f"Score: {result.score:.2f}")
        print(f"Valid: {result.is_valid}")
        print(f"Issues: {len(result.issues)}")
        print(f"Suggestions: {len(result.suggestions)}")
        
        if result.issues:
            print("Issues found:")
            for issue in result.issues:
                print(f"  - {issue}")
        
        return True
        
    except Exception as e:
        logger.error(f"Validation system test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 ArXiv Paper Generation System Tests")
    print("=" * 50)
    
    tests = [
        ("Context Data Collection", test_context_data_collection),
        ("Prompt Template Loading", test_prompt_template_loading),
        ("Validation System", test_validation_system),
        # Note: Section generation test requires API access, so it's optional
        # ("Section Generation", test_section_generation),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}")
        except Exception as e:
            results[test_name] = False
            print(f"   ❌ ERROR: {e}")
    
    # Summary
    print(f"\n📊 Test Summary:")
    print("=" * 30)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for paper generation.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())