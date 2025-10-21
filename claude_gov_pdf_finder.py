#!/usr/bin/env python3
"""
Claude-Powered Government PDF Finder

Uses Claude's agentic capabilities to search for and download recent government PDFs.
This script is meant to be run BY Claude Code, not as a standalone script.
"""

import argparse
from pathlib import Path
from datetime import datetime, timedelta


def main():
    """Main entry point - provides instructions for Claude."""
    parser = argparse.ArgumentParser(
        description="Find and download recent government PDFs using Claude's capabilities"
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

    output_dir = Path(args.output) if args.output else Path.home() / "Downloads" / f"{args.domain}_pdfs"
    output_dir.mkdir(parents=True, exist_ok=True)

    cutoff_date = datetime.now() - timedelta(days=args.days)

    print(f"""
================================================================================
CLAUDE GOVERNMENT PDF FINDER
================================================================================

Domain: {args.domain}
Days back: {args.days}
Cutoff date: {cutoff_date.strftime('%Y-%m-%d')}
Minimum pages: {args.min_pages}
Output directory: {output_dir}

================================================================================
INSTRUCTIONS FOR CLAUDE CODE
================================================================================

Claude, please complete the following steps:

1. Use WebSearch to find recent PDFs from {args.domain}:
   - Search query: "site:{args.domain} filetype:pdf"
   - Look for PDFs posted after {cutoff_date.strftime('%Y-%m-%d')}

2. For each PDF found:
   - Use WebFetch to check if it's accessible
   - Download the PDF to {output_dir}
   - Use PyMuPDF (fitz) to check page count
   - Only keep PDFs with {args.min_pages}+ pages

3. Generate a final report listing:
   - PDF filename
   - URL
   - Page count
   - File size
   - Date discovered

4. Save the report to: {output_dir}/report.txt

Please begin the search now!
================================================================================
""")


if __name__ == "__main__":
    main()
