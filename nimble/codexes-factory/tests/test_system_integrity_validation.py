#!/usr/bin/env python3
"""
System Integrity Validation Test for Dot Release Cleanup.

This comprehensive test validates that all system functionality remains intact
after cleanup operations, including imports, configuration loading, and file references.
"""

import os
import sys
import json
import logging
import subprocess
import importlib
import ast
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import tempfile
import shutil

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    test_name: str
    success: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class SystemIntegrityValidator:
    """
    Comprehensive system integrity validator for cleanup operations.
    
    Validates that all imports work, configurations load correctly,
    and file references remain functional after cleanup operations.
    """
    
    def __init__(self, root_path: str = "."):
        """
        Initialize the system integrity validator.
        
        Args:
            root_path: Root directory of the project
        """
        self.root_path = Path(root_path).resolve()
        self.validation_results: List[ValidationResult] = []
        
        # Critical modules that must import successfully
        self.critical_modules = [
            "codexes.core.llm_caller",
            "codexes.core.enhanced_llm_caller", 
            "codexes.modules.distribution.field_mapping_registry",
            "codexes.modules.distribution.multi_level_config",
            "codexes.modules.metadata.metadata_models",
            "codexes.core.file_analysis_engine",
            "codexes.core.safety_validator",
            "codexes.core.temporary_file_cleaner",
        ]
        
        # Critical configuration files
        self.critical_configs = [
            "configs/default_lsi_config.json",
            "configs/llm_monitoring_config.json",
            "configs/logging_config.json",
        ]
        
        # Critical entry points
        self.critical_scripts = [
            "run_book_pipeline.py",
            "generate_lsi_csv.py",
            "ideation_app.py",
        ]
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """
        Run comprehensive system integrity validation.
        
        Returns:
            Dictionary containing validation results and summary
        """
        logger.info("=" * 60)
        logger.info("STARTING COMPREHENSIVE SYSTEM INTEGRITY VALIDATION")
        logger.info("=" * 60)
        
        validation_summary = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "warnings": 0,
            "test_results": [],
            "overall_success": False
        }
        
        # Test 1: Import validation
        logger.info("\n" + "=" * 40)
        logger.info("TEST 1: IMPORT VALIDATION")
        logger.info("=" * 40)
        
        import_result = self.validate_imports()
        self.validation_results.append(import_result)
        validation_summary["test_results"].append(import_result)
        
        # Test 2: Configuration loading validation
        logger.info("\n" + "=" * 40)
        logger.info("TEST 2: CONFIGURATION LOADING VALIDATION")
        logger.info("=" * 40)
        
        config_result = self.validate_configuration_loading()
        self.validation_results.append(config_result)
        validation_summary["test_results"].append(config_result)
        
        # Test 3: File reference validation
        logger.info("\n" + "=" * 40)
        logger.info("TEST 3: FILE REFERENCE VALIDATION")
        logger.info("=" * 40)
        
        file_ref_result = self.validate_file_references()
        self.validation_results.append(file_ref_result)
        validation_summary["test_results"].append(file_ref_result)
        
        # Test 4: Critical script execution validation
        logger.info("\n" + "=" * 40)
        logger.info("TEST 4: CRITICAL SCRIPT VALIDATION")
        logger.info("=" * 40)
        
        script_result = self.validate_critical_scripts()
        self.validation_results.append(script_result)
        validation_summary["test_results"].append(script_result)
        
        # Test 5: Directory structure validation
        logger.info("\n" + "=" * 40)
        logger.info("TEST 5: DIRECTORY STRUCTURE VALIDATION")
        logger.info("=" * 40)
        
        structure_result = self.validate_directory_structure()
        self.validation_results.append(structure_result)
        validation_summary["test_results"].append(structure_result)
        
        # Test 6: Existing functionality preservation
        logger.info("\n" + "=" * 40)
        logger.info("TEST 6: FUNCTIONALITY PRESERVATION VALIDATION")
        logger.info("=" * 40)
        
        functionality_result = self.validate_functionality_preservation()
        self.validation_results.append(functionality_result)
        validation_summary["test_results"].append(functionality_result)
        
        # Calculate summary statistics
        validation_summary["total_tests"] = len(self.validation_results)
        validation_summary["passed_tests"] = sum(1 for r in self.validation_results if r.success)
        validation_summary["failed_tests"] = validation_summary["total_tests"] - validation_summary["passed_tests"]
        validation_summary["warnings"] = sum(len(r.warnings) for r in self.validation_results)
        validation_summary["overall_success"] = validation_summary["failed_tests"] == 0
        
        # Generate final report
        self._generate_validation_report(validation_summary)
        
        return validation_summary
    
    def validate_imports(self) -> ValidationResult:
        """Validate that all critical imports still work."""
        logger.info("Validating critical module imports...")
        
        import_results = {}
        failed_imports = []
        warnings = []
        
        for module_name in self.critical_modules:
            try:
                # Try to import the module
                module = importlib.import_module(module_name)
                import_results[module_name] = "SUCCESS"
                logger.info(f"✅ Successfully imported: {module_name}")
                
                # Try to reload to catch any issues
                importlib.reload(module)
                
            except ImportError as e:
                import_results[module_name] = f"IMPORT_ERROR: {str(e)}"
                failed_imports.append(module_name)
                logger.error(f"❌ Failed to import: {module_name} - {e}")
                
            except Exception as e:
                import_results[module_name] = f"ERROR: {str(e)}"
                failed_imports.append(module_name)
                logger.error(f"❌ Error importing: {module_name} - {e}")
        
        # Test additional imports from src directory
        src_modules = self._discover_src_modules()
        for module_name in src_modules[:10]:  # Test first 10 discovered modules
            try:
                importlib.import_module(module_name)
                import_results[module_name] = "SUCCESS"
            except Exception as e:
                warnings.append(f"Non-critical module import issue: {module_name} - {str(e)}")
        
        success = len(failed_imports) == 0
        message = f"Import validation: {len(import_results) - len(failed_imports)}/{len(import_results)} modules imported successfully"
        
        if failed_imports:
            message += f". Failed: {failed_imports}"
        
        return ValidationResult(
            test_name="import_validation",
            success=success,
            message=message,
            details={"import_results": import_results, "failed_imports": failed_imports},
            warnings=warnings
        )
    
    def validate_configuration_loading(self) -> ValidationResult:
        """Validate that configuration files load correctly."""
        logger.info("Validating configuration file loading...")
        
        config_results = {}
        failed_configs = []
        warnings = []
        
        for config_path in self.critical_configs:
            full_path = self.root_path / config_path
            
            if not full_path.exists():
                config_results[config_path] = "FILE_NOT_FOUND"
                failed_configs.append(config_path)
                logger.error(f"❌ Configuration file not found: {config_path}")
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                config_results[config_path] = "SUCCESS"
                logger.info(f"✅ Successfully loaded: {config_path}")
                
                # Validate structure for known configs
                if "default_lsi_config.json" in config_path:
                    self._validate_lsi_config_structure(config_data, warnings)
                
            except json.JSONDecodeError as e:
                config_results[config_path] = f"JSON_ERROR: {str(e)}"
                failed_configs.append(config_path)
                logger.error(f"❌ JSON error in: {config_path} - {e}")
                
            except Exception as e:
                config_results[config_path] = f"ERROR: {str(e)}"
                failed_configs.append(config_path)
                logger.error(f"❌ Error loading: {config_path} - {e}")
        
        # Test multi-level configuration system
        try:
            from codexes.modules.distribution.multi_level_config import MultiLevelConfiguration
            multi_config = MultiLevelConfiguration("configs")
            config_results["multi_level_config"] = "SUCCESS"
            logger.info("✅ Multi-level configuration system working")
        except Exception as e:
            config_results["multi_level_config"] = f"ERROR: {str(e)}"
            failed_configs.append("multi_level_config")
            logger.error(f"❌ Multi-level config error: {e}")
        
        success = len(failed_configs) == 0
        message = f"Configuration validation: {len(config_results) - len(failed_configs)}/{len(config_results)} configs loaded successfully"
        
        if failed_configs:
            message += f". Failed: {failed_configs}"
        
        return ValidationResult(
            test_name="configuration_validation",
            success=success,
            message=message,
            details={"config_results": config_results, "failed_configs": failed_configs},
            warnings=warnings
        )
    
    def validate_file_references(self) -> ValidationResult:
        """Validate that file references are still valid."""
        logger.info("Validating file references...")
        
        reference_results = {}
        broken_references = []
        warnings = []
        
        # Check references in Python files
        python_files = list(self.root_path.rglob("*.py"))
        for py_file in python_files[:20]:  # Check first 20 Python files
            try:
                relative_path = str(py_file.relative_to(self.root_path))
                references = self._extract_file_references(py_file)
                
                broken_refs = []
                for ref in references:
                    ref_path = self._resolve_reference_path(ref, py_file.parent)
                    if ref_path and not ref_path.exists():
                        broken_refs.append(ref)
                
                if broken_refs:
                    reference_results[relative_path] = f"BROKEN_REFS: {broken_refs}"
                    broken_references.extend(broken_refs)
                else:
                    reference_results[relative_path] = "SUCCESS"
                
            except Exception as e:
                warnings.append(f"Could not check references in {relative_path}: {str(e)}")
        
        # Check references in configuration files
        config_files = list(self.root_path.rglob("*.json"))
        for config_file in config_files[:10]:  # Check first 10 config files
            try:
                relative_path = str(config_file.relative_to(self.root_path))
                references = self._extract_config_references(config_file)
                
                broken_refs = []
                for ref in references:
                    ref_path = self._resolve_reference_path(ref, config_file.parent)
                    if ref_path and not ref_path.exists():
                        broken_refs.append(ref)
                
                if broken_refs:
                    reference_results[relative_path] = f"BROKEN_REFS: {broken_refs}"
                    broken_references.extend(broken_refs)
                else:
                    reference_results[relative_path] = "SUCCESS"
                
            except Exception as e:
                warnings.append(f"Could not check references in {relative_path}: {str(e)}")
        
        success = len(broken_references) == 0
        message = f"File reference validation: {len(reference_results)} files checked"
        
        if broken_references:
            message += f". Found {len(broken_references)} broken references"
        
        return ValidationResult(
            test_name="file_reference_validation",
            success=success,
            message=message,
            details={"reference_results": reference_results, "broken_references": broken_references},
            warnings=warnings
        )
    
    def validate_critical_scripts(self) -> ValidationResult:
        """Validate that critical scripts can be executed."""
        logger.info("Validating critical script execution...")
        
        script_results = {}
        failed_scripts = []
        warnings = []
        
        for script_path in self.critical_scripts:
            full_path = self.root_path / script_path
            
            if not full_path.exists():
                script_results[script_path] = "FILE_NOT_FOUND"
                failed_scripts.append(script_path)
                logger.error(f"❌ Script not found: {script_path}")
                continue
            
            try:
                # Try to parse the script for syntax errors
                with open(full_path, 'r', encoding='utf-8') as f:
                    script_content = f.read()
                
                ast.parse(script_content)
                script_results[script_path] = "SYNTAX_OK"
                logger.info(f"✅ Script syntax valid: {script_path}")
                
                # Try to run with --help flag if it's a main script
                if script_path.endswith('.py'):
                    try:
                        result = subprocess.run([
                            sys.executable, str(full_path), '--help'
                        ], capture_output=True, text=True, timeout=10)
                        
                        if result.returncode == 0 or "usage:" in result.stdout.lower():
                            script_results[script_path] = "EXECUTABLE"
                            logger.info(f"✅ Script executable: {script_path}")
                        else:
                            warnings.append(f"Script may have execution issues: {script_path}")
                    
                    except subprocess.TimeoutExpired:
                        warnings.append(f"Script execution timeout: {script_path}")
                    except Exception as e:
                        warnings.append(f"Could not test execution of {script_path}: {str(e)}")
                
            except SyntaxError as e:
                script_results[script_path] = f"SYNTAX_ERROR: {str(e)}"
                failed_scripts.append(script_path)
                logger.error(f"❌ Syntax error in: {script_path} - {e}")
                
            except Exception as e:
                script_results[script_path] = f"ERROR: {str(e)}"
                failed_scripts.append(script_path)
                logger.error(f"❌ Error validating: {script_path} - {e}")
        
        success = len(failed_scripts) == 0
        message = f"Script validation: {len(script_results) - len(failed_scripts)}/{len(script_results)} scripts validated successfully"
        
        if failed_scripts:
            message += f". Failed: {failed_scripts}"
        
        return ValidationResult(
            test_name="script_validation",
            success=success,
            message=message,
            details={"script_results": script_results, "failed_scripts": failed_scripts},
            warnings=warnings
        )
    
    def validate_directory_structure(self) -> ValidationResult:
        """Validate that the directory structure is correct."""
        logger.info("Validating directory structure...")
        
        structure_results = {}
        missing_dirs = []
        warnings = []
        
        # Expected critical directories
        expected_dirs = [
            "src",
            "src/codexes",
            "src/codexes/core",
            "src/codexes/modules",
            "tests",
            "docs",
            "configs",
            "data",
            "logs",
            "prompts",
        ]
        
        for dir_path in expected_dirs:
            full_path = self.root_path / dir_path
            
            if full_path.exists() and full_path.is_dir():
                structure_results[dir_path] = "EXISTS"
                logger.info(f"✅ Directory exists: {dir_path}")
            else:
                structure_results[dir_path] = "MISSING"
                missing_dirs.append(dir_path)
                logger.error(f"❌ Directory missing: {dir_path}")
        
        # Check for unexpected directories in root
        root_dirs = [d for d in self.root_path.iterdir() if d.is_dir()]
        expected_root_dirs = {
            "src", "tests", "docs", "configs", "data", "logs", "prompts",
            "resources", "templates", "examples", "imprints", "output",
            ".git", ".venv", ".kiro", "__pycache__", ".pytest_cache"
        }
        
        unexpected_dirs = []
        for root_dir in root_dirs:
            if root_dir.name not in expected_root_dirs:
                unexpected_dirs.append(root_dir.name)
                warnings.append(f"Unexpected directory in root: {root_dir.name}")
        
        success = len(missing_dirs) == 0
        message = f"Directory structure validation: {len(structure_results) - len(missing_dirs)}/{len(structure_results)} expected directories found"
        
        if missing_dirs:
            message += f". Missing: {missing_dirs}"
        
        if unexpected_dirs:
            message += f". Unexpected: {unexpected_dirs}"
        
        return ValidationResult(
            test_name="directory_structure_validation",
            success=success,
            message=message,
            details={
                "structure_results": structure_results,
                "missing_dirs": missing_dirs,
                "unexpected_dirs": unexpected_dirs
            },
            warnings=warnings
        )
    
    def validate_functionality_preservation(self) -> ValidationResult:
        """Validate that existing functionality is preserved."""
        logger.info("Validating functionality preservation...")
        
        functionality_results = {}
        failed_functions = []
        warnings = []
        
        # Test core functionality
        try:
            # Test file analysis engine
            from codexes.core.file_analysis_engine import FileAnalysisEngine
            engine = FileAnalysisEngine()
            engine.scan_directory_structure()
            functionality_results["file_analysis_engine"] = "SUCCESS"
            logger.info("✅ File analysis engine working")
        except Exception as e:
            functionality_results["file_analysis_engine"] = f"ERROR: {str(e)}"
            failed_functions.append("file_analysis_engine")
            logger.error(f"❌ File analysis engine error: {e}")
        
        # Test safety validator
        try:
            from codexes.core.safety_validator import SafetyValidator
            validator = SafetyValidator()
            validator.validate_file_safety("README.md")
            functionality_results["safety_validator"] = "SUCCESS"
            logger.info("✅ Safety validator working")
        except Exception as e:
            functionality_results["safety_validator"] = f"ERROR: {str(e)}"
            failed_functions.append("safety_validator")
            logger.error(f"❌ Safety validator error: {e}")
        
        # Test temporary file cleaner
        try:
            from codexes.core.temporary_file_cleaner import TemporaryFileCleaner
            cleaner = TemporaryFileCleaner()
            cleaner.categorize_temp_files()
            functionality_results["temporary_file_cleaner"] = "SUCCESS"
            logger.info("✅ Temporary file cleaner working")
        except Exception as e:
            functionality_results["temporary_file_cleaner"] = f"ERROR: {str(e)}"
            failed_functions.append("temporary_file_cleaner")
            logger.error(f"❌ Temporary file cleaner error: {e}")
        
        # Test LLM integration (if available)
        try:
            from codexes.core.llm_caller import call_model_with_prompt
            functionality_results["llm_integration"] = "SUCCESS"
            logger.info("✅ LLM integration available")
        except Exception as e:
            warnings.append(f"LLM integration issue (may be expected): {str(e)}")
            functionality_results["llm_integration"] = f"WARNING: {str(e)}"
        
        # Test metadata models
        try:
            from codexes.modules.metadata.metadata_models import CodexMetadata
            test_metadata = CodexMetadata(title="Test", author="Test Author")
            functionality_results["metadata_models"] = "SUCCESS"
            logger.info("✅ Metadata models working")
        except Exception as e:
            functionality_results["metadata_models"] = f"ERROR: {str(e)}"
            failed_functions.append("metadata_models")
            logger.error(f"❌ Metadata models error: {e}")
        
        success = len(failed_functions) == 0
        message = f"Functionality preservation: {len(functionality_results) - len(failed_functions)}/{len(functionality_results)} functions working"
        
        if failed_functions:
            message += f". Failed: {failed_functions}"
        
        return ValidationResult(
            test_name="functionality_preservation",
            success=success,
            message=message,
            details={"functionality_results": functionality_results, "failed_functions": failed_functions},
            warnings=warnings
        )
    
    def _discover_src_modules(self) -> List[str]:
        """Discover Python modules in the src directory."""
        modules = []
        src_path = self.root_path / "src"
        
        if not src_path.exists():
            return modules
        
        for py_file in src_path.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            try:
                relative_path = py_file.relative_to(src_path)
                module_parts = list(relative_path.with_suffix('').parts)
                module_name = '.'.join(module_parts)
                modules.append(module_name)
            except Exception:
                continue
        
        return modules
    
    def _validate_lsi_config_structure(self, config_data: Dict[str, Any], warnings: List[str]) -> None:
        """Validate LSI configuration structure."""
        required_sections = ["field_mappings", "validation_rules", "completion_strategies"]
        
        for section in required_sections:
            if section not in config_data:
                warnings.append(f"Missing section in LSI config: {section}")
    
    def _extract_file_references(self, py_file: Path) -> List[str]:
        """Extract file references from a Python file."""
        references = []
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for file path patterns
            import re
            patterns = [
                r'["\']([^"\']+\.(json|csv|txt|md|py|tex))["\']',
                r'Path\(["\']([^"\']+)["\']',
                r'open\(["\']([^"\']+)["\']',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, tuple):
                        references.append(match[0])
                    else:
                        references.append(match)
        
        except Exception:
            pass
        
        return references
    
    def _extract_config_references(self, config_file: Path) -> List[str]:
        """Extract file references from a configuration file."""
        references = []
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for file paths in JSON values
            import re
            patterns = [
                r'"([^"]+\.(json|csv|txt|md|py|tex))"',
                r'"([^"]+/[^"]+\.[a-zA-Z0-9]+)"',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, tuple):
                        references.append(match[0])
                    else:
                        references.append(match)
        
        except Exception:
            pass
        
        return references
    
    def _resolve_reference_path(self, reference: str, base_dir: Path) -> Optional[Path]:
        """Resolve a file reference to an absolute path."""
        if reference.startswith(('http://', 'https://', 'mailto:')):
            return None
        
        # Try relative to base directory
        ref_path = base_dir / reference
        if ref_path.exists():
            return ref_path
        
        # Try relative to project root
        ref_path = self.root_path / reference
        if ref_path.exists():
            return ref_path
        
        return self.root_path / reference  # Return path even if it doesn't exist for checking
    
    def _generate_validation_report(self, validation_summary: Dict[str, Any]) -> None:
        """Generate a comprehensive validation report."""
        logger.info("\n" + "=" * 60)
        logger.info("SYSTEM INTEGRITY VALIDATION SUMMARY")
        logger.info("=" * 60)
        
        logger.info(f"Total Tests: {validation_summary['total_tests']}")
        logger.info(f"Passed: {validation_summary['passed_tests']}")
        logger.info(f"Failed: {validation_summary['failed_tests']}")
        logger.info(f"Warnings: {validation_summary['warnings']}")
        logger.info(f"Overall Success: {'✅ YES' if validation_summary['overall_success'] else '❌ NO'}")
        
        logger.info("\nDetailed Results:")
        for result in validation_summary["test_results"]:
            status = "✅ PASS" if result.success else "❌ FAIL"
            logger.info(f"  {result.test_name}: {status} - {result.message}")
            
            if result.warnings:
                for warning in result.warnings:
                    logger.info(f"    ⚠️  {warning}")
            
            if result.errors:
                for error in result.errors:
                    logger.info(f"    ❌ {error}")
        
        # Save detailed report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.root_path / f"system_integrity_validation_{timestamp}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(validation_summary, f, indent=2, default=str)
        
        logger.info(f"\nDetailed validation report saved to: {report_path}")


def main():
    """Main function to run system integrity validation."""
    validator = SystemIntegrityValidator()
    results = validator.run_comprehensive_validation()
    
    # Return appropriate exit code
    if results["overall_success"]:
        logger.info("\n🎉 SYSTEM INTEGRITY VALIDATION PASSED!")
        logger.info("All critical functionality is preserved after cleanup operations.")
        return True
    else:
        logger.error("\n💥 SYSTEM INTEGRITY VALIDATION FAILED!")
        logger.error("Some critical functionality may be broken. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)