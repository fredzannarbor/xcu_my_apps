#!/bin/bash
# Activate the virtual environment
source .venv/bin/activate

# Run the book pipeline with focus on mnemonics and quotes
# Important: We need to include both the main prompt and reprompt for mnemonics
uv run run_book_pipeline.py \
  --imprint xynapse_traces \
  --schedule-file data/books.csv \
  --model "gemini/gemini-2.5-pro" \
  --max-books 1 \
  --start-stage 1 \
  --end-stage 3 \
  --quotes-per-book 7 \
  --show-prompt-logs \
  --no-litellm-log \
  --skip-lsi