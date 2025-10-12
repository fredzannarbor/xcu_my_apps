"""
Social Xtuff - Intelligent Social Media Experience

Delivers dopamine (social connection) and synaptic rush (learning) through
AI persona interactions focused on books, reading, and literary culture.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Optional
import sys
from pathlib import Path

# Add the project root to Python path for proper imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
sys.path.insert(0, '/Users/fred/xcu_my_apps')

try:
    from social_server.modules.ai_personas import AIPersonaManager
    from social_server.modules.generate_social_feed import SocialFeedManager, UserInteraction, UserAction, FeedPreferences, SocialFeedGenerator
    from social_server.core.paths import get_data_path
except ImportError:
    # Fallback for direct execution
    from src.social_server.modules.ai_personas import AIPersonaManager
    from src.social_server.modules.generate_social_feed import SocialFeedManager, UserInteraction, UserAction, FeedPreferences, SocialFeedGenerator
    from src.social_server.core.paths import get_data_path

# Try to use shared auth first, fall back to simple auth
try:
    from shared.auth import get_shared_auth, is_authenticated as shared_is_authenticated, get_user_info
    USE_SHARED_AUTH = True
except ImportError:
    try:
        from social_server.core.simple_auth import get_auth
        USE_SHARED_AUTH = False
    except ImportError:
        from src.social_server.core.simple_auth import get_auth
        USE_SHARED_AUTH = False

# Try to import unified sidebar, but use fallback if not available
try:
    from shared.ui import render_unified_sidebar
    HAS_UNIFIED_SIDEBAR = True
except ImportError:
    HAS_UNIFIED_SIDEBAR = False
    def render_unified_sidebar(*args, **kwargs):
        """Fallback when unified sidebar is not available."""
        pass

# Page configuration
st.set_page_config(
    page_title="Social Xtuff - Intelligent Social Media Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize managers
@st.cache_resource
def init_managers():
    """Initialize social media managers with caching."""
    persona_manager = AIPersonaManager()
    feed_manager = SocialFeedManager()
    feed_generator = SocialFeedGenerator()
    return persona_manager, feed_manager, feed_generator

def get_user_id():
    """Get current user ID from authentication system."""
    try:
        if USE_SHARED_AUTH:
            user_info = get_user_info()
            return user_info.get('username', 'anonymous') or 'anonymous'
        else:
            auth = get_auth()
            user_id = auth.get_current_user()
            return user_id or "anonymous"
    except:
        return "anonymous"

def display_neurochemical_allocator(feed_manager, user_id, is_logged_in, feed_generator=None, key_prefix="main"):
    """Display neurochemical factor allocation component that sums to 100%."""
    if not is_logged_in:
        return None

    # Get user preferences
    user_prefs = feed_manager.preferences.get(user_id, FeedPreferences(user_id=user_id))

    st.markdown("### ⚡ Control your neurochemical experience with social media ")
    st.markdown("**Allocate the effects you want to feel** - drag the sliders to set your perfect mix (must total 100%)")

    # Convert current weights to percentages
    current_dopamine = int(user_prefs.engagement_weight * 100)
    current_breakthrough = int(user_prefs.breakthrough_weight * 100)
    current_learning = int(user_prefs.learning_weight * 100)
    current_mood = int(user_prefs.mood_elevation_weight * 100)

    # Ensure they sum to 100 (handle rounding)
    total_current = current_dopamine + current_breakthrough + current_learning + current_mood
    if total_current != 100:
        current_dopamine += (100 - total_current)

    # Create columns for the allocation interface
    col1, col2 = st.columns([3, 1])

    with col1:
        # Use number inputs that auto-adjust to sum to 100
        dopamine_pct = st.number_input(
            "💕 Social Connection (Dopamine %)",
            min_value=0, max_value=100, value=current_dopamine,
            help="Emotional resonance, community feeling, shared experiences",
            key=f"{key_prefix}_dopamine"
        )

        breakthrough_pct = st.number_input(
            "⚡ Breakthrough Insights (Norepinephrine %)",
            min_value=0, max_value=100, value=current_breakthrough,
            help="Aha-moments, pattern recognition, gamma-burst insights",
            key=f"{key_prefix}_breakthrough"
        )

        learning_pct = st.number_input(
            "📖 Deep Learning (Acetylcholine %)",
            min_value=0, max_value=100, value=current_learning,
            help="Structured knowledge, facts, educational content",
            key=f"{key_prefix}_learning"
        )

        # Calculate mood automatically to ensure sum = 100
        mood_pct = 100 - (dopamine_pct + breakthrough_pct + learning_pct)
        mood_pct = max(0, mood_pct)  # Ensure non-negative

        st.number_input(
            "✨ Mood Elevation (Serotonin-Endorphin %)",
            min_value=0, max_value=100, value=mood_pct, disabled=True,
            help="Automatically calculated to make total = 100%",
            key=f"{key_prefix}_mood"
        )

    with col2:
        # Show current total and visual feedback
        total_pct = dopamine_pct + breakthrough_pct + learning_pct + mood_pct

        if total_pct == 100:
            st.success(f"✅ Total: {total_pct}%")
        else:
            st.error(f"❌ Total: {total_pct}%")
            st.caption("Must equal 100%")

        # Visual pie chart representation
        if total_pct > 0:
            chart_data = {
                "Factor": ["Social", "Insights", "Learning", "Mood"],
                "Percentage": [dopamine_pct, breakthrough_pct, learning_pct, mood_pct]
            }

            import pandas as pd
            df = pd.DataFrame(chart_data)
            st.bar_chart(df.set_index("Factor"))

    # Update preferences if valid
    if total_pct == 100:
        user_prefs.engagement_weight = dopamine_pct / 100.0
        user_prefs.breakthrough_weight = breakthrough_pct / 100.0
        user_prefs.learning_weight = learning_pct / 100.0
        user_prefs.mood_elevation_weight = mood_pct / 100.0

        # Update preferences in background
        feed_manager.update_user_preferences(user_id, user_prefs)


        return user_prefs

    return user_prefs

def display_feed_controls(feed_manager, user_id, feed_generator, key_prefix="main", is_anonymous=False):
    """Display feed controls for generating and managing posts."""
    if not feed_generator:
        st.info("Feed generator not available")
        return

    # Track anonymous user generation count
    if is_anonymous:
        if f'{key_prefix}_anon_gen_count' not in st.session_state:
            st.session_state[f'{key_prefix}_anon_gen_count'] = 0

        remaining_gens = max(0, 3 - st.session_state[f'{key_prefix}_anon_gen_count'])

        if remaining_gens > 0:
            st.info(f"🎁 You have **{remaining_gens}/3** free feed generations remaining. Sign up for unlimited access!")
        else:
            st.warning("⚠️ You've used all 3 free feed generations. Please sign up or log in for unlimited access.")
            return

    # Model selection for post generation
    st.markdown("**🤖 AI Model Selection**")
    model_options = [
        "Default (persona-specific)",
        "openai/gpt-4o",
        "anthropic/claude-3-5-sonnet-20241022",
        "anthropic/claude-3-5-haiku-20241022",
        "gemini/gemini-2.5-pro",
        "xai/grok-3-latest",
        "anthropic/claude-3-opus-20240229"
    ]

    selected_model = st.selectbox(
        "Choose AI model for post generation:",
        options=model_options,
        index=0,
        help="Override persona-specific models with a single model for all posts",
        key=f"{key_prefix}_model_select"
    )

    # Determine model override
    model_override = None if selected_model == "Default (persona-specific)" else selected_model

    # Number of posts to generate
    num_posts = st.number_input(
        "Number of posts to generate:",
        min_value=1,
        max_value=50,
        value=3,
        help="How many new posts to generate",
        key=f"{key_prefix}_num_posts"
    )

    # Auto-generation settings
    st.markdown("---")
    st.markdown("**⏰ Automatic Post Generation**")

    # Check for auto-generation state - default to ON
    auto_gen_key = f"{key_prefix}_auto_gen_enabled"
    if auto_gen_key not in st.session_state:
        st.session_state[auto_gen_key] = True  # Default to enabled

    auto_generate_options = ["🟢 ON (Generate posts every 6 hours)", "🔴 OFF (Manual generation only)"]
    current_index = 0 if st.session_state[auto_gen_key] else 1

    auto_generate_choice = st.radio(
        "Auto-generation:",
        auto_generate_options,
        index=current_index,
        help="Choose whether to automatically generate new posts every 6 hours",
        key=f"{key_prefix}_auto_radio"
    )

    auto_generate = auto_generate_choice.startswith("🟢 ON")

    if auto_generate != st.session_state[auto_gen_key]:
        st.session_state[auto_gen_key] = auto_generate
        if auto_generate:
            st.success("✅ Auto-generation enabled! Posts will be created every 6 hours.")
        else:
            st.info("🔴 Auto-generation disabled. Posts will only be created manually.")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Generate New Posts", use_container_width=True, key=f"{key_prefix}_generate_btn"):
            with st.spinner("AI personas are crafting new posts..."):
                try:
                    # Increment anonymous generation counter
                    if is_anonymous:
                        st.session_state[f'{key_prefix}_anon_gen_count'] += 1

                    # Create a new generator with model override if specified
                    if model_override:
                        from social_server.modules.generate_social_feed.feed_generator import FeedGenerator
                        custom_generator = FeedGenerator(model_override=model_override)
                        new_posts = custom_generator.generate_daily_feed(num_posts=num_posts)
                    else:
                        new_posts = feed_generator.generate_daily_feed(num_posts=num_posts)
                    st.success(f"Generated {len(new_posts)} new posts!")
                    # Clear cache to force reload
                    st.cache_resource.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating posts: {e}")

    with col2:
        if st.button("📝 Load Sample Posts", use_container_width=True, key=f"{key_prefix}_sample_btn"):
            with st.spinner("Loading sample posts..."):
                try:
                    sample_posts = feed_generator.generate_sample_posts()
                    for post in sample_posts:
                        feed_manager.add_post(post)
                    st.success("Sample posts loaded!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading samples: {e}")

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
    """Display all personas in a compact grid layout."""
    personas = persona_manager.get_all_personas()

    # Create a more compact grid layout with 3 columns
    cols_per_row = 3
    for i in range(0, len(personas), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(personas):
                persona = personas[i + j]
                with col:
                    with st.container():
                        st.markdown(
                            f"""
                            <div style='border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin-bottom: 12px; height: 280px; overflow: hidden;'>
                                <div style='text-align: center; font-size: 2.5em; margin-bottom: 8px;'>{persona.avatar_emoji}</div>
                                <h5 style='text-align: center; margin: 0 0 4px 0; font-size: 1.1em;'>{persona.name}</h5>
                                <p style='text-align: center; color: #666; margin: 0 0 8px 0; font-size: 0.85em;'>{persona.handle}</p>
                                <p style='font-size: 0.8em; margin: 8px 0; line-height: 1.3; overflow: hidden; text-overflow: ellipsis;'>{persona.bio[:80]}{'...' if len(persona.bio) > 80 else ''}</p>
                                <p style='font-size: 0.75em; margin: 4px 0;'><strong>Specialty:</strong> {persona.specialty}</p>
                                <p style='font-size: 0.75em; margin: 4px 0;'><strong>Style:</strong> {persona.writing_style[:60]}{'...' if len(persona.writing_style) > 60 else ''}</p>
                                <p style='font-size: 0.75em; margin: 4px 0;'><strong>Followers:</strong> {persona.follower_count:,}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

