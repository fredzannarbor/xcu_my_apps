"""
Publication Manager Page for Streamlit UI
Manages book publication status and asset packaging
"""

import streamlit as st
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
import sys
import os
import zipfile
import io
from typing import List, Dict

sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Add src to path for imports
if 'src' not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

try:
    from codexes.modules.distribution.publication_manager import PublicationManager, PublicationCLI
    from codexes.modules.distribution.catalog_manager import CatalogManager
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Publication Manager",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Publication Manager")
st.markdown("Manage publication status and package book assets")

# Initialize managers
@st.cache_resource
def get_publication_manager():
    return PublicationManager()

@st.cache_resource  
def get_catalog_manager():
    return CatalogManager()

pub_manager = get_publication_manager()
catalog_manager = get_catalog_manager()
pub_cli = PublicationCLI(pub_manager)

# Sidebar configuration
st.sidebar.header("📋 Configuration")

# Imprint selection
available_imprints = [d.name for d in Path("imprints").iterdir() if d.is_dir() and d.name != "__pycache__"]
selected_imprint = st.sidebar.selectbox("Select Imprint", available_imprints, index=0)

# Load available catalogs
catalog_options = {}
imprint_catalog = Path(f"imprints/{selected_imprint}/books.csv")
if imprint_catalog.exists():
    catalog_options[f"Imprint Catalog ({selected_imprint})"] = str(imprint_catalog)

if Path("data/catalogs").exists():
    for catalog_file in Path("data/catalogs").glob("*.csv"):
        if selected_imprint in catalog_file.name or "combined" in catalog_file.name:
            catalog_options[f"Versioned: {catalog_file.name}"] = str(catalog_file)

if Path("data/books.csv").exists():
    catalog_options["Main Catalog (data/books.csv)"] = "data/books.csv"

selected_catalog_name = st.sidebar.selectbox("Select Catalog", list(catalog_options.keys()))
selected_catalog_path = catalog_options[selected_catalog_name]

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["📝 Mark Published", "📦 Package Assets", "📊 Status Overview", "🔍 Asset Validation"])

with tab1:
    st.header("📝 Mark Books as Published")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📚 Available Books")
        
        try:
            df = pd.read_csv(selected_catalog_path)
            
            # Filter by imprint if column exists
            if 'imprint' in df.columns and selected_imprint:
                imprint_df = df[df['imprint'] == selected_imprint]
                if len(imprint_df) > 0:
                    df = imprint_df
            
            # Add publication status column
            if len(df) > 0:
                df['published'] = df['isbn13'].apply(lambda isbn: pub_manager.is_book_published(str(isbn)))
                df['isbn13_str'] = df['isbn13'].astype(str)
                
                # Show books with publication status
                display_df = df[['title', 'isbn13_str', 'series_name', 'publication_date', 'published']].copy()
                display_df.columns = ['Title', 'ISBN', 'Series', 'Pub Date', 'Published']
                
                st.dataframe(display_df, use_container_width=True)
                
                # Filter unpublished books for selection
                unpublished_df = df[~df['published']]
                
                if len(unpublished_df) > 0:
                    st.info(f"📋 {len(unpublished_df)} books available to mark as published")
                else:
                    st.success("✅ All books in this catalog are marked as published!")
            else:
                st.warning("No books found in selected catalog")
                
        except Exception as e:
            st.error(f"Error loading catalog: {e}")
            st.stop()
    
    with col2:
        st.subheader("⚙️ Publication Settings")
        
        # Distribution channel selection
        available_channels = ['LSI', 'KDP', 'storefront']
        selected_channels = st.multiselect(
            "Distribution Channels",
            available_channels,
            default=['LSI', 'storefront']
        )
        
        # Book selection method
        selection_method = st.radio(
            "Selection Method",
            ["Select Individual Books", "Mark All Unpublished", "Enter ISBNs Manually"]
        )
        
        if selection_method == "Select Individual Books" and 'unpublished_df' in locals():
            if len(unpublished_df) > 0:
                # Multi-select books
                book_options = {}
                for _, row in unpublished_df.iterrows():
                    label = f"{row['title']} ({row['isbn13_str']})"
                    book_options[label] = row['isbn13_str']
                
                selected_book_labels = st.multiselect(
                    "Select Books to Publish",
                    list(book_options.keys())
                )
                
                selected_isbns = [book_options[label] for label in selected_book_labels]
            else:
                selected_isbns = []
                st.info("No unpublished books to select")
                
        elif selection_method == "Mark All Unpublished" and 'unpublished_df' in locals():
            selected_isbns = unpublished_df['isbn13_str'].tolist()
            if selected_isbns:
                st.info(f"Will mark all {len(selected_isbns)} unpublished books")
            
        elif selection_method == "Enter ISBNs Manually":
            isbn_input = st.text_area("Enter ISBNs (one per line)")
            selected_isbns = [isbn.strip() for isbn in isbn_input.split('\n') if isbn.strip()]
        
        # Mark published button
        if st.button("📤 Mark as Published", type="primary"):
            if not selected_channels:
                st.error("Please select at least one distribution channel")
            elif not selected_isbns:
                st.error("Please select books to mark as published")
            else:
                with st.spinner("Marking books as published..."):
                    results = pub_cli.mark_published_from_catalog(
                        selected_catalog_path, 
                        selected_isbns, 
                        selected_channels
                    )
                    
                    success_count = sum(1 for success in results.values() if success)
                    
                    if success_count == len(selected_isbns):
                        st.success(f"✅ Successfully marked {success_count} books as published!")
                    else:
                        st.warning(f"⚠️ Marked {success_count}/{len(selected_isbns)} books as published")
                    
                    # Show detailed results
                    for isbn, success in results.items():
                        status = "✅" if success else "❌"
                        st.write(f"{status} {isbn}")
                
                # Refresh the page data
                st.experimental_rerun()

