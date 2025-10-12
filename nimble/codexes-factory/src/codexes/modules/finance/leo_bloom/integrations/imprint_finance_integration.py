"""
Imprint-Finance Integration Module

This module provides integration between the imprints configuration system
and the Leo Bloom financial reporting system, enabling imprint-specific
financial reporting and analysis.
"""

import logging
import pandas as pd
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json

# Import following current patterns
try:
    from codexes.modules.imprints.models.imprint_configuration import ImprintConfiguration
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects
    from codexes.core.logging_config import get_logging_manager

    # Set up logging
    logging_manager = get_logging_manager()
    logging_manager.setup_logging()
    logger = logging.getLogger(__name__)
except ModuleNotFoundError:
    try:
        from src.codexes.modules.imprints.models.imprint_configuration import ImprintConfiguration
        from src.codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects
        from src.codexes.core.logging_config import get_logging_manager

        # Set up logging
        logging_manager = get_logging_manager()
        logging_manager.setup_logging()
        logger = logging.getLogger(__name__)
    except ModuleNotFoundError:
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        # Mock classes for fallback
        class ImprintConfiguration:
            pass
        class FinancialReportingObjects:
            pass


class ImprintFinanceIntegration:
    """
    Integration layer between imprint configurations and financial reporting.

    This class enables:
    - Imprint-specific financial filtering and reporting
    - Configuration-driven financial analysis
    - Cross-module data correlation
    - Automated report generation by imprint
    """

    def __init__(self, root_path: Optional[str] = None):
        """Initialize the integration with optional root path."""
        self.root_path = root_path or "/Users/fred/xcu_my_apps/nimble/codexes-factory"
        self.imprint_configs: Dict[str, ImprintConfiguration] = {}
        self.fro: Optional[FinancialReportingObjects] = None

        # Cache for financial data
        self._financial_data_cache: Dict[str, pd.DataFrame] = {}
        self._imprint_mapping_cache: Dict[str, str] = {}

        logger.info(f"Initialized ImprintFinanceIntegration with root: {self.root_path}")

    def _imprint_has_titles(self, imprint_name: str) -> bool:
        """Check if an imprint has any titles in its catalog."""
        # Check common catalog locations
        catalog_paths = [
            Path(self.root_path) / f"imprints/{imprint_name.lower().replace(' ', '_')}/books.csv",
            Path(self.root_path) / f"imprints/{imprint_name}/books.csv",
            Path(self.root_path) / f"data/catalogs/{imprint_name.lower().replace(' ', '_')}_latest.csv",
            Path(self.root_path) / f"batch_output/{imprint_name.replace(' ', '_')}_to_outline.json",
            Path(self.root_path) / f"batch_output/{imprint_name.replace(' ', '_')}_to_synopsis.json"
        ]

        for catalog_path in catalog_paths:
            if catalog_path.exists():
                try:
                    if catalog_path.suffix == '.csv':
                        df = pd.read_csv(catalog_path)
                        if not df.empty and len(df) > 0:
                            return True
                    elif catalog_path.suffix == '.json':
                        with open(catalog_path, 'r') as f:
                            data = json.load(f)
                        if data and len(data) > 0:
                            return True
                except Exception as e:
                    logger.warning(f"Error checking catalog {catalog_path}: {e}")
                    continue

        return False

    def load_imprint_configurations(self, imprint_names: Optional[List[str]] = None) -> None:
        """Load imprint configurations from JSON files."""
        configs_dir = Path(self.root_path) / "configs" / "imprints"

        if not configs_dir.exists():
            logger.warning(f"Imprints config directory not found: {configs_dir}")
            return

        config_files = list(configs_dir.glob("*.json"))

        for config_file in config_files:
            try:
                # Extract imprint name from filename
                imprint_name = config_file.stem.replace('_', ' ').title()

                # Skip if specific imprints requested and this isn't one
                if imprint_names and imprint_name not in imprint_names:
                    continue

                # Skip imprints without titles
                if not self._imprint_has_titles(imprint_name):
                    logger.debug(f"Skipping imprint without titles: {imprint_name}")
                    continue

                # Load configuration
                config = ImprintConfiguration.from_file(config_file)
                self.imprint_configs[imprint_name] = config

                logger.info(f"Loaded configuration for imprint: {imprint_name}")

            except Exception as e:
                logger.error(f"Failed to load imprint config {config_file}: {e}")

        logger.info(f"Loaded {len(self.imprint_configs)} imprint configurations")

    def initialize_financial_reporting(self, root_path: Optional[str] = None) -> None:
        """Initialize the financial reporting objects."""
        try:
            fro_root = root_path or self.root_path
            self.fro = FinancialReportingObjects(root=fro_root)
            logger.info("Initialized FinancialReportingObjects")
        except Exception as e:
            logger.error(f"Failed to initialize FinancialReportingObjects: {e}")
            raise

    def get_imprint_financial_data(self, imprint_name: str) -> Optional[pd.DataFrame]:
        """Get financial data filtered for a specific imprint."""
        if not self.fro:
            logger.error("FinancialReportingObjects not initialized")
            return None

        # Check cache first
        cache_key = f"financial_data_{imprint_name}"
        if cache_key in self._financial_data_cache:
            return self._financial_data_cache[cache_key]

        try:
            # Get full metadata enhanced dataframe
            full_df = self.fro.full_metadata_enhanced_df

            if full_df is None or full_df.empty:
                logger.warning("No financial data available")
                return None

            # Filter by imprint
            imprint_df = self._filter_by_imprint(full_df, imprint_name)

            # Cache the result
            self._financial_data_cache[cache_key] = imprint_df

            logger.info(f"Retrieved {len(imprint_df)} records for imprint: {imprint_name}")
            return imprint_df

        except Exception as e:
            logger.error(f"Error retrieving financial data for {imprint_name}: {e}")
            return None

    def _filter_by_imprint(self, df: pd.DataFrame, imprint_name: str) -> pd.DataFrame:
        """Filter dataframe by imprint name using various matching strategies."""
        if df.empty:
            return df

        # Try different column names that might contain imprint info
        imprint_columns = ['Imprint', 'imprint', 'Publisher', 'publisher', 'Brand', 'brand']

        for col in imprint_columns:
            if col in df.columns:
                # Try exact match first
                exact_match = df[df[col].str.contains(imprint_name, case=False, na=False)]
                if not exact_match.empty:
                    return exact_match

                # Try partial match
                partial_match = df[df[col].str.contains(
                    imprint_name.replace(' ', ''), case=False, na=False)]
                if not partial_match.empty:
                    return partial_match

        # If no direct match, try ISBN-based mapping
        return self._filter_by_isbn_mapping(df, imprint_name)

    def _filter_by_isbn_mapping(self, df: pd.DataFrame, imprint_name: str) -> pd.DataFrame:
        """Filter using ISBN to imprint mapping from configuration."""
        if 'ISBN' not in df.columns:
            logger.warning(f"No ISBN column found for imprint mapping")
            return pd.DataFrame()

        # Get imprint configuration
        config = self.imprint_configs.get(imprint_name)
        if not config:
            logger.warning(f"No configuration found for imprint: {imprint_name}")
            return pd.DataFrame()

        # Get Lightning Source account or other identifying info
        resolved_config = config.get_resolved_config()
        lsi_account = resolved_config.get('lightning_source_account')

        if lsi_account:
            # Filter by Lightning Source account if available in data
            lsi_columns = ['Lightning Source Account', 'LSI Account', 'Account']
            for col in lsi_columns:
                if col in df.columns:
                    account_match = df[df[col].astype(str) == str(lsi_account)]
                    if not account_match.empty:
                        return account_match

        # Return empty dataframe if no matches found
        logger.warning(f"No financial data found for imprint: {imprint_name}")
        return pd.DataFrame()

    def generate_imprint_financial_summary(self, imprint_name: str) -> Dict[str, Any]:
        """Generate comprehensive financial summary for an imprint."""
        financial_data = self.get_imprint_financial_data(imprint_name)
        config = self.imprint_configs.get(imprint_name)

        if financial_data is None or financial_data.empty:
            return {
                'imprint_name': imprint_name,
                'error': 'No financial data available',
                'records_count': 0
            }

        try:
            summary = {
                'imprint_name': imprint_name,
                'records_count': len(financial_data),
                'date_range': {
                    'earliest': None,
                    'latest': None
                },
                'sales_metrics': {},
                'financial_metrics': {},
                'configuration_info': {},
                'top_performers': {},
                'territorial_breakdown': {}
            }

            # Basic metrics
            if 'Net Qty' in financial_data.columns:
                summary['sales_metrics']['total_units_sold'] = financial_data['Net Qty'].sum()
                summary['sales_metrics']['avg_units_per_title'] = financial_data['Net Qty'].mean()

            if 'Net Compensation' in financial_data.columns:
                summary['financial_metrics']['total_revenue'] = financial_data['Net Compensation'].sum()
                summary['financial_metrics']['avg_revenue_per_title'] = financial_data['Net Compensation'].mean()

            # Configuration info
            if config:
                resolved_config = config.get_resolved_config()
                summary['configuration_info'] = {
                    'lightning_source_account': resolved_config.get('lightning_source_account'),
                    'default_wholesale_discount': resolved_config.get('us_wholesale_discount'),
                    'territorial_markets': list(resolved_config.get('territorial_configs', {}).keys()),
                    'primary_genres': resolved_config.get('publishing_focus', {}).get('primary_genres', [])
                }

            # Top performers (by revenue if available)
            if 'Net Compensation' in financial_data.columns and 'Title' in financial_data.columns:
                top_titles = financial_data.nlargest(5, 'Net Compensation')[['Title', 'Net Compensation']]
                summary['top_performers']['by_revenue'] = top_titles.to_dict('records')

            # Date range
            date_columns = ['Date', 'Sale Date', 'Transaction Date', 'Order Date']
            for col in date_columns:
                if col in financial_data.columns:
                    try:
                        dates = pd.to_datetime(financial_data[col], errors='coerce')
                        summary['date_range']['earliest'] = dates.min().isoformat() if not dates.isna().all() else None
                        summary['date_range']['latest'] = dates.max().isoformat() if not dates.isna().all() else None
                        break
                    except:
                        continue

            return summary

        except Exception as e:
            logger.error(f"Error generating summary for {imprint_name}: {e}")
            return {
                'imprint_name': imprint_name,
                'error': str(e),
                'records_count': len(financial_data) if financial_data is not None else 0
            }

    def get_all_imprints_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get financial summaries for all loaded imprints."""
        summaries = {}

        for imprint_name in self.imprint_configs.keys():
            summaries[imprint_name] = self.generate_imprint_financial_summary(imprint_name)

        return summaries

    def get_comparative_analysis(self, imprint_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate comparative analysis across imprints."""
        target_imprints = imprint_names or list(self.imprint_configs.keys())

        comparison_data = {
            'imprints_compared': target_imprints,
            'metrics': {
                'total_revenue': {},
                'total_units': {},
                'avg_revenue_per_title': {},
                'title_count': {}
            },
            'rankings': {},
            'territorial_presence': {}
        }

        for imprint_name in target_imprints:
            summary = self.generate_imprint_financial_summary(imprint_name)

            if 'error' not in summary:
                # Collect metrics
                comparison_data['metrics']['total_revenue'][imprint_name] = \
                    summary.get('financial_metrics', {}).get('total_revenue', 0)
                comparison_data['metrics']['total_units'][imprint_name] = \
                    summary.get('sales_metrics', {}).get('total_units_sold', 0)
                comparison_data['metrics']['avg_revenue_per_title'][imprint_name] = \
                    summary.get('financial_metrics', {}).get('avg_revenue_per_title', 0)
                comparison_data['metrics']['title_count'][imprint_name] = summary.get('records_count', 0)

                # Territorial presence
                territorial_markets = summary.get('configuration_info', {}).get('territorial_markets', [])
                comparison_data['territorial_presence'][imprint_name] = territorial_markets

        # Generate rankings
        for metric_name, metric_data in comparison_data['metrics'].items():
            if metric_data:
                sorted_imprints = sorted(metric_data.items(), key=lambda x: x[1], reverse=True)
                comparison_data['rankings'][metric_name] = [
                    {'imprint': imprint, 'value': value} for imprint, value in sorted_imprints
                ]

        return comparison_data

    def export_imprint_report(self, imprint_name: str, output_path: Optional[str] = None) -> Optional[Path]:
        """Export detailed financial report for an imprint."""
        financial_data = self.get_imprint_financial_data(imprint_name)
        summary = self.generate_imprint_financial_summary(imprint_name)

        if financial_data is None or financial_data.empty:
            logger.error(f"No data to export for imprint: {imprint_name}")
            return None

        # Determine output path
        if output_path is None:
            output_dir = Path(self.root_path) / "output" / "financial_reports" / "imprints"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{imprint_name.lower().replace(' ', '_')}_financial_report.xlsx"
        else:
            output_path = Path(output_path)

        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Financial data sheet
                financial_data.to_excel(writer, sheet_name='Financial Data', index=False)

                # Summary sheet
                summary_df = pd.DataFrame([summary])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)

                # Configuration sheet (if available)
                config = self.imprint_configs.get(imprint_name)
                if config:
                    config_data = config.get_resolved_config()
                    config_df = pd.DataFrame(list(config_data.items()), columns=['Setting', 'Value'])
                    config_df.to_excel(writer, sheet_name='Configuration', index=False)

            logger.info(f"Exported imprint report to: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to export report for {imprint_name}: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._financial_data_cache.clear()
        self._imprint_mapping_cache.clear()
        logger.info("Cleared integration cache")

    def get_available_imprints(self) -> List[str]:
        """Get list of available imprints with configurations."""
        return list(self.imprint_configs.keys())

    def validate_integration(self) -> Dict[str, Any]:
        """Validate the integration setup and data availability."""
        validation_results = {
            'integration_status': 'healthy',
            'issues': [],
            'imprint_configs_loaded': len(self.imprint_configs),
            'financial_data_available': self.fro is not None,
            'imprint_details': {}
        }

        # Check each imprint
        for imprint_name in self.imprint_configs.keys():
            financial_data = self.get_imprint_financial_data(imprint_name)
            has_data = financial_data is not None and not financial_data.empty

            validation_results['imprint_details'][imprint_name] = {
                'config_valid': True,
                'financial_data_available': has_data,
                'record_count': len(financial_data) if has_data else 0
            }

            if not has_data:
                validation_results['issues'].append(f"No financial data for imprint: {imprint_name}")

        if validation_results['issues']:
            validation_results['integration_status'] = 'warning'

        if not self.fro:
            validation_results['integration_status'] = 'error'
            validation_results['issues'].append("FinancialReportingObjects not initialized")

        return validation_results