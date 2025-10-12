#!/usr/bin/env python3
"""
Analyze Maya reader panel results and generate improvement recommendations.

This script:
1. Loads results from all panels
2. Has each panel make recommendations for improvement
3. Compares results across panels
4. Identifies intersections and conflicts
5. Generates synthesis report
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from collections import Counter, defaultdict

try:
    from codexes.core.llm_integration import LLMCaller
except ModuleNotFoundError:
    from src.codexes.core.llm_integration import LLMCaller

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_panel_results(output_dir: Path) -> Dict[str, Dict]:
    """Load the most recent results from each panel."""
    panels = {}

    panel_names = ['children_9_10', 'parents', 'reading_experts', 'purchasing']

    for panel_name in panel_names:
        pattern = f"{panel_name}_feedback_*.json"
        files = list(output_dir.glob(pattern))

        if files:
            # Get most recent file
            latest_file = max(files, key=lambda p: p.stat().st_mtime)

            with open(latest_file) as f:
                panels[panel_name] = json.load(f)
                logger.info(f"Loaded {panel_name}: {panels[panel_name]['total_reviews']} reviews")

    return panels


def get_panel_recommendations(panel_name: str, panel_data: Dict,
                             llm_caller: LLMCaller,
                             model: str = "ollama/deepseek-r1") -> Dict[str, Any]:
    """Have a panel analyze its results and make recommendations."""

    # Extract feedback summaries
    feedback_items = panel_data.get('feedback', [])
    stats = panel_data.get('statistics', {})

    # Create summary for the panel
    concerns_list = []
    recommendations_list = []

    for item in feedback_items:
        concerns_list.extend(item.get('concerns', []))
        recommendations_list.extend(item.get('recommendations', []))

    # Count most common themes
    concern_counts = Counter(concerns_list)
    rec_counts = Counter(recommendations_list)

    prompt = f"""You are analyzing reader feedback for a children's book called "Maya's Story Reel."
This feedback comes from the {panel_name.replace('_', ' ').title()} panel.

PANEL STATISTICS:
- Total Reviews: {stats.get('total_reviews', 0)}
- Average Overall Rating: {stats.get('avg_overall_rating', 0)}/10
- Average Market Appeal: {stats.get('avg_market_appeal', 0)}/10
- Average Genre Fit: {stats.get('avg_genre_fit', 0)}/10
- Average Audience Alignment: {stats.get('avg_audience_alignment', 0)}/10

TOP CONCERNS (from {panel_name.replace('_', ' ').title()}):
{chr(10).join(f'- {concern} (mentioned {count}x)' for concern, count in concern_counts.most_common(10))}

TOP RECOMMENDATIONS (from {panel_name.replace('_', ' ').title()}):
{chr(10).join(f'- {rec} (mentioned {count}x)' for rec, count in rec_counts.most_common(10))}

SAMPLE DETAILED FEEDBACK:
{chr(10).join(f'- {item.get("detailed_feedback", "")[:200]}...' for item in feedback_items[:3])}

Based on this {panel_name.replace('_', ' ').title()} feedback, provide:

1. **Top 5 Priority Improvements** - What should be changed/improved first?
2. **Strengths to Preserve** - What's working well that should be kept?
3. **Target Audience Insights** - How well does this serve the {panel_name.replace('_', ' ').title()}?
4. **Specific Concerns** - What are the main issues from this panel's perspective?

