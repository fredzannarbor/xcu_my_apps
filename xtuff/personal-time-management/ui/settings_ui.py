#!/usr/bin/env python3
"""
Settings UI for Daily Engine
Provides interface for configuring all system settings
"""

import streamlit as st
from config.settings import config
from integrations.stripe_integration import stripe_integration
from streamlit_app_manager import StreamlitAppManager
from launchctl_manager import LaunchCtlManager
from multi_app_support import AppTypeManager
from daily_engine_integration import DailyEngineIntegration
from logging_monitoring_system import get_recent_logs, get_performance_summary
from database_extensions import db_extensions
from datetime import datetime
from ui.persistent_agents_ui import render_family_member_management, render_correspondence_upload
from ui.real_property_ui import render_real_property_management

def render_settings_page():
    """Render the main settings page"""
    st.title("⚙️ Daily Engine Settings")
    
    # Settings tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🎯 Habits & Tasks", 
        "🚀 Projects", 
        "📱 App Management",
        "🤖 Life Agents",
        "🔧 Features", 
        "💳 Subscription",
        "🎨 UI Preferences"
    ])
    
    with tab1:
        render_habits_settings()
    
    with tab2:
        render_projects_settings()
    
    with tab3:
        render_app_management_settings()
    
    with tab4:
        render_persistent_agents_settings()
    
    with tab5:
        render_features_settings()
    
    with tab6:
        stripe_integration.render_subscription_ui()
    
    with tab7:
        render_ui_preferences()

