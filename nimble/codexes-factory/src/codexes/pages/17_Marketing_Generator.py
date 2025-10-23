"""
Marketing Generator Page for Streamlit UI
Generates marketing materials for books and imprints
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




# Add src to path for imports
if 'src' not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

try:
    from codexes.modules.marketing.marketing_manager import MarketingManager
    from codexes.modules.marketing.substack_post_generator import SubstackPostGenerator
    from codexes.modules.distribution.catalog_manager import CatalogManager
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Render unified sidebar only if not already rendered by main app
# Main app sets sidebar_rendered=True to prevent duplication
if not st.session_state.get('sidebar_rendered', False):
    # NOTE: st.set_page_config() and render_unified_sidebar() handled by main app

# Render unified sidebar only if not already rendered by main app
# Main app sets sidebar_rendered=True to prevent duplication
if not st.session_state.get('sidebar_rendered', False):
    # NOTE: st.set_page_config() and render_unified_sidebar() handled by main app
# DO NOT render sidebar here - it's already rendered by codexes-factory-home-ui.py

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




st.title("📢 Marketing Generator")
st.markdown("Generate marketing materials for books and imprints")

# Sidebar for configuration
st.sidebar.header("Configuration")

# Imprint selection
available_imprints = [d.name for d in Path("imprints").iterdir() if d.is_dir() and d.name != "__pycache__"]
selected_imprint = st.sidebar.selectbox("Select Imprint", available_imprints, index=0)

# Load available catalogs
catalog_manager = CatalogManager()
catalog_options = {}

# Check for imprint-specific catalog
imprint_catalog = Path(f"imprints/{selected_imprint}/books.csv")
if imprint_catalog.exists():
    catalog_options[f"Imprint Catalog ({selected_imprint})"] = str(imprint_catalog)

# Check for versioned catalogs
if Path("data/catalogs").exists():
    for catalog_file in Path("data/catalogs").glob("*.csv"):
        if selected_imprint in catalog_file.name or "combined" in catalog_file.name:
            catalog_options[f"Versioned: {catalog_file.name}"] = str(catalog_file)

# Default catalog
if Path("data/books.csv").exists():
    catalog_options["Main Catalog (data/books.csv)"] = "data/books.csv"

selected_catalog_name = st.sidebar.selectbox("Select Catalog", list(catalog_options.keys()))
selected_catalog_path = catalog_options[selected_catalog_name]

# Marketing format selection
format_options = {
    "Substack Posts": "substack",
    "Press Releases": "press_release", 
    "Social Media Posts": "social_media"
}
selected_formats = st.sidebar.multiselect(
    "Marketing Formats",
    list(format_options.keys()),
    default=["Substack Posts"]
)

# Output directory
output_dir = st.sidebar.text_input("Output Directory", value=f"marketing/{selected_imprint}/generated")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📊 Catalog Preview")
    
    try:
        df = pd.read_csv(selected_catalog_path)
        
        # Filter by imprint if column exists
        if 'imprint' in df.columns and selected_imprint:
            imprint_df = df[df['imprint'] == selected_imprint]
            if len(imprint_df) > 0:
                df = imprint_df
        
        st.info(f"📚 Found {len(df)} books in selected catalog")
        
        # Show sample of books
        if len(df) > 0:
            display_columns = ['title', 'author', 'series_name', 'publication_date']
            available_columns = [col for col in display_columns if col in df.columns]
            st.dataframe(df[available_columns].head(10), use_container_width=True)
            
            if len(df) > 10:
                st.caption(f"Showing first 10 of {len(df)} books...")
        else:
            st.warning("No books found in selected catalog")
            
    except Exception as e:
        st.error(f"Error loading catalog: {e}")
        st.stop()

with col2:
    st.header("⚙️ Generation Options")
    
    # Individual book selection
    book_titles = df['title'].tolist() if 'title' in df.columns else []
    individual_book = st.selectbox(
        "Generate for Individual Book (optional)",
        ["All Books"] + book_titles,
        index=0
    )
    
    # Batch options
    max_books = st.number_input("Max Books to Process", min_value=1, max_value=len(df), value=min(10, len(df)))
    
    # Generate button
    generate_button = st.button("🚀 Generate Marketing Materials", type="primary")

# Generation results
if generate_button:
    if not selected_formats:
        st.error("Please select at least one marketing format")
        st.stop()
    
    st.header("📈 Generation Results")
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize marketing manager
        status_text.text("Initializing marketing manager...")
        progress_bar.progress(10)
        
        marketing_manager = MarketingManager(output_dir)
        
        # Prepare format list
        format_list = [format_options[f] for f in selected_formats]
        
        status_text.text("Generating marketing materials...")
        progress_bar.progress(30)
        
        # Handle individual book vs all books
        if individual_book != "All Books":
            # Create temporary CSV for single book
            book_row = df[df['title'] == individual_book]
            temp_path = Path(output_dir) / "temp_single_book.csv"
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            book_row.to_csv(temp_path, index=False)
            catalog_path = str(temp_path)
        else:
            # Use full catalog but limit books if specified
            if max_books < len(df):
                limited_df = df.head(max_books)
                temp_path = Path(output_dir) / "temp_limited_catalog.csv"
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                limited_df.to_csv(temp_path, index=False)
                catalog_path = str(temp_path)
            else:
                catalog_path = selected_catalog_path
        
        progress_bar.progress(50)
        
        # Generate marketing materials
        results = marketing_manager.generate_marketing_materials(
            catalog_path=catalog_path,
            imprint=selected_imprint,
            formats=format_list
        )
        
        progress_bar.progress(90)
        status_text.text("Finalizing results...")
        
        # Display results
        st.success("✅ Marketing materials generated successfully!")
        
        # Results summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Books", results.get('total_books', 0))
        
        with col2:
            success_count = sum(1 for r in results.get('generated_materials', {}).values() if r.get('success', False))
            st.metric("Formats Generated", f"{success_count}/{len(selected_formats)}")
        
        with col3:
            total_items = sum(r.get('generated_count', 0) for r in results.get('generated_materials', {}).values())
            st.metric("Total Items", total_items)
        
        progress_bar.progress(100)
        status_text.text("✅ Complete!")
        
        # Detailed results
        st.subheader("📋 Detailed Results")
        
        for format_name in selected_formats:
            format_key = format_options[format_name]
            format_results = results.get('generated_materials', {}).get(format_key, {})
            
            with st.expander(f"{format_name} Results", expanded=True):
                if format_results.get('success', False):
                    st.success(f"✅ Successfully generated {format_results.get('generated_count', 0)} items")
                    
                    output_path = format_results.get('output_directory')
                    if output_path:
                        st.info(f"📁 Files saved to: `{output_path}`")
                        
                        # List generated files
                        try:
                            output_path_obj = Path(output_path)
                            if output_path_obj.exists():
                                files = list(output_path_obj.glob("*"))
                                if files:
                                    st.write("Generated files:")
                                    for file_path in files[:10]:  # Show first 10 files
                                        st.write(f"- {file_path.name}")
                                    if len(files) > 10:
                                        st.caption(f"... and {len(files) - 10} more files")
                        except Exception as e:
                            st.warning(f"Could not list files: {e}")
                else:
                    st.error(f"❌ Failed to generate {format_name}")
                    error_msg = format_results.get('error', 'Unknown error')
                    st.error(f"Error: {error_msg}")
        
        # Download option
        if results.get('generated_materials'):
            st.subheader("📦 Download Generated Materials")
            
            try:
                # Create zip file of all generated materials
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    base_output_dir = Path(results['output_directory'])
                    
                    for format_key, format_results in results['generated_materials'].items():
                        if format_results.get('success', False):
                            format_dir = Path(format_results['output_directory'])
                            if format_dir.exists():
                                for file_path in format_dir.rglob('*'):
                                    if file_path.is_file():
                                        # Create relative path for zip
                                        relative_path = file_path.relative_to(base_output_dir.parent)
                                        zip_file.write(file_path, relative_path)
                
                zip_buffer.seek(0)
                
                # Create download button
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{selected_imprint}_marketing_materials_{timestamp}.zip"
                
                st.download_button(
                    label="📥 Download All Materials (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=filename,
                    mime="application/zip"
                )
                
            except Exception as e:
                st.warning(f"Could not create download package: {e}")
        
        # Clean up temporary files
        try:
            temp_files = [
                Path(output_dir) / "temp_single_book.csv",
                Path(output_dir) / "temp_limited_catalog.csv"
            ]
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()
        except Exception as e:
            logger.warning(f"Could not clean up temporary files: {e}")
            
    except Exception as e:
        st.error(f"❌ Error generating marketing materials: {e}")
        logger.error(f"Marketing generation error: {e}", exc_info=True)

# Additional tools section
st.header("🛠️ Additional Tools")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 Individual Post Preview")
    
    if book_titles:
        preview_book = st.selectbox("Select Book for Preview", book_titles, key="preview")
        
        if st.button("Preview Substack Post"):
            try:
                generator = SubstackPostGenerator(selected_catalog_path)
                book = generator.get_book_by_title(preview_book)
                
                if book:
                    post_html = generator.generate_individual_post(book)
                    
                    # Display preview
                    st.subheader(f"Preview: {preview_book}")
                    st.components.v1.html(post_html, height=600, scrolling=True)
                    
                    # Download option for individual post
                    safe_filename = preview_book.lower().replace(' ', '_').replace(':', '')
                    st.download_button(
                        "📥 Download Post HTML",
                        data=post_html,
                        file_name=f"{safe_filename}_substack_post.html",
                        mime="text/html"
                    )
                else:
                    st.error("Book not found in catalog")
                    
            except Exception as e:
                st.error(f"Error generating preview: {e}")

with col2:
    st.subheader("📊 Catalog Management")
    
    st.info("**Catalog Information:**")
    st.write(f"- **Selected:** {selected_catalog_name}")
    st.write(f"- **Path:** {selected_catalog_path}")
    st.write(f"- **Books:** {len(df)}")
    
    if 'imprint' in df.columns:
        imprint_counts = df['imprint'].value_counts()
        st.write("**Books by Imprint:**")
        for imprint, count in imprint_counts.items():
            st.write(f"- {imprint}: {count}")
    
    # Validation button
    if st.button("🔍 Validate Catalog"):
        try:
            validation_results = catalog_manager.validate_catalog(selected_catalog_path)
            
            if validation_results['valid']:
                st.success("✅ Catalog is valid")
            else:
                st.warning("⚠️ Catalog has issues:")
                for issue, value in validation_results.items():
                    if issue != 'valid' and value:
                        if isinstance(value, list):
                            st.write(f"- **{issue}:** {', '.join(value)}")
                        else:
                            st.write(f"- **{issue}:** {value}")
        except Exception as e:
            st.error(f"Validation error: {e}")

# Footer
st.markdown("---")
st.markdown("*Marketing Generator - Part of the Codexes Factory Publishing Pipeline*")