#!/bin/bash

# Daily Engine Runner Script
# This script starts the Daily Engine dashboard

echo "🚀 Starting Daily Engine..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install requirements if needed
if [ ! -f ".venv/installed" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
    touch .venv/installed
fi

# Run the Streamlit app
echo "🎯 Opening Daily Engine dashboard..."
streamlit run daily_engine.py --server.port 8508

echo "✅ Daily Engine session complete!"