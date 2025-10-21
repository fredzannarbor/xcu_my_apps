#!/usr/bin/env python3
"""
Government PDF Downloader Agent

Searches specified government websites for newly posted PDF documents within
the last N days and downloads PDFs that meet page count criteria.
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import time

try:
    import requests
    from bs4 import BeautifulSoup
    import fitz  # PyMuPDF
    from tqdm import tqdm
except ImportError as e:
    print(f"Error: Required library not found: {e}")
    print("Install with: pip install requests beautifulsoup4 PyMuPDF tqdm")
    sys.exit(1)


@dataclass
class PDFDocument:
    """Represents a discovered PDF document."""
    url: str
    title: str
    page_count: int
    file_size_mb: float
    discovered_date: datetime
    local_path: Path = None


class GovPDFDownloader:
    """Agent to discover and download recent PDF documents from government websites."""

    # Site-specific search patterns
    SITE_CONFIGS = {
        'nsa.gov': {
            'use_google_search': True,  # NSA blocks scrapers, use Google instead
            'google_query': 'site:nsa.gov filetype:pdf',
            'search_paths': [
                '/news-features/press-room/',
                '/resources/everyone/digital-media-center/',
                '/portals/75/documents/',
            ],
            'pdf_pattern': r'\.pdf$',
            'follow_links': True,
            'max_depth': 2,
        },
        'cia.gov': {
            'use_google_search': True,
            'google_query': 'site:cia.gov filetype:pdf',
            'search_paths': [
                '/readingroom/',
                '/stories/',
                '/resources/',
            ],
            'pdf_pattern': r'\.pdf$',
            'follow_links': True,
            'max_depth': 2,
        },
        'dni.gov': {
            'use_google_search': True,
            'google_query': 'site:dni.gov filetype:pdf',
            'search_paths': [
                '/index.php/newsroom/',
                '/files/',
            ],
            'pdf_pattern': r'\.pdf$',
            'follow_links': True,
            'max_depth': 2,
        },
    }

    def __init__(
        self,
        domain: str,
        days_back: int = 60,
        min_pages: int = 18,
        output_dir: Path = None,
        user_agent: str = None
    ):
        """Initialize the government PDF downloader.

        Args:
            domain: Domain to search (e.g., 'nsa.gov')
            days_back: Number of days to look back for new documents
            min_pages: Minimum page count for PDFs to download
            output_dir: Directory to save downloaded PDFs
            user_agent: Custom user agent string
        """
        self.domain = domain
        self.days_back = days_back
        self.min_pages = min_pages
        self.cutoff_date = datetime.now() - timedelta(days=days_back)

        if output_dir is None:
            output_dir = Path.home() / "Downloads" / f"{domain}_pdfs"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.user_agent = user_agent or (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})

        self.visited_urls: Set[str] = set()
        self.discovered_pdfs: List[PDFDocument] = []

    def discover_pdfs(self) -> List[PDFDocument]:
        """Discover PDF documents on the target website.

        Returns:
            List of discovered PDFDocument objects
        """
        print(f"\nSearching {self.domain} for PDFs from the last {self.days_back} days...")
        print(f"Minimum page count: {self.min_pages}")

        config = self.SITE_CONFIGS.get(self.domain, {
            'search_paths': ['/'],
            'pdf_pattern': r'\.pdf$',
            'follow_links': True,
            'max_depth': 2,
        })

        # Use Google search if configured (for sites that block scrapers)
        if config.get('use_google_search', False):
            print("\nUsing Google search (site blocks direct crawling)...")
            self._google_search_pdfs(config)
        else:
            # Direct crawling
            base_url = f"https://{self.domain}"
            for search_path in config['search_paths']:
                start_url = urljoin(base_url, search_path)
                print(f"\nCrawling: {start_url}")
                self._crawl_page(start_url, config, depth=0)

        print(f"\nDiscovered {len(self.discovered_pdfs)} PDF links")
        return self.discovered_pdfs

    def _google_search_pdfs(self, config: Dict):
        """Use Google search to find PDFs on the domain.

        Args:
            config: Site configuration
        """
        query = config.get('google_query', f'site:{self.domain} filetype:pdf')

        print(f"Google search query: {query}")
        print("\nNote: Google search may have rate limits. Searching first 100 results...")

        try:
            # Use DuckDuckGo HTML search as alternative (no API key needed)
            search_url = f"https://html.duckduckgo.com/html/?q={query}"
            response = self.session.get(search_url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                links = soup.find_all('a', class_='result__url')

                for link in links:
                    href = link.get('href', '')
                    if href and '.pdf' in href.lower():
                        # Clean up the URL
                        if href.startswith('//'):
                            href = 'https:' + href
                        elif not href.startswith('http'):
                            href = f"https://{self.domain}{href}"

                        self._process_pdf_url(href)

            print(f"Discovered {len(self.discovered_pdfs)} PDFs via search")

        except Exception as e:
            print(f"Error with search engine: {e}")
            print("Falling back to direct URL patterns...")

            # Fallback: Try common PDF naming patterns
            self._try_common_pdf_patterns()

    def _crawl_page(self, url: str, config: Dict, depth: int = 0):
        """Recursively crawl pages to find PDFs.

        Args:
            url: URL to crawl
            config: Site configuration
            depth: Current crawl depth
        """
        if depth > config.get('max_depth', 2):
            return

        if url in self.visited_urls:
            return

        self.visited_urls.add(url)

        try:
            response = self.session.get(url, timeout=10, allow_redirects=True)
            response.raise_for_status()

            # Check if this URL itself is a PDF
            if url.lower().endswith('.pdf'):
                self._process_pdf_url(url)
                return

            # Parse HTML to find links
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all links
            links = soup.find_all('a', href=True)

            for link in links:
                href = link['href']
                absolute_url = urljoin(url, href)

                # Only follow links on the same domain
                if urlparse(absolute_url).netloc.endswith(self.domain):
                    if absolute_url.lower().endswith('.pdf'):
                        self._process_pdf_url(absolute_url)
                    elif config.get('follow_links', False) and depth < config.get('max_depth', 2):
                        self._crawl_page(absolute_url, config, depth + 1)

            # Small delay to be polite
            time.sleep(0.5)

        except Exception as e:
            print(f"Error crawling {url}: {e}")

    def _process_pdf_url(self, url: str):
        """Process a discovered PDF URL.

        Args:
            url: URL of the PDF
        """
        if url in [pdf.url for pdf in self.discovered_pdfs]:
            return

        try:
            # Check last modified date if available
            head_response = self.session.head(url, timeout=10, allow_redirects=True)
            last_modified = None

            if 'Last-Modified' in head_response.headers:
                try:
                    last_modified = datetime.strptime(
                        head_response.headers['Last-Modified'],
                        '%a, %d %b %Y %H:%M:%S %Z'
                    )
                except:
                    pass

            # If we can't determine date, we'll still include it
            if last_modified and last_modified < self.cutoff_date:
                return  # Too old, skip

            # Extract title from URL
            title = Path(urlparse(url).path).name

            # Add to discovered list (we'll check page count during download)
            pdf_doc = PDFDocument(
                url=url,
                title=title,
                page_count=0,  # Will be set during download
                file_size_mb=0.0,
                discovered_date=last_modified or datetime.now()
            )
            self.discovered_pdfs.append(pdf_doc)
            print(f"  Found: {title}")

        except Exception as e:
            print(f"Error processing PDF URL {url}: {e}")

    def download_pdfs(self, pdfs: List[PDFDocument] = None) -> List[PDFDocument]:
        """Download PDFs and filter by page count.

        Args:
            pdfs: List of PDFDocuments to download. If None, uses discovered_pdfs

        Returns:
            List of successfully downloaded PDFDocuments that meet criteria
        """
        if pdfs is None:
            pdfs = self.discovered_pdfs

        print(f"\nDownloading and filtering PDFs (min {self.min_pages} pages)...")

        downloaded = []

        for pdf in tqdm(pdfs, desc="Downloading PDFs"):
            try:
                # Download PDF
                response = self.session.get(pdf.url, timeout=30)
                response.raise_for_status()

                # Save temporarily to check page count
                temp_path = self.output_dir / f"temp_{pdf.title}"
                temp_path.write_bytes(response.content)

                # Check page count
                try:
                    doc = fitz.open(temp_path)
                    page_count = len(doc)
                    doc.close()

                    pdf.page_count = page_count
                    pdf.file_size_mb = len(response.content) / (1024 * 1024)

                    if page_count >= self.min_pages:
                        # Keep the file
                        final_path = self.output_dir / pdf.title
                        temp_path.rename(final_path)
                        pdf.local_path = final_path
                        downloaded.append(pdf)
                    else:
                        # Remove file - doesn't meet criteria
                        temp_path.unlink()

                except Exception as e:
                    print(f"\nError checking page count for {pdf.title}: {e}")
                    temp_path.unlink(missing_ok=True)

                # Be polite - small delay between downloads
                time.sleep(1)

            except Exception as e:
                print(f"\nError downloading {pdf.url}: {e}")

        return downloaded

    def generate_report(self, pdfs: List[PDFDocument]) -> None:
        """Generate a report of downloaded PDFs.

        Args:
            pdfs: List of PDFDocuments to report
        """
        print("\n" + "=" * 80)
        print("GOVERNMENT PDF DOWNLOADER - RESULTS")
        print("=" * 80)
        print(f"\nDomain: {self.domain}")
        print(f"Date range: Last {self.days_back} days")
        print(f"Minimum pages: {self.min_pages}")
        print(f"Output directory: {self.output_dir}")
        print(f"\nDownloaded {len(pdfs)} PDF(s) meeting criteria\n")

        if not pdfs:
            print("No PDFs found matching the criteria.")
            return

        # Sort by page count (descending)
        pdfs.sort(key=lambda x: x.page_count, reverse=True)

        for i, pdf in enumerate(pdfs, 1):
            print(f"{i}. {pdf.title}")
            print(f"   URL: {pdf.url}")
            print(f"   Pages: {pdf.page_count}")
            print(f"   Size: {pdf.file_size_mb:.2f} MB")
            print(f"   Date: {pdf.discovered_date.strftime('%Y-%m-%d')}")
            print(f"   Saved to: {pdf.local_path}")
            print()

        print("=" * 80)


def main():
    """Main entry point for the government PDF downloader."""
    parser = argparse.ArgumentParser(
        description="Download recent PDF documents from government websites"
    )
    parser.add_argument(
        "--domain",
        "-d",
        type=str,
        required=True,
        help="Domain to search (e.g., nsa.gov, cia.gov)"
    )
    parser.add_argument(
        "--days",
        "-n",
        type=int,
        default=60,
        help="Number of days to look back (default: 60)"
    )
    parser.add_argument(
        "--min-pages",
        "-p",
        type=int,
        default=18,
        help="Minimum page count (default: 18)"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output directory (default: ~/Downloads/{domain}_pdfs)"
    )

    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else None

    # Create downloader
    downloader = GovPDFDownloader(
        domain=args.domain,
        days_back=args.days,
        min_pages=args.min_pages,
        output_dir=output_dir
    )

    # Discover PDFs
    discovered = downloader.discover_pdfs()

    if not discovered:
        print("\nNo PDFs discovered. Exiting.")
        return

    # Download and filter by page count
    downloaded = downloader.download_pdfs(discovered)

    # Generate report
    downloader.generate_report(downloaded)


if __name__ == "__main__":
    main()
