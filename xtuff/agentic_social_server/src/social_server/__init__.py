"""
Agentic Social Server

An AI-powered social media platform with 4-factor neurochemical optimization
for book lovers, featuring 10 unique AI personas and evidence-based content targeting.
"""

__version__ = "1.0.0"
__author__ = "Nimble Research Collective"
__email__ = "contact@example.org"
__description__ = "AI-powered social media platform with 4-factor neurochemical optimization for book lovers"

# Import main components for easy access
from .app import main
from .modules.ai_personas import AIPersonaManager
from .modules.generate_social_feed import SocialFeedManager, SocialFeedGenerator

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    "main",
    "AIPersonaManager",
    "SocialFeedManager",
    "SocialFeedGenerator"
]