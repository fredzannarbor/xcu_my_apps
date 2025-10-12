#!/usr/bin/env python3
"""
Compare the two extraction methods to see why they give different results.
"""

import os
import sys
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add the src directory to the path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

try:
    from codexes.modules.crawlers.zyte_crawler import ZyteCrawler
except ImportError:
    print("Error: Could not import ZyteCrawler.")
    sys.exit(1)

def main():
    """Compare extraction methods."""

    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        print("Error: ZYTE_API_KEY environment variable not set")
        return

    # Test URL
    test_url = "https://www.cia.gov/readingroom/search/site/?f%5B0%5D=im_field_taxonomy_nic_product%3A15&f%5B1%5D=ds_created"

    print(f"Comparing extraction methods for: {test_url}")

    # Initialize crawler
    crawler = ZyteCrawler(api_key)

    # Enable debug logging
    import logging
    logging.basicConfig(level=logging.DEBUG)

    print("\n=== METHOD 1: Direct _get_document_page_urls ===")
    pdf_urls_method1 = crawler._get_document_page_urls(test_url)
    print(f"Method 1 found: {len(pdf_urls_method1)} PDF URLs")

    print("\n=== METHOD 2: Manual extraction (like our test) ===")
    import requests
    import base64
    import re
    from urllib.parse import urlparse

    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{api_key}:'.encode()).decode()}",
        "Content-Type": "application/json"
    }
    data = {
        "url": test_url,
        "browserHtml": True
    }

    response = requests.post('https://api.zyte.com/v1/extract', headers=headers, json=data, timeout=30)
    if response.status_code == 200:
        html = response.json().get('browserHtml', '')
        parsed_base = urlparse(test_url)

        print(f"HTML length: {len(html)}")
        print(f"Is CIA? {'cia.gov' in parsed_base.netloc.lower()}")

        # Test document ID extraction manually (same as crawler)
        doc_id_patterns = [
            r'\/readingroom\/document\/(\d{10})',
            r'\/document\/(\d{10})',
            r'href=["\'][^"\']*\/document\/(\d{10})[^"\']*["\']',
            r'(\d{10})',
        ]

        document_ids = set()
        for pattern in doc_id_patterns:
            matches = re.findall(pattern, html)
            if matches:
                document_ids.update(matches)
                print(f"Pattern '{pattern}' found {len(matches)} matches")

        print(f"Total unique document IDs found: {len(document_ids)}")
        print(f"Sample IDs: {list(document_ids)[:5]}")

        cia_doc_ids = [doc_id for doc_id in document_ids if doc_id.startswith('0000') and len(doc_id) == 10]
        print(f"CIA format IDs: {len(cia_doc_ids)}")

        method2_pdf_urls = []
        for doc_id in cia_doc_ids:
            pdf_url = f"https://www.cia.gov/readingroom/docs/DOC_{doc_id}.pdf"
            method2_pdf_urls.append(pdf_url)

        print(f"Method 2 found: {len(method2_pdf_urls)} PDF URLs")

        # Compare results
        print(f"\n=== COMPARISON ===")
        print(f"Method 1 (crawler): {len(pdf_urls_method1)} PDFs")
        print(f"Method 2 (manual):  {len(method2_pdf_urls)} PDFs")

        if len(pdf_urls_method1) != len(method2_pdf_urls):
            print("❌ Methods give different results!")
            print(f"Method 1 URLs: {pdf_urls_method1[:3]}")
            print(f"Method 2 URLs: {method2_pdf_urls[:3]}")
        else:
            print("✅ Methods give same results")

    else:
        print(f"Failed to fetch HTML: {response.status_code}")

if __name__ == "__main__":
    main()