with tab2:
    st.header("📦 Package Assets")
    
    # Get published books
    published_books = pub_manager.get_published_books(selected_imprint)
    
    if published_books:
        st.info(f"📚 Found {len(published_books)} published books for {selected_imprint}")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Published Books")
            
            # Create DataFrame for display
            pub_df_data = []
            for book in published_books:
                pub_df_data.append({
                    'Title': book['title'],
                    'ISBN': book['isbn'],
                    'Channels': ', '.join(book['distribution_channels']),
                    'Packaged': "✅" if book.get('assets_packaged', False) else "📋",
                    'Published Date': book['publication_date'][:10]
                })
            
            pub_df = pd.DataFrame(pub_df_data)
            st.dataframe(pub_df, use_container_width=True)
            
            # Filter books that need packaging
            unpackaged_books = [book for book in published_books if not book.get('assets_packaged', False)]
            
            if unpackaged_books:
                st.warning(f"⚠️ {len(unpackaged_books)} books need asset packaging")
            else:
                st.success("✅ All published books have been packaged!")
        
        with col2:
            st.subheader("⚙️ Packaging Options")
            
            # Selection options
            packaging_method = st.radio(
                "Packaging Method",
                ["Package All Unpackaged", "Select Specific Books", "Package All Books"]
            )
            
            if packaging_method == "Package All Unpackaged":
                target_isbns = [book['isbn'] for book in unpackaged_books]
            elif packaging_method == "Select Specific Books":
                book_options = {f"{book['title']} ({book['isbn']})": book['isbn'] 
                              for book in published_books}
                selected_labels = st.multiselect("Select Books", list(book_options.keys()))
                target_isbns = [book_options[label] for label in selected_labels]
            else:  # Package All Books
                target_isbns = [book['isbn'] for book in published_books]
            
            if target_isbns:
                st.info(f"Will package {len(target_isbns)} books")
                
                # Package button
                if st.button("📦 Package Assets", type="primary"):
                    with st.spinner(f"Packaging assets for {len(target_isbns)} books..."):
                        progress_bar = st.progress(0)
                        
                        packaged_files = []
                        for i, isbn in enumerate(target_isbns):
                            progress_bar.progress((i + 1) / len(target_isbns))
                            
                            package_path = pub_manager.package_published_book_assets(isbn)
                            if package_path:
                                packaged_files.append(package_path)
                        
                        if len(packaged_files) == len(target_isbns):
                            st.success(f"✅ Successfully packaged {len(packaged_files)} books!")
                        else:
                            st.warning(f"⚠️ Packaged {len(packaged_files)}/{len(target_isbns)} books")
                        
                        # Show package details
                        if packaged_files:
                            st.subheader("📦 Created Packages")
                            for package_path in packaged_files:
                                file_size = package_path.stat().st_size / 1024 / 1024  # MB
                                st.write(f"📁 {package_path.name} ({file_size:.1f} MB)")
                                
                                # Download button for individual package
                                with open(package_path, 'rb') as f:
                                    st.download_button(
                                        f"📥 Download {package_path.name}",
                                        data=f.read(),
                                        file_name=package_path.name,
                                        mime="application/zip",
                                        key=f"download_{package_path.stem}"
                                    )
                    
                    # Refresh page data
                    st.experimental_rerun()
            else:
                st.info("No books selected for packaging")
    else:
        st.info(f"No published books found for {selected_imprint}")
        st.markdown("Use the **Mark Published** tab to mark books as published first.")

