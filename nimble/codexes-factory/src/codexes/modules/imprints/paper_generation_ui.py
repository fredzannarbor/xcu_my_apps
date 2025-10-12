"""
Streamlit UI Components for Academic Paper Generation in Imprint Creation

This module provides UI components that can be integrated into the Enhanced Imprint Creator
to configure and trigger academic paper generation for new imprints.
"""

import streamlit as st
import json
from typing import Dict, Any, Optional
from pathlib import Path

try:
    from .academic_paper_integration import ImprintPaperGenerator, check_paper_generation_status
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(str(Path(__file__).parent))
    from academic_paper_integration import ImprintPaperGenerator, check_paper_generation_status


def render_paper_generation_configuration_step() -> Dict[str, Any]:
    """
    Render the paper generation configuration step in the imprint creation wizard.

    Returns:
        Dictionary containing paper generation configuration
    """
    st.header("📄 Academic Paper Generation (Optional)")
    st.markdown("""
    Configure automatic generation of academic papers to document your imprint's
    development, methodology, and impact in the publishing industry.
    """)

    # Main enable/disable toggle
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Paper Generation Settings")
    with col2:
        enabled = st.toggle("Enable Paper Generation", key="paper_gen_enabled")

    if not enabled:
        st.info("💡 Paper generation is disabled. You can enable this later in the imprint configuration.")
        return {"enabled": False}

    # Paper generation triggers
    st.subheader("🔄 Generation Triggers")

    col1, col2 = st.columns(2)
    with col1:
        on_creation = st.checkbox(
            "Generate on imprint creation",
            help="Automatically generate a paper when this imprint is first created",
            key="trigger_on_creation"
        )
        on_milestones = st.checkbox(
            "Generate on book milestones",
            help="Generate papers when reaching specific book count milestones",
            key="trigger_on_milestones"
        )

    with col2:
        on_schedule = st.checkbox(
            "Generate on schedule",
            help="Generate papers on a regular schedule (quarterly, annually, etc.)",
            key="trigger_on_schedule"
        )
        manual_only = st.checkbox(
            "Manual generation only",
            value=not (on_creation or on_milestones or on_schedule),
            help="Only generate papers when manually requested",
            key="trigger_manual_only"
        )

    # Paper settings
    st.subheader("📊 Paper Configuration")

    col1, col2 = st.columns(2)
    with col1:
        paper_type = st.selectbox(
            "Default paper type",
            options=["case_study", "methodology_paper", "industry_analysis", "technical_report"],
            index=0,
            help="The primary type of academic paper to generate",
            key="paper_type"
        )

        target_word_count = st.number_input(
            "Target word count",
            min_value=3000,
            max_value=15000,
            value=8000,
            step=500,
            help="Target length for generated papers",
            key="target_word_count"
        )

    with col2:
        target_venues = st.multiselect(
            "Target venues",
            options=[
                "arXiv",
                "Digital Humanities Quarterly",
                "Publishing Research Quarterly",
                "Computers and Composition",
                "Journal of Scholarly Publishing",
                "First Monday",
                "Academic conferences"
            ],
            default=["arXiv"],
            help="Academic venues where the paper might be submitted",
            key="target_venues"
        )

    # Content configuration
    st.subheader("📝 Content Focus")

    focus_areas = st.multiselect(
        "Research focus areas",
        options=[
            "AI-assisted publishing",
            "Imprint development methodology",
            "Publishing innovation",
            "Digital humanities",
            "Technology adoption in publishing",
            "Automated content generation",
            "Publishing workflow optimization",
            "Academic-industry collaboration"
        ],
        default=["AI-assisted publishing", "Imprint development methodology"],
        help="Primary research areas the paper will address",
        key="focus_areas"
    )

    # Data sources
    st.subheader("📈 Data Sources")
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Include in analysis:**")
        include_catalog = st.checkbox("Book catalog data", value=True, key="include_catalog")
        include_production = st.checkbox("Production metrics", value=True, key="include_production")

    with col2:
        include_sales = st.checkbox("Sales metrics", value=False, key="include_sales")
        include_config = st.checkbox("Configuration analysis", value=True, key="include_config")

    # Anonymization settings
    if include_sales:
        st.subheader("🔒 Privacy & Anonymization")
        col1, col2 = st.columns(2)

        with col1:
            anonymize_sales = st.checkbox("Anonymize sales data", value=True, key="anonymize_sales")
            anonymize_authors = st.checkbox("Anonymize author names", value=False, key="anonymize_authors")

        with col2:
            anonymize_titles = st.checkbox("Anonymize specific titles", value=False, key="anonymize_titles")

    # Output settings
    st.subheader("📂 Output Configuration")

    col1, col2 = st.columns(2)
    with col1:
        output_formats = st.multiselect(
            "Output formats",
            options=["latex", "pdf", "markdown", "docx"],
            default=["latex", "pdf", "markdown"],
            help="File formats to generate",
            key="output_formats"
        )

    with col2:
        include_submission = st.checkbox(
            "Include arXiv submission package",
            value=True,
            help="Generate files ready for arXiv submission",
            key="include_submission"
        )

    # Advanced settings in expander
    with st.expander("🔧 Advanced Settings"):
        st.subheader("LLM Configuration")

        col1, col2 = st.columns(2)
        with col1:
            llm_model = st.selectbox(
                "Preferred LLM model",
                options=[
                    "anthropic/claude-3-5-sonnet-20241022",
                    "openai/gpt-4",
                    "openai/gpt-4-turbo"
                ],
                index=0,
                key="llm_model"
            )

            temperature = st.slider(
                "LLM temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Higher values = more creative, lower = more focused",
                key="llm_temperature"
            )

        with col2:
            max_tokens = st.number_input(
                "Max tokens per section",
                min_value=1000,
                max_value=8000,
                value=4000,
                step=500,
                key="max_tokens"
            )

            enable_validation = st.checkbox(
                "Enable quality validation",
                value=True,
                help="Automatically validate generated content quality",
                key="enable_validation"
            )

        st.subheader("Author Attribution")
        col1, col2 = st.columns(2)

        with col1:
            author_byline = st.text_input(
                "Author byline",
                value="Imprint Development Team",
                help="How authors should be credited",
                key="author_byline"
            )

            institutional_affiliation = st.text_input(
                "Institutional affiliation",
                value="AI Lab for Book-Lovers",
                help="Institutional affiliation for authors",
                key="institutional_affiliation"
            )

        with col2:
            contact_email = st.text_input(
                "Contact email",
                value="research@imprint.com",
                help="Contact email for correspondence",
                key="contact_email"
            )

            co_author_llm = st.checkbox(
                "Credit LLM as co-author",
                value=True,
                help="Include LLM attribution in author list",
                key="co_author_llm"
            )

    # Milestone configuration (if enabled)
    if on_milestones:
        with st.expander("📈 Milestone Configuration"):
            st.subheader("Book Count Milestones")
            milestone_books = st.text_input(
                "Book count milestones (comma-separated)",
                value="10, 25, 50, 100",
                help="Generate papers when reaching these book counts",
                key="milestone_books"
            )

            time_milestones = st.multiselect(
                "Time-based milestones",
                options=["6_months", "1_year", "2_years", "5_years"],
                default=["1_year"],
                help="Generate papers at these time intervals",
                key="time_milestones"
            )

    # Schedule configuration (if enabled)
    if on_schedule:
        with st.expander("⏰ Schedule Configuration"):
            frequency = st.selectbox(
                "Generation frequency",
                options=["monthly", "quarterly", "biannual", "annual"],
                index=2,
                help="How often to automatically generate papers",
                key="schedule_frequency"
            )

    # Build configuration dictionary
    config = {
        "enabled": True,
        "auto_generate_on_imprint_creation": on_creation,
        "generation_triggers": {
            "on_imprint_creation": on_creation,
            "on_milestone_books": on_milestones,
            "on_schedule": on_schedule,
            "manual_only": manual_only
        },
        "paper_settings": {
            "target_venues": target_venues,
            "paper_types": [paper_type],
            "default_paper_type": paper_type,
            "target_word_count": target_word_count,
            "citation_style": "academic",
            "include_quantitative_analysis": True
        },
        "content_configuration": {
            "focus_areas": focus_areas,
            "data_sources": {
                "include_book_catalog": include_catalog,
                "include_sales_metrics": include_sales,
                "include_production_metrics": include_production,
                "include_configuration_analysis": include_config
            },
            "anonymization": {
                "anonymize_sales_data": include_sales and anonymize_sales if include_sales else True,
                "anonymize_author_names": anonymize_authors if include_sales else False,
                "anonymize_specific_titles": anonymize_titles if include_sales else False
            }
        },
        "output_settings": {
            "output_directory": "output/academic_papers/{imprint_name}",
            "file_naming": "{imprint_name}_paper_{date}_{type}",
            "formats": output_formats,
            "include_submission_package": include_submission
        },
        "llm_configuration": {
            "preferred_models": [llm_model],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "enable_quality_validation": enable_validation
        },
        "collaboration_settings": {
            "include_attribution": True,
            "author_byline": author_byline,
            "institutional_affiliation": institutional_affiliation,
            "contact_email": contact_email,
            "co_author_llm": co_author_llm
        },
        "validation_criteria": {
            "min_word_count": max(3000, target_word_count - 2000),
            "max_word_count": target_word_count + 4000,
            "required_sections": [
                "abstract", "introduction", "methodology",
                "results", "discussion", "conclusion"
            ],
            "require_quantitative_data": True,
            "require_citations": True,
            "academic_tone_validation": True
        }
    }

    # Add milestone and schedule settings if applicable
    if on_milestones:
        try:
            book_milestones = [int(x.strip()) for x in milestone_books.split(",")]
            config["automation_schedule"] = {
                "enabled": True,
                "milestone_triggers": {
                    "book_count_milestones": book_milestones,
                    "time_milestones": time_milestones
                }
            }
        except ValueError:
            st.error("Invalid book count milestones. Please use comma-separated numbers.")

    if on_schedule:
        config["automation_schedule"] = config.get("automation_schedule", {"enabled": True})
        config["automation_schedule"]["frequency"] = frequency

    return config


