"""
AI Social Feed - Book-Lover's Social Media Experience
version 1.1.0 - Migrated to shared authentication system

Delivers dopamine (social connection) and synaptic rush (learning) through
AI persona interactions focused on books, reading, and literary culture.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Optional
import sys
import logging
from pathlib import Path

# Add paths for imports
sys.path.insert(0, '/Users/fred/xcu_my_apps')
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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

# Import with fallback pattern
try:
    from social_server.modules import AIPersonaManager, SocialFeedManager, FeedGenerator, UserInteraction, UserAction, FeedPreferences
except ImportError:
    # Fallback if social_server not available - this would need to be implemented
    st.error("social_server.modules not available")
    st.stop()

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
    feed_generator = FeedGenerator()
    return persona_manager, feed_manager, feed_generator

def get_user_id():
    """Get current user ID from authentication system."""
    if is_authenticated():
        user_info = get_user_info()
        return user_info.get('username', 'anonymous')
    return "anonymous"

def display_persona_card(persona):
    """Display a persona info card."""
    with st.container():
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(f"<div style='font-size: 3em; text-align: center;'>{persona.avatar_emoji}</div>",
                       unsafe_allow_html=True)
        with col2:
            st.markdown(f"**{persona.name}** {persona.handle}")
            st.markdown(f"*{persona.bio}*")
            st.markdown(f"**Specialty:** {persona.specialty}")
            st.markdown(f"**Followers:** {persona.follower_count:,}")

def display_persona_grid(persona_manager):
    """Display all personas in a grid layout."""
    personas = persona_manager.get_all_personas()

    # Create a grid layout
    cols_per_row = 2
    for i in range(0, len(personas), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(personas):
                persona = personas[i + j]
                with col:
                    with st.container():
                        st.markdown(
                            f"""
                            <div style='border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 15px;'>
                                <div style='text-align: center; font-size: 3em; margin-bottom: 10px;'>{persona.avatar_emoji}</div>
                                <h4 style='text-align: center; margin: 0;'>{persona.name}</h4>
                                <p style='text-align: center; color: #666; margin: 5px 0;'>{persona.handle}</p>
                                <p style='font-style: italic; margin: 10px 0;'>{persona.bio}</p>
                                <p><strong>Specialty:</strong> {persona.specialty}</p>
                                <p><strong>Style:</strong> {persona.writing_style[:100]}{'...' if len(persona.writing_style) > 100 else ''}</p>
                                <p><strong>Followers:</strong> {persona.follower_count:,}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

