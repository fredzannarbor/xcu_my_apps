"""
Unified Finance Data Uploader

Single, consistent upload interface for all finance data types,
replacing multiple redundant upload points across the finance module.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import streamlit as st

from ..core.user_data_manager import UserDataManager
from ..core.fro_coordinator import FROCoordinator

logger = logging.getLogger(__name__)


class UnifiedFinanceUploader:
    """
    Single upload component for all financial data types.

    Replaces multiple upload interfaces with one consistent component
    that handles all file types through the centralized data manager.
    """

    def __init__(self, user_data_manager: UserDataManager, fro_coordinator: FROCoordinator):
        self.udm = user_data_manager
        self.fro_coord = fro_coordinator

        # Define data categories and their requirements
        self.data_categories = {
            'lsi_data': {
                'title': 'LSI Compensation Files',
                'description': 'Lightning Source/IngramSpark compensation reports',
                'file_types': ['xlsx', 'csv', 'xls'],
                'naming_pattern': 'LSI_compensation_YYYY-MM-DD.xlsx or lightning_source_YYYYMM.csv',
                'required_columns': ['ISBN', 'Title', 'Author', 'Format', 'Gross Qty', 'Returned Qty', 'Net Qty', 'Net Compensation', 'Sales Market'],
                'icon': '📊',
                'destinations': ['YTD', 'LYTD', 'LTD', 'ThisMonth']
            },
            'lsi_metadata': {
                'title': 'LSI Books in Print Metadata',
                'description': 'Lightning Source/IngramSpark books in print status and metadata',
                'file_types': ['xlsx', 'csv', 'xls'],
                'naming_pattern': 'LSI_metadata_YYYY-MM-DD.xlsx or books_in_print.csv',
                'required_columns': ['ISBN', 'Title', 'Contributor 1 Name', 'Status', 'Format'],
                'icon': '📚',
                'destinations': ['Current', 'Archive', 'Updates']
            },
            'kdp_data': {
                'title': 'KDP Royalty Files',
                'description': 'Amazon KDP royalty and sales reports',
                'file_types': ['xlsx', 'csv', 'xls'],
                'naming_pattern': 'KDP_Orders-XXXXX.xlsx or kdp_royalty_YYYYMM.xlsx',
                'required_columns': ['Royalty Date', 'Title', 'Author Name', 'ASIN/ISBN', 'Marketplace', 'Units Sold', 'Royalty', 'Currency'],
                'icon': '📚',
                'destinations': ['LTD']
            },
            'direct_sales': {
                'title': 'Direct Sales Data',
                'description': 'Direct sales from your own channels',
                'file_types': ['xlsx', 'csv', 'xls'],
                'naming_pattern': 'direct_sales_YYYY-MM.xlsx or sales_YYYYMMDD.xlsx',
                'required_columns': ['ASIN/ISBN', 'Title', 'royaltied_author_id', 'YTD_net_quantity', 'USDeq_pub_comp'],
                'icon': '💰',
                'destinations': ['Website', 'Events', 'Wholesale', 'Other']
            },
            'author_data': {
                'title': 'Author & Contract Data',
                'description': 'Author contracts, royalty rates, and metadata',
                'file_types': ['xlsx', 'csv', 'xls'],
                'naming_pattern': 'author_contracts_YYYY.xlsx or royaltied_authors.xlsx',
                'required_columns': ['royaltied_author_id', 'Author', 'Title', 'Royalty Rate'],
                'icon': '✍️',
                'destinations': ['Contracts', 'Rates', 'Metadata']
            },
            'market_data': {
                'title': 'Market & Analytics Data',
                'description': 'Market research, competitive analysis, trend data',
                'file_types': ['xlsx', 'csv', 'xls', 'json'],
                'naming_pattern': 'market_analysis_YYYYMM.xlsx or trends_YYYY.json',
                'required_columns': None,  # Variable based on data type
                'icon': '📈',
                'destinations': ['Research', 'Trends', 'Competition', 'Custom']
            }
        }

    def _read_csv_with_encoding(self, file_path, **kwargs):
        """
        Read CSV file with automatic encoding detection.

        Args:
            file_path: Path to CSV file
            **kwargs: Additional arguments to pass to pd.read_csv

        Returns:
            DataFrame with the CSV data
        """
        import pandas as pd
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']

        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding, **kwargs)
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                # For non-encoding errors, raise immediately
                raise

        raise ValueError(f"Unable to read CSV file {file_path} with any standard encoding")

    def render_upload_interface(self):
        """Render the complete unified upload interface."""
        st.header("📤 Financial Data Upload Center")

        # Show current data status
        self._render_data_status_overview()

        # Main upload interface
        upload_tab, manage_tab, history_tab = st.tabs([
            "📁 Upload Files",
            "🗂️ Manage Data",
            "📋 Upload History"
        ])

        with upload_tab:
            self._render_upload_tab()

        with manage_tab:
            self._render_manage_tab()

        with history_tab:
            self._render_history_tab()

    def _render_data_status_overview(self):
        """Show overview of current data status."""
        st.subheader("📊 Current Data Status")

        cols = st.columns(len(self.data_categories))

        for i, (category, info) in enumerate(self.data_categories.items()):
            with cols[i]:
                files = self.udm.list_files(category)
                file_count = len(files)

                last_update = "Never"
                if files:
                    last_update = max(f['upload_time'] for f in files)
                    last_update = datetime.fromisoformat(last_update).strftime("%Y-%m-%d")

                st.metric(
                    label=f"{info['icon']} {info['title']}",
                    value=f"{file_count} files",
                    delta=f"Updated: {last_update}"
                )

    def _render_upload_tab(self):
        """Render the main upload interface."""
        st.subheader("Upload Financial Data Files")

        # Category selection
        col1, col2 = st.columns([1, 2])

        with col1:
            selected_category = st.selectbox(
                "Select Data Category",
                options=list(self.data_categories.keys()),
                format_func=lambda x: f"{self.data_categories[x]['icon']} {self.data_categories[x]['title']}"
            )

        with col2:
            category_info = self.data_categories[selected_category]

            # Show destination options if available
            destination = None
            if category_info.get('destinations'):
                destination = st.selectbox(
                    "Destination/Subcategory",
                    options=category_info['destinations'],
                    help="Organize files into subcategories for better management"
                )

        # Show requirements for selected category
        self._show_category_requirements(selected_category)

        # File uploader
        uploaded_files = st.file_uploader(
            f"Upload {category_info['title']}",
            type=category_info['file_types'],
            accept_multiple_files=True,
            help=f"Upload files for {category_info['description']}"
        )

        # Process uploads
        if uploaded_files:
            self._process_uploads(uploaded_files, selected_category, destination)

    def _show_category_requirements(self, category: str):
        """Show requirements for the selected category."""
        info = self.data_categories[category]

        with st.expander(f"📋 Requirements for {info['title']}", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**File Requirements:**")
                st.write(f"• **File Types:** {', '.join(info['file_types'])}")
                st.write(f"• **Naming Pattern:** {info['naming_pattern']}")
                st.write("• **Max File Size:** 50MB")

            with col2:
                st.markdown("**Data Format:**")
                if info['required_columns']:
                    st.write("**Required Columns:**")
                    for col in info['required_columns']:
                        st.write(f"• {col}")
                else:
                    st.write("• Variable format based on data type")
                st.write("• First row must contain headers")
                st.write("• Dates in YYYY-MM-DD format")
                st.write("• Numbers without currency symbols")

    def _process_uploads(self, uploaded_files: List, category: str, destination: Optional[str]):
        """Process uploaded files through the data manager."""
        st.subheader("📋 Upload Processing")

        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()

        upload_results = []
        total_files = len(uploaded_files)

        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")
            progress_bar.progress((i + 1) / total_files)

            try:
                # Check for duplicates first
                duplicates = self.udm.find_duplicates(uploaded_file, category, destination)

                if duplicates:
                    duplicate_info = []
                    for dup in duplicates:
                        if dup['duplicate_type'] == 'identical_content':
                            duplicate_info.append(f"Identical file: {dup['original_name']} (uploaded {dup['upload_time'][:10]})")
                        else:
                            duplicate_info.append(f"Similar file: {dup['original_name']} (similarity: {dup.get('similarity_score', 0):.0%})")

                    upload_results.append({
                        'filename': uploaded_file.name,
                        'status': 'duplicate',
                        'message': f"Potential duplicates found: {'; '.join(duplicate_info)}",
                        'duplicates': duplicates
                    })
                    continue

                # Validate file format
                is_valid, error_message = self.udm.validate_file_format(
                    uploaded_file,
                    self.data_categories[category].get('required_columns')
                )

                if not is_valid:
                    upload_results.append({
                        'filename': uploaded_file.name,
                        'status': 'error',
                        'message': error_message
                    })
                    continue

                # Save file through data manager
                file_path, file_metadata = self.udm.save_uploaded_file(
                    uploaded_file, category, destination
                )

                # Debug output for KDP files
                if category == 'kdp_data':
                    st.info(f"📋 KDP file saved: {uploaded_file.name} → destination: {destination}")
                    st.info(f"📋 File pattern analysis: starts with KDP_Order? {uploaded_file.name.startswith('KDP_Order')}")

                upload_results.append({
                    'filename': uploaded_file.name,
                    'status': 'success',
                    'message': 'File uploaded successfully',
                    'file_path': file_path,
                    'metadata': file_metadata
                })

            except Exception as e:
                logger.error(f"Error uploading {uploaded_file.name}: {e}")
                upload_results.append({
                    'filename': uploaded_file.name,
                    'status': 'error',
                    'message': str(e)
                })

        # Show results
        self._show_upload_results(upload_results)

        # Clear cache to force refresh of processed data
        self.fro_coord.clear_cache()

        # Offer to process data immediately
        if any(r['status'] == 'success' for r in upload_results):
            if st.button("🔄 Process Data Now"):
                self._process_data_after_upload(category)

    def _show_upload_results(self, results: List[Dict]):
        """Display upload results."""
        st.subheader("📊 Upload Results")

        success_count = sum(1 for r in results if r['status'] == 'success')
        error_count = sum(1 for r in results if r['status'] == 'error')
        duplicate_count = sum(1 for r in results if r['status'] == 'duplicate')

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ Successful", success_count)
        with col2:
            st.metric("❌ Errors", error_count)
        with col3:
            st.metric("⚠️ Duplicates", duplicate_count)

        # Show detailed results
        for result in results:
            if result['status'] == 'success':
                st.success(f"✅ {result['filename']}: {result['message']}")
            elif result['status'] == 'duplicate':
                with st.expander(f"⚠️ {result['filename']}: Potential duplicate detected", expanded=False):
                    st.warning(result['message'])

                    # Show duplicate management options
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"🗑️ Delete Old Files", key=f"delete_dups_{result['filename']}"):
                            self._handle_duplicate_resolution(result, 'delete_old')
                    with col2:
                        if st.button(f"📤 Upload Anyway", key=f"force_upload_{result['filename']}"):
                            self._handle_duplicate_resolution(result, 'upload_anyway')
            else:
                st.error(f"❌ {result['filename']}: {result['message']}")

    def _process_data_after_upload(self, category: str):
        """Process data through FRO after successful upload."""
        with st.spinner("Processing uploaded data through Financial Reporting Objects..."):
            try:
                processed_result = self.fro_coord.process_user_data(category, force_refresh=True)

                if processed_result.get('processing_errors'):
                    st.warning("⚠️ Some processing errors occurred:")
                    for error in processed_result['processing_errors']:
                        st.write(f"• {error}")
                else:
                    st.success("✅ Data processed successfully!")

                    # Show basic processing summary
                    summary_data = processed_result.get('processed_data', {})
                    if summary_data:
                        st.write("**Processing Summary:**")
                        for key, value in summary_data.items():
                            if isinstance(value, dict) and 'summary' in value:
                                st.write(f"• {key}: {value['summary']}")

            except Exception as e:
                st.error(f"❌ Error processing data: {e}")
                logger.error(f"Error processing data after upload: {e}")

    def _handle_duplicate_resolution(self, result: Dict, action: str):
        """Handle duplicate file resolution actions."""
        if action == 'delete_old':
            # Delete the duplicate files
            deleted_count = 0
            for duplicate in result.get('duplicates', []):
                if self.udm.delete_file(duplicate['category'], duplicate['saved_name']):
                    deleted_count += 1

            if deleted_count > 0:
                st.success(f"🗑️ Deleted {deleted_count} duplicate file(s). You can now re-upload {result['filename']}.")
                st.rerun()
            else:
                st.error("❌ Failed to delete duplicate files")

        elif action == 'upload_anyway':
            # Force upload by temporarily bypassing duplicate check
            st.info(f"🔄 Force uploading {result['filename']}...")
            # This would need to be implemented by modifying the upload process
            # For now, show instructions to user
            st.info("💡 To force upload, delete this file and re-upload, or rename the file before uploading.")

    def _render_manage_tab(self):
        """Render the data management interface."""
        st.subheader("🗂️ Manage Your Financial Data")

        # Category selector for management
        category = st.selectbox(
            "Select Category to Manage",
            options=list(self.data_categories.keys()),
            format_func=lambda x: f"{self.data_categories[x]['icon']} {self.data_categories[x]['title']}",
            key="manage_category"
        )

        files = self.udm.list_files(category)

        if not files:
            st.info(f"No files found in {self.data_categories[category]['title']}")
            return

        st.write(f"**Files in {self.data_categories[category]['title']}:**")

        # Show files with management options
        for file_info in files:
            with st.expander(f"{file_info['original_name']} ({file_info['upload_time'][:10]})", expanded=False):
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.write(f"**Original Name:** {file_info['original_name']}")
                    st.write(f"**Saved As:** {file_info['saved_name']}")
                    st.write(f"**Size:** {file_info['file_size']:,} bytes")
                    st.write(f"**Uploaded:** {file_info['upload_time']}")

                with col2:
                    if st.button("🔍 Preview", key=f"preview_{file_info['saved_name']}"):
                        self._preview_file(category, file_info['saved_name'])

                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{file_info['saved_name']}"):
                        if self.udm.delete_file(category, file_info['saved_name']):
                            st.success(f"Deleted {file_info['original_name']}")
                            st.rerun()
                        else:
                            st.error("Failed to delete file")

    def _preview_file(self, category: str, filename: str):
        """Show a preview of the file contents."""
        try:
            file_path = self.udm.get_file_path(category, filename)

            if file_path and file_path.exists():
                import pandas as pd

                # Try to read the file
                if file_path.suffix.lower() == '.csv':
                    df = self._read_csv_with_encoding(file_path, nrows=10)
                elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                    df = pd.read_excel(file_path, nrows=10)
                else:
                    st.error("Cannot preview this file type")
                    return

                st.write(f"**Preview of {filename} (first 10 rows):**")
                st.dataframe(df)
            else:
                st.error("File not found")

        except Exception as e:
            st.error(f"Error previewing file: {e}")

    def _render_history_tab(self):
        """Render the upload history interface."""
        st.subheader("📋 Upload History")

        # Get all metadata
        all_metadata = self.udm.get_data_source_metadata()
        file_history = all_metadata.get('file_history', [])

        if not file_history:
            st.info("No upload history available")
            return

        # Sort by upload time (most recent first)
        file_history = sorted(file_history, key=lambda x: x['upload_time'], reverse=True)

        st.write(f"**Total uploads:** {len(file_history)}")

        # Show recent uploads
        for i, file_info in enumerate(file_history[:20]):  # Show last 20 uploads
            upload_date = datetime.fromisoformat(file_info['upload_time']).strftime("%Y-%m-%d %H:%M")
            category_info = self.data_categories.get(file_info['category'], {})
            category_title = category_info.get('title', file_info['category'])

            st.write(f"{i+1}. **{file_info['original_name']}** → {category_title} ({upload_date})")

        if len(file_history) > 20:
            st.info(f"Showing 20 most recent uploads out of {len(file_history)} total uploads")

    def get_upload_status_summary(self) -> Dict:
        """Get summary of upload status for external display."""
        summary = {
            'categories': {},
            'total_files': 0,
            'last_activity': None
        }

        for category in self.data_categories.keys():
            files = self.udm.list_files(category)
            summary['categories'][category] = {
                'file_count': len(files),
                'last_updated': self.udm.get_data_source_metadata(category).get('last_updated')
            }
            summary['total_files'] += len(files)

        # Find most recent activity
        all_metadata = self.udm.get_data_source_metadata()
        file_history = all_metadata.get('file_history', [])
        if file_history:
            summary['last_activity'] = max(f['upload_time'] for f in file_history)

        return summary