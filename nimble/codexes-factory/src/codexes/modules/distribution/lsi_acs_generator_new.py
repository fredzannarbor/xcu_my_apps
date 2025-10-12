# src/codexes/modules/distribution/lsi_acs_generator_new.py

import os
import csv
import logging
from typing import Optional, List
from ..metadata.metadata_models import CodexMetadata
from .field_mapping import FieldMappingRegistry
from .enhanced_field_mappings import create_comprehensive_lsi_registry
from ..verifiers.validation_framework import LSIValidationPipeline
from .lsi_configuration import LSIConfiguration
from .lsi_logging_manager import LSILoggingManager

from .tranche_config_debugger import TrancheConfigDebugger
from .robust_config_handler import RobustConfigurationHandler
from .batch_processing_reporter import BatchProcessingReporter, BookProcessingResult
from .memory_performance_optimizer import get_global_optimizer, memory_optimized

from .spine_width_calculator import get_spine_calculator


print("Defining LsiAcsGenerator class...")

class LsiAcsGenerator:
    """
    Generates LSI ACS-compatible CSV files from CodexMetadata objects.
    Enhanced with field mapping strategies, validation pipeline, and configuration management.
    """

    def __init__(self, template_path: str, config_path: Optional[str] = None, 
                 tranche_name: Optional[str] = None, log_directory: str = "logs/lsi_generation"):
        """
        Initialize the LSI ACS Generator.
        
        Args:
            template_path: Path to the LSI template CSV file
            config_path: Optional path to configuration file
            tranche_name: Optional name of the tranche configuration to use
            log_directory: Directory for detailed logging
        """
        self.tranche_name = tranche_name
        self.template_path = template_path
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        # Initialize comprehensive logging manager
        self.logging_manager = LSILoggingManager(log_directory)
        
        # Initialize configuration management
        self.config = LSIConfiguration(config_path)
        
        # Initialize LLM field completer for intelligent field completion
        from .enhanced_llm_field_completer import EnhancedLLMFieldCompleter
        
        # Ensure environment variables are loaded
        from dotenv import load_dotenv
        load_dotenv()
        
        self.llm_field_completer = EnhancedLLMFieldCompleter()
        
        # Initialize field mapping registry with comprehensive strategies
        self.field_registry = create_comprehensive_lsi_registry(
            config=self.config,
            llm_field_completer=self.llm_field_completer,
            tranche_name=self.tranche_name
        )
        
        # Load tranche configuration and make it available to field strategies
        if self.tranche_name:
            self._load_tranche_config_for_field_mapping()
        
        # Initialize validation pipeline
        self.validation_pipeline = LSIValidationPipeline()
        
        # Load and register additional field mappings from configuration
        self._setup_enhanced_field_mappings()
        
        # Initialize advanced territorial pricing strategy
        self._setup_advanced_pricing()
        
        # Initialize series integration (will be set up later if needed)
        self.series_integrator = None
        
        
        
        # Initialize enhanced error handling and debugging
        self.config_handler = RobustConfigurationHandler()
        self.tranche_debugger = TrancheConfigDebugger()
        self.batch_reporter = BatchProcessingReporter()
        self.memory_optimizer = get_global_optimizer()

        # Initialize field corrections validator
        from .field_corrections_validator import FieldCorrectionsValidator
        self.field_validator = FieldCorrectionsValidator()
        
        self.logging_manager.log_info(f"LSI ACS Generator initialized with {len(self.field_registry.get_registered_fields())} field mappings")

    def _load_tranche_config_for_field_mapping(self):
        """Load tranche configuration and make it available to field mapping strategies."""
        try:
            import os
            import json
            
            tranche_config_path = f"configs/tranches/{self.tranche_name}.json"
            if os.path.exists(tranche_config_path):
                with open(tranche_config_path, 'r') as f:
                    tranche_config = json.load(f)
                
                # Update the field registry's context config with tranche data
                if not hasattr(self.field_registry, 'context_config'):
                    self.field_registry.context_config = {}
                
                # Add tranche configuration to context
                self.field_registry.context_config.update(tranche_config)
                self.field_registry.context_config['tranche_name'] = self.tranche_name
                
                self.logging_manager.log_info(f"Loaded tranche configuration for field mapping: {self.tranche_name}")
                
                # Log some key tranche overrides
                tranche_fields = [
                    "Contributor One BIO", "Contributor One Affiliations", 
                    "Contributor One Location", "Series Name"
                ]
                for field in tranche_fields:
                    if field in tranche_config:
                        self.logging_manager.log_info(f"Tranche override for {field}: {str(tranche_config[field])[:50]}...")
            else:
                self.logging_manager.log_warning(f"Tranche configuration file not found: {tranche_config_path}")
                
        except Exception as e:
            self.logging_manager.log_error(f"Error loading tranche configuration: {e}")

    def _setup_enhanced_field_mappings(self):
        """Setup enhanced field mappings from configuration and add missing LSI fields."""
        # Since we're now using comprehensive field mappings, we only need to add
        # any custom or override mappings that aren't handled by the comprehensive registry
        
        # Check for any missing fields in the template
        template_headers = self._read_template_headers()
        missing_fields = []
        
        for header in template_headers:
            if not self.field_registry.has_strategy(header):
                missing_fields.append(header)
        
        if missing_fields:
            self.logging_manager.log_warning(f"Found {len(missing_fields)} unmapped fields in template: {missing_fields}")
            
            # Add default empty mappings for any missing fields
            from .field_mapping import DefaultMappingStrategy
            for field in missing_fields:
                self.field_registry.register_strategy(field, DefaultMappingStrategy(""))
                self.logging_manager.log_info(f"Added default empty mapping for field: {field}")
        
        self.logging_manager.log_info(f"Enhanced field mappings setup complete. Total mappings: {len(self.field_registry.get_registered_fields())}")

    def _setup_advanced_pricing(self):
        """Initialize advanced territorial pricing strategy."""
        try:
            from .territorial_pricing import TerritorialPricingStrategy, TerritorialPricingConfig, MarketSpecificPricingStrategy
            
            # Create pricing configuration with configurable parameters
            pricing_config = TerritorialPricingConfig(
                base_currency="USD",
                wiggle_room_percent=5.0,  # 5% wiggle room for unexpected variations
                market_access_fee_usd=0.0,  # No market access fee by default
                cache_duration_hours=24
            )
            
            # Initialize territorial pricing strategy
            territorial_strategy = TerritorialPricingStrategy(pricing_config)
            
            # Initialize market-specific pricing strategy
            self.territorial_pricing_strategy = MarketSpecificPricingStrategy(territorial_strategy)
            
            self.logging_manager.log_info("Advanced territorial pricing strategy initialized")
            
        except Exception as e:
            self.logging_manager.log_warning(f"Failed to initialize advanced pricing strategy: {e}. Using fallback pricing.")
            self.territorial_pricing_strategy = None

    def _create_territorial_pricing_mappings(self):
        """Create mapping strategies for all territorial pricing fields."""
        from .field_mapping import ComputedMappingStrategy
        
        # Define all territorial pricing fields from the LSI template
        territorial_fields = [
            # Standard international territories
            ("GC", "GC Suggested List Price (mode 2)", "GC Wholesale Discount % (Mode 2)"),
            
            # US specialized territories
            ("USBR1", "USBR1 Suggested List Price (mode 2)", "USBR1 Wholesale Discount % (Mode 2)"),
            ("USDE1", "USDE1 Suggested List Price (mode 2)", "USDE1 Wholesale Discount % (Mode 2)"),
            ("USRU1", "USRU1 Suggested List Price (mode 2)", "USRU1 Wholesale Discount % (Mode 2)"),
            ("USPL1", "USPL1 Suggested List Price (mode 2)", "USPL1 Wholesale Discount % (Mode 2)"),
            ("USKR1", "USKR1 Suggested List Price (mode 2)", "USKR1 Wholesale Discount % (Mode 2)"),
            ("USCN1", "USCN1 Suggested List Price (mode 2)", "USCN1 Wholesale Discount % (Mode 2)"),
            ("USIN1", "USIN1 Suggested List Price (mode 2)", "USIN1 Wholesale Discount % (Mode 2)"),
            ("USJP2", "USJP2 Suggested List Price(mode 2)", "USJP2 Wholesale Discount % (Mode 2)"),
            ("UAEUSD", "UAEUSD Suggested List Price (mode 2)", "UAEUSD Wholesale Discount % (Mode 2)"),
            
            # Special US territories
            ("US-Ingram-Only", "US-Ingram-Only* Suggested List Price (mode 2)", "US-Ingram-Only* Wholesale Discount % (Mode 2)"),
            ("US-Ingram-GAP", "US - Ingram - GAP * Suggested List Price (mode 2)", "US - Ingram - GAP * Wholesale Discount % (Mode 2)"),
            ("SIBI-EDUC-US", "SIBI - EDUC - US * Suggested List Price (mode 2)", "SIBI - EDUC - US * Wholesale Discount % (Mode 2)"),
        ]
        
        mappings = {}
        
        for territory_code, price_field, discount_field in territorial_fields:
            # Create computed strategies for pricing fields
            mappings[price_field] = ComputedMappingStrategy(
                lambda metadata, context, territory=territory_code: self._compute_territorial_price(metadata, territory)
            )
            mappings[discount_field] = ComputedMappingStrategy(
                lambda metadata, context, territory=territory_code: self._compute_territorial_discount(metadata, territory)
            )
        
        return mappings

    def _compute_territorial_price(self, metadata: CodexMetadata, territory: str) -> str:
        """Compute territorial pricing using advanced pricing strategies."""
        try:
            # Handle special mode 2 fields that should be blank per punch list task 11
            special_blank_territories = [
                "US-Ingram-Only", "US-Ingram-GAP", "SIBI-EDUC-US"
            ]
            
            if territory in special_blank_territories:
                return ""  # These should be blank per punch list requirements
            
            # Get base US price
            base_price = metadata.list_price_usd
            if not base_price:
                return ""
            
            # Convert to float if needed
            if isinstance(base_price, str):
                # Remove dollar sign if present
                base_price = float(base_price.replace('$', ''))
            
            # For GC market and US-prefixed territories, always use US price
            gc_territories = ["GC", "USBR1", "USDE1", "USRU1", "USPL1", "USKR1", "USCN1", "USIN1", "USJP2", "UAEUSD"]
            if territory in gc_territories:
                self.logging_manager.log_info(f"Using US price for {territory} market: ${base_price:.2f}")
                return f"${base_price:.2f}"
            
            # For other territories, use advanced territorial pricing if available
            if hasattr(self, 'territorial_pricing_strategy'):
                try:
                    # Get territorial configuration to determine currency
                    territorial_config = self.config.get_territorial_config(territory)
                    target_currency = territorial_config.currency if territorial_config else "USD"
                    
                    # Calculate price using advanced strategy
                    price_result = self.territorial_pricing_strategy.calculate_market_price(base_price, territory)
                    
                    if price_result["success"]:
                        return price_result["formatted_price"]
                    else:
                        self.logging_manager.log_warning(f"Advanced pricing failed for {territory}, using fallback")
                except Exception as e:
                    self.logging_manager.log_warning(f"Advanced pricing error for {territory}: {e}, using fallback")
            
            # Fallback to simple territorial configuration
            territorial_config = self.config.get_territorial_config(territory)
            if territorial_config and hasattr(territorial_config, 'pricing_multiplier'):
                adjusted_price = base_price * territorial_config.pricing_multiplier
                currency_symbol = getattr(territorial_config, 'currency', '$')
                if currency_symbol != '$':
                    # Get proper currency symbol
                    from .territorial_pricing import TerritorialPricingStrategy
                    temp_strategy = TerritorialPricingStrategy()
                    currency_symbol = temp_strategy.get_currency_symbol(currency_symbol)
                return f"{currency_symbol}{adjusted_price:.2f}"
            
            # Default: use same price as US
            return f"${base_price:.2f}"
            
        except Exception as e:
            logging.warning(f"Error computing territorial price for {territory}: {e}")
            return ""

    def _compute_territorial_discount(self, metadata: CodexMetadata, territory: str) -> str:
        """Compute territorial discount based on territory configuration."""
        try:
            # Handle special mode 2 fields that should be blank per punch list task 11
            special_blank_territories = [
                "US-Ingram-Only", "US-Ingram-GAP", "SIBI-EDUC-US"
            ]
            
            if territory in special_blank_territories:
                return ""  # These should be blank per punch list requirements
            
            # Get discount from configuration system
            imprint = metadata.imprint or "default"
            
            # Try to get territorial-specific discount
            territorial_config = self.config.get_territorial_config(territory)
            if territorial_config and hasattr(territorial_config, 'wholesale_discount_percent'):
                discount = territorial_config.wholesale_discount_percent
                if discount:
                    # Ensure it has % sign if not already present
                    if not str(discount).endswith('%'):
                        discount = f"{discount}%"
                    return discount
            
            # Fallback to default wholesale discount from config
            default_discount = self.config.get_default_value("us_wholesale_discount")  # Use us_wholesale_discount as default
            if default_discount:
                if not str(default_discount).endswith('%'):
                    default_discount = f"{default_discount}%"
                return default_discount
            
            # Final fallback
            return "40%"
            
        except Exception as e:
            logging.warning(f"Error computing territorial discount for {territory}: {e}")
            return "40%"

    def _compute_weight(self, metadata: CodexMetadata, context) -> str:
        """Compute book weight based on page count and trim size."""
        try:
            page_count = metadata.page_count or 0
            if page_count == 0:
                return ""
            
            # Basic weight calculation: approximately 0.0025 lbs per page for standard paper
            # This is a rough estimate and can be refined based on paper type and trim size
            estimated_weight = page_count * 0.0025
            return f"{estimated_weight:.2f}"
        except Exception as e:
            logging.warning(f"Error computing weight: {e}")
            return ""

    def _compute_returnability(self, metadata: CodexMetadata, context) -> str:
        """Compute returnability based on configuration."""
        try:
            # Get territory from context if available
            territory = None
            if hasattr(context, 'field_name'):
                # Try to extract territory from field name
                field_name = context.field_name
                if "Returnable" in field_name and "-" in field_name:
                    territory = field_name.split("-")[0].strip()
            
            # Default to US if territory not detected
            territory = territory or "US"
            
            # Get territorial configuration
            territorial_config = self.config.get_territorial_config(territory)
            if territorial_config and hasattr(territorial_config, 'returnability'):
                return territorial_config.returnability
            
            # Fallback to default returnability from config
            default_returnability = self.config.get_default_value("returnability")
            if default_returnability:
                return default_returnability
            
            # Final fallback based on territory
            return "Yes - Destroy" if territory == "US" else "No"
            
        except Exception as e:
            logging.warning(f"Error computing returnability for {territory if 'territory' in locals() else 'unknown'}: {e}")
            return "Yes - Destroy" if territory == "US" else "No"

    def validate_submission(self, metadata: CodexMetadata):
        """
        Validate metadata for LSI submission requirements.
        
        Args:
            metadata: CodexMetadata object to validate
            
        Returns:
            ValidationResult with validation outcomes
        """
        return self.validation_pipeline.validate(metadata)

    def generate_with_validation(self, metadata: CodexMetadata, output_path: str, **kwargs):
        """
        Generate LSI ACS CSV with validation and comprehensive reporting.
        
        Args:
            metadata: CodexMetadata object containing the book metadata
            output_path: Path where the CSV file should be saved
            **kwargs: Additional generation options
            
        Returns:
            GenerationResult with validation and generation outcomes
        """
        from .generation_result import GenerationReporter
        
        # Start comprehensive logging session
        session_id = self.logging_manager.start_generation_session(metadata, output_path)
        
        # Initialize generation reporter
        reporter = GenerationReporter()
        result = reporter.start_generation(output_path)
        
        try:
            # Store source metadata summary
            result.source_metadata_summary = {
                "title": metadata.title or "Unknown",
                "author": metadata.author or "Unknown",
                "isbn": metadata.isbn13 or "Unknown",
                "publisher": metadata.publisher or "Unknown",
                "imprint": metadata.imprint or "Unknown"
            }
            
            # Start validation timing
            self.logging_manager.start_operation_timing("validation")
            
            # Validate metadata first
            validation_result = self.validate_submission(metadata)
            
            # Log validation timing and results
            validation_time = self.logging_manager.end_operation_timing("validation")
            self.logging_manager.log_performance_metric("validation_time", validation_time)
            self.logging_manager.log_validation_summary(validation_result)
            
            # Check for blocking errors
            if validation_result.has_blocking_errors():
                error_msg = f"Validation failed with blocking errors: {validation_result.errors}"
                self.logging_manager.log_error(error_msg)
                reporter.add_error(error_msg)
                reporter.complete_generation(False, validation_result)
                self.logging_manager.complete_generation_session(False)
                return result
            
            # Log warnings if any
            if validation_result.warnings:
                warning_msg = f"Validation warnings: {validation_result.warnings}"
                self.logging_manager.log_warning(warning_msg)
                reporter.add_warning(warning_msg)
            
            # Start CSV generation timing
            self.logging_manager.start_operation_timing("csv_generation")
            
            # Generate the CSV with detailed tracking
            self._generate_with_comprehensive_logging(metadata, output_path, reporter, **kwargs)
            
            # Log CSV generation timing
            generation_time = self.logging_manager.end_operation_timing("csv_generation")
            self.logging_manager.log_performance_metric("csv_generation_time", generation_time)
            
            # Get final file size for logging
            final_file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            
            # Complete generation tracking
            reporter.complete_generation(True, validation_result)
            
            # Complete comprehensive logging session
            self.logging_manager.complete_generation_session(True, final_file_size)
            
            self.logging_manager.log_info(f"LSI ACS generation completed: {result.get_summary()}")
            return result
            
        except Exception as e:
            error_msg = f"Generation failed: {str(e)}"
            self.logging_manager.log_error(error_msg)
            reporter.add_error(error_msg)
            reporter.complete_generation(False, validation_result if 'validation_result' in locals() else None)
            self.logging_manager.complete_generation_session(False)
            return result

    def _ensure_series_data(self, metadata: CodexMetadata) -> CodexMetadata:
        """
        Ensure that series data is properly set in metadata before generation.
        
        Args:
            metadata: CodexMetadata object to update
            
        Returns:
            Updated CodexMetadata object with series information
        """
        # If we have a series integrator, use it to ensure series data
        if hasattr(self, 'series_integrator') and self.series_integrator:
            try:
                metadata = self.series_integrator.ensure_series_data(metadata)
                self.logging_manager.log_info(f"Series data ensured for book: {metadata.title}")
            except Exception as e:
                self.logging_manager.log_warning(f"Error ensuring series data: {e}")
        
        return metadata
    
    def _calculate_and_override_spine_width(self, metadata: CodexMetadata) -> CodexMetadata:
        """
        Calculate spine width based on page count and paper type, overriding any configured value.
        This ensures spine width is always calculated according to LSI standards.
        
        Args:
            metadata: CodexMetadata object to update
            
        Returns:
            Updated CodexMetadata object with calculated spine width
        """
        try:
            # Get spine width calculator
            spine_calculator = get_spine_calculator()
            
            # Extract metadata as dictionary for calculation
            metadata_dict = {}
            
            # Map CodexMetadata attributes to dictionary
            if hasattr(metadata, 'page_count') and metadata.page_count:
                metadata_dict['page_count'] = metadata.page_count
            elif hasattr(metadata, 'pages') and metadata.pages:
                metadata_dict['page_count'] = metadata.pages
            
            if hasattr(metadata, 'paper_color') and metadata.paper_color:
                metadata_dict['paper_color'] = metadata.paper_color
            elif hasattr(metadata, 'paper_type') and metadata.paper_type:
                metadata_dict['paper_color'] = metadata.paper_type
            
            if hasattr(metadata, 'binding_type') and metadata.binding_type:
                metadata_dict['binding_type'] = metadata.binding_type
            elif hasattr(metadata, 'binding') and metadata.binding:
                metadata_dict['binding_type'] = metadata.binding
            
            # Calculate spine width using the calculator
            if 'page_count' in metadata_dict:
                result = spine_calculator.calculate_from_metadata(metadata_dict)
                
                # Format spine width to 4 decimal places
                calculated_spine_width = f"{result.spine_width_inches:.4f}"
                
                # Override spine width in metadata
                original_spine_width = getattr(metadata, 'spine_width', None)
                metadata.spine_width = calculated_spine_width
                
                # Log the calculation
                if original_spine_width and str(original_spine_width) != calculated_spine_width:
                    self.logging_manager.log_info(
                        f"Overrode spine width: {original_spine_width} -> {calculated_spine_width} "
                        f"(calculated from {result.page_count} pages, {result.paper_type} paper, {result.binding_type} binding)"
                    )
                else:
                    self.logging_manager.log_info(
                        f"Set calculated spine width: {calculated_spine_width} "
                        f"({result.page_count} pages, {result.paper_type} paper, {result.binding_type} binding)"
                    )
                
                # Add calculation notes if available
                if result.notes:
                    self.logging_manager.log_info(f"Spine calculation notes: {result.notes}")
            
            else:
                self.logging_manager.log_warning(
                    f"Cannot calculate spine width for book '{metadata.title}': page count not available"
                )
            
        except Exception as e:
            self.logging_manager.log_error(f"Error calculating spine width for book '{metadata.title}': {e}")
            # Continue with original metadata if calculation fails
        
        return metadata
    
    def generate_batch_csv(self, metadata_list: List[CodexMetadata], output_path: str, **kwargs):
        """
        Generate LSI ACS CSV with multiple book rows from pipeline job.
        Enhanced with error isolation and recovery mechanisms.
        
        Args:
            metadata_list: List of CodexMetadata objects from pipeline
            output_path: Path where the CSV file should be saved
            **kwargs: Additional generation options
            
        Returns:
            GenerationResult with validation and generation outcomes for all books
        """
        from .generation_result import GenerationReporter
        
        # Initialize generation reporter for batch processing
        reporter = GenerationReporter()
        result = reporter.start_generation(output_path)
        
        # Batch processing statistics
        batch_stats = {
            'total_books': len(metadata_list),
            'successful_books': 0,
            'failed_books': 0,
            'skipped_books': 0,
            'processing_errors': []
        }
        
        try:
            # Check if metadata_list is empty
            if not metadata_list:
                error_msg = "Cannot generate batch CSV: No metadata provided"
                self.logging_manager.log_error(error_msg)
                reporter.add_error(error_msg)
                reporter.complete_generation(False, None)
                return result
                
            # Start a generation session with the first metadata object
            session_id = self.logging_manager.start_generation_session(metadata_list[0], output_path)
            self.logging_manager.log_info(f"Starting batch generation session {session_id} with {len(metadata_list)} books")
            
            # Read template headers once
            try:
                template_headers = self._read_template_headers()
            except Exception as e:
                error_msg = f"Failed to read template headers: {str(e)}"
                self.logging_manager.log_error(error_msg)
                reporter.add_error(error_msg)
                reporter.complete_generation(False, None)
                return result
            
            # Collect all book rows with error isolation
            all_book_rows = []
            batch_validation_results = []
            
            for i, metadata in enumerate(metadata_list):
                book_title = getattr(metadata, 'title', f'Book_{i+1}')
                self.logging_manager.log_info(f"Processing book {i+1}/{len(metadata_list)}: {book_title}")
                
                try:
                    # Ensure series data is properly set before validation and mapping
                    metadata = self._ensure_series_data(metadata)
                    
                    # Calculate and override spine width based on page count and paper type
                    metadata = self._calculate_and_override_spine_width(metadata)
                    
                    # Validate each book with error isolation
                    try:
                        validation_result = self.validate_submission(metadata)
                        batch_validation_results.append(validation_result)
                    except Exception as e:
                        error_msg = f"Validation failed for book '{book_title}': {str(e)}"
                        self.logging_manager.log_error(error_msg)
                        batch_stats['processing_errors'].append(error_msg)
                        # Create a failed validation result
                        from ..verifiers.validation_framework import ValidationResult
                        validation_result = ValidationResult(
                            is_valid=False,
                            field_results=[],
                            errors=[error_msg],
                            warnings=[]
                        )
                        batch_validation_results.append(validation_result)
                    
                    # Map metadata to LSI format with error isolation
                    try:
                        lsi_data = self._map_metadata_with_comprehensive_logging(metadata, template_headers, reporter)
                        all_book_rows.append(lsi_data)
                        batch_stats['successful_books'] += 1
                        self.logging_manager.log_info(f"✅ Successfully processed book '{book_title}'")
                    except Exception as e:
                        error_msg = f"Field mapping failed for book '{book_title}': {str(e)}"
                        self.logging_manager.log_error(error_msg)
                        batch_stats['processing_errors'].append(error_msg)
                        batch_stats['failed_books'] += 1
                        
                        # Create empty row to maintain CSV structure
                        empty_row = [''] * len(template_headers)
                        # Fill in basic info if available
                        try:
                            if hasattr(metadata, 'title') and metadata.title:
                                title_index = template_headers.index('title') if 'title' in template_headers else -1
                                if title_index >= 0:
                                    empty_row[title_index] = f"ERROR: {book_title}"
                        except:
                            pass
                        all_book_rows.append(empty_row)
                        
                except Exception as e:
                    error_msg = f"Critical error processing book '{book_title}': {str(e)}"
                    self.logging_manager.log_error(error_msg)
                    batch_stats['processing_errors'].append(error_msg)
                    batch_stats['failed_books'] += 1
                    
                    # Add empty row to maintain CSV structure
                    empty_row = [''] * len(template_headers)
                    all_book_rows.append(empty_row)
            
            # Write the batch CSV with all books (including failed ones)
            try:
                with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    # Write header row from template
                    writer.writerow(template_headers)
                    # Write all book data rows
                    for book_row in all_book_rows:
                        writer.writerow(book_row)
                
                self.logging_manager.log_info(f"✅ Batch CSV file written to {output_path}")
            except Exception as e:
                error_msg = f"Failed to write batch CSV file: {str(e)}"
                self.logging_manager.log_error(error_msg)
                reporter.add_error(error_msg)
                reporter.complete_generation(False, None)
                return result
            
            # Aggregate validation results
            total_errors = []
            total_warnings = []
            for validation_result in batch_validation_results:
                if validation_result:
                    total_errors.extend(validation_result.errors)
                    total_warnings.extend(validation_result.warnings)
            
            # Add batch processing errors
            total_errors.extend(batch_stats['processing_errors'])
            
            # Create combined validation result
            from ..verifiers.validation_framework import ValidationResult
            combined_validation = ValidationResult(
                is_valid=len(total_errors) == 0,
                field_results=[],
                errors=total_errors,
                warnings=total_warnings
            )
            
            # Log batch processing summary
            success_rate = (batch_stats['successful_books'] / batch_stats['total_books']) * 100 if batch_stats['total_books'] > 0 else 0
            self.logging_manager.log_info(f"Batch processing summary:")
            self.logging_manager.log_info(f"  Total books: {batch_stats['total_books']}")
            self.logging_manager.log_info(f"  Successful: {batch_stats['successful_books']}")
            self.logging_manager.log_info(f"  Failed: {batch_stats['failed_books']}")
            self.logging_manager.log_info(f"  Success rate: {success_rate:.1f}%")
            
            # Complete generation tracking
            reporter.complete_generation(batch_stats['successful_books'] > 0, combined_validation)
            
            # Complete the generation session
            self.logging_manager.complete_generation_session(batch_stats['successful_books'] > 0)
            
            self.logging_manager.log_info(f"Batch LSI ACS generation completed: {batch_stats['successful_books']}/{batch_stats['total_books']} books processed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Batch generation failed: {str(e)}"
            self.logging_manager.log_error(error_msg)
            reporter.add_error(error_msg)
            reporter.complete_generation(False, None)
            
            # Make sure to close the session even on error
            if 'session_id' in locals():
                self.logging_manager.complete_generation_session(False)
                
            return result

    def _generate_with_comprehensive_logging(self, metadata: CodexMetadata, output_path: str, reporter, **kwargs):
        """Generate CSV with comprehensive logging and detailed field tracking."""
        # Start template reading timing
        self.logging_manager.start_operation_timing("template_reading")
        
        # Read the template to get the correct headers
        template_headers = self._read_template_headers()
        
        # Log template reading timing
        template_time = self.logging_manager.end_operation_timing("template_reading")
        self.logging_manager.log_performance_metric("template_reading_time", template_time)
        self.logging_manager.log_info(f"Template loaded with {len(template_headers)} fields")
        
        # Start field mapping timing
        self.logging_manager.start_operation_timing("field_mapping")
        
        # Map metadata to LSI format with comprehensive logging and tranche context
        lsi_data = self._map_metadata_with_comprehensive_logging(metadata, template_headers, reporter)
        
        # Log field mapping timing
        mapping_time = self.logging_manager.end_operation_timing("field_mapping")
        self.logging_manager.log_performance_metric("field_mapping_time", mapping_time)
        
        # Start file writing timing
        self.logging_manager.start_operation_timing("file_writing")
        
        # Write the populated CSV
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            # Write header row from template
            writer.writerow(template_headers)
            # Write data row
            writer.writerow(lsi_data)
        
        # Log file writing timing
        writing_time = self.logging_manager.end_operation_timing("file_writing")
        self.logging_manager.log_performance_metric("file_writing_time", writing_time)
        
        # Validate field corrections if enabled
        self._validate_field_corrections(lsi_data, template_headers, metadata)
        
        self.logging_manager.log_info(f"LSI ACS CSV generated successfully: {output_path}")

    def _map_metadata_with_comprehensive_logging(self, metadata: CodexMetadata, headers: list, reporter) -> list:
        """Map metadata to LSI format with comprehensive logging and detailed tracking."""
        from .field_mapping import MappingContext
        import time
        
        results = []
        
        # Get field exclusions from tranche configuration if available
        field_exclusions = []
        if hasattr(self, 'tranche_name') and self.tranche_name:
            try:
                from .tranche_config_loader import TrancheConfigLoader
                tranche_loader = TrancheConfigLoader()
                field_exclusions = tranche_loader.get_tranche_field_exclusions(self.tranche_name)
                if field_exclusions:
                    self.logging_manager.log_info(f"Excluding fields from CSV output: {field_exclusions}")
            except Exception as e:
                self.logging_manager.log_warning(f"Failed to get field exclusions from tranche: {e}")
        
        for header in headers:
            # Check if this field should be excluded
            if header in field_exclusions:
                self.logging_manager.log_info(f"Excluding field from CSV output: {header}")
                results.append('')
                continue
            
            # Start timing for individual field mapping
            field_start_time = time.time()
            
            strategy = self.field_registry.get_strategy(header)
            if strategy:
                try:
                    # Create enhanced context with raw metadata for JSON extraction
                    context_config = getattr(self.field_registry, 'context_config', {})
                    
                    # Add raw metadata to context for JSON extraction strategies
                    if hasattr(metadata, '__dict__'):
                        context_config['raw_metadata'] = metadata.__dict__
                    
                    # Add tranche configuration for override strategies
                    if self.tranche_name:
                        from .tranche_config_loader import TrancheConfigLoader
                        try:
                            tranche_loader = TrancheConfigLoader()
                            tranche_config = tranche_loader.get_tranche_override_config(self.tranche_name)
                            context_config['tranche_config'] = tranche_config
                        except Exception as e:
                            self.logging_manager.log_warning(f"Failed to load tranche config for context: {e}")
                    
                    context = MappingContext(
                        field_name=header,
                        lsi_headers=headers,
                        current_row_data={},
                        metadata=metadata,
                        config=context_config
                    )
                    
                    # Add raw metadata directly to context for easier access
                    if hasattr(metadata, '__dict__'):
                        context.raw_metadata = metadata.__dict__
                    
                    # Get source value for logging
                    source_value = None
                    if hasattr(strategy, 'metadata_field'):
                        source_value = getattr(metadata, strategy.metadata_field, None)
                    
                    if strategy.validate_input(metadata, context):
                        value = strategy.map_field(metadata, context)
                        
                        # Calculate processing time
                        processing_time_ms = (time.time() - field_start_time) * 1000
                        
                        # Determine mapping type for tracking
                        mapping_type = "direct"
                        strategy_name = type(strategy).__name__
                        if "Computed" in strategy_name:
                            mapping_type = "computed"
                        elif "Default" in strategy_name:
                            mapping_type = "default"
                        elif "Conditional" in strategy_name:
                            mapping_type = "conditional"
                        elif "LLM" in strategy_name:
                            mapping_type = "llm_completion"
                        
                        # Log field mapping with comprehensive details
                        self.logging_manager.log_field_mapping(
                            field_name=header,
                            source_value=source_value,
                            mapped_value=value,
                            mapping_strategy=mapping_type,
                            processing_time_ms=processing_time_ms
                        )
                        
                        # Track the field mapping for reporter
                        reporter.track_field_mapping(header, value, mapping_type)
                        results.append(str(value) if value is not None else '')
                        
                    else:
                        processing_time_ms = (time.time() - field_start_time) * 1000
                        warning_msg = f"Validation failed for field '{header}', using empty value"
                        
                        # Log field mapping with validation failure
                        self.logging_manager.log_field_mapping(
                            field_name=header,
                            source_value=source_value,
                            mapped_value="",
                            mapping_strategy="validation_failed",
                            processing_time_ms=processing_time_ms,
                            warnings=[warning_msg]
                        )
                        
                        self.logging_manager.log_warning(warning_msg)
                        reporter.add_warning(warning_msg)
                        reporter.track_field_mapping(header, "", "validation_failed")
                        results.append('')
                        
                except Exception as e:
                    processing_time_ms = (time.time() - field_start_time) * 1000
                    error_msg = f"Error mapping field '{header}': {e}"
                    
                    # Log field mapping with error
                    self.logging_manager.log_field_mapping(
                        field_name=header,
                        source_value=source_value,
                        mapped_value="",
                        mapping_strategy="error",
                        processing_time_ms=processing_time_ms,
                        errors=[error_msg]
                    )
                    
                    self.logging_manager.log_error(error_msg)
                    reporter.add_error(error_msg)
                    reporter.track_field_mapping(header, "", "error")
                    results.append('')
            else:
                processing_time_ms = (time.time() - field_start_time) * 1000
                
                # Log field mapping with no strategy
                self.logging_manager.log_field_mapping(
                    field_name=header,
                    source_value=None,
                    mapped_value="",
                    mapping_strategy="no_strategy",
                    processing_time_ms=processing_time_ms,
                    warnings=[f"No mapping strategy registered for field '{header}'"]
                )
                
                # No strategy registered, use empty value
                reporter.track_field_mapping(header, "", "no_strategy")
                results.append('')
        
        return results

    def _read_template_headers(self) -> list:
        """Read the LSI template headers."""
        try:
            with open(self.template_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                headers = next(reader)
                return headers
        except Exception as e:
            logging.error(f"Failed to read template headers: {e}")
            # Return minimal set of headers as fallback
            return [
                "Lightning Source Account #", "ISBN or SKU", "Title", "Publisher", 
                "Imprint", "Contributor One", "Pages", "Pub Date"
            ]

    def _validate_field_corrections(self, lsi_data: List[str], headers: List[str], metadata: CodexMetadata):
        """
        Validate field corrections applied during generation.
        
        Args:
            lsi_data: Generated LSI field values
            headers: LSI field headers
            metadata: Source metadata
        """
        try:
            # Create field values dictionary
            field_values = dict(zip(headers, lsi_data))
            
            # Extract data for validation
            validation_data = {}
            
            # Extract thema subjects
            thema_subjects = []
            for i in range(1, 4):
                thema_field = f"Thema Subject {i}"
                if thema_field in field_values and field_values[thema_field]:
                    thema_subjects.append(field_values[thema_field])
            if thema_subjects:
                validation_data['thema_subjects'] = thema_subjects
            
            # Extract age range
            if 'Min Age' in field_values and field_values['Min Age']:
                try:
                    validation_data['min_age'] = int(field_values['Min Age'])
                except ValueError:
                    pass
            if 'Max Age' in field_values and field_values['Max Age']:
                try:
                    validation_data['max_age'] = int(field_values['Max Age'])
                except ValueError:
                    pass
            
            # Extract file paths
            file_paths = {}
            if 'Interior Path / Filename' in field_values and field_values['Interior Path / Filename']:
                file_paths['interior'] = field_values['Interior Path / Filename']
            if 'Cover Path / Filename' in field_values and field_values['Cover Path / Filename']:
                file_paths['cover'] = field_values['Cover Path / Filename']
            if file_paths:
                validation_data['file_paths'] = file_paths
            
            # Extract description and series
            if 'Short Description' in field_values:
                validation_data['description'] = field_values['Short Description']
            if 'Series Name' in field_values:
                validation_data['series_name'] = field_values['Series Name']
            
            # Get blank fields from tranche config
            blank_fields = []
            if self.tranche_name:
                try:
                    from .tranche_config_loader import TrancheConfigLoader
                    tranche_loader = TrancheConfigLoader()
                    blank_fields = tranche_loader.get_blank_fields(self.tranche_name)
                except Exception:
                    pass
            
            if blank_fields:
                validation_data['field_values'] = field_values
                validation_data['blank_fields'] = blank_fields
            
            # Perform validation
            if validation_data:
                is_valid = self.field_validator.validate_all_corrections(validation_data)
                results = self.field_validator.get_validation_results()
                
                # Log validation results
                if results['errors']:
                    for error in results['errors']:
                        self.logging_manager.log_error(f"Field correction validation error: {error}")
                
                if results['warnings']:
                    for warning in results['warnings']:
                        self.logging_manager.log_warning(f"Field correction validation warning: {warning}")
                
                if is_valid:
                    self.logging_manager.log_info("Field corrections validation passed")
                else:
                    self.logging_manager.log_warning("Field corrections validation failed")
            
        except Exception as e:
            self.logging_manager.log_error(f"Error during field corrections validation: {e}")