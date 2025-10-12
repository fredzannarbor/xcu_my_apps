#!/usr/bin/env python3
"""
Daily Engine - Life Automation System
A Streamlit dashboard that automates SaaS project advancement and habit tracking
"""

import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd
import json

# Add modules to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import config
from integrations.stripe_integration import stripe_integration
from ui.management_ui import render_management_ui, render_daily_management_only, render_reports_only
from ui.persistent_agents_ui import render_persistent_agents_panel
from ui.revenue_ui import render_revenue_ui, render_revenue_activities_only
from ui.creative_ui import render_creative_ui
from ui.habit_ui_redesigned import render_habit_system_redesigned
from ui.project_ui import render_projects_ui
from ui.settings_ui import render_settings_page
from utilities_daily_engine import (init_database, get_today_session, update_energy_level, save_energy_comment,
    get_energy_comment
)
from database_extensions import db_extensions
from habit_system.habit_tracker import log_habit_completion
from shared.ui import render_unified_sidebar


def load_weight_data():
    """Load weight data from JSON file."""
    weight_file = os.path.join(os.path.dirname(__file__), 'data', 'weight_history.json')
    if os.path.exists(weight_file):
        try:
            with open(weight_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading weight data: {e}")
            return []
    return []


def save_weight_data(weight_data):
    """Save weight data to JSON file."""
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    weight_file = os.path.join(data_dir, 'weight_history.json')
    try:
        with open(weight_file, 'w') as f:
            json.dump(weight_data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving weight data: {e}")
        return False


def import_weight_history(uploaded_file):
    """Import weight history from uploaded CSV or XLSX file."""
    try:
        # Read file based on extension
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format. Please upload CSV or XLSX.")
            return None

        # Normalize column names to lowercase for case-insensitive matching
        df.columns = df.columns.str.lower().str.strip()

        # Validate columns (expect 'date' and 'weight')
        if 'date' not in df.columns or 'weight' not in df.columns:
            st.error(f"File must contain 'date' and 'weight' columns. Found: {list(df.columns)}")
            return None

        # Debug: Show raw data
        st.write(f"DEBUG - Raw date values (first 3): {df['date'].head(3).tolist()}")
        st.write(f"DEBUG - Date column dtype: {df['date'].dtype}")

        # Convert dates - handle both year-only strings and full dates
        def parse_date(date_val):
            # Convert to string first to handle numeric types
            date_str = str(date_val).strip()

            # If it's just a 4-digit year
            if len(date_str) == 4 and date_str.isdigit():
                return f"{date_str}-01-01"

            # Otherwise try to parse as full date
            try:
                parsed = pd.to_datetime(date_val)
                return parsed.strftime('%Y-%m-%d')
            except:
                # Last resort - return as-is
                return date_str

        df['date'] = df['date'].apply(parse_date)
        weight_data = df[['date', 'weight']].to_dict('records')

        # Sort by date
        weight_data.sort(key=lambda x: x['date'])

        return weight_data
    except Exception as e:
        st.error(f"Error importing file: {e}")
        return None


def render_weight_metrics():
    """Render weight tracking metrics and chart."""
    with st.expander("⚖️ Weight Metrics", expanded=True):
        # Load existing weight data
        weight_data = load_weight_data()

        # Weight entry and file upload in same row
        col_weight, col_upload = st.columns(2)

        with col_weight:
            new_weight = st.number_input("Enter Weight (lbs)", min_value=50.0, max_value=500.0, value=185.0, step=0.1, key="weight_input")
            if st.button("📝 Log Weight", key="log_weight_btn", use_container_width=True):
                today = datetime.now().strftime('%Y-%m-%d')
                # Update or add today's weight
                existing_entry = next((item for item in weight_data if item['date'] == today), None)
                if existing_entry:
                    existing_entry['weight'] = new_weight
                else:
                    weight_data.append({'date': today, 'weight': new_weight})
                    weight_data.sort(key=lambda x: x['date'])

                if save_weight_data(weight_data):
                    st.success(f"Weight logged: {new_weight} lbs")
                    st.rerun()

        with col_upload:
            uploaded_file = st.file_uploader(
                "📁 Import Historic Weight Data",
                type=['csv', 'xlsx'],
                help="Upload CSV/XLSX with 'date' and 'weight' columns",
                key="weight_file_uploader"
            )

            # Process upload only when explicitly triggered
            if uploaded_file is not None:
                if st.button("Import Data (Replace All)", key="import_weight_data_btn", use_container_width=True):
                    imported_data = import_weight_history(uploaded_file)
                    if imported_data:
                        # Replace all existing weight data with imported data
                        save_weight_data(imported_data)
                        st.success(f"✅ Replaced weight history with {len(imported_data)} records!")
                        st.rerun()

        st.divider()

        # Calculate metrics from weight data
        if weight_data:
            current_weight = weight_data[-1]['weight']
            if len(weight_data) > 1:
                prev_weight = weight_data[-2]['weight']
                weight_change = current_weight - prev_weight
            else:
                weight_change = 0

            # Calculate weekly average (last 7 days)
            from datetime import timedelta
            today_date = datetime.now()
            week_ago = (today_date - timedelta(days=7)).strftime('%Y-%m-%d')
            recent_weights = [item['weight'] for item in weight_data if item['date'] >= week_ago]
            weekly_avg = sum(recent_weights) / len(recent_weights) if recent_weights else current_weight

            # Simple BMI calculation (assuming 5'10" height as default - 70 inches)
            height_inches = 70
            bmi = (current_weight / (height_inches ** 2)) * 703
            target_weight = 175
        else:
            current_weight = 185
            weight_change = 0
            weekly_avg = 185
            bmi = 24.5
            target_weight = 175

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Current Weight", f"{current_weight:.1f} lbs", f"{weight_change:+.1f} lbs")

        with col2:
            st.metric("Target Weight", f"{target_weight} lbs", f"{target_weight - current_weight:.0f} lbs to go")

        with col3:
            st.metric("BMI", f"{bmi:.1f}", f"{bmi - 24.5:+.1f}")

        with col4:
            st.metric("Weekly Avg", f"{weekly_avg:.1f} lbs", f"{weekly_avg - current_weight:+.1f} lbs")

        # Weight tracking chart
        try:
            import plotly.graph_objects as go
            from datetime import timedelta

            if weight_data:
                # Debug: Show first few records
                st.caption(f"Debug - First 3 records: {weight_data[:3]}")

                # Use real data
                dates = [item['date'] for item in weight_data]
                weights = [item['weight'] for item in weight_data]

                # Ensure today's weight is included if it exists
                today = datetime.now().strftime('%Y-%m-%d')
                if today not in dates and len(weight_data) > 0:
                    # If today's weight hasn't been logged, show up to today
                    dates.append(today)
                    weights.append(current_weight)
            else:
                # Sample data for demonstration if no data exists
                dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)]
                weights = [187 - (i * 0.07) for i in range(30)]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=weights,
                mode='lines+markers',
                name='Weight',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=4)
            ))

            # Add target line
            fig.add_hline(y=target_weight, line_dash="dash", line_color="green",
                          annotation_text=f"Target: {target_weight} lbs")

            fig.update_layout(
                title=f"Weight Progress ({len(dates)} records)",
                xaxis_title="Date",
                yaxis_title="Weight (lbs)",
                height=300,
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.info("Install plotly for weight tracking charts: `pip install plotly`")


def render_habit_optimization_enhanced(habits, micro_tasks):
    """Enhanced habit tracking UI with intermittent and occasional behaviors."""
    st.header("🎯 Habit Optimization")

    # Consistent habits
    with st.expander("🔄 Consistent Behaviors (Daily)", expanded=True):
        if habits['consistent']:
            consistent_completed = 0
            for habit in habits['consistent']:
                col_habit, col_streak = st.columns([4, 1])
                with col_habit:
                    completed = st.checkbox(
                        f"{habit.replace('_', ' ').title()}",
                        key=f"consistent_{habit}"
                    )
                    if completed:
                        log_habit_completion(habit, True)
                        consistent_completed += 1
                with col_streak:
                    if config.get('ui_preferences.show_streaks', True):
                        st.write("🔥7")

            # Progress bar for consistent habits
            consistent_rate = consistent_completed / len(habits['consistent']) * 100
            st.progress(consistent_rate / 100)
            st.write(f"Progress: {consistent_completed}/{len(habits['consistent'])} ({consistent_rate:.0f}%)")
        else:
            st.info("No consistent habits configured")

    # Intermittent habits with merged micro-tasks
    with st.expander("📅 Intermittent Behaviors (Scheduled)", expanded=True):
        if habits['intermittent']:
            intermittent_completed = 0
            for habit in habits['intermittent']:
                col_habit, col_schedule = st.columns([4, 1])
                with col_habit:
                    completed = st.checkbox(
                        f"{habit.replace('_', ' ').title()}",
                        key=f"intermittent_{habit}"
                    )
                    if completed:
                        log_habit_completion(habit, True)
                        intermittent_completed += 1
                with col_schedule:
                    if 'exercise' in habit.lower():
                        st.write("3x")
                    elif 'connection' in habit.lower():
                        st.write("2x")
                    else:
                        st.write("📅")

            # Progress bar for intermittent habits
            intermittent_rate = intermittent_completed / len(habits['intermittent']) * 100
            st.progress(intermittent_rate / 100)
            st.write(
                f"Progress: {intermittent_completed}/{len(habits['intermittent'])} ({intermittent_rate:.0f}%)")
        else:
            st.info("No intermittent habits configured")

        # Micro-tasks subsection within Intermittent Behaviors
        st.markdown("---")
        st.markdown("### ⚡ Quick Tasks")

        from database_extensions import get_micro_tasks, complete_micro_task
        pending_micro_tasks = get_micro_tasks(completed=False)

        if pending_micro_tasks:
            for task in pending_micro_tasks:
                col_task, col_btn = st.columns([5, 1])

                with col_task:
                    priority_emoji = {"high": "🔥", "medium": "📋", "low": "📝"}
                    st.write(f"**{priority_emoji[task['priority']]} {task['task_name']}** ({task['estimated_minutes']} min)")

                with col_btn:
                    if st.button("✅", key=f"complete_micro_{task['id']}", help=f"Complete: {task['task_name']}"):
                        if complete_micro_task(task['id']):
                            st.success("✓ Completed!")
                            st.rerun()
        else:
            st.write("*No pending micro-tasks*")

    # Occasional behaviors
    with st.expander("🌟 Occasional Behaviors (As-Needed)", expanded=True):
        st.markdown("Track behaviors that occur occasionally or as-needed:")

        # Get countable task definitions
        countable_definitions = db_extensions.get_behavior_counter_definitions()
        occasional_tasks = [d for d in countable_definitions if d['counter_type'] == 'positive']

        if occasional_tasks:
            for task in occasional_tasks:
                col_name, col_count, col_btn = st.columns([3, 1, 1])

                with col_name:
                    st.write(f"**{task['counter_name'].replace('_', ' ').title()}**")

                with col_count:
                    # Get today's count
                    today = datetime.now().strftime('%Y-%m-%d')
                    today_data = db_extensions.get_behavior_counter_data(task['counter_name'], days=1)
                    today_count = today_data[0]['count'] if today_data and today_data[0]['date'] == today else 0
                    st.write(f"Today: {today_count}")

                with col_btn:
                    if st.button("➕", key=f"count_{task['counter_name']}", help=f"Add 1 to {task['counter_name']}"):
                        if db_extensions.increment_behavior_counter(task['counter_name'], 1):
                            st.success("✓")
                            st.rerun()
        else:
            st.info("No occasional behaviors configured. Add them in Settings → Habits & Tasks")


def main():
    st.set_page_config(
        page_title="Daily Engine",
        page_icon="⚡",
        layout="wide"
    )

    # Render unified sidebar
    render_unified_sidebar(
        app_name="Daily Engine",
        nav_items=[]
    )

    # Initialize database
    init_database()

    # Get configuration
    habits = config.get_habits()
    projects = config.get_projects()
    micro_tasks = config.get_micro_tasks()
    creative_areas = config.get_creative_areas()
    sidebar_checkins = config.get_sidebar_checkins()

    # Header
    st.title("⚡ Daily Engine")
    st.markdown("*Automated project advancement & habit optimization*")

    # Check subscription status for premium features
    is_premium = stripe_integration.check_feature_access('premium')

    # Get today's session
    session = get_today_session()
    today = datetime.now().strftime('%Y-%m-%d')

    # Sidebar - Daily Overview
    with st.sidebar:
        st.header("Today's Overview")
        st.write(f"📅 {today}")
        st.write(f"⏰ Available: {session[3]} hours")

        # Interactive Energy Level Update
        st.subheader("⚡ Energy Level")
        energy_options = ['low', 'medium', 'high', 'peak']
        current_energy = session[4] if session[4] in energy_options else 'medium'

        energy_index = energy_options.index(current_energy) if current_energy in energy_options else 1

        new_energy = st.selectbox(
            "Current energy:",
            energy_options,
            index=energy_index,
            key="energy_level_select"
        )

        # Update energy level if changed
        if new_energy != current_energy:
            update_energy_level(new_energy)
            st.success(f"Energy updated to: {new_energy}")
            st.rerun()

        # Energy comment
        existing_comment = get_energy_comment()
        energy_comment = st.text_input(
            "Energy notes:",
            value=existing_comment,
            placeholder="How are you feeling? What's affecting your energy?",
            key="energy_comment_input"
        )

        if st.button("💾 Save Energy Notes", key="save_energy_notes"):
            save_energy_comment(energy_comment)
            st.success("Energy notes saved!")

        # Layout toggle removed - single column only

        # Subscription status
        if config.is_feature_enabled('stripe_subscription'):
            subscription_status = st.session_state.get('subscription_status', 'inactive')
            if subscription_status == 'active':
                st.success("✨ Premium Active")
            else:
                st.warning("🆓 Free Tier")

        # Quick Check-ins removed per user request

        # Micro-Tasks Quick Access
        st.subheader("⚡ Quick Tasks")

        # Get today's pending micro-tasks (up to 3)
        from database_extensions import get_micro_tasks, complete_micro_task
        pending_micro_tasks = get_micro_tasks(completed=False)[:3]

        if pending_micro_tasks:
            for task in pending_micro_tasks:
                col_task, col_btn = st.columns([3, 1])

                with col_task:
                    priority_emoji = {"high": "🔥", "medium": "📋", "low": "📝"}
                    st.write(f"**{priority_emoji[task['priority']]} {task['task_name']}**")
                    st.caption(f"{task['estimated_minutes']} min")

                with col_btn:
                    if st.button("✅", key=f"sidebar_complete_{task['id']}", help=f"Complete: {task['task_name']}"):
                        if complete_micro_task(task['id']):
                            st.success("✓")
                            st.rerun()
        else:
            st.write("*No pending micro-tasks*")
            st.write("Add them in Daily Management")

        st.divider()

        # Countable Tasks Quick Access
        st.subheader("📊 Quick Count")

        # Get countable task definitions
        countable_definitions = db_extensions.get_behavior_counter_definitions()
        countable_tasks = [d for d in countable_definitions if d['counter_type'] == 'positive']

        if countable_tasks:
            # Show up to 3 most recent countable tasks in sidebar
            for task in countable_tasks[:3]:
                col_name, col_count, col_btn = st.columns([2, 1, 1])

                with col_name:
                    st.write(f"**{task['counter_name'].replace('_', ' ').title()}**")

                with col_count:
                    # Get today's count
                    today_data = db_extensions.get_behavior_counter_data(task['counter_name'], days=1)
                    today_count = today_data[0]['count'] if today_data and today_data[0]['date'] == today else 0
                    st.write(f"{today_count}")

                with col_btn:
                    if st.button("➕", key=f"sidebar_count_{task['counter_name']}", help=f"Add 1 to {task['counter_name']}"):
                        if db_extensions.increment_behavior_counter(task['counter_name'], 1):
                            st.success("✓")
                            st.rerun()
        else:
            st.write("*No countable tasks configured*")
            st.write("Add them in Settings → Habits & Tasks")

    # Create tabs for main content
    tabs = st.tabs([
        "🏠 Dashboard",
        "📝 Daily Management",
        "📊 Reports",
        "🚀 Projects",
        "💰 Revenue",
        "🎨 Creative",
        "🤖 Life Guardrails",
        "⚙️ Settings"
    ])

    with tabs[0]:
        # Dashboard - Just the habit system
        render_habit_system_redesigned()

    with tabs[1]:
        # Daily Management
        render_daily_management_only()

    with tabs[2]:
        # Reports
        render_weight_metrics()
        render_reports_only()

    with tabs[3]:
        # Projects Status
        render_projects_ui(projects)

    with tabs[4]:
        # Revenue - Both Action Focus and Revenue Activities
        st.header("💰 Revenue Focus")

        with st.expander("💰 Action Focus", expanded=True):
            render_revenue_ui(micro_tasks)

        with st.expander("💵 Revenue Activities", expanded=False):
            render_revenue_activities_only()

    with tabs[5]:
        # Creative Pipeline
        render_creative_ui(creative_areas)

    with tabs[6]:
        # Life Guardrails
        render_persistent_agents_panel()

    with tabs[7]:
        # Settings
        render_settings_page()


if __name__ == "__main__":
    main()
