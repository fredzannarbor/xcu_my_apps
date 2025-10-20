"""
version 1.1.0 - Migrated to shared authentication system

Sales Analysis Dashboard

Displays all books with sales data, sorted by date, with calculations for days in print.
Shows revenue data and identifies missing data issues.
"""


import pandas as pd
import streamlit as st
import logging
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
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



# Import following current patterns - NEW ARCHITECTURE
try:
    from codexes.modules.finance.core.user_data_manager import UserDataManager
    from codexes.modules.finance.core.fro_coordinator import FROCoordinator
    from codexes.modules.finance.ui.source_display import DataSourceDisplay
    from codexes.core.dataframe_utils import safe_dataframe_display
except ModuleNotFoundError:
    from src.codexes.modules.finance.core.user_data_manager import UserDataManager
    from src.codexes.modules.finance.core.fro_coordinator import FROCoordinator
    from src.codexes.modules.finance.ui.source_display import DataSourceDisplay
    from src.codexes.core.dataframe_utils import safe_dataframe_display

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
st.title("📊 Sales Analysis Dashboard")
st.markdown("*Comprehensive analysis of book sales data with days in print calculations*")

# Authentication and user setup
# Shared auth initialized in header
if not is_authenticated():
    st.error("🔒 Please log in to access sales analysis.")
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

# Get date variables
today, thisyear, starting_day_of_current_year, daysYTD, annualizer, this_year_month = fro_coord.get_date_variables()
today_datetime = datetime.now()

# Sidebar controls
st.sidebar.header("Analysis Controls")
show_days_threshold = st.sidebar.slider(
    "Minimum Days in Print",
    min_value=0,
    max_value=365,
    value=91,
    help="Show only books with at least this many days in print"
)

sales_threshold = st.sidebar.number_input(
    "Minimum Net Sales ($)",
    min_value=0.0,
    value=0.0,
    help="Show only books with sales above this threshold"
)

# Data Processing Section - Load Both LSI and KDP
with st.spinner("Loading and processing sales data..."):
    # Get processed data from FRO coordinator
    processed_data = fro_coord.process_user_data('lsi', force_refresh=False)

    # Get KDP data
    kdp_result = fro_coord.process_user_data('kdp_data')

# Consolidated Views Section - MOVED TO TOP
st.header("🔗 Consolidated & Merged Analysis")

