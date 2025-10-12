# Manual ISBN Assignment from Schedule Files - Complete Guide

## ✅ **YES! You can now manually enter ISBNs in schedule files.**

The ISBN Schedule Assignment system now supports importing publishing schedules from CSV or JSON files where you can manually specify ISBNs for each title.

## 📄 **Supported File Formats**

### CSV Format
```csv
title,book_id,scheduled_date,isbn,imprint,publisher,format,priority,notes
"My Great Book",book_001,2024-12-01,9781234567890,My Imprint,My Publisher,paperback,1,Manual ISBN
"Another Book",book_002,2024-12-15,,My Imprint,My Publisher,hardcover,2,Auto-assign ISBN
```

### JSON Format
```json
[
  {
    "title": "My Great Book",
    "book_id": "book_001",
    "scheduled_date": "2024-12-01",
    "isbn": "9781234567890",
    "imprint": "My Imprint",
    "publisher": "My Publisher",
    "format": "paperback",
    "priority": 1,
    "notes": "Manual ISBN assignment"
  },
  {
    "title": "Another Book",
    "book_id": "book_002",
    "scheduled_date": "2024-12-15",
    "isbn": "",
    "imprint": "My Imprint",
    "publisher": "My Publisher",
    "format": "hardcover",
    "priority": 2,
    "notes": "Auto-assign ISBN"
  }
]
```

## 🎯 **Key Features**

### Manual ISBN Assignment
- **Include specific ISBNs** in the `isbn` column/field
- **13-digit validation** - ISBNs must be exactly 13 digits
- **Duplicate prevention** - System prevents assigning same ISBN twice
- **Immediate assignment** - Manual ISBNs are marked as assigned

### Auto-Assignment Fallback
- **Leave ISBN empty** for automatic assignment from available blocks
- **Rebuild support** - Reuses existing ISBN if book_id already exists
- **Mixed mode** - Same file can have both manual and auto assignments

### Error Handling
- **Validation** - Invalid ISBNs are rejected with clear error messages
- **Conflict detection** - Duplicate ISBN assignments are prevented
- **Partial success** - Import continues even if some entries fail
- **Detailed reporting** - Shows exactly what succeeded and what failed

## 🖥️ **How to Use**

### Command Line Interface
```bash
# Export a template
python tools/isbn_schedule_cli.py export-template --format csv --output my_schedule.csv

# Edit the file to add your books and ISBNs

# Import the schedule
python tools/isbn_schedule_cli.py import-schedule --file my_schedule.csv --show-errors
```

### Streamlit Web Interface
1. Go to **"Import Schedule"** page
2. Upload your CSV or JSON file
3. Preview the file contents
4. Click **"Import Schedule"** to process
5. View detailed results and any errors

### Python API
```python
from codexes.modules.distribution.isbn_scheduler import ISBNScheduler

scheduler = ISBNScheduler()

# Import from CSV
results = scheduler.import_schedule_from_csv('my_schedule.csv')

# Import from JSON
results = scheduler.import_schedule_from_json('my_schedule.json')

# Check results
print(f"Processed: {results['processed']}")
print(f"Manual ISBNs: {results['assigned_manual']}")
print(f"Auto ISBNs: {results['assigned_auto']}")
print(f"Errors: {len(results['errors'])}")
```

## 📋 **Required Fields**

- **title**: Book title
- **book_id**: Unique identifier for the book  
- **scheduled_date**: Publication date (YYYY-MM-DD format)

## 📋 **Optional Fields**

- **isbn**: Manual ISBN assignment (13 digits) - **leave empty for auto-assignment**
- **imprint**: Publishing imprint name
- **publisher**: Publisher name
- **format**: Book format (paperback, hardcover, ebook)
- **priority**: Priority level (1=High, 2=Medium, 3=Low)
- **notes**: Additional notes

## 🔄 **Workflow Examples**

### Initial Publishing Schedule
```csv
title,book_id,scheduled_date,isbn,notes
"Book with Purchased ISBN",book_001,2024-12-01,9781234567890,Pre-purchased ISBN
"Book Needing ISBN",book_002,2024-12-15,,Will auto-assign
```

### Book Rebuilds
```csv
title,book_id,scheduled_date,isbn,notes
"Updated Book Title",book_001,2024-12-01,,Will reuse existing ISBN
```

### Mixed Assignments
```csv
title,book_id,scheduled_date,isbn,notes
"Special Edition",special_001,2024-12-01,9780123456789,Specific ISBN required
"Regular Edition",regular_001,2024-12-15,,Auto-assign from pool
"Reprint",book_001,2024-12-20,,Reuse existing ISBN
```

## 📊 **Import Results**

The system provides detailed feedback:

- **Processed**: Total books successfully imported
- **Manual ISBNs**: Books with manually specified ISBNs
- **Auto ISBNs**: Books that got auto-assigned ISBNs  
- **Updated**: Existing assignments that were updated
- **Errors**: Failed imports with specific error messages

## 🎉 **Perfect for Your Use Case!**

This feature is **exactly what you need** for:

✅ **Pre-assigning specific ISBNs** to books in your schedule  
✅ **Bulk importing** publishing schedules with mixed ISBN types  
✅ **Managing rebuilds** while preserving existing ISBNs  
✅ **Validating ISBN formats** and preventing duplicates  
✅ **Tracking assignment status** throughout the publishing process  

**The manual ISBN assignment functionality is production-ready and immediately available!** 🚀