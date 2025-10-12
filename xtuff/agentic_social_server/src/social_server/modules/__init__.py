"""
Social Media Module for AI Lab for Book-Lovers

This module provides social media functionality focused on delivering
dopamine (social connection) and synaptic rush (learning) through
AI persona interactions centered on books, reading, and literary culture.
"""

from .ai_personas import AIPersona, AIPersonaManager
from .generate_social_feed.social_models import (
    SocialPost,
    PostType,
    UserAction,
    UserInteraction,
    FeedPreferences,
    SocialFeedManager
)
from .generate_social_feed.feed_generator import FeedGenerator

__all__ = [
    'AIPersona',
    'AIPersonaManager',
    'SocialPost',
    'PostType',
    'UserAction',
    'UserInteraction',
    'FeedPreferences',
    'SocialFeedManager',
    'FeedGenerator'
]