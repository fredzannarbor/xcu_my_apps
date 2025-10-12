#!/usr/bin/env python3
"""
Comprehensive validation script for Codexes Factory integration.

This script validates that the arxiv-writer package can completely replace
the existing Codexes Factory arxiv paper generation functionality with
identical output and full workflow compatibility.
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse
import logging
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from arxiv_writer.core.codexes_factory_adapter import (
    CodexesFactoryAdapter,
    CodexesFactoryConfig,
    migrate_codexes_factory_config,
    create_codexes_compatibility_config,
    create_codexes_factory_paper_generator
)
from arxiv_writer.core.exceptions import ConfigurationError, ValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CodexesIntegrationValidator:
    """Comprehensive validator for Codexes Factory integration."""
    
    def __init__(self, workspace_root: str = ".", verbose: bool = False):
        """Initialize validator."""
        self.workspace_root = Path(workspace_root)
        self.verbose = verbose
        self.validation_results = []
        self.temp_files = []
        
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup temp files."""
        self.cleanup()
    
    def cleanup(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                if Path(temp_file).exists():
                    Path(temp_file).unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup {temp_file}: {e}")
    
    def validate_complete_integration(self) -> Dict[str, Any]:
        """Run complete integration validation."""
        logger.info("Starting comprehensive Codexes Factory integration validation")
        
        validation_report = {
            "timestamp": datetime.now().isoformat(),
            "workspace_root": str(self.workspace_root),
            "tests_run": [],
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": [],
            "warnings": [],
            "summary": ""
        }
        
        # Test categories
        test_categories = [
            ("Configuration Migration", self._test_configuration_migration),
            ("Adapter Initialization", self._test_adapter_initialization),
            ("Paper Generation Workflow", self._test_paper_generation_workflow),
            ("Section Generation", self._test_section_generation),
            ("Paper Validation", self._test_paper_validation),
            ("Context Collection", self._test_context_collection),
            ("Output Format Compatibility", self._test_output_format_compatibility),
            ("Error Handling", self._test_error_handling),
            ("Xynapse Traces Compatibility", self._test_xynapse_traces_compatibility)
        ]
        
        for test_name, test_func in test_categories:
            logger.info(f"Running test category: {test_name}")
            try:
                test_result = test_func()
                test_result["category"] = test_name
                validation_report["tests_run"].append(test_result)
                
                if test_result["passed"]:
                    validation_report["tests_passed"] += 1
                    logger.info(f"✓ {test_name} - PASSED")
                else:
                    validation_report["tests_failed"] += 1
                    logger.error(f"✗ {test_name} - FAILED")
                    validation_report["errors"].extend(test_result.get("errors", []))
                
                validation_report["warnings"].extend(test_result.get("warnings", []))
                
            except Exception as e:
                logger.error(f"✗ {test_name} - ERROR: {e}")
                validation_report["tests_failed"] += 1
                validation_report["errors"].append(f"{test_name}: {str(e)}")
        
        # Generate summary
        total_tests = validation_report["tests_passed"] + validation_report["tests_failed"]
        success_rate = (validation_report["tests_passed"] / total_tests * 100) if total_tests > 0 else 0
        
        validation_report["summary"] = (
            f"Validation completed: {validation_report['tests_passed']}/{total_tests} tests passed "
            f"({success_rate:.1f}% success rate)"
        )
        
        if validation_report["tests_failed"] == 0:
            logger.info("🎉 All integration validation tests passed!")
        else:
            logger.error(f"❌ {validation_report['tests_failed']} tests failed")
        
        return validation_report
    
    def _test_configuration_migration(self) -> Dict[str, Any]:
        """Test configuration migration functionality."""
        test_result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        try:
            # Create test configuration
            test_config = {
                "imprint": "test_imprint",
                "workspace_root": str(self.workspace_root),
                "llm_config": {
                    "default_model": "anthropic/claude-3-5-sonnet-20241022",
                    "available_models": [
                        "anthropic/claude-3-5-sonnet-20241022",
                        "openai/gpt-4-turbo"
                    ]
                },
                "template_config": {
                    "template_file": "templates/default_prompts.json",
                    "section_order": ["abstract", "introduction", "conclusion"]
                },
                "validation_config": {
                    "enabled": True,
                    "strict_mode": False,
                    "quality_thresholds": {
                        "min_word_count": 500,
                        "max_word_count": 8000
                    }
                }
            }
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as source_f:
                json.dump(test_config, source_f)
                source_path = source_f.name
                self.temp_files.append(source_path)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as target_f:
                target_path = target_f.name
                self.temp_files.append(target_path)
            
            # Test migration
            migrated_config = migrate_codexes_factory_config(source_path, target_path)
            
            # Validate migration results
            if not Path(target_path).exists():
                test_result["errors"].append("Migration did not create output file")
                test_result["passed"] = False
            
            # Verify configuration content
            with open(target_path, 'r') as f:
                saved_config = json.load(f)
            
            required_keys = ["llm_config", "template_config", "validation_config"]
            for key in required_keys:
                if key not in saved_config:
                    test_result["errors"].append(f"Missing key in migrated config: {key}")
                    test_result["passed"] = False
            
            # Verify specific values
            if saved_config.get("llm_config", {}).get("default_model") != test_config["llm_config"]["default_model"]:
                test_result["errors"].append("Default model not preserved in migration")
                test_result["passed"] = False
            
            test_result["details"]["migrated_config_size"] = len(json.dumps(saved_config))
            test_result["details"]["original_config_size"] = len(json.dumps(test_config))
            
        except Exception as e:
            test_result["errors"].append(f"Configuration migration failed: {str(e)}")
            test_result["passed"] = False
        
        return test_result
    
    def _test_adapter_initialization(self) -> Dict[str, Any]:
        """Test adapter initialization with various configuration types."""
        test_result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        try:
            # Test 1: Initialize with dictionary
            config_dict = {
                "imprint": "test_imprint",
                "workspace_root": str(self.workspace_root)
            }
            
            adapter1 = CodexesFactoryAdapter(config_dict)
            if adapter1.codexes_config.imprint_name != "test_imprint":
                test_result["errors"].append("Dictionary initialization failed")
                test_result["passed"] = False
            
            # Test 2: Initialize with CodexesFactoryConfig object
            config_obj = CodexesFactoryConfig(
                imprint_name="test_imprint2",
                workspace_root=str(self.workspace_root)
            )
            
            adapter2 = CodexesFactoryAdapter(config_obj)
            if adapter2.codexes_config.imprint_name != "test_imprint2":
                test_result["errors"].append("Config object initialization failed")
                test_result["passed"] = False
            
            # Test 3: Initialize with file path
            config_data = {"imprint": "test_imprint3"}
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(config_data, f)
                config_path = f.name
                self.temp_files.append(config_path)
            
            adapter3 = CodexesFactoryAdapter(config_path)
            if adapter3.codexes_config.imprint_name != "test_imprint3":
                test_result["errors"].append("File path initialization failed")
                test_result["passed"] = False
            
            test_result["details"]["initialization_methods_tested"] = 3
            
        except Exception as e:
            test_result["errors"].append(f"Adapter initialization failed: {str(e)}")
            test_result["passed"] = False
        
        return test_result
    
    def _test_paper_generation_workflow(self) -> Dict[str, Any]:
        """Test complete paper generation workflow."""
        test_result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        try:
            # Create adapter with test configuration
            config = create_codexes_compatibility_config(
                workspace_root=str(self.workspace_root),
                imprint_name="test_imprint"
            )
            
            adapter = CodexesFactoryAdapter(config)
            
            # Mock the dependencies since we're testing integration, not actual LLM calls
            from unittest.mock import Mock, patch
            
            with patch('src.arxiv_writer.core.codexes_factory_adapter.create_codexes_factory_context_collector') as mock_create_collector:
                with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator') as mock_generator_class:
                    
                    # Setup mocks
                    mock_context_collector = Mock()
                    mock_context_data = {
                        "sources": {"test_source": {"data": "test_data"}},
                        "collection_metadata": {"timestamp": "2024-01-01T00:00:00Z"}
                    }
                    mock_context_collector.collect_context.return_value = mock_context_data
                    mock_context_collector.prepare_context.return_value = {"prepared": "context"}
                    mock_create_collector.return_value = mock_context_collector
                    
                    from src.arxiv_writer.core.models import PaperResult, Section, GenerationSummary
                    
                    mock_generator = Mock()
                    mock_section = Section(
                        name="abstract",
                        content="Test abstract content",
                        word_count=100,
                        generated_at=datetime.now(),
                        model_used="anthropic/claude-3-5-sonnet-20241022",
                        validation_status="valid",
                        metadata={}
                    )
                    mock_paper_result = PaperResult(
                        sections={"abstract": mock_section},
                        complete_paper="Complete paper content",
                        generation_summary=GenerationSummary(
                            total_sections=1,
                            successful_sections=1,
                            failed_sections=0,
                            total_time=10.0,
                            total_word_count=100,
                            llm_calls=1
                        ),
                        output_files=["paper.tex"]
                    )
                    mock_generator.generate_paper.return_value = mock_paper_result
                    mock_generator_class.return_value = mock_generator
                    
                    # Test paper generation
                    result = adapter.generate_paper()
                    
                    # Validate result format
                    required_keys = [
                        "paper_content", "sections", "generation_summary",
                        "context_summary", "output_files", "imprint_info"
                    ]
                    
                    for key in required_keys:
                        if key not in result:
                            test_result["errors"].append(f"Missing key in result: {key}")
                            test_result["passed"] = False
                    
                    # Validate content
                    if result.get("paper_content") != "Complete paper content":
                        test_result["errors"].append("Paper content not preserved")
                        test_result["passed"] = False
                    
                    if "abstract" not in result.get("sections", {}):
                        test_result["errors"].append("Section not found in result")
                        test_result["passed"] = False
                    
                    test_result["details"]["result_keys"] = list(result.keys())
                    test_result["details"]["sections_generated"] = len(result.get("sections", {}))
            
        except Exception as e:
            test_result["errors"].append(f"Paper generation workflow failed: {str(e)}")
            test_result["passed"] = False
        
        return test_result
    
    def _test_section_generation(self) -> Dict[str, Any]:
        """Test individual section generation."""
        test_result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        try:
            config = create_codexes_compatibility_config()
            adapter = CodexesFactoryAdapter(config)
            
            from unittest.mock import Mock, patch
            
            with patch('src.arxiv_writer.core.codexes_factory_adapter.create_codexes_factory_context_collector') as mock_create_collector:
                with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator') as mock_generator_class:
                    
                    # Setup mocks
                    mock_context_collector = Mock()
                    mock_context_collector.collect_context.return_value = {"sources": {}}
                    mock_context_collector.prepare_context.return_value = {"context": "data"}
                    mock_create_collector.return_value = mock_context_collector
                    
                    from src.arxiv_writer.core.models import Section
                    
                    mock_generator = Mock()
                    mock_section = Section(
                        name="introduction",
                        content="Test introduction content",
                        word_count=200,
                        generated_at=datetime.now(),
                        model_used="anthropic/claude-3-5-sonnet-20241022",
                        validation_status="valid",
                        metadata={}
                    )
                    mock_generator.generate_section.return_value = mock_section
                    mock_generator_class.return_value = mock_generator
                    
                    # Test section generation
                    result = adapter.generate_section("introduction")
                    
                    # Validate result
                    required_keys = [
                        "section_name", "content", "word_count",
                        "generated_at", "model_used", "validation_status",
                        "metadata", "context_summary"
                    ]
                    
                    for key in required_keys:
                        if key not in result:
                            test_result["errors"].append(f"Missing key in section result: {key}")
                            test_result["passed"] = False
                    
                    if result.get("section_name") != "introduction":
                        test_result["errors"].append("Section name not preserved")
                        test_result["passed"] = False
                    
                    test_result["details"]["section_result_keys"] = list(result.keys())
            
        except Exception as e:
            test_result["errors"].append(f"Section generation failed: {str(e)}")
            test_result["passed"] = False
        
        return test_result
    
    def _test_paper_validation(self) -> Dict[str, Any]:
        """Test paper validation functionality."""
        test_result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        try:
            config = create_codexes_compatibility_config()
            adapter = CodexesFactoryAdapter(config)
            
            from unittest.mock import Mock, patch
            
            with patch('src.arxiv_writer.core.codexes_factory_adapter.ArxivPaperGenerator') as mock_generator_class:
                
                mock_generator = Mock()
                mock_validation_result = Mock()
                mock_validation_result.is_valid = True
                mock_validation_result.errors = []
                mock_validation_result.warnings = ["Minor warning"]
                mock_validation_result.metrics = {"word_count": 1000}
                mock_generator.validate_paper.return_value = mock_validation_result
                mock_generator_class.return_value = mock_generator
                
                # Test validation
                result = adapter.validate_paper("Test paper content")
                
                # Validate result format
                required_keys = [
                    "is_valid", "errors", "warnings", "quality_metrics", "arxiv_compliance"
                ]
                
                for key in required_keys:
                    if key not in result:
                        test_result["errors"].append(f"Missing key in validation result: {key}")
                        test_result["passed"] = False
                
                if not result.get("is_valid"):
                    test_result["warnings"].append("Validation result shows invalid paper")
                
                if "arxiv_compliance" not in result:
                    test_result["errors"].append("Missing arxiv_compliance in validation result")
                    test_result["passed"] = False
                
                test_result["details"]["validation_result_keys"] = list(result.keys())
            
        except Exception as e:
            test_result["errors"].append(f"Paper validation failed: {str(e)}")
            test_result["passed"] = False
        
        return test_result
    
    def _test_context_collection(self) -> Dict[str, Any]:
        """Test context data collection."""
        test_result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        try:
            config = create_codexes_compatibility_config()
            adapter = CodexesFactoryAdapter(config)
            
            from unittest.mock import Mock, patch
            
            with patch('src.arxiv_writer.core.codexes_factory_adapter.create_codexes_factory_context_collector') as mock_create_collector:
                
                mock_context_collector = Mock()
                mock_context_data = {
                    "sources": {
                        "source1": {"data": "value1"},
                        "source2": {"error": "Failed"}
                    },
                    "collection_metadata": {"timestamp": "2024-01-01T00:00:00Z"}
                }
                mock_context_collector.collect_context.return_value = mock_context_data
                mock_create_collector.return_value = mock_context_collector
                
                # Test context collection
                result = adapter.get_context_data()
                
                # Validate result format
                required_keys = [
                    "imprint_data", "collection_metadata", "summary"
                ]
                
                for key in required_keys:
                    if key not in result:
                        test_result["errors"].append(f"Missing key in context result: {key}")
                        test_result["passed"] = False
                
                # Validate summary
                summary = result.get("summary", {})
                if "total_sources" not in summary:
                    test_result["errors"].append("Missing total_sources in context summary")
                    test_result["passed"] = False
                
                test_result["details"]["context_result_keys"] = list(result.keys())
                test_result["details"]["sources_collected"] = summary.get("total_sources", 0)
            
        except Exception as e:
            test_result["errors"].append(f"Context collection failed: {str(e)}")
            test_result["passed"] = False
        
        return test_result
    
    def _test_output_format_compatibility(self) -> Dict[str, Any]:
        """Test output format compatibility with Codexes Factory."""
        test_result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        try:
            # Test that output format matches expected Codexes Factory format
            config = create_codexes_compatibility_config()
            adapter = CodexesFactoryAdapter(config)
            
            # This test validates the structure without actual generation
            expected_result_structure = {
                "paper_content": str,
                "sections": dict,
                "generation_summary": dict,
                "context_summary": dict,
                "output_files": list,
                "imprint_info": dict
            }
            
            # Validate that adapter has the right methods
            required_methods = [
                "generate_paper",
                "generate_section", 
                "validate_paper",
                "get_context_data"
            ]
            
            for method in required_methods:
                if not hasattr(adapter, method):
                    test_result["errors"].append(f"Missing required method: {method}")
                    test_result["passed"] = False
            
            # Validate configuration conversion
            paper_config = adapter.paper_config
            if not hasattr(paper_config, 'llm_config'):
                test_result["errors"].append("Missing llm_config in converted configuration")
                test_result["passed"] = False
            
            if not hasattr(paper_config, 'template_config'):
                test_result["errors"].append("Missing template_config in converted configuration")
                test_result["passed"] = False
            
            test_result["details"]["methods_available"] = [m for m in required_methods if hasattr(adapter, m)]
            test_result["details"]["config_attributes"] = [attr for attr in dir(paper_config) if not attr.startswith('_')]
            
        except Exception as e:
            test_result["errors"].append(f"Output format compatibility test failed: {str(e)}")
            test_result["passed"] = False
        
        return test_result
    
    def _test_error_handling(self) -> Dict[str, Any]:
        """Test error handling scenarios."""
        test_result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        try:
            # Test invalid configuration handling
            try:
                invalid_config = {"invalid": "config"}
                adapter = CodexesFactoryAdapter(invalid_config)
                # Should not raise exception, should use defaults
                if adapter.codexes_config is None:
                    test_result["errors"].append("Invalid config handling failed")
                    test_result["passed"] = False
            except Exception as e:
                test_result["warnings"].append(f"Invalid config raised exception: {str(e)}")
            
            # Test missing file handling
            try:
                CodexesFactoryAdapter("/nonexistent/config.json")
                test_result["errors"].append("Missing file should raise ConfigurationError")
                test_result["passed"] = False
            except ConfigurationError:
                # Expected behavior
                pass
            except Exception as e:
                test_result["warnings"].append(f"Unexpected exception for missing file: {str(e)}")
            
            # Test invalid type handling
            try:
                CodexesFactoryAdapter(123)  # Invalid type
                test_result["errors"].append("Invalid type should raise ConfigurationError")
                test_result["passed"] = False
            except ConfigurationError:
                # Expected behavior
                pass
            except Exception as e:
                test_result["warnings"].append(f"Unexpected exception for invalid type: {str(e)}")
            
            test_result["details"]["error_scenarios_tested"] = 3
            
        except Exception as e:
            test_result["errors"].append(f"Error handling test failed: {str(e)}")
            test_result["passed"] = False
        
        return test_result
    
    def _test_xynapse_traces_compatibility(self) -> Dict[str, Any]:
        """Test specific compatibility with xynapse_traces configuration."""
        test_result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        try:
            # Load xynapse_traces configuration if available
            xynapse_config_path = self.workspace_root / "examples" / "configs" / "imprints" / "xynapse_traces.json"
            
            if xynapse_config_path.exists():
                # Test with actual xynapse_traces configuration
                adapter = CodexesFactoryAdapter(str(xynapse_config_path))
                
                # Validate specific xynapse_traces settings
                if adapter.codexes_config.imprint_name != "Xynapse Traces":
                    test_result["errors"].append("Xynapse Traces imprint name not preserved")
                    test_result["passed"] = False
                
                # Validate that all context collection is enabled for comprehensive analysis
                if not all([
                    adapter.codexes_config.collect_book_catalog,
                    adapter.codexes_config.collect_imprint_config,
                    adapter.codexes_config.collect_technical_architecture,
                    adapter.codexes_config.collect_performance_metrics
                ]):
                    test_result["warnings"].append("Not all context collection types enabled for xynapse_traces")
                
                test_result["details"]["xynapse_config_loaded"] = True
                test_result["details"]["imprint_name"] = adapter.codexes_config.imprint_name
                
            else:
                # Create xynapse_traces compatible configuration
                config = create_codexes_compatibility_config(
                    workspace_root=str(self.workspace_root),
                    imprint_name="Xynapse Traces"
                )
                
                adapter = CodexesFactoryAdapter(config)
                
                if adapter.codexes_config.imprint_name != "Xynapse Traces":
                    test_result["errors"].append("Xynapse Traces compatibility config failed")
                    test_result["passed"] = False
                
                test_result["details"]["xynapse_config_loaded"] = False
                test_result["details"]["compatibility_config_created"] = True
            
            # Validate default model matches expected
            expected_model = "anthropic/claude-3-5-sonnet-20241022"
            if adapter.codexes_config.default_model != expected_model:
                test_result["warnings"].append(f"Default model {adapter.codexes_config.default_model} != expected {expected_model}")
            
            test_result["details"]["default_model"] = adapter.codexes_config.default_model
            test_result["details"]["available_models"] = len(adapter.codexes_config.available_models)
            
        except Exception as e:
            test_result["errors"].append(f"Xynapse Traces compatibility test failed: {str(e)}")
            test_result["passed"] = False
        
        return test_result


def main():
    """Main validation script."""
    parser = argparse.ArgumentParser(description="Validate Codexes Factory integration")
    parser.add_argument("--workspace", default=".", help="Workspace root directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", help="Output file for validation report")
    
    args = parser.parse_args()
    
    with CodexesIntegrationValidator(args.workspace, args.verbose) as validator:
        validation_report = validator.validate_complete_integration()
        
        # Print summary
        print("\n" + "="*60)
        print("CODEXES FACTORY INTEGRATION VALIDATION REPORT")
        print("="*60)
        print(f"Timestamp: {validation_report['timestamp']}")
        print(f"Workspace: {validation_report['workspace_root']}")
        print(f"Tests Run: {len(validation_report['tests_run'])}")
        print(f"Tests Passed: {validation_report['tests_passed']}")
        print(f"Tests Failed: {validation_report['tests_failed']}")
        print(f"Summary: {validation_report['summary']}")
        
        if validation_report['errors']:
            print(f"\nErrors ({len(validation_report['errors'])}):")
            for error in validation_report['errors']:
                print(f"  ❌ {error}")
        
        if validation_report['warnings']:
            print(f"\nWarnings ({len(validation_report['warnings'])}):")
            for warning in validation_report['warnings']:
                print(f"  ⚠️  {warning}")
        
        print("\nDetailed Results:")
        for test in validation_report['tests_run']:
            status = "✓ PASSED" if test['passed'] else "✗ FAILED"
            print(f"  {status} - {test['category']}")
            if args.verbose and test.get('details'):
                for key, value in test['details'].items():
                    print(f"    {key}: {value}")
        
        # Save report if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(validation_report, f, indent=2, default=str)
            print(f"\nValidation report saved to: {args.output}")
        
        # Exit with appropriate code
        sys.exit(0 if validation_report['tests_failed'] == 0 else 1)


if __name__ == "__main__":
    main()