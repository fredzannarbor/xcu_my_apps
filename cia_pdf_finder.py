#!/usr/bin/env python3
"""
CIA PDF Finder Agent

Scans a directory (default: ~/Downloads) for PDF files and identifies
documents that appear to be from the Central Intelligence Agency (CIA).
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import re
from dataclasses import dataclass
from tqdm import tqdm

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF is required. Install with: pip install PyMuPDF")
    sys.exit(1)


@dataclass
class CIADocument:
    """Represents a potential CIA document with metadata."""
    file_path: Path
    confidence_score: float
    matching_indicators: List[str]
    page_count: int
    file_size_mb: float


class CIAPDFFinder:
    """Agent to find and identify CIA PDF documents."""

    # Indicators that suggest a document is from the CIA
    CIA_INDICATORS = {
        'high_confidence': [
            r'\bCentral Intelligence Agency\b',
            r'\bCIA\b.*\b(Headquarters|Langley)\b',
            r'APPROVED FOR RELEASE.*CIA',
            r'CIA-RDP\d+',  # CIA FOIA document numbers
            r'FOIA.*CIA',
            r'CIA Historical Review Program',
            r'Office of.*Intelligence.*CIA',
        ],
        'medium_confidence': [
            r'\bCIA\b',
            r'\bLangley,?\s*Virginia\b',
            r'\bDirector of Central Intelligence\b',
            r'\bDCI\b',  # Director of Central Intelligence
            r'\bClandestine Service\b',
            r'\bNational Clandestine Service\b',
            r'CLASSIFIED.*CIA',
            r'SECRET.*CIA',
        ],
        'low_confidence': [
            r'\bintelligence\s+community\b',
            r'\bcovert\s+operations?\b',
            r'\bFOIA\s+Request\b',
        ]
    }

    def __init__(self, target_directory: Path = None):
        """Initialize the CIA PDF finder.

        Args:
            target_directory: Directory to search. Defaults to ~/Downloads
        """
        if target_directory is None:
            target_directory = Path.home() / "Downloads"

        self.target_directory = Path(target_directory).expanduser().resolve()

        if not self.target_directory.exists():
            raise ValueError(f"Directory does not exist: {self.target_directory}")

    def find_all_pdfs(self) -> List[Path]:
        """Recursively find all PDF files in the target directory.

        Returns:
            List of Path objects for all PDF files found
        """
        print(f"Scanning {self.target_directory} for PDF files...")
        pdf_files = list(self.target_directory.rglob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files")
        return pdf_files

    def extract_text_from_pdf(self, pdf_path: Path, max_pages: int = 10) -> str:
        """Extract text from a PDF file.

        Args:
            pdf_path: Path to the PDF file
            max_pages: Maximum number of pages to extract (for performance)

        Returns:
            Extracted text as a string
        """
        text = ""
        try:
            doc = fitz.open(pdf_path)
            pages_to_check = min(max_pages, len(doc))

            for page_num in range(pages_to_check):
                page = doc[page_num]
                text += page.get_text()

            doc.close()
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")

        return text

    def analyze_pdf(self, pdf_path: Path) -> Tuple[float, List[str]]:
        """Analyze a PDF to determine if it's a CIA document.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Tuple of (confidence_score, list of matching indicators)
        """
        text = self.extract_text_from_pdf(pdf_path)

        if not text:
            return 0.0, []

        score = 0.0
        matches = []

        # Check high confidence indicators
        for pattern in self.CIA_INDICATORS['high_confidence']:
            if re.search(pattern, text, re.IGNORECASE):
                score += 40.0
                matches.append(f"HIGH: {pattern}")

        # Check medium confidence indicators
        for pattern in self.CIA_INDICATORS['medium_confidence']:
            if re.search(pattern, text, re.IGNORECASE):
                score += 15.0
                matches.append(f"MEDIUM: {pattern}")

        # Check low confidence indicators
        for pattern in self.CIA_INDICATORS['low_confidence']:
            if re.search(pattern, text, re.IGNORECASE):
                score += 5.0
                matches.append(f"LOW: {pattern}")

        # Cap score at 100
        score = min(score, 100.0)

        return score, matches

    def scan_for_cia_documents(self, min_confidence: float = 30.0) -> List[CIADocument]:
        """Scan the target directory for CIA documents.

        Args:
            min_confidence: Minimum confidence score to include in results

        Returns:
            List of CIADocument objects sorted by confidence score
        """
        pdf_files = self.find_all_pdfs()
        cia_documents = []

        print(f"\nAnalyzing PDFs for CIA indicators (min confidence: {min_confidence}%)...")

        for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
            try:
                score, matches = self.analyze_pdf(pdf_path)

                if score >= min_confidence:
                    # Get file metadata
                    file_size_mb = pdf_path.stat().st_size / (1024 * 1024)

                    # Get page count
                    page_count = 0
                    try:
                        doc = fitz.open(pdf_path)
                        page_count = len(doc)
                        doc.close()
                    except:
                        pass

                    cia_doc = CIADocument(
                        file_path=pdf_path,
                        confidence_score=score,
                        matching_indicators=matches,
                        page_count=page_count,
                        file_size_mb=file_size_mb
                    )
                    cia_documents.append(cia_doc)

            except Exception as e:
                print(f"\nError processing {pdf_path}: {e}")

        # Sort by confidence score (highest first)
        cia_documents.sort(key=lambda x: x.confidence_score, reverse=True)

        return cia_documents

    def generate_report(self, documents: List[CIADocument]) -> None:
        """Generate and print a report of CIA documents found.

        Args:
            documents: List of CIADocument objects to report
        """
        print("\n" + "=" * 80)
        print(f"CIA PDF FINDER - RESULTS")
        print("=" * 80)
        print(f"\nFound {len(documents)} potential CIA document(s)\n")

        if not documents:
            print("No CIA documents found matching the criteria.")
            return

        for i, doc in enumerate(documents, 1):
            print(f"\n{i}. {doc.file_path.name}")
            print(f"   Path: {doc.file_path}")
            print(f"   Confidence: {doc.confidence_score:.1f}%")
            print(f"   Pages: {doc.page_count}")
            print(f"   Size: {doc.file_size_mb:.2f} MB")
            print(f"   Indicators matched:")
            for indicator in doc.matching_indicators[:5]:  # Show first 5 matches
                print(f"      • {indicator}")
            if len(doc.matching_indicators) > 5:
                print(f"      ... and {len(doc.matching_indicators) - 5} more")

        print("\n" + "=" * 80)


def main():
    """Main entry point for the CIA PDF Finder."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Find CIA PDF documents in a directory"
    )
    parser.add_argument(
        "--directory",
        "-d",
        type=str,
        help="Directory to search (default: ~/Downloads)",
        default=None
    )
    parser.add_argument(
        "--min-confidence",
        "-c",
        type=float,
        help="Minimum confidence score (0-100, default: 30)",
        default=30.0
    )

    args = parser.parse_args()

    # Create finder instance
    target_dir = Path(args.directory) if args.directory else None
    finder = CIAPDFFinder(target_directory=target_dir)

    print(f"Target directory: {finder.target_directory}")
    print(f"Minimum confidence: {args.min_confidence}%\n")

    # Scan for documents
    documents = finder.scan_for_cia_documents(min_confidence=args.min_confidence)

    # Generate report
    finder.generate_report(documents)


if __name__ == "__main__":
    main()