def render_paper_generation_preview(paper_config: Dict[str, Any], imprint_config: Dict[str, Any]) -> None:
    """
    Render a preview of what the paper generation will produce.

    Args:
        paper_config: Paper generation configuration
        imprint_config: Full imprint configuration
    """
    if not paper_config.get("enabled"):
        return

    st.subheader("📄 Paper Generation Preview")

    imprint_name = imprint_config.get("imprint", "New Imprint")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Paper Details:**")
        st.write(f"• **Imprint:** {imprint_name}")
        st.write(f"• **Type:** {paper_config['paper_settings']['default_paper_type'].replace('_', ' ').title()}")
        st.write(f"• **Target Length:** {paper_config['paper_settings']['target_word_count']:,} words")
        st.write(f"• **Venues:** {', '.join(paper_config['paper_settings']['target_venues'])}")

    with col2:
        st.write("**Generation Triggers:**")
        triggers = paper_config["generation_triggers"]
        trigger_list = []
        if triggers.get("on_imprint_creation"):
            trigger_list.append("✅ On creation")
        if triggers.get("on_milestone_books"):
            trigger_list.append("✅ On milestones")
        if triggers.get("on_schedule"):
            trigger_list.append("✅ On schedule")
        if triggers.get("manual_only"):
            trigger_list.append("✅ Manual only")

        for trigger in trigger_list:
            st.write(f"• {trigger}")

    st.write("**Focus Areas:**")
    focus_areas = paper_config["content_configuration"]["focus_areas"]
    for area in focus_areas:
        st.write(f"• {area}")

    # Show data sources
    data_sources = paper_config["content_configuration"]["data_sources"]
    included_sources = [key.replace("include_", "").replace("_", " ").title()
                      for key, value in data_sources.items() if value]

    if included_sources:
        st.write("**Data Sources:**")
        for source in included_sources:
            st.write(f"• {source}")

    # Output information
    output_dir = paper_config["output_settings"]["output_directory"].replace("{imprint_name}", imprint_name)
    st.write(f"**Output Directory:** `{output_dir}`")
    st.write(f"**Formats:** {', '.join(paper_config['output_settings']['formats'])}")


