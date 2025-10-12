#!/bin/bash
# Script to run both mnemonic test scripts and compare the results

echo "===== Running test_mnemonic_prompt_preparation.py ====="
python test_mnemonic_prompt_preparation.py --book-json sample_book.json --output prompt_prep_output.txt

echo ""
echo "===== Running test_mnemonic_llm_call.py ====="
python test_mnemonic_llm_call.py --book-json sample_book.json --output llm_call_output.json

echo ""
echo "===== Comparing Results ====="
echo "Check if book content is properly included in both outputs."
echo "If one test passes and the other fails, there's a discrepancy in how the content is prepared."