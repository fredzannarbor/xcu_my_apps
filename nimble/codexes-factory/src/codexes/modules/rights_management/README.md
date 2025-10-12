# Rights Management Module

A comprehensive AI-assisted rights management system for international publishing rights tracking, contract management, and automated offering sheet generation.

## Overview

The Rights Management Module provides a complete solution for publishers to track, manage, and market international rights for their catalog. Built with modern publishing workflows in mind, it combines database-driven rights tracking with automated document generation for professional rights marketing.

## Key Features

### 📊 **Database Management**
- SQLite-based rights tracking with normalized schema
- Territory, language, and publisher relationship management
- Contract lifecycle tracking with begin/end dates
- Rights offering campaign management

### 🎯 **Intelligent Filtering**
- ISBN-based catalog filtering for targeted campaigns
- Territory-specific rights availability
- Language and format filtering
- Custom offering parameters

### 📄 **Professional Document Generation**
- LaTeX-based PDF generation for rights offering sheets
- Multiple format options (imprint-wide, work-specific)
- Professional typography with brand-consistent styling
- Longtable support for multi-page catalogs

### 🌐 **Web Interface**
- Streamlit-based CRUD interface
- Analytics dashboard with revenue tracking
- Import/export functionality for existing data
- Real-time rights availability checking

### 🔗 **Integration Points**
- Seamless integration with imprint creation workflows
- Book pipeline import from publishing schedules
- Distribution system export capabilities
- API-ready architecture for external integrations

## Quick Start

### Installation

```bash
# Install as part of the codexes-factory package
pip install -e .

# Or install dependencies directly
pip install streamlit pandas sqlite3 pathlib jinja2
```

### Basic Usage

```python
from codexes.modules.rights_management import (
    generate_imprint_rights_sheet,
    RightsManager,
    RightsDatabase
)

# Generate a complete imprint rights offering sheet
result = generate_imprint_rights_sheet(
    imprint_config_path="configs/imprints/my_imprint.json",
    output_dir="output/rights_offerings"
)

# Generate with ISBN filtering for targeted campaigns
result = generate_imprint_rights_sheet(
    imprint_config_path="configs/imprints/my_imprint.json",
    output_dir="output/rights_offerings",
    isbn_filter="9781234567890,9781234567891"
)
```

### Command Line Interface

```bash
# Generate full catalog rights offering
python generate_longtable_catalog.py

# Generate targeted rights offering with ISBN filter
python generate_isbn_filtered_rights.py \
    --config configs/imprints/xynapse_traces.json \
    --output-dir output/rights_offerings \
    --isbn-filter "9781608883646,9781608883653"

# Run demo with sample data
python demo_isbn_filtering.py
```

## Architecture

```
rights_management/
├── __init__.py              # Module exports
├── database.py              # Core SQLite database operations
├── crud_operations.py       # High-level business logic
├── offering_sheet_generator.py  # LaTeX document generation
├── README.md               # This file
├── USAGE_GUIDE.md          # Detailed usage documentation
└── docs/
    └── rights_management_ai_survey.pdf  # Academic paper
```

### Core Components

#### 1. **RightsDatabase** (`database.py`)
- SQLite schema with 5 core tables
- Foreign key relationships for data integrity
- Comprehensive CRUD operations
- Territory and language management

#### 2. **RightsManager** (`crud_operations.py`)
- High-level business logic abstraction
- CSV import functionality for existing data
- Contract lifecycle management
- Rights availability calculations

#### 3. **RightsOfferingSheetGenerator** (`offering_sheet_generator.py`)
- Professional LaTeX document generation
- Configurable templates and styling
- Multi-format support (imprint, work-specific)
- ISBN filtering and catalog customization

## Database Schema

```sql
-- Core entities
CREATE TABLE works (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    author_name TEXT,
    isbn TEXT UNIQUE,
    publication_date TEXT,
    imprint TEXT,
    page_count INTEGER
);

CREATE TABLE publishers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    country TEXT,
    contact_email TEXT,
    website TEXT
);

CREATE TABLE territories (
    id INTEGER PRIMARY KEY,
    territory_name TEXT NOT NULL UNIQUE,
    primary_language TEXT,
    currency TEXT
);

-- Relationships
CREATE TABLE rights_contracts (
    id INTEGER PRIMARY KEY,
    work_id INTEGER,
    publisher_id INTEGER,
    territory_id INTEGER,
    language TEXT,
    contract_begin_date TEXT,
    contract_end_date TEXT,
    advance_amount REAL,
    royalty_rate REAL,
    FOREIGN KEY (work_id) REFERENCES works (id),
    FOREIGN KEY (publisher_id) REFERENCES publishers (id),
    FOREIGN KEY (territory_id) REFERENCES territories (id)
);

CREATE TABLE rights_offerings (
    id INTEGER PRIMARY KEY,
    work_id INTEGER,
    territory_ids TEXT,
    offering_date TEXT,
    asking_price REAL,
    notes TEXT,
    FOREIGN KEY (work_id) REFERENCES works (id)
);
```

