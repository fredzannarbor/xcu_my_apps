#!/bin/bash
# Activate the virtual environment
source .venv/bin/activate

# Run the direct mnemonics test script
echo "Running direct mnemonics test..."
uv run test_mnemonics_direct.py

# If successful, run the pipeline with the updated book data
if [ -f "output/debug/book_with_mnemonics.json" ]; then
  echo "Mnemonics generated successfully. Running pipeline with updated book data..."
  
  # Copy the updated book data to the processed_json directory
  cp output/debug/book_with_mnemonics.json output/xynapse_traces_build/processed_json/Martian_Self-Reliance.json
  
  # Run the pipeline
  uv run run_book_pipeline.py \
    --imprint xynapse_traces \
    --schedule-file data/books.csv \
    --model "gemini/gemini-2.5-pro" \
    --max-books 1 \
    --start-stage 3 \
    --end-stage 3 \
    --skip-lsi
else
  echo "Mnemonics generation failed. Check the output for errors."
fi