#!/usr/bin/env python3
"""
Repository Analysis CLI Tool

This script demonstrates the file analysis and safety infrastructure
for the dot-release-cleanup project.
"""

import sys
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codexes.core.file_inventory_system import FileInventorySystem


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Analyze repository structure for cleanup operations"
    )
    parser.add_argument(
        "--root", 
        default=".", 
        help="Root directory to analyze (default: current directory)"
    )
    parser.add_argument(
        "--output", 
        help="Output file for analysis report (JSON format)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Initialize the inventory system
    print(f"Initializing file inventory system for: {Path(args.root).resolve()}")
    inventory_system = FileInventorySystem(args.root)
    
    # Perform full analysis
    try:
        report = inventory_system.perform_full_analysis()
        
        # Display summary
        print("\n" + "="*60)
        print("REPOSITORY ANALYSIS SUMMARY")
        print("="*60)
        print(f"Total files analyzed: {report.total_files}")
        print(f"Analysis timestamp: {report.timestamp}")
        
        print(f"\nFile Categories:")
        for category, files in report.categorized_files.items():
            print(f"  {category}: {len(files)} files")
        
        print(f"\nCleanup Opportunities:")
        print(f"  Temporary files: {len(report.temporary_files)}")
        print(f"  Misplaced tests: {len(report.misplaced_tests)}")
        print(f"  Misplaced docs: {len(report.misplaced_docs)}")
        
        if report.config_files:
            print(f"  Configuration directories: {len(report.config_files)}")
            for config_dir, files in report.config_files.items():
                print(f"    {config_dir}: {len(files)} files")
        
        if report.resource_files:
            print(f"  Resource files to organize:")
            for resource_type, files in report.resource_files.items():
                print(f"    {resource_type}: {len(files)} files")
        
        if report.safety_issues:
            print(f"\nSafety Issues Found: {len(report.safety_issues)}")
            if args.verbose:
                for issue in report.safety_issues[:10]:  # Show first 10
                    print(f"  - {issue}")
                if len(report.safety_issues) > 10:
                    print(f"  ... and {len(report.safety_issues) - 10} more")
        
        print(f"\nRecommendations:")
        for i, recommendation in enumerate(report.recommendations, 1):
            print(f"  {i}. {recommendation}")
        
        # Save report if requested
        if args.output:
            inventory_system.save_inventory_report(report, args.output)
            print(f"\nDetailed report saved to: {args.output}")
        
        # Show some example file details if verbose
        if args.verbose and report.temporary_files:
            print(f"\nExample Temporary Files:")
            for temp_file in report.temporary_files[:5]:
                file_info = inventory_system.get_file_info(temp_file)
                safety_check = inventory_system.get_safety_check(temp_file)
                print(f"  {temp_file}:")
                print(f"    Size: {file_info.size if file_info else 'unknown'} bytes")
                print(f"    Safe to delete: {safety_check.is_safe if safety_check else 'unknown'}")
                if safety_check and safety_check.warnings:
                    print(f"    Warnings: {', '.join(safety_check.warnings)}")
        
        print("\nAnalysis complete!")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()