# Check if both LSI and KDP data are available
try:
    lsi_available = 'lsi_processed_data' in processed_data and processed_data['lsi_processed_data']
    kdp_available = 'kdp_processed_data' in kdp_result and kdp_result['kdp_processed_data']

    if lsi_available or kdp_available:
        # Create tabs for different consolidated views
        tab1, tab2, tab3 = st.tabs(["📊 LSI by Title", "📱 KDP by Title", "🔗 Merged LSI+KDP"])

        # LSI Consolidated by Title
        with tab1:
            if lsi_available:
                st.subheader("📊 LSI Data Consolidated by Title")
                raw_lsi_df = processed_data['lsi_processed_data']['raw_data']

                # Group by Title and sum key metrics
                lsi_consolidated = raw_lsi_df.groupby(['Title', 'Author']).agg({
                    'Net Qty': 'sum',
                    'Gross Qty': 'sum',
                    'Returned Qty': 'sum',
                    'Net Compensation': 'sum',
                    'ISBN': lambda x: list(x.unique()),  # Collect all ISBNs for this title
                    'Format': lambda x: list(x.unique())  # Collect all formats
                }).reset_index()

                # Add calculated fields
                lsi_consolidated['Return_Rate'] = (lsi_consolidated['Returned Qty'] / lsi_consolidated['Gross Qty'].replace(0, 1)) * 100
                lsi_consolidated['Revenue_per_Unit'] = lsi_consolidated['Net Compensation'] / lsi_consolidated['Net Qty'].replace(0, 1)
                lsi_consolidated['ISBN_Count'] = lsi_consolidated['ISBN'].apply(len)
                lsi_consolidated['Format_Count'] = lsi_consolidated['Format'].apply(len)

                # Display summary
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📚 Unique Titles", len(lsi_consolidated))
                with col2:
                    st.metric("💰 Total Compensation", f"${lsi_consolidated['Net Compensation'].sum():,.2f}")
                with col3:
                    st.metric("📖 Total Units Sold", f"{lsi_consolidated['Net Qty'].sum():,}")
                with col4:
                    st.metric("📈 Avg Return Rate", f"{lsi_consolidated['Return_Rate'].mean():.1f}%")

                # Sort by compensation
                lsi_consolidated_sorted = lsi_consolidated.sort_values('Net Compensation', ascending=False)

                # Display consolidated data
                display_cols = ['Title', 'Author', 'Net Qty', 'Net Compensation', 'Revenue_per_Unit', 'Return_Rate', 'ISBN_Count', 'Format_Count']
                st.dataframe(lsi_consolidated_sorted[display_cols], use_container_width=True)

                # Export
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_data = lsi_consolidated_sorted.to_csv(index=False)
                st.download_button(
                    label="📥 Export LSI Consolidated as CSV",
                    data=csv_data,
                    file_name=f"lsi_consolidated_by_title_{timestamp}.csv",
                    mime="text/csv"
                )
            else:
                st.info("LSI data not available for consolidation")

        # KDP Consolidated by Title
        with tab2:
            if kdp_available:
                st.subheader("📱 KDP Data Consolidated by Title")
                # Get KDP raw data from destination-based structure
                kdp_processed = kdp_result['kdp_processed_data']
                kdp_raw_data = None
                for dest_key, dest_data in kdp_processed.items():
                    if isinstance(dest_data, dict) and 'raw_data' in dest_data:
                        kdp_raw_data = dest_data['raw_data']
                        break

                if kdp_raw_data is None:
                    st.error("❌ KDP raw data not found in processed structure")
                    st.stop()

                # Check if currency conversion has been applied
                has_usd_conversion = 'USDeq_Royalty' in kdp_raw_data.columns

                if not has_usd_conversion:
                    st.warning("⚠️ KDP data does not include USD currency conversion. Attempting to convert currencies now...")

                    # Try to do currency conversion on-the-fly
                    try:
                        from datetime import datetime
                        from currency_converter import CurrencyConverter

                        # Check if we have the required columns for conversion
                        required_cols = ['Royalty Date', 'Currency', 'Royalty']
                        missing_cols = [col for col in required_cols if col not in kdp_raw_data.columns]

                        if missing_cols:
                            st.error(f"❌ Cannot perform currency conversion. Missing columns: {missing_cols}")
                            st.stop()

                        # Initialize currency converter
                        c = CurrencyConverter()

                        # Get the currency converter's date bounds
                        try:
                            usd_first_date, usd_last_date = c.bounds['USD']
                            st.info(f"Currency data available from {usd_first_date} to {usd_last_date}")
                        except:
                            # Default bounds if we can't get them
                            usd_first_date = datetime(1999, 1, 4).date()
                            usd_last_date = datetime(2025, 7, 28).date()

                        # Add first day of month date for conversion
                        def parse_royalty_date(date_str):
                            try:
                                target_date = datetime.strptime(str(date_str), '%Y-%m').replace(day=1).date()
                            except:
                                # Fallback - try other formats or use current date
                                try:
                                    target_date = datetime.strptime(str(date_str)[:7], '%Y-%m').replace(day=1).date()
                                except:
                                    target_date = datetime.now().replace(day=1).date()

                            # Clamp date to available range
                            if target_date > usd_last_date:
                                return usd_last_date
                            elif target_date < usd_first_date:
                                return usd_first_date
                            else:
                                return target_date

                        kdp_raw_data['conversion_date'] = kdp_raw_data['Royalty Date'].apply(parse_royalty_date)

                        # Get current exchange rates (most recent available) for fallback
                        current_rates = {}
                        try:
                            for currency in ['GBP', 'EUR', 'JPY', 'AUD', 'CAD', 'BRL', 'MXN', 'INR']:
                                try:
                                    # Get the most recent rate available
                                    current_rates[currency] = c.convert(1, currency, 'USD', date=usd_last_date)
                                except:
                                    # Static fallback rates if we can't get current ones
                                    static_rates = {
                                        'GBP': 1.28, 'EUR': 1.09, 'JPY': 0.0067, 'AUD': 0.66,
                                        'CAD': 0.73, 'BRL': 0.18, 'MXN': 0.056, 'INR': 0.012
                                    }
                                    current_rates[currency] = static_rates.get(currency, 1.0)
                            current_rates['USD'] = 1.0
                        except Exception as e:
                            st.warning(f"Could not fetch current rates: {e}")
                            # Use static fallback rates
                            current_rates = {
                                'USD': 1.0, 'GBP': 1.28, 'EUR': 1.09, 'JPY': 0.0067,
                                'AUD': 0.66, 'CAD': 0.73, 'BRL': 0.18, 'MXN': 0.056, 'INR': 0.012
                            }

                        # Convert to USD with robust fallback
                        def safe_convert_to_usd(row):
                            if row['Currency'] == 'USD':
                                return row['Royalty']

                            currency = row['Currency']
                            original_date = row['conversion_date']

                            try:
                                # Try currency converter first with the clamped date
                                return c.convert(row['Royalty'], currency, 'USD', date=original_date)

                            except Exception as e:
                                # Use current rates as fallback for future dates or missing data
                                if currency in current_rates:
                                    converted = row['Royalty'] * current_rates[currency]
                                    # Only show warning once per currency type
                                    if not hasattr(safe_convert_to_usd, 'warned_currencies'):
                                        safe_convert_to_usd.warned_currencies = set()
                                    if currency not in safe_convert_to_usd.warned_currencies:
                                        st.info(f"Using current rate for {currency}: 1 {currency} = {current_rates[currency]:.4f} USD")
                                        safe_convert_to_usd.warned_currencies.add(currency)
                                    return converted
                                else:
                                    st.warning(f"No rate available for {currency}, using original value")
                                    return row['Royalty']

                        kdp_raw_data['USDeq_Royalty'] = kdp_raw_data.apply(safe_convert_to_usd, axis=1)

                        # Ensure Net_Units_Sold exists
                        if 'Net_Units_Sold' not in kdp_raw_data.columns:
                            kdp_raw_data['Net_Units_Sold'] = kdp_raw_data['Units Sold'] - kdp_raw_data['Units Refunded']

                        has_usd_conversion = True
                        st.success("✅ Currency conversion completed successfully!")

                    except ImportError:
                        st.error("❌ Currency converter not available. Please install: pip install currency_converter")
                        st.stop()
                    except Exception as e:
                        st.error(f"❌ Currency conversion failed: {str(e)}")
                        st.stop()

                # Build aggregation dictionary - Always require USD conversion
                agg_dict = {
                    'Units Sold': 'sum',
                    'Units Refunded': 'sum',
                    'Net_Units_Sold': 'sum',  # From Combined Sales sheet
                    'USDeq_Royalty': 'sum',  # Use USD equivalent only
                    'ASIN/ISBN': lambda x: list(x.unique()),  # Collect all ISBNs/ASINs for this title
                    'Marketplace': lambda x: list(x.unique()),  # Collect all marketplaces
                    'Royalty Date': ['min', 'max']  # First and last sale dates
                }

                # Add conditional aggregations based on available columns
                if 'List Price' in kdp_raw_data.columns:
                    # Free books: where List Price is 0
                    kdp_raw_data['Free_Books'] = (kdp_raw_data['List Price'] == 0).astype(int) * kdp_raw_data['Net_Units_Sold']
                    agg_dict['Free_Books'] = 'sum'

                if 'Sales Type' in kdp_raw_data.columns:
                    # KOLL Borrows: where Sales Type contains 'KOLL' or similar
                    kdp_raw_data['KOLL_Borrows'] = kdp_raw_data['Sales Type'].str.contains('KOLL|KU|Kindle Unlimited', case=False, na=False).astype(int) * kdp_raw_data['Net_Units_Sold']
                    agg_dict['KOLL_Borrows'] = 'sum'

                if 'Format' in kdp_raw_data.columns:
                    # Audiobooks: where Format starts with 'Audio'
                    kdp_raw_data['Audio_Units'] = kdp_raw_data['Format'].str.startswith('Audio', na=False).astype(int) * kdp_raw_data['Net_Units_Sold']
                    agg_dict['Audio_Units'] = 'sum'

                # Group by Title and Author, sum key metrics
                kdp_consolidated = kdp_raw_data.groupby(['Title', 'Author Name']).agg(agg_dict).reset_index()

                # Determine column names based on what was aggregated
                base_columns = ['Title', 'Author_Name', 'Units_Sold', 'Units_Refunded', 'Net_Units_Sold',
                               'Total_USDeq_Royalty', 'ID_List', 'Marketplaces', 'First_Sale', 'Last_Sale']

                if 'Free_Books' in agg_dict:
                    base_columns.insert(-4, 'Free_Books')
                if 'KOLL_Borrows' in agg_dict:
                    base_columns.insert(-4, 'KOLL_Borrows')
                if 'Audio_Units' in agg_dict:
                    base_columns.insert(-4, 'Audio_Units')

                # Flatten column names
                kdp_consolidated.columns = base_columns

                # Adjust Net Units Sold to exclude free books and KOLL borrows
                net_paid_units = kdp_consolidated['Net_Units_Sold'].copy()
                if 'Free_Books' in kdp_consolidated.columns:
                    net_paid_units = net_paid_units - kdp_consolidated['Free_Books']
                if 'KOLL_Borrows' in kdp_consolidated.columns:
                    net_paid_units = net_paid_units - kdp_consolidated['KOLL_Borrows']
                kdp_consolidated['Net_Paid_Units'] = net_paid_units

                # Add calculated fields
                kdp_consolidated['Avg_USDeq_Royalty_per_Unit'] = kdp_consolidated['Total_USDeq_Royalty'] / kdp_consolidated['Net_Paid_Units'].replace(0, 1)
                kdp_consolidated['Return_Rate'] = ((kdp_consolidated['Units_Refunded'] / kdp_consolidated['Units_Sold'].replace(0, 1)) * 100).round(1)
                kdp_consolidated['ID_Count'] = kdp_consolidated['ID_List'].apply(len)
                kdp_consolidated['Marketplace_Count'] = kdp_consolidated['Marketplaces'].apply(len)

                # Add % audiobook calculation
                if 'Audio_Units' in kdp_consolidated.columns:
                    kdp_consolidated['Pct_Audiobook'] = ((kdp_consolidated['Audio_Units'] / kdp_consolidated['Net_Units_Sold'].replace(0, 1)) * 100).round(1)

                # Display summary
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📚 Unique Titles", len(kdp_consolidated))
                with col2:
                    st.metric("💰 Total Royalty (USD)", f"${kdp_consolidated['Total_USDeq_Royalty'].sum():,.2f}")
                with col3:
                    st.metric("📖 Net Paid Units", f"{kdp_consolidated['Net_Paid_Units'].sum():,}")
                with col4:
                    if 'Free_Books' in kdp_consolidated.columns:
                        st.metric("🆓 Free Books", f"{kdp_consolidated['Free_Books'].sum():,}")
                    else:
                        st.metric("🌍 Avg Marketplaces", f"{kdp_consolidated['Marketplace_Count'].mean():.1f}")

                # Sort by USD royalty
                kdp_consolidated_sorted = kdp_consolidated.sort_values('Total_USDeq_Royalty', ascending=False)

                # Build dynamic display columns based on available data
                base_display_cols = ['Title', 'Author_Name', 'Net_Paid_Units']

                if 'Free_Books' in kdp_consolidated.columns:
                    base_display_cols.append('Free_Books')
                if 'KOLL_Borrows' in kdp_consolidated.columns:
                    base_display_cols.append('KOLL_Borrows')

                base_display_cols.extend(['Total_USDeq_Royalty', 'Avg_USDeq_Royalty_per_Unit', 'Return_Rate'])

                if 'Pct_Audiobook' in kdp_consolidated.columns:
                    base_display_cols.append('Pct_Audiobook')

                base_display_cols.extend(['ID_Count', 'Marketplace_Count'])
                display_cols = base_display_cols

                # Format the dataframe for display
                display_df = kdp_consolidated_sorted[display_cols].copy()
                display_df['Total_USDeq_Royalty'] = display_df['Total_USDeq_Royalty'].apply(lambda x: f"${x:.2f}")
                display_df['Avg_USDeq_Royalty_per_Unit'] = display_df['Avg_USDeq_Royalty_per_Unit'].apply(lambda x: f"${x:.2f}")
                display_df['Return_Rate'] = display_df['Return_Rate'].apply(lambda x: f"{x:.1f}%")
                if 'Pct_Audiobook' in display_df.columns:
                    display_df['Pct_Audiobook'] = display_df['Pct_Audiobook'].apply(lambda x: f"{x:.1f}%")

                st.dataframe(display_df, use_container_width=True)

                # Export
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_data = kdp_consolidated_sorted.to_csv(index=False)
                st.download_button(
                    label="📥 Export KDP Consolidated as CSV",
                    data=csv_data,
                    file_name=f"kdp_consolidated_by_title_{timestamp}.csv",
                    mime="text/csv"
                )
            else:
                st.info("KDP data not available for consolidation")

        # Merged LSI+KDP View
        with tab3:
            if lsi_available and kdp_available:
                st.subheader("🔗 Merged LSI + KDP Analysis by ISBN")

                # Get the raw data
                lsi_raw = processed_data['lsi_processed_data']['raw_data']

                # Get KDP raw data from destination-based structure
                kdp_processed = kdp_result['kdp_processed_data']
                kdp_raw = None
                for dest_key, dest_data in kdp_processed.items():
                    if isinstance(dest_data, dict) and 'raw_data' in dest_data:
                        kdp_raw = dest_data['raw_data']
                        break

                if kdp_raw is None:
                    st.error("❌ KDP raw data not found for merged analysis")
                    st.stop()

                # ISBN/ASIN normalization function - updated to include ASINs
                def normalize_isbn_asin(identifier):
                    """Convert ISBN/ASIN to standardized string format, including Kindle ASINs"""
                    if pd.isna(identifier):
                        return None
                    identifier_str = str(identifier).strip().upper()

                    # Handle empty strings
                    if identifier_str == '':
                        return None

                    import re

                    # Check if it's an ASIN (typically starts with B and is 10 characters)
                    if identifier_str.startswith('B') and len(identifier_str) == 10:
                        # It's likely a Kindle ASIN, keep as-is
                        return identifier_str

                    # Otherwise, process as ISBN
                    isbn_clean = re.sub(r'[^\d\-X]', '', identifier_str)
                    isbn_clean = isbn_clean.replace('-', '')

                    # Return None for invalid ISBNs/ASINs
                    if len(isbn_clean) not in [10, 13] or isbn_clean == '':
                        # If it doesn't look like a valid ISBN, but has content, keep the original
                        # This handles other ASIN formats or unusual identifiers
                        if len(identifier_str) >= 6:  # Minimum reasonable identifier length
                            return identifier_str
                        return None
                    return isbn_clean

                # Normalize ISBNs/ASINs before grouping
                lsi_raw_copy = lsi_raw.copy()
                lsi_raw_copy['ID_normalized'] = lsi_raw_copy['ISBN'].apply(normalize_isbn_asin)

                kdp_raw_copy = kdp_raw.copy()
                kdp_raw_copy['ID_normalized'] = kdp_raw_copy['ASIN/ISBN'].apply(normalize_isbn_asin)

                # Create ISBN/ASIN-based aggregations with normalized identifiers
                lsi_by_isbn = lsi_raw_copy[lsi_raw_copy['ID_normalized'].notna()].groupby('ID_normalized').agg({
                    'Title': 'first',
                    'Author': 'first',
                    'Net Qty': 'sum',
                    'Net Compensation': 'sum',
                    'Format': lambda x: list(x.unique())
                }).reset_index()
                lsi_by_isbn.columns = ['ID', 'LSI_Title', 'LSI_Author', 'LSI_Net_Qty', 'LSI_Net_Compensation', 'LSI_Formats']

                # Check if we need to do currency conversion for merged analysis
                if not has_usd_conversion:
                    st.warning("⚠️ Applying currency conversion for merged analysis...")
                    # The conversion was already done in the KDP consolidated section above
                    # So we can proceed with the analysis
                    has_usd_conversion = 'USDeq_Royalty' in kdp_raw.columns

                # Build KDP aggregation - Always use USD conversion
                kdp_agg_dict = {
                    'Title': 'first',
                    'Author Name': 'first',
                    'Net_Units_Sold': 'sum',
                    'USDeq_Royalty': 'sum',  # Use USD equivalent only
                    'Marketplace': lambda x: list(x.unique())
                }

                # Add the same conditional aggregations for merged analysis
                if 'Free_Books' in kdp_raw_copy.columns:
                    kdp_agg_dict['Free_Books'] = 'sum'
                if 'KOLL_Borrows' in kdp_raw_copy.columns:
                    kdp_agg_dict['KOLL_Borrows'] = 'sum'
                if 'Audio_Units' in kdp_raw_copy.columns:
                    kdp_agg_dict['Audio_Units'] = 'sum'

                kdp_by_asin = kdp_raw_copy[kdp_raw_copy['ID_normalized'].notna()].groupby('ID_normalized').agg(kdp_agg_dict).reset_index()

                # Set column names dynamically
                kdp_columns = ['ID', 'KDP_Title', 'KDP_Author', 'KDP_Net_Units', 'KDP_USDeq_Royalty']
                if 'Free_Books' in kdp_agg_dict:
                    kdp_columns.append('KDP_Free_Books')
                if 'KOLL_Borrows' in kdp_agg_dict:
                    kdp_columns.append('KDP_KOLL_Borrows')
                if 'Audio_Units' in kdp_agg_dict:
                    kdp_columns.append('KDP_Audio_Units')
                kdp_columns.append('KDP_Marketplaces')

                kdp_by_asin.columns = kdp_columns

                # Calculate KDP Net Paid Units (excluding free books and KOLL borrows)
                kdp_by_asin['KDP_Net_Paid_Units'] = kdp_by_asin['KDP_Net_Units'].copy()
                if 'KDP_Free_Books' in kdp_by_asin.columns:
                    kdp_by_asin['KDP_Net_Paid_Units'] = kdp_by_asin['KDP_Net_Paid_Units'] - kdp_by_asin['KDP_Free_Books']
                if 'KDP_KOLL_Borrows' in kdp_by_asin.columns:
                    kdp_by_asin['KDP_Net_Paid_Units'] = kdp_by_asin['KDP_Net_Paid_Units'] - kdp_by_asin['KDP_KOLL_Borrows']

                # Calculate % audiobook for merged analysis
                if 'KDP_Audio_Units' in kdp_by_asin.columns:
                    kdp_by_asin['KDP_Pct_Audiobook'] = ((kdp_by_asin['KDP_Audio_Units'] / kdp_by_asin['KDP_Net_Units'].replace(0, 1)) * 100).round(1)

                # Merge on normalized ID (outer join to capture all books, including Kindle-only ASINs)
                merged_data = pd.merge(lsi_by_isbn, kdp_by_asin, on='ID', how='outer')

                # Add calculated fields
                merged_data['Combined_Title'] = merged_data['LSI_Title'].fillna(merged_data['KDP_Title'])
                merged_data['Combined_Author'] = merged_data['LSI_Author'].fillna(merged_data['KDP_Author'])
                merged_data['Total_Units'] = merged_data['LSI_Net_Qty'].fillna(0) + merged_data['KDP_Net_Units'].fillna(0)
                merged_data['Total_Paid_Units'] = merged_data['LSI_Net_Qty'].fillna(0) + merged_data['KDP_Net_Paid_Units'].fillna(0)
                merged_data['Total_Revenue'] = merged_data['LSI_Net_Compensation'].fillna(0) + merged_data['KDP_USDeq_Royalty'].fillna(0)
                merged_data['Data_Source'] = merged_data.apply(lambda row:
                    'Both LSI+KDP' if pd.notnull(row['LSI_Net_Qty']) and pd.notnull(row['KDP_Net_Units'])
                    else ('LSI Only' if pd.notnull(row['LSI_Net_Qty']) else 'KDP Only'), axis=1)

                # Display summary
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🔗 Total Titles (ISBN/ASIN)", len(merged_data))
                with col2:
                    st.metric("💰 Combined Revenue", f"${merged_data['Total_Revenue'].sum():,.2f}")
                with col3:
                    st.metric("📖 Combined Units", f"{merged_data['Total_Units'].sum():,.0f}")
                with col4:
                    both_sources = len(merged_data[merged_data['Data_Source'] == 'Both LSI+KDP'])
                    kindle_only = len(merged_data[merged_data['Data_Source'] == 'KDP Only'])
                    st.metric("📱 Kindle-Only Titles", f"{kindle_only}")

                # Add additional metrics row
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🔗 In Both Sources", f"{both_sources}")
                with col2:
                    lsi_only = len(merged_data[merged_data['Data_Source'] == 'LSI Only'])
                    st.metric("📚 LSI-Only Titles", f"{lsi_only}")
                with col3:
                    # Count ASINs (starting with B) vs ISBNs
                    asin_count = len(merged_data[merged_data['ID'].str.startswith('B', na=False)])
                    st.metric("🅰️ ASIN Titles", f"{asin_count}")
                with col4:
                    isbn_count = len(merged_data) - asin_count
                    st.metric("🔢 ISBN Titles", f"{isbn_count}")

                # Add filtering
                col1, col2 = st.columns(2)
                with col1:
                    source_filter = st.selectbox("Filter by Data Source",
                                               ['All', 'Both LSI+KDP', 'LSI Only', 'KDP Only', 'Kindle-Only (ASIN)'])
                with col2:
                    sort_option = st.selectbox("Sort by",
                                             ['Total Revenue (High to Low)', 'Total Units (High to Low)',
                                              'Title (A-Z)', 'LSI Revenue (High to Low)', 'KDP Revenue USD (High to Low)'])

                # Apply filters
                filtered_merged = merged_data.copy()
                if source_filter != 'All':
                    if source_filter == 'Kindle-Only (ASIN)':
                        # Filter for KDP-only titles that have ASINs (especially B-prefixed Kindle ASINs)
                        filtered_merged = filtered_merged[
                            (filtered_merged['Data_Source'] == 'KDP Only') &
                            (filtered_merged['ID'].str.startswith('B', na=False))
                        ]
                    else:
                        filtered_merged = filtered_merged[filtered_merged['Data_Source'] == source_filter]

                # Apply sorting
                if sort_option == 'Total Revenue (High to Low)':
                    filtered_merged = filtered_merged.sort_values('Total_Revenue', ascending=False)
                elif sort_option == 'Total Units (High to Low)':
                    filtered_merged = filtered_merged.sort_values('Total_Units', ascending=False)
                elif sort_option == 'Title (A-Z)':
                    filtered_merged = filtered_merged.sort_values('Combined_Title')
                elif sort_option == 'LSI Revenue (High to Low)':
                    filtered_merged = filtered_merged.sort_values('LSI_Net_Compensation', ascending=False, na_position='last')
                elif sort_option == 'KDP Revenue USD (High to Low)':
                    filtered_merged = filtered_merged.sort_values('KDP_USDeq_Royalty', ascending=False, na_position='last')

                # Build dynamic display columns for merged analysis
                base_merged_cols = ['ID', 'Combined_Title', 'Combined_Author', 'Data_Source',
                                  'LSI_Net_Qty', 'LSI_Net_Compensation', 'KDP_Net_Paid_Units']

                # Add new KDP columns if available
                if 'KDP_Free_Books' in filtered_merged.columns:
                    base_merged_cols.append('KDP_Free_Books')
                if 'KDP_KOLL_Borrows' in filtered_merged.columns:
                    base_merged_cols.append('KDP_KOLL_Borrows')

                base_merged_cols.extend(['KDP_USDeq_Royalty'])

                if 'KDP_Pct_Audiobook' in filtered_merged.columns:
                    base_merged_cols.append('KDP_Pct_Audiobook')

                base_merged_cols.extend(['Total_Paid_Units', 'Total_Revenue'])
                display_cols = base_merged_cols

                # Format the merged dataframe for display
                display_merged_df = filtered_merged[display_cols].copy()

                # Format monetary columns
                if 'LSI_Net_Compensation' in display_merged_df.columns:
                    display_merged_df['LSI_Net_Compensation'] = display_merged_df['LSI_Net_Compensation'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "")
                if 'KDP_USDeq_Royalty' in display_merged_df.columns:
                    display_merged_df['KDP_USDeq_Royalty'] = display_merged_df['KDP_USDeq_Royalty'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "")
                if 'Total_Revenue' in display_merged_df.columns:
                    display_merged_df['Total_Revenue'] = display_merged_df['Total_Revenue'].apply(lambda x: f"${x:.2f}")

                # Format percentage column
                if 'KDP_Pct_Audiobook' in display_merged_df.columns:
                    display_merged_df['KDP_Pct_Audiobook'] = display_merged_df['KDP_Pct_Audiobook'].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "")

                st.dataframe(display_merged_df, use_container_width=True)

                # Export
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_data = filtered_merged.to_csv(index=False)
                st.download_button(
                    label="📥 Export Merged LSI+KDP as CSV",
                    data=csv_data,
                    file_name=f"merged_lsi_kdp_by_isbn_{timestamp}.csv",
                    mime="text/csv"
                )

            else:
                st.info("🔗 Both LSI and KDP data required for merged analysis")
                if not lsi_available:
                    st.warning("• LSI data not available")
                if not kdp_available:
                    st.warning("• KDP data not available")

    else:
        st.info("No data available for consolidated analysis. Please upload LSI and/or KDP data.")

