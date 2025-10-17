"""
version 1.1.0 - Migrated to shared authentication system

FRO Diagnostics Dashboard

Shows all valid Financial Reporting Objects (FROs) using current data
and reports on what data is missing to create invalid FROs.
"""

import pandas as pd
import streamlit as st
from datetime import datetime
from pathlib import Path
import json
import logging
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


# Import following current patterns - NEW ARCHITECTURE
try:
    from codexes.modules.finance.core.user_data_manager import UserDataManager
    from codexes.modules.finance.core.fro_coordinator import FROCoordinator
    from codexes.modules.finance.ui.source_display import DataSourceDisplay
    from codexes.core.dataframe_utils import safe_dataframe_display
    # Import FRO classes for validation
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.LifetimePaidCompensation import LifetimePaidCompensation
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.KDP_Financial_Reporting_Objects import Ingest_KDP_by_Month
except ModuleNotFoundError:
    from src.codexes.modules.finance.core.user_data_manager import UserDataManager
    from src.codexes.modules.finance.core.fro_coordinator import FROCoordinator
    from src.codexes.modules.finance.ui.source_display import DataSourceDisplay
    from src.codexes.core.dataframe_utils import safe_dataframe_display
    from src.codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects
    from src.codexes.modules.finance.leo_bloom.FinancialReportingObjects.LifetimePaidCompensation import LifetimePaidCompensation
    from src.codexes.modules.finance.leo_bloom.FinancialReportingObjects.KDP_Financial_Reporting_Objects import Ingest_KDP_by_Month

st.set_page_config(
    page_title="FRO Diagnostics",
    page_icon="🔬",
    layout="wide"
)

# Page header
st.title("🔬 FRO Diagnostics Dashboard")
st.markdown("*Comprehensive analysis of Financial Reporting Objects (FROs) validity and data requirements*")

# Authentication and user setup
# Shared auth initialized in header
if not is_authenticated():
    st.error("🔒 Please log in to access FRO diagnostics.")
    st.stop()

current_username = get_user_info().get('username')
user_role = get_user_info().get('user_role', 'user')

if user_role not in ['admin']:
    st.error("🚫 This page requires admin access.")
    st.stop()

# Initialize new architecture components
udm = UserDataManager(current_username)
fro_coord = FROCoordinator(udm)
source_display = DataSourceDisplay()

# Clear any cached data to ensure fresh diagnostics
fro_coord._cache.clear()

logger = logging.getLogger(__name__)

# FRO definitions and requirements
FRO_DEFINITIONS = {
    'LSI Lifetime Compensation': {
        'class': 'LifetimePaidCompensation',
        'description': 'Lifetime paid compensation data from Lightning Source/IngramSpark',
        'required_data': 'lsi_data',
        'required_columns': ['ISBN', 'Title', 'Author', 'Format', 'Gross Qty', 'Returned Qty', 'Net Qty', 'Net Compensation', 'Sales Market'],
        'min_records': 1,
        'data_path': 'userdocs_lsidata_path'
    },
    'KDP Monthly Ingestion': {
        'class': 'Ingest_KDP_by_Month',
        'description': 'Monthly KDP royalty and sales data ingestion',
        'required_data': 'kdp_data',
        'required_columns': ['ASIN/ISBN', 'Title', 'Author Name', 'Marketplace', 'Units Sold', 'Royalty', 'Currency'],
        'min_records': 1,
        'data_path': 'userdocs_kdpdata_path'
    },
    'Direct Sales Processing': {
        'class': 'DirectSalesProcessor',
        'description': 'Direct sales data processing and royalty calculation',
        'required_data': 'direct_sales',
        'required_columns': ['ASIN/ISBN', 'Title', 'royaltied_author_id', 'YTD_net_quantity', 'USDeq_pub_comp'],
        'min_records': 1,
        'data_path': 'userdocs_directsales_path'
    },
    'Author Data Management': {
        'class': 'AuthorDataManager',
        'description': 'Author contracts and royalty rate management',
        'required_data': 'author_data',
        'required_columns': ['royaltied_author_id', 'Author', 'Title', 'Royalty Rate'],
        'min_records': 1,
        'data_path': 'userdocs_authordata_path'
    },
    'LSI Metadata Base': {
        'class': 'LSIMetadataManager',
        'description': 'LSI books in print status and metadata management',
        'required_data': 'lsi_metadata',
        'required_columns': ['ISBN', 'Title', 'Contributor 1 Name', 'Status', 'Format'],
        'min_records': 1,
        'data_path': 'userdocs_lsimetadata_path'
    }
}

