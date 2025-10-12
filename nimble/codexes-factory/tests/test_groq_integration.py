#!/usr/bin/env python3
"""
Test script to verify nimble-llm-caller integration works with GROQ API.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def load_environment():
    """Load environment variables from .env file."""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def test_groq_integration():
    """Test GROQ integration with real API call."""
    print("🧪 Testing GROQ Integration with Real API Call")
    print("=" * 60)
    
    try:
        from codexes.core.llm_integration import get_llm_integration
        
        integration = get_llm_integration()
        
        # Test simple call with GROQ (using llama model)
        response = integration.call_llm(
            prompt="Say 'Hello from GROQ via nimble-llm-caller!' and confirm the integration is working in exactly 10 words.",
            model="groq/llama3-8b-8192",
            temperature=0.7,
            max_tokens=50
        )
        
        print(f"✅ GROQ call successful")
        print(f"📝 Response: {response}")
        
        # Test structured call
        prompt_config = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Respond with exactly the requested JSON format."
                },
                {
                    "role": "user", 
                    "content": "Return this exact JSON: {\"status\": \"success\", \"integration\": \"nimble-llm-caller\", \"model\": \"groq\", \"message\": \"Working!\"}"
                }
            ],
            "params": {
                "temperature": 0.1,
                "max_tokens": 100
            }
        }
        
        result = integration.call_model_with_prompt(
            model_name="groq/llama3-8b-8192",
            prompt_config=prompt_config,
            response_format_type="text"
        )
        
        print(f"✅ Structured GROQ call successful")
        print(f"📝 Raw response: {result.get('raw_content', '')}")
        print(f"📝 Parsed response: {result.get('parsed_content', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ GROQ integration test failed: {e}")
        return False

def main():
    """Run GROQ integration test."""
    print("🚀 GROQ Integration Test")
    print("=" * 40)
    
    load_environment()
    
    # Check if GROQ API key is available
    groq_key = os.getenv('GROQ_API_KEY')
    if not groq_key or groq_key == 'Not set':
        print("❌ GROQ_API_KEY not found in environment")
        return False
    
    print(f"🔑 GROQ API Key: {groq_key[:8]}...")
    
    success = test_groq_integration()
    
    if success:
        print("\n🎉 GROQ integration test PASSED!")
        print("✅ nimble-llm-caller integration is working correctly with GROQ")
        return True
    else:
        print("\n❌ GROQ integration test FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)