#!/usr/bin/env python3
"""
Test entity extraction on 5 pages using gemini/gemini-2.5-flash-lite
Report on cost and performance.
"""

import json
import time
from pathlib import Path
from datetime import datetime

import litellm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure litellm
litellm.telemetry = False
litellm.drop_params = True


ENTITY_EXTRACTION_PROMPT = """You are an extremely knowledgeable naval history enthusiast with deep expertise in World War II Pacific Theater operations. You are aware of the proper names and designations of all US, Japanese, British, and Australian ships, submarines, small craft, aircraft, units, officers, and bases. When you index an entity, you use the most authoritative, widely accepted name or designation.

Extract ALL entities from this historical naval document page in these four categories:

**PERSONS**: Officers, enlisted, civilians (with ranks)
Example: "Nimitz, Chester W., ADM"

**PLACES**: Islands, bases, ports, ocean areas
Example: "Pearl Harbor", "Guadalcanal (Solomon Islands)"

**SHIPS**: All naval vessels with hull numbers
Example: "USS Enterprise (CV-6)", "IJN Yamato"

**ORGANIZATIONS**: Commands, task forces, units
Example: "CINCPAC", "Task Force 16", "3rd Fleet"

Return ONLY valid JSON:
```json
{{
  "persons": ["Name, Rank", ...],
  "places": ["Location", ...],
  "ships": ["Ship (Hull)", ...],
  "organizations": ["Unit", ...]
}}
```

PAGE TEXT:
{page_text}"""


