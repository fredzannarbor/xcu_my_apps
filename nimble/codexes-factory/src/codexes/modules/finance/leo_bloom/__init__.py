"""
Leo Bloom - Financial reporting module for book publishers.

Named after the character from "The Producers", this module provides comprehensive
financial analysis and reporting capabilities for publishing companies.

Main components:
- FinancialReportingObjects: Core financial analysis classes
- ui: Streamlit user interface components
- utilities: Helper functions and tools
"""

# Import main UI components
try:
    from . import ui
except ImportError:
    # Handle cases where streamlit dependencies might not be available
    ui = None

# Import Financial Reporting Objects
try:
    from .FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects
except ImportError:
    FinancialReportingObjects = None

# Import utilities
try:
    from . import utilities
except ImportError:
    utilities = None

__all__ = [
    "FinancialReportingObjects",
    "ui",
    "utilities"
]