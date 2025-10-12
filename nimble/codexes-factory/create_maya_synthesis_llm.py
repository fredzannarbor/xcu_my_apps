#!/usr/bin/env python3
"""
Create an LLM-powered synthesis of Maya feedback that intelligently identifies
agreements and disagreements across the models.
"""

from pathlib import Path
import litellm
import json

# Configure litellm
litellm.telemetry = False

def read_feedback_files():
    """Read all Maya feedback files."""
    feedback_dir = Path(__file__).parent / "data" / "ideation" / "development"

    feedback_files = [
        f for f in feedback_dir.glob("maya_feedback_*.md")
        if f.stem not in ["maya_feedback_summary", "maya_feedback_collated", "maya_feedback_synthesis"]
    ]

    feedbacks = []
    for filepath in feedback_files:
        with open(filepath, 'r') as f:
            content = f.read()

        filename = filepath.stem
        model_name = filename.replace('maya_feedback_', '').replace('_', '/')

        feedbacks.append({
            'model': model_name,
            'content': content
        })

    return feedbacks

def create_synthesis_with_llm(feedbacks):
    """Use an LLM to synthesize the feedback intelligently."""

    # Prepare the prompt for synthesis
    prompt = """You are an expert development editor analyzing feedback from multiple AI models on a children's book outline called "Maya's Story Reel."

Below are detailed feedback reports from 5 different AI models. Your task is to create a CONCISE executive synthesis (max 2500 words) that identifies:

1. **Cross-Cutting Themes**: What topics are most frequently discussed across ALL sections
2. **Strong Agreements**: Where do all or most models agree (both positive and negative)
3. **Key Disagreements**: Where do models have divergent opinions
4. **Actionable Recommendations**: Based on consensus, what are the top 5-7 changes to make

**FEEDBACK FROM MODELS:**

"""

    for i, fb in enumerate(feedbacks, 1):
        # Truncate very long feedback to fit in context
        content = fb['content']
        if len(content) > 20000:
            content = content[:20000] + "\n\n[... truncated for length ...]"

        prompt += f"""
---
## Model {i}: {fb['model']}

{content}

"""

    prompt += """

---

**YOUR SYNTHESIS** (max 2500 words):

Create a markdown document with the following structure:

# Maya's Story Reel: Executive Synthesis

## Overview
Brief intro about what this synthesis covers.

## Cross-Cutting Themes
List the 5-7 most frequently discussed topics across ALL feedback, with:
- Theme name
- How many models mentioned it
- Brief summary of consensus (positive/negative/mixed)

## Strong Agreements

### What's Working Well
List 3-5 elements that most/all models praised

### What Needs Significant Work
List 3-5 elements that most/all models flagged as needing improvement

## Key Disagreements
List 2-3 areas where models had divergent opinions and briefly explain the different viewpoints

## Top Priority Action Items
Based on consensus, provide 5-7 specific, actionable recommendations ranked by importance

## Nuanced Insights
2-3 thoughtful observations that emerged from comparing all the feedback

---

Be CONCISE. Focus on synthesis, not repetition. Cite which models said what when relevant (e.g., "3 of 5 models noted..." or "Grok and Claude both emphasized...").
"""

    print("Generating LLM-powered synthesis...")
    print(f"Prompt length: {len(prompt)} characters")

    try:
        response = litellm.completion(
            model="anthropic/claude-sonnet-4-5-20250929",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Lower temperature for more focused synthesis
            max_tokens=8000
        )

        synthesis = response.choices[0].message.content
        return synthesis

    except Exception as e:
        print(f"Error generating synthesis: {e}")
        return None

def main():
    """Main execution."""

    print("Reading feedback files...")
    feedbacks = read_feedback_files()

    print(f"Found {len(feedbacks)} feedback files")
    for fb in feedbacks:
        print(f"  - {fb['model']}: {len(fb['content'])} characters")

    # Generate synthesis
    synthesis = create_synthesis_with_llm(feedbacks)

    if synthesis:
        # Save synthesis
        output_dir = Path(__file__).parent / "data" / "ideation" / "development"
        output_path = output_dir / "maya_feedback_synthesis.md"

        with open(output_path, 'w') as f:
            f.write(synthesis)

        print(f"\n✓ LLM-powered synthesis saved to: {output_path}")
        print(f"  Length: {len(synthesis)} characters ({len(synthesis.split())} words)")
        print(f"  Approximately {len(synthesis.split()) // 250} pages")
    else:
        print("\n✗ Failed to generate synthesis")

if __name__ == "__main__":
    main()
