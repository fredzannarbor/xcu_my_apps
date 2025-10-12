"""
Enhanced LSI Field Completer Module

This module provides enhanced functionality to complete LSI fields using LLM calls.
It includes improved retry logic, error handling, and fallback values.
"""

import os
import json
import logging
import re
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from ...core.llm_integration import call_model_with_prompt
from ...core.prompt_manager import load_and_prepare_prompts
from ..metadata.metadata_models import CodexMetadata
from .llm_field_completer import LLMFieldCompleter
from .enhanced_error_handler import EnhancedErrorHandler

logger = logging.getLogger(__name__)

# Initialize enhanced error handler
error_handler = EnhancedErrorHandler(logger)

class EnhancedLLMFieldCompleter(LLMFieldCompleter):
    """
    Enhanced version of LLMFieldCompleter with improved retry logic and error handling.
    
    This class extends the base LLMFieldCompleter with the following enhancements:
    - Retry logic with exponential backoff
    - Better error handling
    - Intelligent fallback values
    - Detailed error logging
    """
    
    def __init__(self, model_name: str = "gemini/gemini-2.5-flash", 
                 prompts_path: str = "prompts/enhanced_lsi_field_completion_prompts.json",
                 ensure_min_tokens: bool = True,
                 min_tokens: int = 8192):
        """
        Initialize the enhanced LLM field completer.
        
        Args:
            model_name: Name of the LLM model to use
            prompts_path: Path to the LSI field completion prompts file
            ensure_min_tokens: Whether to ensure minimum token count for responses
            min_tokens: Minimum token count to ensure (default 8192)
        """
        super().__init__(model_name, prompts_path)
        self.ensure_min_tokens = ensure_min_tokens
        self.min_tokens = min_tokens
    
    def complete_missing_fields(self, metadata: CodexMetadata, book_content: Optional[str] = None, 
                               save_to_disk: bool = True, output_dir: Optional[str] = None,
                               max_retries: int = 3, initial_delay: int = 2) -> CodexMetadata:
        """
        Complete missing LSI fields in the metadata object with enhanced error handling.
        
        Args:
            metadata: CodexMetadata object to complete
            book_content: Optional book content to use for field completion
            save_to_disk: Whether to save completions to disk
            output_dir: Directory to save completions (defaults to metadata/ parallel to covers/ and interiors/)
            max_retries: Maximum number of retry attempts for each prompt
            initial_delay: Initial delay in seconds before retrying (will be exponentially increased)
            
        Returns:
            Updated CodexMetadata object with completed fields
        """
        # Initialize llm_completions dictionary if it doesn't exist
        if not hasattr(metadata, 'llm_completions') or metadata.llm_completions is None:
            metadata.llm_completions = {}
        
        # Initialize tracking dictionaries if they don't exist
        if not hasattr(metadata, 'llm_completion_attempts'):
            metadata.llm_completion_attempts = {}
        if not hasattr(metadata, 'llm_completion_failures'):
            metadata.llm_completion_failures = {}
        
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
                    # Process the prompt with enhanced retry logic
                    result = self._process_prompt(prompt_key, metadata, book_content, max_retries, initial_delay)
                    
                    if result:
                        # Save LLM completions to metadata BEFORE filtering via field mapping strategies
                        self._save_llm_completion(metadata, prompt_key, result)
                        
                        logger.info(f"Completed {prompt_key} field")
                        newly_completed_fields.append(prompt_key)
                        
                        # Update metadata fields directly if configured
                        self._update_metadata_fields(metadata, prompt_key, result)
                    else:
                        # If result is None, log the error and continue
                        error_msg = f"Failed to complete {prompt_key} field after {max_retries} attempts"
                        logger.error(error_msg)
                        completion_errors.append(f"{prompt_key}: {error_msg}")
                        
                        # Use fallback value
                        fallback_result = self._provide_fallback_value(prompt_key, metadata)
                        if fallback_result:
                            # Save fallback value to metadata
                            self._save_llm_completion(metadata, prompt_key, fallback_result)
                            
                            logger.info(f"Using fallback value for {prompt_key} field")
                            newly_completed_fields.append(f"{prompt_key} (fallback)")
                            
                            # Update metadata fields with fallback value
                            self._update_metadata_fields(metadata, prompt_key, fallback_result)
                except Exception as e:
                    logger.error(f"Error processing prompt {prompt_key}: {e}")
                    completion_errors.append(f"{prompt_key}: {str(e)}")
                    
                    # Use enhanced error handler for recovery
                    recovery_method = error_handler.handle_field_completion_error(
                        error=e,
                        field_name=prompt_key,
                        completer_obj=self
                    )
                    
                    # Try to use the recovery method
                    try:
                        if callable(recovery_method):
                            fallback_result = recovery_method(metadata, prompt_key)
                        else:
                            fallback_result = self._provide_fallback_value(prompt_key, metadata)
                    except Exception as recovery_error:
                        logger.error(f"Recovery method failed for {prompt_key}: {recovery_error}")
                        fallback_result = self._provide_fallback_value(prompt_key, metadata)
                    
                    if fallback_result:
                        # Save fallback value to metadata
                        self._save_llm_completion(metadata, prompt_key, fallback_result)
                        
                        logger.info(f"Using fallback value for {prompt_key} field after exception")
                        newly_completed_fields.append(f"{prompt_key} (fallback)")
                        
                        # Update metadata fields with fallback value
                        self._update_metadata_fields(metadata, prompt_key, fallback_result)
        
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
                        "saved_path": saved_path,
                        "completion_attempts": metadata.llm_completion_attempts,
                        "completion_failures": metadata.llm_completion_failures
                    })
            except Exception as e:
                logger.error(f"Failed to save completions: {e}")
                # Don't let save failures stop the process
        
        return metadata
    
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
                
                # Make the LLM call with enhanced token limits and debugging
                response = call_model_with_prompt(
                    model_name=self.model_name,
                    prompt_config=prompt_config,
                    ensure_min_tokens=self.ensure_min_tokens,
                    min_tokens=self.min_tokens,
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
                
                # Use enhanced error handler for detailed logging
                error_handler.log_error_with_context(
                    error=e,
                    context={
                        'prompt_key': prompt_key,
                        'retry_count': retry_count,
                        'max_retries': max_retries,
                        'model_name': self.model_name
                    }
                )
                
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
                    
                    # Use enhanced error handler for final recovery attempt
                    recovery_method = error_handler.handle_field_completion_error(
                        error=e,
                        field_name=prompt_key,
                        completer_obj=self
                    )
                    
                    if callable(recovery_method):
                        try:
                            return recovery_method(metadata, prompt_key)
                        except Exception as recovery_error:
                            logger.error(f"Final recovery failed for {prompt_key}: {recovery_error}")
                    
                    # Return fallback value
                    return self._provide_fallback_value(prompt_key, metadata)
        
        # If we've exhausted all retries, record the failure and return fallback value
        if prompt_key not in metadata.llm_completion_failures:
            metadata.llm_completion_failures[prompt_key] = []
        metadata.llm_completion_failures[prompt_key].append(last_error or "Unknown error")
        
        logger.error(f"All {max_retries} attempts failed for prompt {prompt_key}. Using fallback value.")
        return self._provide_fallback_value(prompt_key, metadata)
    
    def _save_llm_completion(self, metadata: CodexMetadata, prompt_key: str, result: Any) -> None:
        """
        Save LLM completion to metadata.llm_completions.
        
        Args:
            metadata: CodexMetadata object to update
            prompt_key: Key of the prompt that generated the result
            result: Result of the LLM call
        """
        try:
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
            
            logger.info(f"Saved LLM completion for {prompt_key} to metadata.llm_completions")
        except Exception as e:
            logger.error(f"Error saving LLM completion for {prompt_key}: {e}")
    
    def _provide_fallback_value(self, prompt_key: str, metadata: CodexMetadata) -> Any:
        """
        Provide an intelligent fallback value when LLM completion fails.
        
        This method uses a sophisticated approach to generate fallback values:
        1. First, it checks if the prompt has a defined fallback value in the prompts file
        2. If so, it formats the fallback value with metadata values
        3. If not, it uses a field-specific fallback generator
        4. Each fallback generator ensures the value meets minimum LSI requirements
        
        Args:
            prompt_key: Key of the prompt that failed
            metadata: CodexMetadata object to use for fallback value generation
            
        Returns:
            Fallback value for the prompt that meets minimum LSI requirements
        """
        # Helper function to safely get attributes
        def safe_get_attr(obj, attr, default=""):
            return getattr(obj, attr, default) or default
        
        # Check if the prompt has a defined fallback value
        prompt_data = self.prompts.get(prompt_key, {})
        fallback = prompt_data.get("fallback")
        
        if fallback:
            # If fallback is a string, format it with metadata values
            if isinstance(fallback, str):
                try:
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
        
        # If no fallback is defined, use a field-specific fallback generator
        logger.info(f"No fallback defined for prompt {prompt_key}. Using field-specific fallback generator.")
        
        # Map of prompt keys to field-specific fallback generators
        fallback_generators = {
            "generate_contributor_bio": self._generate_contributor_bio_fallback,
            "suggest_bisac_codes": self._generate_bisac_codes_fallback,
            "generate_keywords": self._generate_keywords_fallback,
            "create_short_description": self._generate_short_description_fallback,
            "suggest_thema_subjects": self._generate_thema_subjects_fallback,
            "determine_audience": self._generate_audience_fallback,
            "determine_age_range": self._generate_age_range_fallback,
            "extract_lsi_contributor_info": self._generate_contributor_info_fallback,
            "suggest_series_info": self._generate_series_info_fallback,
            "generate_enhanced_annotation": self._generate_enhanced_annotation_fallback,
            "generate_illustration_info": self._generate_illustration_info_fallback,
            "generate_enhanced_toc": self._generate_enhanced_toc_fallback
        }
        
        # Use the field-specific fallback generator if available
        if prompt_key in fallback_generators:
            return fallback_generators[prompt_key](metadata)
        
        # If no field-specific fallback generator is available, use a generic fallback
        logger.warning(f"No field-specific fallback generator for prompt {prompt_key}. Using generic fallback.")
        
        # Generic fallback based on prompt key
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
        
    def _generate_contributor_bio_fallback(self, metadata: CodexMetadata) -> str:
        """
        Generate a fallback contributor bio that meets LSI requirements.
        
        LSI requirements for contributor bio:
        - Professional tone
        - Third-person perspective
        - 100-150 words
        - Relevant to the book topic
        
        Args:
            metadata: CodexMetadata object to use for fallback value generation
            
        Returns:
            Fallback contributor bio
        """
        # Helper function to safely get attributes
        def safe_get_attr(obj, attr, default=""):
            return getattr(obj, attr, default) or default
        
        # Get basic metadata
        title = safe_get_attr(metadata, "title")
        author = safe_get_attr(metadata, "author")
        publisher = safe_get_attr(metadata, "publisher")
        
        # Extract potential subject matter from BISAC codes or keywords
        bisac_codes = safe_get_attr(metadata, "bisac_codes", "")
        keywords = safe_get_attr(metadata, "keywords", "")
        
        # Determine subject area based on BISAC codes
        subject_area = "the field"
        if "BUS" in bisac_codes:
            subject_area = "business and management"
        elif "COM" in bisac_codes:
            subject_area = "computer science and technology"
        elif "SCI" in bisac_codes:
            subject_area = "science"
        elif "SOC" in bisac_codes:
            subject_area = "social sciences"
        elif "HIS" in bisac_codes:
            subject_area = "history"
        elif "PHI" in bisac_codes:
            subject_area = "philosophy"
        elif "REL" in bisac_codes:
            subject_area = "religion and spirituality"
        elif "PSY" in bisac_codes:
            subject_area = "psychology"
        elif "SEL" in bisac_codes:
            subject_area = "self-improvement"
        elif "FIC" in bisac_codes:
            subject_area = "fiction writing"
        
        # Generate a professional bio that meets LSI requirements
        bio = f"{author} is a respected expert in {subject_area} with extensive knowledge and experience related to {title}. "
        bio += f"With a background in research and education, {author.split()[0]} has dedicated years to studying and understanding the complexities of this important subject. "
        bio += f"As an author, {author.split()[0]} is known for presenting complex ideas in an accessible and engaging manner, making {title} a valuable resource for readers interested in {subject_area}. "
        bio += f"In addition to writing, {author.split()[0]} is actively involved in professional organizations and regularly contributes to academic and industry publications."
        
        return bio
    
    def _generate_bisac_codes_fallback(self, metadata: CodexMetadata) -> Dict[str, str]:
        """
        Generate fallback BISAC codes that meet LSI requirements.
        
        LSI requirements for BISAC codes:
        - Valid BISAC codes from the most recent standards
        - Relevant to the book topic
        
        Args:
            metadata: CodexMetadata object to use for fallback value generation
            
        Returns:
            Dictionary with bisac_category_2 and bisac_category_3
        """
        # Helper function to safely get attributes
        def safe_get_attr(obj, attr, default=""):
            return getattr(obj, attr, default) or default
        
        # Get basic metadata
        title = safe_get_attr(metadata, "title")
        keywords = safe_get_attr(metadata, "keywords", "")
        bisac_codes = safe_get_attr(metadata, "bisac_codes", "")
        
        # Default fallback BISAC codes
        fallback_codes = {
            "bisac_category_2": "BUS000000",  # BUSINESS & ECONOMICS / General
            "bisac_category_3": "REF000000"   # REFERENCE / General
        }
        
        # If we have an existing BISAC code, use it to determine related codes
        if bisac_codes:
            # Extract the category prefix (e.g., "BUS", "COM", etc.)
            prefix_match = re.search(r'([A-Z]{3})', bisac_codes)
            if prefix_match:
                prefix = prefix_match.group(1)
                
                # Map of category prefixes to related BISAC codes
                related_codes = {
                    "BUS": ["BUS000000", "BUS041000"],  # Business / General, Business / Management
                    "COM": ["COM000000", "COM051010"],  # Computers / General, Computers / Programming
                    "SCI": ["SCI000000", "SCI063000"],  # Science / General, Science / Study & Teaching
                    "SOC": ["SOC000000", "SOC026000"],  # Social Science / General, Social Science / Sociology
                    "HIS": ["HIS000000", "HIS037000"],  # History / General, History / World
                    "PHI": ["PHI000000", "PHI046000"],  # Philosophy / General, Philosophy / Individual Philosophers
                    "REL": ["REL000000", "REL062000"],  # Religion / General, Religion / Spirituality
                    "PSY": ["PSY000000", "PSY031000"],  # Psychology / General, Psychology / Social Psychology
                    "SEL": ["SEL000000", "SEL021000"],  # Self-Help / General, Self-Help / Personal Growth
                    "FIC": ["FIC000000", "FIC019000"]   # Fiction / General, Fiction / Literary
                }
                
                if prefix in related_codes:
                    fallback_codes["bisac_category_2"] = related_codes[prefix][0]
                    fallback_codes["bisac_category_3"] = related_codes[prefix][1]
        
        return fallback_codes
    
    def _generate_keywords_fallback(self, metadata: CodexMetadata) -> str:
        """
        Generate fallback keywords that meet LSI requirements.
        
        LSI requirements for keywords:
        - Semicolon-separated list
        - Relevant to the book topic
        - 8-12 keywords recommended
        
        Args:
            metadata: CodexMetadata object to use for fallback value generation
            
        Returns:
            Semicolon-separated list of keywords
        """
        # Helper function to safely get attributes
        def safe_get_attr(obj, attr, default=""):
            return getattr(obj, attr, default) or default
        
        # Get basic metadata
        title = safe_get_attr(metadata, "title")
        author = safe_get_attr(metadata, "author")
        bisac_codes = safe_get_attr(metadata, "bisac_codes", "")
        
        # Extract words from title (excluding common stop words)
        stop_words = {"the", "a", "an", "of", "in", "for", "to", "with", "by", "at", "from", "on"}
        title_words = [word.lower() for word in re.findall(r'\b\w+\b', title) if word.lower() not in stop_words]
        
        # Base keywords that are always included
        keywords = [title, author, "book", "publishing", "literature"]
        
        # Add keywords based on BISAC codes
        if "BUS" in bisac_codes:
            keywords.extend(["business", "management", "economics", "leadership", "strategy"])
        elif "COM" in bisac_codes:
            keywords.extend(["computers", "technology", "programming", "software", "digital"])
        elif "SCI" in bisac_codes:
            keywords.extend(["science", "research", "academic", "study", "education"])
        elif "SOC" in bisac_codes:
            keywords.extend(["social science", "sociology", "culture", "society", "research"])
        elif "HIS" in bisac_codes:
            keywords.extend(["history", "historical", "past", "events", "civilization"])
        elif "PHI" in bisac_codes:
            keywords.extend(["philosophy", "thinking", "ideas", "concepts", "theory"])
        elif "REL" in bisac_codes:
            keywords.extend(["religion", "spirituality", "faith", "belief", "practice"])
        elif "PSY" in bisac_codes:
            keywords.extend(["psychology", "mind", "behavior", "mental", "cognitive"])
        elif "SEL" in bisac_codes:
            keywords.extend(["self-help", "personal growth", "improvement", "development", "wellness"])
        elif "FIC" in bisac_codes:
            keywords.extend(["fiction", "novel", "story", "narrative", "literary"])
        
        # Add title words if we don't have enough keywords
        if len(keywords) < 8:
            keywords.extend(title_words)
        
        # Remove duplicates and limit to 12 keywords
        unique_keywords = []
        for keyword in keywords:
            if keyword.lower() not in [k.lower() for k in unique_keywords]:
                unique_keywords.append(keyword)
        
        # Format as semicolon-separated list
        return "; ".join(unique_keywords[:12])
    
    def _generate_short_description_fallback(self, metadata: CodexMetadata) -> str:
        """
        Generate a fallback short description that meets LSI requirements.
        
        LSI requirements for short description:
        - 1-2 sentences
        - Maximum 150 characters
        - Engaging and compelling
        
        Args:
            metadata: CodexMetadata object to use for fallback value generation
            
        Returns:
            Short description
        """
        # Helper function to safely get attributes
        def safe_get_attr(obj, attr, default=""):
            return getattr(obj, attr, default) or default
        
        # Get basic metadata
        title = safe_get_attr(metadata, "title")
        author = safe_get_attr(metadata, "author")
        bisac_codes = safe_get_attr(metadata, "bisac_codes", "")
        
        # Determine subject area based on BISAC codes
        subject_area = "important topic"
        if "BUS" in bisac_codes:
            subject_area = "business and management"
        elif "COM" in bisac_codes:
            subject_area = "technology and computing"
        elif "SCI" in bisac_codes:
            subject_area = "scientific principles"
        elif "SOC" in bisac_codes:
            subject_area = "social dynamics"
        elif "HIS" in bisac_codes:
            subject_area = "historical events"
        elif "PHI" in bisac_codes:
            subject_area = "philosophical concepts"
        elif "REL" in bisac_codes:
            subject_area = "spiritual understanding"
        elif "PSY" in bisac_codes:
            subject_area = "human psychology"
        elif "SEL" in bisac_codes:
            subject_area = "personal development"
        elif "FIC" in bisac_codes:
            subject_area = "compelling narrative"
        
        # Generate a short description (ensuring it's under 150 characters)
        description = f"A compelling exploration of {subject_area} that offers valuable insights for readers interested in {title}."
        
        # Truncate if necessary
        if len(description) > 150:
            description = description[:147] + "..."
        
        return description
    
    def _generate_thema_subjects_fallback(self, metadata: CodexMetadata) -> Dict[str, str]:
        """
        Generate fallback Thema subjects that meet LSI requirements.
        
        LSI requirements for Thema subjects:
        - Valid Thema codes from the most recent standards
        - Relevant to the book topic
        
        Args:
            metadata: CodexMetadata object to use for fallback value generation
            
        Returns:
            Dictionary with thema_subject_1, thema_subject_2, and thema_subject_3
        """
        # Helper function to safely get attributes
        def safe_get_attr(obj, attr, default=""):
            return getattr(obj, attr, default) or default
        
        # Get basic metadata
        bisac_codes = safe_get_attr(metadata, "bisac_codes", "")
        
        # Default fallback Thema subjects
        fallback_subjects = {
            "thema_subject_1": "Y",  # General
            "thema_subject_2": "J",  # Society & Social Sciences
            "thema_subject_3": "D"   # Biography, Literature & Literary Studies
        }
        
        # Map BISAC category prefixes to Thema subjects
        bisac_to_thema = {
            "BUS": ["K", "KJ", "KJM"],  # Economics, Finance, Business & Management
            "COM": ["U", "UD", "UDA"],  # Computing & Information Technology
            "SCI": ["P", "PD", "PDZ"],  # Mathematics & Science
            "SOC": ["J", "JH", "JHB"],  # Society & Social Sciences
            "HIS": ["N", "NH", "NHB"],  # History & Archaeology
            "PHI": ["Q", "QD", "QDH"],  # Philosophy & Religion
            "REL": ["Q", "QR", "QRA"],  # Philosophy & Religion
            "PSY": ["J", "JM", "JMH"],  # Society & Social Sciences
            "SEL": ["V", "VS", "VSP"],  # Health, Relationships & Personal Development
            "FIC": ["F", "FA", "FBA"]   # Fiction & Related Items
        }
        
        # Extract the category prefix (e.g., "BUS", "COM", etc.)
        prefix_match = re.search(r'([A-Z]{3})', bisac_codes)
        if prefix_match:
            prefix = prefix_match.group(1)
            
            if prefix in bisac_to_thema:
                fallback_subjects["thema_subject_1"] = bisac_to_thema[prefix][0]
                fallback_subjects["thema_subject_2"] = bisac_to_thema[prefix][1]
                fallback_subjects["thema_subject_3"] = bisac_to_thema[prefix][2]
        
        return fallback_subjects
    
    def _generate_audience_fallback(self, metadata: CodexMetadata) -> str:
        """
        Generate a fallback audience that meets LSI requirements.
        
        LSI requirements for audience:
        - One of: General, Academic, Professional, Young Adult, Children, Scholarly
        
        Args:
            metadata: CodexMetadata object to use for fallback value generation
            
        Returns:
            Audience category
        """
        # Helper function to safely get attributes
        def safe_get_attr(obj, attr, default=""):
            return getattr(obj, attr, default) or default
        
        # Get basic metadata
        bisac_codes = safe_get_attr(metadata, "bisac_codes", "")
        
        # Determine audience based on BISAC codes
        if "JUV" in bisac_codes or "JNF" in bisac_codes:
            return "Children"
        elif "YAF" in bisac_codes or "YAN" in bisac_codes:
            return "Young Adult"
        elif "EDU" in bisac_codes or "LAN" in bisac_codes:
            return "Academic"
        elif "BUS" in bisac_codes or "LAW" in bisac_codes or "MED" in bisac_codes:
            return "Professional"
        elif "SCI" in bisac_codes or "PHI" in bisac_codes:
            return "Scholarly"
        else:
            return "General"
    
    def _generate_age_range_fallback(self, metadata: CodexMetadata) -> Dict[str, str]:
        """
        Generate fallback age range that meets LSI requirements.
        
        LSI requirements for age range:
        - min_age: Single number
        - max_age: Single number or "Adult" for no upper limit
        
        Args:
            metadata: CodexMetadata object to use for fallback value generation
            
        Returns:
            Dictionary with min_age and max_age
        """
        # Helper function to safely get attributes
        def safe_get_attr(obj, attr, default=""):
            return getattr(obj, attr, default) or default
        
        # Get basic metadata
        bisac_codes = safe_get_attr(metadata, "bisac_codes", "")
        audience = safe_get_attr(metadata, "audience", "")
        
        # Determine age range based on BISAC codes and audience
        if "JUV" in bisac_codes:
            # Children's books
            if "JUV001" in bisac_codes:  # Baby-3
                return {"min_age": "0", "max_age": "3"}
            elif "JUV002" in bisac_codes:  # 4-8
                return {"min_age": "4", "max_age": "8"}
            elif "JUV003" in bisac_codes:  # 9-12
                return {"min_age": "9", "max_age": "12"}
            else:
                return {"min_age": "6", "max_age": "12"}
        elif "YAF" in bisac_codes or "YAN" in bisac_codes or audience == "Young Adult":
            # Young Adult books
            return {"min_age": "13", "max_age": "18"}
        else:
            # Adult books
            return {"min_age": "18", "max_age": "Adult"}
    
    def _generate_contributor_info_fallback(self, metadata: CodexMetadata) -> Dict[str, str]:
        """
        Generate fallback contributor information that meets LSI requirements.
        
        LSI requirements for contributor information:
        - Professional bio
        - Academic or professional affiliations
        - Current job title or position
        - Location (City, State/Country format)
        - Previous notable publications or achievements
        
        Args:
            metadata: CodexMetadata object to use for fallback value generation
            
        Returns:
            Dictionary with contributor information
        """
        # Helper function to safely get attributes
        def safe_get_attr(obj, attr, default=""):
            return getattr(obj, attr, default) or default
        
        # Get basic metadata
        title = safe_get_attr(metadata, "title")
        author = safe_get_attr(metadata, "author")
        bisac_codes = safe_get_attr(metadata, "bisac_codes", "")
        
        # Determine subject area based on BISAC codes
        subject_area = "the field"
        if "BUS" in bisac_codes:
            subject_area = "business and management"
        elif "COM" in bisac_codes:
            subject_area = "computer science and technology"
        elif "SCI" in bisac_codes:
            subject_area = "science"
        elif "SOC" in bisac_codes:
            subject_area = "social sciences"
        elif "HIS" in bisac_codes:
            subject_area = "history"
        elif "PHI" in bisac_codes:
            subject_area = "philosophy"
        elif "REL" in bisac_codes:
            subject_area = "religion and spirituality"
        elif "PSY" in bisac_codes:
            subject_area = "psychology"
        elif "SEL" in bisac_codes:
            subject_area = "self-improvement"
        elif "FIC" in bisac_codes:
            subject_area = "fiction writing"
        
        # Generate contributor information
        bio = self._generate_contributor_bio_fallback(metadata)
        
        return {
            "contributor_one_bio": bio,
            "contributor_one_affiliations": f"Professional association in {subject_area}",
            "contributor_one_professional_position": f"Author and Expert in {subject_area}",
            "contributor_one_location": "United States",
            "contributor_one_prior_work": f"Published works in {subject_area}"
        }
    
    def _generate_series_info_fallback(self, metadata: CodexMetadata) -> Dict[str, str]:
        """
        Generate fallback series information.
        
        Args:
            metadata: CodexMetadata object to use for fallback value generation
            
        Returns:
            Dictionary with series_name and series_number
        """
        # For series info, the default is to assume the book is not part of a series
        return {
            "series_name": "",
            "series_number": ""
        }
    
    def _generate_enhanced_annotation_fallback(self, metadata: CodexMetadata) -> str:
        """
        Generate a fallback enhanced annotation that meets LSI requirements.
        
        LSI requirements for enhanced annotation:
        - HTML formatting with <p>, <b>, <i>, <br> tags
        - Start with a dramatic hook in <b><i>bold italic</i></b>
        - 3-5 paragraphs
        - End with a call-to-action
        - Maximum 4000 characters
        
        Args:
            metadata: CodexMetadata object to use for fallback value generation
            
        Returns:
            HTML-formatted annotation
        """
        # Helper function to safely get attributes
        def safe_get_attr(obj, attr, default=""):
            return getattr(obj, attr, default) or default
        
        # Get basic metadata
        title = safe_get_attr(metadata, "title")
        author = safe_get_attr(metadata, "author")
        summary_short = safe_get_attr(metadata, "summary_short", "")
        summary_long = safe_get_attr(metadata, "summary_long", "")
        bisac_codes = safe_get_attr(metadata, "bisac_codes", "")
        
        # Determine subject area based on BISAC codes
        subject_area = "this important topic"
        if "BUS" in bisac_codes:
            subject_area = "business and management"
        elif "COM" in bisac_codes:
            subject_area = "technology and computing"
        elif "SCI" in bisac_codes:
            subject_area = "science and research"
        elif "SOC" in bisac_codes:
            subject_area = "social dynamics and cultural studies"
        elif "HIS" in bisac_codes:
            subject_area = "historical events and their significance"
        elif "PHI" in bisac_codes:
            subject_area = "philosophical concepts and ideas"
        elif "REL" in bisac_codes:
            subject_area = "spiritual understanding and practice"
        elif "PSY" in bisac_codes:
            subject_area = "human psychology and behavior"
        elif "SEL" in bisac_codes:
            subject_area = "personal growth and self-improvement"
        elif "FIC" in bisac_codes:
            subject_area = "this compelling narrative"
        
        # Generate a hook based on the title and subject area
        hook = f"Discover the fascinating world of {title} in this compelling work by {author}."
        
        # Generate paragraphs based on available information
        paragraphs = []
        
        # Add the hook as the first paragraph
        paragraphs.append(f"<p><b><i>{hook}</i></b></p>")
        
        # Add a paragraph based on the summary if available
        if summary_long:
            paragraphs.append(f"<p>{summary_long}</p>")
        elif summary_short:
            paragraphs.append(f"<p>{summary_short}</p>")
        else:
            paragraphs.append(f"<p>This book offers valuable insights and perspectives on {subject_area} that will engage readers from beginning to end. With expert analysis and engaging prose, it presents complex ideas in an accessible format.</p>")
        
        # Add a paragraph about the author's expertise
        paragraphs.append(f"<p>{author} brings years of expertise and a fresh perspective to {subject_area}, making this book both informative and engaging. Drawing from extensive research and personal experience, the author presents a comprehensive exploration that will appeal to both newcomers and experts alike.</p>")
        
        # Add a paragraph about the book's value
        paragraphs.append(f"<p>Readers will appreciate the depth of research and clarity of presentation that makes this work both informative and enjoyable to read. With practical insights and thoughtful analysis, {title} stands out as an essential resource for anyone interested in {subject_area}.</p>")
        
        # Add a call-to-action as the final paragraph
        paragraphs.append(f"<p>Don't miss this opportunity to expand your understanding of {subject_area}. Get your copy of {title} today and discover why readers and critics alike are praising this exceptional work.</p>")
        
        # Combine paragraphs into a single annotation
        annotation = "\n".join(paragraphs)
        
        # Ensure the annotation is under 4000 characters
        if len(annotation) > 4000:
            # Truncate the annotation and add a closing paragraph tag
            annotation = annotation[:3997] + "..."
            
            # Ensure we don't cut off in the middle of an HTML tag
            last_open_tag = annotation.rfind("<")
            last_close_tag = annotation.rfind(">")
            
            if last_open_tag > last_close_tag:
                annotation = annotation[:last_open_tag] + "..."
        
        return annotation
    
    def _generate_illustration_info_fallback(self, metadata: CodexMetadata) -> Dict[str, str]:
        """
        Generate fallback illustration information.
        
        Args:
            metadata: CodexMetadata object to use for fallback value generation
            
        Returns:
            Dictionary with illustration_count and illustration_notes
        """
        # For illustration info, the default is to assume no illustrations
        return {
            "illustration_count": "0",
            "illustration_notes": "No illustrations indicated in the available content."
        }
    
    def _generate_enhanced_toc_fallback(self, metadata: CodexMetadata) -> str:
        """
        Generate a fallback enhanced table of contents that meets LSI requirements.
        
        LSI requirements for enhanced TOC:
        - Proper hierarchical formatting
        - Include chapter numbers and titles
        - Add page numbers
        - Maximum 2000 characters
        
        Args:
            metadata: CodexMetadata object to use for fallback value generation
            
        Returns:
            Formatted table of contents
        """
        # Helper function to safely get attributes
        def safe_get_attr(obj, attr, default=""):
            return getattr(obj, attr, default) or default
        
        # Get basic metadata
        title = safe_get_attr(metadata, "title")
        page_count = safe_get_attr(metadata, "page_count", "100")
        
        # Convert page_count to integer if possible
        try:
            page_count = int(page_count)
        except (ValueError, TypeError):
            page_count = 100
        
        # Calculate approximate page numbers based on total page count
        intro_page = 1
        chapter1_page = intro_page + 4
        chapter2_page = chapter1_page + int(page_count * 0.2)
        chapter3_page = chapter2_page + int(page_count * 0.2)
        chapter4_page = chapter3_page + int(page_count * 0.2)
        conclusion_page = chapter4_page + int(page_count * 0.2)
        references_page = conclusion_page + 5
        
        # Generate a generic table of contents
        toc = f"Introduction ........................... {intro_page}\n"
        toc += f"Chapter 1: Overview of {title} ........................... {chapter1_page}\n"
        toc += f"Chapter 2: Key Concepts and Principles ........................... {chapter2_page}\n"
        toc += f"Chapter 3: Applications and Examples ........................... {chapter3_page}\n"
        toc += f"Chapter 4: Advanced Topics and Future Directions ........................... {chapter4_page}\n"
        toc += f"Conclusion ........................... {conclusion_page}\n"
        toc += f"References ........................... {references_page}"
        
        # Ensure the TOC is under 2000 characters
        if len(toc) > 2000:
            toc = toc[:1997] + "..."
        
        return toc