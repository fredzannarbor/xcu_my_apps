"""
Enhanced Imprint Creator (Refactored with OO Architecture)

Advanced imprint creation with wizard and one-shot modes.
This is the refactored version using Rich Domain Models and Repository Pattern.
"""

import streamlit as st
import sys
from pathlib import Path
from typing import Dict, Optional
import logging
import json

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add paths for imports
sys.path.insert(0, '/Users/fred/my-apps')
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import shared authentication (optional for testing)
try:
    from shared.auth import is_authenticated, get_user_info
    AUTH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Shared authentication not available: {e}")
    AUTH_AVAILABLE = False
    # Mock functions for testing
    def is_authenticated():
        return True
    def get_user_info():
        return {'username': 'test_user', 'user_name': 'Test User', 'user_email': 'test@example.com'}

# Import with fallback pattern
try:
    from codexes.core.llm_caller import call_model_with_prompt
except ImportError:
    from src.codexes.core.llm_caller import call_model_with_prompt

# Import new OO architecture components
try:
    from codexes.domain.models.imprint import (
        Imprint, BrandingSpecification, PublishingFocus, ImprintStatus
    )
    from codexes.domain.models.publisher_persona import (
        PublisherPersona, RiskTolerance, DecisionStyle
    )
    from codexes.infrastructure.repositories.imprint_repository import ImprintRepository
    from codexes.application.services.imprint_creation_service import ImprintCreationService
except ImportError:
    from src.codexes.domain.models.imprint import (
        Imprint, BrandingSpecification, PublishingFocus, ImprintStatus
    )
    from src.codexes.domain.models.publisher_persona import (
        PublisherPersona, RiskTolerance, DecisionStyle
    )
    from src.codexes.infrastructure.repositories.imprint_repository import ImprintRepository
    from src.codexes.application.services.imprint_creation_service import ImprintCreationService


# Dependency injection - create once, reuse
@st.cache_resource
def get_imprint_service() -> ImprintCreationService:
    """Get imprint creation service with all dependencies."""
    base_path = Path(__file__).parent.parent.parent.parent
    repository = ImprintRepository(base_path)
    # Pass call_model_with_prompt as the AI generator
    return ImprintCreationService(repository, ai_generator=call_model_with_prompt)


def main():
    """Main imprint creator interface using OO architecture."""
    # Sync session state from shared auth
    if is_authenticated():
        user_info = get_user_info()
        st.session_state.username = user_info.get('username')
        st.session_state.user_name = user_info.get('user_name')
        st.session_state.user_email = user_info.get('user_email')
        logger.info(f"User authenticated: {st.session_state.username}")

    st.title("🎨 Enhanced Imprint Creator")
    st.markdown("*Create professional publishing imprints with wizard or AI assistance*")

    # Get service
    service = get_imprint_service()

    # Mode selection
    tab1, tab2 = st.tabs(["🧙 Step-by-Step Wizard", "🤖 AI One-Shot Generation"])

    with tab1:
        render_creation_wizard(service)

    with tab2:
        render_oneshot_creator(service)


def render_creation_wizard(service: ImprintCreationService):
    """Wizard using rich domain models."""
    st.subheader("Step-by-Step Wizard")
    st.markdown("Create your imprint in 4 easy steps")

    # Initialize wizard state
    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = 1

    # Progress indicator
    progress = (st.session_state.wizard_step - 1) / 3
    st.progress(progress)

    # Step indicator
    step_names = ["Basic Info", "Publisher Persona", "Configuration", "Review & Create"]
    st.markdown(f"**Step {st.session_state.wizard_step}/4**: {step_names[st.session_state.wizard_step - 1]}")

    # Render current step
    if st.session_state.wizard_step == 1:
        render_step_basic_info()
    elif st.session_state.wizard_step == 2:
        render_step_publisher_persona()
    elif st.session_state.wizard_step == 3:
        render_step_configuration()
    elif st.session_state.wizard_step == 4:
        render_step_review_create(service)


