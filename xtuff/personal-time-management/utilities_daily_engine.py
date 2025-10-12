#!/usr/bin/env python3
"""
Daily Engine Utilities
Backend functions for database operations, reports, and system operations
"""

import sqlite3
import subprocess
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import re
from config.settings import config


def init_database():
    """Initialize SQLite database for tracking"""
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()

    # Daily sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            session_start TEXT,
            available_hours REAL,
            energy_level TEXT,
            completed_tasks TEXT,
            habit_completions TEXT,
            revenue_generated REAL DEFAULT 0.0,
            notes TEXT,
            energy_comment TEXT,
            energy_updated_at TEXT
        )
    ''')
    
    # Add energy_updated_at column if it doesn't exist (for existing databases)
    try:
        cursor.execute('ALTER TABLE daily_sessions ADD COLUMN energy_updated_at TEXT')
    except sqlite3.OperationalError:
        # Column already exists
        pass

    # SaaS project status table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saas_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT,
            date TEXT,
            last_run TEXT,
            status TEXT,
            metrics TEXT,
            action_required BOOLEAN DEFAULT 0,
            revenue_today REAL DEFAULT 0.0
        )
    ''')

    # Revenue transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS revenue_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            amount REAL,
            description TEXT,
            category TEXT,
            source TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Habit tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS habit_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_name TEXT,
            date TEXT,
            completed BOOLEAN,
            streak_count INTEGER DEFAULT 0,
            notes TEXT
        )
    ''')

    # Creative accomplishments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS creative_accomplishments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            area TEXT,
            accomplishment TEXT
        )
    ''')

    # Revenue activities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS revenue_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            activity TEXT,
            estimated_value REAL DEFAULT 0.0,
            time_spent INTEGER DEFAULT 0,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'planned',
            notes TEXT
        )
    ''')

    # User preferences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            value TEXT,
            updated_at TEXT
        )
    ''')

    conn.commit()
    conn.close()


