#!/usr/bin/env python3
"""
PDF Harvester Page

Admin-only Streamlit page for harvesting PDFs using Google search pagination.
"""


import sys
from pathlib import Path
import logging
import streamlit as st

sys.path.insert(0, '/Users/fred/xcu_my_apps')

# NOTE: st.set_page_config() and render_unified_sidebar() handled by main app

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
except ImportError as e:
    import streamlit as st
    st.error(f"Failed to import shared authentication: {e}")
    st.error("Please ensure /Users/fred/xcu_my_apps/shared/auth is accessible")
    st.stop()




logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)




# Add the project root to Python path for proper imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add the src directory to Python path
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import the page module
from codexes.modules.ui.pages.pdf_harvester import render


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize shared authentication system
try:
    shared_auth = get_shared_auth()
    logger.info("Shared authentication system initialized")
except Exception as e:
    logger.error(f"Failed to initialize shared auth: {e}")
    st.error("Authentication system unavailable.")


# Check user permissions
try:
    from codexes.core.auth import get_user_role, require_role

    # Require admin role for this page
    user_role = get_user_role()

    if user_role != "admin":
        st.error("🚫 Access Denied: Admin role required for PDF Harvester")
        st.info("Please contact an administrator for access to this feature.")
        st.stop()

except ImportError:
    # Fallback if auth system is not available
    pass

# Render the page
if __name__ == "__main__":
    render()