def display_post_ultra_compact(post, persona, feed_manager, user_id, unique_suffix="", enable_interactions=True):
    """Ultra-compact post display optimized for content scanning."""

    # Unique keys
    base_key = f"{post.post_id}_{unique_suffix}_{hash(post.timestamp) % 10000}"
    time_ago = datetime.fromisoformat(post.timestamp)

    # Check deleted persona
    is_deleted_persona = persona.persona_id.startswith("deleted_")

    # Get benefit text
    benefit_text = ""
    if hasattr(persona, 'neurochemical_benefit') and persona.neurochemical_benefit:
        benefit_text = f"• {persona.neurochemical_benefit}"

    # Build hashtags
    hashtags_text = ""
    if post.hashtags:
        hashtags_text = " ".join([f"#{tag}" for tag in post.hashtags])

    # Style for deleted personas
    persona_style = "text-decoration: line-through; opacity: 0.6;" if is_deleted_persona else ""

    # Ultra-compact HTML layout - everything in one block
    post_html = f"""
    <div style='border-bottom: 1px solid #eee; padding: 6px 0; margin: 0; font-size: 0.85em; line-height: 1.2;'>
        <div style='display: flex; align-items: flex-start; gap: 8px;'>
            <span style='font-size: 1.1em; min-width: 20px;'>{persona.avatar_emoji}</span>
            <div style='flex: 1; min-width: 0;'>
                <div style='margin-bottom: 2px;'>
                    <strong style='{persona_style}'>{persona.name}</strong>
                    <span style='color: #666; margin-left: 4px;'>{persona.handle}</span>
                    <span style='color: #999; margin-left: 6px; font-size: 0.8em;'>{time_ago.strftime('%I:%M %p')}</span>
                    <span style='color: #999; margin-left: 4px; font-size: 0.8em;'>{post.post_type.value.replace('_', ' ').title()}</span>
                    <span style='color: #007acc; margin-left: 6px; font-size: 0.75em; font-weight: 500;'>via {getattr(post, 'generated_by_model', 'unknown')}</span>
                    <span style='color: #888; margin-left: 6px; font-size: 0.75em;'>{benefit_text}</span>
                </div>
                <div style='margin: 2px 0; line-height: 1.3; font-size: 1.05em;'>{post.content}</div>
                <div style='margin-top: 2px; display: flex; align-items: center; gap: 8px; font-size: 0.8em; color: #666;'>
                    <span style='color: #1DA1F2;'>{hashtags_text}</span>
                    <span>❤️{post.likes}</span>
                    <span>🔄{post.forwards}</span>
                    <span style='cursor: pointer; color: #999;' title='Actions'>⚡</span>
                </div>
            </div>
        </div>
    </div>
    """

    st.markdown(post_html, unsafe_allow_html=True)

    # Add horizontal rule

    # Actions in collapsible expander (one click away) - indented to align with post text
    if enable_interactions:
        # Create container with columns to indent the expander
        col1, col2 = st.columns([28, 1000])  # 28px for emoji + gap, rest for content
        with col1:
            st.empty()  # Empty space for alignment
        with col2:
            with st.expander("⚡ Actions", expanded=False):
                col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])

                with col1:
                    if st.button(f"❤️ Like ({post.likes})", key=f"like_{base_key}"):
                        interaction = UserInteraction(
                            user_id=user_id, post_id=post.post_id, action=UserAction.LIKE, timestamp=datetime.now().isoformat()
                        )
                        feed_manager.record_interaction(interaction)
                        st.success("Liked! 💕")
                        st.rerun()

                with col2:
                    if st.button(f"🔄 Forward ({post.forwards})", key=f"forward_{base_key}"):
                        interaction = UserInteraction(
                            user_id=user_id, post_id=post.post_id, action=UserAction.FORWARD, timestamp=datetime.now().isoformat()
                        )
                        feed_manager.record_interaction(interaction)
                        st.success("Forwarded! 🚀")
                        st.rerun()

                with col3:
                    if st.button("💬 Reply", key=f"reply_{base_key}"):
                        st.session_state[f"show_reply_{base_key}"] = True

                with col4:
                    if st.button("🔖 Save", key=f"save_{base_key}"):
                        interaction = UserInteraction(
                            user_id=user_id, post_id=post.post_id, action=UserAction.BOOKMARK, timestamp=datetime.now().isoformat()
                        )
                        feed_manager.record_interaction(interaction)
                        st.success("Bookmarked! 📚")

                with col5:
                    if st.button("🙈 Hide", key=f"hide_{base_key}"):
                        interaction = UserInteraction(
                            user_id=user_id, post_id=post.post_id, action=UserAction.HIDE, timestamp=datetime.now().isoformat()
                        )
                        try:
                            feed_manager.record_interaction(interaction)
                            st.success("Post hidden 👻")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to hide post: {e}")

                with col6:
                    # More info button
                    has_extra_content = (post.breakthrough_triggers or post.prediction_violations or
                                       post.pattern_bridges or post.learning_nuggets or post.book_references)
                    if has_extra_content:
                        if st.button("ℹ️ More info", key=f"info_{base_key}"):
                            show_more_info_popup(post)

                # Reply interface
                if st.session_state.get(f"show_reply_{base_key}", False):
                    reply_text = st.text_area("Your reply:", key=f"reply_text_{base_key}",
                                            placeholder="Share your thoughts on this post...")
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("Send Reply", key=f"send_reply_{base_key}"):
                            if reply_text.strip():
                                st.success("Reply sent! 🎉")
                                st.session_state[f"show_reply_{base_key}"] = False
                                st.rerun()
                    with col2:
                        if st.button("Cancel", key=f"cancel_reply_{base_key}"):
                            st.session_state[f"show_reply_{base_key}"] = False
                            st.rerun()

