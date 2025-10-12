# /Users/fred/xcu_my_apps/nimble/codexes-factory/scripts/rename_lsi_assets.py
# version 1.1
"""
Processes a CSV file from LSI to rename corresponding cover and interior
asset files and update the CSV with the new filenames.

This script performs the following actions:
1. Copies the input CSV to a new file to preserve the original.
2. Iterates through each row of the CSV.
3. For each row, it finds the corresponding cover and interior files based on the book title.
4. It renames these files to a standardized format:
   {isbn}_{safe_basename[:8]}_cover.ext
   {isbn}_{safe_basename[:8]}_interior.ext
5. It updates the 'Cover Path / Filename' and 'Interior Path / Filename' columns
   in the new CSV file.
6. It logs all operations and reports any errors, such as missing files.
"""

import csv
import logging
import re
import shutil
from pathlib import Path
from typing import Optional

# --- Configuration ---
BASE_DIR = Path(__file__).resolve().parent.parent
FTP_DIR = BASE_DIR / "ftp2lsi"
INPUT_CSV = FTP_DIR / "xynapse_traces_tranche1.csv"
OUTPUT_CSV = FTP_DIR / "xynapse_traces_tranche1_processed.csv"
COVERS_DIR = FTP_DIR / "tranche1_covers"
INTERIORS_DIR = FTP_DIR / "tranche1_interior"

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / "scripts" / "rename_lsi_assets.log"),
        logging.StreamHandler()
    ]
)


def create_safe_basename(title: str) -> str:
    """Creates a filesystem-safe, underscore-separated basename from a title string."""
    if not title:
        return ""
    s = title.lower()
    s = re.sub(r'[^a-z0-9]+', '_', s)
    s = re.sub(r'_+', '_', s)
    s = s.strip('_')
    return s


def find_source_file(directory: Path, title: str, file_type: str) -> Optional[Path]:
    """
    Finds a source file in a directory based on the title using robust sanitization.

    It sanitizes the title from the CSV to match common filename conventions
    (e.g., 'AI Governance: Freedom vs. Constraint' becomes 'AI_Governance_Freedom_vs_Constraint').
    Then it searches for a file starting with that sanitized name and file type.
    Example search: 'AI_Governance_Freedom_vs_Constraint_cover*.pdf'
    """
    # Sanitize title to match expected filename format.
    # Replace any character that is not a letter, number, or hyphen with a single underscore.
    sanitized_title = re.sub(r'[^\w-]+', '_', title)
    # Consolidate multiple underscores that might result from the substitution.
    sanitized_title = re.sub(r'_+', '_', sanitized_title)
    # Remove leading/trailing underscores.
    sanitized_title = sanitized_title.strip('_')

    # The search pattern looks for files that start with the sanitized title and file type.
    # e.g., "My_Title_cover" which would match "My_Title_cover.pdf" or "My_Title_cover_spread.pdf"
    search_pattern = f"{sanitized_title}_{file_type}*.*"

    found_files = list(directory.glob(search_pattern))

    if len(found_files) == 1:
        return found_files[0]

    if len(found_files) > 1:
        logging.warning(
            f"Found multiple matches for title '{title}' ({file_type}) with pattern '{search_pattern}'. "
            f"Using first one found: {found_files[0].name}"
        )
        return found_files[0]

    # If we are here, no file was found.
    logging.error(
        f"Could not find a source file for title '{title}' ({file_type}) in {directory} "
        f"using search pattern '{search_pattern}'"
    )
    return None


def process_lsi_assets():
    """Main function to process the CSV and rename files."""
    if not INPUT_CSV.exists():
        logging.error(f"Input file not found: {INPUT_CSV}")
        return

    # Ensure asset directories exist
    COVERS_DIR.mkdir(exist_ok=True)
    INTERIORS_DIR.mkdir(exist_ok=True)

    # Read the original CSV data
    try:
        with open(INPUT_CSV, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            data = list(reader)
            headers = reader.fieldnames
    except Exception as e:
        logging.error(f"Failed to read {INPUT_CSV}: {e}")
        return

    error_count = 0
    success_count = 0
    processed_rows = 0

    for i, row in enumerate(data):
        try:
            title = row.get("Title", "").strip()
            isbn = row.get("ISBN or SKU", "").strip()

            if not title or not isbn:
                logging.warning(f"Skipping row {i + 2} due to missing Title or ISBN.")
                continue

            safe_basename = create_safe_basename(title)

            # Process both cover and interior for the current row
            for file_type, directory, column_name in [
                ("cover", COVERS_DIR, "Cover Path / Filename"),
                ("interior", INTERIORS_DIR, "Interior Path / Filename")
            ]:
                target_basename = f"{isbn}_{safe_basename[:8]}_{file_type}"

                # Check if already processed
                if list(directory.glob(f"{target_basename}.*")):
                    logging.info(f"'{title}' ({file_type}) already processed. Skipping.")
                    # Ensure CSV has the correct name even if we skip the move
                    row[column_name] = list(directory.glob(f"{target_basename}.*"))[0].name
                    continue

                source_file = find_source_file(directory, title, file_type)
                if source_file:
                    new_filename = f"{target_basename}{source_file.suffix}"
                    new_filepath = directory / new_filename
                    shutil.move(str(source_file), str(new_filepath))
                    row[column_name] = new_filename
                    logging.info(f"Renamed {file_type} for '{title}' to {new_filename}")
                else:
                    error_count += 1
                    row[column_name] = "ERROR: FILE NOT FOUND"

            processed_rows += 1
            if "ERROR" not in row.get("Cover Path / Filename", "") and "ERROR" not in row.get(
                    "Interior Path / Filename", ""):
                success_count += 1

        except Exception as e:
            logging.exception(f"An unexpected error occurred processing row for title '{title}': {e}")
            error_count += 1
            row["Cover Path / Filename"] = "ERROR: PROCESSING FAILED"
            row["Interior Path / Filename"] = "ERROR: PROCESSING FAILED"

    # Write the updated data to the new CSV file
    try:
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
    except Exception as e:
        logging.error(f"Failed to write updated data to {OUTPUT_CSV}: {e}")
        return

    logging.info("--- Processing Complete ---")
    logging.info(f"Processed {processed_rows} titles.")
    logging.info(f"Successfully renamed assets for {success_count} titles.")
    if error_count > 0:
        logging.warning(f"Encountered errors for {error_count} assets. Please check the logs and '{OUTPUT_CSV}'.")
    else:
        logging.info("All found assets processed without errors.")


if __name__ == "__main__":
    process_lsi_assets()