#!/bin/bash
# Activate the virtual environment
source .venv/bin/activate

# Clear LaTeX auxiliary files and cache
echo "Clearing LaTeX cache and auxiliary files..."
find output/xynapse_traces_build -name "*.aux" -delete
find output/xynapse_traces_build -name "*.log" -delete
find output/xynapse_traces_build -name "*.toc" -delete
find output/xynapse_traces_build -name "*.out" -delete
find output/xynapse_traces_build -name "*.pdf" -delete
find output/xynapse_traces_build -name "*.synctex.gz" -delete
find output/xynapse_traces_build -name "*.fls" -delete
find output/xynapse_traces_build -name "*.fdb_latexmk" -delete

# Clear build directories
echo "Clearing build directories..."
rm -rf output/xynapse_traces_build/interior/*
rm -rf output/xynapse_traces_build/.build/*

# Run the pipeline to rebuild everything
echo "Rebuilding with clean cache..."
uv run run_book_pipeline.py \
  --imprint xynapse_traces \
  --schedule-file data/books.csv \
  --model "gemini/gemini-2.5-pro" \
  --max-books 1 \
  --start-stage 3 \
  --end-stage 3 \
  --skip-lsi

echo "Done!"