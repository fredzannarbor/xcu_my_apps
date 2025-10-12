# Multi-Model Feedback Framework

A reusable framework for collecting professional feedback from multiple AI models and collating their responses section-by-section with agreement analysis.

## Overview

This framework allows you to:
1. Submit any content (outlines, manuscripts, proposals, etc.) to N AI models
2. Collect their detailed professional feedback
3. Automatically collate responses by section for easy comparison
4. Analyze the degree of consensus/disagreement among models

## Installation

The framework is part of the codexes-factory modules:

```python
from codexes.modules.ideation.multi_model_feedback import (
    MultiModelReviewer,
    get_multi_model_feedback
)
```

## Quick Start

### Simple Usage

```python
from codexes.modules.ideation.multi_model_feedback import get_multi_model_feedback

# Your content to review
my_outline = {
    "title": "My Novel",
    "chapters": [...],
    ...
}

# Simple prompt (use {content} placeholder)
prompt = """
You are an experienced editor. Review this outline:

{content}

Provide feedback on structure, pacing, and characters.
"""

# Get feedback from multiple models
results = get_multi_model_feedback(
    content=my_outline,
    prompt_template=prompt,
    models=[
        "xai/grok-4-latest",
        "gemini/gemini-2.5-pro",
        "openai/gpt-4o",
        "anthropic/claude-sonnet-4-5-20250929"
    ],
    output_dir="./feedback",
    content_name="my_novel_outline",
    collate=True  # Automatically creates collated report
)

print(f"Collated report: {results['collated_report_path']}")
```

## Advanced Usage

### Custom Prompt Function

For more control, use a function instead of a string template:

```python
def my_prompt_builder(content_json, author_name="", expertise_area=""):
    """Build a customized prompt."""
    return f"""You are an expert in {expertise_area}.

Author: {author_name}

Please review:
{content_json}

[Your specific instructions...]
"""

reviewer = MultiModelReviewer(
    models=["xai/grok-4-latest", "gemini/gemini-2.5-pro"],
    output_dir="./output"
)

results = reviewer.get_feedback(
    content=my_content,
    prompt_template=my_prompt_builder,
    content_name="my_document",
    author_name="Jane Doe",
    expertise_area="young adult fiction"
)
```

### Custom Section Patterns

Define what sections to extract for collation:

```python
custom_sections = [
    (r'##?\s*Plot Analysis', 'Plot'),
    (r'##?\s*Character.*Development', 'Characters'),
    (r'##?\s*Pacing', 'Pacing'),
    (r'##?\s*Revised.*?Outline', 'Revision'),
]

collated = reviewer.collate_feedback(
    results,
    section_patterns=custom_sections
)
```

### Custom Agreement Analyzer

Implement your own logic to analyze consensus:

```python
def my_analyzer(section_contents):
    """Custom agreement analysis."""
    if not section_contents:
        return "No data."

    # Your custom logic here
    keywords = ['excellent', 'weak', 'needs work']
    counts = {kw: 0 for kw in keywords}

    for item in section_contents:
        text = item['content'].lower()
        for kw in keywords:
            if kw in text:
                counts[kw] += 1

    return f"Sentiment: {counts}"

collated = reviewer.collate_feedback(
    results,
    agreement_analyzer=my_analyzer
)
```

## API Reference

### MultiModelReviewer

Main class for collecting and collating feedback.

```python
reviewer = MultiModelReviewer(
    models: List[str],              # Model identifiers
    output_dir: str | Path,         # Where to save outputs
    temperature: float = 0.7,       # LLM temperature
    max_tokens: int = 16000,        # Max response tokens
    verbose: bool = True            # Print progress
)
```

#### Methods

**get_feedback()**
```python
results = reviewer.get_feedback(
    content: Any,                    # Content to review (dict, str, etc.)
    prompt_template: str | Callable, # Prompt template or function
    content_name: str,               # Name for output files
    **template_kwargs                # Additional template arguments
) -> Dict[str, Any]
```

Returns:
```python
{
    'successful_feedback': [
        {
            'model': 'xai/grok-4-latest',
            'content': 'feedback text...',
            'filepath': 'path/to/file.md',
            'error': None
        },
        ...
    ],
    'failed_models': [...],
    'summary_path': 'path/to/summary.md',
    'content_name': 'my_document'
}
```

**collate_feedback()**
```python
collated_path = reviewer.collate_feedback(
    feedback_results: Dict,                    # From get_feedback()
    section_patterns: List[tuple] = None,      # Custom section patterns
    agreement_analyzer: Callable = None        # Custom analyzer
) -> str  # Path to collated report
```

