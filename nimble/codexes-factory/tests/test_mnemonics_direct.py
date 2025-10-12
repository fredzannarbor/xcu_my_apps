#!/usr/bin/env python3
"""
Direct test script for mnemonics generation using a simplified approach.
"""

import json
import os
import sys
from pathlib import Path
import litellm

# Configure litellm
litellm.set_verbose = False

def generate_mnemonics(book_data):
    """Generate mnemonics for a book using a direct LLM call."""
    
    title = book_data.get("title", "Untitled")
    description = book_data.get('description', 'No description provided')
    quotes = book_data.get("quotes", [])
    
    # Format quotes for the prompt
    quotes_text = ""
    if quotes:
        quotes_text = "\n\nQuotations in this book:\n"
        for i, quote in enumerate(quotes, 1):
            q_text = quote.get("quote", "")
            q_author = quote.get("author", "Unknown")
            q_source = quote.get("source", "Unknown")
            quotes_text += f"{i}. \"{q_text}\" - {q_author}, {q_source}\n"
    
    book_content = f"Title: {title}\n\nDescription: {description}{quotes_text}"
    
    # Create a direct prompt
    prompt = f"""Based on the quotations and content in the provided book, generate a list of 5-7 creative mnemonics to help readers remember the key themes, concepts, and insights from the book's quotations. Focus specifically on the book's content, not on the art of mnemonics itself.

Return as a valid JSON object with one key 'mnemonics_tex' containing complete LaTeX code ready to be saved as a .tex file. The LaTeX should NOT include \\documentclass, \\begin{{document}}, or \\end{{document}} - just the content that will be included in the main document. Each mnemonic acronym and its explanation should total no more than 80 tokens.

Book Content:
{book_content}

Your response must be a valid JSON object with the 'mnemonics_tex' key containing LaTeX code.
"""

    # Call the LLM directly
    try:
        response = litellm.completion(
            model="gemini/gemini-2.5-pro",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Extract the content
        content = response.choices[0].message.content
        print(f"Raw response: {content[:500]}...")
        
        # Try to parse as JSON
        try:
            # Look for JSON in the response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                parsed = json.loads(json_content)
                if 'mnemonics_tex' in parsed:
                    mnemonics_tex = parsed['mnemonics_tex']
                    print(f"Successfully extracted mnemonics_tex ({len(mnemonics_tex)} chars)")
                    
                    # Save to file
                    output_dir = Path("output/debug")
                    output_dir.mkdir(exist_ok=True, parents=True)
                    
                    # Save the raw response
                    with open(output_dir / "raw_response.txt", 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # Save the mnemonics
                    with open(output_dir / "mnemonics.tex", 'w', encoding='utf-8') as f:
                        f.write(mnemonics_tex)
                    
                    # Update the book data
                    book_data['mnemonics_tex'] = mnemonics_tex
                    
                    # Save the updated book data
                    with open(output_dir / "book_with_mnemonics.json", 'w', encoding='utf-8') as f:
                        json.dump(book_data, f, ensure_ascii=False, indent=4)
                    
                    print(f"Files saved to {output_dir}")
                    return mnemonics_tex
                else:
                    print("Error: 'mnemonics_tex' key not found in response")
            else:
                print("Error: No JSON found in response")
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Content: {content}")
    except Exception as e:
        print(f"Error calling LLM: {e}")
    
    return None

def load_book_data(json_path):
    """Load book data from a JSON file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load book data from {json_path}: {e}")
        return None

def main():
    """Main function to test mnemonics generation."""
    # Check if a processed JSON file exists in the output directory
    processed_dir = Path("output/xynapse_traces_build/processed_json")
    json_files = list(processed_dir.glob("*.json"))
    
    if not json_files:
        print("No processed JSON files found. Please run the pipeline first.")
        return
    
    # Use the first JSON file found
    json_path = json_files[0]
    print(f"Using book data from {json_path}")
    
    # Load the book data
    book_data = load_book_data(json_path)
    if not book_data:
        return
    
    # Generate mnemonics
    mnemonics_tex = generate_mnemonics(book_data)
    
    if mnemonics_tex:
        print("\nTo run the pipeline with the updated book data, use:")
        print("python run_book_pipeline.py --imprint xynapse_traces --schedule-file data/books.csv --model gemini/gemini-2.5-pro --max-books 1 --start-stage 3 --end-stage 3 --skip-lsi")

if __name__ == "__main__":
    main()