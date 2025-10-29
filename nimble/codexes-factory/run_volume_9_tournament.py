#!/usr/bin/env python3
"""
Simple Tournament Agent for Nimitz Volume 9 Middle Reader Adaptation Ideas
Accepts simple input specs and generates/evaluates ideas using LLM.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / 'src'))

import litellm
from dotenv import load_dotenv

load_dotenv()

# Configure litellm
litellm.telemetry = False
litellm.drop_params = True


def run_volume_9_tournament():
    """Generate and evaluate 10 Volume 9 adaptation ideas."""

    print("=" * 80)
    print("NIMITZ VOLUME 9: MIDDLE READER ADAPTATION TOURNAMENT")
    print("=" * 80)
    print()

    # Load the Volume 9 prompt
    prompts_file = Path("imprints/warships_and_navies/prompts/nimitz_volume_0_experimental.json")

    with open(prompts_file, 'r') as f:
        prompts_data = json.load(f)

    volume_9_section = prompts_data["volume_0_experimental_sections"]["volume_9_middle_reader_adaptation"]
    generation_prompt = volume_9_section["prompt"]

    print("✓ Loaded Volume 9 tournament prompt")
    print(f"  Description: {volume_9_section['description']}")
    print()

    # Model configuration (with grounding)
    model = "gemini/gemini-2.5-pro"

    print(f"Model: {model}")
    print(f"Grounding: Enabled (MODE_DYNAMIC)")
    print()

    # Generate tournament results
    print("Generating tournament with 10 adaptation approaches...")
    print("This will take 3-5 minutes...")
    print()

    messages = [{
        "role": "user",
        "content": generation_prompt
    }]

    try:
        # Enable grounding for Gemini
        extra_body = {
            "google_search_retrieval": {
                "dynamic_retrieval_config": {
                    "mode": "MODE_DYNAMIC",
                    "dynamic_threshold": 0.3
                }
            }
        } if "gemini" in model.lower() else {}

        response = litellm.completion(
            model=model,
            messages=messages,
            temperature=0.7,  # Some creativity for idea generation
            max_tokens=65536,  # Very large output for full tournament with all details
            **({'extra_body': extra_body} if extra_body else {})
        )

        # Parse response - should be JSON tournament results
        content = response.choices[0].message.content

        # Try to extract JSON from markdown code blocks if present
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        elif "```" in content:
            json_start = content.find("```") + 3
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()

        tournament_results = json.loads(content)

        print("✓ Tournament generation complete!")
        print()

        # Calculate cost
        cost = 0
        if hasattr(response, 'usage') and response.usage:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            # Gemini 2.5 Pro pricing (estimate): ~$2-3 / 1M tokens
            cost = (prompt_tokens * 2.0 / 1_000_000) + (completion_tokens * 6.0 / 1_000_000)

        print(f"Generation cost: ${cost:.4f}")
        print(f"Tokens: {response.usage.prompt_tokens if hasattr(response, 'usage') else '?'} input, "
              f"{response.usage.completion_tokens if hasattr(response, 'usage') else '?'} output")
        print()

        # Display results
        print("=" * 80)
        print("TOURNAMENT RESULTS")
        print("=" * 80)
        print()

        candidates = tournament_results.get("candidates", [])
        print(f"Total approaches generated: {len(candidates)}")
        print()

        # Show rankings
        print("RANKINGS:")
        print("-" * 80)
        sorted_candidates = sorted(candidates, key=lambda x: x.get('total_score', 0), reverse=True)

        for i, candidate in enumerate(sorted_candidates, 1):
            score = candidate.get('total_score', 0)
            name = candidate.get('idea_name', 'Unnamed')
            concept = candidate.get('concept', 'No concept')[:100]

            print(f"{i}. {name} - {score}/100")
            print(f"   {concept}...")
            print()

        # Display winner details
        winner = tournament_results.get("winner", {})
        if winner:
            print("=" * 80)
            print("🏆 WINNING APPROACH")
            print("=" * 80)
            print()
            print(f"**{winner.get('approach', 'Unnamed')}**")
            print()
            print(f"Concept:")
            print(winner.get('full_concept', 'No concept provided'))
            print()

            if 'table_of_contents' in winner:
                print("Table of Contents:")
                toc = winner['table_of_contents']
                if isinstance(toc, list):
                    for chapter in toc:
                        print(f"  - {chapter}")
                print()

            print("Why This Won:")
            print(tournament_results.get('reasoning', 'No reasoning provided'))
            print()

        # Save results
        output_dir = Path("tournaments/nimitz_volume_9")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON
        json_file = output_dir / f"tournament_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "model": model,
                "cost": cost,
                "tokens": {
                    "prompt": response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
                    "completion": response.usage.completion_tokens if hasattr(response, 'usage') else 0
                },
                "tournament_results": tournament_results
            }, f, indent=2)

        print(f"✓ Saved results: {json_file}")

        # Save markdown report
        md_file = output_dir / f"VOLUME_9_WINNER_{timestamp}.md"
        with open(md_file, 'w') as f:
            f.write("# Nimitz Graybook Volume 9: Middle Reader Adaptation\n\n")
            f.write(f"**Tournament Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"**Model:** {model} (with grounding)\n\n")

            f.write("## Winning Approach\n\n")
            f.write(f"### {winner.get('approach', 'Unnamed')}\n\n")
            f.write(f"{winner.get('full_concept', 'No concept')}\n\n")

            if 'table_of_contents' in winner:
                f.write("### Table of Contents\n\n")
                for chapter in winner.get('table_of_contents', []):
                    f.write(f"- {chapter}\n")
                f.write("\n")

            f.write("### Why This Approach Won\n\n")
            f.write(f"{tournament_results.get('reasoning', 'No reasoning')}\n\n")

            if 'implementation_plan' in winner:
                f.write("### Implementation Plan\n\n")
                f.write(f"{winner.get('implementation_plan', 'No plan')}\n\n")

            f.write("## All Approaches (Ranked)\n\n")
            for i, candidate in enumerate(sorted_candidates, 1):
                f.write(f"{i}. **{candidate.get('idea_name', 'Unnamed')}** - {candidate.get('total_score', 0)}/100\n")
                f.write(f"   {candidate.get('concept', 'No concept')}\n\n")

        print(f"✓ Saved report: {md_file}")
        print()

        print("=" * 80)
        print("TOURNAMENT COMPLETE")
        print("=" * 80)
        print()
        print(f"Winner: {winner.get('approach', 'See results')}")
        print(f"Files: {output_dir}/")
        print()

    except json.JSONDecodeError as e:
        print(f"✗ Error parsing tournament results as JSON: {e}")
        print()
        print("Raw response:")
        print(content[:500])
        print()

    except Exception as e:
        print(f"✗ Error generating tournament: {e}")
        print()


if __name__ == "__main__":
    run_volume_9_tournament()
