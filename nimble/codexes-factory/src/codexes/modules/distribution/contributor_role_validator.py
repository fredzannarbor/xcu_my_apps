"""
Contributor Role Validator Module

This module provides utilities for validating contributor roles against
LSI's valid contributor codes.
"""

import os
import csv
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ContributorRoleValidator:
    """
    Validates contributor roles against LSI's valid contributor codes.
    """
    
    def __init__(self, codes_file: str = "resources/lsi_valid_contributor_codes.csv"):
        """
        Initialize the contributor role validator.
        
        Args:
            codes_file: Path to the CSV file containing valid contributor codes
        """
        self.codes_file = codes_file
        self.valid_codes: Dict[str, str] = {}
        self.load_valid_codes()
    
    def load_valid_codes(self) -> None:
        """Load valid contributor codes from CSV file."""
        # Default codes in case file is not found
        self.valid_codes = {
            "A": "Author",
            "B": "Editor",
            "C": "Compiler",
            "D": "Translator",
            "E": "Introduction by",
            "F": "Preface by",
            "G": "Afterword by",
            "H": "Revised by",
            "I": "Illustrator",
            "J": "Photographer",
            "K": "Foreword by",
            "L": "Narrator",
            "M": "Contributor",
            "N": "Composer",
            "O": "Lyricist",
            "P": "Librettist",
            "Q": "Conductor",
            "R": "Performed by",
            "S": "Director",
            "T": "Producer",
            "U": "Other",
            "V": "Actor",
            "W": "Adapted by",
            "X": "Screenplay by",
            "Y": "Created by",
            "Z": "Consultant"
        }
        
        try:
            if not os.path.exists(self.codes_file):
                logger.warning(f"Contributor codes file not found: {self.codes_file}. Using default codes.")
                return
            
            with open(self.codes_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                # Skip header row if present
                header = next(reader, None)
                
                # Determine column indices based on header
                code_idx = 0
                desc_idx = 1
                
                if header:
                    for i, col in enumerate(header):
                        if col.lower() in ('code', 'contributor code'):
                            code_idx = i
                        elif col.lower() in ('description', 'role', 'contributor role'):
                            desc_idx = i
                
                # Read codes and descriptions
                file_codes = {}
                for row in reader:
                    if len(row) > max(code_idx, desc_idx):
                        code = row[code_idx].strip()
                        desc = row[desc_idx].strip()
                        if code:
                            file_codes[code] = desc
                
                # Only replace default codes if we found some in the file
                if file_codes:
                    self.valid_codes = file_codes
            
            logger.info(f"Loaded {len(self.valid_codes)} valid contributor codes")
            
        except Exception as e:
            logger.error(f"Error loading contributor codes: {e}. Using default codes.")
    
    def is_valid_code(self, code: str) -> bool:
        """
        Check if a contributor code is valid.
        
        Args:
            code: Contributor code to validate
            
        Returns:
            True if the code is valid, False otherwise
        """
        if not code:
            return False
        
        return code.strip().upper() in self.valid_codes
    
    def get_code_description(self, code: str) -> Optional[str]:
        """
        Get the description for a contributor code.
        
        Args:
            code: Contributor code
            
        Returns:
            Description of the code or None if not found
        """
        if not code:
            return None
        
        return self.valid_codes.get(code.strip().upper())
    
    def validate_and_correct(self, code: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate a contributor code and suggest a correction if invalid.
        
        Args:
            code: Contributor code to validate
            
        Returns:
            Tuple of (is_valid, corrected_code, error_message)
        """
        if not code:
            return False, "A", "Empty contributor code, using default 'A' (Author)"
        
        clean_code = code.strip().upper()
        
        if clean_code in self.valid_codes:
            return True, clean_code, None
        
        # Try to find a close match
        if len(clean_code) == 1:
            # Single letter code, check if it's a valid code
            for valid_code in self.valid_codes:
                if valid_code.startswith(clean_code):
                    return False, valid_code, f"Invalid contributor code '{clean_code}', using '{valid_code}' ({self.valid_codes[valid_code]})"
        
        # Default to 'A' (Author) if no match found
        return False, "A", f"Invalid contributor code '{clean_code}', using default 'A' (Author)"
    
    def get_valid_codes_list(self) -> List[str]:
        """
        Get a list of all valid contributor codes with descriptions.
        
        Returns:
            List of strings in format "CODE - Description"
        """
        return [f"{code} - {desc}" for code, desc in self.valid_codes.items()]