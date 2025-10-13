"""
Dynamic Imprint Display Page

A single reader-facing page that dynamically displays any imprint
by reading configuration files and catalog data. Uses URL parameters
or selection interface to show different imprints.
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
import json
import logging
import random

sys.path.insert(0, '/Users/fred/my-apps')

# Import enhanced imprint management
try:
    from codexes.modules.imprints.services.imprint_manager import ImprintManager
    from codexes.modules.imprints.models.imprint_core import ImprintCore
except ImportError:
    # Graceful fallback if enhanced system not available
    ImprintManager = None
    ImprintCore = None

from shared.ui import render_unified_sidebar

logger = logging.getLogger(__name__)


def main():
    """Main dynamic imprint display interface."""
    st.set_page_config(
        page_title="Imprint Showcase",
        layout="wide",
        page_icon="🏢"
    )

    render_unified_sidebar(
        app_name="Codexes Factory - Imprint Display",
        nav_items=[]
    )
    
    # Get imprint parameter from URL or selection
    selected_imprint = get_selected_imprint()
    
    if selected_imprint:
        render_imprint_page(selected_imprint)
    else:
        render_imprint_selector()


def get_selected_imprint() -> str:
    """Get selected imprint from URL parameters or user selection."""
    # Check URL parameters first
    query_params = st.query_params
    if "imprint" in query_params:
        return query_params["imprint"]
    
    # Check session state
    if "selected_imprint" in st.session_state:
        return st.session_state.selected_imprint
    
    return None


def render_imprint_selector():
    """Render imprint selection interface."""
    st.title("🏢 Imprint Showcase")
    st.markdown("*Explore our publishing imprints and their unique editorial focus*")
    
    # Get available imprints
    available_imprints = get_available_imprints()
    
    if not available_imprints:
        st.error("No public imprints found. Please check the configuration.")
        return
    
    # View toggle
    view_mode = st.radio("View Mode", ["🎴 Card View", "📊 Table View"], horizontal=True)
    
    if view_mode == "📊 Table View":
        render_imprint_dataframe_view(available_imprints)
    else:
        st.markdown("### Select an Imprint to Explore")
        
        # Display imprints as cards
        cols = st.columns(3)
        
        for i, imprint_info in enumerate(available_imprints):
            with cols[i % 3]:
                render_imprint_selection_card(imprint_info)


def render_imprint_dataframe_view(available_imprints: list):
    """Render imprints in a filterable dataframe table."""
    st.markdown("### 📊 Imprints Table View")
    
    if not available_imprints:
        st.info("No imprints available for display.")
        return
    
    # Convert to DataFrame
    import pandas as pd
    df_data = []
    
    for imprint_info in available_imprints:
        df_data.append({
            "Name": imprint_info.get("name", "Unknown"),
            "Tagline": imprint_info.get("tagline", ""),
            "Specialization": imprint_info.get("specialization", ""),
            "Publisher": imprint_info.get("publisher", "Unknown"),
            "Status": "Public"  # Since we're only showing public imprints
        })
    
    df = pd.DataFrame(df_data)
    
    # Filtering interface
    col1, col2, col3 = st.columns(3)
    
    with col1:
        publisher_filter = st.multiselect(
            "Filter by Publisher",
            options=df["Publisher"].unique(),
            default=[]
        )
    
    with col2:
        name_search = st.text_input("Search Name", placeholder="Enter imprint name...")
    
    with col3:
        tagline_search = st.text_input("Search Tagline", placeholder="Enter tagline keywords...")
    
    # Apply filters
    filtered_df = df.copy()
    
    if publisher_filter:
        filtered_df = filtered_df[filtered_df["Publisher"].isin(publisher_filter)]
    
    if name_search:
        filtered_df = filtered_df[filtered_df["Name"].str.contains(name_search, case=False, na=False)]
    
    if tagline_search:
        filtered_df = filtered_df[filtered_df["Tagline"].str.contains(tagline_search, case=False, na=False)]
    
    # Display filtered results
    st.markdown(f"**{len(filtered_df)} of {len(df)} imprints shown**")
    
    # Interactive dataframe with selection
    selected_rows = st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun"
    )
    
    # Handle selection
    if selected_rows and "selection" in selected_rows and selected_rows["selection"]["rows"]:
        selected_idx = selected_rows["selection"]["rows"][0]
        if selected_idx < len(filtered_df):
            selected_imprint = filtered_df.iloc[selected_idx]
            imprint_name = selected_imprint["Name"]
            
            st.info(f"Selected: **{imprint_name}**")
            
            if st.button(f"🔍 Explore {imprint_name}", use_container_width=True):
                st.session_state.selected_imprint = imprint_name
                st.query_params.imprint = imprint_name
                st.rerun()


def render_imprint_selection_card(imprint_info: dict):
    """Render selection card for an imprint."""
    imprint_name = imprint_info.get("name", "Unknown")
    tagline = imprint_info.get("tagline", "")
    specialization = imprint_info.get("specialization", "")
    
    with st.container(border=True):
        # Try to display imprint logo if available
        logo_displayed = display_imprint_logo(imprint_name)
        
        # Try to display random book thumbnail if available
        thumbnail_displayed = display_random_book_thumbnail(imprint_name)
        
        # Add some spacing if we displayed visual elements
        if logo_displayed or thumbnail_displayed:
            st.markdown("<div style='margin: 0.5rem 0;'></div>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem 0;">
            <h4>{imprint_name}</h4>
            <p><em>"{tagline}"</em></p>
            <p>{specialization}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Explore {imprint_name}", key=f"select_{imprint_name}", use_container_width=True):
            st.session_state.selected_imprint = imprint_name
            st.query_params.imprint = imprint_name
            st.rerun()


def render_imprint_page(imprint_name: str):
    """Render complete imprint page."""
    # Load imprint data
    imprint_data = load_imprint_data(imprint_name)
    
    if not imprint_data:
        st.error(f"Imprint '{imprint_name}' not found.")
        if st.button("← Back to Imprint Selector"):
            st.session_state.pop("selected_imprint", None)
            if "imprint" in st.query_params:
                del st.query_params["imprint"]
            st.rerun()
        return
    
    # Render imprint header with branding
    render_dynamic_header(imprint_data)
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📚 Our Books", "🎯 About This Imprint", "📊 Publishing Focus", "📧 Connect"])
    
    with tab1:
        render_imprint_catalog(imprint_name, imprint_data)
    
    with tab2:
        render_imprint_about(imprint_data)
    
    with tab3:
        render_publishing_focus(imprint_data)
    
    with tab4:
        render_contact_info(imprint_data)
    
    # Back navigation
    st.markdown("---")
    if st.button("← Explore Other Imprints"):
        st.session_state.pop("selected_imprint", None)
        if "imprint" in st.query_params:
            del st.query_params["imprint"]
        st.rerun()


def load_imprint_data(imprint_name: str) -> dict:
    """Load comprehensive imprint data from various sources."""
    imprint_data = {
        "name": imprint_name,
        "config": {},
        "catalog": [],
        "assets": {},
        "persona": None
    }
    
    # Try enhanced imprint manager first
    if ImprintManager:
        try:
            manager = ImprintManager()
            imprint = manager.get_imprint(imprint_name)
            
            if imprint:
                # Load configuration
                if imprint.configuration:
                    imprint_data["config"] = imprint.configuration.get_resolved_config()
                
                # Load catalog from CSV
                catalog_path = imprint.path / "books.csv" if imprint.path else Path(f"imprints/{imprint.slug}/books.csv")
                if catalog_path.exists():
                    try:
                        df = pd.read_csv(catalog_path)
                        imprint_data["catalog"] = df.to_dict('records')
                    except Exception as e:
                        logger.debug(f"Failed to load catalog for {imprint_name}: {e}")
                
                # Load assets info
                if imprint.assets:
                    imprint_data["assets"] = {
                        "total_assets": len(imprint.assets.assets),
                        "fonts": imprint.assets.fonts.to_dict(),
                        "brand_colors": imprint.assets.brand_colors,
                        "tagline": imprint.assets.tagline
                    }
                
                # Load persona
                if imprint.publisher_persona:
                    imprint_data["persona"] = {
                        "name": imprint.publisher_persona.name,
                        "bio": imprint.publisher_persona.bio,
                        "reputation": imprint.publisher_persona.reputation_summary
                    }
                
                return imprint_data
                
        except Exception as e:
            logger.debug(f"Enhanced manager failed for {imprint_name}, trying fallback: {e}")
    
    # Fallback to direct file loading
    return load_imprint_data_fallback(imprint_name)


def load_imprint_data_fallback(imprint_name: str) -> dict:
    """Fallback method to load imprint data from files."""
    imprint_data = {"name": imprint_name, "config": {}, "catalog": [], "assets": {}}
    
    # Try to load config file
    config_paths = [
        Path(f"configs/imprints/{imprint_name.lower().replace(' ', '_')}.json"),
        Path(f"configs/imprints/{imprint_name}.json")
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    imprint_data["config"] = config_data
                break
            except Exception as e:
                logger.debug(f"Failed to load config {config_path}: {e}")
    
    # Try to load catalog
    catalog_paths = [
        Path(f"imprints/{imprint_name.lower().replace(' ', '_')}/books.csv"),
        Path(f"imprints/{imprint_name}/books.csv"),
        Path(f"data/catalogs/{imprint_name.lower().replace(' ', '_')}_latest.csv")
    ]
    
    for catalog_path in catalog_paths:
        if catalog_path.exists():
            try:
                df = pd.read_csv(catalog_path)
                imprint_data["catalog"] = df.to_dict('records')
                break
            except Exception as e:
                logger.debug(f"Failed to load catalog {catalog_path}: {e}")
    
    return imprint_data if imprint_data["config"] else None


def imprint_has_titles(imprint_name: str) -> bool:
    """Check if an imprint has any titles in its catalog."""
    # Check common catalog locations
    catalog_paths = [
        Path(f"imprints/{imprint_name.lower().replace(' ', '_')}/books.csv"),
        Path(f"imprints/{imprint_name}/books.csv"),
        Path(f"data/catalogs/{imprint_name.lower().replace(' ', '_')}_latest.csv"),
        Path(f"batch_output/{imprint_name.replace(' ', '_')}_to_outline.json"),
        Path(f"batch_output/{imprint_name.replace(' ', '_')}_to_synopsis.json")
    ]

    for catalog_path in catalog_paths:
        if catalog_path.exists():
            try:
                if catalog_path.suffix == '.csv':
                    df = pd.read_csv(catalog_path)
                    if not df.empty and len(df) > 0:
                        return True
                elif catalog_path.suffix == '.json':
                    with open(catalog_path, 'r') as f:
                        data = json.load(f)
                    if data and len(data) > 0:
                        return True
            except Exception as e:
                logger.debug(f"Error checking catalog {catalog_path}: {e}")

    return False




def get_available_imprints() -> list:
    """Get list of available public imprints for showcase based on catalog content."""
    imprints = []

    # Try enhanced manager for additional imprints
    if ImprintManager:
        try:
            manager = ImprintManager()
            # Use new public imprints method with visibility filtering
            for imprint in manager.get_public_imprints():
                imprint_name = imprint.name

                imprint_info = {
                    "name": imprint_name,
                    "tagline": imprint.tagline or "A publishing imprint",
                    "specialization": "",
                    "publisher": imprint.publisher
                }

                if imprint.configuration:
                    config = imprint.configuration.get_resolved_config()
                    imprint_info["specialization"] = config.get("specialization", config.get("charter", ""))
                    imprint_info["tagline"] = config.get("tagline", imprint_info["tagline"])

                # Only include imprints that have titles
                if imprint_has_titles(imprint_name):
                    imprints.append(imprint_info)

        except Exception as e:
            logger.debug(f"Enhanced manager failed, using fallback: {e}")

    # Fallback to config file scanning for remaining imprints
    config_dir = Path("configs/imprints")
    if config_dir.exists():
        for config_file in config_dir.glob("*.json"):
            if "template" in config_file.name.lower():
                continue

            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)

                imprint_name = config_data.get("imprint", config_file.stem.replace("_", " ").title())

                # Skip if already added
                if any(imp["name"] == imprint_name for imp in imprints):
                    continue

                # Only include imprints that have titles
                if imprint_has_titles(imprint_name):
                    imprints.append({
                        "name": imprint_name,
                        "tagline": config_data.get("tagline", config_data.get("branding", {}).get("tagline", "")),
                        "specialization": config_data.get("specialization", config_data.get("publishing_focus", {}).get("specialization", "")),
                        "publisher": config_data.get("publisher", "Unknown Publisher")
                    })

            except Exception as e:
                logger.debug(f"Failed to load {config_file}: {e}")

    return imprints


def render_dynamic_header(imprint_data: dict):
    """Render dynamic header based on imprint data."""
    config = imprint_data.get("config", {})
    
    # Extract branding information
    branding = config.get("branding", {})
    tagline = (branding.get("tagline") or 
              config.get("tagline") or 
              imprint_data.get("assets", {}).get("tagline") or
              "A Publishing Imprint")
    
    # Get brand colors
    brand_colors = branding.get("brand_colors", {})
    primary_color = brand_colors.get("primary", "#2C3E50")
    secondary_color = brand_colors.get("secondary", "#3498DB")
    
    st.markdown(f"""
    <style>
    .dynamic-imprint-header {{
        background: linear-gradient(135deg, {primary_color} 0%, {secondary_color} 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }}
    .dynamic-tagline {{
        font-size: 1.2rem;
        font-style: italic;
        opacity: 0.95;
        margin-top: 0.8rem;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="dynamic-imprint-header">
        <h1>🏢 {imprint_data['name']}</h1>
        <div class="dynamic-tagline">{tagline}</div>
    </div>
    """, unsafe_allow_html=True)


def render_imprint_catalog(imprint_name: str, imprint_data: dict):
    """Render catalog for any imprint."""
    st.subheader("📚 Our Collection")
    
    catalog = imprint_data.get("catalog", [])
    
    if not catalog:
        st.info("Catalog coming soon. Check back for new releases!")
        return
    
    st.markdown(f"*{len(catalog)} titles in our collection*")
    
    # Search and filter
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search collection", 
                                  placeholder="Enter title, topic, or keyword...",
                                  key=f"search_{imprint_name}")
    
    with col2:
        sort_by = st.selectbox("Sort by", ["Publication Date", "Title", "Price"], 
                             key=f"sort_{imprint_name}")
    
    # Filter catalog
    filtered_catalog = catalog.copy()
    
    if search_term:
        filtered_catalog = [
            book for book in catalog
            if (search_term.lower() in book.get('title', '').lower() or
                search_term.lower() in book.get('back_cover_text', '').lower() or
                search_term.lower() in book.get('author', '').lower())
        ]
    
    # Sort catalog
    if sort_by == "Title":
        filtered_catalog = sorted(filtered_catalog, key=lambda x: x.get('title', ''))
    elif sort_by == "Price":
        filtered_catalog = sorted(filtered_catalog, key=lambda x: float(x.get('price', 0)))
    # Publication date sorting would need date parsing
    
    # Display books
    if filtered_catalog:
        st.markdown(f"**{len(filtered_catalog)} books found**")
        
        for book in filtered_catalog:
            render_dynamic_book_card(book)
    else:
        st.info("No books match your search criteria.")


def render_dynamic_book_card(book: dict):
    """Render a book card that works for any imprint."""
    st.markdown(f"""
    <div style="border: 1px solid #ddd; border-radius: 8px; padding: 1.5rem; margin: 1rem 0; background: #f8f9fa;">
        <h4>{book.get('title', 'Unknown Title')}</h4>
        <p><strong>Author:</strong> {book.get('author', 'Unknown Author')}</p>
        <p><strong>Series:</strong> {book.get('series_name', 'N/A')}</p>
        <p><strong>Price:</strong> ${book.get('price', '0.00')}</p>
        <p><strong>Pages:</strong> {book.get('page_count', 'Unknown')} pages</p>
        <p><strong>Publication:</strong> {book.get('publication_date', 'Coming Soon')}</p>
        <p><em>{book.get('back_cover_text', book.get('storefront_publishers_note_en', 'Description coming soon...'))[:200]}...</em></p>
    </div>
    """, unsafe_allow_html=True)


def render_imprint_about(imprint_data: dict):
    """Render about section using configuration data."""
    st.subheader("🎯 About This Imprint")
    
    config = imprint_data.get("config", {})
    
    # Charter/Description
    charter = config.get("charter", config.get("description", ""))
    if charter:
        st.markdown(f"### Our Mission\n{charter}")
    
    # Publishing focus
    publishing_focus = config.get("publishing_focus", {})
    if publishing_focus:
        st.markdown("### Our Focus")
        
        if "primary_genres" in publishing_focus:
            genres = publishing_focus["primary_genres"]
            st.markdown(f"**Genres**: {', '.join(genres)}")
        
        if "target_audience" in publishing_focus:
            st.markdown(f"**Target Audience**: {publishing_focus['target_audience']}")
        
        if "specialization" in publishing_focus:
            st.markdown(f"**Specialization**: {publishing_focus['specialization']}")
    
    # Publisher information
    publisher = config.get("publisher", "Unknown Publisher")
    contact_email = config.get("contact_email", "")
    
    st.markdown("---")
    st.markdown(f"**Published by**: {publisher}")
    if contact_email:
        st.markdown(f"**Contact**: {contact_email}")
    
    # Publisher persona (if available)
    if imprint_data.get("persona"):
        persona = imprint_data["persona"]
        st.markdown("### Editorial Leadership")
        st.markdown(f"**{persona['name']}**: {persona.get('bio', persona.get('reputation', ''))}")


def render_publishing_focus(imprint_data: dict):
    """Render publishing focus and standards."""
    st.subheader("📊 Publishing Focus & Standards")
    
    config = imprint_data.get("config", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Metadata standards
        st.markdown("### Editorial Standards")
        
        metadata_defaults = config.get("metadata_defaults", {})
        if metadata_defaults:
            if "edition_description" in metadata_defaults:
                st.write(f"**Edition Standard**: {metadata_defaults['edition_description']}")
            
            if "bisac_category_preferences" in metadata_defaults:
                st.write(f"**BISAC Categories**: {len(metadata_defaults['bisac_category_preferences'])} preferred")
        
        # Quality standards
        quality_standards = config.get("quality_standards", config.get("production_settings", {}).get("quality_standards", {}))
        if quality_standards:
            st.markdown("**Production Quality**:")
            for standard, value in quality_standards.items():
                st.write(f"• {standard.replace('_', ' ').title()}: {value}")
    
    with col2:
        # Distribution and format
        st.markdown("### Distribution & Format")
        
        default_settings = config.get("default_book_settings", {})
        if default_settings:
            if "binding_type" in default_settings:
                st.write(f"**Format**: {default_settings['binding_type'].title()}")
            
            if "territorial_rights" in default_settings:
                st.write(f"**Distribution**: {default_settings['territorial_rights']}")
            
            if "language_code" in default_settings:
                st.write(f"**Language**: {default_settings['language_code'].upper()}")
        
        # Pricing info
        pricing_defaults = config.get("pricing_defaults", {})
        if pricing_defaults:
            st.markdown("**Pricing Standards**:")
            for territory, discount in pricing_defaults.items():
                if "discount" in territory:
                    territory_clean = territory.replace("_wholesale_discount", "").upper()
                    st.write(f"• {territory_clean}: {discount}% wholesale discount")


def render_contact_info(imprint_data: dict):
    """Render contact and connection information."""
    st.subheader("📧 Connect With Us")
    
    config = imprint_data.get("config", {})
    
    # Contact information
    contact_email = config.get("contact_email", "")
    publisher = config.get("publisher", "")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Get In Touch")
        if contact_email:
            st.markdown(f"📧 **Email**: {contact_email}")
        st.markdown(f"🏢 **Publisher**: {publisher}")
        
        # Social media from marketing defaults
        marketing_defaults = config.get("marketing_defaults", {})
        social_handles = marketing_defaults.get("social_media_handles", {})
        
        if social_handles:
            st.markdown("### Follow Us")
            for platform, handle in social_handles.items():
                if handle:
                    st.markdown(f"• **{platform.title()}**: {handle}")
    
    with col2:
        st.markdown("### Newsletter Signup")
        st.markdown("Stay updated on new releases and announcements")
        
        with st.form(f"newsletter_{imprint_data['name']}"):
            email = st.text_input("Email Address")
            interests = st.multiselect("Interests", 
                                     config.get("publishing_focus", {}).get("primary_genres", ["General Interest"]))
            
            if st.form_submit_button("Subscribe"):
                if email:
                    # In a real implementation, this would integrate with email service
                    st.success("Thank you for subscribing!")
                else:
                    st.error("Please enter a valid email address")


def display_imprint_logo(imprint_name: str) -> bool:
    """Try to display imprint logo if available. Returns True if logo was displayed."""
    # Common logo file extensions and locations
    logo_extensions = ['.png', '.jpg', '.jpeg', '.svg', '.webp']
    logo_locations = [
        f"imprints/{imprint_name.lower().replace(' ', '_')}/logo",
        f"imprints/{imprint_name.lower().replace(' ', '_')}/assets/logo", 
        f"assets/imprints/{imprint_name.lower().replace(' ', '_')}/logo",
        f"resources/assets/{imprint_name.lower().replace(' ', '_')}/logo"
    ]
    
    for location in logo_locations:
        for ext in logo_extensions:
            logo_path = Path(f"{location}{ext}")
            if logo_path.exists():
                try:
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.image(str(logo_path), width=120, caption=f"{imprint_name} Logo")
                    return True
                except Exception as e:
                    logger.debug(f"Failed to display logo {logo_path}: {e}")
                    continue
    
    return False


def display_random_book_thumbnail(imprint_name: str) -> bool:
    """Try to display a random book thumbnail if available. Returns True if thumbnail was displayed."""
    # Try to load catalog to get book list
    catalog_data = get_imprint_catalog_for_thumbnail(imprint_name)
    
    if not catalog_data:
        return False
    
    # Pick a random book
    random_book = random.choice(catalog_data)
    book_title = random_book.get('title', '')
    book_isbn = random_book.get('isbn_13', random_book.get('isbn', ''))
    
    if not book_title:
        return False
    
    # Try to find thumbnail/cover image
    thumbnail_extensions = ['.png', '.jpg', '.jpeg', '.webp']
    thumbnail_locations = [
        f"imprints/{imprint_name.lower().replace(' ', '_')}/covers/{book_isbn}",
        f"imprints/{imprint_name.lower().replace(' ', '_')}/covers/{book_title.lower().replace(' ', '_')}",
        f"assets/covers/{book_isbn}",
        f"assets/covers/{book_title.lower().replace(' ', '_')}",
        f"resources/covers/{imprint_name.lower().replace(' ', '_')}/{book_isbn}",
        f"data/covers/{book_isbn}"
    ]
    
    for location in thumbnail_locations:
        for ext in thumbnail_extensions:
            thumbnail_path = Path(f"{location}{ext}")
            if thumbnail_path.exists():
                try:
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.image(str(thumbnail_path), width=80, caption=f"Sample: {book_title[:30]}...")
                    return True
                except Exception as e:
                    logger.debug(f"Failed to display thumbnail {thumbnail_path}: {e}")
                    continue
    
    return False


def get_imprint_catalog_for_thumbnail(imprint_name: str) -> list:
    """Get catalog data specifically for thumbnail selection."""
    catalog_paths = [
        Path(f"imprints/{imprint_name.lower().replace(' ', '_')}/books.csv"),
        Path(f"imprints/{imprint_name}/books.csv"),
        Path(f"data/catalogs/{imprint_name.lower().replace(' ', '_')}_latest.csv")
    ]
    
    for catalog_path in catalog_paths:
        if catalog_path.exists():
            try:
                df = pd.read_csv(catalog_path)
                catalog_data = df.to_dict('records')
                if catalog_data:  # Only return if we have actual books
                    return catalog_data
            except Exception as e:
                logger.debug(f"Failed to load catalog {catalog_path}: {e}")
                continue
    
    return []


if __name__ == "__main__":
    main()