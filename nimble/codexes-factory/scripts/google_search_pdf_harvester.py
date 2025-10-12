#!/usr/bin/env python3
"""
Google Search PDF Harvester

This script replicates the Google search approach:
site:cia.gov filetype:pdf limited to recent year

It paginates through Google search results to find ~300 CIA documents,
evaluates their page counts, and downloads qualifying documents.

Usage:
    python3 scripts/google_search_pdf_harvester.py --site cia.gov --max-docs 300 --min-pages 18
"""

import os
import sys
import argparse
import time
import re
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from codexes.modules.crawlers import ZyteCrawler
    from codexes.core.logging_config import get_logging_manager
except ModuleNotFoundError:
    from src.codexes.modules.crawlers import ZyteCrawler
    from src.codexes.core.logging_config import get_logging_manager

# Load environment variables
load_dotenv()


class GoogleSearchPDFHarvester:
    """
    Harvests PDFs by replicating Google search with pagination.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.crawler = ZyteCrawler(api_key)

        # Initialize logging
        try:
            logging_manager = get_logging_manager()
            self.logger = logging_manager.get_logger(__name__)
        except Exception:
            import logging
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)

    def build_google_search_url(self, site: str, start: int = 0, num: int = 10, time_filter: str = "y") -> str:
        """
        Build Google search URL with pagination.

        Args:
            site: Site to search (e.g., "cia.gov")
            start: Starting result number (0, 10, 20, etc.)
            num: Number of results per page (max 10)
            time_filter: Time filter ("y" = past year, "m" = past month)
        """
        base_url = "https://www.google.com/search"
        query = f"site:{site} filetype:pdf"

        # Build the URL with all necessary parameters
        url = f"{base_url}?q={query.replace(' ', '+')}&num={num}&tbs=qdr:{time_filter}&start={start}"

        return url

    def extract_pdf_urls_from_google_results(self, html: str, site: str) -> List[str]:
        """
        Extract PDF URLs from Google search results HTML.
        """
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

    def search_google_with_pagination(self, site: str, max_docs: int = 300, time_filter: str = "y") -> List[str]:
        """
        Search Google with pagination to get up to max_docs results.
        """
        all_pdf_urls = []
        page_size = 10  # Google's max results per page
        max_pages = min(30, (max_docs + page_size - 1) // page_size)  # Google limits to ~300 results

        self.logger.info(f"Searching Google for site:{site} filetype:pdf (max {max_docs} docs)")

        for page in range(max_pages):
            start = page * page_size

            try:
                self.logger.info(f"Fetching results {start}-{start+page_size-1} (page {page+1}/{max_pages})")

                # Build Google search URL
                google_url = self.build_google_search_url(site, start, page_size, time_filter)

                # Fetch with Zyte
                import requests
                import base64

                headers = {
                    'Authorization': f'Basic {base64.b64encode(f"{self.api_key}:".encode()).decode()}',
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

                # Extract PDF URLs from this page
                page_pdf_urls = self.extract_pdf_urls_from_google_results(html, site)

                self.logger.info(f"Found {len(page_pdf_urls)} PDF URLs on page {page+1}")

                # Add new URLs
                for url in page_pdf_urls:
                    if url not in all_pdf_urls:
                        all_pdf_urls.append(url)

                # Stop if we have enough or if no results found
                if len(all_pdf_urls) >= max_docs or len(page_pdf_urls) == 0:
                    break

                # Rate limiting between pages
                time.sleep(3)

            except Exception as e:
                self.logger.error(f"Error fetching page {page+1}: {e}")
                continue

        unique_urls = list(dict.fromkeys(all_pdf_urls))[:max_docs]
        self.logger.info(f"Total unique PDF URLs found: {len(unique_urls)}")

        return unique_urls

    def evaluate_and_download_pdfs(self, pdf_urls: List[str], min_pages: int = 18,
                                   output_dir: str = "downloads/google_harvest") -> Dict:
        """
        Evaluate PDF page counts and download qualifying documents.
        """
        self.logger.info(f"Evaluating {len(pdf_urls)} PDFs (min {min_pages} pages)")

        documents = []
        processed = 0

        for pdf_url in pdf_urls:
            try:
                processed += 1
                self.logger.info(f"Processing {processed}/{len(pdf_urls)}: {Path(pdf_url).name}")

                # Check page count
                page_count = self.crawler.get_pdf_page_count(pdf_url)

                if page_count >= min_pages:
                    category = self.crawler.categorize_pdf(page_count)

                    # Determine source
                    if "cia.gov" in pdf_url:
                        source = "CIA"
                    elif "fbi.gov" in pdf_url:
                        source = "FBI"
                    elif "dni.gov" in pdf_url or "odni.gov" in pdf_url:
                        source = "ODNI"
                    elif "dhs.gov" in pdf_url:
                        source = "DHS"
                    else:
                        source = "INTEL"

                    doc_info = {
                        'url': pdf_url,
                        'pages': page_count,
                        'category': category,
                        'source': source,
                        'filename': self.crawler._generate_filename(pdf_url, 2025, page_count)
                    }

                    documents.append(doc_info)
                    self.logger.info(f"✅ Qualifying: {page_count} pages, {source}")
                else:
                    self.logger.info(f"❌ Too short: {page_count} pages (need {min_pages}+)")

                # Rate limiting
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error processing {pdf_url}: {e}")
                continue

        # Download qualifying documents
        downloaded = 0
        if documents:
            self.logger.info(f"Downloading {len(documents)} qualifying documents...")

            for i, doc in enumerate(documents):
                try:
                    self.logger.info(f"Downloading {i+1}/{len(documents)}: {doc['filename']}")

                    success = self.crawler.download_pdf(doc['url'], doc['filename'], output_dir)

                    if success:
                        downloaded += 1
                        self.logger.info(f"✅ Downloaded: {doc['source']} - {doc['pages']} pages")
                    else:
                        self.logger.error(f"❌ Download failed: {doc['filename']}")

                    time.sleep(2)

                except Exception as e:
                    self.logger.error(f"Error downloading {doc['filename']}: {e}")
                    continue

        return {
            'total_urls_found': len(pdf_urls),
            'qualifying_documents': len(documents),
            'successfully_downloaded': downloaded,
            'documents': documents
        }

    def harvest_pdfs_from_google(self, site: str, max_docs: int = 300, min_pages: int = 18,
                                output_dir: str = "downloads/google_harvest") -> Dict:
        """
        Main method to harvest PDFs using Google search pagination.
        """
        self.logger.info(f"🚀 Starting Google search PDF harvest for {site}")

        # Step 1: Search Google with pagination
        pdf_urls = self.search_google_with_pagination(site, max_docs)

        if not pdf_urls:
            self.logger.warning(f"No PDF URLs found for {site}")
            return {'error': 'No PDFs found'}

        # Step 2: Evaluate and download
        results = self.evaluate_and_download_pdfs(pdf_urls, min_pages, output_dir)

        self.logger.info(f"🎉 Harvest complete for {site}")
        self.logger.info(f"Found: {results['total_urls_found']} PDFs")
        self.logger.info(f"Qualifying: {results['qualifying_documents']} documents")
        self.logger.info(f"Downloaded: {results['successfully_downloaded']} documents")

        return results


def main():
    """Main command line interface."""
    parser = argparse.ArgumentParser(description="Harvest PDFs using Google search pagination")
    parser.add_argument("--site", default="cia.gov", help="Site to search (default: cia.gov)")
    parser.add_argument("--max-docs", type=int, default=300, help="Maximum documents to find (default: 300)")
    parser.add_argument("--min-pages", type=int, default=18, help="Minimum page count (default: 18)")
    parser.add_argument("--output-dir", default="downloads/google_harvest", help="Output directory")
    parser.add_argument("--time-filter", default="y", choices=["y", "m"], help="Time filter: y=year, m=month")
    parser.add_argument("--timeout", type=int, default=60, help="Request timeout in seconds (default: 60)")

    args = parser.parse_args()

    # Check for API key
    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        print("❌ ZYTE_API_KEY environment variable not set!")
        print("Please set your Zyte API key in .env file")
        return 1

    print(f"🚀 Starting Google Search PDF Harvester")
    print(f"Site: {args.site}")
    print(f"Max documents: {args.max_docs}")
    print(f"Min pages: {args.min_pages}")
    print(f"Time filter: {args.time_filter} ({'past year' if args.time_filter == 'y' else 'past month'})")
    print(f"Output: {args.output_dir}")

    try:
        harvester = GoogleSearchPDFHarvester(api_key)

        results = harvester.harvest_pdfs_from_google(
            site=args.site,
            max_docs=args.max_docs,
            min_pages=args.min_pages,
            output_dir=args.output_dir
        )

        if 'error' not in results:
            print(f"\n📊 FINAL RESULTS:")
            print(f"Total PDF URLs found: {results['total_urls_found']}")
            print(f"Qualifying documents: {results['qualifying_documents']}")
            print(f"Successfully downloaded: {results['successfully_downloaded']}")
            print(f"Success rate: {results['successfully_downloaded']}/{results['qualifying_documents']} downloads")

        return 0

    except KeyboardInterrupt:
        print("\n⏹️ Harvest interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Error during harvest: {e}")
        return 1


if __name__ == "__main__":
    exit(main())