Format your response as JSON:
{{
    "panel_name": "{panel_name}",
    "priority_improvements": ["improvement 1", "improvement 2", ...],
    "strengths": ["strength 1", "strength 2", ...],
    "target_audience_insights": "insight text",
    "specific_concerns": ["concern 1", "concern 2", ...],
    "overall_recommendation": "accept/revise/reject with explanation"
}}
"""

    try:
        response = llm_caller.call_llm(
            prompt=prompt,
            model=model,
            temperature=0.3,
            max_tokens=2000
        )

        # Try to parse JSON response
        try:
            recommendations = json.loads(response)
        except json.JSONDecodeError:
            # Fallback: extract from text
            recommendations = {
                "panel_name": panel_name,
                "priority_improvements": extract_list_from_text(response, "priority improvements"),
                "strengths": extract_list_from_text(response, "strengths"),
                "target_audience_insights": response[:500],
                "specific_concerns": list(concern_counts.most_common(5)),
                "overall_recommendation": "revise - see details"
            }

        return recommendations

    except Exception as e:
        logger.error(f"Error getting recommendations for {panel_name}: {e}")
        return {
            "panel_name": panel_name,
            "error": str(e),
            "priority_improvements": [],
            "strengths": [],
            "specific_concerns": [],
            "overall_recommendation": "error in analysis"
        }


def extract_list_from_text(text: str, section_name: str) -> List[str]:
    """Simple extraction of list items from text."""
    items = []
    in_section = False

    for line in text.split('\n'):
        if section_name.lower() in line.lower():
            in_section = True
            continue

        if in_section:
            line = line.strip()
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                items.append(line.lstrip('-•* '))
            elif line.startswith(('1.', '2.', '3.', '4.', '5.')):
                items.append(line.split('.', 1)[1].strip())
            elif not line:
                break

    return items[:5]  # Top 5


def compare_panels(all_recommendations: Dict[str, Dict]) -> Dict[str, Any]:
    """Compare recommendations across all panels."""

    # Collect all improvements and concerns
    all_improvements = defaultdict(list)  # improvement -> [panels that mentioned it]
    all_concerns = defaultdict(list)
    all_strengths = defaultdict(list)

    for panel_name, recs in all_recommendations.items():
        for imp in recs.get('priority_improvements', []):
            all_improvements[imp.lower()].append(panel_name)

        for concern in recs.get('specific_concerns', []):
            concern_text = concern if isinstance(concern, str) else concern[0]
            all_concerns[concern_text.lower()].append(panel_name)

        for strength in recs.get('strengths', []):
            all_strengths[strength.lower()].append(panel_name)

    # Find intersections (mentioned by multiple panels)
    intersections = {
        'improvements': {k: v for k, v in all_improvements.items() if len(v) >= 2},
        'concerns': {k: v for k, v in all_concerns.items() if len(v) >= 2},
        'strengths': {k: v for k, v in all_strengths.items() if len(v) >= 2}
    }

    # Find conflicts (different panels want different things)
    conflicts = []

    # Example: Kids vs Experts priorities
    kids_improvements = set(imp.lower() for imp in all_recommendations.get('children_9_10', {}).get('priority_improvements', []))
    expert_improvements = set(imp.lower() for imp in all_recommendations.get('reading_experts', {}).get('priority_improvements', []))

    unique_to_kids = kids_improvements - expert_improvements
    unique_to_experts = expert_improvements - kids_improvements

    if unique_to_kids and unique_to_experts:
        conflicts.append({
            'type': 'priority_mismatch',
            'panels': ['children_9_10', 'reading_experts'],
            'description': 'Different priorities between target readers and experts',
            'details': {
                'children_priority': list(unique_to_kids)[:3],
                'expert_priority': list(unique_to_experts)[:3]
            }
        })

    # Parents vs Purchasing
    parent_concerns = set(str(c).lower() for c in all_recommendations.get('parents', {}).get('specific_concerns', []))
    purchasing_concerns = set(str(c).lower() for c in all_recommendations.get('purchasing', {}).get('specific_concerns', []))

    unique_to_parents = parent_concerns - purchasing_concerns
    unique_to_purchasing = purchasing_concerns - parent_concerns

    if unique_to_parents and unique_to_purchasing:
        conflicts.append({
            'type': 'concern_divergence',
            'panels': ['parents', 'purchasing'],
            'description': 'Different concerns between parents and decision makers',
            'details': {
                'parent_concerns': list(unique_to_parents)[:3],
                'purchasing_concerns': list(unique_to_purchasing)[:3]
            }
        })

    return {
        'intersections': intersections,
        'conflicts': conflicts,
        'consensus_improvements': [k for k, v in all_improvements.items() if len(v) >= 3],
        'universal_strengths': [k for k, v in all_strengths.items() if len(v) >= 3],
        'critical_concerns': [k for k, v in all_concerns.items() if len(v) >= 3]
    }


def synthesize_final_recommendations(all_recommendations: Dict, comparison: Dict,
                                    llm_caller: LLMCaller,
                                    model: str = "ollama/deepseek-r1") -> str:
    """Create final synthesis using AI."""

    prompt = f"""You are synthesizing feedback from 4 different reader panels for "Maya's Story Reel":
1. Children (ages 9-10) - the target readers
2. Parents - who buy books for their children
3. Reading Experts - educators and specialists
4. School Purchasing - administrators and decision makers

CONSENSUS IMPROVEMENTS (mentioned by 3+ panels):
{chr(10).join(f'- {item}' for item in comparison['consensus_improvements'])}

UNIVERSAL STRENGTHS (mentioned by 3+ panels):
{chr(10).join(f'- {item}' for item in comparison['universal_strengths'])}

CRITICAL CONCERNS (mentioned by 3+ panels):
{chr(10).join(f'- {item}' for item in comparison['critical_concerns'])}

IDENTIFIED CONFLICTS:
{json.dumps(comparison['conflicts'], indent=2)}

PANEL-SPECIFIC RECOMMENDATIONS:
{json.dumps({k: v.get('priority_improvements', [])[:3] for k, v in all_recommendations.items()}, indent=2)}

Create a FINAL SYNTHESIS REPORT that:
1. Prioritizes improvements that satisfy multiple stakeholders
2. Resolves conflicts by finding win-win solutions
3. Preserves what all groups value
4. Addresses critical concerns systematically
5. Provides an action plan with priorities

