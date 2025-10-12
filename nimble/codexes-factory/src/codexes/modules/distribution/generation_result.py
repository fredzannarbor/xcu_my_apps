# src/codexes/modules/distribution/generation_result.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from ..verifiers.validation_framework import ValidationResult


@dataclass
class FieldStatistics:
    """Statistics about field population in the generated LSI CSV."""
    total_fields: int = 0
    populated_fields: int = 0
    empty_fields: int = 0
    computed_fields: int = 0
    default_fields: int = 0
    
    @property
    def population_percentage(self) -> float:
        """Calculate the percentage of populated fields."""
        if self.total_fields == 0:
            return 0.0
        return (self.populated_fields / self.total_fields) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_fields": self.total_fields,
            "populated_fields": self.populated_fields,
            "empty_fields": self.empty_fields,
            "computed_fields": self.computed_fields,
            "default_fields": self.default_fields,
            "population_percentage": self.population_percentage
        }


@dataclass
class GenerationResult:
    """
    Comprehensive result of LSI ACS generation process.
    
    Contains validation results, field statistics, timing information,
    and detailed reporting for troubleshooting and quality assurance.
    """
    success: bool
    output_path: str
    validation_result: ValidationResult
    field_statistics: FieldStatistics = field(default_factory=FieldStatistics)
    generation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    generation_duration_ms: float = 0.0
    
    # Detailed field information
    populated_fields: Dict[str, str] = field(default_factory=dict)
    empty_fields: List[str] = field(default_factory=list)
    computed_fields: Dict[str, str] = field(default_factory=dict)
    default_fields: Dict[str, str] = field(default_factory=dict)
    
    # Error and warning details
    generation_errors: List[str] = field(default_factory=list)
    generation_warnings: List[str] = field(default_factory=list)
    
    # Metadata information
    source_metadata_summary: Dict[str, Any] = field(default_factory=dict)
    
    def add_populated_field(self, field_name: str, value: str, source: str = "direct"):
        """Add a populated field to the result tracking."""
        self.populated_fields[field_name] = value
        
        if source == "computed":
            self.computed_fields[field_name] = value
        elif source == "default":
            self.default_fields[field_name] = value
    
    def add_empty_field(self, field_name: str):
        """Add an empty field to the result tracking."""
        self.empty_fields.append(field_name)
    
    def add_generation_error(self, error: str):
        """Add a generation error."""
        self.generation_errors.append(error)
    
    def add_generation_warning(self, warning: str):
        """Add a generation warning."""
        self.generation_warnings.append(warning)
    
    def update_field_statistics(self):
        """Update field statistics based on tracked fields."""
        self.field_statistics.populated_fields = len(self.populated_fields)
        self.field_statistics.empty_fields = len(self.empty_fields)
        self.field_statistics.computed_fields = len(self.computed_fields)
        self.field_statistics.default_fields = len(self.default_fields)
        self.field_statistics.total_fields = (
            self.field_statistics.populated_fields + 
            self.field_statistics.empty_fields
        )
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the generation result."""
        if not self.success:
            return f"Generation FAILED: {len(self.generation_errors)} errors"
        
        validation_summary = ""
        if self.validation_result.has_blocking_errors():
            validation_summary = f", {len(self.validation_result.errors)} validation errors"
        elif self.validation_result.warnings:
            validation_summary = f", {len(self.validation_result.warnings)} validation warnings"
        
        return (
            f"Generation SUCCESS: {self.field_statistics.populated_fields}/"
            f"{self.field_statistics.total_fields} fields populated "
            f"({self.field_statistics.population_percentage:.1f}%)"
            f"{validation_summary}"
        )
    
    def get_detailed_report(self) -> str:
        """Get a detailed report of the generation process."""
        lines = [
            "=" * 60,
            "LSI ACS GENERATION REPORT",
            "=" * 60,
            f"Status: {'SUCCESS' if self.success else 'FAILED'}",
            f"Output File: {self.output_path}",
            f"Generated: {self.generation_timestamp}",
            f"Duration: {self.generation_duration_ms:.2f}ms",
            "",
            "FIELD STATISTICS:",
            f"  Total Fields: {self.field_statistics.total_fields}",
            f"  Populated: {self.field_statistics.populated_fields} ({self.field_statistics.population_percentage:.1f}%)",
            f"  Empty: {self.field_statistics.empty_fields}",
            f"  Computed: {self.field_statistics.computed_fields}",
            f"  Default Values: {self.field_statistics.default_fields}",
            "",
        ]
        
        # Validation results
        if self.validation_result:
            lines.extend([
                "VALIDATION RESULTS:",
                f"  Valid: {'YES' if self.validation_result.is_valid else 'NO'}",
                f"  Errors: {len(self.validation_result.errors)}",
                f"  Warnings: {len(self.validation_result.warnings)}",
            ])
            
            if self.validation_result.errors:
                lines.append("  Error Details:")
                for error in self.validation_result.errors[:5]:  # Show first 5 errors
                    lines.append(f"    - {error}")
                if len(self.validation_result.errors) > 5:
                    lines.append(f"    ... and {len(self.validation_result.errors) - 5} more")
            
            if self.validation_result.warnings:
                lines.append("  Warning Details:")
                for warning in self.validation_result.warnings[:3]:  # Show first 3 warnings
                    lines.append(f"    - {warning}")
                if len(self.validation_result.warnings) > 3:
                    lines.append(f"    ... and {len(self.validation_result.warnings) - 3} more")
            
            lines.append("")
        
        # Generation errors and warnings
        if self.generation_errors:
            lines.extend([
                "GENERATION ERRORS:",
                *[f"  - {error}" for error in self.generation_errors],
                ""
            ])
        
        if self.generation_warnings:
            lines.extend([
                "GENERATION WARNINGS:",
                *[f"  - {warning}" for warning in self.generation_warnings],
                ""
            ])
        
        # Sample of populated fields
        if self.populated_fields:
            lines.extend([
                "SAMPLE POPULATED FIELDS:",
                *[f"  {field}: {value[:50]}{'...' if len(value) > 50 else ''}" 
                  for field, value in list(self.populated_fields.items())[:10]],
                ""
            ])
        
        # Empty fields (if not too many)
        if self.empty_fields and len(self.empty_fields) <= 20:
            lines.extend([
                "EMPTY FIELDS:",
                *[f"  - {field}" for field in self.empty_fields],
                ""
            ])
        elif self.empty_fields:
            lines.extend([
                f"EMPTY FIELDS ({len(self.empty_fields)} total):",
                *[f"  - {field}" for field in self.empty_fields[:10]],
                f"  ... and {len(self.empty_fields) - 10} more",
                ""
            ])
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary for serialization."""
        return {
            "success": self.success,
            "output_path": self.output_path,
            "generation_timestamp": self.generation_timestamp,
            "generation_duration_ms": self.generation_duration_ms,
            "field_statistics": self.field_statistics.to_dict(),
            "validation_summary": {
                "is_valid": self.validation_result.is_valid if self.validation_result else True,
                "error_count": len(self.validation_result.errors) if self.validation_result else 0,
                "warning_count": len(self.validation_result.warnings) if self.validation_result else 0,
            },
            "populated_fields_count": len(self.populated_fields),
            "empty_fields_count": len(self.empty_fields),
            "computed_fields_count": len(self.computed_fields),
            "default_fields_count": len(self.default_fields),
            "generation_errors_count": len(self.generation_errors),
            "generation_warnings_count": len(self.generation_warnings),
            "summary": self.get_summary()
        }
    
    def save_report(self, report_path: str):
        """Save the detailed report to a file."""
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self.get_detailed_report())


