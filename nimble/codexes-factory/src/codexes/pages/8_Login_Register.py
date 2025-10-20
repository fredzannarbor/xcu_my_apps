#!/usr/bin/env python3
# ──────────────────────────────────────────────────────────────────────────────
#  8_Login_Register.py – Streamlit Login, Registration, and Navigation Hub
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

# Standard library imports
import logging
from pathlib import Path
import sys

sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
    from shared.ui import render_unified_sidebar
except ImportError as e:
    st.error(f"Failed to import shared authentication: {e}")
    st.error("Please ensure /Users/fred/xcu_my_apps/shared/auth is accessible")
    st.stop()


# Third-party imports
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Define project root by navigating up from the current file's location.
# This file is in: /src/codexes/pages/
# The project root is 4 levels up.
script_path = Path(__file__).resolve()
project_root = script_path.parent.parent.parent.parent

# Local application imports
from src.codexes.core.auth import get_allowed_pages, get_user_role
from src.codexes.core.translations import get_translation
from src.codexes.core.utils import setup_logging

setup_logging(level="INFO")
logger = logging.getLogger("codexes_factory")

# ──────────────────────────────────────────────────────────────────────────────
# Helper – Guarantee unique Streamlit widget keys
# ──────────────────────────────────────────────────────────────────────────────
def _unique_key(base: str) -> str:
    """
version 1.1.0 - Migrated to shared authentication system

    Return an application-wide unique widget key by prefixing `base`
    with the current page name (or 'global' if not yet set).
    """
    page = st.session_state.get("current_page", "global")
    return f"{page}_{base}"

# ──────────────────────────────────────────────────────────────────────────────
# 1. Session-state bootstrap
# ──────────────────────────────────────────────────────────────────────────────
def T(key: str, default: str | None = None, **kwargs) -> str:
    """
    A wrapper for the get_translation function that automatically uses
    the language from the current Streamlit session state.
    """
    lang = st.session_state.get('language', 'en')
    return get_translation(lang, key, default=default, **kwargs)

# Store the master page list in the session for universal access.
ALL_PAGES = [
    st.Page("pages/1_Home.py", title="Home", icon="🏠"),
    st.Page("pages/6_Bookstore.py", title="Bookstore", icon="🛍️"),
    st.Page("pages/2_Annotated_Bibliography.py", title="Annotated Bibliography", icon="📇"),
    st.Page("pages/15_Ideation_and_Development.py", title="Ideation & Development", icon="💡"),
    st.Page("pages/3_Manuscript_Enhancement.py", title="Manuscript Enhancement", icon="✍️"),
    st.Page("pages/4_Metadata_and_Distribution.py", title="Metadata & Distribution", icon="📊"),
    st.Page("pages/5_Settings_and_Commerce.py", title="Settings & Commerce", icon="⚙️"),
    st.Page("pages/7_Admin_Dashboard.py", title="Admin Dashboard", icon="👑"),
    st.Page("pages/8_Login_Register.py", title="Login/Register", icon="🔐"),
    st.Page("pages/10_Book_Pipeline.py", title="Book Pipeline", icon="🚀"),
    st.Page("pages/Configuration_Management.py", title="Configuration Management", icon="⚙️"),
]
if 'all_pages' not in st.session_state:
    st.session_state['all_pages'] = ALL_PAGES

# ──────────────────────────────────────────────────────────────────────────────
# 2. Authentication Setup
# ──────────────────────────────────────────────────────────────────────────────
try:
    config_path = project_root / 'resources/yaml/config.yaml'
    with config_path.open('r') as file:
        config = yaml.load(file, Loader=SafeLoader)

    if 'authenticator' not in st.session_state:
        st.session_state['authenticator'] = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days'],
        )
    authenticator = st.session_state['authenticator']

except FileNotFoundError:
    st.error(T("config_not_found_error", "Configuration file not found. Please ensure 'resources/yaml/config.yaml' exists at the project root."))
    logger.error(f"Failed to find config file at expected path: {config_path}")
    st.stop()
except Exception as e:
    st.error(T("auth_init_failed", "Authentication subsystem failed to start."))
    logger.exception(e)
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# 3. Sidebar and Language Picker
# ──────────────────────────────────��───────────────────────────────────────────
# Sidebar handled by unified sidebar

# Language settings
lang_options = {"en": "English", "ko": "한국어"}
lang_display_to_code = {v: k for k, v in lang_options.items()}
current_lang_code = st.session_state.get("language", "en")

selected_lang_display = st.selectbox(
    label="🌐 Language",
    options=lang_options.values(),
    index=list(lang_options.keys()).index(current_lang_code),
    key=_unique_key("language_picker")
)

# If the language is changed, update the session state and rerun the script
new_lang_code = lang_display_to_code[selected_lang_display]
if st.session_state.get("language") != new_lang_code:
    st.session_state["language"] = new_lang_code
    st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# 4. Role-based Filtering (for display purposes on this page)
# ──────────────────────────────────────────────���───────────────────────────────
user_role = get_user_role(st.session_state.get('username'), config)
st.session_state['user_role'] = user_role

# ──────────────────────────────────────────────────────────────────────────────
# 5. Login, Registration, and Logout UI
# ──────────────────────────────────────────────────────────────────────────────

# Get authentication instance
# Shared auth initialized in header

# If user is already logged in, show a welcome message and a logout button.
if is_authenticated():

    st.write(T("welcome_message", name=auth.get_user_name()))
    st.write(T("role_display", role=get_user_info().get('user_role', 'user')))
    st.info("You are logged in.")

    if st.button(T('logout_button', 'Logout')):
        shared_logout()
        st.rerun()

# If user is not logged in, display the login form
else:
    try:
        # Create tabs for login and registration
        login_tab, register_tab = st.tabs(["Login", "Register"])
        
        with login_tab:
            shared_auth.render_login_form()
        
        with register_tab:
            shared_auth.render_registration_form()

    except Exception as e:
        st.error(f"Authentication error: {e}")
        logger.error(f"An error occurred during login: {e}")
