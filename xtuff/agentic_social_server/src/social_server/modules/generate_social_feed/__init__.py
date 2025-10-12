"""
Generate Social Feed Module

Handles all social media feed generation, including:
- Feed generation using AI personas
- Social post models and management
- User preferences and optimization
"""

from .feed_generator import FeedGenerator as SocialFeedGenerator
from .social_models import (
    SocialPost,
    PostType,
    UserAction,
    FeedPreferences,
    SocialFeedManager,
    UserInteraction
)

__all__ = [
    'SocialFeedGenerator',
    'SocialPost',
    'PostType',
    'UserAction',
    'FeedPreferences',
    'SocialFeedManager',
    'UserInteraction'
]