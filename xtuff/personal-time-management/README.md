# Daily Engine - Life Automation System

A Python/Streamlit dashboard that automates SaaS project advancement and transforms intermittent positive behaviors into consistent daily habits.

## Quick Start

1. **Run the Daily Engine:**
   ```bash
   ./run_daily_engine.sh
   ```
   This will open your dashboard at `http://localhost:8501`

2. **Test Overnight Automation:**
   ```bash
   python automation/overnight_automation.py
   ```

3. **Test Notifications:**
   ```bash
   python notifications/ios_notifications.py
   ```

## Features

### 🚀 SaaS Project Integration
- **Nimble Books**: Automated book pipeline monitoring
- **xtuff.ai**: Collectibles platform status checks  
- **altDOGE**: Governance platform monitoring
- **xstack**: Newsletter builder integration

### 🎯 Smart Habit Tracking
- **Consistent Habits**: Reading, writing, coding, social media (daily)
- **Intermittent Habits**: Exercise, human connection, revenue activities, healthy eating (smart scheduled)
- **Habit Stacking**: Attach new behaviors to existing consistent ones

### 💰 Revenue Optimization
- Daily micro-tasks for revenue generation
- Guidance request tracking
- Project revenue monitoring

### 📱 Notification System
- macOS notifications (iOS integration ready)
- Habit reminders based on your patterns
- SaaS project status alerts
- Revenue opportunity notifications

## Daily Workflow

### Morning (2 minutes)
1. Open IDE → Dashboard auto-launches
2. Review overnight automation results
3. See today's prioritized tasks
4. Check habit schedule

### Throughout Day
- Complete habits as scheduled
- Respond to notifications
- Log revenue activities

### Evening (1 minute)
- Quick progress review
- Set tomorrow's priorities

## File Structure

```
daily_engine/
├── daily_engine.py              # Main Streamlit dashboard
├── automation/
│   ├── saas_automation.py       # SaaS project automation
│   └── overnight_automation.py  # Scheduled automation runner
├── habits/
│   └── habit_tracker.py         # Smart habit tracking system
├── notifications/
│   └── ios_notifications.py     # Notification system
├── run_daily_engine.sh          # Quick start script
└── daily_engine.db              # SQLite database (auto-created)
```

## Integration Points

The system integrates with your existing projects:
- `/Users/fred/my-organizations/nimble/repos/codexes-factory`
- `/Users/fred/my-organizations/xtuff`
- `/Users/fred/my-organizations/altDOGE`
- `/Users/fred/my-organizations/trillionsofpeople`

## Customization

Edit the configuration in `daily_engine.py`:
- `PROJECT_PATHS`: Update paths to your projects
- `HABITS`: Modify habit lists and scheduling rules
- Add new automation scripts in `automation/`

## Next Steps

1. **Test the basic dashboard** - Run it and see how it feels
2. **Customize project integrations** - Add specific commands for your SaaS projects
3. **Set up automation scheduling** - Use cron or launchd for overnight runs
4. **Configure iOS notifications** - Set up proper iOS integration
5. **Add revenue tracking** - Connect to your payment systems

## Philosophy

This system leverages your existing consistent behaviors (coding, writing, reading, social media) as "anchor habits" to pull intermittent behaviors into consistency. Instead of fighting your patterns, it works with them to create sustainable automation and growth.