"""
Feedback-driven improvement system for optimizing ideation based on synthetic reader insights.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict, Counter
import statistics

from .book_idea import BookIdea
from .synthetic_reader import ReaderFeedback, SynthesizedInsights
from ...core.llm_integration import LLMCaller

logger = logging.getLogger(__name__)


class FeedbackAnalyzer:
    """Analyzes patterns in synthetic reader feedback to identify improvement opportunities."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def analyze_feedback_patterns(self, feedback_list: List[ReaderFeedback], 
                                time_window_days: int = 30) -> Dict[str, Any]:
        """Analyze patterns in reader feedback over a time window."""
        
        # Filter feedback by time window
        cutoff_date = datetime.now() - timedelta(days=time_window_days)
        recent_feedback = [
            fb for fb in feedback_list 
            if fb.created_at >= cutoff_date
        ]
        
        if not recent_feedback:
            return {'error': 'No recent feedback available'}
        
        patterns = {
            'total_feedback_count': len(recent_feedback),
            'average_scores': self._calculate_average_scores(recent_feedback),
            'common_concerns': self._identify_common_concerns(recent_feedback),
            'frequent_recommendations': self._identify_frequent_recommendations(recent_feedback),
            'persona_preferences': self._analyze_persona_preferences(recent_feedback),
            'genre_performance': self._analyze_genre_performance(recent_feedback),
            'improvement_trends': self._analyze_improvement_trends(recent_feedback),
            'quality_indicators': self._identify_quality_indicators(recent_feedback)
        }
        
        return patterns

    def _calculate_average_scores(self, feedback_list: List[ReaderFeedback]) -> Dict[str, float]:
        """Calculate average scores across all feedback."""
        if not feedback_list:
            return {}
        
        market_scores = [fb.market_appeal_score for fb in feedback_list]
        genre_scores = [fb.genre_fit_score for fb in feedback_list]
        audience_scores = [fb.audience_alignment_score for fb in feedback_list]
        overall_scores = [fb.overall_rating for fb in feedback_list]
        
        return {
            'market_appeal': statistics.mean(market_scores),
            'genre_fit': statistics.mean(genre_scores),
            'audience_alignment': statistics.mean(audience_scores),
            'overall_rating': statistics.mean(overall_scores),
            'score_variance': statistics.variance(overall_scores) if len(overall_scores) > 1 else 0
        }

    def _identify_common_concerns(self, feedback_list: List[ReaderFeedback]) -> List[Dict[str, Any]]:
        """Identify most common concerns across feedback."""
        all_concerns = []
        for fb in feedback_list:
            all_concerns.extend(fb.concerns)
        
        concern_counts = Counter(all_concerns)
        
        return [
            {
                'concern': concern,
                'frequency': count,
                'percentage': (count / len(feedback_list)) * 100
            }
            for concern, count in concern_counts.most_common(10)
        ]

    def _identify_frequent_recommendations(self, feedback_list: List[ReaderFeedback]) -> List[Dict[str, Any]]:
        """Identify most frequent recommendations."""
        all_recommendations = []
        for fb in feedback_list:
            all_recommendations.extend(fb.recommendations)
        
        rec_counts = Counter(all_recommendations)
        
        return [
            {
                'recommendation': rec,
                'frequency': count,
                'percentage': (count / len(feedback_list)) * 100
            }
            for rec, count in rec_counts.most_common(10)
        ]

    def _analyze_persona_preferences(self, feedback_list: List[ReaderFeedback]) -> Dict[str, Dict[str, float]]:
        """Analyze preferences by reader persona."""
        persona_scores = defaultdict(list)
        
        for fb in feedback_list:
            persona_scores[fb.reader_persona].append(fb.overall_rating)
        
        return {
            persona: {
                'average_rating': statistics.mean(scores),
                'feedback_count': len(scores),
                'rating_variance': statistics.variance(scores) if len(scores) > 1 else 0
            }
            for persona, scores in persona_scores.items()
        }

    def _analyze_genre_performance(self, feedback_list: List[ReaderFeedback]) -> Dict[str, Any]:
        """Analyze performance by genre (would need genre info from ideas)."""
        # This would require linking feedback to ideas with genre information
        # For now, return placeholder
        return {
            'note': 'Genre performance analysis requires linking feedback to idea genres',
            'implementation_needed': True
        }

    def _analyze_improvement_trends(self, feedback_list: List[ReaderFeedback]) -> Dict[str, Any]:
        """Analyze trends in feedback over time."""
        # Sort feedback by date
        sorted_feedback = sorted(feedback_list, key=lambda x: x.created_at)
        
        if len(sorted_feedback) < 10:
            return {'note': 'Insufficient data for trend analysis'}
        
        # Split into early and recent halves
        mid_point = len(sorted_feedback) // 2
        early_feedback = sorted_feedback[:mid_point]
        recent_feedback = sorted_feedback[mid_point:]
        
        early_avg = statistics.mean([fb.overall_rating for fb in early_feedback])
        recent_avg = statistics.mean([fb.overall_rating for fb in recent_feedback])
        
        return {
            'early_period_average': early_avg,
            'recent_period_average': recent_avg,
            'improvement_trend': recent_avg - early_avg,
            'trend_direction': 'improving' if recent_avg > early_avg else 'declining' if recent_avg < early_avg else 'stable'
        }

    def _identify_quality_indicators(self, feedback_list: List[ReaderFeedback]) -> Dict[str, Any]:
        """Identify indicators of high-quality ideas."""
        # Sort feedback by overall rating
        sorted_by_rating = sorted(feedback_list, key=lambda x: x.overall_rating, reverse=True)
        
        # Top 20% of feedback
        top_20_percent = sorted_by_rating[:max(1, len(sorted_by_rating) // 5)]
        
        # Analyze characteristics of highly-rated ideas
        top_concerns = []
        top_recommendations = []
        
        for fb in top_20_percent:
            top_concerns.extend(fb.concerns)
            top_recommendations.extend(fb.recommendations)
        
        return {
            'high_rating_threshold': min([fb.overall_rating for fb in top_20_percent]) if top_20_percent else 0,
            'common_positive_traits': Counter(top_recommendations).most_common(5),
            'rare_concerns_in_top_ideas': Counter(top_concerns).most_common(5)
        }


class PromptOptimizer:
    """Optimizes idea generation prompts based on feedback patterns."""
    
    def __init__(self, llm_caller: LLMCaller):
        self.llm_caller = llm_caller
        self.logger = logging.getLogger(self.__class__.__name__)

    def optimize_prompts_from_feedback(self, feedback_patterns: Dict[str, Any], 
                                     current_prompts: Dict[str, str]) -> Dict[str, str]:
        """Generate optimized prompts based on feedback analysis."""
        
        optimized_prompts = {}
        
        for prompt_type, current_prompt in current_prompts.items():
            try:
                optimized_prompt = self._optimize_single_prompt(
                    current_prompt, feedback_patterns, prompt_type
                )
                optimized_prompts[prompt_type] = optimized_prompt
                
            except Exception as e:
                self.logger.error(f"Error optimizing prompt {prompt_type}: {e}")
                optimized_prompts[prompt_type] = current_prompt  # Fallback to current
        
        return optimized_prompts

    def _optimize_single_prompt(self, current_prompt: str, patterns: Dict[str, Any], 
                              prompt_type: str) -> str:
        """Optimize a single prompt based on feedback patterns."""
        
        optimization_prompt = f"""
        You are an expert prompt engineer specializing in book idea generation.
        
        Current prompt for {prompt_type}:
        {current_prompt}
        
        Based on reader feedback analysis, here are the key insights:
        
        Average Scores:
        - Market Appeal: {patterns.get('average_scores', {}).get('market_appeal', 'N/A')}
        - Genre Fit: {patterns.get('average_scores', {}).get('genre_fit', 'N/A')}
        - Audience Alignment: {patterns.get('average_scores', {}).get('audience_alignment', 'N/A')}
        
        Common Concerns:
        {self._format_concerns(patterns.get('common_concerns', []))}
        
        Frequent Recommendations:
        {self._format_recommendations(patterns.get('frequent_recommendations', []))}
        
        Quality Indicators:
        {patterns.get('quality_indicators', {})}
        
        Please optimize the prompt to address these feedback patterns. Focus on:
        1. Addressing common concerns
        2. Incorporating successful recommendations
        3. Improving areas with low scores
        4. Maintaining what works well
        
        Return only the optimized prompt, no additional explanation.
        """
        
        try:
            response = self.llm_caller.call_llm(
                prompt=optimization_prompt,
                model="mistral",
                temperature=0.3
            )
            
            if response and response.get('content'):
                return response['content'].strip()
            else:
                return current_prompt
                
        except Exception as e:
            self.logger.error(f"Error in LLM prompt optimization: {e}")
            return current_prompt

    def _format_concerns(self, concerns: List[Dict[str, Any]]) -> str:
        """Format concerns for prompt optimization."""
        if not concerns:
            return "No significant concerns identified."
        
        formatted = []
        for concern in concerns[:5]:  # Top 5 concerns
            formatted.append(f"- {concern['concern']} ({concern['frequency']} times, {concern['percentage']:.1f}%)")
        
        return "\n".join(formatted)

    def _format_recommendations(self, recommendations: List[Dict[str, Any]]) -> str:
        """Format recommendations for prompt optimization."""
        if not recommendations:
            return "No frequent recommendations identified."
        
        formatted = []
        for rec in recommendations[:5]:  # Top 5 recommendations
            formatted.append(f"- {rec['recommendation']} ({rec['frequency']} times, {rec['percentage']:.1f}%)")
        
        return "\n".join(formatted)


class EditingWorkflowIntegrator:
    """Integrates reader feedback into editing workflows."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate_editing_guidelines(self, synthesized_insights: Dict[str, SynthesizedInsights]) -> Dict[str, Any]:
        """Generate editing guidelines based on synthesized reader feedback."""
        
        guidelines = {
            'priority_areas': self._identify_priority_editing_areas(synthesized_insights),
            'genre_specific_guidance': self._generate_genre_guidance(synthesized_insights),
            'audience_targeting_advice': self._generate_audience_advice(synthesized_insights),
            'common_improvement_patterns': self._identify_improvement_patterns(synthesized_insights),
            'quality_benchmarks': self._establish_quality_benchmarks(synthesized_insights)
        }
        
        return guidelines

    def _identify_priority_editing_areas(self, insights: Dict[str, SynthesizedInsights]) -> List[Dict[str, Any]]:
        """Identify priority areas for editing focus."""
        all_priorities = []
        
        for insight in insights.values():
            all_priorities.extend(insight.editing_priorities)
        
        priority_counts = Counter(all_priorities)
        
        return [
            {
                'area': area,
                'frequency': count,
                'priority_level': 'high' if count >= len(insights) * 0.5 else 'medium' if count >= len(insights) * 0.25 else 'low'
            }
            for area, count in priority_counts.most_common(10)
        ]

    def _generate_genre_guidance(self, insights: Dict[str, SynthesizedInsights]) -> Dict[str, List[str]]:
        """Generate genre-specific editing guidance."""
        genre_recommendations = defaultdict(list)
        
        for insight in insights.values():
            for genre_rec in insight.genre_recommendations:
                # Extract genre from recommendation (simplified)
                genre_recommendations['general'].append(genre_rec)
        
        return dict(genre_recommendations)

    def _generate_audience_advice(self, insights: Dict[str, SynthesizedInsights]) -> List[str]:
        """Generate audience targeting advice."""
        audience_advice = []
        
        for insight in insights.values():
            if insight.target_audience_refinement:
                audience_advice.append(insight.target_audience_refinement)
        
        return list(set(audience_advice))  # Remove duplicates

    def _identify_improvement_patterns(self, insights: Dict[str, SynthesizedInsights]) -> List[Dict[str, Any]]:
        """Identify common improvement patterns."""
        all_improvements = []
        
        for insight in insights.values():
            all_improvements.extend(insight.recommended_improvements)
        
        improvement_counts = Counter(all_improvements)
        
        return [
            {
                'improvement': improvement,
                'frequency': count,
                'effectiveness_score': count / len(insights)  # Simple effectiveness metric
            }
            for improvement, count in improvement_counts.most_common(15)
        ]

    def _establish_quality_benchmarks(self, insights: Dict[str, SynthesizedInsights]) -> Dict[str, float]:
        """Establish quality benchmarks based on feedback."""
        market_potentials = [insight.market_potential for insight in insights.values()]
        confidence_levels = [insight.confidence_level for insight in insights.values()]
        
        if not market_potentials:
            return {}
        
        return {
            'minimum_market_potential': statistics.quantile(market_potentials, 0.25),
            'target_market_potential': statistics.quantile(market_potentials, 0.75),
            'excellent_market_potential': statistics.quantile(market_potentials, 0.9),
            'minimum_confidence_level': statistics.quantile(confidence_levels, 0.25) if confidence_levels else 0.5,
            'average_market_potential': statistics.mean(market_potentials),
            'market_potential_variance': statistics.variance(market_potentials) if len(market_potentials) > 1 else 0
        }


class ImprintStrategyRefiner:
    """Refines imprint strategies based on feedback patterns."""
    
    def __init__(self, llm_caller: LLMCaller):
        self.llm_caller = llm_caller
        self.logger = logging.getLogger(self.__class__.__name__)

    def analyze_imprint_performance(self, feedback_by_imprint: Dict[str, List[ReaderFeedback]]) -> Dict[str, Any]:
        """Analyze performance patterns by imprint."""
        
        imprint_analysis = {}
        
        for imprint, feedback_list in feedback_by_imprint.items():
            if not feedback_list:
                continue
            
            analyzer = FeedbackAnalyzer()
            patterns = analyzer.analyze_feedback_patterns(feedback_list)
            
            imprint_analysis[imprint] = {
                'performance_summary': patterns,
                'strengths': self._identify_imprint_strengths(patterns),
                'weaknesses': self._identify_imprint_weaknesses(patterns),
                'optimization_opportunities': self._identify_optimization_opportunities(patterns),
                'recommended_adjustments': self._recommend_strategy_adjustments(patterns)
            }
        
        return imprint_analysis

    def _identify_imprint_strengths(self, patterns: Dict[str, Any]) -> List[str]:
        """Identify strengths of an imprint based on feedback patterns."""
        strengths = []
        
        avg_scores = patterns.get('average_scores', {})
        
        if avg_scores.get('market_appeal', 0) >= 7.0:
            strengths.append("Strong market appeal")
        
        if avg_scores.get('genre_fit', 0) >= 7.5:
            strengths.append("Excellent genre alignment")
        
        if avg_scores.get('audience_alignment', 0) >= 7.0:
            strengths.append("Good audience targeting")
        
        if avg_scores.get('score_variance', 1.0) < 0.5:
            strengths.append("Consistent quality")
        
        return strengths

    def _identify_imprint_weaknesses(self, patterns: Dict[str, Any]) -> List[str]:
        """Identify weaknesses of an imprint."""
        weaknesses = []
        
        avg_scores = patterns.get('average_scores', {})
        common_concerns = patterns.get('common_concerns', [])
        
        if avg_scores.get('market_appeal', 10) < 5.0:
            weaknesses.append("Low market appeal")
        
        if avg_scores.get('genre_fit', 10) < 5.0:
            weaknesses.append("Poor genre fit")
        
        if avg_scores.get('audience_alignment', 10) < 5.0:
            weaknesses.append("Weak audience alignment")
        
        # Check for frequent concerns
        for concern in common_concerns[:3]:
            if concern['percentage'] > 50:
                weaknesses.append(f"Frequent concern: {concern['concern']}")
        
        return weaknesses

    def _identify_optimization_opportunities(self, patterns: Dict[str, Any]) -> List[str]:
        """Identify optimization opportunities."""
        opportunities = []
        
        frequent_recs = patterns.get('frequent_recommendations', [])
        
        for rec in frequent_recs[:5]:
            if rec['percentage'] > 30:
                opportunities.append(f"Implement: {rec['recommendation']}")
        
        improvement_trends = patterns.get('improvement_trends', {})
        if improvement_trends.get('trend_direction') == 'declining':
            opportunities.append("Address declining quality trend")
        
        return opportunities

    def _recommend_strategy_adjustments(self, patterns: Dict[str, Any]) -> List[str]:
        """Recommend strategic adjustments for the imprint."""
        adjustments = []
        
        avg_scores = patterns.get('average_scores', {})
        persona_prefs = patterns.get('persona_preferences', {})
        
        # Find best-performing personas
        best_personas = sorted(
            persona_prefs.items(),
            key=lambda x: x[1].get('average_rating', 0),
            reverse=True
        )[:3]
        
        if best_personas:
            top_persona = best_personas[0][0]
            adjustments.append(f"Focus more on {top_persona} reader preferences")
        
        # Score-based adjustments
        if avg_scores.get('market_appeal', 0) < avg_scores.get('genre_fit', 0):
            adjustments.append("Improve market positioning while maintaining genre strength")
        
        if avg_scores.get('audience_alignment', 0) < 6.0:
            adjustments.append("Refine target audience definition and alignment")
        
        return adjustments

    def generate_imprint_refinement_report(self, imprint_analysis: Dict[str, Any]) -> str:
        """Generate a comprehensive imprint refinement report."""
        
        report_prompt = f"""
        Generate a comprehensive imprint strategy refinement report based on this analysis:
        
        {json.dumps(imprint_analysis, indent=2)}
        
        The report should include:
        1. Executive Summary
        2. Performance Analysis by Imprint
        3. Key Findings and Insights
        4. Strategic Recommendations
        5. Implementation Priorities
        6. Success Metrics
        
        Format as a professional business report.
        """
        
        try:
            response = self.llm_caller.call_llm(
                prompt=report_prompt,
                model="mistral",
                temperature=0.3
            )
            
            if response and response.get('content'):
                return response['content']
            else:
                return "Error generating report"
                
        except Exception as e:
            self.logger.error(f"Error generating refinement report: {e}")
            return f"Error generating report: {str(e)}"


class FeedbackDrivenOptimizer:
    """Main orchestrator for feedback-driven improvements."""
    
    def __init__(self, llm_caller: LLMCaller):
        self.llm_caller = llm_caller
        self.feedback_analyzer = FeedbackAnalyzer()
        self.prompt_optimizer = PromptOptimizer(llm_caller)
        self.editing_integrator = EditingWorkflowIntegrator()
        self.imprint_refiner = ImprintStrategyRefiner(llm_caller)
        self.logger = logging.getLogger(self.__class__.__name__)

    def run_comprehensive_optimization(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive optimization based on all available feedback."""
        
        optimization_results = {
            'timestamp': datetime.now().isoformat(),
            'feedback_analysis': {},
            'prompt_optimizations': {},
            'editing_guidelines': {},
            'imprint_refinements': {},
            'success_metrics': {}
        }
        
        try:
            # Analyze feedback patterns
            all_feedback = feedback_data.get('all_feedback', [])
            if all_feedback:
                patterns = self.feedback_analyzer.analyze_feedback_patterns(all_feedback)
                optimization_results['feedback_analysis'] = patterns
                
                # Optimize prompts
                current_prompts = feedback_data.get('current_prompts', {})
                if current_prompts:
                    optimized_prompts = self.prompt_optimizer.optimize_prompts_from_feedback(
                        patterns, current_prompts
                    )
                    optimization_results['prompt_optimizations'] = optimized_prompts
            
            # Generate editing guidelines
            synthesized_insights = feedback_data.get('synthesized_insights', {})
            if synthesized_insights:
                editing_guidelines = self.editing_integrator.generate_editing_guidelines(
                    synthesized_insights
                )
                optimization_results['editing_guidelines'] = editing_guidelines
            
            # Refine imprint strategies
            feedback_by_imprint = feedback_data.get('feedback_by_imprint', {})
            if feedback_by_imprint:
                imprint_analysis = self.imprint_refiner.analyze_imprint_performance(
                    feedback_by_imprint
                )
                optimization_results['imprint_refinements'] = imprint_analysis
            
            # Calculate success metrics
            optimization_results['success_metrics'] = self._calculate_success_metrics(
                optimization_results
            )
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive optimization: {e}")
            optimization_results['error'] = str(e)
        
        return optimization_results

    def _calculate_success_metrics(self, optimization_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics to measure optimization success."""
        
        metrics = {
            'optimization_completeness': 0.0,
            'areas_optimized': [],
            'potential_impact_score': 0.0,
            'implementation_complexity': 'medium'
        }
        
        # Calculate completeness
        completed_areas = 0
        total_areas = 4  # feedback_analysis, prompt_optimizations, editing_guidelines, imprint_refinements
        
        if optimization_results.get('feedback_analysis'):
            completed_areas += 1
            metrics['areas_optimized'].append('feedback_analysis')
        
        if optimization_results.get('prompt_optimizations'):
            completed_areas += 1
            metrics['areas_optimized'].append('prompt_optimization')
        
        if optimization_results.get('editing_guidelines'):
            completed_areas += 1
            metrics['areas_optimized'].append('editing_guidelines')
        
        if optimization_results.get('imprint_refinements'):
            completed_areas += 1
            metrics['areas_optimized'].append('imprint_refinements')
        
        metrics['optimization_completeness'] = completed_areas / total_areas
        
        # Estimate potential impact (simplified)
        feedback_analysis = optimization_results.get('feedback_analysis', {})
        avg_scores = feedback_analysis.get('average_scores', {})
        
        if avg_scores:
            current_avg = avg_scores.get('overall_rating', 5.0)
            potential_improvement = max(0, 8.0 - current_avg)  # Assume target of 8.0
            metrics['potential_impact_score'] = potential_improvement / 3.0  # Normalize to 0-1
        
        return metrics

    def save_optimization_results(self, results: Dict[str, Any], output_path: str):
        """Save optimization results to file."""
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.logger.info(f"Optimization results saved to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving optimization results: {e}")

    def load_feedback_data(self, data_sources: Dict[str, str]) -> Dict[str, Any]:
        """Load feedback data from various sources."""
        feedback_data = {
            'all_feedback': [],
            'synthesized_insights': {},
            'feedback_by_imprint': {},
            'current_prompts': {}
        }
        
        try:
            # Load feedback files
            for source_type, file_path in data_sources.items():
                if Path(file_path).exists():
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                    if source_type == 'feedback':
                        feedback_data['all_feedback'].extend(data.get('feedback', []))
                    elif source_type == 'insights':
                        feedback_data['synthesized_insights'].update(data)
                    elif source_type == 'prompts':
                        feedback_data['current_prompts'].update(data)
                        
        except Exception as e:
            self.logger.error(f"Error loading feedback data: {e}")
        
        return feedback_data