# Xynapse Traces Daily Agent 🤖

Autonomous daily agent that moves the Xynapse Traces imprint forward with one intelligent action per day.

## Overview

Every day at 9:00 AM, this agent:
1. **Selects** one task from 16 possible options
2. **Executes** the task (generating content, analysis, or strategic work)
3. **Saves** output to organized directories
4. **Logs** what it did for tracking

## The 16 Tasks

### Content Creation (External-Facing)
1. Generate social media post about catalog book
2. Write short blog post on pilsa/transcriptive meditation
3. Create book spotlight feature for newsletter
4. Draft themed reading list from catalog

### Catalog Development
5. Write back cover copy for book needing it
6. Generate metadata improvements for book
7. Create publisher's note for book
8. Research and draft author bio enhancement

### Marketing & Discovery
9. Generate Amazon A+ content module
10. Create book comparison chart
11. Draft retailer pitch for specific book
12. Generate reader testimonial request template

### Strategic Development
13. Identify potential new book topics from trends
14. Create educational content about imprint mission
15. Generate partnership/collaboration opportunity brief
16. Develop seasonal catalog promotion concept

## How It Works

### Intelligent Selection
The agent uses weighted random selection:
- **High frequency tasks** (social media, metadata) are chosen more often
- **Recently completed tasks** get reduced weight to avoid repetition
- **Strategic tasks** are chosen less frequently but still regularly

### Output Organization
All outputs are saved to: `/imprints/xynapse_traces/agent_outputs/`

Directory structure:
```
agent_outputs/
├── agent_log.json              # Complete execution history
├── cron_log.txt               # Cron execution logs
├── social_media/              # Social posts
├── blog_posts/                # Blog content
├── newsletters/               # Newsletter spotlights
├── reading_lists/             # Curated lists
├── back_cover_copy/           # Book copy
├── metadata/                  # Metadata improvements
├── publishers_notes/          # Publisher's notes
├── author_bios/               # Author biographies
├── amazon_content/            # A+ content
├── comparisons/               # Comparison charts
├── retailer_pitches/          # Retail pitches
├── templates/                 # Request templates
├── strategic/                 # New topic ideas
├── mission/                   # Mission content
├── partnerships/              # Partnership briefs
└── promotions/                # Seasonal promotions
```

## Setup

### Automatic Setup (Recommended)
```bash
cd /Users/fred/xcu_my_apps/nimble/codexes-factory
./setup_daily_agent_cron.sh
```

### Manual Setup
1. Make the agent executable:
   ```bash
   chmod +x xynapse_traces_daily_agent.py
   ```

2. Test it:
   ```bash
   ./xynapse_traces_daily_agent.py
   ```

3. Add to cron:
   ```bash
   crontab -e
   ```

   Add this line:
   ```
   0 9 * * * /usr/bin/python3 /Users/fred/xcu_my_apps/nimble/codexes-factory/xynapse_traces_daily_agent.py >> /Users/fred/xcu_my_apps/nimble/codexes-factory/imprints/xynapse_traces/agent_outputs/cron_log.txt 2>&1
   ```

## Usage

### Check What It Did Today
```bash
# View latest log entry
tail -20 /Users/fred/xcu_my_apps/nimble/codexes-factory/imprints/xynapse_traces/agent_outputs/agent_log.json

# View cron execution log
tail -50 /Users/fred/xcu_my_apps/nimble/codexes-factory/imprints/xynapse_traces/agent_outputs/cron_log.txt
```

### Run Manually (Test or Extra Run)
```bash
cd /Users/fred/xcu_my_apps/nimble/codexes-factory
./xynapse_traces_daily_agent.py
```

### View Task History
```bash
# See all tasks completed
cat imprints/xynapse_traces/agent_outputs/agent_log.json | python3 -m json.tool

# Count tasks by category
grep '"category"' imprints/xynapse_traces/agent_outputs/agent_log.json | sort | uniq -c
```

## Customization

### Change Run Time
Edit the cron schedule:
```bash
crontab -e
```

Change the first two numbers (MIN HOUR):
- `0 9 * * *` = 9:00 AM daily
- `0 18 * * *` = 6:00 PM daily
- `0 9 * * 1-5` = 9:00 AM weekdays only
- `0 6,18 * * *` = 6:00 AM and 6:00 PM daily

### Adjust Task Frequencies
Edit `xynapse_traces_daily_agent.py` and change the `frequency` field:
- `high`: Selected often (3x weight)
- `medium`: Selected regularly (2x weight)
- `low`: Selected occasionally (1x weight)

### Add New Tasks
1. Add new task to the `self.tasks` dictionary
2. Implement the task function (follow existing patterns)
3. Agent will automatically include it in selection

## Requirements

- Python 3.12+
- pandas (for catalog reading)
- nimble-llm-caller (optional - runs in mock mode without it)

## LLM Integration

The agent uses `nimble-llm-caller` to generate content with `gpt-4o-mini` (cost-effective).

If nimble-llm-caller is not available, it runs in **mock mode** for testing.

To enable full LLM functionality:
```bash
cd /Users/fred/xcu_my_apps
uv pip install nimble-llm-caller
```

Make sure your `.env` file has LLM API keys configured.

## Monitoring

### Daily Summary Email (Optional)
To get daily email summaries, add this to the cron entry:
```bash
0 9 * * * /usr/bin/python3 /path/to/agent.py && echo "Agent completed" | mail -s "Xynapse Traces Agent Report" your@email.com
```

### Slack/Discord Notifications (Optional)
Add webhook notification to agent completion (edit the script).

## Troubleshooting

### Agent Not Running
```bash
# Check if cron job exists
crontab -l | grep xynapse

# Check cron logs
tail -50 /Users/fred/xcu_my_apps/nimble/codexes-factory/imprints/xynapse_traces/agent_outputs/cron_log.txt

# Test manual run
cd /Users/fred/xcu_my_apps/nimble/codexes-factory && ./xynapse_traces_daily_agent.py
```

### No Output Generated
- Check that catalog file exists: `imprints/xynapse_traces/books.csv`
- Verify output directory permissions
- Run manually to see error messages

### LLM Not Working
- Ensure nimble-llm-caller is installed: `pip list | grep nimble-llm-caller`
- Check `.env` file has API keys
- Verify API key is valid and has credits

## Philosophy

This agent embodies the xynapse traces mission:
- **Consistent progress** through daily action
- **Quality over quantity** - one well-executed task per day
- **Intelligent autonomy** - learns from history to vary work
- **Sustainable rhythm** - manageable daily output

Just like pilsa (필사) builds understanding through regular practice, this agent builds the imprint through consistent, thoughtful work.

---

**Created**: October 2025
**Maintainer**: Fred Zimmerman
**License**: Proprietary (Nimble Books LLC)
