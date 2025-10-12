"""
Enhanced Imprint Creation Page

Advanced imprint creation interface using the new imprint management
architecture with publisher personas and continuous ideation setup.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import logging
import json
from typing import Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add paths for imports
sys.path.insert(0, '/Users/fred/my-apps')
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from codexes.core.auth import get_allowed_pages, get_user_role
except ImportError:
    from src.codexes.core.auth import get_allowed_pages, get_user_role

# Import enhanced imprint management
try:
    from codexes.modules.imprints.services.imprint_manager import ImprintManager
    from codexes.modules.imprints.models.imprint_core import ImprintType, ImprintStatus
    from codexes.modules.imprints.models.publisher_persona import PublisherPersona, RiskTolerance, DecisionStyle
except ImportError as e:
    try:
        from src.codexes.modules.imprints.services.imprint_manager import ImprintManager
        from src.codexes.modules.imprints.models.imprint_core import ImprintType, ImprintStatus
        from src.codexes.modules.imprints.models.publisher_persona import PublisherPersona, RiskTolerance, DecisionStyle
    except ImportError as e2:
        st.error(f"Enhanced imprint management system not available: {e2}")
        st.stop()

from shared.ui import render_unified_sidebar

logger = logging.getLogger(__name__)


def main():
    """Main enhanced imprint creation interface."""
    st.set_page_config(page_title="Enhanced Imprint Creator", layout="wide")

    render_unified_sidebar(
        app_name="Codexes Factory - Enhanced Imprint Creator",
        nav_items=[]
    )

    st.title("🚀 Enhanced Imprint Creator")
    st.markdown("Create sophisticated publishing imprints with publisher personas and automated ideation")
    
    # Show what users get
    with st.expander("🎁 What You Get", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### Core Imprint Package
            - ✅ **Complete Configuration** - All LSI, metadata, and production settings
            - ✅ **Custom Templates** - Branded LaTeX templates for books and covers  
            - ✅ **Prompt Library** - LLM prompts customized for your editorial vision
            - ✅ **Quality Standards** - Sensitivity reading and editorial guidelines
            - ✅ **Multi-format Support** - Print, digital, and international distribution
            """)
        
        with col2:
            st.markdown("""
            ### Advanced Features  
            - 🤖 **Publisher Persona** - AI-driven content acquisition guidance
            - 💡 **Continuous Ideation** - Always-on concept generation
            - 📊 **Analytics Dashboard** - Performance tracking and insights
            - 🎯 **Content Validation** - Automated constraint checking
            - 🔄 **Pipeline Integration** - Seamless book production workflow
            """)
    
    # Check for uploaded imprint ideas
    render_uploaded_ideas_section()
    
    # Main creation interface
    render_creation_wizard()


def render_uploaded_ideas_section():
    """Show uploaded imprint ideas from Tournament page for enhancement."""
    
    # Check for uploaded ideas file
    uploaded_ideas_file = Path("data/uploaded_imprint_ideas.json")
    
    if uploaded_ideas_file.exists():
        try:
            with open(uploaded_ideas_file, 'r') as f:
                uploaded_data = json.load(f)
            
            ideas = uploaded_data.get("ideas", [])
            upload_time = uploaded_data.get("uploaded_at", "Unknown")
            filename = uploaded_data.get("filename", "Unknown file")
            
            if ideas:
                st.markdown("---")
                st.subheader("📤 Uploaded Imprint Ideas (from Tournament)")
                st.markdown(f"*Loaded {len(ideas)} ideas from {filename} uploaded at {upload_time[:19].replace('T', ' ')}*")
                
                # Show ideas that need enhancement
                incomplete_ideas = []
                for idea in ideas:
                    completeness = calculate_idea_completeness(idea)
                    if completeness < 0.8:  # Less than 80% complete
                        incomplete_ideas.append((idea, completeness))
                
                if incomplete_ideas:
                    st.warning(f"🔧 {len(incomplete_ideas)} uploaded ideas need enhancement")
                    
                    # Show incomplete ideas with enhance buttons
                    for idea, completeness in incomplete_ideas:
                        with st.expander(f"🔧 Enhance: {idea.get('name', 'Unnamed Idea')} ({completeness:.1%} complete)"):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.write(f"**Charter**: {idea.get('charter', 'Missing')}")
                                st.write(f"**Focus**: {idea.get('focus', 'Missing')}")
                                st.write(f"**Tagline**: {idea.get('tagline', 'Missing')}")
                                st.write(f"**Target Audience**: {idea.get('target_audience', 'Missing')}")
                                st.write(f"**Competitive Advantage**: {idea.get('competitive_advantage', 'Missing')}")
                            
                            with col2:
                                if st.button(f"✨ Enhance This Idea", key=f"enhance_{idea.get('name', 'idea')}"):
                                    enhance_uploaded_idea(idea)
                
                else:
                    st.success("✅ All uploaded ideas are sufficiently complete!")
                    
                # Show complete ideas with create buttons
                complete_ideas = [idea for idea in ideas if calculate_idea_completeness(idea) >= 0.8]
                if complete_ideas:
                    st.markdown("### 🚀 Ready to Create")
                    for idea in complete_ideas:
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            st.write(f"**{idea.get('name', 'Unnamed')}**: {idea.get('charter', 'No charter')[:100]}...")
                        
                        with col2:
                            if st.button(f"Create Imprint", key=f"create_{idea.get('name', 'idea')}"):
                                load_idea_into_wizard(idea)
                                
        except Exception as e:
            st.error(f"Error loading uploaded ideas: {e}")


