#!/usr/bin/env python3
"""
AI Social Server - Main Streamlit App
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st
from social_server.modules.ai_personas import AIPersonaManager
from social_server.modules.generate_social_feed import SocialFeedManager, SocialFeedGenerator
from social_server.core.simple_auth import get_auth
from social_server.core.paths import get_data_path

# Import the main function from the AI Social Feed page
import importlib.util
feed_spec = importlib.util.spec_from_file_location("ai_social_server", "src/social_server/Social_Xtuff.py")
feed_module = importlib.util.module_from_spec(feed_spec)
feed_spec.loader.exec_module(feed_module)

# Run the main feed function
if __name__ == "__main__":
    feed_module.main()