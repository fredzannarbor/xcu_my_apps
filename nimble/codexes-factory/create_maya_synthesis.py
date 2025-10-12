#!/usr/bin/env python3
"""
Create a concise synthesis of Maya feedback focusing on key agreements and disagreements.
"""

from pathlib import Path
import re
from collections import defaultdict

def read_feedback_file(filepath):
    """Read and parse a feedback file."""
    with open(filepath, 'r') as f:
        content = f.read()

    filename = Path(filepath).stem
    model_name = filename.replace('maya_feedback_', '').replace('_', '/')

    return {
        'model': model_name,
        'content': content,
        'filepath': filepath
    }

def extract_sections(feedback_list):
    """Extract sections from all feedback files."""

    # These match ### headings
    section_patterns = [
        (r'###\s*1[\.\)]\s*Overall Story Arc Assessment', 'Overall Story Arc Assessment'),
        (r'###\s*2[\.\)]\s*Character Development', 'Character Development'),
        (r'###\s*3[\.\)]\s*Decodable Text Concerns', 'Decodable Text Concerns'),
        (r'###\s*4[\.\)]\s*Contemporary Hook Effectiveness', 'Contemporary Hook Effectiveness'),
        (r'###\s*5[\.\)]\s*Dialogue and Voice', 'Dialogue and Voice'),
        (r'###\s*6[\.\)]\s*Educational Message', 'Educational Message'),
        (r'###\s*7[\.\)]\s*Specific Chapter-by-Chapter Feedback', 'Chapter-by-Chapter Feedback'),
        (r'###\s*8[\.\)]\s*Suggested Changes', 'Suggested Changes'),
        (r'###\s*9[\.\)]\s*Target Audience Concerns', 'Target Audience Concerns'),
        (r'###\s*10[\.\)]\s*Overall Recommendations', 'Overall Recommendations'),
    ]

    collated = {}

    for feedback in feedback_list:
        model = feedback['model']
        content = feedback['content']

        for pattern, section_name in section_patterns:
            if section_name not in collated:
                collated[section_name] = []

            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                start_pos = match.end()
                # Find next ### heading
                next_section_pattern = r'\n###\s*\d+[\.\)]'
                next_match = re.search(next_section_pattern, content[start_pos:], re.MULTILINE)

                if next_match:
                    end_pos = start_pos + next_match.start()
                else:
                    # Check for ## REVISED OUTLINE
                    revised_pattern = r'\n## REVISED OUTLINE'
                    revised_match = re.search(revised_pattern, content[start_pos:], re.IGNORECASE)
                    if revised_match:
                        end_pos = start_pos + revised_match.start()
                    else:
                        end_pos = len(content)

                section_content = content[start_pos:end_pos].strip()

                collated[section_name].append({
                    'model': model,
                    'content': section_content
                })

    return collated

