#!/usr/bin/env python3
import json

def main():
    # Create a test book data
    book_data = {
        "title": "Test Book",
        "stream": "Test Stream",
        "description": "Test Description",
        "special_requests": "",
        "recommended_sources": ""
    }
    
    # Set quotes_per_book explicitly
    book_data["quotes_per_book"] = 90
    
    # Print the book data
    print(f"Book data: {book_data}")
    
    # Create substitutions
    substitutions = {
        "book_content": f"Title: {book_data['title']}\n\nDescription: {book_data['description']}",
        "topic": book_data["title"],
        "stream": book_data["stream"],
        "description": book_data["description"],
        "quotes_per_book": book_data.get("quotes_per_book", 10),  # Default to 10 if not found
        "special_requests": book_data.get("special_requests", ""),
        "recommended_sources": book_data.get("recommended_sources", "")
    }
    
    # Print the substitutions
    print(f"Substitutions: {substitutions}")
    
    # Load the prompt template
    with open("imprints/xynapse_traces/prompts.json", "r") as f:
        prompts = json.load(f)
    
    # Get the imprint_quotes_prompt
    quotes_prompt = prompts.get("imprint_quotes_prompt", {})
    
    # Print the prompt template
    print(f"Prompt template params: {quotes_prompt.get('params', {})}")
    
    # Format the prompt
    if "messages" in quotes_prompt:
        for i, message in enumerate(quotes_prompt["messages"]):
            if "content" in message:
                content = message["content"]
                try:
                    formatted_content = content.format(**substitutions)
                    print(f"Message {i+1} formatted content: {formatted_content[:200]}...")
                except KeyError as e:
                    print(f"Error formatting message {i+1}: {e}")

if __name__ == "__main__":
    main()