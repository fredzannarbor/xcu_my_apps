"""
Synthetic reader feedback system for evaluating book ideas.
Provides multi-perspective analysis and feedback synthesis.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
from pathlib import Path

from .book_idea import BookIdea
from ...core.llm_integration import LLMCaller

logger = logging.getLogger(__name__)


@dataclass
class ReaderFeedback:
    """Feedback from a synthetic reader persona."""
    reader_persona: str
    idea_id: str
    market_appeal_score: float  # 0-10
    genre_fit_score: float      # 0-10
    audience_alignment_score: float  # 0-10
    detailed_feedback: str
    recommendations: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    overall_rating: float = 0.0  # 0-10
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Calculate overall rating if not provided."""
        if self.overall_rating == 0.0:
            self.overall_rating = (
                self.market_appeal_score + 
                self.genre_fit_score + 
                self.audience_alignment_score
            ) / 3.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'reader_persona': self.reader_persona,
            'idea_id': self.idea_id,
            'market_appeal_score': self.market_appeal_score,
            'genre_fit_score': self.genre_fit_score,
            'audience_alignment_score': self.audience_alignment_score,
            'detailed_feedback': self.detailed_feedback,
            'recommendations': self.recommendations,
            'concerns': self.concerns,
            'overall_rating': self.overall_rating,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReaderFeedback':
        """Create from dictionary format."""
        if 'created_at' in data and isinstance(data['created_at'], str):
            try:
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            except ValueError:
                data['created_at'] = datetime.now()
        
        return cls(**data)


@dataclass
class SynthesizedInsights:
    """Aggregated insights from multiple reader feedback."""
    idea_id: str
    overall_consensus: str
    market_potential: float  # 0-10
    recommended_improvements: List[str] = field(default_factory=list)
    target_audience_refinement: str = ""
    genre_recommendations: List[str] = field(default_factory=list)
    imprint_suggestions: List[str] = field(default_factory=list)
    editing_priorities: List[str] = field(default_factory=list)
    reader_count: int = 0
    confidence_level: float = 0.0  # 0-1
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'idea_id': self.idea_id,
            'overall_consensus': self.overall_consensus,
            'market_potential': self.market_potential,
            'recommended_improvements': self.recommended_improvements,
            'target_audience_refinement': self.target_audience_refinement,
            'genre_recommendations': self.genre_recommendations,
            'imprint_suggestions': self.imprint_suggestions,
            'editing_priorities': self.editing_priorities,
            'reader_count': self.reader_count,
            'confidence_level': self.confidence_level,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }


class SyntheticReaderPersona:
    """Represents a synthetic reader with specific characteristics and preferences."""
    
    def __init__(self, name: str, characteristics: Dict[str, Any]):
        self.name = name
        self.characteristics = characteristics
        self.age_range = characteristics.get('age_range', '25-45')
        self.preferred_genres = characteristics.get('preferred_genres', [])
        self.reading_habits = characteristics.get('reading_habits', {})
        self.demographic = characteristics.get('demographic', {})
        self.personality_traits = characteristics.get('personality_traits', [])

    def get_evaluation_prompt(self, idea: BookIdea) -> str:
        """Generate evaluation prompt from this reader's perspective."""
        return f"""
        You are a synthetic reader named {self.name} with the following characteristics:
        - Age range: {self.age_range}
        - Preferred genres: {', '.join(self.preferred_genres)}
        - Reading habits: {self.reading_habits}
        - Demographic: {self.demographic}
        - Personality traits: {', '.join(self.personality_traits)}
        
        Evaluate this book idea from your perspective as a potential reader:
        
        Title: {idea.title}
        Logline: {idea.logline}
        {f"Description: {idea.description}" if idea.description else ""}
        {f"Genre: {idea.genre}" if idea.genre else ""}
        {f"Target Audience: {idea.target_audience}" if idea.target_audience else ""}
        
        Provide your evaluation in the following JSON format:
        {{
            "market_appeal_score": [0-10 score for how appealing this would be in the market],
            "genre_fit_score": [0-10 score for how well this fits its intended genre],
            "audience_alignment_score": [0-10 score for how well this matches its target audience],
            "detailed_feedback": "[Your detailed thoughts on the book idea]",
            "recommendations": ["List", "of", "specific", "recommendations"],
            "concerns": ["List", "of", "concerns", "or", "issues"]
        }}
        
        Be honest and specific in your evaluation, considering your personal preferences and characteristics.
        """