# Diagnostic functions
def check_fro_validity(fro_name: str, fro_config: dict, udm: UserDataManager, fro_coord: FROCoordinator) -> dict:
    """Check if an FRO can be created with current data."""
    result = {
        'name': fro_name,
        'status': 'unknown',
        'issues': [],
        'data_summary': {},
        'recommendations': []
    }

    try:
        # Check if required data exists
        required_data_type = fro_config['required_data']
        files = udm.list_files(required_data_type)

        if not files:
            result['status'] = 'invalid'
            result['issues'].append(f"No {required_data_type} files found")
            result['recommendations'].append(f"Upload {required_data_type} files to enable this FRO")
            return result

        # Process data through FRO coordinator
        processed_data = fro_coord.process_user_data(required_data_type)

        # Debug logging
        logger.info(f"FRO {fro_name}: Processing result keys: {processed_data.keys()}")

        # Check for processing errors
        if processed_data.get('processing_errors'):
            result['status'] = 'invalid'
            result['issues'].extend(processed_data['processing_errors'])
            result['recommendations'].append("Fix data format issues and re-upload files")
            return result

        # Check if processed data exists - map data types to actual keys
        key_mapping = {
            'lsi_data': 'lsi_processed_data',
            'kdp_data': 'kdp_processed_data',
            'direct_sales': 'direct_sales_processed_data',
            'author_data': 'author_processed_data',
            'lsi_metadata': 'lsi_metadata_processed_data'
        }
        processed_key = key_mapping.get(required_data_type, f'{required_data_type}_processed_data')
        logger.info(f"FRO {fro_name}: Looking for key '{processed_key}' in result")

        if not processed_data.get(processed_key):
            result['status'] = 'invalid'
            result['issues'].append("Data processing failed - no processed data available")
            result['recommendations'].append("Check data format and processing logs")
            logger.info(f"FRO {fro_name}: Key '{processed_key}' not found or empty")
            return result

        # Get data summary
        data_info = processed_data[processed_key]
        if isinstance(data_info, dict) and 'summary' in data_info:
            result['data_summary'] = data_info['summary']

            # Check minimum record requirements
            total_records = data_info['summary'].get('total_records', 0)
            if total_records < fro_config['min_records']:
                result['status'] = 'invalid'
                result['issues'].append(f"Insufficient records: {total_records} (minimum: {fro_config['min_records']})")
                result['recommendations'].append("Upload more data to meet minimum record requirements")
                return result

            # Check for required columns
            available_columns = data_info['summary'].get('columns', [])
            required_columns = fro_config['required_columns']
            missing_columns = set(required_columns) - set(available_columns)

            if missing_columns:
                result['status'] = 'invalid'
                result['issues'].append(f"Missing required columns: {', '.join(missing_columns)}")
                result['recommendations'].append("Ensure data files contain all required columns")
                return result

        # If we get here, FRO should be valid
        result['status'] = 'valid'
        result['data_summary'].update({
            'files_count': len(files),
            'last_updated': max(f['upload_time'] for f in files) if files else 'Never'
        })

    except Exception as e:
        result['status'] = 'error'
        result['issues'].append(f"Diagnostic error: {str(e)}")
        result['recommendations'].append("Check system logs and contact support")
        logger.error(f"Error checking FRO {fro_name}: {e}")

    return result

# Main diagnostic analysis
st.header("🔬 FRO System Diagnostics")

with st.spinner("Running comprehensive FRO diagnostics..."):
    diagnostic_results = []

    for fro_name, fro_config in FRO_DEFINITIONS.items():
        result = check_fro_validity(fro_name, fro_config, udm, fro_coord)
        diagnostic_results.append(result)

# Display results
st.subheader("📊 FRO Status Overview")

# Status metrics
valid_count = sum(1 for r in diagnostic_results if r['status'] == 'valid')
invalid_count = sum(1 for r in diagnostic_results if r['status'] == 'invalid')
error_count = sum(1 for r in diagnostic_results if r['status'] == 'error')

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("✅ Valid FROs", valid_count)
with col2:
    st.metric("❌ Invalid FROs", invalid_count)
