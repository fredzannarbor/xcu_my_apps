"""
Zyte-based web crawler for PDF document extraction and processing.

This module provides the ZyteCrawler class that uses the Zyte API to extract PDF
documents from web pages, categorize them by page count, and process them according
to specified criteria.

The module follows codexes-factory standards with:
- Centralized logging through get_logging_manager()
- Environment configuration via .env file
- Fallback import patterns for both package and direct execution
- Proper error handling and validation
"""

import base64
import datetime
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Fallback import pattern for both package and direct execution
try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("PyMuPDF is required. Install with: pip install PyMuPDF")

try:
    from codexes.core.logging_config import get_logging_manager
except ModuleNotFoundError:
    try:
        from src.codexes.core.logging_config import get_logging_manager
    except ModuleNotFoundError:
        # Fallback for standalone execution
        def get_logging_manager():
            class MockLoggingManager:
                def get_logger(self, name):
                    return logging.getLogger(name)
            return MockLoggingManager()

# Load environment variables
load_dotenv()


class ZyteCrawler:
    """
    Web crawler using Zyte API for PDF document extraction and processing.

    This class provides functionality to:
    - Extract PDF URLs from web pages using Zyte API
    - Check PDF page counts cost-effectively
    - Filter documents by page count criteria
    - Download and categorize PDFs
    - Integrate with existing codexes processing pipeline

    Attributes:
        api_key: Zyte API key for authentication
        base_url: Zyte API endpoint URL
        last_crawl_data: Cache of previously found PDF URLs by source URL
        keyword_phrases: List of keyword phrases for filtering
        size_criteria: Dictionary mapping categories to (min_pages, max_pages) tuples
        logger: Centralized logger instance
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.zyte.com/v1/extract"):
        """
        Initialize the ZyteCrawler.

        Args:
            api_key: Zyte API key. If None, attempts to load from ZYTE_API_KEY environment variable
            base_url: Zyte API endpoint URL

        Raises:
            ValueError: If no API key is provided or found in environment
        """
        # Set up logging
        logging_manager = get_logging_manager()
        self.logger = logging_manager.get_logger(__name__)

        # Configure API key
        self.api_key = api_key or os.getenv('ZYTE_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Zyte API key is required. Provide it as a parameter or set ZYTE_API_KEY environment variable."
            )

        self.base_url = base_url
        self.last_crawl_data: Dict[str, List[str]] = {}  # {URI: [PDF_URLs]}
        self.keyword_phrases: List[str] = []
        self.size_criteria: Dict[str, Tuple[int, int]] = {}  # {"category": (min_pages, max_pages)}

        # Create downloads directory if it doesn't exist
        self.downloads_dir = Path("downloads/pdfs")
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"ZyteCrawler initialized with downloads directory: {self.downloads_dir}")

    def set_keyword_phrases(self, keyword_phrases: List[str]) -> None:
        """
        Set keyword phrases for document filtering.

        Args:
            keyword_phrases: List of keyword phrases to filter documents
        """
        self.keyword_phrases = keyword_phrases
        self.logger.info(f"Set keyword phrases: {keyword_phrases}")

    def set_size_criteria(self, size_criteria: Dict[str, Tuple[int, int]]) -> None:
        """
        Set size criteria for document categorization and filtering.

        Args:
            size_criteria: Dictionary mapping category names to (min_pages, max_pages) tuples
        """
        self.size_criteria = size_criteria
        self.logger.info(f"Set size criteria: {size_criteria}")

    def get_pdf_urls(self, url: str) -> List[str]:
        """
        Extract all PDF URLs from a given webpage using Zyte API.

        Args:
            url: The webpage URL to extract PDF links from

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
            self.logger.info(f"Fetching HTML content from: {url}")
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
        except Exception as e:
            self.logger.error(f"Unexpected error processing {url}: {e}")

        return []

    def _extract_pdf_urls_from_html(self, html: str, base_url: str) -> List[str]:
        """
        Extract PDF URLs from HTML content using BeautifulSoup.

        Args:
            html: HTML content to parse
            base_url: Base URL for resolving relative links

        Returns:
            List of absolute PDF URLs
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            pdf_urls = []

            # Find all links that might be PDFs
            for link in soup.find_all('a', href=True):
                href = link['href']

                # Check if link points to a PDF
                if href.lower().endswith('.pdf') or 'pdf' in href.lower():
                    # Convert relative URLs to absolute
                    if href.startswith('http'):
                        pdf_urls.append(href)
                    elif href.startswith('/'):
                        from urllib.parse import urljoin
                        pdf_urls.append(urljoin(base_url, href))
                    else:
                        from urllib.parse import urljoin
                        pdf_urls.append(urljoin(base_url, href))

            # Remove duplicates while preserving order
            return list(dict.fromkeys(pdf_urls))

        except Exception as e:
            self.logger.error(f"Error parsing HTML: {e}")
            return []

    def get_pdf_page_count(self, pdf_url: str) -> int:
        """
        Get the number of pages in a PDF file cost-effectively.

        This method uses HTTP range requests to download only the beginning
        of the PDF file to extract page count information efficiently.

        Args:
            pdf_url: URL of the PDF file

        Returns:
            Number of pages in the PDF, or 0 if error occurred
        """
        try:
            self.logger.debug(f"Checking page count for: {pdf_url}")

            # First, try a HEAD request to get file size
            head_response = requests.head(pdf_url, timeout=10)
            if head_response.status_code != 200:
                self.logger.warning(f"HEAD request failed for {pdf_url}: {head_response.status_code}")

            # Download first 1MB to get page count (most PDF metadata is in the beginning)
            headers = {'Range': 'bytes=0-1048576'}  # First 1MB
            response = requests.get(pdf_url, headers=headers, timeout=30)

            if response.status_code in [200, 206]:  # 206 for partial content
                with fitz.open(stream=response.content) as doc:
                    page_count = doc.page_count
                    self.logger.debug(f"PDF {pdf_url} has {page_count} pages")
                    return page_count
            else:
                self.logger.warning(f"Failed to fetch PDF content from {pdf_url}: {response.status_code}")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error fetching {pdf_url}: {e}")
        except Exception as e:
            self.logger.error(f"Error parsing PDF {pdf_url}: {e}")

        return 0

    def categorize_pdf(self, page_count: int) -> str:
        """
        Categorize a PDF by page count.

        Args:
            page_count: Number of pages in the PDF

        Returns:
            Category string based on page count
        """
        if 0 <= page_count <= 18:
            return "0-18"
        elif 19 <= page_count <= 50:
            return "19-50"
        elif 51 <= page_count <= 100:
            return "51-100"
        elif 101 <= page_count <= 150:
            return "101-150"
        elif 151 <= page_count <= 800:
            return "151-800"
        else:
            return "800+"

    def download_pdf(self, pdf_url: str, filename: str) -> bool:
        """
        Download a PDF file to the specified location.

        Args:
            pdf_url: URL of the PDF to download
            filename: Local filename to save the PDF

        Returns:
            True if download successful, False otherwise
        """
        try:
            self.logger.info(f"Downloading PDF: {pdf_url}")
            response = requests.get(pdf_url, timeout=300)  # 5 minute timeout for large files
            response.raise_for_status()

            file_path = self.downloads_dir / filename
            with open(file_path, "wb") as f:
                f.write(response.content)

            self.logger.info(f"Successfully downloaded PDF to: {file_path}")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error downloading {pdf_url}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error downloading {pdf_url}: {e}")

        return False

    def call_codexes_processor(self, pdf_path: str, parameters: Optional[List[str]] = None) -> bool:
        """
        Call codexes processing function with given parameters.

        Args:
            pdf_path: Path to the PDF file to process
            parameters: Optional list of parameters for processing

        Returns:
            True if processing successful, False otherwise
        """
        try:
            if parameters is None:
                parameters = []

            # This is a placeholder for codexes processing integration
            # In practice, this would call the appropriate codexes processing function
            self.logger.info(f"Processing PDF with codexes: {pdf_path}")
            self.logger.info(f"Processing parameters: {parameters}")

            # Example of how this might integrate with existing codexes functionality:
            # from codexes.modules.builders import process_pdf_document
            # result = process_pdf_document(pdf_path, parameters)

            return True

        except Exception as e:
            self.logger.error(f"Error processing PDF {pdf_path}: {e}")
            return False

    def crawl_and_process(
        self,
        urls: List[str],
        min_pages: int = 19,
        max_pages: Optional[int] = None,
        download_pdfs: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        Crawl given URLs, find PDFs, categorize, and optionally download and process them.

        Args:
            urls: List of URLs to crawl
            min_pages: Minimum page count for PDF filtering (default: 19 for >18 pages)
            max_pages: Maximum page count for PDF filtering (default: None for no limit)
            download_pdfs: Whether to download PDFs that meet criteria

        Returns:
            Dictionary with crawl results including found PDFs and their metadata
        """
        today = datetime.date.today().strftime("%Y-%m-%d")
        results = {
            "crawl_date": today,
            "urls_processed": [],
            "pdfs_found": [],
            "pdfs_downloaded": [],
            "errors": []
        }

        self.logger.info(f"Starting crawl of {len(urls)} URLs")
        self.logger.info(f"Filter criteria: min_pages={min_pages}, max_pages={max_pages}")

        for url in urls:
            try:
                self.logger.info(f"Processing URL: {url}")

                # Get PDF URLs from the page
                pdf_urls = self.get_pdf_urls(url)

                # Find new PDFs (not seen in previous crawls)
                new_pdfs = []
                for pdf_url in pdf_urls:
                    if pdf_url not in self.last_crawl_data.get(url, []):
                        new_pdfs.append(pdf_url)

                self.last_crawl_data[url] = pdf_urls
                results["urls_processed"].append({
                    "url": url,
                    "total_pdfs": len(pdf_urls),
                    "new_pdfs": len(new_pdfs)
                })

                # Process each new PDF
                for pdf_url in new_pdfs:
                    try:
                        page_count = self.get_pdf_page_count(pdf_url)
                        category = self.categorize_pdf(page_count)

                        pdf_info = {
                            "url": pdf_url,
                            "page_count": page_count,
                            "category": category,
                            "source_url": url,
                            "meets_criteria": False,
                            "downloaded": False
                        }

                        # Check if PDF meets size criteria
                        meets_criteria = page_count >= min_pages
                        if max_pages is not None:
                            meets_criteria = meets_criteria and page_count <= max_pages

                        pdf_info["meets_criteria"] = meets_criteria

                        if meets_criteria and download_pdfs:
                            # Generate filename
                            filename = self._generate_filename(pdf_url, category, today)

                            # Download PDF
                            if self.download_pdf(pdf_url, filename):
                                pdf_info["downloaded"] = True
                                pdf_info["local_path"] = str(self.downloads_dir / filename)
                                results["pdfs_downloaded"].append(pdf_info.copy())

                                # Process with codexes if downloaded successfully
                                self.call_codexes_processor(
                                    str(self.downloads_dir / filename),
                                    ["extract_metadata", "categorize"]
                                )

                        results["pdfs_found"].append(pdf_info)

                    except Exception as e:
                        error_msg = f"Error processing PDF {pdf_url}: {e}"
                        self.logger.error(error_msg)
                        results["errors"].append(error_msg)

            except Exception as e:
                error_msg = f"Error processing URL {url}: {e}"
                self.logger.error(error_msg)
                results["errors"].append(error_msg)

        # Log summary
        total_found = len(results["pdfs_found"])
        total_downloaded = len(results["pdfs_downloaded"])
        self.logger.info(f"Crawl completed: {total_found} PDFs found, {total_downloaded} downloaded")

        return results

    def _generate_filename(self, pdf_url: str, category: str, date: str) -> str:
        """
        Generate a safe filename for downloaded PDFs.

        Args:
            pdf_url: Original PDF URL
            category: Page count category
            date: Date string

        Returns:
            Safe filename for the PDF
        """
        # Extract original filename from URL
        original_name = os.path.basename(pdf_url)
        if not original_name.endswith('.pdf'):
            original_name += '.pdf'

        # Clean filename for filesystem safety
        safe_name = re.sub(r'[^\w\-_\.]', '_', original_name)

        return f"{date}_{category}_{safe_name}"

    def get_crawl_statistics(self) -> Dict:
        """
        Get statistics about previous crawl operations.

        Returns:
            Dictionary with crawl statistics
        """
        total_urls = len(self.last_crawl_data)
        total_pdfs = sum(len(pdfs) for pdfs in self.last_crawl_data.values())

        return {
            "urls_crawled": total_urls,
            "total_pdfs_found": total_pdfs,
            "downloads_directory": str(self.downloads_dir),
            "keyword_phrases": self.keyword_phrases,
            "size_criteria": self.size_criteria
        }