def render_habits_settings():
    """Render habits and tasks configuration"""
    st.header("🎯 Habits & Tasks Configuration")
    
    # Consistent Habits
    st.subheader("Daily Consistent Habits")
    consistent_habits = config.get('habits.consistent', [])
    
    # Display current habits with delete option
    for i, habit in enumerate(consistent_habits):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"• {habit.replace('_', ' ').title()}")
        with col2:
            if st.button("🗑️", key=f"del_consistent_{i}"):
                consistent_habits.remove(habit)
                config.set('habits.consistent', consistent_habits)
                st.rerun()
    
    # Add new consistent habit
    new_consistent = st.text_input("Add new daily habit:", key="new_consistent")
    if st.button("➕ Add Daily Habit") and new_consistent:
        consistent_habits.append(new_consistent.lower().replace(' ', '_'))
        config.set('habits.consistent', consistent_habits)
        st.success(f"Added '{new_consistent}' to daily habits!")
        st.rerun()
    
    st.divider()
    
    # Intermittent Habits
    st.subheader("Intermittent Habits (Smart Scheduled)")
    intermittent_habits = config.get('habits.intermittent', [])
    
    for i, habit in enumerate(intermittent_habits):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"• {habit.replace('_', ' ').title()}")
        with col2:
            if st.button("🗑️", key=f"del_intermittent_{i}"):
                intermittent_habits.remove(habit)
                config.set('habits.intermittent', intermittent_habits)
                st.rerun()
    
    new_intermittent = st.text_input("Add new intermittent habit:", key="new_intermittent")
    if st.button("➕ Add Intermittent Habit") and new_intermittent:
        intermittent_habits.append(new_intermittent.lower().replace(' ', '_'))
        config.set('habits.intermittent', intermittent_habits)
        st.success(f"Added '{new_intermittent}' to intermittent habits!")
        st.rerun()
    
    st.divider()
    
    # Micro Tasks
    st.subheader("Revenue Micro-Tasks")
    micro_tasks = config.get('micro_tasks', [])
    
    for i, task in enumerate(micro_tasks):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"• {task}")
        with col2:
            if st.button("🗑️", key=f"del_task_{i}"):
                micro_tasks.remove(task)
                config.set('micro_tasks', micro_tasks)
                st.rerun()
    
    new_task = st.text_input("Add new micro-task:", key="new_task")
    if st.button("➕ Add Micro-Task") and new_task:
        micro_tasks.append(new_task)
        config.set('micro_tasks', micro_tasks)
        st.success(f"Added '{new_task}' to micro-tasks!")
        st.rerun()
    
    st.divider()
    
    # Countable Tasks
    st.subheader("📊 Countable Tasks")
    st.write("Tasks that can be performed multiple times per day and tracked with counts.")
    
    # Get existing countable task definitions
    countable_definitions = db_extensions.get_behavior_counter_definitions()
    countable_tasks = [d for d in countable_definitions if d['counter_type'] == 'positive']
    
    # Display existing countable tasks
    for task in countable_tasks:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"• **{task['counter_name'].replace('_', ' ').title()}**")
            if task['description']:
                st.write(f"  _{task['description']}_")
        
        with col2:
            # Get today's count
            today = datetime.now().strftime('%Y-%m-%d')
            today_data = db_extensions.get_behavior_counter_data(task['counter_name'], days=1)
            today_count = today_data[0]['count'] if today_data and today_data[0]['date'] == today else 0
            st.write(f"Today: **{today_count}**")
        
        with col3:
            if st.button("➕", key=f"settings_increment_{task['counter_name']}", help="Add one count"):
                if db_extensions.increment_behavior_counter(task['counter_name'], 1):
                    st.success(f"Added 1 to {task['counter_name']}")
                    st.rerun()
                else:
                    st.error("Failed to increment counter")
    
    # Add new countable task
    st.write("**Add New Countable Task:**")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        new_countable_name = st.text_input("Task name:", key="new_countable_name")
        new_countable_desc = st.text_input("Description (optional):", key="new_countable_desc")

    with col2:
        st.write("")  # Spacing
        counter_type = st.selectbox(
            "Type:",
            options=['positive', 'negative'],
            format_func=lambda x: "✅ Positive (goal to increase)" if x == 'positive' else "🚫 Negative (bad habit to reduce)",
            key="new_countable_type"
        )

    with col3:
        st.write("")  # Spacing
        st.write("")  # More spacing
        if st.button("➕ Add Countable Task") and new_countable_name:
            # Convert to snake_case for database
            counter_name = new_countable_name.lower().replace(' ', '_')
            if db_extensions.add_behavior_counter_definition(
                counter_name,
                counter_type,
                new_countable_desc or f"Countable task: {new_countable_name}"
            ):
                st.success(f"Added {'positive' if counter_type == 'positive' else 'negative'} countable task '{new_countable_name}'!")
                st.rerun()
            else:
                st.error("Failed to add countable task")
    
    st.divider()
    
    # Sidebar Quick Check-ins
    st.subheader("Sidebar Quick Check-ins")
    all_habits = consistent_habits + intermittent_habits
    current_checkins = config.get('sidebar_checkins', [])
    
    # Filter current checkins to only include habits that still exist
    valid_current_checkins = [habit for habit in current_checkins if habit in all_habits]
    
    selected_checkins = st.multiselect(
        "Select habits to show in sidebar:",
        options=all_habits,
        default=valid_current_checkins,
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    if st.button("💾 Save Sidebar Settings"):
        config.set('sidebar_checkins', selected_checkins)
        st.success("Sidebar check-ins updated!")

def render_projects_settings():
    """Render projects configuration"""
    st.header("🚀 Projects Configuration")
    
    projects = config.get('projects', {})
    
    for project_id, project_config in projects.items():
        with st.expander(f"📁 {project_config.get('name', project_id)}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                new_name = st.text_input(
                    "Project Name:", 
                    value=project_config.get('name', ''),
                    key=f"name_{project_id}"
                )
                new_path = st.text_input(
                    "Project Path:", 
                    value=project_config.get('path', ''),
                    key=f"path_{project_id}"
                )
            
            with col2:
                enabled = st.checkbox(
                    "Enabled", 
                    value=project_config.get('enabled', True),
                    key=f"enabled_{project_id}"
                )
                
                if st.button("🗑️ Delete", key=f"del_project_{project_id}"):
                    del projects[project_id]
                    config.set('projects', projects)
                    st.rerun()
            
            if st.button("💾 Save Changes", key=f"save_{project_id}"):
                projects[project_id] = {
                    'name': new_name,
                    'path': new_path,
                    'enabled': enabled
                }
                config.set('projects', projects)
                st.success(f"Updated {new_name}!")
    
    st.divider()
    
    # Add new project
    st.subheader("➕ Add New Project")
    col1, col2 = st.columns(2)
    with col1:
        new_project_name = st.text_input("Project Name:", key="new_project_name")
        new_project_path = st.text_input("Project Path:", key="new_project_path")
    with col2:
        new_project_id = st.text_input("Project ID (lowercase, no spaces):", key="new_project_id")
    
    if st.button("➕ Add Project") and all([new_project_name, new_project_path, new_project_id]):
        projects[new_project_id] = {
            'name': new_project_name,
            'path': new_project_path,
            'enabled': True
        }
        config.set('projects', projects)
        st.success(f"Added project '{new_project_name}'!")
        st.rerun()

def render_features_settings():
    """Render features configuration"""
    st.header("🔧 Features Configuration")
    
    # iOS Notifications
    st.subheader("📱 iOS Notifications")
    ios_enabled = st.checkbox(
        "Enable iOS Notifications",
        value=config.get('features.ios_notifications.enabled', False)
    )
    
    if ios_enabled:
        if not stripe_integration.check_feature_access('ios_notifications'):
            stripe_integration.render_paywall("iOS Notifications")
        else:
            device_token = st.text_input(
                "Device Token:",
                value=config.get('features.ios_notifications.device_token', ''),
                type="password"
            )
            
            # Available time options
            time_options = ['06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', 
                           '13:00', '14:00', '15:00', '16:00', '16:30', '17:00', '18:00', 
                           '19:00', '20:00', '21:00', '21:30', '22:00', '23:00']
            
            # Get current reminder times and filter to only include valid options
            current_times = config.get('features.ios_notifications.reminder_times', ['09:00', '15:00', '20:00'])
            valid_current_times = [time for time in current_times if time in time_options]
            
            reminder_times = st.multiselect(
                "Reminder Times:",
                options=time_options,
                default=valid_current_times
            )
            
            if st.button("💾 Save iOS Settings"):
                config.set('features.ios_notifications.enabled', ios_enabled)
                config.set('features.ios_notifications.device_token', device_token)
                config.set('features.ios_notifications.reminder_times', reminder_times)
                st.success("iOS notification settings saved!")
    else:
        config.set('features.ios_notifications.enabled', False)
    
    st.divider()
    
    # Automation
    st.subheader("🤖 Automation")
    automation_enabled = st.checkbox(
        "Enable Automation",
        value=config.get('features.automation.enabled', False)
    )
    
    if automation_enabled:
        if not stripe_integration.check_feature_access('automation'):
            stripe_integration.render_paywall("Automation")
        else:
            overnight_runs = st.checkbox(
                "Overnight automation runs",
                value=config.get('features.automation.overnight_runs', True)
            )
            
            email_reports = st.checkbox(
                "Email daily reports",
                value=config.get('features.automation.email_reports', False)
            )
            
            slack_integration = st.checkbox(
                "Slack integration",
                value=config.get('features.automation.slack_integration', False)
            )
            
            if st.button("💾 Save Automation Settings"):
                config.set('features.automation.enabled', automation_enabled)
                config.set('features.automation.overnight_runs', overnight_runs)
                config.set('features.automation.email_reports', email_reports)
                config.set('features.automation.slack_integration', slack_integration)
                st.success("Automation settings saved!")
    else:
        config.set('features.automation.enabled', False)
    
    st.divider()
    
    # AI Insights
    st.subheader("🧠 AI Insights")
    ai_enabled = st.checkbox(
        "Enable AI Insights",
        value=config.get('features.ai_insights.enabled', False)
    )
    
    if ai_enabled:
        if not stripe_integration.check_feature_access('ai_insights'):
            stripe_integration.render_paywall("AI Insights")
        else:
            openai_key = st.text_input(
                "OpenAI API Key:",
                value=config.get('features.ai_insights.openai_key', ''),
                type="password"
            )
            
            model_options = ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo']
            current_model = config.get('features.ai_insights.model', 'gpt-4')
            model_index = model_options.index(current_model) if current_model in model_options else 0
            
            model = st.selectbox(
                "AI Model:",
                options=model_options,
                index=model_index
            )
            
            if st.button("💾 Save AI Settings"):
                config.set('features.ai_insights.enabled', ai_enabled)
                config.set('features.ai_insights.openai_key', openai_key)
                config.set('features.ai_insights.model', model)
                st.success("AI insights settings saved!")
    else:
        config.set('features.ai_insights.enabled', False)

def render_app_management_settings():
    """Render app management settings"""
    st.header("📱 App Management")
    
    # Initialize app manager
    app_manager = StreamlitAppManager()
    
    # Get current status of all apps
    all_status = app_manager.get_app_status()
    
    st.subheader("🚀 Managed Applications")
    
    # Display each configured app
    for app_name, app_config in app_manager.config['apps'].items():
        with st.expander(f"📱 {app_config.get('name', app_name)}", expanded=True):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            # App info
            with col1:
                st.write(f"**Path:** `{app_config['path']}`")
                
                # Get current status
                current_status = all_status.get(app_name, {})
                status = current_status.get('status', 'unknown')
                port = current_status.get('port', app_config.get('port', 'N/A'))
                
                if status == 'running':
                    st.success(f"🟢 Running on port {port}")
                    if port != 'N/A':
                        st.write(f"**URL:** http://localhost:{port}")
                elif status == 'stopped':
                    st.error("🔴 Stopped")
                else:
                    st.warning("🟡 Unknown status")
                
                # Show additional info if available
                if current_status.get('restart_count', 0) > 0:
                    st.write(f"**Restarts:** {current_status['restart_count']}")
                
                if current_status.get('start_time'):
                    st.write(f"**Started:** {current_status['start_time'][:19]}")
            
            # Control buttons
            with col2:
                if st.button("▶️ Start", key=f"start_{app_name}"):
                    result = app_manager.start_app(app_name)
                    if result['success']:
                        st.success(f"Started {app_name}")
                        st.rerun()
                    else:
                        st.error(f"Failed to start: {result.get('error', 'Unknown error')}")
            
            with col3:
                if st.button("⏹️ Stop", key=f"stop_{app_name}"):
                    result = app_manager.stop_app(app_name)
                    if result['success']:
                        st.success(f"Stopped {app_name}")
                        st.rerun()
                    else:
                        st.error(f"Failed to stop: {result.get('error', 'Unknown error')}")
            
            with col4:
                if st.button("🔄 Restart", key=f"restart_{app_name}"):
                    result = app_manager.restart_app(app_name)
                    if result['success']:
                        st.success(f"Restarted {app_name}")
                        st.rerun()
                    else:
                        st.error(f"Failed to restart: {result.get('error', 'Unknown error')}")
            
            # App configuration
            st.write("**Configuration:**")
            col_config1, col_config2 = st.columns(2)
            
            with col_config1:
                enabled = st.checkbox(
                    "Enabled", 
                    value=app_config.get('enabled', True),
                    key=f"enabled_{app_name}"
                )
                auto_start = st.checkbox(
                    "Auto-start", 
                    value=app_config.get('auto_start', False),
                    key=f"auto_start_{app_name}"
                )
            
            with col_config2:
                restart_on_failure = st.checkbox(
                    "Restart on failure", 
                    value=app_config.get('restart_on_failure', True),
                    key=f"restart_failure_{app_name}"
                )
            
            if st.button("💾 Save Config", key=f"save_config_{app_name}"):
                # Update configuration
                app_manager.config['apps'][app_name]['enabled'] = enabled
                app_manager.config['apps'][app_name]['auto_start'] = auto_start
                app_manager.config['apps'][app_name]['restart_on_failure'] = restart_on_failure
                
                # Save to file
                import json
                with open(app_manager.config_path, 'w') as f:
                    json.dump(app_manager.config, f, indent=2)
                
                st.success(f"Configuration saved for {app_name}")
    
    st.divider()
    
    # Health check section
    st.subheader("🏥 Health Check")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Check All Apps"):
            health_results = app_manager.health_check()
            
            if 'error' in health_results:
                st.error(f"Health check failed: {health_results['error']}")
            else:
                for app_name, health_info in health_results.items():
                    if health_info.get('healthy', False):
                        st.success(f"✅ {app_name}: Healthy")
                    else:
                        reason = health_info.get('reason', 'Unknown')
                        st.error(f"❌ {app_name}: {reason}")
    
    with col2:
        if st.button("📊 Port Status"):
            port_assignments = app_manager.port_manager.get_port_assignments()
            available_ports = app_manager.port_manager.get_available_ports()
            
            st.write("**Port Assignments:**")
            for app_name, port in port_assignments.items():
                st.write(f"• {app_name}: {port}")
            
            st.write(f"**Available Ports:** {', '.join(map(str, available_ports))}")
    
    st.divider()
    
    # Add new app section
    st.subheader("➕ Add New App")
    col1, col2 = st.columns(2)
    
    with col1:
        new_app_name = st.text_input("App Name:", key="new_app_name")
        new_app_path = st.text_input("App Path:", key="new_app_path")
    
    with col2:
        new_app_display_name = st.text_input("Display Name:", key="new_app_display_name")
        new_app_port = st.number_input("Port (optional):", min_value=8501, max_value=8600, value=8504, key="new_app_port")
    
    if st.button("➕ Add App") and new_app_name and new_app_path:
        # Add to configuration
        app_manager.config['apps'][new_app_name] = {
            'name': new_app_display_name or new_app_name,
            'path': new_app_path,
            'port': new_app_port,
            'enabled': True,
            'auto_start': False,
            'restart_on_failure': True,
            'health_check_url': '/health',
            'environment': {}
        }
        
        # Save configuration
        import json
        with open(app_manager.config_path, 'w') as f:
            json.dump(app_manager.config, f, indent=2)
        
        st.success(f"Added new app: {new_app_name}")
        st.rerun()

def render_persistent_agents_settings():
    """Render persistent agents configuration"""
    st.header("🤖 Life Agents Configuration")
    
    st.write("Configure AI agents that monitor your financial and life guardrails.")
    
    # Agent status
    st.subheader("Agent Status")
    
    agents_status = {
        "Social Security Agent": {
            "enabled": True,
            "description": "Monitors Social Security correspondence, deadlines, and family benefit opportunities",
            "last_run": "Recently"
        },
        "Real Property Agent": {
            "enabled": True,
            "description": "Tracks owned properties, watchlist properties, and market trends for investment decisions",
            "last_run": "Recently"
        }
    }
    
    for agent_name, status in agents_status.items():
        with st.expander(f"📋 {agent_name}", expanded=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Description:** {status['description']}")
                st.write(f"**Last Run:** {status['last_run']}")
                st.write(f"**Status:** {'🟢 Active' if status['enabled'] else '🔴 Inactive'}")
            
            with col2:
                enabled = st.checkbox("Enabled", value=status['enabled'], key=f"agent_{agent_name}")
                if st.button("🔄 Run Now", key=f"run_{agent_name}"):
                    st.info(f"Running {agent_name}...")
    
    st.divider()
    
    # Family member management
    render_family_member_management()
    
    st.divider()
    
    # Document upload
    render_correspondence_upload()
    
    st.divider()
    
    # Real property management
    render_real_property_management()

def render_ui_preferences():
    """Render UI preferences"""
    st.header("🎨 UI Preferences")
    
    theme_options = ['light', 'dark', 'auto']
    current_theme = config.get('ui_preferences.theme', 'light')
    theme_index = theme_options.index(current_theme) if current_theme in theme_options else 0
    
    theme = st.selectbox(
        "Theme:",
        options=theme_options,
        index=theme_index
    )
    
    width_options = ['narrow', 'normal', 'wide']
    current_width = config.get('ui_preferences.sidebar_width', 'normal')
    width_index = width_options.index(current_width) if current_width in width_options else 1
    
    sidebar_width = st.selectbox(
        "Sidebar Width:",
        options=width_options,
        index=width_index
    )
    
    show_streaks = st.checkbox(
        "Show habit streaks",
        value=config.get('ui_preferences.show_streaks', True)
    )
    
    show_percentages = st.checkbox(
        "Show completion percentages",
        value=config.get('ui_preferences.show_percentages', True)
    )
    
    compact_mode = st.checkbox(
        "Compact mode",
        value=config.get('ui_preferences.compact_mode', False)
    )
    
    if st.button("💾 Save UI Preferences"):
        config.set('ui_preferences.theme', theme)
        config.set('ui_preferences.sidebar_width', sidebar_width)
        config.set('ui_preferences.show_streaks', show_streaks)
        config.set('ui_preferences.show_percentages', show_percentages)
        config.set('ui_preferences.compact_mode', compact_mode)
        st.success("UI preferences saved!")
        st.info("Some changes may require refreshing the page.")