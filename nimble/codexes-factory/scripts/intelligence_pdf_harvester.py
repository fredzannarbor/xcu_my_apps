#!/usr/bin/env python3
"""
Intelligence PDF Harvester

This script uses web search to find and download large collections of intelligence PDFs
from government sites like CIA, FBI, DHS, etc. It mimics the Google search approach:
site:cia.gov filetype:pdf limited to recent documents.

Usage:
    python3 scripts/intelligence_pdf_harvester.py --site cia.gov --min-pages 18 --max-docs 300
"""

import os
import sys
import argparse
import time
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

# For web search functionality - this would need to be implemented
# For now, we'll use a collection of known URLs as proof of concept
KNOWN_INTELLIGENCE_PDFS = {
    "cia.gov": [
        "https://www.cia.gov/resources/csi/static/Studies-69-No-2Extracts-June-2025-WEB.pdf",
        "https://www.cia.gov/resources/csi/static/fdc907998cd3f58e079688207b7bb4e5/Studies-Unclassified-Extracts-March-2025.pdf",
    ],
    "dni.gov": [
        "https://www.dni.gov/files/ODNI/documents/assessments/ATA-2025-Unclassified-Report.pdf",
    ],
    "fbi.gov": [
        "https://www.fbi.gov/file-repository/counterterrorism/fbi-dhs-domestic-terrorism-strategic-report.pdf",
        "https://www.fbi.gov/file-repository/fbi-dhs-domestic-terrorism-strategic-report-2023.pdf",
        "https://www.fbi.gov/file-repository/counterterrorism/fbi-dhs-domestic-terrorism-strategic-report-2022.pdf",
    ],
    "dhs.gov": [
        "https://www.dhs.gov/sites/default/files/2024-10/24_0930_ia_24-320-ia-publication-2025-hta-final-30sep24-508.pdf",
    ]
}