def render_step_basic_info():
    """Step 1: Basic info - builds domain objects."""
    st.markdown("### Step 1: Basic Information")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Imprint Name*", help="The name of your publishing imprint")
        publisher = st.text_input("Publisher*", help="Parent publishing company")
        tagline = st.text_input("Tagline*", help="Memorable phrase for the imprint")

    with col2:
        charter = st.text_area(
            "Editorial Charter*",
            height=100,
            help="Mission and editorial philosophy"
        )
        mission = st.text_area(
            "Mission Statement*",
            height=100,
            help="Core mission and values"
        )

    contact_email = st.text_input(
        "Contact Email*",
        help="Official contact email for the imprint"
    )

    col_nav1, col_nav2 = st.columns([1, 1])

    with col_nav2:
        if st.button("Next →", type="primary", use_container_width=True):
            # Validation
            if not all([name, publisher, charter, tagline, mission, contact_email]):
                st.error("Please fill in all required fields")
                return

            # Create domain objects
            branding = BrandingSpecification(
                display_name=name,
                tagline=tagline,
                mission_statement=mission,
                brand_values=[],  # Will be filled in later steps
                primary_color="#1E3A8A",  # Default blue
                secondary_color="#3B82F6",
                font_family="Georgia"
            )

            # Store in session state
            st.session_state.imprint_name = name
            st.session_state.publisher = publisher
            st.session_state.charter = charter
            st.session_state.contact_email = contact_email
            st.session_state.branding = branding
            st.session_state.wizard_step = 2
            st.rerun()


def render_step_publisher_persona():
    """Step 2: Publisher persona - builds PublisherPersona object."""
    st.markdown("### Step 2: Publisher Persona")
    st.info("Define the AI-powered editorial decision maker for this imprint")

    col1, col2 = st.columns(2)

    with col1:
        persona_name = st.text_input("Persona Name*", help="Name of the editorial persona")
        bio = st.text_area(
            "Biography*",
            height=150,
            help="Professional background and expertise"
        )

        risk = st.selectbox(
            "Risk Tolerance*",
            ["Conservative", "Moderate", "Aggressive"],
            help="Approach to controversial or experimental content"
        )

        style = st.selectbox(
            "Decision Style*",
            ["Data-Driven", "Intuitive", "Collaborative", "Authoritative"],
            help="How editorial decisions are made"
        )

    with col2:
        topics = st.multiselect(
            "Preferred Topics*",
            ["Fiction", "Non-Fiction", "Business", "Science", "Technology",
             "History", "Biography", "Self-Help", "Philosophy", "Art"],
            help="Areas of editorial interest"
        )

        demographics = st.multiselect(
            "Target Demographics*",
            ["Young Adult", "Adult", "Senior", "Academic", "Professional", "General"],
            help="Primary reader segments"
        )

        vulnerabilities = st.text_area(
            "Vulnerabilities/Blind Spots",
            help="Areas requiring validation or editorial caution (optional)"
        )

    col_nav1, col_nav2 = st.columns([1, 1])

    with col_nav1:
        if st.button("← Back", use_container_width=True):
            st.session_state.wizard_step = 1
            st.rerun()

    with col_nav2:
        if st.button("Next →", type="primary", use_container_width=True):
            # Validation
            if not all([persona_name, bio, topics, demographics]):
                st.error("Please fill in all required fields")
                return

            # Create domain object
            persona = PublisherPersona(
                name=persona_name,
                bio=bio,
                risk_tolerance=RiskTolerance[risk.upper()],
                decision_style=DecisionStyle[style.upper().replace("-", "_")],
                preferred_topics=topics,
                target_demographics=demographics
            )

            # Add vulnerabilities if provided
            if vulnerabilities:
                for vuln in vulnerabilities.split('\n'):
                    if vuln.strip():
                        persona.add_vulnerability(vuln.strip())

            st.session_state.persona = persona
            st.session_state.wizard_step = 3
            st.rerun()