def render_paper_generation_test_button(imprint_name: str) -> None:
    """
    Render a button to test paper generation for an existing imprint.

    Args:
        imprint_name: Name of the imprint to test
    """
    st.subheader("🧪 Test Paper Generation")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.write(f"Test automatic paper generation for **{imprint_name}** imprint.")
        st.write("This will generate a paper using the current configuration.")

    with col2:
        if st.button("🚀 Generate Test Paper", key="test_paper_gen"):
            with st.spinner("Generating academic paper..."):
                try:
                    from academic_paper_integration import generate_paper_for_new_imprint

                    result = generate_paper_for_new_imprint(imprint_name)

                    if result and result.get("success"):
                        st.success("✅ Paper generated successfully!")
                        st.write(f"**Output Directory:** {result.get('output_directory')}")

                        # Show context data used
                        with st.expander("📊 Context Data Used"):
                            st.json(result.get("context_data", {}))

                    else:
                        error_msg = result.get("error", "Unknown error") if result else "Generation failed"
                        st.error(f"❌ Paper generation failed: {error_msg}")

                except Exception as e:
                    st.error(f"❌ Error during paper generation: {str(e)}")


def render_paper_generation_status(imprint_name: str) -> None:
    """
    Render the current paper generation status for an imprint.

    Args:
        imprint_name: Name of the imprint to check
    """
    st.subheader("📊 Paper Generation Status")

    try:
        status = check_paper_generation_status(imprint_name)

        if "error" in status:
            st.error(f"❌ {status['error']}")
            return

        col1, col2 = st.columns(2)

        with col1:
            enabled = status.get("paper_generation_enabled", False)
            st.metric(
                "Paper Generation",
                "Enabled" if enabled else "Disabled",
                delta="✅" if enabled else "❌"
            )

            auto_gen = status.get("auto_generate_on_creation", False)
            st.metric(
                "Auto Generation",
                "On" if auto_gen else "Off",
                delta="🔄" if auto_gen else "⏸️"
            )

        with col2:
            paper_settings = status.get("paper_settings", {})
            word_count = paper_settings.get("target_word_count", 0)
            st.metric("Target Word Count", f"{word_count:,}")

            venues = paper_settings.get("target_venues", [])
            st.metric("Target Venues", len(venues))

        # Show detailed settings
        if enabled:
            with st.expander("📋 Detailed Configuration"):
                st.json(status)

    except Exception as e:
        st.error(f"❌ Error checking status: {str(e)}")


if __name__ == "__main__":
    # Demo the UI components
    st.set_page_config(page_title="Paper Generation UI Demo", layout="wide")

    st.title("📄 Academic Paper Generation UI Demo")

    # Demo configuration step
    st.header("Configuration Step Demo")
    config = render_paper_generation_configuration_step()

    # Demo preview
    if config.get("enabled"):
        dummy_imprint_config = {
            "imprint": "Demo Imprint",
            "publisher": "Demo Publisher",
            "publishing_focus": {
                "specialization": "AI and Technology",
                "primary_genres": ["Technology", "Science"]
            }
        }

        render_paper_generation_preview(config, dummy_imprint_config)

    # Show configuration as JSON
    with st.expander("📋 Generated Configuration"):
        st.json(config)