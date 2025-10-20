# src/codexes/pages/12_Bibliography_Shopping.py
import logging
import streamlit as st
from pathlib import Path
import json
import os
import sys


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


sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
    from shared.ui import render_unified_sidebar
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




# NOTE: st.set_page_config() and render_unified_sidebar() handled by main app

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




st.title("📚 Shop for Works Mentioned")
st.markdown("Find and purchase books referenced in the quotations.")

# Check if shopping list exists
shopping_dir = Path("data/bibliography_shopping_lists")
shopping_file = shopping_dir / "bibliography_shopping_list.html"

if not shopping_file.exists():
    st.warning("No bibliography shopping list has been generated yet. Run the Book Pipeline or Backmatter Manager first.")
    st.stop()

# Read the HTML content
with open(shopping_file, "r", encoding="utf-8") as f:
    html_content = f.read()

# Display the HTML content
st.components.v1.html(html_content, height=800, scrolling=True)

# Add a link to the catalog
st.markdown("---")
st.markdown("Return to the [catalog](/catalog) to explore more books.")