#!/usr/bin/env python3

"""
Contributor Role Fixer

This module provides functionality to fix contributor role validation issues,
ensuring blank contributor names have blank roles and validating role codes.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ContributorInfo:
    """Information about a book contributor."""
    name: str
    role: str
    role_code: Optional[str] = None
    bio: Optional[str] = None
    is_primary: bool = False


class ContributorRoleFixer:
    """Fixes contributor role validation issues."""
    
    def __init__(self):
        """Initialize contributor role fixer."""
        # Valid contributor role codes according to ONIX standards
        self.valid_role_codes = {
            'A01': 'By (author)',
            'A02': 'With',
            'A03': 'Screenplay by',
            'A04': 'Libretto by',
            'A05': 'Lyrics by',
            'A06': 'By (composer)',
            'A07': 'By (artist)',
            'A08': 'By (photographer)',
            'A09': 'Created by',
            'A10': 'From an idea by',
            'A11': 'Designed by',
            'A12': 'Illustrated by',
            'A13': 'Photographs by',
            'A14': 'Text by',
            'A15': 'Preface by',
            'A16': 'Prologue by',
            'A17': 'Summary by',
            'A18': 'Supplement by',
            'A19': 'Afterword by',
            'A20': 'Notes by',
            'A21': 'Commentary by',
            'A22': 'Epilogue by',
            'A23': 'Foreword by',
            'A24': 'Introduction by',
            'A25': 'Footnotes by',
            'A26': 'Memoir by',
            'A27': 'Experiments by',
            'A99': 'Other primary creator',
            'B01': 'Edited by',
            'B02': 'Revised by',
            'B03': 'Retold by',
            'B04': 'Abridged by',
            'B05': 'Adapted by',
            'B06': 'Translated by',
            'B07': 'As told to',
            'B08': 'Interviews by',
            'B09': 'Series edited by',
            'B10': 'Edited and translated by',
            'B11': 'Editor-in-chief',
            'B12': 'Guest editor',
            'B13': 'Volume editor',
            'B14': 'Editorial board member',
            'B15': 'Editorial coordination by',
            'B16': 'Managing editor',
            'B17': 'Founded by',
            'B18': 'Prepared for publication by',
            'B19': 'Associate editor',
            'B20': 'Consultant editor',
            'B21': 'General editor',
            'B22': 'Dramatized by',
            'B23': 'General rapporteur',
            'B24': 'Literary editor',
            'B25': 'Arranged by (music)',
            'B26': 'Technical editor',
            'B27': 'Thesis advisor or supervisor',
            'B28': 'Thesis examiner',
            'B29': 'Scientific editor',
            'B99': 'Other adaptation by',
            'C01': 'Compiled by',
            'C02': 'Selected by',
            'C03': 'Non-text material selected by',
            'C04': 'Curated by',
            'C99': 'Other compilation by',
            'D01': 'Producer',
            'D02': 'Director',
            'D03': 'Conductor',
            'D99': 'Other direction by',
            'E01': 'Actor',
            'E02': 'Dancer',
            'E03': 'Narrator',
            'E04': 'Commentator',
            'E05': 'Vocal soloist',
            'E06': 'Instrumental soloist',
            'E07': 'Read by',
            'E08': 'Performed by (orchestra, band, ensemble)',
            'E09': 'Speaker',
            'E10': 'Presenter',
            'E99': 'Other performance by',
            'F01': 'Filmed/photographed by',
            'F02': 'Editor (film or video)',
            'F99': 'Other recording by',
            'Z01': 'Assisted by',
            'Z02': 'Honored/dedicated to',
            'Z03': 'Enacting jurisdiction',
            'Z04': 'Peer reviewed by',
            'Z99': 'Other'
        }
        
        # Common role name mappings
        self.role_name_mappings = {
            'author': 'A01',
            'writer': 'A01',
            'by': 'A01',
            'editor': 'B01',
            'edited by': 'B01',
            'translator': 'B06',
            'translated by': 'B06',
            'illustrator': 'A12',
            'illustrated by': 'A12',
            'photographer': 'A08',
            'photographs by': 'A13',
            'foreword': 'A23',
            'foreword by': 'A23',
            'introduction': 'A24',
            'introduction by': 'A24',
            'preface': 'A15',
            'preface by': 'A15',
            'afterword': 'A19',
            'afterword by': 'A19',
            'compiled by': 'C01',
            'compiler': 'C01',
            'selected by': 'C02',
            'narrator': 'E03',
            'read by': 'E07'
        }
    
    def fix_contributor_roles(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fix contributor role validation issues in metadata.
        
        Args:
            metadata: Dictionary containing book metadata
            
        Returns:
            Updated metadata with fixed contributor roles
        """
        # Find all contributor fields
        contributor_fields = self._find_contributor_fields(metadata)
        
        if not contributor_fields:
            logger.debug("No contributor fields found in metadata")
            return metadata
        
        # Process each contributor field group
        for field_group in contributor_fields:
            self._fix_contributor_field_group(metadata, field_group)
        
        return metadata
    
    def _find_contributor_fields(self, metadata: Dict[str, Any]) -> List[Dict[str, str]]:
        """Find all contributor field groups in metadata."""
        contributor_fields = []
        
        # Common contributor field patterns
        patterns = [
            # Primary contributors
            ('Author', 'Author Role'),
            ('author', 'author_role'),
            ('Author 1', 'Author 1 Role'),
            ('Author1', 'Author1Role'),
            
            # Secondary contributors
            ('Author 2', 'Author 2 Role'),
            ('Author2', 'Author2Role'),
            ('Author 3', 'Author 3 Role'),
            ('Author3', 'Author3Role'),
            ('Author 4', 'Author 4 Role'),
            ('Author4', 'Author4Role'),
            ('Author 5', 'Author 5 Role'),
            ('Author5', 'Author5Role'),
            
            # Other contributor types
            ('Editor', 'Editor Role'),
            ('editor', 'editor_role'),
            ('Translator', 'Translator Role'),
            ('translator', 'translator_role'),
            ('Illustrator', 'Illustrator Role'),
            ('illustrator', 'illustrator_role'),
            ('Contributor', 'Contributor Role'),
            ('contributor', 'contributor_role'),
            
            # Generic contributor fields
            ('Contributor 1', 'Contributor 1 Role'),
            ('Contributor 2', 'Contributor 2 Role'),
            ('Contributor 3', 'Contributor 3 Role'),
            ('Contributor 4', 'Contributor 4 Role'),
            ('Contributor 5', 'Contributor 5 Role'),
        ]
        
        for name_field, role_field in patterns:
            if name_field in metadata or role_field in metadata:
                contributor_fields.append({
                    'name_field': name_field,
                    'role_field': role_field
                })
        
        return contributor_fields
    
    def _fix_contributor_field_group(self, metadata: Dict[str, Any], field_group: Dict[str, str]):
        """Fix a single contributor field group."""
        name_field = field_group['name_field']
        role_field = field_group['role_field']
        
        name_value = metadata.get(name_field, '').strip()
        role_value = metadata.get(role_field, '').strip()
        
        # Rule 1: If contributor name is blank, role should be blank
        if not name_value:
            if role_value:
                logger.info(f"Clearing role for blank contributor name: {role_field} was '{role_value}'")
                metadata[role_field] = ''
            return
        
        # Rule 2: If contributor name exists but role is blank, try to infer role
        if name_value and not role_value:
            inferred_role = self._infer_contributor_role(name_field, name_value)
            if inferred_role:
                logger.info(f"Inferred role for {name_field} '{name_value}': {inferred_role}")
                metadata[role_field] = inferred_role
            else:
                # Default to 'Author' for primary contributor, 'Contributor' for others
                if 'author' in name_field.lower() or name_field.lower() in ['author', 'author 1', 'author1']:
                    metadata[role_field] = 'A01'  # By (author)
                    logger.info(f"Set default author role for {name_field}: A01")
                else:
                    metadata[role_field] = 'Z99'  # Other
                    logger.info(f"Set default contributor role for {name_field}: Z99")
        
        # Rule 3: Validate and normalize existing roles
        elif name_value and role_value:
            normalized_role = self._normalize_contributor_role(role_value)
            if normalized_role != role_value:
                logger.info(f"Normalized role for {name_field}: '{role_value}' -> '{normalized_role}'")
                metadata[role_field] = normalized_role
    
    def _infer_contributor_role(self, field_name: str, contributor_name: str) -> Optional[str]:
        """Infer contributor role based on field name and contributor name."""
        field_lower = field_name.lower()
        name_lower = contributor_name.lower()
        
        # Infer from field name
        if 'author' in field_lower:
            return 'A01'  # By (author)
        elif 'editor' in field_lower:
            return 'B01'  # Edited by
        elif 'translator' in field_lower:
            return 'B06'  # Translated by
        elif 'illustrator' in field_lower:
            return 'A12'  # Illustrated by
        elif 'photographer' in field_lower:
            return 'A08'  # By (photographer)
        
        # Infer from contributor name patterns
        if any(term in name_lower for term in ['editor', 'ed.', '(editor)', '(ed.)']):
            return 'B01'  # Edited by
        elif any(term in name_lower for term in ['translator', 'trans.', '(translator)', '(trans.)']):
            return 'B06'  # Translated by
        elif any(term in name_lower for term in ['illustrator', 'illus.', '(illustrator)', '(illus.)']):
            return 'A12'  # Illustrated by
        elif any(term in name_lower for term in ['photographer', 'photo.', '(photographer)', '(photo.)']):
            return 'A08'  # By (photographer)
        
        return None
    
    def _normalize_contributor_role(self, role_value: str) -> str:
        """Normalize contributor role to valid ONIX code."""
        role_lower = role_value.lower().strip()
        
        # If it's already a valid code, return as-is
        if role_value.upper() in self.valid_role_codes:
            return role_value.upper()
        
        # Try to map from common role names
        if role_lower in self.role_name_mappings:
            return self.role_name_mappings[role_lower]
        
        # Try partial matches
        for role_name, role_code in self.role_name_mappings.items():
            if role_name in role_lower or role_lower in role_name:
                return role_code
        
        # If no match found, return original value
        logger.warning(f"Could not normalize contributor role: '{role_value}'")
        return role_value
    
    def validate_contributor_roles(self, metadata: Dict[str, Any]) -> List[str]:
        """
        Validate contributor roles and return list of validation issues.
        
        Args:
            metadata: Dictionary containing book metadata
            
        Returns:
            List of validation issue messages
        """
        issues = []
        contributor_fields = self._find_contributor_fields(metadata)
        
        for field_group in contributor_fields:
            name_field = field_group['name_field']
            role_field = field_group['role_field']
            
            name_value = metadata.get(name_field, '').strip()
            role_value = metadata.get(role_field, '').strip()
            
            # Check for blank name with non-blank role
            if not name_value and role_value:
                issues.append(f"Contributor role '{role_field}' has value '{role_value}' but contributor name '{name_field}' is blank")
            
            # Check for non-blank name with blank role
            elif name_value and not role_value:
                issues.append(f"Contributor name '{name_field}' has value '{name_value}' but role '{role_field}' is blank")
            
            # Check for invalid role codes
            elif name_value and role_value:
                if role_value.upper() not in self.valid_role_codes and role_value.lower() not in self.role_name_mappings:
                    issues.append(f"Invalid contributor role code '{role_value}' for '{name_field}'")
        
        return issues
    
    def get_contributor_summary(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of contributors in metadata."""
        contributor_fields = self._find_contributor_fields(metadata)
        contributors = []
        
        for field_group in contributor_fields:
            name_field = field_group['name_field']
            role_field = field_group['role_field']
            
            name_value = metadata.get(name_field, '').strip()
            role_value = metadata.get(role_field, '').strip()
            
            if name_value or role_value:
                contributor = ContributorInfo(
                    name=name_value,
                    role=role_value,
                    role_code=role_value if role_value.upper() in self.valid_role_codes else None,
                    is_primary='author' in name_field.lower()
                )
                contributors.append(contributor)
        
        return {
            'total_contributors': len(contributors),
            'primary_contributors': len([c for c in contributors if c.is_primary]),
            'contributors_with_valid_roles': len([c for c in contributors if c.role_code]),
            'contributors': contributors
        }
    
    def suggest_contributor_roles(self, contributor_name: str, field_name: str = None) -> List[Tuple[str, str]]:
        """
        Suggest appropriate contributor roles for a given contributor.
        
        Args:
            contributor_name: Name of the contributor
            field_name: Optional field name for context
            
        Returns:
            List of (role_code, role_description) tuples
        """
        suggestions = []
        name_lower = contributor_name.lower()
        field_lower = field_name.lower() if field_name else ''
        
        # Primary suggestions based on field name
        if 'author' in field_lower:
            suggestions.append(('A01', 'By (author)'))
        elif 'editor' in field_lower:
            suggestions.append(('B01', 'Edited by'))
        elif 'translator' in field_lower:
            suggestions.append(('B06', 'Translated by'))
        elif 'illustrator' in field_lower:
            suggestions.append(('A12', 'Illustrated by'))
        
        # Additional suggestions based on contributor name
        if 'editor' in name_lower:
            suggestions.append(('B01', 'Edited by'))
        if 'translator' in name_lower:
            suggestions.append(('B06', 'Translated by'))
        if 'illustrator' in name_lower:
            suggestions.append(('A12', 'Illustrated by'))
        if 'photographer' in name_lower:
            suggestions.append(('A08', 'By (photographer)'))
        
        # Default suggestions if no specific matches
        if not suggestions:
            suggestions.extend([
                ('A01', 'By (author)'),
                ('B01', 'Edited by'),
                ('A12', 'Illustrated by'),
                ('Z99', 'Other')
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for code, desc in suggestions:
            if code not in seen:
                seen.add(code)
                unique_suggestions.append((code, desc))
        
        return unique_suggestions[:5]  # Return top 5 suggestions


def fix_contributor_roles_in_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to fix contributor roles in metadata.
    
    Args:
        metadata: Dictionary containing book metadata
        
    Returns:
        Updated metadata with fixed contributor roles
    """
    fixer = ContributorRoleFixer()
    return fixer.fix_contributor_roles(metadata)


def validate_contributor_roles_in_metadata(metadata: Dict[str, Any]) -> List[str]:
    """
    Convenience function to validate contributor roles in metadata.
    
    Args:
        metadata: Dictionary containing book metadata
        
    Returns:
        List of validation issue messages
    """
    fixer = ContributorRoleFixer()
    return fixer.validate_contributor_roles(metadata)