class SyntheticReaderPanel:
    """Manages synthetic reader evaluation of book ideas."""
    
    def __init__(self, llm_caller: LLMCaller):
        self.llm_caller = llm_caller
        self.reader_personas = self._create_default_personas()
        self.feedback_synthesizer = FeedbackSynthesizer()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _create_default_personas(self) -> List[SyntheticReaderPersona]:
        """Create default set of synthetic reader personas."""
        personas = [
            SyntheticReaderPersona("Literary Lisa", {
                'age_range': '30-50',
                'preferred_genres': ['Literary Fiction', 'Historical Fiction', 'Memoir'],
                'reading_habits': {'books_per_month': 4, 'prefers_character_driven': True},
                'demographic': {'education': 'Graduate degree', 'income': 'Upper middle class'},
                'personality_traits': ['Intellectual', 'Thoughtful', 'Values depth over entertainment']
            }),
            
            SyntheticReaderPersona("Thriller Tom", {
                'age_range': '25-45',
                'preferred_genres': ['Thriller', 'Mystery', 'Crime', 'Suspense'],
                'reading_habits': {'books_per_month': 3, 'prefers_fast_paced': True},
                'demographic': {'education': 'College degree', 'income': 'Middle class'},
                'personality_traits': ['Action-oriented', 'Impatient', 'Loves plot twists']
            }),
            
            SyntheticReaderPersona("Romance Rachel", {
                'age_range': '20-40',
                'preferred_genres': ['Romance', 'Contemporary Fiction', 'Women\'s Fiction'],
                'reading_habits': {'books_per_month': 6, 'prefers_emotional_stories': True},
                'demographic': {'education': 'College degree', 'income': 'Middle class'},
                'personality_traits': ['Emotional', 'Optimistic', 'Values relationships']
            }),
            
            SyntheticReaderPersona("Sci-Fi Sam", {
                'age_range': '25-55',
                'preferred_genres': ['Science Fiction', 'Fantasy', 'Speculative Fiction'],
                'reading_habits': {'books_per_month': 3, 'prefers_world_building': True},
                'demographic': {'education': 'STEM background', 'income': 'Upper middle class'},
                'personality_traits': ['Analytical', 'Curious', 'Enjoys complex concepts']
            }),
            
            SyntheticReaderPersona("Business Bob", {
                'age_range': '30-60',
                'preferred_genres': ['Business', 'Self-Help', 'Biography', 'Non-fiction'],
                'reading_habits': {'books_per_month': 2, 'prefers_practical_advice': True},
                'demographic': {'education': 'MBA', 'income': 'High income'},
                'personality_traits': ['Goal-oriented', 'Practical', 'Values actionable insights']
            }),
            
            SyntheticReaderPersona("Young Adult Yara", {
                'age_range': '16-25',
                'preferred_genres': ['Young Adult', 'Fantasy', 'Contemporary Fiction'],
                'reading_habits': {'books_per_month': 5, 'prefers_diverse_characters': True},
                'demographic': {'education': 'High school/College', 'income': 'Low income'},
                'personality_traits': ['Idealistic', 'Social justice oriented', 'Values representation']
            })
        ]
        
        return personas

    def add_persona(self, persona: SyntheticReaderPersona):
        """Add a custom reader persona."""
        self.reader_personas.append(persona)

    def evaluate_ideas(self, ideas: List[BookIdea],
                      selected_personas: Optional[List[str]] = None,
                      model: str = "gemini/gemini-2.5-flash") -> List[ReaderFeedback]:
        """Evaluate ideas from multiple synthetic reader perspectives."""
        all_feedback = []

        # Select personas to use
        personas_to_use = self.reader_personas
        if selected_personas:
            personas_to_use = [p for p in self.reader_personas if p.name in selected_personas]

        for idea in ideas:
            idea_id = idea.generation_metadata.get('idea_id', str(id(idea)))

            for persona in personas_to_use:
                try:
                    feedback = self._evaluate_single_idea(idea, persona, idea_id, model=model)
                    if feedback:
                        all_feedback.append(feedback)
                        
                except Exception as e:
                    self.logger.error(f"Error evaluating idea {idea.title} with persona {persona.name}: {e}")
                    continue
        
        return all_feedback

    def _evaluate_single_idea(self, idea: BookIdea, persona: SyntheticReaderPersona,
                            idea_id: str, model: str = "gemini/gemini-2.5-flash") -> Optional[ReaderFeedback]:
        """Evaluate a single idea from one persona's perspective."""
        prompt = persona.get_evaluation_prompt(idea)

        try:
            response = self.llm_caller.call_llm(
                prompt=prompt,
                model=model,  # Use provided model parameter
                temperature=0.3  # Lower temperature for more consistent evaluation
            )

            # Handle response - call_llm returns a string, not a dict
            if response:
                content = response.strip() if isinstance(response, str) else str(response)

                # Try to parse JSON response
                try:
                    evaluation_data = json.loads(content)
                    
                    feedback = ReaderFeedback(
                        reader_persona=persona.name,
                        idea_id=idea_id,
                        market_appeal_score=float(evaluation_data.get('market_appeal_score', 5.0)),
                        genre_fit_score=float(evaluation_data.get('genre_fit_score', 5.0)),
                        audience_alignment_score=float(evaluation_data.get('audience_alignment_score', 5.0)),
                        detailed_feedback=evaluation_data.get('detailed_feedback', ''),
                        recommendations=evaluation_data.get('recommendations', []),
                        concerns=evaluation_data.get('concerns', [])
                    )
                    
                    return feedback
                    
                except json.JSONDecodeError:
                    # Fallback: parse text response
                    return self._parse_text_evaluation(content, persona.name, idea_id)
                    
        except Exception as e:
            self.logger.error(f"Error in LLM evaluation for {persona.name}: {e}")
            
        return None

    def _parse_text_evaluation(self, content: str, persona_name: str, idea_id: str) -> ReaderFeedback:
        """Parse text-based evaluation response."""
        # Simple fallback parsing
        lines = content.split('\n')
        
        market_score = 5.0
        genre_score = 5.0
        audience_score = 5.0
        feedback_text = content
        recommendations = []
        concerns = []
        
        # Try to extract scores from text
        for line in lines:
            line = line.strip().lower()
            if 'market' in line and any(char.isdigit() for char in line):
                try:
                    market_score = float([char for char in line if char.isdigit() or char == '.'][0])
                except:
                    pass
        
        return ReaderFeedback(
            reader_persona=persona_name,
            idea_id=idea_id,
            market_appeal_score=market_score,
            genre_fit_score=genre_score,
            audience_alignment_score=audience_score,
            detailed_feedback=feedback_text,
            recommendations=recommendations,
            concerns=concerns
        )

    def synthesize_feedback(self, feedback_list: List[ReaderFeedback]) -> Dict[str, SynthesizedInsights]:
        """Synthesize feedback for each idea."""
        return self.feedback_synthesizer.synthesize_feedback(feedback_list)

    def save_feedback(self, feedback_list: List[ReaderFeedback], file_path: str):
        """Save reader feedback to JSON file."""
        data = {
            'feedback': [feedback.to_dict() for feedback in feedback_list],
            'saved_at': datetime.now().isoformat(),
            'total_feedback_count': len(feedback_list)
        }
        
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)


