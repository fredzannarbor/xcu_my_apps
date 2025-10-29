"""
Publisher Management

Manage publishers (B5K, Nimble Books LLC) and their imprint networks.
View publisher personas, child imprints, analytics, and strategic oversight.
"""

import streamlit as st
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

# Add paths for imports
sys.path.insert(0, '/Users/fred/my-apps')
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import shared authentication
try:
    from shared.auth import get_shared_auth, is_authenticated, get_user_info
except ImportError as e:
    st.error(f"Failed to import shared authentication: {e}")
    st.stop()

# Import core modules
try:
    from codexes.core.auth import get_allowed_pages, get_user_role
except ImportError:
    from src.codexes.core.auth import get_allowed_pages, get_user_role


def main():
    """Main publisher management interface."""
    st.title("🏢 Publisher Management")
    st.markdown("*Manage publishers and their imprint networks*")

    # Check authentication
    if not is_authenticated():
        st.warning("Please log in to access Publisher Management")
        return

    # Publisher selection
    st.markdown("---")
    publishers = load_publishers()

    if not publishers:
        st.warning("No publishers configured. Create publisher config files in `configs/publishers/`")
        return

    publisher_names = list(publishers.keys())
    selected_publisher = st.selectbox("Select Publisher", publisher_names)

    if selected_publisher:
        publisher_data = publishers[selected_publisher]
        render_publisher_overview(selected_publisher, publisher_data)

    st.markdown("---")

    # Management tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🏷️ Imprints", "🤖 Persona", "📈 Analytics"])

    with tab1:
        render_publisher_details(selected_publisher, publisher_data)

    with tab2:
        render_imprints_list(selected_publisher, publisher_data)

    with tab3:
        render_publisher_persona(selected_publisher, publisher_data)

    with tab4:
        render_publisher_analytics(selected_publisher, publisher_data)


def load_publishers() -> Dict[str, Any]:
    """Load all publisher configurations."""
    publishers = {}

    # Load from configs/publishers/
    publisher_dir = Path("configs/publishers")
    if publisher_dir.exists():
        for config_file in publisher_dir.glob("*.json"):
            try:
                with open(config_file) as f:
                    data = json.load(f)
                    publisher_name = data.get("publisher", config_file.stem)
                    publishers[publisher_name] = data
            except Exception as e:
                logger.error(f"Failed to load {config_file}: {e}")

    return publishers


