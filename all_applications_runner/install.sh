#!/bin/bash
# Installation script for Fred's Unified App Runner
# Generated automatically - do not edit manually

set -e

echo "Installing Fred's Unified App Runner..."

# Check if we're in the right directory
if [ ! -f "apps_config.json" ]; then
    echo "Error: Must run from app runner directory"
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
if command -v uv &> /dev/null; then
    uv sync
elif [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "Warning: No requirements.txt found"
fi

# Create log directory
mkdir -p "$HOME/Library/Logs/FredApps"

# Install launchctl services
echo "Installing launchctl services..."
python3 deployment/macos_launchctl.py install

echo "Installation complete!"
echo ""
echo "Services installed:"
echo "  - Master App Runner (port 8500)"
echo "  - Process Manager"
echo ""
echo "Check status with: python3 deployment/macos_launchctl.py status"
echo "View logs in: $HOME/Library/Logs/FredApps/"
echo ""
echo "Access the app runner at: http://localhost:8500"
