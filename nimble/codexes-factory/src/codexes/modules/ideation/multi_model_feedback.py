#!/usr/bin/env python3
"""
Multi-Model Feedback Framework

A generalized system for:
1. Submitting content to multiple AI models for professional feedback
2. Collecting their responses and recommended revisions
3. Collating feedback section-by-section with agreement analysis

Usage:
    from codexes.modules.ideation.multi_model_feedback import MultiModelReviewer

    reviewer = MultiModelReviewer(
        models=["xai/grok-4-latest", "gemini/gemini-2.5-pro", "openai/gpt-4o"],
        output_dir="./feedback_output"
    )

    results = reviewer.get_feedback(
        content=my_content,
        prompt_template=my_prompt_template,
        content_name="my_document"
    )

    collated_report = reviewer.collate_feedback(results)
"""

import json
import litellm
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import re
from datetime import datetime

# Configure litellm
litellm.telemetry = False


class MultiModelReviewer:
    """
    Framework for collecting and collating feedback from multiple AI models.
    """

    def __init__(
        self,
        models: List[str],
        output_dir: str | Path,
        temperature: float = 0.7,
        max_tokens: int = 16000,
        verbose: bool = True
    ):
        """
        Initialize the multi-model reviewer.

        Args:
            models: List of model identifiers (e.g., ["xai/grok-4-latest", "gemini/gemini-2.5-pro"])
            output_dir: Directory to save feedback files
            temperature: Temperature for model responses (note: some models may override)
            max_tokens: Maximum tokens for responses
            verbose: Whether to print progress
        """
        self.models = models
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.verbose = verbose

    def create_prompt(
        self,
        content: Any,
        prompt_template: str | Callable,
        **template_kwargs
    ) -> str:
        """
        Create the prompt for models.

        Args:
            content: The content to review (dict, str, etc.)
            prompt_template: Either a string template with {content} placeholder
                           or a callable that takes content and returns prompt
            **template_kwargs: Additional kwargs for template formatting

        Returns:
            Formatted prompt string
        """
        # Convert content to string if needed
        if isinstance(content, dict):
            content_str = json.dumps(content, indent=2)
        elif isinstance(content, (list, tuple)):
            content_str = json.dumps(content, indent=2)
        else:
            content_str = str(content)

        # Apply template
        if callable(prompt_template):
            return prompt_template(content_str, **template_kwargs)
        else:
            return prompt_template.format(content=content_str, **template_kwargs)

    def get_feedback_from_model(
        self,
        model_name: str,
        prompt: str,
        content_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get feedback from a single model.

        Args:
            model_name: Model identifier
            prompt: The prompt to send
            content_name: Name for saving output files

        Returns:
            Dict with model, content, filepath, error (if any)
        """
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"Requesting feedback from: {model_name}")
            print(f"{'='*80}\n")

        try:
            # Handle model-specific temperature constraints
            temperature = self.temperature
            if "gpt-5" in model_name.lower():
                temperature = 1.0  # GPT-5 only supports temperature=1

            response = litellm.completion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=self.max_tokens
            )

            feedback = response.choices[0].message.content

            # Save to file
            model_safe_name = model_name.replace('/', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"{content_name}_feedback_{model_safe_name}.md"
            output_path = self.output_dir / output_filename

            with open(output_path, 'w') as f:
                f.write(f"# Feedback for {content_name}\n\n")
                f.write(f"**Model:** {model_name}\n")
                f.write(f"**Generated:** {timestamp}\n\n")
                f.write("---\n\n")
                f.write(feedback)

            if self.verbose:
                print(f"✓ Saved feedback to: {output_path}\n")

            return {
                'model': model_name,
                'content': feedback,
                'filepath': str(output_path),
                'error': None
            }

        except Exception as e:
            if self.verbose:
                print(f"✗ Error getting feedback from {model_name}: {str(e)}\n")

            return {
                'model': model_name,
                'content': None,
                'filepath': None,
                'error': str(e)
            }

    def get_feedback(
        self,
        content: Any,
        prompt_template: str | Callable,
        content_name: str,
        **template_kwargs
    ) -> Dict[str, Any]:
        """
        Get feedback from all configured models.

        Args:
            content: The content to review
            prompt_template: Template for the prompt
            content_name: Name for output files
            **template_kwargs: Additional template arguments

        Returns:
            Dict with successful_feedback, failed_models, summary_path
        """
        # Create the prompt
        prompt = self.create_prompt(content, prompt_template, **template_kwargs)

        # Collect feedback from all models
        results = []
        for model in self.models:
            result = self.get_feedback_from_model(model, prompt, content_name)
            results.append(result)

        # Separate successful and failed
        successful = [r for r in results if r['error'] is None]
        failed = [r for r in results if r['error'] is not None]

        # Create summary file
        summary_path = self.output_dir / f"{content_name}_feedback_summary.md"
        with open(summary_path, 'w') as f:
            f.write(f"# Feedback Summary: {content_name}\n\n")
            f.write(f"**Models Consulted:** {len(successful)}/{len(self.models)}\n\n")

            if successful:
                f.write("## Successful Responses\n\n")
                for r in successful:
                    f.write(f"### {r['model']}\n\n")
                    f.write(f"See: `{Path(r['filepath']).name}`\n\n")

            if failed:
                f.write("## Failed Responses\n\n")
                for r in failed:
                    f.write(f"### {r['model']}\n\n")
                    f.write(f"Error: {r['error']}\n\n")

        if self.verbose:
            print(f"\n{'='*80}")
            print(f"COMPLETE: Collected feedback from {len(successful)}/{len(self.models)} models")
            print(f"Summary saved to: {summary_path}")
            print(f"{'='*80}\n")

        return {
            'successful_feedback': successful,
            'failed_models': failed,
            'summary_path': str(summary_path),
            'content_name': content_name
        }

    def collate_feedback(
        self,
        feedback_results: Dict[str, Any],
        section_patterns: Optional[List[tuple]] = None,
        agreement_analyzer: Optional[Callable] = None
    ) -> str:
        """
        Collate feedback section by section with agreement analysis.

        Args:
            feedback_results: Results from get_feedback()
            section_patterns: List of (regex_pattern, section_name) tuples
                            If None, uses default patterns
            agreement_analyzer: Custom function to analyze agreement
                              If None, uses default analyzer

        Returns:
            Path to collated report
        """
        successful = feedback_results['successful_feedback']
        content_name = feedback_results['content_name']

        if not successful:
            if self.verbose:
                print("No successful feedback to collate.")
            return None

        # Default section patterns
        if section_patterns is None:
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
                (r'##?\s*11[\.\)]\s*\*?\*?Revised.*?Outline\*?\*?', 'Revised Outline'),
            ]

        # Default agreement analyzer
        if agreement_analyzer is None:
            agreement_analyzer = self._default_agreement_analyzer

        # Extract sections from all feedback
        collated = {}
        for feedback in successful:
            model = feedback['model']
            content = feedback['content']

            for pattern, section_name in section_patterns:
                if section_name not in collated:
                    collated[section_name] = []

                # Find section content
                match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if match:
                    start_pos = match.end()

                    # Find next section or end
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

        # Create collated report
        report = self._create_collated_report(
            collated,
            content_name,
            successful,
            agreement_analyzer
        )

        # Save report
        output_path = self.output_dir / f"{content_name}_feedback_collated.md"
        with open(output_path, 'w') as f:
            f.write(report)

        if self.verbose:
            print(f"\n✓ Collated report saved to: {output_path}")
            print(f"\nSections collated: {len(collated)}")
            for section_name, contents in collated.items():
                print(f"  - {section_name}: {len(contents)} models")

        return str(output_path)

    def _default_agreement_analyzer(self, section_contents: List[Dict]) -> str:
        """Default agreement analysis logic."""
        if not section_contents:
            return "No feedback available for this section."

        if len(section_contents) == 1:
            return "Only one model provided feedback for this section."

        all_text = " ".join([item['content'].lower() for item in section_contents])

        # Agreement indicators
        strong_indicators = ['strong', 'excellent', 'effective', 'well', 'good', 'compelling']
        weak_indicators = ['weak', 'poor', 'lacking', 'needs improvement', 'problematic', 'concern']

        strong_count = sum(1 for word in strong_indicators if word in all_text)
        weak_count = sum(1 for word in weak_indicators if word in all_text)

        total = strong_count + weak_count

        if total == 0:
            return "**Consensus:** Models focused on technical/structural feedback rather than evaluative assessments."

        if strong_count > weak_count * 2:
            return "**Strong Consensus:** Models generally agree this element is well-executed."
        elif weak_count > strong_count * 2:
            return "**Strong Consensus:** Models generally agree this element needs significant improvement."
        elif abs(strong_count - weak_count) <= 1:
            return "**Mixed Reviews:** Models have divergent opinions on this element's effectiveness."
        else:
            return "**Moderate Agreement:** Models show some variation but tend toward similar assessments."

    def _create_collated_report(
        self,
        collated_sections: Dict,
        content_name: str,
        successful_feedback: List[Dict],
        agreement_analyzer: Callable
    ) -> str:
        """Create the collated report."""

        report = f"""# Collated Professional Feedback: {content_name}

## Executive Summary

This document collates professional feedback from multiple AI models, organizing their analysis section by section for easy comparison. Each section concludes with a consensus analysis showing the degree of agreement among the models.

**Models Consulted:**
"""

        for i, feedback in enumerate(successful_feedback, 1):
            report += f"{i}. {feedback['model']}\n"

        report += "\n---\n\n"

        # Add each section
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
            report += agreement_analyzer(contents) + "\n\n"
            report += "---\n\n"

        return report


# Convenience function for quick usage
def get_multi_model_feedback(
    content: Any,
    prompt_template: str | Callable,
    models: List[str],
    output_dir: str | Path,
    content_name: str,
    collate: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to get and optionally collate multi-model feedback.

    Args:
        content: Content to review
        prompt_template: Prompt template (string with {content} or callable)
        models: List of model identifiers
        output_dir: Output directory
        content_name: Name for output files
        collate: Whether to create collated report
        **kwargs: Additional arguments (temperature, max_tokens, etc.)

    Returns:
        Dict with feedback_results and (optionally) collated_report_path
    """
    reviewer = MultiModelReviewer(models=models, output_dir=output_dir, **kwargs)

    results = reviewer.get_feedback(
        content=content,
        prompt_template=prompt_template,
        content_name=content_name
    )

    output = {'feedback_results': results}

    if collate and results['successful_feedback']:
        collated_path = reviewer.collate_feedback(results)
        output['collated_report_path'] = collated_path

    return output