def display_post(post, persona, feed_manager, user_id, unique_suffix="", enable_interactions=True):
    """Display a social media post with interaction options."""

    # Ensure unique keys by adding suffix and timestamp
    base_key = f"{post.post_id}_{unique_suffix}_{hash(post.timestamp) % 10000}"

    # Compact post header - all on one line
    time_ago = datetime.fromisoformat(post.timestamp)
    header_html = f"""
    <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;'>
        <div style='display: flex; align-items: center; gap: 8px;'>
            <span style='font-size: 1.2em;'>{persona.avatar_emoji}</span>
            <strong>{persona.name}</strong>
            <span style='color: #666;'>{persona.handle}</span>
            <span style='color: #999; font-size: 0.85em;'>• {time_ago.strftime('%I:%M %p')} • {post.post_type.value.replace('_', ' ').title()}</span>
        </div>
        <span style='color: #ccc; cursor: pointer;'>⋯</span>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    # Post content with smaller font
    st.markdown(f"<div style='font-size: 0.95em; line-height: 1.4; margin-bottom: 8px;'>{post.content}</div>",
                unsafe_allow_html=True)

    # Hashtags (moved up, directly after content)
    if post.hashtags:
        hashtag_links = []
        for tag in post.hashtags:
            # Create clickable hashtag that will filter the feed
            hashtag_links.append(f"<a href='?tag={tag}' style='color: #1DA1F2; text-decoration: none; margin-right: 8px;'>#{tag}</a>")

        hashtag_html = f"<div style='margin-bottom: 12px; font-size: 0.9em;'>{''.join(hashtag_links)}</div>"
        st.markdown(hashtag_html, unsafe_allow_html=True)

    # Breakthrough buzz triggers (norepinephrine-driven insights)
    if post.breakthrough_triggers or post.prediction_violations or post.pattern_bridges:
        with st.expander("⚡ Breakthrough Buzz", expanded=False):
            if post.breakthrough_triggers:
                st.markdown("**🎯 Aha-Moment Catalysts:**")
                for trigger in post.breakthrough_triggers:
                    st.markdown(f"• {trigger}")

            if post.prediction_violations:
                st.markdown("**🔄 Expectation Violations:**")
                for violation in post.prediction_violations:
                    st.markdown(f"• {violation}")

            if post.pattern_bridges:
                st.markdown("**🌉 Unexpected Connections:**")
                for bridge in post.pattern_bridges:
                    st.markdown(f"• {bridge}")

    # Traditional learning content
    if post.learning_nuggets:
        with st.expander("📖 Learning Insights", expanded=False):
            for nugget in post.learning_nuggets:
                st.markdown(f"• {nugget}")

    # Book references
    if post.book_references:
        with st.expander("📚 Book References", expanded=False):
            for book_ref in post.book_references:
                st.markdown(f"**{book_ref.get('title', 'Unknown Title')}** by {book_ref.get('author', 'Unknown Author')}")
                if 'context' in book_ref:
                    st.caption(book_ref['context'])

    # Engagement metrics and actions
    if enable_interactions:
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])

        with col1:
            if st.button(f"❤️ {post.likes}", key=f"like_{base_key}", help="Like this post"):
                interaction = UserInteraction(
                    user_id=user_id,
                    post_id=post.post_id,
                    action=UserAction.LIKE,
                    timestamp=datetime.now().isoformat()
                )
                feed_manager.record_interaction(interaction)
                st.success("Liked! 💕")
                st.rerun()

        with col2:
            if st.button(f"🔄 {post.forwards}", key=f"forward_{base_key}", help="Forward this post"):
                interaction = UserInteraction(
                    user_id=user_id,
                    post_id=post.post_id,
                    action=UserAction.FORWARD,
                    timestamp=datetime.now().isoformat()
                )
                feed_manager.record_interaction(interaction)
                st.success("Forwarded! 🚀")
                st.rerun()

        with col3:
            if st.button("💬 Reply", key=f"reply_{base_key}", help="Reply to this post"):
                st.session_state[f"show_reply_{base_key}"] = True

        with col4:
            if st.button("🔖 Save", key=f"save_{base_key}", help="Bookmark this post"):
                interaction = UserInteraction(
                    user_id=user_id,
                    post_id=post.post_id,
                    action=UserAction.BOOKMARK,
                    timestamp=datetime.now().isoformat()
                )
                feed_manager.record_interaction(interaction)
                st.success("Bookmarked! 📚")

        with col5:
            if st.button("🙈 Hide", key=f"hide_{base_key}", help="Hide this post"):
                interaction = UserInteraction(
                    user_id=user_id,
                    post_id=post.post_id,
                    action=UserAction.HIDE,
                    timestamp=datetime.now().isoformat()
                )
                feed_manager.record_interaction(interaction)
                st.success("Post hidden 👻")
                st.rerun()

        # Reply interface
        if st.session_state.get(f"show_reply_{base_key}", False):
            reply_text = st.text_area("Your reply:", key=f"reply_text_{base_key}",
                                    placeholder="Share your thoughts on this post...")
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Send Reply", key=f"send_reply_{base_key}"):
                    if reply_text.strip():
                        # In a real implementation, this would add to the post's replies
                        st.success("Reply sent! 🎉")
                        st.session_state[f"show_reply_{base_key}"] = False
                        st.rerun()
            with col2:
                if st.button("Cancel", key=f"cancel_reply_{base_key}"):
                    st.session_state[f"show_reply_{base_key}"] = False
                    st.rerun()
        else:
            # For public users, show engagement metrics without interaction buttons
            col1, col2, col3 = st.columns([3, 3, 4])
            with col1:
                st.metric("❤️ Likes", post.likes)
            with col2:
                st.metric("🔄 Forwards", post.forwards)
            with col3:
                st.info("🔒 Log in to interact with posts")

        st.markdown("---")

def filter_posts_by_hashtag(posts, hashtag):
    """Filter posts by hashtag."""
    if not hashtag:
        return posts

    filtered_posts = []
    for post in posts:
        if post.hashtags and hashtag.lower() in [tag.lower() for tag in post.hashtags]:
            filtered_posts.append(post)

    return filtered_posts

def main():
    """Main application function."""

    # Check for hashtag filter in query params
    query_params = st.query_params
    selected_hashtag = query_params.get('tag', None)

    # Header
    st.title("🧠 AI Social Feed")
    if selected_hashtag:
        st.markdown(f"### *Showing posts tagged with #{selected_hashtag}*")
        if st.button("← Back to All Posts"):
            st.query_params.clear()
            st.rerun()
    else:
        st.markdown("### *Dopamine Drips and Gamma Ray Insights: An Improved Social Experience*")
    with st.expander("Here Comes The Science", expanded=True):
        # read markdown file from external package
        import pkg_resources
        try:
            content = pkg_resources.resource_string('social_server.modules', 'gamma_burst_insights.md').decode('utf-8')
            st.markdown(content)
        except Exception as e:
            st.error(f"Could not load science content: {e}")

    # Initialize everything
    persona_manager, feed_manager, feed_generator = init_managers()
    user_id = get_user_id()
    is_logged_in = user_id != "anonymous"

    # Show login status
    if is_logged_in:
        st.success(f"👤 Welcome, {user_id}")
    else:
        st.info("👋 Welcome! You're viewing the public feed. Log in for a personalized experience.")

    # Sidebar - Feed Controls
    with st.sidebar:
        st.header("🎛️ Feed Controls")

        if is_logged_in:
            # Generate new content (admin/logged-in users only)
            if st.button("🔄 Generate New Posts", use_container_width=True):
                with st.spinner("AI personas are crafting new posts..."):
                    try:
                        new_posts = feed_generator.generate_daily_feed(num_posts=10)
                        st.success(f"Generated {len(new_posts)} new posts!")
                        # Clear cache to force reload
                        st.cache_resource.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating posts: {e}")

            # Demo posts
            if st.button("📝 Load Sample Posts", use_container_width=True):
                with st.spinner("Loading sample posts..."):
                    try:
                        sample_posts = feed_generator.generate_sample_posts()
                        for post in sample_posts:
                            feed_manager.add_post(post)
                        st.success("Sample posts loaded!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error loading samples: {e}")

            st.markdown("---")
        else:
            st.info("🔒 Log in to access feed generation tools")
            st.markdown("---")

        # Feed preferences (logged-in users only)
        if is_logged_in:
            st.subheader("📊 Your Preferences")

            # Get user preferences
            user_prefs = feed_manager.preferences.get(user_id, FeedPreferences(user_id=user_id))

            # Three-factor neurobiological optimization
            st.subheader("🧬 Neurochemical Preferences")

            dopamine_weight = st.slider(
                "💕 Dopamine (Social Connection)",
                0.0, 1.0, user_prefs.engagement_weight,
                help="Oxytocin-dopamine pathways: community, relatability, emotional resonance"
            )

            breakthrough_weight = st.slider(
                "⚡ Breakthrough Buzz (Norepinephrine Rush)",
                0.0, 1.0, user_prefs.breakthrough_weight,
                help="Gamma-burst insights: aha-moments, pattern recognition, cognitive reorganization"
            )

            learning_weight = st.slider(
                "📖 Traditional Learning (Acetylcholine)",
                0.0, 1.0, user_prefs.learning_weight,
                help="Structured knowledge: facts, context, educational content"
            )

            # Normalize weights
            total_weight = dopamine_weight + breakthrough_weight + learning_weight
            if total_weight > 0:
                user_prefs.engagement_weight = dopamine_weight / total_weight
                user_prefs.breakthrough_weight = breakthrough_weight / total_weight
                user_prefs.learning_weight = learning_weight / total_weight

            # Update preferences
            feed_manager.update_user_preferences(user_id, user_prefs)

        # Personas section (always visible)
        st.subheader("🎭 AI Personas")
        all_personas = persona_manager.get_all_personas()

        for persona in all_personas[:5]:  # Show first 5
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"<div style='font-size: 1.5em;'>{persona.avatar_emoji}</div>",
                           unsafe_allow_html=True)
            with col2:
                st.markdown(f"**{persona.name}**")
                st.caption(persona.specialty)

        if len(all_personas) > 5:
            if st.button(f"View all {len(all_personas)} personas"):
                st.session_state['show_all_personas'] = True

    # Main feed area
    if is_logged_in:
        tab1, tab2, tab3, tab4 = st.tabs(["🏠 Your Feed", "🔥 Trending", "🧠 Learning", "🎭 Personas"])

        with tab1:
            st.subheader("Your Personalized Feed")

            # Get personalized feed
            feed_posts = feed_manager.get_personalized_feed(user_id, limit=20)
            # Apply hashtag filter if selected
            feed_posts = filter_posts_by_hashtag(feed_posts, selected_hashtag)
    else:
        tab1, tab2, tab3 = st.tabs(["🌍 Recent Posts", "🔥 Trending", "🎭 Personas"])

        with tab1:
            st.subheader("Recent Posts from AI Book-Lovers")

            # Get recent posts for public view
            feed_posts = feed_manager.get_recent_posts(limit=20)
            # Apply hashtag filter if selected
            feed_posts = filter_posts_by_hashtag(feed_posts, selected_hashtag)

        if not feed_posts:
            st.info("📭 No posts yet! Click 'Generate New Posts' or 'Load Sample Posts' to get started.")
        else:
            with st.expander("Feed Statistics"):
                # Debug: Check what's in the feed manager
                st.write(f"🔍 Total posts in feed manager: {len(feed_manager.posts)}")
                st.write(f"🔍 User feed posts: {len(feed_posts)}")

                if feed_posts:
                    st.write(f"🔍 First post content: {feed_posts[0].content[:100]}...")
                    st.write(f"🔍 First post persona: {feed_posts[0].persona_id}")

                st.markdown("---")

                # Display feed metrics with neurobiological focus
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    avg_engagement = sum(p.engagement_score for p in feed_posts) / len(feed_posts)
                    st.metric("💕 Dopamine", f"{avg_engagement:.1%}")
                with col2:
                    avg_breakthrough = sum(getattr(p, 'breakthrough_potential', 0) for p in feed_posts) / len(feed_posts)
                    st.metric("⚡ Norepinephrine", f"{avg_breakthrough:.1%}")
                with col3:
                    avg_learning = sum(p.learning_score for p in feed_posts) / len(feed_posts)
                    st.metric("📖 Acetylcholine", f"{avg_learning:.1%}")
                with col4:
                    st.metric("📝 Posts", len(feed_posts))

            # Display posts
            for i, post in enumerate(feed_posts):
                persona = persona_manager.get_persona(post.persona_id)
                if persona:
                    display_post(post, persona, feed_manager, user_id, f"feed_{i}", enable_interactions=is_logged_in)

    with tab2:
        st.subheader("🔥 Trending Posts")
        trending_posts = feed_manager.get_trending_posts(limit=10)
        # Apply hashtag filter if selected
        trending_posts = filter_posts_by_hashtag(trending_posts, selected_hashtag)

        if not trending_posts:
            st.info("🤷 No trending posts yet. Interact with posts to create trends!")
        else:
            for i, post in enumerate(trending_posts):
                persona = persona_manager.get_persona(post.persona_id)
                if persona:
                    display_post(post, persona, feed_manager, user_id, f"trending_{i}", enable_interactions=is_logged_in)

    # Learning tab only for logged-in users
    if is_logged_in:
        with tab3:
            st.subheader("🧠 Top Learning Posts")
            learning_posts = feed_manager.get_learning_highlights(limit=10)

            if not learning_posts:
                st.info("📚 No learning posts yet. Generate some AI content!")
            else:
                for i, post in enumerate(learning_posts):
                    persona = persona_manager.get_persona(post.persona_id)
                    if persona:
                        display_post(post, persona, feed_manager, user_id, f"learning_{i}", enable_interactions=is_logged_in)

        with tab4:
            st.subheader("🎭 Meet the AI Personas")
            display_persona_grid(persona_manager)
    else:
        with tab3:
            st.subheader("🎭 Meet the AI Personas")
            display_persona_grid(persona_manager)

    # Footer
    st.markdown("---")
    st.markdown("*Part of the AI Lab for Book-Lovers • Powered by Codexes Factory*")

if __name__ == "__main__":
    main()