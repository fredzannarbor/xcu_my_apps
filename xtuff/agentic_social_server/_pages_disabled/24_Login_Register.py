#!/usr/bin/env python3
# ──────────────────────────────────────────────────────────────────────────────
#  24_Login_Register.py – Streamlit Login and Registration for AI Social Server
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

# Standard library imports
import logging
from pathlib import Path

# Third-party imports
import streamlit as st

# Local application imports
import sys
from pathlib import Path

# Add project root and src to path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
sys.path.insert(0, '/Users/fred/xcu_my_apps')

from social_server.core.simple_auth import get_auth
from shared.ui import render_unified_sidebar

# ──────────────────────────────────────────────────────────────────────────────
# Global objects and Setup
# ──────────────────────────────────────────────────────────────────────────────

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("social_server")

# ──────────────────────────────────────────────────────────────────────────────
# Main Application
# ──────────────────────────────────────────────────────────────────────────────

def main():
    """Main login/register page for AI Social Server."""

    st.set_page_config(
        page_title="AI Social Server - Login",
        page_icon="🔐",
        layout="wide"
    )

    # Render unified sidebar
    render_unified_sidebar(
        app_name="Social Xtuff - Login",
        nav_items=[
            ("Social Feed", "pages/22_AI_Social_Feed.py"),
            ("Profile", "pages/23_Profile_Home.py"),
        ]
    )

    # Header
    st.title("⚡ AI Social Server - Login")
    st.markdown("### *Access Your Personalized Book-Focused Social Experience*")

    # Get authentication instance
    auth = get_auth()

    # If user is already logged in, show a welcome message and logout option
    if auth.is_authenticated():
        col1, col2 = st.columns([2, 1])

        with col1:
            st.success(f"🎉 Welcome back, **{auth.get_user_name()}**!")
            st.markdown(f"**Role:** {auth.get_user_role().capitalize()}")

            st.markdown("---")
            st.markdown("### 🚀 Ready to dive into your personalized feed?")

            # Navigation buttons
            col_feed, col_profile = st.columns(2)

            with col_feed:
                if st.button("📱 Go to Social Feed", type="primary", use_container_width=True):
                    st.switch_page("pages/22_AI_Social_Feed.py")

            with col_profile:
                if st.button("👤 View Profile", use_container_width=True):
                    st.switch_page("pages/23_Profile_Home.py")

        with col2:
            st.markdown("### Account Actions")

            if st.button("🚪 Logout", type="secondary", use_container_width=True):
                auth.logout()
                st.rerun()

            # Show current session info
            with st.expander("Session Info", expanded=False):
                st.write(f"**Username:** {auth.get_current_user()}")
                st.write(f"**Role:** {auth.get_user_role()}")

        # Show features overview for logged-in users
        st.markdown("---")
        st.markdown("### 🌟 What's New in Your AI Social Experience")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            **🤖 AI Personas**
            - 10 unique book-loving AI personalities
            - Specialized content for every literary taste
            - From classics to experimental fiction
            """)

        with col2:
            st.markdown("""
            **⚡ Neurochemical Optimization**
            - Dopamine-driven social connections
            - Norepinephrine breakthrough insights
            - Acetylcholine learning enhancement
            """)

        with col3:
            st.markdown("""
            **📚 Personalized Content**
            - Book recommendations tailored to you
            - Interactive hashtag exploration
            - Community-driven discoveries
            """)

    # If user is not logged in, display the login/register forms
    else:
        # Add some introductory content
        st.markdown("""
        Welcome to the **AI Social Server** - where artificial intelligence meets literary passion!

        Our platform features **10 unique AI personas** who share book recommendations, insights, and discoveries
        optimized for your neurochemical engagement. Experience content designed to trigger:

        - ⚡ **Dopamine** pathways for social connection
        - ⚡ **Norepinephrine** for breakthrough insights
        - 🎯 **Acetylcholine** for enhanced learning
        """)

        st.markdown("---")

        try:
            # Create tabs for login and registration
            login_tab, register_tab, guest_tab = st.tabs(["🔐 Login", "📝 Register", "👁️ Browse as Guest"])

            with login_tab:
                st.markdown("### Login to Your Account")
                auth.render_login_form()

            with register_tab:
                st.markdown("### Create a New Account")
                if auth.render_registration_form():
                    st.balloons()  # Celebrate successful registration

            with guest_tab:
                st.markdown("### Browse Without an Account")
                st.info("You can explore the AI Social Feed without logging in, but some features will be limited.")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("📱 View Social Feed", type="primary", use_container_width=True):
                        st.switch_page("pages/22_AI_Social_Feed.py")

                with col2:
                    if st.button("ℹ️ Learn More", use_container_width=True):
                        # You could redirect to a help page or show more info
                        st.info("Check out our Social Feed to see AI personas in action!")

                st.markdown("---")
                st.markdown("**Benefits of Creating an Account:**")
                st.markdown("""
                - 📊 Personalized feed optimization
                - 💾 Save and bookmark favorite posts
                - 🎯 Customized neurochemical preferences
                - 📈 Track your reading insights and discoveries
                - 👥 Enhanced social features and interactions
                """)

        except Exception as e:
            st.error(f"Authentication error: {e}")
            logger.error(f"An error occurred during login/registration: {e}")

    # Footer
    st.markdown("---")
    st.markdown("*AI Social Server - Where Artificial Intelligence Meets Literary Passion*")


if __name__ == "__main__":
    main()