# ISBN Rebuild Functionality - Complete Guide

## ✅ **YES! The ISBN Schedule Assignment feature includes comprehensive rebuild support.**

The system provides multiple ways to handle book rebuilds while maintaining ISBN consistency:

## 🔄 **Core Rebuild Methods**

### 1. **`get_or_assign_isbn()` - Recommended for Rebuilds**
```python
# This method is perfect for rebuilds - it will:
# - Return existing ISBN if book_id already has one
# - Assign new ISBN if book_id doesn't exist
isbn = scheduler.get_or_assign_isbn(
    book_id="my_book_v1",
    book_title="My Book (Revised)",
    scheduled_date="2024-12-01"
)
```

### 2. **`get_isbn_by_book_id()` - Lookup Existing**
```python
# Look up existing ISBN for a book ID
existing_isbn = scheduler.get_isbn_by_book_id("my_book_v1")
if existing_isbn:
    print(f"Book already has ISBN: {existing_isbn}")
```

### 3. **`assign_specific_isbn()` - Manual Assignment**
```python
# Assign a specific ISBN (for special cases)
success = scheduler.assign_specific_isbn(
    isbn="9781234567890",
    book_title="My Book",
    book_id="my_book_v1",
    scheduled_date="2024-12-01"
)
```

## 🖥️ **User Interface Support**

### Streamlit Web Interface
- **"Lookup/Reuse" tab** in the Schedule Assignment page
- **Quick ISBN Lookup** on the dashboard
- **Search functionality** to find existing assignments

### Command Line Interface
```bash
# Get existing or assign new ISBN (perfect for rebuilds)
python tools/isbn_schedule_cli.py get-or-assign --book-id book_1 --title "My Book" --date 2024-12-01

# Look up existing ISBN
python tools/isbn_schedule_cli.py lookup --book-id book_1

# Search for assignments
python tools/isbn_schedule_cli.py search --query "book_1"
```

## 🏗️ **Integration Example**

Here's how to integrate this into your book pipeline:

```python
from codexes.modules.distribution.isbn_scheduler import ISBNScheduler

def build_book(book_id: str, book_title: str, is_rebuild: bool = False):
    scheduler = ISBNScheduler()
    
    # This handles both new books and rebuilds automatically
    isbn = scheduler.get_or_assign_isbn(
        book_id=book_id,
        book_title=book_title,
        scheduled_date=datetime.now().strftime('%Y-%m-%d'),
        notes=f"{'Rebuild' if is_rebuild else 'Initial build'}"
    )
    
    if isbn:
        print(f"Using ISBN: {isbn}")
        # Continue with book generation...
        return isbn
    else:
        print("No ISBN available")
        return None

# Usage:
# Initial build
isbn1 = build_book("my_book_v1", "My Great Book", is_rebuild=False)

# Rebuild - will reuse the same ISBN
isbn2 = build_book("my_book_v1", "My Great Book (Revised)", is_rebuild=True)

# isbn1 == isbn2 ✅
```

## 🧪 **Tested Scenarios**

The rebuild functionality has been thoroughly tested:

✅ **Initial assignment** - New book gets new ISBN  
✅ **Rebuild with same book ID** - Reuses existing ISBN  
✅ **Assignment updates** - Updates title/metadata while keeping ISBN  
✅ **Status preservation** - Maintains assignment status across rebuilds  
✅ **Error handling** - Graceful handling of edge cases  
✅ **Data persistence** - Works across application restarts  

## 🎯 **Key Benefits**

1. **ISBN Consistency** - Same book always gets same ISBN
2. **Automatic Detection** - System knows if it's a rebuild or new book
3. **Metadata Updates** - Can update book details while keeping ISBN
4. **Status Tracking** - Maintains publication status across rebuilds
5. **Multiple Interfaces** - Available via web UI, CLI, and API
6. **Production Ready** - Fully tested and error-handled

## 🚀 **Ready to Use**

The rebuild functionality is **immediately available** and ready for production use. Simply use `get_or_assign_isbn()` in your book pipeline and it will handle both new assignments and rebuilds automatically.

**Perfect for your use case!** 🎉