#!/usr/bin/env python3
"""
Test imprint generation with a small batch
"""

import json
import logging
from nimble_llm_caller import LLMCaller, LLMRequest

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize LLM caller
llm_caller = LLMCaller()

def test_imprint_generation():
    """Test generating 3 imprints for puzzles/games category"""

    prompt = """Generate 3 publishing imprints for BigFiveReplacement LLC focused on puzzles_games category.

CONTEXT: BigFiveReplacement is a virtual "shadow" publisher designed to exceed the Big Five publishers' scale (550+ imprints) and fill the $4.5B revenue gaps they've left.

REQUIREMENTS:
1. Each imprint needs: name, charter, focus, tagline, target_audience, competitive_advantage, examples
2. Names should be professional, memorable, and category-appropriate
3. Competitive advantages should highlight market gaps or superior positioning
4. Examples should be specific book titles, authors, or series that would fit

STRATEGY FOR PUZZLES_GAMES:
- Focus on underserved profitable niches the Big Five ignore
- This is a $500M+ annual market with only Hachette (Puzzlewright Press) competing
- High margins, recurring purchases, gift market potential

OUTPUT FORMAT: Return as JSON array with this structure:
[
  {
    "name": "Imprint Name",
    "charter": "Brief mission statement",
    "focus": "Specific publishing focus areas",
    "tagline": "Marketing tagline",
    "target_audience": "Primary readership",
    "competitive_advantage": "Why this imprint wins",
    "examples": "Sample titles or authors"
  }
]

Generate exactly 3 unique, high-quality imprints that would collectively dominate the puzzles_games market."""

    try:
        request = LLMRequest(
            prompt_key="main_prompt",
            model="openai/gpt-4",
            substitutions={"main_prompt": prompt},
            model_params={"temperature": 0.8, "max_tokens": 2000}
        )

        response = llm_caller.call(request)

        print("Raw response:")
        print(response.content)
        print("\n" + "="*50 + "\n")

        # Try to parse JSON
        imprint_data = json.loads(response.content)
        print(f"✅ Successfully generated {len(imprint_data)} imprints")

        for i, imprint in enumerate(imprint_data, 1):
            print(f"\n{i}. {imprint['name']}")
            print(f"   Charter: {imprint['charter']}")
            print(f"   Focus: {imprint['focus']}")
            print(f"   Tagline: {imprint['tagline']}")
            print(f"   Audience: {imprint['target_audience']}")
            print(f"   Advantage: {imprint['competitive_advantage']}")
            print(f"   Examples: {imprint['examples']}")

        return True

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Response was: {response.content}")
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing imprint generation...")
    success = test_imprint_generation()
    print(f"\n{'✅ Test passed' if success else '❌ Test failed'}")