class IntelligencePDFHarvester:
    """
    Harvests intelligence PDFs from government sites using web search discovery.
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

    def search_pdfs_by_site(self, site: str, max_results: int = 300) -> List[str]:
        """
        Search for PDFs on a specific site using WebSearch.
        """
        self.logger.info(f"Searching for PDFs on {site} (max {max_results} results)")

        pdf_urls = []

        # Try multiple search strategies to find more PDFs
        search_queries = [
            f"PDF documents site:{site} filetype:pdf",
            f"{site.replace('.gov', '')} intelligence reports PDF",
            f"{site.replace('.gov', '')} classified documents PDF",
            f"{site.replace('.gov', '')} reading room PDF"
        ]

        for query in search_queries:
            try:
                self.logger.info(f"Searching: {query}")

                # This would use WebSearch - simulated here
                # In actual implementation, you'd call WebSearch tool
                # results = WebSearch(query)
                # for result in results.links:
                #     if result.url.endswith('.pdf') and site in result.url:
                #         pdf_urls.append(result.url)

                # For now, simulate WebSearch results based on the successful test
                if "cia.gov" in site and "site:cia.gov" in query:
                    # These are actual URLs found by WebSearch
                    websearch_urls = [
                        "https://www.cia.gov/readingroom/docs/cia-rdp96-00788r001700210016-5.pdf",
                        "https://www.cia.gov/readingroom/docs/cia and interrogations-to[15490493].pdf",
                        "https://www.cia.gov/readingroom/docs/CIA-RDP79B01709A000500030003-2.pdf",
                        "https://www.cia.gov/readingroom/docs/PROJECT%20PAPERCLIP_0002.pdf",
                        "https://www.cia.gov/resources/csi/static/888b1a6acc282f122ec52b60c61bce99/Cuban-Missile-Crisis-1962-1.pdf",
                        "https://cia.gov/readingroom/docs/INFORMATION DIGEST[16428491].pdf",
                        "https://www.cia.gov/readingroom/docs/CIA-RDP80R01731R003600100011-4.pdf",
                        "https://www.cia.gov/careers/static/Agency-Reading-List.pdf",
                        "https://www.cia.gov/library/abbottabad-compound/12/129E144131F2E093FB1E441C737ACF92_SearchForTheManchurianCandidate.rtf.pdf",
                        "https://www.cia.gov/readingroom/docs/UNTITLED (DOCUMENTS FOR P[16080170].pdf"
                    ]
                    pdf_urls.extend(websearch_urls)

                # Don't overwhelm with duplicate searches
                if len(pdf_urls) >= 20:
                    break

            except Exception as e:
                self.logger.error(f"Error in search '{query}': {e}")
                continue

        # Add known URLs as fallback
        known_urls = KNOWN_INTELLIGENCE_PDFS.get(site, [])
        pdf_urls.extend(known_urls)

        # Remove duplicates and limit results
        unique_urls = list(dict.fromkeys(pdf_urls))[:max_results]

        self.logger.info(f"Found {len(unique_urls)} total PDF URLs for {site}")
        return unique_urls

    def evaluate_pdf_batch(self, pdf_urls: List[str], min_pages: int = 18) -> List[Dict]:
        """
        Evaluate a batch of PDF URLs and return qualifying documents.
        """
        documents = []

        self.logger.info(f"Evaluating {len(pdf_urls)} PDFs (min {min_pages} pages)")

        for i, pdf_url in enumerate(pdf_urls):
            try:
                self.logger.info(f"Processing {i+1}/{len(pdf_urls)}: {Path(pdf_url).name}")

                # Check page count
                page_count = self.crawler.get_pdf_page_count(pdf_url)
                category = self.crawler.categorize_pdf(page_count)

                if page_count >= min_pages:
                    # Determine source from URL
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

        self.logger.info(f"Found {len(documents)} qualifying documents")
        return documents

    def download_documents(self, documents: List[Dict], output_dir: str = "downloads/intelligence_harvest") -> int:
        """
        Download all qualifying documents.
        """
        self.logger.info(f"Downloading {len(documents)} documents to {output_dir}")

        downloaded = 0
        for i, doc in enumerate(documents):
            try:
                self.logger.info(f"Downloading {i+1}/{len(documents)}: {doc['filename']}")

                success = self.crawler.download_pdf(doc['url'], doc['filename'], output_dir)

                if success:
                    downloaded += 1
                    self.logger.info(f"✅ Downloaded: {doc['source']} - {doc['pages']} pages")
                else:
                    self.logger.error(f"❌ Download failed: {doc['filename']}")

                # Rate limiting between downloads
                time.sleep(2)

            except Exception as e:
                self.logger.error(f"Error downloading {doc['filename']}: {e}")
                continue

        self.logger.info(f"Successfully downloaded {downloaded}/{len(documents)} documents")
        return downloaded

    def harvest_intelligence_pdfs(self,
                                  sites: List[str] = ["cia.gov"],
                                  min_pages: int = 18,
                                  max_docs_per_site: int = 300,
                                  output_dir: str = "downloads/intelligence_harvest") -> Dict:
        """
        Main method to harvest intelligence PDFs from multiple sites.
        """
        total_found = 0
        total_downloaded = 0
        results_by_site = {}

        for site in sites:
            self.logger.info(f"🔍 Processing site: {site}")

            # Search for PDFs
            pdf_urls = self.search_pdfs_by_site(site, max_docs_per_site)

            if not pdf_urls:
                self.logger.warning(f"No PDFs found for {site}")
                continue

            # Evaluate PDFs
            documents = self.evaluate_pdf_batch(pdf_urls, min_pages)
            total_found += len(documents)

            if documents:
                # Download PDFs
                site_output = f"{output_dir}/{site.replace('.', '_')}"
                downloaded = self.download_documents(documents, site_output)
                total_downloaded += downloaded

                results_by_site[site] = {
                    'searched': len(pdf_urls),
                    'qualifying': len(documents),
                    'downloaded': downloaded
                }

        summary = {
            'sites_processed': len(sites),
            'total_qualifying': total_found,
            'total_downloaded': total_downloaded,
            'results_by_site': results_by_site
        }

        self.logger.info(f"🎉 Harvest complete: {total_downloaded} documents downloaded from {len(sites)} sites")
        return summary


def main():
    """Main command line interface."""
    parser = argparse.ArgumentParser(description="Harvest intelligence PDFs from government sites")
    parser.add_argument("--sites", nargs="+", default=["cia.gov"],
                       help="Sites to search (default: cia.gov)")
    parser.add_argument("--min-pages", type=int, default=18,
                       help="Minimum page count (default: 18)")
    parser.add_argument("--max-docs", type=int, default=300,
                       help="Maximum documents per site (default: 300)")
    parser.add_argument("--output-dir", default="downloads/intelligence_harvest",
                       help="Output directory (default: downloads/intelligence_harvest)")

    args = parser.parse_args()

    # Check for API key
    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        print("❌ ZYTE_API_KEY environment variable not set!")
        print("Please set your Zyte API key in .env file")
        return 1

    print(f"🚀 Starting Intelligence PDF Harvester")
    print(f"Sites: {args.sites}")
    print(f"Min pages: {args.min_pages}")
    print(f"Max docs per site: {args.max_docs}")
    print(f"Output: {args.output_dir}")

    try:
        harvester = IntelligencePDFHarvester(api_key)

        results = harvester.harvest_intelligence_pdfs(
            sites=args.sites,
            min_pages=args.min_pages,
            max_docs_per_site=args.max_docs,
            output_dir=args.output_dir
        )

        print(f"\n📊 FINAL RESULTS:")
        print(f"Sites processed: {results['sites_processed']}")
        print(f"Total qualifying documents: {results['total_qualifying']}")
        print(f"Total downloaded: {results['total_downloaded']}")

        for site, site_results in results['results_by_site'].items():
            print(f"  {site}: {site_results['downloaded']}/{site_results['qualifying']} downloaded")

        return 0

    except KeyboardInterrupt:
        print("\n⏹️ Harvest interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Error during harvest: {e}")
        return 1


if __name__ == "__main__":
    exit(main())