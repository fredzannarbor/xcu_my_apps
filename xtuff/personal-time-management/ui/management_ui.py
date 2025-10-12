
import streamlit as st
from utilities_daily_engine import (
    get_daily_notes, save_daily_notes, get_quick_stats,
    generate_daily_report, generate_weekly_report,
    generate_monthly_report, generate_yearly_report
)
from database_extensions import (
    add_micro_task, complete_micro_task, get_micro_tasks, delete_micro_task
)
from datetime import datetime

def render_management_ui():
    """Renders the daily management, notes, and actions UI."""
    st.header("📝 Daily Management")

    col_notes, col_actions = st.columns([1, 1])

    with col_notes:
        with st.container():
            st.subheader("📝 Notes & Reflection")

            # Load existing notes
            existing_notes = get_daily_notes()
            notes = st.text_area(
                "Today's Notes",
                value=existing_notes or "",
                height=120,
                placeholder="Thoughts, insights, important events, lessons learned..."
            )
            if st.button("💾 Save Notes", type="primary"):
                save_daily_notes(notes)
                st.success("Notes saved!")

            # Quick stats
            with st.expander("📊 Today's Quick Stats", expanded=False):
                stats = get_quick_stats()
                st.write(f"• Energy level updated at: {stats['energy_updated_at']}")
                st.write(f"• Habits completed: {stats['habits_completed']}")
                st.write(f"• Micro-tasks completed: {stats['micro_tasks_completed']}")
                st.write(f"• Revenue generated: {stats['revenue_generated']}")
                st.write(f"• Creative areas active: {stats['creative_areas_active']}")

    with col_actions:
        with st.container():
            st.subheader("🚀 Quick Actions")

            # System actions
            with st.expander("⚙️ System Actions", expanded=True):
                col_refresh, col_auto = st.columns(2)
                with col_refresh:
                    if st.button("🔄 Refresh Status", help="Check all project statuses"):
                        st.info("Refreshing all projects...")

                with col_auto:
                    if st.button("⚡ Run Automation", help="Execute automation scripts"):
                        st.info("Running automation...")

            # Report generation
            with st.expander("📊 Generate Reports", expanded=True):
                report_cols = st.columns(2)

                with report_cols[0]:
                    if st.button("📊 Daily", help="Generate today's report"):
                        with st.spinner("Generating..."):
                            report = generate_daily_report()
                            st.success("Daily report generated!")
                            with st.expander("📊 Daily Report", expanded=False):
                                st.markdown(report)

                    if st.button("📆 Monthly", help="Generate monthly report"):
                        with st.spinner("Generating..."):
                            report = generate_monthly_report()
                            st.success("Monthly report generated!")
                            with st.expander("📆 Monthly Report", expanded=False):
                                st.markdown(report)

                with report_cols[1]:
                    if st.button("📅 Weekly", help="Generate weekly report"):
                        with st.spinner("Generating..."):
                            report = generate_weekly_report()
                            st.success("Weekly report generated!")
                            with st.expander("📅 Weekly Report", expanded=False):
                                st.markdown(report)

                    if st.button("📈 Yearly", help="Generate yearly report"):
                        with st.spinner("Generating..."):
                            report = generate_yearly_report()
                            st.success("Yearly report generated!")
                            with st.expander("📈 Yearly Report", expanded=False):
                                st.markdown(report)


