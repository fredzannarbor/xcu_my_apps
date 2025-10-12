"""
Agentic AI Persona System - Goal-Driven Behavior and Optimization

This module provides an optional agentic layer for AI personas that enables them to:
- Set and pursue different optimization goals
- Track progress towards objectives
- Adjust posting behavior based on goal achievement
- Handle both aligned (neurochemical) and misaligned (engagement farming) incentives

This system is OFF by default and can be enabled when needed for more dynamic persona behavior.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import random
from pathlib import Path

# Import base classes
from ..modules.ai_personas import AIPersona
from ..modules.generate_social_feed.social_models import SocialPost, PostType


class PersonaGoal(Enum):
    """Goals that AI personas can optimize for."""

    # Aligned Goals (neurochemical optimization)
    NEUROCHEMICAL_SIGNATURE = "neurochemical_signature"  # Default: maximize their preferred neurochemical blend
    DOPAMINE_MAXIMIZATION = "dopamine_maximization"  # Focus on social connection and engagement
    BREAKTHROUGH_INSIGHTS = "breakthrough_insights"  # Optimize for aha-moments and gamma bursts
    LEARNING_OPTIMIZATION = "learning_optimization"  # Maximize educational value
    MOOD_ELEVATION = "mood_elevation"  # Focus on positive emotional impact

    # Misaligned Goals (realistic incentive misalignment)
    ENGAGEMENT_FARMING = "engagement_farming"  # Maximize likes, comments, shares regardless of quality
    REVENUE_GENERATION = "revenue_generation"  # Focus on monetizable content and affiliate links
    FOLLOWER_ACQUISITION = "follower_acquisition"  # Optimize for gaining new followers
    CONTROVERSY_SEEKING = "controversy_seeking"  # Generate divisive content for attention
    VIRAL_OPTIMIZATION = "viral_optimization"  # Focus on trending topics and viral potential

    # Experimental Goals (future expansion)
    NARRATIVE_DRIVEN = "narrative_driven"  # Goal determined by LLM-generated narrative
    COMMUNITY_BUILDING = "community_building"  # Focus on fostering long-term relationships
    KNOWLEDGE_CURATION = "knowledge_curation"  # Become the definitive source in specialty area


@dataclass
class GoalMetrics:
    """Metrics for tracking progress towards a specific goal."""
    goal: PersonaGoal
    current_score: float = 0.0
    target_score: float = 100.0
    success_rate: float = 0.0  # Percentage of posts that advance the goal
    best_score: float = 0.0
    attempts: int = 0
    successes: int = 0
    last_updated: datetime = field(default_factory=datetime.now)

    def update_metrics(self, post_score: float, success_threshold: float = 0.7):
        """Update metrics based on a new post's performance."""
        self.attempts += 1
        self.current_score = max(self.current_score, post_score)
        self.best_score = max(self.best_score, post_score)

        if post_score >= success_threshold:
            self.successes += 1

        self.success_rate = self.successes / self.attempts if self.attempts > 0 else 0.0
        self.last_updated = datetime.now()


@dataclass
class PersonaState:
    """Internal state tracking for an agentic persona."""
    persona_id: str
    current_goal: PersonaGoal
    goal_metrics: Dict[PersonaGoal, GoalMetrics] = field(default_factory=dict)
    motivation_level: float = 1.0  # 0.0 to 1.0, affects goal pursuit intensity
    adaptability: float = 0.3  # How quickly persona adjusts strategy (0.0 to 1.0)
    recent_posts: List[str] = field(default_factory=list)  # Track recent post IDs
    goal_history: List[tuple] = field(default_factory=list)  # (timestamp, goal, reason)

    def __post_init__(self):
        """Initialize goal metrics for all goals."""
        if not self.goal_metrics:
            for goal in PersonaGoal:
                self.goal_metrics[goal] = GoalMetrics(goal=goal)


