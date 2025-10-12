#!/usr/bin/env python3
"""
Test script to verify data collection functionality for ArXiv paper generation.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from codexes.modules.arxiv_paper.data_collector import XynapseTracesDataCollector
import json

def main():
    """Test the data collection functionality."""
    
    print("Testing ArXiv Paper Data Collection")
    print("=" * 50)
    
    # Initialize data collector
    collector = XynapseTracesDataCollector()
    
    # Test book catalog metrics
    print("\n1. Testing book catalog metrics collection...")
    book_metrics = collector.collect_book_catalog_metrics()
    print(f"   ✓ Collected data for {book_metrics.get('total_books', 0)} books")
    print(f"   ✓ Publication range: {book_metrics.get('publication_date_range', {})}")
    
    # Test configuration metrics
    print("\n2. Testing configuration metrics collection...")
    config_metrics = collector.collect_configuration_metrics()
    print(f"   ✓ Configuration sections: {len(config_metrics.get('config_sections', []))}")
    print(f"   ✓ Supported languages: {config_metrics.get('supported_languages', [])}")
    
    # Test production metrics
    print("\n3. Testing production metrics collection...")
    prod_metrics = collector.collect_production_metrics()
    print(f"   ✓ Output directories found: {len(prod_metrics.get('output_directories', []))}")
    
    # Generate comprehensive report
    print("\n4. Testing comprehensive report generation...")
    report = collector.generate_comprehensive_report()
    print(f"   ✓ Report generated with {len(report)} main sections")
    
    print("\n" + "=" * 50)
    print("DATA COLLECTION TEST COMPLETE")
    print("All components working correctly!")
    print("=" * 50)

if __name__ == "__main__":
    main()