def test_entity_extraction_5_pages():
    """Test entity extraction on 5 sample pages"""

    # MUST use this specific model
    model = "gemini/gemini-2.5-flash-lite"

    # Load OCR results
    ocr_file = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/nimitz_ocr_gemini/ocr_results.jsonl")

    print("=" * 80)
    print("Entity Extraction Test - 5 Pages")
    print("=" * 80)
    print(f"Model: {model} (REQUIRED)")
    print()

    # Load first 5 pages with substantial content
    ocr_results = []
    with open(ocr_file, 'r') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                # Skip very short pages
                if len(data.get('new_ocr_text', '')) > 200:
                    ocr_results.append(data)
                    if len(ocr_results) >= 5:
                        break

    print(f"Selected {len(ocr_results)} test pages with substantial content")
    print()

    # Process each page
    results = []
    total_cost = 0.0
    total_time = 0.0

    for i, page_data in enumerate(ocr_results, 1):
        page_num = page_data.get("page_number", "?")
        page_text = page_data.get("new_ocr_text", "")

        print(f"Page {i}/5 (Original page {page_num})")
        print(f"  Text length: {len(page_text)} characters")

        # Format prompt
        prompt = ENTITY_EXTRACTION_PROMPT.format(page_text=page_text)

        # Time the request
        start_time = time.time()

        try:
            response = litellm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=2048
            )

            elapsed = time.time() - start_time

            # Parse response
            content = response.choices[0].message.content
            entities = json.loads(content)

            # Calculate cost
            cost = 0
            if hasattr(response, 'usage') and response.usage:
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens

                # Gemini 2.5 Flash Lite pricing (estimate: similar to Flash)
                # Using Flash pricing: $0.075/1M input, $0.30/1M output
                cost = (prompt_tokens * 0.075 / 1_000_000) + (completion_tokens * 0.30 / 1_000_000)

            total_cost += cost
            total_time += elapsed

            print(f"  ✓ Success in {elapsed:.2f}s")
            print(f"  Entities: {len(entities.get('persons', []))} persons, "
                  f"{len(entities.get('places', []))} places, "
                  f"{len(entities.get('ships', []))} ships, "
                  f"{len(entities.get('organizations', []))} orgs")
            print(f"  Tokens: {response.usage.prompt_tokens} input, "
                  f"{response.usage.completion_tokens} output")
            print(f"  Cost: ${cost:.6f}")

            results.append({
                "page_number": page_num,
                "success": True,
                "elapsed_seconds": elapsed,
                "entities": entities,
                "tokens": {
                    "prompt": response.usage.prompt_tokens,
                    "completion": response.usage.completion_tokens,
                    "total": response.usage.total_tokens
                },
                "cost": cost
            })

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ✗ Error in {elapsed:.2f}s: {str(e)[:100]}")
            results.append({
                "page_number": page_num,
                "success": False,
                "error": str(e),
                "elapsed_seconds": elapsed
            })

        print()
        time.sleep(1)  # Small delay between requests

    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Model tested: {model}")
    print(f"Pages attempted: 5")
    print(f"Successful: {sum(1 for r in results if r.get('success'))}")
    print(f"Failed: {sum(1 for r in results if not r.get('success'))}")
    print()
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Avg time per page: {total_time/5:.2f} seconds")
    print()
    print(f"Total cost: ${total_cost:.6f}")
    print(f"Avg cost per page: ${total_cost/5:.6f}")
    print()

    # Extrapolate to full collection
    if total_cost > 0:
        full_collection_cost = (total_cost / 5) * 4023
        full_collection_time = (total_time / 5) * 4023
        print("EXTRAPOLATION TO FULL COLLECTION (4,023 pages):")
        print(f"  Estimated total cost: ${full_collection_cost:.2f}")
        print(f"  Estimated total time: {full_collection_time/60:.1f} minutes ({full_collection_time/3600:.1f} hours)")
        print()

    # Count unique entities across all successful pages
    all_entities = {
        "persons": set(),
        "places": set(),
        "ships": set(),
        "organizations": set()
    }

    for result in results:
        if result.get("success"):
            entities = result.get("entities", {})
            for entity_type in all_entities.keys():
                all_entities[entity_type].update(entities.get(entity_type, []))

    print("ENTITIES EXTRACTED (5 pages):")
    print(f"  Unique persons: {len(all_entities['persons'])}")
    print(f"  Unique places: {len(all_entities['places'])}")
    print(f"  Unique ships: {len(all_entities['ships'])}")
    print(f"  Unique organizations: {len(all_entities['organizations'])}")
    print(f"  Total unique entities: {sum(len(v) for v in all_entities.values())}")
    print()

    # Save results
    output_file = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/nimitz_ocr_gemini/test_5pages_results.json")
    with open(output_file, 'w') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "model": model,
            "pages_tested": 5,
            "results": results,
            "summary": {
                "successful": sum(1 for r in results if r.get('success')),
                "failed": sum(1 for r in results if not r.get('success')),
                "total_cost": total_cost,
                "total_time": total_time,
                "avg_cost_per_page": total_cost / 5,
                "avg_time_per_page": total_time / 5,
                "extrapolated_full_cost": (total_cost / 5) * 4023 if total_cost > 0 else 0,
                "extrapolated_full_time_hours": ((total_time / 5) * 4023) / 3600 if total_time > 0 else 0
            },
            "sample_entities": {
                "persons": sorted(list(all_entities['persons'])),
                "places": sorted(list(all_entities['places'])),
                "ships": sorted(list(all_entities['ships'])),
                "organizations": sorted(list(all_entities['organizations']))
            }
        }, f, indent=2)

    print(f"✓ Results saved: {output_file}")
    print()
    print("=" * 80)

    # Show sample entities
    if len(all_entities['persons']) > 0:
        print("\nSAMPLE EXTRACTED ENTITIES:")
        print(f"\nPersons (showing up to 10):")
        for person in sorted(list(all_entities['persons']))[:10]:
            print(f"  - {person}")

        print(f"\nPlaces (showing up to 10):")
        for place in sorted(list(all_entities['places']))[:10]:
            print(f"  - {place}")

        print(f"\nShips (showing up to 10):")
        for ship in sorted(list(all_entities['ships']))[:10]:
            print(f"  - {ship}")

        print(f"\nOrganizations (showing up to 10):")
        for org in sorted(list(all_entities['organizations']))[:10]:
            print(f"  - {org}")

    print("\n" + "=" * 80)

    return results


if __name__ == "__main__":
    test_entity_extraction_5_pages()