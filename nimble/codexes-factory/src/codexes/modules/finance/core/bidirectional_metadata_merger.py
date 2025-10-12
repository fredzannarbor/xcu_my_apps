"""
Bidirectional Metadata Merger

Provides comprehensive integration between Books In Print Metadata and consolidated sales data:
1. Merges KDP/LSI consolidated sales data INTO Books In Print Metadata
2. Merges publication metadata (pub date, description, BISAC) INTO KDP/LSI consolidated data

This creates a unified view where:
- Books In Print shows complete sales performance across all channels
- Sales databases are enriched with publication metadata for better analysis
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
    from codexes.modules.finance.core.user_data_manager import UserDataManager
    from codexes.modules.finance.core.fro_coordinator import FROCoordinator
except ModuleNotFoundError:
    from src.codexes.core.dataframe_utils import clean_dataframe_for_pyarrow, convert_to_arrow_compatible_types
    from src.codexes.modules.finance.core.user_data_manager import UserDataManager
    from src.codexes.modules.finance.core.fro_coordinator import FROCoordinator

logger = logging.getLogger(__name__)


class BidirectionalMetadataMerger:
    """
    Handles bidirectional merging between Books In Print metadata and sales data.

    Direction 1: Sales data → Books In Print (add sales metrics to catalog)
    Direction 2: Metadata → Sales data (enrich sales with publication info)
    """

    def __init__(self, user_data_manager: UserDataManager, fro_coordinator: FROCoordinator):
        self.udm = user_data_manager
        self.fro_coord = fro_coordinator

        # Cache for loaded data
        self._base_metadata = None
        self._kdp_consolidated = None
        self._lsi_consolidated = None

        # Merge statistics
        self.merge_stats = {
            'books_in_print_with_sales': 0,
            'kdp_consolidated_with_metadata': 0,
            'lsi_consolidated_with_metadata': 0,
            'total_merged_records': 0
        }

    def create_comprehensive_merger(self) -> Dict[str, Any]:
        """
        Create comprehensive bidirectional merge of metadata and sales data.

        Returns:
            Dictionary with merged datasets and statistics
        """
        try:
            logger.info("Starting comprehensive bidirectional metadata merger")

            # Step 1: Load all data sources
            self._load_all_data_sources()

            # Step 2: Create Books In Print enriched with sales data
            books_with_sales = self._merge_sales_into_metadata()

            # Step 3: Create KDP consolidated enriched with metadata
            kdp_with_metadata = self._merge_metadata_into_kdp()

            # Step 4: Create LSI consolidated enriched with metadata
            lsi_with_metadata = self._merge_metadata_into_lsi()

            # Step 5: Generate comprehensive statistics
            stats = self._generate_comprehensive_stats(
                books_with_sales, kdp_with_metadata, lsi_with_metadata
            )

            result = {
                'books_in_print_enriched': books_with_sales,
                'kdp_consolidated_enriched': kdp_with_metadata,
                'lsi_consolidated_enriched': lsi_with_metadata,
                'merge_statistics': stats,
                'processing_status': 'success',
                'last_updated': datetime.now().isoformat(),
                'success': True
            }

            logger.info(f"Bidirectional merger completed successfully: {stats['total_merged_records']} total records")
            return result

        except Exception as e:
            logger.error(f"Error in bidirectional metadata merger: {e}")
            return self._create_error_response(f"Merger error: {str(e)}")

    def _load_all_data_sources(self):
        """Load all required data sources."""
        logger.info("Loading all data sources for bidirectional merger")

        # Load Books In Print metadata
        self._base_metadata = self._load_books_in_print_metadata()

        # Load consolidated sales databases (from processed FRO data)
        self._kdp_consolidated = self._load_kdp_consolidated_data()
        self._lsi_consolidated = self._load_lsi_consolidated_data()

        # Load royaltied status and product line data
        self._royaltied_data = self._load_royaltied_metadata()

        logger.info(f"Loaded data sources: "
                   f"Books In Print: {len(self._base_metadata) if self._base_metadata is not None else 0}, "
                   f"KDP Consolidated: {len(self._kdp_consolidated) if self._kdp_consolidated is not None else 0}, "
                   f"LSI Consolidated: {len(self._lsi_consolidated) if self._lsi_consolidated is not None else 0}, "
                   f"Royaltied Data: {len(self._royaltied_data) if self._royaltied_data is not None else 0}")

        # Debug: Show what data we actually loaded
        if self._kdp_consolidated is not None and not self._kdp_consolidated.empty:
            logger.info(f"KDP columns: {list(self._kdp_consolidated.columns)}")
            logger.info(f"KDP sample ISBNs: {self._kdp_consolidated['ISBN'].head(5).tolist() if 'ISBN' in self._kdp_consolidated.columns else 'No ISBN column'}")

        if self._lsi_consolidated is not None and not self._lsi_consolidated.empty:
            logger.info(f"LSI columns: {list(self._lsi_consolidated.columns)}")
            logger.info(f"LSI sample ISBNs: {self._lsi_consolidated['ISBN'].head(5).tolist() if 'ISBN' in self._lsi_consolidated.columns else 'No ISBN column'}")

        if self._base_metadata is not None and not self._base_metadata.empty:
            logger.info(f"Books In Print columns: {list(self._base_metadata.columns)}")
            logger.info(f"Books In Print sample ISBNs: {self._base_metadata['ISBN'].head(5).tolist() if 'ISBN' in self._base_metadata.columns else 'No ISBN column'}")

    def _load_books_in_print_metadata(self) -> Optional[pd.DataFrame]:
        """Load Books In Print metadata as the base catalog."""
        try:
            lsi_metadata_files = self.udm.list_files('lsi_metadata')

            if not lsi_metadata_files:
                logger.warning("No Books In Print metadata files found")
                return None

            # Get the most recent file
            latest_file = max(lsi_metadata_files, key=lambda x: x['upload_time'])
            file_path = self.udm.base_dir / latest_file['file_path']

            logger.info(f"Loading Books In Print metadata from: {file_path}")

            # Read CSV with encoding detection
            df = self.udm._read_csv_with_encoding(file_path)

            # Standardize key columns
            if 'ISBN' in df.columns:
                df['ISBN'] = df['ISBN'].astype(str).str.strip()

            # Standardize author column
            if 'Contributor One Name' in df.columns and 'Author' not in df.columns:
                df['Author'] = df['Contributor One Name']

            logger.info(f"Loaded {len(df)} books from Books In Print metadata")
            return df

        except Exception as e:
            logger.error(f"Error loading Books In Print metadata: {e}")
            return None

    def _load_kdp_consolidated_data(self) -> Optional[pd.DataFrame]:
        """Load consolidated KDP sales data by processing raw files."""
        try:
            kdp_data_files = self.udm.list_files('kdp_data')

            if not kdp_data_files:
                logger.warning("No KDP data files found")
                return None

            # Get the most recent LTD file
            ltd_files = [f for f in kdp_data_files if f.get('destination') == 'LTD']
            if not ltd_files:
                logger.warning("No KDP LTD files found")
                return None

            latest_file = max(ltd_files, key=lambda x: x['upload_time'])
            file_path = self.udm.base_dir / latest_file['file_path']

            logger.info(f"Loading KDP consolidated data from: {file_path}")

            # Use the existing FRO coordinator's KDP processing logic
            if hasattr(self.fro_coord, 'kdp_lifetime') and self.fro_coord.kdp_lifetime is not None:
                # Use existing processed KDP data if available
                df = self.fro_coord.kdp_lifetime.dataframe.copy()
                logger.info(f"Using existing KDP lifetime data: {len(df)} records")
            else:
                # Fallback: Process KDP data directly
                logger.info("Processing KDP data directly from file")
                df = self._process_kdp_file_directly(str(file_path))

            # Ensure ISBN column exists and is properly formatted
            if 'ISBN' not in df.columns and 'ASIN' in df.columns:
                df['ISBN'] = df['ASIN'].astype(str).str.strip()
            elif 'ISBN' in df.columns:
                df['ISBN'] = df['ISBN'].astype(str).str.strip()

            # Consolidate by ISBN (sum sales data for books that might have multiple entries)
            if not df.empty:
                # Group by ISBN and aggregate sales data
                numeric_cols = ['Units Sold', 'Units Refunded', 'Net Units Sold', 'Royalty', 'USDeq_Royalty']
                agg_dict = {}

                for col in numeric_cols:
                    if col in df.columns:
                        agg_dict[col] = 'sum'

                # Keep first value for non-numeric columns
                for col in df.columns:
                    if col not in numeric_cols and col != 'ISBN':
                        agg_dict[col] = 'first'

                if agg_dict:
                    df = df.groupby('ISBN').agg(agg_dict).reset_index()
                    logger.info(f"Consolidated KDP data by ISBN: {len(df)} unique books")

            logger.info(f"Loaded {len(df)} records from KDP consolidated data")
            return df

        except Exception as e:
            logger.error(f"Error loading KDP consolidated data: {e}")
            return None

    def _process_kdp_file_directly(self, file_path: str) -> pd.DataFrame:
        """Directly process KDP file without full FRO infrastructure."""
        try:
            # Simple direct processing of KDP Excel file
            df = pd.read_excel(file_path, sheet_name='Combined Sales')

            logger.info(f"KDP file columns: {list(df.columns)}")

            # Basic processing without currency conversion for now
            # Handle different possible ISBN/ASIN column names
            if 'ISBN' not in df.columns:
                if 'ASIN' in df.columns:
                    df['ISBN'] = df['ASIN'].astype(str).str.strip()
                elif 'ASIN/ISBN' in df.columns:
                    # Handle the combined ASIN/ISBN column from KDP Orders files
                    df['ISBN'] = df['ASIN/ISBN'].astype(str).str.strip()
                    logger.info(f"Using ASIN/ISBN column for identification: {len(df)} records")
                else:
                    # If no identifier column exists, create empty ISBN column
                    logger.warning("Neither ISBN, ASIN, nor ASIN/ISBN found in KDP data, creating empty ISBN column")
                    df['ISBN'] = ''
            else:
                df['ISBN'] = df['ISBN'].astype(str).str.strip()

            # Calculate Net Units Sold if not present
            if 'Net Units Sold' not in df.columns and 'Units Sold' in df.columns and 'Units Refunded' in df.columns:
                df['Net Units Sold'] = df['Units Sold'] - df['Units Refunded']

            logger.info(f"Direct KDP processing: loaded {len(df)} records")
            return df

        except Exception as e:
            logger.error(f"Error in direct KDP file processing: {e}")
            return pd.DataFrame()

    def _load_lsi_consolidated_data(self) -> Optional[pd.DataFrame]:
        """Load consolidated LSI sales data by processing raw files."""
        try:
            lsi_data_files = self.udm.list_files('lsi_data')

            if not lsi_data_files:
                logger.warning("No LSI data files found")
                return None

            # Get the most recent file
            latest_file = max(lsi_data_files, key=lambda x: x['upload_time'])
            file_path = self.udm.base_dir / latest_file['file_path']

            logger.info(f"Loading LSI consolidated data from: {file_path}")

            # Read Excel file - LSI data is typically in Excel format
            df = pd.read_excel(file_path, engine='openpyxl')

            # Basic cleanup
            if 'ISBN' in df.columns:
                df['ISBN'] = df['ISBN'].astype(str).str.strip()

            # Consolidate by ISBN (sum sales data for books that might have multiple entries)
            if not df.empty:
                # Group by ISBN and aggregate sales data
                numeric_cols = ['Gross Qty', 'Returned Qty', 'Net Qty', 'Net Compensation']
                agg_dict = {}

                for col in numeric_cols:
                    if col in df.columns:
                        agg_dict[col] = 'sum'

                # Keep first value for non-numeric columns
                for col in df.columns:
                    if col not in numeric_cols and col != 'ISBN':
                        agg_dict[col] = 'first'

                if agg_dict:
                    df = df.groupby('ISBN').agg(agg_dict).reset_index()
                    logger.info(f"Consolidated LSI data by ISBN: {len(df)} unique books")

            logger.info(f"Loaded {len(df)} records from LSI consolidated data")
            return df

        except Exception as e:
            logger.error(f"Error loading LSI consolidated data: {e}")
            return None

    def _load_royaltied_metadata(self) -> Optional[pd.DataFrame]:
        """Load royaltied status and product line metadata from add2fme.xlsx file."""
        try:
            # First try the uploaded file location in author_data
            author_data_files = self.udm.list_files('author_data')
            add2fme_file = None

            for file_info in author_data_files:
                if file_info['original_name'] == 'add2fme.xlsx':
                    add2fme_file = file_info
                    break

            if add2fme_file:
                add2fme_path = self.udm.base_dir / add2fme_file['file_path']
                logger.info(f"Loading royaltied metadata from uploaded file: {add2fme_path}")
            else:
                # Fallback to direct path in base directory
                add2fme_path = self.udm.base_dir / "add2fme.xlsx"
                if not add2fme_path.exists():
                    logger.warning("add2fme.xlsx file not found - royaltied status will not be available")
                    return None
                logger.info(f"Loading royaltied metadata from base directory: {add2fme_path}")

            df = pd.read_excel(add2fme_path)

            # Ensure ISBN is string for matching
            if 'ISBN' in df.columns:
                df['ISBN'] = df['ISBN'].astype(str).str.strip()

            # Clean product_line and royaltied columns
            if 'royaltied' in df.columns:
                df['royaltied'] = df['royaltied'].fillna(False)

            if 'product_line' in df.columns:
                df['product_line'] = df['product_line'].fillna('Not Specified')

            logger.info(f"Loaded {len(df)} royaltied records")
            logger.info(f"Royaltied breakdown: {df['royaltied'].value_counts().to_dict() if 'royaltied' in df.columns else 'No royaltied column'}")
            logger.info(f"Product lines: {df['product_line'].value_counts().head().to_dict() if 'product_line' in df.columns else 'No product_line column'}")

            return df

        except Exception as e:
            logger.error(f"Error loading royaltied metadata: {e}")
            return None

    def _merge_sales_into_metadata(self) -> pd.DataFrame:
        """
        Merge KDP and LSI consolidated sales data INTO Books In Print metadata.
        This creates an enriched catalog with complete sales performance.
        """
        logger.info("Merging sales data into Books In Print metadata")

        if self._base_metadata is None:
            logger.error("No base metadata available for sales merge")
            return pd.DataFrame()

        # Start with Books In Print metadata
        enriched_catalog = self._base_metadata.copy()

        # Merge LSI consolidated sales data
        if self._lsi_consolidated is not None:
            # Prepare LSI data with prefixed column names
            lsi_sales_cols = self._get_relevant_sales_columns(self._lsi_consolidated, 'lsi_')
            lsi_for_merge = self._lsi_consolidated[['ISBN'] + lsi_sales_cols].copy()
            lsi_for_merge = lsi_for_merge.add_suffix('_sales').rename(columns={'ISBN_sales': 'ISBN'})

            enriched_catalog = enriched_catalog.merge(
                lsi_for_merge,
                on='ISBN',
                how='left'
            )
            logger.info(f"Merged LSI sales data: {len(lsi_for_merge)} records")

        # Merge KDP consolidated sales data
        if self._kdp_consolidated is not None:
            # Prepare KDP data with prefixed column names
            kdp_sales_cols = self._get_relevant_sales_columns(self._kdp_consolidated, 'kdp_')
            kdp_for_merge = self._kdp_consolidated[['ISBN'] + kdp_sales_cols].copy()
            kdp_for_merge = kdp_for_merge.add_suffix('_sales').rename(columns={'ISBN_sales': 'ISBN'})

            enriched_catalog = enriched_catalog.merge(
                kdp_for_merge,
                on='ISBN',
                how='left'
            )
            logger.info(f"Merged KDP sales data: {len(kdp_for_merge)} records")

        # Merge royaltied status and product line metadata
        if self._royaltied_data is not None:
            royaltied_for_merge = self._royaltied_data[['ISBN', 'royaltied', 'product_line']].copy()

            enriched_catalog = enriched_catalog.merge(
                royaltied_for_merge,
                on='ISBN',
                how='left'
            )
            logger.info(f"Merged royaltied metadata: {len(royaltied_for_merge)} records")

            # Fill NaN values with defaults for books not in royaltied file
            enriched_catalog['royaltied'] = enriched_catalog['royaltied'].fillna(False)
            enriched_catalog['product_line'] = enriched_catalog['product_line'].fillna('Not Specified')

        # Add calculated fields for total sales performance
        enriched_catalog = self._add_total_sales_calculations(enriched_catalog)

        logger.info(f"Created enriched Books In Print catalog with {len(enriched_catalog)} books")
        return enriched_catalog

    def _merge_metadata_into_kdp(self) -> pd.DataFrame:
        """
        Merge publication metadata INTO KDP consolidated sales data.
        This enriches sales records with publication information.
        """
        logger.info("Merging metadata into KDP consolidated data")

        if self._kdp_consolidated is None:
            logger.warning("No KDP consolidated data available for metadata merge")
            return pd.DataFrame()

        # Start with KDP consolidated data
        enriched_kdp = self._kdp_consolidated.copy()

        if self._base_metadata is not None:
            # Prepare metadata columns for merging
            metadata_cols = self._get_relevant_metadata_columns()
            metadata_for_merge = self._base_metadata[['ISBN'] + metadata_cols].copy()

            enriched_kdp = enriched_kdp.merge(
                metadata_for_merge,
                on='ISBN',
                how='left'
            )

            logger.info(f"Enriched KDP data with metadata: {len(enriched_kdp)} records")

        return enriched_kdp

    def _merge_metadata_into_lsi(self) -> pd.DataFrame:
        """
        Merge publication metadata INTO LSI consolidated sales data.
        This enriches sales records with publication information.
        """
        logger.info("Merging metadata into LSI consolidated data")

        if self._lsi_consolidated is None:
            logger.warning("No LSI consolidated data available for metadata merge")
            return pd.DataFrame()

        # Start with LSI consolidated data
        enriched_lsi = self._lsi_consolidated.copy()

        if self._base_metadata is not None:
            # Prepare metadata columns for merging
            metadata_cols = self._get_relevant_metadata_columns()
            metadata_for_merge = self._base_metadata[['ISBN'] + metadata_cols].copy()

            enriched_lsi = enriched_lsi.merge(
                metadata_for_merge,
                on='ISBN',
                how='left'
            )

            logger.info(f"Enriched LSI data with metadata: {len(enriched_lsi)} records")

        return enriched_lsi

    def _get_relevant_sales_columns(self, df: pd.DataFrame, prefix: str = '') -> List[str]:
        """Get relevant sales columns from a consolidated database."""
        sales_columns = []

        # Common sales metrics to include based on data source
        if prefix.startswith('kdp'):
            # KDP-specific columns
            potential_cols = [
                'Units Sold', 'Units Refunded', 'Net Units Sold',
                'Royalty', 'USDeq_Royalty', 'List Price', 'Currency',
                'Royalty Date', 'Sales Type', 'Format'
            ]
        else:
            # LSI-specific columns
            potential_cols = [
                'Gross Qty', 'Returned Qty', 'Net Qty', 'Net Compensation',
                'Royalty Rate', 'Sales Market', 'Format'
            ]

        for col in potential_cols:
            if col in df.columns:
                sales_columns.append(col)

        # Add any other numeric columns that might be sales-related
        for col in df.columns:
            if col not in sales_columns and col != 'ISBN':
                if df[col].dtype in ['int64', 'float64'] and any(keyword in col.lower() for keyword in ['sales', 'revenue', 'qty', 'units', 'royalty']):
                    sales_columns.append(col)

        return sales_columns

    def _get_relevant_metadata_columns(self) -> List[str]:
        """Get relevant metadata columns to merge into sales data."""
        if self._base_metadata is None:
            return []

        metadata_columns = []

        # Publication metadata to include in sales data
        potential_cols = [
            'Title', 'Author', 'Contributor One Name',
            'Pub Date', 'Publication Date', 'Published Date',
            'Description', 'Long Description', 'Short Description',
            'BISAC Category', 'BISAC Category Code', 'Subject',
            'Format', 'Binding', 'Page Count', 'Pages',
            'Publisher', 'Imprint', 'Series',
            'Price', 'List Price', 'MSRP'
        ]

        for col in potential_cols:
            if col in self._base_metadata.columns:
                metadata_columns.append(col)

        return metadata_columns

    def _add_total_sales_calculations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add calculated fields for total sales performance across channels."""
        try:
            logger.info("Adding total sales calculations and publishing metrics")

            # Initialize totals
            df['total_units_all_channels'] = 0
            df['total_revenue_all_channels'] = 0.0
            df['total_compensation_all_channels'] = 0.0

            # Sum LSI sales - look for merged columns ending with _sales that contain LSI revenue data
            lsi_units_cols = []
            lsi_revenue_cols = []

            # LSI columns after merge have _sales suffix and contain LSI sales terms
            for col in df.columns:
                if col.endswith('_sales'):
                    if any(term in col.lower() for term in ['net qty', 'gross qty', 'units']):
                        lsi_units_cols.append(col)
                    if any(term in col.lower() for term in ['net compensation', 'revenue', 'royalty']):
                        lsi_revenue_cols.append(col)

            logger.info(f"Found LSI units columns: {lsi_units_cols}")
            logger.info(f"Found LSI revenue columns: {lsi_revenue_cols}")

            for col in lsi_units_cols:
                df['total_units_all_channels'] += pd.to_numeric(df[col], errors='coerce').fillna(0)

            for col in lsi_revenue_cols:
                df['total_revenue_all_channels'] += pd.to_numeric(df[col], errors='coerce').fillna(0)
                df['total_compensation_all_channels'] += pd.to_numeric(df[col], errors='coerce').fillna(0)

            # Sum KDP sales - look for merged columns ending with _sales that contain KDP revenue data
            kdp_units_cols = []
            kdp_revenue_cols = []

            for col in df.columns:
                if col.endswith('_sales'):
                    if any(term in col.lower() for term in ['units sold', 'net units', 'units']):
                        kdp_units_cols.append(col)
                    if any(term in col.lower() for term in ['royalty', 'revenue', 'usdeq_royalty']):
                        kdp_revenue_cols.append(col)

            logger.info(f"Found KDP units columns: {kdp_units_cols}")
            logger.info(f"Found KDP revenue columns: {kdp_revenue_cols}")

            for col in kdp_units_cols:
                df['total_units_all_channels'] += pd.to_numeric(df[col], errors='coerce').fillna(0)

            for col in kdp_revenue_cols:
                df['total_revenue_all_channels'] += pd.to_numeric(df[col], errors='coerce').fillna(0)
                df['total_compensation_all_channels'] += pd.to_numeric(df[col], errors='coerce').fillna(0)

            # Add publishing time metrics
            today = pd.Timestamp.now().normalize()

            # Find publication date column (try common variations)
            pub_date_cols = ['Pub Date', 'Publication Date', 'Published Date', 'Release Date', 'pub_date']
            pub_date_col = None

            for col in pub_date_cols:
                if col in df.columns:
                    pub_date_col = col
                    break

            if pub_date_col:
                logger.info(f"Calculating publishing metrics using {pub_date_col}")

                # Convert publication date to datetime, handling various formats
                df[pub_date_col] = pd.to_datetime(df[pub_date_col], errors='coerce')

                # Calculate days in print (subtract pub date from today)
                df['days_in_print'] = (today - df[pub_date_col]).dt.days

                # Calculate compensated days in print (days in print - 91)
                df['compensated_days_in_print'] = df['days_in_print'] - 91

                # Calculate months in print (days in print / 30)
                df['months_in_print'] = df['days_in_print'] / 30.0

                # Set negative values to 0 for compensated days (books published < 91 days ago)
                df['compensated_days_in_print'] = df['compensated_days_in_print'].clip(lower=0)

                logger.info("Publishing metrics calculated: days_in_print, compensated_days_in_print, months_in_print")

                # Add publishing age categories using industry standards
                df['publishing_age_category'] = 'Not Published'
                df.loc[df['days_in_print'] >= 0, 'publishing_age_category'] = 'New (0-90 days)'
                df.loc[df['days_in_print'] > 90, 'publishing_age_category'] = 'Frontlist (91 days - 18 months)'
                df.loc[df['days_in_print'] > 548, 'publishing_age_category'] = 'Backlist (18 months - 5 years)'  # 548 days = ~18 months
                df.loc[df['days_in_print'] > 1825, 'publishing_age_category'] = 'Deep backlist (>5 years)'  # 1825 days = ~5 years

            else:
                logger.warning("No publication date column found - publishing metrics not calculated")
                df['days_in_print'] = np.nan
                df['compensated_days_in_print'] = np.nan
                df['months_in_print'] = np.nan
                df['publishing_age_category'] = 'Unknown'

            # Add revenue per time period calculations
            df['revenue_per_month_in_print'] = df['total_revenue_all_channels'] / df['months_in_print'].replace(0, np.nan)

            # Calculate compensated months in print for revenue calculation
            df['compensated_months_in_print'] = df['compensated_days_in_print'] / 30.0
            df['revenue_per_compensated_month_in_print'] = df['total_revenue_all_channels'] / df['compensated_months_in_print'].replace(0, np.nan)

            # Add performance indicators
            df['has_sales_data'] = (df['total_units_all_channels'] > 0) | (df['total_revenue_all_channels'] > 0)
            df['revenue_per_unit_all_channels'] = df['total_revenue_all_channels'] / df['total_units_all_channels'].replace(0, np.nan)

            # Performance categories
            df['sales_performance_tier'] = 'No Sales'
            df.loc[df['total_revenue_all_channels'] > 0, 'sales_performance_tier'] = 'Low'
            df.loc[df['total_revenue_all_channels'] > 1000, 'sales_performance_tier'] = 'Medium'
            df.loc[df['total_revenue_all_channels'] > 5000, 'sales_performance_tier'] = 'High'
            df.loc[df['total_revenue_all_channels'] > 10000, 'sales_performance_tier'] = 'Top'

            logger.info("Total sales calculations and publishing metrics completed: revenue per month, revenue per compensated month")
            return df

        except Exception as e:
            logger.error(f"Error adding total sales calculations: {e}")
            return df

    def _generate_comprehensive_stats(self, books_with_sales: pd.DataFrame,
                                    kdp_with_metadata: pd.DataFrame,
                                    lsi_with_metadata: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive statistics for the bidirectional merge."""
        stats = {
            # Books In Print enriched with sales
            'books_in_print_total': len(books_with_sales) if not books_with_sales.empty else 0,
            'books_with_sales_data': len(books_with_sales[books_with_sales.get('has_sales_data', False)]) if not books_with_sales.empty else 0,
            'books_with_lsi_sales': len(books_with_sales[books_with_sales.filter(regex='lsi.*sales').sum(axis=1) > 0]) if not books_with_sales.empty else 0,
            'books_with_kdp_sales': len(books_with_sales[books_with_sales.filter(regex='kdp.*sales').sum(axis=1) > 0]) if not books_with_sales.empty else 0,

            # KDP consolidated enriched with metadata
            'kdp_consolidated_total': len(kdp_with_metadata) if not kdp_with_metadata.empty else 0,
            'kdp_with_metadata': len(kdp_with_metadata.dropna(subset=['Title'], how='all')) if not kdp_with_metadata.empty and 'Title' in kdp_with_metadata.columns else 0,

            # LSI consolidated enriched with metadata
            'lsi_consolidated_total': len(lsi_with_metadata) if not lsi_with_metadata.empty else 0,
            'lsi_with_metadata': len(lsi_with_metadata.dropna(subset=['Title'], how='all')) if not lsi_with_metadata.empty and 'Title' in lsi_with_metadata.columns else 0,

            # Overall statistics
            'total_merged_records': sum([
                len(books_with_sales) if not books_with_sales.empty else 0,
                len(kdp_with_metadata) if not kdp_with_metadata.empty else 0,
                len(lsi_with_metadata) if not lsi_with_metadata.empty else 0
            ]),

            'merge_success_rate': 0.0,
            'processing_timestamp': datetime.now().isoformat()
        }

        # Calculate merge success rate
        total_records = stats['books_in_print_total'] + stats['kdp_consolidated_total'] + stats['lsi_consolidated_total']
        if total_records > 0:
            successful_merges = stats['books_with_sales_data'] + stats['kdp_with_metadata'] + stats['lsi_with_metadata']
            stats['merge_success_rate'] = (successful_merges / total_records) * 100

        return stats

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            'books_in_print_enriched': pd.DataFrame(),
            'kdp_consolidated_enriched': pd.DataFrame(),
            'lsi_consolidated_enriched': pd.DataFrame(),
            'merge_statistics': {},
            'processing_status': f'error: {error_message}',
            'last_updated': datetime.now().isoformat(),
            'success': False
        }