def analyze_section_consensus(section_name, section_contents):
    """Analyze a section for agreements and disagreements."""

    if not section_contents:
        return None

    all_text = " ".join([item['content'].lower() for item in section_contents])

    # Extract bullet points and sub-questions from all models
    points = defaultdict(list)

    for item in section_contents:
        content = item['content']
        model = item['model']

        # Find bullet points or numbered items
        bullets = re.findall(r'[-\*]\s*\*?\*?([^\n]+)', content)
        for bullet in bullets:
            clean = bullet.strip().rstrip('*').strip()
            if len(clean) > 20:  # Meaningful content
                points[clean[:80]].append({'model': model, 'text': clean})

        # Find questions and answers
        questions = re.findall(r'\*\*([^*]+\?)\*\*\s+([^\n]+)', content)
        for q, a in questions:
            key = q.strip()[:60]
            points[key].append({'model': model, 'text': a.strip()})

    # Identify common themes
    theme_keywords = {
        'pacing': ['pacing', 'rushed', 'slow', 'repetitive'],
        'character_depth': ['character', 'one-dimensional', 'dimensional', 'motivation', 'arc'],
        'thorne_villain': ['thorne', 'antagonist', 'villain'],
        'age_appropriate': ['age-appropriate', 'grade', 'level', '9-10'],
        'phonics': ['phonics', 'decodable', 'science of reading', 'sor'],
        'dialogue': ['dialogue', 'voice', 'authentic'],
        'literary_quotes': ['quotes', 'literary', 'angelou', 'morrison', 'woolf'],
        'stakes': ['stakes', 'tension', 'conflict'],
        'chapter_3': ['chapter 3', 'chapter 5'],
        'sora_ai': ['sora', 'ai', 'viral', 'views'],
    }

    theme_counts = {}
    theme_examples = defaultdict(list)

    for theme, keywords in theme_keywords.items():
        count = sum(all_text.count(kw) for kw in keywords)
        if count > 0:
            theme_counts[theme] = count
            # Extract a sample mention
            for item in section_contents:
                for kw in keywords:
                    if kw in item['content'].lower():
                        # Get sentence containing keyword
                        sentences = item['content'].split('.')
                        for sent in sentences:
                            if kw in sent.lower() and len(sent.strip()) > 20:
                                theme_examples[theme].append({
                                    'model': item['model'],
                                    'sample': sent.strip()[:200]
                                })
                                break
                        break

    # Sentiment analysis
    positive_words = ['strong', 'excellent', 'effective', 'well', 'good', 'compelling', 'engaging', 'authentic', 'appropriate', 'works well']
    negative_words = ['weak', 'poor', 'lacking', 'needs improvement', 'problematic', 'concern', 'rushed', 'slow', 'forced', 'one-dimensional']

    pos_count = sum(all_text.count(word) for word in positive_words)
    neg_count = sum(all_text.count(word) for word in negative_words)

    return {
        'model_count': len(section_contents),
        'theme_counts': theme_counts,
        'theme_examples': theme_examples,
        'positive_count': pos_count,
        'negative_count': neg_count,
        'raw_content': section_contents
    }

def format_section_synthesis(section_name, analysis):
    """Format the synthesis for a section."""

    if not analysis:
        return f"### {section_name}\n\n*No feedback for this section.*\n\n---\n\n"

    output = f"### {section_name}\n\n"
    output += f"**Feedback from {analysis['model_count']} models**\n\n"

    # Overall sentiment
    pos = analysis['positive_count']
    neg = analysis['negative_count']

    if pos > neg * 1.5:
        output += "**Consensus:** ✓ Generally positive\n\n"
    elif neg > pos * 1.5:
        output += "**Consensus:** ⚠ Needs significant work\n\n"
    else:
        output += "**Consensus:** ◐ Mixed - has strengths and weaknesses\n\n"

    # Top themes
    sorted_themes = sorted(analysis['theme_counts'].items(), key=lambda x: x[1], reverse=True)

    if sorted_themes:
        output += "**Key themes discussed:**\n"
        for theme, count in sorted_themes[:4]:  # Top 4 themes
            theme_label = theme.replace('_', ' ').title()
            output += f"- **{theme_label}**"

            # Add representative example
            if theme in analysis['theme_examples'] and analysis['theme_examples'][theme]:
                example = analysis['theme_examples'][theme][0]
                sample = example['sample']
                # Clean up sample
                if len(sample) > 150:
                    sample = sample[:150] + "..."
                output += f" — _{sample}_"

            output += "\n"
        output += "\n"

    # Extract specific agreements/disagreements
    all_models_agree = []
    some_disagree = []

    # Simple check: look for common sentence fragments
    for item in analysis['raw_content'][:1]:  # Check first model's points
        content_lower = item['content'].lower()
        # Find sentences with strong opinions
        sentences = item['content'].split('.')
        for sent in sentences:
            sent_lower = sent.lower()
            if any(word in sent_lower for word in ['yes', 'strong', 'effective', 'good', 'works well']) and len(sent) > 30:
                # Check if other models mention similar thing
                key_words = [w for w in sent.split() if len(w) > 6][:3]
                if key_words:
                    matches = sum(1 for other in analysis['raw_content']
                                 if any(kw.lower() in other['content'].lower() for kw in key_words))
                    if matches >= len(analysis['raw_content']) * 0.7:  # 70% agree
                        all_models_agree.append(sent.strip()[:180])

    if all_models_agree:
        output += "**Strong agreement points:**\n"
        for point in all_models_agree[:2]:
            output += f"- {point}\n"
        output += "\n"

    output += "---\n\n"

    return output

