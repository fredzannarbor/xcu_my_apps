#!/usr/bin/env python3
"""
Evaluate Maya's Story Reel from the perspective of 80 diverse parent readers.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
import litellm

# Load environment variables
load_dotenv()

def load_evaluation_data(file_path: str) -> Dict[str, Any]:
    """Load the evaluation data JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def create_evaluation_prompt(parent_persona: Dict[str, Any], book_info: Dict[str, Any]) -> str:
    """Create a detailed evaluation prompt for a specific parent persona."""

    persona_name = parent_persona['name']
    characteristics = parent_persona['characteristics']

    prompt = f"""You are evaluating a children's book from the perspective of a parent with specific concerns and priorities.

BOOK INFORMATION:
Title: {book_info['book_title']}
Logline: {book_info['book_logline']}

Description:
{book_info['book_description']}

YOUR PARENT PERSONA:
Name: {persona_name}
Age Range: {characteristics.get('age_range', 'N/A')}
Concerns: {', '.join(characteristics.get('concerns', []))}
Priorities: {', '.join(characteristics.get('priorities', []))}
Personality Traits: {', '.join(characteristics.get('personality_traits', []))}
Books Purchased Per Month: {characteristics.get('reading_habits', {}).get('buys_books_per_month', 'N/A')}

EVALUATION TASK:
As this parent persona, evaluate the book considering your specific concerns about literacy, screen time, and educational value. Provide:

1. Market Appeal (0-10): Would you buy this book for your child? Consider:
   - Does it address your concerns?
   - Is it worth the investment?
   - Would your child want to read it?

2. Genre Fit (0-10): Does it fit your expectations for a children's book? Consider:
   - Is it appropriate for the age group?
   - Does the AI/tech integration feel appropriate?
   - Does it balance entertainment with education?

3. Audience Alignment (0-10): Is it right for your child? Consider:
   - Will it engage struggling readers?
   - Is the content relatable?
   - Does it build confidence without being preachy?

4. Detailed Feedback: Share your honest thoughts as this parent about:
   - What excites you about this book
   - What concerns you
   - How it addresses (or doesn't address) your priorities
   - Whether you'd recommend it to other parents

5. Recommendations: What changes or additions would make you MORE likely to purchase this book?

6. Concerns: What specific worries do you have about this book? Be honest about:
   - Screen time and AI messaging
   - Educational effectiveness
   - Age appropriateness
   - Any other parental concerns

Provide your evaluation in JSON format:
{{
  "market_appeal": <score 0-10>,
  "genre_fit": <score 0-10>,
  "audience_alignment": <score 0-10>,
  "overall_rating": <average of the three scores>,
  "detailed_feedback": "<your detailed parent perspective>",
  "recommendations": "<what would make you buy this>",
  "concerns": "<your specific worries as a parent>"
}}

Think deeply from this parent's perspective. Be honest and specific."""

    return prompt

def evaluate_parent_persona(
    parent_persona: Dict[str, Any],
    book_info: Dict[str, Any],
    model: str = "claude-sonnet-4.5"
) -> Dict[str, Any]:
    """Evaluate the book from one parent's perspective."""

    prompt = create_evaluation_prompt(parent_persona, book_info)

    try:
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )

        # Extract JSON from response
        content = response['choices'][0]['message']['content']

        # Try to parse JSON from the response
        # Look for JSON block in markdown or direct JSON
        if '```json' in content:
            json_start = content.find('```json') + 7
            json_end = content.find('```', json_start)
            json_str = content[json_start:json_end].strip()
        elif '```' in content:
            json_start = content.find('```') + 3
            json_end = content.find('```', json_start)
            json_str = content[json_start:json_end].strip()
        else:
            # Try to find JSON object directly
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            json_str = content[json_start:json_end].strip()

        evaluation = json.loads(json_str)

        # Calculate overall rating if not provided
        if 'overall_rating' not in evaluation or evaluation['overall_rating'] == 0:
            evaluation['overall_rating'] = round(
                (evaluation['market_appeal'] +
                 evaluation['genre_fit'] +
                 evaluation['audience_alignment']) / 3,
                1
            )

        # Add persona information
        evaluation['persona_name'] = parent_persona['name']
        evaluation['persona_type'] = parent_persona['name'].rsplit('#', 1)[0].strip()
        evaluation['model_used'] = model

        return evaluation

    except Exception as e:
        print(f"ERROR evaluating {parent_persona['name']}: {e}")
        # Return a default evaluation
        return {
            "persona_name": parent_persona['name'],
            "persona_type": parent_persona['name'].rsplit('#', 1)[0].strip(),
            "market_appeal": 0,
            "genre_fit": 0,
            "audience_alignment": 0,
            "overall_rating": 0,
            "detailed_feedback": f"Error during evaluation: {str(e)}",
            "recommendations": "Unable to evaluate",
            "concerns": "Evaluation failed"
        }