def get_today_session():
    """Get or create today's session"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM daily_sessions WHERE date = ?', (today,))
    session = cursor.fetchone()

    if not session:
        cursor.execute('''
            INSERT INTO daily_sessions (date, session_start, available_hours, energy_level, revenue_generated)
            VALUES (?, ?, ?, ?, ?)
        ''', (today, datetime.now().strftime('%H:%M'), 4.0, 'medium', 0.0))
        conn.commit()
        cursor.execute('SELECT * FROM daily_sessions WHERE date = ?', (today,))
        session = cursor.fetchone()

    conn.close()
    return session


def update_energy_level(energy_level):
    """Update energy level for today's session"""
    today = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%H:%M')
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE daily_sessions 
        SET energy_level = ?, energy_updated_at = ?
        WHERE date = ?
    ''', (energy_level, current_time, today))

    conn.commit()
    conn.close()


def save_energy_comment(comment):
    """Save energy level comment to today's session"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()

    # Add energy_comment column if it doesn't exist
    try:
        cursor.execute('ALTER TABLE daily_sessions ADD COLUMN energy_comment TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists

    cursor.execute('''
        UPDATE daily_sessions 
        SET energy_comment = ?
        WHERE date = ?
    ''', (comment, today))

    conn.commit()
    conn.close()


def get_energy_comment():
    """Get energy comment for today's session"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT energy_comment FROM daily_sessions WHERE date = ?', (today,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else ""
    except sqlite3.OperationalError:
        # Column doesn't exist yet
        conn.close()
        return ""


def save_daily_notes(notes):
    """Save daily notes to database"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()

    # Update today's session with notes
    cursor.execute('''
        UPDATE daily_sessions 
        SET notes = ?
        WHERE date = ?
    ''', (notes, today))

    conn.commit()
    conn.close()


def get_daily_notes():
    """Get today's notes from database"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()

    cursor.execute('SELECT notes FROM daily_sessions WHERE date = ?', (today,))
    result = cursor.fetchone()

    conn.close()
    return result[0] if result and result[0] else ""


def get_quick_stats():
    """Get quick stats for today's dashboard"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()

    # Get session info including energy level and when it was last updated
    cursor.execute('SELECT session_start, revenue_generated, energy_level, energy_updated_at FROM daily_sessions WHERE date = ?', (today,))
    session_info = cursor.fetchone()
    
    if session_info:
        session_start = session_info[0]
        revenue_generated = session_info[1] if session_info[1] is not None else 0.0
        energy_level = session_info[2] if session_info[2] else "medium"
        energy_updated_at = session_info[3]
        
        # Format the energy update time more user-friendly
        try:
            if energy_updated_at:
                # If it's just time (HH:MM), add today's date
                if len(energy_updated_at) == 5 and ':' in energy_updated_at:
                    energy_updated_display = f"Today at {energy_updated_at}"
                else:
                    energy_updated_display = energy_updated_at
            elif session_start and session_start != "N/A":
                # Fallback to session start if energy_updated_at is not available
                if len(session_start) == 5 and ':' in session_start:
                    energy_updated_display = f"Session started at {session_start}"
                else:
                    energy_updated_display = session_start
            else:
                energy_updated_display = "Not updated today"
        except:
            energy_updated_display = "Not updated today"
    else:
        revenue_generated = 0.0
        energy_level = "medium"
        energy_updated_display = "Not updated today"

    # Get habit info
    cursor.execute('SELECT COUNT(*) FROM habit_tracking WHERE date = ? AND completed = 1', (today,))
    completed_habits_result = cursor.fetchone()
    completed_habits = completed_habits_result[0] if completed_habits_result else 0

    # Get total habits from config
    try:
        habits_config = config.get_habits()
        consistent_habits = habits_config.get('consistent', []) if habits_config else []
        intermittent_habits = habits_config.get('intermittent', []) if habits_config else []
        total_habits = len(consistent_habits) + len(intermittent_habits)
    except:
        total_habits = 0

    # Get creative areas info
    cursor.execute('SELECT COUNT(DISTINCT area) FROM creative_accomplishments WHERE date = ?', (today,))
    creative_areas_result = cursor.fetchone()
    creative_areas_active = creative_areas_result[0] if creative_areas_result else 0
    
    try:
        total_creative_areas = len(config.get_creative_areas())
    except:
        total_creative_areas = 0

    # Get micro-tasks info
    try:
        cursor.execute('SELECT COUNT(*) FROM micro_tasks WHERE date = ? AND completed = 1', (today,))
        completed_micro_tasks_result = cursor.fetchone()
        completed_micro_tasks = completed_micro_tasks_result[0] if completed_micro_tasks_result else 0
        
        cursor.execute('SELECT COUNT(*) FROM micro_tasks WHERE date = ?', (today,))
        total_micro_tasks_result = cursor.fetchone()
        total_micro_tasks = total_micro_tasks_result[0] if total_micro_tasks_result else 0
    except:
        completed_micro_tasks = 0
        total_micro_tasks = 0

    conn.close()

    return {
        "energy_updated_at": energy_updated_display,
        "habits_completed": f"{completed_habits}/{total_habits}",
        "revenue_generated": f"${revenue_generated:.2f}",
        "creative_areas_active": f"{creative_areas_active}/{total_creative_areas}",
        "micro_tasks_completed": f"{completed_micro_tasks}/{total_micro_tasks}"
    }


def save_creative_accomplishments(accomplishments):
    """Save creative accomplishments to database"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()

    # Delete existing accomplishments for today
    cursor.execute('DELETE FROM creative_accomplishments WHERE date = ?', (today,))

    # Insert new accomplishments
    for area, accomplishment in accomplishments.items():
        if accomplishment.strip():  # Only save non-empty accomplishments
            cursor.execute('''
                INSERT INTO creative_accomplishments (date, area, accomplishment)
                VALUES (?, ?, ?)
            ''', (today, area, accomplishment.strip()))

    conn.commit()
    conn.close()


def get_creative_accomplishments(date=None):
    """Get creative accomplishments for a specific date"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()

    cursor.execute('SELECT area, accomplishment FROM creative_accomplishments WHERE date = ?', (date,))
    results = cursor.fetchall()

    conn.close()
    return {area: accomplishment for area, accomplishment in results}


def get_revenue_activities_text():
    """Get revenue activities text for today.

    Returns:
        str: Combined text of all revenue activities for today, or empty string if none
    """
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT activity FROM revenue_activities 
            WHERE date = ? 
            ORDER BY id
        ''', (today,))

        activities = cursor.fetchall()
        # Join all activities with newlines to recreate the original text format
        return '\n'.join([activity[0] for activity in activities])

    except sqlite3.Error:
        return ""
    finally:
        conn.close()


def _extract_monetary_value(text):
    """Extract monetary value from text containing dollar amounts.

    Args:
        text (str): Text that may contain dollar amounts like '$50' or '$123.45'

    Returns:
        float: The extracted monetary value, or 0.0 if no valid amount found
    """
    value_match = re.search(r'\$(\d+(?:\.\d{2})?)', text)
    return float(value_match.group(1)) if value_match else 0.0

