#!/bin/bash
# Setup cron job for Xynapse Traces Daily Agent

echo "🤖 Setting up Xynapse Traces Daily Agent to run automatically"
echo ""
echo "This will add a cron job to run the agent every day at 9:00 AM"
echo ""

# Path to the agent script
AGENT_SCRIPT="/Users/fred/xcu_my_apps/nimble/codexes-factory/xynapse_traces_daily_agent.py"
PYTHON_PATH="/usr/bin/python3"
LOG_DIR="/Users/fred/xcu_my_apps/nimble/codexes-factory/imprints/xynapse_traces/agent_outputs"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Cron entry - runs at 9 AM daily
CRON_ENTRY="0 9 * * * $PYTHON_PATH $AGENT_SCRIPT >> $LOG_DIR/cron_log.txt 2>&1"

echo "The following cron entry will be added:"
echo "$CRON_ENTRY"
echo ""

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -q "xynapse_traces_daily_agent.py"; then
    echo "⚠️  Cron job already exists!"
    echo ""
    echo "Current crontab entries for this agent:"
    crontab -l 2>/dev/null | grep "xynapse_traces_daily_agent.py"
    echo ""
    read -p "Do you want to update it? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    # Remove existing entry
    crontab -l 2>/dev/null | grep -v "xynapse_traces_daily_agent.py" | crontab -
fi

# Add new cron entry
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron job added successfully!"
echo ""
echo "The agent will now run automatically every day at 9:00 AM"
echo ""
echo "To verify, run: crontab -l"
echo "To test manually, run: $AGENT_SCRIPT"
echo "To view logs, check: $LOG_DIR/cron_log.txt"
echo ""
echo "📝 To change the time, edit the cron entry:"
echo "   crontab -e"
echo ""
echo "   Cron time format: MIN HOUR DAY MONTH WEEKDAY"
echo "   Examples:"
echo "     0 9 * * *    = 9:00 AM daily"
echo "     0 18 * * *   = 6:00 PM daily"
echo "     0 9 * * 1-5  = 9:00 AM weekdays only"
echo ""
