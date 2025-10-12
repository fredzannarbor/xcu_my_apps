#!/usr/bin/env python3
"""
Test crawling a specific CIA collection to see if it contains document IDs.
"""

import os
import re
import base64
import requests
from pathlib import Path
import sys

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
    """Test collection crawling."""

    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        print("Error: ZYTE_API_KEY environment variable not set")
        return

    # Test one of the collections we found
    collection_url = "https://www.cia.gov/readingroom/collection/nixon-collection"

    print(f"Testing collection: {collection_url}")

    # Initialize crawler
    crawler = ZyteCrawler(api_key)

    # Test document ID extraction from collection
    pdf_urls = crawler._get_document_page_urls(collection_url)
    print(f"Found {len(pdf_urls)} PDF URLs in collection")

    for i, pdf_url in enumerate(pdf_urls[:5]):
        print(f"  {i+1}. {pdf_url}")

    # Also test raw HTML analysis
    print(f"\n=== RAW HTML ANALYSIS ===")

    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{api_key}:'.encode()).decode()}",
        "Content-Type": "application/json"
    }
    data = {
        "url": collection_url,
        "browserHtml": True
    }

    response = requests.post('https://api.zyte.com/v1/extract', headers=headers, json=data, timeout=30)

    if response.status_code == 200:
        html = response.json().get('browserHtml', '')

        # Look for document IDs
        doc_id_patterns = [
            r'\/readingroom\/document\/(\d{10})',
            r'\/document\/(\d{10})',
            r'(\d{10})',
        ]

        all_document_ids = set()
        for pattern in doc_id_patterns:
            matches = re.findall(pattern, html)
            if matches:
                all_document_ids.update(matches)
                print(f"Pattern '{pattern}' found {len(matches)} matches")

        # Filter for CIA format
        cia_doc_ids = [doc_id for doc_id in all_document_ids if doc_id.startswith('0000') and len(doc_id) == 10]
        print(f"\nFound {len(cia_doc_ids)} CIA document IDs in collection:")
        for i, doc_id in enumerate(sorted(cia_doc_ids)[:10]):
            print(f"  {i+1}. {doc_id}")

        # Look for any mentions of specific document patterns
        pdf_mentions = re.findall(r'DOC_\d{10}\.pdf', html)
        print(f"\nFound {len(pdf_mentions)} DOC_*.pdf mentions:")
        for mention in pdf_mentions[:5]:
            print(f"  {mention}")

        # Look for links in general
        all_links = re.findall(r'href=["\']([^"\']+)["\']', html)
        document_links = [link for link in all_links if '/document/' in link]
        print(f"\nFound {len(document_links)} /document/ links:")
        for link in document_links[:5]:
            print(f"  {link}")

    else:
        print(f"Failed to fetch collection: {response.status_code}")

if __name__ == "__main__":
    main()