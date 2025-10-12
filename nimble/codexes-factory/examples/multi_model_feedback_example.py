#!/usr/bin/env python3
"""
Example usage of the Multi-Model Feedback Framework

This demonstrates how to use the framework to get professional feedback
from multiple AI models and collate their responses.
"""

import json
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codexes.modules.ideation.multi_model_feedback import (
    MultiModelReviewer,
    get_multi_model_feedback
)


# ==============================================================================
# EXAMPLE 1: Simple usage with convenience function
# ==============================================================================

def example_simple_usage():
    """Simplest way to get multi-model feedback."""

    # Your content to review
    content = {
        "title": "My Novel Outline",
        "chapters": [
            {"number": 1, "title": "The Beginning", "summary": "..."},
            {"number": 2, "title": "The Middle", "summary": "..."},
        ]
    }

    # Simple prompt template with {content} placeholder
    prompt_template = """
You are an experienced editor. Please review this outline:

{content}

Provide detailed feedback on:
1. Structure
2. Pacing
3. Character development
4. Suggested improvements
"""

    # Models to consult
    models = [
        "xai/grok-4-latest",
        "gemini/gemini-2.5-pro",
        "openai/gpt-4o",
        "anthropic/claude-sonnet-4-5-20250929"
    ]

    # Get feedback (automatically collates)
    results = get_multi_model_feedback(
        content=content,
        prompt_template=prompt_template,
        models=models,
        output_dir="./feedback_output",
        content_name="my_novel_outline",
        collate=True  # Creates collated report
    )

    print(f"Feedback collected: {len(results['feedback_results']['successful_feedback'])} models")
    print(f"Collated report: {results.get('collated_report_path')}")


# ==============================================================================
# EXAMPLE 2: Advanced usage with custom prompt function
# ==============================================================================

def example_advanced_usage():
    """Advanced usage with custom prompt and section patterns."""

    # Load content from file
    content_path = Path("data/ideation/development/maya_for_development.json")
    with open(content_path, 'r') as f:
        content = json.load(f)

    # Custom prompt function (more control than string template)
    def create_development_editing_prompt(content_json, author_context=""):
        """Create a detailed development editing prompt."""

        return f"""You are an experienced development editor and professional novelist.

{author_context}

Please provide detailed, professional feedback on this chapter book outline.

**OUTLINE:**
{content_json}

**PROVIDE:**
1. Overall Story Arc Assessment
2. Character Development analysis
3. Pacing concerns
4. Suggested improvements
5. Complete revised outline incorporating your changes (in JSON format)

Be thorough and specific."""

    # Initialize reviewer with specific config
    reviewer = MultiModelReviewer(
        models=[
            "xai/grok-4-latest",
            "gemini/gemini-2.5-pro",
            "anthropic/claude-sonnet-4-5-20250929"
        ],
        output_dir="./feedback_output",
        temperature=0.7,
        max_tokens=16000,
        verbose=True
    )

    # Get feedback
    results = reviewer.get_feedback(
        content=content,
        prompt_template=create_development_editing_prompt,
        content_name="maya_outline",
        author_context="I am a highly successful novelist seeking detailed professional feedback."
    )

    # Custom section patterns for collation
    custom_sections = [
        (r'##?\s*1[\.\)]\s*\*?\*?Overall Story Arc', 'Story Arc'),
        (r'##?\s*2[\.\)]\s*\*?\*?Character Development', 'Characters'),
        (r'##?\s*3[\.\)]\s*\*?\*?Pacing', 'Pacing'),
        (r'##?\s*4[\.\)]\s*\*?\*?Suggested', 'Suggestions'),
        (r'##?\s*5[\.\)]\s*\*?\*?Revised.*?Outline', 'Revised Outline'),
    ]

    # Collate with custom patterns
    collated_path = reviewer.collate_feedback(
        results,
        section_patterns=custom_sections
    )

    print(f"Collated report: {collated_path}")


