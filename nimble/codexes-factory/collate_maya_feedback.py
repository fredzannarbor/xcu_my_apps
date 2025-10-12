#!/usr/bin/env python3
"""
Script to collate Maya feedback from multiple AI models section by section.
"""

from pathlib import Path
import re

def read_feedback_file(filepath):
    """Read and parse a feedback file."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Extract model name from filename or content
    filename = Path(filepath).stem
    model_name = filename.replace('maya_feedback_', '').replace('_', '/')

    return {
        'model': model_name,
        'content': content,
        'filepath': filepath
    }

def extract_sections(feedback_list):
    """Extract sections from all feedback files."""

    # Section patterns to look for
    section_patterns = [
        (r'##?\s*1[\.\)]\s*\*?\*?Overall Story Arc Assessment\*?\*?', 'Overall Story Arc Assessment'),
        (r'##?\s*2[\.\)]\s*\*?\*?Character Development\*?\*?', 'Character Development'),
        (r'##?\s*3[\.\)]\s*\*?\*?Decodable Text Concerns\*?\*?', 'Decodable Text Concerns'),
        (r'##?\s*4[\.\)]\s*\*?\*?Contemporary Hook Effectiveness\*?\*?', 'Contemporary Hook Effectiveness'),
        (r'##?\s*5[\.\)]\s*\*?\*?Dialogue and Voice\*?\*?', 'Dialogue and Voice'),
        (r'##?\s*6[\.\)]\s*\*?\*?Educational Message\*?\*?', 'Educational Message'),
        (r'##?\s*7[\.\)]\s*\*?\*?Specific Chapter-by-Chapter Feedback\*?\*?', 'Chapter-by-Chapter Feedback'),
        (r'##?\s*8[\.\)]\s*\*?\*?Suggested Changes\*?\*?', 'Suggested Changes'),
        (r'##?\s*9[\.\)]\s*\*?\*?Target Audience Concerns\*?\*?', 'Target Audience Concerns'),
        (r'##?\s*10[\.\)]\s*\*?\*?Overall Recommendations\*?\*?', 'Overall Recommendations'),
        (r'##?\s*11[\.\)]\s*\*?\*?Revised Chapter-by-Chapter Outline\*?\*?', 'Revised Outline'),
    ]

    collated = {}

    for feedback in feedback_list:
        model = feedback['model']
        content = feedback['content']

        for pattern, section_name in section_patterns:
            if section_name not in collated:
                collated[section_name] = []

            # Find section content
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                start_pos = match.end()

                # Find the next section or end of content
                next_section_pattern = r'\n##?\s*\d+[\.\)]'
                next_match = re.search(next_section_pattern, content[start_pos:], re.MULTILINE)

                if next_match:
                    end_pos = start_pos + next_match.start()
                else:
                    end_pos = len(content)

                section_content = content[start_pos:end_pos].strip()

                collated[section_name].append({
                    'model': model,
                    'content': section_content
                })

    return collated

def analyze_agreement(section_contents):
    """Analyze degree of agreement among models for a section."""
    if not section_contents:
        return "No feedback available for this section."

    if len(section_contents) == 1:
        return "Only one model provided feedback for this section."

    # Extract key themes/points from each model
    # This is a simplified analysis - could be enhanced with NLP

    all_text = " ".join([item['content'].lower() for item in section_contents])

    # Check for agreement indicators
    strong_indicators = ['strong', 'excellent', 'effective', 'well', 'good', 'compelling']
    weak_indicators = ['weak', 'poor', 'lacking', 'needs improvement', 'problematic', 'concern']
    neutral_indicators = ['adequate', 'okay', 'reasonable', 'mixed']

    strong_count = sum(1 for word in strong_indicators if word in all_text)
    weak_count = sum(1 for word in weak_indicators if word in all_text)
    neutral_count = sum(1 for word in neutral_indicators if word in all_text)

    total = strong_count + weak_count + neutral_count

    if total == 0:
        return "**Consensus:** Models focused on technical/structural feedback rather than evaluative assessments."

    # Determine agreement
    if strong_count > weak_count * 2:
        agreement = "**Strong Consensus:** Models generally agree this element is well-executed."
    elif weak_count > strong_count * 2:
        agreement = "**Strong Consensus:** Models generally agree this element needs significant improvement."
    elif abs(strong_count - weak_count) <= 1:
        agreement = "**Mixed Reviews:** Models have divergent opinions on this element's effectiveness."
    else:
        agreement = "**Moderate Agreement:** Models show some variation but tend toward similar assessments."

    return agreement

def create_collated_report(collated_sections):
    """Create the collated report with agreement analysis."""

    report = """# Maya's Story Reel: Collated Professional Feedback

## Executive Summary

This document collates development editing feedback from five professional AI models, organizing their analysis section by section for easy comparison. Each section concludes with a consensus analysis showing the degree of agreement among the models.

**Models Consulted:**
1. Gemini 2.0 Flash (gemini/gemini-2.0-flash-exp)
2. GPT-4o (openai/gpt-4o)
3. Claude 3.7 Sonnet (anthropic/claude-3-7-sonnet-20250219)
4. Grok 4 (xai/grok-4-latest)
5. Gemini 2.5 Pro (gemini/gemini-2.5-pro)

---

"""

    # Add each section with model feedback and agreement analysis
    for section_name, contents in collated_sections.items():
        report += f"\n## {section_name}\n\n"

        if not contents:
            report += "*No feedback provided for this section.*\n\n"
            continue

        # Add each model's feedback
        for item in contents:
            report += f"### {item['model']}\n\n"
            report += item['content'] + "\n\n"

        # Add agreement analysis
        report += "### Agreement Analysis\n\n"
        report += analyze_agreement(contents) + "\n\n"
        report += "---\n\n"

    return report

def main():
    """Main execution."""

    # Path to feedback files
    feedback_dir = Path(__file__).parent / "data" / "ideation" / "development"

    # Get all feedback files (excluding summary)
    feedback_files = [
        f for f in feedback_dir.glob("maya_feedback_*.md")
        if f.stem != "maya_feedback_summary"
    ]

    print(f"Found {len(feedback_files)} feedback files:")
    for f in feedback_files:
        print(f"  - {f.name}")

    # Read all feedback
    feedback_list = [read_feedback_file(f) for f in feedback_files]

    # Extract and collate sections
    print("\nExtracting sections...")
    collated = extract_sections(feedback_list)

    # Create collated report
    print("Creating collated report...")
    report = create_collated_report(collated)

    # Save report
    output_path = feedback_dir / "maya_feedback_collated.md"
    with open(output_path, 'w') as f:
        f.write(report)

    print(f"\n✓ Collated report saved to: {output_path}")
    print(f"\nSections collated: {len(collated)}")
    for section_name, contents in collated.items():
        print(f"  - {section_name}: {len(contents)} models")

if __name__ == "__main__":
    main()
