#!/usr/bin/env python3
"""
Configuration Unification Demo

This script demonstrates how to use the configuration directory unification system
to merge config/ and configs/ directories and update all code references.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.codexes.core.unified_configuration_system import UnifiedConfigurationSystem
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Demonstrate the configuration unification process."""
    print("Configuration Directory Unification Demo")
    print("=" * 50)
    
    # Initialize the unified configuration system
    system = UnifiedConfigurationSystem()
    
    print("\n1. Analyzing current configuration state...")
    analysis = system.analyze_current_state()
    
    # Display analysis results
    if "directory_analysis" in analysis:
        dir_stats = analysis["directory_analysis"]["statistics"]
        print(f"   - Config files: {dir_stats['config_files_count']}")
        print(f"   - Configs files: {dir_stats['configs_files_count']}")
        print(f"   - Conflicts: {dir_stats['conflicts_count']}")
    
    if "reference_analysis" in analysis:
        ref_stats = analysis["reference_analysis"]
        print(f"   - Files scanned: {len(ref_stats['files_scanned'])}")
        print(f"   - References found: {len(ref_stats['references_found'])}")
    
    # Display readiness assessment
    if "readiness_assessment" in analysis:
        readiness = analysis["readiness_assessment"]
        print(f"\n2. Readiness Assessment:")
        print(f"   - Ready for unification: {readiness['ready']}")
        print(f"   - Confidence level: {readiness['confidence_level']}")
        
        if readiness["blocking_issues"]:
            print("   - Blocking issues:")
            for issue in readiness["blocking_issues"]:
                print(f"     * {issue}")
        
        if readiness["warnings"]:
            print("   - Warnings:")
            for warning in readiness["warnings"]:
                print(f"     * {warning}")
    
    # Display recommendations
    if "recommendations" in analysis:
        recommendations = analysis["recommendations"]
        if recommendations:
            print("\n3. Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
    
    print("\n4. Executing unification (DRY RUN)...")
    
    # Execute unification in dry run mode
    results = system.execute_unification(dry_run=True)
    
    print(f"   - Success: {results.success}")
    print(f"   - Directory operations: {results.directory_merge_results.get('operations_completed', 0)}")
    print(f"   - Reference updates: {results.reference_update_results.get('references_updated', 0)}")
    
    if results.errors:
        print("   - Errors:")
        for error in results.errors:
            print(f"     * {error}")
    
    if results.warnings:
        print("   - Warnings:")
        for warning in results.warnings:
            print(f"     * {warning}")
    
    print("\n5. Generating report...")
    report = system.generate_unification_report(results)
    
    # Save report to file
    report_file = Path("config_unification_report.md")
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"   - Report saved to: {report_file}")
    
    print("\nDemo complete!")
    print("\nTo execute the actual unification:")
    print("  results = system.execute_unification(dry_run=False)")
    print("\nTo validate after unification:")
    print("  validation = system.validate_post_unification()")


if __name__ == "__main__":
    main()