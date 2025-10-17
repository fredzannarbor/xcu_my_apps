"""
Max Bialystok Financial Analysis
version 1.1.0 - Migrated to shared authentication system

Financial analysis dashboard for book publishers inspired by "The Producers".
Provides comprehensive financial reporting, royalty calculation, and performance analytics.
"""

import pandas as pd
import streamlit as st
import os
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import glob
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


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# Optional imports
try:
    from currency_converter import CurrencyConverter
    CURRENCY_CONVERTER_AVAILABLE = True
except ImportError:
    CURRENCY_CONVERTER_AVAILABLE = False
    st.warning("⚠️ Currency converter not available. Install with: pip install currency_converter")

# Import following current patterns - UPDATED FOR NEW ARCHITECTURE
try:
    from codexes.modules.finance.core.user_data_manager import UserDataManager
    from codexes.modules.finance.core.fro_coordinator import FROCoordinator
    from codexes.modules.finance.ui.unified_uploader import UnifiedFinanceUploader
    from codexes.modules.finance.ui.source_display import DataSourceDisplay
    # Keep some legacy imports for compatibility during transition
    from codexes.modules.finance.leo_bloom.integrations.imprint_finance_integration import ImprintFinanceIntegration
except ModuleNotFoundError:
    from src.codexes.modules.finance.core.user_data_manager import UserDataManager
    from src.codexes.modules.finance.core.fro_coordinator import FROCoordinator
    from src.codexes.modules.finance.ui.unified_uploader import UnifiedFinanceUploader
    from src.codexes.modules.finance.ui.source_display import DataSourceDisplay
    try:
        from src.codexes.modules.finance.leo_bloom.integrations.imprint_finance_integration import ImprintFinanceIntegration
    except ModuleNotFoundError:
        ImprintFinanceIntegration = None

st.set_page_config(
    page_title="Max Bialystok Financial Analysis",
    page_icon="💰",
    layout="wide"
)

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



# Render unified sidebar
render_unified_sidebar(
    app_name="Codexes Factory",
    show_auth=True,
    show_xtuff_nav=True
)

    st.stop()

# Sync session state from shared auth
if is_authenticated():
    user_info = get_user_info()
    st.session_state.username = user_info.get('username')
    st.session_state.user_name = user_info.get('user_name')
    st.session_state.user_email = user_info.get('user_email')
    current_username = user_info.get('username')
    user_role = user_info.get('user_role', 'user')
    logger.info(f"User authenticated via shared auth: {current_username}")
else:
    st.error("🔒 Please log in to access financial data.")
    st.stop()

if user_role not in ['admin']:
    st.error("🚫 This page requires admin access.")
    st.stop()

# Page header
st.title("💰 Max Bialystok Financial Analysis")
st.markdown("*Financial Analysis Software for Book Publishers*")

# Initialize new architecture components
udm = UserDataManager(current_username)
fro_coord = FROCoordinator(udm)
uploader = UnifiedFinanceUploader(udm, fro_coord)
source_display = DataSourceDisplay()

# Get date variables from FRO coordinator
today, thisyear, starting_day_of_current_year, daysYTD, annualizer, this_year_month = fro_coord.get_date_variables()

# Legacy compatibility
deep_backlist_window = 60  # months
user_id = udm.user_id  # For backward compatibility with existing code

# Display current information
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Today", str(today)[:10] if hasattr(today, 'strftime') else str(today))
with col2:
    st.metric("Current Year", str(thisyear))
with col3:
    st.metric("Days YTD", str(daysYTD))

# Currency conversion
if CURRENCY_CONVERTER_AVAILABLE:
    try:
        c = CurrencyConverter()
        cgbp = c.convert(1, 'USD', 'GBP')
        st.info(f"Exchange Rate: 1 USD = {cgbp:.4f} GBP")
    except Exception as e:
        st.warning(f"Currency conversion unavailable: {e}")
else:
    st.info("💱 Currency conversion: 1 USD ≈ 0.82 GBP (static rate - install currency_converter for live rates)")