class GenerationReporter:
    """
    Helper class for tracking and reporting generation progress.
    """
    
    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.result: Optional[GenerationResult] = None
    
    def start_generation(self, output_path: str) -> GenerationResult:
        """Start tracking a new generation process."""
        self.start_time = datetime.now()
        self.result = GenerationResult(
            success=False,  # Will be updated on completion
            output_path=output_path,
            validation_result=None,  # Will be set later
            generation_timestamp=self.start_time.isoformat()
        )
        return self.result
    
    def complete_generation(self, success: bool, validation_result: ValidationResult = None):
        """Complete the generation tracking."""
        if not self.result or not self.start_time:
            raise ValueError("Generation tracking not started")
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds() * 1000
        
        self.result.success = success
        self.result.generation_duration_ms = duration
        if validation_result:
            self.result.validation_result = validation_result
        
        # Update field statistics
        self.result.update_field_statistics()
    
    def track_field_mapping(self, field_name: str, value: str, mapping_type: str = "direct"):
        """Track a field mapping during generation."""
        if not self.result:
            return
        
        if value and str(value).strip():
            self.result.add_populated_field(field_name, str(value), mapping_type)
        else:
            self.result.add_empty_field(field_name)
    
    def add_error(self, error: str):
        """Add an error to the generation result."""
        if self.result:
            self.result.add_generation_error(error)
    
    def add_warning(self, warning: str):
        """Add a warning to the generation result."""
        if self.result:
            self.result.add_generation_warning(warning)
    
    def get_result(self) -> Optional[GenerationResult]:
        """Get the current generation result."""
        return self.result