def render_daily_management_only():
    """Renders only the daily management section (notes and quick actions, no reports)."""
    
    # Quick stats at the top (expanded by default)
    with st.expander("📊 Today's Quick Stats", expanded=True):
        stats = get_quick_stats()
        st.write(f"• Energy level updated at: {stats['energy_updated_at']}")
        st.write(f"• Habits completed: {stats['habits_completed']}")
        st.write(f"• Micro-tasks completed: {stats['micro_tasks_completed']}")
        st.write(f"• Revenue generated: {stats['revenue_generated']}")
        st.write(f"• Creative areas active: {stats['creative_areas_active']}")
    
    # Micro-tasks section (expanded by default)
    with st.expander("⚡ Micro-Tasks", expanded=True):
        render_micro_tasks_ui()
    
    col_notes, col_actions = st.columns([1, 1])

    with col_notes:
        st.subheader("📝 Notes & Reflection")

        # Load existing notes
        existing_notes = get_daily_notes()
        notes = st.text_area(
            "Today's Notes",
            value=existing_notes or "",
            height=120,
            placeholder="Thoughts, insights, important events, lessons learned...",
            key="daily_notes_main"
        )
        if st.button("💾 Save Notes", type="primary", key="save_notes_main"):
            save_daily_notes(notes)
            st.success("Notes saved!")

    with col_actions:
        st.subheader("🚀 Quick Actions")

        # System actions
        col_refresh, col_auto = st.columns(2)
        with col_refresh:
            if st.button("🔄 Refresh Status", help="Check all project statuses", key="refresh_main"):
                st.info("Refreshing all projects...")

        with col_auto:
            if st.button("⚡ Run Automation", help="Execute automation scripts", key="automation_main"):
                st.info("Running automation...")


def get_cached_daily_report():
    """Get cached daily report or generate new one if needed."""
    today = datetime.now().strftime('%Y-%m-%d')
    cache_key = f"daily_report_{today}"
    
    # Check if report is already cached for today
    if cache_key not in st.session_state:
        # Generate and cache the report
        with st.spinner("Generating today's report..."):
            st.session_state[cache_key] = generate_daily_report()
    
    return st.session_state[cache_key]


def render_reports_only():
    """Renders only the reports generation section."""
    
    # Auto-generated daily report (cached)
    st.subheader("📊 Today's Auto-Generated Report")
    cached_report = get_cached_daily_report()
    
    col_report, col_regenerate = st.columns([4, 1])
    with col_report:
        with st.expander("📊 Daily Report", expanded=True):
            st.markdown(cached_report)
    
    with col_regenerate:
        if st.button("🔄 Regenerate", help="Generate fresh daily report", key="regenerate_daily"):
            # Clear cache and regenerate
            today = datetime.now().strftime('%Y-%m-%d')
            cache_key = f"daily_report_{today}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]
            st.rerun()
    
    st.divider()
    
    # Manual report generation
    st.subheader("📈 Additional Reports")
    report_cols = st.columns(3)

    with report_cols[0]:
        if st.button("📅 Weekly", help="Generate weekly report", key="weekly_report"):
            with st.spinner("Generating..."):
                report = generate_weekly_report()
                st.success("Weekly report generated!")
                with st.expander("📅 Weekly Report", expanded=False):
                    st.markdown(report)

    with report_cols[1]:
        if st.button("📆 Monthly", help="Generate monthly report", key="monthly_report"):
            with st.spinner("Generating..."):
                report = generate_monthly_report()
                st.success("Monthly report generated!")
                with st.expander("📆 Monthly Report", expanded=False):
                    st.markdown(report)

    with report_cols[2]:
        if st.button("📈 Yearly", help="Generate yearly report", key="yearly_report"):
            with st.spinner("Generating..."):
                report = generate_yearly_report()
                st.success("Yearly report generated!")
                with st.expander("📈 Yearly Report", expanded=False):
                    st.markdown(report)


