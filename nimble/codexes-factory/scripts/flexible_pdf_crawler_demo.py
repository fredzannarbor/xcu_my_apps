#!/usr/bin/env python3
"""
Flexible PDF Crawler Demo

This script demonstrates the flexible URL crawling capability of ZyteCrawler.
It can crawl any website for PDF documents with configurable parameters.

Usage:
    python flexible_pdf_crawler_demo.py <URL> [min_pages] [max_docs] [max_pages_to_crawl]

Examples:
    # Crawl CIA reading room for PDFs with 18+ pages
    python flexible_pdf_crawler_demo.py "https://www.cia.gov/readingroom/search/site/?f%5B0%5D=im_field_taxonomy_nic_product%3A15&f%5B1%5D=ds_created%3A%5B2012-01-01T00%3A00%3A00Z%20TO%202013-01-01T00%3A00%3A00Z%5D&f%5B2%5D=ds_created%3A%5B2012-10-01T00%3A00%3A00Z%20TO%202012-11-01T00%3A00%3A00Z%5D" 18 100 20

    # Crawl any government site for PDFs
    python flexible_pdf_crawler_demo.py "https://www.fbi.gov/services/records-management/foipa/foia-and-pa-resources" 10 50 10
"""

import os
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not found. Using system environment variables only.")

# Add the src directory to the path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

try:
    from codexes.modules.crawlers.zyte_crawler import ZyteCrawler
except ImportError:
    print("Error: Could not import ZyteCrawler. Make sure you're running from the correct directory.")
    sys.exit(1)


def main():
    """Main function for the flexible PDF crawler demo."""
    if len(sys.argv) < 2:
        print(__doc__)
        return

    # Parse command line arguments
    url = sys.argv[1]
    min_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 18
    max_docs = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    max_pages_to_crawl = int(sys.argv[4]) if len(sys.argv) > 4 else 10

    # Check for Zyte API key
    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        print("Error: ZYTE_API_KEY environment variable not set")
        print("Please set your Zyte API key: export ZYTE_API_KEY='your_key_here'")
        return

    print("=" * 80)
    print("FLEXIBLE PDF CRAWLER DEMO")
    print("=" * 80)
    print(f"Target URL: {url}")
    print(f"Min pages: {min_pages}")
    print(f"Max documents: {max_docs}")
    print(f"Max pages to crawl: {max_pages_to_crawl}")
    print("=" * 80)

    # Initialize crawler
    crawler = ZyteCrawler(api_key)

    try:
        # Start crawling (auto-detect two-level crawling)
        print(f"\n🚀 Starting crawl of: {url}")
        print("🔍 Auto-detecting crawling strategy...")

        # Enable debug logging
        import logging
        logging.basicConfig(level=logging.DEBUG)

        documents = crawler.crawl_url_for_pdfs(
            start_url=url,
            min_pages=min_pages,
            max_docs=max_docs,
            max_pages_to_crawl=max_pages_to_crawl,
            two_level_crawl=None,  # Auto-detect
            output_dir="downloads/flexible_crawl"
        )

        # Display results
        if documents:
            print(f"\n✅ Found {len(documents)} documents matching criteria:")
            print("-" * 80)

            # Group by page category
            categories = {}
            for doc in documents:
                category = doc['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(doc)

            for category, docs in sorted(categories.items()):
                print(f"\n📄 {category} pages ({len(docs)} documents):")
                for doc in docs[:5]:  # Show first 5 in each category
                    print(f"   • {doc['pages']:3d} pages: {doc['filename'][:60]}...")
                    print(f"     Source: {doc['source_page']}")
                if len(docs) > 5:
                    print(f"   ... and {len(docs) - 5} more documents")

            # Summary
            total_pages = sum(doc['pages'] for doc in documents)
            avg_pages = total_pages / len(documents) if documents else 0
            print(f"\n📊 SUMMARY:")
            print(f"   • Total documents: {len(documents)}")
            print(f"   • Total pages: {total_pages:,}")
            print(f"   • Average pages per document: {avg_pages:.1f}")
            print(f"   • Pages crawled: {max([doc['crawl_page'] for doc in documents])}")

            # Ask user if they want to download
            print(f"\n💾 Download options:")
            print(f"   1. Download all {len(documents)} documents")
            print(f"   2. Download only long documents (100+ pages)")
            print(f"   3. Skip download")

            choice = input("\nChoose option (1/2/3): ").strip()

            if choice == "1":
                print(f"\n⬇️  Downloading all {len(documents)} documents...")
                downloaded = crawler.download_filtered_documents(
                    documents,
                    "downloads/flexible_crawl"
                )
                print(f"✅ Downloaded {downloaded}/{len(documents)} documents")

            elif choice == "2":
                long_docs = [doc for doc in documents if doc['pages'] >= 100]
                if long_docs:
                    print(f"\n⬇️  Downloading {len(long_docs)} long documents...")
                    downloaded = crawler.download_filtered_documents(
                        long_docs,
                        "downloads/flexible_crawl/long_docs"
                    )
                    print(f"✅ Downloaded {downloaded}/{len(long_docs)} long documents")
                else:
                    print("No documents with 100+ pages found")

            else:
                print("📋 Document list saved for review. No downloads performed.")

        else:
            print("\n❌ No documents found matching criteria")
            print("Try adjusting the parameters:")
            print(f"   • Lower min_pages (currently {min_pages})")
            print(f"   • Increase max_docs (currently {max_docs})")
            print(f"   • Increase max_pages_to_crawl (currently {max_pages_to_crawl})")

    except KeyboardInterrupt:
        print("\n\n⏹️  Crawl interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during crawling: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("Demo complete. Thank you for using Flexible PDF Crawler!")


if __name__ == "__main__":
    main()