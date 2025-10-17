#!/usr/bin/env python3
"""
Rights Management Main Dashboard

Central hub for managing international rights, contracts, and offering sheets.
"""


import streamlit as st
import pandas as pd
import json
from pathlib import Path
import logging
from datetime import datetime
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




# Import rights management modules
try:
    from codexes.modules.rights_management.crud_operations import RightsManager
    from codexes.modules.rights_management.offering_sheet_generator import RightsOfferingSheetGenerator
except ImportError:
    sys.path.append('src')

logger = logging.getLogger(__name__)

def main():
    """Main rights management dashboard."""
    st.set_page_config(

        page_title="Rights Management - Codexes Factory",
        page_icon="📋",
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




    st.title("📋 Rights Management Dashboard")

    st.markdown("Manage international rights, contracts, and generate offering sheets")

    # Initialize rights manager
    if 'rights_manager' not in st.session_state:

        st.session_state.rights_manager = RightsManager()

    rights_manager = st.session_state.rights_manager

    # Main navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard",
        "📚 Works",
        "🏢 Publishers",
        "📋 Contracts",
        "📄 Offering Sheets"
    ])

    with tab1:
        show_dashboard(rights_manager)

    with tab2:
        show_works_management(rights_manager)

    with tab3:
        show_publishers_management(rights_manager)

    with tab4:
        show_contracts_management(rights_manager)

    with tab5:
        show_offering_sheets(rights_manager)

def show_dashboard(rights_manager):
    """Show main dashboard with overview statistics."""
    st.header("Rights Management Overview")

    try:
        # Get summary statistics
        revenue_summary = rights_manager.get_rights_revenue_summary()
        totals = revenue_summary.get('totals', {})

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Contracts", totals.get('total_contracts', 0))

        with col2:
            total_revenue = totals.get('total_revenue', 0) or 0
            st.metric("Total Revenue", f"${total_revenue:,.2f}")

        with col3:
            total_due = totals.get('total_due_authors', 0) or 0
            st.metric("Due to Authors", f"${total_due:,.2f}")

        with col4:
            works = rights_manager.db.get_works()
            st.metric("Total Works", len(works))

        # Revenue by territory chart
        st.subheader("Revenue by Territory")
        by_territory = revenue_summary.get('by_territory', [])
        if by_territory:
            territory_df = pd.DataFrame(by_territory)
            territory_df['revenue'] = territory_df['revenue'].fillna(0)
            st.bar_chart(territory_df.set_index('territory_name')['revenue'])
        else:
            st.info("No revenue data available yet.")

        # Recent activity
        st.subheader("Recent Contracts")
        contracts = rights_manager.db.get_rights_contracts()
        if contracts:
            recent_contracts = contracts[:5]  # Show last 5
            contract_data = []
            for contract in recent_contracts:
                contract_data.append({
                    'Title': contract['title'],
                    'Publisher': contract['organization_name'],
                    'Territory': contract['territory_name'],
                    'Start Date': contract['contract_start_date'],
                    'Revenue': f"${contract['net_compensation'] or 0:,.2f}"
                })
            st.dataframe(pd.DataFrame(contract_data), use_container_width=True)
        else:
            st.info("No contracts found. Add your first contract in the Contracts tab.")

    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
        logger.error(f"Dashboard error: {e}")

