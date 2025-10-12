"""
Data Collection Framework for ArXiv Paper Generation

This module provides tools to collect quantitative metrics from the xynapse_traces imprint
for academic paper documentation.
"""

import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class XynapseTracesDataCollector:
    """Collects and analyzes data from the xynapse_traces imprint for academic documentation."""
    
    def __init__(self, base_path: str = "."):
        """
        Initialize the data collector.
        
        Args:
            base_path: Base path to the project directory
        """
        self.base_path = Path(base_path)
        self.imprint_path = self.base_path / "imprints" / "xynapse_traces"
        self.config_path = self.base_path / "configs" / "imprints" / "xynapse_traces.json"
        self.output_path = self.base_path / "output" / "arxiv_paper" / "data"
        
        # Ensure output directory exists
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def collect_book_catalog_metrics(self) -> Dict[str, Any]:
        """
        Collect quantitative metrics from the xynapse_traces book catalog.
        
        Returns:
            Dictionary containing book catalog metrics
        """
        try:
            # Load book catalog
            books_csv_path = self.imprint_path / "books.csv"
            if not books_csv_path.exists():
                logger.error(f"Book catalog not found at {books_csv_path}")
                return {}
            
            df = pd.read_csv(books_csv_path)
            
            # Basic statistics
            metrics = {
                "total_books": len(df),
                "publication_date_range": {
                    "earliest": df['publication_date'].min() if 'publication_date' in df.columns else None,
                    "latest": df['publication_date'].max() if 'publication_date' in df.columns else None
                },
                "page_count_stats": {
                    "mean": df['page_count'].mean() if 'page_count' in df.columns else None,
                    "median": df['page_count'].median() if 'page_count' in df.columns else None,
                    "min": df['page_count'].min() if 'page_count' in df.columns else None,
                    "max": df['page_count'].max() if 'page_count' in df.columns else None
                },
                "pricing_stats": {
                    "mean": df['price'].mean() if 'price' in df.columns else None,
                    "median": df['price'].median() if 'price' in df.columns else None,
                    "min": df['price'].min() if 'price' in df.columns else None,
                    "max": df['price'].max() if 'price' in df.columns else None
                },
                "unique_authors": df['author'].nunique() if 'author' in df.columns else None,
                "series_distribution": df['series_name'].value_counts().to_dict() if 'series_name' in df.columns else {},
                "collection_timestamp": datetime.now().isoformat()
            }
            
            # Save raw data for reference
            self._save_data(df.to_dict('records'), "book_catalog_raw.json")
            self._save_data(metrics, "book_catalog_metrics.json")
            
            logger.info(f"Collected metrics for {metrics['total_books']} books")
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting book catalog metrics: {e}")
            return {}
    
    def collect_configuration_metrics(self) -> Dict[str, Any]:
        """
        Collect metrics about the xynapse_traces configuration system.
        
        Returns:
            Dictionary containing configuration metrics
        """
        try:
            # Load imprint configuration
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            metrics = {
                "config_sections": list(config.keys()),
                "branding_elements": len(config.get("branding", {})),
                "supported_languages": config.get("publishing_focus", {}).get("languages", []),
                "primary_genres": config.get("publishing_focus", {}).get("primary_genres", []),
                "territorial_configs": list(config.get("territorial_configs", {}).keys()),
                "distribution_channels": {
                    "lightning_source_account": config.get("distribution_settings", {}).get("lightning_source_account"),
                    "submission_methods": [
                        config.get("distribution_settings", {}).get("cover_submission_method"),
                        config.get("distribution_settings", {}).get("text_block_submission_method")
                    ]
                },
                "workflow_automation": {
                    "auto_generate_missing_fields": config.get("workflow_settings", {}).get("auto_generate_missing_fields"),
                    "llm_completion_enabled": config.get("workflow_settings", {}).get("llm_completion_enabled"),
                    "computed_fields_enabled": config.get("workflow_settings", {}).get("computed_fields_enabled")
                },
                "collection_timestamp": datetime.now().isoformat()
            }
            
            self._save_data(metrics, "configuration_metrics.json")
            
            logger.info("Collected configuration metrics")
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting configuration metrics: {e}")
            return {}
    
    def collect_production_metrics(self) -> Dict[str, Any]:
        """
        Collect metrics about the production pipeline and output files.
        
        Returns:
            Dictionary containing production metrics
        """
        try:
            output_build_path = self.base_path / "output" / "xynapse_traces_build"
            
            metrics = {
                "output_directories": [],
                "file_counts": {},
                "file_types": {},
                "collection_timestamp": datetime.now().isoformat()
            }
            
            if output_build_path.exists():
                # Analyze output directory structure
                for item in output_build_path.rglob("*"):
                    if item.is_file():
                        relative_path = item.relative_to(output_build_path)
                        dir_name = str(relative_path.parent)
                        file_ext = item.suffix.lower()
                        
                        if dir_name not in metrics["file_counts"]:
                            metrics["file_counts"][dir_name] = 0
                            metrics["output_directories"].append(dir_name)
                        
                        metrics["file_counts"][dir_name] += 1
                        
                        if file_ext not in metrics["file_types"]:
                            metrics["file_types"][file_ext] = 0
                        metrics["file_types"][file_ext] += 1
            
            self._save_data(metrics, "production_metrics.json")
            
            logger.info("Collected production metrics")
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting production metrics: {e}")
            return {}
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive data report combining all metrics.
        
        Returns:
            Dictionary containing all collected metrics
        """
        logger.info("Generating comprehensive data report")
        
        report = {
            "report_metadata": {
                "generation_timestamp": datetime.now().isoformat(),
                "imprint_name": "xynapse_traces",
                "report_version": "1.0"
            },
            "book_catalog": self.collect_book_catalog_metrics(),
            "configuration": self.collect_configuration_metrics(),
            "production": self.collect_production_metrics()
        }
        
        # Save comprehensive report
        self._save_data(report, "comprehensive_report.json")
        
        logger.info("Comprehensive report generated successfully")
        return report
    
    def _save_data(self, data: Any, filename: str) -> None:
        """
        Save data to JSON file in the output directory.
        
        Args:
            data: Data to save
            filename: Name of the output file
        """
        output_file = self.output_path / filename
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logger.debug(f"Saved data to {output_file}")


def main():
    """Main function for standalone execution."""
    logging.basicConfig(level=logging.INFO)
    
    collector = XynapseTracesDataCollector()
    report = collector.generate_comprehensive_report()
    
    print(f"Data collection complete. Report saved with {report['book_catalog']['total_books']} books analyzed.")


if __name__ == "__main__":
    main()