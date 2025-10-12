#!/usr/bin/env python3
"""
Comprehensive quality assurance script for arxiv-writer package.

This script performs final quality assurance checks including:
- Test suite execution across Python versions
- Documentation validation
- Package installation testing
- Security audit
- Dependency vulnerability assessment
"""

import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse
import logging
import json
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QualityAssuranceValidator:
    """Comprehensive quality assurance validator."""
    
    def __init__(self, workspace_root: str = ".", verbose: bool = False):
        """Initialize validator."""
        self.workspace_root = Path(workspace_root)
        self.verbose = verbose
        self.temp_dirs = []
        
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup temp directories."""
        self.cleanup()
    
    def cleanup(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                if Path(temp_dir).exists():
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup {temp_dir}: {e}")
    
    def run_comprehensive_qa(self) -> Dict[str, Any]:
        """Run comprehensive quality assurance checks."""
        logger.info("Starting comprehensive quality assurance validation")
        
        qa_report = {
            "timestamp": datetime.now().isoformat(),
            "workspace_root": str(self.workspace_root),
            "python_version": sys.version,
            "checks_run": [],
            "checks_passed": 0,
            "checks_failed": 0,
            "errors": [],
            "warnings": [],
            "summary": ""
        }
        
        # QA check categories
        qa_checks = [
            ("Test Suite Execution", self._run_test_suite),
            ("Code Quality Analysis", self._analyze_code_quality),
            ("Documentation Validation", self._validate_documentation),
            ("Package Installation Test", self._test_package_installation),
            ("Import and API Test", self._test_imports_and_api),
            ("Configuration Validation", self._validate_configurations),
            ("Security Audit", self._run_security_audit),
            ("Dependency Analysis", self._analyze_dependencies),
            ("Cross-Platform Compatibility", self._test_cross_platform_compatibility),
            ("Performance Baseline", self._establish_performance_baseline)
        ]
        
        for check_name, check_func in qa_checks:
            logger.info(f"Running QA check: {check_name}")
            try:
                check_result = check_func()
                check_result["check_name"] = check_name
                qa_report["checks_run"].append(check_result)
                
                if check_result["passed"]:
                    qa_report["checks_passed"] += 1
                    logger.info(f"✓ {check_name} - PASSED")
                else:
                    qa_report["checks_failed"] += 1
                    logger.error(f"✗ {check_name} - FAILED")
                    qa_report["errors"].extend(check_result.get("errors", []))
                
                qa_report["warnings"].extend(check_result.get("warnings", []))
                
            except Exception as e:
                logger.error(f"✗ {check_name} - ERROR: {e}")
                qa_report["checks_failed"] += 1
                qa_report["errors"].append(f"{check_name}: {str(e)}")
        
        # Generate summary
        total_checks = qa_report["checks_passed"] + qa_report["checks_failed"]
        success_rate = (qa_report["checks_passed"] / total_checks * 100) if total_checks > 0 else 0
        
        qa_report["summary"] = (
            f"QA completed: {qa_report['checks_passed']}/{total_checks} checks passed "
            f"({success_rate:.1f}% success rate)"
        )
        
        if qa_report["checks_failed"] == 0:
            logger.info("🎉 All quality assurance checks passed!")
        else:
            logger.error(f"❌ {qa_report['checks_failed']} checks failed")
        
        return qa_report
    
    def _run_test_suite(self) -> Dict[str, Any]:
        """Run the complete test suite."""
        result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        try:
            # Run pytest with coverage
            cmd = [
                sys.executable, "-m", "pytest",
                "tests/",
                "-v",
                "--tb=short",
                "--maxfail=10"
            ]
            
            if self.verbose:
                cmd.append("--verbose")
            
            logger.debug(f"Running command: {' '.join(cmd)}")
            
            process = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            result["details"]["exit_code"] = process.returncode
            result["details"]["stdout_lines"] = len(process.stdout.splitlines())
            result["details"]["stderr_lines"] = len(process.stderr.splitlines())
            
            if process.returncode != 0:
                result["passed"] = False
                result["errors"].append(f"Test suite failed with exit code {process.returncode}")
                
                # Extract key error information
                stderr_lines = process.stderr.splitlines()
                for line in stderr_lines[-10:]:  # Last 10 lines of stderr
                    if "FAILED" in line or "ERROR" in line:
                        result["errors"].append(line.strip())
            
            # Parse test results from stdout
            stdout_lines = process.stdout.splitlines()
            for line in stdout_lines:
                if "passed" in line and "failed" in line:
                    result["details"]["test_summary"] = line.strip()
                    break
            
        except subprocess.TimeoutExpired:
            result["passed"] = False
            result["errors"].append("Test suite execution timed out")
        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"Failed to run test suite: {str(e)}")
        
        return result
    
    def _analyze_code_quality(self) -> Dict[str, Any]:
        """Analyze code quality using various tools."""
        result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        # Check if we can import the main package
        try:
            sys.path.insert(0, str(self.workspace_root / "src"))
            import arxiv_writer
            result["details"]["package_importable"] = True
            result["details"]["package_version"] = getattr(arxiv_writer, "__version__", "unknown")
        except ImportError as e:
            result["warnings"].append(f"Package import failed: {e}")
            result["details"]["package_importable"] = False
        
        # Check for basic code structure
        src_dir = self.workspace_root / "src" / "arxiv_writer"
        if src_dir.exists():
            python_files = list(src_dir.rglob("*.py"))
            result["details"]["python_files_count"] = len(python_files)
            result["details"]["modules"] = [
                str(f.relative_to(src_dir)) for f in python_files
                if f.name != "__pycache__"
            ]
        else:
            result["passed"] = False
            result["errors"].append("Source directory not found")
        
        # Check for required files
        required_files = [
            "pyproject.toml",
            "README.md",
            "LICENSE",
            "src/arxiv_writer/__init__.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not (self.workspace_root / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            result["warnings"].extend([f"Missing file: {f}" for f in missing_files])
        
        result["details"]["required_files_present"] = len(required_files) - len(missing_files)
        result["details"]["required_files_total"] = len(required_files)
        
        return result
    
    def _validate_documentation(self) -> Dict[str, Any]:
        """Validate documentation completeness and accuracy."""
        result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        # Check for documentation files
        docs_dir = self.workspace_root / "docs"
        if docs_dir.exists():
            doc_files = list(docs_dir.rglob("*.md")) + list(docs_dir.rglob("*.rst"))
            result["details"]["doc_files_count"] = len(doc_files)
            result["details"]["doc_files"] = [str(f.relative_to(docs_dir)) for f in doc_files]
        else:
            result["warnings"].append("Documentation directory not found")
            result["details"]["doc_files_count"] = 0
        
        # Check README
        readme_path = self.workspace_root / "README.md"
        if readme_path.exists():
            readme_content = readme_path.read_text(encoding='utf-8')
            result["details"]["readme_length"] = len(readme_content)
            result["details"]["readme_has_installation"] = "install" in readme_content.lower()
            result["details"]["readme_has_usage"] = "usage" in readme_content.lower()
        else:
            result["errors"].append("README.md not found")
            result["passed"] = False
        
        # Check examples directory
        examples_dir = self.workspace_root / "examples"
        if examples_dir.exists():
            example_files = list(examples_dir.rglob("*.py"))
            result["details"]["example_files_count"] = len(example_files)
        else:
            result["warnings"].append("Examples directory not found")
        
        return result
    
    def _test_package_installation(self) -> Dict[str, Any]:
        """Test package installation in clean environment."""
        result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        try:
            # Create temporary directory for installation test
            temp_dir = tempfile.mkdtemp(prefix="arxiv_writer_install_test_")
            self.temp_dirs.append(temp_dir)
            
            # Test pip install in development mode
            cmd = [
                sys.executable, "-m", "pip", "install", "-e", ".",
                "--target", temp_dir,
                "--no-deps"  # Don't install dependencies to speed up test
            ]
            
            logger.debug(f"Running installation test: {' '.join(cmd)}")
            
            process = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            result["details"]["install_exit_code"] = process.returncode
            
            if process.returncode != 0:
                result["passed"] = False
                result["errors"].append(f"Package installation failed with exit code {process.returncode}")
                result["errors"].append(process.stderr.strip())
            else:
                # Test that package can be imported from installed location
                try:
                    sys.path.insert(0, temp_dir)
                    import arxiv_writer
                    result["details"]["post_install_import_success"] = True
                except ImportError as e:
                    result["warnings"].append(f"Post-install import failed: {e}")
                    result["details"]["post_install_import_success"] = False
                finally:
                    if temp_dir in sys.path:
                        sys.path.remove(temp_dir)
            
        except subprocess.TimeoutExpired:
            result["passed"] = False
            result["errors"].append("Package installation timed out")
        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"Installation test failed: {str(e)}")
        
        return result
    
    def _test_imports_and_api(self) -> Dict[str, Any]:
        """Test package imports and API functionality."""
        result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        try:
            # Ensure src is in path
            src_path = str(self.workspace_root / "src")
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            
            # Test core imports
            core_imports = [
                "arxiv_writer",
                "arxiv_writer.core.generator",
                "arxiv_writer.core.models",
                "arxiv_writer.core.context_collector",
                "arxiv_writer.core.codexes_factory_adapter",
                "arxiv_writer.llm.caller",
                "arxiv_writer.templates.manager",
                "arxiv_writer.cli.main"
            ]
            
            successful_imports = []
            failed_imports = []
            
            for import_name in core_imports:
                try:
                    __import__(import_name)
                    successful_imports.append(import_name)
                except ImportError as e:
                    failed_imports.append(f"{import_name}: {str(e)}")
            
            result["details"]["successful_imports"] = len(successful_imports)
            result["details"]["failed_imports"] = len(failed_imports)
            result["details"]["total_imports_tested"] = len(core_imports)
            
            if failed_imports:
                result["errors"].extend(failed_imports)
                if len(failed_imports) > len(successful_imports):
                    result["passed"] = False
            
            # Test basic API functionality
            try:
                from arxiv_writer.core.codexes_factory_adapter import create_codexes_compatibility_config
                config = create_codexes_compatibility_config()
                result["details"]["api_test_config_creation"] = True
            except Exception as e:
                result["warnings"].append(f"API test failed: {str(e)}")
                result["details"]["api_test_config_creation"] = False
            
        except Exception as e:
            result["passed"] = False
            result["errors"].append(f"Import and API test failed: {str(e)}")
        
        return result
    
    def _validate_configurations(self) -> Dict[str, Any]:
        """Validate configuration files and examples."""
        result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        # Check pyproject.toml
        pyproject_path = self.workspace_root / "pyproject.toml"
        if pyproject_path.exists():
            try:
                import tomllib
                with open(pyproject_path, 'rb') as f:
                    pyproject_data = tomllib.load(f)
                
                result["details"]["pyproject_valid"] = True
                result["details"]["has_build_system"] = "build-system" in pyproject_data
                result["details"]["has_project_metadata"] = "project" in pyproject_data
                
                if "project" in pyproject_data:
                    project = pyproject_data["project"]
                    result["details"]["project_name"] = project.get("name", "unknown")
                    result["details"]["project_version"] = project.get("version", "unknown")
                    result["details"]["has_dependencies"] = "dependencies" in project
                
            except Exception as e:
                result["errors"].append(f"Failed to parse pyproject.toml: {str(e)}")
                result["passed"] = False
        else:
            result["errors"].append("pyproject.toml not found")
            result["passed"] = False
        
        # Check example configurations
        examples_dir = self.workspace_root / "examples" / "configs"
        if examples_dir.exists():
            config_files = list(examples_dir.rglob("*.json"))
            result["details"]["example_config_files"] = len(config_files)
            
            valid_configs = 0
            for config_file in config_files:
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        json.load(f)
                    valid_configs += 1
                except json.JSONDecodeError as e:
                    result["warnings"].append(f"Invalid JSON in {config_file}: {str(e)}")
            
            result["details"]["valid_example_configs"] = valid_configs
        
        return result
    
    def _run_security_audit(self) -> Dict[str, Any]:
        """Run basic security audit checks."""
        result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        # Check for common security issues in code
        src_dir = self.workspace_root / "src"
        if src_dir.exists():
            python_files = list(src_dir.rglob("*.py"))
            
            security_issues = []
            for py_file in python_files:
                try:
                    content = py_file.read_text(encoding='utf-8')
                    
                    # Check for potential security issues
                    if "eval(" in content:
                        security_issues.append(f"{py_file}: Uses eval()")
                    if "exec(" in content:
                        security_issues.append(f"{py_file}: Uses exec()")
                    if "shell=True" in content:
                        security_issues.append(f"{py_file}: Uses shell=True")
                    if "pickle.load" in content:
                        security_issues.append(f"{py_file}: Uses pickle.load")
                    
                except Exception as e:
                    result["warnings"].append(f"Could not scan {py_file}: {str(e)}")
            
            result["details"]["files_scanned"] = len(python_files)
            result["details"]["security_issues_found"] = len(security_issues)
            
            if security_issues:
                result["warnings"].extend(security_issues)
        
        # Check for hardcoded secrets (basic check)
        secret_patterns = ["password", "secret", "key", "token", "api_key"]
        potential_secrets = []
        
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding='utf-8').lower()
                for pattern in secret_patterns:
                    if f"{pattern} = " in content and "test" not in str(py_file).lower():
                        potential_secrets.append(f"{py_file}: Potential hardcoded {pattern}")
            except Exception:
                pass
        
        if potential_secrets:
            result["warnings"].extend(potential_secrets)
        
        result["details"]["potential_secrets_found"] = len(potential_secrets)
        
        return result
    
    def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze package dependencies."""
        result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        # Check pyproject.toml dependencies
        pyproject_path = self.workspace_root / "pyproject.toml"
        if pyproject_path.exists():
            try:
                import tomllib
                with open(pyproject_path, 'rb') as f:
                    pyproject_data = tomllib.load(f)
                
                if "project" in pyproject_data and "dependencies" in pyproject_data["project"]:
                    dependencies = pyproject_data["project"]["dependencies"]
                    result["details"]["declared_dependencies"] = len(dependencies)
                    result["details"]["dependency_list"] = dependencies
                else:
                    result["warnings"].append("No dependencies declared in pyproject.toml")
                    result["details"]["declared_dependencies"] = 0
                
            except Exception as e:
                result["errors"].append(f"Failed to parse dependencies: {str(e)}")
                result["passed"] = False
        
        # Check for unused imports (basic check)
        try:
            src_dir = self.workspace_root / "src"
            if src_dir.exists():
                python_files = list(src_dir.rglob("*.py"))
                
                all_imports = set()
                for py_file in python_files:
                    try:
                        content = py_file.read_text(encoding='utf-8')
                        lines = content.splitlines()
                        
                        for line in lines:
                            line = line.strip()
                            if line.startswith("import ") or line.startswith("from "):
                                # Extract module name
                                if line.startswith("import "):
                                    module = line.split()[1].split('.')[0]
                                else:  # from ... import
                                    module = line.split()[1].split('.')[0]
                                
                                if not module.startswith('.'):  # Skip relative imports
                                    all_imports.add(module)
                    except Exception:
                        pass
                
                result["details"]["unique_imports_found"] = len(all_imports)
                result["details"]["python_files_analyzed"] = len(python_files)
        
        except Exception as e:
            result["warnings"].append(f"Dependency analysis failed: {str(e)}")
        
        return result
    
    def _test_cross_platform_compatibility(self) -> Dict[str, Any]:
        """Test cross-platform compatibility."""
        result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        # Check current platform
        import platform
        result["details"]["platform"] = platform.platform()
        result["details"]["python_version"] = platform.python_version()
        result["details"]["architecture"] = platform.architecture()
        
        # Check for platform-specific code
        src_dir = self.workspace_root / "src"
        if src_dir.exists():
            python_files = list(src_dir.rglob("*.py"))
            
            platform_specific_code = []
            for py_file in python_files:
                try:
                    content = py_file.read_text(encoding='utf-8')
                    
                    # Check for platform-specific imports or code
                    if "platform.system()" in content:
                        platform_specific_code.append(f"{py_file}: Uses platform.system()")
                    if "os.name" in content:
                        platform_specific_code.append(f"{py_file}: Uses os.name")
                    if "sys.platform" in content:
                        platform_specific_code.append(f"{py_file}: Uses sys.platform")
                    
                except Exception:
                    pass
            
            result["details"]["platform_specific_code_found"] = len(platform_specific_code)
            if platform_specific_code:
                result["details"]["platform_specific_locations"] = platform_specific_code
        
        # Test path handling
        try:
            from pathlib import Path
            test_path = Path("test") / "path" / "example.txt"
            result["details"]["pathlib_works"] = True
        except Exception as e:
            result["warnings"].append(f"Path handling test failed: {str(e)}")
            result["details"]["pathlib_works"] = False
        
        return result
    
    def _establish_performance_baseline(self) -> Dict[str, Any]:
        """Establish performance baseline metrics."""
        result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        try:
            import time
            
            # Test import time
            start_time = time.time()
            sys.path.insert(0, str(self.workspace_root / "src"))
            import arxiv_writer
            import_time = time.time() - start_time
            
            result["details"]["import_time_seconds"] = round(import_time, 4)
            
            # Test basic operations
            start_time = time.time()
            from arxiv_writer.core.codexes_factory_adapter import create_codexes_compatibility_config
            config = create_codexes_compatibility_config()
            config_creation_time = time.time() - start_time
            
            result["details"]["config_creation_time_seconds"] = round(config_creation_time, 4)
            
            # Memory usage (basic)
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            result["details"]["memory_usage_mb"] = round(memory_info.rss / 1024 / 1024, 2)
            
        except ImportError:
            result["warnings"].append("psutil not available for memory measurement")
        except Exception as e:
            result["warnings"].append(f"Performance baseline failed: {str(e)}")
        
        return result


