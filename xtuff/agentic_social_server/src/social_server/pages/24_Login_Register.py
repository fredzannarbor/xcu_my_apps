#!/usr/bin/env python3
# ──────────────────────────────────────────────────────────────────────────────
#  24_Login_Register.py – Streamlit Login and Registration for Social Xtuff
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

# Standard library imports
import logging
import sys
from pathlib import Path

# Add monorepo root for shared imports
sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Import shared authentication and UI
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout, register_user as shared_register
    from shared.ui import render_unified_sidebar
except ImportError as e:
    import streamlit as st
    st.error(f"Failed to import shared authentication: {e}")
    st.stop()

# Third-party imports
import streamlit as st

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
    """
version 1.1.0 - Migrated to shared authentication system
Main login/register page for Social Xtuff."""

    st.set_page_config(
        page_title="Social Xtuff - Login",
        page_icon="⚡",
        layout="wide"
    )


# Hide native Streamlit navigation
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

# Render unified sidebar
render_unified_sidebar(
    app_name="Social Server",
    show_auth=True,
    show_xtuff_nav=True
)

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


    # Header
    st.title("⚡ Social Xtuff - Login")
    st.markdown("### *Access Your Personalized Book-Focused Social Experience*")

    # Get authentication instance
    # Shared auth initialized in header

    # If user is already logged in, show a welcome message and logout option
    if is_authenticated():
        col1, col2 = st.columns([2, 1])

        with col1:
            user_info = get_user_info()
            st.success(f"🎉 Welcome back, **{user_info.get('user_name', user_info.get('username'))}**!")
            st.markdown(f"**Role:** {user_info.get('user_role', 'user').capitalize()}")

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
                shared_logout()
                st.rerun()

            # Show current session info
            with st.expander("Session Info", expanded=False):
                user_info = get_user_info()
                st.write(f"**Username:** {user_info.get('username')}")
                st.write(f"**Role:** {user_info.get('user_role', 'user')}")

        # Show features overview for logged-in users
        st.markdown("---")
        st.markdown("### 🌟 What's New in Your Social Xtuff Experience")

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
        Welcome to **Social Xtuff** - where artificial intelligence meets intelligent social interaction!

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

                with st.form("login_form"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    submit = st.form_submit_button("Login", use_container_width=True)

                    if submit:
                        success, message = shared_authenticate(username, password)
                        if success:
                            st.success(message)
                            logger.info(f"User logged in: {username}")
                            st.rerun()
                        else:
                            st.error(message)

            with register_tab:
                st.markdown("### Create a New Account")

                with st.form("register_form"):
                    new_username = st.text_input("Username", key="reg_username")
                    new_email = st.text_input("Email", key="reg_email")
                    new_name = st.text_input("Full Name", key="reg_name")
                    new_password = st.text_input("Password", type="password", key="reg_password")
                    confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
                    register_submit = st.form_submit_button("Register", use_container_width=True)

                    if register_submit:
                        if new_password != confirm_password:
                            st.error("Passwords do not match")
                        elif len(new_password) < 6:
                            st.error("Password must be at least 6 characters")
                        else:
                            if shared_register(new_username, new_password, new_email, new_name):
                                st.success("Registration successful! Please login.")
                                st.balloons()
                                logger.info(f"New user registered: {new_username}")
                            else:
                                st.error("Username already exists")

            with guest_tab:
                st.markdown("### Browse Without an Account")
                st.info("You can explore Social Xtuff without logging in, but some features will be limited.")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("📱 View Social Feed", type="primary", use_container_width=True):
                        st.switch_page("pages/22_AI_Social_Feed.py")

                with col2:
                    if st.button("ℹ️ Learn More", use_container_width=True):
                        # You could redirect to a help page or show more info
                        st.info("Check out Social Xtuff to see AI personas in action!")

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
    st.markdown("*Social Xtuff - Intelligent Social Media Platform*")


if __name__ == "__main__":
    main()