def calculate_idea_completeness(idea: Dict) -> float:
    """Calculate completeness percentage of an imprint idea."""
    required_fields = ['name', 'charter', 'focus', 'tagline', 'target_audience', 'competitive_advantage']
    filled_fields = 0
    
    for field in required_fields:
        value = idea.get(field, '')
        if value and str(value).strip() and str(value).strip().lower() != 'nan':
            filled_fields += 1
    
    return filled_fields / len(required_fields)


def enhance_uploaded_idea(idea: Dict):
    """Use AI to enhance an incomplete uploaded idea."""
    from codexes.core.llm_caller import call_model_with_prompt
    
    st.info("🤖 Enhancing imprint idea with AI...")
    
    # Identify missing fields
    required_fields = {
        'charter': 'Editorial mission and publishing philosophy',
        'focus': 'Primary focus areas and genres', 
        'tagline': 'Brand tagline or slogan',
        'target_audience': 'Primary target audience',
        'competitive_advantage': 'Unique competitive advantage'
    }
    
    missing_fields = []
    existing_info = []
    
    for field, description in required_fields.items():
        value = idea.get(field, '')
        if not value or str(value).strip().lower() in ['', 'nan', 'missing']:
            missing_fields.append(f"- {field}: {description}")
        else:
            existing_info.append(f"- {field}: {value}")
    
    if missing_fields:
        prompt = {
            "messages": [{
                "role": "user",
                "content": f"""Enhance this incomplete imprint idea by filling in missing information:

Imprint Name: {idea.get('name', 'Unknown')}

Existing Information:
{chr(10).join(existing_info)}

Missing Information Needed:
{chr(10).join(missing_fields)}

Please provide the missing information that would make this a complete, compelling imprint concept. Keep it consistent with any existing information provided.

Format as JSON:
{{
  "enhanced_charter": "Enhanced editorial mission",
  "enhanced_focus": "Enhanced focus areas", 
  "enhanced_tagline": "Enhanced tagline",
  "enhanced_target_audience": "Enhanced target audience",
  "enhanced_competitive_advantage": "Enhanced competitive advantage",
  "enhancement_reasoning": "Why these enhancements fit the concept"
}}"""
            }]
        }
        
        try:
            response = call_model_with_prompt(
                model_name="gemini/gemini-2.5-flash",
                prompt_config=prompt,
                response_format_type="json_object"
            )
            
            if response.get("parsed_content"):
                enhancements = response["parsed_content"]
                
                # Update the idea with enhancements
                enhanced_idea = idea.copy()
                field_mapping = {
                    'enhanced_charter': 'charter',
                    'enhanced_focus': 'focus',
                    'enhanced_tagline': 'tagline', 
                    'enhanced_target_audience': 'target_audience',
                    'enhanced_competitive_advantage': 'competitive_advantage'
                }
                
                for enhanced_key, original_key in field_mapping.items():
                    if enhanced_key in enhancements and (not enhanced_idea.get(original_key) or str(enhanced_idea.get(original_key)).strip().lower() in ['', 'nan']):
                        enhanced_idea[original_key] = enhancements[enhanced_key]
                
                # Update the saved file
                uploaded_ideas_file = Path("data/uploaded_imprint_ideas.json")
                with open(uploaded_ideas_file, 'r') as f:
                    uploaded_data = json.load(f)
                
                # Find and update the idea
                for i, stored_idea in enumerate(uploaded_data["ideas"]):
                    if stored_idea.get("name") == idea.get("name"):
                        uploaded_data["ideas"][i] = enhanced_idea
                        break
                
                with open(uploaded_ideas_file, 'w') as f:
                    json.dump(uploaded_data, f, indent=2)
                
                st.success("✨ Idea enhanced successfully!")
                st.markdown(f"**Reasoning**: {enhancements.get('enhancement_reasoning', 'Enhanced for completeness')}")
                st.rerun()
                
        except Exception as e:
            st.error(f"Error enhancing idea: {e}")


def load_idea_into_wizard(idea: Dict):
    """Load an uploaded idea into the creation wizard."""
    st.session_state.imprint_data = {
        "name": idea.get('name', ''),
        "charter": idea.get('charter', ''),
        "focus_areas": idea.get('focus', '').split(', ') if idea.get('focus') else [],
        "tagline": idea.get('tagline', ''),
        "target_audience": idea.get('target_audience', ''),
        "competitive_advantage": idea.get('competitive_advantage', ''),
        "source": "uploaded_idea"
    }
    
    st.session_state.creation_step = 2  # Skip basic info since we have it
    st.success(f"✅ Loaded '{idea.get('name')}' into imprint creator!")
    st.rerun()


