#!/usr/bin/env python3
"""
Test the correct CIA URL to see if it returns individual documents.
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

def main():
    """Test the correct CIA URL."""

    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        print("Error: ZYTE_API_KEY environment variable not set")
        return

    # Test the correct URL
    correct_url = "https://www.cia.gov/readingroom/search/site/?f%5B0%5D=im_field_taxonomy_nic_product%3A15&f%5B1%5D=ds_created"

    print(f"Testing correct URL: {correct_url}")

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
        print(f"HTML length: {len(html)}")

        # Look for all /readingroom/ links
        readingroom_links = re.findall(r'href=["\']([^"\']*\/readingroom\/[^"\'\s]*)["\']', html)
        print(f"\nFound {len(readingroom_links)} total readingroom links")

        # Categorize them
        node_links = [link for link in readingroom_links if '/node/' in link]
        doc_links = [link for link in readingroom_links if '/document/' in link]
        collection_links = [link for link in readingroom_links if '/collection/' in link]

        print(f"  /node/ links: {len(node_links)}")
        print(f"  /document/ links: {len(doc_links)}")
        print(f"  /collection/ links: {len(collection_links)}")

        if doc_links:
            print("\nSample /document/ links:")
            for i, link in enumerate(doc_links[:10]):
                print(f"    {i+1}. {link}")

        # Extract document IDs
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
                print(f"\nPattern '{pattern}' found {len(matches)} matches")

        # Filter for CIA format
        cia_doc_ids = [doc_id for doc_id in all_document_ids if doc_id.startswith('0000') and len(doc_id) == 10]
        print(f"\nFound {len(cia_doc_ids)} CIA document IDs:")
        for i, doc_id in enumerate(sorted(cia_doc_ids)[:20]):
            print(f"  {i+1}. {doc_id}")

        if cia_doc_ids:
            # Test a few PDF URLs
            print(f"\nTesting PDF URLs:")
            for doc_id in cia_doc_ids[:3]:
                pdf_url = f"https://www.cia.gov/readingroom/docs/DOC_{doc_id}.pdf"
                print(f"  {pdf_url}")

    else:
        print(f"Failed to fetch: {response.status_code}")

if __name__ == "__main__":
    main()