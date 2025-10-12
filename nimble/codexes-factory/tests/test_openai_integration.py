#!/usr/bin/env python3
"""
Test script to verify nimble-llm-caller integration works with OpenAI API.
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

def test_openai_integration():
    """Test OpenAI integration with real API call."""
    print("🧪 Testing OpenAI Integration with Real API Call")
    print("=" * 60)
    
    try:
        from codexes.core.llm_integration import get_llm_integration
        
        integration = get_llm_integration()
        
        # Test simple call with OpenAI
        response = integration.call_llm(
            prompt="Say 'Hello from OpenAI via nimble-llm-caller!' and confirm the integration is working.",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=100
        )
        
        print(f"✅ OpenAI call successful")
        print(f"📝 Response: {response}")
        
        # Test structured call
        prompt_config = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that responds in JSON format."
                },
                {
                    "role": "user", 
                    "content": "Create a JSON object with: {\"status\": \"success\", \"integration\": \"nimble-llm-caller\", \"model\": \"gpt-4o\", \"message\": \"Integration working perfectly!\"}"
                }
            ],
            "params": {
                "temperature": 0.3,
                "max_tokens": 200
            }
        }
        
        result = integration.call_model_with_prompt(
            model_name="gpt-4o",
            prompt_config=prompt_config,
            response_format_type="json_object"
        )
        
        print(f"✅ Structured OpenAI call successful")
        print(f"📝 Raw response: {result.get('raw_content', '')}")
        print(f"📝 Parsed response: {result.get('parsed_content', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI integration test failed: {e}")
        return False

def main():
    """Run OpenAI integration test."""
    print("🚀 OpenAI Integration Test")
    print("=" * 40)
    
    load_environment()
    
    # Check if OpenAI API key is available
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key or openai_key == 'Not set':
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    print(f"🔑 OpenAI API Key: {openai_key[:8]}...")
    
    success = test_openai_integration()
    
    if success:
        print("\n🎉 OpenAI integration test PASSED!")
        print("✅ nimble-llm-caller integration is working correctly with OpenAI")
        return True
    else:
        print("\n❌ OpenAI integration test FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)