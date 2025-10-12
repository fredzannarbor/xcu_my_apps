# src/codexes/modules/distribution/lsi_checkpoint_manager.py

import csv
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import fcntl
import time

from ..metadata.metadata_models import CodexMetadata


@dataclass
class CheckpointInfo:
    """Metadata about a checkpoint file."""
    file_path: Path
    books_processed: int
    last_updated: datetime
    imprint: str
    pipeline_id: str


class LSICheckpointManager:
    """
    Manages cumulative LSI CSV checkpoint files during batch processing.
    
    Provides resilient batch processing by maintaining cumulative LSI CSV files
    during pipeline execution with minimal overhead and graceful error handling.
    """
    
    def __init__(self, checkpoint_dir: str = "data"):
        """
        Initialize the LSI Checkpoint Manager.
        
        Args:
            checkpoint_dir: Directory where checkpoint files will be stored
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.current_checkpoint_file: Optional[Path] = None
        self.headers_written = False
        self.books_processed = 0
        self.logger = logging.getLogger(__name__)
        
        # Ensure checkpoint directory exists
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # LSI CSV headers (matching existing LSI structure)
        self.lsi_headers = self._get_lsi_headers()
    
    def _get_lsi_headers(self) -> List[str]:
        """
        Get the standard LSI CSV headers.
        
        Returns:
            List of LSI field names for CSV header
        """
        # Standard LSI headers based on existing template
        return [
            "Title", "Author", "ISBN13", "Publisher", "Publication Date",
            "Language", "Format", "Country of Origin", "Audience",
            "Short Description", "Long Description", "Keywords",
            "BISAC Codes", "BISAC Text", "BIC Codes", "Thema Codes",
            "Series Name", "Series Number", "Page Count", "Trim Size",
            "Cover Type", "Interior Color", "Binding", "Illustration Count",
            "Min Age", "Max Age", "Contributor One", "Contributor One Role",
            "Contributor Two", "Contributor Two Role", "Contributor Three",
            "Contributor Three Role", "Table of Contents", "Review Quotes",
            "Annotation Summary", "Thema Subject 1", "Thema Subject 2",
            "Thema Subject 3", "Regional Subjects", "Min Grade", "Max Grade",
            "Edition Statement", "Volume Number", "Illustration Notes",
            "Word Count", "Interior Paper", "Carton Quantity", "Carton Weight",
            "Carton Length"
        ]
    
    def create_checkpoint_file(self, imprint: str, pipeline_id: Optional[str] = None) -> Path:
        """
        Create a new timestamped checkpoint file.
        
        Args:
            imprint: The imprint name for the checkpoint file
            pipeline_id: Optional pipeline identifier
            
        Returns:
            Path to the created checkpoint file
            
        Raises:
            OSError: If file creation fails
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"cumulative_checkpoint_{timestamp}_{imprint}.csv"
        
        if pipeline_id:
            filename = f"cumulative_checkpoint_{timestamp}_{imprint}_{pipeline_id}.csv"
        
        self.current_checkpoint_file = self.checkpoint_dir / filename
        self.headers_written = False
        self.books_processed = 0
        
        try:
            # Create the file and write headers
            self._write_headers()
            self.logger.info(f"Created checkpoint file: {self.current_checkpoint_file}")
            return self.current_checkpoint_file
            
        except Exception as e:
            self.logger.error(f"Failed to create checkpoint file {self.current_checkpoint_file}: {e}")
            raise
    
    def _write_headers(self) -> None:
        """
        Write CSV headers to the checkpoint file.
        
        Raises:
            OSError: If header writing fails
        """
        if not self.current_checkpoint_file:
            raise ValueError("No checkpoint file initialized")
        
        try:
            with open(self.current_checkpoint_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.lsi_headers)
            
            self.headers_written = True
            self.logger.debug(f"Headers written to checkpoint file: {self.current_checkpoint_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to write headers to checkpoint file: {e}")
            raise
    
    def append_book_data(self, metadata: CodexMetadata) -> bool:
        """
        Append a single book's LSI data to the checkpoint file using atomic operations.
        
        Args:
            metadata: CodexMetadata object containing book information
            
        Returns:
            True if append was successful, False otherwise
        """
        if not self.current_checkpoint_file:
            self.logger.warning("No checkpoint file initialized, skipping append")
            return False
        
        try:
            # Convert metadata to CSV row
            csv_row = self._metadata_to_csv_row(metadata)
            
            # Use atomic write operation
            return self._atomic_append(csv_row)
            
        except Exception as e:
            self.logger.warning(f"Failed to append book data to checkpoint: {e}")
            return False
    
    def _metadata_to_csv_row(self, metadata: CodexMetadata) -> List[str]:
        """
        Convert CodexMetadata to CSV row format matching LSI structure.
        
        Args:
            metadata: CodexMetadata object to convert
            
        Returns:
            List of strings representing CSV row data
        """
        return [
            metadata.title or "",
            metadata.author or "",
            metadata.isbn13 or "",
            metadata.publisher or "",
            metadata.publication_date or "",
            metadata.language or "",
            metadata.format or "",
            metadata.country_of_origin or "",
            metadata.audience or "",
            metadata.summary_short or "",
            metadata.summary_long or "",
            metadata.keywords or "",
            metadata.bisac_codes or "",
            metadata.bisac_text or "",
            metadata.bic_codes or "",
            metadata.thema_codes or "",
            metadata.series_name or "",
            metadata.series_number or "",
            str(metadata.page_count) if metadata.page_count else "",
            metadata.trim_size or "",
            metadata.cover_type or "",
            metadata.interior_color or "",
            metadata.binding or "",
            metadata.illustration_count or "",
            metadata.min_age or "",
            metadata.max_age or "",
            metadata.contributor_one or "",
            metadata.contributor_one_role or "",
            metadata.contributor_two or "",
            metadata.contributor_two_role or "",
            metadata.contributor_three or "",
            metadata.contributor_three_role or "",
            metadata.table_of_contents or "",
            metadata.review_quotes or "",
            metadata.annotation_summary or "",
            metadata.thema_subject_1 or "",
            metadata.thema_subject_2 or "",
            metadata.thema_subject_3 or "",
            metadata.regional_subjects or "",
            metadata.min_grade or "",
            metadata.max_grade or "",
            metadata.edition_statement or "",
            metadata.volume_number or "",
            metadata.illustration_notes or "",
            str(metadata.word_count) if metadata.word_count else "",
            metadata.interior_paper or "",
            metadata.carton_quantity or "",
            metadata.carton_weight or "",
            metadata.carton_length or ""
        ]
    
    def _atomic_append(self, csv_row: List[str]) -> bool:
        """
        Atomically append a CSV row to the checkpoint file.
        
        Uses temporary file and atomic rename to prevent corruption.
        
        Args:
            csv_row: List of strings representing the CSV row
            
        Returns:
            True if append was successful, False otherwise
        """
        if not self.current_checkpoint_file:
            return False
        
        temp_file = None
        try:
            # Create temporary file in same directory
            temp_fd, temp_path = tempfile.mkstemp(
                dir=self.current_checkpoint_file.parent,
                prefix=f".{self.current_checkpoint_file.name}",
                suffix=".tmp"
            )
            temp_file = Path(temp_path)
            
            # Copy existing content and append new row
            with os.fdopen(temp_fd, 'w', encoding='utf-8-sig', newline='') as temp_f:
                # Copy existing content if file exists
                if self.current_checkpoint_file.exists():
                    with open(self.current_checkpoint_file, 'r', encoding='utf-8-sig') as existing_f:
                        temp_f.write(existing_f.read())
                
                # Append new row
                writer = csv.writer(temp_f)
                writer.writerow(csv_row)
            
            # Atomic rename
            temp_file.replace(self.current_checkpoint_file)
            
            self.books_processed += 1
            self.logger.debug(f"Appended book data to checkpoint (total: {self.books_processed})")
            return True
            
        except Exception as e:
            self.logger.warning(f"Atomic append failed: {e}")
            # Clean up temporary file if it exists
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass
            return False
    
    def finalize_checkpoint(self) -> bool:
        """
        Mark checkpoint as complete and perform any cleanup.
        
        Returns:
            True if finalization was successful, False otherwise
        """
        if not self.current_checkpoint_file:
            self.logger.warning("No checkpoint file to finalize")
            return False
        
        try:
            self.logger.info(
                f"Checkpoint finalized: {self.current_checkpoint_file} "
                f"({self.books_processed} books processed)"
            )
            
            # Reset state
            self.current_checkpoint_file = None
            self.headers_written = False
            self.books_processed = 0
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to finalize checkpoint: {e}")
            return False
    
    def get_checkpoint_info(self) -> Optional[CheckpointInfo]:
        """
        Get information about the current checkpoint.
        
        Returns:
            CheckpointInfo object if checkpoint is active, None otherwise
        """
        if not self.current_checkpoint_file:
            return None
        
        try:
            stat = self.current_checkpoint_file.stat()
            return CheckpointInfo(
                file_path=self.current_checkpoint_file,
                books_processed=self.books_processed,
                last_updated=datetime.fromtimestamp(stat.st_mtime),
                imprint=self._extract_imprint_from_filename(),
                pipeline_id=""
            )
        except Exception as e:
            self.logger.warning(f"Failed to get checkpoint info: {e}")
            return None
    
    def _extract_imprint_from_filename(self) -> str:
        """
        Extract imprint name from checkpoint filename.
        
        Returns:
            Imprint name or empty string if not found
        """
        if not self.current_checkpoint_file:
            return ""
        
        try:
            # Parse filename: cumulative_checkpoint_YYYYMMDD_HHMM_imprint.csv
            parts = self.current_checkpoint_file.stem.split('_')
            if len(parts) >= 5:
                return parts[4]  # imprint is the 5th part
        except:
            pass
        
        return ""
    
    def list_checkpoint_files(self) -> List[Path]:
        """
        List all checkpoint files in the checkpoint directory.
        
        Returns:
            List of checkpoint file paths, sorted by modification time (newest first)
        """
        try:
            checkpoint_files = list(self.checkpoint_dir.glob("cumulative_checkpoint_*.csv"))
            # Sort by modification time, newest first
            checkpoint_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            return checkpoint_files
        except Exception as e:
            self.logger.warning(f"Failed to list checkpoint files: {e}")
            return []