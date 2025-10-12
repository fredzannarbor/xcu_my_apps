"""
CSV Reader component for batch processing of imprint concepts.

This module handles reading CSV files, column mapping, validation,
and extraction of imprint concepts for batch processing.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

from .batch_models import (
    ImprintRow,
    ValidationResult,
    ProcessingError,
    ProcessingContext,
    SourceInfo
)


class CSVReader:
    """Handles reading and processing CSV files for batch imprint processing."""
    
    # Default column mappings for common variations
    DEFAULT_COLUMN_MAPPINGS = {
        "concept": "imprint_concept",
        "description": "imprint_concept",
        "imprint_concept": "imprint_concept",
        "imprint_description": "imprint_concept",
        "text": "imprint_concept",
        "content": "imprint_concept"
    }
    
    # Required columns after mapping
    REQUIRED_COLUMNS = {"imprint_concept"}
    
    def __init__(self, column_mapping: Optional[Dict[str, str]] = None):
        """
        Initialize CSVReader with optional column mapping.
        
        Args:
            column_mapping: Dictionary mapping CSV column names to expected field names
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.column_mapping = column_mapping or {}
        
        # Merge with default mappings, user mappings take precedence
        self.effective_mapping = {**self.DEFAULT_COLUMN_MAPPINGS, **self.column_mapping}
        
        self.logger.info(f"Initialized CSVReader with {len(self.effective_mapping)} column mappings")
    
    def read_csv(self, csv_path: Path) -> List[ImprintRow]:
        """
        Read CSV file and extract imprint concepts.
        
        Args:
            csv_path: Path to the CSV file
            
        Returns:
            List of ImprintRow objects
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV is invalid or missing required columns
        """
        self.logger.info(f"Reading CSV file: {csv_path}")
        
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        try:
            # Read CSV with pandas
            df = pd.read_csv(csv_path, encoding='utf-8')
            self.logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
            
            # Validate and map columns
            validation_result = self.validate_columns(df)
            if not validation_result.valid:
                error_msg = f"CSV validation failed: {'; '.join(validation_result.errors)}"
                raise ValueError(error_msg)
            
            # Apply column mapping
            mapped_df = self.map_columns(df)
            
            # Extract imprint concepts
            imprint_rows = self.extract_imprint_concepts(mapped_df, csv_path)
            
            self.logger.info(f"Successfully extracted {len(imprint_rows)} imprint concepts")
            return imprint_rows
            
        except pd.errors.EmptyDataError:
            raise ValueError(f"CSV file is empty: {csv_path}")
        except pd.errors.ParserError as e:
            raise ValueError(f"Failed to parse CSV file {csv_path}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error reading CSV {csv_path}: {str(e)}")
            raise
    
    def validate_columns(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate CSV columns and check for required fields.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            ValidationResult with validation status and messages
        """
        result = ValidationResult(valid=True)
        
        # Check if we have any columns first
        if len(df.columns) == 0:
            result.add_error("CSV file has no columns")
            return result
        
        # Check if DataFrame is empty (no rows)
        if len(df) == 0:
            result.add_error("CSV file is empty")
            return result
        
        # Get available columns (case-insensitive)
        available_columns = {col.lower().strip() for col in df.columns}
        
        # Check if we can map to required columns
        mapped_columns = set()
        for csv_col, target_col in self.effective_mapping.items():
            if csv_col.lower() in available_columns:
                mapped_columns.add(target_col)
        
        # Check for required columns
        missing_required = self.REQUIRED_COLUMNS - mapped_columns
        if missing_required:
            # Try to find unmapped columns that might contain concept data
            concept_candidates = []
            for col in df.columns:
                col_lower = col.lower().strip()
                if any(keyword in col_lower for keyword in ['concept', 'description', 'text', 'content']):
                    concept_candidates.append(col)
            
            if concept_candidates:
                result.add_warning(f"Missing required columns {missing_required}, but found potential candidates: {concept_candidates}")
                result.add_warning("Consider updating column mapping to include these columns")
                # Still add error since required columns are missing
                result.add_error(f"Missing required columns: {missing_required}")
            else:
                result.add_error(f"Missing required columns: {missing_required}")
                result.add_error(f"Available columns: {list(df.columns)}")
                result.add_error("Update column mapping or ensure CSV has required columns")
        
        # Check for empty columns
        empty_columns = [col for col in df.columns if df[col].isna().all()]
        if empty_columns:
            result.add_warning(f"Found completely empty columns: {empty_columns}")
        
        # Log column information
        self.logger.debug(f"Available columns: {list(df.columns)}")
        self.logger.debug(f"Mapped columns: {mapped_columns}")
        
        return result
    
    def map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply column mapping to DataFrame.
        
        Args:
            df: Original DataFrame
            
        Returns:
            DataFrame with mapped column names
        """
        mapped_df = df.copy()
        
        # Create case-insensitive mapping, avoiding duplicates
        column_map = {}
        used_targets = set()
        
        for csv_col, target_col in self.effective_mapping.items():
            # Skip if target already used (first match wins)
            if target_col in used_targets:
                continue
                
            # Find matching column (case-insensitive)
            for actual_col in df.columns:
                if actual_col.lower().strip() == csv_col.lower():
                    column_map[actual_col] = target_col
                    used_targets.add(target_col)
                    break
        
        if column_map:
            mapped_df = mapped_df.rename(columns=column_map)
            self.logger.info(f"Applied column mapping: {column_map}")
        
        return mapped_df
    
    def extract_imprint_concepts(self, df: pd.DataFrame, source_file: Path) -> List[ImprintRow]:
        """
        Extract imprint concepts from mapped DataFrame.
        
        Args:
            df: Mapped DataFrame
            source_file: Source CSV file path
            
        Returns:
            List of ImprintRow objects
        """
        imprint_rows = []
        total_rows = len(df)
        
        for idx, row in df.iterrows():
            row_number = idx + 1  # 1-based row numbering
            
            # Get imprint concept
            imprint_concept = ""
            if "imprint_concept" in df.columns:
                concept_value = row["imprint_concept"]
                if pd.notna(concept_value):
                    imprint_concept = str(concept_value).strip()
            
            # Skip empty concepts
            if not imprint_concept:
                self.logger.warning(f"Skipping row {row_number} - empty imprint concept")
                continue
            
            # Collect additional data (all other columns)
            additional_data = {}
            mapped_columns = {}
            
            for col_name, value in row.items():
                if col_name != "imprint_concept":
                    # Store non-null values
                    if pd.notna(value):
                        additional_data[col_name] = value
                    
                    # Track mapped columns
                    original_col = self._find_original_column_name(col_name, df)
                    if original_col:
                        mapped_columns[original_col] = col_name
            
            # Create source info
            source_info = SourceInfo(
                file_path=source_file,
                file_name=source_file.name,
                row_number=row_number,
                total_rows=total_rows
            )
            
            # Create imprint row
            imprint_row = ImprintRow(
                row_number=row_number,
                imprint_concept=imprint_concept,
                source_file=source_file,
                additional_data=additional_data,
                mapped_columns=mapped_columns,
                source_info=source_info
            )
            
            imprint_rows.append(imprint_row)
        
        return imprint_rows
    
    def _find_original_column_name(self, mapped_name: str, df: pd.DataFrame) -> Optional[str]:
        """Find the original column name that was mapped to the given name."""
        for original_col in df.columns:
            for csv_col, target_col in self.effective_mapping.items():
                if (target_col == mapped_name and 
                    original_col.lower().strip() == csv_col.lower()):
                    return original_col
        return mapped_name  # Return mapped name if no original found
    
    def get_column_info(self, csv_path: Path) -> Dict[str, Any]:
        """
        Get information about CSV columns without full processing.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            Dictionary with column information
        """
        try:
            # Read just the header
            df = pd.read_csv(csv_path, nrows=0)
            
            available_columns = list(df.columns)
            mappable_columns = []
            
            for col in available_columns:
                for csv_col in self.effective_mapping.keys():
                    if col.lower().strip() == csv_col.lower():
                        mappable_columns.append({
                            "original": col,
                            "maps_to": self.effective_mapping[csv_col]
                        })
                        break
            
            return {
                "total_columns": len(available_columns),
                "available_columns": available_columns,
                "mappable_columns": mappable_columns,
                "required_mappings": list(self.REQUIRED_COLUMNS),
                "has_required_mappings": any(
                    mapping["maps_to"] in self.REQUIRED_COLUMNS 
                    for mapping in mappable_columns
                )
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "total_columns": 0,
                "available_columns": [],
                "mappable_columns": [],
                "required_mappings": list(self.REQUIRED_COLUMNS),
                "has_required_mappings": False
            }
    
    def preview_csv(self, csv_path: Path, num_rows: int = 5) -> Dict[str, Any]:
        """
        Preview CSV file content.
        
        Args:
            csv_path: Path to CSV file
            num_rows: Number of rows to preview
            
        Returns:
            Dictionary with preview information
        """
        try:
            df = pd.read_csv(csv_path, nrows=num_rows)
            
            return {
                "success": True,
                "total_columns": len(df.columns),
                "preview_rows": len(df),
                "columns": list(df.columns),
                "sample_data": df.to_dict('records'),
                "column_info": self.get_column_info(csv_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_columns": 0,
                "preview_rows": 0,
                "columns": [],
                "sample_data": []
            }


def create_csv_reader(column_mapping: Optional[Dict[str, str]] = None) -> CSVReader:
    """
    Factory function to create a CSVReader instance.
    
    Args:
        column_mapping: Optional column mapping dictionary
        
    Returns:
        Configured CSVReader instance
    """
    return CSVReader(column_mapping=column_mapping)