# ==============================================================================
# EXAMPLE 3: Custom agreement analyzer
# ==============================================================================

def example_custom_agreement_analyzer():
    """Example with custom agreement analysis logic."""

    def my_agreement_analyzer(section_contents):
        """Custom logic to analyze agreement."""
        if not section_contents:
            return "No feedback."

        # Count models that mention specific themes
        mentions_pacing = sum(1 for item in section_contents if 'pacing' in item['content'].lower())
        mentions_characters = sum(1 for item in section_contents if 'character' in item['content'].lower())

        analysis = f"**Thematic Analysis:**\n"
        analysis += f"- {mentions_pacing}/{len(section_contents)} models discussed pacing\n"
        analysis += f"- {mentions_characters}/{len(section_contents)} models discussed characters\n"

        return analysis

    # Use with collation
    reviewer = MultiModelReviewer(
        models=["xai/grok-4-latest", "gemini/gemini-2.5-pro"],
        output_dir="./feedback_output"
    )

    # ... get feedback ...
    # results = reviewer.get_feedback(...)

    # Collate with custom analyzer
    # collated = reviewer.collate_feedback(
    #     results,
    #     agreement_analyzer=my_agreement_analyzer
    # )


# ==============================================================================
# EXAMPLE 4: Refactored Maya script using the framework
# ==============================================================================

def maya_example():
    """Recreate the Maya feedback script using the framework."""

    # Load Maya outline
    outline_path = Path("data/ideation/development/maya_for_development.json")
    with open(outline_path, 'r') as f:
        maya_outline = json.load(f)

    # Define the prompt template
    def maya_prompt_template(outline_json):
        return f"""You are an experienced development editor and professional novelist who specializes in early readers chapter books for ages 9-10. You are also deeply familiar with writing decodable texts and the Science of Reading approach.

I am a highly successful novelist seeking your detailed, professional feedback and suggested changes for this chapter book outline titled "Maya's Story Reel."

Please provide thorough, specific, and actionable feedback as you would to a fellow professional author.

**BOOK OVERVIEW:**
- Target age: 9-10 years old
- Format: Early readers chapter book
- Word count: 11,000 words across 11 chapters
- Genre: Contemporary realistic fiction
- Primary theme: Self-awareness (for children)
- Secondary theme: Growth mindset (for families)
- Contemporary hook: Sora AI video generation

**OUTLINE:**
{outline_json}

**PLEASE PROVIDE:**

1. Overall Story Arc Assessment
2. Character Development
3. Decodable Text Concerns
4. Contemporary Hook Effectiveness
5. Dialogue and Voice
6. Educational Message
7. Specific Chapter-by-Chapter Feedback
8. Suggested Changes
9. Target Audience Concerns
10. Overall Recommendations
11. Revised Chapter-by-Chapter Outline (complete JSON incorporating your changes)

Please be thorough, honest, and specific. Your response must conclude with the complete revised outline in valid JSON format under "## REVISED OUTLINE (JSON)"."""

    # Get feedback
    results = get_multi_model_feedback(
        content=maya_outline,
        prompt_template=maya_prompt_template,
        models=[
            "xai/grok-4-latest",
            "gemini/gemini-2.5-pro",
            "openai/gpt-4o",
            "anthropic/claude-sonnet-4-5-20250929"
        ],
        output_dir="data/ideation/development",
        content_name="maya_story_reel",
        collate=True,
        temperature=0.7,
        max_tokens=16000
    )

    print(f"\nFeedback collection complete!")
    print(f"Successful: {len(results['feedback_results']['successful_feedback'])}")
    print(f"Failed: {len(results['feedback_results']['failed_models'])}")
    if results.get('collated_report_path'):
        print(f"Collated report: {results['collated_report_path']}")


if __name__ == "__main__":
    print("Multi-Model Feedback Framework Examples\n")
    print("="*80)

    # Run the examples
    # example_simple_usage()
    # example_advanced_usage()
    # maya_example()

    print("\nUncomment the example you want to run!")