def render_micro_tasks_ui():
    """Render the micro-tasks management interface"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Add new micro-task form
    st.subheader("➕ Add Micro-Task")
    
    col_task, col_priority, col_time = st.columns([3, 1, 1])
    
    with col_task:
        new_task = st.text_input(
            "Task name",
            placeholder="Quick task to complete today...",
            key="new_micro_task"
        )
    
    with col_priority:
        priority = st.selectbox(
            "Priority",
            ["low", "medium", "high"],
            index=1,
            key="micro_task_priority"
        )
    
    with col_time:
        estimated_minutes = st.number_input(
            "Minutes",
            min_value=5,
            max_value=120,
            value=15,
            step=5,
            key="micro_task_minutes"
        )
    
    description = st.text_input(
        "Description (optional)",
        placeholder="Additional details...",
        key="micro_task_description"
    )
    
    col_add, col_clear = st.columns([1, 1])
    
    with col_add:
        if st.button("➕ Add Task", type="primary", key="add_micro_task_btn"):
            if new_task.strip():
                if add_micro_task(
                    task_name=new_task.strip(),
                    description=description.strip() if description.strip() else None,
                    priority=priority,
                    estimated_minutes=int(estimated_minutes)
                ):
                    st.success("Micro-task added!")
                    st.rerun()
                else:
                    st.error("Failed to add micro-task")
            else:
                st.warning("Please enter a task name")
    
    with col_clear:
        if st.button("🗑️ Clear Form", key="clear_micro_task_form"):
            st.rerun()
    
    st.divider()
    
    # Display existing micro-tasks
    st.subheader("📋 Today's Micro-Tasks")
    
    # Get today's micro-tasks
    pending_tasks = get_micro_tasks(date=today, completed=False)
    completed_tasks = get_micro_tasks(date=today, completed=True)
    
    # Show pending tasks
    if pending_tasks:
        st.write("**⏳ Pending Tasks:**")
        
        for task in pending_tasks:
            col_check, col_task_info, col_actions = st.columns([1, 6, 1])
            
            with col_check:
                if st.button("✅", key=f"complete_task_{task['id']}", help="Mark as complete"):
                    if complete_micro_task(task['id']):
                        st.success("Task completed!")
                        st.rerun()
                    else:
                        st.error("Failed to complete task")
            
            with col_task_info:
                priority_emoji = {"high": "🔥", "medium": "📋", "low": "📝"}
                priority_color = {"high": "red", "medium": "orange", "low": "gray"}
                
                st.markdown(f"""
                <div style="padding: 8px; border-left: 3px solid {priority_color[task['priority']]}; margin: 4px 0;">
                    <strong>{priority_emoji[task['priority']]} {task['task_name']}</strong><br>
                    <small>⏱️ {task['estimated_minutes']} min | Priority: {task['priority'].title()}</small>
                    {f"<br><em>{task['description']}</em>" if task['description'] else ""}
                </div>
                """, unsafe_allow_html=True)
            
            with col_actions:
                if st.button("🗑️", key=f"delete_task_{task['id']}", help="Delete task"):
                    if delete_micro_task(task['id']):
                        st.success("Task deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete task")
    else:
        st.info("No pending micro-tasks for today. Add some above!")
    
    # Show completed tasks (collapsed by default)
    if completed_tasks:
        with st.expander(f"✅ Completed Tasks ({len(completed_tasks)})", expanded=False):
            for task in completed_tasks:
                priority_emoji = {"high": "🔥", "medium": "📋", "low": "📝"}
                completed_time = task['completed_at'][:16] if task['completed_at'] else "Unknown"
                
                st.markdown(f"""
                <div style="padding: 8px; background-color: #f0f8f0; border-radius: 4px; margin: 4px 0;">
                    <strong>✅ {priority_emoji[task['priority']]} {task['task_name']}</strong><br>
                    <small>⏱️ {task['estimated_minutes']} min | Completed: {completed_time}</small>
                    {f"<br><em>{task['description']}</em>" if task['description'] else ""}
                </div>
                """, unsafe_allow_html=True)
    
    # Show summary
    total_tasks = len(pending_tasks) + len(completed_tasks)
    if total_tasks > 0:
        completion_rate = len(completed_tasks) / total_tasks * 100
        total_estimated_time = sum(task['estimated_minutes'] for task in pending_tasks + completed_tasks)
        completed_time = sum(task['estimated_minutes'] for task in completed_tasks)
        
        st.divider()
        st.subheader("📊 Micro-Task Summary")
        
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        
        with col_stats1:
            st.metric("Completion Rate", f"{completion_rate:.1f}%", f"{len(completed_tasks)}/{total_tasks}")
        
        with col_stats2:
            st.metric("Time Completed", f"{completed_time} min", f"of {total_estimated_time} min")
        
        with col_stats3:
            remaining_time = total_estimated_time - completed_time
            st.metric("Remaining Time", f"{remaining_time} min", f"{len(pending_tasks)} tasks")