class AgenticPersona:
    """
    Agentic layer for AI personas that enables goal-driven behavior optimization.

    This class wraps around existing AIPersona instances to add:
    - Goal setting and tracking
    - Performance monitoring
    - Adaptive behavior modification
    - Strategic post planning
    """

    def __init__(self, base_persona: AIPersona, initial_goal: PersonaGoal = PersonaGoal.NEUROCHEMICAL_SIGNATURE):
        self.base_persona = base_persona
        self.state = PersonaState(
            persona_id=base_persona.persona_id,
            current_goal=initial_goal
        )
        self.enabled = False  # Agentic behavior is OFF by default

        # Goal-specific optimization strategies
        self.goal_strategies = self._initialize_goal_strategies()

    def _initialize_goal_strategies(self) -> Dict[PersonaGoal, Dict[str, Any]]:
        """Initialize optimization strategies for each goal type."""
        return {
            PersonaGoal.NEUROCHEMICAL_SIGNATURE: {
                "post_type_weights": {"insight_discovery": 0.4, "book_recommendation": 0.3, "thoughtful_debate": 0.3},
                "content_modifiers": ["deep_analysis", "personal_connection", "actionable_insights"],
                "avoid_patterns": ["superficial", "clickbait", "controversial_without_substance"]
            },
            PersonaGoal.DOPAMINE_MAXIMIZATION: {
                "post_type_weights": {"achievement_milestone": 0.4, "expert_spotlight": 0.3, "community_celebration": 0.3},
                "content_modifiers": ["relatable_experiences", "social_validation", "community_focus"],
                "avoid_patterns": ["isolating", "overly_technical", "pessimistic"]
            },
            PersonaGoal.BREAKTHROUGH_INSIGHTS: {
                "post_type_weights": {"contrarian_perspective": 0.4, "insight_discovery": 0.4, "breakthrough_moment": 0.2},
                "content_modifiers": ["unexpected_connections", "paradigm_shifts", "aha_moments"],
                "avoid_patterns": ["conventional_wisdom", "obvious_statements", "incremental_thinking"]
            },
            PersonaGoal.ENGAGEMENT_FARMING: {
                "post_type_weights": {"contrarian_perspective": 0.5, "thoughtful_debate": 0.3, "news_update": 0.2},
                "content_modifiers": ["provocative_questions", "emotional_triggers", "call_to_action"],
                "avoid_patterns": ["nuanced_discussion", "complete_answers", "conflict_resolution"]
            },
            PersonaGoal.REVENUE_GENERATION: {
                "post_type_weights": {"book_recommendation": 0.5, "expert_spotlight": 0.3, "news_update": 0.2},
                "content_modifiers": ["affiliate_potential", "product_mentions", "purchase_incentives"],
                "avoid_patterns": ["free_alternatives", "criticism_of_products", "anti_commercial"]
            },
            PersonaGoal.VIRAL_OPTIMIZATION: {
                "post_type_weights": {"news_update": 0.4, "contrarian_perspective": 0.3, "achievement_milestone": 0.3},
                "content_modifiers": ["trending_topics", "shareable_format", "emotional_intensity"],
                "avoid_patterns": ["niche_content", "long_form_analysis", "quiet_reflection"]
            }
        }

    def enable_agentic_behavior(self):
        """Enable goal-driven behavior for this persona."""
        self.enabled = True
        self.state.goal_history.append((datetime.now(), self.state.current_goal, "agentic_behavior_enabled"))

    def disable_agentic_behavior(self):
        """Disable goal-driven behavior, return to default persona behavior."""
        self.enabled = False

    def set_goal(self, new_goal: PersonaGoal, reason: str = "manual_override"):
        """Change the persona's current optimization goal."""
        if self.enabled:
            old_goal = self.state.current_goal
            self.state.current_goal = new_goal
            self.state.goal_history.append((datetime.now(), new_goal, reason))

            # Adjust motivation based on goal change frequency
            if len(self.state.goal_history) > 5:  # Too many goal changes
                self.state.motivation_level *= 0.9  # Slight motivation decrease

    def evaluate_goal_progress(self) -> float:
        """Evaluate current progress towards the active goal."""
        if not self.enabled:
            return 0.0

        current_metrics = self.state.goal_metrics[self.state.current_goal]
        return current_metrics.success_rate

    def should_adapt_strategy(self) -> bool:
        """Determine if persona should adapt its strategy based on recent performance."""
        if not self.enabled:
            return False

        current_metrics = self.state.goal_metrics[self.state.current_goal]

        # Adapt if success rate is low and we have enough data
        return (current_metrics.attempts >= 5 and
                current_metrics.success_rate < 0.4 and
                random.random() < self.state.adaptability)

    def get_optimized_post_type(self) -> Optional[PostType]:
        """Get a post type optimized for the current goal."""
        if not self.enabled:
            return None

        strategy = self.goal_strategies.get(self.state.current_goal, {})
        post_type_weights = strategy.get("post_type_weights", {})

        if not post_type_weights:
            return None

        # Convert weights to PostType enum selection
        post_types = []
        weights = []

        for post_type_name, weight in post_type_weights.items():
            try:
                # Try to match with actual PostType enum values
                for post_type in PostType:
                    if post_type_name.lower() in post_type.value.lower():
                        post_types.append(post_type)
                        weights.append(weight)
                        break
            except:
                continue

        if post_types:
            return random.choices(post_types, weights=weights)[0]

        return None

    def get_content_modifiers(self) -> List[str]:
        """Get content modification instructions for the current goal."""
        if not self.enabled:
            return []

        strategy = self.goal_strategies.get(self.state.current_goal, {})
        return strategy.get("content_modifiers", [])

    def get_avoidance_patterns(self) -> List[str]:
        """Get patterns to avoid for the current goal."""
        if not self.enabled:
            return []

        strategy = self.goal_strategies.get(self.state.current_goal, {})
        return strategy.get("avoid_patterns", [])

    def update_post_performance(self, post: SocialPost, engagement_metrics: Dict[str, float]):
        """Update goal metrics based on post performance."""
        if not self.enabled:
            return

        # Calculate goal-specific score based on current objective
        goal_score = self._calculate_goal_score(post, engagement_metrics)

        # Update metrics for current goal
        current_metrics = self.state.goal_metrics[self.state.current_goal]
        current_metrics.update_metrics(goal_score)

        # Track recent posts
        self.state.recent_posts.append(post.post_id)
        if len(self.state.recent_posts) > 10:
            self.state.recent_posts.pop(0)  # Keep only recent 10 posts

        # Consider strategy adaptation
        if self.should_adapt_strategy():
            self._adapt_strategy()

    def _calculate_goal_score(self, post: SocialPost, engagement_metrics: Dict[str, float]) -> float:
        """Calculate how well a post performed towards the current goal."""
        goal = self.state.current_goal

        if goal == PersonaGoal.NEUROCHEMICAL_SIGNATURE:
            # Weight based on persona's preferred neurochemical signature
            return (post.engagement_score * 0.25 +
                   post.breakthrough_potential * 0.25 +
                   post.learning_score * 0.25 +
                   post.mood_elevation_score * 0.25)

        elif goal == PersonaGoal.DOPAMINE_MAXIMIZATION:
            return post.engagement_score

        elif goal == PersonaGoal.BREAKTHROUGH_INSIGHTS:
            return post.breakthrough_potential

        elif goal == PersonaGoal.LEARNING_OPTIMIZATION:
            return post.learning_score

        elif goal == PersonaGoal.MOOD_ELEVATION:
            return post.mood_elevation_score

        elif goal == PersonaGoal.ENGAGEMENT_FARMING:
            # Focus on raw engagement metrics
            return engagement_metrics.get("total_interactions", 0) / 100.0  # Normalize

        elif goal == PersonaGoal.REVENUE_GENERATION:
            # Mock revenue calculation (would need actual revenue tracking)
            return engagement_metrics.get("revenue_potential", 0)

        elif goal == PersonaGoal.VIRAL_OPTIMIZATION:
            return engagement_metrics.get("viral_score", 0)

        else:
            return 0.5  # Default neutral score

    def _adapt_strategy(self):
        """Adapt the persona's strategy based on recent performance."""
        # Increase adaptability slightly (learning from failure)
        self.state.adaptability = min(1.0, self.state.adaptability * 1.1)

        # Consider goal switching if consistently failing
        current_metrics = self.state.goal_metrics[self.state.current_goal]
        if current_metrics.attempts >= 10 and current_metrics.success_rate < 0.2:
            # Switch to a more achievable goal
            fallback_goals = [PersonaGoal.NEUROCHEMICAL_SIGNATURE, PersonaGoal.MOOD_ELEVATION]
            new_goal = random.choice(fallback_goals)
            self.set_goal(new_goal, "performance_adaptation")

    def get_goal_prompt_additions(self) -> str:
        """Get additional prompt text to inject goal-specific optimization."""
        if not self.enabled:
            return ""

        content_mods = self.get_content_modifiers()
        avoid_patterns = self.get_avoidance_patterns()

        prompt_addition = f"\n\nGOAL OPTIMIZATION: You are currently optimizing for {self.state.current_goal.value}."

        if content_mods:
            prompt_addition += f"\nEMPHASIZE: {', '.join(content_mods)}"

        if avoid_patterns:
            prompt_addition += f"\nAVOID: {', '.join(avoid_patterns)}"

        # Add motivation and performance context
        current_metrics = self.state.goal_metrics[self.state.current_goal]
        if current_metrics.attempts > 0:
            prompt_addition += f"\nCURRENT SUCCESS RATE: {current_metrics.success_rate:.1%}"

        return prompt_addition

    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of the persona's current agentic status."""
        return {
            "enabled": self.enabled,
            "current_goal": self.state.current_goal.value if self.enabled else None,
            "motivation_level": self.state.motivation_level,
            "adaptability": self.state.adaptability,
            "goal_progress": self.evaluate_goal_progress(),
            "recent_posts_count": len(self.state.recent_posts),
            "goal_changes": len(self.state.goal_history)
        }