def render_step_configuration():
    """Step 3: Configuration - builds PublishingFocus object."""
    st.markdown("### Step 3: Publishing Configuration")

    col1, col2 = st.columns(2)

    with col1:
        genres = st.multiselect(
            "Primary Genres*",
            ["Fiction", "Non-Fiction", "Mystery", "Romance", "Science Fiction",
             "Fantasy", "Thriller", "Biography", "History", "Business",
             "Self-Help", "Poetry", "Drama"],
            help="Main genre focus areas"
        )

        audience = st.text_input(
            "Target Audience*",
            help="Main readership demographic description"
        )

        languages = st.multiselect(
            "Supported Languages",
            ["English", "Spanish", "French", "German", "Chinese", "Japanese"],
            default=["English"],
            help="Publishing languages"
        )

    with col2:
        price = st.number_input(
            "Standard Price Point*",
            min_value=0.0,
            value=24.99,
            step=0.50,
            help="Typical book pricing"
        )

        books_per_year = st.number_input(
            "Books Per Year*",
            min_value=1,
            value=12,
            help="Target catalog size annually"
        )

        page_count = st.number_input(
            "Standard Page Count",
            min_value=50,
            value=200,
            help="Typical book length"
        )

    # Brand colors
    st.markdown("#### Brand Colors")
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        primary_color = st.color_picker("Primary Color", "#1E3A8A")

    with col_c2:
        secondary_color = st.color_picker("Secondary Color", "#3B82F6")

    # Brand values
    brand_values = st.multiselect(
        "Brand Values",
        ["Quality", "Innovation", "Excellence", "Integrity", "Creativity",
         "Accessibility", "Diversity", "Sustainability"],
        default=["Quality", "Innovation"],
        help="Core values that define the imprint"
    )

    col_nav1, col_nav2 = st.columns([1, 1])

    with col_nav1:
        if st.button("← Back", use_container_width=True):
            st.session_state.wizard_step = 2
            st.rerun()

    with col_nav2:
        if st.button("Next →", type="primary", use_container_width=True):
            # Validation
            if not all([genres, audience, price > 0, books_per_year > 0]):
                st.error("Please fill in all required fields")
                return

            # Create domain object
            publishing_focus = PublishingFocus(
                primary_genres=genres,
                target_audience=audience,
                price_point=price,
                books_per_year=books_per_year
            )

            # Update branding with colors and values
            branding = st.session_state.branding
            branding.primary_color = primary_color
            branding.secondary_color = secondary_color
            branding.brand_values = brand_values

            st.session_state.publishing_focus = publishing_focus
            st.session_state.branding = branding
            st.session_state.languages = languages
            st.session_state.page_count = page_count
            st.session_state.wizard_step = 4
            st.rerun()