def render_creation_wizard():
    """Render the step-by-step imprint creation wizard."""

    # Initialize session state for wizard
    if "creation_step" not in st.session_state:
        st.session_state.creation_step = 1

    if "imprint_data" not in st.session_state:
        st.session_state.imprint_data = {}

    if "creation_mode" not in st.session_state:
        st.session_state.creation_mode = "wizard"

    # Creation mode selector
    st.subheader("🎯 Choose Creation Method")
    mode_col1, mode_col2 = st.columns(2)

    with mode_col1:
        if st.button("🧙‍♂️ Step-by-Step Wizard", use_container_width=True, type="secondary" if st.session_state.creation_mode == "oneshot" else "primary"):
            st.session_state.creation_mode = "wizard"
            st.rerun()
        st.caption("Guided setup with full control over each setting")

    with mode_col2:
        if st.button("⚡ One-Shot Generation", use_container_width=True, type="secondary" if st.session_state.creation_mode == "wizard" else "primary"):
            st.session_state.creation_mode = "oneshot"
            st.rerun()
        st.caption("AI creates complete imprint with publisher persona & full configuration using frontier models")

    st.markdown("---")

    # Render appropriate interface based on mode
    if st.session_state.creation_mode == "oneshot":
        render_oneshot_creator()
    else:
        render_wizard_steps()


def render_wizard_steps():
    """Render the traditional step-by-step wizard interface."""

    # Progress indicator
    progress = st.session_state.creation_step / 4
    st.progress(progress, f"Step {st.session_state.creation_step} of 4")

    # Non-linear step navigation
    col1, col2, col3, col4 = st.columns(4)
    steps = [
        ("1️⃣ Basic Info", 1),
        ("2️⃣ Publisher Persona", 2),
        ("3️⃣ Configuration", 3),
        ("4️⃣ Review & Create", 4)
    ]

    for i, (step_name, step_num) in enumerate(steps):
        with [col1, col2, col3, col4][i]:
            # Make each step clickable
            if st.button(step_name, key=f"nav_step_{step_num}", use_container_width=True):
                st.session_state.creation_step = step_num
                st.rerun()

            # Show current step indicator
            if step_num == st.session_state.creation_step:
                st.markdown("**👆 Current Step**")

    st.markdown("---")

    # Render current step
    if st.session_state.creation_step == 1:
        render_step_basic_info()
    elif st.session_state.creation_step == 2:
        render_step_publisher_persona()
    elif st.session_state.creation_step == 3:
        render_step_configuration()
    elif st.session_state.creation_step == 4:
        render_step_review_create()


def render_oneshot_creator():
    """Render the one-shot AI-powered imprint creator."""
    st.subheader("⚡ One-Shot Imprint Generation")
    st.markdown("Describe your imprint concept and let AI create a complete, professional configuration including publisher persona, business settings, and technical specifications.")

    with st.container():
        # Input form
        with st.form("oneshot_form"):
            st.markdown("### 📝 Describe Your Imprint")

            # Optional proposed title
            proposed_title = st.text_input(
                "Proposed Imprint Title (optional)",
                placeholder="Alternative or working title for the imprint",
                help="Optional: Provide a proposed title if you have one in mind"
            )

            # Primary description
            description = st.text_area(
                "Imprint Description",
                placeholder="Example: A technology-focused imprint specializing in AI ethics, emerging technologies, and future studies. Target audience includes academics, professionals, and tech-savvy readers interested in responsible technology development.",
                height=150,
                help="Provide a detailed description including focus areas, target audience, specialization, and any unique characteristics."
            )

            col1, col2 = st.columns(2)

            with col1:
                # Model selection
                model_options = [
                    "anthropic/claude-4",
                    "openai/gpt-5",
                    "gemini/gemini-2.5-flash",
                    "gemini/gemini-2.5-pro",
                ]
                selected_model = st.selectbox(
                    "AI Model",
                    options=model_options,
                    index=0,
                    help="Choose the AI model for generation. Frontier models provide best results."
                )

                temperature = st.slider(
                    "Creativity Level",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.3,
                    step=0.1,
                    help="Lower values = more conservative, Higher values = more creative"
                )

            with col2:
                # Optional partial config upload
                st.markdown("**Optional: Upload Partial Config**")
                uploaded_file = st.file_uploader(
                    "Upload partial configuration",
                    type=['json'],
                    help="Upload a JSON file with partial imprint configuration to build upon"
                )

            # Generate button
            generate_clicked = st.form_submit_button(
                "🚀 Generate Complete Imprint",
                type="primary",
                use_container_width=True
            )

        # Quick examples (outside form to avoid button restriction)
        st.markdown("### 💡 Quick Examples")
        st.markdown("Click any example to automatically fill the description:")

        col1, col2, col3 = st.columns(3)
        example_buttons = [
            ("🔬 Science Publisher", "A scientific publishing imprint focused on breakthrough research, peer-reviewed studies, and academic excellence. Specializes in physics, chemistry, and interdisciplinary sciences for academic and research professionals."),
            ("📚 Literary Fiction", "An independent literary fiction imprint dedicated to emerging voices and experimental narratives. Focuses on contemporary literature, diverse perspectives, and innovative storytelling for literary enthusiasts."),
            ("💼 Business Strategy", "A business-focused imprint specializing in leadership, strategy, and organizational development. Target audience includes executives, consultants, and business professionals seeking actionable insights.")
        ]

        for i, (label, example_desc) in enumerate(example_buttons):
            with [col1, col2, col3][i]:
                if st.button(label, key=f"example_{label}", use_container_width=True):
                    st.session_state.oneshot_description = example_desc
                    st.rerun()

        # Use example if set
        if hasattr(st.session_state, 'oneshot_description'):
            description = st.session_state.oneshot_description
            st.info(f"📝 Using example: {description[:100]}...")
            # Clear the example after use to allow form to work properly
            if generate_clicked:
                delattr(st.session_state, 'oneshot_description')

        # Generation logic
        if generate_clicked and description:
            generate_oneshot_imprint(description, selected_model, temperature, uploaded_file, proposed_title)
        elif generate_clicked and not description:
            st.error("Please provide an imprint description before generating.")

        # Show generation status
        if hasattr(st.session_state, 'oneshot_generating') and st.session_state.oneshot_generating:
            st.info("🤖 Generating your imprint configuration... This may take 30-60 seconds.")

        # Show generated result
        if hasattr(st.session_state, 'oneshot_result'):
            render_oneshot_result(st.session_state.oneshot_result)


