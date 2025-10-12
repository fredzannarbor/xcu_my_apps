#!/usr/bin/env python3
"""
Test pagination detection for the CIA search URL.
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
    """Test pagination detection."""

    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        print("Error: ZYTE_API_KEY environment variable not set")
        return

    # Test the URL with sorting
    test_url = "https://www.cia.gov/readingroom/search/site?f%5B0%5D=im_field_taxonomy_nic_product%3A15&solrsort=sort_label%20asc"

    print(f"Testing pagination for: {test_url}")

    # Initialize crawler
    crawler = ZyteCrawler(api_key)

    # Test next page URL detection
    print("\n=== TESTING PAGINATION DETECTION ===")
    next_url = crawler._find_next_page_url(test_url)

    if next_url:
        print(f"✅ Found next page URL: {next_url}")

        # Test if the next page has different documents
        print("\n=== TESTING NEXT PAGE CONTENT ===")
        current_page_pdfs = crawler._get_document_page_urls(test_url)
        next_page_pdfs = crawler._get_document_page_urls(next_url)

        print(f"Current page: {len(current_page_pdfs)} PDFs")
        print(f"Next page: {len(next_page_pdfs)} PDFs")

        if current_page_pdfs and next_page_pdfs:
            print(f"Current page first PDF: {current_page_pdfs[0]}")
            print(f"Next page first PDF: {next_page_pdfs[0]}")

            if current_page_pdfs[0] != next_page_pdfs[0]:
                print("✅ Pages have different content")
            else:
                print("❌ Pages have same content")
    else:
        print("❌ No next page URL found")

        # Debug: let's see what pagination elements exist
        print("\n=== DEBUG: CHECKING FOR PAGINATION ELEMENTS ===")
        import requests
        import base64
        from bs4 import BeautifulSoup

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
            soup = BeautifulSoup(html, 'html.parser')

            # Look for common pagination patterns
            pagination_patterns = [
                'next', 'Next', '>', '»', 'more', 'More',
                'page 2', 'Page 2', '[2]'
            ]

            for pattern in pagination_patterns:
                links = soup.find_all('a', string=lambda text: text and pattern in text)
                if links:
                    print(f"Found '{pattern}' links: {len(links)}")
                    for link in links[:2]:
                        print(f"  {link.get('href')} - '{link.get_text(strip=True)}'")

            # Look for numbered pagination
            numbered_links = soup.find_all('a', string=lambda text: text and text.isdigit())
            if numbered_links:
                print(f"Found numbered links: {[link.get_text() for link in numbered_links]}")

if __name__ == "__main__":
    main()