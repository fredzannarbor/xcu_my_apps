"""
version 1.1.0 - Migrated to shared authentication system

Leo Bloom Analytics Dashboard

Advanced financial analytics and reporting dashboard for publishers.
Provides deep-dive analysis into financial performance, trends, and insights.
"""


import pandas as pd
import streamlit as st
import logging
import plotly.express as px
import plotly.graph_objects as go
import os
import glob
from datetime import datetime, timedelta
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



# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)



# Import following current patterns - UPDATED FOR NEW ARCHITECTURE
try:
    from codexes.modules.finance.core.user_data_manager import UserDataManager
    from codexes.modules.finance.core.fro_coordinator import FROCoordinator
    from codexes.modules.finance.ui.unified_uploader import UnifiedFinanceUploader
    from codexes.modules.finance.ui.source_display import DataSourceDisplay
    # Keep legacy FRO imports for advanced analytics
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects import FinancialReportingObjects as FRO
    from codexes.modules.finance.leo_bloom.utilities import classes_utilities as Leo
except ModuleNotFoundError:
    from src.codexes.modules.finance.core.user_data_manager import UserDataManager
    from src.codexes.modules.finance.core.fro_coordinator import FROCoordinator
    from src.codexes.modules.finance.ui.unified_uploader import UnifiedFinanceUploader
    from src.codexes.modules.finance.ui.source_display import DataSourceDisplay
    from src.codexes.modules.finance.leo_bloom.FinancialReportingObjects import FinancialReportingObjects as FRO
    from src.codexes.modules.finance.leo_bloom.utilities import classes_utilities as Leo

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




# Page header
st.title("📊 Leo Bloom Analytics Dashboard")
st.markdown("*Advanced Financial Analytics for Book Publishers*")

# Authentication and user setup - NEW ARCHITECTURE
# Shared auth initialized in header
if not is_authenticated():
    st.error("🔒 Please log in to access financial analytics.")
    st.stop()

current_username = get_user_info().get('username')
user_role = get_user_info().get('user_role', 'user')

if user_role not in ['admin']:
    st.error("🚫 This page requires admin access.")
    st.stop()

# Initialize new architecture components
udm = UserDataManager(current_username)
fro_coord = FROCoordinator(udm)
uploader = UnifiedFinanceUploader(udm, fro_coord)
source_display = DataSourceDisplay()

# Sidebar controls
st.sidebar.header("Analytics Controls")
analysis_period = st.sidebar.selectbox(
    "Analysis Period",
    ["YTD", "Last 12 Months", "Last 24 Months", "All Time"]
)

frontlist_window = st.sidebar.slider(
    "Frontlist Window (months)",
    min_value=6,
    max_value=36,
    value=18,
    help="Number of months to consider for frontlist analysis"
)

# Data type filter
data_type_filter = st.sidebar.multiselect(
    "Data Sources",
    ["LSI Data", "KDP Data", "Direct Sales", "Author Data"],
    default=["LSI Data", "KDP Data"],
    help="Select which data sources to include in analysis"
)

# Data Management Section
with st.expander("📊 Advanced Data Analytics & Management", expanded=False):
    st.markdown("### Analytics Data Sources & Upload")

    # Get current data status from user data manager
    col1, col2 = st.columns([2, 1])

    with col1:
        # Display comprehensive data status
        data_categories = ['lsi_data', 'kdp_data', 'direct_sales', 'author_data', 'market_data']

        for category in data_categories:
            files = udm.list_files(category)

            with st.container():
                category_name = category.replace('_', ' ').title()

                if files:
                    st.success(f"✅ **{category_name}**: {len(files)} files")

                    # Show latest file details
                    if files:
                        latest_file = max(files, key=lambda x: x.get('modified', datetime.min))
                        col_a, col_b, col_c = st.columns(3)

                        with col_a:
                            st.caption(f"Latest: {latest_file.get('name', 'Unknown')}")
                        with col_b:
                            size_mb = latest_file.get('size', 0) / (1024*1024)
                            st.caption(f"Size: {size_mb:.1f} MB")
                        with col_c:
                            mod_date = latest_file.get('modified', datetime.min)
                            if isinstance(mod_date, datetime):
                                st.caption(f"Modified: {mod_date.strftime('%Y-%m-%d')}")
                else:
                    st.warning(f"⚠️ **{category_name}**: No files")

    with col2:
        st.markdown("#### 🎯 Analytics Actions")

        if st.button("🔄 Refresh All Analytics", use_container_width=True):
            fro_coord.clear_cache()
            st.success("Analytics cache cleared!")
            st.rerun()

        if st.button("📈 Process Advanced Analytics", use_container_width=True):
            with st.spinner("Processing advanced analytics..."):
                # Process all data types for analytics
                analytics_data = fro_coord.process_user_data('all', force_refresh=True)
                st.success("Advanced analytics processed!")

    st.markdown("---")

    # Use unified uploader
    st.markdown("#### 📤 Upload Analytics Data")
    uploader.render_upload_interface()

# Main Analytics Content
st.markdown("---")

# Get processed data for analytics
with st.spinner("Loading analytics data..."):
    display_data = fro_coord.get_display_data('summary', 'all')

# Analytics Overview
st.header("📈 Analytics Overview")

