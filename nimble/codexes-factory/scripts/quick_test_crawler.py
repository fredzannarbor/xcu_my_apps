#!/usr/bin/env python3
"""
Quick test of the flexible crawler to verify it finds PDFs without page counting.
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
    """Quick test of crawler functionality."""

    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        print("Error: ZYTE_API_KEY environment variable not set")
        return

    # Test the correct URL
    correct_url = "https://www.cia.gov/readingroom/search/site/?f%5B0%5D=im_field_taxonomy_nic_product%3A15&f%5B1%5D=ds_created"

    print(f"Testing crawler with: {correct_url}")

    # Initialize crawler
    crawler = ZyteCrawler(api_key)

    # Test direct PDF extraction without page counting
    print("\n=== TESTING PDF URL EXTRACTION ===")

    # Enable debug logging temporarily
    import logging
    logging.basicConfig(level=logging.INFO)

    pdf_urls = crawler._get_document_page_urls(correct_url)
    print(f"Found {len(pdf_urls)} PDF URLs:")

    for i, pdf_url in enumerate(pdf_urls[:10]):
        print(f"  {i+1}. {pdf_url}")

    if pdf_urls:
        print(f"\n✅ SUCCESS! The crawler found {len(pdf_urls)} PDF URLs")
        print("🚀 The flexible crawler is working correctly!")
        print(f"📊 To get all 988+ PDFs, run with higher limits:")
        print(f"   python flexible_pdf_crawler_demo.py \"{correct_url}\" 18 988 50")
        print(f"⏰ Note: This will take time as it checks page counts for each PDF")
    else:
        print("❌ No PDF URLs found - checking debug info...")

        # Manual debug - let's see what the method is actually doing
        import requests
        import base64
        import re
        from urllib.parse import urlparse

        headers = {
            "Authorization": f"Basic {base64.b64encode(f'{api_key}:'.encode()).decode()}",
            "Content-Type": "application/json"
        }
        data = {
            "url": correct_url,
            "browserHtml": True
        }

        response = requests.post('https://api.zyte.com/v1/extract', headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            html = response.json().get('browserHtml', '')
            parsed_base = urlparse(correct_url)

            print(f"HTML length: {len(html)}")
            print(f"Domain: {parsed_base.netloc}")
            print(f"Is CIA? {'cia.gov' in parsed_base.netloc.lower()}")

            # Test document ID extraction manually
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

            cia_doc_ids = [doc_id for doc_id in document_ids if doc_id.startswith('0000') and len(doc_id) == 10]
            print(f"Found {len(cia_doc_ids)} CIA document IDs")

            if cia_doc_ids:
                print("Building PDF URLs...")
                for doc_id in cia_doc_ids[:5]:
                    pdf_url = f"https://www.cia.gov/readingroom/docs/DOC_{doc_id}.pdf"
                    print(f"  {pdf_url}")
        else:
            print(f"Failed to fetch HTML: {response.status_code}")

if __name__ == "__main__":
    main()