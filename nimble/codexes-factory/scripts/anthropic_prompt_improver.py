#!/usr/bin/env python3
"""
Anthropic Prompt Improver

Uses Claude API to improve prompts using Anthropic's prompt engineering guidelines.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.core.llm_caller import call_model_with_prompt


def improve_prompt(original_prompt: str, context: str = "") -> dict:
    """Improve a prompt using Anthropic's prompt improvement methodology."""
    
    improvement_prompt = {
        "messages": [
            {
                "role": "user",
                "content": f"""You are an expert prompt engineer. Improve the following prompt using Anthropic's best practices:

ORIGINAL PROMPT:
{original_prompt}

CONTEXT (if provided):
{context}

Please improve this prompt by:
1. Making it more specific and clear
2. Adding relevant examples if helpful  
3. Structuring it better with clear sections
4. Removing ambiguity
5. Adding appropriate constraints or formatting instructions
6. Following Anthropic's prompt engineering guidelines

Return your response in JSON format:
{{
  "improved_prompt": "The enhanced version of the prompt",
  "key_improvements": [
    "List of specific improvements made"
  ],
  "reasoning": "Explanation of why these changes improve the prompt",
  "usage_tips": "Tips for using this improved prompt effectively"
}}"""
            }
        ]
    }
    
    try:
        response = call_model_with_prompt(
            model_name="anthropic/claude-3-5-sonnet-20241022",
            prompt_config=improvement_prompt,
            response_format_type="json_object",
            prompt_name="anthropic_prompt_improvement"
        )
        
        if response.get("parsed_content"):
            return response["parsed_content"]
        else:
            return {"error": "No response content received"}
            
    except Exception as e:
        return {"error": f"Error calling Claude API: {e}"}


def main():
    """Main CLI interface for prompt improvement."""
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python anthropic_prompt_improver.py 'Your prompt here'")
        print("  python anthropic_prompt_improver.py 'Your prompt here' 'Optional context'")
        print("  python anthropic_prompt_improver.py --file prompt.txt")
        return
    
    if sys.argv[1] == "--file" and len(sys.argv) > 2:
        # Read from file
        prompt_file = Path(sys.argv[2])
        if not prompt_file.exists():
            print(f"❌ File not found: {prompt_file}")
            return
        
        original_prompt = prompt_file.read_text()
        context = f"Prompt loaded from file: {prompt_file}"
        
    else:
        # Read from command line
        original_prompt = sys.argv[1]
        context = sys.argv[2] if len(sys.argv) > 2 else ""
    
    print("🔄 Improving prompt using Anthropic's Claude API...")
    print(f"📝 Original prompt length: {len(original_prompt)} characters")
    print()
    
    result = improve_prompt(original_prompt, context)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print("✅ Prompt improvement completed!")
    print()
    print("🎯 IMPROVED PROMPT:")
    print("=" * 60)
    print(result.get("improved_prompt", "No improved prompt provided"))
    print("=" * 60)
    print()
    
    print("🔧 KEY IMPROVEMENTS:")
    for improvement in result.get("key_improvements", []):
        print(f"  • {improvement}")
    print()
    
    print("💡 REASONING:")
    print(result.get("reasoning", "No reasoning provided"))
    print()
    
    print("📋 USAGE TIPS:")
    print(result.get("usage_tips", "No usage tips provided"))
    
    # Optionally save to file
    output_file = Path("improved_prompt.json")
    with open(output_file, 'w') as f:
        json.dump({
            "original_prompt": original_prompt,
            "improved_prompt": result.get("improved_prompt"),
            "improvements": result,
            "timestamp": str(datetime.now())
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    from datetime import datetime
    main()