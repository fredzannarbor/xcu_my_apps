#!/bin/bash
# Setup cron job for Xynapse Traces Queue Agent

echo "🤖 Setting up Xynapse Traces Queue Agent (Queue Mode)"
echo ""
echo "This will add a cron job to queue tasks daily at 9:00 AM"
echo "You execute them later with: /xynapse command in Claude Code"
echo ""

# Path to the agent script
AGENT_SCRIPT="/Users/fred/xcu_my_apps/nimble/codexes-factory/xynapse_traces_queue_agent.py"
PYTHON_PATH="/usr/bin/python3"
LOG_DIR="/Users/fred/xcu_my_apps/nimble/codexes-factory/imprints/xynapse_traces/agent_queue"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Cron entry - runs at 9 AM daily in QUEUE mode
CRON_ENTRY="0 9 * * * $PYTHON_PATH $AGENT_SCRIPT queue >> $LOG_DIR/queue_cron_log.txt 2>&1"

echo "The following cron entry will be added:"
echo "$CRON_ENTRY"
echo ""

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -q "xynapse_traces_queue_agent.py"; then
    echo "⚠️  Cron job already exists!"
    echo ""
    echo "Current crontab entries for this agent:"
    crontab -l 2>/dev/null | grep "xynapse_traces_queue_agent.py"
    echo ""
    read -p "Do you want to update it? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    # Remove existing entry
    crontab -l 2>/dev/null | grep -v "xynapse_traces_queue_agent.py" | crontab -
fi

# Add new cron entry
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron job added successfully!"
echo ""
echo "📋 How it works:"
echo "  1. Every day at 9 AM, one task is selected and queued"
echo "  2. No API calls are made (no cost)"
echo "  3. Tasks accumulate in the queue"
echo "  4. When ready, run: /xynapse in Claude Code"
echo "  5. I'll execute all queued tasks using Claude Max (free)"
echo ""
echo "📊 Check queue status: $AGENT_SCRIPT status"
echo "🔍 View queue log: cat $LOG_DIR/queue_cron_log.txt"
echo "⚡ Execute queue: /xynapse (in Claude Code)"
echo ""