with tab3:
    st.header("📊 Publication Status Overview")
    
    # Get statistics
    stats = pub_manager.get_publication_statistics()
    
    # Overview metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Published", stats.get('total_published', 0))
    
    with col2:
        packaged_count = sum(1 for book in pub_manager.get_published_books() 
                           if book.get('assets_packaged', False))
        st.metric("Assets Packaged", packaged_count)
    
    with col3:
        # Calculate total package size
        total_size = 0
        for zip_file in Path("data/published_books").glob("*.zip"):
            total_size += zip_file.stat().st_size
        total_size_mb = total_size / 1024 / 1024
        st.metric("Total Package Size", f"{total_size_mb:.1f} MB")
    
    # Distribution channels breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 By Distribution Channel")
        channel_stats = stats.get('by_channel', {})
        if channel_stats:
            for channel, count in channel_stats.items():
                st.write(f"**{channel}:** {count} books")
        else:
            st.info("No channel statistics available")
    
    with col2:
        st.subheader("📖 By Imprint")
        imprint_stats = stats.get('by_imprint', {})
        if imprint_stats:
            for imprint, count in imprint_stats.items():
                st.write(f"**{imprint}:** {count} books")
        else:
            st.info("No imprint statistics available")
    
    # Recent publications
    st.subheader("📅 Recent Publications")
    all_published = pub_manager.get_published_books()
    
    if all_published:
        # Sort by publication date
        all_published.sort(key=lambda x: x.get('publication_date', ''), reverse=True)
        
        recent_books = all_published[:10]  # Show last 10
        
        for book in recent_books:
            pub_date = book.get('publication_date', '')[:10] if book.get('publication_date') else 'Unknown'
            channels = ', '.join(book.get('distribution_channels', []))
            packaged = "📦" if book.get('assets_packaged', False) else "📋"
            
            st.write(f"{packaged} **{book['title']}** (ISBN: {book['isbn']}) - {channels} - {pub_date}")
    else:
        st.info("No published books found")

