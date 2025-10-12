#!/usr/bin/env python3
"""
Custom version of llm_get_book_data.py for testing.
"""

import json
import logging
import os
from pathlib import Path
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s.%(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

def prepare_book_content(book_data):
    """Prepare the book content for the mnemonics prompt."""
    title = book_data.get("title", "Untitled")
    description = book_data.get('description', 'No description provided')
    stream = book_data.get('stream', 'Stream_TBD')
    
    # For mnemonics prompt, we need to include the quotes if they exist
    quotes = book_data.get("quotes", [])
    quotes_text = ""
    
    if quotes:
        quotes_text = "\n\nQuotations in this book:\n"
        # Use all quotes but be mindful of potential token limits
        num_quotes = len(quotes)
        
        # If there are many quotes, provide a summary of themes and authors
        if num_quotes > 30:
            # Include a sample of quotes (first 10, middle 10, last 10)
            sample_quotes = quotes[:10] + quotes[num_quotes//2-5:num_quotes//2+5] + quotes[-10:]
            
            # Get all unique authors
            all_authors = set(quote.get("author", "Unknown") for quote in quotes)
            authors_text = ", ".join(list(all_authors)[:20])  # Limit to 20 authors if there are many
            if len(all_authors) > 20:
                authors_text += f", and {len(all_authors) - 20} more"
                
            # Add summary information
            quotes_text += f"This book contains {num_quotes} quotes from authors including {authors_text}.\n"
            quotes_text += f"Here is a representative sample of {len(sample_quotes)} quotes:\n\n"
            
            # Add the sample quotes
            for i, quote in enumerate(sample_quotes, 1):
                q_text = quote.get("quote", "")
                q_author = quote.get("author", "Unknown")
                q_source = quote.get("source", "Unknown")
                quotes_text += f"{i}. \"{q_text}\" - {q_author}, {q_source}\n"
        else:
            # If there aren't too many quotes, include all of them
            for i, quote in enumerate(quotes, 1):
                q_text = quote.get("quote", "")
                q_author = quote.get("author", "Unknown")
                q_source = quote.get("source", "Unknown")
                quotes_text += f"{i}. \"{q_text}\" - {q_author}, {q_source}\n"
    
    book_content = f"Title: {title}\n\nStream: {stream}\n\nDescription: {description}{quotes_text}"
    return book_content

def process_book(book_data, prompt_template_file, model_name, per_model_params, raw_output_dir, safe_basename, prompt_keys, catalog_only=False):
    """
    Processes a single book entry, generates all required data, and returns stats.
    Saves raw LLM responses to the specified directory.
    """
    title = book_data.get("title", f"Title_TBD_{time.time()}")
    stream = book_data.get("stream", "Stream_TBD")
    description = book_data.get('description', 'Expand topic logically into related concepts.')
    logging.info(f"Processing book: '{title}' in stream: '{stream}'")

    # Prepare the book content
    book_content = prepare_book_content(book_data)
    
    # Load the mnemonics prompt
    mnemonics_prompt = None
    try:
        with open(prompt_template_file, 'r', encoding='utf-8') as f:
            prompts_data = json.load(f)
            if "mnemonics_prompt" in prompts_data and "messages" in prompts_data["mnemonics_prompt"]:
                mnemonics_prompt = prompts_data["mnemonics_prompt"].copy()
                # Replace $book_content$ placeholder with actual book content
                for i, message in enumerate(mnemonics_prompt["messages"]):
                    if "content" in message:
                        mnemonics_prompt["messages"][i]["content"] = message["content"].replace("$book_content$", book_content)
    except Exception as e:
        logging.error(f"Error loading mnemonics prompt: {e}")
        return None, {"prompts_successful": 0, "quotes_found": 0}
    
    # For testing purposes, we'll simulate a successful LLM response
    mnemonics_tex = """% Mnemonics for Key Themes in This Book
\\chapter*{Mnemonics}
\\addcontentsline{toc}{chapter}{Mnemonics}

\\textbf{C.L.E.A.R. Thinking} (from the critical thinking quotations)

\\begin{itemize}
    \\item \\textbf{C}hallenge assumptions (Aristotle: "It is the mark of an educated mind...")
    \\item \\textbf{L}ook for evidence (Boorstin: "The greatest enemy of knowledge...")
    \\item \\textbf{E}valuate alternatives (Voltaire: "Doubt is not a pleasant condition...")
    \\item \\textbf{A}pply reasoning (Descartes: "I think, therefore I am.")
    \\item \\textbf{R}eflect on outcomes (Confucius: "Real knowledge is to know...")
\\end{itemize}

\\vspace{2em}

\\textbf{Q.U.E.S.T.} (for intellectual growth)

\\begin{itemize}
    \\item \\textbf{Q}uestion everything (Einstein: "The important thing is not to stop questioning...")
    \\item \\textbf{U}nderstand deeply (Plutarch: "The mind is not a vessel to be filled...")
    \\item \\textbf{E}xamine perspectives (Nin: "We don't see things as they are...")
    \\item \\textbf{S}eek wisdom (Socrates: "The unexamined life is not worth living.")
    \\item \\textbf{T}rain consistently (Aristotle: "We are what we repeatedly do...")
\\end{itemize}
"""
    
    # Create the final book JSON
    final_book_json = {
        "title": title,
        "stream": stream,
        "description": description,
        "author": "AI Lab for Book-Lovers",
        "publisher": "Nimble Books LLC",
        "imprint": "xynapse traces",
        "quotes": book_data.get("quotes", []),
        "mnemonics_tex": mnemonics_tex
    }
    
    # Save the raw response
    raw_filename = f"{safe_basename}_mnemonics_prompt.txt"
    (raw_output_dir / raw_filename).write_text(json.dumps(mnemonics_prompt, indent=2), encoding='utf-8')
    
    return final_book_json, {"prompts_successful": 1, "quotes_found": len(book_data.get("quotes", []))}

def main():
    """Main function for testing."""
    # Load the sample book
    with open("sample_book.json", 'r', encoding='utf-8') as f:
        book_data = json.load(f)
    
    # Create a temporary output directory
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    raw_output_dir = output_dir / "raw_json_responses"
    raw_output_dir.mkdir(exist_ok=True)
    
    # Process the book
    book_json_data, llm_stats = process_book(
        book_data=book_data,
        prompt_template_file="prompts/prompts.json",
        model_name="gemini/gemini-2.5-flash",
        per_model_params={},
        raw_output_dir=raw_output_dir,
        safe_basename="test_book",
        prompt_keys=["mnemonics_prompt"],
        catalog_only=False
    )
    
    # Save the processed book data
    with open(output_dir / "test_book.json", 'w', encoding='utf-8') as f:
        json.dump(book_json_data, f, indent=2)
    
    # Print the mnemonics_tex field
    print("mnemonics_tex field:")
    print(book_json_data.get("mnemonics_tex", ""))

if __name__ == "__main__":
    main()