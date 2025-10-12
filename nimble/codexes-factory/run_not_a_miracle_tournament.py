#!/usr/bin/env python3
"""
Run tournament evaluation for Not A Miracle Readers V2 ideas.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add paths for imports
sys.path.insert(0, '/Users/fred/xcu_my_apps')
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from codexes.core.llm_caller import call_model_with_prompt
except ImportError:
    from src.codexes.core.llm_caller import call_model_with_prompt


def evaluate_idea_pair(idea1, idea2, evaluation_criteria):
    """Evaluate two ideas head-to-head."""

    prompt = f"""You are an expert children's book editor evaluating early chapter book concepts for "Not A Miracle Readers," an imprint focused on helping families navigate Science of Reading-based school systems.

Compare these two book concepts and determine which is BETTER based on the criteria below.

IDEA 1: {idea1['title']}
Logline: {idea1['logline']}
Setting: {idea1['setting']}
Protagonist: {idea1['protagonist']['name']} ({idea1['protagonist']['ethnicity']})
Hook: {idea1['contemporary_hook']}
Synopsis: {idea1['synopsis'][:500]}...

IDEA 2: {idea2['title']}
Logline: {idea2['logline']}
Setting: {idea2['setting']}
Protagonist: {idea2['protagonist']['name']} ({idea2['protagonist']['ethnicity']})
Hook: {idea2['contemporary_hook']}
Synopsis: {idea2['synopsis'][:500]}...

EVALUATION CRITERIA:
1. Alignment with imprint mission (supporting families in SoR school systems)
2. Contemporary relevance and cultural authenticity (2025 pop culture hooks)
3. Character authenticity and appeal to 9-10 year olds
4. Thematic integration of A-plot and B-plot
5. Market viability for blue state knowledge worker families
6. Originality and freshness of premise

Which idea is BETTER overall? Consider all criteria.

Return ONLY a JSON object:
{{
  "winner": "IDEA 1" or "IDEA 2",
  "reasoning": "2-3 sentence explanation of why this idea is stronger",
  "score": 0.0-1.0 (confidence in this choice)
}}
"""

    try:
        prompt_config = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert children's book editor specializing in early chapter books for 9-10 year olds. You evaluate concepts based on market potential, educational value, and contemporary relevance."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "params": {
                "temperature": 0.3,
                "max_tokens": 500
            }
        }

        response = call_model_with_prompt(
            model_name="gemini/gemini-2.5-flash",
            prompt_config=prompt_config,
            response_format_type="json_object",
            prompt_name="tournament_evaluation"
        )

        if response and "parsed_content" in response:
            return response["parsed_content"]
        else:
            return None

    except Exception as e:
        print(f"  ✗ Error evaluating pair: {e}")
        return None


def run_tournament(ideas):
    """Run a single-elimination tournament."""

    print("\n" + "=" * 80)
    print("TOURNAMENT BRACKET")
    print("=" * 80)

    round_num = 1
    current_round = ideas.copy()

    while len(current_round) > 1:
        print(f"\n{'ROUND ' + str(round_num) + ': ':=^80}")
        print(f"({len(current_round)} ideas competing)")
        print()

        next_round = []

        # Pair up ideas
        for i in range(0, len(current_round), 2):
            if i + 1 < len(current_round):
                idea1 = current_round[i]
                idea2 = current_round[i + 1]

                print(f"Match {i//2 + 1}:")
                print(f"  {idea1['title']}")
                print(f"    vs")
                print(f"  {idea2['title']}")

                # Evaluate
                result = evaluate_idea_pair(idea1, idea2, [
                    "Alignment with imprint mission",
                    "Contemporary relevance",
                    "Character appeal",
                    "Thematic integration",
                    "Market viability",
                    "Originality"
                ])

                if result:
                    winner_idx = 1 if result['winner'] == "IDEA 1" else 2
                    winner = idea1 if winner_idx == 1 else idea2
                    print(f"  → Winner: {winner['title']}")
                    print(f"     Reasoning: {result.get('reasoning', 'N/A')}")
                    next_round.append(winner)
                else:
                    # Default to first idea if evaluation fails
                    print(f"  → Default winner: {idea1['title']} (evaluation failed)")
                    next_round.append(idea1)

                print()
            else:
                # Odd one out gets a bye
                print(f"Bye: {current_round[i]['title']} (advances automatically)")
                next_round.append(current_round[i])
                print()

        current_round = next_round
        round_num += 1

    return current_round[0] if current_round else None


def main():
    print("=" * 80)
    print("Not A Miracle Readers Tournament - V2")
    print("=" * 80)
    print()

    # Load ideas
    ideas_file = Path("tournaments/not_a_miracle_readers/not_a_miracle_readers_ideas_v2_20251005_234522.json")
    print(f"Loading ideas from: {ideas_file}")

    with open(ideas_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    ideas = data['ideas']
    print(f"  ✓ Loaded {len(ideas)} ideas")
    print()

    # Run tournament
    print("Starting tournament evaluation...")
    print("Using Gemini 2.5 Flash for head-to-head comparisons")
    print()

    winner = run_tournament(ideas)

    if winner:
        print("\n" + "=" * 80)
        print("🏆 TOURNAMENT WINNER 🏆")
        print("=" * 80)
        print()
        print(f"Title: {winner['title']}")
        print(f"Logline: {winner['logline']}")
        print(f"Setting: {winner['setting']}")
        prot = winner['protagonist']
        print(f"Protagonist: {prot['name']} ({prot['ethnicity']}, age {prot['age']})")
        print(f"Contemporary Hook: {winner['contemporary_hook']}")
        print(f"Primary Focus: {winner['primary_skill_focus']}")
        print(f"Secondary Focus: {winner['secondary_skill_focus']}")
        print()
        print("Synopsis:")
        print(winner['synopsis'])
        print()
        print(f"Persona Appeal Score: {winner.get('persona_appeal_score', 'N/A')}")
        print(f"Word Count: {winner.get('word_count', 'N/A')}")
        print()

        # Save winner
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        winner_file = Path("tournaments/not_a_miracle_readers") / f"tournament_winner_v2_{timestamp}.json"
        with open(winner_file, 'w', encoding='utf-8') as f:
            json.dump(winner, f, indent=2)

        print(f"✓ Winner saved to: {winner_file}")
    else:
        print("\n✗ Tournament failed to produce a winner")


if __name__ == "__main__":
    main()
