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

# Run the pipeline to test the compile log feature
uv run run_book_pipeline.py \
  --imprint xynapse_traces \
  --schedule-file data/books.csv \
  --model "gemini/gemini-2.5-pro" \
  --max-books 1 \
  --start-stage 3 \
  --end-stage 3 \
  --skip-lsi

# Find and display the compile log
echo "Looking for compile log files..."
find output/.build -name "compile_log_*.log" | sort -r | head -n 1 | xargs cat