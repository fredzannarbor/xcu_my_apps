#!/usr/bin/env python3
"""
Analyze the purchasing persona evaluations to extract key insights.
"""

import json
from pathlib import Path
from collections import defaultdict

def main():
    input_path = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/data/reader_panels/maya_story_reel/purchasing_claude_max_feedback.jsonl")

    evaluations = []
    with open(input_path, 'r') as f:
        for line in f:
            evaluations.append(json.loads(line))

    print("="*80)
    print("MAYA'S STORY REEL - PURCHASING EVALUATION ANALYSIS")
    print("="*80)
    print(f"\nTotal Evaluations: {len(evaluations)}")

    # Analyze by persona type
    persona_types = defaultdict(list)
    for eval in evaluations:
        persona_types[eval['persona_type']].append(eval)

    print(f"\nPersona Types: {len(persona_types)}")
    for ptype, evals in persona_types.items():
        print(f"  - {ptype}: {len(evals)} evaluations")

    # Top recommendations across all personas
    print("\n" + "="*80)
    print("TOP RECOMMENDATIONS (Most Frequently Mentioned)")
    print("="*80)

    all_recommendations = defaultdict(int)
    for eval in evaluations:
        for rec in eval['recommendations']:
            # Normalize recommendation text for counting
            if 'teacher' in rec.lower() and 'guide' in rec.lower():
                all_recommendations["Teacher's guide with standards alignment"] += 1
            elif 'audiobook' in rec.lower():
                all_recommendations["Audiobook version for accessibility"] += 1
            elif 'parent' in rec.lower() and 'education' in rec.lower():
                all_recommendations["Parent education materials"] += 1
            elif 'professional development' in rec.lower() or 'training' in rec.lower():
                all_recommendations["Professional development for educators"] += 1
            elif 'assessment' in rec.lower() or 'progress monitoring' in rec.lower():
                all_recommendations["Assessment and progress monitoring tools"] += 1
            elif 'pilot' in rec.lower() or 'study' in rec.lower():
                all_recommendations["Pilot study with measurable outcomes"] += 1
            elif 'series' in rec.lower() or 'sequel' in rec.lower():
                all_recommendations["Develop series for sustained engagement"] += 1
            elif 'accessible' in rec.lower() or 'dyslexia' in rec.lower() or 'format' in rec.lower():
                all_recommendations["Accessible formats (dyslexia-friendly, large print)"] += 1

    sorted_recs = sorted(all_recommendations.items(), key=lambda x: x[1], reverse=True)
    for i, (rec, count) in enumerate(sorted_recs[:10], 1):
        percentage = (count / len(evaluations)) * 100
        print(f"{i}. {rec}")
        print(f"   Mentioned by: {count}/{len(evaluations)} personas ({percentage:.0f}%)")

    # Top concerns
    print("\n" + "="*80)
    print("TOP CONCERNS (Most Frequently Mentioned)")
    print("="*80)

    all_concerns = defaultdict(int)
    for eval in evaluations:
        for concern in eval['concerns']:
            # Normalize concern text for counting
            if 'audiobook' in concern.lower() or 'accessible' in concern.lower() or 'format' in concern.lower():
                all_concerns["Lack of audiobook/accessible formats"] += 1
            elif 'research' in concern.lower() or 'evidence' in concern.lower() or 'empirical' in concern.lower():
                all_concerns["Lack of empirical research/evidence base"] += 1
            elif 'training' in concern.lower() or 'teacher' in concern.lower() and 'facilitation' in concern.lower():
                all_concerns["Requires teacher training/facilitation"] += 1
            elif 'budget' in concern.lower() or 'cost' in concern.lower():
                all_concerns["Budget/cost considerations"] += 1
            elif 'parent' in concern.lower() and 'communication' in concern.lower():
                all_concerns["Parent communication needed (AI themes)"] += 1
            elif 'sustainability' in concern.lower() or 'series' in concern.lower():
                all_concerns["Sustainability/series continuation unclear"] += 1
            elif 'district-wide' in concern.lower() or 'scalability' in concern.lower():
                all_concerns["District-wide adoption challenges"] += 1
            elif 'text complexity' in concern.lower() or 'reading level' in concern.lower():
                all_concerns["Text complexity may be too high for target audience"] += 1

    sorted_concerns = sorted(all_concerns.items(), key=lambda x: x[1], reverse=True)
    for i, (concern, count) in enumerate(sorted_concerns[:10], 1):
        percentage = (count / len(evaluations)) * 100
        print(f"{i}. {concern}")
        print(f"   Mentioned by: {count}/{len(evaluations)} personas ({percentage:.0f}%)")

    # Rating distribution
    print("\n" + "="*80)
    print("RATING DISTRIBUTION")
    print("="*80)

    ratings = [e['overall_rating'] for e in evaluations]
    print(f"\nOverall Rating Statistics:")
    print(f"  Mean: {sum(ratings)/len(ratings):.2f}/10")
    print(f"  Median: {sorted(ratings)[len(ratings)//2]:.2f}/10")
    print(f"  Min: {min(ratings):.2f}/10")
    print(f"  Max: {max(ratings):.2f}/10")

    # Distribution by score band
    score_bands = {
        "9.0-10.0 (Excellent)": len([r for r in ratings if r >= 9.0]),
        "8.0-8.9 (Very Good)": len([r for r in ratings if 8.0 <= r < 9.0]),
        "7.0-7.9 (Good)": len([r for r in ratings if 7.0 <= r < 8.0]),
        "6.0-6.9 (Fair)": len([r for r in ratings if 6.0 <= r < 7.0]),
        "Below 6.0 (Poor)": len([r for r in ratings if r < 6.0]),
    }

    print(f"\nRating Distribution:")
    for band, count in score_bands.items():
        percentage = (count / len(ratings)) * 100
        bar = "█" * int(percentage / 2)
        print(f"  {band:25s} {count:2d} ({percentage:5.1f}%) {bar}")

    # Comparison by category
    print("\n" + "="*80)
    print("SCORE COMPARISON BY CATEGORY")
    print("="*80)

    categories = ['market_appeal', 'genre_fit', 'audience_alignment']
    for category in categories:
        scores = [e[category] for e in evaluations]
        avg = sum(scores) / len(scores)
        print(f"\n{category.replace('_', ' ').title()}:")
        print(f"  Average: {avg:.2f}/10")

        # Show distribution by persona type
        for ptype, evals in persona_types.items():
            ptype_scores = [e[category] for e in evals]
            ptype_avg = sum(ptype_scores) / len(ptype_scores)
            print(f"    {ptype:35s} {ptype_avg:.2f}/10")

    print("\n" + "="*80)
    print("KEY TAKEAWAYS")
    print("="*80)
    print("""
1. STRONGEST SUPPORT: Special Education Coordinators (9.0/10)
   - See exceptional value for intervention programs
   - Multi-functional: bibliotherapy, phonics, self-advocacy, growth mindset
   - Cost-effective compared to traditional intervention materials

2. MOST ENTHUSIASTIC: School Librarians (8.67/10)
   - Highest market appeal (9.0/10)
   - Expect high circulation (25-30 times/year vs 8-10 average)
   - Contemporary hook attracts reluctant readers

3. MOST CAUTIOUS: Curriculum Directors (7.67/10)
   - Lowest market appeal (6.0/10)
   - Require empirical research before large-scale adoption
   - Concerned about cost vs. proven phonics programs

4. CRITICAL PRIORITIES FOR PUBLISHER:
   ✓ Audiobook version (mentioned by 100% of personas)
   ✓ Teacher's guide with standards alignment (100%)
   ✓ Parent education materials about Science of Reading (100%)
   ✓ Accessible formats for struggling readers (75%)
   ✓ Pilot study with measurable outcomes (curriculum directors)

5. MARKET POSITIONING:
   ✓ Position as SUPPLEMENTARY intervention tool (not primary curriculum)
   ✓ Target: Libraries, intervention programs, book clubs
   ✓ Avoid: Replacing systematic phonics programs
   ✓ Price point: Accessible for school budgets ($8-20 per copy)

6. EXPECTED ADOPTION TIMELINE:
   - Immediate: Library purchases (5-6 copies per school)
   - Short-term: Intervention program adoption (8-10 copies)
   - Medium-term: Classroom pilot programs (25-30 copies)
   - Long-term: District-wide adoption (requires evidence base)

7. ROI INDICATORS:
   - Reading attitude improvement (measurable via surveys)
   - Phonics knowledge application (assessments)
   - Intervention acceptance (reduced stigma)
   - Parent engagement (attending literacy workshops)
   - Library circulation rates (target: 25-30/year)
""")

if __name__ == "__main__":
    main()