# Data Management Section using New Architecture
with st.expander("📋 Data Management & Upload", expanded=True):
    st.markdown("### Unified Financial Data Management")

    # Display current data sources
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### 📁 Data Sources Overview")

        # Get current data status from user data manager
        data_sources = {
            'LSI Data': udm.list_files('lsi_data'),
            'KDP Data': udm.list_files('kdp_data'),
            'Direct Sales': udm.list_files('direct_sales'),
            'Author Data': udm.list_files('author_data'),
            'Market Data': udm.list_files('market_data')
        }

        for source_type, files in data_sources.items():
            with st.container():
                col_icon, col_info = st.columns([1, 4])
                with col_icon:
                    if files:
                        st.success("✅")
                    else:
                        st.warning("⚠️")
                with col_info:
                    st.write(f"**{source_type}**: {len(files)} files")
                    if files:
                        latest_file = max(files, key=lambda x: x.get('modified', datetime.min))
                        st.caption(f"Latest: {latest_file.get('name', 'Unknown')}")

    with col2:
        st.markdown("#### 🛠 Quick Actions")
        if st.button("🔄 Refresh Data Sources", use_container_width=True):
            fro_coord.clear_cache()
            st.rerun()

        if st.button("📊 Process All Data", use_container_width=True):
            with st.spinner("Processing financial data..."):
                processed_data = fro_coord.process_user_data('all', force_refresh=True)
                if processed_data.get('processing_errors'):
                    st.error(f"Processing errors: {processed_data['processing_errors']}")
                else:
                    st.success("✅ All data processed successfully!")

    st.markdown("---")

    # Use the unified uploader
    st.markdown("#### 📤 Upload Financial Data")
    uploader.render_upload_interface()

# Imprint Filter Section (if integration available)
if ImprintFinanceIntegration:
    with st.expander("🎯 Imprint-Specific Analysis", expanded=False):
        try:
            integration = ImprintFinanceIntegration()
            integration.load_imprint_configurations()

            available_imprints = integration.get_available_imprints()

            if available_imprints:
                selected_imprint = st.selectbox(
                    "Filter by Imprint:",
                    options=["All Imprints"] + available_imprints,
                    help="Select an imprint to filter financial data"
                )

                if selected_imprint != "All Imprints":
                    st.info(f"🎯 Filtering data for: **{selected_imprint}**")

                    # Initialize financial reporting if not done yet
                    try:
                        integration.initialize_financial_reporting()

                        # Get imprint-specific financial data
                        imprint_data = integration.get_imprint_financial_data(selected_imprint)
                        if imprint_data is not None and not imprint_data.empty:
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                total_revenue = imprint_data.get('Net Compensation', pd.Series()).sum()
                                st.metric(f"{selected_imprint} Revenue", f"${total_revenue:,.2f}")

                            with col2:
                                total_units = imprint_data.get('Net Qty', pd.Series()).sum()
                                st.metric(f"{selected_imprint} Units", f"{total_units:,}")

                            with col3:
                                title_count = len(imprint_data)
                                st.metric(f"{selected_imprint} Titles", title_count)

                            # Quick access to detailed dashboard
                            if st.button(f"📊 Open Detailed Dashboard for {selected_imprint}"):
                                st.info("Navigate to the 'Imprint Financial Dashboard' page for detailed analysis")
                        else:
                            st.warning(f"No financial data found for {selected_imprint}")

                    except Exception as e:
                        st.warning(f"Could not load financial data: {e}")
                else:
                    st.info("Showing data for all imprints")
            else:
                st.warning("No imprint configurations found")

        except Exception as e:
            st.warning(f"Imprint integration not available: {e}")

# Main tabs
tab1, tab2 = st.tabs(["📊 Analysis", "💰 Royalties"])

