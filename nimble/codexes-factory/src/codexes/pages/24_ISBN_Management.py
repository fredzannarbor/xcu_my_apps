"""
ISBN Management - Unified ISBN management for the Book Pipeline.

This page consolidates all ISBN functionality and integrates with the existing
ISBN database (data/isbn_database.json) with 1150+ records.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import logging
import sys


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


sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
    from shared.ui import render_unified_sidebar
except ImportError as e:
    import streamlit as st
    st.error(f"Failed to import shared authentication: {e}")
    st.error("Please ensure /Users/fred/xcu_my_apps/shared/auth is accessible")
    st.stop()




logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)




# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import ISBN integration
try:
    from src.codexes.modules.distribution.isbn_integration import get_isbn_integration
    from src.codexes.modules.distribution.isbn_database import ISBNStatus
except ImportError:
    from codexes.modules.distribution.isbn_integration import get_isbn_integration
    from codexes.modules.distribution.isbn_database import ISBNStatus

st.set_page_config(
    page_title="ISBN Management",
    page_icon="📖",
    layout="wide"
)

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
    """Main ISBN Management interface"""
    st.title("📖 ISBN Management")
    st.markdown("**Unified ISBN management using your existing database with 1150+ records**")
    
    # Initialize ISBN integration
    if 'isbn_integration' not in st.session_state:
        st.session_state.isbn_integration = get_isbn_integration()
    
    isbn_integration = st.session_state.isbn_integration
    
    # Get current statistics
    stats = isbn_integration.get_database_stats()
    
    # Display database overview
    st.subheader("📊 Database Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total ISBNs", f"{stats['total_isbns']:,}")
    with col2:
        st.metric("Available", f"{stats['available_count']:,}", 
                 help="ISBNs ready for assignment")
    with col3:
        st.metric("Assigned", f"{stats['assigned_count']:,}",
                 help="ISBNs assigned to books")
    with col4:
        st.metric("Published", f"{stats['published_count']:,}",
                 help="ISBNs for published books")
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Book Pipeline Integration", 
        "🔍 Search & Manage", 
        "📋 Browse Database",
        "📊 Reports",
        "⚙️ Tools"
    ])
    
    with tab1:
        render_pipeline_integration(isbn_integration)
    
    with tab2:
        render_search_manage(isbn_integration)
    
    with tab3:
        render_browse_database(isbn_integration)
    
    with tab4:
        render_reports(isbn_integration)
    
    with tab5:
        render_tools(isbn_integration)

def render_pipeline_integration(isbn_integration):
    """Render Book Pipeline integration interface"""
    st.header("🎯 Book Pipeline Integration")
    st.markdown("**This is the main interface for getting ISBNs during book production**")
    
    # Quick ISBN assignment for pipeline
    st.subheader("📚 Get ISBN for Book")
    
    with st.form("pipeline_isbn_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            book_id = st.text_input("Book ID*", help="Unique identifier for the book")
            book_title = st.text_input("Book Title*", help="Title of the book")
            publisher_id = st.selectbox("Publisher", ["nimble-books"], help="Publisher ID")
        
        with col2:
            manual_isbn = st.text_input("Manual ISBN (Optional)", 
                                       help="Leave empty for auto-assignment")
            st.markdown("**Assignment Mode:**")
            if manual_isbn:
                st.info("🎯 Manual assignment mode")
            else:
                st.info("🤖 Auto-assignment mode (or reuse existing)")
        
        submitted = st.form_submit_button("📖 Get ISBN", type="primary")
        
        if submitted:
            if book_id and book_title:
                # Get ISBN using integration
                result = isbn_integration.get_isbn_for_book(
                    book_id=book_id,
                    book_title=book_title,
                    publisher_id=publisher_id,
                    manual_isbn=manual_isbn.strip() if manual_isbn else None
                )
                
                if result['success']:
                    st.success(f"✅ {result['message']}")
                    
                    # Display ISBN details
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("ISBN", result['isbn'])
                    with col2:
                        st.metric("Source", result['source'].title())
                    with col3:
                        if result['source'] == 'existing':
                            st.info("♻️ Reused for rebuild")
                        elif result['source'] == 'manual':
                            st.info("🎯 Manual assignment")
                        else:
                            st.info("🤖 Auto-assigned")
                    
                    # Show how to use in pipeline
                    st.markdown("**📋 For Book Pipeline:**")
                    st.code(f'ISBN: {result["isbn"]}', language="text")
                    
                else:
                    st.error(f"❌ {result['message']}")
                    if result.get('error'):
                        st.error(f"Error: {result['error']}")
            else:
                st.error("❌ Please provide both Book ID and Title")
    
    # Quick lookup for existing books
    st.subheader("🔍 Quick Lookup")
    lookup_id = st.text_input("Enter Book ID to find its ISBN:")
    if lookup_id:
        existing_isbn = isbn_integration._find_existing_isbn(lookup_id)
        if existing_isbn:
            details = isbn_integration.get_isbn_details(existing_isbn)
            st.success(f"📖 Book '{lookup_id}' has ISBN: **{existing_isbn}**")
            if details:
                st.info(f"Title: {details['title']} | Status: {details['status']}")
        else:
            st.warning(f"❌ No ISBN found for book ID '{lookup_id}'")

def render_search_manage(isbn_integration):
    """Render search and management interface"""
    st.header("🔍 Search & Manage ISBNs")
    
    # Search interface
    search_query = st.text_input("🔍 Search ISBNs", 
                                help="Search by ISBN, title, or book ID")
    
    if search_query:
        results = isbn_integration.search_isbns(search_query)
        
        if results:
            st.write(f"Found {len(results)} results:")
            
            # Convert to DataFrame for display
            df = pd.DataFrame(results)
            
            # Display results
            selected_rows = st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "isbn": "ISBN",
                    "title": "Title",
                    "status": "Status",
                    "assigned_to": "Assigned To",
                    "assignment_date": "Assignment Date",
                    "publisher_id": "Publisher",
                    "format": "Format"
                }
            )
            
            # Management actions
            if len(results) > 0:
                st.subheader("📝 Management Actions")
                
                selected_isbn = st.selectbox("Select ISBN for action:", 
                                           [""] + [r['isbn'] for r in results])
                
                if selected_isbn:
                    details = isbn_integration.get_isbn_details(selected_isbn)
                    
                    if details:
                        # Show current details
                        st.markdown("**Current Details:**")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Status:** {details['status']}")
                            st.write(f"**Title:** {details['title']}")
                        with col2:
                            st.write(f"**Assigned To:** {details['assigned_to']}")
                            st.write(f"**Format:** {details['format']}")
                        with col3:
                            st.write(f"**Publisher:** {details['publisher_id']}")
                            st.write(f"**Assignment Date:** {details['assignment_date']}")
                        
                        # Action buttons
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("🔓 Release ISBN"):
                                if isbn_integration.release_isbn(selected_isbn):
                                    st.success(f"✅ Released ISBN {selected_isbn}")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to release ISBN")
                        
                        with col2:
                            if st.button("📚 Mark as Published"):
                                if isbn_integration.mark_as_published(selected_isbn):
                                    st.success(f"✅ Marked ISBN {selected_isbn} as published")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to mark as published")
                        
                        with col3:
                            st.button("📋 View Details", disabled=True, 
                                    help="Details shown above")
        else:
            st.info(f"No results found for '{search_query}'")

def render_browse_database(isbn_integration):
    """Render database browsing interface"""
    st.header("📋 Browse ISBN Database")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("Filter by Status", 
                                   ["All", "available", "assigned", "published", "publicly_assigned"])
    
    with col2:
        publisher_filter = st.selectbox("Filter by Publisher", 
                                      ["All", "nimble-books"])
    
    with col3:
        limit = st.selectbox("Show", [50, 100, 200, 500], index=1)
    
    # Get filtered data
    all_isbns = []
    count = 0
    
    for isbn, isbn_obj in isbn_integration.isbn_db.isbns.items():
        if count >= limit:
            break
            
        # Apply filters
        if status_filter != "All" and isbn_obj.status.value != status_filter:
            continue
        if publisher_filter != "All" and isbn_obj.publisher_id != publisher_filter:
            continue
        
        all_isbns.append({
            'ISBN': isbn,
            'Title': isbn_obj.title or '',
            'Status': isbn_obj.status.value,
            'Assigned To': isbn_obj.assigned_to or '',
            'Assignment Date': isbn_obj.assignment_date or '',
            'Publisher': isbn_obj.publisher_id,
            'Format': isbn_obj.format or ''
        })
        count += 1
    
    if all_isbns:
        st.write(f"Showing {len(all_isbns)} ISBNs (limited to {limit})")
        df = pd.DataFrame(all_isbns)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No ISBNs match the current filters")

def render_reports(isbn_integration):
    """Render reports interface"""
    st.header("📊 Reports & Analytics")
    
    stats = isbn_integration.get_database_stats()
    
    # Status distribution
    st.subheader("📈 Status Distribution")
    status_data = {
        'Available': stats['available_count'],
        'Assigned': stats['assigned_count'], 
        'Published': stats['published_count'],
        'Publicly Assigned': stats.get('publicly_assigned_count', 0)
    }
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        for status, count in status_data.items():
            percentage = (count / stats['total_isbns'] * 100) if stats['total_isbns'] > 0 else 0
            st.metric(status, f"{count:,}", f"{percentage:.1f}%")
    
    with col2:
        # Create chart data
        chart_data = pd.DataFrame({
            'Status': list(status_data.keys()),
            'Count': list(status_data.values())
        })
        st.bar_chart(chart_data.set_index('Status'))
    
    # Publisher breakdown
    st.subheader("📚 Publisher Breakdown")
    publisher_stats = {}
    for isbn_obj in isbn_integration.isbn_db.isbns.values():
        pub = isbn_obj.publisher_id
        if pub not in publisher_stats:
            publisher_stats[pub] = {'total': 0, 'available': 0, 'assigned': 0}
        publisher_stats[pub]['total'] += 1
        if isbn_obj.status == ISBNStatus.AVAILABLE:
            publisher_stats[pub]['available'] += 1
        elif isbn_obj.status == ISBNStatus.ASSIGNED:
            publisher_stats[pub]['assigned'] += 1
    
    pub_data = []
    for pub, counts in publisher_stats.items():
        pub_data.append({
            'Publisher': pub,
            'Total': counts['total'],
            'Available': counts['available'],
            'Assigned': counts['assigned'],
            'Utilization %': round((counts['assigned'] / counts['total'] * 100), 1) if counts['total'] > 0 else 0
        })
    
    if pub_data:
        st.dataframe(pd.DataFrame(pub_data), use_container_width=True)

def render_tools(isbn_integration):
    """Render tools and utilities"""
    st.header("⚙️ Tools & Utilities")
    
    # Database refresh
    st.subheader("🔄 Database Management")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Database"):
            # Reload the database
            isbn_integration.isbn_db.load_database()
            st.success("✅ Database refreshed")
            st.rerun()
    
    with col2:
        if st.button("💾 Save Database"):
            isbn_integration.isbn_db.save_database()
            st.success("✅ Database saved")
    
    # Integration with other tools
    st.subheader("🔗 Integration Links")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📚 Book Pipeline**")
        st.markdown("Use the 'Book Pipeline Integration' tab above for production")
        
    with col2:
        st.markdown("**📋 Schedule Manager**")
        if st.button("Open Schedule Manager"):
            st.switch_page("pages/25_Schedule_ISBN_Manager.py")
    
    with col3:
        st.markdown("**📊 Database Info**")
        st.write(f"Database path: `{isbn_integration.isbn_db.storage_path}`")
        st.write(f"Last loaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()