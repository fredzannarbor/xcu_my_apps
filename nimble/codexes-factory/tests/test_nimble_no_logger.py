#!/usr/bin/env python3
"""
Test nimble_llm_caller without interaction logger
"""

try:
    from nimble_llm_caller.core.llm_caller import LLMCaller  # Use base class instead
    from nimble_llm_caller.models.request import LLMRequest, ResponseFormat
    
    # Create base caller (no enhanced features)
    caller = LLMCaller()
    
    # Create simple request
    request = LLMRequest(
        prompt_key="test_prompt",
        model="gpt-4",
        response_format=ResponseFormat.TEXT,
        model_params={
            "temperature": 0.7,
            "max_tokens": 100
        },
        metadata={
            "content": "Say hello world"
        }
    )
    
    print("Making LLM call...")
    response = caller.call(request)
    
    print(f"Response status: {response.status}")
    print(f"Response is_success: {response.is_success}")
    print(f"Response content: {response.content}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()