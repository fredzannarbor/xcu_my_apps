#!/bin/bash
# Setup cron jobs for all enabled imprint queue agents

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
AGENT_SCRIPT="$SCRIPT_DIR/imprint_queue_agent.py"
PYTHON_PATH="/opt/homebrew/bin/python3"
LOG_DIR="$SCRIPT_DIR/logs"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "============================================================"
echo "Imprint Queue Agents - Cron Setup"
echo "============================================================"
echo ""

# Get list of enabled imprints
IMPRINTS=$($PYTHON_PATH "$AGENT_SCRIPT" list | grep "✓ ENABLED" | awk '{print $3}')

if [ -z "$IMPRINTS" ]; then
    echo "❌ No enabled imprints found!"
    exit 1
fi

echo "Found enabled imprints:"
for imprint in $IMPRINTS; do
    echo "  - $imprint"
done
echo ""

# Remove existing imprint agent cron entries
echo "Removing existing imprint agent cron entries..."
crontab -l 2>/dev/null | grep -v "imprint_queue_agent.py" | crontab - 2>/dev/null || true

# Add cron entry for each enabled imprint
echo "Adding cron entries..."
for imprint in $IMPRINTS; do
    # Run at 9 AM daily for each imprint
    CRON_ENTRY="0 9 * * * $PYTHON_PATH $AGENT_SCRIPT queue $imprint >> $LOG_DIR/${imprint}_queue.log 2>&1"

    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

    echo "✓ Added cron job for $imprint (runs daily at 9:00 AM)"
done

echo ""
echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo ""
echo "📅 All enabled imprints will queue one task daily at 9:00 AM"
echo "📋 View logs: ls -la $LOG_DIR/*_queue.log"
echo ""
echo "To verify cron jobs:"
echo "  crontab -l | grep imprint_queue_agent"
echo ""
echo "To manually queue a task:"
echo "  $PYTHON_PATH $AGENT_SCRIPT queue <imprint_name>"
echo ""
echo "To check queue status:"
echo "  $PYTHON_PATH $AGENT_SCRIPT status <imprint_name>"
echo ""