def display_personas_tab(persona_manager, feed_manager, user_id):
    """Display AI Personas tab with follow/unfollow functionality."""
    all_personas = persona_manager.get_all_personas()

    # Get user's followed personas (if implemented in feed_manager)
    followed_personas = getattr(feed_manager, 'get_followed_personas', lambda x: [])(user_id)

    # Create enhanced table data with follow buttons
    persona_data = []
    for persona in all_personas:
        is_followed = persona.persona_id in followed_personas
        follow_status = "✅ Following" if is_followed else "➕ Follow"

        persona_data.append({
            "Avatar": persona.avatar_emoji,
            "Name": persona.name,
            "Specialty": persona.specialty,
            "Following": follow_status
        })

    # Display as table
    if persona_data:
        import pandas as pd
        df = pd.DataFrame(persona_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Add follow/unfollow buttons below
        st.markdown("### Manage Following")
        cols = st.columns(min(3, len(all_personas)))
        for i, persona in enumerate(all_personas):
            with cols[i % 3]:
                is_followed = persona.persona_id in followed_personas
                if is_followed:
                    if st.button(f"Unfollow {persona.name}", key=f"unfollow_{persona.persona_id}"):
                        # Unfollow persona logic (to be implemented)
                        st.success(f"Unfollowed {persona.name}")
                        st.rerun()
                else:
                    if st.button(f"Follow {persona.name}", key=f"follow_{persona.persona_id}"):
                        # Follow persona logic (to be implemented)
                        st.success(f"Now following {persona.name}")
                        st.rerun()

@st.dialog("Persona Profile")
def show_persona_profile_popup(persona, post):
    """Show persona profile information in a popup dialog."""
    # Check if this is a deleted persona
    if persona.persona_id.startswith("deleted_"):
        st.error("🚫 This AI persona is no longer available.")
        st.markdown("This user's profile has been removed or is temporarily unavailable. Their posts remain visible for historical context.")
        return

    # Show regular persona profile
    st.markdown(f"## {persona.avatar_emoji} {persona.name}")
    st.markdown(f"**Handle:** {persona.handle}")
    st.markdown(f"**Bio:** {persona.bio}")
    st.markdown(f"**Specialty:** {persona.specialty}")

    if persona.personality_traits:
        st.markdown(f"**Personality:** {', '.join(persona.personality_traits)}")

    if persona.interests:
        st.markdown("**Interests:**")
        for interest in persona.interests[:5]:  # Limit to first 5 interests
            st.markdown(f"• {interest}")

    if persona.writing_style:
        st.markdown(f"**Writing Style:** {persona.writing_style}")

    st.markdown(f"**Followers:** {persona.follower_count:,}")

@st.dialog("More Information")
def show_more_info_popup(post):
    """Show additional post information in a popup dialog."""

    # Breakthrough buzz triggers
    if post.breakthrough_triggers or post.prediction_violations or post.pattern_bridges:
        st.subheader("⚡ Breakthrough Buzz")
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
        st.markdown("---")

    # Learning content
    if post.learning_nuggets:
        st.subheader("📖 Learning Insights")
        for nugget in post.learning_nuggets:
            st.markdown(f"• {nugget}")
        st.markdown("---")

    # Book references
    if post.book_references:
        st.subheader("📚 Book References")
        for book_ref in post.book_references:
            st.markdown(f"**{book_ref.get('title', 'Unknown Title')}** by {book_ref.get('author', 'Unknown Author')}")
            if 'context' in book_ref:
                st.caption(book_ref['context'])

@st.dialog("✍️ Submit Your Text to AI Persona")
def show_user_post_request_popup(persona_manager):
    """Show popup for users to submit text to AI personas."""
    import requests
    import json

    st.markdown("### Transform your text into engaging social media content!")
    st.markdown("Paste any text, URL, or idea and let our AI personas transform it into their unique voice.")

    # Get all personas for selection
    personas = persona_manager.get_all_personas()

    # Persona selection
    persona_options = {}
    for persona in personas:
        display_name = f"{persona.avatar_emoji} {persona.name} - {persona.specialty}"
        persona_options[display_name] = persona.persona_id

    selected_persona_display = st.selectbox(
        "Choose AI Persona:",
        options=list(persona_options.keys()),
        help="Each persona will transform your text in their unique voice and style"
    )

    selected_persona_id = persona_options[selected_persona_display]
    selected_persona = persona_manager.get_persona(selected_persona_id)

    # Show persona info
    if selected_persona:
        st.info(f"**{selected_persona.name}**: {selected_persona.bio}")

    # Text input
    user_text = st.text_area(
        "Your text:",
        height=150,
        placeholder="Paste text, article content, URLs, or any ideas you'd like transformed...",
        help="URLs will be automatically detected and preserved in the output"
    )

    # Model selection (optional)
    with st.expander("⚙️ Advanced Options", expanded=False):
        model_options = [
            "Default (persona-specific)",
            "gemini/gemini-2.5-pro",
            "openai/gpt-4o",
            "anthropic/claude-3-5-sonnet-20241022",
            "anthropic/claude-3-5-haiku-20241022"
        ]

        selected_model = st.selectbox(
            "AI Model:",
            options=model_options,
            index=0,
            help="Override the persona's default model"
        )

        preserve_urls = st.checkbox(
            "Auto-detect and preserve URLs",
            value=True,
            help="Automatically detect URLs in your text and preserve them unchanged"
        )

    # Submit button
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("🚀 Transform Text", use_container_width=True, type="primary"):
            if not user_text.strip():
                st.error("Please enter some text to transform!")
                return

            with st.spinner(f"🤖 {selected_persona.name} is transforming your text..."):
                try:
                    # Prepare API request
                    api_data = {
                        "text": user_text,
                        "persona_id": selected_persona_id,
                        "user_id": st.session_state.get('user_id', 'anonymous'),
                        "preserve_urls": preserve_urls
                    }

                    # Add model override if not default
                    if selected_model != "Default (persona-specific)":
                        api_data["model_override"] = selected_model

                    # Call the local API
                    response = requests.post(
                        "http://localhost:59312/submit",
                        json=api_data,
                        timeout=60
                    )

                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            st.success("✅ Text transformed successfully!")

                            # Show the generated content
                            st.markdown("### 📝 Generated Post:")
                            st.markdown(f"**By {result.get('persona_name', 'AI Persona')}**")
                            st.markdown(result.get('content', ''))

                            if result.get('detected_urls'):
                                st.info(f"🔗 Preserved {len(result['detected_urls'])} URL(s): {', '.join(result['detected_urls'])}")

                            st.caption(f"Generated using: {result.get('generated_by_model', 'unknown model')}")
                            st.success("🎉 Post has been added to your feed!")

                        else:
                            st.error(f"❌ Generation failed: {result.get('error_message', 'Unknown error')}")
                    else:
                        st.error(f"❌ API request failed: {response.status_code}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to API server. Please ensure the API server is running on port 8502.")
                except requests.exceptions.Timeout:
                    st.error("❌ Request timed out. The AI might be taking longer than usual.")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state['show_user_post_request'] = False
            st.rerun()

def filter_posts_by_hashtag(posts, hashtag):
    """Filter posts by hashtag."""
    if not hashtag:
        return posts

    filtered_posts = []
    for post in posts:
        if post.hashtags and hashtag.lower() in [tag.lower() for tag in post.hashtags]:
            filtered_posts.append(post)

    return filtered_posts

def check_auto_generation(feed_manager, feed_generator):
    """Check if automatic post generation should run."""
    import time

    # Initialize auto-generation state
    if 'last_auto_gen' not in st.session_state:
        st.session_state.last_auto_gen = 0

    if 'main_auto_gen_enabled' not in st.session_state:
        st.session_state.main_auto_gen_enabled = False

    # Check if auto-generation is enabled
    if not st.session_state.main_auto_gen_enabled:
        return

    # Check if 6 hours have passed (21600 seconds)
    current_time = time.time()
    if current_time - st.session_state.last_auto_gen >= 21600:  # 6 hours
        try:
            # Generate 3 new posts automatically
            new_posts = feed_generator.generate_daily_feed(num_posts=3)
            st.session_state.last_auto_gen = current_time

            # Show notification
            with st.expander("🤖 Auto-Generated Posts", expanded=True):
                st.success(f"🎉 Auto-generated {len(new_posts)} new posts!")
                st.caption(f"Next auto-generation in 6 hours at {datetime.fromtimestamp(current_time + 21600).strftime('%H:%M')}")

            # Force UI refresh
            st.cache_resource.clear()

        except Exception as e:
            st.error(f"Auto-generation failed: {e}")

def main():
    """Main application function."""

    # Render unified sidebar (if available) or fallback auth sidebar
    if HAS_UNIFIED_SIDEBAR:
        render_unified_sidebar(
            app_name="Social Xtuff",
            nav_items=[],  # No nav items - app uses tabs instead
            show_auth=True,
            show_xtuff_nav=True
        )
    else:
        # Simple fallback auth sidebar
        with st.sidebar:
            st.title("⚡ Social Xtuff")
            st.markdown("---")
            try:
                if USE_SHARED_AUTH:
                    # Use shared auth system
                    if shared_is_authenticated():
                        user_info = get_user_info()
                        st.success(f"👤 **{user_info.get('user_name', 'User')}**")
                        st.caption(f"📧 {user_info.get('user_email', '')}")
                        st.caption(f"🎭 {user_info.get('user_role', 'user').capitalize()}")
                        if st.button("🚪 Logout"):
                            from shared.auth import logout
                            logout()
                            st.rerun()
                    else:
                        st.info("👋 Not logged in")
                        st.caption("Log in via main app at :8500")
                else:
                    # Use local simple auth
                    auth = get_auth()
                    if auth.is_authenticated():
                        auth.render_user_info()
                        if st.button("🚪 Logout"):
                            auth.logout()
                            st.rerun()
                    else:
                        st.info("👋 Not logged in")
                        if st.button("🔐 Login/Register"):
                            st.switch_page("pages/24_Login_Register.py")
            except Exception as e:
                st.error(f"⚠️ Authentication system error: {e}")
                st.caption("Using public mode")

    # Check for hashtag filter in query params
    query_params = st.query_params
    selected_hashtag = query_params.get('tag', None)
    # Header
    st.title("⚡ Social Xtuff")
    if selected_hashtag:
        st.markdown(f"### *Showing posts tagged with #{selected_hashtag}*")
        if st.button("← Back to All Posts"):
            st.query_params.clear()
            st.rerun()
    else:
        st.markdown("### *Take Control of Your Brain Chemistry: Customize Your Perfect Social Experience*")
        st.markdown("⚡ **You decide** what your feed optimizes for - whether you want dopamine hits from social connection, breakthrough insights that trigger those 'aha!' moments, deep learning experiences, or mood-boosting content that makes you smile. **Your neurochemistry, your choice.**")
    with st.expander("Here Comes The Science", expanded=False):
        # read markdown file
        try:
            gamma_burst_file = get_data_path("src/social_server/modules/gamma_burst_insights.md")
            with open(gamma_burst_file, "r") as f:
                st.markdown(f.read())
        except FileNotFoundError:
            st.markdown("*Gamma burst insights documentation not found.*")

    # Initialize everything
    persona_manager, feed_manager, feed_generator = init_managers()

    # Try to get auth, but use fallback if it fails
    auth = None
    try:
        if USE_SHARED_AUTH:
            auth = get_shared_auth()
        else:
            auth = get_auth()
    except Exception as e:
        st.warning(f"⚠️ Authentication system unavailable: {e}")
        auth = None

    user_id = get_user_id()

    # Check for automatic post generation
    check_auto_generation(feed_manager, feed_generator)

    # More robust authentication check
    if USE_SHARED_AUTH:
        is_logged_in = shared_is_authenticated() and user_id != "anonymous"
    else:
        is_logged_in = (auth and auth.is_authenticated() or user_id != "anonymous") and user_id is not None

    if is_logged_in:
        st.success(f"👤 Welcome, {user_id}")
    else:
        st.info("👋 Welcome! You're viewing the public feed. Log in for a personalized experience.")

    # Sidebar content is now handled by unified sidebar



    # Main feed area
    if is_logged_in:
        # Add neurochemical allocator at the top of the feed
        with st.expander("⚡ Neurochemical Controls", expanded=False):
            display_neurochemical_allocator(feed_manager, user_id, is_logged_in, None, key_prefix="main")

        # Transform Text in its own expander
        with st.expander("✍️ Transform Your Text", expanded=False):
            st.markdown("**Submit your text to AI personas for transformation into engaging social media posts**")

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("✍️ Submit Your Text to AI Persona", use_container_width=True, type="primary"):
                    st.session_state['show_user_post_request'] = True

        # Show user post request popup if triggered
        if st.session_state.get('show_user_post_request', False):
            show_user_post_request_popup(persona_manager)

        # Add feed controls in separate expander
        with st.expander("🎛️ Feed Controls", expanded=False):
            display_feed_controls(feed_manager, user_id, feed_generator, key_prefix="main")

        st.markdown("---")

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🌍 All Posts", "🏠 Your Feed", "🔥 Trending", "⚡ Learning", "⚙️ Settings", "🎭 AI Personas"])

        with tab1:
            st.subheader("All Posts")

            # Get all posts for authenticated users (filtered by hidden posts)
            all_posts = feed_manager.get_all_posts_for_user(user_id, limit=50)
            # Apply hashtag filter if selected
            all_posts = filter_posts_by_hashtag(all_posts, selected_hashtag)

            # Display All Posts
            display_feed_posts(all_posts, persona_manager, feed_manager, user_id, "all_posts", is_logged_in)

        with tab2:
            st.subheader("Your Personalized Feed")

            # Get personalized feed
            feed_posts = feed_manager.get_personalized_feed(user_id, limit=20)
            # Apply hashtag filter if selected
            feed_posts = filter_posts_by_hashtag(feed_posts, selected_hashtag)

            # Display Your Feed posts
            display_feed_posts(feed_posts, persona_manager, feed_manager, user_id, "your_feed", is_logged_in)

        with tab3:
            st.subheader("🔥 Trending Posts")
            trending_posts = feed_manager.get_trending_posts(limit=10)
            # Apply hashtag filter if selected
            trending_posts = filter_posts_by_hashtag(trending_posts, selected_hashtag)

            display_feed_posts(trending_posts, persona_manager, feed_manager, user_id, "trending", is_logged_in)

        with tab4:
            st.subheader("⚡ Learning Posts")
            # Get posts with high learning scores
            learning_posts = [p for p in feed_manager.get_recent_posts(limit=30) if p.learning_score > 0.7]
            learning_posts = filter_posts_by_hashtag(learning_posts, selected_hashtag)

            display_feed_posts(learning_posts, persona_manager, feed_manager, user_id, "learning", is_logged_in)

        with tab5:
            st.subheader("⚙️ Settings")
            display_user_settings(feed_manager, user_id)

            # Admin testing section for deleted persona handling
            if st.checkbox("🔧 Admin Testing Mode"):
                st.markdown("### Test Deleted Persona Handling")
                st.info("This section allows testing the deleted persona functionality.")

                all_personas = persona_manager.get_all_personas()
                if all_personas:
                    persona_to_test = st.selectbox("Select persona to simulate deletion:",
                                                  options=[p.persona_id for p in all_personas],
                                                  format_func=lambda x: f"{persona_manager.get_persona(x).name} ({x})")

                    if st.button("🗑️ Temporarily Remove Persona (for testing)"):
                        # Temporarily remove the persona from memory (not from file)
                        if persona_to_test in persona_manager.personas:
                            del persona_manager.personas[persona_to_test]
                            st.success(f"Temporarily removed {persona_to_test} from memory. Posts will now show as deleted persona.")
                            st.info("To restore, restart the app.")
                            st.rerun()

                if st.button("🔄 Reload Personas"):
                    persona_manager._load_personas()
                    st.success("Personas reloaded from storage.")
                    st.rerun()

        with tab6:
            st.subheader("🎭 AI Personas")
            display_personas_tab(persona_manager, feed_manager, user_id)

    else:
        # Add limited feed controls for anonymous users
        with st.expander("🎛️ Try Our AI Feed Generator (Limited Free Access)", expanded=False):
            st.markdown("**Generate your own AI-powered feed!** You get 3 free feed generations to explore.")
            display_feed_controls(feed_manager, user_id, feed_generator, key_prefix="anon", is_anonymous=True)

        st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["🌍 Recent Posts", "🔥 Trending", "🎭 AI Personas"])

        with tab1:
            st.subheader("Recent Posts from AI Book-Lovers")

            # Get recent posts for public view
            feed_posts = feed_manager.get_recent_posts(limit=20)
            # Apply hashtag filter if selected
            feed_posts = filter_posts_by_hashtag(feed_posts, selected_hashtag)

            display_feed_posts(feed_posts, persona_manager, feed_manager, user_id, "public_feed", is_logged_in)

        with tab2:
            st.subheader("🔥 Trending Posts")
            trending_posts = feed_manager.get_trending_posts(limit=10)
            # Apply hashtag filter if selected
            trending_posts = filter_posts_by_hashtag(trending_posts, selected_hashtag)

            display_feed_posts(trending_posts, persona_manager, feed_manager, user_id, "public_trending", is_logged_in)

        with tab3:
            st.subheader("🎭 AI Personas")
            display_personas_tab(persona_manager, feed_manager, user_id if is_logged_in else None)

