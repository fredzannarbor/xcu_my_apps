#!/usr/bin/env python3
"""
Rights Management Module

Comprehensive rights management system for tracking international rights sales,
contracts, territories, and generating professional offering sheets.

Main Components:
- Database: SQLite-based rights tracking
- CRUD Operations: High-level business logic
- Offering Sheet Generator: PDF generation for rights marketing
- Streamlit UI: Web interface for rights management

Integration Points:
- Imprint Creation: Auto-generate rights offering sheets for new imprints
- Book Pipeline: Import works from publishing schedules
- Distribution: Export rights data for reporting
"""

from .database import RightsDatabase, get_rights_database
from .crud_operations import RightsManager, get_rights_manager
from .offering_sheet_generator import (
    RightsOfferingSheetGenerator,
    generate_imprint_rights_sheet,
    generate_work_rights_sheet
)

__all__ = [
    'RightsDatabase',
    'get_rights_database',
    'RightsManager',
    'get_rights_manager',
    'RightsOfferingSheetGenerator',
    'generate_imprint_rights_sheet',
    'generate_work_rights_sheet'
]