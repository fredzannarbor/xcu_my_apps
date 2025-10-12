#!/usr/bin/env python3
"""
Fix all prompts files to ensure they have prompt_keys and reprompt_keys arrays.

This script scans prompts/ and imprints/ directories for JSON files that should be prompts files,
checks if they have the required structure, and fixes them if needed.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Set
import argparse

# Standard prompt keys that should be available in most prompts files
STANDARD_PROMPT_KEYS = [
    "gemini_get_basic_info",
    "bibliographic_key_phrases",
    "storefront_get_en_metadata",
    "imprint_quotes_prompt",
    "mnemonics_prompt",
    "bibliography_prompt",
    "back_cover_text"
]

# Keys that are commonly re-prompted
STANDARD_REPROMPT_KEYS = [
    "mnemonics_prompt"
]

def is_prompts_file(file_path: Path) -> bool:
    """Determine if a JSON file is likely a prompts file."""
    if file_path.name == "prompts.json":
        return True

    # Check if file contains prompt-like structures
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Look for prompt-like keys (objects with 'messages' field)
        prompt_like_keys = 0
        for key, value in data.items():
            if isinstance(value, dict) and 'messages' in value:
                prompt_like_keys += 1

        # If it has multiple prompt-like keys, it's probably a prompts file
        return prompt_like_keys >= 2

    except Exception:
        return False

def analyze_prompts_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a prompts file and return its structure."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return {
            'valid_json': False,
            'error': str(e),
            'has_prompt_keys': False,
            'has_reprompt_keys': False,
            'prompt_definitions': [],
            'needs_fixing': True
        }

    # Find all prompt definitions (objects with 'messages' field)
    prompt_definitions = []
    for key, value in data.items():
        if isinstance(value, dict) and 'messages' in value:
            prompt_definitions.append(key)

    has_prompt_keys = 'prompt_keys' in data and isinstance(data['prompt_keys'], list)
    has_reprompt_keys = 'reprompt_keys' in data and isinstance(data['reprompt_keys'], list)

    # Check if current prompt_keys match available definitions
    valid_prompt_keys = True
    if has_prompt_keys:
        for key in data['prompt_keys']:
            if key not in prompt_definitions:
                valid_prompt_keys = False
                break

    needs_fixing = not (has_prompt_keys and has_reprompt_keys) or not valid_prompt_keys

    return {
        'valid_json': True,
        'has_prompt_keys': has_prompt_keys,
        'has_reprompt_keys': has_reprompt_keys,
        'prompt_definitions': prompt_definitions,
        'current_prompt_keys': data.get('prompt_keys', []),
        'current_reprompt_keys': data.get('reprompt_keys', []),
        'valid_prompt_keys': valid_prompt_keys,
        'needs_fixing': needs_fixing,
        'data': data
    }

def fix_prompts_file(file_path: Path, analysis: Dict[str, Any], dry_run: bool = False) -> bool:
    """Fix a prompts file by adding/correcting prompt_keys and reprompt_keys."""
    if not analysis['valid_json']:
        print(f"❌ Cannot fix {file_path}: {analysis['error']}")
        return False

    data = analysis['data']
    prompt_definitions = analysis['prompt_definitions']

    # Determine appropriate prompt_keys
    if not analysis['has_prompt_keys'] or not analysis['valid_prompt_keys']:
        # Use available prompt definitions, prioritizing standard keys
        new_prompt_keys = []

        # Add standard keys that exist in definitions
        for key in STANDARD_PROMPT_KEYS:
            if key in prompt_definitions:
                new_prompt_keys.append(key)

        # Add any other prompt definitions not in standard list
        for key in prompt_definitions:
            if key not in new_prompt_keys:
                new_prompt_keys.append(key)

        data['prompt_keys'] = new_prompt_keys
        print(f"  ✅ Added/fixed prompt_keys: {new_prompt_keys}")

    # Determine appropriate reprompt_keys
    if not analysis['has_reprompt_keys']:
        # Use standard reprompt keys that exist in prompt_keys
        new_reprompt_keys = []
        for key in STANDARD_REPROMPT_KEYS:
            if key in data.get('prompt_keys', []):
                new_reprompt_keys.append(key)

        data['reprompt_keys'] = new_reprompt_keys
        print(f"  ✅ Added reprompt_keys: {new_reprompt_keys}")

    # Add metadata if missing
    if '_metadata' not in data:
        data['_metadata'] = {
            "fixed_by_script": True,
            "fixed_at": "2025-09-26T07:00:00.000000"
        }
    elif isinstance(data['_metadata'], dict):
        data['_metadata']['fixed_by_script'] = True
        data['_metadata']['fixed_at'] = "2025-09-26T07:00:00.000000"

    if dry_run:
        print(f"  🔍 DRY RUN: Would save fixed file to {file_path}")
        return True

    # Save the fixed file
    try:
        # Create backup
        backup_path = file_path.with_suffix('.json.backup')
        if not backup_path.exists():
            with open(file_path, 'r', encoding='utf-8') as src, open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
            print(f"  💾 Created backup: {backup_path}")

        # Save fixed file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"  ✅ Fixed and saved: {file_path}")
        return True

    except Exception as e:
        print(f"  ❌ Failed to save {file_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Fix prompts files to ensure they have prompt_keys and reprompt_keys"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )

    args = parser.parse_args()

    print("🔍 Scanning for prompts files...")

    # Find all potential prompts files
    prompts_files = []

    # Scan prompts/ directory
    prompts_dir = Path("prompts")
    if prompts_dir.exists():
        for json_file in prompts_dir.glob("*.json"):
            if is_prompts_file(json_file):
                prompts_files.append(json_file)

    # Scan imprints/ directory
    imprints_dir = Path("imprints")
    if imprints_dir.exists():
        for json_file in imprints_dir.glob("**/prompts.json"):
            prompts_files.append(json_file)

    print(f"📋 Found {len(prompts_files)} prompts files to check")

    # Analyze and fix each file
    files_needing_fix = 0
    files_fixed = 0

    for file_path in prompts_files:
        print(f"\n📄 Checking: {file_path}")

        analysis = analyze_prompts_file(file_path)

        if args.verbose:
            print(f"  Valid JSON: {analysis['valid_json']}")
            print(f"  Has prompt_keys: {analysis['has_prompt_keys']}")
            print(f"  Has reprompt_keys: {analysis['has_reprompt_keys']}")
            print(f"  Prompt definitions: {len(analysis.get('prompt_definitions', []))}")

        if analysis['needs_fixing']:
            files_needing_fix += 1
            print(f"  ⚠️ Needs fixing")

            if fix_prompts_file(file_path, analysis, args.dry_run):
                files_fixed += 1
        else:
            print(f"  ✅ Already correct")

    print(f"\n📊 Summary:")
    print(f"   Files checked: {len(prompts_files)}")
    print(f"   Files needing fix: {files_needing_fix}")
    print(f"   Files {'would be ' if args.dry_run else ''}fixed: {files_fixed}")

    if args.dry_run:
        print(f"\n🔍 This was a dry run. Use without --dry-run to apply fixes.")

if __name__ == "__main__":
    main()