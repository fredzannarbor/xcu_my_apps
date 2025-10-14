# Xynapse Traces Queue Agent 🤖

**Queue-based autonomous agent that builds Xynapse Traces momentum daily using Claude Max (free for you!)**

## How It Works - The Full Workflow

### Step 1: Daily Queueing (Automatic via Cron)
```
Every day at 9:00 AM:
├─ Cron runs the agent in QUEUE mode
├─ Agent intelligently selects 1 task from 16 options
├─ Task details + prompt are added to queue
├─ NO API calls made = $0 cost
└─ Takes < 1 second
```

### Step 2: Batch Execution (When You're Ready)
```
When convenient (weekly, bi-weekly, etc.):
├─ You open Claude Code
├─ Say: "/xynapse" or "execute xynapse queue"
├─ I (Claude) process ALL queued tasks using my Claude Max brain
├─ Generate high-quality content for each task
├─ Save everything to organized directories
├─ Mark tasks as completed
└─ FREE - uses included Claude Max capacity
```

## Benefits of This Approach

✅ **Zero API Costs** - Queue mode uses no external APIs
✅ **Claude Max Quality** - I generate content using my full capabilities
✅ **Batch Efficiency** - Process multiple tasks in one session
✅ **Flexible Timing** - Execute when convenient for you
✅ **Smart Selection** - Tasks are intelligently varied to avoid repetition
✅ **Organized Output** - Everything saved to proper directories
✅ **Complete Logging** - Full history of what was generated

## The 16 Tasks

### Content Creation (4 tasks)
1. Social media post about catalog book
2. Blog post on pilsa/transcriptive meditation
3. Newsletter book spotlight
4. Themed reading list

### Catalog Development (4 tasks)
5. Back cover copy
6. Metadata improvements
7. Publisher's note
8. Author bio enhancement

### Marketing & Discovery (4 tasks)
9. Amazon A+ content
10. Book comparison chart
11. Retailer pitch
12. Reader testimonial request template

### Strategic Development (4 tasks)
13. New book topic ideas
14. Educational content about imprint mission
15. Partnership opportunity brief
16. Seasonal catalog promotion

## Setup

### 1. Install the Cron Job
```bash
cd /Users/fred/xcu_my_apps/nimble/codexes-factory
./setup_queue_agent_cron.sh
```

This adds a daily cron job that queues one task each morning at 9 AM.

### 2. Verify Cron is Running
```bash
crontab -l | grep xynapse
```

You should see:
```
0 9 * * * /usr/bin/python3 /Users/fred/xcu_my_apps/nimble/codexes-factory/xynapse_traces_queue_agent.py queue >> ...
```

## Daily Usage

### Morning (Automatic)
Nothing! Cron handles it. Tasks queue up automatically.

### When Ready to Execute (Your Choice)
```bash
# Option 1: In Claude Code, just say:
"/xynapse"

# Option 2: Or type:
"execute xynapse queue"

# Option 3: Or manually check first:
python3 xynapse_traces_queue_agent.py status
# Then: /xynapse
```

## Command Reference

### Queue Mode (Automatic via Cron)
```bash
python3 xynapse_traces_queue_agent.py queue
```
Selects and queues one task. No API calls.

### Check Status
```bash
python3 xynapse_traces_queue_agent.py status
```
Shows pending and completed tasks.

### Prepare for Execution
```bash
python3 xynapse_traces_queue_agent.py execute
```
Exports queue to JSON for Claude Code execution.

### Execute Queue (in Claude Code)
```
/xynapse
```
I'll process all pending tasks using Claude Max.

## File Locations

```
imprints/xynapse_traces/
├── agent_queue/
│   ├── task_queue.json              # Queue of pending/completed tasks
│   ├── claude_execution_batch.json   # Export for Claude execution
│   └── queue_cron_log.txt           # Cron execution log
└── agent_outputs/
    ├── agent_log.json               # Complete execution history
    ├── social_media/                # Social posts
    ├── blog_posts/                  # Blog content
    ├── newsletters/                 # Book spotlights
    ├── reading_lists/               # Curated lists
    ├── back_cover_copy/             # Book copy
    ├── metadata/                    # Metadata improvements
    ├── publishers_notes/            # Publisher's notes
    ├── author_bios/                 # Author bios
    ├── amazon_content/              # A+ content
    ├── comparisons/                 # Comparison charts
    ├── retailer_pitches/            # Retail pitches
    ├── templates/                   # Request templates
    ├── strategic/                   # New topic ideas
    ├── mission/                     # Mission content
    ├── partnerships/                # Partnership briefs
    └── promotions/                  # Seasonal promotions
```