## Document Generation

The module generates professional rights offering sheets in multiple formats:

### Imprint-Wide Offerings
- Complete catalog overview with publishing philosophy
- Featured title with detailed description and cover image
- Professional longtable catalog with pagination
- ISBN filtering for targeted campaigns

### Work-Specific Offerings
- Individual title focus with comprehensive details
- Territory availability matrix
- Contract terms and pricing information
- Rights history and availability

### Output Features
- **LaTeX/PDF Generation**: Professional typography with brand fonts
- **Responsive Tables**: Longtable support for large catalogs
- **Visual Elements**: Cover thumbnails and branded headers
- **Multi-page Support**: Automatic pagination with headers/footers

## Integration Examples

### Imprint Creation Workflow
```python
# Automatic rights offering generation during imprint setup
from codexes.modules.imprints.pipeline_generator import generate_imprint

# Rights offering sheet is automatically generated if enabled
generate_imprint(
    config_path="configs/imprints/new_imprint.json",
    enable_rights_offering=True
)
```

### Book Pipeline Integration
```python
# Import works from publishing schedule
rights_manager = RightsManager()
works_imported = rights_manager.import_from_schedule(
    "imprints/my_imprint/schedule.csv"
)
```

### Streamlit Dashboard
```bash
# Launch web interface
streamlit run src/codexes/pages/25_Rights_Management.py
```

## Configuration

### Imprint Configuration
Rights offering sheets use imprint configuration files:

```json
{
  "imprint": "Xynapse Traces",
  "publisher": "Nimble Books LLC",
  "contact_email": "rights@example.com",
  "branding": {
    "primary_color": "#2C3E50",
    "secondary_color": "#E74C3C",
    "tagline": "Tracing the Future of Knowledge"
  },
  "publishing_focus": {
    "primary_genres": ["Technology", "Science"],
    "target_audience": "Academic and Professional",
    "specialization": "Cutting-edge research"
  }
}
```

### LaTeX Styling
- Brand-consistent fonts and colors
- Professional document structure
- Configurable layout parameters
- Responsive table formatting

## Advanced Features

### ISBN Filtering
Target specific titles for focused rights campaigns:

```python
# Multiple ISBNs
generate_imprint_rights_sheet(
    imprint_config_path="config.json",
    output_dir="output/",
    isbn_filter="9781234567890,9781234567891,9781234567892"
)

# Single ISBN
generate_imprint_rights_sheet(
    imprint_config_path="config.json",
    output_dir="output/",
    isbn_filter="9781234567890"
)
```

### Analytics and Reporting
- Territory-based revenue analysis
- Rights utilization metrics
- Contract expiration tracking
- Market penetration reports

### Data Import/Export
- CSV import for existing rights data
- Bulk territory and publisher setup
- Export capabilities for reporting
- Integration with distribution systems

## Dependencies

- **Core**: Python 3.8+, SQLite3, Pandas
- **Document Generation**: LaTeX, PyPDF2
- **Web Interface**: Streamlit
- **Data Processing**: JSON, CSV modules
- **Integration**: Pathlib, logging

## Contributing

1. Follow the existing code structure and patterns
2. Add comprehensive tests for new functionality
3. Update documentation for API changes
4. Ensure LaTeX templates remain professionally formatted

## License

This module is part of the Codexes Factory platform. See the main project license for details.

## Support

- **Documentation**: See `USAGE_GUIDE.md` for detailed usage examples
- **Academic Context**: See `docs/rights_management_ai_survey.pdf` for research background
- **Issues**: Report bugs and feature requests through the main project repository
- **Integration**: Contact the development team for custom integration needs

---

*The Rights Management Module represents a significant advancement in automated rights management for international publishing, combining traditional publishing workflows with modern AI-assisted automation and professional document generation.*