if display_data.get('display_data'):
    # Key Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)

    # Extract metrics from processed data
    lsi_summary = display_data['display_data'].get('lsi', {})
    kdp_summary = display_data['display_data'].get('kdp', {})
    direct_summary = display_data['display_data'].get('direct_sales', {})

    with col1:
        lsi_records = lsi_summary.get('total_records', 0)
        st.metric("📊 LSI Records", f"{lsi_records:,}")

    with col2:
        kdp_records = kdp_summary.get('total_records', 0)
        st.metric("📱 KDP Records", f"{kdp_records:,}")

    with col3:
        direct_records = direct_summary.get('total_records', 0)
        st.metric("🛒 Direct Sales", f"{direct_records:,}")

    with col4:
        total_records = lsi_records + kdp_records + direct_records
        st.metric("📈 Total Records", f"{total_records:,}")

    with col5:
        # Calculate data completeness
        expected_sources = len([s for s in data_type_filter])
        available_sources = len([s for s in [lsi_summary, kdp_summary, direct_summary] if s.get('total_records', 0) > 0])
        completeness = (available_sources / max(expected_sources, 1)) * 100
        st.metric("✓ Data Completeness", f"{completeness:.0f}%")

    # Data Source Attribution
    with st.expander("📁 Analytics Data Sources", expanded=False):
        source_display.render_source_info("Leo Bloom Analytics", display_data['source_attribution'])

else:
    st.info("📋 No analytics data available. Upload financial data files to begin advanced analysis.")

# Analytics Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Performance Analytics", "📈 Trend Analysis", "💰 Revenue Insights", "⚙️ Data Quality"])

with tab1:
    st.header("Performance Analytics")

    if display_data.get('display_data'):
        # Performance metrics based on processed data
        st.subheader("📊 Channel Performance")

        # Create performance comparison chart
        performance_data = []

        if lsi_summary:
            performance_data.append({"Channel": "LSI", "Records": lsi_summary.get('total_records', 0), "Columns": len(lsi_summary.get('columns', []))})

        if kdp_summary:
            performance_data.append({"Channel": "KDP", "Records": kdp_summary.get('total_records', 0), "Columns": len(kdp_summary.get('columns', []))})

        if direct_summary:
            performance_data.append({"Channel": "Direct Sales", "Records": direct_summary.get('total_records', 0), "Columns": len(direct_summary.get('columns', []))})

        if performance_data:
            perf_df = pd.DataFrame(performance_data)

            col1, col2 = st.columns(2)

            with col1:
                fig = px.bar(perf_df, x="Channel", y="Records", title="Records by Channel", color="Channel")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.pie(perf_df, values="Records", names="Channel", title="Records Distribution")
                st.plotly_chart(fig, use_container_width=True)

        # Additional analytics would go here based on actual FRO data structure
        st.info("📊 Advanced performance analytics will be implemented based on specific FRO data structures")

    else:
        st.info("📋 Upload financial data to see performance analytics")

with tab2:
    st.header("Trend Analysis")

    if display_data.get('display_data') and lsi_summary.get('date_range'):
        st.subheader("📅 Data Timeline")

        date_range = lsi_summary.get('date_range', {})
        if date_range.get('start') and date_range.get('end'):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Data Start", str(date_range.get('start', 'N/A')))
            with col2:
                st.metric("Data End", str(date_range.get('end', 'N/A')))
            with col3:
                # Calculate data span
                try:
                    start_date = pd.to_datetime(date_range.get('start'))
                    end_date = pd.to_datetime(date_range.get('end'))
                    span_days = (end_date - start_date).days
                    st.metric("Data Span", f"{span_days} days")
                except:
                    st.metric("Data Span", "N/A")

        st.info("📈 Advanced trend analysis will be implemented with time-series data from FRO objects")
    else:
        st.info("📋 Upload time-series financial data to see trend analysis")

with tab3:
    st.header("Revenue Insights")

    # Revenue analysis using FRO coordinator
    revenue_data = fro_coord.get_display_data('revenue', 'all')

    if revenue_data.get('display_data'):
        st.subheader("💰 Revenue Breakdown")
        st.info("💰 Revenue insights will be calculated from processed FRO financial data")

        # Placeholder for revenue analysis
        st.json(revenue_data['display_data'])  # Will be replaced with charts and analysis
    else:
        st.info("📋 Upload revenue data to see detailed financial insights")

with tab4:
    st.header("Data Quality Dashboard")

    # Enhanced data quality analysis
    st.subheader("🔍 Data Quality Assessment")

    if display_data.get('processing_errors'):
        st.error("⚠️ Data Quality Issues Detected:")
        for error in display_data['processing_errors']:
            st.error(f"- {error}")
    else:
        st.success("✅ No data quality issues detected")

    # Data quality metrics
    quality_metrics = []

    for data_type, summary in display_data.get('display_data', {}).items():
        if isinstance(summary, dict) and 'total_records' in summary:
            quality_score = 100  # Default good quality
            issues = []

            # Assess quality based on available data
            if summary.get('total_records', 0) == 0:
                quality_score = 0
                issues.append("No data")
            elif summary.get('total_records', 0) < 100:
                quality_score = 60
                issues.append("Limited data")

            quality_metrics.append({
                'Data Type': data_type.upper(),
                'Records': summary.get('total_records', 0),
                'Columns': len(summary.get('columns', [])),
                'Quality Score': quality_score,
                'Issues': ', '.join(issues) if issues else 'Good'
            })

    if quality_metrics:
        quality_df = pd.DataFrame(quality_metrics)

        col1, col2 = st.columns(2)

        with col1:
            st.dataframe(quality_df, use_container_width=True)

        with col2:
            fig = px.bar(quality_df, x='Data Type', y='Quality Score',
                        title='Data Quality Scores', color='Quality Score',
                        color_continuous_scale='RdYlGn')
            st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.caption("Leo Bloom Analytics - Advanced Financial Intelligence")
st.caption("💡 Named after Gene Wilder's Leo Bloom character from 'The Producers'")