## Example Workflow

### Week 1
```
Monday 9 AM:   Task queued (social post)
Tuesday 9 AM:  Task queued (metadata improvement)
Wednesday 9 AM: Task queued (blog post)
Thursday 9 AM: Task queued (back cover copy)
Friday 9 AM:   Task queued (Amazon A+ content)

Friday afternoon:
> /xynapse
✅ Executed 5 tasks in 2 minutes using Claude Max
📁 All content saved and ready to use
```

### Benefits
- 5 quality pieces of content created
- $0 in API costs
- 2 minutes of your time
- All using Claude Max capabilities

## Monitoring

### Check What's Queued
```bash
python3 xynapse_traces_queue_agent.py status
```

### View Cron Log
```bash
tail -20 imprints/xynapse_traces/agent_queue/queue_cron_log.txt
```

### See Execution History
```bash
cat imprints/xynapse_traces/agent_outputs/agent_log.json | python3 -m json.tool | tail -50
```

### Count Tasks by Category
```bash
grep '"category"' imprints/xynapse_traces/agent_outputs/agent_log.json | sort | uniq -c
```

## Customization

### Change Queue Time
```bash
crontab -e
```
Change first two numbers (MIN HOUR):
- `0 9 * * *` = 9:00 AM daily (default)
- `0 18 * * *` = 6:00 PM daily
- `0 9 * * 1-5` = 9:00 AM weekdays only

### Adjust Task Frequencies
Edit `xynapse_traces_queue_agent.py`:
```python
{
    "name": "Task name",
    "frequency": "high",  # high=3x, medium=2x, low=1x weight
    ...
}
```

### Queue Multiple Tasks Daily
Modify cron to run multiple times:
```
0 9 * * * python3 .../xynapse_traces_queue_agent.py queue
0 15 * * * python3 .../xynapse_traces_queue_agent.py queue
```

## Troubleshooting

### Cron Not Running
```bash
# Check cron exists
crontab -l | grep xynapse

# View cron log
tail -50 imprints/xynapse_traces/agent_queue/queue_cron_log.txt

# Test manual queue
python3 xynapse_traces_queue_agent.py queue
```

### Queue Not Building
```bash
# Check if tasks are being queued
python3 xynapse_traces_queue_agent.py status

# Check queue file directly
cat imprints/xynapse_traces/agent_queue/task_queue.json
```

### Execution Issues
- Make sure you say "/xynapse" in Claude Code (not in terminal)
- Check that queue file exists and has pending tasks
- Verify output directories have write permissions

## FAQ

### Q: How much does this cost?
**A:** $0. Queue mode has no API costs. Execution uses Claude Max which is included with Claude Code.

### Q: How often should I execute the queue?
**A:** Your choice! Weekly works well (5-7 tasks at once). Monthly is fine too (20-30 tasks).

### Q: Can I queue more than one task per day?
**A:** Yes! Modify the cron job to run multiple times daily, or manually run `python3 xynapse_traces_queue_agent.py queue`

### Q: What if I want to execute just one task?
**A:** Currently processes all pending tasks. If you only want one, execute after just 1-2 days of queueing.

### Q: Can I preview tasks before executing?
**A:** Yes! Run `python3 xynapse_traces_queue_agent.py execute` to create the batch file, then read it before saying "/xynapse"

### Q: What if I don't like a queued task?
**A:** Edit `agent_queue/task_queue.json` and remove it before executing.

## Philosophy

This queue-based approach embodies sustainable creativity:

- **Daily momentum** without daily pressure
- **Quality content** without burning out
- **Smart automation** without sacrificing control
- **Free execution** using Claude Max
- **Batch processing** for efficiency

Just like pilsa (필사) builds understanding through regular practice, this agent builds your imprint through consistent, thoughtful work—on your schedule.

---

**Created**: October 2025
**Maintainer**: Fred Zimmerman
**License**: Proprietary (Nimble Books LLC)