def create_synthesis_report(collated_sections):
    """Create the concise synthesis report."""

    report = """# Maya's Story Reel: Executive Synthesis of Professional Feedback

## Overview

This document provides a **concise synthesis** of development editing feedback from 5 AI models, focusing on key areas of agreement and disagreement.

**Models Consulted:**
1. Gemini 2.0 Flash (gemini/gemini-2.0-flash-exp)
2. GPT-4o (openai/gpt-4o)
3. Claude 3.7 Sonnet (anthropic/claude-3-7-sonnet-20250219)
4. Grok 4 (xai/grok-4-latest)
5. Gemini 2.5 Pro (gemini/gemini-2.5-pro)

**Legend:**
- ✓ = Generally positive consensus
- ⚠ = Needs significant improvement
- ◐ = Mixed reviews

---

## High-Level Cross-Cutting Themes

"""

    # Analyze all sections for common themes
    all_analyses = {}
    global_themes = defaultdict(int)

    for section_name, contents in collated_sections.items():
        analysis = analyze_section_consensus(section_name, contents)
        all_analyses[section_name] = analysis

        if analysis:
            for theme, count in analysis['theme_counts'].items():
                global_themes[theme] += count

    # Report top global themes
    sorted_global = sorted(global_themes.items(), key=lambda x: x[1], reverse=True)

    report += "**Most frequently discussed across ALL sections:**\n\n"
    for theme, count in sorted_global[:8]:
        theme_label = theme.replace('_', ' ').title()
        report += f"- **{theme_label}** ({count} mentions)\n"

    report += "\n---\n\n## Section-by-Section Analysis\n\n"

    # Add each section
    for section_name in collated_sections.keys():
        analysis = all_analyses.get(section_name)
        report += format_section_synthesis(section_name, analysis)

    # Add action items summary
    report += "## Suggested Action Items (Based on Consensus)\n\n"

    # Look for common recommendations across sections
    action_items = []

    # Check Suggested Changes section specifically
    if 'Suggested Changes' in all_analyses and all_analyses['Suggested Changes']:
        sc_analysis = all_analyses['Suggested Changes']
        top_themes = sorted(sc_analysis['theme_counts'].items(), key=lambda x: x[1], reverse=True)

        for theme, _ in top_themes[:5]:
            theme_label = theme.replace('_', ' ').title()
            action_items.append(f"Address {theme_label.lower()} concerns")

    # Add general action items based on global themes
    if 'thorne_villain' in global_themes and global_themes['thorne_villain'] > 10:
        action_items.append("Develop Dr. Thorne's character beyond one-dimensional villain")

    if 'literary_quotes' in global_themes and global_themes['literary_quotes'] > 8:
        action_items.append("Simplify or reduce literary quotes for age appropriateness")

    if 'pacing' in global_themes and global_themes['pacing'] > 8:
        action_items.append("Address pacing issues, particularly in Chapters 3-5")

    if action_items:
        for i, item in enumerate(action_items[:8], 1):
            report += f"{i}. {item}\n"
    else:
        report += "*See individual section feedback for specific recommendations.*\n"

    report += "\n---\n\n"
    report += "*For detailed feedback from each model, see the full collated report: `maya_feedback_collated.md`*\n"

    return report

def main():
    """Main execution."""

    feedback_dir = Path(__file__).parent / "data" / "ideation" / "development"

    # Get all feedback files (excluding summary and collated)
    feedback_files = [
        f for f in feedback_dir.glob("maya_feedback_*.md")
        if f.stem not in ["maya_feedback_summary", "maya_feedback_collated", "maya_feedback_synthesis"]
    ]

    print(f"Found {len(feedback_files)} feedback files")

    # Read all feedback
    feedback_list = [read_feedback_file(f) for f in feedback_files]

    # Extract and collate sections
    print("Extracting sections...")
    collated = extract_sections(feedback_list)

    print(f"Extracted {len(collated)} sections")
    for section_name, contents in collated.items():
        print(f"  - {section_name}: {len(contents)} models")

    # Create synthesis report
    print("Creating synthesis report...")
    report = create_synthesis_report(collated)

    # Save report
    output_path = feedback_dir / "maya_feedback_synthesis.md"
    with open(output_path, 'w') as f:
        f.write(report)

    print(f"\n✓ Synthesis report saved to: {output_path}")
    print(f"  Report length: {len(report)} characters ({len(report.split())} words)")
    print(f"  Approximately {len(report.split()) // 250} pages")

if __name__ == "__main__":
    main()
