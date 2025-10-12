#!/bin/bash
# Activate the virtual environment
source .venv/bin/activate

# First, run the pipeline to generate quotes
echo "Step 1: Running pipeline to generate quotes..."
uv run run_book_pipeline.py \
  --imprint xynapse_traces \
  --schedule-file data/books.csv \
  --model "gemini/gemini-2.5-pro" \
  --max-books 1 \
  --only-run-prompts "imprint_quotes_prompt" \
  --quotes-per-book 7 \
  --start-stage 1 \
  --end-stage 1 \
  --skip-lsi

# Then run the debug script to generate mnemonics
echo "Step 2: Running debug script to generate mnemonics..."
uv run debug_mnemonics.py

# Finally, run the pipeline again with the updated book data
echo "Step 3: Running pipeline with updated book data..."
uv run run_book_pipeline.py \
  --imprint xynapse_traces \
  --schedule-file data/books.csv \
  --model "gemini/gemini-2.5-pro" \
  --max-books 1 \
  --start-stage 3 \
  --end-stage 3 \
  --skip-lsi