def save_revenue_activities(activities_text):
    """Save revenue activities from text input"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()

    # Update revenue in daily session
    total_value = 0.0
    for line in activities_text.split('\n'):
        if line.strip():
            total_value += _extract_monetary_value(line)

    if total_value > 0:
        cursor.execute('''
            UPDATE daily_sessions
            SET revenue_generated = revenue_generated + ?
            WHERE date = ?
        ''', (total_value, today))

    # Delete existing revenue activities for today
    cursor.execute('DELETE FROM revenue_activities WHERE date = ?', (today,))

    if activities_text.strip():
        # Split by lines and save each as separate activity
        activities = [line.strip() for line in activities_text.split('\n') if line.strip()]

        for activity in activities:
            # Parse potential value and time estimates from activity text
            estimated_value = _extract_monetary_value(activity)
            time_spent = 0
            priority = 'medium'

            # Look for time patterns like "2hrs" in the activity text
            time_match = re.search(r'(\d+)(?:hr|hour|min)', activity.lower())
            if time_match:
                time_spent = int(time_match.group(1))

            # Determine priority based on keywords
            if any(keyword in activity.lower() for keyword in ['urgent', 'critical', 'asap', 'priority']):
                priority = 'high'
            elif any(keyword in activity.lower() for keyword in ['later', 'low', 'minor', 'when time']):
                priority = 'low'

            cursor.execute('''
                INSERT INTO revenue_activities (date, activity, estimated_value, time_spent, priority, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (today, activity, estimated_value, time_spent, priority, 'planned'))

    conn.commit()
    conn.close()

def run_project_command(project_id, command, projects_config):
    """Run a command for a specific project"""
    try:
        project_config = projects_config.get(project_id)
        if not project_config:
            return f"Project configuration not found: {project_id}"

        project_path = project_config.get('path')
        if not project_path or not os.path.exists(project_path):
            return f"Project path not found: {project_path}"

        result = subprocess.run(
            command,
            shell=True,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        return f"Exit code: {result.returncode}\nOutput: {result.stdout}\nError: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def generate_daily_report():
    """Generate a comprehensive daily report"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()

    # Get today's session with energy comment
    try:
        cursor.execute('SELECT *, energy_comment FROM daily_sessions WHERE date = ?', (today,))
    except sqlite3.OperationalError:
        # Fallback if energy_comment column doesn't exist
        cursor.execute('SELECT * FROM daily_sessions WHERE date = ?', (today,))

    session = cursor.fetchone()

    # Get habit completions for today
    cursor.execute('SELECT habit_name, completed FROM habit_tracking WHERE date = ?', (today,))
    habits = cursor.fetchall()

    # Get SaaS project status
    cursor.execute('SELECT project_name, status, revenue_today FROM saas_status WHERE date = ?', (today,))
    projects = cursor.fetchall()

    # Get revenue activities
    cursor.execute('''
        SELECT activity, estimated_value, priority, status 
        FROM revenue_activities 
        WHERE date = ?
        ORDER BY priority DESC, estimated_value DESC
    ''', (today,))
    revenue_activities = cursor.fetchall()

    conn.close()

    # Calculate metrics
    config_habits = config.get_habits()
    total_habits = len(config_habits['consistent']) + len(config_habits['intermittent'])
    completed_habits = len([h for h in habits if h[1]]) if habits else 0
    habit_completion_rate = (completed_habits / total_habits * 100) if total_habits > 0 else 0

    total_revenue = sum([p[2] for p in projects if p[2]]) if projects else 0.0
    estimated_revenue_potential = sum([r[1] for r in revenue_activities if r[1]]) if revenue_activities else 0.0

    # Generate report
    report = f"""
# 📊 Daily Report - {today}

## ⚡ Energy & Time Management
"""

    if session:
        report += f"- **Available Hours**: {session[3]}\n"
        report += f"- **Energy Level**: {session[4].title()}\n"
        report += f"- **Session Start**: {session[2]}\n"

        # Add energy comment if it exists
        energy_comment = session[-1] if len(session) > 9 and session[-1] else None
        if energy_comment:
            report += f"- **Energy Notes**: {energy_comment}\n"

    report += f"""
## 🎯 Habit Performance
- **Completion Rate**: {habit_completion_rate:.1f}% ({completed_habits}/{total_habits})
- **Consistent Habits**: {len([h for h in habits if h[1] and h[0] in config_habits['consistent']])}/{len(config_habits['consistent'])}
- **Intermittent Habits**: {len([h for h in habits if h[1] and h[0] in config_habits['intermittent']])}/{len(config_habits['intermittent'])}

## 🚀 SaaS Projects Status
"""

    if projects:
        for project_name, status, revenue in projects:
            report += f"- **{project_name.title()}**: {status}"
            if revenue and revenue > 0:
                report += f" (${revenue:.2f})"
            report += "\n"
    else:
        report += "- No project updates recorded today\n"

    report += f"""
## 💰 Revenue Summary
- **Total Revenue Today**: ${total_revenue:.2f}
- **Revenue per Hour**: ${total_revenue / 4:.2f} (based on 4-hour work window)
- **Estimated Revenue Potential**: ${estimated_revenue_potential:.2f}
"""

    # Add revenue activities section
    if revenue_activities:
        report += f"""
## 💼 Revenue Activities Summary
- **Total Revenue Activities**: {len(revenue_activities)}


### 📋 Planned Activities
"""
        high_priority = [r for r in revenue_activities if r[2] == 'high']
        medium_priority = [r for r in revenue_activities if r[2] == 'medium']
        low_priority = [r for r in revenue_activities if r[2] == 'low']

        if high_priority:
            report += f"**🔥 High Priority:**\n"
            for activity, estimated_value, priority, status in high_priority:
                value_str = f" (${estimated_value:.2f})" if estimated_value > 0 else ""
                status_emoji = "✅" if status == 'completed' else "⏳" if status == 'in_progress' else "📋"
                report += f"- {status_emoji} {activity}{value_str}\n"

        if medium_priority:
            report += f"\n**📋 Medium Priority:**\n"
            for activity, estimated_value, priority, status in medium_priority:
                value_str = f" (${estimated_value:.2f})" if estimated_value > 0 else ""
                status_emoji = "✅" if status == 'completed' else "⏳" if status == 'in_progress' else "📋"
                report += f"- {status_emoji} {activity}{value_str}\n"

        if low_priority:
            report += f"\n**📝 Low Priority:**\n"
            for activity, estimated_value, priority, status in low_priority:
                value_str = f" (${estimated_value:.2f})" if estimated_value > 0 else ""
                status_emoji = "✅" if status == 'completed' else "⏳" if status == 'in_progress' else "📋"
                report += f"- {status_emoji} {activity}{value_str}\n"

    # Add today's notes if they exist
    if session and len(session) > 8 and session[8]:  # notes are at index 8
        report += f"""
## 📝 Today's Notes
{session[8]}
"""

    # Add creative accomplishments
    creative_work = get_creative_accomplishments(today)
    if creative_work:
        report += f"""
## 🎨 Creative Accomplishments
"""
        for area, accomplishment in creative_work.items():
            report += f"**{area}:**\n{accomplishment}\n\n"

    report += f"""
## 📈 Recommendations for Tomorrow
"""

    # Generate energy-based recommendations
    current_energy = session[4] if session else 'medium'
    if current_energy == 'low':
        report += "- **Energy Recovery**: Focus on rest and low-intensity tasks\n"
        report += "- Consider adjusting tomorrow's schedule for better energy management\n"
    elif current_energy == 'peak':
        report += "- **High Energy Day**: Great time for challenging projects and creative work\n"
        report += "- Consider tackling the most difficult items on your list\n"

    # Generate recommendations based on today's performance
    if habit_completion_rate < 50:
        report += "- Focus on completing at least 3 core habits\n"
    elif habit_completion_rate < 80:
        report += "- Good progress! Try to add one more intermittent habit\n"
    else:
        report += "- Excellent habit performance! Consider adding a new challenge\n"

    if total_revenue == 0 and not revenue_activities:
        report += "- **Revenue Focus**: Plan specific revenue-generating activities\n"
    elif revenue_activities and not any(r[3] == 'completed' for r in revenue_activities):
        report += "- **Revenue Action**: Execute planned revenue activities\n"
    elif total_revenue < 50:
        report += "- Look for higher-value revenue opportunities\n"
    else:
        report += "- Great revenue day! Scale successful activities\n"

    # Revenue-specific recommendations
    if estimated_revenue_potential > total_revenue * 2:
        report += f"- **Revenue Opportunity**: ${estimated_revenue_potential - total_revenue:.2f} in planned activities waiting\n"

    report += f"""
## 🎨 Creative Focus Areas
- Review and update SaaS project roadmaps
- Identify automation opportunities
- Plan next high-value creative project

---
*Generated at {datetime.now().strftime('%H:%M')} on {today}*
"""

    return report


