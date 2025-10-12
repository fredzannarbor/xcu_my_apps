# Tools Directory

This directory contains utility scripts for managing the Codexes Factory system.

## Available Tools

### ingest_isbn.py

A comprehensive tool for ingesting ISBNs into the ISBN database from various sources.

**Features:**
- Import from Bowker spreadsheets (Excel or CSV format)
- Import from custom CSV files with configurable column names
- Manual entry of individual ISBNs
- Database statistics reporting
- Dry-run mode for testing
- Verbose logging support

**Usage Examples:**

```bash
# Show current database statistics
python tools/ingest_isbn.py --stats

# Import from Bowker spreadsheet
python tools/ingest_isbn.py --bowker path/to/bowker.xlsx --publisher nimble-books

# Import from CSV file
python tools/ingest_isbn.py --csv path/to/isbns.csv --publisher nimble-books

# Import from CSV with custom column names
python tools/ingest_isbn.py --csv path/to/isbns.csv --publisher nimble-books \
  --isbn-column "ISBN-13" --status-column "Status" --title-column "Book Title"

# Manually add a single ISBN
python tools/ingest_isbn.py --manual --isbn 9781234567890 --publisher nimble-books \
  --title "My Book" --status available --format "Paperback"

# Test import without making changes (dry run)
python tools/ingest_isbn.py --csv path/to/isbns.csv --publisher nimble-books --dry-run
```

**Supported ISBN Statuses:**
- `available` - ISBN is available for assignment
- `assigned` - ISBN is privately assigned to a book
- `published` - ISBN is publicly assigned (book is published)

### report_isbns.py

Reports on the most recently assigned ISBNs from the database.

**Usage:**
```bash
# Show 10 most recent assignments (default)
python tools/report_isbns.py

# Show 25 most recent assignments
python tools/report_isbns.py -n 25

# Use custom database file
python tools/report_isbns.py --db-file path/to/custom_database.json
```

## Database Structure

The ISBN database is stored in JSON format at `data/isbn_database.json`. Each ISBN record contains:

- `isbn`: The 13-digit ISBN
- `publisher_id`: Publisher identifier
- `status`: Current status (available, privately_assigned, publicly_assigned)
- `assigned_to`: Book ID if assigned (optional)
- `assignment_date`: Date when ISBN was assigned (optional)
- `publication_date`: Date when book was published (optional)
- `title`: Book title (optional)
- `format`: Book format (Paperback, Hardback, Ebook, etc.) (optional)
- `imprint`: Imprint name (optional)
- `notes`: Additional notes (optional)

## Development

When adding new tools to this directory:

1. Follow the existing naming convention (`verb_noun.py`)
2. Include comprehensive help text and examples
3. Add error handling and logging
4. Support dry-run mode where applicable
5. Update this README with documentation

## Dependencies

Tools in this directory may require additional Python packages:
- `pandas` - For CSV and Excel file processing
- `openpyxl` - For Excel file support

Install dependencies with:
```bash
uv add pandas openpyxl
```