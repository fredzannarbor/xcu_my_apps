# src/codexes/modules/distribution/rebuild_catalog.py
# version 1.0.1
import argparse
import json
import logging
from pathlib import Path
import pandas as pd

# Setup logging to provide clear feedback during execution.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the expected columns for the catalog CSV, consistent with the main pipeline.
CATALOG_COLUMNS = [
    'id', 'title', 'subtitle', 'author', 'isbn13', 'series_name',
    'series_number', 'page_count', 'publication_date', 'imprint',
    'back_cover_text', 'storefront_publishers_note_en',
    'front_cover_image_path', 'full_spread_pdf_path', 'interior_pdf_path'
]


def rebuild_catalog(input_dir: Path, output_file: Path):
    """
    Scans a directory of book JSON files and creates a new, clean catalog CSV.

    This function iterates through all .json files in the input directory,
    extracts the relevant data, and compiles it into a single pandas DataFrame.
    It then applies deduplication logic to ensure each book is represented
    only once, prioritizing entries with an ISBN.

    Args:
        input_dir: The directory containing the processed book JSON files.
        output_file: The path where the final catalog CSV will be saved.
    """
    if not input_dir.is_dir():
        logger.error(f"Input directory not found: {input_dir}")
        return

    json_files = list(input_dir.glob("*.json"))
    if not json_files:
        logger.warning(f"No JSON files found in {input_dir}. Catalog will not be created.")
        return

    logger.info(f"Found {len(json_files)} JSON files to process in '{input_dir}'.")

    all_book_data = []
    for json_path in json_files:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # The 'shortuuid' is required as the primary identifier for each book.
            book_id = data.get('shortuuid')
            if not book_id:
                logger.warning(f"Skipping {json_path.name}: missing 'shortuuid'.")
                continue

            # Map JSON data to the defined catalog columns, handling missing keys gracefully.
            row = {col: data.get(col) for col in CATALOG_COLUMNS}
            row['id'] = book_id  # Ensure the 'id' column is correctly set from shortuuid
            all_book_data.append(row)

        except json.JSONDecodeError:
            logger.error(f"Skipping {json_path.name}: could not decode JSON.")
        except Exception as e:
            logger.error(f"Skipping {json_path.name} due to an unexpected error: {e}", exc_info=True)

    if not all_book_data:
        logger.error("No valid book data could be extracted. Catalog will not be created.")
        return

    # Create a DataFrame from all processed books
    full_df = pd.DataFrame(all_book_data)

    # --- Deduplication Logic ---
    logger.info("Deduplicating records to ensure a clean catalog...")

    # FIX: Deduplicate based only on the 'title' column, keeping the last entry found.
    # The previous logic incorrectly treated all empty ISBNs as a single duplicate entry.
    final_df = full_df.drop_duplicates(subset=['title'], keep='last')

    # Ensure the final DataFrame has the correct columns in the specified order
    final_df = final_df.reindex(columns=CATALOG_COLUMNS)

    # Sort the catalog alphabetically by title for consistent output
    final_df.sort_values(by='title', inplace=True)

    # Save the final, clean catalog to the specified output file
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        final_df.to_csv(output_file, index=False)
        logger.info(f"✅ Successfully created new catalog with {len(final_df)} total entries at: {output_file}")
    except Exception as e:
        logger.error(f"Failed to write the final catalog to {output_file}: {e}", exc_info=True)


def main():
    """
    Parses command-line arguments and runs the catalog rebuilding process.
    """
    parser = argparse.ArgumentParser(
        description="Rebuild the book catalog CSV from a directory of JSON files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Directory containing the processed book JSON files (e.g., 'output/imprint_build/processed_json')."
    )
    parser.add_argument(
        "--output-file",
        default="data/books.csv",
        help="Path to save the final catalog CSV file."
    )
    args = parser.parse_args()

    rebuild_catalog(input_dir=Path(args.input_dir), output_file=Path(args.output_file))


if __name__ == "__main__":
    main()
