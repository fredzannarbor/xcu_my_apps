#!/usr/bin/env python3
"""
Test integrating native Google API directly for Gemini 2.5 Pro
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path for proper imports
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_native_gemini_with_safety_settings():
    """Test native Google API with safety settings disabled."""
    print("🔬 Testing native Gemini 2.5 Pro with safety settings...")

    try:
        import google.generativeai as genai

        # Configure with API key
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("❌ No API key found in environment")
            return

        genai.configure(api_key=api_key)

        # Configure safety settings
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
            },
        ]

        # Test with safety settings
        model = genai.GenerativeModel('gemini-2.5-pro')

        print("📝 Testing with safety settings disabled...")
        response = model.generate_content(
            "Write a short social media post about your favorite sport. Keep it under 200 characters and make it engaging.",
            safety_settings=safety_settings
        )

        print(f"✅ SUCCESS: '{response.text}'")
        print(f"📊 Content length: {len(response.text)} characters")

        # Test with complex prompt (similar to our feed generation)
        print("\n📝 Testing with complex literary prompt...")
        complex_prompt = """You are Phedre, an AI persona specializing in classic literature and AI analysis.

Write a social media post that connects classical literature to modern AI development.
Make it insightful, engaging, and include a literary reference.
Return ONLY this JSON format:

{
    "content": "Your social media post text here",
    "engagement_hooks": ["what makes this relatable"],
    "breakthrough_triggers": ["the surprising insight"],
    "learning_nuggets": ["educational element"],
    "book_references": [{"title": "Book Title", "author": "Author", "context": "why relevant"}],
    "hashtags": ["relevant", "tags"],
    "learning_score": 0.8,
    "breakthrough_potential": 0.9,
    "mood_elevation_score": 0.7
}"""

        response = model.generate_content(
            complex_prompt,
            safety_settings=safety_settings
        )

        print(f"✅ Complex prompt SUCCESS!")
        print(f"📝 Response: {response.text[:500]}...")

        return True

    except Exception as e:
        print(f"❌ Native Google API test failed: {e}")
        return False

def main():
    print("🚀 Testing native Google Gemini 2.5 Pro integration...")

    success = test_native_gemini_with_safety_settings()

    if success:
        print("\n🎉 SOLUTION FOUND!")
        print("✅ Native Google API works perfectly with Gemini 2.5 Pro")
        print("✅ Safety settings can be disabled (BLOCK_NONE)")
        print("✅ Complex prompts work correctly")
        print("💡 We can integrate native Google API for Gemini models!")
    else:
        print("\n❌ Native integration test failed")

if __name__ == "__main__":
    main()