with tab4:
    st.header("🔍 Asset Validation")
    
    # Get published books for validation
    published_books = pub_manager.get_published_books(selected_imprint)
    
    if published_books:
        # Book selection for validation
        book_options = {f"{book['title']} ({book['isbn']})": book['isbn'] 
                       for book in published_books}
        
        if book_options:
            selected_book_label = st.selectbox("Select Book to Validate", list(book_options.keys()))
            selected_isbn = book_options[selected_book_label]
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Validate button
                if st.button("🔍 Validate Assets", type="primary"):
                    with st.spinner("Validating book assets..."):
                        validation_result = pub_manager.validate_book_assets(selected_isbn)
                        
                        # Display validation results
                        if validation_result.get('valid', False):
                            st.success("✅ All assets found and validated!")
                        else:
                            st.warning("⚠️ Some assets are missing")
                        
                        st.subheader("📋 Asset Inventory")
                        
                        # Found assets
                        found_assets = validation_result.get('found_assets', {})
                        if found_assets:
                            st.write("**✅ Found Assets:**")
                            for asset_type, asset_path in found_assets.items():
                                file_path = Path(asset_path)
                                file_size = file_path.stat().st_size / 1024  # KB
                                st.write(f"- **{asset_type}:** {file_path.name} ({file_size:.1f} KB)")
                        
                        # Missing assets
                        missing_assets = validation_result.get('missing_assets', {})
                        if missing_assets:
                            st.write("**❌ Missing Assets:**")
                            for asset_type, expected_path in missing_assets.items():
                                st.write(f"- **{asset_type}:** {expected_path}")
                        
                        # Package status
                        if validation_result.get('assets_packaged', False):
                            package_path = validation_result.get('package_path')
                            st.info(f"📦 Assets already packaged: {Path(package_path).name}")
                        else:
                            st.info("📋 Assets not yet packaged")
            
            with col2:
                st.subheader("🛠️ Quick Actions")
                
                # Quick package button
                if st.button("📦 Package This Book"):
                    with st.spinner("Packaging book assets..."):
                        package_path = pub_manager.package_published_book_assets(selected_isbn)
                        
                        if package_path:
                            st.success(f"✅ Packaged: {package_path.name}")
                            
                            # Download button
                            with open(package_path, 'rb') as f:
                                st.download_button(
                                    "📥 Download Package",
                                    data=f.read(),
                                    file_name=package_path.name,
                                    mime="application/zip"
                                )
                        else:
                            st.error("❌ Failed to package assets")
                
                # Quick unmark button
                if st.button("📝 Unmark as Published", type="secondary"):
                    success = pub_manager.mark_book_unpublished(selected_isbn)
                    if success:
                        st.success("✅ Book unmarked as published")
                        st.experimental_rerun()
                    else:
                        st.error("❌ Failed to unmark book")
    else:
        st.info("No published books found for validation")

# Footer section
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🗂️ Package Directory")
    
    # List existing packages
    package_dir = Path("data/published_books")
    if package_dir.exists():
        packages = list(package_dir.glob("*.zip"))
        
        if packages:
            st.write(f"📦 {len(packages)} asset packages created:")
            for package in sorted(packages, key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
                file_size = package.stat().st_size / 1024 / 1024  # MB
                modified_time = datetime.fromtimestamp(package.stat().st_mtime)
                st.write(f"- {package.name} ({file_size:.1f} MB) - {modified_time.strftime('%Y-%m-%d %H:%M')}")
                
            if len(packages) > 10:
                st.caption(f"... and {len(packages) - 10} more packages")
        else:
            st.info("No asset packages created yet")
    else:
        st.info("Package directory not yet created")

with col2:
    st.subheader("🧹 Maintenance")
    
    # Cleanup orphaned packages
    if st.button("🧹 Cleanup Orphaned Packages"):
        with st.spinner("Cleaning up orphaned packages..."):
            removed_count = pub_manager.cleanup_unpublished_packages()
            
            if removed_count > 0:
                st.success(f"✅ Removed {removed_count} orphaned packages")
            else:
                st.info("No orphaned packages found")
    
    # Bulk download option
    if Path("data/published_books").exists():
        packages = list(Path("data/published_books").glob("*.zip"))
        
        if packages and st.button("📥 Download All Packages"):
            # Create combined zip of all packages
            with st.spinner("Creating combined download..."):
                try:
                    zip_buffer = io.BytesIO()
                    
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as combined_zip:
                        for package in packages:
                            combined_zip.write(package, package.name)
                    
                    zip_buffer.seek(0)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    combined_filename = f"{selected_imprint}_all_packages_{timestamp}.zip"
                    
                    st.download_button(
                        "📦 Download Combined Package",
                        data=zip_buffer.getvalue(),
                        file_name=combined_filename,
                        mime="application/zip"
                    )
                    
                except Exception as e:
                    st.error(f"Error creating combined package: {e}")

st.markdown("---")
st.markdown("*Publication Manager - Complete asset lifecycle management*")