def show_works_management(rights_manager):
    """Show works management interface."""
    st.header("Works Management")

    # Add new work section
    with st.expander("➕ Add New Work"):
        with st.form("add_work_form"):
            col1, col2 = st.columns(2)

            with col1:
                title = st.text_input("Title*", help="Book title")
                author = st.text_input("Author*", help="Author name")
                isbn = st.text_input("ISBN", help="Optional ISBN")
                genre = st.text_input("Genre", help="Book genre")

            with col2:
                subtitle = st.text_input("Subtitle", help="Optional subtitle")
                imprint = st.text_input("Imprint", help="Publishing imprint")
                pages = st.number_input("Page Count", min_value=0, value=200)
                pub_date = st.date_input("Publication Date", value=datetime.now().date())

            description = st.text_area("Description", help="Book description")

            if st.form_submit_button("Add Work"):
                if title and author:
                    try:
                        work_id = rights_manager.db.add_work(
                            title=title,
                            author_name=author,
                            isbn=isbn if isbn else None,
                            subtitle=subtitle if subtitle else None,
                            genre=genre if genre else None,
                            imprint=imprint if imprint else None,
                            page_count=pages if pages > 0 else None,
                            publication_date=pub_date.isoformat(),
                            description=description if description else None
                        )
                        st.success(f"Added work: {title} (ID: {work_id})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding work: {e}")
                else:
                    st.error("Title and Author are required")

    # Import from CSV
    with st.expander("📂 Import Existing Rights Data"):
        uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
        if uploaded_file:
            try:
                # Save uploaded file temporarily
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    tmp_path = tmp.name

                if st.button("Import Data"):
                    works_imported, contracts_imported, errors = rights_manager.import_existing_rights_data(tmp_path)

                    st.success(f"Imported {works_imported} works and {contracts_imported} contracts")

                    if errors:
                        st.warning("Some errors occurred during import:")
                        for error in errors[:10]:  # Show first 10 errors
                            st.text(error)

                    st.rerun()

            except Exception as e:
                st.error(f"Error processing file: {e}")

    # Search and display works
    st.subheader("Existing Works")

    search_term = st.text_input("🔍 Search works", placeholder="Search by title, author, or ISBN")

    try:
        if search_term:
            works = rights_manager.db.search_works(search_term)
        else:
            works = rights_manager.db.get_works(limit=50)

        if works:
            # Display works in a more compact format
            for work in works:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        st.write(f"**{work['title']}**")
                        if work.get('subtitle'):
                            st.write(f"*{work['subtitle']}*")
                        st.write(f"by {work['author_name']}")

                    with col2:
                        if work.get('isbn'):
                            st.write(f"ISBN: {work['isbn']}")
                        if work.get('genre'):
                            st.write(f"Genre: {work['genre']}")
                        if work.get('imprint'):
                            st.write(f"Imprint: {work['imprint']}")

                    with col3:
                        if st.button("View Rights", key=f"view_rights_{work['id']}"):
                            st.session_state.selected_work_id = work['id']
                            st.rerun()

                    st.divider()

        else:
            st.info("No works found. Add your first work using the form above.")

    except Exception as e:
        st.error(f"Error loading works: {e}")
        logger.error(f"Works loading error: {e}")

    # Show selected work details
    if hasattr(st.session_state, 'selected_work_id'):
        show_work_rights_details(rights_manager, st.session_state.selected_work_id)

def show_work_rights_details(rights_manager, work_id):
    """Show detailed rights information for a specific work."""
    try:
        rights_summary = rights_manager.get_work_rights_summary(work_id)
        if not rights_summary:
            st.error("Work not found")
            return

        work = rights_summary['work']
        st.subheader(f"Rights Details: {work['title']}")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Work Information**")
            st.write(f"Title: {work['title']}")
            st.write(f"Author: {work['author_name']}")
            if work.get('isbn'):
                st.write(f"ISBN: {work['isbn']}")
            if work.get('genre'):
                st.write(f"Genre: {work['genre']}")

        with col2:
            st.write("**Rights Summary**")
            st.write(f"Total Revenue: ${rights_summary['total_revenue']:,.2f}")
            st.write(f"Rights Sold: {rights_summary['rights_sold_count']}")
            st.write(f"Due to Author: ${rights_summary['total_due_author']:,.2f}")

        # Territories sold
        if rights_summary['territories_sold']:
            st.write("**Territories Licensed**")
            for territory, details in rights_summary['territories_sold'].items():
                st.write(f"• {territory}: {details['publisher']} (${details['revenue']:,.2f})")

        # Available territories
        available = rights_manager.get_available_territories_for_work(work_id)
        if available:
            st.write(f"**Available Territories ({len(available)})**")
            territory_names = [t['territory_name'] for t in available[:10]]
            st.write(", ".join(territory_names))
            if len(available) > 10:
                st.write(f"... and {len(available) - 10} more")

    except Exception as e:
        st.error(f"Error loading work details: {e}")

