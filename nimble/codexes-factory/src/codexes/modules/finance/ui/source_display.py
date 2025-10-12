"""
Data Source Display Component

Provides transparent display of data sources and attribution
for financial metrics and reports.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import streamlit as st

logger = logging.getLogger(__name__)


class DataSourceDisplay:
    """
    Component for displaying data source attribution and transparency.

    Shows users exactly which files and data sources generated
    each financial metric or report.
    """

    def __init__(self):
        pass

    def render_source_info(self, metric_name: str, source_metadata: Dict,
                          expanded: bool = False, show_details: bool = True):
        """
        Show which files/data sources generated a specific metric.

        Args:
            metric_name: Name of the metric or report
            source_metadata: Metadata about the data sources
            expanded: Whether to show the expander expanded by default
            show_details: Whether to show detailed file information
        """
        if not source_metadata:
            st.info(f"ℹ️ No data sources available for {metric_name}")
            return

        total_sources = self._count_total_sources(source_metadata)

        with st.expander(f"📊 Data Sources for {metric_name} ({total_sources} files)", expanded=expanded):
            self._render_source_details(source_metadata, show_details)

    def render_source_summary(self, source_metadata: Dict):
        """
        Render a compact summary of data sources.

        Args:
            source_metadata: Complete source metadata from FRO coordinator
        """
        st.markdown("### 📋 Data Source Summary")

        if not source_metadata:
            st.info("No data sources available")
            return

        # Create summary metrics
        col1, col2, col3, col4 = st.columns(4)

        lsi_sources = source_metadata.get('lsi_sources', {}).get('files', [])
        kdp_sources = source_metadata.get('kdp_sources', {}).get('files', [])
        direct_sources = source_metadata.get('direct_sales_sources', {}).get('files', [])
        author_sources = source_metadata.get('author_sources', {}).get('files', [])

        with col1:
            st.metric(
                label="📊 LSI Files",
                value=len(lsi_sources),
                help="Lightning Source/IngramSpark compensation files"
            )

        with col2:
            st.metric(
                label="📚 KDP Files",
                value=len(kdp_sources),
                help="Amazon KDP royalty files"
            )

        with col3:
            st.metric(
                label="💰 Direct Sales",
                value=len(direct_sources),
                help="Direct sales data files"
            )

        with col4:
            st.metric(
                label="✍️ Author Data",
                value=len(author_sources),
                help="Author contracts and metadata files"
            )

    def render_detailed_source_table(self, source_metadata: Dict):
        """
        Render a detailed table of all data sources.

        Args:
            source_metadata: Complete source metadata
        """
        st.markdown("### 📁 Detailed File Information")

        all_files = []

        # Collect all files from different sources
        for source_type, source_info in source_metadata.items():
            if not source_info or 'files' not in source_info:
                continue

            for file_info in source_info['files']:
                file_record = {
                    'Source Type': source_type.replace('_sources', '').replace('_', ' ').title(),
                    'Original Name': file_info.get('original_name', 'Unknown'),
                    'Upload Date': self._format_datetime(file_info.get('upload_time')),
                    'Category': file_info.get('category', 'Unknown'),
                    'Destination': file_info.get('destination', 'Main'),
                    'Size (KB)': round(file_info.get('file_size', 0) / 1024, 1)
                }
                all_files.append(file_record)

        if all_files:
            # Sort by upload date (most recent first)
            all_files.sort(key=lambda x: x['Upload Date'], reverse=True)

            import pandas as pd
            df = pd.DataFrame(all_files)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No file data available")

    def render_user_attribution(self, username: str, user_id: str, last_updated: Optional[str] = None):
        """
        Show user attribution for the data.

        Args:
            username: Username of the data owner
            user_id: User ID of the data owner
            last_updated: Last update timestamp
        """
        st.markdown("### 👤 Data Attribution")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"**User:** {username}")

        with col2:
            st.write(f"**User ID:** {user_id}")

        with col3:
            if last_updated:
                formatted_date = self._format_datetime(last_updated)
                st.write(f"**Last Updated:** {formatted_date}")
            else:
                st.write("**Last Updated:** Never")

    def render_processing_status(self, processed_data: Dict):
        """
        Show processing status and any errors.

        Args:
            processed_data: Result from FRO coordinator processing
        """
        st.markdown("### ⚙️ Processing Status")

        # Check for processing errors
        errors = processed_data.get('processing_errors', [])
        lsi_errors = processed_data.get('lsi_processing_errors', [])
        kdp_errors = processed_data.get('kdp_processing_errors', [])
        direct_errors = processed_data.get('direct_sales_processing_errors', [])

        all_errors = errors + lsi_errors + kdp_errors + direct_errors

        if all_errors:
            st.warning("⚠️ Processing Issues Found:")
            for error in all_errors:
                st.write(f"• {error}")
        else:
            st.success("✅ All data processed successfully")

        # Show processing summary
        processing_summary = {}

        if 'lsi_processed_data' in processed_data:
            lsi_summary = processed_data['lsi_processed_data'].get('summary', {})
            if lsi_summary:
                processing_summary['LSI Data'] = f"{lsi_summary.get('total_records', 0)} records processed"

        if 'kdp_processed_data' in processed_data:
            kdp_summary = processed_data['kdp_processed_data'].get('summary', {})
            if kdp_summary:
                processing_summary['KDP Data'] = f"{kdp_summary.get('total_records', 0)} records processed"

        if 'direct_sales_processed_data' in processed_data:
            direct_summary = processed_data['direct_sales_processed_data'].get('summary', {})
            if direct_summary:
                processing_summary['Direct Sales'] = f"{direct_summary.get('total_records', 0)} records processed"

        if processing_summary:
            st.write("**Processing Summary:**")
            for category, summary in processing_summary.items():
                st.write(f"• {category}: {summary}")

    def _render_source_details(self, source_metadata: Dict, show_details: bool):
        """Render detailed source information."""
        username = source_metadata.get('username', 'Unknown User')
        user_id = source_metadata.get('user_id', 'Unknown ID')

        st.markdown(f"**User:** {username} (ID: {user_id})")

        # Show each source type
        for source_type, source_info in source_metadata.items():
            if source_type in ['username', 'user_id']:
                continue

            if not source_info or 'files' not in source_info:
                continue

            files = source_info['files']
            if not files:
                continue

            source_title = source_type.replace('_sources', '').replace('_', ' ').title()

            st.markdown(f"**{source_title}:**")

            if show_details:
                for file_info in files:
                    upload_date = self._format_datetime(file_info.get('upload_time'))
                    file_size = file_info.get('file_size', 0)

                    st.write(f"• {file_info.get('original_name', 'Unknown')} "
                            f"(uploaded {upload_date}, {file_size:,} bytes)")
            else:
                st.write(f"• {len(files)} file(s)")

    def _count_total_sources(self, source_metadata: Dict) -> int:
        """Count total number of source files."""
        total = 0
        for source_type, source_info in source_metadata.items():
            if source_type in ['username', 'user_id']:
                continue
            if source_info and 'files' in source_info:
                total += len(source_info['files'])
        return total

    def _format_datetime(self, datetime_str: Optional[str]) -> str:
        """Format datetime string for display."""
        if not datetime_str:
            return "Unknown"

        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return datetime_str

    def render_metric_with_sources(self, metric_name: str, metric_value: str,
                                  source_metadata: Dict, delta: Optional[str] = None,
                                  help_text: Optional[str] = None):
        """
        Render a metric with integrated source information.

        Args:
            metric_name: Name of the metric
            metric_value: Value to display
            source_metadata: Source metadata
            delta: Optional delta value for st.metric
            help_text: Optional help text
        """
        # Create metric
        if delta:
            st.metric(
                label=metric_name,
                value=metric_value,
                delta=delta,
                help=help_text
            )
        else:
            st.metric(
                label=metric_name,
                value=metric_value,
                help=help_text
            )

        # Add compact source info
        if source_metadata:
            total_sources = self._count_total_sources(source_metadata)
            if total_sources > 0:
                st.caption(f"📊 Based on {total_sources} data file(s)")

    def render_compact_source_badge(self, source_metadata: Dict):
        """
        Render a compact badge showing source information.

        Args:
            source_metadata: Source metadata
        """
        if not source_metadata:
            return

        total_sources = self._count_total_sources(source_metadata)
        username = source_metadata.get('username', 'Unknown')

        if total_sources > 0:
            st.markdown(
                f'<div style="background-color: #f0f2f6; padding: 5px 10px; border-radius: 5px; font-size: 0.8em; margin: 5px 0;">'
                f'📊 Data from {total_sources} file(s) | User: {username}'
                f'</div>',
                unsafe_allow_html=True
            )

    def render_data_quality_indicator(self, source_metadata: Dict, processed_data: Dict):
        """
        Show a data quality indicator based on sources and processing.

        Args:
            source_metadata: Source metadata
            processed_data: Processed data results
        """
        # Calculate quality score
        quality_score = self._calculate_quality_score(source_metadata, processed_data)

        if quality_score >= 80:
            quality_color = "green"
            quality_text = "High Quality"
            quality_icon = "✅"
        elif quality_score >= 60:
            quality_color = "orange"
            quality_text = "Medium Quality"
            quality_icon = "⚠️"
        else:
            quality_color = "red"
            quality_text = "Low Quality"
            quality_icon = "❌"

        st.markdown(
            f'<div style="color: {quality_color}; font-weight: bold;">'
            f'{quality_icon} Data Quality: {quality_text} ({quality_score}%)'
            f'</div>',
            unsafe_allow_html=True
        )

    def _calculate_quality_score(self, source_metadata: Dict, processed_data: Dict) -> int:
        """Calculate a data quality score."""
        score = 100

        # Deduct points for missing sources
        total_sources = self._count_total_sources(source_metadata)
        if total_sources == 0:
            return 0

        # Deduct points for processing errors
        all_errors = []
        for error_key in ['processing_errors', 'lsi_processing_errors',
                         'kdp_processing_errors', 'direct_sales_processing_errors']:
            errors = processed_data.get(error_key, [])
            all_errors.extend(errors)

        error_penalty = min(len(all_errors) * 15, 50)  # Max 50 point penalty
        score -= error_penalty

        # Bonus for recent data
        # This could be enhanced to check file ages

        return max(score, 0)