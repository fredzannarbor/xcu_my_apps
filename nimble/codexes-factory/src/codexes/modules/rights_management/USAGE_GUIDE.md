# Rights Management Module - Usage Guide

This comprehensive guide provides detailed instructions for using the Rights Management Module effectively in your publishing workflow.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Database Setup](#database-setup)
3. [Core Operations](#core-operations)
4. [Document Generation](#document-generation)
5. [Web Interface](#web-interface)
6. [Advanced Features](#advanced-features)
7. [Integration Patterns](#integration-patterns)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## Getting Started

### Prerequisites

- Python 3.8 or higher
- SQLite3 (included with Python)
- LaTeX installation for PDF generation
- Streamlit for web interface

### Initial Setup

1. **Import the module**:
```python
from codexes.modules.rights_management import (
    RightsDatabase,
    RightsManager,
    generate_imprint_rights_sheet,
    generate_work_rights_sheet
)
```

2. **Initialize the database**:
```python
# Initialize with default database location
rights_manager = RightsManager()

# Or specify custom database path
rights_manager = RightsManager(db_path="custom/path/rights.db")
```

3. **Verify installation**:
```python
# Check database connection
db = rights_manager.db
tables = db.get_table_info()
print(f"Database initialized with {len(tables)} tables")
```

## Database Setup

### Core Entities

#### 1. Works Management

```python
# Add a new work
work_data = {
    'title': 'Advanced AI Techniques',
    'author_name': 'Dr. Jane Smith',
    'isbn': '9781234567890',
    'publication_date': '2025-01-15',
    'imprint': 'Tech Publishers',
    'page_count': 320,
    'description': 'Comprehensive guide to modern AI methods'
}
work_id = rights_manager.add_work(work_data)
```

#### 2. Publisher Database

```python
# Add publishers
publisher_data = {
    'name': 'European Academic Press',
    'country': 'Germany',
    'contact_email': 'rights@europeanacademic.de',
    'website': 'www.europeanacademic.com'
}
publisher_id = rights_manager.add_publisher(publisher_data)
```

#### 3. Territory Configuration

```python
# Add territories
territory_data = {
    'territory_name': 'German-speaking Europe',
    'primary_language': 'German',
    'currency': 'EUR'
}
territory_id = rights_manager.add_territory(territory_data)
```

### Bulk Data Import

#### From CSV Files

```python
# Import works from schedule CSV
works_imported = rights_manager.import_from_schedule(
    schedule_path="imprints/my_imprint/schedule.csv"
)
print(f"Imported {works_imported} works")

# Import existing rights data
rights_imported = rights_manager.import_existing_rights_data(
    csv_path="data/existing_rights.csv"
)
print(f"Imported {rights_imported} rights contracts")
```

#### Sample CSV Format

**schedule.csv**:
```csv
title,author,isbn,publication_date,imprint,page_count,description
"AI in Publishing","Dr. Smith","9781234567890","2025-01-15","Tech Books",320,"Comprehensive AI guide"
"Future of Rights","J. Doe","9781234567891","2025-02-20","Tech Books",280,"Rights management evolution"
```

**existing_rights.csv**:
```csv
work_title,publisher_name,territory,language,contract_begin,contract_end,advance,royalty_rate
"AI in Publishing","European Press","Germany","German","2025-01-01","2032-01-01",5000,0.08
"Future of Rights","Asian Publishers","Japan","Japanese","2025-02-01","2032-02-01",3000,0.10
```

## Core Operations

### Rights Contract Management

#### Creating Rights Contracts

```python
# Complete contract creation
contract_data = {
    'work_id': work_id,
    'publisher_id': publisher_id,
    'territory_id': territory_id,
    'language': 'German',
    'contract_begin_date': '2025-01-01',
    'contract_end_date': '2032-01-01',
    'advance_amount': 5000.0,
    'royalty_rate': 0.08,
    'notes': 'Standard translation rights contract'
}
contract_id = rights_manager.add_rights_contract(contract_data)
```

#### Checking Rights Availability

```python
# Check if rights are available for a territory
available_territories = rights_manager.get_available_territories(work_id)
print(f"Available territories: {[t['territory_name'] for t in available_territories]}")

# Check specific territory availability
is_available = rights_manager.check_rights_availability(
    work_id=work_id,
    territory_name="France",
    language="French"
)
print(f"French rights available: {is_available}")
```

#### Contract Queries

```python
# Get all contracts for a work
contracts = rights_manager.get_work_contracts(work_id)

# Get contracts by territory
territory_contracts = rights_manager.get_territory_contracts("Germany")

# Get expiring contracts (within 6 months)
expiring = rights_manager.get_expiring_contracts(months_ahead=6)
```

### Rights Offering Management

#### Creating Offerings

```python
# Create a rights offering
offering_data = {
    'work_id': work_id,
    'territory_ids': [territory_id],
    'asking_price': 8000.0,
    'notes': 'Premium territory with strong market potential'
}
offering_id = rights_manager.add_rights_offering(offering_data)
```

#### Managing Offering Campaigns

```python
# Get active offerings
active_offerings = rights_manager.get_active_offerings()

# Update offering status
rights_manager.update_offering_status(offering_id, "negotiating")

# Close successful offering
rights_manager.close_offering(offering_id, success=True, final_amount=7500.0)
```

## Document Generation

### Imprint-Wide Rights Offerings

#### Basic Generation

```python
# Generate complete imprint catalog
result = generate_imprint_rights_sheet(
    imprint_config_path="configs/imprints/tech_books.json",
    output_dir="output/rights_offerings"
)
print(f"Generated: {result}")
```

#### With ISBN Filtering

```python
# Target specific titles
result = generate_imprint_rights_sheet(
    imprint_config_path="configs/imprints/tech_books.json",
    output_dir="output/rights_offerings",
    isbn_filter="9781234567890,9781234567891"
)
```

#### Command Line Generation

```bash
# Full catalog
python generate_longtable_catalog.py

# Filtered catalog
python generate_isbn_filtered_rights.py \
    --config configs/imprints/tech_books.json \
    --output-dir output/rights_offerings \
    --isbn-filter "9781234567890,9781234567891"

# Demo mode
python demo_isbn_filtering.py
```

### Work-Specific Rights Sheets

```python
# Generate offering sheet for specific work
result = generate_work_rights_sheet(
    work_id=work_id,
    output_dir="output/rights_offerings",
    offering_params={
        'asking_price': 8000,
        'target_territories': ['Germany', 'Austria', 'Switzerland'],
        'available_languages': ['German', 'English']
    }
)
```

### Customizing Output

#### Template Configuration

```python
# Custom template parameters
template_params = {
    'highlight_territories': ['Germany', 'France', 'Japan'],
    'include_sales_history': True,
    'show_comparable_titles': True,
    'format_style': 'professional'  # or 'compact', 'detailed'
}

result = generate_imprint_rights_sheet(
    imprint_config_path="configs/imprints/tech_books.json",
    output_dir="output/rights_offerings",
    template_params=template_params
)
```

#### LaTeX Styling Options

Create custom styling by modifying the generator:

```python
from codexes.modules.rights_management import RightsOfferingSheetGenerator

# Custom generator with styling
generator = RightsOfferingSheetGenerator()

# Override default colors
generator.brand_colors = {
    'primary': '#1E3A8A',    # Deep blue
    'secondary': '#DC2626',  # Red
    'accent': '#059669'      # Green
}

# Generate with custom styling
result = generator.generate_imprint_offering_sheet(
    imprint_config_path="configs/imprints/tech_books.json",
    output_dir="output/rights_offerings"
)
```

## Web Interface

### Launching the Dashboard

```bash
# Start Streamlit application
streamlit run src/codexes/pages/25_Rights_Management.py

# Access at http://localhost:8501
```

### Dashboard Features

#### 1. Main Rights Management Page

- **Works Management**: Add, edit, delete works
- **Publisher Database**: Manage publisher information
- **Contract Tracking**: Create and monitor rights contracts
- **Import/Export**: Bulk data operations

#### 2. Analytics Dashboard

```bash
# Launch analytics page
streamlit run src/codexes/pages/26_Rights_Analytics.py
```

Features:
- Revenue analysis by territory and year
- Rights utilization metrics
- Contract expiration tracking
- Market penetration reports

#### 3. Interactive Operations

```python
# Example: Web-based contract creation
import streamlit as st
from codexes.modules.rights_management import RightsManager

# In Streamlit app
rights_manager = RightsManager()

# Form for contract creation
with st.form("contract_form"):
    work_title = st.selectbox("Work", options=work_titles)
    publisher_name = st.selectbox("Publisher", options=publisher_names)
    territory = st.selectbox("Territory", options=territories)

    advance = st.number_input("Advance Amount", min_value=0.0)
    royalty = st.slider("Royalty Rate", 0.0, 0.20, 0.08, 0.01)

    if st.form_submit_button("Create Contract"):
        # Process contract creation
        contract_data = {
            'work_id': get_work_id(work_title),
            'publisher_id': get_publisher_id(publisher_name),
            'territory_id': get_territory_id(territory),
            'advance_amount': advance,
            'royalty_rate': royalty
        }
        contract_id = rights_manager.add_rights_contract(contract_data)
        st.success(f"Contract created with ID: {contract_id}")
```

## Advanced Features

### ISBN Filtering Strategies

#### Campaign-Specific Filtering

```python
# Scenario 1: Frankfurt Book Fair preparation
frankfurt_isbns = "9781234567890,9781234567891,9781234567892"
result = generate_imprint_rights_sheet(
    imprint_config_path="configs/imprints/tech_books.json",
    output_dir="output/frankfurt2025",
    isbn_filter=frankfurt_isbns
)

# Scenario 2: Territory-specific campaign
asian_market_isbns = get_titles_for_territory("Asia-Pacific")
result = generate_imprint_rights_sheet(
    imprint_config_path="configs/imprints/tech_books.json",
    output_dir="output/asia_campaign",
    isbn_filter=",".join(asian_market_isbns)
)
```

#### Dynamic ISBN Selection

```python
def get_high_potential_titles(rights_manager, territory="Europe"):
    """Select titles with high market potential for territory."""

    # Get works without existing contracts in territory
    available_works = rights_manager.get_available_works_for_territory(territory)

    # Filter by criteria (e.g., recent publications, good sales data)
    high_potential = []
    for work in available_works:
        if (work.get('publication_date', '') >= '2023-01-01' and
            work.get('page_count', 0) > 200):
            high_potential.append(work['isbn'])

    return high_potential

# Use dynamic selection
isbns = get_high_potential_titles(rights_manager, "Germany")
result = generate_imprint_rights_sheet(
    imprint_config_path="configs/imprints/tech_books.json",
    output_dir="output/germany_campaign",
    isbn_filter=",".join(isbns)
)
```

### Analytics and Reporting

#### Revenue Analysis

```python
# Territory revenue analysis
territory_revenue = rights_manager.get_territory_revenue_analysis()
for territory, data in territory_revenue.items():
    print(f"{territory}: {data['total_revenue']:.2f} ({data['contract_count']} contracts)")

# Yearly performance
yearly_performance = rights_manager.get_yearly_performance()
for year, metrics in yearly_performance.items():
    print(f"{year}: {metrics['revenue']:.2f} revenue, {metrics['new_contracts']} new contracts")
```

#### Contract Lifecycle Management

```python
# Monitor contract health
def monitor_contract_portfolio(rights_manager):
    """Generate comprehensive portfolio report."""

    # Expiring contracts (next 12 months)
    expiring = rights_manager.get_expiring_contracts(months_ahead=12)
    print(f"Contracts expiring in 12 months: {len(expiring)}")

    # High-value contracts at risk
    high_value_expiring = [c for c in expiring if c['advance_amount'] > 5000]
    print(f"High-value contracts at risk: {len(high_value_expiring)}")

    # Territory coverage analysis
    coverage = rights_manager.get_territory_coverage_analysis()
    under_utilized = [t for t, cov in coverage.items() if cov < 0.3]
    print(f"Under-utilized territories: {under_utilized}")

    return {
        'expiring_contracts': expiring,
        'high_value_at_risk': high_value_expiring,
        'under_utilized_territories': under_utilized
    }

# Run monthly portfolio review
portfolio_health = monitor_contract_portfolio(rights_manager)
```

### Integration with External Systems

#### CRM Integration

```python
def sync_with_crm(rights_manager, crm_client):
    """Synchronize rights data with CRM system."""

    # Get recent contract updates
    recent_contracts = rights_manager.get_recent_contracts(days=7)

    for contract in recent_contracts:
        # Update CRM with contract information
        crm_client.update_publisher_relationship(
            publisher_id=contract['publisher_id'],
            contract_value=contract['advance_amount'],
            contract_date=contract['contract_begin_date']
        )

        # Create follow-up tasks
        if contract['contract_end_date']:
            crm_client.create_renewal_task(
                contract_id=contract['id'],
                due_date=calculate_renewal_date(contract['contract_end_date'])
            )

# Schedule regular sync
import schedule
schedule.every().day.at("09:00").do(sync_with_crm, rights_manager, crm_client)
```

#### Distribution System Integration

```python
def export_for_distribution(rights_manager, format="csv"):
    """Export rights data for distribution systems."""

    # Get all active contracts
    active_contracts = rights_manager.get_active_contracts()

    # Format for distribution system
    distribution_data = []
    for contract in active_contracts:
        distribution_data.append({
            'isbn': contract['work_isbn'],
            'territory': contract['territory_name'],
            'language': contract['language'],
            'publisher': contract['publisher_name'],
            'status': 'licensed',
            'expiry_date': contract['contract_end_date']
        })

    # Export in required format
    if format == "csv":
        df = pd.DataFrame(distribution_data)
        df.to_csv("output/distribution_rights_export.csv", index=False)
    elif format == "json":
        with open("output/distribution_rights_export.json", 'w') as f:
            json.dump(distribution_data, f, indent=2)

    return f"Exported {len(distribution_data)} records"

# Automated export
export_result = export_for_distribution(rights_manager, format="csv")
```

## Integration Patterns

### Imprint Creation Workflow

```python
# Automatic rights offering generation during imprint setup
from codexes.modules.imprints.pipeline_generator import ImpartPipelineGenerator

class RightsEnabledImprint(ImpartPipelineGenerator):
    def generate_imprint_complete(self, config_path):
        """Enhanced imprint generation with rights offering."""

        # Standard imprint generation
        result = super().generate_imprint_complete(config_path)

        # Generate rights offering sheet
        if self.config.get('enable_rights_offering', True):
            rights_result = generate_imprint_rights_sheet(
                imprint_config_path=config_path,
                output_dir=f"output/rights_offerings/{self.imprint_name}"
            )
            result['rights_offering'] = rights_result

        return result
```

### Publishing Pipeline Integration

```python
# Integrate with book production pipeline
class RightsAwareBookPipeline:
    def __init__(self, rights_manager):
        self.rights_manager = rights_manager

    def process_new_book(self, book_data):
        """Process new book and set up rights tracking."""

        # Add to rights database
        work_id = self.rights_manager.add_work(book_data)

        # Create initial offering for major territories
        major_territories = ['Germany', 'France', 'Japan', 'Brazil']
        for territory in major_territories:
            if self.rights_manager.check_rights_availability(work_id, territory):
                offering_data = {
                    'work_id': work_id,
                    'territory_ids': [self.get_territory_id(territory)],
                    'asking_price': self.calculate_asking_price(book_data, territory),
                    'notes': f'Initial offering for {territory} market'
                }
                self.rights_manager.add_rights_offering(offering_data)

        return work_id
```

## Troubleshooting

### Common Issues

#### 1. Database Connectivity

```python
# Test database connection
try:
    rights_manager = RightsManager()
    test_query = rights_manager.db.get_works()
    print("Database connection successful")
except Exception as e:
    print(f"Database error: {e}")
    # Reinitialize database
    rights_manager.db.initialize_database()
```

#### 2. LaTeX Generation Errors

```python
# Debug LaTeX generation
import logging
logging.basicConfig(level=logging.DEBUG)

try:
    result = generate_imprint_rights_sheet(
        imprint_config_path="configs/imprints/test.json",
        output_dir="output/debug"
    )
except Exception as e:
    print(f"LaTeX generation error: {e}")
    # Check LaTeX installation
    import subprocess
    result = subprocess.run(['pdflatex', '--version'], capture_output=True, text=True)
    print(f"LaTeX available: {result.returncode == 0}")
```

#### 3. ISBN Filter Issues

```python
# Debug ISBN filtering
def debug_isbn_filter(rights_manager, isbn_filter):
    """Debug ISBN filtering issues."""

    # Parse ISBNs
    target_isbns = set()
    for isbn in isbn_filter.split(','):
        cleaned = isbn.strip().replace('-', '').replace(' ', '')
        if cleaned:
            target_isbns.add(cleaned)

    print(f"Target ISBNs: {target_isbns}")

    # Check available ISBNs
    all_works = rights_manager.db.get_works()
    available_isbns = set()
    for work in all_works:
        work_isbn = work.get('isbn', '') or work.get('isbn13', '')
        if work_isbn:
            cleaned = str(work_isbn).replace('-', '').replace(' ', '')
            available_isbns.add(cleaned)

    print(f"Available ISBNs: {len(available_isbns)}")

    # Find matches
    matches = target_isbns.intersection(available_isbns)
    print(f"Matching ISBNs: {matches}")

    # Find missing
    missing = target_isbns - available_isbns
    if missing:
        print(f"Missing ISBNs: {missing}")

    return len(matches) > 0

# Test filtering
success = debug_isbn_filter(rights_manager, "9781234567890,9781234567891")
```

### Performance Optimization

#### 1. Database Indexing

```python
# Add indexes for common queries
def optimize_database(rights_manager):
    """Add performance indexes."""

    db = rights_manager.db
    cursor = db.conn.cursor()

    # Index common lookup fields
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_works_isbn ON works(isbn)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_works_imprint ON works(imprint)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contracts_work ON rights_contracts(work_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contracts_territory ON rights_contracts(territory_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contracts_dates ON rights_contracts(contract_begin_date, contract_end_date)")

    db.conn.commit()
    print("Database indexes created")

optimize_database(rights_manager)
```

#### 2. Bulk Operations

```python
# Efficient bulk operations
def bulk_add_works(rights_manager, works_data):
    """Add multiple works efficiently."""

    db = rights_manager.db
    cursor = db.conn.cursor()

    # Prepare bulk insert
    insert_query = """
    INSERT INTO works (title, author_name, isbn, publication_date, imprint, page_count)
    VALUES (?, ?, ?, ?, ?, ?)
    """

    # Prepare data tuples
    work_tuples = []
    for work in works_data:
        work_tuples.append((
            work['title'],
            work.get('author_name', ''),
            work.get('isbn', ''),
            work.get('publication_date', ''),
            work.get('imprint', ''),
            work.get('page_count', 0)
        ))

    # Bulk insert
    cursor.executemany(insert_query, work_tuples)
    db.conn.commit()

    print(f"Bulk inserted {len(work_tuples)} works")

# Example usage
works_data = [
    {'title': 'Book 1', 'isbn': '123', 'imprint': 'Tech Books'},
    {'title': 'Book 2', 'isbn': '456', 'imprint': 'Tech Books'},
    # ... many more works
]
bulk_add_works(rights_manager, works_data)
```

## Best Practices

### 1. Data Management

- **Consistent ISBN Formats**: Always clean and validate ISBNs
- **Territory Standardization**: Use consistent territory naming conventions
- **Date Formats**: Use ISO format (YYYY-MM-DD) for all dates
- **Regular Backups**: Implement automated database backups

### 2. Rights Offering Generation

- **Template Consistency**: Maintain brand-consistent templates
- **Content Review**: Always review generated content before distribution
- **Version Control**: Track offering sheet versions and updates
- **Target Audience**: Customize content for specific markets/territories

### 3. Contract Management

- **Renewal Tracking**: Set up automated renewal reminders
- **Performance Monitoring**: Track royalty payments and performance
- **Document Storage**: Maintain links to contract documents
- **Compliance Checking**: Regular compliance and territory restriction reviews

### 4. Integration Workflows

- **API Documentation**: Document all integration points
- **Error Handling**: Implement robust error handling and logging
- **Testing**: Comprehensive testing of all integration workflows
- **Monitoring**: Set up monitoring for automated processes

### 5. Security Considerations

- **Access Controls**: Implement appropriate access controls for sensitive rights data
- **Data Encryption**: Encrypt sensitive contract and financial information
- **Audit Trails**: Maintain audit trails for all rights transactions
- **Backup Security**: Secure backup storage and access

---

This usage guide provides comprehensive coverage of the Rights Management Module functionality. For additional support or advanced integration needs, consult the module documentation or contact the development team.