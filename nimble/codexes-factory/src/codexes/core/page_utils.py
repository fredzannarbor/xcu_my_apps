"""
Shared utilities for Streamlit pages in multi-page apps.

Provides consistent sidebar rendering and authentication checking
across all pages in the Codexes Factory application.
"""

import logging
import streamlit as st

logger = logging.getLogger(__name__)

def render_page_sidebar():
    """
    Render the unified sidebar for any page in the Codexes Factory app.

    This function should be called at the top of every page's main() function
    to ensure consistent sidebar appearance and authentication display across
    all pages, whether accessed via navigation or direct URL.

    In Streamlit multi-page apps, the main app file only runs once at startup.
    When navigating directly to a page via URL, only that page's code runs,
    so each page needs to set up its own sidebar.
    """
    try:
        from shared.ui import render_unified_sidebar
        from shared.auth import is_authenticated, get_user_info

        # Render the unified sidebar with all standard sections
        render_unified_sidebar(
            app_name="Codexes Factory",
            nav_items=[],  # Navigation handled by Streamlit's native multi-page system
            show_auth=True,
            show_xtuff_nav=True,
            show_version=True,
            show_contact=True
        )

        logger.debug("Rendered unified sidebar successfully")

    except ImportError as e:
        logger.warning(f"Could not import render_unified_sidebar: {e}")
        # Fallback to simple auth display
        from shared.auth import is_authenticated, get_user_info

        st.sidebar.title("🔐 Authentication")
        if is_authenticated():
            user_info = get_user_info()
            st.sidebar.success(f"👤 {user_info.get('user_name', 'User')}")
            st.sidebar.caption(f"Role: {user_info.get('user_role', 'public')}")
        else:
            st.sidebar.info("Not logged in")

    except Exception as e:
        logger.error(f"Error rendering page sidebar: {e}", exc_info=True)
        # Don't crash the page - just skip sidebar rendering
        pass


def ensure_auth_checked():
    """
    Ensure authentication has been checked for this page load.

    Call this at the top of every page to ensure the shared auth system
    has checked for active sessions (from session_state or URL query params).
    """
    try:
        from shared.auth import get_shared_auth

        # This will trigger session checking if not already done
        get_shared_auth()

    except Exception as e:
        logger.error(f"Error checking authentication: {e}", exc_info=True)
