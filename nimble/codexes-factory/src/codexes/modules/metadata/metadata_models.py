# src/codexes/modules/metadata/metadata_models.py

import uuid
import json
import os
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime

logging.getLogger("pydantic").setLevel(logging.ERROR)


@dataclass
class CodexMetadata:
    """
    A data class to hold all bibliographic and generative metadata for a single volume.
    Serves as a single source of truth during processing.
    """
    # --- Core Identifiers ---
    filepath: str = ""
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    shortuuid: str = field(init=False)

    # --- Basic Publication Information ---
    title: str = ""
    subtitle: str = ""
    author: str = "AI Lab for Book-Lovers"
    publisher: str = "Nimble Books LLC"
    imprint: str = "Nimble Books LLC"
    publication_date: str = "" # YYYY-MM-DD, should be tuesday
    language: str = "English"
    format: str = "Paperback"
    country_of_origin: str = "US"
    audience: str = "General"

    # --- Content Descriptions ---
    summary_short: str = ""  # Maps to Short Description
    summary_long: str = ""
    annotation_summary: str = ""  # Enhanced HTML-formatted annotation for LSI
    keywords: str = ""  # Should be a semicolon-separated string
    table_of_contents: str = ""  # Maps to Table of Contents
    review_quotes: str = ""  # Maps to Review Quote(s)

    # --- Classification Codes ---
    bisac_codes: str = ""  # Semicolon-separated string
    bisac_text: str = ""  # Maps to BISAC_Text
    bic_codes: str = ""  # Semicolon-separated string
    thema_codes: str = ""  # Semicolon-separated string
    thema_subject_1: str = ""
    thema_subject_2: str = ""
    thema_subject_3: str = ""
    regional_subjects: str = ""

    # --- Age/Grade Information ---
    min_age: str = ""
    max_age: str = ""
    min_grade: str = ""
    max_grade: str = ""

    # --- Contributors ---
    contributor_one: str = ""
    contributor_one_role: str = "Author"
    contributor_two: str = ""
    contributor_two_role: str = ""
    contributor_three: str = ""
    contributor_three_role: str = ""

    # --- Series Information ---
    series_name: str = ""
    series_number: str = ""
    volume_number: str = ""
    edition_statement: str = ""

    # --- ISBNs ---
    isbn13: str = ""
    isbn10: str = ""

    # --- Interior Illustrations ---
    illustration_count: str = "0"  # Maps to # Illustrations
    illustration_notes: str = ""

    # --- Physical Properties ---
    page_count: int = 0
    word_count: int = 0
    trim_size: str = "6 x 9"  # Standard paperback size
    trim_width_in: float = 6.0  # Add this
    trim_height_in: float = 9.0  # Add this
    spine_width_in: float = 0.0  # Add this, will be calculated later
    cover_type: str = "Paperback"
    interior_color: str = "Black & White"
    interior_paper: str = "Cream"
    binding: str = "Perfect Bound"
    cover_image_path: str = ""  # Add this
    cover_thumbnail_path: str = ""  # Add this

    # --- Shipping Information ---
    carton_quantity: str = "1"
    carton_weight: str = "1.0"
    carton_length: str = "8.5"
    carton_width: str = "5.5"
    carton_height: str = "1.0"

    # --- Distribution Settings ---
    availability: str = "Available"
    discount_code: str = "STD"
    tax_code: str = "Standard"
    returns_allowed: str = "Yes"

    # --- Pricing - US and Primary Markets ---
    list_price_usd: float = 19.95
    us_suggested_list_price: str = ""  # Calculated from list_price_usd
    us_wholesale_discount: str = "40%" # default short discount

    # --- International Pricing ---
    uk_suggested_list_price: str = ""
    uk_wholesale_discount_percent: str = "40%"

    eu_suggested_list_price_mode2: str = ""
    eu_wholesale_discount_percent_mode2: str = "40%"

    au_suggested_list_price_mode2: str = ""
    au_wholesale_discount_percent_mode2: str = "40%"

    ca_suggested_list_price_mode2: str = ""
    ca_wholesale_discount_percent_mode2: str = "40%"

    gc_suggested_list_price_mode2: str = ""
    gc_wholesale_discount_percent_mode2: str = "40%"

    # --- Regional Pricing (USBR1, USDE1, etc.) ---
    usbr1_suggested_list_price_mode2: str = ""
    usbr1_wholesale_discount_percent_mode2: str = "40%"

    usde1_suggested_list_price_mode2: str = ""
    usde1_wholesale_discount_percent_mode2: str = "40%"

    usru1_suggested_list_price_mode2: str = ""
    usru1_wholesale_discount_percent_mode2: str = "40%"

    uspl1_suggested_list_price_mode2: str = ""
    uspl1_wholesale_discount_percent_mode2: str = "40%"

    uskr1_suggested_list_price_mode2: str = ""
    uskr1_wholesale_discount_percent_mode2: str = "40%"

    uscn1_suggested_list_price_mode2: str = ""
    uscn1_wholesale_discount_percent_mode2: str = "40%"

    usin1_suggested_list_price_mode2: str = ""
    usin1_wholesale_discount_percent_mode2: str = "40%"

    usjp2_suggested_list_price_mode2: str = ""
    usjp2_wholesale_discount_percent_mode2: str = "40%"

    uaeusd_suggested_list_price_mode2: str = ""
    uaeusd_wholesale_discount_percent_mode2: str = "40%"

    # --- Special Distribution Channels ---
    us_ingram_only_suggested_list_price_mode2: str = ""
    us_ingram_only_wholesale_discount_percent_mode2: str = "40%"

    us_ingram_gap_suggested_list_price_mode2: str = ""
    us_ingram_gap_wholesale_discount_percent_mode2: str = "40%"

    sibi_educ_us_suggested_list_price_mode2: str = ""
    sibi_educ_us_wholesale_discount_percent_mode2: str = "40%"

    # --- Storefront ---
    storefront_title_en: str = ""
    storefront_author_en: str = ""
    storefront_description_en: str = ""
    storefront_publishers_note_en: str = ""
    storefront_title_ko: str = ""
    storefront_author_ko: str = ""
    storefront_description_ko: str = ""
    storefront_publishers_note_ko: str = ""


    # --- Copyright Information ---
    copyright_year: str = datetime.now().year
    copyright_holder: str = "Nimble Books LLC"


    # --- LSI Account and Submission Information ---
    lightning_source_account: str = ""
    metadata_contact_dictionary: Dict[str, Any] = field(default_factory=dict)
    parent_isbn: str = ""
    cover_submission_method: str = "FTP"  # FTP, Email, Portal
    text_block_submission_method: str = "FTP"

    # --- Enhanced Contributor Information ---
    contributor_one_bio: str = ""
    contributor_one_affiliations: str = ""
    contributor_one_professional_position: str = ""
    contributor_one_location: str = ""
    contributor_one_location_type_code: str = ""  # lookup table
    contributor_one_prior_work: str = ""

    # --- Physical Specifications ---
    weight_lbs: str = ""  # calculate
    carton_pack_quantity: str = "1"

    # --- Publication Timing ---
    street_date: str = ""  # Different from pub_date

    # --- Territorial Rights ---
    territorial_rights: str = "World"  # default. Alternatives should be validated against lookup table.

    # --- Edition Information ---
    edition_number: str = ""
    edition_description: str = ""

    # --- File Paths for Submission ---
    jacket_path_filename: str = ""
    interior_path_filename: str = ""
    cover_path_filename: str = ""

    # --- Special LSI Fields ---
    lsi_special_category: str = ""
    stamped_text_left: str = ""
    stamped_text_center: str = ""
    stamped_text_right: str = ""
    order_type_eligibility: str = ""

    # --- LSI Flex Fields (5 configurable fields) ---
    lsi_flexfield1: str = ""
    lsi_flexfield2: str = ""
    lsi_flexfield3: str = ""
    lsi_flexfield4: str = ""
    lsi_flexfield5: str = ""

    # --- Publisher Reference ---
    publisher_reference_id: str = ""  # safe folder name for digital artifacts

    # --- Marketing ---
    marketing_image: str = ""  # path to artifact created during production

    # --- File and System Properties ---
    source_file_basename: str = ""
    text_extractableness: bool = False
    processing_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # --- Raw LLM responses for debugging ---
    raw_llm_responses: Dict[str, Any] = field(default_factory=dict)
    llm_completions: Dict[str, Any] = field(default_factory=dict)
    stream: Optional[str] = None  # Book topic/subject area

    def __post_init__(self):
        # Generate shortuuid after the main init
        self.shortuuid = self.uuid[:8]
        # Default contributor_one to author if not provided
        if not self.contributor_one and self.author:
            self.contributor_one = self.author
        # Set US suggested list price from calculated USD price
        if self.list_price_usd > 0 and not self.us_suggested_list_price:
            self.us_suggested_list_price = f"${self.list_price_usd:.2f}"

    def update_from_dict(self, data: Dict[str, Any]):
        """
        Updates attributes from a dictionary, typically the content of an LLM response.
        This method is flexible to handle various keys from different prompts.
        """
        if not isinstance(data, dict):
            logging.warning(f"Attempted to update metadata with non-dict data: {type(data)}")
            return

        for key, value in data.items():
            # Sanitize keys that might come from LLMs (e.g., 'gemini_title' -> 'title')
            sanitized_key = key.strip().lower().replace('-', '_')
            if 'gemini_' in sanitized_key:
                sanitized_key = sanitized_key.replace('gemini_', '')
            if 'bibliographic_key_phrases' in sanitized_key:
                sanitized_key = 'keywords'  # Remap this specific key

            if hasattr(self, sanitized_key):
                # Special handling for lists, join them into a string
                if isinstance(value, list):
                    setattr(self, sanitized_key, "; ".join(map(str, value)))
                else:
                    setattr(self, sanitized_key, value)
                logging.debug(f"Set metadata attribute '{sanitized_key}'")
            else:
                logging.warning(f"Metadata object has no attribute '{sanitized_key}'. It will be ignored.")

    def to_dict(self) -> Dict[str, Any]:
        """Converts the dataclass to a dictionary."""
        return asdict(self)

    def to_json(self, indent=4) -> str:
        """Serializes the object to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save_to_file(self, file_path: str):
        """Saves the metadata object to a JSON file."""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
            logging.info(f"Metadata object saved to {file_path}")
        except Exception as e:
            logging.error(f"Failed to save metadata to {file_path}: {e}", exc_info=True)