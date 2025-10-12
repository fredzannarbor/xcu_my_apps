# /Users/fred/xcu_my_apps/nimble/codexes-factory/scripts/validate_lsi_deliverables.py
# version 1.0
"""
Performs a comprehensive validation of LSI deliverables.

This script checks for consistency and integrity across three areas:
1.  Internal consistency of the LSI metadata CSV.
    - Checks for consistent row lengths.
    - Verifies UTF-8 encoding.
    - Reports on languages, pricing, and discount consistency.
    - Performs a sanity check on international prices against USD.

2.  Consistency between the CSV and the contents of the asset directories.
    - Verifies that file counts match the number of CSV rows.
    - Ensures every book in the CSV has corresponding cover/interior files.
    - Ensures every cover/interior file corresponds to a book in the CSV.

3.  Consistency between the CSV metadata and the PDF file contents.
    - Matches the page count in the CSV with the actual PDF page count.
    - Verifies that the book title in the CSV matches the PDF metadata title.
    - Checks if the Table of Contents entries from the CSV are present in the PDF.

The script generates a detailed `validation_report.csv` and logs results to the console.
"""

import csv
import logging
import re
from pathlib import Path
from typing import List, Dict, Any

import fitz  # PyMuPDF
import requests

# --- Configuration ---
BASE_DIR = Path(__file__).resolve().parent.parent
FTP_DIR = BASE_DIR / "ftp2lsi"
# Use the processed CSV as the source of truth
INPUT_CSV = FTP_DIR / "xynapse_traces_tranche1_processed.csv"
COVERS_DIR = FTP_DIR / "tranche1_covers"
INTERIORS_DIR = FTP_DIR / "tranche1_interior"
REPORT_CSV = FTP_DIR / "validation_report.csv"

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / "scripts" / "validation.log"),
        logging.StreamHandler()
    ]
)

# --- Globals ---
currency_cache = {}
validation_results = []


def add_result(isbn: str, title: str, check: str, status: str, message: str):
    """Adds a validation result to the global list."""
    validation_results.append({
        "ISBN": isbn,
        "Title": title,
        "Check": check,
        "Status": status,
        "Message": message
    })


def get_exchange_rates():
    """Fetches and caches exchange rates for USD."""
    global currency_cache
    if currency_cache:
        return currency_cache

    logging.info("Fetching latest currency exchange rates from API...")
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        response.raise_for_status()
        currency_cache = response.json().get("rates", {})
        logging.info("Successfully fetched exchange rates.")
        return currency_cache
    except requests.exceptions.RequestException as e:
        logging.error(f"Could not fetch currency exchange rates: {e}")
        return None


def check_csv_internal_consistency(data: List[Dict[str, str]], headers: List[str]):
    """Performs all internal consistency checks on the CSV data."""
    logging.info("--- Starting Internal CSV Consistency Checks ---")
    header_count = len(headers)
    all_languages = set()
    rates = get_exchange_rates()

    # Find price and discount columns dynamically
    gc_price_cols = [h for h in headers if "GC Suggested List Price" in h]
    discount_cols = [h for h in headers if "Wholesale Discount" in h]

    for i, row in enumerate(data):
        isbn = row.get("ISBN or SKU", f"ROW_{i + 2}")
        title = row.get("Title", "N/A")

        # 1. Row length consistency
        if len(row) != header_count:
            add_result(isbn, title, "CSV Row Length", "FAIL", f"Row has {len(row)} cells, header has {header_count}.")
        else:
            add_result(isbn, title, "CSV Row Length", "OK", f"Row has {header_count} cells.")

        # 2. Report languages
        lang = row.get("Language Code")
        if lang:
            all_languages.add(lang)

        # 3. GC Market prices
        gc_prices = {row.get(col) for col in gc_price_cols if row.get(col)}
        if len(gc_prices) > 1:
            add_result(isbn, title, "GC Price Consistency", "FAIL", f"Multiple different GC prices found: {gc_prices}")
        else:
            add_result(isbn, title, "GC Price Consistency", "OK",
                       f"GC prices are consistent: {gc_prices.pop() if gc_prices else 'N/A'}")

        # 4. Discount consistency
        discounts = {row.get(col) for col in discount_cols if row.get(col)}
        if len(discounts) > 1:
            add_result(isbn, title, "Discount Consistency", "FAIL", f"Multiple different discounts found: {discounts}")
        else:
            add_result(isbn, title, "Discount Consistency", "OK",
                       f"Discounts are consistent: {discounts.pop() if discounts else 'N/A'}")

        # 5. Price sanity check
        if rates:
            try:
                usd_price = float(row.get("US Suggested List Price"))
                # Check EUR, GBP, AUD, CAD
                for currency, col_name, rate in [
                    ("EUR", "EU Suggested List Price (mode 2)", rates.get("EUR")),
                    ("GBP", "UK Suggested List Price", rates.get("GBP")),
                    ("AUD", "AU Suggested List Price (mode 2)", rates.get("AUD")),
                    ("CAD", "CA Suggested List Price (mode 2)", rates.get("CAD")),
                ]:
                    if not rate:
                        continue

                    local_price_str = row.get(col_name)
                    if not local_price_str:
                        add_result(isbn, title, f"{currency} Price Sanity", "WARN", f"No price found for {currency}.")
                        continue

                    local_price = float(local_price_str)
                    converted_price = usd_price * rate
                    lower_bound = converted_price * 1.00
                    upper_bound = converted_price * 1.20

                    if not (lower_bound <= local_price <= upper_bound):
                        msg = (f"Price {local_price} {currency} is outside expected range. "
                               f"USD price {usd_price} converts to ~{converted_price:.2f} {currency}. "
                               f"Expected range: {lower_bound:.2f}-{upper_bound:.2f}.")
                        add_result(isbn, title, f"{currency} Price Sanity", "FAIL", msg)
                    else:
                        add_result(isbn, title, f"{currency} Price Sanity", "OK",
                                   f"Price {local_price} {currency} is within expected range.")
            except (ValueError, TypeError):
                add_result(isbn, title, "Price Sanity Check", "FAIL", "Could not parse USD price to float.")

    logging.info(f"CSV contains the following languages: {', '.join(sorted(list(all_languages)))}")
    logging.info("--- Finished Internal CSV Consistency Checks ---")