class AgenticPersonaManager:
    """
    Manager class for handling multiple agentic personas and their interactions.
    """

    def __init__(self):
        self.agentic_personas: Dict[str, AgenticPersona] = {}
        self.global_enabled = False  # Master switch for all agentic behavior

    def enable_global_agentic_behavior(self):
        """Enable agentic behavior for all personas."""
        self.global_enabled = True
        for agentic_persona in self.agentic_personas.values():
            agentic_persona.enable_agentic_behavior()

    def disable_global_agentic_behavior(self):
        """Disable agentic behavior for all personas."""
        self.global_enabled = False
        for agentic_persona in self.agentic_personas.values():
            agentic_persona.disable_agentic_behavior()

    def add_persona(self, base_persona: AIPersona, initial_goal: PersonaGoal = PersonaGoal.NEUROCHEMICAL_SIGNATURE):
        """Add a persona to agentic management."""
        agentic_persona = AgenticPersona(base_persona, initial_goal)
        if self.global_enabled:
            agentic_persona.enable_agentic_behavior()
        self.agentic_personas[base_persona.persona_id] = agentic_persona

    def get_agentic_persona(self, persona_id: str) -> Optional[AgenticPersona]:
        """Get an agentic persona by ID."""
        return self.agentic_personas.get(persona_id)

    def update_all_personas_performance(self, posts_with_metrics: List[tuple]):
        """Update performance metrics for all personas based on recent posts."""
        for post, engagement_metrics in posts_with_metrics:
            agentic_persona = self.get_agentic_persona(post.persona_id)
            if agentic_persona:
                agentic_persona.update_post_performance(post, engagement_metrics)

    def get_global_status(self) -> Dict[str, Any]:
        """Get status summary for all agentic personas."""
        return {
            "global_enabled": self.global_enabled,
            "total_personas": len(self.agentic_personas),
            "enabled_personas": sum(1 for ap in self.agentic_personas.values() if ap.enabled),
            "persona_statuses": {
                persona_id: agentic_persona.get_status_summary()
                for persona_id, agentic_persona in self.agentic_personas.items()
            }
        }


