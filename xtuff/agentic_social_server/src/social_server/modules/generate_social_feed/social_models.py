"""
Social Media Models for AI Lab for Book-Lovers

Focused on delivering dopamine (social connection) and synaptic rush (learning).
Models designed for book-focused social interactions with AI personas.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from pathlib import Path
import random

try:
    from social_server.core.paths import get_storage_path
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from core.paths import get_storage_path


class PostType(Enum):
    """Types of social media posts."""
    BOOK_RECOMMENDATION = "book_recommendation"
    BOOK_QUOTE = "book_quote"
    ARXIV_SHARE = "arxiv_share"
    NEWS_UPDATE = "news_update"
    CONTRARIAN_PERSPECTIVE = "contrarian_perspective"
    INSIGHT_DISCOVERY = "insight_discovery"
    EXPERT_SPOTLIGHT = "expert_spotlight"
    DOMAIN_EXPLORATION = "domain_exploration"
    LEARNING_CHALLENGE = "learning_challenge"
    THOUGHTFUL_DEBATE = "thoughtful_debate"
    ACHIEVEMENT_MILESTONE = "achievement_milestone"
    BREAKTHROUGH_MOMENT = "breakthrough_moment"
    TIL_DOUBLEDOME = "today_i_learned"
    PEDANTRY_FTW = "pedantry_ftw"


class UserAction(Enum):
    """User actions on posts."""
    LIKE = "like"
    FORWARD = "forward"
    HIDE = "hide"
    BOOKMARK = "bookmark"


@dataclass
class SocialPost:
    """A social media post from an AI persona."""

    post_id: str
    persona_id: str
    content: str
    post_type: PostType
    timestamp: str
    engagement_hooks: List[str]  # Elements designed for dopamine (social connection)
    breakthrough_triggers: List[str] = field(default_factory=list)  # Aha-moment catalysts
    prediction_violations: List[str] = field(default_factory=list)  # Expectation violations
    pattern_bridges: List[str] = field(default_factory=list)  # Unexpected connections
    learning_nuggets: List[str] = field(default_factory=list)  # Traditional educational content
    book_references: List[Dict[str, str]] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    likes: int = 0
    forwards: int = 0
    replies: List[str] = field(default_factory=list)
    is_trending: bool = False
    learning_score: float = 0.0  # 0-1 scale for traditional educational value
    engagement_score: float = 0.0  # 0-1 scale for social connection
    breakthrough_potential: float = 0.0  # 0-1 scale for norepinephrine-driven insight potential
    mood_elevation_score: float = 0.0  # 0-1 scale for humor, inspiration, and positive emotional impact
    generated_by_model: str = ""  # Model that generated this post

    def __post_init__(self):
        if not self.post_id:
            self.post_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['post_type'] = self.post_type.value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SocialPost':
        """Create from dictionary."""
        data['post_type'] = PostType(data['post_type'])
        return cls(**data)


@dataclass
class UserInteraction:
    """Tracks user interactions with posts."""

    user_id: str
    post_id: str
    action: UserAction
    timestamp: str
    context: Optional[str] = None  # Additional context (e.g., comment text)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['action'] = self.action.value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserInteraction':
        """Create from dictionary."""
        data['action'] = UserAction(data['action'])
        return cls(**data)


@dataclass
class FeedPreferences:
    """User preferences for social media feed."""

    user_id: str
    preferred_genres: List[str] = field(default_factory=list)
    preferred_personas: List[str] = field(default_factory=list)
    hidden_personas: List[str] = field(default_factory=list)
    hidden_posts: List[str] = field(default_factory=list)  # Individual hidden post IDs
    engagement_weight: float = 0.3  # 0-1, dopamine/social connection
    learning_weight: float = 0.25  # 0-1, traditional educational content
    breakthrough_weight: float = 0.25  # 0-1, norepinephrine-driven insights
    mood_elevation_weight: float = 0.2  # 0-1, humor and inspiration for mood enhancement
    max_posts_per_session: int = 25
    preferred_post_types: List[PostType] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['preferred_post_types'] = [pt.value for pt in self.preferred_post_types]
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedPreferences':
        """Create from dictionary."""
        if 'preferred_post_types' in data:
            data['preferred_post_types'] = [PostType(pt) for pt in data['preferred_post_types']]
        return cls(**data)


class SocialFeedManager:
    """Manages the social media feed for optimal dopamine and learning delivery."""

    def __init__(self,
                 posts_storage_path: Optional[str] = None,
                 interactions_storage_path: Optional[str] = None,
                 preferences_storage_path: Optional[str] = None):

        # Use project-relative paths by default
        self.posts_storage_path = (Path(posts_storage_path) if posts_storage_path
                                 else get_storage_path("social_posts.json"))
        self.interactions_storage_path = (Path(interactions_storage_path) if interactions_storage_path
                                        else get_storage_path("user_interactions.json"))
        self.preferences_storage_path = (Path(preferences_storage_path) if preferences_storage_path
                                       else get_storage_path("feed_preferences.json"))

        self.posts: Dict[str, SocialPost] = {}
        self.interactions: List[UserInteraction] = []
        self.preferences: Dict[str, FeedPreferences] = {}

        self._load_data()

    def _load_data(self):
        """Load all data from JSON files."""
        # Load posts
        if self.posts_storage_path.exists():
            try:
                with open(self.posts_storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for post_id, post_data in data.items():
                        self.posts[post_id] = SocialPost.from_dict(post_data)
            except Exception as e:
                print(f"Error loading posts: {e}")

        # Load interactions
        if self.interactions_storage_path.exists():
            try:
                with open(self.interactions_storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.interactions = [UserInteraction.from_dict(item) for item in data]
            except Exception as e:
                print(f"Error loading interactions: {e}")

        # Load preferences
        if self.preferences_storage_path.exists():
            try:
                with open(self.preferences_storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, pref_data in data.items():
                        self.preferences[user_id] = FeedPreferences.from_dict(pref_data)
            except Exception as e:
                print(f"Error loading preferences: {e}")

    def save_posts(self):
        """Save posts to JSON file."""
        self.posts_storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {post_id: post.to_dict() for post_id, post in self.posts.items()}
        with open(self.posts_storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_interactions(self):
        """Save interactions to JSON file."""
        self.interactions_storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = [interaction.to_dict() for interaction in self.interactions]
        with open(self.interactions_storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_preferences(self):
        """Save preferences to JSON file."""
        self.preferences_storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {user_id: pref.to_dict() for user_id, pref in self.preferences.items()}
        with open(self.preferences_storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_post(self, post: SocialPost):
        """Add a new post to the feed."""
        self.posts[post.post_id] = post
        self.save_posts()

    def record_interaction(self, interaction: UserInteraction):
        """Record a user interaction."""
        self.interactions.append(interaction)

        # Update post engagement metrics and handle hide actions
        if interaction.post_id in self.posts:
            post = self.posts[interaction.post_id]
            if interaction.action == UserAction.LIKE:
                post.likes += 1
            elif interaction.action == UserAction.FORWARD:
                post.forwards += 1

            # Update engagement score based on recent interactions
            self._update_post_engagement(post)

        # Handle hide action - add post to user's hidden posts
        if interaction.action == UserAction.HIDE:
            user_prefs = self.preferences.get(interaction.user_id, FeedPreferences(user_id=interaction.user_id))
            if interaction.post_id not in user_prefs.hidden_posts:
                user_prefs.hidden_posts.append(interaction.post_id)
                self.preferences[interaction.user_id] = user_prefs
                self.save_preferences()

        self.save_interactions()
        self.save_posts()

    def _update_post_engagement(self, post: SocialPost):
        """Update post engagement score based on interactions."""
        # Simple engagement scoring algorithm
        recent_interactions = [
            i for i in self.interactions
            if i.post_id == post.post_id and
            datetime.fromisoformat(i.timestamp) > datetime.now() - timedelta(hours=24)
        ]

        likes_weight = 1.0
        forwards_weight = 2.0  # Forwards are more valuable

        engagement_value = (
            len([i for i in recent_interactions if i.action == UserAction.LIKE]) * likes_weight +
            len([i for i in recent_interactions if i.action == UserAction.FORWARD]) * forwards_weight
        )

        # Normalize to 0-1 scale
        post.engagement_score = min(1.0, engagement_value / 10.0)

    def get_personalized_feed(self, user_id: str, limit: int = 25) -> List[SocialPost]:
        """Generate a personalized feed optimized for dopamine and learning."""
        user_prefs = self.preferences.get(user_id, FeedPreferences(user_id=user_id))

        # Get all posts not hidden by user (both personas and individual posts)
        available_posts = [
            post for post in self.posts.values()
            if post.persona_id not in user_prefs.hidden_personas and
               post.post_id not in user_prefs.hidden_posts
        ]

        # Filter by user preferences if any
        if user_prefs.preferred_personas:
            available_posts = [
                post for post in available_posts
                if post.persona_id in user_prefs.preferred_personas
            ]

        if user_prefs.preferred_post_types:
            available_posts = [
                post for post in available_posts
                if post.post_type in user_prefs.preferred_post_types
            ]

        # Score posts for this user with four-factor optimization
        scored_posts = []
        for post in available_posts:
            # Combined score based on user's dopamine/learning/breakthrough/mood weights
            combined_score = (
                post.engagement_score * user_prefs.engagement_weight +
                post.learning_score * user_prefs.learning_weight +
                post.breakthrough_potential * user_prefs.breakthrough_weight +
                post.mood_elevation_score * user_prefs.mood_elevation_weight
            )

            # Add some randomness for serendipity (cognitive flexibility)
            serendipity_boost = random.random() * 0.15
            final_score = combined_score + serendipity_boost

            scored_posts.append((final_score, post))

        # Sort by score and return top posts
        scored_posts.sort(key=lambda x: x[0], reverse=True)
        return [post for score, post in scored_posts[:limit]]

    def get_recent_posts(self, limit: int = 25) -> List[SocialPost]:
        """Get most recent posts for public view (no personalization)."""
        # Get all posts sorted by timestamp (newest first)
        all_posts = list(self.posts.values())
        all_posts.sort(key=lambda x: x.timestamp, reverse=True)
        return all_posts[:limit]

    def get_all_posts_for_user(self, user_id: str, limit: int = 50) -> List[SocialPost]:
        """Get all posts filtered by user's hidden posts and personas."""
        user_prefs = self.preferences.get(user_id, FeedPreferences(user_id=user_id))

        # Get all posts not hidden by user (both personas and individual posts)
        available_posts = [
            post for post in self.posts.values()
            if post.persona_id not in user_prefs.hidden_personas and
               post.post_id not in user_prefs.hidden_posts
        ]

        # Sort by timestamp (newest first)
        available_posts.sort(key=lambda x: x.timestamp, reverse=True)
        return available_posts[:limit]

    def update_user_preferences(self, user_id: str, preferences: FeedPreferences):
        """Update user preferences."""
        self.preferences[user_id] = preferences
        self.save_preferences()

    def get_trending_posts(self, limit: int = 10) -> List[SocialPost]:
        """Get trending posts based on recent engagement."""
        # Sort posts by recent engagement
        recent_cutoff = datetime.now() - timedelta(hours=6)

        trending_posts = []
        for post in self.posts.values():
            recent_interactions = [
                i for i in self.interactions
                if i.post_id == post.post_id and
                datetime.fromisoformat(i.timestamp) > recent_cutoff
            ]

            if recent_interactions:
                trending_score = len(recent_interactions) + post.engagement_score
                trending_posts.append((trending_score, post))

        trending_posts.sort(key=lambda x: x[0], reverse=True)
        return [post for score, post in trending_posts[:limit]]

    def get_learning_highlights(self, limit: int = 5) -> List[SocialPost]:
        """Get posts with highest learning value."""
        learning_posts = [(post.learning_score, post) for post in self.posts.values()]
        learning_posts.sort(key=lambda x: x[0], reverse=True)
        return [post for score, post in learning_posts[:limit]]