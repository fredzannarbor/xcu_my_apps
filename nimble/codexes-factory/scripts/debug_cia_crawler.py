#!/usr/bin/env python3
"""
Debug script for CIA crawler to understand why document links aren't being found.
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
    """Debug the CIA crawler to see what's happening."""

    # CIA URL from the user
    cia_url = "https://www.cia.gov/readingroom/search/site/?f%5B0%5D=im_field_taxonomy_nic_product%3A15&f%5B1%5D=ds_created%3A%5B2012-01-01T00%3A00%3A00Z%20TO%202013-01-01T00%3A00%3A00Z%5D&f%5B2%5D=ds_created%3A%5B2012-10-01T00%3A00%3A00Z%20TO%202012-11-01T00%3A00%3A00Z%5D"

    # Check for Zyte API key
    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        print("Error: ZYTE_API_KEY environment variable not set")
        return

    print("=" * 80)
    print("CIA CRAWLER DEBUG")
    print("=" * 80)
    print(f"Target URL: {cia_url}")
    print("=" * 80)

    # Initialize crawler
    crawler = ZyteCrawler(api_key)

    try:
        print("\n🔍 Step 1: Testing document page URL extraction...")

        # Test the document page URL extraction directly
        document_urls = crawler._get_document_page_urls(cia_url)

        print(f"Found {len(document_urls)} document page URLs")

        if document_urls:
            print("\nFirst 10 document URLs:")
            for i, url in enumerate(document_urls[:10]):
                print(f"  {i+1}. {url}")

            # Test getting PDFs from the first document page
            if len(document_urls) > 0:
                test_doc_url = document_urls[0]
                print(f"\n🔍 Step 2: Testing PDF extraction from: {test_doc_url}")

                # Let's also check what's actually on the document page
                print(f"\n🔍 Step 2a: Analyzing document page HTML...")
                import requests
                import base64
                headers = {
                    "Authorization": f"Basic {base64.b64encode(f'{api_key}:'.encode()).decode()}",
                    "Content-Type": "application/json"
                }
                data = {
                    "url": test_doc_url,
                    "browserHtml": True
                }
                response = requests.post('https://api.zyte.com/v1/extract', headers=headers, json=data, timeout=30)
                if response.status_code == 200:
                    doc_html = response.json().get('browserHtml', '')

                    # Look for PDF links
                    import re
                    pdf_links = re.findall(r'href=["\']([^"\']*\.pdf[^"\'\s]*)["\']', doc_html)
                    print(f"Found {len(pdf_links)} .pdf links in document page:")
                    for pdf_link in pdf_links:
                        print(f"  {pdf_link}")

                    # Look for /docs/ links (CIA pattern)
                    docs_links = re.findall(r'href=["\']([^"\']*\/docs\/[^"\']*)["\']', doc_html)
                    print(f"Found {len(docs_links)} /docs/ links:")
                    for docs_link in docs_links:
                        print(f"  {docs_link}")

                pdf_urls = crawler.get_pdf_urls(test_doc_url)
                print(f"\nCrawler found {len(pdf_urls)} PDF URLs on document page")

                for pdf_url in pdf_urls:
                    print(f"  PDF: {pdf_url}")

                    # Test page count for first PDF
                    if pdf_urls:
                        test_pdf = pdf_urls[0]
                        print(f"\n🔍 Step 3: Testing page count for: {test_pdf}")
                        page_count = crawler.get_pdf_page_count(test_pdf)
                        print(f"Page count: {page_count}")
        else:
            print("❌ No document URLs found!")

        # Debug: Try the old CIA method to compare
        print("\n🔍 Comparing with legacy CIA method...")
        legacy_docs = crawler.get_cia_document_page_urls(cia_url, max_docs=10)
        print(f"Legacy method found {len(legacy_docs)} document URLs")
        for i, url in enumerate(legacy_docs[:5]):
            print(f"  {i+1}. {url}")

        # Debug: Let's see what the raw HTML contains
        print("\n🔍 Step 3: Raw HTML analysis...")
        import requests
        import base64
        headers = {
            "Authorization": f"Basic {base64.b64encode(f'{api_key}:'.encode()).decode()}",
            "Content-Type": "application/json"
        }
        data = {
            "url": cia_url,
            "browserHtml": True
        }
        response = requests.post('https://api.zyte.com/v1/extract', headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            html = response.json().get('browserHtml', '')

            # Look for all /readingroom/ links
            import re
            readingroom_links = re.findall(r'href=["\']([^"\']*\/readingroom\/[^"\'\s]*)["\']', html)
            print(f"Found {len(readingroom_links)} total readingroom links")

            # Categorize them
            node_links = [link for link in readingroom_links if '/node/' in link]
            doc_links = [link for link in readingroom_links if '/document/' in link]
            collection_links = [link for link in readingroom_links if '/collection/' in link]

            print(f"  /node/ links: {len(node_links)}")
            print(f"  /document/ links: {len(doc_links)}")
            print(f"  /collection/ links: {len(collection_links)}")

            if doc_links:
                print("Sample /document/ links:")
                for i, link in enumerate(doc_links[:5]):
                    print(f"    {i+1}. {link}")

            if node_links:
                print("Sample /node/ links:")
                for i, link in enumerate(node_links[:5]):
                    print(f"    {i+1}. {link}")

            # Check for document IDs using the new extraction method
            print("\n🔍 Step 4: Document ID extraction test...")

            # Test the same patterns used in the crawler
            doc_id_patterns = [
                r'\/readingroom\/document\/(\d{10})',  # /readingroom/document/0000119706
                r'\/document\/(\d{10})',               # /document/0000119706
                r'href=["\'][^"\']*\/document\/(\d{10})[^"\']*["\']',  # In href attributes
                r'(\d{10})',  # Any 10-digit number (fallback)
            ]

            all_document_ids = set()
            for pattern in doc_id_patterns:
                matches = re.findall(pattern, html)
                if matches:
                    all_document_ids.update(matches)
                    print(f"  Pattern '{pattern}' found {len(matches)} matches: {matches[:5]}")

            # Filter for CIA format (starting with 0000)
            cia_doc_ids = [doc_id for doc_id in all_document_ids if doc_id.startswith('0000') and len(doc_id) == 10]
            print(f"\nFiltered CIA document IDs: {len(cia_doc_ids)}")
            for i, doc_id in enumerate(sorted(cia_doc_ids)[:10]):
                print(f"  {i+1}. {doc_id}")

            if cia_doc_ids:
                # Test constructing a PDF URL
                test_doc_id = cia_doc_ids[0]
                test_pdf_url = f"https://www.cia.gov/readingroom/docs/DOC_{test_doc_id}.pdf"
                print(f"\nTest PDF URL: {test_pdf_url}")

        else:
            print(f"Failed to fetch raw HTML: {response.status_code}")

    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("Debug complete.")


if __name__ == "__main__":
    main()