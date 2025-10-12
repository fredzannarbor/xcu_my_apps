"""
Crawler module for Codexes Factory.

This module provides web crawling capabilities for extracting and processing
documents from various sources, with specialized focus on PDF document extraction
and analysis.

Key Components:
- ZyteCrawler: Web crawler using Zyte API for PDF extraction and processing
- Document filtering and categorization by page count
- Integration with codexes-factory logging and environment systems

Usage:
    from codexes.modules.crawler import ZyteCrawler

    crawler = ZyteCrawler(api_key="your-zyte-api-key")
    crawler.crawl_and_process(["https://example.com"])
"""

from .zyte_crawler import ZyteCrawler

__all__ = [
    "ZyteCrawler",
]