def check_filesystem_consistency(data: List[Dict[str, str]]):
    """Checks for consistency between CSV data and files on disk."""
    logging.info("--- Starting Filesystem Consistency Checks ---")

    csv_rows = len(data)
    cover_files = list(COVERS_DIR.glob("*.*"))
    interior_files = list(INTERIORS_DIR.glob("*.*"))

    # 1. File counts
    if csv_rows == len(cover_files):
        logging.info(f"[OK] CSV row count ({csv_rows}) matches cover file count ({len(cover_files)}).")
    else:
        logging.error(f"[FAIL] CSV row count ({csv_rows}) does not match cover file count ({len(cover_files)}).")

    if csv_rows == len(interior_files):
        logging.info(f"[OK] CSV row count ({csv_rows}) matches interior file count ({len(interior_files)}).")
    else:
        logging.error(f"[FAIL] CSV row count ({csv_rows}) does not match interior file count ({len(interior_files)}).")

    # 2. Check CSV against filesystem
    csv_covers = {row.get("Cover Path / Filename") for row in data if row.get("Cover Path / Filename")}
    csv_interiors = {row.get("Interior Path / Filename") for row in data if row.get("Interior Path / Filename")}

    for row in data:
        isbn = row.get("ISBN or SKU")
        title = row.get("Title")
        cover_path = row.get("Cover Path / Filename")
        interior_path = row.get("Interior Path / Filename")

        if not (COVERS_DIR / cover_path).exists():
            add_result(isbn, title, "Cover File Exists", "FAIL",
                       f"File '{cover_path}' listed in CSV not found in {COVERS_DIR}.")
        else:
            add_result(isbn, title, "Cover File Exists", "OK", f"File '{cover_path}' found.")

        if not (INTERIORS_DIR / interior_path).exists():
            add_result(isbn, title, "Interior File Exists", "FAIL",
                       f"File '{interior_path}' listed in CSV not found in {INTERIORS_DIR}.")
        else:
            add_result(isbn, title, "Interior File Exists", "OK", f"File '{interior_path}' found.")

    # 3. Check filesystem against CSV
    for f in cover_files:
        if f.name not in csv_covers:
            logging.warning(f"[WARN] Cover file '{f.name}' exists on disk but is not found in the CSV.")
    for f in interior_files:
        if f.name not in csv_interiors:
            logging.warning(f"[WARN] Interior file '{f.name}' exists on disk but is not found in the CSV.")

    logging.info("--- Finished Filesystem Consistency Checks ---")


def _normalize_for_comparison(text: str) -> str:
    """Prepares text for robust substring checking by lowercasing and standardizing punctuation."""
    # Lowercase and replace common typographic variants with standard ASCII
    return text.lower().replace("’", "'").replace("“", '"').replace("”", '"')


