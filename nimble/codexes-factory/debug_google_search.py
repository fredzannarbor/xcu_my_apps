#!/usr/bin/env python3
"""
Debug script to test Google search PDF extraction
"""

import os
import sys
import re
import requests
import base64
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def build_google_search_url(site: str, start: int = 0, num: int = 10, time_filter: str = "y") -> str:
    """Build Google search URL with pagination."""
    base_url = "https://www.google.com/search"
    query = f"site:{site} filetype:pdf"
    url = f"{base_url}?q={query.replace(' ', '+')}&num={num}&tbs=qdr:{time_filter}&start={start}"
    return url

def extract_pdf_urls_from_google_results(html: str, site: str) -> list:
    """Extract PDF URLs from Google search results HTML."""
    pdf_urls = []

    # Pattern to find PDF URLs for the specific site
    pdf_pattern = rf'https?://[^\s"]*{re.escape(site)}[^\s"]*\.pdf'
    found_urls = re.findall(pdf_pattern, html, re.IGNORECASE)

    for url in found_urls:
        # Clean up URL encoding
        clean_url = (url.replace('%20', ' ')
                       .replace('%5B', '[')
                       .replace('%5D', ']')
                       .replace('%2C', ',')
                       .replace('%252C', ',')
                       .replace('%2520', ' '))

        if clean_url not in pdf_urls and clean_url.endswith('.pdf'):
            pdf_urls.append(clean_url)

    return pdf_urls

def test_google_search():
    """Test the Google search PDF extraction."""
    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        print("❌ ZYTE_API_KEY environment variable not set!")
        return

    print("🔍 Testing Google search PDF extraction...")

    # Test with CIA
    site = "cia.gov"
    google_url = build_google_search_url(site, 0, 10, "y")

    print(f"📄 Testing Google URL:")
    print(f"   {google_url}")

    try:
        # Fetch with Zyte
        headers = {
            'Authorization': f'Basic {base64.b64encode(f"{api_key}:".encode()).decode()}',
            'Content-Type': 'application/json'
        }

        data = {
            'url': google_url,
            'browserHtml': True,
            'javascript': True
        }

        response = requests.post('https://api.zyte.com/v1/extract', headers=headers, json=data, timeout=60)
        response.raise_for_status()

        html = response.json().get('browserHtml', '')

        print(f"📄 Got HTML response: {len(html)} characters")

        # Save HTML for inspection
        with open('debug_google_response.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("💾 Saved HTML response to debug_google_response.html")

        # Extract PDF URLs
        pdf_urls = extract_pdf_urls_from_google_results(html, site)
        print(f"🔍 Found {len(pdf_urls)} PDF URLs:")

        for i, url in enumerate(pdf_urls, 1):
            print(f"   {i}. {url}")

        # Show sample of HTML around PDF links
        print("\n📝 Sample HTML content (first 2000 chars):")
        print(html[:2000])

        # Search for any cia.gov mentions
        cia_mentions = html.count('cia.gov')
        print(f"\n🔍 Total 'cia.gov' mentions in HTML: {cia_mentions}")

        # Search for pdf mentions
        pdf_mentions = html.count('.pdf')
        print(f"🔍 Total '.pdf' mentions in HTML: {pdf_mentions}")

        # Test different regex patterns
        print("\n🧪 Testing different regex patterns:")

        patterns = [
            rf'https?://[^"\\s]*{re.escape(site)}[^"\\s]*\\.pdf',
            rf'https?://[^"\\s]*cia\.gov[^"\\s]*\.pdf',
            r'https?://[^\s"]*cia\.gov[^\s"]*\.pdf',
            r'https://[^\s"]+cia\.gov[^\s"]+\.pdf',
        ]

        for i, pattern in enumerate(patterns, 1):
            matches = re.findall(pattern, html, re.IGNORECASE)
            print(f"   Pattern {i}: {len(matches)} matches")
            if matches:
                for match in matches[:3]:  # Show first 3 matches
                    print(f"      - {match}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_google_search()