#!/bin/bash
source .venv/bin/activate
python run_book_pipeline.py \
  --imprint xynapse_traces \
  --schedule-file imprints/xynapse_traces/xynapse_traces_schedule.json \
  --start-stage 1 \
  --end-stage 4 \
  --model gemini/gemini-2.5-pro \
  --verifier-model gemini/gemini-2.5-pro \
  --enable-llm-completion \
  --enable-isbn-assignment \
  --max-books 1 \
  --model-params-file temp_model_params.json \
  --verbose