def generate_weekly_report():
    """Generate a weekly report"""
    today = datetime.now()
    week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
    week_end = today.strftime('%Y-%m-%d')

    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()

    # Get habit data for the week
    cursor.execute('''
        SELECT habit_name, COUNT(*) as completed_days, 
               COUNT(CASE WHEN completed = 1 THEN 1 END) as successful_days
        FROM habit_tracking 
        WHERE date >= ? AND date <= ?
        GROUP BY habit_name
    ''', (week_start, week_end))
    habit_data = cursor.fetchall()

    # Get creative accomplishments for the week
    cursor.execute('''
        SELECT date, area, accomplishment 
        FROM creative_accomplishments 
        WHERE date >= ? AND date <= ?
        ORDER BY date DESC
    ''', (week_start, week_end))
    creative_data = cursor.fetchall()

    # Get revenue data
    cursor.execute('''
        SELECT SUM(revenue_today) as total_revenue
        FROM saas_status 
        WHERE date >= ? AND date <= ?
    ''', (week_start, week_end))
    revenue_result = cursor.fetchone()
    total_revenue = revenue_result[0] if revenue_result[0] else 0.0

    # Get revenue activities for the week
    cursor.execute('''
        SELECT date, activity, estimated_value, status
        FROM revenue_activities 
        WHERE date >= ? AND date <= ?
        ORDER BY date DESC, estimated_value DESC
    ''', (week_start, week_end))
    revenue_activities_data = cursor.fetchall()

    conn.close()

    # Calculate revenue activities metrics
    total_planned_value = sum([r[2] for r in revenue_activities_data if r[2]])
    completed_activities = [r for r in revenue_activities_data if r[3] == 'completed']
    completed_value = sum([r[2] for r in completed_activities if r[2]])

    report = f"""
# 📅 Weekly Report - {week_start} to {week_end}

## 🎯 Habit Performance This Week
"""

    if habit_data:
        for habit_name, total_days, successful_days in habit_data:
            success_rate = (successful_days / total_days * 100) if total_days > 0 else 0
            report += f"- **{habit_name.replace('_', ' ').title()}**: {successful_days}/{total_days} days ({success_rate:.1f}%)\n"
    else:
        report += "- No habit data recorded this week\n"

    report += f"""
## 💰 Revenue Activities This Week
- **Total Revenue**: ${total_revenue:.2f}
- **Planned Revenue Activities Value**: ${total_planned_value:.2f}
- **Completed Activities Value**: ${completed_value:.2f}
- **Activity Completion Rate**: {len(completed_activities)}/{len(revenue_activities_data)} ({len(completed_activities)/len(revenue_activities_data)*100 if revenue_activities_data else 0:.1f}%)
"""

    if revenue_activities_data:
        report += f"\n**📋 This Week's Revenue Activities:**\n"
        current_date = None
        for date, activity, estimated_value, status in revenue_activities_data:
            if date != current_date:
                report += f"\n**{date}:**\n"
                current_date = date

            status_emoji = "✅" if status == 'completed' else "⏳" if status == 'in_progress' else "📋"
            value_str = f" (${estimated_value:.2f})" if estimated_value > 0 else ""
            report += f"- {status_emoji} {activity}{value_str}\n"

    report += f"""
## 🎨 Creative Work This Week
"""

    if creative_data:
        current_date = None
        for date, area, accomplishment in creative_data:
            if date != current_date:
                report += f"\n**{date}:**\n"
                current_date = date
            report += f"- *{area}*: {accomplishment}\n"
    else:
        report += "- No creative work recorded this week\n"
        report += f"""
## 📊 Weekly Insights
- **Average Daily Revenue**: ${total_revenue / 7:.2f}
- **Potential Revenue Left**: ${total_planned_value - completed_value:.2f}
- **High Completion Rate**: $({len(completed_activities)}/{len(revenue_activities_data)}
---
*Generated at {datetime.now().strftime('%H:%M')} on {today.strftime('%Y-%m-%d')}*
"""

    return report