with col3:
    st.metric("🔥 Error FROs", error_count)
with col4:
    system_health = "Good" if valid_count > invalid_count else "Needs Attention"
    st.metric("🏥 System Health", system_health)

# Detailed FRO status
st.subheader("🔍 Detailed FRO Analysis")

for result in diagnostic_results:
    fro_config = FRO_DEFINITIONS[result['name']]

    if result['status'] == 'valid':
        with st.expander(f"✅ {result['name']} - Valid", expanded=False):
            st.success(f"**Status**: {result['status'].upper()}")
            st.write(f"**Description**: {fro_config['description']}")

            # Data summary
            if result['data_summary']:
                st.write("**Data Summary**:")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Files", result['data_summary'].get('files_count', 0))
                with col2:
                    st.metric("Records", result['data_summary'].get('total_records', 0))
                with col3:
                    last_updated = result['data_summary'].get('last_updated', 'Never')
                    if isinstance(last_updated, str) and last_updated != 'Never' and len(last_updated) >= 10:
                        last_updated = last_updated[:10]  # Show date only
                    st.metric("Last Updated", last_updated)

                # Column availability
                available_columns = result['data_summary'].get('columns', [])
                required_columns = fro_config['required_columns']
                st.write(f"**Columns Available**: {len(available_columns)}/{len(required_columns)}")
                st.write(f"**Required Columns**: {', '.join(required_columns)}")

    elif result['status'] == 'invalid':
        with st.expander(f"❌ {result['name']} - Invalid", expanded=True):
            st.error(f"**Status**: {result['status'].upper()}")
            st.write(f"**Description**: {fro_config['description']}")

            # Issues
            if result['issues']:
                st.write("**Issues Found**:")
                for issue in result['issues']:
                    st.write(f"• {issue}")

            # Recommendations
            if result['recommendations']:
                st.write("**Recommendations**:")
                for rec in result['recommendations']:
                    st.write(f"• {rec}")

            # Requirements
            st.write("**Requirements**:")
            st.write(f"• **Data Type**: {fro_config['required_data']}")
            st.write(f"• **Required Columns**: {', '.join(fro_config['required_columns'])}")
            st.write(f"• **Minimum Records**: {fro_config['min_records']}")

    else:  # error status
        with st.expander(f"🔥 {result['name']} - Error", expanded=True):
            st.error(f"**Status**: {result['status'].upper()}")
            st.write(f"**Description**: {fro_config['description']}")

            if result['issues']:
                st.write("**Error Details**:")
                for issue in result['issues']:
                    st.write(f"• {issue}")

            if result['recommendations']:
                st.write("**Recommendations**:")
                for rec in result['recommendations']:
                    st.write(f"• {rec}")

# Data Upload Status
st.subheader("📁 Data Upload Status")

data_categories = ['lsi_data', 'lsi_metadata', 'kdp_data', 'direct_sales', 'author_data', 'market_data']
upload_status = []

for category in data_categories:
    files = udm.list_files(category)
    metadata = udm.get_data_source_metadata(category)

    # Handle last_updated safely
    last_updated = metadata.get('last_updated', 'Never')
    if last_updated and last_updated != 'Never' and isinstance(last_updated, str) and len(last_updated) >= 10:
        last_updated_display = last_updated[:10]
    else:
        last_updated_display = 'Never'

    upload_status.append({
        'Data Type': category.replace('_', ' ').title(),
        'Files Count': len(files),
        'Last Updated': last_updated_display,
        'Status': '✅ Available' if files else '❌ Missing'
    })

upload_df = pd.DataFrame(upload_status)
safe_dataframe_display(upload_df, width='stretch', hide_index=True)

# System Recommendations
st.subheader("💡 System Recommendations")

all_recommendations = []
for result in diagnostic_results:
    if result['status'] != 'valid':
        all_recommendations.extend(result['recommendations'])

if all_recommendations:
    # Remove duplicates while preserving order
    unique_recommendations = list(dict.fromkeys(all_recommendations))

    for i, rec in enumerate(unique_recommendations, 1):
        st.write(f"{i}. {rec}")
else:
    st.success("🎉 All FROs are valid! Your financial reporting system is fully operational.")

