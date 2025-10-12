#!/usr/bin/env python3

import json
import logging
from codexes.core.enhanced_llm_caller import call_llm_json_with_exponential_backoff

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mnemonic_llm_call():
    """Test the LLM call for mnemonic generation."""
    
    # Simple test content
    book_content = """Title: Martian Self-Reliance: Isolation versus Earth Support

Description: A compelling exploration of human adaptation and self-reliance in the harsh environment of Mars

Key Quotations:
1. "We are caught in a dynamic process of having to create a new culture, a new society, a new way of being human. We are the first Martians." - Kim Stanley Robinson
2. "The key to making Mars settlements practical is 'living off the land'—using Martian resources to supply the needs of the colonists." - Robert Zubrin and Richard Wagner
3. "If the oxygenator breaks down, I'll suffocate. If the water reclaimer breaks down, I'll die of thirst." - Andy Weir

IMPORTANT: Create mnemonics that are DIRECTLY related to these specific quotations."""
    
    messages = [
        {
            "role": "system",
            "content": "You are an expert at creating educational mnemonics. Create memorable acronyms that help readers retain key insights from the provided book content. Focus ONLY on the specific themes and concepts that emerge from the provided quotations."
        },
        {
            "role": "user",
            "content": f"Based on the quotations in the provided book, create 3 mnemonics that help readers remember key themes and insights from THESE SPECIFIC QUOTATIONS. Each mnemonic should be structured as: 1) An acronym (3-6 letters), 2) What each letter stands for, 3) A brief explanation connecting it to the book's content. Return as JSON with key 'mnemonics_data' containing an array of objects with keys: 'acronym', 'expansion', 'explanation'.\n\nBook Content:\n{book_content}"
        }
    ]
    
    print("=== TESTING LLM CALL ===")
    print(f"Messages: {json.dumps(messages, indent=2)}")
    
    try:
        response = call_llm_json_with_exponential_backoff(
            model="gemini/gemini-2.5-flash",
            messages=messages,
            expected_keys=['mnemonics_data'],
            temperature=0.7,
            max_tokens=2000
        )
        
        print(f"\n=== RESPONSE ===")
        print(f"Response type: {type(response)}")
        print(f"Response: {response}")
        
        if response and 'mnemonics_data' in response:
            print(f"\n=== SUCCESS ===")
            print(f"Generated {len(response['mnemonics_data'])} mnemonics")
            for i, mnemonic in enumerate(response['mnemonics_data']):
                print(f"{i+1}. {mnemonic.get('acronym', 'N/A')}: {mnemonic.get('expansion', 'N/A')}")
        else:
            print(f"\n=== FAILED ===")
            print("No mnemonics_data in response or response is None")
            
    except Exception as e:
        print(f"\n=== ERROR ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mnemonic_llm_call()