def main():
    """Main evaluation function."""

    # File paths
    data_file = "/Users/fred/xcu_my_apps/nimble/codexes-factory/data/reader_panels/maya_story_reel/agent_evaluation_data.json"
    output_file = "/Users/fred/xcu_my_apps/nimble/codexes-factory/data/reader_panels/maya_story_reel/parents_claude_max_feedback.jsonl"

    # Load evaluation data
    print("Loading evaluation data...")
    data = load_evaluation_data(data_file)

    book_info = {
        'book_title': data['book_title'],
        'book_logline': data['book_logline'],
        'book_description': data['book_description']
    }

    parents = data['panels']['parents']
    print(f"Found {len(parents)} parent personas to evaluate")

    # Create output directory if needed
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Check which evaluations are already completed
    completed_names = set()
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            for line in f:
                try:
                    eval_data = json.loads(line)
                    completed_names.add(eval_data['persona_name'])
                except:
                    pass
        print(f"Found {len(completed_names)} already completed evaluations")

    # Open output file for appending
    evaluations_completed = len(completed_names)

    with open(output_file, 'a') as outfile:
        for i, parent in enumerate(parents, 1):
            # Skip if already completed
            if parent['name'] in completed_names:
                print(f"\n[{i}/80] Skipping (already done): {parent['name']}")
                continue

            print(f"\n[{i}/80] Evaluating: {parent['name']}")

            # Evaluate this parent persona
            evaluation = evaluate_parent_persona(
                parent,
                book_info,
                model="gpt-4o"
            )

            # Write to JSONL file
            outfile.write(json.dumps(evaluation) + '\n')
            outfile.flush()  # Ensure it's written immediately

            evaluations_completed += 1

            # Progress reports every 20 evaluations
            if i % 20 == 0:
                print(f"\n{'='*60}")
                print(f"PROGRESS REPORT: {i}/80 evaluations completed")
                print(f"{'='*60}")

                # Calculate average scores so far
                with open(output_file, 'r') as f:
                    completed = [json.loads(line) for line in f]

                avg_market = sum(e['market_appeal'] for e in completed) / len(completed)
                avg_genre = sum(e['genre_fit'] for e in completed) / len(completed)
                avg_audience = sum(e['audience_alignment'] for e in completed) / len(completed)
                avg_overall = sum(e['overall_rating'] for e in completed) / len(completed)

                print(f"Average Scores:")
                print(f"  Market Appeal: {avg_market:.1f}/10")
                print(f"  Genre Fit: {avg_genre:.1f}/10")
                print(f"  Audience Alignment: {avg_audience:.1f}/10")
                print(f"  Overall Rating: {avg_overall:.1f}/10")
                print(f"{'='*60}\n")

    # Final summary
    print(f"\n{'='*60}")
    print(f"FINAL SUMMARY: All 80 parent evaluations completed!")
    print(f"{'='*60}")

    # Load all evaluations for final statistics
    with open(output_file, 'r') as f:
        all_evaluations = [json.loads(line) for line in f]

    # Overall statistics
    avg_market = sum(e['market_appeal'] for e in all_evaluations) / len(all_evaluations)
    avg_genre = sum(e['genre_fit'] for e in all_evaluations) / len(all_evaluations)
    avg_audience = sum(e['audience_alignment'] for e in all_evaluations) / len(all_evaluations)
    avg_overall = sum(e['overall_rating'] for e in all_evaluations) / len(all_evaluations)

    print(f"\nFinal Average Scores:")
    print(f"  Market Appeal: {avg_market:.1f}/10")
    print(f"  Genre Fit: {avg_genre:.1f}/10")
    print(f"  Audience Alignment: {avg_audience:.1f}/10")
    print(f"  Overall Rating: {avg_overall:.1f}/10")

    # Statistics by parent type
    print(f"\nBreakdown by Parent Type:")
    parent_types = {}
    for e in all_evaluations:
        ptype = e['persona_type']
        if ptype not in parent_types:
            parent_types[ptype] = []
        parent_types[ptype].append(e['overall_rating'])

    for ptype, ratings in sorted(parent_types.items()):
        avg = sum(ratings) / len(ratings)
        print(f"  {ptype}: {avg:.1f}/10 (n={len(ratings)})")

    print(f"\nOutput saved to: {output_file}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
