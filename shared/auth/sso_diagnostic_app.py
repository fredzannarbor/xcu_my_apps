#!/usr/bin/env python3
"""
SSO Diagnostic App - Standalone Streamlit app for debugging SSO issues

Run with:
    streamlit run /Users/fred/xcu_my_apps/shared/auth/sso_diagnostic_app.py --server.port=8599
"""

import sys
from pathlib import Path

# Add shared path
sys.path.insert(0, "/Users/fred/xcu_my_apps")

import streamlit as st

# Must be first Streamlit command
st.set_page_config(
    page_title="SSO Diagnostics",
    page_icon="🔍",
    layout="wide"
)

from shared.auth.diagnostics import show_sso_diagnostics
from shared.auth import get_shared_auth

# Initialize auth (this will check for active sessions)
auth = get_shared_auth()

# Show diagnostics
show_sso_diagnostics()