with tab1:
    st.header("📈 Financial Analysis")

    # Get processed data from FRO coordinator
    with st.spinner("Loading financial data..."):
        display_data = fro_coord.get_display_data('summary', 'all')

    # Data source attribution
    with st.expander("📁 Data Sources & Attribution", expanded=False):
        source_display.render_source_info("Financial Analysis", display_data['source_attribution'])

    # Financial Overview Metrics
    with st.expander("💰 Financial Overview", expanded=True):
        if display_data['display_data']:
            col1, col2, col3, col4 = st.columns(4)

            # LSI Metrics
            lsi_summary = display_data['display_data'].get('lsi', {})
            if lsi_summary:
                with col1:
                    record_count = lsi_summary.get('total_records', 0)
                    st.metric("📊 LSI Records", f"{record_count:,}")

                date_range = lsi_summary.get('date_range', {})
                if date_range:
                    st.caption(f"Range: {date_range.get('start', 'N/A')} to {date_range.get('end', 'N/A')}")

            # KDP Metrics
            kdp_summary = display_data['display_data'].get('kdp', {})
            if kdp_summary:
                with col2:
                    kdp_records = kdp_summary.get('total_records', 0)
                    st.metric("📱 KDP Records", f"{kdp_records:,}")

            # Direct Sales Metrics
            direct_summary = display_data['display_data'].get('direct_sales', {})
            if direct_summary:
                with col3:
                    direct_records = direct_summary.get('total_records', 0)
                    st.metric("🛒 Direct Sales", f"{direct_records:,}")

            # Combined Metrics
            with col4:
                total_records = sum([
                    lsi_summary.get('total_records', 0),
                    kdp_summary.get('total_records', 0),
                    direct_summary.get('total_records', 0)
                ])
                st.metric("📈 Total Records", f"{total_records:,}")

        else:
            st.info("📋 No processed financial data available. Upload data files to begin analysis.")

    # Processing Status
    with st.expander("⚙️ Processing Status", expanded=False):
        if display_data.get('processing_errors'):
            st.error("⚠️ Processing Errors:")
            for error in display_data['processing_errors']:
                st.error(f"- {error}")
        else:
            st.success("✅ All data processed successfully")

        # Processing controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh All Data", use_container_width=True):
                with st.spinner("Refreshing all financial data..."):
                    fro_coord.clear_cache()
                    new_data = fro_coord.process_user_data('all', force_refresh=True)
                    st.success("Data refreshed successfully!")
                    st.rerun()

        with col2:
            data_type = st.selectbox("Process Specific Type", ['lsi', 'kdp', 'direct_sales', 'author_data'])
            if st.button(f"▶️ Process {data_type.upper()}", use_container_width=True):
                with st.spinner(f"Processing {data_type} data..."):
                    specific_data = fro_coord.process_user_data(data_type, force_refresh=True)
                    st.success(f"{data_type.upper()} data processed successfully!")

    # Revenue Analysis
    with st.expander("📈 Revenue Analysis", expanded=False):
        revenue_data = fro_coord.get_display_data('revenue', 'all')

        if revenue_data['display_data']:
            st.info("🕰 Revenue analysis will be implemented with specific FRO data structures")
            st.json(revenue_data['display_data'])  # Placeholder - will be replaced with charts
        else:
            st.info("📋 Upload financial data to see revenue analysis")

    # Performance Metrics
    with st.expander("🏆 Performance Metrics", expanded=False):
        st.info("Performance metrics will be calculated from processed FRO data")

        # Placeholder metrics grid
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Data Completeness", "85%", help="Percentage of expected data fields present")
        with col2:
            st.metric("Processing Health", "Good", help="Overall health of data processing pipeline")
        with col3:
            st.metric("Last Updated", str(today)[:10] if hasattr(today, 'strftime') else str(today), help="Most recent data processing timestamp")

with tab2:
    st.header("💰 Royalty Management")

    # Author data processing
    author_data = fro_coord.process_user_data('author_data')

    with st.expander("💳 Payments Data and Reporting", expanded=True):
        st.markdown("#### Payment Processing Status")

        if author_data.get('author_processed_data'):
            # Display processed author data
            for file_name, data_info in author_data['author_processed_data'].items():
                st.subheader(f"📄 {file_name}")

                summary = data_info.get('summary', {})
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Authors", summary.get('total_authors', 0))
                with col2:
                    st.metric("File Size", f"{summary.get('file_size', 0) / 1024:.1f} KB")
                with col3:
                    st.metric("Columns", len(summary.get('columns', [])))

                if 'data' in data_info and hasattr(data_info['data'], 'head'):
                    st.dataframe(data_info['data'].head(), use_container_width=True)

                    # Payment analysis
                    if any(col.lower() in ['amount', 'payment', 'royalty'] for col in data_info['data'].columns):
                        payment_col = next((col for col in data_info['data'].columns if col.lower() in ['amount', 'payment', 'royalty']), None)
                        if payment_col:
                            total_payments = data_info['data'][payment_col].sum()
                            st.metric(f"Total {payment_col}", f"${total_payments:.2f}")
        else:
            st.info("📋 No author payment data found. Upload author data files to see payment analysis.")

        # Data source attribution for royalty data
        st.markdown("---")
        st.markdown("#### 📁 Data Sources")
        source_display.render_source_info("Royalty Data", author_data.get('author_source_metadata', {}))

        # Quick actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Author Data", use_container_width=True):
                with st.spinner("Refreshing author data..."):
                    refreshed_data = fro_coord.process_user_data('author_data', force_refresh=True)
                    st.success("Author data refreshed!")
                    st.rerun()

        with col2:
            if st.button("📤 Upload Author Files", use_container_width=True):
                st.info("Use the 'Data Management & Upload' section above to upload author files.")

# Footer
st.markdown("---")
st.caption("Max Bialystok Financial Analysis - Inspired by 'The Producers'")
st.caption("💡 The inspired lunacy of Zero Mostel as Max Bialystok in the classic movie THE PRODUCERS.")