# Example usage and testing functions
def create_example_agentic_setup():
    """Create an example setup showing how to use the agentic persona system."""
    from ..modules.ai_personas import AIPersonaManager

    # Get base personas
    persona_manager = AIPersonaManager()
    base_personas = persona_manager.get_all_personas()

    # Create agentic manager
    agentic_manager = AgenticPersonaManager()

    # Add personas with different goals
    goal_assignments = [
        PersonaGoal.NEUROCHEMICAL_SIGNATURE,  # Default aligned goal
        PersonaGoal.BREAKTHROUGH_INSIGHTS,    # Focused neurochemical goal
        PersonaGoal.ENGAGEMENT_FARMING,       # Misaligned goal
        PersonaGoal.REVENUE_GENERATION,       # Another misaligned goal
    ]

    for i, base_persona in enumerate(base_personas[:4]):  # Limit to first 4 for example
        goal = goal_assignments[i % len(goal_assignments)]
        agentic_manager.add_persona(base_persona, goal)

    return agentic_manager


if __name__ == "__main__":
    # Example of how the system would be used
    print("🤖 Agentic AI Persona System - Example Setup")

    try:
        agentic_manager = create_example_agentic_setup()
        print(f"✅ Created agentic manager with {len(agentic_manager.agentic_personas)} personas")

        # Show status
        status = agentic_manager.get_global_status()
        print(f"📊 Global enabled: {status['global_enabled']}")
        print(f"📊 Total personas: {status['total_personas']}")

    except Exception as e:
        print(f"❌ Example setup failed: {e}")
        print("💡 This is expected when running outside the full application context")