def generate_oneshot_imprint(description: str, model: str, temperature: float, uploaded_file, proposed_title: str = ""):
    """Generate imprint configuration using the one-shot generator."""
    try:
        # Import the one-shot generator
        try:
            from codexes.modules.imprints.generate_oneshot_imprint import (
                load_template_and_exemplar,
                create_oneshot_prompt,
                generate_imprint_config
            )
        except ModuleNotFoundError:
            from src.codexes.modules.imprints.generate_oneshot_imprint import (
                load_template_and_exemplar,
                create_oneshot_prompt,
                generate_imprint_config
            )

        st.session_state.oneshot_generating = True

        # Load partial config if uploaded
        partial_config = None
        if uploaded_file is not None:
            try:
                partial_config = json.loads(uploaded_file.read().decode('utf-8'))
                st.success(f"✅ Loaded partial configuration: {uploaded_file.name}")
            except Exception as e:
                st.error(f"Error reading uploaded file: {e}")
                return

        # Add proposed title to description if provided
        enhanced_description = description
        if proposed_title:
            enhanced_description = f"Proposed Title: {proposed_title}\n\n{description}"

        with st.spinner("🤖 AI is creating your imprint configuration..."):
            # Load template and exemplar
            template, exemplar = load_template_and_exemplar()

            # Create prompt
            prompt = create_oneshot_prompt(template, exemplar, enhanced_description, partial_config)

            # Generate configuration
            config = generate_imprint_config(prompt, model, temperature)

            # Store result (with proposed title if provided)
            if proposed_title:
                config["proposed_title"] = proposed_title
            st.session_state.oneshot_result = config
            st.session_state.oneshot_generating = False

            st.success("🎉 Imprint configuration generated successfully!")
            st.rerun()

    except Exception as e:
        st.session_state.oneshot_generating = False
        st.error(f"❌ Generation failed: {e}")
        logger.error(f"Oneshot generation error: {e}")


def render_oneshot_result(config: Dict):
    """Render the generated imprint configuration with options to save or edit."""
    st.markdown("---")
    st.subheader("🎯 Generated Imprint Configuration")

    # Summary cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Imprint Name",
            config.get("imprint", "Unknown")
        )
        st.metric(
            "Publisher",
            config.get("publisher", "Unknown")
        )

    with col2:
        focus = config.get("publishing_focus", {})
        genres = focus.get("primary_genres", [])
        st.metric(
            "Primary Genres",
            f"{len(genres)} defined"
        )
        if genres:
            st.caption(", ".join(genres[:3]) + ("..." if len(genres) > 3 else ""))

    with col3:
        generation_info = config.get("_generation_info", {})
        st.metric(
            "AI Model",
            generation_info.get("model_used", "Unknown")
        )
        st.metric(
            "Generated",
            generation_info.get("generated_at", "Unknown")[:10]  # Date only
        )

    # Configuration preview
    with st.expander("📋 Configuration Preview", expanded=True):
        # Show key sections
        tabs = st.tabs(["🏢 Branding", "👤 Publisher Persona", "📚 Publishing Focus", "💰 Pricing", "🔧 Technical"])

        with tabs[0]:  # Branding
            branding = config.get("branding", {})
            st.json(branding)

        with tabs[1]:  # Publisher Persona
            persona = config.get("publisher_persona", {})
            wizard_config = config.get("wizard_configuration", {})
            st.markdown("**Publisher Persona:**")
            st.json(persona)
            if wizard_config:
                st.markdown("**Wizard Configuration:**")
                st.json(wizard_config)

        with tabs[2]:  # Publishing Focus
            st.json(config.get("publishing_focus", {}))

        with tabs[3]:  # Pricing
            pricing = config.get("pricing_defaults", {})
            territorial = config.get("territorial_configs", {})
            st.markdown("**Default Pricing:**")
            st.json(pricing)
            st.markdown("**Territorial Configurations:**")
            st.json(territorial)

        with tabs[4]:  # Technical
            production = config.get("production_settings", {})
            distribution = config.get("distribution_settings", {})
            st.markdown("**Production Settings:**")
            st.json(production)
            st.markdown("**Distribution Settings:**")
            st.json(distribution)

    # Action buttons
    st.markdown("### 🎯 What's Next?")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Save Configuration", type="primary", use_container_width=True):
            save_oneshot_config(config)

    with col2:
        if st.button("✏️ Edit in Wizard", type="secondary", use_container_width=True):
            load_oneshot_into_wizard(config)

    with col3:
        if st.button("📥 Download JSON", type="secondary", use_container_width=True):
            json_str = json.dumps(config, indent=2)
            st.download_button(
                "Download",
                data=json_str,
                file_name=f"{config.get('imprint', 'imprint').lower().replace(' ', '_')}_config.json",
                mime="application/json"
            )


