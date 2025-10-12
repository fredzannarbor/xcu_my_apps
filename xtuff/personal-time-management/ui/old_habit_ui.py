
import streamlit as st
from habit_system.habit_tracker import log_habit_completion
from config.settings import config

def render_habit_ui(habits):
    """Renders the habit tracking UI."""
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

    # Intermittent habits
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
