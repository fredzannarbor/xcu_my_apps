#!/usr/bin/env python3

"""
Reserved Fields Manager

This module manages reserved and unused fields in LSI CSV files,
ensuring they are consistently blank and preventing accidental population.
"""

import logging
from typing import Dict, List, Any, Set, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ReservedFieldInfo:
    """Information about a reserved field."""
    field_name: str
    reason: str
    category: str
    should_be_blank: bool = True
    notes: Optional[str] = None


class ReservedFieldsManager:
    """Manages reserved and unused fields in LSI CSV data."""
    
    def __init__(self):
        """Initialize reserved fields manager."""
        # Define reserved fields that should always be blank
        self.reserved_fields = self._initialize_reserved_fields()
        
        # Define deprecated fields that are no longer used
        self.deprecated_fields = self._initialize_deprecated_fields()
        
        # Define internal/system fields that should not be populated
        self.internal_fields = self._initialize_internal_fields()
        
        # Combine all fields that should be blank
        self.all_blank_fields = set()
        self.all_blank_fields.update(self.reserved_fields.keys())
        self.all_blank_fields.update(self.deprecated_fields.keys())
        self.all_blank_fields.update(self.internal_fields.keys())
    
    def _initialize_reserved_fields(self) -> Dict[str, ReservedFieldInfo]:
        """Initialize reserved fields that should always be blank."""
        return {
            # LSI system reserved fields
            'Reserved 1': ReservedFieldInfo(
                field_name='Reserved 1',
                reason='System reserved field',
                category='system_reserved',
                notes='Reserved for future LSI system use'
            ),
            'Reserved 2': ReservedFieldInfo(
                field_name='Reserved 2',
                reason='System reserved field',
                category='system_reserved',
                notes='Reserved for future LSI system use'
            ),
            'Reserved 3': ReservedFieldInfo(
                field_name='Reserved 3',
                reason='System reserved field',
                category='system_reserved',
                notes='Reserved for future LSI system use'
            ),
            'Reserved 4': ReservedFieldInfo(
                field_name='Reserved 4',
                reason='System reserved field',
                category='system_reserved',
                notes='Reserved for future LSI system use'
            ),
            'Reserved 5': ReservedFieldInfo(
                field_name='Reserved 5',
                reason='System reserved field',
                category='system_reserved',
                notes='Reserved for future LSI system use'
            ),
            
            # Future expansion fields
            'Future Use 1': ReservedFieldInfo(
                field_name='Future Use 1',
                reason='Reserved for future expansion',
                category='future_expansion',
                notes='Field reserved for future feature expansion'
            ),
            'Future Use 2': ReservedFieldInfo(
                field_name='Future Use 2',
                reason='Reserved for future expansion',
                category='future_expansion',
                notes='Field reserved for future feature expansion'
            ),
            'Future Use 3': ReservedFieldInfo(
                field_name='Future Use 3',
                reason='Reserved for future expansion',
                category='future_expansion',
                notes='Field reserved for future feature expansion'
            ),
            
            # Placeholder fields
            'Placeholder 1': ReservedFieldInfo(
                field_name='Placeholder 1',
                reason='Placeholder field',
                category='placeholder',
                notes='Placeholder field - should remain blank'
            ),
            'Placeholder 2': ReservedFieldInfo(
                field_name='Placeholder 2',
                reason='Placeholder field',
                category='placeholder',
                notes='Placeholder field - should remain blank'
            ),
            
            # System processing fields
            'System Processing Flag': ReservedFieldInfo(
                field_name='System Processing Flag',
                reason='Internal system use',
                category='system_processing',
                notes='Used internally by LSI processing system'
            ),
            'Batch Processing ID': ReservedFieldInfo(
                field_name='Batch Processing ID',
                reason='Internal system use',
                category='system_processing',
                notes='Used internally for batch processing tracking'
            ),
            'Processing Status': ReservedFieldInfo(
                field_name='Processing Status',
                reason='Internal system use',
                category='system_processing',
                notes='Used internally to track processing status'
            ),
            
            # Legacy compatibility fields
            'Legacy Field 1': ReservedFieldInfo(
                field_name='Legacy Field 1',
                reason='Legacy compatibility',
                category='legacy',
                notes='Maintained for legacy system compatibility'
            ),
            'Legacy Field 2': ReservedFieldInfo(
                field_name='Legacy Field 2',
                reason='Legacy compatibility',
                category='legacy',
                notes='Maintained for legacy system compatibility'
            ),
        }
    
    def _initialize_deprecated_fields(self) -> Dict[str, ReservedFieldInfo]:
        """Initialize deprecated fields that are no longer used."""
        return {
            # Old format fields
            'Old Format Price': ReservedFieldInfo(
                field_name='Old Format Price',
                reason='Deprecated pricing format',
                category='deprecated',
                notes='Replaced by new pricing fields'
            ),
            'Legacy ISBN Format': ReservedFieldInfo(
                field_name='Legacy ISBN Format',
                reason='Deprecated ISBN format',
                category='deprecated',
                notes='Replaced by standard ISBN field'
            ),
            'Old Category System': ReservedFieldInfo(
                field_name='Old Category System',
                reason='Deprecated categorization',
                category='deprecated',
                notes='Replaced by BISAC categories'
            ),
            
            # Discontinued features
            'Discontinued Feature 1': ReservedFieldInfo(
                field_name='Discontinued Feature 1',
                reason='Feature discontinued',
                category='discontinued',
                notes='Feature no longer supported by LSI'
            ),
            'Discontinued Feature 2': ReservedFieldInfo(
                field_name='Discontinued Feature 2',
                reason='Feature discontinued',
                category='discontinued',
                notes='Feature no longer supported by LSI'
            ),
            
            # Old territorial fields
            'Old Territory Code': ReservedFieldInfo(
                field_name='Old Territory Code',
                reason='Deprecated territory system',
                category='deprecated',
                notes='Replaced by new territorial pricing system'
            ),
            'Legacy Distribution': ReservedFieldInfo(
                field_name='Legacy Distribution',
                reason='Deprecated distribution system',
                category='deprecated',
                notes='Replaced by new distribution channels'
            ),
        }
    
    def _initialize_internal_fields(self) -> Dict[str, ReservedFieldInfo]:
        """Initialize internal/system fields that should not be populated."""
        return {
            # Debug and testing fields
            'Debug Flag': ReservedFieldInfo(
                field_name='Debug Flag',
                reason='Internal debugging',
                category='internal',
                notes='Used only for internal debugging'
            ),
            'Test Mode': ReservedFieldInfo(
                field_name='Test Mode',
                reason='Internal testing',
                category='internal',
                notes='Used only for internal testing'
            ),
            'Development Notes': ReservedFieldInfo(
                field_name='Development Notes',
                reason='Internal development',
                category='internal',
                notes='Used only during development'
            ),
            
            # System metadata
            'System Version': ReservedFieldInfo(
                field_name='System Version',
                reason='Internal system metadata',
                category='internal',
                notes='Populated automatically by system'
            ),
            'Generation Timestamp': ReservedFieldInfo(
                field_name='Generation Timestamp',
                reason='Internal system metadata',
                category='internal',
                notes='Populated automatically by system'
            ),
            'Processing Log': ReservedFieldInfo(
                field_name='Processing Log',
                reason='Internal system metadata',
                category='internal',
                notes='Used for internal processing logs'
            ),
            
            # Validation fields
            'Validation Status': ReservedFieldInfo(
                field_name='Validation Status',
                reason='Internal validation',
                category='internal',
                notes='Used internally for validation tracking'
            ),
            'Validation Errors': ReservedFieldInfo(
                field_name='Validation Errors',
                reason='Internal validation',
                category='internal',
                notes='Used internally for validation error tracking'
            ),
        }
    
    def ensure_reserved_fields_blank(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure all reserved fields are blank in metadata.
        
        Args:
            metadata: Dictionary containing book metadata
            
        Returns:
            Updated metadata with reserved fields set to blank
        """
        changes_made = []
        
        for field_name in self.all_blank_fields:
            if field_name in metadata:
                current_value = metadata[field_name]
                
                # Check if field has a non-blank value
                if current_value and str(current_value).strip():
                    # Clear the field
                    metadata[field_name] = ''
                    changes_made.append(f"Cleared reserved field '{field_name}': was '{current_value}'")
                    
                    # Log the change
                    field_info = self._get_field_info(field_name)
                    logger.info(
                        f"Cleared reserved field '{field_name}' (reason: {field_info.reason}): "
                        f"was '{current_value}'"
                    )
        
        # Log summary of changes
        if changes_made:
            logger.info(f"Cleared {len(changes_made)} reserved fields")
        
        return metadata
    
    def validate_reserved_fields(self, metadata: Dict[str, Any]) -> List[str]:
        """
        Validate that reserved fields are blank.
        
        Args:
            metadata: Dictionary containing book metadata
            
        Returns:
            List of validation issues
        """
        issues = []
        
        for field_name in self.all_blank_fields:
            if field_name in metadata:
                current_value = metadata[field_name]
                
                # Check if field has a non-blank value
                if current_value and str(current_value).strip():
                    field_info = self._get_field_info(field_name)
                    issues.append(
                        f"Reserved field '{field_name}' should be blank but contains: '{current_value}' "
                        f"(reason: {field_info.reason})"
                    )
        
        return issues
    
    def _get_field_info(self, field_name: str) -> ReservedFieldInfo:
        """Get information about a reserved field."""
        if field_name in self.reserved_fields:
            return self.reserved_fields[field_name]
        elif field_name in self.deprecated_fields:
            return self.deprecated_fields[field_name]
        elif field_name in self.internal_fields:
            return self.internal_fields[field_name]
        else:
            # Return default info for unknown fields
            return ReservedFieldInfo(
                field_name=field_name,
                reason='Unknown reserved field',
                category='unknown',
                notes='Field should be blank but reason unknown'
            )
    
    def get_reserved_fields_summary(self) -> Dict[str, Any]:
        """Get summary of all reserved fields."""
        summary = {
            'total_reserved_fields': len(self.all_blank_fields),
            'categories': {},
            'fields_by_category': {}
        }
        
        # Count fields by category
        all_fields = {}
        all_fields.update(self.reserved_fields)
        all_fields.update(self.deprecated_fields)
        all_fields.update(self.internal_fields)
        
        for field_info in all_fields.values():
            category = field_info.category
            if category not in summary['categories']:
                summary['categories'][category] = 0
                summary['fields_by_category'][category] = []
            
            summary['categories'][category] += 1
            summary['fields_by_category'][category].append(field_info.field_name)
        
        return summary
    
    def is_reserved_field(self, field_name: str) -> bool:
        """Check if a field is reserved and should be blank."""
        return field_name in self.all_blank_fields
    
    def get_field_category(self, field_name: str) -> Optional[str]:
        """Get the category of a reserved field."""
        field_info = self._get_field_info(field_name)
        return field_info.category if field_info else None
    
    def add_custom_reserved_field(self, field_name: str, reason: str, 
                                category: str = 'custom', notes: str = None):
        """
        Add a custom reserved field.
        
        Args:
            field_name: Name of the field to reserve
            reason: Reason why the field should be blank
            category: Category of the reserved field
            notes: Optional additional notes
        """
        field_info = ReservedFieldInfo(
            field_name=field_name,
            reason=reason,
            category=category,
            notes=notes
        )
        
        self.reserved_fields[field_name] = field_info
        self.all_blank_fields.add(field_name)
        
        logger.info(f"Added custom reserved field: {field_name} (reason: {reason})")
    
    def remove_reserved_field(self, field_name: str):
        """
        Remove a field from the reserved fields list.
        
        Args:
            field_name: Name of the field to remove from reserved list
        """
        removed = False
        
        if field_name in self.reserved_fields:
            del self.reserved_fields[field_name]
            removed = True
        
        if field_name in self.deprecated_fields:
            del self.deprecated_fields[field_name]
            removed = True
        
        if field_name in self.internal_fields:
            del self.internal_fields[field_name]
            removed = True
        
        if field_name in self.all_blank_fields:
            self.all_blank_fields.remove(field_name)
            removed = True
        
        if removed:
            logger.info(f"Removed field from reserved list: {field_name}")
        else:
            logger.warning(f"Field not found in reserved list: {field_name}")
    
    def generate_reserved_fields_documentation(self) -> str:
        """Generate documentation for reserved fields."""
        lines = []
        lines.append("# Reserved Fields Documentation")
        lines.append("")
        lines.append("This document lists all fields that should remain blank in LSI CSV files.")
        lines.append("")
        
        # Group by category
        all_fields = {}
        all_fields.update(self.reserved_fields)
        all_fields.update(self.deprecated_fields)
        all_fields.update(self.internal_fields)
        
        categories = {}
        for field_info in all_fields.values():
            category = field_info.category
            if category not in categories:
                categories[category] = []
            categories[category].append(field_info)
        
        # Generate documentation for each category
        for category, fields in sorted(categories.items()):
            lines.append(f"## {category.replace('_', ' ').title()} Fields")
            lines.append("")
            
            for field_info in sorted(fields, key=lambda x: x.field_name):
                lines.append(f"### {field_info.field_name}")
                lines.append(f"- **Reason**: {field_info.reason}")
                if field_info.notes:
                    lines.append(f"- **Notes**: {field_info.notes}")
                lines.append("")
        
        lines.append("## Summary")
        lines.append(f"Total reserved fields: {len(self.all_blank_fields)}")
        lines.append("")
        lines.append("### Fields by Category")
        for category, count in sorted(self.get_reserved_fields_summary()['categories'].items()):
            lines.append(f"- {category.replace('_', ' ').title()}: {count} fields")
        
        return "\\n".join(lines)
    
    def check_for_accidental_population(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for accidental population of reserved fields and suggest fixes.
        
        Args:
            metadata: Dictionary containing book metadata
            
        Returns:
            Dictionary with analysis results and suggestions
        """
        analysis = {
            'populated_reserved_fields': [],
            'severity_levels': {'high': [], 'medium': [], 'low': []},
            'suggestions': [],
            'auto_fix_available': True
        }
        
        for field_name in self.all_blank_fields:
            if field_name in metadata:
                current_value = metadata[field_name]
                
                if current_value and str(current_value).strip():
                    field_info = self._get_field_info(field_name)
                    
                    populated_field = {
                        'field_name': field_name,
                        'current_value': current_value,
                        'reason': field_info.reason,
                        'category': field_info.category
                    }
                    
                    analysis['populated_reserved_fields'].append(populated_field)
                    
                    # Determine severity based on category
                    if field_info.category in ['system_reserved', 'system_processing']:
                        analysis['severity_levels']['high'].append(populated_field)
                    elif field_info.category in ['deprecated', 'discontinued']:
                        analysis['severity_levels']['medium'].append(populated_field)
                    else:
                        analysis['severity_levels']['low'].append(populated_field)
        
        # Generate suggestions
        if analysis['populated_reserved_fields']:
            analysis['suggestions'].append(
                f"Found {len(analysis['populated_reserved_fields'])} reserved fields with values - "
                "these should be cleared to blank"
            )
            
            if analysis['severity_levels']['high']:
                analysis['suggestions'].append(
                    f"HIGH PRIORITY: {len(analysis['severity_levels']['high'])} system reserved fields "
                    "are populated - this may cause processing errors"
                )
            
            if analysis['severity_levels']['medium']:
                analysis['suggestions'].append(
                    f"MEDIUM PRIORITY: {len(analysis['severity_levels']['medium'])} deprecated fields "
                    "are populated - these should be migrated to current fields"
                )
            
            analysis['suggestions'].append(
                "Use ensure_reserved_fields_blank() to automatically fix these issues"
            )
        
        return analysis


def ensure_reserved_fields_blank(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to ensure reserved fields are blank.
    
    Args:
        metadata: Dictionary containing book metadata
        
    Returns:
        Updated metadata with reserved fields cleared
    """
    manager = ReservedFieldsManager()
    return manager.ensure_reserved_fields_blank(metadata)


def validate_reserved_fields(metadata: Dict[str, Any]) -> List[str]:
    """
    Convenience function to validate reserved fields.
    
    Args:
        metadata: Dictionary containing book metadata
        
    Returns:
        List of validation issues
    """
    manager = ReservedFieldsManager()
    return manager.validate_reserved_fields(metadata)


def is_reserved_field(field_name: str) -> bool:
    """
    Convenience function to check if a field is reserved.
    
    Args:
        field_name: Name of the field to check
        
    Returns:
        True if the field is reserved and should be blank
    """
    manager = ReservedFieldsManager()
    return manager.is_reserved_field(field_name)