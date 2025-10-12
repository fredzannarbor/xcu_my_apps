#!/usr/bin/env python3
"""Test small batch imprint generation"""

import json
import litellm

def test_single_category():
    prompt = """Generate 2 unique publishing imprints for BigFiveReplacement LLC focused on puzzles games category.

CONTEXT: BigFiveReplacement is a virtual publisher designed to exceed the Big Five publishers' 550+ imprints and capture the $4.5B in revenue gaps they've left.

CATEGORY FOCUS: Crosswords, sudoku, brain teasers, word games
Market size: $500M+

Each imprint should have:
- Professional, memorable name
- Clear mission/charter
- Specific publishing focus
- Catchy tagline
- Target audience
- Competitive advantage
- Example titles

Return ONLY a valid JSON array:
[
  {
    "name": "Professional Imprint Name",
    "charter": "Brief mission statement",
    "focus": "Specific publishing areas",
    "tagline": "Marketing tagline",
    "target_audience": "Primary readership",
    "competitive_advantage": "Why this imprint wins",
    "examples": "Sample book titles"
  }
]"""

    try:
        response = litellm.completion(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=1500
        )

        content = response.choices[0].message.content.strip()
        print(f"Raw response:\n{content}\n")

        # Parse JSON
        imprints = json.loads(content)
        print(f"✅ Generated {len(imprints)} imprints")

        for i, imprint in enumerate(imprints, 1):
            print(f"\n{i}. {imprint['name']}")
            print(f"   Charter: {imprint['charter']}")
            print(f"   Tagline: {imprint['tagline']}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_single_category()