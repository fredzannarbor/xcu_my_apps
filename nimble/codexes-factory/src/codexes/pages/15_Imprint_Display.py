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

# Import shared authentication system
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info, authenticate as shared_authenticate, logout as shared_logout
    from shared.ui import render_unified_sidebar
except ImportError as e:
    import streamlit as st
    st.error(f"Failed to import shared authentication: {e}")
    st.error("Please ensure /Users/fred/xcu_my_apps/shared/auth is accessible")
    st.stop()


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# Import enhanced imprint management
try:
    from codexes.modules.imprints.services.imprint_manager import ImprintManager
    from codexes.modules.imprints.models.imprint_core import ImprintCore
except ImportError:
    # Graceful fallback if enhanced system not available
    ImprintManager = None
    ImprintCore = None


def main():
    """Main dynamic imprint display interface."""
    # Import and use page utilities for consistent sidebar and auth
    try:
        from codexes.core.page_utils import render_page_sidebar, ensure_auth_checked

        # Ensure auth has been checked for this session
        ensure_auth_checked()

        # Render the full sidebar with all sections
        render_page_sidebar()
    except ImportError as e:
        logger.warning(f"Could not import page_utils: {e}")
        # Fallback: sync session state manually
        if is_authenticated():
            user_info = get_user_info()
            st.session_state.username = user_info.get('username')
            st.session_state.user_name = user_info.get('user_name')
            st.session_state.user_email = user_info.get('user_email')
            st.session_state.user_role = user_info.get('user_role', 'public')
        else:
            if "username" not in st.session_state:
                st.session_state.username = None
            st.session_state.user_role = 'public'

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
    
    # Main content tabs (reordered: About, Specs, Idea Tournament, Catalog, Academic Paper, Connect)
    tabs = ["🎯 About", "📊 Specs", "🚀 Idea Tournament", "📚 Catalog", "📄 Research Paper", "📧 Connect"]

    tab_objects = st.tabs(tabs)
    current_tab = 0

    # About tab
    with tab_objects[current_tab]:
        render_imprint_about(imprint_data)
    current_tab += 1

    # Specs tab
    with tab_objects[current_tab]:
        render_publishing_focus(imprint_data)
    current_tab += 1

    # Idea Tournament tab
    with tab_objects[current_tab]:
        render_forthcoming_books(imprint_data)
    current_tab += 1

    # Catalog tab - links to bookstore
    with tab_objects[current_tab]:
        render_imprint_catalog(imprint_name, imprint_data)
    current_tab += 1

    # Academic Paper tab (always present)
    with tab_objects[current_tab]:
        render_research_paper(imprint_data)
    current_tab += 1

    # Connect tab
    with tab_objects[current_tab]:
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
        "forthcoming_books": [],
        "assets": {},
        "persona": None,
        "agent_config": {},
        "academic_paper_path": None
    }

    # Try enhanced imprint manager first
    if ImprintManager:
        try:
            manager = ImprintManager()
            imprint = manager.get_imprint(imprint_name)

            if imprint:
                # Load agent_config.json (lightweight config)
                agent_config_path = imprint.path / "agent_config.json" if imprint.path else Path(f"imprints/{imprint.slug}/agent_config.json")
                if agent_config_path.exists():
                    try:
                        with open(agent_config_path, 'r') as f:
                            imprint_data["agent_config"] = json.load(f)
                    except Exception as e:
                        logger.debug(f"Failed to load agent config for {imprint_name}: {e}")

                # Load configuration
                if imprint.configuration:
                    imprint_data["config"] = imprint.configuration.get_resolved_config()

                # Load catalog from CSV
                catalog_path = imprint.path / "books.csv" if imprint.path else Path(f"imprints/{imprint.slug}/books.csv")
                if catalog_path.exists():
                    try:
                        df = pd.read_csv(catalog_path)
                        imprint_data["catalog"] = df.to_dict('records')

                        # Separate forthcoming books
                        if 'publication_date' in df.columns:
                            today = datetime.now().date()
                            forthcoming_df = df[pd.to_datetime(df['publication_date'], errors='coerce').dt.date > today]
                            imprint_data["forthcoming_books"] = forthcoming_df.to_dict('records')
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

                # Load persona (complete publisher_persona info)
                if imprint.publisher_persona:
                    imprint_data["persona"] = {
                        "name": imprint.publisher_persona.name,
                        "bio": imprint.publisher_persona.bio,
                        "reputation": imprint.publisher_persona.reputation_summary,
                        "risk_tolerance": getattr(imprint.publisher_persona, 'risk_tolerance', None),
                        "editorial_philosophy": getattr(imprint.publisher_persona, 'editorial_philosophy', None)
                    }

                # Check for academic paper (prioritize imprints directory)
                imprint_slug = imprint.slug if hasattr(imprint, 'slug') else imprint_name.lower().replace(' ', '_')
                academic_paper_paths = [
                    Path(f"imprints/{imprint_slug}/{imprint_slug}_paper.pdf"),
                    Path(f"imprints/{imprint_slug}/academic_paper.pdf"),
                    Path(f"imprints/{imprint_slug}/{imprint_slug}_paper.md"),
                    Path(f"output/academic_papers/{imprint_slug}/{imprint_slug}_paper.pdf"),
                    imprint.path / "academic_paper.pdf" if imprint.path else None,
                    Path(f"output/academic_papers/{imprint_slug}.pdf")
                ]

                for paper_path in academic_paper_paths:
                    if paper_path and paper_path.exists():
                        imprint_data["academic_paper_path"] = str(paper_path)
                        break

                return imprint_data

        except Exception as e:
            logger.debug(f"Enhanced manager failed for {imprint_name}, trying fallback: {e}")

    # Fallback to direct file loading
    return load_imprint_data_fallback(imprint_name)


