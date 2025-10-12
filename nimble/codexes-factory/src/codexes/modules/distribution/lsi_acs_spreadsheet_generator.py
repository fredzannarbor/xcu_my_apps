# src/codexes/modules/distribution/lsi_acs_spreadsheet_generator.py
import csv
import logging
from pathlib import Path
from typing import Dict, Any

import pandas as pd

from codexes.modules.metadata.metadata_models import CodexMetadata

logger = logging.getLogger(__name__)


class LsiAcsSpreadsheetGenerator:
    """
    Generates a meticulously formatted CSV file for LSI's ACS system.

    This class handles the complex mapping from a CodexMetadata object to the
    specific columns and codes required by LSI, including looking up codes
    from provided specification files.
    """

    def __init__(self, codes_csv_path: Path, header_csv_path: Path):
        """
        Initializes the generator with necessary LSI specification files.

        Args:
            codes_csv_path: Path to the 'ACS-codes-and-descriptions.csv'.
            header_csv_path: Path to the 'LSI_ACS_header.csv'.
        """
        if not codes_csv_path.exists():
            raise FileNotFoundError(f"LSI codes file not found at: {codes_csv_path}")
        if not header_csv_path.exists():
            raise FileNotFoundError(f"LSI header file not found at: {header_csv_path}")

        # Read the CSV using the second row as the header, which contains the actual column titles.
        # Pandas will automatically handle duplicate column names by appending .1, .2, etc.
        self.codes_df = pd.read_csv(codes_csv_path, header=1, dtype=str)
        self.lsi_headers = self._load_lsi_headers(header_csv_path)

        # Create lookup dictionaries for faster access using the predictable column names
        self.book_type_lookup = self._create_lookup_direct('Description', 'Description')
        self.contributor_role_lookup = self._create_lookup_direct('Description.1', 'Code')
        self.language_lookup = self._create_lookup_direct('Description.2', 'Code.1')
        self.audience_lookup = self._create_lookup_direct('Description.3', 'Code.2')

    @staticmethod
    def _load_lsi_headers(header_path: Path) -> list[str]:
        """Loads the exact header row from the LSI template."""
        with open(header_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            return next(reader)

    def _create_lookup_direct(self, key_col: str, val_col: str) -> Dict[str, Any]:
        """Creates a lookup dictionary directly from the specified columns."""
        try:
            # Drop rows where the key column is NaN
            df_lookup = self.codes_df[[key_col, val_col]].dropna(subset=[key_col])

            # Special handling for contributor roles which have trailing spaces in the description
            if 'Description' in key_col:
                # Use .copy() to avoid SettingWithCopyWarning and ensure we get a Series
                df_lookup = df_lookup.copy()
                df_lookup[key_col] = df_lookup[key_col].str.strip()

            return pd.Series(df_lookup[val_col].values, index=df_lookup[key_col]).to_dict()
        except KeyError as e:
            logger.error(
                f"Failed to create lookup. Column not found: {e}. Available columns: {self.codes_df.columns.tolist()}")
            return {}

    def _map_metadata_to_lsi(self, metadata: CodexMetadata) -> Dict[str, Any]:
        """
        Maps data from a CodexMetadata object to the LSI CSV format.

        This is the core transformation logic. It handles data mapping,
        default values, and code lookups.
        """
        # --- Basic Information ---
        data = {
            "ISBN or SKU": metadata.isbn13,
            "Title": metadata.title,
            "Publisher": metadata.publisher,
            "Imprint": metadata.imprint,
            "Pub Date": metadata.publication_date,
            "Pages": metadata.page_count,
            "Annotation / Summary": metadata.summary_long,
            "Short Description": metadata.summary_short,
            "Keywords": ", ".join(metadata.keywords) if metadata.keywords else "",
            "BISAC Category": metadata.bisac_codes[0] if metadata.bisac_codes else "",
            "BISAC Category 2": metadata.bisac_codes[1] if len(metadata.bisac_codes) > 1 else "",
            "BISAC Category 3": metadata.bisac_codes[2] if len(metadata.bisac_codes) > 2 else "",
            "Thema Subject 1": metadata.thema_subject_1,
            "Series Name": metadata.series_name,
            "# in Series": metadata.series_number,
        }

        # --- Contributor Mapping ---
        if metadata.authors:
            data["Contributor One"] = metadata.authors[0].get("name", "")
            role_desc = metadata.authors[0].get("role", "Author").strip()
            data["Contributor One Role"] = self.contributor_role_lookup.get(role_desc, "A")

        # --- Code Lookups ---
        data["Rendition /Booktype"] = self.book_type_lookup.get(metadata.format, "POD: 6 x 9 in or 229 x 152 mm Perfect Bound WHITE")
        data["Language Code"] = self.language_lookup.get(metadata.language, "ENG")
        data["Audience"] = self.audience_lookup.get(metadata.audience, "01") # Default to General/Trade

        # --- Pricing ---
        data["US Suggested List Price"] = metadata.list_price_usd
        # Add other pricing tiers as needed...

        # --- Defaults for required fields ---
        data["Returnable"] = "Yes"
        data["Territorial Rights"] = "WW" # World Wide

        # Add more complex mappings here...

        return data

    def generate(self, metadata: CodexMetadata, output_path: Path):
        """
        Generates the LSI ACS spreadsheet.

        Args:
            metadata: The populated CodexMetadata object for the book.
            output_path: The path to save the final CSV file.
        """
        logger.info(f"Generating LSI ACS spreadsheet for '{metadata.title}'...")
        mapped_data = self._map_metadata_to_lsi(metadata)

        # Ensure all headers are present, filling missing ones with empty strings
        output_row = {header: mapped_data.get(header, "") for header in self.lsi_headers}

        try:
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.lsi_headers)
                writer.writeheader()
                writer.writerow(output_row)
            logger.info(f"✅ Successfully generated LSI spreadsheet: {output_path}")
        except IOError as e:
            logger.error(f"❌ Failed to write LSI spreadsheet to {output_path}: {e}")
            raise
