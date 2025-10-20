"""
Schedule ISBN Manager - Streamlit UI

This page provides a user interface for managing ISBN assignments in publishing schedules.
"""


import logging
import streamlit as st
import json
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize shared authentication system
try:
    shared_auth = get_shared_auth()
    logger.info("Shared authentication system initialized")
except Exception as e:
    logger.error(f"Failed to initialize shared auth: {e}")
    st.error("Authentication system unavailable.")




logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)



# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
except ImportError as e:
    import streamlit as st
    st.error(f"Failed to import shared authentication: {e}")
    st.error("Please ensure /Users/fred/xcu_my_apps/shared/auth is accessible")
    st.stop()


try:
    from src.codexes.modules.distribution.schedule_isbn_manager import ScheduleISBNManager
    from src.codexes.modules.distribution.isbn_database import ISBNStatus
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# NOTE: st.set_page_config() and render_unified_sidebar() handled by main app

# Sync session state from shared auth
if is_authenticated():
    user_info = get_user_info()
    st.session_state.username = user_info.get('username')
    st.session_state.user_name = user_info.get('user_name')
    st.session_state.user_email = user_info.get('user_email')
    logger.info(f"User authenticated via shared auth: {st.session_state.username}")
else:
    if "username" not in st.session_state:
        st.session_state.username = None




# Initialize session state
if 'isbn_manager' not in st.session_state:
    st.session_state.isbn_manager = None
if 'schedule_data' not in st.session_state:
    st.session_state.schedule_data = None
if 'schedule_path' not in st.session_state:
    st.session_state.schedule_path = None

def load_schedule_manager():
    """Load the ISBN manager."""
    try:
        isbn_db_path = st.session_state.get('isbn_db_path', 'data/isbn_database.json')
        st.session_state.isbn_manager = ScheduleISBNManager(isbn_db_path)
        return True
    except Exception as e:
        st.error(f"Error loading ISBN manager: {e}")
        return False