def render_step_review_create(service: ImprintCreationService):
    """Step 4: Review & Create - uses service to persist."""
    st.markdown("### Step 4: Review & Create")

    # Display summary
    st.markdown("#### Imprint Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Name**: {st.session_state.imprint_name}")
        st.write(f"**Publisher**: {st.session_state.publisher}")
        st.write(f"**Tagline**: {st.session_state.branding.tagline}")
        st.write(f"**Charter**: {st.session_state.charter}")

    with col2:
        st.write(f"**Genres**: {', '.join(st.session_state.publishing_focus.primary_genres)}")
        st.write(f"**Target Audience**: {st.session_state.publishing_focus.target_audience}")
        st.write(f"**Price Point**: ${st.session_state.publishing_focus.price_point:.2f}")
        st.write(f"**Books/Year**: {st.session_state.publishing_focus.books_per_year}")

    # Publisher persona summary
    if hasattr(st.session_state, 'persona'):
        with st.expander("👤 Publisher Persona Details"):
            persona = st.session_state.persona
            st.write(f"**Name**: {persona.name}")
            st.write(f"**Risk Tolerance**: {persona.risk_tolerance.value}")
            st.write(f"**Decision Style**: {persona.decision_style.value}")
            st.write(f"**Preferred Topics**: {', '.join(persona.preferred_topics)}")

    col_nav1, col_nav2 = st.columns([1, 1])

    with col_nav1:
        if st.button("← Back", use_container_width=True):
            st.session_state.wizard_step = 3
            st.rerun()

    with col_nav2:
        if st.button("🚀 Create Imprint", type="primary", use_container_width=True):
            try:
                # Use service to create imprint
                imprint = service.create_from_wizard(
                    name=st.session_state.imprint_name,
                    publisher=st.session_state.publisher,
                    charter=st.session_state.charter,
                    branding=st.session_state.branding,
                    publishing_focus=st.session_state.publishing_focus,
                    persona=st.session_state.get('persona')
                )

                st.success(f"✅ Created imprint: {imprint.display_name}")
                st.balloons()

                # Display created imprint details
                with st.expander("📋 Imprint Details", expanded=True):
                    st.json(imprint.to_dict())

                # Reset wizard
                st.session_state.wizard_step = 1
                st.session_state.pop('imprint_name', None)
                st.session_state.pop('publisher', None)
                st.session_state.pop('charter', None)
                st.session_state.pop('branding', None)
                st.session_state.pop('publishing_focus', None)
                st.session_state.pop('persona', None)

            except ValueError as e:
                st.error(f"Failed to create imprint: {e}")
                logger.error(f"Imprint creation failed: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
                logger.error(f"Unexpected error during imprint creation: {e}", exc_info=True)


def render_oneshot_creator(service: ImprintCreationService):
    """One-shot AI generation using service."""
    st.subheader("AI One-Shot Generation")
    st.markdown("Generate a complete imprint configuration with a single AI call")

    # Quick examples
    with st.expander("💡 Quick Examples"):
        if st.button("Tech & AI Publisher"):
            st.session_state.oneshot_description = "A cutting-edge publisher focused on artificial intelligence, machine learning, and emerging technologies"
        if st.button("Literary Fiction Imprint"):
            st.session_state.oneshot_description = "A prestigious imprint dedicated to literary fiction with emphasis on diverse voices and experimental narratives"
        if st.button("Business & Leadership"):
            st.session_state.oneshot_description = "A business-focused imprint publishing practical guides for entrepreneurs and corporate leaders"

    # Main form
    description = st.text_area(
        "Describe Your Imprint Concept",
        value=st.session_state.get('oneshot_description', ''),
        height=150,
        help="Describe the imprint's focus, audience, and unique positioning"
    )

    col1, col2 = st.columns(2)

    with col1:
        model = st.selectbox(
            "AI Model",
            ["gemini/gemini-2.5-pro", "claude-opus-4", "gpt-5", "gemini/gemini-2.5-flash"],
            help="Frontier model for generation"
        )

    with col2:
        temperature = st.slider(
            "Temperature",
            0.0, 1.0, 0.3,
            help="Higher = more creative, Lower = more focused"
        )

    # Upload partial config
    uploaded_file = st.file_uploader(
        "Upload Partial Configuration (Optional)",
        type=['json'],
        help="Upload a partial config to guide generation"
    )

    proposed_title = st.text_input(
        "Proposed Imprint Name (Optional)",
        help="Suggest a name for the AI to use"
    )

    if st.button("🤖 Generate Imprint", type="primary"):
        if not description:
            st.error("Please provide a description of your imprint concept")
            return

        with st.spinner("Generating complete imprint configuration..."):
            try:
                # Load partial config if provided
                partial_config = None
                if uploaded_file:
                    partial_config = json.load(uploaded_file)

                # Generate using service
                imprint = service.create_from_ai(
                    description=description,
                    model=model,
                    temperature=temperature,
                    partial_config=partial_config
                )

                st.success(f"✅ Generated imprint: {imprint.display_name}")
                st.balloons()

                # Display result
                render_oneshot_result(imprint)

            except Exception as e:
                st.error(f"Failed to generate imprint: {e}")
                logger.error(f"AI generation failed: {e}", exc_info=True)


def render_oneshot_result(imprint: Imprint):
    """Display the generated imprint result."""
    st.markdown("### Generated Imprint")

    # Summary
    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Name**: {imprint.display_name}")
        st.write(f"**Tagline**: {imprint.branding.tagline}")
        st.write(f"**Status**: {imprint.status.value}")

    with col2:
        genres = ', '.join(imprint.publishing_focus.primary_genres) if imprint.publishing_focus.primary_genres else 'Not specified'
        st.write(f"**Genres**: {genres}")
        price = f"${imprint.publishing_focus.price_point:.2f}" if imprint.publishing_focus.price_point else 'Not specified'
        st.write(f"**Price Point**: {price}")
        books = imprint.publishing_focus.books_per_year if imprint.publishing_focus.books_per_year else 'Not specified'
        st.write(f"**Books/Year**: {books}")

    # Full details
    with st.expander("📋 Full Configuration", expanded=False):
        st.json(imprint.to_dict())

    # Actions
    col_a1, col_a2 = st.columns(2)

    with col_a1:
        if st.button("✏️ Edit in Wizard"):
            # Load into wizard
            st.session_state.imprint_name = imprint.name
            st.session_state.publisher = imprint.publisher
            st.session_state.charter = imprint.charter
            st.session_state.branding = imprint.branding
            st.session_state.publishing_focus = imprint.publishing_focus
            st.session_state.wizard_step = 1
            st.rerun()

    with col_a2:
        if st.button("🚀 Activate Imprint"):
            try:
                service.activate_imprint(imprint.slug)
                st.success(f"Activated imprint: {imprint.display_name}")
            except Exception as e:
                st.error(f"Failed to activate: {e}")


if __name__ == "__main__":
    main()
