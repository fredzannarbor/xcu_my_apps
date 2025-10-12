"""
Enhanced Metadata Processor for Books In Print

Creates a modernized FullMetadataEnhanced object that combines:
- LSI Books In Print Metadata (base)
- Direct sales data (LSI lifetime)
- Rights sales data (KDP lifetime)
- Contract information (royaltied/non-royaltied status)

This integrates with the current UserDataManager/FROCoordinator architecture
while providing comprehensive book metadata with financial performance.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Import dataframe utils for PyArrow compatibility
try:
    from codexes.core.dataframe_utils import clean_dataframe_for_pyarrow, convert_to_arrow_compatible_types
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.KDP_Financial_Reporting_Objects import Ingest_KDP_Lifetime_Data
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects
    from codexes.modules.finance.core.bidirectional_metadata_merger import BidirectionalMetadataMerger
except ModuleNotFoundError:
    from src.codexes.core.dataframe_utils import clean_dataframe_for_pyarrow, convert_to_arrow_compatible_types
    from src.codexes.modules.finance.leo_bloom.FinancialReportingObjects.KDP_Financial_Reporting_Objects import Ingest_KDP_Lifetime_Data
    from src.codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects
    from src.codexes.modules.finance.core.bidirectional_metadata_merger import BidirectionalMetadataMerger

logger = logging.getLogger(__name__)


class EnhancedMetadataProcessor:
    """
    Modern processor for creating enhanced metadata that combines
    LSI Books In Print data with financial and contract information.
    """

    def __init__(self, user_data_manager, fro_coordinator):
        self.udm = user_data_manager
        self.fro_coord = fro_coordinator
        self.enhanced_data = None
        self.source_attribution = {}
        self.processing_status = {}

    def create_enhanced_metadata(self, force_refresh: bool = False, use_bidirectional: bool = True) -> Dict[str, Any]:
        """
        Create enhanced metadata by combining all data sources.

        Args:
            force_refresh: Force reprocessing even if cached data exists
            use_bidirectional: Use bidirectional merger for comprehensive integration

        Returns:
            Dictionary with enhanced metadata and processing information
        """
        try:
            logger.info(f"Starting enhanced metadata processing (bidirectional: {use_bidirectional})")

            if use_bidirectional:
                # Use the new bidirectional merger for comprehensive integration
                return self._create_bidirectional_enhanced_metadata()
            else:
                # Use the original approach for backward compatibility
                return self._create_legacy_enhanced_metadata()

        except Exception as e:
            logger.error(f"Error in enhanced metadata processing: {e}")
            return self._create_error_response(f"Processing error: {str(e)}")

    def _create_bidirectional_enhanced_metadata(self) -> Dict[str, Any]:
        """
        Create enhanced metadata using the bidirectional merger.
        This provides comprehensive integration of metadata and sales data.
        """
        logger.info("Using bidirectional metadata merger")

        # Initialize the bidirectional merger
        bidirectional_merger = BidirectionalMetadataMerger(self.udm, self.fro_coord)

        # Perform comprehensive merger
        merger_result = bidirectional_merger.create_comprehensive_merger()

        if not merger_result['success']:
            return merger_result

        # Use the Books In Print enriched data as our primary enhanced metadata
        enhanced_df = merger_result['books_in_print_enriched']

        if enhanced_df.empty:
            return self._create_error_response("Bidirectional merger produced no results")

        # Add our standard calculated fields and enhancements
        enhanced_df = self._add_calculated_fields(enhanced_df)
        enhanced_df = self._ensure_essential_columns(enhanced_df)
        enhanced_df = clean_dataframe_for_pyarrow(enhanced_df)

        # Store results
        self.enhanced_data = enhanced_df

        # Create comprehensive result including all merger outputs
        result = {
            'enhanced_metadata': enhanced_df,
            'books_in_print_enriched': merger_result['books_in_print_enriched'],
            'kdp_consolidated_enriched': merger_result['kdp_consolidated_enriched'],
            'lsi_consolidated_enriched': merger_result['lsi_consolidated_enriched'],
            'source_attribution': {
                'merger_type': 'bidirectional',
                'merge_statistics': merger_result['merge_statistics'],
                'processing_method': 'comprehensive_bidirectional_merger'
            },
            'processing_status': {
                'bidirectional_merger': 'success',
                'enhanced_processing': 'success'
            },
            'record_count': len(enhanced_df),
            'last_updated': datetime.now().isoformat(),
            'success': True
        }

        logger.info(f"Bidirectional enhanced metadata processing completed: {result['record_count']} records")
        return result

    def _create_legacy_enhanced_metadata(self) -> Dict[str, Any]:
        """
        Create enhanced metadata using the original approach.
        This is for backward compatibility.
        """
        logger.info("Using legacy enhanced metadata approach")

        # Step 1: Load LSI Books In Print Metadata (base)
        base_metadata = self._load_base_metadata()
        if base_metadata is None:
            return self._create_error_response("No LSI metadata available")

        # Step 2: Load and integrate direct sales data (LSI lifetime)
        lsi_sales_data = self._load_lsi_sales_data()

        # Step 3: Load and integrate rights sales data (KDP lifetime)
        kdp_sales_data = self._load_kdp_sales_data()

        # Step 4: Load contract information (placeholder for now)
        contract_data = self._load_contract_data()

        # Step 5: Merge all data sources
        enhanced_df = self._merge_data_sources(
            base_metadata, lsi_sales_data, kdp_sales_data, contract_data
        )

        # Step 6: Add calculated fields and enhancements
        enhanced_df = self._add_calculated_fields(enhanced_df)

        # Step 7: Ensure essential columns exist with default values
        enhanced_df = self._ensure_essential_columns(enhanced_df)

        # Step 8: Clean and prepare for display
        enhanced_df = clean_dataframe_for_pyarrow(enhanced_df)

        # Store results
        self.enhanced_data = enhanced_df

        result = {
            'enhanced_metadata': enhanced_df,
            'source_attribution': self.source_attribution,
            'processing_status': self.processing_status,
            'record_count': len(enhanced_df) if enhanced_df is not None else 0,
            'last_updated': datetime.now().isoformat(),
            'success': True
        }

        logger.info(f"Legacy enhanced metadata processing completed: {result['record_count']} records")
        return result

    def _load_base_metadata(self) -> Optional[pd.DataFrame]:
        """Load LSI Books In Print metadata as the base dataset."""
        try:
            lsi_metadata_files = self.udm.list_files('lsi_metadata')

            if not lsi_metadata_files:
                logger.warning("No LSI metadata files found")
                self.processing_status['base_metadata'] = 'missing'
                return None

            # Get the most recent file
            latest_file = max(lsi_metadata_files, key=lambda x: x['upload_time'])
            file_path = self.udm.base_dir / latest_file['file_path']

            logger.info(f"Loading LSI metadata from: {file_path}")

            # Read CSV with encoding detection
            df = self.udm._read_csv_with_encoding(file_path)

            # Basic cleanup
            if 'ISBN' in df.columns:
                df['ISBN'] = df['ISBN'].astype(str).str.strip()

            # Standardize common LSI column names for consistency
            if 'Contributor One Name' in df.columns and 'Author' not in df.columns:
                df['Author'] = df['Contributor One Name']

            # Add source attribution
            self.source_attribution['base_metadata'] = {
                'source_type': 'lsi_metadata',
                'file_info': latest_file,
                'record_count': len(df),
                'columns': list(df.columns)
            }

            self.processing_status['base_metadata'] = 'success'
            logger.info(f"Loaded {len(df)} records from LSI metadata")
            return df

        except Exception as e:
            logger.error(f"Error loading base metadata: {e}")
            self.processing_status['base_metadata'] = f'error: {str(e)}'
            return None

    def _load_lsi_sales_data(self) -> Optional[pd.DataFrame]:
        """Load LSI lifetime sales data."""
        try:
            lsi_data_files = self.udm.list_files('lsi_data')

            if not lsi_data_files:
                logger.warning("No LSI sales data files found")
                self.processing_status['lsi_sales'] = 'missing'
                return None

            # Get the most recent file
            latest_file = max(lsi_data_files, key=lambda x: x['upload_time'])
            file_path = self.udm.base_dir / latest_file['file_path']

            logger.info(f"Loading LSI sales data from: {file_path}")

            # Read Excel file - LSI data is typically in Excel format
            df = pd.read_excel(file_path, engine='openpyxl')

            # Basic cleanup
            if 'ISBN' in df.columns:
                df['ISBN'] = df['ISBN'].astype(str).str.strip()

            # Standardize column names for LSI data
            df = self._standardize_lsi_columns(df)

            # Add source attribution
            self.source_attribution['lsi_sales'] = {
                'source_type': 'lsi_data',
                'file_info': latest_file,
                'record_count': len(df),
                'columns': list(df.columns)
            }

            self.processing_status['lsi_sales'] = 'success'
            logger.info(f"Loaded {len(df)} records from LSI sales data")
            return df

        except Exception as e:
            logger.error(f"Error loading LSI sales data: {e}")
            self.processing_status['lsi_sales'] = f'error: {str(e)}'
            return None

    def _load_kdp_sales_data(self) -> Optional[pd.DataFrame]:
        """Load KDP lifetime sales data."""
        try:
            kdp_data_files = self.udm.list_files('kdp_data')

            if not kdp_data_files:
                logger.warning("No KDP sales data files found")
                self.processing_status['kdp_sales'] = 'missing'
                return None

            # Get the most recent LTD file
            ltd_files = [f for f in kdp_data_files if f.get('destination') == 'LTD']
            if not ltd_files:
                logger.warning("No KDP LTD files found")
                self.processing_status['kdp_sales'] = 'no_ltd_files'
                return None

            latest_file = max(ltd_files, key=lambda x: x['upload_time'])
            file_path = self.udm.base_dir / latest_file['file_path']

            logger.info(f"Loading KDP sales data from: {file_path}")

            # Use the KDP lifetime processing logic
            try:
                fro = FinancialReportingObjects(self.udm.get_processing_paths()['userdocs_path'])
                kdp_processor = Ingest_KDP_Lifetime_Data(fro)

                # Process the KDP data
                df = kdp_processor.ingest_kdp_lifetime_data(str(file_path))

                # Ensure ISBN column exists and is properly formatted
                if 'ISBN' not in df.columns and 'ASIN' in df.columns:
                    # For KDP data, we often have ASIN instead of ISBN
                    df['ISBN'] = df['ASIN'].astype(str).str.strip()
                elif 'ISBN' in df.columns:
                    df['ISBN'] = df['ISBN'].astype(str).str.strip()

                # Standardize column names for KDP data
                df = self._standardize_kdp_columns(df)

                # Add source attribution
                self.source_attribution['kdp_sales'] = {
                    'source_type': 'kdp_data',
                    'file_info': latest_file,
                    'record_count': len(df),
                    'columns': list(df.columns),
                    'processing_method': 'kdp_lifetime_processor'
                }

                self.processing_status['kdp_sales'] = 'success'
                logger.info(f"Loaded {len(df)} records from KDP sales data")
                return df

            except Exception as e:
                logger.error(f"Error processing KDP data with FRO processor: {e}")
                # Fallback to simple Excel reading
                df = pd.read_excel(file_path, sheet_name='Combined Sales', engine='openpyxl')

                # Basic cleanup for fallback
                if 'ASIN' in df.columns:
                    df['ISBN'] = df['ASIN'].astype(str).str.strip()
                elif 'ISBN' in df.columns:
                    df['ISBN'] = df['ISBN'].astype(str).str.strip()

                self.source_attribution['kdp_sales'] = {
                    'source_type': 'kdp_data',
                    'file_info': latest_file,
                    'record_count': len(df),
                    'columns': list(df.columns),
                    'processing_method': 'fallback_excel_reader'
                }

                self.processing_status['kdp_sales'] = f'fallback_success: {str(e)}'
                return df

        except Exception as e:
            logger.error(f"Error loading KDP sales data: {e}")
            self.processing_status['kdp_sales'] = f'error: {str(e)}'
            return None

    def _load_contract_data(self) -> Optional[pd.DataFrame]:
        """Load contract information (royaltied/non-royaltied status)."""
        try:
            # For now, this is a placeholder
            # In production, this would load from a contract/rights management system
            # or from uploaded contract files

            logger.info("Contract data loading not yet implemented - using placeholder")
            self.processing_status['contract_data'] = 'placeholder'

            # Create a simple placeholder DataFrame with common contract statuses
            # This would be replaced with actual contract data loading
            placeholder_contracts = pd.DataFrame({
                'ISBN': [],  # Empty for now
                'royaltied': [],
                'contract_type': [],
                'royalty_rate': []
            })

            self.source_attribution['contract_data'] = {
                'source_type': 'placeholder',
                'record_count': 0,
                'status': 'not_implemented'
            }

            return placeholder_contracts

        except Exception as e:
            logger.error(f"Error loading contract data: {e}")
            self.processing_status['contract_data'] = f'error: {str(e)}'
            return None

    def _merge_data_sources(self, base_metadata: pd.DataFrame, lsi_sales: Optional[pd.DataFrame],
                          kdp_sales: Optional[pd.DataFrame], contract_data: Optional[pd.DataFrame]) -> pd.DataFrame:
        """Merge all data sources using ISBN as the key."""
        try:
            logger.info("Starting data source merging")

            # Start with base metadata
            enhanced_df = base_metadata.copy()

            # Merge LSI sales data
            if lsi_sales is not None and not lsi_sales.empty:
                enhanced_df = enhanced_df.merge(
                    lsi_sales.add_suffix('_lsi'),
                    left_on='ISBN',
                    right_on='ISBN_lsi',
                    how='left'
                )
                # Remove duplicate ISBN column
                if 'ISBN_lsi' in enhanced_df.columns:
                    enhanced_df = enhanced_df.drop('ISBN_lsi', axis=1)
                logger.info("Merged LSI sales data")

            # Merge KDP sales data
            if kdp_sales is not None and not kdp_sales.empty:
                enhanced_df = enhanced_df.merge(
                    kdp_sales.add_suffix('_kdp'),
                    left_on='ISBN',
                    right_on='ISBN_kdp',
                    how='left'
                )
                # Remove duplicate ISBN column
                if 'ISBN_kdp' in enhanced_df.columns:
                    enhanced_df = enhanced_df.drop('ISBN_kdp', axis=1)
                logger.info("Merged KDP sales data")

            # Merge contract data
            if contract_data is not None and not contract_data.empty:
                enhanced_df = enhanced_df.merge(
                    contract_data.add_suffix('_contract'),
                    left_on='ISBN',
                    right_on='ISBN_contract',
                    how='left'
                )
                # Remove duplicate ISBN column
                if 'ISBN_contract' in enhanced_df.columns:
                    enhanced_df = enhanced_df.drop('ISBN_contract', axis=1)
                logger.info("Merged contract data")

            logger.info(f"Data merging completed: {len(enhanced_df)} records")
            return enhanced_df

        except Exception as e:
            logger.error(f"Error merging data sources: {e}")
            # Return base metadata if merge fails
            return base_metadata

    def _standardize_lsi_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize LSI data column names."""
        column_mapping = {
            'Net Qty': 'lsi_net_qty',
            'Gross Qty': 'lsi_gross_qty',
            'Returned Qty': 'lsi_returned_qty',
            'Net Compensation': 'lsi_net_compensation',
            'Royalty Rate': 'lsi_royalty_rate'
        }

        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})

        return df

    def _standardize_kdp_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize KDP data column names."""
        column_mapping = {
            'Units Sold': 'kdp_units_sold',
            'Units Refunded': 'kdp_units_refunded',
            'Net Units Sold': 'kdp_net_units_sold',
            'Royalty': 'kdp_royalty',
            'USDeq_Royalty': 'kdp_usdeq_royalty',
            'Currency': 'kdp_currency',
            'List Price': 'kdp_list_price'
        }

        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})

        return df

    def _add_calculated_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add calculated fields and performance metrics."""
        try:
            logger.info("Adding calculated fields")

            # Total units sold across all channels
            df['total_units_sold'] = 0
            if 'lsi_net_qty' in df.columns:
                df['total_units_sold'] += df['lsi_net_qty'].fillna(0)
            if 'kdp_net_units_sold' in df.columns:
                df['total_units_sold'] += df['kdp_net_units_sold'].fillna(0)

            # Total revenue across all channels
            df['total_revenue'] = 0
            if 'lsi_net_compensation' in df.columns:
                df['total_revenue'] += df['lsi_net_compensation'].fillna(0)
            if 'kdp_usdeq_royalty' in df.columns:
                df['total_revenue'] += df['kdp_usdeq_royalty'].fillna(0)

            # Revenue per unit
            df['revenue_per_unit'] = df['total_revenue'] / df['total_units_sold'].replace(0, np.nan)

            # Channel distribution
            df['lsi_revenue_pct'] = 0
            df['kdp_revenue_pct'] = 0

            mask = df['total_revenue'] > 0
            if 'lsi_net_compensation' in df.columns:
                df.loc[mask, 'lsi_revenue_pct'] = (df.loc[mask, 'lsi_net_compensation'].fillna(0) /
                                                  df.loc[mask, 'total_revenue']) * 100
            if 'kdp_usdeq_royalty' in df.columns:
                df.loc[mask, 'kdp_revenue_pct'] = (df.loc[mask, 'kdp_usdeq_royalty'].fillna(0) /
                                                  df.loc[mask, 'total_revenue']) * 100

            # Performance categories
            df['performance_tier'] = 'No Sales'
            df.loc[df['total_revenue'] > 0, 'performance_tier'] = 'Low'
            df.loc[df['total_revenue'] > 1000, 'performance_tier'] = 'Medium'
            df.loc[df['total_revenue'] > 5000, 'performance_tier'] = 'High'
            df.loc[df['total_revenue'] > 10000, 'performance_tier'] = 'Top'

            # Sales status flags - ensure these columns always exist
            df['has_lsi_sales'] = False
            df['has_kdp_sales'] = False
            df['has_any_sales'] = False

            # Set LSI sales flag if LSI data is available
            if 'lsi_net_qty' in df.columns:
                df['has_lsi_sales'] = (df['lsi_net_qty'].fillna(0) > 0)

            # Set KDP sales flag if KDP data is available
            if 'kdp_net_units_sold' in df.columns:
                df['has_kdp_sales'] = (df['kdp_net_units_sold'].fillna(0) > 0)
            elif 'kdp_units_sold' in df.columns:
                df['has_kdp_sales'] = (df['kdp_units_sold'].fillna(0) > 0)

            # Overall sales flag
            df['has_any_sales'] = df['has_lsi_sales'] | df['has_kdp_sales']

            logger.info("Calculated fields added successfully")
            return df

        except Exception as e:
            logger.error(f"Error adding calculated fields: {e}")
            return df

    def _ensure_essential_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure that essential columns exist in the dataframe with appropriate defaults."""
        try:
            logger.info("Ensuring essential columns exist")

            # Define essential columns with their default values
            essential_columns = {
                'total_revenue': 0.0,
                'total_units_sold': 0,
                'revenue_per_unit': 0.0,
                'lsi_revenue_pct': 0.0,
                'kdp_revenue_pct': 0.0,
                'performance_tier': 'No Sales',
                'has_lsi_sales': False,
                'has_kdp_sales': False,
                'has_any_sales': False
            }

            # Add missing columns with default values
            for column, default_value in essential_columns.items():
                if column not in df.columns:
                    logger.info(f"Adding missing essential column: {column}")
                    if isinstance(default_value, bool):
                        df[column] = pd.Series([default_value] * len(df), dtype=bool)
                    elif isinstance(default_value, (int, float)):
                        df[column] = pd.Series([default_value] * len(df), dtype=type(default_value))
                    else:
                        df[column] = pd.Series([default_value] * len(df), dtype=str)

            logger.info("Essential columns verification completed")
            return df

        except Exception as e:
            logger.error(f"Error ensuring essential columns: {e}")
            return df

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            'enhanced_metadata': None,
            'source_attribution': self.source_attribution,
            'processing_status': self.processing_status,
            'record_count': 0,
            'error_message': error_message,
            'last_updated': datetime.now().isoformat(),
            'success': False
        }

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics for the enhanced metadata."""
        if self.enhanced_data is None:
            return {'error': 'No enhanced data available'}

        try:
            df = self.enhanced_data

            # Safe column access for statistics
            has_any_sales = df.get('has_any_sales', pd.Series([False] * len(df), dtype=bool))
            has_lsi_sales = df.get('has_lsi_sales', pd.Series([False] * len(df), dtype=bool))
            has_kdp_sales = df.get('has_kdp_sales', pd.Series([False] * len(df), dtype=bool))
            total_revenue = df.get('total_revenue', pd.Series([0.0] * len(df), dtype=float))
            total_units = df.get('total_units_sold', pd.Series([0] * len(df), dtype=int))
            performance_tier = df.get('performance_tier', pd.Series(['No Sales'] * len(df), dtype=str))

            stats = {
                'total_books': len(df),
                'books_with_sales': len(df[has_any_sales]),
                'books_with_lsi_sales': len(df[has_lsi_sales]),
                'books_with_kdp_sales': len(df[has_kdp_sales]),
                'total_revenue': total_revenue.sum(),
                'total_units_sold': total_units.sum(),
                'avg_revenue_per_book': total_revenue.mean(),
                'performance_tiers': performance_tier.value_counts().to_dict()
            }

            return stats

        except Exception as e:
            logger.error(f"Error generating summary statistics: {e}")
            return {'error': str(e)}