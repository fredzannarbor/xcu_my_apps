#!/usr/bin/env python3
"""
Evaluate Maya's Story Reel from the perspective of 100 diverse 9-10 year old readers.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import litellm

# Load environment variables
load_dotenv()


def load_evaluation_data(file_path: str) -> dict:
    """Load the evaluation data JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def create_evaluation_prompt(persona: dict, book_data: dict) -> str:
    """Create a detailed evaluation prompt for a specific persona."""

    characteristics = persona['characteristics']

    prompt = f"""You are evaluating a children's book from the perspective of a specific 9-10 year old child reader.

PERSONA DETAILS:
Name: {persona['name']}
Age: {characteristics['age_range']}
Reading Level: {characteristics['reading_habits']['reading_level']}
Books per Month: {characteristics['reading_habits']['books_per_month']}
Preferred Genres: {', '.join(characteristics['preferred_genres'])}
Interests: {', '.join(characteristics['interests'])}
Personality: {', '.join(characteristics['personality_traits'])}

BOOK TO EVALUATE:
Title: {book_data['book_title']}
Logline: {book_data['book_logline']}

Description:
{book_data['book_description']}

TASK: Evaluate this book from this specific child's perspective. Consider:
1. Would THIS specific child be interested in reading this book?
2. How well does it match their reading level, interests, and personality?
3. What would they like or dislike about it?
4. Would they recommend it to their friends?

Provide your evaluation in the following JSON format:
{{
  "market_appeal_score": [0-10 integer],
  "genre_fit_score": [0-10 integer],
  "audience_alignment_score": [0-10 integer],
  "detailed_feedback": "[2-3 paragraphs from the child's perspective explaining their honest reaction]",
  "recommendations": "[1-2 specific suggestions for improvement from their viewpoint]",
  "concerns": "[1-2 specific concerns or things that might not work for them]"
}}

Be honest and authentic to this specific persona. Different children will have different reactions.
Score 0-10 where:
- 0-3: Strong dislike/poor fit
- 4-6: Neutral/some interest
- 7-8: Good fit/interested
- 9-10: Excellent fit/very excited

RESPOND ONLY WITH THE JSON OBJECT, NO ADDITIONAL TEXT."""

    return prompt


def evaluate_persona(persona: dict, book_data: dict, model: str = "gpt-4o") -> dict:
    """Evaluate the book from a single persona's perspective."""

    prompt = create_evaluation_prompt(persona, book_data)

    try:
        # Use Claude Sonnet for thoughtful, nuanced evaluations
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.7
        )

        # Extract content from response
        content = response['choices'][0]['message']['content']

        # Try to parse JSON from the response
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

        # Parse the JSON response
        evaluation = json.loads(json_str)

        # Calculate overall rating
        overall_rating = round(
            (evaluation['market_appeal_score'] +
             evaluation['genre_fit_score'] +
             evaluation['audience_alignment_score']) / 3,
            1
        )

        # Add metadata
        evaluation['persona_name'] = persona['name']
        evaluation['overall_rating'] = overall_rating
        evaluation['created_at'] = datetime.now().isoformat()

        return evaluation

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON for {persona['name']}: {e}")
        print(f"Response: {response}")
        raise
    except Exception as e:
        print(f"Error evaluating {persona['name']}: {e}")
        raise


def save_evaluation(evaluation: dict, output_file: str):
    """Append a single evaluation to the JSONL file."""
    with open(output_file, 'a') as f:
        f.write(json.dumps(evaluation) + '\n')


def main():
    """Main evaluation workflow."""

    # File paths
    input_file = "/Users/fred/xcu_my_apps/nimble/codexes-factory/data/reader_panels/maya_story_reel/agent_evaluation_data.json"
    output_file = "/Users/fred/xcu_my_apps/nimble/codexes-factory/data/reader_panels/maya_story_reel/children_9_10_claude_max_feedback.jsonl"

    # Ensure output directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    # Clear existing output file if it exists
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Cleared existing output file: {output_file}")

    # Load evaluation data
    print("Loading evaluation data...")
    data = load_evaluation_data(input_file)
    personas = data['panels']['children_9_10']
    book_data = {
        'book_title': data['book_title'],
        'book_logline': data['book_logline'],
        'book_description': data['book_description']
    }

    print(f"Found {len(personas)} personas to evaluate")
    print(f"Book: {book_data['book_title']}")
    print(f"Output: {output_file}\n")

    # Evaluate each persona
    successful_evaluations = 0
    failed_evaluations = 0

    for i, persona in enumerate(personas, 1):
        try:
            print(f"[{i}/100] Evaluating from perspective of: {persona['name']}...")

            evaluation = evaluate_persona(persona, book_data)
            save_evaluation(evaluation, output_file)

            successful_evaluations += 1
            print(f"  ✓ Overall Rating: {evaluation['overall_rating']}/10")
            print(f"    Market Appeal: {evaluation['market_appeal_score']}, "
                  f"Genre Fit: {evaluation['genre_fit_score']}, "
                  f"Audience Alignment: {evaluation['audience_alignment_score']}\n")

            # Progress reports every 20 evaluations
            if i % 20 == 0:
                print(f"\n{'='*60}")
                print(f"PROGRESS REPORT: {i}/100 evaluations complete")
                print(f"Successful: {successful_evaluations}, Failed: {failed_evaluations}")
                print(f"{'='*60}\n")

        except Exception as e:
            failed_evaluations += 1
            print(f"  ✗ Failed: {e}\n")
            continue

    # Final summary
    print(f"\n{'='*60}")
    print(f"EVALUATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total personas: {len(personas)}")
    print(f"Successful evaluations: {successful_evaluations}")
    print(f"Failed evaluations: {failed_evaluations}")
    print(f"\nResults saved to: {output_file}")

    # Calculate aggregate statistics
    if successful_evaluations > 0:
        print(f"\nCalculating aggregate statistics...")

        evaluations = []
        with open(output_file, 'r') as f:
            for line in f:
                evaluations.append(json.loads(line))

        avg_market_appeal = sum(e['market_appeal_score'] for e in evaluations) / len(evaluations)
        avg_genre_fit = sum(e['genre_fit_score'] for e in evaluations) / len(evaluations)
        avg_audience_alignment = sum(e['audience_alignment_score'] for e in evaluations) / len(evaluations)
        avg_overall = sum(e['overall_rating'] for e in evaluations) / len(evaluations)

        print(f"\nAGGREGATE SCORES (n={len(evaluations)}):")
        print(f"  Market Appeal: {avg_market_appeal:.1f}/10")
        print(f"  Genre Fit: {avg_genre_fit:.1f}/10")
        print(f"  Audience Alignment: {avg_audience_alignment:.1f}/10")
        print(f"  Overall Rating: {avg_overall:.1f}/10")

        # Distribution analysis
        high_ratings = sum(1 for e in evaluations if e['overall_rating'] >= 7)
        medium_ratings = sum(1 for e in evaluations if 4 <= e['overall_rating'] < 7)
        low_ratings = sum(1 for e in evaluations if e['overall_rating'] < 4)

        print(f"\nRATING DISTRIBUTION:")
        print(f"  High (7-10): {high_ratings} ({high_ratings/len(evaluations)*100:.1f}%)")
        print(f"  Medium (4-6): {medium_ratings} ({medium_ratings/len(evaluations)*100:.1f}%)")
        print(f"  Low (0-3): {low_ratings} ({low_ratings/len(evaluations)*100:.1f}%)")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
