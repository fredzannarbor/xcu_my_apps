#!/bin/bash
# Uninstallation script for Fred's Unified App Runner
# Generated automatically - do not edit manually

set -e

echo "Uninstalling Fred's Unified App Runner..."

# Uninstall launchctl services
echo "Removing launchctl services..."
python3 deployment/macos_launchctl.py uninstall

echo "Uninstallation complete!"
echo ""
echo "Note: Configuration files and logs have been preserved."
echo "To remove completely, delete:"
echo "  - $HOME/Library/Logs/FredApps/"
echo "  - ~/bin/all_applications_runner"
