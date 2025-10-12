#!/bin/bash
# Activate the virtual environment
source .venv/bin/activate

# Run the book pipeline with focus on mnemonics and quotes
uv run run_book_pipeline.py \
  --imprint xynapse_traces \
  --schedule-file data/books.csv \
  --model "gemini/gemini-2.5-pro" \
  --max-books 1 \
  --only-run-prompts "mnemonics_prompt,imprint_quotes_prompt" \
  --quotes-per-book 7 \
  --show-prompt-logs \
  --no-litellm-log \
  --skip-lsi