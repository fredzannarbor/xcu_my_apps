"""
FRO Coordinator

Centralizes Financial Reporting Objects processing and provides
unified interface between user data and FRO computations.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .user_data_manager import UserDataManager

# Import following current patterns
try:
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects
    from codexes.modules.finance.leo_bloom.ui.LeoBloom import (
        ingest_lsi, ingest_direct_sales, create_date_variables
    )
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.KDP_Financial_Reporting_Objects import Ingest_KDP_by_Month
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.DirectSales import ingest_direct_sales as fro_ingest_direct_sales
except ModuleNotFoundError:
    from src.codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects
    from src.codexes.modules.finance.leo_bloom.ui.LeoBloom import (
        ingest_lsi, ingest_direct_sales, create_date_variables
    )
    from src.codexes.modules.finance.leo_bloom.FinancialReportingObjects.KDP_Financial_Reporting_Objects import Ingest_KDP_by_Month
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
            if data_type == 'lsi' or data_type == 'all':
                result.update(self._process_lsi_data())

            if data_type == 'kdp' or data_type == 'all':
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
                    # Use existing LSI ingest function
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
            if not kdp_files:
                logger.info("No KDP files found for processing")
                return kdp_result

            # Process through KDP FRO
            kdp_data_path = self.processing_paths['userdocs_kdpdata_path']

            if Path(kdp_data_path).exists() and any(Path(kdp_data_path).iterdir()):
                try:
                    # Use existing KDP ingest function (call as static method)
                    processed_kdp = Ingest_KDP_by_Month.ingest_kdp_by_month(kdp_data_path)
                    kdp_result['kdp_processed_data'] = {
                        'raw_data': processed_kdp,
                        'summary': self._generate_kdp_summary(processed_kdp) if processed_kdp is not None else {}
                    }
                except Exception as e:
                    logger.error(f"Error in KDP ingest: {e}")
                    kdp_result['kdp_processing_errors'] = [str(e)]

        except Exception as e:
            logger.error(f"Error processing KDP data: {e}")
            kdp_result['kdp_processing_errors'] = [str(e)]

        return kdp_result

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