### get_multi_model_feedback()

Convenience function combining get_feedback() and collate_feedback():

```python
results = get_multi_model_feedback(
    content: Any,
    prompt_template: str | Callable,
    models: List[str],
    output_dir: str | Path,
    content_name: str,
    collate: bool = True,           # Whether to create collated report
    **kwargs                        # Additional MultiModelReviewer args
) -> Dict[str, Any]
```

Returns:
```python
{
    'feedback_results': {...},      # Results from get_feedback()
    'collated_report_path': '...'   # Path to collated report (if collate=True)
}
```

## Output Files

The framework generates:

1. **Individual feedback files**: `{content_name}_feedback_{model}.md`
   - One per model
   - Contains full response from that model

2. **Summary file**: `{content_name}_feedback_summary.md`
   - Lists all models consulted
   - Shows which succeeded/failed

3. **Collated report**: `{content_name}_feedback_collated.md`
   - Organizes all feedback section-by-section
   - Includes agreement analysis for each section

## Default Section Patterns

The default collation looks for these sections:

1. Overall Story Arc Assessment
2. Character Development
3. Decodable Text Concerns
4. Contemporary Hook Effectiveness
5. Dialogue and Voice
6. Educational Message
7. Chapter-by-Chapter Feedback
8. Suggested Changes
9. Target Audience Concerns
10. Overall Recommendations
11. Revised Outline

## Default Agreement Analysis

The default analyzer categorizes consensus as:

- **Strong Consensus (Positive)**: Models overwhelmingly use positive language
- **Strong Consensus (Negative)**: Models overwhelmingly identify issues
- **Mixed Reviews**: Models have divergent opinions
- **Moderate Agreement**: Some variation but generally aligned
- **Technical Focus**: Models focus on structure rather than evaluation

## Examples

See `examples/multi_model_feedback_example.py` for:

- Simple usage example
- Advanced usage with custom prompts
- Custom agreement analyzer
- Refactored Maya script using the framework

## Model Compatibility

The framework handles model-specific requirements:

- **GPT-5**: Automatically sets `temperature=1.0` (only supported value)
- **Other models**: Uses configured temperature (default 0.7)

Supported model identifiers:
- `xai/grok-4-latest`
- `gemini/gemini-2.5-pro`
- `openai/gpt-4o`
- `openai/gpt-5`
- `anthropic/claude-sonnet-4-5-20250929`
- Any other LiteLLM-supported model

## Error Handling

The framework gracefully handles:
- Model timeouts (captures error, continues with other models)
- Invalid model names (captures error, continues)
- API errors (captures error, continues)

Failed models are reported in the summary file but don't stop the process.

## Use Cases

1. **Manuscript Development**
   - Get editing feedback from multiple perspectives
   - Compare developmental suggestions
   - Identify consensus on strengths/weaknesses

2. **Outline Refinement**
   - Submit story outlines for structural feedback
   - Collect revised outlines from multiple models
   - Synthesize best suggestions

3. **Content Review**
   - Review marketing copy, proposals, etc.
   - Get diverse professional opinions
   - Identify areas of agreement/disagreement

4. **Quality Assurance**
   - Validate content against multiple AI evaluators
   - Ensure comprehensive coverage of issues
   - Build confidence through consensus

## Best Practices

1. **Prompt Design**
   - Be specific about what feedback you want
   - Ask for structured responses (numbered sections)
   - Request both analysis AND revisions if needed

2. **Model Selection**
   - Use 3-5 models for good coverage
   - Mix model providers for diverse perspectives
   - Consider cost vs. quality tradeoffs

3. **Section Patterns**
   - Match patterns to your prompt structure
   - Use regex for flexibility
   - Test patterns on sample output first

4. **Agreement Analysis**
   - Customize analyzer for your domain
   - Consider qualitative vs. quantitative analysis
   - Review agreement summaries critically

## Troubleshooting

**Problem**: Section not being extracted
- **Solution**: Check your regex pattern matches the model's actual output format

**Problem**: Model timeout
- **Solution**: Reduce `max_tokens` or simplify prompt

**Problem**: GPT-5 temperature error
- **Solution**: Framework handles this automatically, but ensure using latest version

**Problem**: No collated report generated
- **Solution**: Check that at least one model succeeded and `collate=True`

## Contributing

To extend the framework:

1. **Add new default section patterns**: Edit `_default_section_patterns` in `multi_model_feedback.py`
2. **Improve agreement analysis**: Enhance `_default_agreement_analyzer()`
3. **Add model-specific handling**: Update `get_feedback_from_model()` temperature logic

## License

Part of the codexes-factory project. See main project license.
