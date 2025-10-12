#!/usr/bin/env python3
"""
Comprehensive Visualization Dashboard
Main dashboard showing all metrics, trends, and habit analytics
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any
from habit_metrics_manager import habit_metrics_manager
from behavior_counter_manager import behavior_counter_manager
from enhanced_promotion_system import enhanced_promotion_system
from habit_visualization_engine import visualization_engine
from config.settings import config


def render_comprehensive_dashboard():
    """Render the main comprehensive dashboard"""
    st.set_page_config(
        page_title="Habit Analytics Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Comprehensive Habit Analytics Dashboard")
    st.markdown("*Data-driven insights for habit optimization and behavioral analysis*")
    
    # Time period selector
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        time_period = st.selectbox(
            "📅 Time Period:",
            [7, 14, 30, 60, 90],
            index=2,
            format_func=lambda x: f"Last {x} days"
        )
    
    with col2:
        auto_refresh = st.checkbox("🔄 Auto Refresh", value=False)
    
    with col3:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    
    # Main dashboard sections
    render_overview_metrics(time_period)
    render_habit_performance_section(time_period)
    render_behavior_analysis_section(time_period)
    render_trends_and_correlations_section(time_period)
    render_promotion_insights_section()
    
    # Auto refresh
    if auto_refresh:
        st.rerun()


def render_overview_metrics(time_period: int):
    """Render overview metrics section"""
    st.header("🎯 Overview Metrics")
    
    # Get summary data
    habits = config.get_habits()
    all_habits = habits['consistent'] + habits['intermittent']
    
    # Calculate key metrics
    total_habits = len(all_habits)
    daily_counts = behavior_counter_manager.get_daily_counts()
    
    # Get metrics consistency
    all_definitions = habit_metrics_manager.get_habit_metric_definitions()
    metrics_logged_today = len(habit_metrics_manager.get_metrics_for_date())
    total_possible_metrics = len(all_definitions)
    
    # Display key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "📋 Total Habits",
            total_habits,
            help="Total number of tracked habits"
        )
    
    with col2:
        positive_total = daily_counts.get('total_positive', 0)
        st.metric(
            "✅ Positive Behaviors",
            positive_total,
            help="Today's positive behavior count"
        )
    
    with col3:
        negative_total = daily_counts.get('total_negative', 0)
        st.metric(
            "⚠️ Negative Behaviors",
            negative_total,
            delta=-negative_total if negative_total > 0 else None,
            help="Today's negative behavior count"
        )
    
    with col4:
        metrics_rate = (metrics_logged_today / total_possible_metrics * 100) if total_possible_metrics > 0 else 0
        st.metric(
            "📊 Metrics Logged",
            f"{metrics_rate:.0f}%",
            f"{metrics_logged_today}/{total_possible_metrics}",
            help="Percentage of metrics logged today"
        )
    
    with col5:
        # Calculate overall habit score (placeholder)
        habit_score = min(100, (positive_total * 10 - negative_total * 5 + metrics_rate) / 2)
        st.metric(
            "🏆 Habit Score",
            f"{habit_score:.0f}",
            help="Overall habit performance score"
        )


def render_habit_performance_section(time_period: int):
    """Render habit performance analysis section"""
    st.header("📈 Habit Performance Analysis")
    
    # Get habits and their performance
    habits = config.get_habits()
    all_habits = habits['consistent'] + habits['intermittent']
    
    if not all_habits:
        st.info("No habits configured for analysis")
        return
    
    # Create performance comparison chart
    fig = create_habit_performance_chart(all_habits, time_period)
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed habit breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔄 Consistent Habits")
        if habits['consistent']:
            for habit in habits['consistent']:
                render_habit_performance_card(habit, 'consistent', time_period)
        else:
            st.info("No consistent habits configured")
    
    with col2:
        st.subheader("📅 Intermittent Habits")
        if habits['intermittent']:
            for habit in habits['intermittent']:
                render_habit_performance_card(habit, 'intermittent', time_period)
        else:
            st.info("No intermittent habits configured")


def create_habit_performance_chart(habits: List[str], time_period: int) -> go.Figure:
    """Create habit performance comparison chart"""
    fig = go.Figure()
    
    # Get performance data for each habit
    habit_data = []
    for habit in habits:
        # Get enhanced analysis
        analysis = enhanced_promotion_system.analyze_habit_performance(habit)
        
        if analysis.get('recommendation') != 'insufficient_data':
            metrics = analysis.get('metrics', {})
            consistency_rate = metrics.get('consistency_rate', 0) * 100
            max_streak = metrics.get('max_streak', 0)
            recent_performance = metrics.get('recent_performance', 0) * 100
            
            habit_data.append({
                'habit': habit.replace('_', ' ').title(),
                'consistency': consistency_rate,
                'max_streak': max_streak,
                'recent_performance': recent_performance
            })
    
    if not habit_data:
        fig.add_annotation(
            text="Insufficient data for habit performance analysis",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Create grouped bar chart
    habits_names = [d['habit'] for d in habit_data]
    consistency_rates = [d['consistency'] for d in habit_data]
    recent_performance = [d['recent_performance'] for d in habit_data]
    
    fig.add_trace(go.Bar(
        name='Overall Consistency',
        x=habits_names,
        y=consistency_rates,
        marker_color='lightblue',
        text=[f"{rate:.1f}%" for rate in consistency_rates],
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        name='Recent Performance',
        x=habits_names,
        y=recent_performance,
        marker_color='darkblue',
        text=[f"{rate:.1f}%" for rate in recent_performance],
        textposition='outside'
    ))
    
    fig.update_layout(
        title=f"Habit Performance Comparison ({time_period} days)",
        xaxis_title="Habits",
        yaxis_title="Performance (%)",
        barmode='group',
        height=400
    )
    
    return fig


def render_habit_performance_card(habit_name: str, category: str, time_period: int):
    """Render individual habit performance card"""
    with st.container():
        # Get habit analysis
        analysis = enhanced_promotion_system.analyze_habit_performance(habit_name)
        
        if analysis.get('recommendation') == 'insufficient_data':
            st.info(f"{habit_name.replace('_', ' ').title()}: Insufficient data")
            return
        
        # Create expandable card
        with st.expander(f"📊 {habit_name.replace('_', ' ').title()}", expanded=False):
            metrics = analysis.get('metrics', {})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                consistency = metrics.get('consistency_rate', 0)
                st.metric("Consistency", f"{consistency:.1%}")
            
            with col2:
                max_streak = metrics.get('max_streak', 0)
                st.metric("Max Streak", f"{max_streak} days")
            
            with col3:
                recent_perf = metrics.get('recent_performance', 0)
                st.metric("Recent", f"{recent_perf:.1%}")
            
            # Recommendation
            recommendation = analysis.get('enhanced_recommendation', analysis.get('recommendation', ''))
            if recommendation:
                rec_color = {
                    'promote_to_consistent': '🟢',
                    'strongly_promote_to_consistent': '🟢',
                    'maintain_consistent': '🔵',
                    'consider_promotion': '🟡',
                    'maintain_intermittent': '🔵',
                    'consider_demotion': '🟡',
                    'demote_to_intermittent': '🔴'
                }.get(recommendation, '⚪')
                
                st.write(f"{rec_color} **Recommendation:** {recommendation.replace('_', ' ').title()}")


def render_behavior_analysis_section(time_period: int):
    """Render behavior analysis section"""
    st.header("🔄 Behavior Analysis")
    
    # Get behavior data
    daily_counts = behavior_counter_manager.get_daily_counts()
    weekly_summary = behavior_counter_manager.get_weekly_summary()
    
    # Behavior overview chart
    fig = create_behavior_overview_chart(time_period)
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed behavior breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ Positive Behavior Trends")
        render_positive_behavior_trends(time_period)
    
    with col2:
        st.subheader("⚠️ Negative Behavior Patterns")
        render_negative_behavior_patterns(time_period)
    
    # Weekly insights
    if weekly_summary.get('summary'):
        st.subheader("📊 Weekly Insights")
        render_weekly_behavior_insights(weekly_summary)


def create_behavior_overview_chart(time_period: int) -> go.Figure:
    """Create behavior overview chart"""
    # Get all counter trends
    all_trends = behavior_counter_manager.get_all_counter_trends(time_period)
    
    if not all_trends:
        fig = go.Figure()
        fig.add_annotation(
            text="No behavior data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig
    
    # Create subplots for positive and negative behaviors
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Positive Behaviors', 'Negative Behaviors'),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )
    
    # Get counter definitions to separate positive/negative
    counter_definitions = behavior_counter_manager.get_counter_definitions()
    counter_types = {c['counter_name']: c['counter_type'] for c in counter_definitions}
    
    positive_data = {}
    negative_data = {}
    
    for counter_name, trend_data in all_trends.items():
        counter_type = counter_types.get(counter_name, 'positive')
        total_count = sum(entry['count'] for entry in trend_data)
        
        if counter_type == 'positive':
            positive_data[counter_name] = total_count
        else:
            negative_data[counter_name] = total_count
    
    # Add positive behaviors
    if positive_data:
        fig.add_trace(
            go.Bar(
                x=list(positive_data.keys()),
                y=list(positive_data.values()),
                name='Positive',
                marker_color='green',
                text=list(positive_data.values()),
                textposition='outside'
            ),
            row=1, col=1
        )
    
    # Add negative behaviors
    if negative_data:
        fig.add_trace(
            go.Bar(
                x=list(negative_data.keys()),
                y=list(negative_data.values()),
                name='Negative',
                marker_color='red',
                text=list(negative_data.values()),
                textposition='outside'
            ),
            row=1, col=2
        )
    
    fig.update_layout(
        title=f"Behavior Overview ({time_period} days)",
        height=400,
        showlegend=False
    )
    
    return fig


def render_positive_behavior_trends(time_period: int):
    """Render positive behavior trends"""
    counter_definitions = behavior_counter_manager.get_counter_definitions()
    positive_counters = [c for c in counter_definitions if c['counter_type'] == 'positive']
    
    if not positive_counters:
        st.info("No positive behavior counters configured")
        return
    
    for counter in positive_counters[:3]:  # Show top 3
        counter_name = counter['counter_name']
        stats = behavior_counter_manager.get_counter_statistics(counter_name, time_period)
        
        if 'error' not in stats:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total", stats.get('total_count', 0))
            with col2:
                st.metric("Daily Avg", f"{stats.get('average_daily', 0):.1f}")
            with col3:
                trend = stats.get('trend_direction', 'stable')
                trend_emoji = {'increasing': '📈', 'decreasing': '📉', 'stable': '➡️'}.get(trend, '➡️')
                st.metric("Trend", f"{trend_emoji} {trend.title()}")
            
            st.caption(f"**{counter_name.replace('_', ' ').title()}**")


def render_negative_behavior_patterns(time_period: int):
    """Render negative behavior patterns"""
    counter_definitions = behavior_counter_manager.get_counter_definitions()
    negative_counters = [c for c in counter_definitions if c['counter_type'] == 'negative']
    
    if not negative_counters:
        st.info("No negative behavior counters configured")
        return
    
    for counter in negative_counters[:3]:  # Show top 3
        counter_name = counter['counter_name']
        stats = behavior_counter_manager.get_counter_statistics(counter_name, time_period)
        
        if 'error' not in stats:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total = stats.get('total_count', 0)
                st.metric("Total", total, delta=-total if total > 0 else None)
            with col2:
                avg = stats.get('average_daily', 0)
                st.metric("Daily Avg", f"{avg:.1f}", delta=-avg if avg > 0 else None)
            with col3:
                streak = stats.get('current_streak', 0)
                # For negative behaviors, we want to show avoidance streak
                avoidance_streak = time_period - streak if streak < time_period else 0
                st.metric("Avoidance", f"{avoidance_streak} days")
            
            st.caption(f"**{counter_name.replace('_', ' ').title()}**")


def render_weekly_behavior_insights(weekly_summary: Dict):
    """Render weekly behavior insights"""
    summary = weekly_summary.get('summary', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Positive Total", summary.get('total_positive_behaviors', 0))
    
    with col2:
        st.metric("Negative Total", summary.get('total_negative_behaviors', 0))
    
    with col3:
        st.metric("Consistency", f"{summary.get('consistency_score', 0):.1f}%")
    
    with col4:
        # Calculate behavior ratio
        pos_total = summary.get('total_positive_behaviors', 0)
        neg_total = summary.get('total_negative_behaviors', 0)
        ratio = pos_total / max(neg_total, 1)  # Avoid division by zero
        st.metric("Pos/Neg Ratio", f"{ratio:.1f}:1")


def render_trends_and_correlations_section(time_period: int):
    """Render trends and correlations section"""
    st.header("📊 Trends & Correlations")
    
    # Get all metrics for correlation analysis
    all_definitions = habit_metrics_manager.get_habit_metric_definitions()
    
    if len(all_definitions) < 2:
        st.info("Need at least 2 metrics for correlation analysis")
        return
    
    # Correlation analysis
    st.subheader("🔗 Metric Correlations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        metric1_options = [f"{d['habit_name']}.{d['metric_name']}" for d in all_definitions]
        metric1_selection = st.selectbox("First metric:", metric1_options, key="corr_metric1")
    
    with col2:
        metric2_options = [opt for opt in metric1_options if opt != metric1_selection]
        if metric2_options:
            metric2_selection = st.selectbox("Second metric:", metric2_options, key="corr_metric2")
        else:
            metric2_selection = None
    
    if metric1_selection and metric2_selection:
        # Parse selections
        habit1, metric1 = metric1_selection.split('.')
        habit2, metric2 = metric2_selection.split('.')
        
        # Show correlation chart
        from habit_visualization_engine import show_correlation_chart
        show_correlation_chart(habit1, metric1, habit2, metric2, time_period)
        
        # Calculate and display correlation
        correlation_data = habit_metrics_manager.get_metric_correlation(
            habit1, metric1, habit2, metric2, time_period
        )
        
        if 'error' not in correlation_data:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                corr = correlation_data.get('correlation', 0)
                st.metric("Correlation", f"{corr:.3f}")
            
            with col2:
                strength = correlation_data.get('strength', 'none')
                st.metric("Strength", strength.title())
            
            with col3:
                direction = correlation_data.get('direction', 'none')
                st.metric("Direction", direction.title())


def render_promotion_insights_section():
    """Render habit promotion insights section"""
    st.header("🧠 Promotion Insights")
    
    # Get promotion analysis for all habits
    results = enhanced_promotion_system.execute_all_promotions(auto_execute=False)
    
    # Promotion candidates
    promotion_candidates = [r for r in results['recommended_changes'] 
                          if r['recommendation'] == 'promote_to_consistent']
    
    demotion_candidates = [r for r in results['recommended_changes'] 
                         if r['recommendation'] == 'demote_to_intermittent']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 Ready for Promotion")
        if promotion_candidates:
            for candidate in promotion_candidates:
                habit = candidate['habit']
                analysis = candidate['analysis']
                confidence = analysis.get('confidence_score', 0)
                
                with st.container():
                    st.write(f"**{habit.replace('_', ' ').title()}**")
                    st.progress(confidence)
                    st.caption(f"Confidence: {confidence:.1%}")
        else:
            st.info("No habits ready for promotion")
    
    with col2:
        st.subheader("⚠️ Consider Demotion")
        if demotion_candidates:
            for candidate in demotion_candidates:
                habit = candidate['habit']
                analysis = candidate['analysis']
                confidence = analysis.get('confidence_score', 0)
                
                with st.container():
                    st.write(f"**{habit.replace('_', ' ').title()}**")
                    st.progress(confidence)
                    st.caption(f"Confidence: {confidence:.1%}")
        else:
            st.info("No habits need demotion")
    
    # Summary statistics
    st.subheader("📈 Promotion Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Analyzed", len(results['recommended_changes']) + len(results['no_changes']))
    
    with col2:
        st.metric("Promotion Ready", len(promotion_candidates))
    
    with col3:
        st.metric("Demotion Risk", len(demotion_candidates))
    
    with col4:
        st.metric("Stable Habits", len(results['no_changes']))


if __name__ == "__main__":
    render_comprehensive_dashboard()