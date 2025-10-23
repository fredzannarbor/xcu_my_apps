import logging
import streamlit as st
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




# Render unified sidebar only if not already rendered by main app
# Main app sets sidebar_rendered=True to prevent duplication
if not st.session_state.get('sidebar_rendered', False):
    # NOTE: st.set_page_config() and render_unified_sidebar() handled by main app

# Render unified sidebar only if not already rendered by main app
# Main app sets sidebar_rendered=True to prevent duplication
if not st.session_state.get('sidebar_rendered', False):
    # NOTE: st.set_page_config() and render_unified_sidebar() handled by main app
# DO NOT render sidebar here - it's already rendered by codexes-factory-home-ui.py

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




st.title("⚙️ Settings & Commerce")
st.markdown("This page is a placeholder for future functionality.")

st.header("API Keys")
st.markdown("API keys are loaded from your `.env` file in the project root (`codexes/.env`).")
st.info("To add or change a key, edit the `.env` file and restart the Streamlit app.")

keys_found = []
if os.getenv("GEMINI_API_KEY"): keys_found.append("Google Gemini")
if os.getenv("OPENAI_API_KEY"): keys_found.append("OpenAI")
if os.getenv("ANTHROPIC_API_KEY"): keys_found.append("Anthropic")
if os.getenv("GROQ_API_KEY"): keys_found.append("Groq")

if keys_found:
    st.success(f"Found API keys for: {', '.join(keys_found)}")
else:
    st.warning("No API keys found in `.env` file. LLM calls will fail.")

st.header("Commerce (Stripe Integration)")
st.markdown("This section is a placeholder for future Stripe integration.")
st.write("Functionality to be added:")
st.markdown("""
- User account creation and management.
- Tiered subscription plans for different levels of usage.
- Pay-per-use credit system.
- Secure checkout process via Stripe.
"""
)