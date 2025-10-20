"""
User Profile Home Page - AI Personas & Users
version 1.1.0 - Migrated to shared authentication system

A comprehensive profile page showcasing AI personas and user statistics,
preferences, and activity within the AI Lab for Book-Lovers community.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import sys
import logging
from pathlib import Path
import json

sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Add the project root to Python path for proper imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
except ImportError as e:
    st.error(f"Failed to import shared authentication: {e}")
    st.error("Please ensure /Users/fred/xcu_my_apps/shared/auth is accessible")
    st.stop()

try:
    from social_server.modules import AIPersonaManager, SocialFeedManager, UserInteraction, UserAction, FeedPreferences
except ImportError:
    # Fallback for direct execution
    from social_server.modules import AIPersonaManager, SocialFeedManager, UserInteraction, UserAction, FeedPreferences

# NOTE: st.set_page_config() and render_unified_sidebar() handled by main app

# Hide native Streamlit navigation
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

# Initialize shared authentication system
try:
    shared_auth = get_shared_auth()
    logger.info("Shared authentication system initialized")
except Exception as e:
    logger.error(f"Failed to initialize shared auth: {e}")
    st.error("Authentication system unavailable.")

# Sync session state from shared auth
if is_authenticated():
    user_info = get_user_info()
    st.session_state.username = user_info.get('username')
    st.session_state.user_name = user_info.get('user_name')
    st.session_state.user_email = user_info.get('user_email')
    logger.info(f"User authenticated via shared auth: {st.session_state.username}")
else:
    if "username" not in st.session_state:
        st.session_state.username = None

# Initialize managers
@st.cache_resource
def init_managers():
    """Initialize social media managers with caching."""
    persona_manager = AIPersonaManager()
    feed_manager = SocialFeedManager()
    return persona_manager, feed_manager

def get_user_id():
    """Get current user ID from authentication system."""
    if is_authenticated():
        user_info = get_user_info()
        return user_info.get('username', 'anonymous')
    return "anonymous"

def get_user_stats(feed_manager, user_id):
    """Get user activity statistics."""
    if user_id == "anonymous":
        return {}

    # Get user interactions
    user_interactions = [i for i in feed_manager.interactions if i.user_id == user_id]

    # Calculate stats
    stats = {
        "total_interactions": len(user_interactions),
        "likes_given": len([i for i in user_interactions if i.action == UserAction.LIKE]),
        "forwards_given": len([i for i in user_interactions if i.action == UserAction.FORWARD]),
        "bookmarks_made": len([i for i in user_interactions if i.action == UserAction.BOOKMARK]),
        "posts_hidden": len([i for i in user_interactions if i.action == UserAction.HIDE]),
        "days_active": len(set(i.timestamp[:10] for i in user_interactions)),  # Unique dates
        "favorite_personas": get_favorite_personas(user_interactions),
        "activity_by_day": get_activity_by_day(user_interactions),
        "recent_activity": user_interactions[-10:] if user_interactions else []
    }

    return stats

def get_favorite_personas(interactions):
    """Get user's most interacted-with personas."""
    persona_counts = {}
    for interaction in interactions:
        # We'd need to look up the persona from the post, simplified for now
        persona_counts[interaction.post_id] = persona_counts.get(interaction.post_id, 0) + 1

    # Return top 3 (simplified - in real implementation would map to actual personas)
    return list(persona_counts.keys())[:3]

def get_activity_by_day(interactions):
    """Get activity breakdown by day of week."""
    from collections import defaultdict
    activity = defaultdict(int)

    for interaction in interactions:
        try:
            day = datetime.fromisoformat(interaction.timestamp).strftime("%A")
            activity[day] += 1
        except:
            continue

    return dict(activity)

