# Design Document

## Overview

This design implements LLM-based back cover text generation by integrating it into Stage 1 (LLM Content Generation) of the book pipeline. Instead of using basic string substitution during cover generation, the system will generate clean, final back cover text during the initial content generation phase when all book metadata is available and other LLM calls are already being made.

## Architecture

The system integrates into the existing book pipeline workflow:

```
Stage 1: LLM Content Generation
├── Load book metadata and generate quotes
├── Process other metadata fields (title, description, etc.)
├── **NEW: Generate final back cover text**
│   ├── Use book metadata and quotes context
│   ├── Call LLM with back cover prompt
│   ├── Store clean, final text in book data
│   └── No variables or substitutions needed
├── Save processed data to JSON
└── Continue to Stage 2...

Stage 3: Cover Generation
├── Load book metadata from JSON
├── Use pre-generated back_cover_text (no processing needed)
├── Apply LaTeX escaping and formatting
└── Generate cover PDF
```

This approach eliminates the need for variable substitution during cover generation since the text is already finalized.

## Components and Interfaces

### 1. Stage 1 Content Generation Enhancement

**Location:** `src/codexes/modules/builders/llm_get_book_data.py`

The existing content generation process will be enhanced to include back cover text generation:

```python
def generate_back_cover_text(book_data: Dict[str, Any], quotes: List[Dict]) -> str:
    """Generate final back cover text using LLM with full book context."""
    # Use existing LLM infrastructure to generate clean, final text
    # No variables or substitutions - just clean, ready-to-use text
```

**Integration Points:**
- Called after quote generation when full context is available
- Uses existing `call_model_with_prompt()` infrastructure
- Stores result in `book_data['back_cover_text']` for later use

### 2. Cover Generator Simplification

**Location:** `src/codexes/modules/covers/cover_generator.py`

The existing `create_cover_latex()` function will be simplified:
- Remove `substitute_template_variables()` function call
- Use `data.get('back_cover_text', '')` directly (already processed)
- Apply existing LaTeX escaping to the final text

### 3. Enhanced Prompt Configuration

**Location:** `prompts/prompts.json`

The existing `back_cover_text` prompt will be enhanced to generate final text directly:

```json
{
  "back_cover_text": {
    "params": {
      "temperature": 0.7,
      "max_tokens": 500
    },
    "messages": [
      {
        "role": "system",
        "content": "You are a professional book marketing copywriter. Generate engaging back cover text that flows naturally and is ready for publication."
      },
      {
        "role": "user", 
        "content": "Generate back cover text for '{title}' by {author} in the {stream} domain. The book contains {quotes_per_book} quotations with bibliography and verification log. Description: {description}. Return clean, final text with no variables or placeholders."
      }
    ]
  }
}
```

## Data Models

### Stage 1 Input Data
```python
{
    "book_data": {
        "title": str,
        "author": str,
        "imprint": str,
        "subject": str,  # Stream/topic
        "description": str,
        "quotes_per_book": int,
        "storefront_publishers_note_en": str,
        # ... other metadata
    },
    "generated_quotes": List[Dict],  # Available for context
}
```

### LLM Response Structure
```python
{
    "back_cover_text": str  # Clean, final text ready for cover placement
}
```

### Updated Book Data Structure
After Stage 1 processing, the book data will contain:
```python
{
    # ... existing fields
    "back_cover_text": str,  # Final, processed text (no variables)
    # ... other fields
}
```

## Error Handling

### LLM Generation Errors
1. **Rate Limiting:** Use existing retry logic in `call_model_with_prompt()`
2. **Invalid Response:** Validate JSON response format and retry if malformed
3. **Timeout:** Use existing timeout handling in LLM caller
4. **Service Unavailable:** Retry with exponential backoff per existing patterns

### Fallback Strategy
When back cover text generation fails during Stage 1:
1. Log the failure with full context
2. Generate a simple fallback text using book metadata
3. Store fallback text in `back_cover_text` field
4. Continue with pipeline processing
5. Add warning to processing log for manual review

### Validation Rules
- Response must contain `back_cover_text` field
- Text length must be reasonable (50-200 words)
- Text must end with complete sentence
- No template variables or placeholders remaining
- Text must be suitable for LaTeX processing

## Testing Strategy

### Unit Tests
- `test_back_cover_text_processor.py`: Test the processor class in isolation
- Mock LLM responses to test various scenarios
- Test fallback behavior when LLM fails
- Validate response parsing and error handling

### Integration Tests
- `test_cover_generation_with_llm.py`: Test full cover generation pipeline
- Test with real book data and LLM calls
- Verify LaTeX compilation with processed text
- Test performance under various load conditions

### Test Data
- Sample back cover templates with various variable combinations
- Mock book metadata covering different genres and formats
- Edge cases: missing metadata, malformed templates, special characters

## Implementation Phases

### Phase 1: Stage 1 Integration
- Add back cover text generation to `llm_get_book_data.py`
- Enhance existing `back_cover_text` prompt in `prompts.json`
- Implement LLM call using existing infrastructure
- Add validation and fallback logic

### Phase 2: Cover Generator Simplification
- Remove variable substitution from `cover_generator.py`
- Update to use pre-generated `back_cover_text` directly
- Remove unused `substitute_template_variables()` function
- Test cover generation with new approach

### Phase 3: Testing and Validation
- Test full pipeline from Stage 1 through cover generation
- Validate text quality and LaTeX compatibility
- Add monitoring for back cover text generation success rates
- Fine-tune prompt for optimal results

## Configuration Options

### LLM Settings
```json
{
  "back_cover_llm_config": {
    "model": "gemini/gemini-2.5-flash",
    "max_retries": 3,
    "timeout_seconds": 30,
    "temperature": 0.7,
    "max_tokens": 500
  }
}
```

### Processing Options
```json
{
  "back_cover_processing": {
    "enable_llm_processing": true,
    "fallback_on_failure": true,
    "cache_responses": true,
    "max_text_length": 200,
    "required_variables": ["title", "author", "stream"]
  }
}
```

## Performance Considerations

### Caching Strategy
- Cache processed text based on template + metadata hash
- Use file-based cache with TTL for development
- Consider Redis for production environments

### Cost Optimization
- Use faster, cheaper models for simple substitutions
- Implement request batching where possible
- Monitor token usage and implement alerts

### Latency Management
- Async processing where cover generation allows
- Parallel processing of multiple covers
- Precompute common templates during off-peak hours