# Data Quality Score
st.subheader("🏆 Data Quality Score")

# Calculate overall score
total_fros = len(diagnostic_results)
quality_score = (valid_count / total_fros) * 100 if total_fros > 0 else 0

col1, col2 = st.columns(2)
with col1:
    # Create a visual quality score display
    st.write("**Data Quality Score**")

    # Progress bar visualization
    progress_color = "🟢" if quality_score >= 80 else "🟡" if quality_score >= 60 else "🔴"
    st.write(f"{progress_color} **{quality_score:.1f}%**")

    # Create progress bar
    st.progress(quality_score / 100)

    # Score interpretation
    if quality_score >= 90:
        st.success("🌟 Excellent")
    elif quality_score >= 80:
        st.success("✅ Good")
    elif quality_score >= 60:
        st.warning("⚠️ Fair")
    else:
        st.error("🚨 Poor")

with col2:
    st.write("**Quality Score Breakdown**:")
    st.write(f"• Valid FROs: {valid_count}/{total_fros}")
    st.write(f"• Success Rate: {quality_score:.1f}%")

    if quality_score >= 90:
        st.success("🌟 Excellent! Your data quality is outstanding.")
    elif quality_score >= 70:
        st.warning("⚠️ Good, but some improvements needed.")
    else:
        st.error("🚨 Poor data quality. Immediate attention required.")

# Book Metadata Display
st.subheader("📚 Book Metadata (Enhanced)")

# Get LSI data if available
try:
    lsi_result = fro_coord.process_user_data('lsi_data')
    if 'lsi_processed_data' in lsi_result and lsi_result['lsi_processed_data']:
        lsi_data = lsi_result['lsi_processed_data']['raw_data']

        st.write(f"**Available Book Records**: {len(lsi_data)} books")

        # Add filtering options
        col1, col2, col3 = st.columns(3)

        with col1:
            # Filter by author
            authors = sorted(lsi_data['Author'].unique())
            selected_author = st.selectbox(
                "Filter by Author",
                ['All'] + authors,
                key="fro_author_filter"
            )

        with col2:
            # Filter by format
            formats = sorted(lsi_data['Format'].unique())
            selected_format = st.selectbox(
                "Filter by Format",
                ['All'] + formats,
                key="fro_format_filter"
            )

        with col3:
            # Filter by minimum sales
            min_sales = st.number_input(
                "Minimum Net Sales",
                min_value=0,
                value=0,
                key="fro_min_sales"
            )

        # Apply filters
        filtered_data = lsi_data.copy()

        if selected_author != 'All':
            filtered_data = filtered_data[filtered_data['Author'] == selected_author]

        if selected_format != 'All':
            filtered_data = filtered_data[filtered_data['Format'] == selected_format]

        if min_sales > 0:
            filtered_data = filtered_data[filtered_data['Net Qty'] >= min_sales]

        # Display summary metrics
        if not filtered_data.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Books", len(filtered_data))
            with col2:
                st.metric("Total Net Sales", f"{filtered_data['Net Qty'].sum():,}")
            with col3:
                st.metric("Total Compensation", f"${filtered_data['Net Compensation'].sum():,.2f}")
            with col4:
                avg_comp = filtered_data['Net Compensation'].mean()
                st.metric("Avg Compensation", f"${avg_comp:.2f}")

            # Display the data table
            st.write("**Book Details:**")
            # Sort by net compensation (highest first)
            display_data = filtered_data.sort_values('Net Compensation', ascending=False)
            safe_dataframe_display(display_data, use_container_width=True, hide_index=True)

        else:
            st.warning("No books found matching the selected filters.")
    else:
        st.info("📝 No LSI book data available. Upload LSI compensation files to see book metadata.")

except Exception as e:
    st.error(f"Error loading book metadata: {e}")
    logger.error(f"Error in book metadata display: {e}")

# Data Sources Attribution
st.markdown("---")
with st.expander("📁 Data Sources & Attribution", expanded=False):
    all_metadata = udm.get_data_source_metadata()
    source_display.render_source_info("FRO Diagnostics", all_metadata)

# Footer
st.markdown("---")
st.caption("FRO Diagnostics Dashboard - Financial Reporting Objects System Analysis")
st.caption("💡 This dashboard helps ensure all Financial Reporting Objects have the data they need to function properly")