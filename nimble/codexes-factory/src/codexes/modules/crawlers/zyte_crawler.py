#!/usr/bin/env python3
"""
Zyte Crawler for PDF Document Retrieval

This module provides functionality to crawl websites using the Zyte API,
extract PDF URLs, analyze document properties, and selectively download
documents based on specified criteria.
"""

import os
import base64
import datetime
import requests
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import logging

# Handle imports for both package and direct execution
try:
    from codexes.core.logging_config import get_logging_manager
except ModuleNotFoundError:
    from src.codexes.core.logging_config import get_logging_manager

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# Initialize logging
logger = logging.getLogger(__name__)


class ZyteCrawler:
    """
    A web crawler that uses the Zyte API to extract PDF documents from websites.

    This class provides functionality to:
    - Extract PDF URLs from web pages using Zyte's browser rendering
    - Analyze PDF documents to determine page counts
    - Filter and categorize documents based on size criteria
    - Download documents that meet specified criteria
    """

    def __init__(self, api_key: str, base_url: str = "https://api.zyte.com/v1/extract", timeout: int = 60):
        """
        Initialize the ZyteCrawler.She i

        Args:
            api_key: Zyte API key for authentication
            base_url: Base URL for Zyte API endpoints
        """
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.last_crawl_data: Dict[str, List[str]] = {}  # {URI: [PDF_URLs]}
        self.keyword_phrases: List[str] = []
        self.size_criteria: Dict[str, Tuple[int, int]] = {}  # {"category": (min_pages, max_pages)}

        # Initialize logging
        try:
            logging_manager = get_logging_manager()
            self.logger = logging_manager.get_logger(__name__)
        except Exception:
            self.logger = logging.getLogger(__name__)

        # Validate required dependencies
        if not fitz:
            self.logger.warning("PyMuPDF not available - PDF page counting will be disabled")
        if not BeautifulSoup:
            self.logger.warning("BeautifulSoup not available - HTML parsing will be limited")

    def set_keyword_phrases(self, keyword_phrases: List[str]) -> None:
        """Set keyword phrases for filtering documents."""
        self.keyword_phrases = keyword_phrases
        self.logger.info(f"Set {len(keyword_phrases)} keyword phrases for filtering")

    def set_size_criteria(self, size_criteria: Dict[str, Tuple[int, int]]) -> None:
        """
        Set size criteria for document categorization.

        Args:
            size_criteria: Dict mapping category names to (min_pages, max_pages) tuples
        """
        self.size_criteria = size_criteria
        self.logger.info(f"Set size criteria for {len(size_criteria)} categories")

    def get_pdf_urls(self, url: str) -> List[str]:
        """
        Extract all PDF URLs from a given webpage using Zyte API.

        Args:
            url: The webpage URL to crawl

        Returns:
            List of PDF URLs found on the page
        """
        headers = {
            "Authorization": f"Basic {base64.b64encode(f'{self.api_key}:'.encode()).decode()}",
            "Content-Type": "application/json"
        }

        data = {
            "url": url,
            "browserHtml": True
        }

        try:
            self.logger.info(f"Fetching PDF URLs from: {url}")
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()

            if response.status_code == 200:
                html = response.json().get('browserHtml', '')
                pdf_urls = self._extract_pdf_urls_from_html(html, url)
                self.logger.info(f"Found {len(pdf_urls)} PDF URLs on {url}")
                return pdf_urls
            else:
                self.logger.error(f"Error fetching {url}: HTTP {response.status_code}")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")

        return []

    def _extract_pdf_urls_from_html(self, html: str, base_url: str) -> List[str]:
        """
        Extract PDF URLs from HTML content.

        Args:
            html: HTML content to parse
            base_url: Base URL for resolving relative links

        Returns:
            List of absolute PDF URLs
        """
        pdf_urls = []

        if not BeautifulSoup:
            self.logger.warning("BeautifulSoup not available - using basic string matching")
            # Basic fallback - look for .pdf in href attributes
            import re
            pdf_links = re.findall(r'href=["\']([^"\']*\.pdf[^"\']*)["\']', html, re.IGNORECASE)
            pdf_urls.extend(pdf_links)
        else:
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a', href=True)

            for link in links:
                href = link['href']
                if href.lower().endswith('.pdf'):
                    # Convert relative URLs to absolute
                    if href.startswith('http'):
                        pdf_urls.append(href)
                    else:
                        from urllib.parse import urljoin
                        pdf_urls.append(urljoin(base_url, href))

        # Remove duplicates while preserving order
        return list(dict.fromkeys(pdf_urls))

    def get_pdf_page_count(self, pdf_url: str) -> int:
        """
        Get the number of pages in a PDF file using Zyte API.

        Args:
            pdf_url: URL of the PDF file

        Returns:
            Number of pages, or 0 if unable to determine
        """
        if not fitz:
            self.logger.warning("PyMuPDF not available - cannot count PDF pages")
            return 0

        try:
            self.logger.debug(f"Checking page count for: {pdf_url}")

            # Use Zyte API to fetch PDF content (handles redirects, auth, etc.)
            import requests
            import base64

            headers = {
                'Authorization': f'Basic {base64.b64encode(f"{self.api_key}:".encode()).decode()}',
                'Content-Type': 'application/json'
            }

            data = {
                'url': pdf_url,
                'httpResponseBody': True,
                'httpResponseHeaders': True
            }

            response = requests.post('https://api.zyte.com/v1/extract',
                                   headers=headers,
                                   json=data,
                                   timeout=self.timeout)
            response.raise_for_status()

            result = response.json()

            # Check if we got content
            if not result.get('httpResponseBody'):
                self.logger.warning(f"No content received for PDF: {pdf_url}")
                return 0

            # Decode base64 content
            import base64
            pdf_content = base64.b64decode(result['httpResponseBody'])

            # Check content size to avoid processing huge files
            if len(pdf_content) > 100 * 1024 * 1024:  # 100MB limit
                self.logger.warning(f"PDF too large ({len(pdf_content)} bytes): {pdf_url}")
                return 0

            # Count pages using PyMuPDF
            with fitz.open(stream=pdf_content) as doc:
                page_count = doc.page_count
                self.logger.debug(f"PDF {pdf_url} has {page_count} pages")
                return page_count

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching PDF via Zyte API {pdf_url}: {e}")
        except Exception as e:
            self.logger.error(f"Error parsing PDF {pdf_url}: {e}")

        return 0

    def categorize_pdf(self, page_count: int) -> str:
        """
        Categorize a PDF by page count.

        Args:
            page_count: Number of pages in the PDF

        Returns:
            Category string
        """
        if page_count <= 18:
            return "0-18"
        elif page_count <= 50:
            return "19-50"
        elif page_count <= 100:
            return "51-100"
        elif page_count <= 150:
            return "101-150"
        elif page_count <= 800:
            return "151-800"
        else:
            return "800+"

    def download_pdf(self, pdf_url: str, filename: str, output_dir: str = "downloads") -> bool:
        """
        Download a PDF file using Zyte API.

        Args:
            pdf_url: URL of the PDF to download
            filename: Local filename to save as
            output_dir: Directory to save the file in

        Returns:
            True if download successful, False otherwise
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            file_path = output_path / filename

            self.logger.info(f"Downloading {pdf_url} to {file_path}")

            # Use Zyte API to fetch PDF content (handles redirects, auth, etc.)
            headers = {
                'Authorization': f'Basic {base64.b64encode(f"{self.api_key}:".encode()).decode()}',
                'Content-Type': 'application/json'
            }

            data = {
                'url': pdf_url,
                'httpResponseBody': True,
                'httpResponseHeaders': True
            }

            response = requests.post('https://api.zyte.com/v1/extract',
                                   headers=headers,
                                   json=data,
                                   timeout=self.timeout)
            response.raise_for_status()

            result = response.json()

            # Check if we got content
            if not result.get('httpResponseBody'):
                self.logger.warning(f"No content received for PDF: {pdf_url}")
                return False

            # Decode base64 content
            pdf_content = base64.b64decode(result['httpResponseBody'])

            # Write to file
            with open(file_path, "wb") as f:
                f.write(pdf_content)

            self.logger.info(f"Successfully downloaded {filename} ({len(pdf_content)} bytes)")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error downloading PDF via Zyte API {pdf_url}: {e}")
        except Exception as e:
            self.logger.error(f"Error saving file {filename}: {e}")

        return False

    def get_cia_document_page_urls(self, search_url: str, max_docs: int = 50) -> List[str]:
        """
        Get document page URLs from CIA Reading Room search results.

        Args:
            search_url: The search URL to crawl
            max_docs: Maximum number of document URLs to return

        Returns:
            List of document page URLs
        """
        headers = {
            "Authorization": f"Basic {base64.b64encode(f'{self.api_key}:'.encode()).decode()}",
            "Content-Type": "application/json"
        }

        data = {
            "url": search_url,
            "browserHtml": True
        }

        try:
            self.logger.info(f"Fetching document page URLs from: {search_url}")
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()

            if response.status_code == 200:
                html = response.json().get('browserHtml', '')
                doc_urls = self._extract_document_urls_from_html(html)
                limited_urls = doc_urls[:max_docs]
                self.logger.info(f"Found {len(limited_urls)} document page URLs (limited from {len(doc_urls)})")
                return limited_urls
            else:
                self.logger.error(f"Error fetching {search_url}: HTTP {response.status_code}")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching {search_url}: {e}")

        return []

    def _extract_document_urls_from_html(self, html: str) -> List[str]:
        """
        Extract document/collection page URLs from CIA Reading Room search results HTML.

        Args:
            html: HTML content to parse

        Returns:
            List of absolute document/collection page URLs
        """
        doc_urls = []

        if not BeautifulSoup:
            self.logger.warning("BeautifulSoup not available - using regex fallback")
            import re
            # Look for both node links and collection links
            node_links = re.findall(r'href=["\']([^"\']*\/readingroom\/node\/\d+[^"\'\s]*)["\']', html)
            collection_links = re.findall(r'href=["\']([^"\']*\/readingroom\/collection\/[^"\'\s]*)["\']', html)
            doc_urls.extend(node_links)
            doc_urls.extend(collection_links)
        else:
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a', href=True)

            for link in links:
                href = link['href']
                # Look for node-based, document-based, and collection links
                if (('/readingroom/node/' in href and href != '/readingroom/node') or
                    ('/readingroom/collection/' in href and '?' not in href) or
                    ('/readingroom/document/' in href and '?' not in href)):  # Exclude pagination
                    # Convert relative URLs to absolute
                    if href.startswith('http'):
                        doc_urls.append(href)
                    else:
                        from urllib.parse import urljoin
                        doc_urls.append(urljoin('https://www.cia.gov', href))

        # Remove duplicates while preserving order
        return list(dict.fromkeys(doc_urls))

    def search_and_download_intelligence_docs(self,
                                             site: str = "cia.gov",
                                             min_pages: int = 18,
                                             max_docs: int = 300,
                                             time_filter: str = "recent") -> List[Dict]:
        """
        Use web search to find intelligence documents, then download them.

        Args:
            site: Site to search (e.g., "cia.gov", "fbi.gov", "dni.gov")
            min_pages: Minimum page count for documents
            max_docs: Maximum number of documents to process
            time_filter: Time filter ("recent", "year", "month")

        Returns:
            List of document info dictionaries
        """
        self.logger.info(f"Searching {site} for PDF documents with >{min_pages} pages")

        # This method would use WebSearch to find PDFs, then process them
        # For now, return the existing crawl method
        return self.crawl_cia_reading_room_legacy(2025, min_pages, max_docs)

    def crawl_cia_reading_room_legacy(self, year: int = 2025, min_pages: int = 18, max_docs: int = 20) -> List[Dict]:
        """
        Crawl CIA Reading Room for documents from a specific year with minimum page count.

        Args:
            year: Year to filter documents by (default: 2025)
            min_pages: Minimum page count for documents (default: 18)
            max_docs: Maximum number of documents to check (default: 20)

        Returns:
            List of document info dictionaries
        """
        base_url = "https://www.cia.gov/readingroom/search/site"

        # Construct search URL with correct date filter format
        search_url = f"{base_url}/?f%5B0%5D=ds_created%3A%5B{year}-01-01T00%3A00%3A00Z%20TO%20{year+1}-01-01T00%3A00%3A00Z%5D"

        self.logger.info(f"Crawling CIA Reading Room for {year} documents with >{min_pages} pages")

        # Step 1: Get document page URLs from search results
        doc_page_urls = self.get_cia_document_page_urls(search_url, max_docs)

        if not doc_page_urls:
            self.logger.warning("No document page URLs found in search results")
            return []

        documents = []

        # Step 2: Extract PDF URLs from each document page and check page count
        for doc_url in doc_page_urls:
            try:
                self.logger.debug(f"Processing document page: {doc_url}")
                pdf_urls = self.get_pdf_urls(doc_url)

                for pdf_url in pdf_urls:
                    try:
                        page_count = self.get_pdf_page_count(pdf_url)

                        if page_count > min_pages:
                            doc_info = {
                                'url': pdf_url,
                                'pages': page_count,
                                'category': self.categorize_pdf(page_count),
                                'filename': self._generate_filename(pdf_url, year, page_count),
                                'source_page': doc_url
                            }
                            documents.append(doc_info)
                            self.logger.info(f"Found suitable document: {page_count} pages - {pdf_url}")
                        else:
                            self.logger.debug(f"Skipping document with {page_count} pages: {pdf_url}")

                    except Exception as e:
                        self.logger.error(f"Error processing PDF {pdf_url}: {e}")
                        continue

            except Exception as e:
                self.logger.error(f"Error processing document page {doc_url}: {e}")
                continue

        self.logger.info(f"Found {len(documents)} documents matching criteria from {len(doc_page_urls)} document pages")
        return documents

    def _generate_filename(self, pdf_url: str, year: int, page_count: int, source_prefix: str = None) -> str:
        """Generate a standardized filename for downloaded PDFs."""
        base_name = Path(pdf_url).name
        if not base_name.endswith('.pdf'):
            base_name += '.pdf'

        # Auto-detect source if not provided
        if source_prefix is None:
            if "cia.gov" in pdf_url.lower():
                source_prefix = "CIA"
            elif "nsa.gov" in pdf_url.lower():
                source_prefix = "NSA"
            elif "fbi.gov" in pdf_url.lower():
                source_prefix = "FBI"
            elif "dni.gov" in pdf_url.lower() or "odni.gov" in pdf_url.lower():
                source_prefix = "ODNI"
            elif "dhs.gov" in pdf_url.lower():
                source_prefix = "DHS"
            else:
                source_prefix = "INTEL"

        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        return f"{source_prefix}_{year}_{page_count}p_{timestamp}_{base_name}"

    def crawl_url_for_pdfs(self,
                          start_url: str,
                          min_pages: int = 18,
                          max_docs: int = 100,
                          max_pages_to_crawl: int = 10,
                          two_level_crawl: bool = None,
                          output_dir: str = "downloads/flexible_crawl") -> List[Dict]:
        """
        Crawl any URL for PDF documents with flexible pagination handling.

        This method can handle different site structures by:
        1. Finding PDF links on the current page (direct PDFs)
        2. Finding document page links that lead to PDFs (two-level crawling)
        3. Looking for pagination links to crawl additional pages
        4. Filtering PDFs by page count criteria

        Args:
            start_url: The starting URL to begin crawling
            min_pages: Minimum page count for documents to include
            max_docs: Maximum number of documents to process
            max_pages_to_crawl: Maximum number of pages to crawl for pagination
            two_level_crawl: If True, look for document pages then PDFs. If None, auto-detect.
            output_dir: Directory to save downloads

        Returns:
            List of document info dictionaries
        """
        self.logger.info(f"Starting flexible crawl of: {start_url}")
        self.logger.info(f"Criteria: min_pages={min_pages}, max_docs={max_docs}, max_pages={max_pages_to_crawl}")

        # Auto-detect two-level crawling if not specified
        if two_level_crawl is None:
            two_level_crawl = self._should_use_two_level_crawl(start_url)

        self.logger.info(f"Using {'two-level' if two_level_crawl else 'direct'} crawling strategy")

        documents = []
        pages_crawled = 0
        current_url = start_url
        visited_urls = set()

        while pages_crawled < max_pages_to_crawl and len(documents) < max_docs and current_url:
            if current_url in visited_urls:
                self.logger.warning(f"Already visited {current_url}, stopping to avoid loop")
                break

            visited_urls.add(current_url)
            pages_crawled += 1

            self.logger.info(f"Crawling page {pages_crawled}: {current_url}")

            if two_level_crawl:
                # Two-level crawling: find document pages/IDs, then PDFs

                # Get URLs (collections or direct PDFs) for CIA
                if 'cia.gov' in current_url.lower():
                    self.logger.info("Processing CIA search page with robust fallback strategy")

                    # Strategy 1: Try direct document ID extraction from search page
                    pdf_urls = self._get_document_page_urls(current_url)

                    if pdf_urls:
                        self.logger.info(f"Strategy 1 success: Found {len(pdf_urls)} direct PDF URLs from search page")
                        # Process PDFs directly
                        for pdf_url in pdf_urls:
                            if len(documents) >= max_docs:
                                break

                            try:
                                page_count = self.get_pdf_page_count(pdf_url)

                                if page_count >= min_pages:
                                    doc_info = {
                                        'url': pdf_url,
                                        'pages': page_count,
                                        'category': self.categorize_pdf(page_count),
                                        'filename': self._generate_flexible_filename(pdf_url, page_count, current_url),
                                        'source_page': current_url,
                                        'direct_pdf': True,
                                        'crawl_page': pages_crawled
                                    }
                                    documents.append(doc_info)
                                    self.logger.info(f"Found suitable PDF: {page_count} pages - {pdf_url}")
                                else:
                                    self.logger.debug(f"Skipping PDF with {page_count} pages: {pdf_url}")

                            except Exception as e:
                                self.logger.error(f"Error processing PDF {pdf_url}: {e}")
                                continue
                    else:
                        # Strategy 2: Try known working document IDs as fallback
                        self.logger.info("Strategy 1 failed, trying Strategy 2: known working document IDs")

                        # Use some known working document IDs as fallback
                        known_working_ids = [
                            "0000119706", "0000258356", "0000272975", "0000258552",
                            "0000265620", "0000267692", "0000278546", "0000283820",
                            "0000042667", "0000218509"
                        ]

                        fallback_pdf_urls = []
                        for doc_id in known_working_ids[:min(max_docs, 10)]:
                            pdf_url = f"https://www.cia.gov/readingroom/docs/DOC_{doc_id}.pdf"
                            fallback_pdf_urls.append(pdf_url)

                        self.logger.info(f"Strategy 2: Testing {len(fallback_pdf_urls)} known working PDF URLs")

                        for pdf_url in fallback_pdf_urls:
                            if len(documents) >= max_docs:
                                break

                            try:
                                page_count = self.get_pdf_page_count(pdf_url)

                                if page_count >= min_pages:
                                    doc_info = {
                                        'url': pdf_url,
                                        'pages': page_count,
                                        'category': self.categorize_pdf(page_count),
                                        'filename': self._generate_flexible_filename(pdf_url, page_count, current_url),
                                        'source_page': current_url,
                                        'fallback_strategy': True,
                                        'crawl_page': pages_crawled
                                    }
                                    documents.append(doc_info)
                                    self.logger.info(f"Fallback success: {page_count} pages - {pdf_url}")
                                else:
                                    self.logger.debug(f"Skipping fallback PDF with {page_count} pages: {pdf_url}")

                            except Exception as e:
                                self.logger.error(f"Error processing fallback PDF {pdf_url}: {e}")
                                continue

                        # Strategy 3: Try collection-based approach if we still don't have enough
                        if len(documents) < max_docs:
                            self.logger.info("Strategy 3: Trying CIA collection crawling")
                            collection_urls = self.get_cia_document_page_urls(current_url, max_docs=5)
                            self.logger.info(f"Found {len(collection_urls)} CIA collections to crawl")

                            for collection_url in collection_urls:
                                if len(documents) >= max_docs:
                                    break

                                try:
                                    self.logger.info(f"Crawling CIA collection: {collection_url}")
                                    collection_pdf_urls = self._get_document_page_urls(collection_url)
                                    self.logger.info(f"Found {len(collection_pdf_urls)} PDFs in collection")

                                    for pdf_url in collection_pdf_urls:
                                        if len(documents) >= max_docs:
                                            break

                                        try:
                                            page_count = self.get_pdf_page_count(pdf_url)

                                            if page_count >= min_pages:
                                                doc_info = {
                                                    'url': pdf_url,
                                                    'pages': page_count,
                                                    'category': self.categorize_pdf(page_count),
                                                    'filename': self._generate_flexible_filename(pdf_url, page_count, current_url),
                                                    'source_page': current_url,
                                                    'collection_page': collection_url,
                                                    'crawl_page': pages_crawled
                                                }
                                                documents.append(doc_info)
                                                self.logger.info(f"Collection success: {page_count} pages - {pdf_url}")
                                            else:
                                                self.logger.debug(f"Skipping collection PDF with {page_count} pages: {pdf_url}")

                                        except Exception as e:
                                            self.logger.error(f"Error processing collection PDF {pdf_url}: {e}")
                                            continue

                                except Exception as e:
                                    self.logger.error(f"Error processing collection {collection_url}: {e}")
                                    continue

                else:
                    # For non-CIA sites, use traditional two-level crawling
                    document_page_urls = self._get_document_page_urls(current_url)
                    self.logger.info(f"Found {len(document_page_urls)} document pages to check for PDFs")

                    for doc_page_url in document_page_urls:
                        if len(documents) >= max_docs:
                            break

                        try:
                            self.logger.debug(f"Checking document page for PDFs: {doc_page_url}")
                            pdf_urls = self.get_pdf_urls(doc_page_url)

                            for pdf_url in pdf_urls:
                                if len(documents) >= max_docs:
                                    break

                                try:
                                    page_count = self.get_pdf_page_count(pdf_url)

                                    if page_count >= min_pages:
                                        doc_info = {
                                            'url': pdf_url,
                                            'pages': page_count,
                                            'category': self.categorize_pdf(page_count),
                                            'filename': self._generate_flexible_filename(pdf_url, page_count, current_url),
                                            'source_page': current_url,
                                            'document_page': doc_page_url,
                                            'crawl_page': pages_crawled
                                        }
                                        documents.append(doc_info)
                                        self.logger.info(f"Found suitable PDF: {page_count} pages - {pdf_url}")
                                    else:
                                        self.logger.debug(f"Skipping PDF with {page_count} pages: {pdf_url}")

                                except Exception as e:
                                    self.logger.error(f"Error processing PDF {pdf_url}: {e}")
                                    continue

                        except Exception as e:
                            self.logger.error(f"Error processing document page {doc_page_url}: {e}")
                            continue
            else:
                # Direct crawling: look for PDFs directly on the current page
                pdf_urls = self.get_pdf_urls(current_url)

                # Process PDFs from this page
                for pdf_url in pdf_urls:
                    if len(documents) >= max_docs:
                        break

                    try:
                        page_count = self.get_pdf_page_count(pdf_url)

                        if page_count >= min_pages:
                            doc_info = {
                                'url': pdf_url,
                                'pages': page_count,
                                'category': self.categorize_pdf(page_count),
                                'filename': self._generate_flexible_filename(pdf_url, page_count, current_url),
                                'source_page': current_url,
                                'crawl_page': pages_crawled
                            }
                            documents.append(doc_info)
                            self.logger.info(f"Found suitable PDF: {page_count} pages - {pdf_url}")
                        else:
                            self.logger.debug(f"Skipping PDF with {page_count} pages: {pdf_url}")

                    except Exception as e:
                        self.logger.error(f"Error processing PDF {pdf_url}: {e}")
                        continue

            # Look for next page URL if we haven't reached limits
            if pages_crawled < max_pages_to_crawl and len(documents) < max_docs:
                next_url = self._find_next_page_url(current_url)
                if next_url and next_url not in visited_urls:
                    current_url = next_url
                else:
                    self.logger.info("No more pages found or reached crawl limit")
                    break
            else:
                break

        self.logger.info(f"Crawl complete: Found {len(documents)} documents from {pages_crawled} pages")
        return documents

    def _generate_flexible_filename(self, pdf_url: str, page_count: int, source_url: str) -> str:
        """Generate a filename for flexibly crawled PDFs."""
        # Extract domain for prefix
        from urllib.parse import urlparse
        parsed_url = urlparse(source_url)
        domain = parsed_url.netloc.replace('www.', '').replace('.', '_').upper()

        # Get base filename
        base_name = Path(pdf_url).name
        if not base_name.endswith('.pdf'):
            base_name += '.pdf'

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        return f"{domain}_{page_count}p_{timestamp}_{base_name}"

    def _should_use_two_level_crawl(self, url: str) -> bool:
        """
        Auto-detect if a URL should use two-level crawling based on patterns.

        Args:
            url: The URL to analyze

        Returns:
            True if two-level crawling should be used
        """
        # Known patterns that typically use two-level crawling
        two_level_patterns = [
            'cia.gov/readingroom/search',
            'fbi.gov/services/records-management',
            'nsa.gov/releases',
            'dni.gov/index.php/newsroom',
            'dhs.gov/library',
            '/search/',
            '/results/',
            '/documents/',
            '/records/'
        ]

        url_lower = url.lower()
        for pattern in two_level_patterns:
            if pattern in url_lower:
                self.logger.info(f"Auto-detected two-level crawling needed for pattern: {pattern}")
                return True

        return False

    def _get_document_page_urls(self, search_page_url: str) -> List[str]:
        """
        Get document page URLs from a search results page.

        This is a generic version of get_cia_document_page_urls that works
        with different government sites.

        Args:
            search_page_url: The search results page URL

        Returns:
            List of document page URLs
        """
        headers = {
            "Authorization": f"Basic {base64.b64encode(f'{self.api_key}:'.encode()).decode()}",
            "Content-Type": "application/json"
        }

        data = {
            "url": search_page_url,
            "browserHtml": True
        }

        try:
            self.logger.debug(f"Fetching document page URLs from: {search_page_url}")
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()

            if response.status_code == 200:
                html = response.json().get('browserHtml', '')
                doc_urls = self._extract_generic_document_urls_from_html(html, search_page_url)
                self.logger.debug(f"Found {len(doc_urls)} document page URLs")
                return doc_urls
            else:
                self.logger.error(f"Error fetching {search_page_url}: HTTP {response.status_code}")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching {search_page_url}: {e}")

        return []

    def _extract_generic_document_urls_from_html(self, html: str, base_url: str) -> List[str]:
        """
        Extract document page URLs from search results HTML.

        This method looks for common patterns used by government sites
        for linking to individual document pages.

        Args:
            html: HTML content to parse
            base_url: Base URL for resolving relative links

        Returns:
            List of absolute document page URLs
        """
        doc_urls = []

        # For CIA sites, use document ID extraction for direct PDF construction
        from urllib.parse import urlparse
        parsed_base = urlparse(base_url)

        if 'cia.gov' in parsed_base.netloc.lower():
            self.logger.info("Using CIA document ID extraction for direct PDF construction")
            import re

            # Extract document IDs from the HTML (pattern: /document/0000123456 or similar)
            doc_id_patterns = [
                r'\/readingroom\/document\/(\d{10})',  # /readingroom/document/0000119706
                r'\/document\/(\d{10})',               # /document/0000119706
                r'href=["\'][^"\']*\/document\/(\d{10})[^"\']*["\']',  # In href attributes
                r'(\d{10})',  # Any 10-digit number (fallback)
            ]

            document_ids = set()
            for pattern in doc_id_patterns:
                matches = re.findall(pattern, html)
                if matches:
                    document_ids.update(matches)
                    self.logger.info(f"Document ID pattern {pattern} found {len(matches)} matches")

            # Convert document IDs to direct PDF URLs
            pdf_urls = []
            self.logger.info(f"Filtering {len(document_ids)} document IDs: {list(document_ids)[:10]}")

            for doc_id in document_ids:
                self.logger.debug(f"Checking doc_id: '{doc_id}' (len={len(doc_id)}, starts_with_0000={doc_id.startswith('0000')})")
                if doc_id.startswith('0000') and len(doc_id) == 10:  # CIA format validation
                    pdf_url = f"https://www.cia.gov/readingroom/docs/DOC_{doc_id}.pdf"
                    pdf_urls.append(pdf_url)
                    self.logger.debug(f"Added PDF URL: {pdf_url}")

            self.logger.info(f"Constructed {len(pdf_urls)} direct PDF URLs from {len(document_ids)} document IDs")

            # Return PDF URLs instead of document page URLs for CIA
            return pdf_urls

        else:
            # For non-CIA sites, use the original generic extraction
            self.logger.info("Using generic document URL extraction for non-CIA sites")
            import re
            # Generic patterns for document links
            patterns = [
                r'href=["\']([^"\']*\/readingroom\/node\/\d+[^"\'\s]*)["\']',
                r'href=["\']([^"\']*\/readingroom\/collection\/[^"\'\s]*)["\']',
                r'href=["\']([^"\']*\/readingroom\/document\/\d+[^"\'\s]*)["\']',
                r'href=["\']([^"\']*\/documents?\/[^"\'\s]*)["\']',
                r'href=["\']([^"\']*\/records?\/[^"\'\s]*)["\']',
                r'href=["\']([^"\']*\/doc\/[^"\'\s]*)["\']',
                r'href=["\']([^"\']*\/item\/[^"\'\s]*)["\']'
            ]

            for pattern in patterns:
                matches = re.findall(pattern, html)
                doc_urls.extend(matches)
                if matches:
                    self.logger.info(f"Pattern {pattern} found {len(matches)} matches")

            # Convert relative URLs to absolute for regex results
            from urllib.parse import urljoin
            absolute_urls = []
            for url in doc_urls:
                if url.startswith('http'):
                    absolute_urls.append(url)
                else:
                    absolute_urls.append(urljoin(base_url, url))

            doc_urls = absolute_urls

        # Remove duplicates while preserving order
        unique_urls = list(dict.fromkeys(doc_urls))

        # Filter out obviously wrong URLs (too short, etc.)
        filtered_urls = [url for url in unique_urls if len(url) > 20]

        # Debug logging
        if filtered_urls:
            self.logger.info(f"Found {len(filtered_urls)} document page URLs:")
            for i, url in enumerate(filtered_urls[:5]):  # Show first 5
                self.logger.info(f"  {i+1}. {url}")
            if len(filtered_urls) > 5:
                self.logger.info(f"  ... and {len(filtered_urls) - 5} more")
        else:
            self.logger.warning("No document page URLs found. Debug info:")
            if BeautifulSoup:
                soup = BeautifulSoup(html, 'html.parser')
                all_links = soup.find_all('a', href=True)
                self.logger.warning(f"Total links found on page: {len(all_links)}")
                # Show a sample of links for debugging
                sample_links = [link['href'] for link in all_links[:10]]
                self.logger.warning(f"Sample links: {sample_links}")

                # Debug: show which extraction method is being used
                self.logger.warning(f"Using BeautifulSoup extraction for domain: {parsed_base.netloc}")

        return filtered_urls

    def _find_next_page_url(self, current_url: str) -> Optional[str]:
        """
        Find the next page URL for pagination.

        This method looks for common pagination patterns:
        - "Next" links
        - Numbered page links
        - "More results" links

        Args:
            current_url: Current page URL

        Returns:
            Next page URL if found, None otherwise
        """
        try:
            headers = {
                "Authorization": f"Basic {base64.b64encode(f'{self.api_key}:'.encode()).decode()}",
                "Content-Type": "application/json"
            }

            data = {
                "url": current_url,
                "browserHtml": True
            }

            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()

            if response.status_code == 200:
                html = response.json().get('browserHtml', '')
                return self._extract_next_page_url_from_html(html, current_url)

        except Exception as e:
            self.logger.error(f"Error finding next page URL from {current_url}: {e}")

        return None

    def _extract_next_page_url_from_html(self, html: str, current_url: str) -> Optional[str]:
        """Extract next page URL from HTML using various pagination patterns."""
        if not BeautifulSoup:
            self.logger.warning("BeautifulSoup not available - pagination detection limited")
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Pattern 1: Look for "Next" links
        next_patterns = [
            'next', 'Next', 'NEXT', 'next page', 'Next Page',
            '>', '→', '»', 'more', 'More', 'Continue'
        ]

        for pattern in next_patterns:
            # Check link text
            next_link = soup.find('a', string=lambda text: text and pattern in text)
            if next_link and next_link.get('href'):
                href = next_link['href']
                if href.startswith('http'):
                    return href
                else:
                    from urllib.parse import urljoin
                    return urljoin(current_url, href)

            # Check link titles or aria-labels
            next_link = soup.find('a', attrs={'title': lambda x: x and pattern in x})
            if not next_link:
                next_link = soup.find('a', attrs={'aria-label': lambda x: x and pattern in x})

            if next_link and next_link.get('href'):
                href = next_link['href']
                if href.startswith('http'):
                    return href
                else:
                    from urllib.parse import urljoin
                    return urljoin(current_url, href)

        # Pattern 2: Look for pagination with page numbers
        # Find current page number and look for next number
        page_links = soup.find_all('a', string=lambda text: text and text.isdigit())
        if page_links:
            try:
                # Find the highest page number and see if there's a pattern
                page_numbers = [int(link.string) for link in page_links if link.string.isdigit()]
                if page_numbers:
                    max_page = max(page_numbers)
                    # Look for a link with the next page number
                    next_page_link = soup.find('a', string=str(max_page + 1))
                    if next_page_link and next_page_link.get('href'):
                        href = next_page_link['href']
                        if href.startswith('http'):
                            return href
                        else:
                            from urllib.parse import urljoin
                            return urljoin(current_url, href)
            except (ValueError, TypeError):
                pass

        # Pattern 3: Look for URL patterns with page parameters
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed = urlparse(current_url)
        query_params = parse_qs(parsed.query)

        # Common page parameter names
        page_param_names = ['page', 'p', 'start', 'offset', 'from']

        for param_name in page_param_names:
            if param_name in query_params:
                try:
                    current_page = int(query_params[param_name][0])
                    query_params[param_name] = [str(current_page + 1)]
                    new_query = urlencode(query_params, doseq=True)
                    next_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path,
                                         parsed.params, new_query, parsed.fragment))
                    return next_url
                except (ValueError, IndexError):
                    continue

        # Pattern 4: For CIA searches, try adding page parameter if none exists
        if 'cia.gov' in current_url.lower() and 'search/site' in current_url:
            self.logger.info("CIA search detected - trying page parameter pagination")

            # Check if we already have a page parameter
            if not any(param in query_params for param in ['page', 'p']):
                # Add page=1 to create page 2 URL
                query_params['page'] = ['1']
                new_query = urlencode(query_params, doseq=True)
                next_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path,
                                     parsed.params, new_query, parsed.fragment))
                self.logger.info(f"Generated page 2 URL: {next_url}")
                return next_url
            else:
                # Increment existing page parameter
                for param_name in ['page', 'p']:
                    if param_name in query_params:
                        try:
                            current_page = int(query_params[param_name][0])
                            query_params[param_name] = [str(current_page + 1)]
                            new_query = urlencode(query_params, doseq=True)
                            next_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path,
                                                 parsed.params, new_query, parsed.fragment))
                            self.logger.info(f"Generated page {current_page + 1} URL: {next_url}")
                            return next_url
                        except (ValueError, IndexError):
                            continue

        self.logger.debug(f"No pagination found on {current_url}")
        return None

    def download_filtered_documents(self, documents: List[Dict], output_dir: str = "downloads/cia_docs") -> int:
        """
        Download a list of filtered documents.

        Args:
            documents: List of document info dictionaries
            output_dir: Directory to save downloads

        Returns:
            Number of successfully downloaded documents
        """
        downloaded = 0

        for doc in documents:
            if self.download_pdf(doc['url'], doc['filename'], output_dir):
                downloaded += 1

        self.logger.info(f"Successfully downloaded {downloaded}/{len(documents)} documents")
        return downloaded


def main():
    """Demonstration of ZyteCrawler functionality."""
    import sys

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # Continue without dotenv if not available

    # This would typically come from environment variables
    api_key = os.getenv("ZYTE_API_KEY")

    if not api_key:
        print("Error: ZYTE_API_KEY environment variable not set")
        return

    crawler = ZyteCrawler(api_key)

    # Check command line arguments for flexible URL crawling
    if len(sys.argv) > 1:
        url = sys.argv[1]
        min_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 18
        max_docs = int(sys.argv[3]) if len(sys.argv) > 3 else 100

        print(f"Crawling URL: {url}")
        print(f"Min pages: {min_pages}, Max docs: {max_docs}")

        # Demonstrate flexible URL crawling
        documents = crawler.crawl_url_for_pdfs(
            start_url=url,
            min_pages=min_pages,
            max_docs=max_docs,
            max_pages_to_crawl=20
        )

        if documents:
            print(f"\nFound {len(documents)} documents matching criteria:")
            for doc in documents[:10]:  # Show first 10
                print(f"  {doc['pages']} pages: {doc['filename']} (from page {doc['crawl_page']})")

            # Ask user if they want to download
            response = input(f"\nDownload {len(documents)} documents? (y/N): ")
            if response.lower().startswith('y'):
                downloaded = crawler.download_filtered_documents(documents, "downloads/flexible_crawl")
                print(f"Downloaded {downloaded} documents")
        else:
            print("No documents found matching criteria")
    else:
        # Demonstrate CIA Reading Room crawling (legacy method)
        print("No URL provided. Demonstrating CIA Reading Room crawling...")
        print("Usage: python zyte_crawler.py <URL> [min_pages] [max_docs]")
        print("Example: python zyte_crawler.py 'https://www.cia.gov/readingroom/search/site/?f%5B0%5D=...' 18 100")

        # Show how to use the CIA-specific method
        documents = crawler.crawl_cia_reading_room_legacy(year=2025, min_pages=18)

        if documents:
            print(f"Found {len(documents)} CIA documents matching criteria:")
            for doc in documents[:5]:  # Show first 5
                print(f"  {doc['pages']} pages: {doc['filename']}")

            # Optionally download (commented out for safety)
            # downloaded = crawler.download_filtered_documents(documents)
            # print(f"Downloaded {downloaded} documents")


if __name__ == "__main__":
    main()