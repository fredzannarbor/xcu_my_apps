"""
Workflow Analytics Component

Provides detailed analytics and insights for workflow results.
Implements advanced analysis capabilities for tournaments, reader panels, and series generation.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import numpy as np
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).resolve().parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from codexes.modules.ideation.core.codex_object import CodexObject, CodexObjectType

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsMetrics:
    """Container for workflow analytics metrics."""
    total_objects: int
    unique_types: int
    type_distribution: Dict[str, int]
    performance_metrics: Dict[str, float]
    insights: List[str]
    recommendations: List[str]


class WorkflowAnalytics:
    """
    Advanced analytics component for workflow results.
    Provides detailed insights, visualizations, and recommendations.
    """
    
    def __init__(self):
        """Initialize the workflow analytics component."""
        self.session_key = "workflow_analytics_state"
        logger.info("WorkflowAnalytics initialized")
    
    def render_analytics_dashboard(self, workflow_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render comprehensive analytics dashboard for workflow results.
        
        Args:
            workflow_results: Results from workflow execution
            
        Returns:
            Dictionary containing analytics data and user interactions
        """
        if not workflow_results or not workflow_results.get("success"):
            st.info("📊 No workflow results available for analysis.")
            return {}
        
        workflow_type = workflow_results.get("workflow_type", "unknown")
        
        st.markdown("### 📊 Workflow Analytics Dashboard")
        
        # Create analytics tabs
        if workflow_type == "tournament":
            return self._render_tournament_analytics(workflow_results)
        elif workflow_type == "reader_panel":
            return self._render_reader_panel_analytics(workflow_results)
        elif workflow_type == "series_generation":
            return self._render_series_analytics(workflow_results)
        else:
            st.warning(f"Analytics not available for workflow type: {workflow_type}")
            return {}
    
    def _render_tournament_analytics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Render analytics for tournament results."""
        tournament_results = results.get("tournament_results", {})
        
        if not tournament_results:
            st.warning("No tournament results data available.")
            return {}
        
        # Extract tournament data
        participants = tournament_results.get("participants", [])
        matches = tournament_results.get("matches", [])
        final_rankings = tournament_results.get("final_rankings", [])
        
        # Create analytics tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🏆 Results Overview", "📈 Performance Analysis", "🔍 Match Details", "💡 Insights"])
        
        with tab1:
            self._render_tournament_overview(participants, final_rankings, matches)
        
        with tab2:
            self._render_tournament_performance_analysis(participants, matches, final_rankings)
        
        with tab3:
            self._render_tournament_match_details(matches, participants)
        
        with tab4:
            insights = self._generate_tournament_insights(participants, matches, final_rankings)
            self._render_insights_panel(insights)
        
        return {"analytics_type": "tournament", "insights": insights}
    
    def _render_reader_panel_analytics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Render analytics for reader panel results."""
        panel_results = results.get("panel_results", [])
        
        if not panel_results:
            st.warning("No reader panel results data available.")
            return {}
        
        # Create analytics tabs
        tab1, tab2, tab3, tab4 = st.tabs(["👥 Panel Overview", "📊 Evaluation Scores", "🎯 Demographic Analysis", "💡 Insights"])
        
        with tab1:
            self._render_reader_panel_overview(panel_results)
        
        with tab2:
            self._render_reader_panel_scores(panel_results)
        
        with tab3:
            self._render_demographic_analysis(panel_results)
        
        with tab4:
            insights = self._generate_reader_panel_insights(panel_results)
            self._render_insights_panel(insights)
        
        return {"analytics_type": "reader_panel", "insights": insights}
    
    def _render_series_analytics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Render analytics for series generation results."""
        series_data = results.get("series_data", {})
        
        if not series_data:
            st.warning("No series generation results data available.")
            return {}
        
        # Create analytics tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📚 Series Overview", "🔗 Consistency Analysis", "📈 Progression Tracking", "💡 Insights"])
        
        with tab1:
            self._render_series_overview(series_data)
        
        with tab2:
            self._render_consistency_analysis(series_data)
        
        with tab3:
            self._render_progression_tracking(series_data)
        
        with tab4:
            insights = self._generate_series_insights(series_data)
            self._render_insights_panel(insights)
        
        return {"analytics_type": "series_generation", "insights": insights}
    
    def _render_tournament_overview(self, participants: List[Dict], rankings: List[Dict], matches: List[Dict]):
        """Render tournament results overview."""
        st.markdown("#### 🏆 Tournament Results")
        
        # Winner announcement
        if rankings:
            winner = rankings[0]
            st.success(f"🥇 **Winner:** {winner.get('title', 'Unknown')} ({winner.get('type', 'Unknown Type')})")
            
            # Top 3 podium
            col1, col2, col3 = st.columns(3)
            
            if len(rankings) >= 1:
                with col2:  # Winner in center
                    st.markdown("### 🥇")
                    st.write(f"**{rankings[0].get('title', 'Unknown')}**")
                    st.write(f"Type: {rankings[0].get('type', 'Unknown')}")
                    st.write(f"Score: {rankings[0].get('final_score', 0):.2f}")
            
            if len(rankings) >= 2:
                with col1:  # Second place
                    st.markdown("### 🥈")
                    st.write(f"**{rankings[1].get('title', 'Unknown')}**")
                    st.write(f"Type: {rankings[1].get('type', 'Unknown')}")
                    st.write(f"Score: {rankings[1].get('final_score', 0):.2f}")
            
            if len(rankings) >= 3:
                with col3:  # Third place
                    st.markdown("### 🥉")
                    st.write(f"**{rankings[2].get('title', 'Unknown')}**")
                    st.write(f"Type: {rankings[2].get('type', 'Unknown')}")
                    st.write(f"Score: {rankings[2].get('final_score', 0):.2f}")
        
        # Tournament statistics
        st.markdown("#### 📊 Tournament Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Participants", len(participants))
        
        with col2:
            st.metric("Total Matches", len(matches))
        
        with col3:
            # Count content types
            type_counts = {}
            for participant in participants:
                content_type = participant.get('type', 'Unknown')
                type_counts[content_type] = type_counts.get(content_type, 0) + 1
            st.metric("Content Types", len(type_counts))
        
        with col4:
            # Calculate average score
            if rankings:
                avg_score = sum(r.get('final_score', 0) for r in rankings) / len(rankings)
                st.metric("Average Score", f"{avg_score:.2f}")
        
        # Full rankings table
        if rankings:
            st.markdown("#### 📋 Complete Rankings")
            
            rankings_df = pd.DataFrame([
                {
                    "Rank": i + 1,
                    "Title": r.get('title', 'Unknown'),
                    "Type": r.get('type', 'Unknown'),
                    "Final Score": f"{r.get('final_score', 0):.3f}",
                    "Wins": r.get('wins', 0),
                    "Losses": r.get('losses', 0)
                }
                for i, r in enumerate(rankings)
            ])
            
            st.dataframe(rankings_df, use_container_width=True)
    
    def _render_tournament_performance_analysis(self, participants: List[Dict], matches: List[Dict], rankings: List[Dict]):
        """Render detailed performance analysis."""
        st.markdown("#### 📈 Performance Analysis")
        
        if not rankings:
            st.warning("No ranking data available for analysis.")
            return
        
        # Score distribution chart
        scores = [r.get('final_score', 0) for r in rankings]
        titles = [r.get('title', f'Participant {i+1}') for i, r in enumerate(rankings)]
        types = [r.get('type', 'Unknown') for r in rankings]
        
        # Create score distribution chart
        fig = px.bar(
            x=titles,
            y=scores,
            color=types,
            title="Final Scores by Participant",
            labels={'x': 'Participants', 'y': 'Final Score', 'color': 'Content Type'}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance by content type
        if len(set(types)) > 1:
            st.markdown("#### 🎯 Performance by Content Type")
            
            type_performance = {}
            for ranking in rankings:
                content_type = ranking.get('type', 'Unknown')
                score = ranking.get('final_score', 0)
                
                if content_type not in type_performance:
                    type_performance[content_type] = []
                type_performance[content_type].append(score)
            
            # Calculate statistics by type
            type_stats = []
            for content_type, scores in type_performance.items():
                type_stats.append({
                    'Content Type': content_type,
                    'Count': len(scores),
                    'Average Score': np.mean(scores),
                    'Best Score': max(scores),
                    'Worst Score': min(scores),
                    'Score Range': max(scores) - min(scores)
                })
            
            type_stats_df = pd.DataFrame(type_stats)
            st.dataframe(type_stats_df, use_container_width=True)
            
            # Box plot of scores by type
            fig = go.Figure()
            for content_type, scores in type_performance.items():
                fig.add_trace(go.Box(
                    y=scores,
                    name=content_type,
                    boxpoints='all',
                    jitter=0.3,
                    pointpos=-1.8
                ))
            
            fig.update_layout(
                title="Score Distribution by Content Type",
                yaxis_title="Final Score",
                xaxis_title="Content Type"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_tournament_match_details(self, matches: List[Dict], participants: List[Dict]):
        """Render detailed match information."""
        st.markdown("#### 🔍 Match Details")
        
        if not matches:
            st.warning("No match data available.")
            return
        
        # Match summary
        total_matches = len(matches)
        completed_matches = len([m for m in matches if m.get('completed', False)])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Matches", total_matches)
        with col2:
            st.metric("Completed Matches", completed_matches)
        
        # Match results table
        if matches:
            match_data = []
            for i, match in enumerate(matches):
                match_data.append({
                    "Match #": i + 1,
                    "Participant 1": match.get('participant1_title', 'Unknown'),
                    "Participant 2": match.get('participant2_title', 'Unknown'),
                    "Winner": match.get('winner_title', 'TBD'),
                    "Score": f"{match.get('score1', 0):.3f} - {match.get('score2', 0):.3f}",
                    "Status": "✅ Complete" if match.get('completed', False) else "⏳ Pending"
                })
            
            matches_df = pd.DataFrame(match_data)
            st.dataframe(matches_df, use_container_width=True)
        
        # Match visualization
        if completed_matches > 0:
            st.markdown("#### 🏆 Match Results Visualization")
            
            # Create a simple bracket visualization (for small tournaments)
            if total_matches <= 15:  # Only for small tournaments
                self._render_simple_bracket(matches)
    
    def _render_simple_bracket(self, matches: List[Dict]):
        """Render a simple bracket visualization."""
        st.markdown("**Tournament Bracket:**")
        
        # Group matches by round (simple heuristic)
        rounds = {}
        for i, match in enumerate(matches):
            round_num = 1  # Simplified - would need more complex logic for real brackets
            if round_num not in rounds:
                rounds[round_num] = []
            rounds[round_num].append(match)
        
        # Display matches by round
        for round_num, round_matches in rounds.items():
            st.markdown(f"**Round {round_num}:**")
            for match in round_matches:
                p1 = match.get('participant1_title', 'Unknown')
                p2 = match.get('participant2_title', 'Unknown')
                winner = match.get('winner_title', 'TBD')
                
                if winner != 'TBD':
                    if winner == p1:
                        st.write(f"🏆 **{p1}** vs {p2}")
                    else:
                        st.write(f"{p1} vs **{p2}** 🏆")
                else:
                    st.write(f"{p1} vs {p2} (Pending)")
    
    def _render_reader_panel_overview(self, panel_results: List[Dict]):
        """Render reader panel overview."""
        st.markdown("#### 👥 Reader Panel Overview")
        
        if not panel_results:
            st.warning("No panel results available.")
            return
        
        # Panel statistics
        total_evaluations = sum(len(result.get('results', {}).get('individual_scores', [])) for result in panel_results)
        total_objects = len(panel_results)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Objects Evaluated", total_objects)
        
        with col2:
            st.metric("Total Evaluations", total_evaluations)
        
        with col3:
            avg_evaluations = total_evaluations / total_objects if total_objects > 0 else 0
            st.metric("Avg Evaluations/Object", f"{avg_evaluations:.1f}")
        
        # Top rated content
        st.markdown("#### ⭐ Top Rated Content")
        
        # Calculate average scores
        scored_objects = []
        for result in panel_results:
            obj_title = result.get('object_title', 'Unknown')
            results_data = result.get('results', {})
            
            if 'overall_score' in results_data:
                scored_objects.append({
                    'title': obj_title,
                    'score': results_data['overall_score'],
                    'type': results_data.get('content_type', 'Unknown')
                })
        
        if scored_objects:
            # Sort by score
            scored_objects.sort(key=lambda x: x['score'], reverse=True)
            
            # Display top 5
            for i, obj in enumerate(scored_objects[:5]):
                rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
                st.write(f"{rank_emoji} **{obj['title']}** - {obj['score']:.2f}/5.0 ({obj['type']})")
    
    def _render_reader_panel_scores(self, panel_results: List[Dict]):
        """Render detailed score analysis."""
        st.markdown("#### 📊 Evaluation Scores")
        
        if not panel_results:
            st.warning("No panel results available.")
            return
        
        # Collect all scores
        all_scores = []
        for result in panel_results:
            obj_title = result.get('object_title', 'Unknown')
            results_data = result.get('results', {})
            
            if 'individual_scores' in results_data:
                for score_data in results_data['individual_scores']:
                    all_scores.append({
                        'Object': obj_title,
                        'Reader': score_data.get('reader_id', 'Unknown'),
                        'Overall Score': score_data.get('overall_score', 0),
                        'Market Appeal': score_data.get('market_appeal', 0),
                        'Emotional Engagement': score_data.get('emotional_engagement', 0),
                        'Genre Fit': score_data.get('genre_fit', 0)
                    })
        
        if all_scores:
            scores_df = pd.DataFrame(all_scores)
            
            # Score distribution
            fig = px.histogram(
                scores_df,
                x='Overall Score',
                nbins=20,
                title="Distribution of Overall Scores",
                labels={'count': 'Number of Evaluations'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Scores by object
            fig = px.box(
                scores_df,
                x='Object',
                y='Overall Score',
                title="Score Distribution by Object"
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Criteria comparison
            criteria_cols = ['Market Appeal', 'Emotional Engagement', 'Genre Fit']
            if all(col in scores_df.columns for col in criteria_cols):
                criteria_means = scores_df[criteria_cols].mean()
                
                fig = px.bar(
                    x=criteria_cols,
                    y=criteria_means.values,
                    title="Average Scores by Evaluation Criteria"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_demographic_analysis(self, panel_results: List[Dict]):
        """Render demographic analysis of reader panel."""
        st.markdown("#### 🎯 Demographic Analysis")
        
        # This would require demographic data from the reader panel
        # For now, show placeholder
        st.info("Demographic analysis would show how different reader segments rated the content.")
        
        # Example of what this could show:
        st.markdown("""
        **Potential Demographic Insights:**
        - Age group preferences
        - Gender-based rating differences
        - Reading level impact on scores
        - Genre familiarity effects
        """)
    
    def _render_series_overview(self, series_data: Dict[str, Any]):
        """Render series generation overview."""
        st.markdown("#### 📚 Series Overview")
        
        series_entries = series_data.get('series_entries', [])
        base_concept = series_data.get('base_concept', {})
        
        if not series_entries:
            st.warning("No series entries available.")
            return
        
        # Series statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Books Generated", len(series_entries))
        
        with col2:
            total_words = sum(entry.get('word_count', 0) for entry in series_entries)
            st.metric("Total Words", f"{total_words:,}")
        
        with col3:
            avg_words = total_words / len(series_entries) if series_entries else 0
            st.metric("Avg Words/Book", f"{avg_words:.0f}")
        
        # Series entries table
        st.markdown("#### 📖 Generated Books")
        
        entries_data = []
        for i, entry in enumerate(series_entries):
            entries_data.append({
                "Book #": i + 1,
                "Title": entry.get('title', f'Book {i+1}'),
                "Genre": entry.get('genre', 'Unknown'),
                "Word Count": entry.get('word_count', 0),
                "Consistency Score": f"{entry.get('consistency_score', 0):.2f}"
            })
        
        entries_df = pd.DataFrame(entries_data)
        st.dataframe(entries_df, use_container_width=True)
    
    def _render_consistency_analysis(self, series_data: Dict[str, Any]):
        """Render consistency analysis for series."""
        st.markdown("#### 🔗 Consistency Analysis")
        
        series_entries = series_data.get('series_entries', [])
        
        if not series_entries:
            st.warning("No series entries available for consistency analysis.")
            return
        
        # Extract consistency scores
        consistency_scores = []
        for i, entry in enumerate(series_entries):
            consistency_scores.append({
                'Book': f"Book {i+1}",
                'Title': entry.get('title', f'Book {i+1}'),
                'Overall Consistency': entry.get('consistency_score', 0),
                'Setting Consistency': entry.get('setting_consistency', 0),
                'Tone Consistency': entry.get('tone_consistency', 0),
                'Theme Consistency': entry.get('theme_consistency', 0)
            })
        
        if consistency_scores:
            consistency_df = pd.DataFrame(consistency_scores)
            
            # Overall consistency chart
            fig = px.bar(
                consistency_df,
                x='Title',
                y='Overall Consistency',
                title="Overall Consistency Scores"
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed consistency breakdown
            consistency_categories = ['Setting Consistency', 'Tone Consistency', 'Theme Consistency']
            if all(col in consistency_df.columns for col in consistency_categories):
                fig = go.Figure()
                
                for category in consistency_categories:
                    fig.add_trace(go.Scatter(
                        x=consistency_df['Title'],
                        y=consistency_df[category],
                        mode='lines+markers',
                        name=category
                    ))
                
                fig.update_layout(
                    title="Consistency Breakdown by Category",
                    xaxis_title="Books",
                    yaxis_title="Consistency Score",
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_progression_tracking(self, series_data: Dict[str, Any]):
        """Render progression tracking for series."""
        st.markdown("#### 📈 Series Progression")
        
        # This would show how the series develops over time
        st.info("Progression tracking would show how themes, characters, and plot elements develop across the series.")
        
        # Placeholder for progression metrics
        st.markdown("""
        **Potential Progression Metrics:**
        - Character development arcs
        - Plot complexity evolution
        - Theme exploration depth
        - World-building expansion
        """)
    
    def _render_insights_panel(self, insights: Dict[str, Any]):
        """Render insights and recommendations panel."""
        st.markdown("#### 💡 Key Insights")
        
        # Performance insights
        if 'performance' in insights:
            st.markdown("**Performance Insights:**")
            for insight in insights['performance']:
                st.write(f"• {insight}")
        
        # Content insights
        if 'content' in insights:
            st.markdown("**Content Insights:**")
            for insight in insights['content']:
                st.write(f"• {insight}")
        
        # Recommendations
        if 'recommendations' in insights:
            st.markdown("**Recommendations:**")
            for rec in insights['recommendations']:
                st.write(f"💡 {rec}")
        
        # Mixed-type insights
        if 'mixed_type' in insights:
            st.markdown("**Mixed Content Type Analysis:**")
            for insight in insights['mixed_type']:
                st.write(f"🔄 {insight}")
    
    def _generate_tournament_insights(self, participants: List[Dict], matches: List[Dict], rankings: List[Dict]) -> Dict[str, Any]:
        """Generate insights for tournament results."""
        insights = {
            'performance': [],
            'content': [],
            'recommendations': [],
            'mixed_type': []
        }
        
        if not rankings:
            return insights
        
        # Performance insights
        scores = [r.get('final_score', 0) for r in rankings]
        if scores:
            avg_score = np.mean(scores)
            score_std = np.std(scores)
            
            insights['performance'].append(f"Average tournament score: {avg_score:.3f}")
            insights['performance'].append(f"Score variation: {score_std:.3f} (higher = more competitive)")
            
            if score_std < 0.1:
                insights['performance'].append("Very close competition - small differences determined winners")
            elif score_std > 0.3:
                insights['performance'].append("Wide performance gap - clear quality differences")
        
        # Content type analysis
        type_counts = {}
        type_performance = {}
        
        for ranking in rankings:
            content_type = ranking.get('type', 'Unknown')
            score = ranking.get('final_score', 0)
            
            type_counts[content_type] = type_counts.get(content_type, 0) + 1
            if content_type not in type_performance:
                type_performance[content_type] = []
            type_performance[content_type].append(score)
        
        if len(type_counts) > 1:
            # Mixed type insights
            insights['mixed_type'].append(f"Tournament included {len(type_counts)} different content types")
            
            # Find best performing type
            type_averages = {t: np.mean(scores) for t, scores in type_performance.items()}
            best_type = max(type_averages.items(), key=lambda x: x[1])
            worst_type = min(type_averages.items(), key=lambda x: x[1])
            
            insights['mixed_type'].append(f"Best performing type: {best_type[0]} (avg: {best_type[1]:.3f})")
            insights['mixed_type'].append(f"Lowest performing type: {worst_type[0]} (avg: {worst_type[1]:.3f})")
            
            # Type distribution insights
            dominant_type = max(type_counts.items(), key=lambda x: x[1])
            if dominant_type[1] > len(participants) * 0.6:
                insights['content'].append(f"Tournament dominated by {dominant_type[0]} content ({dominant_type[1]} entries)")
        
        # Recommendations
        if len(participants) < 4:
            insights['recommendations'].append("Consider adding more participants for more meaningful results")
        
        if scores and max(scores) - min(scores) < 0.1:
            insights['recommendations'].append("Very close scores suggest refining evaluation criteria for better differentiation")
        
        return insights
    
    def _generate_reader_panel_insights(self, panel_results: List[Dict]) -> Dict[str, Any]:
        """Generate insights for reader panel results."""
        insights = {
            'performance': [],
            'content': [],
            'recommendations': [],
            'mixed_type': []
        }
        
        if not panel_results:
            return insights
        
        # Calculate overall statistics
        all_scores = []
        for result in panel_results:
            results_data = result.get('results', {})
            if 'overall_score' in results_data:
                all_scores.append(results_data['overall_score'])
        
        if all_scores:
            avg_score = np.mean(all_scores)
            score_std = np.std(all_scores)
            
            insights['performance'].append(f"Average reader score: {avg_score:.2f}/5.0")
            insights['performance'].append(f"Score consistency: {score_std:.2f} (lower = more agreement)")
            
            if avg_score > 4.0:
                insights['content'].append("Content received very positive reader feedback")
            elif avg_score < 2.5:
                insights['content'].append("Content may need significant improvement for market appeal")
        
        # Recommendations
        if len(panel_results) < 3:
            insights['recommendations'].append("Consider evaluating more content for better insights")
        
        return insights
    
    def _generate_series_insights(self, series_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights for series generation results."""
        insights = {
            'performance': [],
            'content': [],
            'recommendations': [],
            'mixed_type': []
        }
        
        series_entries = series_data.get('series_entries', [])
        
        if not series_entries:
            return insights
        
        # Consistency analysis
        consistency_scores = [entry.get('consistency_score', 0) for entry in series_entries]
        if consistency_scores:
            avg_consistency = np.mean(consistency_scores)
            consistency_std = np.std(consistency_scores)
            
            insights['performance'].append(f"Average consistency score: {avg_consistency:.2f}")
            insights['performance'].append(f"Consistency variation: {consistency_std:.2f}")
            
            if avg_consistency > 0.8:
                insights['content'].append("Series maintains strong consistency across books")
            elif avg_consistency < 0.5:
                insights['content'].append("Series may be too varied - consider strengthening common elements")
        
        # Series length insights
        if len(series_entries) < 3:
            insights['recommendations'].append("Consider generating more books for a fuller series")
        elif len(series_entries) > 7:
            insights['recommendations'].append("Large series - ensure each book adds unique value")
        
        return insights