class FeedbackSynthesizer:
    """Synthesizes multiple reader feedback into actionable insights."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def synthesize_feedback(self, feedback_list: List[ReaderFeedback]) -> Dict[str, SynthesizedInsights]:
        """Synthesize feedback grouped by idea ID."""
        # Group feedback by idea
        feedback_by_idea = {}
        for feedback in feedback_list:
            if feedback.idea_id not in feedback_by_idea:
                feedback_by_idea[feedback.idea_id] = []
            feedback_by_idea[feedback.idea_id].append(feedback)
        
        # Synthesize insights for each idea
        synthesized_insights = {}
        for idea_id, idea_feedback in feedback_by_idea.items():
            insights = self._synthesize_single_idea(idea_id, idea_feedback)
            synthesized_insights[idea_id] = insights
        
        return synthesized_insights

    def _synthesize_single_idea(self, idea_id: str, feedback_list: List[ReaderFeedback]) -> SynthesizedInsights:
        """Synthesize feedback for a single idea."""
        if not feedback_list:
            return SynthesizedInsights(
                idea_id=idea_id,
                overall_consensus="No feedback available",
                market_potential=0.0
            )
        
        # Calculate average scores
        market_scores = [f.market_appeal_score for f in feedback_list]
        genre_scores = [f.genre_fit_score for f in feedback_list]
        audience_scores = [f.audience_alignment_score for f in feedback_list]
        overall_scores = [f.overall_rating for f in feedback_list]
        
        avg_market = sum(market_scores) / len(market_scores)
        avg_genre = sum(genre_scores) / len(genre_scores)
        avg_audience = sum(audience_scores) / len(audience_scores)
        avg_overall = sum(overall_scores) / len(overall_scores)
        
        # Aggregate recommendations and concerns
        all_recommendations = []
        all_concerns = []
        
        for feedback in feedback_list:
            all_recommendations.extend(feedback.recommendations)
            all_concerns.extend(feedback.concerns)
        
        # Remove duplicates while preserving order
        unique_recommendations = list(dict.fromkeys(all_recommendations))
        unique_concerns = list(dict.fromkeys(all_concerns))
        
        # Determine consensus
        consensus = self._determine_consensus(avg_overall, feedback_list)
        
        # Calculate confidence based on agreement
        confidence = self._calculate_confidence(overall_scores)
        
        # Generate improvement suggestions
        improvements = self._generate_improvements(unique_recommendations, unique_concerns)
        
        return SynthesizedInsights(
            idea_id=idea_id,
            overall_consensus=consensus,
            market_potential=avg_overall,
            recommended_improvements=improvements,
            target_audience_refinement=self._suggest_audience_refinement(feedback_list),
            genre_recommendations=self._suggest_genre_refinements(feedback_list),
            imprint_suggestions=self._suggest_imprints(avg_market, avg_genre, avg_audience),
            editing_priorities=self._prioritize_editing_needs(unique_concerns),
            reader_count=len(feedback_list),
            confidence_level=confidence
        )

    def _determine_consensus(self, avg_score: float, feedback_list: List[ReaderFeedback]) -> str:
        """Determine overall consensus from feedback."""
        if avg_score >= 8.0:
            return "Strong positive consensus - highly recommended for publication"
        elif avg_score >= 6.5:
            return "Positive consensus - recommended with minor improvements"
        elif avg_score >= 5.0:
            return "Mixed consensus - needs significant improvements before publication"
        elif avg_score >= 3.0:
            return "Negative consensus - major revisions required"
        else:
            return "Strong negative consensus - not recommended for publication"

    def _calculate_confidence(self, scores: List[float]) -> float:
        """Calculate confidence level based on score agreement."""
        if len(scores) <= 1:
            return 0.5
        
        # Calculate standard deviation
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        std_dev = variance ** 0.5
        
        # Convert to confidence (lower std_dev = higher confidence)
        max_std_dev = 3.0  # Maximum expected standard deviation
        confidence = max(0.0, min(1.0, 1.0 - (std_dev / max_std_dev)))
        
        return confidence

    def _generate_improvements(self, recommendations: List[str], concerns: List[str]) -> List[str]:
        """Generate prioritized improvement suggestions."""
        improvements = []
        
        # Add top recommendations
        improvements.extend(recommendations[:5])  # Top 5 recommendations
        
        # Convert concerns to improvement suggestions
        for concern in concerns[:3]:  # Top 3 concerns
            if concern.lower().startswith('the'):
                improvement = f"Address concern: {concern}"
            else:
                improvement = f"Improve: {concern}"
            improvements.append(improvement)
        
        return improvements

    def _suggest_audience_refinement(self, feedback_list: List[ReaderFeedback]) -> str:
        """Suggest target audience refinements."""
        # Analyze which personas gave highest scores
        high_scoring_personas = [f.reader_persona for f in feedback_list if f.overall_rating >= 7.0]
        
        if high_scoring_personas:
            return f"Consider targeting readers similar to: {', '.join(set(high_scoring_personas))}"
        else:
            return "Consider broadening or refining target audience based on feedback"

    def _suggest_genre_refinements(self, feedback_list: List[ReaderFeedback]) -> List[str]:
        """Suggest genre refinements."""
        genre_scores = [(f.reader_persona, f.genre_fit_score) for f in feedback_list]
        high_genre_fit = [persona for persona, score in genre_scores if score >= 7.0]
        
        suggestions = []
        if high_genre_fit:
            suggestions.append(f"Strong genre fit with {', '.join(high_genre_fit)} readers")
        else:
            suggestions.append("Consider genre repositioning or clarification")
        
        return suggestions

    def _suggest_imprints(self, market_score: float, genre_score: float, audience_score: float) -> List[str]:
        """Suggest suitable imprints based on scores."""
        suggestions = []
        
        if market_score >= 7.0 and genre_score >= 7.0:
            suggestions.append("Suitable for mainstream imprint")
        elif genre_score >= 8.0:
            suggestions.append("Consider genre-specific imprint")
        elif audience_score >= 8.0:
            suggestions.append("Consider audience-specific imprint")
        else:
            suggestions.append("May need specialized or niche imprint")
        
        return suggestions

    def _prioritize_editing_needs(self, concerns: List[str]) -> List[str]:
        """Prioritize editing needs based on concerns."""
        priorities = []
        
        # Common editing priorities based on typical concerns
        priority_keywords = {
            'plot': 'Plot development and structure',
            'character': 'Character development and depth',
            'pacing': 'Pacing and narrative flow',
            'dialogue': 'Dialogue improvement',
            'setting': 'Setting and world-building',
            'theme': 'Theme clarification and development'
        }
        
        for keyword, priority in priority_keywords.items():
            if any(keyword.lower() in concern.lower() for concern in concerns):
                priorities.append(priority)
        
        # Add generic priorities if none found
        if not priorities:
            priorities.extend(['Overall narrative structure', 'Character development', 'Market positioning'])
        
        return priorities[:5]  # Top 5 priorities