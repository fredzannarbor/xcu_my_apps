#!/usr/bin/env python3
"""
Test HTML parsing to see why we're getting different results.
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

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("BeautifulSoup not available")
    BeautifulSoup = None

def main():
    """Test HTML parsing."""

    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        print("Error: ZYTE_API_KEY environment variable not set")
        return

    cia_url = "https://www.cia.gov/readingroom/search/site/?f%5B0%5D=im_field_taxonomy_nic_product%3A15&f%5B1%5D=ds_created%3A%5B2012-01-01T00%3A00%3A00Z%20TO%202013-01-01T00%3A00%3A00Z%5D&f%5B2%5D=ds_created%3A%5B2012-10-01T00%3A00%3A00Z%20TO%202012-11-01T00%3A00%3A00Z%5D"

    print("Fetching HTML...")
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{api_key}:'.encode()).decode()}",
        "Content-Type": "application/json"
    }
    data = {
        "url": cia_url,
        "browserHtml": True
    }
    response = requests.post('https://api.zyte.com/v1/extract', headers=headers, json=data, timeout=30)

    if response.status_code != 200:
        print(f"Failed to fetch: {response.status_code}")
        return

    html = response.json().get('browserHtml', '')
    print(f"HTML length: {len(html)}")

    # Test regex extraction
    print("\n=== REGEX EXTRACTION ===")
    doc_pattern = r'href=["\']([^"\']*\/readingroom\/document\/\d+[^"\'\s]*)["\']'
    regex_matches = re.findall(doc_pattern, html)
    print(f"Regex found {len(regex_matches)} /document/ links:")
    for i, link in enumerate(regex_matches[:5]):
        print(f"  {i+1}. {link}")

    # Test BeautifulSoup extraction
    if BeautifulSoup:
        print("\n=== BEAUTIFULSOUP EXTRACTION ===")
        soup = BeautifulSoup(html, 'html.parser')
        all_links = soup.find_all('a', href=True)
        print(f"BeautifulSoup found {len(all_links)} total links")

        document_links = []
        collection_links = []

        for link in all_links:
            href = link['href']
            if '/readingroom/document/' in href:
                document_links.append(href)
            elif '/readingroom/collection/' in href:
                collection_links.append(href)

        print(f"BeautifulSoup /document/ links: {len(document_links)}")
        for i, link in enumerate(document_links[:5]):
            print(f"  {i+1}. {link}")

        print(f"BeautifulSoup /collection/ links: {len(collection_links)}")
        for i, link in enumerate(collection_links[:5]):
            print(f"  {i+1}. {link}")

        # Let's see if there are any clues in the link text or classes
        print("\n=== LINK ANALYSIS ===")
        for link in all_links[:10]:
            href = link.get('href', '')
            text = link.get_text(strip=True)[:50]
            classes = link.get('class', [])
            if '/readingroom/' in href:
                print(f"Link: {href}")
                print(f"  Text: {text}")
                print(f"  Classes: {classes}")
                print()

    # Check for JavaScript or JSON data containing document links
    print("\n=== SCRIPT/JSON ANALYSIS ===")

    # Look for document IDs in script tags or JSON
    doc_id_pattern = r'0000\d{6}'  # Pattern like 0000119706
    doc_ids = re.findall(doc_id_pattern, html)
    print(f"Found {len(set(doc_ids))} unique document IDs in HTML:")
    for doc_id in sorted(set(doc_ids))[:10]:
        print(f"  {doc_id}")

    # Look for /document/ in scripts or data
    script_doc_matches = re.findall(r'["\'][^"\']*\/readingroom\/document\/[^"\']*["\']', html)
    print(f"\nFound {len(script_doc_matches)} /document/ references in quotes:")
    for match in script_doc_matches[:5]:
        print(f"  {match}")

    # Look for any data attributes or JSON containing documents
    json_pattern = r'\{[^}]*document[^}]*\}'
    json_matches = re.findall(json_pattern, html, re.IGNORECASE)
    print(f"\nFound {len(json_matches)} JSON-like structures with 'document':")
    for match in json_matches[:3]:
        print(f"  {match[:100]}...")

    # Check if there are results containers that might be populated by JS
    if BeautifulSoup:
        soup = BeautifulSoup(html, 'html.parser')
        results_divs = soup.find_all(['div', 'section'], class_=re.compile(r'result|search|item', re.I))
        print(f"\nFound {len(results_divs)} potential results containers")
        for div in results_divs[:3]:
            print(f"  Class: {div.get('class')}")
            print(f"  ID: {div.get('id')}")
            print(f"  Content preview: {div.get_text(strip=True)[:100]}...")
            print()

if __name__ == "__main__":
    main()