def check_pdf_content_consistency(data: List[Dict[str, str]]):
    """Checks consistency between CSV metadata and PDF file content."""
    logging.info("--- Starting PDF Content Consistency Checks ---")

    for row in data:
        isbn = row.get("ISBN or SKU")
        title = row.get("Title")
        interior_filename = row.get("Interior Path / Filename")
        pdf_path = INTERIORS_DIR / interior_filename

        if not pdf_path.exists():
            logging.error(f"Skipping content check for '{title}': Interior PDF not found.")
            continue

        try:
            doc = fitz.open(pdf_path)

            # 1. Page count
            csv_pages = int(row.get("Pages", 0))
            pdf_pages = doc.page_count
            if csv_pages == pdf_pages:
                add_result(isbn, title, "Page Count", "OK", f"CSV and PDF both have {pdf_pages} pages.")
            else:
                add_result(isbn, title, "Page Count", "FAIL", f"CSV has {csv_pages} pages, PDF has {pdf_pages} pages.")

            # 2. Title
            csv_title = title
            pdf_title = doc.metadata.get("title", "")
            if csv_title.strip().lower() == pdf_title.strip().lower():
                add_result(isbn, title, "PDF Title", "OK", f"Title matches: '{csv_title}'")
            else:
                add_result(isbn, title, "PDF Title", "FAIL",
                           f"CSV title: '{csv_title}', PDF metadata title: '{pdf_title}'")

            # 3. Table of Contents
            toc_str = row.get("Table of Contents", "")
            if toc_str:
                toc_items = [item.strip() for item in toc_str.split('\n') if item.strip()]

                # Extract all text for searching
                full_text = "".join(page.get_text() for page in doc)
                normalized_full_text = _normalize_for_comparison(full_text)

                missing_items = []
                for item in toc_items:
                    # A simple check. More complex checks could look for font size/style.
                    if _normalize_for_comparison(item) not in normalized_full_text:
                        missing_items.append(item)

                if not missing_items:
                    add_result(isbn, title, "TOC Check", "OK", f"All {len(toc_items)} TOC items found in PDF.")
                else:
                    add_result(isbn, title, "TOC Check", "FAIL",
                               f"Missing {len(missing_items)} TOC items: {', '.join(missing_items)}")
            else:
                add_result(isbn, title, "TOC Check", "WARN", "No Table of Contents data in CSV to check.")

            doc.close()

            # 4. Field size limits.
            # Annotation Summary < 4000 bytes
            # Keywords < 500 characters, separated by semi-colons
            

        except Exception as e:
            logging.exception(f"Failed to process PDF for '{title}': {e}")
            add_result(isbn, title, "PDF Processing", "FAIL", f"Error processing PDF: {e}")

    logging.info("--- Finished PDF Content Consistency Checks ---")


def write_report_csv():
    """Writes the collected validation results to a CSV file."""
    if not validation_results:
        logging.warning("No validation results to write to report.")
        return

    try:
        with open(REPORT_CSV, 'w', newline='', encoding='utf-8') as outfile:
            headers = ["ISBN", "Title", "Check", "Status", "Message"]
            writer = csv.DictWriter(outfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(validation_results)
        logging.info(f"Successfully wrote validation report to {REPORT_CSV}")
    except Exception as e:
        logging.error(f"Failed to write report CSV: {e}")


def main():
    """Main function to run all validation checks."""
    logging.info(f"Starting validation for deliverables in {FTP_DIR}")

    if not INPUT_CSV.exists():
        logging.error(f"Input CSV not found: {INPUT_CSV}")
        return

    # 1. Read CSV data
    try:
        # Use utf-8-sig to handle potential BOM (Byte Order Mark)
        with open(INPUT_CSV, 'r', newline='', encoding='utf-8-sig') as infile:
            reader = csv.DictReader(infile)
            data = list(reader)
            headers = reader.fieldnames
            if not data:
                logging.error("CSV file is empty.")
                return
            logging.info(f"Successfully read {len(data)} rows from {INPUT_CSV}.")
    except UnicodeDecodeError:
        logging.error(f"CSV file {INPUT_CSV} is not in UTF-8 format. Please save it as UTF-8 and try again.")
        add_result("N/A", "N/A", "CSV Encoding", "FAIL", "File is not UTF-8 encoded.")
        write_report_csv()
        return
    except Exception as e:
        logging.error(f"Failed to read {INPUT_CSV}: {e}")
        return

    # 2. Run checks
    check_csv_internal_consistency(data, headers)
    check_filesystem_consistency(data)
    check_pdf_content_consistency(data)

    # 3. Final reporting
    write_report_csv()

    # Summarize results to stdout
    failures = [r for r in validation_results if r["Status"] == "FAIL"]
    warnings = [r for r in validation_results if r["Status"] == "WARN"]

    logging.info("--- Validation Summary ---")
    if not failures and not warnings:
        logging.info("✅ All checks passed successfully!")
    else:
        logging.warning(f"Found {len(failures)} failures and {len(warnings)} warnings.")
        logging.warning("Please review the console logs and the detailed report in validation_report.csv")

    logging.info("--- Validation Complete ---")


if __name__ == "__main__":
    # Ensure required libraries are installed
    try:
        import fitz
        import requests
    except ImportError:
        print("Required libraries not found. Please install them by running:")
        print("pip install PyMuPDF requests")
    else:
        main()