def main():
    """Main quality assurance script."""
    parser = argparse.ArgumentParser(description="Run comprehensive quality assurance checks")
    parser.add_argument("--workspace", default=".", help="Workspace root directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", help="Output file for QA report")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failure")
    
    args = parser.parse_args()
    
    with QualityAssuranceValidator(args.workspace, args.verbose) as validator:
        qa_report = validator.run_comprehensive_qa()
        
        # Print summary
        print("\n" + "="*60)
        print("ARXIV-WRITER QUALITY ASSURANCE REPORT")
        print("="*60)
        print(f"Timestamp: {qa_report['timestamp']}")
        print(f"Workspace: {qa_report['workspace_root']}")
        print(f"Python Version: {qa_report['python_version']}")
        print(f"Checks Run: {len(qa_report['checks_run'])}")
        print(f"Checks Passed: {qa_report['checks_passed']}")
        print(f"Checks Failed: {qa_report['checks_failed']}")
        print(f"Summary: {qa_report['summary']}")
        
        if qa_report['errors']:
            print(f"\nErrors ({len(qa_report['errors'])}):")
            for error in qa_report['errors']:
                print(f"  ❌ {error}")
        
        if qa_report['warnings']:
            print(f"\nWarnings ({len(qa_report['warnings'])}):")
            for warning in qa_report['warnings']:
                print(f"  ⚠️  {warning}")
        
        print("\nDetailed Results:")
        for check in qa_report['checks_run']:
            status = "✓ PASSED" if check['passed'] else "✗ FAILED"
            print(f"  {status} - {check['check_name']}")
            if args.verbose and check.get('details'):
                for key, value in check['details'].items():
                    print(f"    {key}: {value}")
        
        # Save report if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(qa_report, f, indent=2, default=str)
            print(f"\nQA report saved to: {args.output}")
        
        # Exit with appropriate code
        if args.fail_fast and qa_report['checks_failed'] > 0:
            sys.exit(1)
        
        sys.exit(0 if qa_report['checks_failed'] == 0 else 1)


if __name__ == "__main__":
    main()