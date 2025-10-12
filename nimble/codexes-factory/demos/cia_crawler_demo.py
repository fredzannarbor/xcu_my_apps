#!/usr/bin/env python3
"""
CIA Reading Room PDF Crawler Demo

This script demonstrates how to use the ZyteCrawler to:
1. Search the CIA Reading Room for documents from 2025
2. Filter for documents with more than 18 pages
3. Download qualifying documents

Requirements:
- ZYTE_API_KEY environment variable must be set
- Dependencies: requests, PyMuPDF, beautifulsoup4
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from codexes.modules.crawlers import ZyteCrawler
    from codexes.core.logging_config import get_logging_manager
except ModuleNotFoundError:
    from src.codexes.modules.crawlers import ZyteCrawler
    from src.codexes.core.logging_config import get_logging_manager

import logging


def setup_logging():
    """Setup logging for the demo."""
    try:
        logging_manager = get_logging_manager()
        logger = logging_manager.get_logger(__name__)
        return logger
    except Exception:
        logging.basicConfig(level=logging.INFO,
                          format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        return logging.getLogger(__name__)


def main():
    """Main demonstration function."""
    logger = setup_logging()

    # Check for required API key
    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        logger.error("ZYTE_API_KEY environment variable not set!")
        logger.info("Please set your Zyte API key: export ZYTE_API_KEY='your_key_here'")
        return 1

    logger.info("🚀 Starting CIA Reading Room PDF Crawler Demo")

    try:
        # Initialize crawler
        crawler = ZyteCrawler(api_key)

        # Search for 2025 documents with >18 pages
        logger.info("🔍 Searching CIA Reading Room for 2025 documents with >18 pages...")
        documents = crawler.crawl_cia_reading_room(year=2025, min_pages=18)

        if not documents:
            logger.warning("❌ No documents found matching criteria")
            return 0

        logger.info(f"✅ Found {len(documents)} qualifying documents:")

        # Display results
        print("\n" + "="*80)
        print("QUALIFYING DOCUMENTS FOUND:")
        print("="*80)

        for i, doc in enumerate(documents, 1):
            print(f"{i:2d}. {doc['pages']:3d} pages | {doc['category']:>7} | {doc['filename']}")
            print(f"     URL: {doc['url']}")
            print()

        # Ask user if they want to download
        print(f"\nFound {len(documents)} documents. Download them? (y/N): ", end="")
        response = input().strip().lower()

        if response in ('y', 'yes'):
            output_dir = "downloads/cia_reading_room_2025"
            logger.info(f"📥 Downloading documents to {output_dir}...")

            downloaded = crawler.download_filtered_documents(documents, output_dir)

            if downloaded > 0:
                logger.info(f"✅ Successfully downloaded {downloaded}/{len(documents)} documents")
                print(f"\nDocuments saved to: {Path(output_dir).absolute()}")
            else:
                logger.error("❌ No documents were successfully downloaded")
        else:
            logger.info("ℹ️  Download skipped by user")

        return 0

    except KeyboardInterrupt:
        logger.info("⏹️  Demo interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Error during demo: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)