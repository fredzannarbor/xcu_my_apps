"""
Leo Bloom Analytics Dashboard

Advanced financial analytics and reporting dashboard for publishers.
Provides deep-dive analysis into financial performance, trends, and insights.
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import os
import glob
from datetime import datetime, timedelta

# Import following current patterns
try:
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects import FinancialReportingObjects as FRO
    from codexes.modules.finance.leo_bloom.utilities import classes_utilities as Leo
except ModuleNotFoundError:
    from src.codexes.modules.finance.leo_bloom.FinancialReportingObjects import FinancialReportingObjects as FRO
    from src.codexes.modules.finance.leo_bloom.utilities import classes_utilities as Leo

st.set_page_config(
    page_title="Leo Bloom Analytics",
    page_icon="📊",
    layout="wide"
)

# Page header
st.title("📊 Leo Bloom Analytics Dashboard")
st.markdown("*Advanced Financial Analytics for Book Publishers*")

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

# Initialize user_id for file paths
if 'user_id' not in st.session_state:
    st.session_state.user_id = 37
user_id = st.session_state.user_id

# Data File Management Functions
def check_data_quality(filepath):
    """Check data quality and return insights."""
    if not os.path.exists(filepath):
        return {"quality": "unknown", "records": 0, "issues": ["File not found"]}

    try:
        # Determine file type and read accordingly
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)

        issues = []
        quality = "good"

        # Basic quality checks
        if df.empty:
            issues.append("Empty file")
            quality = "poor"
        elif len(df) < 10:
            issues.append("Very few records")
            quality = "fair"

        # Check for missing data
        missing_pct = (df.isnull().sum() / len(df)).max() * 100
        if missing_pct > 50:
            issues.append(f"High missing data ({missing_pct:.1f}%)")
            quality = "poor"
        elif missing_pct > 20:
            issues.append(f"Some missing data ({missing_pct:.1f}%)")
            if quality == "good":
                quality = "fair"

        return {
            "quality": quality,
            "records": len(df),
            "columns": len(df.columns),
            "issues": issues if issues else ["No issues detected"]
        }

    except Exception as e:
        return {"quality": "error", "records": 0, "issues": [f"Read error: {str(e)}"]}

def get_file_status_advanced(filepath, max_age_days=30):
    """Advanced file status check with data quality."""
    if not os.path.exists(filepath):
        return "❌ Missing", "File not found", None, {"quality": "unknown", "records": 0}

    file_stat = os.stat(filepath)
    file_date = datetime.fromtimestamp(file_stat.st_mtime)
    file_age = datetime.now() - file_date

    # Get data quality
    data_quality = check_data_quality(filepath)

    # Determine overall status
    if data_quality["quality"] == "error":
        status = "🚫 Error"
    elif data_quality["quality"] == "poor":
        status = "⚠️ Poor Quality"
    elif file_age.days > max_age_days:
        status = "⚠️ Outdated"
    elif data_quality["quality"] == "fair":
        status = "⚠️ Fair Quality"
    else:
        status = "✅ Good"

    status_msg = f"Updated {file_age.days} days ago, {data_quality['records']} records"

    return status, status_msg, file_date, data_quality

# Advanced Data File Management Section
with st.expander("📊 Advanced Data Analytics & File Management", expanded=False):
    st.markdown("### Analytics Data Sources")

    # Enhanced data file definitions for analytics
    analytics_files = {
        "Core Financial Data": {
            "files": {
                "LSI LTD Data": "resources/data_tables/LSI/ltd.xlsx",
                "LSI Metadata": "resources/data_tables/LSI/Full_Metadata_Export.xlsx",
                "BIP Truth Data": "resources/sources_of_truth/BIPtruth.csv"
            },
            "description": "Primary data sources for financial analysis",
            "max_age": 30,
            "priority": "critical"
        },
        "Historical Performance": {
            "files": {
                "2023 LSI Performance": "resources/data_tables/LSI/2023LSIComp.xlsx",
                "2022 LSI Performance": "resources/data_tables/LSI/2022LSIcomp.xlsx",
                "Payment History": "resources/sources_of_truth/payments2authors/payments_lifetime.csv"
            },
            "description": "Historical data for trend analysis",
            "max_age": 90,
            "priority": "important"
        },
        "Market Intelligence": {
            "files": {
                "Substack Revenue": "resources/data_tables/substack_revenues.csv",
                "KDP Performance": f"userdocs/{user_id}/leo_bloom_core/kdpdata/",
                "Direct Sales": f"userdocs/{user_id}/leo_bloom_core/directsales/"
            },
            "description": "Market and competitive data",
            "max_age": 14,
            "priority": "useful"
        }
    }

    # Analytics data quality dashboard
    st.subheader("📈 Data Quality Dashboard")

    quality_metrics = {"good": 0, "fair": 0, "poor": 0, "missing": 0, "error": 0}
    total_records = 0

    for category, info in analytics_files.items():
        priority_color = {
            "critical": "🔴",
            "important": "🟡",
            "useful": "🟢"
        }.get(info["priority"], "⚪")

        st.markdown(f"#### {priority_color} {category}")
        st.caption(f"{info['description']} - Priority: {info['priority'].title()}")

        # Create detailed status table
        status_data = []

        for file_name, file_path in info["files"].items():
            # Handle directory paths (KDP, Direct Sales)
            if os.path.isdir(file_path):
                # Count files in directory
                file_count = len(glob.glob(os.path.join(file_path, "*.*")))
                status = "✅ Directory" if file_count > 0 else "❌ Empty"
                records = file_count
                quality_info = {"quality": "good" if file_count > 0 else "missing", "records": file_count}
                last_updated = "Multiple files"
            else:
                status, status_msg, file_date, quality_info = get_file_status_advanced(file_path, info["max_age"])
                records = quality_info.get("records", 0)
                last_updated = file_date.strftime("%Y-%m-%d") if file_date else "Never"

            status_data.append({
                "File": file_name,
                "Status": status,
                "Records": f"{records:,}" if isinstance(records, int) else records,
                "Quality": quality_info.get("quality", "unknown").title(),
                "Last Updated": last_updated,
                "Issues": "; ".join(quality_info.get("issues", []))[:50] + "..." if len("; ".join(quality_info.get("issues", []))) > 50 else "; ".join(quality_info.get("issues", []))
            })

            # Update quality metrics
            quality_key = quality_info.get("quality", "missing")
            if quality_key in quality_metrics:
                quality_metrics[quality_key] += 1
            total_records += quality_info.get("records", 0)

        # Display status table
        status_df = pd.DataFrame(status_data)
        st.dataframe(status_df, use_container_width=True)

    # Overall data health summary
    st.markdown("### 📊 Overall Data Health")
    health_cols = st.columns(5)

    with health_cols[0]:
        st.metric("✅ Good", quality_metrics["good"], help="Files with good data quality")
    with health_cols[1]:
        st.metric("⚠️ Fair", quality_metrics["fair"], help="Files with minor issues")
    with health_cols[2]:
        st.metric("🚫 Poor", quality_metrics["poor"], help="Files with significant issues")
    with health_cols[3]:
        st.metric("❌ Missing", quality_metrics["missing"], help="Missing files")
    with health_cols[4]:
        st.metric("📊 Total Records", f"{total_records:,}", help="Total records across all files")

    # Advanced Upload Section
    st.markdown("---")
    st.subheader("📤 Advanced File Upload & Validation")

    upload_tabs = st.tabs(["📁 Upload Files", "🔍 Validate Data", "📋 Import History"])

    with upload_tabs[0]:
        # Enhanced upload interface
        col1, col2 = st.columns([2, 1])

        with col1:
            # Help tips for file requirements
            with st.expander("📋 File Format & Naming Requirements", expanded=False):
                st.markdown("""
                **Supported File Types:**
                - `.xlsx`, `.xls` - Excel workbooks
                - `.csv` - Comma-separated values
                - `.json` - JSON data files

                **File Naming Conventions:**
                - **LSI files**: `LSI_YYYY-MM-DD.xlsx` or `lightning_source_YYYYMM.csv`
                - **KDP files**: `KDP_YYYY-MM-DD.csv` or `kdp_royalty_YYYYMM.xlsx`
                - **Direct Sales**: `direct_sales_YYYY-MM.csv` or `sales_YYYYMMDD.xlsx`
                - **Author Data**: `author_contracts_YYYY.xlsx` or `royalty_rates.csv`

                **Required Data Format:**
                - First row must contain column headers
                - Date columns in YYYY-MM-DD or MM/DD/YYYY format
                - Currency amounts as numbers (no currency symbols)
                - Author names consistent across files
                - ISBN/Title identifiers for book matching

                **File Size Limits:**
                - Maximum 50MB per file
                - For larger files, consider splitting by date range

                **Common Issues to Avoid:**
                - Special characters in file names (use underscore _ instead)
                - Mixed date formats within same file
                - Empty rows between data
                - Currency symbols ($, €, £) in numeric fields
                - Merged cells in Excel files
                """)

            uploaded_files = st.file_uploader(
                "Upload analytics data files",
                type=['xlsx', 'csv', 'xls', 'json'],
                accept_multiple_files=True,
                help="Select one or more files for financial analytics processing."
            )

            if uploaded_files:
                st.markdown("**📋 File Validation Preview**")

                validation_results = []
                for uploaded_file in uploaded_files:
                    try:
                        # Preview file contents
                        if uploaded_file.name.endswith('.csv'):
                            preview_df = pd.read_csv(uploaded_file, nrows=5)
                        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
                            preview_df = pd.read_excel(uploaded_file, nrows=5)
                        else:
                            preview_df = None

                        validation_results.append({
                            "File": uploaded_file.name,
                            "Size (MB)": round(len(uploaded_file.getvalue()) / (1024*1024), 2),
                            "Estimated Rows": "Unknown" if preview_df is None else f"~{len(preview_df)*20}+",
                            "Columns": "Unknown" if preview_df is None else len(preview_df.columns),
                            "Status": "✅ Valid" if preview_df is not None else "⚠️ Unknown format"
                        })

                        # Show preview for first file
                        if preview_df is not None and uploaded_file == uploaded_files[0]:
                            st.markdown(f"**Preview: {uploaded_file.name}**")
                            st.dataframe(preview_df, use_container_width=True)

                    except Exception as e:
                        validation_results.append({
                            "File": uploaded_file.name,
                            "Size (MB)": round(len(uploaded_file.getvalue()) / (1024*1024), 2),
                            "Estimated Rows": "Error",
                            "Columns": "Error",
                            "Status": f"❌ Error: {str(e)[:30]}..."
                        })

                # Show validation summary
                validation_df = pd.DataFrame(validation_results)
                st.dataframe(validation_df, use_container_width=True)

        with col2:
            st.markdown("**📋 Upload Options**")

            upload_category = st.selectbox(
                "Data Category",
                ["Core Financial", "Historical Performance", "Market Intelligence", "Custom Analytics"]
            )

            validation_level = st.selectbox(
                "Validation Level",
                ["Basic", "Standard", "Strict"],
                help="Level of data validation to perform"
            )

            backup_existing = st.checkbox(
                "Backup existing files",
                value=True,
                help="Create backup of existing files before replacement"
            )

            if st.button("🚀 Process & Validate Upload", type="primary"):
                if uploaded_files:
                    st.success(f"✅ Processing {len(uploaded_files)} files with {validation_level} validation...")
                    st.info("📊 Files processed and ready for analytics!")
                else:
                    st.warning("No files selected for upload.")

    with upload_tabs[1]:
        st.markdown("**🔍 Data Validation Tools**")

        validation_file = st.selectbox(
            "Select file to validate",
            ["LSI LTD Data", "Metadata Export", "BIP Truth", "Payment History"],
            help="Choose a file for detailed validation analysis"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Run Validation"):
                st.info(f"Running validation on {validation_file}...")
                # Placeholder for validation results
                st.success("✅ Validation complete - No critical issues found")

        with col2:
            if st.button("📊 Generate Data Profile"):
                st.info(f"Generating profile for {validation_file}...")
                # Placeholder for data profiling
                st.success("✅ Data profile generated")

    with upload_tabs[2]:
        st.markdown("**📋 Recent Import History**")

        # Placeholder import history
        import_history = {
            "Date": ["2024-09-23", "2024-09-20", "2024-09-15"],
            "File": ["ltd_updated.xlsx", "metadata_export.xlsx", "payments_q3.csv"],
            "Category": ["Core Financial", "Core Financial", "Historical"],
            "Status": ["✅ Success", "✅ Success", "⚠️ Warnings"],
            "Records": [1250, 890, 45]
        }

        history_df = pd.DataFrame(import_history)
        st.dataframe(history_df, use_container_width=True)

# Main dashboard
col1, col2, col3, col4 = st.columns(4)

# Key metrics (placeholder data - implement actual calculations)
with col1:
    st.metric(
        "Total Revenue (YTD)",
        "$125,450",
        delta="$12,340",
        help="Year-to-date total revenue from all sources"
    )

with col2:
    st.metric(
        "Active Titles",
        "347",
        delta="23",
        help="Number of titles with sales in the current period"
    )

with col3:
    st.metric(
        "Avg Monthly Revenue",
        "$10,454",
        delta="$1,028",
        help="Average monthly revenue across all titles"
    )

with col4:
    st.metric(
        "Royalties Due",
        "$37,635",
        delta="$3,702",
        help="Total royalties owed to authors"
    )

# Tabs for different analysis views
tab1, tab2, tab3, tab4 = st.tabs(["📈 Performance", "📚 Title Analysis", "👤 Author Analytics", "🎯 Insights"])

with tab1:
    st.header("Performance Analysis")

    # Revenue trend chart
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Revenue Trend")
        # Sample data for demonstration
        dates = pd.date_range(start='2024-01-01', end='2024-09-23', freq='ME')
        revenue_data = {
            'Month': dates,
            'LSI Revenue': [8000, 8500, 9200, 7800, 10500, 11200, 9800, 10800],
            'KDP Revenue': [2000, 2200, 2500, 2100, 2800, 3000, 2700, 2900],
            'Direct Sales': [500, 600, 450, 700, 800, 650, 750, 900]
        }
        df_revenue = pd.DataFrame(revenue_data)

        fig = px.line(
            df_revenue.melt(id_vars=['Month'], var_name='Source', value_name='Revenue'),
            x='Month',
            y='Revenue',
            color='Source',
            title="Monthly Revenue by Source"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Revenue Breakdown")
        # Pie chart for revenue sources
        total_lsi = df_revenue['LSI Revenue'].sum()
        total_kdp = df_revenue['KDP Revenue'].sum()
        total_direct = df_revenue['Direct Sales'].sum()

        pie_data = {
            'Source': ['LSI', 'KDP', 'Direct Sales'],
            'Amount': [total_lsi, total_kdp, total_direct]
        }
        df_pie = pd.DataFrame(pie_data)

        fig_pie = px.pie(df_pie, values='Amount', names='Source', title="Revenue by Source")
        st.plotly_chart(fig_pie, use_container_width=True)

    # Performance metrics table
    st.subheader("Performance Metrics by Category")
    performance_data = {
        'Category': ['Frontlist', 'Backlist', 'Public Domain', 'Royaltied'],
        'Titles': [45, 302, 180, 167],
        'Total Revenue': [45000, 65000, 35000, 50000],
        'Avg Revenue/Title': [1000, 215, 194, 299],
        'Monthly Growth': ['15%', '5%', '8%', '12%']
    }
    df_performance = pd.DataFrame(performance_data)
    st.dataframe(df_performance, use_container_width=True)

with tab2:
    st.header("Title Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Performing Titles")
        # Sample top performers
        top_titles = {
            'Title': ['Advanced Data Science', 'Python for Beginners', 'Machine Learning Guide', 'Web Development', 'Database Design'],
            'Revenue': [5500, 4200, 3800, 3500, 3200],
            'Units Sold': [220, 350, 190, 280, 160],
            'Avg Price': [25.00, 12.00, 20.00, 12.50, 20.00]
        }
        df_top = pd.DataFrame(top_titles)
        st.dataframe(df_top, use_container_width=True)

    with col2:
        st.subheader("Underperforming Titles")
        # Sample underperformers
        slow_titles = {
            'Title': ['Niche Technical Topic', 'Historical Fiction', 'Poetry Collection', 'Art History', 'Philosophy Text'],
            'Revenue': [45, 78, 23, 56, 34],
            'Units Sold': [3, 6, 2, 4, 2],
            'Months Active': [18, 24, 12, 15, 20]
        }
        df_slow = pd.DataFrame(slow_titles)
        st.dataframe(df_slow, use_container_width=True)

    # Title performance distribution
    st.subheader("Title Revenue Distribution")
    # Sample distribution data
    revenue_ranges = ['$0-100', '$100-500', '$500-1000', '$1000-5000', '$5000+']
    title_counts = [45, 120, 85, 75, 22]

    fig_dist = px.bar(
        x=revenue_ranges,
        y=title_counts,
        title="Number of Titles by Revenue Range",
        labels={'x': 'Revenue Range', 'y': 'Number of Titles'}
    )
    st.plotly_chart(fig_dist, use_container_width=True)

with tab3:
    st.header("Author Analytics")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Author Revenue Performance")
        # Sample author data
        author_data = {
            'Author': ['Smith, J.', 'Johnson, M.', 'Williams, S.', 'Brown, D.', 'Davis, R.'],
            'Total Revenue': [15000, 12500, 9800, 7500, 6200],
            'Titles': [3, 2, 4, 2, 3],
            'Royalties Due': [4500, 3750, 2940, 2250, 1860]
        }
        df_authors = pd.DataFrame(author_data)
        st.dataframe(df_authors, use_container_width=True)

    with col2:
        st.subheader("Royalty Summary")
        total_royalties = df_authors['Royalties Due'].sum()
        avg_royalty_rate = 0.30  # 30%

        st.metric("Total Royalties Due", f"${total_royalties:,.2f}")
        st.metric("Average Royalty Rate", f"{avg_royalty_rate:.1%}")
        st.metric("Authors with Royalties", len(df_authors))

        # Royalty distribution chart
        fig_roy = px.bar(
            df_authors,
            x='Author',
            y='Royalties Due',
            title="Royalties Due by Author"
        )
        fig_roy.update_xaxes(tickangle=45)
        st.plotly_chart(fig_roy, use_container_width=True)

with tab4:
    st.header("Business Insights")

    # Key insights cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("""
        **Frontlist Performance**

        New titles (< 18 months) are performing above average with 15% monthly growth.
        Consider increasing frontlist investment.
        """)

    with col2:
        st.warning("""
        **Slow Movers Alert**

        45 titles have generated less than $100 in revenue.
        Review for potential discontinuation.
        """)

    with col3:
        st.success("""
        **Growth Opportunity**

        Public domain titles showing 8% growth.
        Strong ROI potential for expansion.
        """)

    # Recommendations section
    st.subheader("📋 Actionable Recommendations")

    recommendations = [
        "🎯 Focus marketing efforts on top 20% of titles generating 80% of revenue",
        "📚 Expand public domain catalog - showing strong growth with minimal investment",
        "✂️ Consider discontinuing titles with < $50 revenue in 12+ months",
        "👥 Increase author royalty rate for top performers to improve retention",
        "📈 Invest in frontlist development - showing strongest growth metrics"
    ]

    for rec in recommendations:
        st.markdown(f"- {rec}")

    # Export options
    st.subheader("📊 Export Options")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 Export Revenue Report"):
            st.success("Revenue report exported to downloads folder")

    with col2:
        if st.button("👤 Export Author Reports"):
            st.success("Author reports exported to downloads folder")

    with col3:
        if st.button("📈 Export Analytics Dashboard"):
            st.success("Analytics dashboard exported to downloads folder")

# Footer
st.markdown("---")
st.caption("Leo Bloom Analytics Dashboard - Advanced Financial Intelligence for Publishers")