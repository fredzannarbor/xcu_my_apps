#!/usr/bin/env python3
"""
Authentication Integration for Unified App Runner

UPDATED: Now uses shared authentication system for true SSO across all apps.
Replaces streamlit-authenticator with shared.auth system.
"""

import streamlit as st
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate, logout
except ImportError as e:
    logging.error(f"Failed to import shared auth: {e}")
    raise ImportError(
        "Shared authentication module not found. "
        "Ensure /Users/fred/xcu_my_apps/shared/auth is accessible."
    )

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages authentication using the shared auth system for SSO across all apps."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the AuthManager with shared auth system."""
        # config_path parameter kept for backward compatibility but not used
        # Shared auth uses its own config at /nimble/codexes-factory/resources/yaml/config.yaml

        self.shared_auth = get_shared_auth()
        logger.info("AuthManager initialized with shared authentication system")

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get the currently authenticated user from shared auth session."""
        if not is_authenticated():
            return None

        user_info = get_user_info()

        return {
            "name": user_info.get("user_name", "Unknown"),
            "email": user_info.get("user_email", ""),
            "role": user_info.get("user_role", "user"),
            "username": user_info.get("username", ""),
            "subscription_tier": user_info.get("subscription_tier", "free"),
            "subscription_status": user_info.get("subscription_status", "inactive"),
            "app_access": []  # Placeholder for future implementation
        }

    def get_user_role(self) -> str:
        """Get the role of the currently authenticated user."""
        if not is_authenticated():
            return "anonymous"

        user_info = get_user_info()
        return user_info.get("user_role", "user")

    def get_user_subscription_tier(self) -> str:
        """Get the subscription tier of the currently authenticated user."""
        if not is_authenticated():
            return "free"

        user_info = get_user_info()
        return user_info.get("subscription_tier", "free")

    def has_app_access(self, org_id: str) -> bool:
        """Check if user has access to apps from a specific organization."""
        user = self.get_current_user()
        if not user:
            return False

        # Admin always has access
        if user.get("role") in ["admin", "superadmin"]:
            return True

        # For now, all authenticated users have access to all orgs
        # TODO: Implement app_access restrictions from config
        return True

    def has_access(self, required_auth_level: str) -> bool:
        """Check if the current user has access to the required auth level."""
        if required_auth_level == "public":
            return True

        user_role = self.get_user_role()

        # Define role hierarchy
        role_hierarchy = {
            "anonymous": 0,
            "public": 0,
            "user": 1,
            "registered": 1,
            "subscriber": 2,
            "admin": 3,
            "superadmin": 4
        }

        required_level_map = {
            "public": 0,
            "anonymous": 0,
            "user": 1,
            "registered": 1,
            "subscriber": 2,
            "admin": 3,
            "superadmin": 4
        }

        user_level = role_hierarchy.get(user_role, 0)
        required_level = required_level_map.get(required_auth_level, 4)

        return user_level >= required_level

    def render_login_widget(self, location: str = "sidebar"):
        """Render the login widget using shared auth system."""

        if location == "sidebar":
            container = st.sidebar
        else:
            container = st

        if not is_authenticated():
            # Show tabbed interface for Login vs Create Account inside collapsed expander
            with container.expander("🔐 Login / Create Account", expanded=False):
                tab1, tab2 = st.tabs(["Login", "Create Account"])

                # Login Tab
                with tab1:
                    with st.form("shared_auth_login_form"):
                        username = st.text_input("Username", key="auth_username")
                        password = st.text_input("Password", type="password", key="auth_password")
                        submit = st.form_submit_button("Login", type="primary")

                        if submit:
                            if username and password:
                                success, message = authenticate(username, password)
                                if success:
                                    st.success(message)
                                    logger.info(f"User {username} logged in successfully")
                                    st.rerun()
                                else:
                                    st.error(message)
                                    logger.warning(f"Failed login attempt for user {username}")
                            else:
                                st.error("Please enter both username and password")

                # Create Account Tab
                with tab2:
                    with st.form("shared_auth_register_form"):
                        new_name = st.text_input("Full Name", key="auth_reg_name")
                        new_email = st.text_input("Email", key="auth_reg_email")
                        new_username = st.text_input("Username", key="auth_reg_username")
                        new_password = st.text_input("Password", type="password", key="auth_reg_password")
                        new_password_confirm = st.text_input("Confirm Password", type="password", key="auth_reg_password_confirm")
                        submit_reg = st.form_submit_button("Create Account", type="primary")

                        if submit_reg:
                            if not all([new_name, new_email, new_username, new_password, new_password_confirm]):
                                st.error("Please fill in all fields")
                            elif new_password != new_password_confirm:
                                st.error("Passwords do not match")
                            elif len(new_password) < 8:
                                st.error("Password must be at least 8 characters")
                            else:
                                # Try to register user through shared auth
                                try:
                                    # Use the shared auth system to register
                                    auth_system = self.shared_auth

                                    # Call register_user if available
                                    if hasattr(auth_system, 'register_user'):
                                        success = auth_system.register_user(
                                            username=new_username,
                                            password=new_password,
                                            email=new_email,
                                            name=new_name
                                        )
                                        if success:
                                            st.success(f"✅ Account created! You can now login as '{new_username}'")
                                            logger.info(f"New user registered: {new_username}")
                                        else:
                                            st.error("Username or email already exists")
                                    else:
                                        # Fallback: add user directly to config if register_user not available
                                        st.error("Registration temporarily unavailable. Please contact support.")
                                        logger.error("register_user method not found in shared auth system")
                                except Exception as e:
                                    st.error(f"Registration failed: {str(e)}")
                                    logger.error(f"Registration error: {e}")

        else:
            # User is authenticated - show user info
            user_info = get_user_info()

            if location == "sidebar":
                container.success(f"👤 **{user_info.get('user_name', 'User')}**")
                container.caption(f"📧 {user_info.get('user_email', '')}")
                container.caption(f"🎭 {user_info.get('user_role', 'user').capitalize()}")

                # Subscription info
                sub_tier = user_info.get('subscription_tier', 'free')
                if sub_tier and sub_tier != 'free':
                    container.info(f"💎 {sub_tier.capitalize()} Tier")

    def logout(self):
        """Log out the current user from shared auth system."""
        username = st.session_state.get('username', 'unknown')
        logout()
        logger.info(f"User {username} logged out")

    def render_auth_check(self, required_auth_level: str) -> bool:
        """Render authentication check UI and return if user has access."""
        if required_auth_level == "public":
            return True

        if self.has_access(required_auth_level):
            return True

        # Show login prompt
        st.warning(f"⚠️ Authentication required. Minimum role: {required_auth_level}")
        st.info("Please login using the sidebar.")
        return False

    def render_user_info(self):
        """Render user information in sidebar."""
        user = self.get_current_user()

        if user:
            st.sidebar.markdown("---")
            st.sidebar.subheader("👤 User Info")
            st.sidebar.write(f"**Name:** {user.get('name', 'Unknown')}")
            st.sidebar.write(f"**Email:** {user.get('email', 'Unknown')}")
            st.sidebar.write(f"**Role:** {user.get('role', 'user')}")
        else:
            st.sidebar.markdown("---")
            st.sidebar.info("🔓 Not logged in")


def create_auth_wrapper(auth_manager: AuthManager):
    """Create a decorator for protecting app functions."""

    def auth_required(required_level: str = "subscriber"):
        def decorator(func):
            def wrapper(*args, **kwargs):
                if auth_manager.render_auth_check(required_level):
                    return func(*args, **kwargs)
                else:
                    st.stop()
            return wrapper
        return decorator
    return auth_required


def get_auth_manager() -> AuthManager:
    """Get a configured AuthManager instance using shared auth."""
    try:
        return AuthManager()
    except Exception as e:
        logger.error(f"Failed to initialize AuthManager: {e}")
        raise


if __name__ == "__main__":
    # Test the auth system
    st.title("Shared Authentication System Test")

    auth_manager = get_auth_manager()

    # Show login widget
    auth_manager.render_login_widget(location="main")

    # Test different auth levels
    st.subheader("Access Level Tests")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Public Access**")
        if auth_manager.render_auth_check("public"):
            st.success("✅ Access granted")

    with col2:
        st.write("**Subscriber Access**")
        if auth_manager.render_auth_check("subscriber"):
            st.success("✅ Access granted")

    with col3:
        st.write("**Admin Access**")
        if auth_manager.render_auth_check("admin"):
            st.success("✅ Access granted")

    # Show user info
    auth_manager.render_user_info()

    # Show session info
    if is_authenticated():
        st.subheader("Session Info")
        st.json(get_user_info())
