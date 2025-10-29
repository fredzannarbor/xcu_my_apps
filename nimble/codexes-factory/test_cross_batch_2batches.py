#!/usr/bin/env python3
"""
Test cross-batch harmonization with 2 small batches using gpt-4o-mini.
Validates the two-pass approach works before scaling up.
"""

import json
import litellm
from dotenv import load_dotenv

load_dotenv()

litellm.telemetry = False
litellm.drop_params = True


# Test data with known cross-batch duplicates
TEST_BATCH_A = [
    "ARNOLD",
    "Arnold, GENERAL",
    "Arnold, Gen",
    "AINSWORTH",
    "ABBOT",
    "Admiral Nimitz"
]

TEST_BATCH_M = [
    "Marshall, Gen",
    "Marshall, George C.",
    "Marshall, George C., GEN",
    "MacArthur",
    "MacArthur, General",
    "Nimitz, Chester W., ADM"
]


PASS1_PROMPT = """Harmonize these person name variants within this batch.

RULES:
1. Normalize capitalization
2. Spell out ranks: Gen → General, Adm → Admiral
3. Use full names when you know them

Return JSON:
{{
  "Authoritative Name": ["variant1", "variant2"],
  ...
}}

ENTRIES:
{entity_list}"""


PASS2_PROMPT = """You processed two batches separately. Now find duplicates ACROSS batches.

BATCH A (harmonized): {batch_a}
BATCH M (harmonized): {batch_m}

Find persons that appear in BOTH batches with different name formats.

Example:
- "Admiral Nimitz" (from Batch A) + "Nimitz, Chester W., ADM" (from Batch M) → SAME PERSON

Return JSON:
{{
  "cross_batch_merges": [
    {{
      "authoritative": "Nimitz, Chester W., Admiral",
      "merge_from_batch_a": ["Admiral Nimitz"],
      "merge_from_batch_m": ["Nimitz, Chester W., ADM"],
      "reasoning": "Both refer to Chester W. Nimitz, CINCPAC"
    }}
  ]
}}"""


def test_cross_batch_harmonization():
    """Test two-pass harmonization with known duplicates"""

    model = "openai/gpt-5-mini"

    print("=" * 80)
    print("Cross-Batch Harmonization Test")
    print(f"Model: {model}")
    print("=" * 80)
    print()

    # PASS 1: Harmonize each batch separately
    print("PASS 1: Within-batch harmonization")
    print("-" * 80)

    # Batch A
    print("\nBatch A (A-names):")
    print(f"  Input: {TEST_BATCH_A}")

    prompt_a = PASS1_PROMPT.format(entity_list="\n".join(TEST_BATCH_A))

    response_a = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": prompt_a}],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=2048
    )

    content_a = response_a.choices[0].message.content
    harmonized_a = json.loads(content_a)

    print(f"  Output: {list(harmonized_a.keys())}")
    cost_a = (response_a.usage.prompt_tokens * 0.15 / 1_000_000) + (response_a.usage.completion_tokens * 0.60 / 1_000_000)
    print(f"  Cost: ${cost_a:.6f}")

    # Batch M
    print("\nBatch M (M-names):")
    print(f"  Input: {TEST_BATCH_M}")

    prompt_m = PASS1_PROMPT.format(entity_list="\n".join(TEST_BATCH_M))

    response_m = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": prompt_m}],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=2048
    )

    content_m = response_m.choices[0].message.content
    harmonized_m = json.loads(content_m)

    print(f"  Output: {list(harmonized_m.keys())}")
    cost_m = (response_m.usage.prompt_tokens * 0.15 / 1_000_000) + (response_m.usage.completion_tokens * 0.60 / 1_000_000)
    print(f"  Cost: ${cost_m:.6f}")

    # PASS 2: Find cross-batch duplicates
    print("\n" + "=" * 80)
    print("PASS 2: Cross-batch reconciliation")
    print("-" * 80)

    prompt_pass2 = PASS2_PROMPT.format(
        batch_a=json.dumps(list(harmonized_a.keys()), indent=2),
        batch_m=json.dumps(list(harmonized_m.keys()), indent=2)
    )

    print(f"\nComparing:")
    print(f"  Batch A harmonized: {list(harmonized_a.keys())}")
    print(f"  Batch M harmonized: {list(harmonized_m.keys())}")
    print()

    response_pass2 = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": prompt_pass2}],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=2048
    )

    content_pass2 = response_pass2.choices[0].message.content
    cross_batch_merges = json.loads(content_pass2)

    cost_pass2 = (response_pass2.usage.prompt_tokens * 0.15 / 1_000_000) + (response_pass2.usage.completion_tokens * 0.60 / 1_000_000)

    print("Cross-batch merges found:")
    for merge in cross_batch_merges.get("cross_batch_merges", []):
        print(f"\n  ✓ {merge['authoritative']}")
        print(f"    Merging: {merge.get('merge_from_batch_a', [])} (Batch A)")
        print(f"           + {merge.get('merge_from_batch_m', [])} (Batch M)")
        print(f"    Reason: {merge.get('reasoning', 'No reason')}")

    print(f"\n  Cost: ${cost_pass2:.6f}")

    # Final results
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    print(f"\nOriginal entries: {len(TEST_BATCH_A) + len(TEST_BATCH_M)}")
    print(f"After Pass 1: {len(harmonized_a) + len(harmonized_m)}")
    print(f"Cross-batch merges: {len(cross_batch_merges.get('cross_batch_merges', []))}")
    print(f"\nExpected final: {len(harmonized_a) + len(harmonized_m) - len(cross_batch_merges.get('cross_batch_merges', []))}")
    print()
    print(f"Total cost: ${cost_a + cost_m + cost_pass2:.6f}")
    print()
    print("✓ Two-pass approach validated!" if cross_batch_merges.get("cross_batch_merges") else "⚠️  No cross-batch duplicates found (check logic)")
    print()
    print("If this works, scale up to full dataset with smaller batches (~100 entries each)")
    print("=" * 80)


if __name__ == "__main__":
    test_cross_batch_harmonization()
