#!/bin/bash

# Streamlit startup script for Codexes Factory
echo "Starting Codexes Factory Streamlit Application..."

# Ensure we're in the project root
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Set PYTHONPATH to include src directory
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"

# Verify imports work
echo "Testing UI component imports..."
if [ -f "test_ui_imports.py" ]; then
    if uv run python test_ui_imports.py; then
        echo "✅ All imports verified successfully"
    else
        echo "❌ Import verification failed"
        exit 1
    fi
else
    echo "⚠️  Import test script not found, proceeding anyway"
fi

# Start Streamlit
echo "Starting Streamlit on http://localhost:8502"
echo "PYTHONPATH: $PYTHONPATH"
PYTHONPATH="${PWD}/src:${PYTHONPATH}" uv run streamlit run src/codexes/codexes-factory-home-ui.py \
    --server.port 8502 \
    --server.address 0.0.0.0 \
    --server.headless true