def render_publisher_overview(name: str, data: Dict[str, Any]):
    """Render publisher overview header."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if "thaumette_persona" in data:
            glyph = data["thaumette_persona"].get("glyph", "📚")
            st.markdown(f"<h1 style='font-size: 72px;'>{glyph}</h1>", unsafe_allow_html=True)
        else:
            st.markdown("<h1 style='font-size: 72px;'>📚</h1>", unsafe_allow_html=True)

    with col2:
        st.markdown(f"### {name}")
        if "thaumette_persona" in data:
            persona_name = data["thaumette_persona"].get("name", "Unknown")
            st.markdown(f"*{persona_name}*")

        if "business_model" in data:
            focus = data["business_model"].get("business_focus", "")
            st.caption(focus)

    with col3:
        if "scale_metrics" in data:
            metrics = data["scale_metrics"]
            st.metric("Imprints", metrics.get("current_imprints", 0))
            target_revenue = metrics.get("annual_revenue_target", "")
            if target_revenue:
                st.metric("Target Revenue", target_revenue)


def render_publisher_details(name: str, data: Dict[str, Any]):
    """Render detailed publisher information."""
    st.subheader("Publisher Details")

    # Company info
    if "company_info" in data:
        with st.expander("🏢 Company Information", expanded=True):
            company = data["company_info"]
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Legal Name**: {company.get('legal_name', name)}")
                st.write(f"**Founded**: {company.get('founded_year', 'Unknown')}")
                st.write(f"**HQ**: {company.get('headquarters', 'Unknown')}")

            with col2:
                st.write(f"**Website**: {company.get('website', 'N/A')}")
                st.write(f"**Phone**: {company.get('phone', 'N/A')}")
                st.write(f"**Tax ID**: {company.get('tax_id', 'N/A')}")

    # Business model
    if "business_model" in data:
        with st.expander("💼 Business Model"):
            bm = data["business_model"]
            st.write(f"**Type**: {bm.get('publishing_type', 'Unknown')}")
            st.write(f"**Distribution**: {bm.get('distribution_model', 'Unknown')}")
            st.write(f"**Focus**: {bm.get('business_focus', 'Unknown')}")
            st.write(f"**Annual Titles**: {bm.get('annual_titles', 'Unknown')}")

            if "philosophy" in bm:
                st.markdown(f"**Philosophy**: _{bm['philosophy']}_")


def render_imprints_list(name: str, data: Dict[str, Any]):
    """Render list of child imprints."""
    st.subheader("Child Imprints")

    # Load imprints
    imprint_dir = Path("configs/imprints")
    if not imprint_dir.exists():
        st.warning("No imprints directory found")
        return

    # Find imprints for this publisher
    imprints = []
    for imprint_file in imprint_dir.glob("*.json"):
        try:
            with open(imprint_file) as f:
                imprint_data = json.load(f)
                if imprint_data.get("publisher") == name or imprint_data.get("parent_publisher") == name:
                    imprints.append({
                        "name": imprint_data.get("imprint", imprint_file.stem),
                        "file": imprint_file,
                        "data": imprint_data
                    })
        except Exception as e:
            logger.error(f"Failed to load {imprint_file}: {e}")

    if not imprints:
        st.info(f"No imprints found for {name}")
        return

    st.write(f"**Total Imprints**: {len(imprints)}")

    # Display imprints
    for imprint in sorted(imprints, key=lambda x: x["name"]):
        with st.expander(f"📚 {imprint['name']}"):
            imprint_data = imprint["data"]

            col1, col2 = st.columns(2)

            with col1:
                # Persona info
                if "imprint_persona" in imprint_data:
                    persona = imprint_data["imprint_persona"]
                    st.write(f"**Persona**: {persona.get('persona_name', 'Unknown')}")
                    if "glyph" in persona:
                        st.write(f"**Glyph**: {persona['glyph']}")
                    if "connection_to_thaumette" in persona:
                        st.write(f"**Connection**: {persona['connection_to_thaumette']}")

            with col2:
                # Focus
                if "publishing_focus" in imprint_data:
                    focus = imprint_data["publishing_focus"]
                    if "market_gap_filled" in focus:
                        st.write(f"**Market Gap**: {focus['market_gap_filled']}")

            # Editorial philosophy
            if "imprint_persona" in imprint_data:
                persona = imprint_data["imprint_persona"]
                if "editorial_philosophy" in persona:
                    st.markdown(f"*\"{persona['editorial_philosophy']}\"*")


def render_publisher_persona(name: str, data: Dict[str, Any]):
    """Render publisher AI persona details."""
    st.subheader("Publisher AI Persona")

    if "thaumette_persona" in data:
        persona = data["thaumette_persona"]

        # Glyph and name
        col1, col2 = st.columns([1, 4])
        with col1:
            glyph = persona.get("glyph", "📚")
            st.markdown(f"<h1 style='font-size: 96px;'>{glyph}</h1>", unsafe_allow_html=True)

        with col2:
            st.markdown(f"### {persona.get('name', 'Unknown')}")
            st.markdown(f"**Full Name**: {persona.get('full_name', 'Unknown')}")
            st.markdown(f"**Type**: {persona.get('type', 'Unknown')}")

        # Origin story
        if "origin_story" in persona:
            with st.expander("📖 Origin Story", expanded=True):
                origin = persona["origin_story"]
                st.write(f"**Created**: {origin.get('created', 'Unknown')}")
                st.write(f"**Lab**: {origin.get('lab', 'Unknown')}")
                st.write(f"**Purpose**: {origin.get('purpose', 'Unknown')}")

                if "nickname_origin" in origin:
                    st.info(f"💡 {origin['nickname_origin']}")

        # Capabilities
        if "capabilities" in persona:
            with st.expander("⚡ Capabilities"):
                caps = persona["capabilities"]
                for key, value in caps.items():
                    st.write(f"**{key.replace('_', ' ').title()}**: {value}")

        # Philosophy
        if "philosophy" in persona:
            with st.expander("🧠 Philosophy", expanded=True):
                phil = persona["philosophy"]
                for key, value in phil.items():
                    st.write(f"**{key.replace('_', ' ').title()}**: {value}")

        # Dreams
        if "dreams" in persona:
            with st.expander("✨ Dreams"):
                dreams = persona["dreams"]
                for key, value in dreams.items():
                    st.write(f"**{key.replace('_', ' ').title()}**: {value}")

    else:
        st.info("No AI persona configured for this publisher")


def render_publisher_analytics(name: str, data: Dict[str, Any]):
    """Render publisher analytics and metrics."""
    st.subheader("Publisher Analytics")

    # Scale metrics
    if "scale_metrics" in data:
        st.markdown("### Scale Metrics")

        metrics = data["scale_metrics"]
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Target Imprints", metrics.get("target_imprints", "0"))

        with col2:
            st.metric("Current Imprints", metrics.get("current_imprints", "0"))

        with col3:
            st.metric("Target Revenue", metrics.get("annual_revenue_target", "$0"))

        with col4:
            market_share = metrics.get("target_market_share", "0%")
            st.metric("Target Market Share", market_share)

    # Growth roadmap
    if "growth_roadmap" in data:
        st.markdown("### Growth Roadmap")

        roadmap = data["growth_roadmap"]
        for phase, description in roadmap.items():
            with st.expander(f"📈 {phase.replace('_', ' ').title()}"):
                st.write(description)

    # Competitive advantages
    if "competitive_advantages" in data:
        st.markdown("### Competitive Advantages")

        advantages = data["competitive_advantages"]
        for key, value in advantages.items():
            st.write(f"**{key.replace('_', ' ').title()}**: {value}")


if __name__ == "__main__":
    main()