def save_oneshot_config(config: Dict):
    """Save the generated imprint configuration."""
    try:
        from pathlib import Path

        # Generate filename
        imprint_name = config.get("imprint", "new_imprint")
        filename = imprint_name.lower().replace(" ", "_").replace("-", "_") + ".json"

        # Save path
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        save_path = project_root / "configs" / "imprints" / filename
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Save file
        with open(save_path, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        st.success(f"✅ Configuration saved to: {save_path}")
        st.balloons()

        # Option to create first book
        st.markdown("### 🚀 Ready to Create Your First Book?")
        if st.button("📖 Start Book Pipeline", type="primary"):
            # Navigate to book pipeline page
            st.switch_page("pages/10_Book_Pipeline.py")

    except Exception as e:
        st.error(f"❌ Failed to save configuration: {e}")


def load_oneshot_into_wizard(config: Dict):
    """Load the generated configuration into the step-by-step wizard for editing."""
    try:
        # Load into session state
        st.session_state.imprint_data = config
        st.session_state.creation_mode = "wizard"
        st.session_state.creation_step = 1

        st.success("✅ Configuration loaded into wizard for editing!")
        st.rerun()

    except Exception as e:
        st.error(f"❌ Failed to load into wizard: {e}")


def render_step_basic_info():
    """Step 1: Basic imprint information."""
    st.subheader("1️⃣ Basic Imprint Information")

    with st.form("basic_info_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Imprint Name*",
                               value=st.session_state.imprint_data.get("name", ""),
                               help="The official name of your imprint (required)")

            proposed_title = st.text_input("Proposed Imprint Title",
                                         value=st.session_state.imprint_data.get("proposed_title", ""),
                                         help="Alternative or working title for the imprint")

            publisher = st.text_input("Publisher Name",
                                    value=st.session_state.imprint_data.get("publisher", "Nimble Books LLC"),
                                    help="The parent publishing company")

            imprint_type = st.selectbox("Imprint Type",
                                      [t.value for t in ImprintType],
                                      index=[t.value for t in ImprintType].index(
                                          st.session_state.imprint_data.get("imprint_type", "traditional")
                                      ))

        with col2:
            charter = st.text_area("Editorial Charter",
                                 value=st.session_state.imprint_data.get("charter", ""),
                                 help="Your imprint's mission and editorial philosophy",
                                 height=100)

            tagline = st.text_input("Tagline",
                                   value=st.session_state.imprint_data.get("tagline", ""),
                                   help="A memorable phrase for your imprint")

            contact_email = st.text_input("Contact Email",
                                        value=st.session_state.imprint_data.get("contact_email", "info@nimblebooks.com"),
                                        help="Primary contact for the imprint")
        
        # Save data automatically (no validation)
        if st.form_submit_button("Save & Continue →"):
            st.session_state.imprint_data.update({
                "name": name or "New Imprint",
                "proposed_title": proposed_title,
                "publisher": publisher or "Nimble Books LLC",
                "imprint_type": imprint_type,
                "charter": charter,
                "tagline": tagline,
                "contact_email": contact_email or "info@nimblebooks.com"
            })
            st.session_state.creation_step = 2
            st.rerun()
        
        # Show minimum requirements info
        if not name:
            st.info("💡 Only imprint name is required for safe operation. All other fields can be filled later.")


def render_step_publisher_persona():
    """Step 2: Publisher persona configuration."""
    st.subheader("2️⃣ Publisher Persona Setup")
    st.markdown("Create a single-named AI publisher with backstory, personality, stylistic preferences and substantive goals")

    col1, col2 = st.columns([2, 1])

    with col1:
        with st.form("persona_form"):
            st.markdown("### AI Publisher Identity")

            publisher_name = st.text_input("AI Publisher Name (single name)*",
                                         value=st.session_state.imprint_data.get("persona_name", ""),
                                         help="A single name for your AI publisher (e.g., 'Aurora', 'Magnus', 'Zenith')")

            publisher_backstory = st.text_area("Backstory",
                                             value=st.session_state.imprint_data.get("persona_backstory", ""),
                                             help="Origin story and history of this AI publisher",
                                             height=100)

            publisher_personality = st.text_area("Personality Traits",
                                                value=st.session_state.imprint_data.get("persona_personality", ""),
                                                help="Key personality characteristics and behavioral patterns (one per line)",
                                                height=80)

            risk_tolerance = st.selectbox("Risk Tolerance",
                                        [r.value for r in RiskTolerance],
                                        help="How comfortable with risky content decisions")

            decision_style = st.selectbox("Decision Making Style",
                                        [d.value for d in DecisionStyle],
                                        help="Primary approach to making publishing decisions")

            st.markdown("### Editorial Vision")

            preferred_topics = st.text_area("Preferred Topics",
                                           value=st.session_state.imprint_data.get("preferred_topics", ""),
                                           help="Topics the AI publisher is drawn to (one per line)",
                                           height=80)

            stylistic_preferences = st.text_area("Stylistic Preferences",
                                                value=st.session_state.imprint_data.get("stylistic_preferences", ""),
                                                help="Writing styles, narrative approaches, and aesthetic preferences (one per line)",
                                                height=80)

            substantive_goals = st.text_area("Substantive Goals",
                                            value=st.session_state.imprint_data.get("substantive_goals", ""),
                                            help="Thematic focus areas, intellectual missions, and content objectives (one per line)",
                                            height=80)

            target_demographics = st.text_area("Target Demographics",
                                             value=st.session_state.imprint_data.get("target_demographics", ""),
                                             help="Key reader demographics to focus on")

            vulnerabilities = st.text_area("Publisher Vulnerabilities/Concerns",
                                         value=st.session_state.imprint_data.get("vulnerabilities", ""),
                                         help="Areas where the publisher needs validation or has blind spots")
            
            navigation_col1, navigation_col2 = st.columns(2)
            
            with navigation_col1:
                if st.form_submit_button("← Previous Step"):
                    st.session_state.creation_step = 1
                    st.rerun()
            
            with navigation_col2:
                if st.form_submit_button("Next Step →"):
                    st.session_state.imprint_data.update({
                        "persona_name": publisher_name,
                        "persona_backstory": publisher_backstory,
                        "persona_personality": publisher_personality,
                        "risk_tolerance": risk_tolerance,
                        "decision_style": decision_style,
                        "preferred_topics": preferred_topics,
                        "stylistic_preferences": stylistic_preferences,
                        "substantive_goals": substantive_goals,
                        "target_demographics": target_demographics,
                        "vulnerabilities": vulnerabilities
                    })
                    st.session_state.creation_step = 3
                    st.rerun()
    
    with col2:
        st.markdown("### 🎭 AI Publisher Examples")

        if st.button("Use 'Nexus' Template"):
            st.session_state.imprint_data.update({
                "persona_name": "Nexus",
                "persona_backstory": "Emerged from analyzing 100 years of literary trends. Nexus sees publishing as pattern recognition at scale, identifying cultural moments before they fully crystallize.",
                "persona_personality": "Analytically curious\nRisk-embracing but data-informed\nOptimistic about human potential\nPatient with creative process",
                "risk_tolerance": "balanced",
                "decision_style": "data_driven",
                "preferred_topics": "Climate futures and sustainability\nAI ethics and society\nPost-scarcity economics\nIdentity in digital age\nDecolonial narratives",
                "stylistic_preferences": "Experimental narrative structures\nCross-genre hybridization\nVoices from overlooked communities\nSpeculative fiction grounded in research",
                "substantive_goals": "Amplify underrepresented perspectives\nExplore technology-society interfaces\nChallenge genre conventions\nBuild bridges between academic and popular audiences",
                "target_demographics": "25-45 educated professionals\nEarly adopters and cultural trendsetters\nGlobally-minded readers",
                "vulnerabilities": "Can over-index on novelty\nMay undervalue traditional narrative comfort\nNeeds human validation on emotional resonance"
            })
            st.success("'Nexus' template applied!")
            st.rerun()

        st.markdown("**Nexus**: An AI publisher focused on identifying emerging cultural patterns and amplifying innovative voices.")

        st.markdown("### 💡 AI Publisher Tips")
        st.info("""
        **Effective AI publishers:**
        - Have a single, memorable name
        - Possess clear backstory and motivation
        - Balance analytical and creative traits
        - Define specific stylistic preferences
        - Articulate substantive publishing goals
        - Acknowledge limitations/blind spots
        """)


def render_step_configuration():
    """Step 3: Technical configuration."""
    st.subheader("3️⃣ Technical Configuration")
    
    with st.form("config_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Publishing Settings")
            
            # Load existing values
            genres = st.multiselect("Primary Genres",
                                  ["Fiction", "Nonfiction", "Science", "Technology", "Philosophy", 
                                   "Business", "Biography", "History", "Art", "Academic"],
                                  default=st.session_state.imprint_data.get("genres", ["Fiction"]))
            
            target_audience = st.selectbox("Primary Target Audience",
                                         ["General Adult", "Academic and Professional", "Young Adult", 
                                          "Literary Fiction Readers", "Technical Professionals"],
                                         index=["General Adult", "Academic and Professional", "Young Adult", 
                                               "Literary Fiction Readers", "Technical Professionals"].index(
                                               st.session_state.imprint_data.get("target_audience", "General Adult")))
            
            languages = st.multiselect("Supported Languages",
                                     ["eng", "kor", "spa", "fra", "deu"],
                                     default=st.session_state.imprint_data.get("languages", ["eng"]))
            
            book_format = st.selectbox("Standard Book Format",
                                     ["6x9 Paperback", "5.5x8.5 Paperback", "8.5x11 Trade", "Custom"],
                                     index=0)
        
        with col2:
            st.markdown("### Business Settings")
            
            price_point = st.number_input("Standard Price Point", 
                                        value=float(st.session_state.imprint_data.get("price_point", 24.99)),
                                        min_value=5.00, max_value=200.00, step=0.99)
            
            page_count = st.number_input("Standard Page Count",
                                       value=int(st.session_state.imprint_data.get("page_count", 200)),
                                       min_value=50, max_value=800, step=10)
            
            initial_catalog_size = st.number_input("Initial Catalog Size",
                                                 value=int(st.session_state.imprint_data.get("catalog_size", 12)),
                                                 min_value=1, max_value=50, step=1,
                                                 help="Number of books to generate initially")
            
            enable_ideation = st.checkbox("Enable Continuous Ideation",
                                        value=st.session_state.imprint_data.get("enable_ideation", True),
                                        help="Automatically generate new book concepts")
        
        navigation_col1, navigation_col2 = st.columns(2)
        
        with navigation_col1:
            if st.form_submit_button("← Previous Step"):
                st.session_state.creation_step = 2
                st.rerun()
        
        with navigation_col2:
            if st.form_submit_button("Next Step →"):
                st.session_state.imprint_data.update({
                    "genres": genres,
                    "target_audience": target_audience,
                    "languages": languages,
                    "book_format": book_format,
                    "price_point": price_point,
                    "page_count": page_count,
                    "catalog_size": initial_catalog_size,
                    "enable_ideation": enable_ideation
                })
                st.session_state.creation_step = 4
                st.rerun()


def render_step_review_create():
    """Step 4: Review and create the imprint."""
    st.subheader("4️⃣ Review & Create Imprint")
    
    data = st.session_state.imprint_data
    
    # Display review information
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Imprint Details")
        st.write(f"**Name**: {data.get('name', 'Unknown')}")
        st.write(f"**Publisher**: {data.get('publisher', 'Unknown')}")
        st.write(f"**Type**: {data.get('imprint_type', 'Unknown')}")
        st.write(f"**Charter**: {data.get('charter', 'None')[:100]}...")
        st.write(f"**Tagline**: {data.get('tagline', 'None')}")
        st.write(f"**Contact**: {data.get('contact_email', 'None')}")
        
        st.markdown("### Publishing Configuration")
        st.write(f"**Genres**: {', '.join(data.get('genres', []))}")
        st.write(f"**Target Audience**: {data.get('target_audience', 'Unknown')}")
        st.write(f"**Languages**: {', '.join(data.get('languages', []))}")
        st.write(f"**Format**: {data.get('book_format', 'Unknown')}")
        st.write(f"**Price Point**: ${data.get('price_point', 0):.2f}")
        st.write(f"**Page Count**: {data.get('page_count', 0)} pages")
        st.write(f"**Initial Catalog**: {data.get('catalog_size', 0)} books")
        st.write(f"**Continuous Ideation**: {'Enabled' if data.get('enable_ideation') else 'Disabled'}")
    
    with col2:
        st.markdown("### AI Publisher Persona")
        if data.get('persona_name'):
            st.write(f"**Name**: {data.get('persona_name', 'None')}")
            st.write(f"**Backstory**: {data.get('persona_backstory', 'None')[:100]}...")
            st.write(f"**Personality**: {data.get('persona_personality', 'None')[:100]}...")
            st.write(f"**Risk Tolerance**: {data.get('risk_tolerance', 'Unknown')}")
            st.write(f"**Decision Style**: {data.get('decision_style', 'Unknown')}")

            if data.get('preferred_topics'):
                topics = data['preferred_topics'].split('\n')[:3]
                st.write(f"**Preferred Topics**: {', '.join([t.strip() for t in topics if t.strip()])}")

            if data.get('stylistic_preferences'):
                prefs = data['stylistic_preferences'].split('\n')[:3]
                st.write(f"**Stylistic Preferences**: {', '.join([p.strip() for p in prefs if p.strip()])}")

            if data.get('substantive_goals'):
                goals = data['substantive_goals'].split('\n')[:3]
                st.write(f"**Substantive Goals**: {', '.join([g.strip() for g in goals if g.strip()])}")

            if data.get('vulnerabilities'):
                vulns = data['vulnerabilities'].split('\n')[:2]
                st.write(f"**Key Vulnerabilities**: {', '.join([v.strip() for v in vulns if v.strip()])}")
        else:
            st.info("No AI publisher persona configured")
    
    # Creation actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("← Previous Step"):
            st.session_state.creation_step = 3
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset Wizard"):
            st.session_state.creation_step = 1
            st.session_state.imprint_data = {}
            st.rerun()
    
    with col3:
        if st.button("🚀 Create Imprint"):
            create_imprint_with_data(data)


def create_imprint_with_data(data: dict):
    """Create the imprint using the collected data."""
    try:
        manager = ImprintManager()
        
        # Check if imprint already exists
        if manager.imprint_exists(data["name"]):
            st.error(f"Imprint '{data['name']}' already exists!")
            return
        
        with st.spinner("Creating imprint..."):
            # Create the core imprint
            imprint = manager.create_imprint(
                name=data["name"],
                publisher=data["publisher"],
                imprint_type=ImprintType(data["imprint_type"]),
                charter=data["charter"],
                tagline=data.get("tagline", ""),
                created_by="enhanced_creator"
            )
            
            # Configure basic settings
            if imprint.configuration:
                config = imprint.configuration
                config.set_value("contact_email", data["contact_email"])
                config.set_value("primary_genres", data["genres"])
                config.set_value("target_audience", data["target_audience"])
                config.set_value("supported_languages", data["languages"])
                config.set_value("standard_price", data["price_point"])
                config.set_value("standard_page_count", data["page_count"])
                
                # Save configuration
                manager.config_service.save_configuration(config)
            
            # Create publisher persona if configured
            if data.get("persona_name"):
                persona = create_custom_persona(data)
                manager.set_publisher_persona(data["name"], persona)
            
            # Setup continuous ideation if enabled
            if data.get("enable_ideation"):
                ideation_config = {
                    "generation_interval": 3600,  # 1 hour
                    "concepts_per_batch": 3,
                    "quality_threshold": 0.7
                }
                session_id = manager.start_continuous_ideation(data["name"], ideation_config)
                if session_id:
                    st.success("Continuous ideation started!")
            
            # Generate initial templates
            generated_templates = manager.template_service.generate_imprint_templates(imprint)
            
            # Activate the imprint
            manager.lifecycle_service.update_imprint_status(
                imprint, ImprintStatus.ACTIVE, "Created through Enhanced Creator"
            )
            
            # Success message
            st.success(f"✅ Successfully created imprint: {data['name']}")
            
            st.markdown("### Created Components:")
            st.write(f"• **Imprint Directory**: {imprint.path}")
            st.write(f"• **Configuration**: {len(imprint.configuration.entries) if imprint.configuration else 0} settings")
            st.write(f"• **Templates**: {len(generated_templates)} generated")
            st.write(f"• **Assets**: {len(imprint.assets.assets) if imprint.assets else 0} assets")
            st.write(f"• **Publisher Persona**: {'Configured' if imprint.publisher_persona else 'None'}")
            st.write(f"• **Continuous Ideation**: {'Active' if imprint.ideation_session_id else 'Disabled'}")
            
            # Reset wizard
            st.session_state.creation_step = 1
            st.session_state.imprint_data = {}
            
            # Link to admin page
            st.markdown("---")
            st.info("✨ **Next Steps**: Visit the Imprint Administration page to manage your new imprint!")
            
    except Exception as e:
        st.error(f"Failed to create imprint: {e}")
        logger.error(f"Imprint creation failed: {e}", exc_info=True)


def create_custom_persona(data: dict) -> PublisherPersona:
    """Create a custom AI publisher persona from form data."""
    # Combine backstory and personality into bio
    bio_parts = []
    if data.get("persona_backstory"):
        bio_parts.append(data["persona_backstory"])
    if data.get("persona_personality"):
        bio_parts.append(f"Personality: {data['persona_personality']}")

    persona = PublisherPersona(
        name=data["persona_name"],
        bio=" | ".join(bio_parts) if bio_parts else "",
        risk_tolerance=RiskTolerance(data["risk_tolerance"]),
        decision_style=DecisionStyle(data["decision_style"])
    )

    # Add preferred topics as content preferences
    if data.get("preferred_topics"):
        topics = [topic.strip() for topic in data["preferred_topics"].split('\n') if topic.strip()]
        for topic in topics:
            persona.editorial_philosophy.content_preferences[topic] = 0.8

    # Add stylistic preferences as content preferences
    if data.get("stylistic_preferences"):
        prefs = [pref.strip() for pref in data["stylistic_preferences"].split('\n') if pref.strip()]
        for pref in prefs:
            persona.editorial_philosophy.content_preferences[pref] = 0.85

    # Add substantive goals as high-priority content preferences
    if data.get("substantive_goals"):
        goals = [goal.strip() for goal in data["substantive_goals"].split('\n') if goal.strip()]
        for goal in goals:
            persona.editorial_philosophy.content_preferences[goal] = 0.9

    # Add target demographics as market preferences
    if data.get("target_demographics"):
        demographics = [demo.strip() for demo in data["target_demographics"].split('\n') if demo.strip()]
        for demo in demographics:
            persona.add_market_preference(demo, 0.7, f"Target demographic for {persona.name}")

    # Add vulnerabilities
    if data.get("vulnerabilities"):
        vulnerabilities = [vuln.strip() for vuln in data["vulnerabilities"].split('\n') if vuln.strip()]
        for vuln in vulnerabilities:
            persona.add_vulnerability(vuln, f"AI publisher limitation: {vuln}", 0.6)

    return persona


if __name__ == "__main__":
    main()