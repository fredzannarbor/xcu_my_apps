#!/usr/bin/env python3

import json
from codexes.core.enhanced_llm_caller import EnhancedLLMCaller

def test_json_parsing():
    """Test the JSON parsing directly."""
    
    # This is the actual content from the LLM response
    test_content = '''```json
{
  "mnemonics_data": [
    {
      "acronym": "MARS",
      "expansion": "Martian Autonomy, Resourceful Self-reliance",
      "explanation": "This mnemonic highlights the core necessity for Martian settlements to achieve independence. By utilizing local resources and 'living off the land,' colonists can become self-sufficient, making long-term presence practical and economically viable without prohibitive Earth support."
    },
    {
      "acronym": "ALONE",
      "expansion": "Alone, Lag, On Necessity, Earth-independent",
      "explanation": "This emphasizes the profound isolation and communication delays faced by Martian settlers, making continuous Earth support impractical. It underscores that being 'on their own' is not just a choice but a critical necessity for survival, demanding complete independence from Earth."
    }
  ]
}
```'''
    
    caller = EnhancedLLMCaller()
    
    print("=== TESTING JSON PARSING ===")
    print(f"Content length: {len(test_content)}")
    print(f"Content preview: {test_content[:200]}...")
    
    parsed = caller._extract_and_parse_json(test_content)
    
    print(f"Parsed result: {parsed}")
    print(f"Parsed type: {type(parsed)}")
    
    if parsed and 'mnemonics_data' in parsed:
        print("✅ JSON parsing successful!")
        print(f"Found {len(parsed['mnemonics_data'])} mnemonics")
        for i, mnemonic in enumerate(parsed['mnemonics_data']):
            print(f"{i+1}. {mnemonic.get('acronym', 'N/A')}: {mnemonic.get('expansion', 'N/A')}")
    else:
        print("❌ JSON parsing failed")

if __name__ == "__main__":
    test_json_parsing()