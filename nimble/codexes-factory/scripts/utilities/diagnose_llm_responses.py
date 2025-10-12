#!/usr/bin/env python3

"""
LLM Response Diagnostic Tool

This tool helps diagnose why LLM calls are returning empty results by:
1. Testing individual prompts with sample data
2. Showing the actual prompts being sent
3. Displaying raw LLM responses
4. Identifying potential issues
"""

import os
import sys
import json
import logging
from pathlib import Path

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

def diagnose_llm_responses():
    """Diagnose LLM response issues."""
    logger.info("🔍 Starting LLM Response Diagnosis")
    
    try:
        from codexes.modules.distribution.enhanced_llm_field_completer import EnhancedLLMFieldCompleter
        from codexes.modules.metadata.metadata_models import CodexMetadata
        from codexes.core.llm_integration import LLMCaller
        
        # Create test metadata (similar to what might be causing issues)
        test_metadata = CodexMetadata(
            title="Advanced Machine Learning: Theory and Practice",
            author="Dr. Sarah Johnson",
            isbn13="9781234567890",
            summary_long="A comprehensive guide to machine learning algorithms, covering both theoretical foundations and practical implementations. This book includes detailed explanations of neural networks, deep learning, and modern AI techniques.",
            page_count=450,
            binding="paperback",
            trim_size="7x10"
        )
        
        # Initialize LLM components
        llm_caller = LLMCaller()
        field_completer = EnhancedLLMFieldCompleter(
            llm_caller=llm_caller,
            model_name="gemini/gemini-2.5-flash"
        )
        
        # Test the specific prompt that's failing
        logger.info("🧪 Testing illustration_info prompt")
        
        # Get the prompt template
        prompts = field_completer.prompts
        if "generate_illustration_info" in prompts:
            prompt_template = prompts["generate_illustration_info"]
            logger.info(f"📝 Prompt template found: {prompt_template['description']}")
            
            # Generate the actual prompt
            try:
                actual_prompt = field_completer._generate_prompt("generate_illustration_info", test_metadata)
                logger.info("📄 Generated prompt:")
                logger.info("-" * 50)
                logger.info(actual_prompt)
                logger.info("-" * 50)
                
                # Make the LLM call directly to see raw response
                logger.info("🤖 Making direct LLM call...")
                raw_response = llm_caller.call_model_with_prompt(
                    prompt=actual_prompt,
                    model_name="gemini/gemini-2.5-flash"
                )
                
                logger.info("📥 Raw LLM response:")
                logger.info("-" * 50)
                logger.info(f"Response type: {type(raw_response)}")
                logger.info(f"Response content: {repr(raw_response)}")
                logger.info("-" * 50)
                
                # Test the processing
                processed_result = field_completer._process_prompt("generate_illustration_info", test_metadata)
                logger.info(f"🔄 Processed result: {repr(processed_result)}")
                
            except Exception as e:
                logger.error(f"❌ Error testing prompt: {e}")
                import traceback
                traceback.print_exc()
        else:
            logger.error("❌ Prompt 'generate_illustration_info' not found in prompts")
            logger.info(f"Available prompts: {list(prompts.keys())}")
        
        # Test other potentially problematic prompts
        problematic_prompts = [
            "generate_bisac_categories",
            "generate_contributor_bio", 
            "generate_thema_subjects",
            "generate_age_range"
        ]
        
        for prompt_name in problematic_prompts:
            if prompt_name in prompts:
                logger.info(f"\n🧪 Testing {prompt_name}")
                try:
                    result = field_completer._process_prompt(prompt_name, test_metadata)
                    logger.info(f"✅ {prompt_name}: {repr(result)}")
                except Exception as e:
                    logger.error(f"❌ {prompt_name} failed: {e}")
        
        # Test with different metadata to see if content affects results
        logger.info("\n🧪 Testing with minimal metadata")
        minimal_metadata = CodexMetadata(
            title="Simple Book",
            author="Author Name"
        )
        
        try:
            result = field_completer._process_prompt("generate_illustration_info", minimal_metadata)
            logger.info(f"📊 Minimal metadata result: {repr(result)}")
        except Exception as e:
            logger.error(f"❌ Minimal metadata test failed: {e}")
        
        # Test with rich metadata
        logger.info("\n🧪 Testing with rich metadata")
        rich_metadata = CodexMetadata(
            title="The Visual Guide to Data Science: Charts, Graphs, and Infographics",
            author="Dr. Maria Rodriguez",
            isbn13="9781234567890",
            summary_long="This comprehensive guide contains over 200 illustrations, including charts, graphs, diagrams, and infographics. Each chapter features detailed visual examples and step-by-step illustrations to help readers understand complex data science concepts.",
            page_count=350,
            binding="paperback",
            trim_size="8.5x11",
            keywords="data science, visualization, charts, graphs, illustrations, infographics"
        )
        
        try:
            result = field_completer._process_prompt("generate_illustration_info", rich_metadata)
            logger.info(f"📊 Rich metadata result: {repr(result)}")
        except Exception as e:
            logger.error(f"❌ Rich metadata test failed: {e}")
            
    except Exception as e:
        logger.error(f"❌ Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()

def analyze_prompt_effectiveness():
    """Analyze which prompts are most/least effective."""
    logger.info("\n📈 Analyzing prompt effectiveness")
    
    try:
        from codexes.modules.distribution.enhanced_llm_field_completer import EnhancedLLMFieldCompleter
        from codexes.modules.metadata.metadata_models import CodexMetadata
        from codexes.core.llm_integration import LLMCaller
        
        # Test metadata
        test_metadata = CodexMetadata(
            title="Python Programming for Beginners",
            author="John Smith",
            isbn13="9781234567890",
            summary_long="A beginner-friendly introduction to Python programming with practical examples and exercises.",
            page_count=300
        )
        
        llm_caller = LLMCaller()
        field_completer = EnhancedLLMFieldCompleter(
            llm_caller=llm_caller,
            model_name="gemini/gemini-2.5-flash"
        )
        
        # Test all prompts
        results = {}
        for prompt_name in field_completer.prompts.keys():
            logger.info(f"Testing {prompt_name}...")
            try:
                result = field_completer._process_prompt(prompt_name, test_metadata)
                success = bool(result and str(result).strip())
                results[prompt_name] = {
                    "success": success,
                    "result": str(result)[:100] + "..." if len(str(result)) > 100 else str(result),
                    "length": len(str(result)) if result else 0
                }
                status = "✅" if success else "❌"
                logger.info(f"{status} {prompt_name}: {success}")
            except Exception as e:
                results[prompt_name] = {
                    "success": False,
                    "error": str(e),
                    "length": 0
                }
                logger.error(f"❌ {prompt_name}: ERROR - {e}")
        
        # Summary
        successful = sum(1 for r in results.values() if r["success"])
        total = len(results)
        logger.info(f"\n📊 Summary: {successful}/{total} prompts successful ({successful/total*100:.1f}%)")
        
        # Show failed prompts
        failed_prompts = [name for name, result in results.items() if not result["success"]]
        if failed_prompts:
            logger.info(f"❌ Failed prompts: {failed_prompts}")
        
        # Save detailed results
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        with open(f"{output_dir}/prompt_analysis.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"📄 Detailed results saved to {output_dir}/prompt_analysis.json")
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_llm_responses()
    analyze_prompt_effectiveness()