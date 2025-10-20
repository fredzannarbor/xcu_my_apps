"""
Imprint Financial Dashboard Page

Comprehensive financial reporting and analysis by imprint using the
integrated imprints and finance modules.
"""


import logging
import streamlit as st
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




# Import following current patterns
try:
    from codexes.modules.finance.leo_bloom.ui.ImprintFinancialDashboard import show_imprint_financial_dashboard
    from codexes.core.logging_config import get_logging_manager

    # Set up logging
    logging_manager = get_logging_manager()
    logging_manager.setup_logging()
    logger = logging.getLogger(__name__)
except ModuleNotFoundError:
    try:
        from src.codexes.modules.finance.leo_bloom.ui.ImprintFinancialDashboard import show_imprint_financial_dashboard
        from src.codexes.core.logging_config import get_logging_manager

        # Set up logging
        logging_manager = get_logging_manager()
        logging_manager.setup_logging()
        logger = logging.getLogger(__name__)
    except ModuleNotFoundError:
        # Fallback
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        def show_imprint_financial_dashboard():
            st.error("❌ Imprint Financial Dashboard module not available")
            st.info("Please ensure the finance and imprints modules are properly installed")

# NOTE: st.set_page_config() and render_unified_sidebar() handled by main app

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




def main():
    """Main function for the Imprint Financial Dashboard page."""
    try:
        # Show the dashboard
        show_imprint_financial_dashboard()

    except Exception as e:
        st.error(f"❌ Error loading Imprint Financial Dashboard: {e}")
        logger.error(f"Error in Imprint Financial Dashboard page: {e}")

        # Fallback content
        st.title("📊 Imprint Financial Dashboard")
        st.warning("The imprint financial dashboard is currently unavailable.")

        with st.expander("💡 Expected Features", expanded=True):
            st.markdown("""
            This dashboard provides:

            **📈 Individual Imprint Analysis**
            - Revenue and sales metrics by imprint
            - Top-performing titles
            - Configuration and settings view

            **🔍 Comparative Analysis**
            - Side-by-side imprint comparison
            - Performance rankings
            - Territorial presence mapping

            **📋 Portfolio Overview**
            - All imprints summary table
            - Portfolio-wide statistics
            - Revenue and units aggregation

            **⚙️ Export & Configuration**
            - Excel report generation
            - Data export capabilities
            - Integration status monitoring
            """)

if __name__ == "__main__":
    main()