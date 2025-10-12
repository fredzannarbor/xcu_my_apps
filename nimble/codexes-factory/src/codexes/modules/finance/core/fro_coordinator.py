"""
FRO Coordinator

Centralizes Financial Reporting Objects processing and provides
unified interface between user data and FRO computations.
"""

import logging
import glob
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .user_data_manager import UserDataManager

# Import dataframe utils for PyArrow compatibility
try:
    from codexes.core.dataframe_utils import clean_dataframe_for_pyarrow, convert_to_arrow_compatible_types
except ModuleNotFoundError:
    from src.codexes.core.dataframe_utils import clean_dataframe_for_pyarrow, convert_to_arrow_compatible_types

# Import following current patterns
try:
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects
    from codexes.modules.finance.leo_bloom.ui.LeoBloom import (
        ingest_lsi, ingest_direct_sales, create_date_variables
    )
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.KDP_Financial_Reporting_Objects import Ingest_KDP_by_Month, Ingest_KDP_Lifetime_Data
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.DirectSales import ingest_direct_sales as fro_ingest_direct_sales
except ModuleNotFoundError:
    from src.codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects
    from src.codexes.modules.finance.leo_bloom.ui.LeoBloom import (
        ingest_lsi, ingest_direct_sales, create_date_variables
    )
    from src.codexes.modules.finance.leo_bloom.FinancialReportingObjects.KDP_Financial_Reporting_Objects import Ingest_KDP_by_Month, Ingest_KDP_Lifetime_Data
    from src.codexes.modules.finance.leo_bloom.FinancialReportingObjects.DirectSales import ingest_direct_sales as fro_ingest_direct_sales

logger = logging.getLogger(__name__)