def generate_monthly_report():
    """Generate a monthly report"""
    today = datetime.now()
    month_start = today.replace(day=1).strftime('%Y-%m-%d')
    month_end = today.strftime('%Y-%m-%d')

    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()

    # Get habit statistics
    cursor.execute('''
        SELECT habit_name, 
               COUNT(*) as total_entries,
               COUNT(CASE WHEN completed = 1 THEN 1 END) as successful_days,
               MAX(streak_count) as best_streak
        FROM habit_tracking 
        WHERE date >= ? AND date <= ?
        GROUP BY habit_name
    ''', (month_start, month_end))
    habit_stats = cursor.fetchall()

    # Get total revenue
    cursor.execute('''
        SELECT SUM(revenue_today) as total_revenue, COUNT(DISTINCT date) as active_days
        FROM saas_status 
        WHERE date >= ? AND date <= ?
    ''', (month_start, month_end))
    revenue_stats = cursor.fetchone()

    # Get creative work count
    cursor.execute('''
        SELECT COUNT(DISTINCT date) as creative_days, COUNT(*) as total_accomplishments
        FROM creative_accomplishments 
        WHERE date >= ? AND date <= ?
    ''', (month_start, month_end))
    creative_stats = cursor.fetchone()

    # Get revenue activities statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total_activities,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_activities,
            SUM(estimated_value) as total_planned_value,
            SUM(CASE WHEN status = 'completed' THEN estimated_value ELSE 0 END) as completed_value,
            COUNT(DISTINCT date) as days_with_activities
        FROM revenue_activities 
        WHERE date >= ? AND date <= ?
    ''', (month_start, month_end))
    revenue_activity_stats = cursor.fetchone()

    conn.close()

    days_in_month = today.day
    total_revenue = revenue_stats[0] if revenue_stats[0] else 0.0

    report = f"""
# 📆 Monthly Report - {today.strftime('%B %Y')}

## 🎯 Habit Performance This Month
"""

    if habit_stats:
        for habit_name, total_entries, successful_days, best_streak in habit_stats:
            success_rate = (successful_days / days_in_month * 100) if days_in_month > 0 else 0
            report += f"- **{habit_name.replace('_', ' ').title()}**: {successful_days}/{days_in_month} days ({success_rate:.1f}%) | Best streak: {best_streak}\n"

    report += f"""
## 💰 Revenue Performance
- **Total Revenue**: ${total_revenue:.2f}
- **Average per Day**: ${total_revenue / days_in_month:.2f}
- **Revenue Days**: {revenue_stats[1] if revenue_stats[1] else 0}/{days_in_month}
"""

    # Initialize variables for revenue activities analysis
    completion_rate = 0
    total_planned_value = 0
    completed_value = 0
    
    # Add revenue activities analysis
    if revenue_activity_stats and revenue_activity_stats[0] > 0:
        total_activities, completed_activities, total_planned_value, completed_value, days_with_activities = revenue_activity_stats
        completion_rate = (completed_activities / total_activities * 100) if total_activities > 0 else 0

        report += f"""
## 📋 Revenue Activities Analysis
- **Total Activities Planned**: {total_activities}
- **Activities Completed**: {completed_activities} ({completion_rate:.1f}%)
- **Total Planned Value**: ${total_planned_value:.2f}
- **Completed Activity Value**: ${completed_value:.2f}
- **Days with Revenue Activities**: {days_with_activities}/{days_in_month}
- **Value Completion Rate**: {completed_value/total_planned_value*100 if total_planned_value > 0 else 0:.1f}%
- **Missed Revenue Opportunity**: ${total_planned_value - completed_value:.2f}
"""

    report += f"""
## 🎨 Creative Productivity
- **Days with creative work**: {creative_stats[1] if creative_stats else 0}/{days_in_month}
- **Total accomplishments recorded**: {creative_stats[0] if creative_stats else 0}

## 📊 Monthly Insights
"""

    # Generate insights
    if revenue_activity_stats and completion_rate < 50:
        report += f"- **Action Required**: Low revenue activity completion rate ({completion_rate:.1f}%)\n"
        report += f"- **Opportunity**: ${total_planned_value - completed_value:.2f} in missed revenue activities\n"
    elif revenue_activity_stats and completion_rate > 80:
        report += f"- **Excellent**: High revenue activity completion rate ({completion_rate:.1f}%)\n"

    if total_revenue > 0:
        monthly_avg = total_revenue
        report += f"- **Revenue Trend**: ${monthly_avg:.2f} this month\n"
        if revenue_activity_stats and completed_value > 0:
            conversion_rate = total_revenue / completed_value * 100 if completed_value > 0 else 0
            report += f"- **Activity ROI**: ${total_revenue:.2f} actual revenue from ${completed_value:.2f} activity value ({conversion_rate:.1f}% conversion)\n"

    report += f"""
---
*Generated at {datetime.now().strftime('%H:%M')} on {today.strftime('%Y-%m-%d')}*
"""

    return report


def generate_yearly_report():
    """Generate a yearly report (YTD)"""
    today = datetime.now()
    year_start = today.replace(month=1, day=1).strftime('%Y-%m-%d')
    year_end = today.strftime('%Y-%m-%d')

    conn = sqlite3.connect('daily_engine.db')
    cursor = conn.cursor()

    # Get comprehensive habit statistics
    cursor.execute('''
        SELECT habit_name, 
               COUNT(CASE WHEN completed = 1 THEN 1 END) as successful_days,
               COUNT(*) as total_tracked_days,
               MAX(streak_count) as best_streak,
               AVG(CASE WHEN completed = 1 THEN streak_count ELSE 0 END) as avg_streak
        FROM habit_tracking 
        WHERE date >= ? AND date <= ?
        GROUP BY habit_name
    ''', (year_start, year_end))
    habit_stats = cursor.fetchall()

    # Get revenue statistics
    cursor.execute('''
        SELECT SUM(revenue_today) as total_revenue, 
               AVG(revenue_today) as avg_daily_revenue,
               MAX(revenue_today) as best_day_revenue,
               COUNT(CASE WHEN revenue_today > 0 THEN 1 END) as revenue_days
        FROM saas_status 
        WHERE date >= ? AND date <= ?
    ''', (year_start, year_end))
    revenue_stats = cursor.fetchone()

    # Get creative work statistics
    cursor.execute('''
        SELECT COUNT(DISTINCT date) as creative_days, 
               COUNT(*) as total_accomplishments,
               area, COUNT(*) as area_count
        FROM creative_accomplishments 
        WHERE date >= ? AND date <= ?
        GROUP BY area
        ORDER BY area_count DESC
    ''', (year_start, year_end))
    creative_stats = cursor.fetchall()

    # Get comprehensive revenue activities statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total_activities,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_activities,
            SUM(estimated_value) as total_planned_value,
            SUM(CASE WHEN status = 'completed' THEN estimated_value ELSE 0 END) as completed_value,
            COUNT(DISTINCT date) as days_with_activities,
            AVG(estimated_value) as avg_activity_value,
            priority, COUNT(*) as priority_count
        FROM revenue_activities 
        WHERE date >= ? AND date <= ?
        GROUP BY priority
        ORDER BY priority_count DESC
    ''', (year_start, year_end))
    revenue_activity_detailed = cursor.fetchall()

    # Get total revenue activities stats
    cursor.execute('''
        SELECT 
            COUNT(*) as total_activities,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_activities,
            SUM(estimated_value) as total_planned_value,
            SUM(CASE WHEN status = 'completed' THEN estimated_value ELSE 0 END) as completed_value,
            COUNT(DISTINCT date) as days_with_activities
        FROM revenue_activities 
        WHERE date >= ? AND date <= ?
    ''', (year_start, year_end))
    revenue_activity_totals = cursor.fetchone()

    conn.close()

    days_ytd = today.timetuple().tm_yday
    total_revenue = revenue_stats[0] if revenue_stats[0] else 0.0

    report = f"""
# 📈 Year-to-Date Report - {today.strftime('%Y')}

## 🎯 Habit Performance YTD ({days_ytd} days)
"""

    if habit_stats:
        for habit_name, successful_days, tracked_days, best_streak, avg_streak in habit_stats:
            success_rate = (successful_days / days_ytd * 100) if days_ytd > 0 else 0
            report += f"- **{habit_name.replace('_', ' ').title()}**: {successful_days}/{days_ytd} days ({success_rate:.1f}%)\n"
            report += f"  - Best streak: {best_streak} days | Avg streak: {avg_streak:.1f}\n"

    report += f"""
## 💰 Revenue Performance YTD
- **Total Revenue**: ${total_revenue:.2f}
- **Average per Day**: ${total_revenue / days_ytd:.2f}
- **Best Single Day**: ${revenue_stats[2] if revenue_stats[2] else 0:.2f}
- **Revenue-Generating Days**: {revenue_stats[3] if revenue_stats[3] else 0}/{days_ytd}
"""

    # Initialize variables for revenue activities analysis
    completion_rate = 0
    total_planned_value = 0
    completed_value = 0
    days_with_activities = 0
    
    # Add comprehensive revenue activities analysis
    if revenue_activity_totals and revenue_activity_totals[0] > 0:
        total_activities, completed_activities, total_planned_value, completed_value, days_with_activities = revenue_activity_totals
        completion_rate = (completed_activities / total_activities * 100) if total_activities > 0 else 0

        report += f"""
## 📋 Revenue Activities Analysis YTD
- **Total Activities Planned**: {total_activities}
- **Activities Completed**: {completed_activities} ({completion_rate:.1f}%)
- **Total Planned Value**: ${total_planned_value:.2f}
- **Completed Activity Value**: ${completed_value:.2f}
- **Days with Revenue Planning**: {days_with_activities}/{days_ytd} ({days_with_activities/days_ytd*100:.1f}%)
- **Average Activity Value**: ${total_planned_value/total_activities:.2f}
- **Value Completion Rate**: {completed_value/total_planned_value*100 if total_planned_value > 0 else 0:.1f}%
- **Total Missed Opportunity**: ${total_planned_value - completed_value:.2f}
"""

        if revenue_activity_detailed:
            report += f"\n**Activity Breakdown by Priority:**\n"
            for priority, count, _, _, _, _, _, priority_count in revenue_activity_detailed:
                if priority:  # Skip None priorities
                    report += f"- **{priority.title()} Priority**: {priority_count} activities\n"

    report += f"""
## 🎨 Creative Productivity YTD
"""

    if creative_stats:
        total_creative_days = len(set([stat[0] for stat in creative_stats]))
        total_accomplishments = sum([stat[1] for stat in creative_stats])
        report += f"- **Days with creative work**: {total_creative_days}/{days_ytd}\n"
        report += f"- **Total accomplishments**: {total_accomplishments}\n"
        report += f"- **Most active areas**:\n"
        for area, area_count in creative_stats[:3]:  # Top 3 areas
            report += f"  - {area}: {area_count} accomplishments\n"

    report += f"""
## 📊 Key Insights YTD
"""

    # Generate insights based on data
    if habit_stats:
        best_habit = max(habit_stats, key=lambda x: x[1]/days_ytd if days_ytd > 0 else 0)
        report += f"- **Most consistent habit**: {best_habit[0].replace('_', ' ').title()} ({best_habit[1]/days_ytd*100:.1f}%)\n"

    if total_revenue > 0:
        monthly_avg = total_revenue / (today.month)
        report += f"- **Monthly revenue average**: ${monthly_avg:.2f}\n"
        report += f"- **Projected annual revenue**: ${monthly_avg * 12:.2f}\n"

        if revenue_activity_totals and completed_value > 0:
            conversion_rate = total_revenue / completed_value * 100 if completed_value > 0 else 0
            report += f"- **Revenue Activity ROI**: {conversion_rate:.1f}% conversion from planned to actual revenue\n"

    if revenue_activity_totals:
        planning_consistency = days_with_activities / days_ytd * 100
        if planning_consistency > 70:
            report += f"- **Excellent Planning**: Revenue activities planned {planning_consistency:.1f}% of days\n"
        elif planning_consistency > 40:
            report += f"- **Good Planning**: Revenue activities planned {planning_consistency:.1f}% of days\n"
        else:
            report += f"- **Opportunity**: Only {planning_consistency:.1f}% of days had revenue activities planned\n"

    report += f"""
## 🎯 Strategic Recommendations
"""

    if revenue_activity_totals and completion_rate < 60:
        report += f"- **Focus on Execution**: {100-completion_rate:.1f}% of planned revenue activities remain incomplete\n"
        report += f"- **Process Improvement**: Analyze barriers to completing revenue activities\n"

    if revenue_activity_totals and days_with_activities < days_ytd * 0.5:
        report += f"- **Increase Planning**: Revenue activities planned on only {days_with_activities} of {days_ytd} days\n"

    if total_revenue > 0 and revenue_activity_totals and completed_value > 0:
        roi_ratio = total_revenue / completed_value
        if roi_ratio < 0.5:
            report += f"- **Value Calibration**: Estimated activity values may be too high (ROI: {roi_ratio:.1%})\n"
        elif roi_ratio > 2.0:
            report += f"- **Conservative Estimates**: Activity values may be too low (ROI: {roi_ratio:.1%})\n"

    report += f"""
*Generated at {datetime.now().strftime('%H:%M')} on {today.strftime('%Y-%m-%d')}*
"""

    return report