def load_schedule_file(file_path: str):
    """Load a schedule file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            st.session_state.schedule_data = json.load(f)
        st.session_state.schedule_path = file_path
        return True
    except Exception as e:
        st.error(f"Error loading schedule file: {e}")
        return False

def get_available_schedules():
    """Get list of available schedule files."""
    schedule_files = []
    
    # Look for schedule files in common locations
    search_paths = [
        Path("imprints"),
        Path("schedules"),
        Path(".")
    ]
    
    for search_path in search_paths:
        if search_path.exists():
            for file_path in search_path.rglob("*schedule*.json"):
                schedule_files.append(str(file_path))
    
    return sorted(schedule_files)

def display_schedule_overview(schedule_data: Dict[str, Any]):
    """Display an overview of the schedule."""
    if not schedule_data or 'publishing_schedule' not in schedule_data:
        st.warning("Invalid schedule format")
        return
    
    total_books = 0
    books_with_isbn = 0
    months = []
    
    for month_data in schedule_data['publishing_schedule']:
        month_name = month_data.get('month', 'Unknown')
        month_books = len(month_data.get('books', []))
        month_with_isbn = sum(1 for book in month_data.get('books', []) if book.get('isbn'))
        
        months.append({
            'Month': month_name,
            'Total Books': month_books,
            'With ISBN': month_with_isbn,
            'Without ISBN': month_books - month_with_isbn,
            'Coverage %': round((month_with_isbn / month_books * 100) if month_books > 0 else 0, 1)
        })
        
        total_books += month_books
        books_with_isbn += month_with_isbn
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Books", total_books)
    
    with col2:
        st.metric("With ISBN", books_with_isbn)
    
    with col3:
        st.metric("Without ISBN", total_books - books_with_isbn)
    
    with col4:
        coverage = round((books_with_isbn / total_books * 100) if total_books > 0 else 0, 1)
        st.metric("Coverage", f"{coverage}%")
    
    # Display monthly breakdown
    if months:
        st.subheader("Monthly Breakdown")
        df = pd.DataFrame(months)
        st.dataframe(df, use_container_width=True)

def display_isbn_assignment_form():
    """Display the ISBN assignment form."""
    st.subheader("📖 Assign ISBNs")
    
    if not st.session_state.isbn_manager or not st.session_state.schedule_data:
        st.warning("Please load a schedule file first.")
        return
    
    with st.form("isbn_assignment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            publisher_id = st.text_input(
                "Publisher ID",
                value="nimble-books",
                help="Publisher identifier for ISBN assignment"
            )
            
            format_type = st.selectbox(
                "Book Format",
                ["paperback", "hardcover", "ebook"],
                help="Default format for books"
            )
        
        with col2:
            dry_run = st.checkbox(
                "Dry Run",
                value=True,
                help="Preview assignments without actually assigning ISBNs"
            )
            
            output_path = st.text_input(
                "Output Path (optional)",
                placeholder="Leave empty to overwrite original file",
                help="Path to save updated schedule"
            )
        
        submitted = st.form_submit_button("Assign ISBNs", type="primary")
        
        if submitted:
            if not publisher_id:
                st.error("Publisher ID is required")
                return
            
            # Check available ISBNs
            available_count = st.session_state.isbn_manager.get_available_isbn_count(publisher_id)
            
            if available_count == 0 and not dry_run:
                st.error(f"No available ISBNs found for publisher '{publisher_id}'")
                st.info("Please add ISBNs to the database using the ISBN ingestion tool.")
                return
            
            st.info(f"Available ISBNs for {publisher_id}: {available_count}")
            
            # Perform assignment
            with st.spinner("Processing ISBN assignments..."):
                results = st.session_state.isbn_manager.assign_isbns_to_schedule(
                    schedule_path=st.session_state.schedule_path,
                    publisher_id=publisher_id,
                    output_path=output_path if output_path else None,
                    format_type=format_type,
                    dry_run=dry_run
                )
            
            if 'error' in results:
                st.error(f"Error: {results['error']}")
                return
            
            # Display results
            st.success("Assignment completed!")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Books", results['total_books'])
            with col2:
                st.metric("Assigned", results['assigned'])
            with col3:
                st.metric("Already Had ISBN", results['already_assigned'])
            with col4:
                st.metric("Failed", results['failed'])
            
            # Show assignments
            if results['assignments']:
                st.subheader("📋 Assignment Details")
                assignments_df = pd.DataFrame(results['assignments'])
                st.dataframe(assignments_df, use_container_width=True)
            
            # Show errors
            if results['errors']:
                st.subheader("❌ Errors")
                errors_df = pd.DataFrame(results['errors'])
                st.dataframe(errors_df, use_container_width=True)
            
            # Reload schedule if not dry run
            if not dry_run and results['assigned'] > 0:
                load_schedule_file(st.session_state.schedule_path)
                st.rerun()

def display_validation_results():
    """Display ISBN validation results."""
    st.subheader("🔍 Validate ISBNs")
    
    if not st.session_state.isbn_manager or not st.session_state.schedule_path:
        st.warning("Please load a schedule file first.")
        return
    
    if st.button("Validate Schedule ISBNs", type="primary"):
        with st.spinner("Validating ISBNs..."):
            results = st.session_state.isbn_manager.validate_schedule_isbns(
                st.session_state.schedule_path
            )
        
        if 'error' in results:
            st.error(f"Error: {results['error']}")
            return
        
        # Display validation summary
        st.subheader("📊 Validation Summary")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Books", results['total_books'])
        with col2:
            st.metric("With ISBN", results['books_with_isbn'])
        with col3:
            st.metric("Valid ISBNs", results['valid_isbns'])
        with col4:
            st.metric("Invalid ISBNs", results['invalid_isbns'])
        with col5:
            st.metric("Duplicates", results['duplicate_isbns'])
        
        # Show coverage
        if results['total_books'] > 0:
            coverage = (results['books_with_isbn'] / results['total_books']) * 100
            st.progress(coverage / 100)
            st.write(f"ISBN Coverage: {coverage:.1f}%")
        
        # Show validation details
        if results['validation_details']:
            st.subheader("📋 Validation Details")
            
            # Create a more readable dataframe
            details_for_display = []
            for detail in results['validation_details']:
                status_icons = {
                    'valid': '✅',
                    'no_isbn': '📝',
                    'invalid_format': '❌',
                    'duplicate': '⚠️',
                    'not_in_database': '🔍'
                }
                
                details_for_display.append({
                    'Status': status_icons.get(detail['status'], '❓'),
                    'Title': detail['title'],
                    'Month': detail.get('month', 'Unknown'),
                    'ISBN': detail.get('isbn', 'N/A'),
                    'Message': detail['message']
                })
            
            df = pd.DataFrame(details_for_display)
            st.dataframe(df, use_container_width=True)

def display_bulk_assignment_form():
    """Display the bulk ISBN assignment form."""
    st.subheader("📚 Bulk Assign ISBNs")
    
    if not st.session_state.isbn_manager or not st.session_state.schedule_data:
        st.warning("Please load a schedule file first.")
        return
    
    st.write("Upload a JSON file with ISBN assignments in the format:")
    st.code('''[
  {"title": "Book Title 1", "isbn": "9781234567890"},
  {"title": "Book Title 2", "isbn": "9780987654321"}
]''', language="json")
    
    uploaded_file = st.file_uploader(
        "Choose assignments file",
        type=['json'],
        help="JSON file with title-ISBN mappings"
    )
    
    if uploaded_file is not None:
        try:
            assignments = json.load(uploaded_file)
            
            if not isinstance(assignments, list):
                st.error("File must contain a JSON array")
                return
            
            # Validate format
            valid_assignments = []
            for i, assignment in enumerate(assignments):
                if isinstance(assignment, dict) and 'title' in assignment and 'isbn' in assignment:
                    valid_assignments.append(assignment)
                else:
                    st.warning(f"Invalid assignment at index {i}: missing 'title' or 'isbn'")
            
            if not valid_assignments:
                st.error("No valid assignments found in file")
                return
            
            st.success(f"Loaded {len(valid_assignments)} valid assignments")
            
            # Show preview
            st.subheader("📋 Assignment Preview")
            preview_df = pd.DataFrame(valid_assignments)
            st.dataframe(preview_df, use_container_width=True)
            
            # Bulk assignment form
            with st.form("bulk_assignment_form"):
                output_path = st.text_input(
                    "Output Path (optional)",
                    placeholder="Leave empty to overwrite original file"
                )
                
                submitted = st.form_submit_button("Apply Bulk Assignments", type="primary")
                
                if submitted:
                    with st.spinner("Applying bulk assignments..."):
                        results = st.session_state.isbn_manager.bulk_assign_isbns(
                            valid_assignments,
                            st.session_state.schedule_path,
                            output_path if output_path else None
                        )
                    
                    if 'error' in results:
                        st.error(f"Error: {results['error']}")
                        return
                    
                    # Display results
                    st.success("Bulk assignment completed!")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Assignments", results['total_assignments'])
                    with col2:
                        st.metric("Successful", results['successful'])
                    with col3:
                        st.metric("Failed", results['failed'])
                    with col4:
                        st.metric("Not Found", results['not_found'])
                    
                    # Show details
                    if results['details']:
                        st.subheader("📋 Assignment Results")
                        details_df = pd.DataFrame(results['details'])
                        st.dataframe(details_df, use_container_width=True)
                    
                    # Reload schedule
                    if results['successful'] > 0:
                        load_schedule_file(st.session_state.schedule_path)
                        st.rerun()
        
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON file: {e}")
        except Exception as e:
            st.error(f"Error processing file: {e}")

def main():
    """Main Streamlit app."""
    st.title("📚 Schedule ISBN Manager")
    st.write("Assign and manage ISBNs in publishing schedules")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # ISBN Database path
        isbn_db_path = st.text_input(
            "ISBN Database Path",
            value="data/isbn_database.json",
            help="Path to the ISBN database JSON file"
        )
        st.session_state.isbn_db_path = isbn_db_path
        
        # Load ISBN manager
        if st.button("Load ISBN Manager"):
            if load_schedule_manager():
                st.success("ISBN Manager loaded successfully!")
            else:
                st.error("Failed to load ISBN Manager")
        
        st.divider()
        
        # Schedule file selection
        st.header("📅 Schedule File")
        
        # Get available schedules
        available_schedules = get_available_schedules()
        
        if available_schedules:
            selected_schedule = st.selectbox(
                "Select Schedule File",
                options=available_schedules,
                help="Choose a schedule file to work with"
            )
            
            if st.button("Load Schedule"):
                if load_schedule_file(selected_schedule):
                    st.success("Schedule loaded successfully!")
                    st.rerun()
        else:
            st.warning("No schedule files found")
        
        # Manual file path input
        manual_path = st.text_input(
            "Or enter path manually",
            placeholder="path/to/schedule.json"
        )
        
        if manual_path and st.button("Load Manual Path"):
            if load_schedule_file(manual_path):
                st.success("Schedule loaded successfully!")
                st.rerun()
        
        # Show current status
        if st.session_state.schedule_path:
            st.success(f"📅 Loaded: {Path(st.session_state.schedule_path).name}")
        
        if st.session_state.isbn_manager:
            st.success("📚 ISBN Manager: Ready")
    
    # Main content area
    if not st.session_state.isbn_manager:
        st.info("👈 Please configure and load the ISBN Manager from the sidebar")
        return
    
    if not st.session_state.schedule_data:
        st.info("👈 Please select and load a schedule file from the sidebar")
        return
    
    # Display schedule overview
    st.header("📊 Schedule Overview")
    display_schedule_overview(st.session_state.schedule_data)
    
    # Tabs for different operations
    tab1, tab2, tab3 = st.tabs(["📖 Assign ISBNs", "🔍 Validate ISBNs", "📚 Bulk Assign"])
    
    with tab1:
        display_isbn_assignment_form()
    
    with tab2:
        display_validation_results()
    
    with tab3:
        display_bulk_assignment_form()

if __name__ == "__main__":
    main()