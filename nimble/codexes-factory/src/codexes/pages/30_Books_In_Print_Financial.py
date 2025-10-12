"""
Books In Print with Enhanced Financial Metadata

Comprehensive view of all books in print using the FullMetadataEnhanced approach.
Combines LSI Books In Print Metadata with direct sales, rights sales, and contract data.

This page starts with LSI Books In Print Metadata as the base and enhances it with:
- Direct sales data (LSI lifetime sales)
- Rights sales data (KDP lifetime sales)
- Contract information (royaltied/non-royaltied status)
- Calculated performance metrics and analytics
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import numpy as np

sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Import following current patterns
try:
    from codexes.modules.finance.core.user_data_manager import UserDataManager
    from codexes.modules.finance.core.fro_coordinator import FROCoordinator
    from codexes.modules.finance.core.enhanced_metadata_processor import EnhancedMetadataProcessor
    from codexes.modules.finance.ui.source_display import DataSourceDisplay
    from codexes.core.auth import get_user_role
    from codexes.core.simple_auth import get_auth
except ModuleNotFoundError:
    from src.codexes.modules.finance.core.user_data_manager import UserDataManager
    from src.codexes.modules.finance.core.fro_coordinator import FROCoordinator
    from src.codexes.modules.finance.core.enhanced_metadata_processor import EnhancedMetadataProcessor
    from src.codexes.modules.finance.ui.source_display import DataSourceDisplay
    from src.codexes.core.auth import get_user_role
    from src.codexes.core.simple_auth import get_auth

logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Books In Print - Enhanced Financial Metadata",
    page_icon="📚",
    layout="wide"
)

# Authentication check
auth = get_auth()
if not auth.is_authenticated():
    st.error("🔒 Please log in to access financial data.")
    st.stop()

current_username = auth.get_current_user()
user_role = auth.get_user_role()

if user_role not in ['admin', 'subscriber']:
    st.error("🚫 This page requires subscriber or admin access.")
    st.stop()

# Initialize data management and enhanced metadata processor
udm = UserDataManager(current_username)
fro_coord = FROCoordinator(udm)
enhanced_processor = EnhancedMetadataProcessor(udm, fro_coord)
source_display = DataSourceDisplay()

# Header
st.title("📚 Books In Print with Enhanced Financial Metadata")
st.markdown("""
Comprehensive view combining LSI Books In Print Metadata with financial performance data:
- **Base**: LSI Books In Print Metadata (title, author, publication info)
- **Direct Sales**: LSI lifetime sales data (units sold, net compensation)
- **Rights Sales**: KDP lifetime sales data (royalties, units sold)
- **Contract Info**: Royaltied/non-royaltied status and terms
""")

# Add refresh button for processing
refresh_col1, refresh_col2 = st.columns([1, 4])
with refresh_col1:
    if st.button("🔄 Process Enhanced Metadata"):
        with st.spinner("Processing enhanced metadata..."):
            st.cache_data.clear()
            st.rerun()

# Process enhanced metadata
with st.spinner("Loading enhanced metadata..."):
    processed_data = enhanced_processor.create_enhanced_metadata()

if not processed_data['success']:
    st.error(f"❌ Enhanced metadata processing failed: {processed_data.get('error_message', 'Unknown error')}")

    # Show processing status
    with st.expander("🔍 Processing Status Details"):
        processing_status = processed_data.get('processing_status', {})
        if isinstance(processing_status, dict):
            for component, status in processing_status.items():
                if 'error' in status:
                    st.error(f"**{component}**: {status}")
                elif 'missing' in status:
                    st.warning(f"**{component}**: {status}")
                else:
                    st.success(f"**{component}**: {status}")
        else:
            st.info(f"Processing status: {processing_status}")

    st.stop()

enhanced_metadata = processed_data['enhanced_metadata']
summary_stats = enhanced_processor.get_summary_statistics()

# Show data source attribution with enhanced metadata info
source_display.render_user_attribution(
    current_username,
    udm.user_id,
    processed_data.get('last_updated')
)

# Show enhanced metadata summary with bidirectional merger info
merger_type = processed_data.get('source_attribution', {}).get('merger_type', 'standard')
merge_stats = processed_data.get('source_attribution', {}).get('merge_statistics', {})

if merger_type == 'bidirectional':
    st.success(
        f"✅ **Bidirectional metadata merger completed**: "
        f"**{processed_data['record_count']:,} books** in enriched catalog | "
        f"**{merge_stats.get('kdp_consolidated_total', 0):,} KDP** + "
        f"**{merge_stats.get('lsi_consolidated_total', 0):,} LSI** sales records enriched with metadata"
    )

    # Show detailed merger statistics
    with st.expander("📊 Bidirectional Merger Statistics"):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "📚 Books In Print → Sales Data",
                f"{merge_stats.get('books_with_sales_data', 0):,}",
                f"{((merge_stats.get('books_with_sales_data', 0)/max(processed_data['record_count'], 1))*100):.1f}%"
            )
            st.caption("Books in catalog with sales data from KDP/LSI")

        with col2:
            st.metric(
                "📈 KDP Sales → Metadata",
                f"{merge_stats.get('kdp_with_metadata', 0):,}",
                f"{((merge_stats.get('kdp_with_metadata', 0)/max(merge_stats.get('kdp_consolidated_total', 1), 1))*100):.1f}%"
            )
            st.caption("KDP sales records enriched with publication metadata")

        with col3:
            st.metric(
                "📦 LSI Sales → Metadata",
                f"{merge_stats.get('lsi_with_metadata', 0):,}",
                f"{((merge_stats.get('lsi_with_metadata', 0)/max(merge_stats.get('lsi_consolidated_total', 1), 1))*100):.1f}%"
            )
            st.caption("LSI sales records enriched with publication metadata")
else:
    st.info(
        f"✅ Enhanced metadata successfully processed: **{processed_data['record_count']:,} books** "
        f"({summary_stats.get('books_with_sales', 0):,} with sales data)"
    )

# Main content tabs - add bidirectional merger tabs if available
if merger_type == 'bidirectional' and processed_data.get('kdp_consolidated_enriched') is not None:
    overview_tab, detailed_tab, analytics_tab, kdp_enriched_tab, lsi_enriched_tab, metadata_tab, sources_tab = st.tabs([
        "📊 Overview",
        "📋 Books In Print Enhanced",
        "📈 Performance Analytics",
        "🔥 KDP Sales + Metadata",
        "📦 LSI Sales + Metadata",
        "🔍 Metadata Integration",
        "📁 Data Sources"
    ])
else:
    overview_tab, detailed_tab, analytics_tab, metadata_tab, sources_tab = st.tabs([
        "📊 Overview",
        "📋 Enhanced Data View",
        "📈 Performance Analytics",
        "🔍 Metadata Integration",
        "📁 Data Sources"
    ])

with overview_tab:
    st.header("📊 Enhanced Metadata Overview")

    # Key metrics row from actual enhanced data
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        source_display.render_metric_with_sources(
            "📚 Total Books",
            f"{summary_stats.get('total_books', 0):,}",
            processed_data.get('source_attribution', {}),
            help_text="Total books in LSI Books In Print catalog"
        )

    with col2:
        source_display.render_metric_with_sources(
            "📈 Books with Sales",
            f"{summary_stats.get('books_with_sales', 0):,}",
            processed_data.get('source_attribution', {}),
            delta=f"{((summary_stats.get('books_with_sales', 0)/max(summary_stats.get('total_books', 1), 1))*100):.1f}%",
            help_text="Books with sales data from LSI or KDP"
        )

    with col3:
        source_display.render_metric_with_sources(
            "💰 Total Revenue",
            f"${summary_stats.get('total_revenue', 0):,.2f}",
            processed_data.get('source_attribution', {}),
            help_text="Total revenue across all channels"
        )

    with col4:
        source_display.render_metric_with_sources(
            "💵 Avg Revenue/Book",
            f"${summary_stats.get('avg_revenue_per_book', 0):,.2f}",
            processed_data.get('source_attribution', {}),
            help_text="Average revenue per book with sales"
        )

    # Channel Performance Overview
    st.subheader("📈 Channel Performance")

    channel_col1, channel_col2 = st.columns(2)

    with channel_col1:
        st.write("**Sales Channel Distribution**")

        # Calculate channel metrics from enhanced data - with safe column checking
        books_with_lsi = summary_stats.get('books_with_lsi_sales', 0)
        books_with_kdp = summary_stats.get('books_with_kdp_sales', 0)

        # Safe calculation of books with both channels
        books_with_both = 0
        if enhanced_metadata is not None and not enhanced_metadata.empty:
            has_lsi_col = enhanced_metadata.get('has_lsi_sales', pd.Series([False] * len(enhanced_metadata), dtype=bool))
            has_kdp_col = enhanced_metadata.get('has_kdp_sales', pd.Series([False] * len(enhanced_metadata), dtype=bool))
            books_with_both = len(enhanced_metadata[has_lsi_col & has_kdp_col])

        channel_summary = pd.DataFrame({
            'Channel': ['LSI Only', 'KDP Only', 'Both Channels', 'No Sales'],
            'Books': [
                books_with_lsi - books_with_both,
                books_with_kdp - books_with_both,
                books_with_both,
                summary_stats.get('total_books', 0) - summary_stats.get('books_with_sales', 0)
            ]
        })

        fig_pie = px.pie(
            channel_summary,
            values='Books',
            names='Channel',
            title="Books by Sales Channel"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with channel_col2:
        st.write("**Performance Tier Distribution**")

        # Performance tiers from enhanced data
        performance_data = summary_stats.get('performance_tiers', {})
        if performance_data:
            perf_df = pd.DataFrame(list(performance_data.items()), columns=['Tier', 'Books'])

            fig_bar = px.bar(
                perf_df,
                x='Books',
                y='Tier',
                orientation='h',
                title="Books by Performance Tier",
                color='Tier'
            )
            fig_bar.update_layout(height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Performance tier data not available")

with detailed_tab:
    st.header("📋 Enhanced Book Data with Financial Metrics")

    if enhanced_metadata is None or enhanced_metadata.empty:
        st.warning("No enhanced metadata available to display")
    else:
        # Filters in expander
        with st.expander("🔍 **Filters & Display Options**", expanded=False):
            # First row of filters
            filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns(5)

            with filter_col1:
                revenue_filter = st.selectbox(
                    "Revenue Range",
                    ["All", "No Sales", "$1-1000", "$1000-5000", "$5000-10000", "$10000+"]
                )

            with filter_col2:
                channel_filter = st.selectbox(
                    "Sales Channel",
                    ["All", "LSI Only", "KDP Only", "Both Channels", "No Sales"]
                )

            with filter_col3:
                performance_filter = st.selectbox(
                    "Performance Tier",
                    ["All"] + list(enhanced_metadata['performance_tier'].unique())
                )

            with filter_col4:
                # Get unique publishing age categories for filtering
                pub_age_categories = ["All"] + sorted([cat for cat in enhanced_metadata['publishing_age_category'].dropna().unique() if cat and str(cat).strip()])
                pub_age_filter = st.selectbox(
                    "Publishing Age",
                    pub_age_categories,
                    key="pub_age_filter"
                )

            with filter_col5:
                # Royaltied status filter
                royaltied_filter = st.selectbox(
                    "Royaltied Status",
                    ["All", "Royaltied", "Non-Royaltied"],
                    key="royaltied_filter"
                )

            st.write("") # Add spacing

            # Second row for date, BISAC, and product line filters
            date_col1, date_col2, product_line_col, bisac_col = st.columns([1, 1, 1, 2])

            with date_col1:
                # Publication date range filter
                if 'Pub Date' in enhanced_metadata.columns:
                    pub_dates = pd.to_datetime(enhanced_metadata['Pub Date'], errors='coerce').dropna()
                    if not pub_dates.empty:
                        min_date = pub_dates.min().date()
                        max_date = pub_dates.max().date()

                        pub_date_start = st.date_input(
                            "Pub Date From",
                            value=min_date,
                            min_value=min_date,
                            max_value=max_date,
                            key="pub_date_start"
                        )
                    else:
                        pub_date_start = None
                else:
                    pub_date_start = None

            with date_col2:
                if 'Pub Date' in enhanced_metadata.columns and not pub_dates.empty:
                    pub_date_end = st.date_input(
                        "Pub Date To",
                        value=max_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="pub_date_end"
                    )
                else:
                    pub_date_end = None

            with product_line_col:
                # Product line filter
                if 'product_line' in enhanced_metadata.columns:
                    product_lines = ["All"] + sorted([pl for pl in enhanced_metadata['product_line'].dropna().unique() if pl and str(pl).strip()])
                    product_line_filter = st.selectbox(
                        "Product Line",
                        product_lines,
                        key="product_line_filter"
                    )
                else:
                    product_line_filter = "All"

            with bisac_col:
                # Get ALL unique BISAC 1 descriptions for multiselect filtering
                all_bisac_descriptions = sorted([desc for desc in enhanced_metadata['BISAC 1 Description'].dropna().unique() if desc and str(desc).strip()])
                bisac_desc_filter = st.multiselect(
                    "BISAC Categories (Select multiple)",
                    all_bisac_descriptions,
                    default=[],
                    key="bisac_desc_filter"
                )

            st.write("") # Add spacing

            # Third row for column selection
            st.subheader("Display Columns")
            # Get available columns from enhanced metadata for display
            available_display_cols = []
            for col in enhanced_metadata.columns:
                if col in ['Title', 'Author', 'Contributor One Name', 'ISBN', 'total_revenue_all_channels', 'total_units_all_channels',
                          'lsi_net_compensation', 'kdp_usdeq_royalty', 'performance_tier', 'revenue_per_unit',
                          'days_in_print', 'months_in_print', 'compensated_days_in_print', 'compensated_months_in_print',
                          'revenue_per_month_in_print', 'revenue_per_compensated_month_in_print', 'publishing_age_category',
                          'revenue_per_unit_all_channels', 'BISAC 1 Description', 'BISAC 2 Description', 'BISAC 3 Description',
                          'Pub Date', 'royaltied', 'product_line']:
                    available_display_cols.append(col)

            show_columns = st.multiselect(
                "Show Columns",
                available_display_cols,
                default=[col for col in ['Title', 'Author', 'total_revenue_all_channels', 'total_units_all_channels', 'revenue_per_month_in_print', 'publishing_age_category', 'BISAC 1 Description']
                        if col in available_display_cols]
            )

        # Work with the actual enhanced metadata
        display_df = enhanced_metadata.copy()

        # Apply filters
        if revenue_filter != "All":
            if revenue_filter == "No Sales":
                display_df = display_df[display_df['total_revenue_all_channels'] == 0]
            elif revenue_filter == "$1-1000":
                display_df = display_df[(display_df['total_revenue_all_channels'] > 0) & (display_df['total_revenue_all_channels'] <= 1000)]
            elif revenue_filter == "$1000-5000":
                display_df = display_df[(display_df['total_revenue_all_channels'] > 1000) & (display_df['total_revenue_all_channels'] <= 5000)]
            elif revenue_filter == "$5000-10000":
                display_df = display_df[(display_df['total_revenue_all_channels'] > 5000) & (display_df['total_revenue_all_channels'] <= 10000)]
            elif revenue_filter == "$10000+":
                display_df = display_df[display_df['total_revenue_all_channels'] > 10000]

        if channel_filter != "All":
            if channel_filter == "LSI Only":
                has_lsi = display_df.get('has_lsi_sales', pd.Series([False] * len(display_df), dtype=bool))
                has_kdp = display_df.get('has_kdp_sales', pd.Series([False] * len(display_df), dtype=bool))
                display_df = display_df[has_lsi & ~has_kdp]
            elif channel_filter == "KDP Only":
                has_lsi = display_df.get('has_lsi_sales', pd.Series([False] * len(display_df), dtype=bool))
                has_kdp = display_df.get('has_kdp_sales', pd.Series([False] * len(display_df), dtype=bool))
                display_df = display_df[has_kdp & ~has_lsi]
            elif channel_filter == "Both Channels":
                has_lsi = display_df.get('has_lsi_sales', pd.Series([False] * len(display_df), dtype=bool))
                has_kdp = display_df.get('has_kdp_sales', pd.Series([False] * len(display_df), dtype=bool))
                display_df = display_df[has_lsi & has_kdp]
            elif channel_filter == "No Sales":
                has_any = display_df.get('has_any_sales', pd.Series([False] * len(display_df), dtype=bool))
                display_df = display_df[~has_any]

        if performance_filter != "All":
            display_df = display_df[display_df['performance_tier'] == performance_filter]

        # Apply publishing age filter
        if pub_age_filter != "All":
            display_df = display_df[display_df['publishing_age_category'] == pub_age_filter]

        # Apply royaltied status filter
        if royaltied_filter != "All":
            if 'royaltied' in display_df.columns:
                if royaltied_filter == "Royaltied":
                    display_df = display_df[display_df['royaltied'] == True]
                elif royaltied_filter == "Non-Royaltied":
                    display_df = display_df[display_df['royaltied'] == False]
            else:
                st.warning("⚠️ Royaltied status data not available. Please ensure add2fme.xlsx file is loaded.")

        # Apply product line filter
        if product_line_filter != "All":
            if 'product_line' in display_df.columns:
                display_df = display_df[display_df['product_line'] == product_line_filter]
            else:
                st.warning("⚠️ Product line data not available. Please ensure add2fme.xlsx file is loaded.")

        # Apply publication date filters
        if pub_date_start is not None and pub_date_end is not None and 'Pub Date' in display_df.columns:
            display_df['Pub Date'] = pd.to_datetime(display_df['Pub Date'], errors='coerce')
            pub_date_start_ts = pd.Timestamp(pub_date_start)
            pub_date_end_ts = pd.Timestamp(pub_date_end)
            display_df = display_df[
                (display_df['Pub Date'] >= pub_date_start_ts) &
                (display_df['Pub Date'] <= pub_date_end_ts)
            ]

        # Apply BISAC filters (multiselect)
        if bisac_desc_filter and len(bisac_desc_filter) > 0:
            display_df = display_df[display_df['BISAC 1 Description'].isin(bisac_desc_filter)]

        # Sort by total revenue
        display_df = display_df.sort_values('total_revenue_all_channels', ascending=False)

        # Display table
        st.write(f"**Showing {len(display_df):,} books** (filtered from {len(enhanced_metadata):,} total)")

        # Prepare display columns
        if show_columns:
            # Only show selected columns that exist in the dataframe
            available_columns = [col for col in show_columns if col in display_df.columns]
            table_df = display_df[available_columns].copy()

            # Ensure currency columns are numeric (don't format as strings here - let column_config handle formatting)
            currency_cols = ['total_revenue', 'lsi_net_compensation', 'kdp_usdeq_royalty', 'revenue_per_unit',
                           'total_revenue_all_channels', 'total_compensation_all_channels', 'revenue_per_unit_all_channels',
                           'revenue_per_month_in_print', 'revenue_per_compensated_month_in_print']
            for col in currency_cols:
                if col in table_df.columns:
                    table_df[col] = pd.to_numeric(table_df[col], errors='coerce').fillna(0)

            # Ensure unit columns are numeric integers
            unit_cols = ['total_units_sold', 'lsi_net_qty', 'kdp_net_units_sold']
            for col in unit_cols:
                if col in table_df.columns:
                    table_df[col] = pd.to_numeric(table_df[col], errors='coerce').fillna(0).astype(int)

            # Build dynamic column configuration for proper formatting and sorting
            column_config = {}

            # Configure currency columns as NumberColumn with dollar formatting
            for col in currency_cols:
                if col in table_df.columns:
                    if 'revenue' in col.lower():
                        column_config[col] = st.column_config.NumberColumn(
                            col.replace('_', ' ').title(),
                            help=f"{col.replace('_', ' ').title()} in USD",
                            format="$%.2f"
                        )
                    elif 'compensation' in col.lower():
                        column_config[col] = st.column_config.NumberColumn(
                            col.replace('_', ' ').title(),
                            help=f"{col.replace('_', ' ').title()} in USD",
                            format="$%.2f"
                        )

            # Configure unit columns as NumberColumn with integer formatting
            for col in unit_cols:
                if col in table_df.columns:
                    column_config[col] = st.column_config.NumberColumn(
                        col.replace('_', ' ').title(),
                        help=f"Number of {col.replace('_', ' ').lower()}",
                        format="%d"
                    )

            st.dataframe(
                table_df,
                use_container_width=True,
                hide_index=True,
                column_config=column_config
            )

            # Display median and average monthly revenue for the filtered view
            if 'revenue_per_month_in_print' in display_df.columns and len(display_df) > 0:
                # Calculate median and average from the original numeric values (before formatting)
                median_monthly_revenue = display_df['revenue_per_month_in_print'].median()
                average_monthly_revenue = display_df['revenue_per_month_in_print'].mean()

                if pd.notna(median_monthly_revenue) and median_monthly_revenue > 0:
                    st.markdown(f"**📊 Monthly Revenue Stats (Filtered View):** Median: \\${median_monthly_revenue:,.2f} • Average: \\${average_monthly_revenue:,.2f}")
                else:
                    st.markdown("**📊 Monthly Revenue Stats (Filtered View):** No data available")
            else:
                st.markdown("**📊 Monthly Revenue Stats (Filtered View):** Revenue per month data not available")
        else:
            st.info("Please select columns to display in the filter above")

with analytics_tab:
    st.header("📈 Performance Analytics")

    if enhanced_metadata is None or enhanced_metadata.empty:
        st.warning("No enhanced metadata available for analytics")
    else:
        # Revenue distribution analysis
        st.subheader("💰 Revenue Distribution Analysis")

        analytics_col1, analytics_col2 = st.columns(2)

        with analytics_col1:
            # Revenue distribution histogram
            st.write("**Revenue Distribution (Books with Sales)**")
            books_with_sales = enhanced_metadata[enhanced_metadata['total_revenue'] > 0]

            if not books_with_sales.empty:
                fig_hist = px.histogram(
                    books_with_sales,
                    x='total_revenue',
                    nbins=50,
                    title="Revenue Distribution",
                    labels={'total_revenue': 'Total Revenue ($)', 'count': 'Number of Books'}
                )
                fig_hist.update_layout(height=400)
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("No books with sales data available")

        with analytics_col2:
            # Channel comparison
            st.write("**Channel Performance Comparison**")

            channel_stats = []
            if 'lsi_net_compensation' in enhanced_metadata.columns:
                has_lsi_sales = enhanced_metadata.get('has_lsi_sales', pd.Series([False] * len(enhanced_metadata), dtype=bool))
                lsi_books = enhanced_metadata[has_lsi_sales]
                lsi_total_revenue = lsi_books['lsi_net_compensation'].sum() if not lsi_books.empty else 0
                lsi_avg_revenue = lsi_books['lsi_net_compensation'].mean() if not lsi_books.empty else 0
                channel_stats.append({
                    'Channel': 'LSI',
                    'Books': len(lsi_books),
                    'Total Revenue': lsi_total_revenue,
                    'Avg Revenue': lsi_avg_revenue
                })

            if 'kdp_usdeq_royalty' in enhanced_metadata.columns:
                has_kdp_sales = enhanced_metadata.get('has_kdp_sales', pd.Series([False] * len(enhanced_metadata), dtype=bool))
                kdp_books = enhanced_metadata[has_kdp_sales]
                kdp_total_revenue = kdp_books['kdp_usdeq_royalty'].sum() if not kdp_books.empty else 0
                kdp_avg_revenue = kdp_books['kdp_usdeq_royalty'].mean() if not kdp_books.empty else 0
                channel_stats.append({
                    'Channel': 'KDP',
                    'Books': len(kdp_books),
                    'Total Revenue': kdp_total_revenue,
                    'Avg Revenue': kdp_avg_revenue
                })

            if channel_stats:
                channel_df = pd.DataFrame(channel_stats)
                st.dataframe(channel_df, hide_index=True)
            else:
                st.info("No channel data available")

        # Top performers analysis
        st.subheader("🏆 Top Performers")

        top_col1, top_col2 = st.columns(2)

        with top_col1:
            st.write("**Top 15 Books by Revenue**")

            # Use available columns, prioritizing standardized names
            display_cols = ['total_revenue_all_channels', 'total_units_all_channels']
            if 'Title' in books_with_sales.columns:
                display_cols.insert(0, 'Title')
            if 'Author' in books_with_sales.columns:
                display_cols.insert(-2, 'Author')  # Insert before revenue/units

            if not books_with_sales.empty and len(display_cols) >= 2:
                top_books = books_with_sales.nlargest(15, 'total_revenue_all_channels')[display_cols]

                # Format for display
                display_top = top_books.copy()
                display_top['total_revenue_all_channels'] = display_top['total_revenue_all_channels'].apply(lambda x: f"${x:,.2f}")
                display_top['total_units_all_channels'] = display_top['total_units_all_channels'].apply(lambda x: f"{int(x):,}")

                # Rename columns for display
                display_top = display_top.rename(columns={
                    'total_revenue_all_channels': 'Revenue',
                    'total_units_all_channels': 'Units'
                })

                st.dataframe(display_top, hide_index=True, use_container_width=True)
            else:
                st.info("No top performers data available")

        with top_col2:
            st.write("**Revenue vs Units Analysis**")

            if not books_with_sales.empty:
                # Use available columns for hover data
                hover_cols = []
                if 'Title' in books_with_sales.columns:
                    hover_cols.append('Title')
                if 'Author' in books_with_sales.columns:
                    hover_cols.append('Author')

                fig_scatter = px.scatter(
                    books_with_sales,
                    x='total_units_sold',
                    y='total_revenue',
                    hover_data=hover_cols if hover_cols else None,
                    title="Revenue vs Units Sold",
                    labels={'total_units_sold': 'Total Units Sold', 'total_revenue': 'Total Revenue ($)'}
                )
                fig_scatter.update_layout(height=400)
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("No scatter plot data available")

        # Performance tier analysis
        st.subheader("🎯 Performance Tier Analysis")

        tier_col1, tier_col2 = st.columns(2)

        with tier_col1:
            st.write("**Performance Tier Breakdown**")
            tier_stats = enhanced_metadata['performance_tier'].value_counts()

            if not tier_stats.empty:
                tier_df = tier_stats.reset_index()
                tier_df.columns = ['Performance Tier', 'Number of Books']
                tier_df['Percentage'] = (tier_df['Number of Books'] / len(enhanced_metadata) * 100).round(1)
                tier_df['Percentage'] = tier_df['Percentage'].apply(lambda x: f"{x}%")

                st.dataframe(tier_df, hide_index=True)
            else:
                st.info("No performance tier data available")

        with tier_col2:
            st.write("**Channel Coverage**")

            coverage_stats = [
                {'Metric': 'Books with LSI Sales', 'Count': summary_stats.get('books_with_lsi_sales', 0)},
                {'Metric': 'Books with KDP Sales', 'Count': summary_stats.get('books_with_kdp_sales', 0)},
                {'Metric': 'Books with Any Sales', 'Count': summary_stats.get('books_with_sales', 0)},
                {'Metric': 'Books with No Sales', 'Count': summary_stats.get('total_books', 0) - summary_stats.get('books_with_sales', 0)}
            ]

            coverage_df = pd.DataFrame(coverage_stats)
            coverage_df['Percentage'] = (coverage_df['Count'] / summary_stats.get('total_books', 1) * 100).round(1)
            coverage_df['Percentage'] = coverage_df['Percentage'].apply(lambda x: f"{x}%")

            st.dataframe(coverage_df, hide_index=True)

# Add the new bidirectional merger tabs if available
if merger_type == 'bidirectional' and processed_data.get('kdp_consolidated_enriched') is not None:

    with kdp_enriched_tab:
        st.header("🔥 KDP Sales Data Enriched with Publication Metadata")

        kdp_enriched = processed_data.get('kdp_consolidated_enriched', pd.DataFrame())

        if kdp_enriched.empty:
            st.warning("No KDP enriched data available")
        else:
            # Check for available title columns
            kdp_title_cols = [col for col in kdp_enriched.columns if 'title' in col.lower()]
            kdp_metadata_count = 0
            if kdp_title_cols:
                # Use the first available title column
                kdp_title_col = kdp_title_cols[0]
                kdp_metadata_count = len(kdp_enriched.dropna(subset=[kdp_title_col], how='all'))
            else:
                # Count records that have any metadata columns
                kdp_metadata_cols = [col for col in kdp_enriched.columns if col in ['Title', 'Pub Date', 'Description', 'BISAC Category']]
                if kdp_metadata_cols:
                    kdp_metadata_count = len(kdp_enriched.dropna(subset=kdp_metadata_cols, how='all'))

            st.markdown(f"""
            **KDP sales records enriched with publication metadata**
            - Total KDP sales records: **{len(kdp_enriched):,}**
            - Records with metadata: **{kdp_metadata_count:,}**
            - Metadata enrichment adds: Publication dates, descriptions, BISAC categories, and more
            """)

            # KDP enriched data filters
            kdp_filter_col1, kdp_filter_col2 = st.columns(2)

            with kdp_filter_col1:
                kdp_revenue_filter = st.selectbox(
                    "KDP Revenue Filter",
                    ["All", "No Sales", "$1-100", "$100-1000", "$1000+"],
                    key="kdp_revenue_filter"
                )

            with kdp_filter_col2:
                # Get available columns and safe defaults for KDP
                kdp_available_cols = [col for col in kdp_enriched.columns if col in ['Title', 'Author', 'Pub Date', 'Description', 'BISAC Category', 'Format', 'Royalty', 'USDeq_Royalty', 'Units Sold', 'Currency', 'List Price']]
                kdp_safe_defaults = [col for col in ['Title', 'Author', 'USDeq_Royalty', 'Units Sold', 'Pub Date'] if col in kdp_available_cols]

                kdp_show_cols = st.multiselect(
                    "Show KDP Columns",
                    kdp_available_cols,
                    default=kdp_safe_defaults,
                    key="kdp_show_cols"
                )

            # Filter KDP data
            kdp_display_df = kdp_enriched.copy()

            # Apply revenue filter
            if kdp_revenue_filter == "No Sales":
                kdp_display_df = kdp_display_df[kdp_display_df.get('USDeq_Royalty', 0) == 0]
            elif kdp_revenue_filter == "$1-100":
                kdp_display_df = kdp_display_df[(kdp_display_df.get('USDeq_Royalty', 0) > 0) & (kdp_display_df.get('USDeq_Royalty', 0) <= 100)]
            elif kdp_revenue_filter == "$100-1000":
                kdp_display_df = kdp_display_df[(kdp_display_df.get('USDeq_Royalty', 0) > 100) & (kdp_display_df.get('USDeq_Royalty', 0) <= 1000)]
            elif kdp_revenue_filter == "$1000+":
                kdp_display_df = kdp_display_df[kdp_display_df.get('USDeq_Royalty', 0) > 1000]

            # Display KDP enriched data
            if kdp_show_cols and not kdp_display_df.empty:
                available_cols = [col for col in kdp_show_cols if col in kdp_display_df.columns]
                if available_cols:
                    display_kdp = kdp_display_df[available_cols].copy()

                    # Format currency columns
                    currency_cols = ['Royalty', 'USDeq_Royalty', 'List Price']
                    for col in currency_cols:
                        if col in display_kdp.columns:
                            display_kdp[col] = display_kdp[col].fillna(0).apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")

                    st.write(f"**Showing {len(display_kdp):,} KDP records** (filtered from {len(kdp_enriched):,} total)")
                    st.dataframe(display_kdp, use_container_width=True, hide_index=True)
                else:
                    st.info("No available columns to display")
            else:
                st.info("Select columns to display or check data availability")

    with lsi_enriched_tab:
        st.header("📦 LSI Sales Data Enriched with Publication Metadata")

        lsi_enriched = processed_data.get('lsi_consolidated_enriched', pd.DataFrame())

        if lsi_enriched.empty:
            st.warning("No LSI enriched data available")
        else:
            # Check for available title columns
            title_cols = [col for col in lsi_enriched.columns if 'title' in col.lower()]
            metadata_count = 0
            if title_cols:
                # Use the first available title column
                title_col = title_cols[0]
                metadata_count = len(lsi_enriched.dropna(subset=[title_col], how='all'))
            else:
                # Count records that have any metadata columns
                metadata_cols = [col for col in lsi_enriched.columns if col in ['Title', 'Pub Date', 'Description', 'BISAC Category']]
                if metadata_cols:
                    metadata_count = len(lsi_enriched.dropna(subset=metadata_cols, how='all'))

            st.markdown(f"""
            **LSI sales records enriched with publication metadata**
            - Total LSI sales records: **{len(lsi_enriched):,}**
            - Records with metadata: **{metadata_count:,}**
            - Metadata enrichment adds: Publication dates, descriptions, BISAC categories, and more
            """)

            # LSI enriched data filters
            lsi_filter_col1, lsi_filter_col2 = st.columns(2)

            with lsi_filter_col1:
                lsi_revenue_filter = st.selectbox(
                    "LSI Revenue Filter",
                    ["All", "No Sales", "$1-100", "$100-1000", "$1000+"],
                    key="lsi_revenue_filter"
                )

            with lsi_filter_col2:
                # Get available columns and safe defaults
                available_cols = [col for col in lsi_enriched.columns if col in ['Title', 'Author', 'Pub Date', 'Description', 'BISAC Category', 'Format', 'Net Compensation', 'Net Qty', 'Gross Qty', 'Returned Qty']]
                safe_defaults = [col for col in ['Title', 'Author', 'Net Compensation', 'Net Qty', 'Pub Date'] if col in available_cols]

                lsi_show_cols = st.multiselect(
                    "Show LSI Columns",
                    available_cols,
                    default=safe_defaults,
                    key="lsi_show_cols"
                )

            # Filter LSI data
            lsi_display_df = lsi_enriched.copy()

            # Apply revenue filter
            if lsi_revenue_filter == "No Sales":
                lsi_display_df = lsi_display_df[lsi_display_df.get('Net Compensation', 0) == 0]
            elif lsi_revenue_filter == "$1-100":
                lsi_display_df = lsi_display_df[(lsi_display_df.get('Net Compensation', 0) > 0) & (lsi_display_df.get('Net Compensation', 0) <= 100)]
            elif lsi_revenue_filter == "$100-1000":
                lsi_display_df = lsi_display_df[(lsi_display_df.get('Net Compensation', 0) > 100) & (lsi_display_df.get('Net Compensation', 0) <= 1000)]
            elif lsi_revenue_filter == "$1000+":
                lsi_display_df = lsi_display_df[lsi_display_df.get('Net Compensation', 0) > 1000]

            # Display LSI enriched data
            if lsi_show_cols and not lsi_display_df.empty:
                available_cols = [col for col in lsi_show_cols if col in lsi_display_df.columns]
                if available_cols:
                    display_lsi = lsi_display_df[available_cols].copy()

                    # Format currency columns
                    currency_cols = ['Net Compensation']
                    for col in currency_cols:
                        if col in display_lsi.columns:
                            display_lsi[col] = display_lsi[col].fillna(0).apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")

                    # Format unit columns
                    unit_cols = ['Net Qty', 'Gross Qty', 'Returned Qty']
                    for col in unit_cols:
                        if col in display_lsi.columns:
                            display_lsi[col] = display_lsi[col].fillna(0).apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")

                    st.write(f"**Showing {len(display_lsi):,} LSI records** (filtered from {len(lsi_enriched):,} total)")
                    st.dataframe(display_lsi, use_container_width=True, hide_index=True)
                else:
                    st.info("No available columns to display")
            else:
                st.info("Select columns to display or check data availability")

# Add the new metadata integration tab
with metadata_tab:
    st.header("🔍 Enhanced Metadata Integration")

    st.markdown("""
    This view shows how the FullMetadataEnhanced object combines multiple data sources
    to create comprehensive book metadata with financial performance data.
    """)

    # Processing status overview
    st.subheader("🔄 Processing Status")

    status_cols = st.columns(4)
    status_components = processed_data.get('processing_status', {})

    for i, (component, status) in enumerate(status_components.items()):
        with status_cols[i % 4]:
            if 'success' in status:
                st.success(f"**{component.title()}**\n{status}")
            elif 'error' in status:
                st.error(f"**{component.title()}**\n{status}")
            elif 'missing' in status:
                st.warning(f"**{component.title()}**\n{status}")
            else:
                st.info(f"**{component.title()}**\n{status}")

    # Source data summary
    st.subheader("📊 Data Source Summary")

    source_attribution = processed_data.get('source_attribution', {})

    # Handle different source attribution structures
    if merger_type == 'bidirectional':
        # Bidirectional merger has different structure
        st.info("**Bidirectional Merger Configuration**")
        st.write(f"**Merger Type**: {source_attribution.get('merger_type', 'Unknown')}")
        st.write(f"**Processing Method**: {source_attribution.get('processing_method', 'Unknown')}")

        # Show merge statistics
        merge_stats = source_attribution.get('merge_statistics', {})
        if merge_stats:
            st.write("**Merge Statistics**:")
            for stat_name, stat_value in merge_stats.items():
                if isinstance(stat_value, (int, float)):
                    st.write(f"- {stat_name.replace('_', ' ').title()}: {stat_value:,}")
                else:
                    st.write(f"- {stat_name.replace('_', ' ').title()}: {stat_value}")
    else:
        # Original source attribution structure
        for source_name, source_info in source_attribution.items():
            # Ensure source_info is a dictionary
            if not isinstance(source_info, dict):
                st.warning(f"Invalid source info for {source_name}: {type(source_info)}")
                continue

            with st.expander(f"📄 {source_name.replace('_', ' ').title()}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Source Type**: {source_info.get('source_type', 'Unknown')}")
                    st.write(f"**Records**: {source_info.get('record_count', 0):,}")
                    if 'file_info' in source_info and isinstance(source_info['file_info'], dict):
                        file_info = source_info['file_info']
                        st.write(f"**File**: {file_info.get('original_name', 'Unknown')}")
                        st.write(f"**Upload Time**: {file_info.get('upload_time', 'Unknown')}")

                with col2:
                    if 'columns' in source_info and isinstance(source_info['columns'], list):
                        st.write(f"**Available Columns** ({len(source_info['columns'])})")
                        st.text("\n".join(source_info['columns'][:10]) +
                                ("\n..." if len(source_info['columns']) > 10 else ""))
                    if 'processing_method' in source_info:
                        st.write(f"**Processing Method**: {source_info['processing_method']}")

    # Integration statistics
    st.subheader("🔗 Integration Statistics")

    if enhanced_metadata is not None:
        # Safe column access for integration stats
        has_lsi_sales = enhanced_metadata.get('has_lsi_sales', pd.Series([False] * len(enhanced_metadata), dtype=bool))
        has_kdp_sales = enhanced_metadata.get('has_kdp_sales', pd.Series([False] * len(enhanced_metadata), dtype=bool))
        has_any_sales = enhanced_metadata.get('has_any_sales', pd.Series([False] * len(enhanced_metadata), dtype=bool))

        integration_stats = {
            "Total Books in Catalog": len(enhanced_metadata),
            "Books with LSI Data": len(enhanced_metadata[has_lsi_sales]),
            "Books with KDP Data": len(enhanced_metadata[has_kdp_sales]),
            "Books with Both LSI & KDP": len(enhanced_metadata[has_lsi_sales & has_kdp_sales]),
            "Books with Financial Data": len(enhanced_metadata[has_any_sales])
        }

        stats_df = pd.DataFrame(list(integration_stats.items()), columns=['Metric', 'Count'])
        stats_df['Percentage'] = (stats_df['Count'] / len(enhanced_metadata) * 100).round(1)
        stats_df['Percentage'] = stats_df['Percentage'].apply(lambda x: f"{x}%")

        st.dataframe(stats_df, hide_index=True)
    else:
        st.warning("No integration statistics available")

with sources_tab:
    st.header("📁 Data Sources & Attribution")

    # Show comprehensive source information
    source_display.render_source_summary(processed_data.get('source_attribution', {}))

    st.markdown("---")

    # Data quality assessment
    source_display.render_data_quality_indicator(
        processed_data.get('source_attribution', {}),
        processed_data
    )

    st.markdown("---")

    # Processing status
    source_display.render_processing_status(processed_data)

    st.markdown("---")

    # Detailed source table
    source_display.render_detailed_source_table(processed_data.get('source_attribution', {}))

# Footer with refresh and export options
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("🔄 Refresh Enhanced Data"):
        st.cache_data.clear()
        st.rerun()

with col2:
    if st.button("📅 Export Enhanced Data"):
        if enhanced_metadata is not None and not enhanced_metadata.empty:
            # Create export data
            export_data = enhanced_metadata.copy()

            # Format currency columns for export
            currency_cols = ['total_revenue', 'lsi_net_compensation', 'kdp_usdeq_royalty', 'revenue_per_unit',
                           'total_revenue_all_channels', 'total_compensation_all_channels', 'revenue_per_unit_all_channels',
                           'revenue_per_month_in_print', 'revenue_per_compensated_month_in_print']
            for col in currency_cols:
                if col in export_data.columns:
                    export_data[col] = export_data[col].fillna(0).round(2)

            # Convert to CSV
            csv = export_data.to_csv(index=False)

            st.download_button(
                label="📥 Download Enhanced Metadata CSV",
                data=csv,
                file_name=f"enhanced_books_metadata_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No enhanced metadata available to export")

with col3:
    st.caption(
        f"📅 Last updated: {processed_data.get('last_updated', 'Unknown')} | "
        f"User: {current_username} | "
        f"Records: {processed_data.get('record_count', 0):,}"
    )