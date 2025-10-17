#!/usr/bin/env python3
"""
Enhanced Habit Tracker UI
Version 1.1.0 - Migrated to shared authentication system
Extended habit tracker with metrics input and behavior counters
"""

import streamlit as st
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add shared modules to path
sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
    from shared.ui import render_unified_sidebar
except ImportError as e:
    st.error(f"Failed to import shared authentication: {e}")
    st.error("Please ensure /Users/fred/xcu_my_apps/shared/auth is accessible")
    st.stop()

from habit_metrics_manager import habit_metrics_manager, add_metric_to_habit, log_metric_value
from behavior_counter_manager import behavior_counter_manager, create_positive_counter, create_negative_counter, increment_counter
from enhanced_promotion_system import enhanced_promotion_system, get_enhanced_habit_analysis
from habit_visualization_engine import show_metric_trend_chart, show_behavior_counter_chart, show_habit_dashboard
from habits.habit_tracker import log_habit_completion
from config.settings import config

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize shared authentication system
try:
    shared_auth = get_shared_auth()
    logger.info("Shared authentication system initialized")
except Exception as e:
    logger.error(f"Failed to initialize shared auth: {e}")
    st.error("Authentication system unavailable.")


def render_enhanced_habit_tracker():
    """Render the enhanced habit tracker interface"""

    # Initialize session state for auth sync
    if is_authenticated():
        user_info = get_user_info()
        st.session_state.username = user_info.get('username')
        st.session_state.user_name = user_info.get('user_name')
        st.session_state.user_email = user_info.get('user_email')
        logger.info(f"User authenticated via shared auth: {st.session_state.username}")
    else:
        if "username" not in st.session_state:
            st.session_state.username = None

    st.title("🎯 Enhanced Habit Tracker")
    st.markdown("*Track habits with quantitative metrics and behavior counters*")

    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Today's Tracking",
        "📈 Metrics & Trends",
        "🔄 Behavior Counters",
        "🧠 Habit Analysis",
        "⚙️ Configuration"
    ])
    
    with tab1:
        render_daily_tracking()
    
    with tab2:
        render_metrics_trends()
    
    with tab3:
        render_behavior_counters()
    
    with tab4:
        render_habit_analysis()
    
    with tab5:
        render_habit_configuration()


def render_daily_tracking():
    """Render today's habit tracking interface"""
    st.header("📊 Today's Tracking")
    
    # Get habits configuration
    habits = config.get_habits()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Consistent Habits Section
    st.subheader("🔄 Daily Consistent Habits")
    
    if habits['consistent']:
        consistent_completed = 0
        
        for habit in habits['consistent']:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                completed = st.checkbox(
                    f"{habit.replace('_', ' ').title()}",
                    key=f"consistent_{habit}_{today}"
                )
                if completed:
                    log_habit_completion(habit, True)
                    consistent_completed += 1
            
            with col2:
                # Show current streak
                st.write("🔥 7")  # Placeholder - would get real streak
            
            with col3:
                # Quick metrics button
                if st.button("📊", key=f"metrics_{habit}", help="Log metrics"):
                    st.session_state[f'show_metrics_{habit}'] = True
            
            # Show metrics input if requested
            if st.session_state.get(f'show_metrics_{habit}', False):
                render_habit_metrics_input(habit)
        
        # Progress indicator
        if habits['consistent']:
            progress = consistent_completed / len(habits['consistent'])
            st.progress(progress)
            st.write(f"Progress: {consistent_completed}/{len(habits['consistent'])} ({progress*100:.0f}%)")
    else:
        st.info("No consistent habits configured")
    
    st.divider()
    
    # Intermittent Habits Section
    st.subheader("📅 Intermittent Habits")
    
    if habits['intermittent']:
        intermittent_completed = 0
        
        for habit in habits['intermittent']:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                completed = st.checkbox(
                    f"{habit.replace('_', ' ').title()}",
                    key=f"intermittent_{habit}_{today}"
                )
                if completed:
                    log_habit_completion(habit, True)
                    intermittent_completed += 1
            
            with col2:
                # Show schedule indicator
                st.write("3x/wk")  # Placeholder
            
            with col3:
                # Quick metrics button
                if st.button("📊", key=f"metrics_int_{habit}", help="Log metrics"):
                    st.session_state[f'show_metrics_{habit}'] = True
            
            # Show metrics input if requested
            if st.session_state.get(f'show_metrics_{habit}', False):
                render_habit_metrics_input(habit)
        
        # Progress indicator
        if habits['intermittent']:
            progress = intermittent_completed / len(habits['intermittent'])
            st.progress(progress)
            st.write(f"Progress: {intermittent_completed}/{len(habits['intermittent'])} ({progress*100:.0f}%)")
    else:
        st.info("No intermittent habits configured")


