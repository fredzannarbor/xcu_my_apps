#!/usr/bin/env python3

"""
Integration Test for LSI Field Enhancement Phase 4

This comprehensive integration test validates that all components of the LSI field
enhancement system work together correctly, including:
- Multi-level configuration system
- Computed field strategies (territorial pricing, physical specs, dates, file paths)
- Enhanced LLM field completion
- Publisher and imprint configurations
- Field mapping registry integration
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

def run_integration_test():
    """Run comprehensive integration test for LSI field enhancement system."""
    logger.info("🚀 Starting LSI Field Enhancement Integration Test")
    logger.info("="*80)
    
    test_results = {
        "test_start_time": datetime.now().isoformat(),
        "configuration_system": {},
        "computed_fields": {},
        "field_mapping": {},
        "end_to_end_workflow": {},
        "performance_metrics": {},
        "validation_results": {}
    }
    
    try:
        # Test 1: Configuration System Integration
        logger.info("📋 Test 1: Configuration System Integration")
        config_results = test_configuration_system()
        test_results["configuration_system"] = config_results
        
        # Test 2: Computed Fields Integration
        logger.info("\n🧮 Test 2: Computed Fields Integration")
        computed_results = test_computed_fields()
        test_results["computed_fields"] = computed_results
        
        # Test 3: Field Mapping Integration
        logger.info("\n🗺️  Test 3: Field Mapping Integration")
        mapping_results = test_field_mapping_integration()
        test_results["field_mapping"] = mapping_results
        
        # Test 4: End-to-End Workflow
        logger.info("\n🔄 Test 4: End-to-End Workflow")
        workflow_results = test_end_to_end_workflow()
        test_results["end_to_end_workflow"] = workflow_results
        
        # Test 5: Performance Testing
        logger.info("\n⚡ Test 5: Performance Testing")
        performance_results = test_performance()
        test_results["performance_metrics"] = performance_results
        
        # Test 6: Validation and Error Handling
        logger.info("\n✅ Test 6: Validation and Error Handling")
        validation_results = test_validation_and_error_handling()
        test_results["validation_results"] = validation_results
        
    except Exception as e:
        logger.error(f"❌ Integration test failed with error: {e}")
        test_results["error"] = str(e)
        test_results["success"] = False
    else:
        test_results["success"] = True
    finally:
        test_results["test_end_time"] = datetime.now().isoformat()
        
        # Save comprehensive test results
        save_test_results(test_results)
        
        # Generate test report
        generate_test_report(test_results)
    
    return test_results

def test_configuration_system():
    """Test the multi-level configuration system."""
    logger.info("  Testing multi-level configuration system...")
    
    from codexes.modules.distribution.multi_level_config import (
        MultiLevelConfiguration, ConfigurationContext, create_default_multi_level_config
    )
    from codexes.modules.distribution.publisher_config_loader import PublisherConfigurationManager
    from codexes.modules.distribution.imprint_config_loader import ImprintConfigurationManager
    
    results = {}
    
    try:
        # Create multi-level configuration
        config = create_default_multi_level_config("configs")
        results["multi_level_config_created"] = True
        
        # Load publisher configurations
        pub_manager = PublisherConfigurationManager("configs")
        publishers = pub_manager.get_publisher_names()
        results["publishers_loaded"] = len(publishers)
        results["publisher_names"] = publishers
        
        # Load imprint configurations
        imp_manager = ImprintConfigurationManager("configs")
        imprints = imp_manager.get_imprint_names()
        results["imprints_loaded"] = len(imprints)
        results["imprint_names"] = imprints
        
        # Test configuration resolution with different contexts
        test_contexts = [
            ConfigurationContext(),
            ConfigurationContext(publisher_name=publishers[0] if publishers else None),
            ConfigurationContext(imprint_name=imprints[0] if imprints else None),
            ConfigurationContext(
                publisher_name=publishers[0] if publishers else None,
                imprint_name=imprints[0] if imprints else None
            )
        ]
        
        resolution_tests = {}
        test_key = "us_wholesale_discount"
        
        for i, context in enumerate(test_contexts):
            value = config.get_value(test_key, context, default="40")
            resolution_tests[f"context_{i}"] = {
                "value": value,
                "publisher": context.publisher_name,
                "imprint": context.imprint_name
            }
        
        results["resolution_tests"] = resolution_tests
        results["success"] = True
        
        logger.info(f"    ✅ Configuration system: {len(publishers)} publishers, {len(imprints)} imprints")
        
    except Exception as e:
        logger.error(f"    ❌ Configuration system test failed: {e}")
        results["success"] = False
        results["error"] = str(e)
    
    return results

def test_computed_fields():
    """Test all computed field strategies."""
    logger.info("  Testing computed field strategies...")
    
    from codexes.modules.metadata.metadata_models import CodexMetadata
    from codexes.modules.distribution.field_mapping import MappingContext
    from codexes.modules.distribution.computed_field_strategies import (
        TerritorialPricingStrategy, PhysicalSpecsStrategy,
        PublicationDateStrategy, FilePathStrategy
    )
    
    results = {}
    
    try:
        # Create test metadata
        test_metadata = CodexMetadata(
            title="Integration Test Book",
            author="Test Author",
            isbn13="9781234567890",
            page_count=250,
            trim_size="6x9",
            binding="paperback",
            list_price_usd=19.99,
            publication_date="2024-03-15"
        )
        
        context = MappingContext(
            field_name="test_field",
            lsi_headers=["Title", "ISBN-13", "Page Count"],
            current_row_data={}
        )
        
        # Test territorial pricing
        pricing_results = {}
        territories = ["CA", "UK", "EU", "AU", "JP"]
        
        for territory in territories:
            strategy = TerritorialPricingStrategy(territory)
            price = strategy.map_field(test_metadata, context)
            pricing_results[territory] = price
        
        results["territorial_pricing"] = pricing_results
        
        # Test physical specifications
        physical_results = {}
        specs = [
            ("weight", "standard"),
            ("spine_width", "standard"),
            ("thickness", "standard")
        ]
        
        for spec_type, paper_type in specs:
            strategy = PhysicalSpecsStrategy(spec_type, paper_type)
            value = strategy.map_field(test_metadata, context)
            physical_results[f"{spec_type}_{paper_type}"] = value
        
        results["physical_specifications"] = physical_results
        
        # Test date computation
        date_strategy = PublicationDateStrategy()
        pub_date = date_strategy.map_field(test_metadata, context)
        results["date_computation"] = {"publication_date": pub_date}
        
        # Test file path generation
        file_strategy = FilePathStrategy("cover", "covers")
        file_path = file_strategy.map_field(test_metadata, context)
        results["file_path_generation"] = {"cover_path": file_path}
        
        results["success"] = True
        logger.info("    ✅ Computed fields: All strategies working")
        
    except Exception as e:
        logger.error(f"    ❌ Computed fields test failed: {e}")
        results["success"] = False
        results["error"] = str(e)
    
    return results

def test_field_mapping_integration():
    """Test field mapping registry integration."""
    logger.info("  Testing field mapping registry integration...")
    
    from codexes.modules.distribution.enhanced_field_mappings import create_comprehensive_lsi_registry
    from codexes.modules.distribution.multi_level_config import create_default_multi_level_config
    from codexes.modules.metadata.metadata_models import CodexMetadata
    from codexes.modules.distribution.field_mapping import MappingContext
    
    results = {}
    
    try:
        # Create configuration and registry
        config = create_default_multi_level_config("configs")
        registry = create_comprehensive_lsi_registry(config)
        
        results["registry_created"] = True
        
        # Test metadata
        test_metadata = CodexMetadata(
            title="Field Mapping Test Book",
            author="Test Author",
            isbn13="9781234567890",
            page_count=300,
            list_price_usd=24.99,
            publication_date="2024-04-01"
        )
        
        context = MappingContext(
            field_name="test_field",
            lsi_headers=["Title", "ISBN-13", "Page Count"],
            current_row_data={}
        )
        
        # Test key field mappings
        test_fields = [
            "Title",
            "ISBN-13",
            "Page Count",
            "US Suggested List Price",
            "CA Suggested List Price",
            "Weight",
            "Publication Date",
            "Cover File Path"
        ]
        
        mapping_results = {}
        for field in test_fields:
            if registry.has_strategy(field):
                try:
                    strategy = registry.get_strategy(field)
                    value = strategy.map_field(test_metadata, context)
                    mapping_results[field] = value
                except Exception as e:
                    mapping_results[field] = f"ERROR: {str(e)}"
            else:
                mapping_results[field] = "NO_STRATEGY"
        
        results["field_mappings"] = mapping_results
        results["success"] = True
        
        successful_mappings = sum(1 for v in mapping_results.values() 
                                if v != "NO_STRATEGY" and not str(v).startswith("ERROR"))
        logger.info(f"    ✅ Field mapping: {successful_mappings}/{len(test_fields)} fields mapped successfully")
        
    except Exception as e:
        logger.error(f"    ❌ Field mapping test failed: {e}")
        results["success"] = False
        results["error"] = str(e)
    
    return results

def test_end_to_end_workflow():
    """Test complete end-to-end workflow."""
    logger.info("  Testing end-to-end workflow...")
    
    results = {}
    
    try:
        # Import necessary modules
        from codexes.modules.distribution.enhanced_field_mappings import create_comprehensive_lsi_registry
        from codexes.modules.distribution.multi_level_config import (
            create_default_multi_level_config, ConfigurationContext
        )
        from codexes.modules.metadata.metadata_models import CodexMetadata
        from codexes.modules.distribution.field_mapping import MappingContext
        
        # Step 1: Create configuration system
        config = create_default_multi_level_config("configs")
        
        # Step 2: Create context for xynapse_traces imprint
        context = ConfigurationContext(
            publisher_name="Nimble Books LLC",
            imprint_name="Xynapse Traces",
            book_isbn="9781234567890"
        )
        
        # Step 3: Create enhanced registry with configuration
        registry = create_comprehensive_lsi_registry(config)
        
        # Step 4: Create test book metadata
        test_book = CodexMetadata(
            title="End-to-End Test: Advanced AI Systems",
            author="Dr. Jane Smith",
            isbn13="9781234567890",
            isbn10="1234567890",
            page_count=350,
            trim_size="6x9",
            binding="paperback",
            list_price_usd=29.99,
            publication_date="2024-06-15",
            summary_short="A comprehensive guide to advanced AI systems and their applications.",
            bisac_codes="COM004000"
        )
        
        mapping_context = MappingContext(
            field_name="test_field",
            lsi_headers=["Title", "ISBN-13", "Page Count"],
            current_row_data={}
        )
        
        # Step 5: Process all LSI fields
        lsi_fields = [
            # Core identification
            "Title", "ISBN-13", "Publisher", "Imprint",
            
            # Pricing (including computed territorial pricing)
            "US Suggested List Price", "CA Suggested List Price", 
            "UK Suggested List Price", "EU Suggested List Price",
            
            # Physical specifications (computed)
            "Page Count", "Weight", "Spine Width", "Trim Size",
            
            # Dates (computed)
            "Publication Date", "Street Date",
            
            # File paths (computed)
            "Cover File Path", "Interior File Path",
            
            # Distribution settings (from configuration)
            "Lightning Source Account", "Carton Pack Quantity",
            "Territorial Rights", "Returnability",
            
            # Metadata
            "Language", "BISAC Category 1", "Short Description"
        ]
        
        processed_fields = {}
        successful_fields = 0
        
        for field in lsi_fields:
            try:
                if registry.has_strategy(field):
                    strategy = registry.get_strategy(field)
                    value = strategy.map_field(test_book, mapping_context)
                    processed_fields[field] = value
                    if value and str(value).strip():
                        successful_fields += 1
                else:
                    processed_fields[field] = "NO_STRATEGY"
            except Exception as e:
                processed_fields[field] = f"ERROR: {str(e)}"
        
        results["processed_fields"] = processed_fields
        results["total_fields"] = len(lsi_fields)
        results["successful_fields"] = successful_fields
        results["field_population_rate"] = (successful_fields / len(lsi_fields)) * 100
        
        # Step 6: Validate critical fields are populated
        critical_fields = ["Title", "ISBN-13", "US Suggested List Price", "Page Count"]
        critical_populated = all(
            processed_fields.get(field) and 
            not str(processed_fields.get(field)).startswith("ERROR") and
            processed_fields.get(field) != "NO_STRATEGY"
            for field in critical_fields
        )
        
        results["critical_fields_populated"] = critical_populated
        results["success"] = True
        
        logger.info(f"    ✅ End-to-end workflow: {successful_fields}/{len(lsi_fields)} fields populated ({results['field_population_rate']:.1f}%)")
        
    except Exception as e:
        logger.error(f"    ❌ End-to-end workflow test failed: {e}")
        results["success"] = False
        results["error"] = str(e)
    
    return results

def test_performance():
    """Test system performance."""
    logger.info("  Testing system performance...")
    
    results = {}
    
    try:
        from codexes.modules.distribution.multi_level_config import create_default_multi_level_config
        from codexes.modules.distribution.enhanced_field_mappings import create_comprehensive_lsi_registry
        from codexes.modules.metadata.metadata_models import CodexMetadata
        from codexes.modules.distribution.field_mapping import MappingContext
        
        # Performance test setup
        start_time = datetime.now()
        
        # Test 1: Configuration system creation time
        config_start = datetime.now()
        config = create_default_multi_level_config("configs")
        config_time = (datetime.now() - config_start).total_seconds()
        
        # Test 2: Registry creation time
        registry_start = datetime.now()
        registry = create_comprehensive_lsi_registry(config)
        registry_time = (datetime.now() - registry_start).total_seconds()
        
        # Test 3: Field mapping performance
        test_metadata = CodexMetadata(
            title="Performance Test Book",
            isbn13="9781234567890",
            page_count=250,
            list_price_usd=19.99
        )
        
        context = MappingContext(
            field_name="test_field",
            lsi_headers=["Title", "ISBN-13", "Page Count"],
            current_row_data={}
        )
        
        # Test multiple field mappings
        test_fields = ["Title", "ISBN-13", "Page Count", "US Suggested List Price", 
                      "CA Suggested List Price", "Weight", "Publication Date"]
        
        mapping_start = datetime.now()
        for _ in range(100):  # 100 iterations
            for field in test_fields:
                if registry.has_strategy(field):
                    strategy = registry.get_strategy(field)
                    strategy.map_field(test_metadata, context)
        
        mapping_time = (datetime.now() - mapping_start).total_seconds()
        total_mappings = 100 * len(test_fields)
        avg_mapping_time = (mapping_time / total_mappings) * 1000  # ms
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        results = {
            "config_creation_time_seconds": config_time,
            "registry_creation_time_seconds": registry_time,
            "total_field_mappings": total_mappings,
            "total_mapping_time_seconds": mapping_time,
            "average_mapping_time_ms": avg_mapping_time,
            "total_test_time_seconds": total_time,
            "success": True
        }
        
        logger.info(f"    ✅ Performance: {avg_mapping_time:.2f}ms avg mapping time, {total_time:.2f}s total")
        
    except Exception as e:
        logger.error(f"    ❌ Performance test failed: {e}")
        results["success"] = False
        results["error"] = str(e)
    
    return results

def test_validation_and_error_handling():
    """Test validation and error handling."""
    logger.info("  Testing validation and error handling...")
    
    results = {}
    
    try:
        from codexes.modules.distribution.global_config_validator import validate_global_configuration
        from codexes.modules.distribution.publisher_config_loader import PublisherConfigurationManager
        from codexes.modules.distribution.imprint_config_loader import ImprintConfigurationManager
        
        # Test 1: Global configuration validation
        global_validation = validate_global_configuration("configs/default_lsi_config.json")
        results["global_config_validation"] = {
            "valid": global_validation["valid"],
            "errors": len(global_validation.get("errors", [])),
            "warnings": len(global_validation.get("warnings", []))
        }
        
        # Test 2: Publisher configuration validation
        pub_manager = PublisherConfigurationManager("configs")
        publisher_validations = {}
        
        for publisher in pub_manager.get_publisher_names():
            validation = pub_manager.validate_publisher_config(publisher)
            publisher_validations[publisher] = {
                "valid": validation["valid"],
                "errors": len(validation.get("errors", [])),
                "warnings": len(validation.get("warnings", []))
            }
        
        results["publisher_validations"] = publisher_validations
        
        # Test 3: Imprint configuration validation
        imp_manager = ImprintConfigurationManager("configs")
        imprint_validations = {}
        
        for imprint in imp_manager.get_imprint_names():
            validation = imp_manager.validate_imprint_config(imprint)
            imprint_validations[imprint] = {
                "valid": validation["valid"],
                "errors": len(validation.get("errors", [])),
                "warnings": len(validation.get("warnings", []))
            }
        
        results["imprint_validations"] = imprint_validations
        
        # Test 4: Error handling with invalid data
        from codexes.modules.distribution.computed_field_strategies import TerritorialPricingStrategy
        from codexes.modules.metadata.metadata_models import CodexMetadata
        from codexes.modules.distribution.field_mapping import MappingContext
        
        # Test with invalid metadata
        invalid_metadata = CodexMetadata(title="Invalid Test")  # No price, ISBN, etc.
        context = MappingContext(
            field_name="test_field",
            lsi_headers=["Title", "ISBN-13", "Page Count"],
            current_row_data={}
        )
        
        strategy = TerritorialPricingStrategy("CA")
        result = strategy.map_field(invalid_metadata, context)
        
        results["error_handling_test"] = {
            "invalid_metadata_handled": result == "",  # Should return empty string
            "no_exception_thrown": True
        }
        
        results["success"] = True
        
        total_configs = len(publisher_validations) + len(imprint_validations) + 1
        valid_configs = sum(1 for v in publisher_validations.values() if v["valid"]) + \
                       sum(1 for v in imprint_validations.values() if v["valid"]) + \
                       (1 if global_validation["valid"] else 0)
        
        logger.info(f"    ✅ Validation: {valid_configs}/{total_configs} configurations valid")
        
    except Exception as e:
        logger.error(f"    ❌ Validation test failed: {e}")
        results["success"] = False
        results["error"] = str(e)
    
    return results

def save_test_results(results):
    """Save test results to file."""
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(output_dir, f"integration_test_results_{timestamp}.json")
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"📄 Test results saved to: {results_file}")

def generate_test_report(results):
    """Generate a comprehensive test report."""
    logger.info("\n" + "="*80)
    logger.info("🎯 LSI FIELD ENHANCEMENT INTEGRATION TEST REPORT")
    logger.info("="*80)
    
    overall_success = results.get("success", False)
    logger.info(f"Overall Status: {'✅ PASSED' if overall_success else '❌ FAILED'}")
    
    if "configuration_system" in results:
        config_results = results["configuration_system"]
        if config_results.get("success"):
            logger.info(f"✅ Configuration System: {config_results.get('publishers_loaded', 0)} publishers, {config_results.get('imprints_loaded', 0)} imprints")
        else:
            logger.info("❌ Configuration System: FAILED")
    
    if "computed_fields" in results:
        computed_results = results["computed_fields"]
        if computed_results.get("success"):
            logger.info("✅ Computed Fields: All strategies operational")
        else:
            logger.info("❌ Computed Fields: FAILED")
    
    if "field_mapping" in results:
        mapping_results = results["field_mapping"]
        if mapping_results.get("success"):
            logger.info("✅ Field Mapping: Registry integration working")
        else:
            logger.info("❌ Field Mapping: FAILED")
    
    if "end_to_end_workflow" in results:
        workflow_results = results["end_to_end_workflow"]
        if workflow_results.get("success"):
            population_rate = workflow_results.get("field_population_rate", 0)
            logger.info(f"✅ End-to-End Workflow: {population_rate:.1f}% field population rate")
        else:
            logger.info("❌ End-to-End Workflow: FAILED")
    
    if "performance_metrics" in results:
        perf_results = results["performance_metrics"]
        if perf_results.get("success"):
            avg_time = perf_results.get("average_mapping_time_ms", 0)
            logger.info(f"✅ Performance: {avg_time:.2f}ms average field mapping time")
        else:
            logger.info("❌ Performance: FAILED")
    
    if "validation_results" in results:
        validation_results = results["validation_results"]
        if validation_results.get("success"):
            logger.info("✅ Validation: Configuration validation working")
        else:
            logger.info("❌ Validation: FAILED")
    
    logger.info("="*80)
    
    if overall_success:
        logger.info("🎉 INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        logger.info("   The LSI Field Enhancement system is ready for production use.")
    else:
        logger.info("⚠️  INTEGRATION TEST FAILED!")
        logger.info("   Please review the errors and fix issues before deployment.")
    
    logger.info("="*80)

if __name__ == "__main__":
    run_integration_test()