except Exception as e:
    st.error(f"❌ Error in consolidated analysis: {str(e)}")

# Individual Data Analysis Sections
st.markdown("---")
st.header("📈 Individual Data Analysis")

# Check LSI data for detailed analysis
lsi_data = processed_data.get('lsi_processed_data', {})
if lsi_data and 'raw_data' in lsi_data:
    raw_lsi_df = lsi_data['raw_data']

    if raw_lsi_df is not None and len(raw_lsi_df) > 0:
        # Continue with existing LSI analysis...
        pass
    else:
        st.warning("⚠️ LSI data is empty or could not be processed.")
else:
    st.warning("⚠️ No LSI sales data found. Please upload LSI compensation files to see detailed analysis.")
    st.info("💡 Go to Max Bialystok Financial page to upload LSI data files.")

# Data Visualization and Performance Analysis using LSI+KDP Merged Data
st.markdown("---")
st.subheader("📈 Data Visualization and Performance Analysis")

# Use merged data from the LSI+KDP analysis above
if 'merged_data' in locals() and not merged_data.empty:
    # Prepare visualization data - filter for books with revenue
    viz_data = merged_data[merged_data['Total_Revenue'] > 0].copy()
    viz_data = viz_data.sort_values('Total_Revenue', ascending=False)

    if len(viz_data) == 0:
        st.warning("⚠️ No books found with revenue data for visualization")
    else:
        # Summary metrics for LSI+KDP combined
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📚 Books with Revenue", len(viz_data))
        with col2:
            total_combined_revenue = viz_data['Total_Revenue'].sum()
            st.metric("💰 Total Combined Revenue", f"${total_combined_revenue:,.2f}")
        with col3:
            total_combined_units = viz_data['Total_Paid_Units'].sum()
            st.metric("📖 Total Paid Units", f"{total_combined_units:,.0f}")
        with col4:
            avg_revenue_per_book = viz_data['Total_Revenue'].mean()
            st.metric("📊 Avg Revenue/Book", f"${avg_revenue_per_book:.2f}")

        # Charts Section
        tab1, tab2, tab3 = st.tabs(["📊 Revenue Distribution", "📈 Unit Sales", "🎯 Performance Analysis"])

        with tab1:
            # Combined revenue distribution chart
            top_books = viz_data.head(20)
            fig_revenue = px.bar(
                top_books,
                x='Combined_Title',
                y='Total_Revenue',
                color='Data_Source',
                title="Top 20 Books by Combined Revenue (LSI + KDP)",
                labels={'Total_Revenue': 'Total Revenue ($)', 'Combined_Title': 'Book Title'},
                hover_data=['Combined_Author', 'LSI_Net_Compensation', 'KDP_USDeq_Royalty']
            )
            fig_revenue.update_xaxes(tickangle=45)
            st.plotly_chart(fig_revenue, use_container_width=True)

        with tab2:
            # Unit sales vs revenue scatter plot
            fig_units = px.scatter(
                viz_data,
                x='Total_Paid_Units',
                y='Total_Revenue',
                color='Data_Source',
                size='Total_Revenue',
                hover_data=['Combined_Title', 'Combined_Author'],
                title="Revenue vs Paid Units Sold (LSI + KDP Combined)",
                labels={'Total_Paid_Units': 'Total Paid Units Sold', 'Total_Revenue': 'Total Revenue ($)'}
            )
            st.plotly_chart(fig_units, use_container_width=True)

        with tab3:
            # Revenue per unit performance
            viz_data['Revenue_per_Unit'] = viz_data['Total_Revenue'] / viz_data['Total_Paid_Units'].replace(0, 1)
            top_performers = viz_data.head(15)

            fig_perf = px.bar(
                top_performers,
                x='Combined_Title',
                y='Revenue_per_Unit',
                color='Data_Source',
                title="Top 15 Books by Revenue per Unit (LSI + KDP Combined)",
                labels={'Revenue_per_Unit': 'Revenue per Unit ($)', 'Combined_Title': 'Book Title'},
                hover_data=['Combined_Author', 'Total_Paid_Units']
            )
            fig_perf.update_xaxes(tickangle=45)
            st.plotly_chart(fig_perf, use_container_width=True)

        # Source breakdown visualization
        st.markdown("### 📊 Revenue Source Breakdown")

        # Create source summary
        source_summary = viz_data.groupby('Data_Source').agg({
            'Total_Revenue': 'sum',
            'Total_Paid_Units': 'sum',
            'Combined_Title': 'count'
        }).reset_index()
        source_summary.columns = ['Source', 'Total_Revenue', 'Total_Units', 'Title_Count']

        col1, col2 = st.columns(2)

        with col1:
            # Revenue by source
            fig_source_rev = px.pie(
                source_summary,
                values='Total_Revenue',
                names='Source',
                title="Revenue Distribution by Source"
            )
            st.plotly_chart(fig_source_rev, use_container_width=True)

        with col2:
            # Unit count by source
            fig_source_units = px.pie(
                source_summary,
                values='Title_Count',
                names='Source',
                title="Title Count by Source"
            )
            st.plotly_chart(fig_source_units, use_container_width=True)

else:
    st.warning("⚠️ Merged LSI+KDP data not available. Please ensure both LSI and KDP data are loaded for visualization.")

# Data Source Attribution
st.markdown("---")
with st.expander("📁 Data Sources & Attribution", expanded=False):
    if 'lsi_source_metadata' in processed_data:
        st.subheader("LSI Data Sources")
        source_display.render_source_info("Sales Analysis", processed_data.get('lsi_source_metadata', {}))

    if 'kdp_result' in locals() and 'kdp_source_metadata' in kdp_result:
        st.subheader("KDP Data Sources")
        source_display.render_source_info("KDP Sales Analysis", kdp_result.get('kdp_source_metadata', {}))

# Footer
st.markdown("---")
st.caption("Sales Analysis Dashboard - Comprehensive Book Performance Analysis")
st.caption("💡 For accurate 'Days in Print' calculations, upload LSI metadata with publication dates")