def render_habit_metrics_input(habit_name: str):
    """Render metrics input for a specific habit"""
    with st.expander(f"📊 Metrics for {habit_name.replace('_', ' ').title()}", expanded=True):
        # Get metric definitions for this habit
        metric_definitions = habit_metrics_manager.get_habit_metric_definitions(habit_name)
        
        if not metric_definitions:
            st.info(f"No metrics defined for {habit_name}. Configure metrics in the Configuration tab.")
            return
        
        # Create input fields for each metric
        metric_values = {}
        
        for metric_def in metric_definitions:
            metric_name = metric_def['metric_name']
            data_type = metric_def['data_type']
            description = metric_def.get('description', '')
            unit = metric_def.get('unit', '')
            min_value = metric_def.get('min_value')
            max_value = metric_def.get('max_value')
            
            label = f"{metric_name.replace('_', ' ').title()}"
            if unit:
                label += f" ({unit})"
            if description:
                label += f" - {description}"
            
            if data_type == 'int':
                value = st.number_input(
                    label,
                    min_value=int(min_value) if min_value is not None else None,
                    max_value=int(max_value) if max_value is not None else None,
                    step=1,
                    key=f"metric_{habit_name}_{metric_name}"
                )
                metric_values[metric_name] = int(value) if value is not None else None
                
            elif data_type == 'float':
                value = st.number_input(
                    label,
                    min_value=float(min_value) if min_value is not None else None,
                    max_value=float(max_value) if max_value is not None else None,
                    step=0.1,
                    key=f"metric_{habit_name}_{metric_name}"
                )
                metric_values[metric_name] = float(value) if value is not None else None
                
            elif data_type == 'string':
                value = st.text_input(
                    label,
                    key=f"metric_{habit_name}_{metric_name}"
                )
                metric_values[metric_name] = value if value else None
        
        # Save button
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button(f"💾 Save Metrics", key=f"save_metrics_{habit_name}"):
                saved_count = 0
                for metric_name, value in metric_values.items():
                    if value is not None:
                        success = log_metric_value(habit_name, metric_name, value)
                        if success:
                            saved_count += 1
                
                if saved_count > 0:
                    st.success(f"Saved {saved_count} metrics for {habit_name}")
                else:
                    st.warning("No metrics to save")
        
        with col2:
            if st.button(f"❌ Close", key=f"close_metrics_{habit_name}"):
                st.session_state[f'show_metrics_{habit_name}'] = False
                st.rerun()


