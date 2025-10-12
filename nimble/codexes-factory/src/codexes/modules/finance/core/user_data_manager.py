"""
User Data Manager for Finance Module

Centralizes user-specific financial data management, eliminating redundant
uploads and providing consistent data source tracking.
"""

import hashlib
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


class UserDataManager:
    """
    Manages user-specific financial data directories and file operations.

    Provides centralized management of:
    - User-specific data directories
    - File upload processing and storage
    - Data source metadata tracking
    - File validation and organization
    """

    def __init__(self, username: str, base_dir: str = "userdocs"):
        self.username = username
        self.user_id = self._get_user_id_from_username(username)
        self.base_dir = Path(base_dir)
        self.user_base_path = self.base_dir / str(self.user_id) / "finance_data"

        # Ensure directories exist
        self._ensure_directories()

        # Initialize metadata tracking
        self.metadata_file = self.user_base_path / "metadata.json"
        self._load_metadata()

    def _get_user_id_from_username(self, username: str) -> str:
        """
        Generate consistent user ID from username.
        For now, use a simple hash. In production, this should map to actual user IDs.
        """
        if not username or username == "guest":
            return "guest"

        # Create consistent hash-based ID
        user_hash = hashlib.md5(username.encode()).hexdigest()[:8]
        return f"user_{user_hash}"

    def get_data_directories(self) -> Dict[str, Path]:
        """Return standardized directory structure for user's financial data."""
        directories = {
            'lsi_data': self.user_base_path / "lsi",
            'lsi_metadata': self.user_base_path / "lsi_metadata",
            'kdp_data': self.user_base_path / "kdp",
            'direct_sales': self.user_base_path / "direct_sales",
            'author_data': self.user_base_path / "authors",
            'market_data': self.user_base_path / "market_data",
            'processed': self.user_base_path / "processed",
            'reports': self.user_base_path / "reports",
            'working_docs': self.user_base_path / "working_docs",
            'royalty_reports': self.user_base_path / "royalty_reports"
        }
        return directories

    def _ensure_directories(self):
        """Create all necessary directories if they don't exist."""
        directories = self.get_data_directories()
        for dir_path in directories.values():
            dir_path.mkdir(parents=True, exist_ok=True)

    def _load_metadata(self):
        """Load existing metadata or initialize empty."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {
                    'user_id': self.user_id,
                    'username': self.username,
                    'created': datetime.now().isoformat(),
                    'data_sources': {},
                    'file_history': []
                }
                self._save_metadata()
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            # Initialize with empty metadata if load fails
            self.metadata = {
                'user_id': self.user_id,
                'username': self.username,
                'created': datetime.now().isoformat(),
                'data_sources': {},
                'file_history': []
            }

    def _save_metadata(self):
        """Save metadata to file."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    def save_uploaded_file(self, uploaded_file, category: str,
                          destination: Optional[str] = None) -> Tuple[str, Dict]:
        """
        Save uploaded file with metadata tracking and duplicate detection.

        Args:
            uploaded_file: Streamlit uploaded file object
            category: Data category (lsi_data, kdp_data, etc.)
            destination: Optional subdirectory within category

        Returns:
            Tuple of (file_path, file_metadata)
        """
        directories = self.get_data_directories()

        if category not in directories:
            raise ValueError(f"Unknown category: {category}")

        target_dir = directories[category]
        if destination:
            target_dir = target_dir / destination
            target_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = uploaded_file.name
        base_name, ext = os.path.splitext(file_name)
        unique_name = f"{base_name}_{timestamp}{ext}"

        file_path = target_dir / unique_name

        # Save file
        try:
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Create file metadata
            file_metadata = {
                'original_name': file_name,
                'saved_name': unique_name,
                'category': category,
                'destination': destination,
                'upload_time': datetime.now().isoformat(),
                'file_size': uploaded_file.size,
                'file_path': str(file_path.relative_to(self.base_dir))
            }

            # Debug output for KDP files
            if category == 'kdp_data':
                logger.info(f"Created KDP file metadata: {file_metadata}")
                print(f"🔍 DEBUG: Created KDP file metadata: {file_metadata}")
                print(f"🔍 DEBUG: File will be saved to: {file_path}")

            # Update metadata tracking
            if category not in self.metadata['data_sources']:
                self.metadata['data_sources'][category] = []

            self.metadata['data_sources'][category].append(file_metadata)

            # Debug output after adding to data sources
            if category == 'kdp_data':
                logger.info(f"Added to data_sources[kdp_data]. New count: {len(self.metadata['data_sources'][category])}")
                print(f"🔍 DEBUG: Added to data_sources[kdp_data]. New count: {len(self.metadata['data_sources'][category])}")

            self.metadata['file_history'].append(file_metadata)
            self._save_metadata()

            logger.info(f"Saved file {unique_name} to {category}")
            return str(file_path), file_metadata

        except Exception as e:
            logger.error(f"Error saving uploaded file: {e}")
            raise

    def get_data_source_metadata(self, category: Optional[str] = None) -> Dict:
        """
        Return metadata about data sources for a category or all categories.

        Args:
            category: Specific category to get metadata for, or None for all

        Returns:
            Dictionary with data source information
        """
        if category:
            return {
                'username': self.username,
                'user_id': self.user_id,
                'category': category,
                'files': self.metadata['data_sources'].get(category, []),
                'last_updated': self._get_last_update_time(category)
            }
        else:
            return {
                'username': self.username,
                'user_id': self.user_id,
                'data_sources': self.metadata['data_sources'],
                'file_history': self.metadata['file_history'],
                'created': self.metadata['created']
            }

    def _get_last_update_time(self, category: str) -> Optional[str]:
        """Get the last update time for a category."""
        files = self.metadata['data_sources'].get(category, [])
        if not files:
            return None
        return max(f['upload_time'] for f in files)

    def list_files(self, category: str) -> List[Dict]:
        """List all files in a category with their metadata."""
        files = self.metadata['data_sources'].get(category, [])

        # Debug output for KDP file searches
        if category == 'kdp_data':
            logger.info(f"UserDataManager.list_files('kdp_data'): Found {len(files)} files in metadata")
            print(f"🔍 DEBUG: UserDataManager - kdp_data category has {len(files)} files in metadata")
            if files:
                for i, file_info in enumerate(files):
                    print(f"🔍 DEBUG: KDP metadata file {i+1}: {file_info.get('original_name', 'Unknown')} -> {file_info.get('saved_name', 'Unknown')}")
            else:
                print("🔍 DEBUG: UserDataManager - No files found in kdp_data metadata")

        return files

    def get_file_path(self, category: str, filename: str) -> Optional[Path]:
        """Get the full path to a specific file."""
        files = self.list_files(category)
        for file_info in files:
            if file_info['original_name'] == filename or file_info['saved_name'] == filename:
                return self.base_dir / file_info['file_path']
        return None

    def delete_file(self, category: str, filename: str) -> bool:
        """
        Delete a file and update metadata.

        Args:
            category: Data category
            filename: Original or saved filename

        Returns:
            True if file was deleted, False otherwise
        """
        try:
            file_path = self.get_file_path(category, filename)
            if file_path and file_path.exists():
                file_path.unlink()

                # Remove from metadata
                files = self.metadata['data_sources'].get(category, [])
                self.metadata['data_sources'][category] = [
                    f for f in files
                    if f['original_name'] != filename and f['saved_name'] != filename
                ]
                self._save_metadata()

                logger.info(f"Deleted file {filename} from {category}")
                return True

        except Exception as e:
            logger.error(f"Error deleting file {filename}: {e}")

        return False

    def get_processing_paths(self) -> Dict[str, str]:
        """
        Get paths for FRO processing in the expected format.

        Returns:
            Dictionary with paths that FRO objects expect
        """
        directories = self.get_data_directories()
        return {
            'userdocs_path': str(self.user_base_path),
            'userdocs_working_docs_path': str(directories['working_docs']),
            'userdocs_results_path': str(directories['processed']),
            'userdocs_authordata_path': str(directories['author_data']),
            'userdocs_lsidata_path': str(directories['lsi_data']),
            'userdocs_lsimetadata_path': str(directories['lsi_metadata']),
            'userdocs_kdpdata_path': str(directories['kdp_data']),
            'userdocs_directsales_path': str(directories['direct_sales']),
            'userdocs_royaltyreports_path': str(directories['royalty_reports'])
        }

    def validate_file_format(self, uploaded_file, expected_columns: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Validate uploaded file format.

        Args:
            uploaded_file: Streamlit uploaded file object
            expected_columns: Optional list of required columns

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file extension
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            if file_ext not in ['.xlsx', '.xls', '.csv', '.json']:
                return False, f"Unsupported file type: {file_ext}"

            # Try to read file to validate format
            if file_ext == '.csv':
                try:
                    df = self._read_csv_with_encoding(uploaded_file, nrows=5)
                except ValueError as e:
                    return False, str(e)
            elif file_ext in ['.xlsx', '.xls']:
                # For Excel files, use the same sheet detection logic as KDP processing
                try:
                    excel_file = pd.ExcelFile(uploaded_file)
                    sheet_names = excel_file.sheet_names

                    # Use KDP-specific sheet detection logic
                    target_sheet = self._get_kdp_sheet_name(uploaded_file.name, sheet_names)

                    logger.info(f"Reading Excel sheet: {target_sheet} from file with sheets: {sheet_names}")
                    df = pd.read_excel(uploaded_file, sheet_name=target_sheet, nrows=5, engine='openpyxl')

                except Exception as e:
                    logger.error(f"Error reading Excel file: {e}")
                    # Fallback to default reading
                    uploaded_file.seek(0)
                    try:
                        df = pd.read_excel(uploaded_file, nrows=5, engine='openpyxl')
                    except:
                        df = pd.read_excel(uploaded_file, nrows=5)
            elif file_ext == '.json':
                # Basic JSON validation
                json.load(uploaded_file)
                return True, "Valid JSON file"
            else:
                return False, "Unknown file format"

            # Check for expected columns if specified
            if expected_columns:
                missing_columns = set(expected_columns) - set(df.columns)
                if missing_columns:
                    return False, f"Missing required columns: {', '.join(missing_columns)}"

            # Reset file position for later reading
            uploaded_file.seek(0)
            return True, "File format is valid"

        except Exception as e:
            uploaded_file.seek(0)  # Reset position even on error
            return False, f"File validation error: {str(e)}"

    def _read_csv_with_encoding(self, file_path, **kwargs) -> pd.DataFrame:
        """
        Read CSV file with automatic encoding detection.

        Args:
            file_path: Path to CSV file or file-like object
            **kwargs: Additional arguments to pass to pd.read_csv

        Returns:
            DataFrame with the CSV data
        """
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']

        for encoding in encodings:
            try:
                if hasattr(file_path, 'seek'):
                    file_path.seek(0)
                df = pd.read_csv(file_path, encoding=encoding, **kwargs)
                logger.debug(f"Successfully read CSV with encoding: {encoding}")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                # For non-encoding errors, raise immediately
                logger.error(f"Error reading CSV with encoding {encoding}: {e}")
                raise

        raise ValueError("Unable to read CSV file with any standard encoding")

    def _calculate_file_hash(self, uploaded_file) -> str:
        """Calculate MD5 hash of uploaded file content for duplicate detection."""
        try:
            content = uploaded_file.getbuffer()
            hash_md5 = hashlib.md5(content).hexdigest()
            uploaded_file.seek(0)  # Reset position
            return hash_md5
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            uploaded_file.seek(0)
            return ""

    def find_duplicates(self, uploaded_file, category: str, destination: Optional[str] = None) -> List[Dict]:
        """
        Find potential duplicate files based on content hash and metadata.

        Args:
            uploaded_file: Streamlit uploaded file object
            category: Data category to check for duplicates
            destination: Optional subdirectory within category

        Returns:
            List of potential duplicate files with their metadata
        """
        duplicates = []
        file_hash = self._calculate_file_hash(uploaded_file)

        if not file_hash:
            return duplicates

        # Check existing files for content-based duplicates
        existing_files = self.list_files(category)

        for existing_file in existing_files:
            # Check if destination matches (same channel/period)
            if destination and existing_file.get('destination') != destination:
                continue

            # Try to calculate hash of existing file for comparison
            try:
                existing_path = self.base_dir / existing_file['file_path']
                if existing_path.exists():
                    with open(existing_path, 'rb') as f:
                        existing_hash = hashlib.md5(f.read()).hexdigest()

                    if existing_hash == file_hash:
                        duplicates.append({
                            **existing_file,
                            'duplicate_type': 'identical_content',
                            'match_confidence': 'high'
                        })
                    else:
                        # Check for potential same-period duplicates based on filename patterns
                        name_similarity = self._check_filename_similarity(
                            uploaded_file.name, existing_file['original_name'], category
                        )
                        if name_similarity > 0.7:
                            duplicates.append({
                                **existing_file,
                                'duplicate_type': 'similar_filename',
                                'match_confidence': 'medium',
                                'similarity_score': name_similarity
                            })
            except Exception as e:
                logger.error(f"Error checking file {existing_file['saved_name']} for duplicates: {e}")

        return duplicates

    def _check_filename_similarity(self, filename1: str, filename2: str, category: str) -> float:
        """
        Check filename similarity to detect same-period files.
        Returns similarity score from 0.0 to 1.0.
        """
        import re
        from difflib import SequenceMatcher

        # Extract base names without extensions
        base1 = os.path.splitext(filename1)[0].lower()
        base2 = os.path.splitext(filename2)[0].lower()

        # For LSI files, look for period indicators (ltd, ytd, lytd, etc.)
        if category == 'lsi_data':
            period_patterns = ['ltd', 'ytd', 'lytd', 'thismonth', r'\d{4}-\d{2}', r'\d{6}']

            for pattern in period_patterns:
                if re.search(pattern, base1) and re.search(pattern, base2):
                    # If both files have the same period indicator, high similarity
                    if re.search(pattern, base1).group() == re.search(pattern, base2).group():
                        return 0.9

        # General filename similarity using sequence matcher
        return SequenceMatcher(None, base1, base2).ratio()

    def _get_kdp_sheet_name(self, file_name: str, available_sheets: List[str]) -> str:
        """
        Determine the correct sheet name for different KDP file types.
        Uses the same logic as the KDP processing system.
        """
        try:
            logger.info(f"KDP sheet detection for file: {file_name}, available sheets: {available_sheets}")

            # For KDP_Order* or KDP_Orders- files, use "Combined Sales" sheet
            if file_name.startswith('KDP_Order'):
                logger.info("KDP_Order* file detected, using 'Combined Sales' sheet")
                return 'Combined Sales'

            # Priority order for sheet names
            preferred_sheets = ['Combined Sales', 'Total Royalty', 'Royalty', 'Sales']

            for preferred in preferred_sheets:
                if preferred in available_sheets:
                    logger.info(f"Found preferred sheet '{preferred}'")
                    return preferred

            # If no preferred sheet found, use the first available sheet
            if available_sheets:
                logger.info(f"Using first available sheet: '{available_sheets[0]}'")
                return available_sheets[0]

            # Fallback to 'Combined Sales'
            logger.info("No sheets detected, fallback to 'Combined Sales'")
            return 'Combined Sales'

        except Exception as e:
            logger.error(f"Error in KDP sheet detection: {e}, fallback to 'Combined Sales'")
            return 'Combined Sales'