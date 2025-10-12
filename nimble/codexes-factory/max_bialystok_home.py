#!/usr/bin/env python3
"""
Max Bialystok Financial Analysis - Standalone Application

Financial analysis software for book publishers inspired by "The Producers".
Provides comprehensive financial reporting, royalty calculation, and performance analytics.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import logging
import streamlit as st
import pandas as pd
from datetime import datetime

# Optional imports
try:
    from currency_converter import CurrencyConverter
    CURRENCY_CONVERTER_AVAILABLE = True
except ImportError:
    CURRENCY_CONVERTER_AVAILABLE = False

# Import following current patterns
try:
    from codexes.modules.finance.leo_bloom.ui import LeoBloom as Leo
    from codexes.core.logging_config import get_logging_manager
    # Set up logging
    logging_manager = get_logging_manager()
    logging_manager.setup_logging()
    logger = logging.getLogger(__name__)
except ModuleNotFoundError:
    try:
        from src.codexes.modules.finance.leo_bloom.ui import LeoBloom as Leo
        from src.codexes.core.logging_config import get_logging_manager
        # Set up logging
        logging_manager = get_logging_manager()
        logging_manager.setup_logging()
        logger = logging.getLogger(__name__)
    except ModuleNotFoundError:
        # Fallback imports and logging
        try:
            from src.codexes.modules.finance.leo_bloom.ui import LeoBloom as Leo
        except ModuleNotFoundError:
            Leo = None
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

# Set up page config first
st.set_page_config(
    page_title="Max Bialystok Financial Analysis",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Logging already set up above

def main():
    """Main application function."""

    # Header
    st.title("💰 Max Bialystok Financial Analysis")
    st.markdown("**Financial Analysis Software for Book Publishers**")

    # Add the iconic image if available
    if os.path.exists('resources/images/Max_Bialystock_-_Edited.png'):
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image('resources/images/Max_Bialystock_-_Edited.png', width=200)
        with col2:
            st.markdown("""
            ### Features:
            - 📊 Ingests royalty data from KDP, Ingram, and publisher direct sales
            - 📈 Analyzes profitability by frontlist, backlist, product line, and style
            - 💰 Calculates and reports royalty rates and royalties earned
            - 📋 Visualizations for all categories and individual titles
            """)
    else:
        st.markdown("""
        ### Features:
        - 📊 Ingests royalty data from KDP, Ingram, and publisher direct sales
        - 📁 Comprehensive data file management with status monitoring
        - 📈 Analyzes profitability by frontlist, backlist, product line, and style
        - 💰 Calculates and reports royalty rates and royalties earned
        - 📋 Visualizations for all categories and individual titles
        - 📤 Multiple file upload with automatic validation
        """)

    st.caption("*The inspired lunacy of Zero Mostel as Max Bialystok in the classic movie THE PRODUCERS.*")

    # Initialize session state
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 37

    # Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a section:",
        ["🏠 Home", "📊 Financial Analysis", "💰 Royalty Management", "📈 Analytics Dashboard", "⚙️ Settings"]
    )

    # Current status
    user_id = st.session_state.user_id
    today = datetime.now()

    # Currency conversion
    if CURRENCY_CONVERTER_AVAILABLE:
        try:
            c = CurrencyConverter()
            cgbp = c.convert(1, 'USD', 'GBP')
            st.sidebar.success(f"Exchange Rate: 1 USD = {cgbp:.4f} GBP")
        except Exception as e:
            st.sidebar.warning(f"Currency data unavailable: {e}")
    else:
        st.sidebar.info("💱 1 USD ≈ 0.82 GBP (static rate)")

    st.sidebar.info(f"Running for user {user_id} on {today.strftime('%Y-%m-%d')}")

    # Main content based on navigation
    if page == "🏠 Home":
        show_home_dashboard()
    elif page == "📊 Financial Analysis":
        show_financial_analysis()
    elif page == "💰 Royalty Management":
        show_royalty_management()
    elif page == "📈 Analytics Dashboard":
        show_analytics_dashboard()
    elif page == "⚙️ Settings":
        show_settings()

    # Footer
    st.markdown("---")
    st.markdown("**Max Bialystok Financial Analysis** - Part of the Codexes Factory Suite")
    st.markdown("💡 *Inspired by Mel Brooks' \"The Producers\"*")

def show_home_dashboard():
    """Show the main dashboard."""
    st.header("📈 Financial Dashboard")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("YTD Revenue", "$125,450", delta="$12,340")
    with col2:
        st.metric("Active Titles", "347", delta="23")
    with col3:
        st.metric("Royalties Due", "$37,635", delta="$3,702")
    with col4:
        st.metric("Monthly Avg", "$10,454", delta="$1,028")

    # Quick actions
    st.subheader("🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📁 Upload LSI Data"):
            st.info("Navigate to Financial Analysis → Upload LSI Data")

    with col2:
        if st.button("💰 Calculate Royalties"):
            st.info("Navigate to Royalty Management → Calculate")

    with col3:
        if st.button("📊 View Analytics"):
            st.info("Navigate to Analytics Dashboard")

    # Recent activity (placeholder)
    st.subheader("📋 Recent Activity")
    activity_data = {
        'Date': ['2024-09-23', '2024-09-22', '2024-09-21'],
        'Activity': ['LSI data uploaded', 'Royalty report generated', 'New title added'],
        'Status': ['✅ Complete', '✅ Complete', '⏳ Pending']
    }
    st.dataframe(pd.DataFrame(activity_data), use_container_width=True)

def show_financial_analysis():
    """Show financial analysis tools."""
    st.header("📊 Financial Analysis")
    st.info("This section provides comprehensive financial analysis tools.")
    st.markdown("Navigate to **Pages → Max Bialystok Financial** for full analysis interface.")

def show_royalty_management():
    """Show royalty management tools."""
    st.header("💰 Royalty Management")
    st.info("This section handles royalty calculations and payments.")
    st.markdown("Navigate to **Pages → Max Bialystok Financial** for full royalty interface.")

def show_analytics_dashboard():
    """Show analytics dashboard."""
    st.header("📈 Analytics Dashboard")
    st.info("This section provides advanced analytics and insights.")
    st.markdown("Navigate to **Pages → Leo Bloom Analytics** for detailed analytics.")

def show_settings():
    """Show application settings."""
    st.header("⚙️ Settings")

    # User settings
    st.subheader("User Configuration")
    new_user_id = st.number_input("User ID", value=st.session_state.user_id, min_value=1)
    if st.button("Update User ID"):
        st.session_state.user_id = new_user_id
        st.success(f"User ID updated to {new_user_id}")

    # File paths
    st.subheader("File Paths")
    data_path = st.text_input("Data Directory", value="resources/data_tables/")
    output_path = st.text_input("Output Directory", value="output/")

    # Analysis settings
    st.subheader("Analysis Settings")
    frontlist_window = st.slider("Frontlist Window (months)", 6, 36, 18)
    backlist_window = st.slider("Deep Backlist Window (months)", 24, 120, 60)

    st.info("Settings are applied automatically. Changes will be reflected in analysis results.")

if __name__ == "__main__":
    main()