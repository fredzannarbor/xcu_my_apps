#!/usr/bin/env python3

import json
import logging
from src.codexes.core.enhanced_llm_caller import EnhancedLLMCaller

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_llm_response():
    """Debug the LLM response to see why content is None."""
    
    # Load the assembled responses file
    with open('data/July_2025/Martian_Self-Reliance_Isolation_versus_Earth_Support_assembled_raw_responses.json', 'r') as f:
        raw_data = json.load(f)

    # Extract quotes from the first model's response
    first_model_key = list(raw_data.keys())[0]
    first_response = raw_data[first_model_key][0]
    quotes = first_response['content']['quotes']

    # Create book data structure
    book_data = {
        'title': 'Martian Self-Reliance: Isolation versus Earth Support',
        'description': 'A compelling exploration of human adaptation and self-reliance in the harsh environment of Mars',
        'quotes': quotes
    }

    # Prepare content like the backmatter processor does
    title = book_data.get('title', 'Untitled')
    description = book_data.get('description', '')
    quotes = book_data.get('quotes', [])
    
    content = f"Title: {title}\n\nDescription: {description}\n\nKey Quotations:\n"
    
    # Include all quotes to ensure mnemonics are related to the actual content
    for i, quote in enumerate(quotes):
        quote_text = quote.get('quote', '')
        author = quote.get('author', 'Unknown')
        content += f"{i+1}. \"{quote_text}\" - {author}\n"
    
    # Add specific instructions to ensure relevance
    content += "\n\nIMPORTANT: Create mnemonics that are DIRECTLY related to these specific quotations. Do NOT create generic mnemonics about reading or writing. The mnemonics must help readers remember the specific themes, concepts, and ideas present in these exact quotations."
    
    print(f"Content length: {len(content)} characters")
    print(f"Number of quotes: {len(quotes)}")
    
    # Prepare messages
    messages = [
        {
            "role": "system",
            "content": "You are an expert at creating educational mnemonics. Create memorable acronyms that help readers retain key insights from the provided book content. Focus ONLY on the specific themes and concepts that emerge from the provided quotations. Do not create generic mnemonics about reading or writing unless those are central themes in the quotations."
        },
        {
            "role": "user",
            "content": f"Based on the quotations in the provided book, create 5-7 mnemonics that help readers remember key themes and insights from THESE SPECIFIC QUOTATIONS. Each mnemonic should be structured as: 1) An acronym (3-6 letters), 2) What each letter stands for, 3) A brief explanation connecting it to the book's content. Format as structured data that can be easily converted to LaTeX. Return as JSON with key 'mnemonics_data' containing an array of objects with keys: 'acronym', 'expansion', 'explanation'. Each explanation should be 2-3 sentences maximum.\n\nBook Content:\n{content}"
        }
    ]
    
    # Use the enhanced caller directly
    caller = EnhancedLLMCaller()
    
    print("=== MAKING LLM CALL ===")
    response = caller.call_llm_with_retry(
        model="gemini/gemini-2.5-flash",
        messages=messages,
        temperature=0.7,
        max_tokens=2000
    )
    
    print(f"Response type: {type(response)}")
    print(f"Response: {response}")
    
    if response:
        print(f"Content: {response.get('content')}")
        print(f"Content type: {type(response.get('content'))}")
        if response.get('content'):
            print(f"Content length: {len(response.get('content'))}")
            print(f"Content preview: {response.get('content')[:200]}")
    
if __name__ == "__main__":
    debug_llm_response()