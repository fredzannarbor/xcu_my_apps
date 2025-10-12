#!/usr/bin/env python3
"""
Test a specific CIA document page to understand the structure.
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
    """Test a specific document URL."""

    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        print("Error: ZYTE_API_KEY environment variable not set")
        return

    # Test the specific document URL you mentioned
    doc_url = "https://www.cia.gov/readingroom/document/0000119706"

    print(f"Testing specific document: {doc_url}")

    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{api_key}:'.encode()).decode()}",
        "Content-Type": "application/json"
    }
    data = {
        "url": doc_url,
        "browserHtml": True
    }

    response = requests.post('https://api.zyte.com/v1/extract', headers=headers, json=data, timeout=30)

    if response.status_code != 200:
        print(f"Failed to fetch: {response.status_code}")
        return

    html = response.json().get('browserHtml', '')
    print(f"HTML length: {len(html)}")

    # Look for PDF links (should be like DOC_0000119706.pdf)
    pdf_links = re.findall(r'href=["\']([^"\']*\.pdf[^"\'\s]*)["\']', html)
    print(f"\nFound {len(pdf_links)} .pdf links:")
    for pdf_link in pdf_links:
        print(f"  {pdf_link}")

    # Look for /docs/ links specifically
    docs_links = re.findall(r'href=["\']([^"\']*\/docs\/[^"\']*)["\']', html)
    print(f"\nFound {len(docs_links)} /docs/ links:")
    for docs_link in docs_links:
        print(f"  {docs_link}")

    # Look for the specific pattern you mentioned: DOC_0000119706.pdf
    doc_pattern = re.findall(r'href=["\']([^"\']*DOC_0000119706\.pdf[^"\'\s]*)["\']', html)
    print(f"\nFound {len(doc_pattern)} DOC_0000119706.pdf links:")
    for link in doc_pattern:
        print(f"  {link}")

    # Look for any links containing "0000119706"
    id_links = re.findall(r'href=["\']([^"\']*0000119706[^"\'\s]*)["\']', html)
    print(f"\nFound {len(id_links)} links containing '0000119706':")
    for link in id_links:
        print(f"  {link}")

    # Let's see if there are download buttons or other elements
    download_patterns = [
        r'href=["\']([^"\']*download[^"\'\s]*)["\']',
        r'href=["\']([^"\']*view[^"\'\s]*)["\']',
        r'href=["\']([^"\']*file[^"\'\s]*)["\']'
    ]

    for pattern in download_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            print(f"\nPattern '{pattern}' found {len(matches)} matches:")
            for match in matches:
                print(f"  {match}")

    # Show a sample of the page content to understand structure
    print(f"\n=== SAMPLE CONTENT ===")
    # Remove HTML tags for readability
    text_content = re.sub(r'<[^>]+>', ' ', html)
    text_content = re.sub(r'\s+', ' ', text_content)
    print(text_content[:500] + "...")

if __name__ == "__main__":
    main()