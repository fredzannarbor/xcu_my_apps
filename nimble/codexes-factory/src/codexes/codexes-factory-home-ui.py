from __future__ import annotations
#!/usr/bin/env python3
# ──────────────────────────────────────────────────────────────────────────────
#  codexes-factory-home-ui.py – Streamlit front-end for Codexes-Factory
#  UPDATED: Now uses shared authentication system for SSO
# ──────────────────────────────────────────────────────────────────────────────

import logging
import sys
from pathlib import Path
from typing import Dict

import streamlit as st

# Add the project root to Python path for proper imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add the src directory to Python path
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Add /Users/fred/xcu_my_apps for shared modules
my_apps_path = "/"
if my_apps_path not in sys.path:
    sys.path.insert(0, my_apps_path)

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info
except ImportError as e:
    st.error(f"Failed to import shared authentication: {e}")
    st.error("Please ensure /Users/fred/xcu_my_apps/shared/auth is accessible")
    st.stop()

# Now all imports use the standardized 'codexes.' prefix
try:
    from codexes.core.auth import get_allowed_pages
    from codexes.core.config import get_version_as_dict
    from codexes.core.translations import get_translation
    from codexes.core.utils import setup_logging
except ModuleNotFoundError as e:
    st.error(f"Failed to import required modules: {e}")
    st.error("Please ensure the application is run from the correct directory and all dependencies are installed.")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# Page Config & Initial Setup
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded",
    page_title="The Codex Factory at Nimble Books",
    page_icon="🏭"
)

setup_logging(level="INFO")
logger = logging.getLogger("codexes_factory")

# ──────────────────────────────────────────────────────────────────────────────
# Application Constants
# ──────────────────────────────────────────────────────────────────────────────
ALL_PAGES = [
    st.Page("pages/1_Home.py", title="Home", icon="🏠"),
    st.Page("pages/2_Annotated_Bibliography.py", title="Annotated Bibliography", icon="📚", url_path="annotated_bibliography_alt"),
    st.Page("pages/22_AI_Social_Feed.py", title="AI Social Feed", icon="🧠"),
    st.Page("pages/6_Bookstore.py", title="Bookstore", icon="🛍️", url_path="6_Bookstore"),
    st.Page("pages/8_Login_Register.py", title="Login/Register", icon="🔐"),
    st.Page("pages/15_Ideation_and_Development.py", title="Ideation & Development", icon="💡"),
    st.Page("pages/ideation_dashboard.py", title="Ideation Dashboard", icon="💡"),

    st.Page("pages/10_Book_Pipeline.py", title="Book Pipeline", icon="🚀"),
    st.Page("pages/15_Imprint_Display.py", title="Imprint Display", icon="🏢"),
    st.Page("pages/21_Imprint_Ideas_Tournament.py", title="Imprint Ideas Tournament", icon="🏆"),
    st.Page("pages/20_Enhanced_Imprint_Creator.py", title="Enhanced Imprint Creator", icon="🌟"),
    st.Page("pages/3_Manuscript_Enhancement.py", title="Manuscript Enhancement", icon="✍️"),
    st.Page("pages/4_Metadata_and_Distribution.py", title="Metadata & Distribution", icon="📊"),
    st.Page("pages/5_Settings_and_Commerce.py", title="Settings & Commerce", icon="⚙️"),
    st.Page("pages/Configuration_Management.py", title="Configuration Management", icon="⚙️"),

    # Finance Pages - Combined functionality from both branches
    st.Page("pages/26_Rights_Analytics.py", title="Rights Analytics", icon="📈"),
    st.Page("pages/27_Max_Bialystok_Financial.py", title="Max Bialystok Financial", icon="💰"),
    st.Page("pages/28_Leo_Bloom_Analytics.py", title="Leo Bloom Analytics", icon="📈"),
    st.Page("pages/29_Imprint_Financial_Dashboard.py", title="Imprint Financial Dashboard", icon="💼"),
    st.Page("pages/30_Books_In_Print_Financial.py", title="Books In Print Financial", icon="📚"),
    st.Page("pages/30_Sales_Analysis.py", title="Sales Analysis", icon="💹"),
    st.Page("pages/31_FRO_Diagnostics.py", title="FRO Diagnostics", icon="🔧"),

    st.Page("pages/7_Admin_Dashboard.py", title="Admin Dashboard", icon="👑"),
    st.Page("pages/32_PDF_Harvester.py", title="PDF Harvester", icon="🔍"),

]

