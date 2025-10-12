#!/usr/bin/env python3
"""
Script to get development editing feedback on Maya's Story Reel from multiple AI models.
Submits the chapter outline to xai/grok-beta, gemini/gemini-2.0-flash-exp,
openai/gpt-4o, and anthropic/claude-3-7-sonnet-20250219.
"""

import json
import litellm
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure litellm
litellm.telemetry = False
litellm.set_verbose = True

def load_outline():
    """Load the Maya outline JSON file."""
    outline_path = Path(__file__).parent / "data" / "ideation" / "development" / "maya_for_development.json"
    with open(outline_path, 'r') as f:
        return json.load(f)

def create_feedback_prompt(outline_data):
    """Create comprehensive development editing feedback prompt."""

    outline_json = json.dumps(outline_data, indent=2)

    prompt = f"""You are an experienced development editor and professional novelist who specializes in early readers chapter books for ages 9-10. You are also deeply familiar with writing decodable texts and the Science of Reading approach.

I am a highly successful novelist seeking your detailed, professional feedback and suggested changes for this chapter book outline titled "Maya's Story Reel."

Please provide thorough, specific, and actionable feedback as you would to a fellow professional author.

**BOOK OVERVIEW:**
- Target age: 9-10 years old
- Format: Early readers chapter book
- Word count: 11,000 words across 11 chapters (avg. 1,000 words/chapter)
- Genre: Contemporary realistic fiction
- Primary theme: Self-awareness (for children)
- Secondary theme: Growth mindset (for families)
- Contemporary hook: Sora AI video generation (POV storytelling)

**UNIQUE ELEMENTS:**
- Protagonist: Maya Chan, a 4th grader who struggles with reading but excels at creating viral Sora POV rescue videos
- AI companion: SoRogue, a "quirky young female science nerd AI" who quotes famous women writers and guides Maya toward literacy
- Educational integration: Science of Reading principles woven throughout
- Antagonist: Dr. Elias Thorne, a principal tracking rogue AIs like SoRogue

**OUTLINE:**
{outline_json}

**PLEASE PROVIDE:**

1. **Overall Story Arc Assessment**
   - Does the three-act structure work effectively for this age group?
   - Are the pacing and chapter lengths appropriate?
   - Does the conflict escalate naturally?

2. **Character Development**
   - Is Maya's character arc believable and age-appropriate?
   - Does SoRogue feel like an authentic ally without being preachy?
   - Is Dr. Thorne a compelling antagonist or too one-dimensional?
   - Are supporting characters (Mom, Ms. Albright) well-utilized?

3. **Decodable Text Concerns**
   - Are the phonics patterns introduced in logical progression?
   - Does the integration of Science of Reading feel organic or forced?
   - Are the "Phonics Rescue Reels" concepts clear and engaging?

4. **Contemporary Hook Effectiveness**
   - Does the Sora AI video generation feel authentic and current?
   - Will the viral view counts resonate with 9-10 year olds?
   - Is the tech integration balanced with traditional literacy themes?

5. **Dialogue and Voice**
   - Does Maya's voice feel authentic for a 4th grader?
   - Are the literary quotes from SoRogue age-appropriate and effective?
   - Is there enough "show" versus "tell" in the dialogue samples?

6. **Educational Message**
   - Is the growth mindset theme heavy-handed or well-integrated?
   - Does the book avoid stigmatizing reading struggles?
   - Will parents find the Science of Reading information helpful or overwhelming?

7. **Specific Chapter-by-Chapter Feedback**
   - Flag any chapters that feel rushed, slow, or unnecessary
   - Note plot holes or inconsistencies
   - Suggest specific improvements to plot beats or emotional arcs

8. **Suggested Changes**
   - What would you change, cut, or expand?
   - Are there missing scenes or emotional beats?
   - How can the antagonist subplot be strengthened?

9. **Target Audience Concerns**
   - Will 9-10 year olds find this engaging despite the literacy struggle theme?
   - Is the reading level appropriate (should aim for grade 4-5 complexity)?
   - Are there any potentially triggering or confusing elements?

10. **Overall Recommendations**
    - Rate the outline's readiness (1-10 scale)
    - What are the 3-5 most critical issues to address?
    - What are the strongest elements to preserve?

11. **Revised Chapter-by-Chapter Outline**
    - Provide a COMPLETE revised chapter-by-chapter outline in JSON format
    - Incorporate all your suggested changes and improvements
    - Maintain the same structure as the original (chapter_number, chapter_title, estimated_word_count, setting_details, characters_present, plot_summary, emotional_beats, skill_focus_integration, contemporary_hook_usage, dialogue_highlights, scene_breakdown, chapter_purpose, foreshadowing_elements, cliffhanger_or_transition)
    - Make sure your revised outline is actionable and ready for drafting

Please be thorough, honest, and specific. Use examples from the outline to illustrate your points.

IMPORTANT: Your response must conclude with the complete revised outline in valid JSON format, clearly marked with a heading "## REVISED OUTLINE (JSON)" followed by a code block containing the full JSON structure."""

    return prompt

def get_feedback_from_model(model_name, prompt, temperature=0.7):
    """Get feedback from a specific model."""
    print(f"\n{'='*80}")
    print(f"Requesting feedback from: {model_name}")
    print(f"{'='*80}\n")

    try:
        response = litellm.completion(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=16000  # Allow for comprehensive responses
        )

        feedback = response.choices[0].message.content

        # Save to file
        model_safe_name = model_name.replace('/', '_')
        output_path = Path(__file__).parent / "data" / "ideation" / "development" / f"maya_feedback_{model_safe_name}.md"

        with open(output_path, 'w') as f:
            f.write(f"# Development Editing Feedback for Maya's Story Reel\n\n")
            f.write(f"**Model:** {model_name}\n\n")
            f.write(f"**Generated:** {Path(__file__).name}\n\n")
            f.write("---\n\n")
            f.write(feedback)

        print(f"✓ Saved feedback to: {output_path}\n")
        return feedback

    except Exception as e:
        print(f"✗ Error getting feedback from {model_name}: {str(e)}\n")
        return None

def main():
    """Main execution function."""

    # Load the outline
    print("Loading Maya outline...")
    outline = load_outline()

    # Create the feedback prompt
    print("Creating feedback prompt...")
    prompt = create_feedback_prompt(outline)

    # Models to query (updated to latest versions)
    models = [
        "xai/grok-4-latest",  # Latest xAI Grok 4
        "gemini/gemini-2.5-pro",  # Gemini 2.5 Pro
        "openai/gpt-5",  # GPT-5
        "anthropic/claude-sonnet-4-5-20250929"  # Claude Sonnet 4.5
    ]

    # Collect all feedback
    all_feedback = {}

    for model in models:
        feedback = get_feedback_from_model(model, prompt)
        if feedback:
            all_feedback[model] = feedback

    # Create summary file
    summary_path = Path(__file__).parent / "data" / "ideation" / "development" / "maya_feedback_summary.md"
    with open(summary_path, 'w') as f:
        f.write("# Development Editing Feedback Summary\n\n")
        f.write("## Maya's Story Reel - Multi-Model Analysis\n\n")
        f.write(f"**Models Consulted:** {len(all_feedback)}/{len(models)}\n\n")

        for model, feedback in all_feedback.items():
            f.write(f"### {model}\n\n")
            f.write(f"See: `maya_feedback_{model.replace('/', '_')}.md`\n\n")

    print(f"\n{'='*80}")
    print(f"COMPLETE: Collected feedback from {len(all_feedback)}/{len(models)} models")
    print(f"Summary saved to: {summary_path}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
