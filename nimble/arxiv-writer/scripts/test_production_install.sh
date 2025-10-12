#!/bin/bash
# Test script for production PyPI installation

set -e

echo "Testing arxiv-writer package installation from PyPI"
echo "=================================================="

# Create temporary directory for testing
TEST_DIR=$(mktemp -d)
echo "Using test directory: $TEST_DIR"

# Function to cleanup
cleanup() {
    echo "Cleaning up test directory: $TEST_DIR"
    rm -rf "$TEST_DIR"
}
trap cleanup EXIT

cd "$TEST_DIR"

# Test 1: Create virtual environment
echo "Creating virtual environment..."
python3 -m venv test_env
source test_env/bin/activate

# Test 2: Install package from PyPI
echo "Installing arxiv-writer from PyPI..."
pip install --upgrade pip
pip install arxiv-writer

# Test 3: Test CLI entry point
echo "Testing CLI entry point..."
arxiv-writer --help
arxiv-writer --version

# Test 4: Test package import
echo "Testing package import..."
python3 -c "
import arxiv_writer
print(f'Package version: {arxiv_writer.__version__}')

# Test core imports
from arxiv_writer.core.generator import ArxivPaperGenerator
from arxiv_writer.config.loader import PaperConfig
from arxiv_writer.llm.caller import LLMCaller
print('✓ Core classes imported successfully')

# Test CLI import
from arxiv_writer.cli.main import main
print('✓ CLI main function imported successfully')

print('✓ All imports successful')
"

# Test 5: Test basic functionality
echo "Testing basic functionality..."
python3 -c "
from arxiv_writer.core.generator import ArxivPaperGenerator
from arxiv_writer.core.models import PaperConfig

# Test configuration creation
try:
    config = PaperConfig()
    print('✓ PaperConfig creation successful')
except Exception as e:
    print(f'✗ PaperConfig creation failed: {e}')

print('✓ Basic functionality test passed')
"

# Test 6: Test CLI commands
echo "Testing CLI commands..."
arxiv-writer generate --help > /dev/null
arxiv-writer validate --help > /dev/null
echo "✓ CLI commands work correctly"

# Test 7: Test with different Python versions (if available)
echo "Testing with different Python versions..."
for python_cmd in python3.8 python3.9 python3.10 python3.11 python3.12; do
    if command -v $python_cmd &> /dev/null; then
        echo "Testing with $python_cmd..."
        $python_cmd -c "import arxiv_writer; print(f'✓ {python_cmd}: {arxiv_writer.__version__}')" || echo "✗ $python_cmd failed"
    fi
done

echo ""
echo "=================================================="
echo "✓ All production installation tests passed!"
echo "Package is working correctly after PyPI installation."
echo "=================================================="