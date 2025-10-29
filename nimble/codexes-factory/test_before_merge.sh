#!/bin/bash
# Comprehensive testing script before merging to clean-production
# Run this before merging any feature branch

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                          ║"
echo "║              🧪 REGRESSION TEST SUITE FOR CLEAN-PRODUCTION               ║"
echo "║                                                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

FAILED_TESTS=0
PASSED_TESTS=0

# Test 1: Python Syntax (Core Pipeline Files Only)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  TEST 1: Python Syntax Validation (Core Pipeline)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
# Test only core pipeline files to avoid pre-existing page UI issues
SYNTAX_ERRORS=0
for file in src/codexes/modules/builders/llm_get_book_data.py \
            src/codexes/core/llm_integration.py \
            src/codexes/core/prompt_manager.py \
            src/codexes/modules/prepress/markdown_to_latex.py \
            imprints/nimble_ultra/prepress.py \
            run_book_pipeline.py; do
    if ! python3 -m py_compile "$file" 2>/dev/null; then
        echo "  ❌ Syntax error in $file"
        ((SYNTAX_ERRORS++))
    fi
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    echo "✅ PASS: Core pipeline syntax valid"
    ((PASSED_TESTS++))
else
    echo "❌ FAIL: $SYNTAX_ERRORS syntax errors in core files"
    ((FAILED_TESTS++))
fi
echo ""

# Test 2: Critical Imports (using uv environment)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  TEST 2: Critical Module Imports"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
PYTHONPATH="$PWD/src:$PYTHONPATH" uv run python << 'PYEOF'
import sys
errors = []

try:
    from codexes.modules.builders import llm_get_book_data
except ImportError as e:
    errors.append(f"llm_get_book_data: {e}")

try:
    from codexes.core import llm_integration
except ImportError as e:
    errors.append(f"llm_integration: {e}")

try:
    from codexes.modules.prepress import markdown_to_latex
except ImportError as e:
    errors.append(f"markdown_to_latex: {e}")

try:
    from imprints.nimble_ultra.prepress import NimbleUltraGlobalProcessor
except ImportError as e:
    errors.append(f"NimbleUltraGlobalProcessor: {e}")

if errors:
    print("❌ FAIL: Import errors:")
    for e in errors:
        print(f"   • {e}")
    sys.exit(1)
else:
    print("✅ PASS: All critical imports successful")
PYEOF

if [ $? -eq 0 ]; then
    ((PASSED_TESTS++))
else
    ((FAILED_TESTS++))
fi
echo ""

# Test 3: Nimble Ultra Configuration
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  TEST 3: Nimble Ultra Configuration Integrity"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
PYTHONPATH="$PWD/src:$PWD:$PYTHONPATH" python3 << 'PYEOF'
import json
import sys
from pathlib import Path

errors = []
warnings = []

# Check prompts.json
prompts_path = Path('imprints/nimble_ultra/prompts.json')
with open(prompts_path) as f:
    prompts = json.load(f)

# Required keys
required_keys = ['publishers_note', 'abstracts_x4', 'mnemonics_prompt',
                 'most_important_passages_with_reasoning', 'index_of_persons', 'index_of_places']

for key in required_keys:
    if key not in prompts.get('prompt_keys', []):
        errors.append(f"Missing required prompt key: {key}")

# Check for old terminology
if 'motivation' in prompts.get('prompt_keys', []):
    errors.append("Old 'motivation' key still present (should be 'publishers_note')")

# Check structured format in abstracts
if 'abstracts_x4' in prompts:
    content = str(prompts['abstracts_x4'])
    if 'tldr' not in content or 'executive_summary' not in content:
        warnings.append("Abstracts prompt may not use structured format")

# Check structured format in mnemonics
if 'mnemonics_prompt' in prompts:
    content = str(prompts['mnemonics_prompt'])
    if 'acronym' not in content or 'items' not in content:
        warnings.append("Mnemonics prompt may not use structured format")

# Check prepress.py
prepress_path = Path('imprints/nimble_ultra/prepress.py')
with open(prepress_path) as f:
    prepress_content = f.read()

required_methods = ['_render_structured_abstracts', '_render_structured_mnemonics',
                    '_format_publishers_note_signature']
for method in required_methods:
    if f'def {method}' not in prepress_content:
        errors.append(f"Missing required method in prepress.py: {method}")

# Check field mapping in llm_get_book_data.py
llm_path = Path('src/codexes/modules/builders/llm_get_book_data.py')
with open(llm_path) as f:
    llm_content = f.read()

if "'publishers_note': 'publishers_note'" not in llm_content:
    errors.append("Missing publishers_note field mapping in llm_get_book_data.py")

if "'abstracts': 'abstracts_x4'" not in llm_content:
    warnings.append("Missing abstracts field mapping (needed for structured format)")

# Report results
if errors:
    print("❌ FAIL: Configuration errors:")
    for e in errors:
        print(f"   • {e}")
    sys.exit(1)

if warnings:
    print("⚠️  WARNINGS:")
    for w in warnings:
        print(f"   • {w}")

if not errors:
    print("✅ PASS: Nimble Ultra configuration intact")
PYEOF

if [ $? -eq 0 ]; then
    ((PASSED_TESTS++))
else
    ((FAILED_TESTS++))
fi
echo ""

# Test 4: Pipeline Smoke Test (using uv)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  TEST 4: Pipeline Smoke Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "(Checking that pipeline script loads without errors)"

PYTHONPATH="$PWD/src:$PYTHONPATH" uv run python -c "
import sys
try:
    # Try to import the pipeline script
    sys.path.insert(0, '$PWD')
    import run_book_pipeline
    print('✅ PASS: Pipeline script loads successfully')
except Exception as e:
    print(f'❌ FAIL: Pipeline script error: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    ((PASSED_TESTS++))
else
    ((FAILED_TESTS++))
fi
echo ""

# Final Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Tests Passed: $PASSED_TESTS"
echo "Tests Failed: $FAILED_TESTS"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo "✅ ALL TESTS PASSED - Safe to merge to clean-production"
    echo ""
    exit 0
else
    echo "❌ TESTS FAILED - DO NOT merge to clean-production"
    echo ""
    exit 1
fi