def render_metrics_trends():
    """Render metrics and trends visualization"""
    st.header("📈 Metrics & Trends")
    
    # Get all habits with metrics
    all_definitions = habit_metrics_manager.get_habit_metric_definitions()
    
    if not all_definitions:
        st.info("No metrics defined yet. Configure metrics in the Configuration tab.")
        return
    
    # Group by habit
    habits_with_metrics = {}
    for definition in all_definitions:
        habit_name = definition['habit_name']
        if habit_name not in habits_with_metrics:
            habits_with_metrics[habit_name] = []
        habits_with_metrics[habit_name].append(definition)
    
    # Habit selector
    selected_habit = st.selectbox(
        "Select habit to view:",
        options=list(habits_with_metrics.keys()),
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    if selected_habit:
        st.subheader(f"📊 {selected_habit.replace('_', ' ').title()} Metrics")
        
        # Time period selector
        col1, col2 = st.columns([1, 1])
        with col1:
            days = st.selectbox("Time period:", [7, 14, 30, 60, 90], index=2)
        
        with col2:
            chart_type = st.selectbox("View type:", ["Individual Charts", "Combined Dashboard"])
        
        if chart_type == "Individual Charts":
            # Show individual metric charts
            for metric_def in habits_with_metrics[selected_habit]:
                metric_name = metric_def['metric_name']
                st.subheader(f"{metric_name.replace('_', ' ').title()}")
                
                # Show trend chart
                show_metric_trend_chart(selected_habit, metric_name, days)
                
                # Show statistics
                stats = habit_metrics_manager.get_metric_statistics(selected_habit, metric_name, days)
                if 'error' not in stats:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Average", f"{stats.get('mean', 0):.2f}")
                    with col2:
                        st.metric("Latest", f"{stats.get('latest_value', 0)}")
                    with col3:
                        st.metric("Trend", stats.get('trend', 'stable').title())
                    with col4:
                        st.metric("Data Points", stats.get('count', 0))
        
        else:
            # Show combined dashboard
            show_habit_dashboard(selected_habit)


def render_behavior_counters():
    """Render behavior counters interface"""
    st.header("🔄 Behavior Counters")
    
    # Get today's counts
    daily_counts = behavior_counter_manager.get_daily_counts()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ Positive Behaviors")
        
        positive_counters = daily_counts['positive']
        if positive_counters:
            for counter_name, counter_data in positive_counters.items():
                col_name, col_count, col_btn = st.columns([2, 1, 1])
                
                with col_name:
                    st.write(f"**{counter_name.replace('_', ' ').title()}**")
                    if counter_data.get('description'):
                        st.caption(counter_data['description'])
                
                with col_count:
                    st.metric("Today", counter_data['count'])
                
                with col_btn:
                    if st.button("➕", key=f"inc_pos_{counter_name}", help="Increment"):
                        increment_counter(counter_name, 1)
                        st.rerun()
        else:
            st.info("No positive behavior counters configured")
        
        # Quick add positive behavior
        with st.expander("➕ Quick Add Positive Behavior"):
            new_behavior = st.text_input("Behavior name:", key="new_pos_behavior")
            if st.button("Add & Increment", key="add_pos_behavior") and new_behavior:
                create_positive_counter(new_behavior.lower().replace(' ', '_'), new_behavior)
                increment_counter(new_behavior.lower().replace(' ', '_'), 1)
                st.success(f"Added and incremented {new_behavior}")
                st.rerun()
    
    with col2:
        st.subheader("⚠️ Negative Behaviors")
        
        negative_counters = daily_counts['negative']
        if negative_counters:
            for counter_name, counter_data in negative_counters.items():
                col_name, col_count, col_btn = st.columns([2, 1, 1])
                
                with col_name:
                    st.write(f"**{counter_name.replace('_', ' ').title()}**")
                    if counter_data.get('description'):
                        st.caption(counter_data['description'])
                
                with col_count:
                    st.metric("Today", counter_data['count'])
                
                with col_btn:
                    if st.button("➕", key=f"inc_neg_{counter_name}", help="Report occurrence"):
                        increment_counter(counter_name, 1)
                        st.rerun()
        else:
            st.info("No negative behavior counters configured")
        
        # Quick add negative behavior
        with st.expander("➕ Quick Add Negative Behavior"):
            new_behavior = st.text_input("Behavior name:", key="new_neg_behavior")
            if st.button("Add & Report", key="add_neg_behavior") and new_behavior:
                create_negative_counter(new_behavior.lower().replace(' ', '_'), new_behavior)
                increment_counter(new_behavior.lower().replace(' ', '_'), 1)
                st.success(f"Added and reported {new_behavior}")
                st.rerun()
    
    st.divider()
    
    # Behavior trends
    st.subheader("📊 Behavior Trends")
    
    # Get all counter definitions
    all_counters = behavior_counter_manager.get_counter_definitions()
    
    if all_counters:
        selected_counter = st.selectbox(
            "Select behavior to view trend:",
            options=[c['counter_name'] for c in all_counters],
            format_func=lambda x: x.replace('_', ' ').title()
        )
        
        if selected_counter:
            days = st.selectbox("Time period:", [7, 14, 30], index=1, key="behavior_trend_days")
            show_behavior_counter_chart(selected_counter, days)
            
            # Show statistics
            stats = behavior_counter_manager.get_counter_statistics(selected_counter, days)
            if 'error' not in stats:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Count", stats.get('total_count', 0))
                with col2:
                    st.metric("Daily Average", f"{stats.get('average_daily', 0):.1f}")
                with col3:
                    st.metric("Current Streak", stats.get('current_streak', 0))
                with col4:
                    st.metric("Trend", stats.get('trend_direction', 'stable').title())


def render_habit_analysis():
    """Render enhanced habit analysis"""
    st.header("🧠 Enhanced Habit Analysis")
    
    # Get all habits
    habits = config.get_habits()
    all_habits = habits['consistent'] + habits['intermittent']
    
    if not all_habits:
        st.info("No habits configured")
        return
    
    # Habit selector
    selected_habit = st.selectbox(
        "Select habit to analyze:",
        options=all_habits,
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    if selected_habit:
        # Get enhanced analysis
        analysis = get_enhanced_habit_analysis(selected_habit)
        
        if analysis.get('recommendation') == 'insufficient_data':
            st.warning(f"Insufficient data for {selected_habit}. Track this habit for at least 21 days for analysis.")
            return
        
        # Display analysis results
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Current Status")
            
            current_category = analysis.get('current_category', 'unknown')
            st.metric("Current Category", current_category.title())
            
            base_recommendation = analysis.get('recommendation', 'maintain')
            enhanced_recommendation = analysis.get('enhanced_recommendation', base_recommendation)
            
            st.metric("Base Recommendation", base_recommendation.replace('_', ' ').title())
            st.metric("Enhanced Recommendation", enhanced_recommendation.replace('_', ' ').title())
            
            confidence = analysis.get('confidence_score', 0)
            st.metric("Confidence Score", f"{confidence:.1%}")
        
        with col2:
            st.subheader("🔍 Analysis Factors")
            
            metrics = analysis.get('metrics', {})
            if metrics:
                st.metric("Consistency Rate", f"{metrics.get('consistency_rate', 0):.1%}")
                st.metric("Max Streak", f"{metrics.get('max_streak', 0)} days")
                st.metric("Recent Performance", f"{metrics.get('recent_performance', 0):.1%}")
        
        # Enhanced factors
        if 'behavior_influence' in analysis:
            st.subheader("🎯 Behavior Influence")
            
            behavior_inf = analysis['behavior_influence']
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Positive Influence", f"{behavior_inf.get('positive_influence', 0):.2f}")
            with col2:
                st.metric("Negative Influence", f"{behavior_inf.get('negative_influence', 0):.2f}")
            with col3:
                st.metric("Overall Influence", f"{behavior_inf.get('overall_influence', 0):.2f}")
            
            # Related counters
            if behavior_inf.get('related_counters'):
                st.write("**Related Behavior Counters:**")
                for counter in behavior_inf['related_counters']:
                    influence = counter.get('influence', 0)
                    emoji = "✅" if influence > 0 else "⚠️" if influence < 0 else "➖"
                    st.write(f"{emoji} {counter['counter_name'].replace('_', ' ').title()}: {influence:+.2f}")
        
        # Metrics influence
        if 'metrics_influence' in analysis:
            st.subheader("📈 Metrics Influence")
            
            metrics_inf = analysis['metrics_influence']
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Consistency Score", f"{metrics_inf.get('consistency_score', 0):.1%}")
            with col2:
                st.metric("Improvement Score", f"{metrics_inf.get('improvement_score', 0):.2f}")
            
            # Analyzed metrics
            if metrics_inf.get('metrics_analyzed'):
                st.write("**Analyzed Metrics:**")
                for metric in metrics_inf['metrics_analyzed']:
                    consistency = metric.get('consistency', 0)
                    st.write(f"• {metric['metric_name'].replace('_', ' ').title()}: {consistency:.1%} consistency")
        
        # Research basis
        if analysis.get('research_basis'):
            with st.expander("🔬 Research Basis"):
                st.write(analysis['research_basis'])


def render_habit_configuration():
    """Render habit configuration interface"""
    st.header("⚙️ Habit Configuration")
    
    tab1, tab2 = st.tabs(["📊 Metrics Setup", "🔄 Behavior Counters Setup"])
    
    with tab1:
        render_metrics_configuration()
    
    with tab2:
        render_behavior_counters_configuration()


def render_metrics_configuration():
    """Render metrics configuration interface"""
    st.subheader("📊 Habit Metrics Configuration")
    
    # Get all habits
    habits = config.get_habits()
    all_habits = habits['consistent'] + habits['intermittent']
    
    if not all_habits:
        st.info("No habits configured. Add habits in the main settings.")
        return
    
    # Select habit to configure
    selected_habit = st.selectbox(
        "Select habit to configure metrics:",
        options=all_habits,
        format_func=lambda x: x.replace('_', ' ').title(),
        key="metrics_config_habit"
    )
    
    if selected_habit:
        # Show existing metrics
        existing_metrics = habit_metrics_manager.get_habit_metric_definitions(selected_habit)
        
        if existing_metrics:
            st.write("**Existing Metrics:**")
            for metric in existing_metrics:
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.write(f"• {metric['metric_name'].replace('_', ' ').title()}")
                with col2:
                    st.write(metric['data_type'])
                with col3:
                    st.write(metric.get('unit', '-'))
                with col4:
                    if st.button("🗑️", key=f"del_metric_{metric['metric_name']}", help="Delete metric"):
                        # Note: Would implement deletion here
                        st.warning("Metric deletion not implemented in demo")
        
        st.divider()
        
        # Add new metric
        st.write("**Add New Metric:**")
        
        col1, col2 = st.columns(2)
        with col1:
            metric_name = st.text_input("Metric name:", key="new_metric_name")
            data_type = st.selectbox("Data type:", ['int', 'float', 'string'], key="new_metric_type")
        
        with col2:
            description = st.text_input("Description:", key="new_metric_desc")
            unit = st.text_input("Unit (optional):", key="new_metric_unit")
        
        if data_type in ['int', 'float']:
            col1, col2 = st.columns(2)
            with col1:
                min_value = st.number_input("Minimum value (optional):", value=None, key="new_metric_min")
            with col2:
                max_value = st.number_input("Maximum value (optional):", value=None, key="new_metric_max")
        else:
            min_value = max_value = None
        
        if st.button("➕ Add Metric", key="add_new_metric"):
            if metric_name:
                success = add_metric_to_habit(
                    selected_habit, 
                    metric_name.lower().replace(' ', '_'),
                    data_type,
                    description=description or None,
                    unit=unit or None,
                    min_value=min_value,
                    max_value=max_value
                )
                
                if success:
                    st.success(f"Added metric '{metric_name}' to {selected_habit}")
                    st.rerun()
                else:
                    st.error("Failed to add metric")
            else:
                st.error("Metric name is required")


def render_behavior_counters_configuration():
    """Render behavior counters configuration interface"""
    st.subheader("🔄 Behavior Counters Configuration")
    
    # Show existing counters
    existing_counters = behavior_counter_manager.get_counter_definitions()
    
    if existing_counters:
        st.write("**Existing Counters:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Positive Behaviors:**")
            positive_counters = [c for c in existing_counters if c['counter_type'] == 'positive']
            for counter in positive_counters:
                st.write(f"✅ {counter['counter_name'].replace('_', ' ').title()}")
                if counter.get('description'):
                    st.caption(counter['description'])
        
        with col2:
            st.write("**Negative Behaviors:**")
            negative_counters = [c for c in existing_counters if c['counter_type'] == 'negative']
            for counter in negative_counters:
                st.write(f"⚠️ {counter['counter_name'].replace('_', ' ').title()}")
                if counter.get('description'):
                    st.caption(counter['description'])
    
    st.divider()
    
    # Add new counter
    st.write("**Add New Behavior Counter:**")
    
    col1, col2 = st.columns(2)
    with col1:
        counter_name = st.text_input("Counter name:", key="new_counter_name")
        counter_type = st.selectbox("Counter type:", ['positive', 'negative'], key="new_counter_type")
    
    with col2:
        counter_description = st.text_area("Description:", key="new_counter_desc", height=100)
    
    if st.button("➕ Add Counter", key="add_new_counter"):
        if counter_name:
            if counter_type == 'positive':
                success = create_positive_counter(
                    counter_name.lower().replace(' ', '_'),
                    counter_description or None
                )
            else:
                success = create_negative_counter(
                    counter_name.lower().replace(' ', '_'),
                    counter_description or None
                )
            
            if success:
                st.success(f"Added {counter_type} counter '{counter_name}'")
                st.rerun()
            else:
                st.error("Failed to add counter")
        else:
            st.error("Counter name is required")


if __name__ == "__main__":
    # Set page config
    st.set_page_config(
        page_title="Enhanced Habit Tracker",
        page_icon="🎯",
        layout="wide"
    )

    # Hide native Streamlit navigation
    st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

    # Render unified sidebar
    render_unified_sidebar(
        app_name="Time Management",
        show_auth=True,
        show_xtuff_nav=True
    )

    # Initialize the enhanced habit tracker UI
    render_enhanced_habit_tracker()