Be specific and actionable. Format as markdown.
"""

    try:
        synthesis = llm_caller.call_llm(
            prompt=prompt,
            model=model,
            temperature=0.5,
            max_tokens=3000
        )

        return synthesis

    except Exception as e:
        logger.error(f"Error in synthesis: {e}")
        return f"Error generating synthesis: {e}"


def main():
    """Main analysis workflow."""
    logger.info("="*80)
    logger.info("MAYA'S STORY REEL - PANEL RESULTS ANALYSIS")
    logger.info("="*80)

    # Configuration
    output_dir = Path('data/reader_panels/maya_story_reel')
    model = "ollama/deepseek-r1"

    # Load results
    logger.info("\nLoading panel results...")
    panels = load_panel_results(output_dir)

    if not panels:
        logger.error("No panel results found!")
        return

    # Initialize LLM
    llm_caller = LLMCaller()

    # Get recommendations from each panel
    logger.info("\nGetting recommendations from each panel...")
    all_recommendations = {}

    for panel_name, panel_data in panels.items():
        logger.info(f"\nAnalyzing {panel_name}...")
        recommendations = get_panel_recommendations(
            panel_name, panel_data, llm_caller, model
        )
        all_recommendations[panel_name] = recommendations

        # Print summary
        logger.info(f"  Top improvements: {recommendations.get('priority_improvements', [])[:3]}")
        logger.info(f"  Overall: {recommendations.get('overall_recommendation', 'N/A')}")

    # Compare across panels
    logger.info("\nComparing across panels...")
    comparison = compare_panels(all_recommendations)

    logger.info(f"\nConsensus improvements: {len(comparison['consensus_improvements'])}")
    logger.info(f"Universal strengths: {len(comparison['universal_strengths'])}")
    logger.info(f"Critical concerns: {len(comparison['critical_concerns'])}")
    logger.info(f"Conflicts identified: {len(comparison['conflicts'])}")

    # Generate synthesis
    logger.info("\nGenerating final synthesis...")
    synthesis = synthesize_final_recommendations(
        all_recommendations, comparison, llm_caller, model
    )

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save full analysis
    analysis_file = output_dir / f"analysis_{timestamp}.json"
    with open(analysis_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'panel_recommendations': all_recommendations,
            'comparison': comparison,
            'synthesis_text': synthesis
        }, f, indent=2)

    # Save synthesis report
    report_file = output_dir / f"synthesis_report_{timestamp}.md"
    with open(report_file, 'w') as f:
        f.write(f"# Maya's Story Reel - Reader Panel Synthesis Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Executive Summary\n\n")
        f.write(synthesis)
        f.write("\n\n## Consensus Improvements\n\n")
        for item in comparison['consensus_improvements']:
            panels = comparison['intersections']['improvements'].get(item, [])
            f.write(f"- **{item.title()}** (mentioned by: {', '.join(panels)})\n")

        f.write("\n\n## Universal Strengths\n\n")
        for item in comparison['universal_strengths']:
            panels = comparison['intersections']['strengths'].get(item, [])
            f.write(f"- **{item.title()}** (mentioned by: {', '.join(panels)})\n")

        f.write("\n\n## Critical Concerns\n\n")
        for item in comparison['critical_concerns']:
            panels = comparison['intersections']['concerns'].get(item, [])
            f.write(f"- **{item.title()}** (mentioned by: {', '.join(panels)})\n")

        f.write("\n\n## Identified Conflicts\n\n")
        for conflict in comparison['conflicts']:
            f.write(f"### {conflict['description']}\n")
            f.write(f"**Panels:** {', '.join(conflict['panels'])}\n\n")
            f.write(f"**Details:**\n```json\n{json.dumps(conflict['details'], indent=2)}\n```\n\n")

        f.write("\n\n## Panel-Specific Recommendations\n\n")
        for panel_name, recs in all_recommendations.items():
            f.write(f"### {panel_name.replace('_', ' ').title()}\n\n")
            f.write(f"**Overall:** {recs.get('overall_recommendation', 'N/A')}\n\n")
            f.write(f"**Priority Improvements:**\n")
            for imp in recs.get('priority_improvements', [])[:5]:
                f.write(f"- {imp}\n")
            f.write("\n")

    logger.info(f"\nAnalysis saved to: {analysis_file}")
    logger.info(f"Report saved to: {report_file}")

    # Print summary
    print("\n" + "="*80)
    print("SYNTHESIS SUMMARY")
    print("="*80)
    print(synthesis[:1000] + "..." if len(synthesis) > 1000 else synthesis)
    print("\n" + "="*80)
    print(f"\nFull report: {report_file}")
    print("="*80)


if __name__ == "__main__":
    main()
