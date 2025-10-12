"""Unified Configuration System

This module provides a complete system for unifying configuration directories
and updating all references in the codebase.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass

from .configuration_unifier import ConfigurationUnifier
from .configuration_reference_updater import ConfigurationReferenceUpdater

logger = logging.getLogger(__name__)


@dataclass
class UnificationResults:
    """Results of the complete configuration unification process."""
    success: bool
    directory_merge_results: Dict[str, Any]
    reference_update_results: Dict[str, Any]
    validation_results: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    summary: Dict[str, Any]


class UnifiedConfigurationSystem:
    """
    Complete system for configuration directory unification.
    
    This class orchestrates the entire process of:
    1. Analyzing and merging config/ and configs/ directories
    2. Updating all code references to use the unified structure
    3. Validating that everything still works correctly
    """
    
    def __init__(self, root_dir: str = "."):
        """
        Initialize the unified configuration system.
        
        Args:
            root_dir: Root directory of the project
        """
        self.root_dir = Path(root_dir)
        self.unifier = ConfigurationUnifier(root_dir)
        self.reference_updater = ConfigurationReferenceUpdater(root_dir)
        
    def analyze_current_state(self) -> Dict[str, Any]:
        """
        Analyze the current state of configuration directories and references.
        
        Returns:
            Dictionary containing comprehensive analysis results
        """
        logger.info("Analyzing current configuration state...")
        
        analysis = {
            "directory_analysis": {},
            "reference_analysis": {},
            "readiness_assessment": {},
            "recommendations": []
        }
        
        # Analyze directories
        try:
            directory_analysis = self.unifier.analyze_configuration_directories()
            analysis["directory_analysis"] = directory_analysis
            
            # Analyze references
            reference_analysis = self.reference_updater.search_and_replace_config_paths()
            analysis["reference_analysis"] = reference_analysis
            
            # Assess readiness for unification
            readiness = self._assess_unification_readiness(
                directory_analysis, reference_analysis
            )
            analysis["readiness_assessment"] = readiness
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                directory_analysis, reference_analysis, readiness
            )
            analysis["recommendations"] = recommendations
            
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    def execute_unification(self, dry_run: bool = True) -> UnificationResults:
        """
        Execute the complete configuration unification process.
        
        Args:
            dry_run: If True, only simulate the unification without making changes
            
        Returns:
            UnificationResults containing all operation results
        """
        logger.info(f"Executing configuration unification (dry_run={dry_run})...")
        
        errors = []
        warnings = []
        
        try:
            # Step 1: Analyze current state
            logger.info("Step 1: Analyzing current state...")
            analysis = self.analyze_current_state()
            
            if "error" in analysis:
                errors.append(f"Analysis failed: {analysis['error']}")
                return self._create_failed_results(errors)
            
            # Step 2: Execute directory merge
            logger.info("Step 2: Merging configuration directories...")
            merge_results = self.unifier.execute_merge(dry_run=dry_run)
            
            if not merge_results["success"]:
                errors.extend(merge_results["errors"])
                return self._create_failed_results(errors, merge_results)
            
            # Step 3: Update code references
            logger.info("Step 3: Updating configuration references...")
            reference_results = self.reference_updater.execute_updates(dry_run=dry_run)
            
            if not reference_results["success"]:
                errors.extend(reference_results["errors"])
                warnings.append("Reference updates failed - manual intervention may be required")
            
            # Step 4: Validate results
            logger.info("Step 4: Validating unification results...")
            if not dry_run:
                validation_results = self._validate_unification_results()
            else:
                validation_results = {"dry_run": True, "validation_skipped": True}
            
            # Create summary
            summary = self._create_summary(
                analysis, merge_results, reference_results, validation_results
            )
            
            # Determine overall success
            overall_success = (
                merge_results["success"] and 
                reference_results["success"] and
                (dry_run or validation_results.get("all_valid", False))
            )
            
            return UnificationResults(
                success=overall_success,
                directory_merge_results=merge_results,
                reference_update_results=reference_results,
                validation_results=validation_results,
                errors=errors,
                warnings=warnings,
                summary=summary
            )
            
        except Exception as e:
            error_msg = f"Unification execution failed: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            return self._create_failed_results(errors)
    
    def validate_post_unification(self) -> Dict[str, Any]:
        """
        Validate the system after unification is complete.
        
        Returns:
            Dictionary containing validation results
        """
        logger.info("Validating post-unification state...")
        
        validation = {
            "directory_structure_valid": True,
            "configuration_loading_valid": True,
            "reference_updates_complete": True,
            "no_remaining_configs_refs": True,
            "all_valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check directory structure
            config_dir = self.root_dir / "config"
            configs_dir = self.root_dir / "configs"
            
            if not config_dir.exists():
                validation["directory_structure_valid"] = False
                validation["errors"].append("config/ directory does not exist")
            
            if configs_dir.exists():
                remaining_files = list(configs_dir.rglob("*.json"))
                if remaining_files:
                    validation["warnings"].append(
                        f"configs/ directory still contains {len(remaining_files)} files"
                    )
            
            # Validate configuration loading
            config_validation = self.reference_updater.validate_configuration_loading()
            validation["configuration_loading_valid"] = config_validation["all_valid"]
            validation["errors"].extend(config_validation["errors"])
            validation["warnings"].extend(config_validation["warnings"])
            
            # Check for remaining configs/ references
            remaining_refs = self.reference_updater._find_remaining_configs_references()
            if remaining_refs:
                validation["no_remaining_configs_refs"] = False
                validation["warnings"].extend([
                    f"Remaining configs/ reference: {ref['file']}:{ref['line']}"
                    for ref in remaining_refs[:5]  # Limit to first 5
                ])
                if len(remaining_refs) > 5:
                    validation["warnings"].append(f"... and {len(remaining_refs) - 5} more")
            
            # Overall validation
            validation["all_valid"] = (
                validation["directory_structure_valid"] and
                validation["configuration_loading_valid"] and
                validation["no_remaining_configs_refs"]
            )
            
        except Exception as e:
            validation["errors"].append(f"Validation failed: {e}")
            validation["all_valid"] = False
        
        return validation
    
    def generate_unification_report(self, results: UnificationResults) -> str:
        """
        Generate a comprehensive report of the unification process.
        
        Args:
            results: UnificationResults from the unification process
            
        Returns:
            Formatted report string
        """
        report_lines = [
            "# Configuration Unification Report",
            "",
            f"**Status:** {'SUCCESS' if results.success else 'FAILED'}",
            "",
            "## Summary",
            ""
        ]
        
        # Add summary information
        summary = results.summary
        for key, value in summary.items():
            report_lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
        
        report_lines.extend(["", "## Directory Merge Results", ""])
        
        # Directory merge details
        merge_results = results.directory_merge_results
        report_lines.extend([
            f"- Operations completed: {merge_results.get('operations_completed', 0)}",
            f"- Operations failed: {merge_results.get('operations_failed', 0)}",
            f"- Backup location: {merge_results.get('backup_location', 'N/A')}"
        ])
        
        report_lines.extend(["", "## Reference Update Results", ""])
        
        # Reference update details
        ref_results = results.reference_update_results
        report_lines.extend([
            f"- Files updated: {ref_results.get('files_updated', 0)}",
            f"- References updated: {ref_results.get('references_updated', 0)}",
            f"- Backup location: {ref_results.get('backup_location', 'N/A')}"
        ])
        
        # Add errors and warnings
        if results.errors:
            report_lines.extend(["", "## Errors", ""])
            for error in results.errors:
                report_lines.append(f"- {error}")
        
        if results.warnings:
            report_lines.extend(["", "## Warnings", ""])
            for warning in results.warnings:
                report_lines.append(f"- {warning}")
        
        # Add validation results if available
        if "all_valid" in results.validation_results:
            report_lines.extend(["", "## Validation Results", ""])
            validation = results.validation_results
            report_lines.append(f"- Overall validation: {'PASSED' if validation['all_valid'] else 'FAILED'}")
            
            if validation.get("errors"):
                report_lines.append("- Validation errors:")
                for error in validation["errors"]:
                    report_lines.append(f"  - {error}")
        
        return "\n".join(report_lines)
    
    def _assess_unification_readiness(self, directory_analysis: Dict[str, Any], 
                                    reference_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess readiness for configuration unification."""
        readiness = {
            "ready": True,
            "blocking_issues": [],
            "warnings": [],
            "confidence_level": "high"
        }
        
        # Check for blocking issues
        if directory_analysis["configs_dir"]["total_files"] == 0:
            readiness["blocking_issues"].append("No files found in configs/ directory")
        
        if len(reference_analysis["errors"]) > 0:
            readiness["warnings"].append(f"{len(reference_analysis['errors'])} errors during reference analysis")
        
        # Assess confidence level
        conflicts_count = directory_analysis["statistics"]["conflicts_count"]
        if conflicts_count > 10:
            readiness["confidence_level"] = "medium"
            readiness["warnings"].append(f"High number of conflicts: {conflicts_count}")
        elif conflicts_count > 5:
            readiness["confidence_level"] = "medium"
        
        # Determine overall readiness
        readiness["ready"] = len(readiness["blocking_issues"]) == 0
        
        return readiness
    
    def _generate_recommendations(self, directory_analysis: Dict[str, Any],
                                reference_analysis: Dict[str, Any],
                                readiness: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        if not readiness["ready"]:
            recommendations.append("Resolve blocking issues before proceeding with unification")
        
        if readiness["confidence_level"] == "medium":
            recommendations.append("Consider running in dry-run mode first to preview changes")
        
        conflicts_count = directory_analysis["statistics"]["conflicts_count"]
        if conflicts_count > 0:
            recommendations.append(f"Review {conflicts_count} configuration conflicts before merging")
        
        references_count = len(reference_analysis["references_found"])
        if references_count > 20:
            recommendations.append("Large number of references to update - ensure adequate testing")
        
        if len(reference_analysis["errors"]) > 0:
            recommendations.append("Fix reference analysis errors before proceeding")
        
        return recommendations
    
    def _validate_unification_results(self) -> Dict[str, Any]:
        """Validate the results of the unification process."""
        return self.validate_post_unification()
    
    def _create_summary(self, analysis: Dict[str, Any], merge_results: Dict[str, Any],
                       reference_results: Dict[str, Any], validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the unification process."""
        return {
            "total_config_files": analysis["directory_analysis"]["statistics"]["config_files_count"],
            "total_configs_files": analysis["directory_analysis"]["statistics"]["configs_files_count"],
            "conflicts_resolved": analysis["directory_analysis"]["statistics"]["conflicts_count"],
            "merge_operations": merge_results.get("operations_completed", 0),
            "files_updated": reference_results.get("files_updated", 0),
            "references_updated": reference_results.get("references_updated", 0),
            "validation_passed": validation_results.get("all_valid", False)
        }
    
    def _create_failed_results(self, errors: List[str], 
                              partial_results: Dict[str, Any] = None) -> UnificationResults:
        """Create a failed UnificationResults object."""
        return UnificationResults(
            success=False,
            directory_merge_results=partial_results or {},
            reference_update_results={},
            validation_results={},
            errors=errors,
            warnings=[],
            summary={}
        )