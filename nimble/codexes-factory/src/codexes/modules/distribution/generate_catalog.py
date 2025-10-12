# src/codexes/modules/distribution/generate_catalog.py
# version 1.2.0
import json
import logging
from pathlib import Path
from typing import List
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)

# Define the expected columns for the catalog CSV.
CATALOG_COLUMNS = [
    'id', 'title', 'subtitle', 'author', 'isbn13', 'series_name',
    'series_number', 'page_count', 'publication_date', 'imprint',
    'back_cover_text', 'storefront_publishers_note_en',
    'front_cover_image_path', 'full_spread_pdf_path', 'interior_pdf_path'
]


def verify_catalog(catalog_path: Path) -> bool:
    """
    Verifies the integrity and validity of a generated catalog CSV file.

    Checks for:
    - Presence of all required columns.
    - Uniqueness and presence of 'id' column.
    - Presence of 'title' column.
    - Validity of 'publication_date' format.

    Args:
        catalog_path: The path to the catalog CSV file to verify.

    Returns:
        True if the catalog is valid, False otherwise.
    """
    if not catalog_path.exists():
        logger.error(f"Verification failed: Catalog file not found at {catalog_path}")
        return False

    logger.info(f"--- Verifying catalog file: {catalog_path} ---")
    is_valid = True
    try:
        df = pd.read_csv(catalog_path)

        # 1. Check for all required columns
        missing_cols = [col for col in CATALOG_COLUMNS if col not in df.columns]
        if missing_cols:
            logger.error(f"Verification failed: Missing required columns: {missing_cols}")
            is_valid = False

        # 2. Check 'id' column for presence and uniqueness
        if 'id' in df.columns:
            if df['id'].isnull().any():
                logger.error("Verification failed: 'id' column contains missing values.")
                is_valid = False
            if df['id'].duplicated().any():
                logger.error("Verification failed: 'id' column contains duplicate values.")
                is_valid = False
        else:
            logger.error("Verification failed: 'id' column is missing.")
            is_valid = False

        # 3. Check 'title' column for presence
        if 'title' in df.columns and df['title'].isnull().any():
            logger.error("Verification failed: 'title' column contains missing values.")
            is_valid = False

        # 4. Check date formats for each row
        for index, row in df.iterrows():
            if 'publication_date' in row and pd.notna(row['publication_date']):
                try:
                    datetime.strptime(str(row['publication_date']), '%Y-%m-%d')
                except (ValueError, TypeError):
                    logger.error(
                        f"Row {index + 2} (ID: {row.get('id')}): Invalid 'publication_date' format: {row['publication_date']}. Expected YYYY-MM-DD.")
                    is_valid = False

        if is_valid:
            logger.info("✅ Catalog verification successful. All checks passed.")
        else:
            logger.error("❌ Catalog verification failed. Please review the errors above.")

        return is_valid

    except Exception as e:
        logger.error(f"An unexpected error occurred during catalog verification: {e}", exc_info=True)
        return False


def create_catalog_from_json(json_files: List[Path], output_file: str):
    """
    Creates a new master CSV catalog from a list of book JSON files and appends to cumulative.csv.

    This function reads data from each specified JSON file, validates it, and creates a new catalog.
    It does not merge with an existing catalog, creating a fresh database instead.
    The existing books.csv is renamed with a timestamp, and the new catalog is saved as books.csv.
    The new catalog is also appended to cumulative.csv.

    Args:
        json_files: A list of Path objects pointing to the JSON files to process.
        output_file: The path to the output CSV catalog file (books.csv).
    """
    # --- Process JSON Files ---
    new_book_data = []
    for json_path in json_files:
        if not json_path.exists():
            logger.warning(f"Skipping non-existent JSON file: {json_path}")
            continue
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Processed {json_path.name} for catalog creation.")

            # Use shortuuid as the primary identifier.
            book_id = data.get('shortuuid')
            if not book_id:
                logger.warning(f"Skipping {json_path.name} as it is missing a 'shortuuid' for the ID.")
                continue

            # Map JSON data to catalog columns
            row = {col: data.get(col) for col in CATALOG_COLUMNS}
            row['id'] = book_id  # Ensure the 'id' column is set from shortuuid
            new_book_data.append(row)

        except json.JSONDecodeError:
            logger.error(f"Could not decode JSON from {json_path}. File may be corrupt.")
        except Exception as e:
            logger.error(f"Failed to process {json_path.name} for catalog: {e}", exc_info=True)

    if not new_book_data:
        logger.error("No valid book data could be processed. Catalog will not be created.")
        return

    # FIX: Create the DataFrame and ensure the 'id' column is preserved by not setting it as the index.
    new_df = pd.DataFrame(new_book_data)

    # Ensure the DataFrame has the correct columns in the correct order
    new_df = new_df.reindex(columns=CATALOG_COLUMNS)

    # Sort for consistent output
    new_df.sort_values(by='title', inplace=True)

    # --- Rename Existing books.csv ---
    output_path = Path(output_file)
    if output_path.exists():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        new_name = output_path.parent / f"{timestamp}_books.csv"
        try:
            output_path.rename(new_name)
            logger.info(f"Renamed existing {output_file} to {new_name}")
        except Exception as e:
            logger.error(f"Failed to rename {output_file} to {new_name}: {e}", exc_info=True)
            return

    # --- Save New Catalog as books.csv ---
    try:
        new_df.to_csv(output_path, index=False)
        logger.info(f"✅ Successfully created new catalog with {len(new_df)} entries at: {output_file}")
    except Exception as e:
        logger.error(f"Failed to write the new catalog to {output_file}: {e}", exc_info=True)
        return

    # --- Append to cumulative.csv ---
    cumulative_path = output_path.parent / 'cumulative.csv'
    try:
        if cumulative_path.exists():
            # Append to existing cumulative.csv without deduplication
            with open(cumulative_path, 'a', encoding='utf-8') as f:
                new_df.to_csv(f, index=False, header=False)
            logger.info(f"Appended {len(new_df)} entries to {cumulative_path}")
        else:
            # Create new cumulative.csv
            new_df.to_csv(cumulative_path, index=False)
            logger.info(f"Created new {cumulative_path} with {len(new_df)} entries")
    except Exception as e:
        logger.error(f"Failed to append to {cumulative_path}: {e}", exc_info=True)

    # --- Verify the newly created catalog ---
    verify_catalog(output_path)