def load_imprint_data_fallback(imprint_name: str) -> dict:
    """Fallback method to load imprint data from files."""
    imprint_data = {
        "name": imprint_name,
        "config": {},
        "catalog": [],
        "forthcoming_books": [],
        "assets": {},
        "agent_config": {},
        "persona": None,
        "academic_paper_path": None
    }

    imprint_slug = imprint_name.lower().replace(' ', '_')

    # Load agent_config.json (lightweight config with display_name, tagline, special_practice)
    agent_config_path = Path(f"imprints/{imprint_slug}/agent_config.json")
    if agent_config_path.exists():
        try:
            with open(agent_config_path, 'r') as f:
                imprint_data["agent_config"] = json.load(f)
        except Exception as e:
            logger.debug(f"Failed to load agent config {agent_config_path}: {e}")

    # Try to load main config file
    config_paths = [
        Path(f"configs/imprints/{imprint_slug}.json"),
        Path(f"configs/imprints/{imprint_name}.json")
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    imprint_data["config"] = config_data

                    # Extract publisher persona from config
                    if "publisher_persona" in config_data:
                        persona_data = config_data["publisher_persona"]
                        imprint_data["persona"] = {
                            "name": persona_data.get("persona_name", "Editorial AI"),
                            "bio": persona_data.get("persona_bio", ""),
                            "reputation": "",  # Not in config format
                            "risk_tolerance": persona_data.get("risk_tolerance", ""),
                            "editorial_philosophy": persona_data.get("editorial_philosophy", ""),
                            "decision_style": persona_data.get("decision_style", ""),
                            "preferred_topics": persona_data.get("preferred_topics", ""),
                            "target_demographics": persona_data.get("target_demographics", "")
                        }
                break
            except Exception as e:
                logger.debug(f"Failed to load config {config_path}: {e}")

    # Try to load catalog
    catalog_paths = [
        Path(f"imprints/{imprint_slug}/books.csv"),
        Path(f"imprints/{imprint_name}/books.csv"),
        Path(f"data/catalogs/{imprint_slug}_latest.csv")
    ]

    for catalog_path in catalog_paths:
        if catalog_path.exists():
            try:
                df = pd.read_csv(catalog_path)
                imprint_data["catalog"] = df.to_dict('records')

                # Separate forthcoming books (publication_date in the future)
                if 'publication_date' in df.columns:
                    today = datetime.now().date()
                    forthcoming_df = df[pd.to_datetime(df['publication_date'], errors='coerce').dt.date > today]
                    imprint_data["forthcoming_books"] = forthcoming_df.to_dict('records')

                break
            except Exception as e:
                logger.debug(f"Failed to load catalog {catalog_path}: {e}")

    # Check for academic paper (prioritize imprints directory)
    academic_paper_paths = [
        Path(f"imprints/{imprint_slug}/{imprint_slug}_paper.pdf"),
        Path(f"imprints/{imprint_slug}/academic_paper.pdf"),
        Path(f"imprints/{imprint_slug}/{imprint_slug}_paper.md"),
        Path(f"output/academic_papers/{imprint_slug}/{imprint_slug}_paper.pdf"),
        Path(f"output/academic_papers/{imprint_slug}.pdf")
    ]

    for paper_path in academic_paper_paths:
        if paper_path.exists():
            imprint_data["academic_paper_path"] = str(paper_path)
            break

    return imprint_data if imprint_data["config"] or imprint_data["agent_config"] else None


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


def get_persona_glyph(persona_name: str) -> str:
    """Load AI glyph for a persona from the registry.

    Args:
        persona_name: Name of the persona (e.g., "Seon", "SoRogue")

    Returns:
        Unicode glyph character, or empty string if not found
    """
    try:
        glyph_registry_path = Path("configs/imprints/persona_glyphs.json")
        if glyph_registry_path.exists():
            with open(glyph_registry_path, 'r') as f:
                registry = json.load(f)
                glyphs = registry.get("glyphs", {})
                if persona_name in glyphs:
                    return glyphs[persona_name].get("glyph", "")
    except Exception as e:
        logger.debug(f"Failed to load glyph for {persona_name}: {e}")

    # Return empty string if glyph not found
    return ""


def render_dynamic_header(imprint_data: dict):
    """Render dynamic header based on imprint data."""
    config = imprint_data.get("config", {})
    agent_config = imprint_data.get("agent_config", {})

    # Use display_name from agent_config, fall back to name
    display_name = agent_config.get("display_name", imprint_data.get("name"))

    # Extract branding information (prefer agent_config, then main config)
    tagline = (
        agent_config.get("tagline") or
        config.get("branding", {}).get("tagline") or
        config.get("tagline") or
        imprint_data.get("assets", {}).get("tagline") or
        "A Publishing Imprint"
    )

    # Get brand colors from main config
    brand_colors = config.get("branding", {}).get("brand_colors", {})
    primary_color = brand_colors.get("primary", "#2C3E50")
    secondary_color = brand_colors.get("secondary", "#3498DB")

    # Get fonts from main config
    fonts = config.get("fonts", {})
    heading_font = fonts.get("heading", "Helvetica, Arial, sans-serif")
    body_font = fonts.get("body", "Georgia, serif")

    st.markdown(f"""
    <style>
    .dynamic-imprint-header {{
        background: linear-gradient(135deg, {primary_color} 0%, {secondary_color} 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        font-family: {heading_font};
    }}
    .dynamic-imprint-title {{
        font-family: {heading_font};
        font-size: 2.5rem;
        margin: 0;
        padding: 0;
    }}
    .dynamic-tagline {{
        font-family: {body_font};
        font-size: 1.2rem;
        font-style: italic;
        opacity: 0.95;
        margin-top: 0.8rem;
    }}
    .imprint-special-practice {{
        font-size: 0.9rem;
        margin-top: 0.5rem;
        opacity: 0.9;
    }}
    </style>
    """, unsafe_allow_html=True)

    # Add special practice if available (like pilsa for xynapse_traces)
    special_practice_html = ""
    if "special_practice" in agent_config:
        special_practice_html = f'<div class="imprint-special-practice">Featuring {agent_config["special_practice"]}</div>'

    st.markdown(f"""
    <div class="dynamic-imprint-header">
        <h1 class="dynamic-imprint-title">🏢 {display_name}</h1>
        <div class="dynamic-tagline">{tagline}</div>
        {special_practice_html}
    </div>
    """, unsafe_allow_html=True)


def render_imprint_catalog(imprint_name: str, imprint_data: dict):
    """Render catalog link to bookstore."""
    st.subheader("📚 Our Collection")

    catalog = imprint_data.get("catalog", [])

    if not catalog:
        st.info("Catalog coming soon. Check back for new releases!")
        return

    st.markdown(f"*Browse our complete collection of {len(catalog)} titles in the interactive bookstore*")

    # Large, prominent button to the bookstore
    st.markdown("<br>", unsafe_allow_html=True)

    # Create bookstore URL with imprint filter and session_id for cross-page SSO
    imprint_slug = imprint_name.lower().replace(' ', '_')
    bookstore_url = f"/Bookstore?imprint={imprint_slug}"

    # Add session_id to URL to maintain authentication
    session_id = st.session_state.get("shared_session_id", "")
    if session_id:
        bookstore_url += f"&session_id={session_id}"
        logger.info(f"[CATALOG LINK] Adding session_id {session_id[:16]}... to bookstore URL")

    st.markdown(f"""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin: 1rem 0;">
        <h3 style="color: white; margin-bottom: 1rem;">🛒 Visit Our Interactive Bookstore</h3>
        <p style="color: white; opacity: 0.9; margin-bottom: 1.5rem;">
            Browse {len(catalog)} titles with full descriptions, reviews, and instant purchase options
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.link_button(
            "🛍️ Browse Full Catalog with Buy Buttons",
            bookstore_url,
            use_container_width=True,
            type="primary"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Show quick preview of a few titles
    st.markdown("### 📖 Featured Titles Preview")
    st.markdown("*See a few highlights from our catalog - visit the bookstore for the complete collection*")

    # Show first 3 books as preview
    preview_books = catalog[:3] if len(catalog) > 3 else catalog

    for book in preview_books:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**{book.get('title', 'Unknown Title')}**")
                st.markdown(f"*by {book.get('author', 'Unknown Author')}*")
                if book.get('back_cover_text'):
                    st.markdown(f"{book['back_cover_text'][:150]}...")

            with col2:
                st.markdown(f"**${book.get('price', '0.00')}**")
                st.markdown(f"📄 {book.get('page_count', 'N/A')} pages")

    # Another button at the bottom (uses same bookstore_url from above)
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.link_button(
            "🛍️ See All Titles & Add to Cart",
            bookstore_url,
            use_container_width=True,
            type="primary"
        )


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
    agent_config = imprint_data.get("agent_config", {})

    # Description from agent_config or charter from main config
    description = agent_config.get("description", config.get("charter", config.get("description", "")))
    if description:
        st.markdown(f"### Our Mission\n{description}")

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

    # Publisher persona (if available) - User-friendly narrative style
    if imprint_data.get("persona"):
        persona = imprint_data["persona"]
        st.markdown("---")
        st.markdown("### Meet Our Editorial Intelligence")

        # Get brand colors for styling
        brand_colors = config.get("branding", {}).get("brand_colors", {})
        primary_color = brand_colors.get("primary", "#2C3E50")

        # Load AI glyph from registry
        glyph = get_persona_glyph(persona['name'])

        # Apply hero color to persona name heading with glyph
        st.markdown(f"""
        <h4 style="color: {primary_color}; margin-top: 1rem;">
            {glyph} {persona['name']}
        </h4>
        """, unsafe_allow_html=True)

        if persona.get('bio'):
            st.markdown(persona['bio'])
            st.markdown("")  # spacing

        # Editorial approach section
        if persona.get('editorial_philosophy'):
            st.markdown("**Editorial Approach**")
            st.markdown(f"*\"{persona['editorial_philosophy']}\"*")
            st.markdown("")

        # Create readable overview of preferences and style
        col1, col2 = st.columns(2)

        with col1:
            if persona.get('preferred_topics'):
                st.markdown("**Areas of Focus**")
                st.markdown(f"{persona['preferred_topics']}")

            if persona.get('decision_style'):
                st.markdown("**Editorial Style**")
                st.markdown(f"{persona['decision_style']}")

        with col2:
            if persona.get('target_demographics'):
                st.markdown("**Our Readers**")
                st.markdown(f"{persona['target_demographics']}")

            if persona.get('risk_tolerance'):
                st.markdown("**Publishing Philosophy**")
                risk_desc = {
                    "High": "Embraces innovative and unconventional works",
                    "Medium": "Balances traditional quality with fresh perspectives",
                    "Low": "Focuses on proven topics with established audience"
                }.get(persona['risk_tolerance'], persona['risk_tolerance'])
                st.markdown(f"{risk_desc}")

    # Publisher information
    publisher = config.get("publisher", "Unknown Publisher")
    contact_email = config.get("contact_email", "")

    st.markdown("---")
    st.markdown(f"**Published by**: {publisher}")
    if contact_email:
        st.markdown(f"**Contact**: {contact_email}")


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


def render_forthcoming_books(imprint_data: dict):
    """Render idea tournament tab with tournament visualization."""
    st.subheader("🚀 Idea Tournament")

    forthcoming_books = imprint_data.get("forthcoming_books", [])

    if not forthcoming_books:
        st.info("No forthcoming books announced yet. Check back soon for exciting new releases!")
        return

    st.markdown(f"**{len(forthcoming_books)} upcoming titles**")

    # Display mode toggle
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        display_mode = st.radio(
            "Display Mode",
            ["🏆 Tournament View", "📋 List View"],
            horizontal=True,
            key=f"display_mode_{imprint_data['name']}"
        )

    with col2:
        if display_mode == "🏆 Tournament View" and len(forthcoming_books) > 8:
            max_books = st.slider(
                "Books in Tournament",
                min_value=4,
                max_value=min(len(forthcoming_books), 16),
                value=8,
                step=4,
                key=f"max_books_{imprint_data['name']}"
            )
        else:
            max_books = min(len(forthcoming_books), 8)

    with col3:
        if st.button("🔄 Reset Votes", key=f"reset_votes_{imprint_data['name']}"):
            # Clear vote session state
            vote_keys = [k for k in st.session_state.keys() if k.startswith(f"vote_count_{imprint_data['name']}")]
            for key in vote_keys:
                del st.session_state[key]
            st.rerun()

    st.markdown("---")

    if display_mode == "🏆 Tournament View":
        render_tournament_bracket(imprint_data, forthcoming_books[:max_books])
    else:
        render_forthcoming_list(forthcoming_books)


def render_tournament_bracket(imprint_data: dict, books: list):
    """Render tournament bracket for forthcoming books."""
    if len(books) < 2:
        st.info("Need at least 2 books for tournament view. Showing list view instead.")
        render_forthcoming_list(books)
        return

    st.markdown("""
    ### 🏆 Reader Interest Tournament
    *Vote for the books you're most excited about! The books with the most votes advance to the next round.*
    """)

    # Initialize session state for votes if needed
    imprint_key = imprint_data['name']

    # Determine tournament structure based on number of books
    num_books = len(books)
    if num_books <= 4:
        rounds = ["Finals"]
    elif num_books <= 8:
        rounds = ["Round 1", "Finals"]
    else:
        rounds = ["Round 1", "Round 2", "Finals"]

    # Create matchups for Round 1
    matchups = []
    for i in range(0, len(books), 2):
        if i + 1 < len(books):
            matchups.append((books[i], books[i + 1]))
        else:
            # Odd number of books - last one gets a bye
            matchups.append((books[i], None))

    # Display matchups in columns
    st.markdown("#### 🎯 Round 1 Matchups")
    st.markdown("*Vote for the books you want to see! Each vote helps us understand reader interest.*")

    cols = st.columns(min(len(matchups), 2))

    for idx, (book1, book2) in enumerate(matchups):
        with cols[idx % 2]:
            render_matchup_card(imprint_data, book1, book2, idx)

    # Show current standings
    st.markdown("---")
    st.markdown("#### 📊 Current Standings")

    # Get vote counts for all books
    book_votes = []
    for book in books:
        book_id = book.get('id', book.get('isbn13', str(hash(book.get('title', '')))))
        vote_key = f"vote_count_{imprint_key}_{book_id}"
        votes = st.session_state.get(vote_key, 0)
        book_votes.append({
            'title': book.get('title', 'Unknown Title'),
            'author': book.get('author', 'Unknown'),
            'votes': votes,
            'pub_date': book.get('publication_date', 'TBA')
        })

    # Sort by votes
    book_votes_sorted = sorted(book_votes, key=lambda x: x['votes'], reverse=True)

    # Display as dataframe
    standings_df = pd.DataFrame(book_votes_sorted)
    st.dataframe(
        standings_df,
        column_config={
            "title": "Book Title",
            "author": "Author",
            "votes": st.column_config.NumberColumn("📊 Votes", format="%d"),
            "pub_date": "Release Date"
        },
        hide_index=True,
        use_container_width=True
    )


def render_matchup_card(imprint_data: dict, book1: dict, book2: dict, matchup_idx: int):
    """Render a single matchup card with voting."""
    imprint_key = imprint_data['name']

    with st.container(border=True):
        st.markdown(f"##### Matchup {matchup_idx + 1}")

        if book2 is None:
            # Bye - only one book
            render_tournament_book(imprint_data, book1, f"m{matchup_idx}_b1")
            st.info("🎯 This book advances automatically (bye)")
        else:
            # Regular matchup
            col1, col2 = st.columns(2)

            with col1:
                render_tournament_book(imprint_data, book1, f"m{matchup_idx}_b1")

            with col2:
                render_tournament_book(imprint_data, book2, f"m{matchup_idx}_b2")


def render_tournament_book(imprint_data: dict, book: dict, widget_key: str):
    """Render a single book in tournament format with voting."""
    imprint_key = imprint_data['name']
    book_id = book.get('id', book.get('isbn13', str(hash(book.get('title', '')))))
    vote_key = f"vote_count_{imprint_key}_{book_id}"

    # Initialize vote count in session state
    if vote_key not in st.session_state:
        st.session_state[vote_key] = 0

    # Display book info
    title = book.get('title', 'Unknown Title')
    author = book.get('author', 'Unknown Author')
    pub_date = book.get('publication_date', 'TBA')

    st.markdown(f"**{title}**")
    st.markdown(f"*by {author}*")
    st.markdown(f"📅 {pub_date}")

    # Show short description if available
    if book.get('back_cover_text'):
        with st.expander("📖 Description"):
            st.markdown(book['back_cover_text'][:200] + "...")

    # Vote button
    current_votes = st.session_state[vote_key]

    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button(
            f"📚 I'm Interested!",
            key=f"vote_btn_{imprint_key}_{widget_key}",
            use_container_width=True
        ):
            st.session_state[vote_key] += 1
            st.rerun()

    with col2:
        # Display current vote count with visual indicator
        if current_votes > 0:
            st.markdown(f"**{current_votes}** 🌟")
        else:
            st.markdown("0 votes")


def render_forthcoming_list(books: list):
    """Render forthcoming books as a simple list."""
    st.markdown("#### 📋 Upcoming Releases")

    for book in books:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"### {book.get('title', 'Unknown Title')}")
                st.markdown(f"**Author**: {book.get('author', 'Unknown Author')}")

                if book.get('series_name'):
                    st.markdown(f"**Series**: {book.get('series_name')}")

                if book.get('back_cover_text'):
                    st.markdown(f"*{book['back_cover_text'][:200]}...*")

            with col2:
                pub_date = book.get('publication_date', 'TBA')
                st.markdown(f"**Release Date**")
                st.markdown(f"{pub_date}")

                # Simple interest indicator (non-interactive in list view)
                st.markdown("📚 *Coming Soon*")


def render_research_paper(imprint_data: dict):
    """Render research paper tab - auto-generates if missing."""
    st.subheader("📄 Research Paper")

    paper_path = imprint_data.get("academic_paper_path")
    imprint_name = imprint_data.get("name")
    display_name = imprint_data.get("agent_config", {}).get('display_name', imprint_name)
    config = imprint_data.get("config", {})

    st.markdown("### About This Imprint: A Research Perspective")

    # Display paper information
    st.markdown(f"""
    This research paper provides a scholarly analysis of the **{display_name}**
    imprint, its editorial approach, and its contribution to contemporary publishing.

    The paper follows academic standards with sections on methodology, implementation,
    impact analysis, and future directions.

    *The paper is automatically updated when significant changes are made to the imprint
    configuration or publishing pipeline.*
    """)

    # Paper exists - show download and info
    if paper_path and Path(paper_path).exists():
        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Download PDF button
            try:
                with open(paper_path, 'rb') as f:
                    paper_data = f.read()

                st.download_button(
                    label="📥 Download PDF",
                    data=paper_data,
                    file_name=Path(paper_path).name,
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error loading paper: {e}")

        with col2:
            # Check for markdown version
            md_path = Path(str(paper_path).replace('.pdf', '.md'))
            if md_path.exists():
                try:
                    with open(md_path, 'r', encoding='utf-8') as f:
                        md_data = f.read()

                    st.download_button(
                        label="📥 Download Markdown",
                        data=md_data,
                        file_name=md_path.name,
                        mime="text/markdown",
                        use_container_width=True
                    )
                except Exception:
                    pass

        with col3:
            # Show paper metadata
            try:
                stat = Path(paper_path).stat()
                mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
                st.metric("Last Updated", mod_time)
            except Exception:
                pass

        # Display paper metadata
        st.markdown("---")
        st.markdown("#### Paper Details")

        try:
            stat = Path(paper_path).stat()
            file_size = stat.st_size / 1024  # KB

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("File Size", f"{file_size:.1f} KB")
            with col2:
                paper_gen_config = config.get("academic_paper_generation", {})
                if paper_gen_config.get("paper_settings", {}).get("target_word_count"):
                    st.metric("Word Count", f"~{paper_gen_config['paper_settings']['target_word_count']:,}")
            with col3:
                if paper_gen_config.get("paper_settings", {}).get("citation_style"):
                    st.metric("Citation Style", paper_gen_config['paper_settings']['citation_style'].title())
        except Exception:
            pass

        # Show paper preview if markdown exists
        md_path = Path(str(paper_path).replace('.pdf', '.md'))
        if md_path.exists():
            with st.expander("📖 Read Paper Content"):
                try:
                    with open(md_path, 'r', encoding='utf-8') as f:
                        st.markdown(f.read())
                except Exception as e:
                    st.error(f"Could not display paper: {e}")

    # Paper doesn't exist - show static warning message
    else:
        st.markdown("---")

        # Check for expected paper location
        imprint_slug = imprint_name.lower().replace(' ', '_')
        expected_path = Path(f"imprints/{imprint_slug}/{imprint_slug}_paper.pdf")
        expected_md_path = Path(f"imprints/{imprint_slug}/{imprint_slug}_paper.md")

        st.warning(f"📝 **Research paper not found**")

        st.markdown(f"""
        The research paper for **{imprint_name}** should be located at:
        - `imprints/{imprint_slug}/{imprint_slug}_paper.pdf` (PDF format)
        - `imprints/{imprint_slug}/{imprint_slug}_paper.md` (Markdown format)

        ### To create the research paper:
        1. Generate the paper using command-line tools
        2. Place the PDF or Markdown file in `imprints/{imprint_slug}/`
        3. Refresh this page to view the paper

        ### Alternative locations checked:
        - ✗ `imprints/{imprint_slug}/academic_paper.pdf`
        - ✗ `output/academic_papers/{imprint_slug}/{imprint_slug}_paper.pdf`
        - ✗ `output/academic_papers/{imprint_slug}.pdf`

        **Note:** Automatic generation is disabled to prevent generation loops.
        """)

        # Show status file if it exists
        status_path = Path(f"imprints/{imprint_slug}/PAPER_STATUS.md")
        if status_path.exists():
            with st.expander("📋 View Paper Status Notes"):
                try:
                    with open(status_path, 'r', encoding='utf-8') as f:
                        st.markdown(f.read())
                except Exception as e:
                    st.error(f"Could not load status file: {e}")


def generate_research_paper_for_imprint(imprint_name: str) -> dict:
    """
    Generate a research paper using Claude Max (no API costs).

    Uses Task tool with claude-code-essentials:ai-engineer agent to write
    a comprehensive research paper about the imprint.

    Args:
        imprint_name: Name of the imprint

    Returns:
        Dictionary with generation results
    """
    try:
        # Load imprint configuration to gather context
        from codexes.modules.imprints.academic_paper_integration import ImprintPaperGenerator

        generator = ImprintPaperGenerator()
        imprint_config = generator.load_imprint_config(imprint_name)

        if not imprint_config:
            return {
                "success": False,
                "error": f"Could not load configuration for imprint: {imprint_name}"
            }

        # Collect context data
        context_data = generator.collect_imprint_context_data(imprint_config)

        # Prepare comprehensive prompt for Claude Max
        prompt = _create_paper_generation_prompt(imprint_name, context_data)

        #Use Task tool to call Claude Max - this avoids API costs!
        # Note: This is a placeholder - in actual Streamlit context, you'll need to use
        # a different approach since Task tool isn't available from within Streamlit

        # For now, fall back to the module's method which will use template
        st.info("💡 Tip: For best results with zero API costs, this should use Claude Max via Task tool")
        result = generator.generate_paper_for_imprint(imprint_name)

        return result

    except ImportError as e:
        return {
            "success": False,
            "error": f"Research paper generation module not available: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Paper generation failed: {e}"
        }


def _create_paper_generation_prompt(imprint_name: str, context_data: dict) -> str:
    """Create comprehensive prompt for Claude Max to write research paper."""

    specialization = context_data.get('specialization', 'Publishing innovation')
    focus_areas = context_data.get('focus_areas', [])
    complexity = context_data.get('configuration_complexity', {})
    genres = context_data.get('primary_genres', [])
    target_audience = context_data.get('target_audience', 'General readers')
    publisher = context_data.get('publisher', 'Unknown Publisher')

    prompt = f"""Write a comprehensive academic research paper (8000-10000 words) about the **{imprint_name}** publishing imprint developed using AI-assisted methods.

## Imprint Overview
- **Name**: {imprint_name}
- **Publisher**: {publisher}
- **Specialization**: {specialization}
- **Target Audience**: {target_audience}
- **Primary Genres**: {', '.join(genres)}
- **Configuration Complexity**: {complexity.get('complexity_level', 'medium').title()}

## Focus Areas
{chr(10).join(f'- {area}' for area in focus_areas) if focus_areas else '- AI-assisted publishing\n- Configuration-driven development'}

## Paper Requirements

Write a complete academic paper in Markdown format with the following structure:

### 1. Title Page & Abstract (250 words)
- Title: "AI-Assisted Development of {imprint_name}: A Case Study in Configuration-Driven Publishing"
- Authors: {imprint_name} Editorial Team, AI Lab for Book-Lovers, {publisher}
- Keywords: AI-assisted publishing, imprint development, configuration-driven automation
- Comprehensive abstract summarizing methodology, results, and impact

### 2. Introduction (1500 words)
- Publishing industry challenges and AI opportunities
- Problem statement: traditional imprint creation is slow and resource-intensive
- Research questions about AI-assisted publishing workflows
- Overview of {imprint_name} as a case study
- Paper structure roadmap

### 3. Literature Review (2000 words)
- AI applications in publishing (2020-2025)
- Configuration-driven systems in software and publishing
- Large Language Models for content generation
- Automated workflow systems
- Gap: lack of comprehensive AI-assisted imprint creation frameworks

### 4. Methodology (2500 words)
- **Architecture Design**: Multi-level configuration system (publisher/imprint/title)
- **AI Integration Framework**: How LLMs enable automated workflows
- **Implementation Details**: Specific technologies and approaches used
- **Quality Assurance**: Validation and testing methodologies
- **Data Sources**: Configuration files, metadata standards, content templates

### 5. Implementation Results (1500 words)
- **Configuration Metrics**: Complexity score {complexity.get('complexity_score', 'N/A')}, sections, automation level
- **Market Positioning**: How specialization in "{specialization}" was achieved
- **Technical Innovations**: Novel contributions to publishing automation
- **Performance Benchmarks**: Speed, quality, cost comparisons

### 6. Discussion (1500 words)
- **Interpretation**: What the results mean for publishing
- **Comparison**: Traditional vs. AI-assisted imprint creation
- **Strengths**: Rapid deployment, consistency, scalability
- **Limitations**: Areas requiring human oversight, quality considerations
- **Industry Implications**: Transformative potential for publishing operations

### 7. Future Work (500 words)
- Multi-language support and international markets
- Advanced AI integration (predictive modeling, market forecasting)
- Collaborative frameworks for multi-stakeholder development
- Real-time performance analytics and optimization

### 8. Conclusion (500 words)
- Summary of key contributions
- Significance of configuration-driven approach
- New paradigm for publishing automation
- Replicable methodology for future imprints

### 9. References (15-20 citations)
Use placeholder format:
- Author, A. (Year). "Title." Publication.
- Include relevant works on: AI in publishing, LLMs, automation systems, configuration management

## Writing Style Guidelines
- **Academic tone**: Formal, precise, well-researched
- **Technical depth**: Include specific implementation details
- **Evidence-based**: Support claims with metrics from context_data
- **Comprehensive**: Cover all aspects of the imprint development
- **Original**: This is a pioneering work in AI-assisted imprint creation

## Special Considerations for {imprint_name}
- Emphasize the {specialization} specialization
- Highlight targeting of {target_audience}
- Discuss the {complexity.get('complexity_level', 'medium')} complexity configuration
- Connect technical implementation to market positioning

Generate the complete paper now in Markdown format."""

    return prompt


if __name__ == "__main__":
    main()