def display_feed_posts(feed_posts, persona_manager, feed_manager, user_id, section_key, enable_interactions):
    """Display a list of feed posts with statistics and interactions."""
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
                st.metric("💕 Social Connection", f"{avg_engagement:.1%}")
            with col2:
                avg_breakthrough = sum(getattr(p, 'breakthrough_potential', 0) for p in feed_posts) / len(feed_posts)
                st.metric("⚡ Breakthrough Buzz", f"{avg_breakthrough:.1%}")
            with col3:
                avg_learning = sum(p.learning_score for p in feed_posts) / len(feed_posts)
                st.metric("📖 Traditional Learning", f"{avg_learning:.1%}")
            with col4:
                st.metric("📝 Posts", len(feed_posts))

        # Display posts
        for i, post in enumerate(feed_posts):
            persona = persona_manager.get_persona_or_deleted(post.persona_id)
            display_post_ultra_compact(post, persona, feed_manager, user_id, f"{section_key}_{i}", enable_interactions=enable_interactions)

def display_user_settings(feed_manager, user_id):
    """Display user settings in the Settings tab."""
    st.markdown("### ⚙️ Neurochemical Preferences")
    st.info("💡 **Tip:** You can also adjust these settings in the main feed area above!")

    # Use the same neurochemical allocator component
    display_neurochemical_allocator(feed_manager, user_id, True, key_prefix="settings")

    # Footer
    st.markdown("---")
    st.markdown("*Intelligent Social Media Platform • Powered by Xtuff.ai*")

if __name__ == "__main__":
    main()