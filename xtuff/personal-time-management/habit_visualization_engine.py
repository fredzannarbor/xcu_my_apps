#!/usr/bin/env python3
"""
Habit Visualization Engine
Creates interactive charts and visualizations for habit metrics and behavior trends
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from habit_metrics_manager import HabitMetricsManager
from behavior_counter_manager import BehaviorCounterManager


class HabitVisualizationEngine:
    """Creates visualizations for habit metrics and behavior trends"""
    
    def __init__(self, db_path='daily_engine.db'):
        self.metrics_manager = HabitMetricsManager(db_path)
        self.behavior_manager = BehaviorCounterManager(db_path)
        
        # Color schemes for different chart types
        self.color_schemes = {
            'metrics': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
            'positive_behaviors': ['#2ca02c', '#32cd32', '#90ee90', '#98fb98', '#00ff7f'],
            'negative_behaviors': ['#d62728', '#ff6b6b', '#ff8c8c', '#ffa8a8', '#ffb3b3'],
            'trends': ['#1f77b4', '#ff7f0e', '#2ca02c']
        }
    
    def generate_metric_trend_chart(self, habit_name: str, metric_name: str, days: int = 30) -> go.Figure:
        """Generate line chart for metric trends over time"""
        history = self.metrics_manager.get_metric_history(habit_name, metric_name, days)
        
        if not history:
            # Return empty chart with message
            fig = go.Figure()
            fig.add_annotation(
                text=f"No data available for {habit_name}.{metric_name}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16)
            )
            fig.update_layout(title=f"{habit_name.replace('_', ' ').title()} - {metric_name.replace('_', ' ').title()}")
            return fig
        
        # Get metric definition for context
        definitions = self.metrics_manager.get_habit_metric_definitions(habit_name)
        metric_def = next((d for d in definitions if d['metric_name'] == metric_name), None)
        
        # Prepare data
        df = pd.DataFrame(history)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Convert values to numeric if possible
        if metric_def and metric_def['data_type'] in ['int', 'float']:
            df['numeric_value'] = pd.to_numeric(df['value'], errors='coerce')
            y_column = 'numeric_value'
            y_title = f"{metric_name.replace('_', ' ').title()}"
            if metric_def.get('unit'):
                y_title += f" ({metric_def['unit']})"
        else:
            # For string metrics, we'll show count of unique values or frequency
            y_column = 'value'
            y_title = "Value"
        
        # Create the chart
        fig = go.Figure()
        
        if metric_def and metric_def['data_type'] in ['int', 'float']:
            # Line chart for numeric data
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df[y_column],
                mode='lines+markers',
                name=metric_name.replace('_', ' ').title(),
                line=dict(color=self.color_schemes['metrics'][0], width=3),
                marker=dict(size=8, color=self.color_schemes['metrics'][0])
            ))
            
            # Add trend line if enough data points
            if len(df) >= 3:
                z = np.polyfit(range(len(df)), df[y_column].fillna(0), 1)
                trend_line = np.poly1d(z)(range(len(df)))
                
                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=trend_line,
                    mode='lines',
                    name='Trend',
                    line=dict(color='red', width=2, dash='dash'),
                    opacity=0.7
                ))
            
            # Add target lines if min/max values are defined
            if metric_def.get('min_value') is not None:
                fig.add_hline(
                    y=metric_def['min_value'],
                    line_dash="dot",
                    line_color="orange",
                    annotation_text=f"Min: {metric_def['min_value']}"
                )
            
            if metric_def.get('max_value') is not None:
                fig.add_hline(
                    y=metric_def['max_value'],
                    line_dash="dot",
                    line_color="red",
                    annotation_text=f"Max: {metric_def['max_value']}"
                )
        
        else:
            # Bar chart for categorical data
            value_counts = df['value'].value_counts()
            fig.add_trace(go.Bar(
                x=value_counts.index,
                y=value_counts.values,
                name='Frequency',
                marker_color=self.color_schemes['metrics'][0]
            ))
            y_title = "Frequency"
        
        # Update layout
        fig.update_layout(
            title=f"{habit_name.replace('_', ' ').title()} - {metric_name.replace('_', ' ').title()} ({days} days)",
            xaxis_title="Date",
            yaxis_title=y_title,
            hovermode='x unified',
            showlegend=True,
            height=400
        )
        
        return fig
    
    def generate_behavior_counter_chart(self, counter_name: str, days: int = 30) -> go.Figure:
        """Generate bar chart for behavior counter analysis"""
        trend_data = self.behavior_manager.get_counter_trends(counter_name, days)
        
        if not trend_data:
            fig = go.Figure()
            fig.add_annotation(
                text=f"No data available for {counter_name}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16)
            )
            fig.update_layout(title=f"{counter_name.replace('_', ' ').title()}")
            return fig
        
        # Get counter definition
        definitions = self.behavior_manager.get_counter_definitions()
        counter_def = next((d for d in definitions if d['counter_name'] == counter_name), None)
        
        # Prepare data
        df = pd.DataFrame(trend_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Choose colors based on counter type
        if counter_def and counter_def['counter_type'] == 'positive':
            colors = self.color_schemes['positive_behaviors']
            color_scale = 'Greens'
        else:
            colors = self.color_schemes['negative_behaviors']
            color_scale = 'Reds'
        
        # Create bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['count'],
            name=counter_name.replace('_', ' ').title(),
            marker=dict(
                color=df['count'],
                colorscale=color_scale,
                showscale=True,
                colorbar=dict(title="Count")
            ),
            text=df['count'],
            textposition='outside'
        ))
        
        # Add average line
        avg_count = df['count'].mean()
        fig.add_hline(
            y=avg_count,
            line_dash="dash",
            line_color="blue",
            annotation_text=f"Average: {avg_count:.1f}"
        )
        
        # Update layout
        counter_type = counter_def['counter_type'] if counter_def else 'behavior'
        fig.update_layout(
            title=f"{counter_name.replace('_', ' ').title()} - {counter_type.title()} Behavior ({days} days)",
            xaxis_title="Date",
            yaxis_title="Count",
            hovermode='x unified',
            height=400
        )
        
        return fig
    
    def generate_correlation_chart(self, habit1: str, metric1: str, habit2: str, metric2: str, days: int = 30) -> go.Figure:
        """Generate scatter plot showing correlation between two metrics"""
        # Get correlation data
        correlation_data = self.metrics_manager.get_metric_correlation(habit1, metric1, habit2, metric2, days)
        
        if 'error' in correlation_data:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Correlation Error: {correlation_data['error']}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16)
            )
            return fig
        
        # Get data for both metrics
        history1 = self.metrics_manager.get_metric_history(habit1, metric1, days)
        history2 = self.metrics_manager.get_metric_history(habit2, metric2, days)
        
        # Create date-indexed dictionaries
        data1 = {entry['date']: float(entry['value']) for entry in history1}
        data2 = {entry['date']: float(entry['value']) for entry in history2}
        
        # Find common dates and create scatter plot data
        common_dates = set(data1.keys()) & set(data2.keys())
        scatter_data = [(data1[date], data2[date], date) for date in common_dates]
        
        if not scatter_data:
            fig = go.Figure()
            fig.add_annotation(
                text="No overlapping data points found",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16)
            )
            return fig
        
        x_vals, y_vals, dates = zip(*scatter_data)
        
        # Create scatter plot
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode='markers',
            marker=dict(
                size=10,
                color=self.color_schemes['trends'][0],
                opacity=0.7
            ),
            text=dates,
            hovertemplate='<b>%{text}</b><br>' +
                         f'{metric1}: %{{x}}<br>' +
                         f'{metric2}: %{{y}}<extra></extra>',
            name='Data Points'
        ))
        
        # Add trend line
        if len(x_vals) >= 2:
            z = np.polyfit(x_vals, y_vals, 1)
            trend_line = np.poly1d(z)
            x_trend = np.linspace(min(x_vals), max(x_vals), 100)
            y_trend = trend_line(x_trend)
            
            fig.add_trace(go.Scatter(
                x=x_trend,
                y=y_trend,
                mode='lines',
                name='Trend Line',
                line=dict(color='red', width=2, dash='dash')
            ))
        
        # Update layout with correlation info
        correlation = correlation_data['correlation']
        strength = correlation_data['strength']
        direction = correlation_data['direction']
        
        fig.update_layout(
            title=f"Correlation: {metric1} vs {metric2}<br>" +
                  f"<sub>r = {correlation:.3f} ({strength} {direction} correlation)</sub>",
            xaxis_title=f"{habit1}.{metric1}",
            yaxis_title=f"{habit2}.{metric2}",
            height=500
        )
        
        return fig
    
    def generate_habit_overview_dashboard(self, habit_name: str = None) -> Dict[str, go.Figure]:
        """Generate comprehensive dashboard for habit overview"""
        charts = {}
        
        if habit_name:
            # Single habit dashboard
            charts.update(self._generate_single_habit_dashboard(habit_name))
        else:
            # All habits overview
            charts.update(self._generate_all_habits_dashboard())
        
        return charts
    
    def _generate_single_habit_dashboard(self, habit_name: str) -> Dict[str, go.Figure]:
        """Generate dashboard for a single habit"""
        charts = {}
        
        # Get all metrics for this habit
        metric_definitions = self.metrics_manager.get_habit_metric_definitions(habit_name)
        
        # Metrics overview chart
        if metric_definitions:
            charts['metrics_overview'] = self._create_metrics_overview_chart(habit_name, metric_definitions)
        
        # Individual metric trend charts
        for metric_def in metric_definitions:
            metric_name = metric_def['metric_name']
            chart_key = f"metric_{metric_name}"
            charts[chart_key] = self.generate_metric_trend_chart(habit_name, metric_name)
        
        # Related behavior counters
        related_counters = self._get_related_behavior_counters(habit_name)
        for counter_name, counter_type in related_counters:
            chart_key = f"behavior_{counter_name}"
            charts[chart_key] = self.generate_behavior_counter_chart(counter_name)
        
        return charts
    
    def _generate_all_habits_dashboard(self) -> Dict[str, go.Figure]:
        """Generate overview dashboard for all habits"""
        charts = {}
        
        # Habits completion overview
        charts['habits_completion'] = self._create_habits_completion_chart()
        
        # Behavior counters summary
        charts['behavior_summary'] = self._create_behavior_summary_chart()
        
        # Metrics consistency chart
        charts['metrics_consistency'] = self._create_metrics_consistency_chart()
        
        return charts
    
    def _create_metrics_overview_chart(self, habit_name: str, metric_definitions: List[Dict]) -> go.Figure:
        """Create overview chart showing all metrics for a habit"""
        fig = make_subplots(
            rows=len(metric_definitions),
            cols=1,
            subplot_titles=[f"{m['metric_name'].replace('_', ' ').title()}" for m in metric_definitions],
            vertical_spacing=0.1
        )
        
        for i, metric_def in enumerate(metric_definitions, 1):
            metric_name = metric_def['metric_name']
            history = self.metrics_manager.get_metric_history(habit_name, metric_name, 30)
            
            if history:
                df = pd.DataFrame(history)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                
                if metric_def['data_type'] in ['int', 'float']:
                    df['numeric_value'] = pd.to_numeric(df['value'], errors='coerce')
                    
                    fig.add_trace(
                        go.Scatter(
                            x=df['date'],
                            y=df['numeric_value'],
                            mode='lines+markers',
                            name=metric_name,
                            line=dict(color=self.color_schemes['metrics'][i % len(self.color_schemes['metrics'])])
                        ),
                        row=i, col=1
                    )
        
        fig.update_layout(
            title=f"{habit_name.replace('_', ' ').title()} - All Metrics Overview",
            height=200 * len(metric_definitions),
            showlegend=False
        )
        
        return fig
    
    def _create_habits_completion_chart(self) -> go.Figure:
        """Create chart showing habit completion rates"""
        # This would integrate with the existing habit tracking system
        # For now, create a placeholder
        fig = go.Figure()
        
        # Get habit data from the existing system
        try:
            from config.settings import config
            habits = config.get_habits()
            
            # Create sample completion data (would be real data in production)
            habit_names = habits['consistent'] + habits['intermittent']
            completion_rates = [85, 92, 78, 65, 88, 73, 95, 82]  # Sample data
            
            fig.add_trace(go.Bar(
                x=[h.replace('_', ' ').title() for h in habit_names[:len(completion_rates)]],
                y=completion_rates[:len(habit_names)],
                marker_color=self.color_schemes['metrics'][0],
                text=[f"{rate}%" for rate in completion_rates[:len(habit_names)]],
                textposition='outside'
            ))
            
            fig.update_layout(
                title="Habit Completion Rates (Last 30 Days)",
                xaxis_title="Habits",
                yaxis_title="Completion Rate (%)",
                height=400
            )
            
        except Exception as e:
            fig.add_annotation(
                text=f"Error loading habit data: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False
            )
        
        return fig
    
    def _create_behavior_summary_chart(self) -> go.Figure:
        """Create summary chart of all behavior counters"""
        # Get daily counts for today
        daily_counts = self.behavior_manager.get_daily_counts()
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Positive Behaviors', 'Negative Behaviors'),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Positive behaviors
        positive_data = daily_counts['positive']
        if positive_data:
            fig.add_trace(
                go.Bar(
                    x=list(positive_data.keys()),
                    y=[data['count'] for data in positive_data.values()],
                    name='Positive',
                    marker_color=self.color_schemes['positive_behaviors'][0]
                ),
                row=1, col=1
            )
        
        # Negative behaviors
        negative_data = daily_counts['negative']
        if negative_data:
            fig.add_trace(
                go.Bar(
                    x=list(negative_data.keys()),
                    y=[data['count'] for data in negative_data.values()],
                    name='Negative',
                    marker_color=self.color_schemes['negative_behaviors'][0]
                ),
                row=1, col=2
            )
        
        fig.update_layout(
            title=f"Today's Behavior Summary ({daily_counts['date']})",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def _create_metrics_consistency_chart(self) -> go.Figure:
        """Create chart showing metrics logging consistency"""
        # Get all metric definitions
        all_definitions = self.metrics_manager.get_habit_metric_definitions()
        
        if not all_definitions:
            fig = go.Figure()
            fig.add_annotation(
                text="No metrics defined yet",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False
            )
            return fig
        
        # Calculate consistency for each metric
        consistency_data = []
        for definition in all_definitions:
            habit_name = definition['habit_name']
            metric_name = definition['metric_name']
            
            history = self.metrics_manager.get_metric_history(habit_name, metric_name, 30)
            days_with_data = len(set(entry['date'] for entry in history)) if history else 0
            consistency = (days_with_data / 30.0) * 100  # Percentage
            
            consistency_data.append({
                'metric': f"{habit_name}.{metric_name}",
                'consistency': consistency
            })
        
        # Create bar chart
        fig = go.Figure()
        
        metrics = [item['metric'] for item in consistency_data]
        consistencies = [item['consistency'] for item in consistency_data]
        
        fig.add_trace(go.Bar(
            x=metrics,
            y=consistencies,
            marker_color=self.color_schemes['metrics'][0],
            text=[f"{c:.1f}%" for c in consistencies],
            textposition='outside'
        ))
        
        # Add target line at 80%
        fig.add_hline(
            y=80,
            line_dash="dash",
            line_color="green",
            annotation_text="Target: 80%"
        )
        
        fig.update_layout(
            title="Metrics Logging Consistency (Last 30 Days)",
            xaxis_title="Metrics",
            yaxis_title="Consistency (%)",
            height=400,
            xaxis_tickangle=-45
        )
        
        return fig
    
    def _get_related_behavior_counters(self, habit_name: str) -> List[Tuple[str, str]]:
        """Get behavior counters related to a habit"""
        # Simple keyword matching - could be enhanced
        all_counters = self.behavior_manager.get_counter_definitions()
        habit_keywords = habit_name.lower().split('_')
        
        related = []
        for counter in all_counters:
            counter_name = counter['counter_name'].lower()
            for keyword in habit_keywords:
                if keyword in counter_name:
                    related.append((counter['counter_name'], counter['counter_type']))
                    break
        
        return related


# Global visualization engine instance
visualization_engine = HabitVisualizationEngine()


# Convenience functions for Streamlit integration
def show_metric_trend_chart(habit_name: str, metric_name: str, days: int = 30):
    """Display metric trend chart in Streamlit"""
    fig = visualization_engine.generate_metric_trend_chart(habit_name, metric_name, days)
    st.plotly_chart(fig, use_container_width=True)


def show_behavior_counter_chart(counter_name: str, days: int = 30):
    """Display behavior counter chart in Streamlit"""
    fig = visualization_engine.generate_behavior_counter_chart(counter_name, days)
    st.plotly_chart(fig, use_container_width=True)


def show_correlation_chart(habit1: str, metric1: str, habit2: str, metric2: str, days: int = 30):
    """Display correlation chart in Streamlit"""
    fig = visualization_engine.generate_correlation_chart(habit1, metric1, habit2, metric2, days)
    st.plotly_chart(fig, use_container_width=True)


def show_habit_dashboard(habit_name: str = None):
    """Display comprehensive habit dashboard in Streamlit"""
    charts = visualization_engine.generate_habit_overview_dashboard(habit_name)
    
    for chart_name, fig in charts.items():
        st.subheader(chart_name.replace('_', ' ').title())
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    # Test the visualization engine
    print("Testing Habit Visualization Engine...")
    
    engine = HabitVisualizationEngine()
    
    # Test metric trend chart
    try:
        fig = engine.generate_metric_trend_chart('exercise', 'weight')
        print("✓ Metric trend chart generated")
    except Exception as e:
        print(f"✗ Metric trend chart error: {e}")
    
    # Test behavior counter chart
    try:
        fig = engine.generate_behavior_counter_chart('healthy_eating')
        print("✓ Behavior counter chart generated")
    except Exception as e:
        print(f"✗ Behavior counter chart error: {e}")
    
    # Test dashboard
    try:
        charts = engine.generate_habit_overview_dashboard()
        print(f"✓ Dashboard generated with {len(charts)} charts")
    except Exception as e:
        print(f"✗ Dashboard error: {e}")
    
    print("Habit Visualization Engine test completed!")