LANG_OPTIONS: Dict[str, str] = {"en": "English", "ko": "한국어"}

# ──────────────────────────────────────────────────────────────────────────────
# Session state initialization
# ──────────────────────────────────────────────────────────────────────────────
if 'language' not in st.session_state:
    st.session_state.language = 'en'

T = lambda key, **kwargs: get_translation(st.session_state.get('language', 'en'), key, **kwargs)

# ──────────────────────────────────────────────────────────────────────────────
# Authentication Setup - Using Shared Auth System
# ──────────────────────────────────────────────────────────────────────────────
try:
    # Initialize shared authentication system
    auth = get_shared_auth()

    # Get current auth state
    authentication_status = is_authenticated()
    user_info = get_user_info() if authentication_status else {}

    current_username = user_info.get('username')
    user_role = user_info.get('user_role', 'public')

    # Update session state for compatibility with existing pages
    st.session_state['user_role'] = user_role
    st.session_state['username'] = current_username
    st.session_state['authentication_status'] = authentication_status
    st.session_state['user_name'] = user_info.get('user_name')
    st.session_state['user_email'] = user_info.get('user_email')

    logger.info(f"Auth initialized - User: {current_username}, Role: {user_role}, Authenticated: {authentication_status}")

except Exception as e:
    st.error("Authentication subsystem failed to start. Please check the logs.")
    logger.critical(f"Failed to initialize shared authenticator: {e}", exc_info=True)
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# Determine user role and filter pages
# ──────────────────────────────────────────────────────────────────────────────
allowed_pages = get_allowed_pages(user_role, ALL_PAGES)

# Version info
try:
    version_info = get_version_as_dict()
except Exception as e:
    version_info = {"error": "Could not load version info."}
    logger.error(f"Error loading version info: {e}", exc_info=True)

# ──────────────────────────────────────────────────────────────────────────────
# Build Sidebar with Shared Auth
# ──────────────────────────────────────────────────────────────────────────────

# Render unified sidebar at the top
try:
    from shared.ui import render_unified_sidebar

    render_unified_sidebar(
        app_name="Codexes Factory",
        nav_items=[],  # App-specific nav handled by st.navigation below
        show_auth=True,
        show_xtuff_nav=True,
        show_version=True,
        show_contact=True
    )

    # Mark sidebar as rendered to prevent child pages from duplicating it
    st.session_state.sidebar_rendered = True
    logger.debug("Main app rendered sidebar, set sidebar_rendered flag")

except ImportError as e:
    logger.warning(f"Could not import render_unified_sidebar: {e}")
    # Fallback to simple auth display
    st.sidebar.title("🔐 Authentication")
    if authentication_status:
        st.sidebar.success(f"👤 {user_info.get('user_name', 'User')}")
        st.sidebar.caption(f"Role: {user_role}")
    else:
        st.sidebar.info("Not logged in")

    # Mark sidebar as rendered even in fallback mode
    st.session_state.sidebar_rendered = True

# Add separator before app navigation
st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 Codexes Factory")

# Additional sidebar info
if authentication_status:
    st.sidebar.info(f"**Pages Available:** {len(allowed_pages)}")
else:
    st.sidebar.warning("Login to access all features")

# Show version info
with st.sidebar.expander("ℹ️ App Version"):
    st.json(version_info)

# ──────────────────────────────────────────────────────────────────────────────
# Run Navigation (with native navigation hidden - use custom sidebar instead)
# ──────────────────────────────────────────────────────────────────────────────
pg = st.navigation(allowed_pages, position="hidden")
pg.run()