def display_ai_persona_profile(persona):
    """Display detailed AI persona profile."""
    # Header with avatar and basic info
    col1, col2 = st.columns([2, 5])

    with col1:
        st.markdown(
            f"<div style='text-align: center; font-size: 6em; padding: 20px;'>{persona.avatar_emoji}</div>",
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(f"# {persona.name}")
        st.markdown(f"## {persona.handle}")
        st.markdown(f"*{persona.bio}*")

        # Key stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👥 Followers", f"{persona.follower_count:,}")
        with col2:
            st.metric("📚 Specialty", persona.specialty)
        with col3:
            st.metric("📅 Active Since", persona.created_at[:10] if persona.created_at else "N/A")

    # Detailed sections
    st.markdown("---")

    # Personality and Interests
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🧠 Personality Traits")
        for trait in persona.personality_traits:
            st.markdown(f"• **{trait.title()}**")

        st.subheader("✍️ Writing Style")
        st.markdown(f"*{persona.writing_style}*")

    with col2:
        st.subheader("📖 Interests")
        for interest in persona.interests:
            st.markdown(f"• {interest}")

    # Technical Details (if available)
    if persona.claude_agent_config:
        st.subheader("🤖 AI Configuration")
        config_col1, config_col2 = st.columns(2)

        with config_col1:
            st.markdown(f"**Model:** {persona.claude_agent_config.get('model', 'N/A')}")
        with config_col2:
            st.markdown(f"**Temperature:** {persona.claude_agent_config.get('temperature', 'N/A')}")

def display_user_profile(user_id, feed_manager):
    """Display user profile with stats and preferences."""
    if user_id == "anonymous":
        st.info("👋 Welcome! Log in to see your personalized profile.")
        return

    # Header
    st.markdown(f"# 👤 {user_id}")
    st.markdown("### Your AI Lab for Book-Lovers Profile")

    # Get user stats and preferences
    stats = get_user_stats(feed_manager, user_id)
    user_prefs = feed_manager.preferences.get(user_id, FeedPreferences(user_id=user_id))

    # Activity Overview
    st.subheader("📊 Activity Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("💝 Total Interactions", stats.get("total_interactions", 0))
    with col2:
        st.metric("❤️ Likes Given", stats.get("likes_given", 0))
    with col3:
        st.metric("🔄 Forwards", stats.get("forwards_given", 0))
    with col4:
        st.metric("📚 Bookmarks", stats.get("bookmarks_made", 0))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📅 Days Active", stats.get("days_active", 0))
    with col2:
        st.metric("🙈 Posts Hidden", stats.get("posts_hidden", 0))
    with col3:
        if stats.get("activity_by_day"):
            most_active_day = max(stats["activity_by_day"], key=stats["activity_by_day"].get)
            st.metric("📈 Most Active Day", most_active_day)

    # Neurochemical Preferences
    st.subheader("🧬 Your Neurochemical Profile")

    # Display preferences as progress bars
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**💕 Dopamine (Social Connection)**")
        st.progress(user_prefs.engagement_weight)
        st.caption(f"{user_prefs.engagement_weight:.1%}")

    with col2:
        st.markdown("**⚡ Breakthrough Buzz (Insights)**")
        st.progress(user_prefs.breakthrough_weight)
        st.caption(f"{user_prefs.breakthrough_weight:.1%}")

    with col3:
        st.markdown("**📖 Traditional Learning**")
        st.progress(user_prefs.learning_weight)
        st.caption(f"{user_prefs.learning_weight:.1%}")

    # Activity Timeline
    if stats.get("recent_activity"):
        st.subheader("🕐 Recent Activity")

        for i, activity in enumerate(stats["recent_activity"][-5:]):  # Show last 5
            with st.expander(f"{activity.action.value.title()} - {activity.timestamp[:16]}"):
                st.markdown(f"**Action:** {activity.action.value}")
                st.markdown(f"**Post ID:** {activity.post_id[:8]}...")
                st.markdown(f"**Time:** {activity.timestamp}")

def main():
    """Main application function."""
    # Import and use page utilities for consistent sidebar and auth
    try:
        from codexes.core.page_utils import render_page_sidebar, ensure_auth_checked

        # Ensure auth has been checked for this session
        ensure_auth_checked()

        # Render the full sidebar with all sections
        render_page_sidebar()
    except ImportError as e:
        logger.warning(f"Could not import page_utils: {e}")
        # Fallback continues with existing code

    # Header
    st.title("👤 Profile Home")
    st.markdown("### *AI Personas & User Profiles - AI Lab for Book-Lovers*")

    # Initialize everything
    persona_manager, feed_manager = init_managers()
    user_id = get_user_id()
    is_logged_in = user_id != "anonymous"

    # Navigation
    view_type = st.radio(
        "Choose View:",
        ["👤 My Profile", "🤖 AI Personas", "🌟 Featured Personas"],
        index=0 if is_logged_in else 1
    )

    if view_type == "🤖 AI Personas":
        st.subheader("Select AI Persona")
        personas = persona_manager.get_all_personas()
        persona_names = [f"{p.avatar_emoji} {p.name}" for p in personas]
        selected_persona = st.selectbox("Choose persona:", persona_names)

    # Quick stats for logged-in users
    if is_logged_in:
        st.markdown("---")
        st.subheader("📊 Quick Stats")
        stats = get_user_stats(feed_manager, user_id)
        st.metric("Total Interactions", stats.get("total_interactions", 0))
        st.metric("Days Active", stats.get("days_active", 0))

    # Main Content Area
    if view_type == "👤 My Profile":
        display_user_profile(user_id, feed_manager)

    elif view_type == "🤖 AI Personas":
        if 'selected_persona' in locals():
            personas = persona_manager.get_all_personas()
            # Find the selected persona
            for persona in personas:
                if f"{persona.avatar_emoji} {persona.name}" == selected_persona:
                    display_ai_persona_profile(persona)
                    break

    elif view_type == "🌟 Featured Personas":
        st.subheader("🌟 Featured AI Personas")
        st.markdown("*Meet our top AI book-lovers and their unique perspectives*")

        personas = persona_manager.get_all_personas()

        # Show top 3 personas with highest follower counts
        featured_personas = sorted(personas, key=lambda p: p.follower_count, reverse=True)[:3]

        for persona in featured_personas:
            with st.expander(f"{persona.avatar_emoji} {persona.name} - {persona.follower_count:,} followers"):
                display_ai_persona_profile(persona)
            st.markdown("---")

    # Footer
    st.markdown("---")
    st.markdown("*Part of the AI Lab for Book-Lovers • Powered by Codexes Factory*")

if __name__ == "__main__":
    main()