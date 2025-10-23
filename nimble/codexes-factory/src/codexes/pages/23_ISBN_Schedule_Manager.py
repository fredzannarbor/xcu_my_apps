"""
ISBN Schedule Manager - Streamlit page for managing ISBN assignments in publishing schedules.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging
import sys
from pathlib import Path


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



# Add paths for imports
sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
except ImportError as e:
    import streamlit as st
    st.error(f"Failed to import shared authentication: {e}")
    st.error("Please ensure /Users/fred/xcu_my_apps/shared/auth is accessible")
    st.stop()


sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import with fallback pattern
try:
    from codexes.modules.distribution.isbn_scheduler import ISBNScheduler, ISBNStatus, ISBNAssignment
except ImportError:
    from src.codexes.modules.distribution.isbn_scheduler import ISBNScheduler, ISBNStatus, ISBNAssignment

# Render unified sidebar only if not already rendered by main app
# Main app sets sidebar_rendered=True to prevent duplication
if not st.session_state.get('sidebar_rendered', False):
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




def main():
    """Main ISBN Schedule Manager interface"""
    # Render unified sidebar only if not already rendered by main app
    # Main app sets sidebar_rendered=True to prevent duplication
    if not st.session_state.get('sidebar_rendered', False):
        # NOTE: st.set_page_config() and render_unified_sidebar() handled by main app
    # DO NOT render sidebar here - it's already rendered by codexes-factory-home-ui.py

        st.title("📚 ISBN Schedule Manager")
    st.markdown("Manage ISBN assignments across your publishing schedule")

    if 'isbn_scheduler' not in st.session_state:
        st.session_state.isbn_scheduler = ISBNScheduler()

    scheduler = st.session_state.isbn_scheduler

    page = st.selectbox(
        "Select Function",
        [
            "📊 Dashboard",
            "📅 Schedule Assignment",
            "📋 View Assignments",
            "🏷️ Manage ISBN Blocks",
            "📈 Reports",
            "📤 Import Schedule"
        ]
    )
    
    if page == "📊 Dashboard":
        render_dashboard(scheduler)
    elif page == "📅 Schedule Assignment":
        render_schedule_assignment(scheduler)
    elif page == "📋 View Assignments":
        render_view_assignments(scheduler)
    elif page == "🏷️ Manage ISBN Blocks":
        render_manage_blocks(scheduler)
    elif page == "📈 Reports":
        render_reports(scheduler)
    elif page == "📤 Import Schedule":
        render_import_schedule(scheduler)

def render_dashboard(scheduler: ISBNScheduler):
    """Render the main dashboard"""
    st.header("📊 ISBN Assignment Dashboard")
    
    report = scheduler.get_isbn_availability_report()
    if not report:
        st.error("Unable to generate availability report")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total ISBNs", report.get('total_isbns', 0))
    with col2:
        st.metric("Available ISBNs", report.get('available_isbns', 0))
    with col3:
        st.metric("Used ISBNs", report.get('used_isbns', 0))
    with col4:
        st.metric("Reserved ISBNs", report.get('reserved_isbns', 0))
    
    st.subheader("📅 Upcoming Assignments (Next 30 Days)")
    upcoming = scheduler.get_upcoming_assignments(30)
    if upcoming:
        upcoming_data = []
        for assignment in upcoming[:10]:
            upcoming_data.append({
                "ISBN": assignment.isbn,
                "Title": assignment.book_title,
                "Scheduled Date": assignment.scheduled_date,
                "Status": assignment.status.replace('_', ' ').title(),
                "Priority": "High" if assignment.priority == 1 else "Medium" if assignment.priority == 2 else "Low"
            })
        st.dataframe(pd.DataFrame(upcoming_data), use_container_width=True)
    else:
        st.info("No upcoming assignments in the next 30 days")
    
    # Quick lookup section
    st.subheader("🔍 Quick ISBN Lookup")
    col1, col2 = st.columns([2, 1])
    with col1:
        lookup_book_id = st.text_input("Enter Book ID to find its ISBN:", key="dashboard_lookup")
    with col2:
        st.write("")  # Spacer
        if st.button("🔍 Look Up", key="dashboard_lookup_btn"):
            if lookup_book_id:
                isbn = scheduler.get_isbn_by_book_id(lookup_book_id)
                if isbn:
                    assignment = scheduler.get_assignment_by_book_id(lookup_book_id)
                    st.success(f"📖 Book ID '{lookup_book_id}' has ISBN: **{isbn}**")
                    st.info(f"Title: {assignment.book_title} | Status: {assignment.status.replace('_', ' ').title()}")
                else:
                    st.warning(f"❌ No ISBN found for book ID '{lookup_book_id}'")

def render_schedule_assignment(scheduler: ISBNScheduler):
    """Render ISBN assignment scheduling form"""
    st.header("📅 Schedule ISBN Assignment")
    
    # Add tabs for different assignment types
    tab1, tab2, tab3 = st.tabs(["📅 New Assignment", "🔍 Lookup/Reuse", "🎯 Specific ISBN"])
    
    with tab1:
        st.subheader("Schedule New ISBN Assignment")
        with st.form("schedule_assignment_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                book_title = st.text_input("Book Title*")
                book_id = st.text_input("Book ID*")
                scheduled_date = st.date_input("Scheduled Date*", value=datetime.now().date())
                format_type = st.selectbox("Format", ["paperback", "hardcover", "ebook"])
            
            with col2:
                imprint = st.text_input("Imprint")
                publisher = st.text_input("Publisher")
                priority = st.selectbox("Priority", [1, 2, 3], format_func=lambda x: "High" if x == 1 else "Medium" if x == 2 else "Low")
                notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("📅 Schedule Assignment")
            
            if submitted:
                if book_title and book_id:
                    isbn = scheduler.schedule_isbn_assignment(
                        book_title=book_title,
                        book_id=book_id,
                        scheduled_date=scheduled_date.strftime('%Y-%m-%d'),
                        imprint=imprint,
                        publisher=publisher,
                        format=format_type,
                        priority=priority,
                        notes=notes
                    )
                    if isbn:
                        st.success(f"✅ Successfully scheduled ISBN {isbn} for '{book_title}'")
                        st.balloons()
                    else:
                        st.error("❌ Failed to schedule ISBN assignment. No available ISBNs found.")
                else:
                    st.error("❌ Please fill in all required fields (marked with *)")
    
    with tab2:
        st.subheader("Get Existing or Assign New ISBN")
        st.info("💡 This is perfect for book rebuilds - it will reuse the existing ISBN if the book ID already has one, or assign a new one if not.")
        
        with st.form("get_or_assign_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                book_title_reuse = st.text_input("Book Title*", key="reuse_title")
                book_id_reuse = st.text_input("Book ID*", key="reuse_book_id", help="Enter the book ID to look up existing ISBN")
                scheduled_date_reuse = st.date_input("Scheduled Date*", value=datetime.now().date(), key="reuse_date")
                format_type_reuse = st.selectbox("Format", ["paperback", "hardcover", "ebook"], key="reuse_format")
            
            with col2:
                imprint_reuse = st.text_input("Imprint", key="reuse_imprint")
                publisher_reuse = st.text_input("Publisher", key="reuse_publisher")
                priority_reuse = st.selectbox("Priority", [1, 2, 3], format_func=lambda x: "High" if x == 1 else "Medium" if x == 2 else "Low", key="reuse_priority")
                notes_reuse = st.text_area("Notes", key="reuse_notes")
            
            submitted_reuse = st.form_submit_button("🔍 Get or Assign ISBN")
            
            if submitted_reuse:
                if book_title_reuse and book_id_reuse:
                    isbn = scheduler.get_or_assign_isbn(
                        book_id=book_id_reuse,
                        book_title=book_title_reuse,
                        scheduled_date=scheduled_date_reuse.strftime('%Y-%m-%d'),
                        imprint=imprint_reuse,
                        publisher=publisher_reuse,
                        format=format_type_reuse,
                        priority=priority_reuse,
                        notes=notes_reuse
                    )
                    if isbn:
                        assignment = scheduler.get_assignment_by_book_id(book_id_reuse)
                        is_existing = assignment.assigned_date is not None or assignment.status != ISBNStatus.SCHEDULED.value
                        
                        if is_existing:
                            st.success(f"✅ Found existing ISBN {isbn} for book ID '{book_id_reuse}'")
                            st.info(f"📖 Status: {assignment.status.replace('_', ' ').title()}")
                        else:
                            st.success(f"✅ Assigned new ISBN {isbn} for book ID '{book_id_reuse}'")
                        st.balloons()
                    else:
                        st.error("❌ Failed to get or assign ISBN. No available ISBNs found.")
                else:
                    st.error("❌ Please fill in all required fields (marked with *)")
    
    with tab3:
        st.subheader("Assign Specific ISBN")
        st.warning("⚠️ Use this carefully - only assign ISBNs you own and that aren't already in use.")
        
        with st.form("assign_specific_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                specific_isbn = st.text_input("Specific ISBN*", key="specific_isbn", help="Enter the exact 13-digit ISBN")
                book_title_specific = st.text_input("Book Title*", key="specific_title")
                book_id_specific = st.text_input("Book ID*", key="specific_book_id")
                scheduled_date_specific = st.date_input("Scheduled Date*", value=datetime.now().date(), key="specific_date")
            
            with col2:
                imprint_specific = st.text_input("Imprint", key="specific_imprint")
                publisher_specific = st.text_input("Publisher", key="specific_publisher")
                format_type_specific = st.selectbox("Format", ["paperback", "hardcover", "ebook"], key="specific_format")
                priority_specific = st.selectbox("Priority", [1, 2, 3], format_func=lambda x: "High" if x == 1 else "Medium" if x == 2 else "Low", key="specific_priority")
                notes_specific = st.text_area("Notes", key="specific_notes")
            
            submitted_specific = st.form_submit_button("🎯 Assign Specific ISBN")
            
            if submitted_specific:
                if specific_isbn and book_title_specific and book_id_specific:
                    # Validate ISBN format
                    if len(specific_isbn) != 13 or not specific_isbn.isdigit():
                        st.error("❌ ISBN must be exactly 13 digits")
                    else:
                        success = scheduler.assign_specific_isbn(
                            isbn=specific_isbn,
                            book_title=book_title_specific,
                            book_id=book_id_specific,
                            scheduled_date=scheduled_date_specific.strftime('%Y-%m-%d'),
                            imprint=imprint_specific,
                            publisher=publisher_specific,
                            format=format_type_specific,
                            priority=priority_specific,
                            notes=notes_specific
                        )
                        if success:
                            st.success(f"✅ Successfully assigned specific ISBN {specific_isbn} to '{book_title_specific}'")
                            st.balloons()
                        else:
                            st.error("❌ Failed to assign specific ISBN. It may already be assigned to a different book.")
                else:
                    st.error("❌ Please fill in all required fields (marked with *)")

def render_view_assignments(scheduler: ISBNScheduler):
    """Render assignments view and management"""
    st.header("📋 View & Manage Assignments")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All"] + [status.value.replace('_', ' ').title() for status in ISBNStatus])
    with col2:
        date_range = st.date_input("Date Range", value=[datetime.now().date() - timedelta(days=30), datetime.now().date() + timedelta(days=90)])
    with col3:
        search_term = st.text_input("Search", help="Search by title, ISBN, or book ID")
    
    if status_filter == "All":
        assignments = list(scheduler.assignments.values())
    else:
        status_enum = next(s for s in ISBNStatus if s.value.replace('_', ' ').title() == status_filter)
        assignments = scheduler.get_assignments_by_status(status_enum)
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        assignments = [a for a in assignments if start_date.strftime('%Y-%m-%d') <= a.scheduled_date <= end_date.strftime('%Y-%m-%d')]
    
    if search_term:
        search_lower = search_term.lower()
        assignments = [a for a in assignments if (search_lower in a.book_title.lower() or search_lower in a.isbn.lower() or search_lower in a.book_id.lower())]
    
    if assignments:
        st.write(f"Found {len(assignments)} assignments")
        assignment_data = []
        for assignment in assignments:
            assignment_data.append({
                "ISBN": assignment.isbn,
                "Title": assignment.book_title,
                "Book ID": assignment.book_id,
                "Scheduled Date": assignment.scheduled_date,
                "Status": assignment.status.replace('_', ' ').title(),
                "Imprint": assignment.imprint,
                "Publisher": assignment.publisher,
                "Format": assignment.format,
                "Priority": "High" if assignment.priority == 1 else "Medium" if assignment.priority == 2 else "Low",
                "Assigned Date": assignment.assigned_date or "Not assigned",
                "Notes": assignment.notes
            })
        
        df = pd.DataFrame(assignment_data)
        st.dataframe(df, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_isbn = st.selectbox("Select ISBN for action:", [""] + [a.isbn for a in assignments])
        with col2:
            if st.button("✅ Assign Now") and selected_isbn:
                if scheduler.assign_isbn_now(selected_isbn):
                    st.success(f"ISBN {selected_isbn} assigned successfully!")
                    st.rerun()
                else:
                    st.error("Failed to assign ISBN")
        with col3:
            if st.button("🔒 Reserve") and selected_isbn:
                reason = st.text_input("Reservation reason:")
                if reason and scheduler.reserve_isbn(selected_isbn, reason):
                    st.success(f"ISBN {selected_isbn} reserved!")
                    st.rerun()
    else:
        st.info("No assignments found matching the current filters")

def render_manage_blocks(scheduler: ISBNScheduler):
    """Render ISBN block management"""
    st.header("🏷️ Manage ISBN Blocks")
    
    st.subheader("➕ Add New ISBN Block")
    with st.form("add_block_form"):
        col1, col2 = st.columns(2)
        with col1:
            prefix = st.text_input("ISBN Prefix*", value="978")
            publisher_code = st.text_input("Publisher Code*")
            imprint_code = st.text_input("Imprint Code")
        with col2:
            start_number = st.number_input("Start Number*", min_value=1, value=1)
            end_number = st.number_input("End Number*", min_value=1, value=1000)
        
        submitted = st.form_submit_button("➕ Add Block")
        
        if submitted:
            if prefix and publisher_code and end_number > start_number:
                block_id = scheduler.add_isbn_block(
                    prefix=prefix,
                    start_number=start_number,
                    end_number=end_number,
                    publisher_code=publisher_code,
                    imprint_code=imprint_code
                )
                if block_id:
                    st.success(f"✅ Added ISBN block: {block_id}")
                    st.rerun()
                else:
                    st.error("❌ Failed to add ISBN block")
            else:
                st.error("❌ Please fill in all required fields")
    
    st.subheader("📋 Existing ISBN Blocks")
    if scheduler.isbn_blocks:
        blocks_data = []
        for block_id, block in scheduler.isbn_blocks.items():
            available = block.total_count - block.used_count - block.reserved_count
            utilization = (block.used_count + block.reserved_count) / block.total_count * 100
            blocks_data.append({
                "Block ID": block_id,
                "Prefix": block.prefix,
                "Publisher Code": block.publisher_code,
                "Imprint Code": block.imprint_code,
                "Range": f"{block.start_number:,} - {block.end_number:,}",
                "Total": f"{block.total_count:,}",
                "Used": f"{block.used_count:,}",
                "Reserved": f"{block.reserved_count:,}",
                "Available": f"{available:,}",
                "Utilization %": f"{utilization:.1f}%"
            })
        st.dataframe(pd.DataFrame(blocks_data), use_container_width=True)
    else:
        st.info("No ISBN blocks configured. Add a block to get started.")

def render_reports(scheduler: ISBNScheduler):
    """Render reports and analytics"""
    st.header("📈 Reports & Analytics")
    
    report = scheduler.get_isbn_availability_report()
    if not report:
        st.error("Unable to generate reports")
        return
    
    st.subheader("📊 Summary Report")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total ISBN Blocks", report.get('total_blocks', 0))
        st.metric("Total ISBNs", f"{report.get('total_isbns', 0):,}")
        st.metric("Available ISBNs", f"{report.get('available_isbns', 0):,}")
    with col2:
        st.metric("Used ISBNs", f"{report.get('used_isbns', 0):,}")
        st.metric("Reserved ISBNs", f"{report.get('reserved_isbns', 0):,}")
        total = report.get('total_isbns', 1)
        used = report.get('used_isbns', 0) + report.get('reserved_isbns', 0)
        utilization = (used / total * 100) if total > 0 else 0
        st.metric("Overall Utilization", f"{utilization:.1f}%")
    
    st.subheader("📊 ISBN Block Utilization")
    blocks_detail = report.get('blocks_detail', [])
    if blocks_detail:
        blocks_df = pd.DataFrame(blocks_detail)
        st.bar_chart(blocks_df.set_index('block_id')['utilization_percent'], height=300)
        
        with st.expander("📋 Detailed Block Information"):
            st.dataframe(blocks_df, use_container_width=True)

def render_import_schedule(scheduler: ISBNScheduler):
    """Render schedule import interface"""
    st.header("📤 Import Publishing Schedule")
    st.markdown("Import book schedules from CSV or JSON files with optional manual ISBN assignments")
    
    # Create tabs for different operations
    tab1, tab2, tab3 = st.tabs(["📤 Import Schedule", "📝 Export Template", "📋 Format Guide"])
    
    with tab1:
        st.subheader("Import Schedule File")
        st.info("💡 You can include an 'isbn' column in your file to manually assign specific ISBNs to books. Leave it empty for auto-assignment.")
        
        uploaded_file = st.file_uploader(
            "Choose schedule file", 
            type=['csv', 'json'],
            help="Upload a CSV or JSON file with your book schedule"
        )
        
        if uploaded_file is not None:
            # Show file preview
            st.subheader("📋 File Preview")
            
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    # Check for ISBN column
                    has_isbn_column = 'isbn' in df.columns
                    manual_isbns = df['isbn'].notna().sum() if has_isbn_column else 0
                    
                    st.write(f"📊 **File Statistics:**")
                    st.write(f"- Total books: {len(df)}")
                    st.write(f"- Manual ISBNs: {manual_isbns}")
                    st.write(f"- Auto-assign: {len(df) - manual_isbns}")
                    
                elif uploaded_file.name.endswith('.json'):
                    import json
                    uploaded_file.seek(0)  # Reset file pointer
                    data = json.load(uploaded_file)
                    
                    if isinstance(data, list):
                        books = data
                    else:
                        books = [data]
                    
                    st.json(books[:3])  # Show first 3 books
                    
                    manual_isbns = sum(1 for book in books if book.get('isbn', '').strip())
                    
                    st.write(f"📊 **File Statistics:**")
                    st.write(f"- Total books: {len(books)}")
                    st.write(f"- Manual ISBNs: {manual_isbns}")
                    st.write(f"- Auto-assign: {len(books) - manual_isbns}")
                
                # Import button
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("🚀 Import Schedule", type="primary"):
                        # Save uploaded file temporarily
                        import tempfile
                        with tempfile.NamedTemporaryFile(mode='wb', suffix=f".{uploaded_file.name.split('.')[-1]}", delete=False) as f:
                            f.write(uploaded_file.getvalue())
                            temp_file = f.name
                        
                        try:
                            # Import the schedule
                            if uploaded_file.name.endswith('.csv'):
                                results = scheduler.import_schedule_from_csv(temp_file)
                            else:
                                results = scheduler.import_schedule_from_json(temp_file)
                            
                            # Display results
                            if results['processed'] > 0:
                                st.success(f"🎉 Successfully imported {results['processed']} book assignments!")
                                
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Processed", results['processed'])
                                with col2:
                                    st.metric("Manual ISBNs", results['assigned_manual'])
                                with col3:
                                    st.metric("Auto ISBNs", results['assigned_auto'])
                                with col4:
                                    st.metric("Updated", results['updated'])
                                
                                if results['errors']:
                                    st.warning(f"⚠️ {len(results['errors'])} errors occurred during import")
                                    with st.expander("View Error Details"):
                                        for error in results['errors']:
                                            st.error(error)
                                
                                st.balloons()
                            else:
                                st.error("❌ No books were successfully imported")
                                if results['errors']:
                                    st.write("**Errors:**")
                                    for error in results['errors']:
                                        st.error(error)
                        
                        finally:
                            # Clean up temp file
                            import os
                            os.unlink(temp_file)
                
                with col2:
                    st.info("💡 **Tip:** Manual ISBNs must be exactly 13 digits. Leave the ISBN column empty for auto-assignment.")
                
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
    
    with tab2:
        st.subheader("Export Schedule Template")
        st.markdown("Download a template file to fill in with your book information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📄 CSV Template**")
            st.markdown("Perfect for Excel or Google Sheets")
            if st.button("📥 Download CSV Template"):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                    success = scheduler.export_schedule_template_csv(f.name)
                    if success:
                        with open(f.name, 'r') as template_file:
                            st.download_button(
                                label="💾 Save CSV Template",
                                data=template_file.read(),
                                file_name="isbn_schedule_template.csv",
                                mime="text/csv"
                            )
                        os.unlink(f.name)
        
        with col2:
            st.markdown("**📄 JSON Template**")
            st.markdown("Perfect for programmatic use")
            if st.button("📥 Download JSON Template"):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    success = scheduler.export_schedule_template_json(f.name)
                    if success:
                        with open(f.name, 'r') as template_file:
                            st.download_button(
                                label="💾 Save JSON Template",
                                data=template_file.read(),
                                file_name="isbn_schedule_template.json",
                                mime="application/json"
                            )
                        os.unlink(f.name)
    
    with tab3:
        st.subheader("📋 File Format Guide")
        
        st.markdown("### Required Fields")
        st.markdown("""
        - **title**: Book title
        - **book_id**: Unique identifier for the book
        - **scheduled_date**: Publication date (YYYY-MM-DD format)
        """)
        
        st.markdown("### Optional Fields")
        st.markdown("""
        - **isbn**: Manual ISBN assignment (13 digits) - leave empty for auto-assignment
        - **imprint**: Publishing imprint name
        - **publisher**: Publisher name
        - **format**: Book format (paperback, hardcover, ebook)
        - **priority**: Priority level (1=High, 2=Medium, 3=Low)
        - **notes**: Additional notes
        """)
        
        st.markdown("### CSV Example")
        st.code("""
title,book_id,scheduled_date,isbn,imprint,publisher,format,priority,notes
"My Great Book",book_001,2024-12-01,9781234567890,My Imprint,My Publisher,paperback,1,Manual ISBN
"Another Book",book_002,2024-12-15,,My Imprint,My Publisher,hardcover,2,Auto-assign ISBN
        """, language="csv")
        
        st.markdown("### JSON Example")
        st.code("""
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
        """, language="json")
        
        st.markdown("### 💡 Pro Tips")
        st.markdown("""
        - **Manual ISBNs**: Include specific ISBNs you want to assign to particular books
        - **Auto-assignment**: Leave ISBN field empty to automatically assign from available blocks
        - **Rebuilds**: Use the same book_id to update existing assignments
        - **Validation**: The system validates ISBN format and prevents duplicates
        - **Error handling**: Import continues even if some rows fail - check the error report
        """)

if __name__ == "__main__":
    main()