class FROCoordinator:
    """
    Coordinates between User Data Manager and Financial Reporting Objects.

    Provides centralized processing of user financial data through FRO objects
    while maintaining source attribution and user data isolation.
    """

    def __init__(self, user_data_manager: UserDataManager):
        self.udm = user_data_manager
        self.processing_paths = user_data_manager.get_processing_paths()

        # Initialize FRO with user-specific root path
        try:
            self.fro = FinancialReportingObjects(self.processing_paths['userdocs_path'])
        except Exception as e:
            logger.error(f"Error initializing FRO: {e}")
            self.fro = None

        # Cache for processed data to avoid recomputation
        self._cache = {}

    def _read_csv_with_encoding(self, file_path, **kwargs) -> pd.DataFrame:
        """
        Read CSV file with automatic encoding detection.

        Args:
            file_path: Path to CSV file
            **kwargs: Additional arguments to pass to pd.read_csv

        Returns:
            DataFrame with the CSV data
        """
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']

        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding, **kwargs)
                logger.debug(f"Successfully read CSV {file_path} with encoding: {encoding}")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                # For non-encoding errors, raise immediately
                logger.error(f"Error reading CSV {file_path} with encoding {encoding}: {e}")
                raise

        raise ValueError(f"Unable to read CSV file {file_path} with any standard encoding")

    def process_user_data(self, data_type: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Process user's data through appropriate FRO objects.

        Args:
            data_type: Type of data to process ('lsi', 'kdp', 'direct_sales', 'all')
            force_refresh: Force reprocessing even if cached data exists

        Returns:
            Dictionary with processed data and source metadata
        """
        cache_key = f"{data_type}_{self.udm.username}"

        if not force_refresh and cache_key in self._cache:
            return self._cache[cache_key]

        result = {
            'data_type': data_type,
            'username': self.udm.username,
            'user_id': self.udm.user_id,
            'processed_data': {},
            'source_metadata': {},
            'processing_errors': []
        }

        try:
            if data_type in ['lsi', 'lsi_data'] or data_type == 'all':
                result.update(self._process_lsi_data())

            if data_type in ['kdp', 'kdp_data'] or data_type == 'all':
                result.update(self._process_kdp_data())

            if data_type == 'direct_sales' or data_type == 'all':
                result.update(self._process_direct_sales_data())

            if data_type == 'author_data' or data_type == 'all':
                result.update(self._process_author_data())

            # Cache the result
            self._cache[cache_key] = result

        except Exception as e:
            logger.error(f"Error processing {data_type} data for user {self.udm.username}: {e}")
            result['processing_errors'].append(str(e))

        return result

    def _process_lsi_data(self) -> Dict[str, Any]:
        """Process LSI data through appropriate FROs."""
        lsi_result = {
            'lsi_processed_data': {},
            'lsi_source_metadata': self.udm.get_data_source_metadata('lsi_data')
        }

        try:
            lsi_files = self.udm.list_files('lsi_data')
            if not lsi_files:
                logger.info("No LSI files found for processing")
                return lsi_result

            # Process through LSI ingest function
            lsi_data_path = self.processing_paths['userdocs_lsidata_path']

            if Path(lsi_data_path).exists() and any(Path(lsi_data_path).iterdir()):
                try:
                    # First try the new unified processing approach
                    processed_lsi = self._process_lsi_files_directly(lsi_data_path)
                    if processed_lsi is not None and len(processed_lsi) > 0:
                        lsi_result['lsi_processed_data'] = {
                            'raw_data': processed_lsi,
                            'summary': self._generate_lsi_summary(processed_lsi)
                        }
                    else:
                        # Fallback to original LSI ingest function
                        processed_lsi = ingest_lsi(lsi_data_path)
                        lsi_result['lsi_processed_data'] = {
                            'raw_data': processed_lsi,
                            'summary': self._generate_lsi_summary(processed_lsi) if processed_lsi is not None else {}
                        }
                except Exception as e:
                    logger.error(f"Error in LSI ingest: {e}")
                    lsi_result['lsi_processing_errors'] = [str(e)]

        except Exception as e:
            logger.error(f"Error processing LSI data: {e}")
            lsi_result['lsi_processing_errors'] = [str(e)]

        return lsi_result

    def _process_kdp_data(self) -> Dict[str, Any]:
        """Process KDP data through appropriate FROs."""
        kdp_result = {
            'kdp_processed_data': {},
            'kdp_source_metadata': self.udm.get_data_source_metadata('kdp_data')
        }

        try:
            kdp_files = self.udm.list_files('kdp_data')

            # Enhanced debugging for file discovery
            logger.info(f"KDP file search: udm.list_files('kdp_data') returned {len(kdp_files) if kdp_files else 0} files")
            print(f"🔍 DEBUG: KDP file search returned {len(kdp_files) if kdp_files else 0} files")

            if kdp_files:
                for i, file_info in enumerate(kdp_files):
                    logger.info(f"KDP file {i+1}: {file_info}")
                    print(f"🔍 DEBUG: KDP file {i+1}: {file_info}")

            if not kdp_files:
                logger.info("No KDP files found for processing")
                print("🔍 DEBUG: No KDP files found in user data manager")
                return kdp_result

            # Process files based on their destination (Monthly, Quarterly, YTD, LTD)
            processed_files = 0
            for file_info in kdp_files:
                destination = file_info.get('destination', 'Monthly')  # Default to Monthly
                full_file_path = self.udm.get_file_path('kdp_data', file_info['saved_name'])

                if full_file_path and full_file_path.exists():
                    try:
                        logger.info(f"Processing KDP {destination} file: {full_file_path}")

                        if destination == 'LTD':
                            # Use KDP Lifetime Data processor
                            processed_kdp = self._process_kdp_lifetime_file(str(full_file_path))
                        else:
                            # Use standard KDP processing for Monthly, Quarterly, YTD
                            processed_kdp = self._process_kdp_file_directly(str(full_file_path))

                        if processed_kdp is not None and len(processed_kdp) > 0:
                            kdp_result['kdp_processed_data'][destination] = {
                                'raw_data': processed_kdp,
                                'summary': self._generate_kdp_summary(processed_kdp)
                            }
                            logger.info(f"Successfully processed {len(processed_kdp)} KDP {destination} records")
                            processed_files += 1
                        else:
                            logger.warning(f"KDP {destination} processing returned empty data")

                    except Exception as e:
                        logger.error(f"Error in KDP {destination} ingest: {e}")
                        if 'kdp_processing_errors' not in kdp_result:
                            kdp_result['kdp_processing_errors'] = []
                        kdp_result['kdp_processing_errors'].append(f"{destination}: {str(e)}")
                else:
                    logger.error(f"KDP file not found: {full_file_path}")

            if processed_files == 0:
                kdp_result['kdp_processing_errors'] = ["No KDP files could be processed"]

        except Exception as e:
            logger.error(f"Error processing KDP data: {e}")
            kdp_result['kdp_processing_errors'] = [str(e)]

        return kdp_result

    def _process_kdp_file_directly(self, file_path: str) -> pd.DataFrame:
        """Simplified KDP file processing that handles different KDP file types and sheet names."""
        try:
            import os
            from pathlib import Path

            file_name = os.path.basename(file_path)
            logger.info(f"Processing KDP file: {file_name}")

            # Determine sheet name based on file naming pattern
            sheet_name = self._get_kdp_sheet_name(file_name, file_path)

            # Debug output showing which sheet is being read
            logger.info(f"Reading sheet '{sheet_name}' from file {file_name}")
            print(f"🔍 DEBUG: Reading sheet '{sheet_name}' from file {file_name}")

            # Add Streamlit notification for debugging
            try:
                import streamlit as st
                st.info(f"📋 Reading sheet '{sheet_name}' from file {file_name}")
            except Exception:
                pass  # Streamlit may not be available in all contexts

            # Read the Excel file with the determined sheet name
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            if len(df) == 0:
                logger.warning("KDP file is empty")
                return df

            # Add some basic calculated columns similar to FRO processing
            df['Net_Units_Sold'] = df.get('Units Sold', 0) - df.get('Units Refunded', 0)

            # Apply dataframe cleaning for PyArrow compatibility
            df = clean_dataframe_for_pyarrow(df)

            logger.info(f"Successfully processed KDP file with {len(df)} records from sheet '{sheet_name}'")
            return df

        except Exception as e:
            logger.error(f"Error in direct KDP processing: {e}")
            return pd.DataFrame()

    def _get_kdp_sheet_name(self, file_name: str, file_path: str) -> str:
        """Determine the correct sheet name for different KDP file types."""
        try:
            print(f"🔍 DEBUG: Analyzing file name pattern: {file_name}")

            # For KDP_Order* or KDP_Orders- files, use "Combined Sales" sheet
            if file_name.startswith('KDP_Order'):
                logger.info("Detected KDP_Order*/KDP_Orders- file, using 'Combined Sales' sheet")
                print(f"🔍 DEBUG: KDP_Order*/KDP_Orders- pattern detected -> 'Combined Sales' sheet")
                return 'Combined Sales'

            # For other KDP file patterns, try to detect available sheets
            import pandas as pd
            excel_file = pd.ExcelFile(file_path)
            available_sheets = excel_file.sheet_names
            logger.info(f"Available sheets in {file_name}: {available_sheets}")
            print(f"🔍 DEBUG: Available sheets: {available_sheets}")

            # Priority order for sheet names
            preferred_sheets = ['Combined Sales', 'Total Royalty', 'Royalty', 'Sales']

            for preferred in preferred_sheets:
                if preferred in available_sheets:
                    logger.info(f"Using sheet '{preferred}' for file {file_name}")
                    print(f"🔍 DEBUG: Found preferred sheet '{preferred}'")
                    return preferred

            # If no preferred sheet found, use the first available sheet
            if available_sheets:
                default_sheet = available_sheets[0]
                logger.warning(f"No preferred sheet found, using first available sheet '{default_sheet}' for {file_name}")
                print(f"🔍 DEBUG: Using first available sheet: '{default_sheet}'")
                return default_sheet

            # Fallback to 'Combined Sales' if no sheets detected
            logger.warning(f"Could not detect sheets, defaulting to 'Combined Sales' for {file_name}")
            print(f"🔍 DEBUG: No sheets detected, fallback to 'Combined Sales'")
            return 'Combined Sales'

        except Exception as e:
            logger.error(f"Error detecting sheet name for {file_name}: {e}")
            print(f"🔍 DEBUG: Error in sheet detection: {e}, fallback to 'Combined Sales'")
            # Default fallback
            return 'Combined Sales'

    def _process_kdp_lifetime_file(self, file_path: str) -> pd.DataFrame:
        """Process KDP Lifetime Data files using the existing KDP Lifetime processor."""
        try:
            from ..leo_bloom.FinancialReportingObjects.KDP_Financial_Reporting_Objects import Ingest_KDP_Lifetime_Data

            # Create a dummy parent instance for the KDP Lifetime processor
            class DummyParent:
                def __init__(self):
                    self.root = "."

            parent = DummyParent()
            kdp_lifetime_processor = Ingest_KDP_Lifetime_Data(parent)

            # Use the existing ingest method
            df = kdp_lifetime_processor.ingest_kdp_lifetime_data(file_path)

            if df is not None and len(df) > 0:
                # Apply dataframe cleaning for PyArrow compatibility
                df = clean_dataframe_for_pyarrow(df)
                logger.info(f"Successfully processed KDP Lifetime file with {len(df)} records")
                return df
            else:
                logger.warning("KDP Lifetime processing returned empty data")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error in KDP Lifetime processing: {e}")
            # Fallback to direct processing if KDP Lifetime processor fails
            return self._process_kdp_file_directly(file_path)

    def _process_direct_sales_data(self) -> Dict[str, Any]:
        """Process direct sales data through appropriate FROs."""
        direct_sales_result = {
            'direct_sales_processed_data': {},
            'direct_sales_source_metadata': self.udm.get_data_source_metadata('direct_sales')
        }

        try:
            direct_sales_files = self.udm.list_files('direct_sales')
            if not direct_sales_files:
                logger.info("No direct sales files found for processing")
                return direct_sales_result

            # Process through direct sales FRO
            direct_sales_path = self.processing_paths['userdocs_directsales_path']

            if Path(direct_sales_path).exists() and any(Path(direct_sales_path).iterdir()):
                try:
                    # Use existing direct sales ingest function
                    processed_direct = fro_ingest_direct_sales(direct_sales_path)
                    direct_sales_result['direct_sales_processed_data'] = {
                        'raw_data': processed_direct,
                        'summary': self._generate_direct_sales_summary(processed_direct) if processed_direct is not None else {}
                    }
                except Exception as e:
                    logger.error(f"Error in direct sales ingest: {e}")
                    direct_sales_result['direct_sales_processing_errors'] = [str(e)]

        except Exception as e:
            logger.error(f"Error processing direct sales data: {e}")
            direct_sales_result['direct_sales_processing_errors'] = [str(e)]

        return direct_sales_result

    def _process_author_data(self) -> Dict[str, Any]:
        """Process author data through appropriate FROs."""
        author_result = {
            'author_processed_data': {},
            'author_source_metadata': self.udm.get_data_source_metadata('author_data')
        }

        try:
            author_files = self.udm.list_files('author_data')
            if not author_files:
                logger.info("No author files found for processing")
                return author_result

            # Basic author data processing
            author_data_path = self.processing_paths['userdocs_authordata_path']

            if Path(author_data_path).exists():
                try:
                    # Look for common author data files
                    author_files_path = Path(author_data_path)
                    for file_path in author_files_path.glob("*.xlsx"):
                        try:
                            df = pd.read_excel(file_path)
                            author_result['author_processed_data'][file_path.name] = {
                                'data': df,
                                'summary': {
                                    'total_authors': len(df) if 'author' in df.columns or 'Author' in df.columns else 0,
                                    'columns': list(df.columns),
                                    'file_size': file_path.stat().st_size
                                }
                            }
                        except Exception as e:
                            logger.error(f"Error processing author file {file_path.name}: {e}")

                except Exception as e:
                    logger.error(f"Error processing author data: {e}")
                    author_result['author_processing_errors'] = [str(e)]

        except Exception as e:
            logger.error(f"Error in author data processing: {e}")
            author_result['author_processing_errors'] = [str(e)]

        return author_result

    def _process_lsi_files_directly(self, lsi_data_path: str) -> pd.DataFrame:
        """
        Process LSI files directly from the uploaded files directory.
        This handles files uploaded through the unified uploader with timestamp names.
        """

        lsi_path = Path(lsi_data_path)
        combined_df = pd.DataFrame()

        # Look for all Excel and CSV files in the directory and subdirectories
        file_patterns = [
            str(lsi_path / "*.xlsx"),
            str(lsi_path / "*.xls"),
            str(lsi_path / "*.csv"),
            str(lsi_path / "**" / "*.xlsx"),  # Recursive search
            str(lsi_path / "**" / "*.xls"),   # Recursive search
            str(lsi_path / "**" / "*.csv")    # Recursive search
        ]

        files_found = []
        for pattern in file_patterns:
            if "**" in pattern:
                # Use recursive glob for subdirectories
                files_found.extend(glob.glob(pattern, recursive=True))
            else:
                files_found.extend(glob.glob(pattern))

        # Remove duplicates while preserving order
        files_found = list(dict.fromkeys(files_found))

        if not files_found:
            logger.warning(f"No LSI files found in {lsi_data_path}")
            return None

        logger.info(f"Found {len(files_found)} LSI files to process")

        for file_path in files_found:
            try:
                logger.info(f"Processing LSI file: {file_path}")

                # Read the file based on extension
                if file_path.endswith('.csv'):
                    df = self._read_csv_with_encoding(file_path)
                elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                    df = pd.read_excel(file_path)
                else:
                    logger.warning(f"Skipping unsupported file type: {file_path}")
                    continue

                # Validate that it has the expected LSI columns
                expected_columns = ['ISBN', 'Title', 'Author', 'Format', 'Gross Qty', 'Returned Qty', 'Net Qty', 'Net Compensation', 'Sales Market']

                if all(col in df.columns for col in expected_columns):
                    logger.info(f"File {file_path} has all required LSI columns")
                    combined_df = pd.concat([combined_df, df], ignore_index=True)
                else:
                    missing_cols = [col for col in expected_columns if col not in df.columns]
                    logger.warning(f"File {file_path} missing columns: {missing_cols}")
                    logger.info(f"Available columns: {list(df.columns)}")

                    # Still try to process if it has most of the important columns
                    if 'ISBN' in df.columns and 'Title' in df.columns and 'Net Compensation' in df.columns:
                        logger.info(f"File {file_path} has core columns, processing anyway")
                        combined_df = pd.concat([combined_df, df], ignore_index=True)

            except Exception as e:
                logger.error(f"Error processing LSI file {file_path}: {e}")
                continue

        if len(combined_df) == 0:
            logger.warning("No valid LSI data found after processing all files")
            return None

        logger.info(f"Successfully combined {len(combined_df)} LSI records from {len(files_found)} files")

        # Clean the dataframe for PyArrow compatibility
        try:
            cleaned_df = clean_dataframe_for_pyarrow(combined_df)
            logger.debug("Cleaned LSI data for PyArrow compatibility")
            return cleaned_df
        except Exception as e:
            logger.warning(f"Error cleaning LSI data for PyArrow: {e}. Returning original data.")
            return combined_df

    def _generate_lsi_summary(self, lsi_data) -> Dict[str, Any]:
        """Generate summary statistics for LSI data."""
        if lsi_data is None or not isinstance(lsi_data, pd.DataFrame):
            return {}

        try:
            return {
                'total_records': len(lsi_data),
                'date_range': {
                    'start': lsi_data.index.min() if hasattr(lsi_data, 'index') else 'Unknown',
                    'end': lsi_data.index.max() if hasattr(lsi_data, 'index') else 'Unknown'
                },
                'columns': list(lsi_data.columns) if hasattr(lsi_data, 'columns') else [],
                'numeric_columns': list(lsi_data.select_dtypes(include=['number']).columns) if hasattr(lsi_data, 'select_dtypes') else []
            }
        except Exception as e:
            logger.error(f"Error generating LSI summary: {e}")
            return {}

    def _generate_kdp_summary(self, kdp_data) -> Dict[str, Any]:
        """Generate summary statistics for KDP data."""
        if kdp_data is None or not isinstance(kdp_data, pd.DataFrame):
            return {}

        try:
            return {
                'total_records': len(kdp_data),
                'columns': list(kdp_data.columns) if hasattr(kdp_data, 'columns') else [],
                'numeric_columns': list(kdp_data.select_dtypes(include=['number']).columns) if hasattr(kdp_data, 'select_dtypes') else []
            }
        except Exception as e:
            logger.error(f"Error generating KDP summary: {e}")
            return {}

    def _generate_direct_sales_summary(self, direct_sales_data) -> Dict[str, Any]:
        """Generate summary statistics for direct sales data."""
        if direct_sales_data is None or not isinstance(direct_sales_data, pd.DataFrame):
            return {}

        try:
            return {
                'total_records': len(direct_sales_data),
                'columns': list(direct_sales_data.columns) if hasattr(direct_sales_data, 'columns') else [],
                'numeric_columns': list(direct_sales_data.select_dtypes(include=['number']).columns) if hasattr(direct_sales_data, 'select_dtypes') else []
            }
        except Exception as e:
            logger.error(f"Error generating direct sales summary: {e}")
            return {}

    def get_display_data(self, metric: str, data_type: str = 'all') -> Dict[str, Any]:
        """
        Get processed data for display with source attribution.

        Args:
            metric: Specific metric to retrieve ('revenue', 'units', 'summary', etc.)
            data_type: Data type to process ('lsi', 'kdp', 'direct_sales', 'all')

        Returns:
            Dictionary with display data and source attribution
        """
        processed_data = self.process_user_data(data_type)

        display_result = {
            'metric': metric,
            'data_type': data_type,
            'username': self.udm.username,
            'display_data': {},
            'source_attribution': {},
            'last_updated': None
        }

        # Extract specific metric data based on request
        if metric == 'summary':
            display_result['display_data'] = self._extract_summary_data(processed_data)
        elif metric == 'revenue':
            display_result['display_data'] = self._extract_revenue_data(processed_data)
        elif metric == 'units':
            display_result['display_data'] = self._extract_units_data(processed_data)
        else:
            # Return all processed data
            display_result['display_data'] = processed_data.get('processed_data', {})

        # Add source attribution
        display_result['source_attribution'] = {
            'lsi_sources': processed_data.get('lsi_source_metadata', {}),
            'kdp_sources': processed_data.get('kdp_source_metadata', {}),
            'direct_sales_sources': processed_data.get('direct_sales_source_metadata', {}),
            'author_sources': processed_data.get('author_source_metadata', {})
        }

        return display_result

    def _extract_summary_data(self, processed_data: Dict) -> Dict:
        """Extract summary data for display."""
        summary = {}

        # LSI summary
        lsi_data = processed_data.get('lsi_processed_data', {}).get('summary', {})
        if lsi_data:
            summary['lsi'] = lsi_data

        # KDP summary
        kdp_data = processed_data.get('kdp_processed_data', {}).get('summary', {})
        if kdp_data:
            summary['kdp'] = kdp_data

        # Direct sales summary
        direct_data = processed_data.get('direct_sales_processed_data', {}).get('summary', {})
        if direct_data:
            summary['direct_sales'] = direct_data

        return summary

    def _extract_revenue_data(self, processed_data: Dict) -> Dict:
        """Extract revenue data for display."""
        revenue_data = {}

        # This would be expanded based on actual FRO data structure
        # For now, return basic structure
        return revenue_data

    def _extract_units_data(self, processed_data: Dict) -> Dict:
        """Extract units data for display."""
        units_data = {}

        # This would be expanded based on actual FRO data structure
        # For now, return basic structure
        return units_data

    def get_date_variables(self):
        """Get date variables using existing function."""
        try:
            return create_date_variables()
        except Exception as e:
            logger.error(f"Error getting date variables: {e}")
            from datetime import datetime, timedelta
            today = datetime.now()
            return (
                today.strftime('%Y-%m-%d'),  # today
                today.year,                   # thisyear
                f"{today.year}-01-01",       # starting_day_of_current_year
                today.timetuple().tm_yday,   # daysYTD
                365.0 / today.timetuple().tm_yday,  # annualizer
                today.month                   # this_year_month
            )

    def clear_cache(self):
        """Clear the processing cache to force refresh on next request."""
        self._cache = {}