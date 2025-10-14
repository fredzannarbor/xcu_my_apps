"""
Unified sidebar component for all xcu_my_apps applications.

Provides:
- Authentication (login/register/subscribe)
- xtuff.ai navigation
- App-specific navigation
- Version info (machine, git, pypi)
- Contact widget
"""

import streamlit as st
import subprocess
import socket
import sys
from pathlib import Path
from typing import Optional, List, Dict

# Import shared authentication system
try:
    # Try relative import first (when called from within shared module)
    from ..auth import get_shared_auth, is_authenticated, get_user_info, authenticate, logout
    AUTH_AVAILABLE = True
    AUTH_ERROR = None
except ImportError:
    try:
        # Fallback to absolute import (when called from external apps)
        from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate, logout
        AUTH_AVAILABLE = True
        AUTH_ERROR = None
    except ImportError as e:
        AUTH_AVAILABLE = False
        AUTH_ERROR = str(e)
        # Fallback if shared.auth not available
        def get_shared_auth(): return None
        def is_authenticated(): return False
        def get_user_info(): return {}
        def authenticate(u, p): return False, f"Auth import failed: {AUTH_ERROR}"
        def logout(): pass


def get_git_info() -> Dict[str, str]:
    """Get git repository information."""
    try:
        # Get git describe output
        describe = subprocess.check_output(
            ['git', 'describe', '--tags', '--always', '--dirty'],
            cwd=Path(__file__).parent.parent.parent,
            stderr=subprocess.DEVNULL
        ).decode().strip()

        # Get branch name
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=Path(__file__).parent.parent.parent,
            stderr=subprocess.DEVNULL
        ).decode().strip()

        # Get commit hash
        commit = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=Path(__file__).parent.parent.parent,
            stderr=subprocess.DEVNULL
        ).decode().strip()

        return {
            'describe': describe,
            'branch': branch,
            'commit': commit
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {
            'describe': 'unknown',
            'branch': 'unknown',
            'commit': 'unknown'
        }


def get_machine_info() -> str:
    """Get machine hostname."""
    try:
        return socket.gethostname()
    except:
        return 'unknown'


def get_package_version(package_name: str) -> Optional[str]:
    """Get installed package version from PyPI."""
    try:
        import importlib.metadata
        return importlib.metadata.version(package_name)
    except:
        return None


def render_auth_section():
    """Render authentication/subscription section using shared auth system."""
    # Check if auth is available
    if not AUTH_AVAILABLE:
        st.sidebar.error(f"Auth unavailable: {AUTH_ERROR}")
        return

    # Initialize shared auth
    auth = get_shared_auth()
    if auth is None:
        st.sidebar.warning("Authentication system not initialized")
        return

    # Generate unique key prefix for this render to avoid collisions
    import time
    key_prefix = f"auth_{int(time.time() * 1000) % 100000}"

    if not is_authenticated():
        # Not authenticated - show expanded Account section
        st.sidebar.title("🔐 Account")
        tab1, tab2, tab3 = st.sidebar.tabs(["Login", "Register", "Subscribe"])

        with tab1:
            # Use unique form key to avoid collisions when multiple pages use unified_sidebar
            form_key = f"{key_prefix}_login_form"
            with st.form(form_key):
                username = st.text_input("Username", key=f"{form_key}_username")
                password = st.text_input("Password", type="password", key=f"{form_key}_password")
                submit = st.form_submit_button("Login")

                if submit:
                    success, message = authenticate(username, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

        with tab2:
            st.info("📝 Registration coming soon!")
            st.markdown("Contact admin@nimblebooks.com for account creation")

        with tab3:
            st.markdown("**Subscription Plans**")
            st.markdown("- 🆓 Free: Basic access")
            st.markdown("- 💎 Pro: Full features")
            st.markdown("- 🌟 Enterprise: Custom solutions")
            st.info("💳 Subscription management coming soon!")
    else:
        # Authenticated - show collapsed Account section
        user_info = get_user_info()

        with st.sidebar.expander("🔐 Account", expanded=False):
            st.success(f"👤 {user_info.get('user_name', 'User')}")
            st.caption(f"📧 {user_info.get('user_email', '')}")
            st.caption(f"🎭 Role: {user_info.get('user_role', 'user').capitalize()}")

            # Show subscription tier
            sub_tier = user_info.get('subscription_tier', 'free')
            sub_status = user_info.get('subscription_status', 'inactive')

            if sub_status == 'active':
                tier_emoji = {'free': '🆓', 'pro': '💎', 'enterprise': '🌟'}.get(sub_tier, '🆓')
                st.info(f"{tier_emoji} {sub_tier.capitalize()} Subscription")

            if st.button("Logout", key=f"{key_prefix}_logout_btn"):
                logout()
                st.rerun()


def render_xtuff_nav():
    """Render xtuff.ai Cinematic Universe navigation menu."""
    with st.sidebar.expander("🌐 xtuff.ai Cinematic Universe (xCU)"):
        st.markdown("### Apps")

        # Updated to match apps_config.json - only showing public_visible apps
        apps = [
            ("🏠 Home", "http://localhost:8500"),
            ("🤖 Social Xtuff", "http://localhost:8501"),
            ("📚 Codexes Factory", "http://localhost:8502"),
            ("🌍 Trillions of People", "http://localhost:8504"),
            ("⏰ Daily Engine", "http://localhost:8509"),
            ("👤 AI Resume Builder", "http://localhost:8512"),
        ]

        for name, url in apps:
            st.markdown(f"[{name}]({url})")


def render_app_nav(app_name: str, nav_items: Optional[List[tuple]] = None):
    """
    Render app-specific navigation.

    Args:
        app_name: Name of the current application
        nav_items: List of (label, url/page) tuples for navigation
    """
    st.sidebar.markdown(f"### 📱 {app_name}")

    if nav_items:
        for label, target in nav_items:
            if target.startswith('http'):
                st.sidebar.markdown(f"[{label}]({target})")
            else:
                # Internal Streamlit page
                if st.sidebar.button(label, key=f"nav_{label}"):
                    st.switch_page(target)


def render_version_info():
    """Render version and environment information."""
    with st.sidebar.expander("ℹ️ Version Info"):
        git_info = get_git_info()
        machine = get_machine_info()

        # Get current page path
        try:
            current_script = st.runtime.scriptrunner.get_script_run_ctx()
            if current_script and hasattr(current_script, 'page_script_hash'):
                # Try to get the current page name from session state
                page_name = getattr(st.session_state, '_main_script_path', 'main')
                if page_name and '/' in page_name:
                    page_name = page_name.split('/')[-1]
                st.markdown(f"**Page:** `{page_name}`")
        except:
            # Fallback - just show __file__ relative path
            try:
                current_file = Path(__file__).resolve()
                st.markdown(f"**Page:** `{current_file.name}`")
            except:
                pass

        st.markdown(f"**Machine:** `{machine}`")
        st.markdown(f"**Branch:** `{git_info['branch']}`")
        st.markdown(f"**Commit:** `{git_info['commit']}`")
        st.markdown(f"**Version:** `{git_info['describe']}`")

        # Try to get package version if available
        st.markdown(f"**Python:** `{sys.version.split()[0]}`")


def render_contact_widget():
    """Render contact form widget."""
    # Generate unique key prefix based on timestamp to avoid collisions
    import time
    key_prefix = f"contact_{int(time.time() * 1000) % 100000}"

    with st.sidebar.expander("📧 Contact"):
        st.markdown("### Subscribe to the xCU")

        # Substack embed form
        st.markdown("""
        <iframe src="https://fredzannarbor.substack.com/embed"
                width="100%"
                height="150"
                style="border:1px solid #EEE; background:white;"
                frameborder="0"
                scrolling="no">
        </iframe>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Quick message form with unique keys
        st.text_area("Quick Message", key=f"{key_prefix}_message", height=100)
        if st.button("Send Message", key=f"{key_prefix}_send_btn"):
            # TODO: Integrate with email/notification system
            st.success("Message sent! We'll get back to you soon.")


def render_unified_sidebar(
    app_name: str,
    nav_items: Optional[List[tuple]] = None,
    show_auth: bool = True,
    show_xtuff_nav: bool = True,
    show_version: bool = True,
    show_contact: bool = True
):
    """
    Render complete unified sidebar for xcu_my_apps applications.

    Args:
        app_name: Name of the current application
        nav_items: Optional list of (label, url/page) tuples for app navigation
        show_auth: Show authentication section (default: True)
        show_xtuff_nav: Show xtuff.ai navigation (default: True)
        show_version: Show version info (default: True)
        show_contact: Show contact widget (default: True)

    Example:
        ```python
        from shared.ui import render_unified_sidebar

        render_unified_sidebar(
            app_name="My App",
            nav_items=[
                ("Home", "pages/home.py"),
                ("Settings", "pages/settings.py"),
            ]
        )
        ```
    """
    # Render sections in order
    if show_auth:
        render_auth_section()
        st.sidebar.markdown("---")

    if show_xtuff_nav:
        render_xtuff_nav()
        st.sidebar.markdown("---")

    if nav_items:
        render_app_nav(app_name, nav_items)
        st.sidebar.markdown("---")

    if show_version:
        render_version_info()

    if show_contact:
        st.sidebar.markdown("---")
        render_contact_widget()
