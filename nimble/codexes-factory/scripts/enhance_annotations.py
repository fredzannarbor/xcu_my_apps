# /Users/fred/xcu_my_apps/nimble/codexes-factory/scripts/enhance_annotations.py
# version 1.2
"""
Reads the processed LSI CSV file, cleans up the 'Annotation / Summary' column
from HTML to plain text, and enriches it with standardized paragraphs.

This script performs the following actions:
1.  Reads the input CSV file.
2.  Creates a new, separate output CSV file.
3.  For each row:
    a. Converts the HTML content in the 'Annotation / Summary' column to plain text.
    b. Appends a specific string (A) to the end of the first paragraph of the text.
    c. Appends a second, standardized string (B) to the end of the entire text.
4.  Saves the updated data to the new output file.
"""

import csv
import logging
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Required library not found. Please install it by running:")
    print("pip install beautifulsoup4")
    exit(1)

# --- Configuration ---
BASE_DIR = Path(__file__).resolve().parent.parent
FTP_DIR = BASE_DIR / "ftp2lsi"
CSV_DIR = FTP_DIR / "csv"

# Use the 'processed' CSV as input
INPUT_CSV = CSV_DIR / "xynapse_traces_tranche1_processed.csv"
# Create a new file for the output
OUTPUT_CSV = CSV_DIR / "xynapse_traces_tranche1_annotated.csv"

# The strings to be inserted
STRING_A = "This innovative pilsa book--필사, or Korean transcriptive meditation--will stimulate you to think and explore."
STRING_B = "Books in this series feature quotations on the verso page with an industry standard 5-mm dot grid transcription area on the right. Each book includes a Publisher's Note, a Foreword, a Glossary of pilsa terms, a set of Mnemonics, a Verification Log with detailed notes, and a Bibliography. The paper is high-quality 70-lb white."

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)


def enhance_annotations():
    """Main function to process the CSV and enhance annotations."""
    if not INPUT_CSV.exists():
        logging.error(f"❌ Input file not found: {INPUT_CSV}")
        return

    # Read the original CSV data
    try:
        with open(INPUT_CSV, 'r', newline='', encoding='utf-8-sig') as infile:
            reader = csv.DictReader(infile)
            data = list(reader)
            headers = reader.fieldnames
            if not headers:
                logging.error("❌ CSV file is empty or has no headers.")
                return
    except Exception as e:
        logging.error(f"❌ Failed to read {INPUT_CSV}: {e}")
        return

    logging.info(f"✅ Read {len(data)} rows from {INPUT_CSV}.")
    processed_count = 0

    for i, row in enumerate(data):
        title = row.get("Title", f"Row {i+2}")
        annotation_html = row.get("Annotation / Summary", "")

        if not annotation_html:
            logging.warning(f"⚠️ Skipping '{title}': No annotation found.")
            continue

        # 1. Convert all HTML to plain text, handling block and inline tags correctly.
        soup = BeautifulSoup(annotation_html, 'html.parser')

        # Replace <br> tags with newlines to preserve them.
        for br in soup.find_all("br"):
            br.replace_with("\n")

        # Find all paragraph tags. If there are none, treat the whole thing as one block.
        # Otherwise, process each paragraph and join them with double newlines.
        # This ensures block-level separation is respected.
        paragraphs = soup.find_all('p')
        if not paragraphs:
            # No <p> tags found, so treat the whole content as a single block.
            # Use a single space as a separator to handle inline tags like <b> correctly.
            plain_text = soup.get_text(separator=' ', strip=True)
        else:
            # Process each paragraph individually to maintain text flow within them.
            text_blocks = [p.get_text(separator=' ', strip=True) for p in paragraphs]
            # Join the processed paragraphs with double newlines to create the final text.
            plain_text = '\n\n'.join(text_blocks)

        # Split the text into the first paragraph and the rest.
        text_parts = plain_text.split('\n\n', 1)
        first_paragraph = text_parts[0]
        rest_of_text = text_parts[1] if len(text_parts) > 1 else ''

        # 2. Add String A to the end of the first paragraph.
        first_paragraph_enhanced = first_paragraph + " " + STRING_A

        # Reassemble the main body of the text.
        if rest_of_text:
            modified_text = f"{first_paragraph_enhanced}\n\n{rest_of_text}"
        else:
            modified_text = first_paragraph_enhanced

        # 3. Add String B at the end, prefaced by a blank line.
        enhanced_text = f"{modified_text}\n\n{STRING_B}"

        # Update the row with the new, enhanced text
        row["Annotation / Summary"] = enhanced_text
        processed_count += 1

    # Write the updated data to the new CSV file
    try:
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        logging.info(f"✅ Successfully processed {processed_count} rows.")
        logging.info(f"✅ Output saved to: {OUTPUT_CSV}")
    except Exception as e:
        logging.error(f"❌ Failed to write updated data to {OUTPUT_CSV}: {e}")


if __name__ == "__main__":
    enhance_annotations()