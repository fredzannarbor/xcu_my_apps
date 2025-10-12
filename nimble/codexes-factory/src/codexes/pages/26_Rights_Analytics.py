#!/usr/bin/env python3
"""
Rights Tracking and Analytics

Comprehensive rights management system integrating:
- Books in Print tracking via FullMetadataEnhanced
- Rights contracts by territory/language with grant/expiry dates
- Rights revenue tracking
- Author compensation tracking
- Offering sheet generation
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from pathlib import Path
import json
import sys

sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Import rights management modules
try:
    from codexes.modules.rights_management.crud_operations import RightsManager
    from codexes.modules.rights_management.offering_sheet_generator import RightsOfferingSheetGenerator
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.RightsRevenueAuthorReports import RightsRevenues
except ImportError:
    import sys
    sys.path.append('src')
    from codexes.modules.rights_management.crud_operations import RightsManager
    from codexes.modules.rights_management.offering_sheet_generator import RightsOfferingSheetGenerator
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.FinancialReportingObjects import FinancialReportingObjects
    from codexes.modules.finance.leo_bloom.FinancialReportingObjects.RightsRevenueAuthorReports import RightsRevenues

def main():
    """Rights tracking and analytics dashboard."""
    st.set_page_config(
        page_title="Rights Tracking & Analytics - Codexes Factory",
        page_icon="📈",
        layout="wide"
    )

    st.title("📈 Rights Tracking and Analytics")
    st.markdown("Comprehensive rights management for international publishing")

    # Initialize managers
    if 'rights_manager' not in st.session_state:
        st.session_state.rights_manager = RightsManager()

    if 'fro_instance' not in st.session_state:
        try:
            st.session_state.fro_instance = FinancialReportingObjects()
        except Exception as e:
            st.warning(f"Could not initialize Financial Reporting Objects: {e}")
            st.session_state.fro_instance = None

    rights_manager = st.session_state.rights_manager

    # Navigation tabs
    tabs = st.tabs([
        "📚 Rights Sold/Available",
        "📋 Rights Contracts",
        "🗺️ Rights Matrix",
        "💰 Revenue Tracking",
        "👤 Author Payments",
        "📊 Analytics",
        "🎯 Offerings & Sales"
    ])

    with tabs[0]:
        show_rights_sold_available(rights_manager)

    with tabs[1]:
        show_rights_contracts(rights_manager)

    with tabs[2]:
        show_rights_matrix(rights_manager)

    with tabs[3]:
        show_revenue_tracking(rights_manager)

    with tabs[4]:
        show_author_payments()

    with tabs[5]:
        show_analytics(rights_manager)

    with tabs[6]:
        show_offerings_and_sales(rights_manager)

def show_rights_sold_available(rights_manager):
    """Display books in print with rights sold/available by territory."""
    st.header("📚 Rights Sold/Available")
    st.markdown("Track which rights are sold vs available for each title")

    try:
        fro = st.session_state.fro_instance
        if fro is None:
            st.error("Financial Reporting Objects not available. Please check configuration.")
            return

        # Load FullMetadataEnhanced
        with st.spinner("Loading books in print..."):
            fme_df = fro.full_metadata_enhanced_df

        if fme_df is None or fme_df.empty:
            st.warning("No books found in Full Metadata Enhanced.")
            return

        # Get all contracts to see which territories have been sold
        contracts = rights_manager.db.get_rights_contracts()
        contracts_df = pd.DataFrame(contracts) if contracts else pd.DataFrame()

        # Get all available territories
        territories = rights_manager.db.get_territories()
        territories_list = [t['territory_name'] for t in territories]

        # Build rights status for each book
        rights_data = []
        for idx, book in fme_df.iterrows():
            isbn = str(book.get('ISBN', '')).strip()
            title = book.get('Title', '')

            # Find contracts for this ISBN
            if not contracts_df.empty and isbn:
                book_contracts = contracts_df[contracts_df['isbn'] == isbn] if 'isbn' in contracts_df.columns else pd.DataFrame()
                if book_contracts.empty:
                    # Try matching by title if ISBN doesn't work
                    book_contracts = contracts_df[contracts_df['title'] == title]
            else:
                book_contracts = pd.DataFrame()

            # Determine rights granted to Nimble Books
            author_name = book.get('Author Name', '')
            # Simple heuristic - can be made more sophisticated
            if 'Zimmerman' in str(author_name) or 'Nimble' in str(author_name):
                rights_source = 'Nimble Books'
            elif pd.isna(author_name) or author_name == '':
                rights_source = 'Public Domain'
            else:
                rights_source = author_name

            # Count territories sold
            territories_sold = []
            if not book_contracts.empty:
                territories_sold = book_contracts['territory_name'].dropna().unique().tolist()

            rights_data.append({
                'ISBN': isbn,
                'Title': title,
                'Author Name': author_name,
                'Rights Granted By': rights_source,
                'Royaltied': book.get('royaltied', False),
                'Territories Sold': len(territories_sold),
                'Territories Available': len(territories_list) - len(territories_sold),
                'Sold To': ', '.join(territories_sold) if territories_sold else 'None',
                'LTD Sales': book.get('LTD Net Qty', 0),
                'Imprint': book.get('Imprint', '')
            })

        rights_status_df = pd.DataFrame(rights_data)

        # Display summary metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Titles", len(rights_status_df))
        with col2:
            titles_with_sales = len(rights_status_df[rights_status_df['Territories Sold'] > 0])
            st.metric("Titles with Rights Sold", titles_with_sales)
        with col3:
            royaltied_count = rights_status_df['Royaltied'].sum()
            st.metric("Royaltied Titles", royaltied_count)
        with col4:
            total_territories_sold = rights_status_df['Territories Sold'].sum()
            st.metric("Total Territories Sold", total_territories_sold)
        with col5:
            avg_territories = rights_status_df['Territories Sold'].mean()
            st.metric("Avg Territories/Title", f"{avg_territories:.1f}")

        # Search and filter
        st.subheader("Search & Filter")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            search_term = st.text_input("Search by Title, Author, or ISBN", "")

        with col2:
            authors = ['All'] + sorted(rights_status_df['Author Name'].dropna().unique().tolist())
            selected_author = st.selectbox("Filter by Author", authors)

        with col3:
            rights_filter = st.selectbox("Rights Status",
                ["All", "Rights Sold", "No Rights Sold", "Royaltied", "Non-Royaltied"])

        with col4:
            imprints = ['All'] + sorted(rights_status_df['Imprint'].dropna().unique().tolist())
            selected_imprint = st.selectbox("Filter by Imprint", imprints)

        # Apply filters
        filtered_df = rights_status_df.copy()

        if search_term:
            search_mask = (
                filtered_df['Title'].str.contains(search_term, case=False, na=False) |
                filtered_df['Author Name'].str.contains(search_term, case=False, na=False) |
                filtered_df['ISBN'].astype(str).str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[search_mask]

        if selected_author != 'All':
            filtered_df = filtered_df[filtered_df['Author Name'] == selected_author]

        if rights_filter == "Rights Sold":
            filtered_df = filtered_df[filtered_df['Territories Sold'] > 0]
        elif rights_filter == "No Rights Sold":
            filtered_df = filtered_df[filtered_df['Territories Sold'] == 0]
        elif rights_filter == "Royaltied":
            filtered_df = filtered_df[filtered_df['Royaltied'] == True]
        elif rights_filter == "Non-Royaltied":
            filtered_df = filtered_df[filtered_df['Royaltied'] == False]

        if selected_imprint != 'All':
            filtered_df = filtered_df[filtered_df['Imprint'] == selected_imprint]

        # Sort by rights sold (highest first), then by title
        filtered_df = filtered_df.sort_values(['Territories Sold', 'Title'], ascending=[False, True])

        st.markdown(f"**Showing {len(filtered_df)} of {len(rights_status_df)} titles**")

        # Display rights status table
        display_df = filtered_df[[
            'ISBN', 'Title', 'Author Name', 'Rights Granted By', 'Royaltied',
            'Territories Sold', 'Territories Available', 'Sold To', 'LTD Sales'
        ]].copy()

        # Format numeric columns
        display_df['LTD Sales'] = display_df['LTD Sales'].fillna(0).astype(int)

        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
            column_config={
                "Royaltied": st.column_config.CheckboxColumn("Royaltied"),
                "LTD Sales": "Lifetime Sales",
                "Sold To": st.column_config.TextColumn("Territories Sold", width="medium")
            }
        )

        # Export functionality
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Rights Status (CSV)",
            data=csv,
            file_name=f"rights_status_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Error loading books in print: {e}")
        import traceback
        st.code(traceback.format_exc())

def show_rights_matrix(rights_manager):
    """Visualize rights sold/available as a matrix of books x territories."""
    st.header("🗺️ Rights Matrix Visualization")
    st.markdown("Visual map of which territories have rights sold for each title")

    try:
        fro = st.session_state.fro_instance
        if fro is None:
            st.error("Financial Reporting Objects not available.")
            return

        # Load books
        with st.spinner("Loading rights matrix..."):
            fme_df = fro.full_metadata_enhanced_df

        if fme_df is None or fme_df.empty:
            st.warning("No books found.")
            return

        # Get contracts and territories
        contracts = rights_manager.db.get_rights_contracts()
        contracts_df = pd.DataFrame(contracts) if contracts else pd.DataFrame()
        territories = rights_manager.db.get_territories()

        # View options
        st.subheader("Matrix Options")
        col1, col2, col3 = st.columns(3)

        with col1:
            view_by = st.radio("Group by", ["Territory", "Language"])

        with col2:
            max_titles = st.slider("Max Titles to Display", 10, 100, 50, 5)

        with col3:
            show_filter = st.selectbox("Show", ["All Titles", "Only Titles with Rights Sold", "Only Available Titles"])

        # Build the matrix
        if view_by == "Territory":
            dimension_list = sorted([t['territory_name'] for t in territories])
        else:  # Language
            dimension_list = sorted(list(set([t['primary_language'] for t in territories if t.get('primary_language')])))

        # Create matrix data
        matrix_data = []

        for idx, book in fme_df.head(max_titles).iterrows():
            isbn = str(book.get('ISBN', '')).strip()
            title = book.get('Title', '')

            # Get contracts for this book
            if not contracts_df.empty and isbn:
                book_contracts = contracts_df[contracts_df['isbn'] == isbn] if 'isbn' in contracts_df.columns else pd.DataFrame()
                if book_contracts.empty:
                    book_contracts = contracts_df[contracts_df['title'] == title]
            else:
                book_contracts = pd.DataFrame()

            # Build row data
            row_data = {'Title': title[:50]}  # Truncate long titles

            # Check each dimension
            has_any_rights = False
            for dimension in dimension_list:
                if not book_contracts.empty:
                    if view_by == "Territory":
                        sold = dimension in book_contracts['territory_name'].values
                    else:  # Language
                        sold = dimension in book_contracts['target_language'].values

                    row_data[dimension] = 1 if sold else 0
                    if sold:
                        has_any_rights = True
                else:
                    row_data[dimension] = 0

            # Apply filter
            if show_filter == "Only Titles with Rights Sold" and not has_any_rights:
                continue
            elif show_filter == "Only Available Titles" and has_any_rights:
                continue

            matrix_data.append(row_data)

        if not matrix_data:
            st.warning("No data to display with current filters.")
            return

        matrix_df = pd.DataFrame(matrix_data).fillna(0)

        st.subheader(f"Rights Matrix: {len(matrix_df)} Titles × {len(dimension_list)} {view_by}s")

        # Summary statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            total_rights = matrix_df[dimension_list].sum().sum()
            st.metric("Total Rights Sold", int(total_rights))
        with col2:
            avg_per_title = matrix_df[dimension_list].sum(axis=1).mean()
            st.metric(f"Avg {view_by}s per Title", f"{avg_per_title:.1f}")
        with col3:
            most_active_dimension = matrix_df[dimension_list].sum().idxmax() if not matrix_df.empty else "N/A"
            st.metric(f"Most Active {view_by}", most_active_dimension)

        # Visualization options
        viz_type = st.radio("Visualization Type", ["Heatmap", "Detailed Table"], horizontal=True)

        if viz_type == "Heatmap":
            # Create heatmap
            import numpy as np

            # Prepare data for heatmap
            heatmap_data = matrix_df.set_index('Title')[dimension_list]

            # Create heatmap with plotly
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data.values,
                x=heatmap_data.columns,
                y=heatmap_data.index,
                colorscale=[[0, '#f0f0f0'], [1, '#2ca02c']],
                showscale=True,
                hovertemplate='Title: %{y}<br>' + view_by + ': %{x}<br>Status: %{z}<extra></extra>',
                colorbar=dict(
                    title="Status",
                    tickvals=[0, 1],
                    ticktext=["Available", "Sold"]
                )
            ))

            fig.update_layout(
                title=f"Rights Matrix: Titles × {view_by}s",
                xaxis_title=view_by,
                yaxis_title="Title",
                height=max(600, len(matrix_df) * 20),
                xaxis={'side': 'bottom'},
                yaxis={'tickmode': 'linear'}
            )

            st.plotly_chart(fig, use_container_width=True)

        else:  # Detailed Table
            # Show as styled dataframe
            def highlight_sold(val):
                if val == 1:
                    return 'background-color: #2ca02c; color: white'
                return 'background-color: #f0f0f0'

            styled_df = matrix_df.style.applymap(highlight_sold, subset=dimension_list)
            st.dataframe(styled_df, use_container_width=True, height=600)

        # Export matrix
        csv = matrix_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Rights Matrix (CSV)",
            data=csv,
            file_name=f"rights_matrix_{view_by.lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

        # Summary by dimension
        with st.expander(f"View {view_by} Summary"):
            dimension_summary = matrix_df[dimension_list].sum().sort_values(ascending=False)
            summary_df = pd.DataFrame({
                view_by: dimension_summary.index,
                'Titles with Rights': dimension_summary.values
            })

            fig = px.bar(summary_df, x=view_by, y='Titles with Rights',
                        title=f'Titles with Rights Sold by {view_by}')
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(summary_df, use_container_width=True)

    except Exception as e:
        st.error(f"Error generating rights matrix: {e}")
        import traceback
        st.code(traceback.format_exc())

def show_rights_contracts(rights_manager):
    """Display and manage rights contracts."""
    st.header("📋 Rights Contracts")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Existing Contracts")

        try:
            contracts = rights_manager.db.get_rights_contracts()

            if not contracts:
                st.info("No contracts found. Add your first rights contract below.")
            else:
                df = pd.DataFrame(contracts)
                df['contract_start_date'] = pd.to_datetime(df['contract_start_date'])
                df['contract_end_date'] = pd.to_datetime(df['contract_end_date'])

                # Summary metrics
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Total Contracts", len(df))
                with col_b:
                    active_count = len(df[df['contract_end_date'] > datetime.now()])
                    st.metric("Active Contracts", active_count)
                with col_c:
                    total_revenue = df['net_compensation'].sum()
                    st.metric("Total Revenue", f"${total_revenue:,.2f}")

                # Display contracts table
                display_df = df[[
                    'title', 'author_name', 'territory_name', 'target_language',
                    'rights_type', 'contract_start_date', 'contract_end_date',
                    'net_compensation', 'payment_status'
                ]].copy()

                display_df['contract_start_date'] = display_df['contract_start_date'].dt.strftime('%Y-%m-%d')
                display_df['contract_end_date'] = display_df['contract_end_date'].dt.strftime('%Y-%m-%d')
                display_df['net_compensation'] = display_df['net_compensation'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "")

                st.dataframe(display_df, use_container_width=True, height=300)

                # Export
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Contracts (CSV)",
                    data=csv,
                    file_name=f"rights_contracts_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

        except Exception as e:
            st.error(f"Error loading contracts: {e}")

    with col2:
        st.subheader("Add New Contract")

        with st.form("new_contract_form"):
            # Work selection
            works = rights_manager.db.get_works()
            if not works:
                st.warning("No works found. Please add books to the system first.")
                st.form_submit_button("Submit", disabled=True)
                return

            work_options = {f"{w['title']} - {w['author_name']}": w['id'] for w in works}
            selected_work = st.selectbox("Select Work", options=list(work_options.keys()))

            # Publisher
            publishers = rights_manager.db.get_publishers()
            if publishers:
                publisher_options = {p['organization_name']: p['id'] for p in publishers}
                selected_publisher = st.selectbox("Publisher", options=list(publisher_options.keys()))
            else:
                new_publisher_name = st.text_input("Publisher Name (will be created)")
                selected_publisher = None

            # Territory
            territories = rights_manager.db.get_territories()
            territory_options = {t['territory_name']: t['id'] for t in territories}
            selected_territory = st.selectbox("Territory", options=list(territory_options.keys()))

            # Contract details
            rights_type = st.selectbox("Rights Type",
                ["Translation", "Distribution", "Audio", "Digital", "Film/TV", "Other"])

            target_language = st.text_input("Target Language (if translation)")

            col_a, col_b = st.columns(2)
            with col_a:
                start_date = st.date_input("Contract Start Date", value=date.today())
            with col_b:
                end_date = st.date_input("Contract End Date",
                    value=date.today() + timedelta(days=365*7))

            # Financial terms
            net_compensation = st.number_input("Net Compensation ($)", min_value=0.0, value=500.0, step=100.0)
            author_share = st.number_input("Author Share (%)", min_value=0.0, max_value=100.0, value=50.0, step=5.0) / 100

            amount_due_author = net_compensation * author_share
            st.write(f"**Amount Due Author:** ${amount_due_author:,.2f}")

            payment_status = st.selectbox("Payment Status", ["Pending", "Paid", "Overdue"])

            contract_notes = st.text_area("Contract Notes")

            submitted = st.form_submit_button("Add Contract")

            if submitted:
                try:
                    work_id = work_options[selected_work]

                    # Create publisher if needed
                    if selected_publisher is None:
                        publisher_id = rights_manager.db.add_publisher(new_publisher_name)
                    else:
                        publisher_id = publisher_options[selected_publisher]

                    territory_id = territory_options[selected_territory]

                    # Add contract
                    contract_id = rights_manager.db.add_rights_contract(
                        work_id=work_id,
                        publisher_id=publisher_id,
                        territory_id=territory_id,
                        rights_type=rights_type,
                        contract_start_date=start_date.isoformat(),
                        contract_end_date=end_date.isoformat(),
                        target_language=target_language if target_language else None,
                        net_compensation=net_compensation,
                        author_share=author_share,
                        amount_due_author=amount_due_author,
                        payment_status=payment_status,
                        contract_notes=contract_notes if contract_notes else None
                    )

                    st.success(f"Contract added successfully! (ID: {contract_id})")
                    st.rerun()

                except Exception as e:
                    st.error(f"Error adding contract: {e}")

def show_revenue_tracking(rights_manager):
    """Track and display rights revenue using RightsRevenues FRO."""
    st.header("💰 Rights Revenue Tracking")

    try:
        fro = st.session_state.fro_instance
        if fro is None:
            st.warning("Financial Reporting Objects not available. Showing database data only.")
            show_database_revenue(rights_manager)
            return

        # Try to load RightsRevenues FRO
        try:
            rights_revenues = RightsRevenues(fro)
            df = rights_revenues.dataframe

            if df.empty:
                st.info("No rights revenue data found in FRO system. Using database records.")
                show_database_revenue(rights_manager)
                return

            # Display summary
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_revenue = df['Net Compensation'].sum()
                st.metric("Total Revenue", f"${total_revenue:,.2f}")
            with col2:
                total_due = df['Due to Author'].sum()
                st.metric("Total Due Authors", f"${total_due:,.2f}")
            with col3:
                avg_deal = df['Net Compensation'].mean()
                st.metric("Avg Deal Size", f"${avg_deal:,.2f}")
            with col4:
                st.metric("Total Deals", len(df))

            # Revenue by territory/language
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Revenue by Language")
                lang_revenue = df.groupby('Rights purchased')['Net Compensation'].sum().sort_values(ascending=False)
                fig = px.bar(x=lang_revenue.index, y=lang_revenue.values,
                           labels={'x': 'Language', 'y': 'Revenue ($)'})
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Revenue by Author")
                author_revenue = df.groupby('Author Name')['Net Compensation'].sum().sort_values(ascending=False).head(10)
                fig = px.bar(x=author_revenue.index, y=author_revenue.values,
                           labels={'x': 'Author', 'y': 'Revenue ($)'})
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

            # Detailed table
            st.subheader("Detailed Revenue Records")
            display_df = df.copy()
            display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%Y-%m-%d')
            st.dataframe(display_df, use_container_width=True)

            # Export
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Revenue Data (CSV)",
                data=csv,
                file_name=f"rights_revenue_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.warning(f"Could not load RightsRevenues FRO: {e}")
            show_database_revenue(rights_manager)

    except Exception as e:
        st.error(f"Error in revenue tracking: {e}")

def show_database_revenue(rights_manager):
    """Show revenue data from rights_contracts database."""
    contracts = rights_manager.db.get_rights_contracts()

    if not contracts:
        st.info("No contract revenue data available.")
        return

    df = pd.DataFrame(contracts)

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        total_revenue = df['net_compensation'].sum()
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    with col2:
        total_due = df['amount_due_author'].sum()
        st.metric("Total Due Authors", f"${total_due:,.2f}")
    with col3:
        paid_count = len(df[df['payment_status'] == 'Paid'])
        st.metric("Paid Contracts", f"{paid_count}/{len(df)}")

    # Revenue table
    st.dataframe(df[['title', 'territory_name', 'target_language', 'net_compensation',
                    'author_share', 'amount_due_author', 'payment_status']],
                use_container_width=True)

def show_author_payments():
    """Track author compensation and payment history."""
    st.header("👤 Author Payment Tracking")

    try:
        fro = st.session_state.fro_instance
        if fro is None:
            st.warning("Financial Reporting Objects not available.")
            return

        # Try to load payment history
        try:
            from codexes.modules.finance.leo_bloom.FinancialReportingObjects.ActualPaymentHistory import ActualPaymentHistory

            payment_history = ActualPaymentHistory(fro)
            df = payment_history.dataframe

            if df.empty:
                st.info("No payment history recorded. Add payments below.")
            else:
                # Summary by author
                st.subheader("Payment Summary by Author")
                author_summary = df.groupby('Author').agg({
                    'Amount': 'sum',
                    'Date': 'count'
                }).rename(columns={'Amount': 'Total Paid', 'Date': 'Payment Count'})

                col1, col2 = st.columns([2, 1])
                with col1:
                    st.dataframe(author_summary, use_container_width=True)
                with col2:
                    total_paid = df['Amount'].sum()
                    st.metric("Total Paid to Authors", f"${total_paid:,.2f}")
                    st.metric("Unique Authors Paid", len(author_summary))

                # Payment history table
                st.subheader("Payment History")
                display_df = df.copy()
                display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%Y-%m-%d')
                display_df['Amount'] = display_df['Amount'].apply(lambda x: f"${x:,.2f}")
                st.dataframe(display_df, use_container_width=True)

        except Exception as e:
            st.warning(f"Could not load payment history: {e}")

        # Add new payment form
        st.subheader("Record New Payment")

        with st.form("new_payment_form"):
            col1, col2 = st.columns(2)

            with col1:
                author_name = st.text_input("Author Name")
                amount = st.number_input("Amount Paid ($)", min_value=0.0, step=10.0)

            with col2:
                payment_date = st.date_input("Payment Date", value=date.today())
                payment_method = st.selectbox("Payment Method",
                    ["Check", "ACH", "PayPal", "Venmo", "Wire Transfer", "Other"])

            notes = st.text_area("Payment Notes")

            submitted = st.form_submit_button("Record Payment")

            if submitted:
                if not author_name or amount <= 0:
                    st.error("Please provide author name and payment amount.")
                else:
                    st.success(f"Payment of ${amount:,.2f} to {author_name} recorded!")
                    st.info("Note: This form will be integrated with actual payment recording system.")

    except Exception as e:
        st.error(f"Error in payment tracking: {e}")

def show_analytics(rights_manager):
    """Show comprehensive analytics dashboards."""
    st.header("📊 Rights Analytics")

    try:
        contracts = rights_manager.db.get_rights_contracts()

        if not contracts:
            st.info("No contract data available for analytics.")
            return

        df = pd.DataFrame(contracts)
        df['contract_start_date'] = pd.to_datetime(df['contract_start_date'])
        df['contract_end_date'] = pd.to_datetime(df['contract_end_date'])
        df['net_compensation'] = df['net_compensation'].fillna(0)

        # Time-based analytics
        st.subheader("Revenue Trends Over Time")

        df['year'] = df['contract_start_date'].dt.year
        yearly_revenue = df.groupby('year')['net_compensation'].sum().reset_index()

        if len(yearly_revenue) > 1:
            fig = px.line(yearly_revenue, x='year', y='net_compensation',
                         title='Annual Rights Revenue',
                         labels={'net_compensation': 'Revenue ($)', 'year': 'Year'},
                         markers=True)
            st.plotly_chart(fig, use_container_width=True)

        # Territory analysis
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Revenue by Territory")
            territory_revenue = df.groupby('territory_name')['net_compensation'].sum().sort_values(ascending=False).head(10)
            fig = px.bar(x=territory_revenue.index, y=territory_revenue.values,
                        title='Top 10 Territories by Revenue',
                        labels={'x': 'Territory', 'y': 'Revenue ($)'})
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Revenue by Rights Type")
            rights_revenue = df.groupby('rights_type')['net_compensation'].sum()
            fig = px.pie(values=rights_revenue.values, names=rights_revenue.index,
                        title='Revenue Distribution by Rights Type')
            st.plotly_chart(fig, use_container_width=True)

        # Contract expiration tracking
        st.subheader("Contract Expiration Timeline")

        current_date = datetime.now()
        df['days_until_expiry'] = (df['contract_end_date'] - current_date).dt.days

        expiring_soon = df[df['days_until_expiry'].between(0, 365)]
        expired = df[df['days_until_expiry'] < 0]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Expiring This Year", len(expiring_soon))
        with col2:
            st.metric("Already Expired", len(expired))
        with col3:
            avg_term = (df['contract_end_date'] - df['contract_start_date']).dt.days.mean() / 365
            st.metric("Avg Contract Term", f"{avg_term:.1f} years")

        # Show expiring contracts
        if len(expiring_soon) > 0:
            st.warning(f"⚠️ {len(expiring_soon)} contracts expiring within 12 months")
            expiring_display = expiring_soon[['title', 'territory_name', 'contract_end_date', 'days_until_expiry']].copy()
            expiring_display['contract_end_date'] = expiring_display['contract_end_date'].dt.strftime('%Y-%m-%d')
            st.dataframe(expiring_display, use_container_width=True)

    except Exception as e:
        st.error(f"Error generating analytics: {e}")

def show_offerings_and_sales(rights_manager):
    """Generate and manage rights offering sheets."""
    st.header("🎯 Rights Offerings & Sales Materials")

    st.markdown("""
    Generate professional offering sheets for:
    - Individual titles
    - Imprint catalogs
    - Series collections
    - Custom selections
    """)

    tab1, tab2 = st.tabs(["Generate Offering Sheets", "Manage Offerings"])

    with tab1:
        st.subheader("Generate Offering Sheet")

        offering_type = st.radio("Offering Type",
            ["Individual Title", "Imprint Catalog", "Custom Selection"])

        if offering_type == "Individual Title":
            works = rights_manager.db.get_works()
            if works:
                work_options = {f"{w['title']} - {w['author_name']}": w['id'] for w in works}
                selected_work = st.selectbox("Select Title", options=list(work_options.keys()))

                if st.button("Generate Title Sheet"):
                    st.info("Title offering sheet generation coming soon!")
                    st.write(f"Would generate offering sheet for: {selected_work}")

        elif offering_type == "Imprint Catalog":
            # Find imprint configs
            config_dir = Path("configs/imprints")
            if config_dir.exists():
                imprint_files = list(config_dir.glob("*.json"))
                if imprint_files:
                    imprint_options = {f.stem.replace('_', ' ').title(): f for f in imprint_files}
                    selected_imprint = st.selectbox("Select Imprint", options=list(imprint_options.keys()))

                    output_dir = st.text_input("Output Directory", value="output/offering_sheets")

                    if st.button("Generate Imprint Catalog"):
                        try:
                            generator = RightsOfferingSheetGenerator(rights_manager)
                            imprint_file = imprint_options[selected_imprint]

                            with st.spinner(f"Generating offering sheet for {selected_imprint}..."):
                                result = generator.generate_imprint_offering_sheet(
                                    str(imprint_file),
                                    output_dir
                                )

                            if result:
                                st.success(f"Offering sheet generated: {result}")
                            else:
                                st.warning("Could not generate offering sheet. Check logs.")

                        except Exception as e:
                            st.error(f"Error generating offering sheet: {e}")
                else:
                    st.warning("No imprint configuration files found in configs/imprints/")
            else:
                st.warning("Imprints config directory not found.")

        elif offering_type == "Custom Selection":
            st.info("Custom selection offering sheets coming soon!")
            st.markdown("Will allow selection of specific ISBNs to create targeted offering sheets.")

    with tab2:
        st.subheader("Active Offerings")

        # Show available territories
        territories = rights_manager.db.get_territories()
        if territories:
            st.write(f"**Available Territories:** {len(territories)}")

            with st.expander("View All Territories"):
                terr_df = pd.DataFrame(territories)
                st.dataframe(terr_df[['territory_name', 'primary_language', 'currency', 'market_notes']],
                           use_container_width=True)

        # Import existing rights data
        st.subheader("Import Rights Data")
        st.markdown("Import existing rights contracts from CSV file (RightsRevenues format)")

        uploaded_file = st.file_uploader("Upload Rights CSV", type=['csv'])

        if uploaded_file:
            if st.button("Import Data"):
                try:
                    # Save uploaded file temporarily
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name

                    # Import data
                    with st.spinner("Importing rights data..."):
                        works_count, contracts_count, errors = rights_manager.import_existing_rights_data(tmp_path)

                    st.success(f"Import complete! Works: {works_count}, Contracts: {contracts_count}")

                    if errors:
                        with st.expander("View Import Errors"):
                            for error in errors:
                                st.error(error)

                    # Clean up temp file
                    Path(tmp_path).unlink()

                except Exception as e:
                    st.error(f"Error importing data: {e}")

if __name__ == "__main__":
    main()
