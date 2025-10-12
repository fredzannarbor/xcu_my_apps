#!/usr/bin/env python3
"""
Test script to verify PDF page count functionality with Zyte API
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from codexes.modules.crawlers import ZyteCrawler
except ModuleNotFoundError:
    from src.codexes.modules.crawlers import ZyteCrawler

def test_pdf_page_counts():
    """Test the PDF page count functionality."""
    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        print("❌ ZYTE_API_KEY environment variable not set!")
        return

    print("🔍 Testing PDF page count functionality...")

    # Test URLs from our previous debug session
    test_urls = [
        "https://www.cia.gov/static/OPCL_2024_803_Report.pdf",
        "https://www.cia.gov/static/cdfb671704c790a62fbbb6f0f9335042/InsideTheCollection_Digital_Mar2025.pdf",
        "https://www.cia.gov/static/OfficesOfCIA.pdf",
        "https://www.cia.gov/readingroom/docs/DOC_0000917008.pdf",  # This was failing with redirects
        "https://www.cia.gov/readingroom/docs/DOC_0000014625.pdf",  # This was failing with redirects
    ]

    crawler = ZyteCrawler(api_key)

    for i, url in enumerate(test_urls, 1):
        print(f"\n📄 Test {i}/5: {Path(url).name}")
        print(f"   URL: {url}")

        try:
            page_count = crawler.get_pdf_page_count(url)

            if page_count > 0:
                print(f"   ✅ Success: {page_count} pages")
                category = crawler.categorize_pdf(page_count)
                print(f"   📊 Category: {category}")
            else:
                print(f"   ❌ Failed: returned 0 pages")

        except Exception as e:
            print(f"   💥 Error: {e}")

        # Add a small delay to be respectful to the API
        import time
        time.sleep(2)

    print(f"\n🎯 Test completed!")

if __name__ == "__main__":
    test_pdf_page_counts()