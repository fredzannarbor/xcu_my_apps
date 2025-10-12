"""
LSI Field Completer Module

This module provides functionality to complete LSI fields using LLM calls.
It leverages the existing llm_caller module to generate high-quality content
for LSI fields during stage 1 of the book creation process.
"""

import os
import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from ...core.llm_integration import call_model_with_prompt
from ...core.prompt_manager import load_and_prepare_prompts
from ..metadata.metadata_models import CodexMetadata

logger = logging.getLogger(__name__)


class LLMFieldCompleter:
    """
    Completes LSI fields using LLM calls.
    
    This class leverages the existing llm_caller module to generate high-quality content
    for LSI fields during stage 1 of the book creation process.
    """
    
    def __init__(self, model_name: str = "gemini/gemini-2.5-flash", 
                prompts_path: str = "prompts/lsi_field_completion_prompts.json"):
        """
        Initialize the LLM field completer.
        
        Args:
            model_name: Name of the LLM model to use
            prompts_path: Path to the LSI field completion prompts file
        """
        self.model_name = model_name
        self.prompts_path = prompts_path
        self.prompts = self._load_prompts()
        
        # Map of prompt keys to metadata fields
        self.prompt_field_mapping = {
            "generate_contributor_bio": "contributor_one_bio",
            "suggest_bisac_codes": ["bisac_category_2", "bisac_category_3"],
            "generate_keywords": "keywords",
            "create_short_description": "summary_short",
            "suggest_thema_subjects": ["thema_subject_1", "thema_subject_2", "thema_subject_3"],
            "determine_audience": "audience",
            "determine_age_range": ["min_age", "max_age"],
            "extract_lsi_contributor_info": [
                "contributor_one_bio", 
                "contributor_one_affiliations",
                "contributor_one_professional_position",
                "contributor_one_location",
                "contributor_one_prior_work"
            ],
            "suggest_series_info": ["series_name", "series_number"],
            "generate_enhanced_annotation": "annotation_summary",
            "generate_illustration_info": ["illustration_count", "illustration_notes"],
            "generate_enhanced_toc": "table_of_contents"
            # Deterministic fields like weight and carton size are handled by direct computation
        }
    
    def _load_prompts(self) -> Dict[str, Any]:
        """Load LSI field completion prompts from file."""
        try:
            with open(self.prompts_path, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            logger.info(f"✅ Loaded {len(prompts)} LSI field completion prompts from {self.prompts_path}")
            return prompts
        except Exception as e:
            logger.error(f"Failed to load LSI field completion prompts: {e}")
            return {}
    
    def complete_missing_fields(self, metadata: CodexMetadata, book_content: Optional[str] = None, 
                           save_to_disk: bool = True, output_dir: Optional[str] = None) -> CodexMetadata:
        """
        Complete missing LSI fields in the metadata object.
        
        Args:
            metadata: CodexMetadata object to complete
            book_content: Optional book content to use for field completion
            save_to_disk: Whether to save completions to disk
            output_dir: Directory to save completions (defaults to metadata/ parallel to covers/ and interiors/)
            
        Returns:
            Updated CodexMetadata object with completed fields
        """
        # Initialize llm_completions dictionary if it doesn't exist
        if not hasattr(metadata, 'llm_completions') or metadata.llm_completions is None:
            metadata.llm_completions = {}
        
        # Track which fields were completed in this run
        newly_completed_fields = []
        completion_errors = []
        
        # Process each prompt
        for prompt_key, prompt_data in self.prompts.items():
            # Skip if we've already processed this prompt
            if prompt_key in metadata.llm_completions:
                logger.info(f"Skipping {prompt_key} as it's already in llm_completions")
                continue
            
            # Check if we should process this prompt based on existing metadata
            if self._should_process_prompt(prompt_key, metadata):
                try:
                    # Process the prompt
                    result = self._process_prompt(prompt_key, metadata, book_content)
                    if result:
                        # Add timestamp to track when this completion was generated
                        if isinstance(result, dict):
                            # For dictionary results, add metadata at the top level
                            metadata.llm_completions[prompt_key] = {
                                **result,
                                "_completion_metadata": {
                                    "timestamp": datetime.now().isoformat(),
                                    "model": self.model_name,
                                    "prompt_key": prompt_key
                                }
                            }
                        else:
                            # For string or other results, wrap in a dictionary
                            metadata.llm_completions[prompt_key] = {
                                "value": result,
                                "_completion_metadata": {
                                    "timestamp": datetime.now().isoformat(),
                                    "model": self.model_name,
                                    "prompt_key": prompt_key
                                }
                            }
                        
                        logger.info(f"Completed {prompt_key} field")
                        newly_completed_fields.append(prompt_key)
                        
                        # Update metadata fields directly if configured
                        self._update_metadata_fields(metadata, prompt_key, result)
                except Exception as e:
                    logger.error(f"Error processing prompt {prompt_key}: {e}")
                    completion_errors.append(f"{prompt_key}: {str(e)}")
                    # Continue with other prompts despite errors
        
        # Save completions to disk if requested
        if save_to_disk and metadata.llm_completions:
            try:
                saved_path = self._save_completions_to_disk(metadata, output_dir)
                if saved_path:
                    logger.info(f"Successfully saved completions to {saved_path}")
                    
                    # Add completion summary to metadata
                    if not hasattr(metadata, 'llm_completion_summary'):
                        metadata.llm_completion_summary = {}
                    
                    metadata.llm_completion_summary.update({
                        "last_completion_time": datetime.now().isoformat(),
                        "completed_fields": newly_completed_fields,
                        "completion_errors": completion_errors,
                        "saved_path": saved_path
                    })
            except Exception as e:
                logger.error(f"Failed to save completions: {e}")
                # Don't let save failures stop the process
        
        return metadata
        
    def _save_completions_to_disk(self, metadata: CodexMetadata, output_dir: Optional[str] = None) -> Optional[str]:
        """
        Save LLM completions to disk with improved directory discovery and error handling.
        
        Args:
            metadata: CodexMetadata object with completions
            output_dir: Directory to save completions (defaults to metadata/ parallel to covers/ and interiors/)
            
        Returns:
            Path to the saved file or None if saving failed
        """
        try:
            # Determine output directory using robust directory discovery
            if not output_dir:
                output_dir = self._discover_output_directory(metadata)
                logger.info(f"Using output directory: {output_dir}")
            
            # Create output directory structure if it doesn't exist
            try:
                os.makedirs(output_dir, exist_ok=True)
                logger.debug(f"Created or verified output directory: {output_dir}")
            except PermissionError:
                logger.error(f"Permission denied when creating directory: {output_dir}")
                # Try to use a fallback directory in the current working directory
                output_dir = os.path.join(os.getcwd(), 'metadata_output')
                os.makedirs(output_dir, exist_ok=True)
                logger.warning(f"Using fallback directory: {output_dir}")
            except Exception as e:
                logger.error(f"Failed to create output directory {output_dir}: {e}")
                # Try to use a fallback directory in the current working directory
                output_dir = os.path.join(os.getcwd(), 'metadata_output')
                os.makedirs(output_dir, exist_ok=True)
                logger.warning(f"Using fallback directory: {output_dir}")
            
            # Create consistent filename with timestamp and ISBN
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            isbn = getattr(metadata, 'isbn13', 'unknown')
            ref_id = getattr(metadata, 'publisher_reference_id', '')
            
            # Include reference ID in filename if available
            if ref_id:
                filename = f"llm_completions_{isbn}_{ref_id}_{timestamp}.json"
            else:
                filename = f"llm_completions_{isbn}_{timestamp}.json"
            
            filepath = os.path.join(output_dir, filename)
            
            # Prepare enhanced metadata context for saved files
            data_to_save = {
                "metadata": {
                    "title": getattr(metadata, 'title', 'Unknown'),
                    "author": getattr(metadata, 'author', 'Unknown'),
                    "isbn13": isbn,
                    "publisher_reference_id": ref_id,
                    "timestamp": timestamp,
                    "generation_date": datetime.now().strftime("%Y-%m-%d"),
                    "imprint": getattr(metadata, 'imprint', 'Unknown'),
                    "publisher": getattr(metadata, 'publisher', 'Unknown'),
                    "model_used": self.model_name
                },
                "llm_completions": metadata.llm_completions
            }
            
            # Save timestamped version
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved LLM completions to {filepath}")
            except Exception as e:
                logger.error(f"Failed to save timestamped completions to {filepath}: {e}")
            
            # Save latest version for easier access
            try:
                # Create a consistent "latest" filename that includes the ISBN for uniqueness
                latest_filename = f"latest_llm_completions_{isbn}.json"
                latest_filepath = os.path.join(output_dir, latest_filename)
                
                with open(latest_filepath, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved latest version to {latest_filepath}")
                
                # Also save a generic latest version for backward compatibility
                compat_filepath = os.path.join(output_dir, "latest_llm_completions.json")
                with open(compat_filepath, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                
                return filepath
            except Exception as e:
                logger.error(f"Failed to save latest version: {e}")
                return filepath if os.path.exists(filepath) else None
            
        except Exception as e:
            logger.error(f"Failed to save LLM completions to disk: {e}")
            return None
            
    def _discover_output_directory(self, metadata: CodexMetadata) -> str:
        """
        Discover the appropriate output directory for saving completions.
        
        This method implements robust directory discovery that looks for existing book
        directories by publisher_reference_id or ISBN, with multiple fallback options.
        
        Args:
            metadata: CodexMetadata object with book information
            
        Returns:
            Path to the appropriate output directory
        """
        # Get key identifiers from metadata
        ref_id = getattr(metadata, 'publisher_reference_id', None)
        isbn = getattr(metadata, 'isbn13', 'unknown')
        imprint = getattr(metadata, 'imprint', '').lower().replace(' ', '_')
        
        # List of potential base directories to search
        base_dirs = ['output', '.', 'data', 'books']
        
        # List of common imprint directories to check
        imprint_dirs = ['xynapse_traces', 'nimble_books']
        if imprint and imprint not in imprint_dirs:
            imprint_dirs.insert(0, imprint)
        
        # 1. First try: Look by publisher_reference_id in standard locations
        if ref_id:
            logger.debug(f"Searching for existing directory using publisher_reference_id: {ref_id}")
            for base_dir in base_dirs:
                # Check direct path: base_dir/ref_id
                direct_path = os.path.join(base_dir, ref_id)
                if os.path.isdir(direct_path):
                    metadata_dir = os.path.join(direct_path, 'metadata')
                    logger.info(f"Found existing directory by reference ID: {direct_path}")
                    return metadata_dir
                
                # Check imprint paths: base_dir/imprint/ref_id
                for imprint_dir in imprint_dirs:
                    potential_dir = os.path.join(base_dir, imprint_dir, ref_id)
                    if os.path.isdir(potential_dir):
                        # Check if covers or interiors directory exists to confirm it's a book directory
                        if (os.path.exists(os.path.join(potential_dir, 'covers')) or 
                            os.path.exists(os.path.join(potential_dir, 'interiors'))):
                            metadata_dir = os.path.join(potential_dir, 'metadata')
                            logger.info(f"Found existing book directory structure at {potential_dir}")
                            return metadata_dir
        
        # 2. Second try: Look by ISBN in directory names
        if isbn and isbn != 'unknown':
            logger.debug(f"Searching for existing directory using ISBN: {isbn}")
            for base_dir in base_dirs:
                # Use os.walk to find directories containing the ISBN
                for root, dirs, files in os.walk(base_dir):
                    # Skip very deep directories to avoid excessive searching
                    if root.count(os.sep) > 5:
                        continue
                    
                    # Check if ISBN is in the path
                    if isbn in root:
                        metadata_dir = os.path.join(root, 'metadata')
                        logger.info(f"Found directory containing ISBN {isbn}: {root}")
                        return metadata_dir
                    
                    # Also check immediate subdirectories for ISBN
                    for dir_name in dirs:
                        if isbn in dir_name:
                            found_dir = os.path.join(root, dir_name)
                            metadata_dir = os.path.join(found_dir, 'metadata')
                            logger.info(f"Found directory with ISBN in name: {found_dir}")
                            return metadata_dir
        
        # 3. Third try: Look for metadata directories in output locations
        logger.debug("Searching for existing metadata directories")
        for base_dir in base_dirs:
            # Check for standard metadata directory structure
            for imprint_dir in imprint_dirs:
                metadata_base = os.path.join(base_dir, imprint_dir, 'metadata')
                if os.path.isdir(metadata_base):
                    logger.info(f"Found existing metadata directory: {metadata_base}")
                    
                    # If we have ISBN, create a subdirectory for this book
                    if isbn and isbn != 'unknown':
                        book_metadata_dir = os.path.join(metadata_base, isbn)
                        return book_metadata_dir
                    
                    # Otherwise use the base metadata directory
                    return metadata_base
        
        # 4. Fallback: Create a structured path based on available information
        logger.debug("No existing directory found, creating structured path")
        
        # Use the most specific information available
        if ref_id and imprint:
            # Use imprint and reference ID
            output_dir = os.path.join('output', imprint, ref_id, 'metadata')
        elif ref_id:
            # Use just reference ID
            output_dir = os.path.join('output', 'books', ref_id, 'metadata')
        elif isbn and isbn != 'unknown':
            # Use ISBN and title
            title = getattr(metadata, 'title', 'unknown')
            safe_title = re.sub(r'[^\w\-_]', '_', title)
            output_dir = os.path.join('output', 'metadata', f"{isbn}_{safe_title}")
        else:
            # Last resort - use timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join('output', 'metadata', f"unknown_{timestamp}")
        
        logger.info(f"Created new structured path for metadata: {output_dir}")
        return output_dir
    
    def _should_process_prompt(self, prompt_key: str, metadata: CodexMetadata) -> bool:
        """
        Determine if a prompt should be processed based on existing metadata.
        
        Args:
            prompt_key: Key of the prompt to check
            metadata: CodexMetadata object to check
            
        Returns:
            True if the prompt should be processed, False otherwise
        """
        # Get the corresponding metadata fields
        fields = self.prompt_field_mapping.get(prompt_key)
        if not fields:
            return True
        
        # Convert to list if it's a single field
        if isinstance(fields, str):
            fields = [fields]
        
        # Check if any of the fields are empty
        for field in fields:
            value = getattr(metadata, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                return True
        
        return False
    
    def _process_prompt(self, prompt_key: str, metadata: CodexMetadata, book_content: Optional[str] = None, 
                      max_retries: int = 3, initial_delay: int = 2) -> Any:
        """
        Process a prompt to complete a field with enhanced retry logic and error handling.
        
        Args:
            prompt_key: Key of the prompt to process
            metadata: CodexMetadata object to use for prompt variables
            book_content: Optional book content to use for prompt variables
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before retrying (will be exponentially increased)
            
        Returns:
            Result of the LLM call or fallback value if all retries fail
        """
        # Get the prompt data
        prompt_data = self.prompts.get(prompt_key)
        if not prompt_data:
            logger.warning(f"No prompt data found for {prompt_key}")
            return self._provide_fallback_value(prompt_key, metadata)
        
        # Track retry attempts
        retry_count = 0
        last_error = None
        
        # Initialize retry tracking in metadata if it doesn't exist
        if not hasattr(metadata, 'llm_completion_attempts'):
            metadata.llm_completion_attempts = {}
        if not hasattr(metadata, 'llm_completion_failures'):
            metadata.llm_completion_failures = {}
            
        # Update retry count for this prompt
        metadata.llm_completion_attempts[prompt_key] = metadata.llm_completion_attempts.get(prompt_key, 0) + 1
        
        # Implement retry loop with exponential backoff
        while retry_count < max_retries:
            try:
                # Prepare variables for the prompt
                variables = self._prepare_prompt_variables(prompt_key, metadata, book_content)
                
                # Format the prompt messages
                messages = prompt_data.get("messages", [])
                formatted_messages = []
                for message in messages:
                    formatted_content = message["content"]
                    for var_name, var_value in variables.items():
                        placeholder = f"{{{var_name}}}"
                        if placeholder in formatted_content:
                            formatted_content = formatted_content.replace(placeholder, str(var_value) if var_value else "")
                    
                    formatted_messages.append({
                        "role": message["role"],
                        "content": formatted_content
                    })
                
                # Get the parameters
                params = prompt_data.get("params", {}).copy()
                
                # Create prompt config for call_model_with_prompt
                prompt_config = {
                    "messages": formatted_messages,
                    "params": {
                        "temperature": params.get("temperature", 0.7),
                        "max_tokens": params.get("max_tokens", 200)
                    }
                }
                
                # Log attempt information
                logger.info(f"Processing prompt {prompt_key} (Attempt {retry_count + 1}/{max_retries})")
                
                # Make the LLM call
                response = call_model_with_prompt(
                    model_name=self.model_name,
                    prompt_config=prompt_config,
                    prompt_name=prompt_key
                )
                
                # Process the response
                if response and "parsed_content" in response:
                    result = response["parsed_content"]
                    
                    # Check for error in parsed content
                    if isinstance(result, dict) and "error" in result:
                        error_msg = f"LLM returned error: {result['error']}"
                        logger.warning(f"Attempt {retry_count + 1}/{max_retries} failed: {error_msg}")
                        last_error = error_msg
                        retry_count += 1
                        delay = initial_delay * (2 ** retry_count)
                        logger.info(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                        continue
                    
                    # If result is a string and looks like JSON, try to parse it
                    if isinstance(result, str) and result.startswith("{") and result.endswith("}"):
                        try:
                            result = json.loads(result)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse JSON result: {e}")
                            # Continue with the string result
                    
                    # Check if result is empty or None
                    if result is None or (isinstance(result, str) and not result.strip()):
                        logger.warning(f"LLM returned empty result for prompt {prompt_key}")
                        retry_count += 1
                        delay = initial_delay * (2 ** retry_count)
                        logger.info(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                        continue
                    
                    logger.info(f"Successfully processed prompt {prompt_key}")
                    return result
                else:
                    error_msg = "No valid response from LLM"
                    logger.warning(f"Attempt {retry_count + 1}/{max_retries} failed: {error_msg}")
                    last_error = error_msg
                    retry_count += 1
                    delay = initial_delay * (2 ** retry_count)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                
            except Exception as e:
                # Log the error and retry
                logger.error(f"Error processing prompt {prompt_key} (Attempt {retry_count + 1}/{max_retries}): {e}")
                last_error = str(e)
                retry_count += 1
                
                # Implement exponential backoff
                if retry_count < max_retries:
                    delay = initial_delay * (2 ** retry_count)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    # Record the failure in metadata
                    if prompt_key not in metadata.llm_completion_failures:
                        metadata.llm_completion_failures[prompt_key] = []
                    metadata.llm_completion_failures[prompt_key].append(str(e))
                    
                    # Log the final failure
                    logger.error(f"Final failure after {max_retries} retries for prompt {prompt_key}: {e}")
                    
                    # Return fallback value
                    return self._provide_fallback_value(prompt_key, metadata)
        
        # If we've exhausted all retries, record the failure and return fallback value
        if prompt_key not in metadata.llm_completion_failures:
            metadata.llm_completion_failures[prompt_key] = []
        metadata.llm_completion_failures[prompt_key].append(last_error or "Unknown error")
        
        logger.error(f"All {max_retries} attempts failed for prompt {prompt_key}. Using fallback value.")
        return self._provide_fallback_value(prompt_key, metadata)
    
    def _prepare_prompt_variables(self, prompt_key: str, metadata: CodexMetadata, book_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Prepare variables for a prompt.
        
        Args:
            prompt_key: Key of the prompt to prepare variables for
            metadata: CodexMetadata object to use for variables
            book_content: Optional book content to use for variables
            
        Returns:
            Dictionary of variables for the prompt
        """
        # Helper function to safely get attributes
        def safe_get_attr(obj, attr, default=""):
            return getattr(obj, attr, default) or default
        
        variables = {
            "title": safe_get_attr(metadata, "title"),
            "author": safe_get_attr(metadata, "author"),
            "publisher": safe_get_attr(metadata, "publisher"),
            "summary_long": safe_get_attr(metadata, "summary_long"),
            "summary_short": safe_get_attr(metadata, "summary_short"),
            "keywords": safe_get_attr(metadata, "keywords"),
            "bisac_codes": safe_get_attr(metadata, "bisac_codes"),
            "isbn13": safe_get_attr(metadata, "isbn13"),
            "page_count": safe_get_attr(metadata, "page_count"),
            "trim_size": f"{safe_get_attr(metadata, 'trim_width_in', '6')} x {safe_get_attr(metadata, 'trim_height_in', '9')}",
            "binding": safe_get_attr(metadata, "rendition_booktype", "Perfect Bound"),
            "audience": safe_get_attr(metadata, "audience"),
            "language": safe_get_attr(metadata, "language", "eng"),
            "country_of_origin": "US",  # Default
            "subtitle": safe_get_attr(metadata, "subtitle"),
            "table_of_contents": safe_get_attr(metadata, "table_of_contents"),
            "publisher_reference_id": safe_get_attr(metadata, "publisher_reference_id"),
            "book_content": self._truncate_book_content(book_content, prompt_key)  # Using truncated book content for context
        }
        
        # Add field-specific variables
        if prompt_key == "generate_contributor_bio":
            variables["current_value"] = safe_get_attr(metadata, "contributor_one_bio")
        elif prompt_key == "suggest_bisac_codes":
            variables["current_value"] = safe_get_attr(metadata, "bisac_codes")
        elif prompt_key == "generate_keywords":
            variables["current_value"] = safe_get_attr(metadata, "keywords")
        elif prompt_key == "create_short_description":
            variables["current_value"] = safe_get_attr(metadata, "summary_short")
        elif prompt_key == "suggest_thema_subjects":
            variables["current_value"] = safe_get_attr(metadata, "thema_subject_1")
        elif prompt_key == "determine_age_range":
            variables["field_name"] = "min_age"
            variables["current_value"] = safe_get_attr(metadata, "min_age")
        
        return variables
    
    def _update_metadata_fields(self, metadata: CodexMetadata, prompt_key: str, result: Any) -> None:
        """
        Update metadata fields with the result of a prompt.
        
        Args:
            metadata: CodexMetadata object to update
            prompt_key: Key of the prompt that generated the result
            result: Result of the LLM call
        """
        try:
            fields = self.prompt_field_mapping.get(prompt_key)
            if not fields:
                return
            
            # Handle the case where result might be wrapped in a completion metadata structure
            actual_result = result
            if isinstance(result, dict) and "_completion_metadata" in result and "value" in result:
                actual_result = result["value"]
            
            # Special handling for enhanced annotation
            if prompt_key == "generate_enhanced_annotation":
                processed_annotation = self._process_enhanced_annotation(actual_result)
                setattr(metadata, "annotation_summary", processed_annotation)
                logger.debug(f"Updated annotation_summary with enhanced HTML formatting")
                return
            
            # Special handling for enhanced TOC
            if prompt_key == "generate_enhanced_toc":
                processed_toc = self._process_enhanced_toc(actual_result)
                setattr(metadata, "table_of_contents", processed_toc)
                logger.debug(f"Updated table_of_contents with enhanced formatting")
                return
            
            # Convert to list if it's a single field
            if isinstance(fields, str):
                fields = [fields]
                
                # Set the single field directly
                if isinstance(actual_result, dict):
                    # If result is a dictionary, try to find a matching key
                    for key, value in actual_result.items():
                        if key == fields[0] or key in fields[0] or fields[0] in key:
                            setattr(metadata, fields[0], value)
                            logger.debug(f"Updated field {fields[0]} with value from key {key}")
                            break
                    else:
                        # If no matching key found, use the first value
                        if actual_result:
                            first_value = next(iter(actual_result.values()))
                            setattr(metadata, fields[0], first_value)
                            logger.debug(f"Updated field {fields[0]} with first value from result dictionary")
                else:
                    # If result is not a dictionary, set it directly
                    setattr(metadata, fields[0], actual_result)
                    logger.debug(f"Updated field {fields[0]} with direct value")
            else:
                # Handle multiple fields
                if isinstance(actual_result, dict):
                    # If result is a dictionary, match keys to fields
                    for field in fields:
                        for key, value in actual_result.items():
                            if key == field or key in field or field in key:
                                setattr(metadata, field, value)
                                logger.debug(f"Updated field {field} with value from key {key}")
                                break
                elif isinstance(actual_result, str) and ";" in actual_result and len(fields) > 1:
                    # If result is a semicolon-separated string, split it
                    values = [v.strip() for v in actual_result.split(";")]
                    for i, field in enumerate(fields):
                        if i < len(values):
                            setattr(metadata, field, values[i])
                            logger.debug(f"Updated field {field} with value from split string at index {i}")
                
            # Track field updates in metadata
            if not hasattr(metadata, 'field_update_history'):
                metadata.field_update_history = {}
            
            # Record this update in the history
            for field in fields:
                if hasattr(metadata, field):
                    metadata.field_update_history[field] = {
                        "timestamp": datetime.now().isoformat(),
                        "source": f"llm_completion:{prompt_key}",
                        "value": getattr(metadata, field)
                    }
        
        except Exception as e:
            logger.error(f"Error updating metadata fields from prompt {prompt_key}: {e}")
            # Don't let field update failures stop the process
    
    def _process_enhanced_annotation(self, annotation_text: str) -> str:
        """
        Process and validate the enhanced annotation with HTML formatting.
        
        Args:
            annotation_text: Raw annotation text from LLM
            
        Returns:
            Processed annotation with proper HTML formatting and character limits
        """
        if not annotation_text:
            return ""
        
        # Clean up the annotation text
        processed = annotation_text.strip()
        
        # Ensure it doesn't exceed 4000 characters
        if len(processed) > 4000:
            # Try to truncate at a sentence boundary
            sentences = processed.split('. ')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence + '. ') <= 3950:  # Leave some buffer
                    truncated += sentence + '. '
                else:
                    break
            
            if truncated:
                processed = truncated.rstrip('. ') + '...'
            else:
                # If no good sentence boundary, just truncate
                processed = processed[:3997] + '...'
        
        # Ensure proper HTML formatting
        if not processed.startswith("<p>"):
            processed = f"<p>{processed}</p>"
        
        # Replace newlines with <br> tags if not already in HTML paragraphs
        if "<p>" not in processed[3:]:  # Skip the first <p> we just added
            processed = processed.replace("\n", "<br>")
        
        # Validate HTML tags (basic validation)
        allowed_tags = ['<p>', '</p>', '<b>', '</b>', '<i>', '</i>', '<br>', '<br/>', '<br />']
        
        # Log the processed annotation length
        logger.info(f"Processed enhanced annotation: {len(processed)} characters")
        
        # Note: Boilerplate text will be added by the AnnotationProcessor when generating LSI CSV
        
        return processed
        
    def _process_enhanced_toc(self, toc_text: str) -> str:
        """
        Process and format a table of contents.
        
        Args:
            toc_text: Raw table of contents text
            
        Returns:
            Formatted table of contents
        """
        import re
        
        if not toc_text:
            return ""
        
        # Clean up the TOC text
        processed = toc_text.strip()
        
        # Ensure consistent formatting for page numbers
        dot_pattern = r'\.{3,}'
        processed = re.sub(dot_pattern, ' ', processed)
        
        # Ensure proper indentation for hierarchical structure
        lines = processed.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Check if this is a part/section header
            if re.match(r'^(?:Part|PART|Section|SECTION)', line):
                formatted_lines.append(line)
            # Check if this is a chapter
            elif re.match(r'^(?:Chapter|CHAPTER)', line):
                formatted_lines.append(f"  {line}")
            # Otherwise, assume it's a subsection or appendix
            elif line:
                if re.match(r'^(?:Appendix|APPENDIX)', line):
                    formatted_lines.append(line)
                else:
                    formatted_lines.append(f"    {line}")
        
        # Ensure it doesn't exceed 2000 characters
        result = "\n".join(formatted_lines)
        if len(result) > 2000:
            result = result[:1997] + "..."
        
        # Log the processed TOC length
        logger.info(f"Processed enhanced TOC: {len(result)} characters")
        
        return result
    
    def _truncate_book_content(self, book_content: Optional[str], prompt_key: str) -> str:
        """
        Truncate book content based on the prompt type to manage token usage.
        
        Args:
            book_content: The full book content
            prompt_key: The prompt key to determine truncation strategy
            
        Returns:
            Truncated book content appropriate for the prompt
        """
        if not book_content:
            return ""
            
        # Define max content lengths for different prompt types
        content_limits = {
            # For contributor info, we need more content to extract biographical details
            "extract_lsi_contributor_info": 15000,
            "generate_contributor_bio": 10000,
            # For classification, we need a good amount of content
            "suggest_bisac_codes": 8000,
            "suggest_thema_subjects": 8000,
            # For marketing copy, we need less content but enough for context
            "create_short_description": 5000,
            "generate_keywords": 5000,
            # For enhanced annotation, we need substantial content for compelling copy
            "generate_enhanced_annotation": 12000,
            # For audience determination, we need moderate content
            "determine_audience": 3000,
            "determine_age_range": 3000,
            # For series info, we need less content
            "suggest_series_info": 3000,
            # For illustration info, we need moderate content to detect visual elements
            "generate_illustration_info": 6000,
            # For enhanced TOC, we need good content structure visibility
            "generate_enhanced_toc": 8000,
            # Default limit for any other prompts
            "default": 5000
        }
        
        # Get the appropriate limit for this prompt
        limit = content_limits.get(prompt_key, content_limits["default"])
        
        # Truncate the content if it exceeds the limit
        if len(book_content) > limit:
            # Take the first third and last third of the content to capture intro and conclusion
            first_part = book_content[:limit // 3]
            last_part = book_content[-limit // 3:]
            middle_indicator = "\n\n[...content truncated for brevity...]\n\n"
            truncated_content = first_part + middle_indicator + last_part
            logger.info(f"Truncated book content for {prompt_key} from {len(book_content)} to {len(truncated_content)} characters")
            return truncated_content
        
        return book_content
    
    def _complete_field(self, metadata: CodexMetadata, field_name: str) -> str:
        """
        Complete a specific field using the appropriate prompt.
        
        Args:
            metadata: CodexMetadata object to use for prompt variables
            field_name: Name of the field to complete
            
        Returns:
            Completed field value or empty string if completion failed
        """
        # Find the prompt key for this field
        prompt_key = None
        for key, fields in self.prompt_field_mapping.items():
            if isinstance(fields, str) and fields == field_name:
                prompt_key = key
                break
            elif isinstance(fields, list) and field_name in fields:
                prompt_key = key
                break
        
        if not prompt_key:
            logger.warning(f"No prompt found for field {field_name}")
            return ""
        
        # Process the prompt
        result = self._process_prompt(prompt_key, metadata, None)
        if not result:
            return ""
        
        # Extract the field value from the result
        if isinstance(result, dict):
            # If result is a dictionary, try to find a matching key
            for key, value in result.items():
                if key == field_name or key in field_name or field_name in key:
                    return value
            
            # If no matching key found, use the first value
            if result:
                return next(iter(result.values()))
        elif isinstance(result, str):
            # If result is a string, use it directly
            return result
        
        return ""
    
    def _complete_field(self, metadata: CodexMetadata, field_name: str) -> str:
        """
        Complete a specific field using the appropriate prompt.
        
        Args:
            metadata: CodexMetadata object to update
            field_name: Name of the field to complete
            
        Returns:
            Completed field value or empty string if completion failed
        """
        # Find the prompt key for this field
        prompt_key = None
        for key, fields in self.prompt_field_mapping.items():
            if isinstance(fields, str) and fields == field_name:
                prompt_key = key
                break
            elif isinstance(fields, list) and field_name in fields:
                prompt_key = key
                break
        
        if not prompt_key:
            logger.warning(f"No prompt key found for field {field_name}")
            return ""
        
        # Check if we already have a completion for this prompt
        if hasattr(metadata, 'llm_completions') and prompt_key in metadata.llm_completions:
            result = metadata.llm_completions[prompt_key]
            
            # Extract the field value from the result
            if isinstance(result, dict):
                # Check for direct field match (case-insensitive)
                for key, value in result.items():
                    if key.lower() == field_name.lower() or key.lower() in field_name.lower() or field_name.lower() in key.lower():
                        logger.info(f"Using existing LLM completion for field {field_name} from {prompt_key}")
                        return value
                
                # Check for field name match (e.g., "bio" in "contributor_one_bio")
                field_name_part = field_name.split('_')[-1]
                for key, value in result.items():
                    if field_name_part.lower() in key.lower():
                        logger.info(f"Using existing LLM completion for field {field_name} based on field name {field_name_part}")
                        return value
                
                # If no matching key found but we have a "value" key, use that
                if "value" in result:
                    logger.info(f"Using 'value' from existing LLM completion for field {field_name}")
                    return result["value"]
                
                # If no matching key found, use the first non-metadata value
                for key, value in result.items():
                    if not key.startswith("_"):  # Skip metadata keys
                        logger.info(f"Using first non-metadata value from existing LLM completion for field {field_name}")
                        return value
            elif isinstance(result, str):
                # If result is a string, use it directly
                logger.info(f"Using existing LLM completion string for field {field_name}")
                return result
        
        # If we get here, we need to complete the field
        try:
            # Process the prompt
            result = self._process_prompt(prompt_key, metadata, None)
            if result:
                # Save LLM completion to metadata BEFORE filtering via field mapping strategies
                self._save_llm_completion(metadata, prompt_key, result)
                
                # Update metadata fields directly
                self._update_metadata_fields(metadata, prompt_key, result)
                
                # Extract the field value from the result
                if isinstance(result, dict):
                    # Check for direct field match (case-insensitive)
                    for key, value in result.items():
                        if key.lower() == field_name.lower() or key.lower() in field_name.lower() or field_name.lower() in key.lower():
                            return value
                    
                    # Check for field name match (e.g., "bio" in "contributor_one_bio")
                    field_name_part = field_name.split('_')[-1]
                    for key, value in result.items():
                        if field_name_part.lower() in key.lower():
                            return value
                    
                    # If no matching key found but we have a "value" key, use that
                    if "value" in result:
                        return result["value"]
                    
                    # If no matching key found, use the first non-metadata value
                    for key, value in result.items():
                        if not key.startswith("_"):  # Skip metadata keys
                            return value
                else:
                    # If result is not a dictionary, return it directly
                    return result
            
            return ""
        except Exception as e:
            logger.error(f"Error completing field {field_name}: {e}")
            return ""    
def _provide_fallback_value(self, prompt_key: str, metadata: CodexMetadata) -> Any:
        """
        Provide an intelligent fallback value when LLM completion fails.
        
        Args:
            prompt_key: Key of the prompt that failed
            metadata: CodexMetadata object to use for fallback value generation
            
        Returns:
            Fallback value for the prompt
        """
        # Check if the prompt has a defined fallback value
        prompt_data = self.prompts.get(prompt_key, {})
        fallback = prompt_data.get("fallback")
        
        if fallback:
            # If fallback is a string, format it with metadata values
            if isinstance(fallback, str):
                try:
                    # Helper function to safely get attributes
                    def safe_get_attr(obj, attr, default=""):
                        return getattr(obj, attr, default) or default
                    
                    # Format the fallback string with metadata values
                    formatted_fallback = fallback.format(
                        title=safe_get_attr(metadata, "title"),
                        author=safe_get_attr(metadata, "author"),
                        publisher=safe_get_attr(metadata, "publisher"),
                        summary_short=safe_get_attr(metadata, "summary_short"),
                        summary_long=safe_get_attr(metadata, "summary_long"),
                        keywords=safe_get_attr(metadata, "keywords"),
                        bisac_codes=safe_get_attr(metadata, "bisac_codes"),
                        isbn13=safe_get_attr(metadata, "isbn13"),
                        page_count=safe_get_attr(metadata, "page_count"),
                        trim_width_in=safe_get_attr(metadata, "trim_width_in", "6"),
                        trim_height_in=safe_get_attr(metadata, "trim_height_in", "9"),
                        rendition_booktype=safe_get_attr(metadata, "rendition_booktype", "Perfect Bound"),
                        audience=safe_get_attr(metadata, "audience"),
                        language=safe_get_attr(metadata, "language", "eng"),
                        subtitle=safe_get_attr(metadata, "subtitle"),
                        table_of_contents=safe_get_attr(metadata, "table_of_contents"),
                        publisher_reference_id=safe_get_attr(metadata, "publisher_reference_id")
                    )
                    
                    logger.info(f"Using formatted fallback value for prompt {prompt_key}")
                    return formatted_fallback
                except Exception as e:
                    logger.error(f"Error formatting fallback value for prompt {prompt_key}: {e}")
                    # Return the unformatted fallback value
                    return fallback
            else:
                # Return the fallback value as is (e.g., dictionary, list, etc.)
                logger.info(f"Using fallback value for prompt {prompt_key}")
                return fallback
        
        # If no fallback is defined, provide a generic fallback based on prompt key
        logger.warning(f"No fallback defined for prompt {prompt_key}. Using generic fallback.")
        
        # Map of prompt keys to generic fallback values
        generic_fallbacks = {
            "generate_contributor_bio": f"A respected expert in the field with extensive knowledge and experience related to {safe_get_attr(metadata, 'title')}.",
            "suggest_bisac_codes": {"bisac_category_2": "BUS000000", "bisac_category_3": "REF000000"},
            "generate_keywords": f"{safe_get_attr(metadata, 'title')}; {safe_get_attr(metadata, 'author')}; books; publishing; literature",
            "create_short_description": f"A compelling exploration of {safe_get_attr(metadata, 'title')} that offers valuable insights for readers.",
            "suggest_thema_subjects": {"thema_subject_1": "Y", "thema_subject_2": "J", "thema_subject_3": "D"},
            "determine_audience": "General",
            "determine_age_range": {"min_age": "18", "max_age": "Adult"},
            "extract_lsi_contributor_info": {
                "contributor_one_bio": f"A respected expert in the field with extensive knowledge and experience related to {safe_get_attr(metadata, 'title')}.",
                "contributor_one_affiliations": "Professional association in the relevant field",
                "contributor_one_professional_position": "Author and Subject Matter Expert",
                "contributor_one_location": "United States",
                "contributor_one_prior_work": "Published works in the field"
            },
            "suggest_series_info": {"series_name": "", "series_number": ""},
            "generate_enhanced_annotation": f"<p><b><i>Discover the fascinating world of {safe_get_attr(metadata, 'title')} in this compelling work by {safe_get_attr(metadata, 'author')}.</i></b></p><p>This book offers valuable insights and perspectives on an important topic that will engage readers from beginning to end. With expert analysis and engaging prose, it presents complex ideas in an accessible format.</p><p>Readers will appreciate the depth of research and clarity of presentation that makes this work both informative and enjoyable to read.</p>",
            "generate_illustration_info": {"illustration_count": "0", "illustration_notes": "No illustrations indicated in the available content."},
            "generate_enhanced_toc": f"Introduction ........................... 1\nChapter 1: Overview ........................... 5\nChapter 2: Main Content ....................... 15\nChapter 3: Further Discussion ................. 30\nConclusion ........................... 45\nReferences ........................... 50"
        }
        
        return generic_fallbacks.get(prompt_key, "")