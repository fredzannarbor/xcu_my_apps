#!/usr/bin/env python3
"""
Comprehensive Cleanup Validation Runner.

This script orchestrates the complete cleanup validation process including:
1. System integrity validation
2. Cleanup report generation
3. Documentation creation
4. Final validation summary
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add src and tests to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from test_system_integrity_validation import SystemIntegrityValidator
from codexes.core.cleanup_report_generator import (
    CleanupReportGenerator, CleanupOperation, DirectoryStructureChange
)


class ComprehensiveCleanupValidator:
    """
    Comprehensive validator that orchestrates all cleanup validation processes.
    
    Combines system integrity validation, cleanup reporting, and documentation
    generation into a single comprehensive validation workflow.
    """
    
    def __init__(self, root_path: str = "."):
        """
        Initialize the comprehensive cleanup validator.
        
        Args:
            root_path: Root directory of the project
        """
        self.root_path = Path(root_path).resolve()
        self.system_validator = SystemIntegrityValidator(str(self.root_path))
        self.report_generator = CleanupReportGenerator(str(self.root_path))
        
        # Results storage
        self.validation_results = {}
        self.cleanup_operations = []
        self.directory_changes = []
    
    def run_comprehensive_validation(self, 
                                   operations: list = None, 
                                   directory_changes: list = None) -> dict:
        """
        Run comprehensive cleanup validation.
        
        Args:
            operations: Optional list of cleanup operations performed
            directory_changes: Optional list of directory structure changes
            
        Returns:
            Dictionary containing all validation results and reports
        """
        print("🚀 STARTING COMPREHENSIVE CLEANUP VALIDATION")
        print("=" * 80)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "validation_phase": {},
            "reporting_phase": {},
            "documentation_phase": {},
            "overall_success": False,
            "generated_files": []
        }
        
        # Phase 1: System Integrity Validation
        print("\n📋 PHASE 1: SYSTEM INTEGRITY VALIDATION")
        print("-" * 50)
        
        try:
            validation_results = self.system_validator.run_comprehensive_validation()
            results["validation_phase"] = validation_results
            
            if validation_results["overall_success"]:
                print("✅ System integrity validation PASSED")
            else:
                print("⚠️ System integrity validation had issues")
                print(f"   Failed tests: {validation_results['failed_tests']}")
                print(f"   Warnings: {validation_results['warnings']}")
        
        except Exception as e:
            print(f"❌ System integrity validation FAILED: {e}")
            results["validation_phase"] = {"error": str(e), "overall_success": False}
        
        # Phase 2: Cleanup Report Generation
        print("\n📊 PHASE 2: CLEANUP REPORT GENERATION")
        print("-" * 50)
        
        try:
            # Start cleanup session
            session_id = self.report_generator.start_cleanup_session()
            print(f"Started cleanup session: {session_id}")
            
            # Record operations if provided
            if operations:
                for operation in operations:
                    self.report_generator.record_operation(operation)
                print(f"Recorded {len(operations)} cleanup operations")
            
            # Record directory changes if provided
            if directory_changes:
                for change in directory_changes:
                    self.report_generator.record_directory_change(change)
                print(f"Recorded {len(directory_changes)} directory changes")
            
            # Generate comprehensive report
            report_path = self.report_generator.generate_comprehensive_report(
                validation_results=results["validation_phase"]
            )
            
            results["reporting_phase"] = {
                "session_id": session_id,
                "report_path": str(report_path),
                "success": True
            }
            results["generated_files"].append(str(report_path))
            
            print(f"✅ Generated cleanup report: {report_path}")
        
        except Exception as e:
            print(f"❌ Cleanup report generation FAILED: {e}")
            results["reporting_phase"] = {"error": str(e), "success": False}
        
        # Phase 3: Documentation Generation
        print("\n📚 PHASE 3: DOCUMENTATION GENERATION")
        print("-" * 50)
        
        try:
            # Generate directory structure documentation
            structure_doc_path = self.report_generator.generate_directory_structure_documentation()
            print(f"✅ Generated directory structure documentation: {structure_doc_path}")
            results["generated_files"].append(str(structure_doc_path))
            
            # Generate validation summary
            validation_summary_path = self.report_generator.generate_validation_summary(
                validation_results=results["validation_phase"]
            )
            print(f"✅ Generated validation summary: {validation_summary_path}")
            results["generated_files"].append(str(validation_summary_path))
            
            results["documentation_phase"] = {
                "structure_doc_path": str(structure_doc_path),
                "validation_summary_path": str(validation_summary_path),
                "success": True
            }
        
        except Exception as e:
            print(f"❌ Documentation generation FAILED: {e}")
            results["documentation_phase"] = {"error": str(e), "success": False}
        
        # Phase 4: Final Assessment
        print("\n🎯 PHASE 4: FINAL ASSESSMENT")
        print("-" * 50)
        
        validation_success = results["validation_phase"].get("overall_success", False)
        reporting_success = results["reporting_phase"].get("success", False)
        documentation_success = results["documentation_phase"].get("success", False)
        
        results["overall_success"] = validation_success and reporting_success and documentation_success
        
        # Generate final summary
        self._generate_final_summary(results)
        
        return results
    
    def create_sample_cleanup_data(self) -> tuple:
        """
        Create sample cleanup operations and directory changes for demonstration.
        
        Returns:
            Tuple of (operations, directory_changes)
        """
        operations = [
            CleanupOperation(
                operation_id="temp_cleanup_001",
                operation_type="delete",
                source_path="exported_config_20240826_120000.json",
                destination_path=None,
                timestamp=datetime.now(),
                success=True,
                message="Removed temporary exported configuration file",
                files_affected=["exported_config_20240826_120000.json"]
            ),
            CleanupOperation(
                operation_id="test_move_001",
                operation_type="move",
                source_path="test_pipeline_success_messages.py",
                destination_path="tests/test_pipeline_success_messages.py",
                timestamp=datetime.now(),
                success=True,
                message="Moved test file to tests directory",
                files_affected=["test_pipeline_success_messages.py"],
                references_updated=["docs/TESTING_README.md"]
            ),
            CleanupOperation(
                operation_id="config_merge_001",
                operation_type="merge",
                source_path="config",
                destination_path="configs",
                timestamp=datetime.now(),
                success=True,
                message="Merged config directory into configs for consistency",
                files_affected=["config/streamlit_apps.json", "config/user_config.json"],
                references_updated=["multistart_streamlit.py", "start_streamlit.py"]
            )
        ]
        
        directory_changes = [
            DirectoryStructureChange(
                change_type="removed",
                path="config",
                reason="Merged into configs directory for consistency",
                files_count=2
            ),
            DirectoryStructureChange(
                change_type="created",
                path="cleanup_reports",
                reason="Created directory for cleanup reports and documentation",
                files_count=0
            ),
            DirectoryStructureChange(
                change_type="moved",
                path="tests/test_pipeline_success_messages.py",
                old_path="test_pipeline_success_messages.py",
                new_path="tests/test_pipeline_success_messages.py",
                reason="Moved test file to proper tests directory",
                files_count=1
            )
        ]
        
        return operations, directory_changes
    
    def _generate_final_summary(self, results: dict) -> None:
        """Generate and display final summary."""
        print("\n" + "=" * 80)
        print("🏁 COMPREHENSIVE CLEANUP VALIDATION SUMMARY")
        print("=" * 80)
        
        # Overall status
        if results["overall_success"]:
            print("✅ OVERALL STATUS: SUCCESS")
            print("   All validation phases completed successfully!")
        else:
            print("❌ OVERALL STATUS: ISSUES DETECTED")
            print("   Some validation phases had problems.")
        
        print()
        
        # Phase results
        validation_status = "✅ PASS" if results["validation_phase"].get("overall_success", False) else "❌ FAIL"
        reporting_status = "✅ PASS" if results["reporting_phase"].get("success", False) else "❌ FAIL"
        documentation_status = "✅ PASS" if results["documentation_phase"].get("success", False) else "❌ FAIL"
        
        print(f"📋 System Integrity Validation: {validation_status}")
        print(f"📊 Cleanup Report Generation:   {reporting_status}")
        print(f"📚 Documentation Generation:    {documentation_status}")
        
        print()
        
        # Generated files
        if results["generated_files"]:
            print("📁 Generated Files:")
            for file_path in results["generated_files"]:
                print(f"   - {file_path}")
        
        print()
        
        # Recommendations
        print("💡 Recommendations:")
        
        if results["overall_success"]:
            print("   ✅ All validation phases passed successfully")
            print("   ✅ Repository cleanup operations are validated")
            print("   ✅ Documentation has been generated")
            print("   📝 Review the generated reports for detailed information")
            print("   🚀 Repository is ready for continued development")
        else:
            print("   ⚠️ Review failed validation phases above")
            print("   🔧 Fix any identified issues before proceeding")
            print("   📋 Check generated reports for detailed error information")
            print("   🔄 Re-run validation after fixing issues")
        
        print("=" * 80)


def main():
    """Main function to run comprehensive cleanup validation."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive cleanup validation including system integrity, reporting, and documentation"
    )
    parser.add_argument(
        "--root-path",
        default=".",
        help="Root path of the project (default: current directory)"
    )
    parser.add_argument(
        "--with-sample-data",
        action="store_true",
        help="Include sample cleanup operations for demonstration"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize validator
    validator = ComprehensiveCleanupValidator(args.root_path)
    
    # Prepare cleanup data
    operations = None
    directory_changes = None
    
    if args.with_sample_data:
        operations, directory_changes = validator.create_sample_cleanup_data()
        print(f"Using sample data: {len(operations)} operations, {len(directory_changes)} directory changes")
    
    # Run comprehensive validation
    results = validator.run_comprehensive_validation(operations, directory_changes)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_path = Path(args.root_path) / f"comprehensive_validation_results_{timestamp}.json"
    
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_path}")
    
    # Return appropriate exit code
    return 0 if results["overall_success"] else 1


if __name__ == "__main__":
    sys.exit(main())