def show_publishers_management(rights_manager):
    """Show publishers management interface."""
    st.header("Publishers Management")

    # Add new publisher
    with st.expander("➕ Add New Publisher"):
        with st.form("add_publisher_form"):
            col1, col2 = st.columns(2)

            with col1:
                org_name = st.text_input("Organization Name*")
                contact_name = st.text_input("Contact Name")
                contact_email = st.text_input("Contact Email")

            with col2:
                country = st.text_input("Country")
                primary_language = st.text_input("Primary Language")
                contact_phone = st.text_input("Contact Phone")

            address = st.text_area("Address")
            specialties = st.text_input("Specialties", help="Comma-separated genres/specialties")
            notes = st.text_area("Notes")

            if st.form_submit_button("Add Publisher"):
                if org_name:
                    try:
                        specialties_list = [s.strip() for s in specialties.split(',')] if specialties else []
                        publisher_id = rights_manager.db.add_publisher(
                            organization_name=org_name,
                            contact_name=contact_name if contact_name else None,
                            contact_email=contact_email if contact_email else None,
                            contact_phone=contact_phone if contact_phone else None,
                            address=address if address else None,
                            country=country if country else None,
                            primary_language=primary_language if primary_language else None,
                            specialties=specialties_list,
                            notes=notes if notes else None
                        )
                        st.success(f"Added publisher: {org_name} (ID: {publisher_id})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding publisher: {e}")
                else:
                    st.error("Organization name is required")

    # Display existing publishers
    st.subheader("Existing Publishers")

    try:
        publishers = rights_manager.db.get_publishers()
        if publishers:
            publisher_data = []
            for pub in publishers:
                publisher_data.append({
                    'Organization': pub['organization_name'],
                    'Contact': pub.get('contact_name', 'N/A'),
                    'Email': pub.get('contact_email', 'N/A'),
                    'Country': pub.get('country', 'N/A'),
                    'Language': pub.get('primary_language', 'N/A')
                })
            st.dataframe(pd.DataFrame(publisher_data), use_container_width=True)
        else:
            st.info("No publishers found. Add your first publisher using the form above.")

    except Exception as e:
        st.error(f"Error loading publishers: {e}")

    # Add divider between publishers and territories
    st.divider()

    # Territories Management Section
    st.header("Territories Management")

    # Add new territory
    with st.expander("➕ Add New Territory"):
        with st.form("add_territory_form"):
            col1, col2 = st.columns(2)

            with col1:
                territory_name = st.text_input("Territory Name*", help="e.g., 'South Africa', 'Argentina'")
                territory_code = st.text_input("Territory Code", help="2-letter code, e.g., 'ZA', 'AR'")
                primary_language = st.text_input("Primary Language", help="e.g., 'English', 'Spanish'")

            with col2:
                currency = st.text_input("Currency", help="e.g., 'USD', 'EUR', 'ZAR'")
                market_notes = st.text_area("Market Notes", help="Notes about this market")

            if st.form_submit_button("Add Territory"):
                if territory_name:
                    try:
                        # Add territory directly to database
                        conn = rights_manager.db.connect()
                        cursor = conn.cursor()

                        cursor.execute("""
                            INSERT INTO territories (territory_name, territory_code, primary_language, currency, market_notes)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            territory_name,
                            territory_code if territory_code else None,
                            primary_language if primary_language else None,
                            currency if currency else None,
                            market_notes if market_notes else None
                        ))

                        conn.commit()
                        st.success(f"Added territory: {territory_name}")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error adding territory: {e}")
                else:
                    st.error("Territory name is required")

    # Display existing territories
    st.subheader("Existing Territories")

    try:
        territories = rights_manager.db.get_territories()
        if territories:
            territory_data = []
            for terr in territories:
                territory_data.append({
                    'Territory': terr['territory_name'],
                    'Code': terr.get('territory_code', 'N/A'),
                    'Language': terr.get('primary_language', 'N/A'),
                    'Currency': terr.get('currency', 'N/A'),
                    'Notes': terr.get('market_notes', '')[:50] + '...' if terr.get('market_notes') and len(terr.get('market_notes', '')) > 50 else terr.get('market_notes', 'N/A')
                })
            st.dataframe(pd.DataFrame(territory_data), use_container_width=True)
            st.caption(f"Total: {len(territories)} territories")
        else:
            st.info("No territories found. Add your first territory using the form above.")

    except Exception as e:
        st.error(f"Error loading territories: {e}")

def show_contracts_management(rights_manager):
    """Show contracts management interface."""
    st.header("Contracts Management")

    # Add new contract
    with st.expander("➕ Add New Contract"):
        with st.form("add_contract_form"):
            # Get works and publishers for dropdowns
            works = rights_manager.db.get_works()
            publishers = rights_manager.db.get_publishers()
            territories = rights_manager.db.get_territories()

            if not works or not publishers or not territories:
                st.warning("You need at least one work, publisher, and territory to create a contract.")
                st.form_submit_button("Add Contract", disabled=True)
            else:
                col1, col2 = st.columns(2)

                with col1:
                    work_options = {f"{w['title']} - {w['author_name']}": w['id'] for w in works}
                    selected_work = st.selectbox("Work*", options=list(work_options.keys()))

                    publisher_options = {p['organization_name']: p['id'] for p in publishers}
                    selected_publisher = st.selectbox("Publisher*", options=list(publisher_options.keys()))

                    territory_options = {t['territory_name']: t['id'] for t in territories}
                    selected_territory = st.selectbox("Territory*", options=list(territory_options.keys()))

                with col2:
                    rights_type = st.selectbox("Rights Type*", [
                        "Translation", "Distribution", "Audio", "Digital", "Educational"
                    ])

                    target_language = st.text_input("Target Language")
                    exclusive = st.checkbox("Exclusive Rights", value=True)

                col3, col4 = st.columns(2)

                with col3:
                    start_date = st.date_input("Contract Start Date*", value=datetime.now().date())
                    end_date = st.date_input("Contract End Date*", value=datetime.now().date().replace(year=datetime.now().year + 7))

                with col4:
                    net_compensation = st.number_input("Net Compensation ($)", min_value=0.0, step=100.0)
                    author_share = st.number_input("Author Share (0.0-1.0)", min_value=0.0, max_value=1.0, value=0.5, step=0.05)

                contract_notes = st.text_area("Contract Notes")

                if st.form_submit_button("Add Contract"):
                    try:
                        work_id = work_options[selected_work]
                        publisher_id = publisher_options[selected_publisher]
                        territory_id = territory_options[selected_territory]

                        amount_due_author = net_compensation * author_share if net_compensation > 0 else 0

                        contract_id = rights_manager.db.add_rights_contract(
                            work_id=work_id,
                            publisher_id=publisher_id,
                            territory_id=territory_id,
                            rights_type=rights_type,
                            contract_start_date=start_date.isoformat(),
                            contract_end_date=end_date.isoformat(),
                            target_language=target_language if target_language else None,
                            exclusive=exclusive,
                            net_compensation=net_compensation if net_compensation > 0 else None,
                            author_share=author_share,
                            amount_due_author=amount_due_author if amount_due_author > 0 else None,
                            contract_notes=contract_notes if contract_notes else None
                        )
                        st.success(f"Added contract (ID: {contract_id})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding contract: {e}")

    # Display existing contracts
    st.subheader("Existing Contracts")

    try:
        contracts = rights_manager.db.get_rights_contracts()
        if contracts:
            contract_data = []
            for contract in contracts:
                contract_data.append({
                    'Title': contract['title'],
                    'Author': contract['author_name'],
                    'Publisher': contract['organization_name'],
                    'Territory': contract['territory_name'],
                    'Language': contract.get('target_language', 'N/A'),
                    'Start Date': contract['contract_start_date'],
                    'Revenue': f"${contract['net_compensation'] or 0:,.2f}",
                    'Due Author': f"${contract['amount_due_author'] or 0:,.2f}"
                })
            st.dataframe(pd.DataFrame(contract_data), use_container_width=True)
        else:
            st.info("No contracts found. Add your first contract using the form above.")

    except Exception as e:
        st.error(f"Error loading contracts: {e}")

def show_offering_sheets(rights_manager):
    """Show offering sheets generation interface."""
    st.header("Rights Offering Sheets")

    # Generate work-specific offering sheet
    st.subheader("Generate Work Offering Sheet")

    works = rights_manager.db.get_works()
    if works:
        work_options = {f"{w['title']} - {w['author_name']}": w['id'] for w in works}
        selected_work = st.selectbox("Select Work", options=list(work_options.keys()))

        col1, col2 = st.columns(2)
        with col1:
            asking_price = st.text_input("Asking Price", value="Negotiable")
            minimum_advance = st.text_input("Minimum Advance", value="Negotiable")

        with col2:
            output_dir = st.text_input("Output Directory", value="output/rights_sheets")

        if st.button("Generate Work Offering Sheet"):
            try:
                work_id = work_options[selected_work]
                generator = RightsOfferingSheetGenerator(rights_manager)

                result = generator.generate_work_offering_sheet(
                    work_id=work_id,
                    output_dir=output_dir,
                    asking_price=asking_price,
                    minimum_advance=minimum_advance
                )

                if result:
                    st.success(f"Generated offering sheet: {result}")
                    if Path(result).exists():
                        with open(result, 'rb') as f:
                            st.download_button(
                                label="Download Offering Sheet",
                                data=f.read(),
                                file_name=Path(result).name,
                                mime="application/pdf" if result.endswith('.pdf') else "text/plain"
                            )
                else:
                    st.error("Failed to generate offering sheet")

            except Exception as e:
                st.error(f"Error generating offering sheet: {e}")

    # Generate imprint offering sheet
    st.subheader("Generate Imprint Offering Sheet")

    imprint_file = st.file_uploader("Upload Imprint Configuration", type=['json'])
    if imprint_file:
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
                tmp.write(imprint_file.getbuffer())
                tmp_path = tmp.name

            output_dir_imprint = st.text_input("Output Directory", value="output/rights_sheets", key="imprint_output")

            if st.button("Generate Imprint Offering Sheet"):
                generator = RightsOfferingSheetGenerator(rights_manager)
                result = generator.generate_imprint_offering_sheet(tmp_path, output_dir_imprint)

                if result:
                    st.success(f"Generated imprint offering sheet: {result}")
                    if Path(result).exists():
                        with open(result, 'rb') as f:
                            st.download_button(
                                label="Download Imprint Offering Sheet",
                                data=f.read(),
                                file_name=Path(result).name,
                                mime="application/pdf" if result.endswith('.pdf') else "text/plain"
                            )
                else:
                    st.error("Failed to generate imprint offering sheet")

        except Exception as e:
            st.error(f"Error with imprint file: {e}")

if __name__ == "__main__":
    main()