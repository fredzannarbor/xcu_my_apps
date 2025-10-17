"""
Modern Streamlit web application for Trillions of People.
Version 1.1.0 - Migrated to shared authentication system
Refactored from the legacy trillionsofpeople.py monolith.
"""

import csv
import datetime
import random
import sys
from pathlib import Path
from typing import Optional, Dict, Any

sys.path.insert(0, '/Users/fred/xcu_my_apps')

import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from gibberish import Gibberish

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
    from shared.ui import render_unified_sidebar
except ImportError as e:
    st.error(f"Failed to import shared authentication: {e}")
    st.error("Please ensure /Users/fred/xcu_my_apps/shared/auth is accessible")
    st.stop()

from ..core.logging_config import get_logger
from ..modules.people_utilities import PeopleManager
from .components import (
    render_about_section,
    render_browse_section,
    render_cards_section,
    render_generation_section,
    render_upload_section
)
from .utils import create_api_key_manager

logger = get_logger(__name__)

# Initialize shared authentication system
try:
    shared_auth = get_shared_auth()
    logger.info("Shared authentication system initialized")
except Exception as e:
    logger.error(f"Failed to initialize shared auth: {e}")
    st.error("Authentication system unavailable.")


class TrillionsWebApp:
    """Main Streamlit web application class."""

    def __init__(self):
        self.people_manager = PeopleManager()
        self.gib = Gibberish()
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if "openai_key" not in st.session_state:
            st.session_state.openai_key = None

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

    def submit_guard(self) -> Optional[str]:
        """Validate API key before form submission."""
        if not st.session_state.openai_key or len(st.session_state.openai_key) != 51:
            st.error("Before submitting a request, you must enter a valid API key for OpenAI in the sidebar.")
            st.stop()
        return st.session_state.openai_key

    def run(self):
        """Main application entry point."""
        try:
            self._setup_page()
            self._render_unified_sidebar()
            self._render_header()
            self._render_main_content()

        except Exception as e:
            logger.error(f"Application error: {e}")
            st.error(f"An error occurred: {e}")

    def _setup_page(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="TrillionsOfPeople.info",
            page_icon="👥",
            layout="wide",
            initial_sidebar_state="expanded"
        )

    def _render_header(self):
        """Render the main page header."""
        st.title('TrillionsOfPeople.info')
        st.markdown("""_One row for every person who ever lived, might have lived, or may live someday._

_**Create, edit, register, claim, share**_ stories about your fellow souls.

_A tool to explore the human story._""")

    def _render_unified_sidebar(self):
        """Render the unified sidebar."""
        # Hide native Streamlit navigation
        st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {display: none;}
        </style>
        """, unsafe_allow_html=True)

        render_unified_sidebar(
            app_name="Trillions of People",
            show_auth=True,
            show_xtuff_nav=True
        )

    def _render_main_content(self):
        """Render the main application content sections."""
        # API Key Management (functional requirement, not just UI)
        with st.expander("API Key Setup", expanded=not st.session_state.openai_key):
            st.info("An OpenAI API key is required to generate new personas.")
            api_key_manager = create_api_key_manager()
            st.session_state.openai_key = api_key_manager.enter_api_key("openai")

        # Load countries data
        countries = self.people_manager.load_countries()

        # About section
        render_about_section()

        # Browse people section
        render_browse_section(self.people_manager)

        # People cards section
        render_cards_section(self.people_manager)

        # Generation section
        render_generation_section(self.people_manager, countries, self.submit_guard)

        # Upload section
        render_upload_section(self.people_manager)


def main():
    """Entry point for the Streamlit web application."""
    app = TrillionsWebApp()
    app.run()


if __name__ == "__main__":
    main()