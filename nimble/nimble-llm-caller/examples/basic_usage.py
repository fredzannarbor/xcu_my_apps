#!/usr/bin/env python3
"""
Basic usage examples for nimble-llm-caller.
"""

import os
from pathlib import Path
from nimble_llm_caller import LLMContentGenerator, LLMRequest, ResponseFormat

# Set up environment variables (you would do this in your .env file)
# os.environ["OPENAI_API_KEY"] = "your-openai-key"
# os.environ["ANTHROPIC_API_KEY"] = "your-anthropic-key"

def basic_single_call():
    """Example of a basic single LLM call."""
    print("=== Basic Single Call ===")
    
    # Initialize the generator with a prompts file
    generator = LLMContentGenerator(
        prompt_file_path="examples/sample_prompts.json",
        default_model="gpt-4o"
    )
    
    # Make a single call
    response = generator.call_single(
        prompt_key="summarize_text",
        substitutions={
            "text": "Artificial intelligence is transforming how we work, learn, and interact with technology. From automated customer service to advanced medical diagnostics, AI systems are becoming increasingly sophisticated and ubiquitous in our daily lives."
        },
        response_format=ResponseFormat.TEXT
    )
    
    print(f"Status: {response.status}")
    print(f"Content: {response.content}")
    print(f"Execution time: {response.execution_time:.2f}s")
    print()

def json_response_example():
    """Example of getting structured JSON responses."""
    print("=== JSON Response Example ===")
    
    generator = LLMContentGenerator(
        prompt_file_path="examples/sample_prompts.json"
    )
    
    response = generator.call_single(
        prompt_key="extract_metadata",
        substitutions={
            "content": "The Great Gatsby by F. Scott Fitzgerald is a classic American novel published in 1925. It explores themes of wealth, love, and the American Dream during the Jazz Age."
        },
        response_format=ResponseFormat.JSON
    )
    
    print(f"Status: {response.status}")
    print(f"Parsed content: {response.parsed_content}")
    print()

def batch_processing_example():
    """Example of batch processing multiple prompts."""
    print("=== Batch Processing Example ===")
    
    generator = LLMContentGenerator(
        prompt_file_path="examples/sample_prompts.json"
    )
    
    # Process multiple prompts with shared content
    batch_response = generator.call_batch(
        prompt_keys=["summarize_text", "extract_keywords", "generate_title"],
        shared_substitutions={
            "content": "Climate change represents one of the most pressing challenges of our time. Rising global temperatures, melting ice caps, and extreme weather events are clear indicators that immediate action is needed. Renewable energy sources like solar and wind power offer promising solutions, but require significant investment and policy support to scale effectively."
        },
        models=["gpt-4o", "claude-3-sonnet"],  # Alternate between models
        parallel=True
    )
    
    print(f"Total requests: {batch_response.total_requests}")
    print(f"Success rate: {batch_response.success_rate:.1f}%")
    
    for response in batch_response.get_successful_responses():
        print(f"- {response.prompt_key}: {response.get_content_preview(50)}")
    print()

def document_assembly_example():
    """Example of assembling responses into a document."""
    print("=== Document Assembly Example ===")
    
    generator = LLMContentGenerator(
        prompt_file_path="examples/sample_prompts.json",
        output_dir="examples/output"
    )
    
    # Generate content
    batch_response = generator.call_batch(
        prompt_keys=["generate_introduction", "main_content", "conclusion"],
        shared_substitutions={
            "topic": "The Future of Remote Work",
            "context": "Post-pandemic workplace transformation"
        }
    )
    
    # Assemble into a document
    document = generator.assemble_document(
        batch_response,
        format="markdown",
        output_filename="remote_work_report.md",
        custom_sections={
            "executive_summary": "This report examines the evolving landscape of remote work and its implications for businesses and employees."
        }
    )
    
    print(f"Document assembled: {document.word_count} words")
    print(f"Format: {document.format}")
    print()

def reprompting_example():
    """Example of using previous results in new prompts."""
    print("=== Reprompting Example ===")
    
    generator = LLMContentGenerator(
        prompt_file_path="examples/sample_prompts.json"
    )
    
    # First call: generate initial content
    initial_response = generator.call_single(
        prompt_key="brainstorm_ideas",
        substitutions={
            "topic": "sustainable transportation"
        }
    )
    
    # Second call: refine based on initial results
    refined_response = generator.reprompt(
        base_prompt_key="refine_ideas",
        previous_results=[initial_response],
        additional_substitutions={
            "focus": "urban environments"
        }
    )
    
    print(f"Initial ideas: {initial_response.get_content_preview(100)}")
    print(f"Refined ideas: {refined_response.get_content_preview(100)}")
    print()

def error_handling_example():
    """Example of handling errors and validation."""
    print("=== Error Handling Example ===")
    
    generator = LLMContentGenerator(
        prompt_file_path="examples/sample_prompts.json"
    )
    
    # Try a call that might fail
    response = generator.call_single(
        prompt_key="nonexistent_prompt",  # This will fail
        substitutions={"text": "test"}
    )
    
    if not response.is_success:
        print(f"Call failed: {response.error_message}")
    
    # Example with validation
    json_response = generator.call_single(
        prompt_key="extract_metadata",
        substitutions={"content": "Some content"},
        response_format=ResponseFormat.JSON
    )
    
    # Validate the response
    validation = generator.llm_caller.validate_response(
        json_response,
        required_keys=["title", "author", "summary"]
    )
    
    print(f"Validation passed: {validation['valid']}")
    if not validation['valid']:
        print(f"Issues: {validation['issues']}")
    print()

def main():
    """Run all examples."""
    print("Nimble LLM Caller - Basic Usage Examples")
    print("=" * 50)
    
    try:
        basic_single_call()
        json_response_example()
        batch_processing_example()
        document_assembly_example()
        reprompting_example()
        error_handling_example()
        
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure you have set up your API keys in environment variables.")

if __name__ == "__main__":
    main()