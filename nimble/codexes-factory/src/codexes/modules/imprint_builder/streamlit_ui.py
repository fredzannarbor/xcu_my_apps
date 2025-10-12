"""
Streamlit UI components for the imprint builder.
"""

import streamlit as st
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


# Import safety patterns from the centralized module
try:
    from ..ui.safety_patterns import (
        safe_getattr, safe_dict_get, safe_iteration, safe_len, safe_join,
        validate_not_none, log_none_encounter
    )
    from ..ui.data_validators import UIDataValidator, StructureNormalizer
except ImportError:
    # Fallback safety functions
    def safe_getattr(obj, attr, default=None):
        if obj is None:
            return default
        return getattr(obj, attr, default)
    
    def safe_dict_get(d, key, default=None):
        return (d or {}).get(key, default)
    
    def safe_len(collection):
        return len(collection or [])
    
    def safe_join(items, separator=", "):
        """Safely join a list of items, handling None values."""
        if not items:
            return ""
        return separator.join(str(item) for item in items if item is not None)
    
    def validate_not_none(value, context, attr):
        return value is not None
    
    def log_none_encounter(context, attr):
        pass
    
    UIDataValidator = None
    StructureNormalizer = None

from .imprint_concept import ImprintConcept, ImprintConceptParser
from .imprint_expander import ImprintExpander, ExpandedImprint
from .unified_editor import ImprintEditor, EditingSession
from .artifact_generator import ImprintArtifactGenerator
from .schedule_generator import ImprintScheduleGenerator
from .validation import ValidationResult
from ...core.llm_integration import LLMCaller

logger = logging.getLogger(__name__)


class StreamlitImprintBuilder:
    """Streamlit UI for the imprint builder system."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize safety components
        if UIDataValidator:
            self.ui_validator = UIDataValidator()
            self.structure_normalizer = StructureNormalizer(self.ui_validator)
        else:
            self.ui_validator = None
            self.structure_normalizer = None
        
        # Initialize components with safe session state access
        if 'llm_caller' not in st.session_state or st.session_state.llm_caller is None:
            try:
                st.session_state.llm_caller = LLMCaller()
            except Exception as e:
                log_none_encounter('llm_caller_init', 'LLMCaller')
                st.session_state.llm_caller = None
        
        # Safe initialization of other components
        llm_caller = st.session_state.llm_caller
        
        if 'concept_parser' not in st.session_state or st.session_state.concept_parser is None:
            try:
                st.session_state.concept_parser = ImprintConceptParser(llm_caller) if llm_caller else None
            except Exception as e:
                log_none_encounter('concept_parser_init', 'ImprintConceptParser')
                st.session_state.concept_parser = None
        
        if 'imprint_expander' not in st.session_state or st.session_state.imprint_expander is None:
            try:
                st.session_state.imprint_expander = ImprintExpander(llm_caller) if llm_caller else None
            except Exception as e:
                log_none_encounter('imprint_expander_init', 'ImprintExpander')
                st.session_state.imprint_expander = None
        
        if 'imprint_editor' not in st.session_state or st.session_state.imprint_editor is None:
            try:
                st.session_state.imprint_editor = ImprintEditor(llm_caller) if llm_caller else None
            except Exception as e:
                log_none_encounter('imprint_editor_init', 'ImprintEditor')
                st.session_state.imprint_editor = None
        
        if 'artifact_generator' not in st.session_state or st.session_state.artifact_generator is None:
            try:
                st.session_state.artifact_generator = ImprintArtifactGenerator(llm_caller) if llm_caller else None
            except Exception as e:
                log_none_encounter('artifact_generator_init', 'ImprintArtifactGenerator')
                st.session_state.artifact_generator = None
        
        if 'schedule_generator' not in st.session_state or st.session_state.schedule_generator is None:
            try:
                st.session_state.schedule_generator = ImprintScheduleGenerator(llm_caller) if llm_caller else None
            except Exception as e:
                log_none_encounter('schedule_generator_init', 'ImprintScheduleGenerator')
                st.session_state.schedule_generator = None

    def render_main_interface(self):
        """Render the main imprint builder interface."""
        st.title("🏢 Streamlined Imprint Builder")
        st.markdown("Create professional publishing imprints from simple descriptions")
        
        # Initialize active tab
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = "create"
        
        # Navigation tabs
        tab_names = ["📝 Create Imprint", "✏️ Edit Imprint", "📋 Generate Artifacts", "📅 Schedule Planning", "📊 Management"]
        tab_keys = ["create", "edit", "artifacts", "schedule", "management"]
        
        # Find active tab index
        try:
            active_index = tab_keys.index(st.session_state.active_tab)
        except ValueError:
            active_index = 0
            st.session_state.active_tab = "create"
        
        # Create tabs
        tabs = st.tabs(tab_names)
        
        # Handle tab selection
        for i, (tab, key) in enumerate(zip(tabs, tab_keys)):
            if i == active_index:
                with tab:
                    if key == "create":
                        self.render_creation_interface()
                    elif key == "edit":
                        self.render_editing_interface()
                    elif key == "artifacts":
                        self.render_artifact_generation()
                    elif key == "schedule":
                        self.render_schedule_planning()
                    elif key == "management":
                        self.render_management_interface()


    def render_creation_interface(self):
        """Render the imprint creation interface."""
        st.header("Create New Imprint")
        
        # Single field input
        st.markdown("### Describe Your Imprint Vision")
        st.markdown("Enter a description of your imprint concept. Include themes, target audience, publishing focus, and any special requirements.")
        
        concept_input = st.text_area(
            "Imprint Concept",
            placeholder="Example: A literary imprint focused on contemporary fiction for young adults, emphasizing diverse voices and social issues. We want a modern, accessible brand that connects with readers aged 16-25 through social media and book clubs.",
            height=150,
            help="Describe your imprint's mission, target audience, genres, and any specific requirements"
        )
        
        # Advanced options
        with st.expander("Advanced Options"):
            col1, col2 = st.columns(2)
            
            with col1:
                target_books_per_year = st.number_input(
                    "Target Books Per Year",
                    min_value=1,
                    max_value=100,
                    value=12,
                    help="How many books do you plan to publish annually?"
                )
                
                priority_focus = st.selectbox(
                    "Priority Focus",
                    ["Quality over Quantity", "Balanced Approach", "High Volume Production"],
                    help="What's your primary focus for this imprint?"
                )
            
            with col2:
                budget_range = st.selectbox(
                    "Budget Range",
                    ["Startup (< $50K)", "Small ($50K - $200K)", "Medium ($200K - $500K)", "Large (> $500K)"],
                    help="What's your approximate annual budget?"
                )
                
                automation_level = st.selectbox(
                    "Automation Preference",
                    ["Minimal", "Moderate", "High"],
                    help="How much automation do you want in your workflow?"
                )
        
        # Create button
        if st.button("🚀 Create Imprint", type="primary", disabled=not concept_input.strip()):
            with st.spinner("Creating your imprint..."):
                try:
                    # Parse concept
                    concept = st.session_state.concept_parser.parse_concept(concept_input)
                    
                    # Additional preferences are already stored in the concept object
                    # target_books_per_year, priority_focus, budget_range, automation_level
                    # are already part of the concept
                    
                    # Expand concept
                    expanded_imprint = st.session_state.imprint_expander.expand_concept(concept)
                    
                    # Store in session state
                    st.session_state.current_imprint = expanded_imprint
                    st.session_state.current_concept = concept
                    
                    # Show results
                    self.display_creation_results(concept, expanded_imprint)
                    
                except Exception as e:
                    st.error(f"Error creating imprint: {str(e)}")
                    self.logger.error(f"Error in imprint creation: {e}")

    def display_creation_results(self, concept: ImprintConcept, imprint: ExpandedImprint):
        """Display the results of imprint creation."""
        st.success("✅ Imprint created successfully!")
        
        # Quick action buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🔧 Skip to Artifacts", type="primary"):
                st.session_state.active_tab = "artifacts"
                st.rerun()
        with col2:
            if st.button("✏️ Edit First"):
                st.session_state.active_tab = "edit"
                st.rerun()
        
        # Overview
        st.markdown("### 📋 Imprint Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Safe access to concept attributes
            genre_focus = safe_getattr(concept, 'genre_focus', [])
            st.metric("Genre Focus", safe_len(genre_focus))
        
        with col2:
            # Safe access to description
            description = safe_getattr(concept, 'description', '')
            st.metric("Description Length", safe_len(description))
        
        with col3:
            # Safe access to nested attributes
            publishing = safe_getattr(imprint, 'publishing', None)
            primary_genres = safe_getattr(publishing, 'primary_genres', [])
            st.metric("Primary Genres", safe_len(primary_genres))
        
        # Key details
        st.markdown("### 🎯 Key Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Imprint Name**")
            branding = safe_getattr(imprint, 'branding', None)
            imprint_name = safe_getattr(branding, 'imprint_name', 'Not specified')
            st.write(imprint_name)
            
            st.markdown("**Mission Statement**")
            mission_statement = safe_getattr(branding, 'mission_statement', 'Not specified')
            st.write(mission_statement)
            
            st.markdown("**Target Audience**")
            publishing = safe_getattr(imprint, 'publishing', None)
            target_audience = safe_getattr(publishing, 'target_audience', 'Not specified')
            st.write(target_audience)
        
        with col2:
            st.markdown("**Primary Genres**")
            primary_genres = safe_getattr(publishing, 'primary_genres', [])
            for genre in safe_iteration(primary_genres):
                if genre:  # Additional None check
                    st.write(f"• {genre}")
            
            st.markdown("**Brand Values**")
            brand_values = safe_getattr(branding, 'brand_values', [])
            for value in safe_iteration(brand_values):
                if value:  # Additional None check
                    st.write(f"• {value}")
            
            st.markdown("**Unique Selling Proposition**")
            usp = safe_getattr(branding, 'unique_selling_proposition', 'Not specified')
            st.write(usp)
        
        # Design preview
        st.markdown("### 🎨 Design Preview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Color Palette**")
            design = safe_getattr(imprint, 'design', None)
            colors = safe_getattr(design, 'color_palette', {})
            if colors:
                for color_name, color_value in (colors or {}).items():
                    if color_name and color_value:  # Additional None checks
                        safe_color_name = str(color_name).title()
                        st.markdown(f"**{safe_color_name}:** `{color_value}`")
        
        with col2:
            st.markdown("**Typography**")
            typography = safe_getattr(design, 'typography', {})
            if typography:
                for font_type, font_name in (typography or {}).items():
                    if font_type and font_name:  # Additional None checks
                        safe_font_type = str(font_type).replace('_', ' ').title()
                        st.markdown(f"**{safe_font_type}:** {font_name}")
        
        with col3:
            st.markdown("**Trim Sizes**")
            trim_sizes = safe_getattr(design, 'trim_sizes', [])
            for size in safe_iteration(trim_sizes):
                if size:  # Additional None check
                    st.write(f"• {size}")
        
        # Next steps
        st.markdown("### 🎯 Next Steps")
        st.info("Your imprint has been created! You can now:")
        st.markdown("""
        - **Edit & Refine**: Use the 'Edit Imprint' tab to make adjustments
        - **Generate Artifacts**: Create templates, prompts, and configurations
        - **Plan Schedule**: Set up your publication timeline
        - **Export**: Download your imprint definition
        """)

    def render_editing_interface(self):
        """Render the imprint editing interface."""
        st.header("Edit Imprint")
        
        if 'current_imprint' not in st.session_state:
            st.info("👈 Create an imprint first using the 'Create Imprint' tab")
            return
        
        imprint = st.session_state.current_imprint
        
        # Create editing session if not exists
        if 'editing_session' not in st.session_state:
            st.session_state.editing_session = st.session_state.imprint_editor.create_editing_session(imprint)
        
        session = st.session_state.editing_session
        
        # Session info
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Changes Made", len(session.change_history))
        
        with col2:
            validation = st.session_state.imprint_editor.validate_imprint(session)
            st.metric("Completeness", f"{validation.completeness_score:.1%}")
        
        with col3:
            st.metric("Errors", len(validation.errors))
        
        with col4:
            st.metric("Warnings", len(validation.warnings))
        
        # Undo/Redo buttons
        col1, col2, col3 = st.columns([1, 1, 4])
        
        with col1:
            if st.button("↶ Undo", disabled=session.current_position < 0):
                st.session_state.imprint_editor.undo_change(session)
                st.rerun()
        
        with col2:
            if st.button("↷ Redo", disabled=session.current_position >= len(session.change_history) - 1):
                st.session_state.imprint_editor.redo_change(session)
                st.rerun()
        
        # Editing sections
        st.markdown("### Edit Sections")
        
        edit_tab1, edit_tab2, edit_tab3, edit_tab4, edit_tab5, edit_tab6 = st.tabs([
            "🏷️ Branding", 
            "🎨 Design", 
            "📚 Publishing", 
            "⚙️ Operations",
            "📈 Marketing",
            "💰 Financial"
        ])
        
        with edit_tab1:
            self.render_branding_editor(session)
        
        with edit_tab2:
            self.render_design_editor(session)
        
        with edit_tab3:
            self.render_publishing_editor(session)
        
        with edit_tab4:
            self.render_operations_editor(session)
        
        with edit_tab5:
            self.render_marketing_editor(session)
        
        with edit_tab6:
            self.render_financial_editor(session)
        
        # Validation results
        if validation.errors or validation.warnings:
            st.markdown("### 🔍 Validation Results")
            
            if validation.errors:
                st.error("**Errors:**")
                errors = getattr(validation, 'errors', None) or []
                for error in errors:
                    st.write(f"• {error}")
            
            if validation.warnings:
                st.warning("**Warnings:**")
                warnings = getattr(validation, 'warnings', None) or []
                for warning in warnings:
                    st.write(f"• {warning}")
        
        # Suggestions
        suggestions = st.session_state.imprint_editor.suggest_improvements(session)
        if suggestions:
            st.markdown("### 💡 Suggestions")
            for suggestion in suggestions[:5]:  # Show top 5
                st.info(suggestion)

    def render_branding_editor(self, session: EditingSession):
        """Render branding section editor."""
        branding = session.imprint.branding
        
        # Imprint name
        current_name = safe_getattr(branding, 'imprint_name', '')
        new_name = st.text_input(
            "Imprint Name",
            value=current_name,
            help="The official name of your imprint"
        )
        if new_name != current_name:
            st.session_state.imprint_editor.update_field(session, 'branding', 'imprint_name', new_name)
        
        # Tagline
        current_tagline = safe_getattr(branding, 'tagline', '')
        new_tagline = st.text_input(
            "Tagline",
            value=current_tagline,
            help="A memorable tagline for your imprint"
        )
        if new_tagline != current_tagline:
            st.session_state.imprint_editor.update_field(session, 'branding', 'tagline', new_tagline)
        
        # Mission statement
        current_mission = safe_getattr(branding, 'mission_statement', '')
        new_mission = st.text_area(
            "Mission Statement",
            value=current_mission,
            help="Your imprint's mission and purpose"
        )
        if new_mission != current_mission:
            st.session_state.imprint_editor.update_field(session, 'branding', 'mission_statement', new_mission)
        
        # Brand values
        st.markdown("**Brand Values**")
        current_brand_values = safe_getattr(branding, 'brand_values', [])
        values_text = "\n".join(current_brand_values) if current_brand_values else ""
        new_values_text = st.text_area(
            "Brand Values (one per line)",
            value=values_text,
            help="Core values that define your brand"
        )
        new_values = [v.strip() for v in new_values_text.split('\n') if v.strip()]
        if new_values != current_brand_values:
            st.session_state.imprint_editor.update_field(session, 'branding', 'brand_values', new_values)
        
        # Unique selling proposition
        current_usp = safe_getattr(branding, 'unique_selling_proposition', '')
        new_usp = st.text_area(
            "Unique Selling Proposition",
            value=current_usp,
            help="What makes your imprint unique in the market"
        )
        if new_usp != current_usp:
            st.session_state.imprint_editor.update_field(session, 'branding', 'unique_selling_proposition', new_usp)

    def render_design_editor(self, session: EditingSession):
        """Render design section editor."""
        design = session.imprint.design
        
        # Typography
        st.markdown("**Typography**")
        
        # Safe access to typography - handle None values
        typography = getattr(design, 'typography', None) or {}
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            primary_font = st.text_input(
                "Primary Font",
                value=typography.get('primary_font', ''),
                help="Main font for headings and titles"
            )
            if primary_font != typography.get('primary_font', ''):
                new_typography = typography.copy()
                new_typography['primary_font'] = primary_font
                st.session_state.imprint_editor.update_field(session, 'design', 'typography', new_typography)
        
        with col2:
            secondary_font = st.text_input(
                "Secondary Font",
                value=typography.get('secondary_font', ''),
                help="Secondary font for accents and captions"
            )
            if secondary_font != typography.get('secondary_font', ''):
                new_typography = typography.copy()
                new_typography['secondary_font'] = secondary_font
                st.session_state.imprint_editor.update_field(session, 'design', 'typography', new_typography)
        
        with col3:
            body_font = st.text_input(
                "Body Font",
                value=typography.get('body_font', ''),
                help="Font for body text"
            )
            if body_font != typography.get('body_font', ''):
                new_typography = typography.copy()
                new_typography['body_font'] = body_font
                st.session_state.imprint_editor.update_field(session, 'design', 'typography', new_typography)
        
        # Typography styles (from LLM generation)
        col1, col2 = st.columns(2)
        with col1:
            headline_style = st.text_input(
                "Headline Style",
                value=typography.get('headline', ''),
                help="Style description for headlines"
            )
            if headline_style != typography.get('headline', ''):
                new_typography = typography.copy()
                new_typography['headline'] = headline_style
                st.session_state.imprint_editor.update_field(session, 'design', 'typography', new_typography)
        
        with col2:
            body_style = st.text_input(
                "Body Style",
                value=typography.get('body', ''),
                help="Style description for body text"
            )
            if body_style != typography.get('body', ''):
                new_typography = typography.copy()
                new_typography['body'] = body_style
                st.session_state.imprint_editor.update_field(session, 'design', 'typography', new_typography)
        
        # Color palette
        st.markdown("**Color Palette**")
        col1, col2, col3 = st.columns(3)
        
        # Safe access to color_palette - handle None values
        color_palette = getattr(design, 'color_palette', None) or {}
        
        with col1:
            primary_color = st.color_picker(
                "Primary Color",
                value=color_palette.get('primary_color', '#2C3E50'),
                help="Main brand color"
            )
            if primary_color != color_palette.get('primary_color', ''):
                new_palette = color_palette.copy()
                new_palette['primary_color'] = primary_color
                st.session_state.imprint_editor.update_field(session, 'design', 'color_palette', new_palette)
        
        with col2:
            secondary_color = st.color_picker(
                "Secondary Color",
                value=color_palette.get('secondary_color', '#3498DB'),
                help="Accent color"
            )
            if secondary_color != color_palette.get('secondary_color', ''):
                new_palette = color_palette.copy()
                new_palette['secondary_color'] = secondary_color
                st.session_state.imprint_editor.update_field(session, 'design', 'color_palette', new_palette)
        
        with col3:
            accent_color = st.color_picker(
                "Accent Color",
                value=color_palette.get('accent_color', '#E74C3C'),
                help="Highlight color"
            )
            if accent_color != color_palette.get('accent_color', ''):
                new_palette = color_palette.copy()
                new_palette['accent_color'] = accent_color
                st.session_state.imprint_editor.update_field(session, 'design', 'color_palette', new_palette)
        
        # Trim sizes
        st.markdown("**Trim Sizes**")
        available_sizes = ["5x8", "5.5x8.5", "6x9", "7x10", "8.5x11"]
        
        # Safe access to trim_sizes - handle None values
        trim_sizes = getattr(design, 'trim_sizes', None) or []
        
        selected_sizes = st.multiselect(
            "Preferred Trim Sizes",
            available_sizes,
            default=[size for size in trim_sizes if size in available_sizes],
            help="Standard book sizes for your imprint"
        )
        if selected_sizes != trim_sizes:
            st.session_state.imprint_editor.update_field(session, 'design', 'trim_sizes', selected_sizes)

    def render_publishing_editor(self, session: EditingSession):
        """Render publishing section editor."""
        publishing = session.imprint.publishing
        
        # Primary genres
        st.markdown("**Primary Genres**")
        available_genres = [
            "Fiction", "Non-Fiction", "Mystery", "Romance", "Science Fiction", 
            "Fantasy", "Thriller", "Biography", "Self-Help", "Business", 
            "History", "Science", "Art", "Children's", "Young Adult"
        ]
        # Safe access to primary_genres - handle None values
        primary_genres = getattr(publishing, 'primary_genres', None) or []
        selected_genres = st.multiselect(
            "Primary Genres",
            available_genres,
            default=[genre for genre in primary_genres if genre in available_genres],
            help="Main genres your imprint will focus on"
        )
        if selected_genres != publishing.primary_genres:
            st.session_state.imprint_editor.update_field(session, 'publishing', 'primary_genres', selected_genres)
        
        # Target audience
        current_audience = safe_getattr(publishing, 'target_audience', '')
        new_audience = st.text_input(
            "Target Audience",
            value=current_audience,
            help="Primary readership for your books"
        )
        if new_audience != current_audience:
            st.session_state.imprint_editor.update_field(session, 'publishing', 'target_audience', new_audience)
        
        # Publication frequency
        frequency_options = ["Weekly", "Bi-weekly", "Monthly", "Bi-monthly", "Quarterly", "Irregular"]
        current_frequency = publishing.publication_frequency if publishing.publication_frequency in frequency_options else "Monthly"
        new_frequency = st.selectbox(
            "Publication Frequency",
            frequency_options,
            index=frequency_options.index(current_frequency),
            help="How often you plan to publish new books"
        )
        if new_frequency != publishing.publication_frequency:
            st.session_state.imprint_editor.update_field(session, 'publishing', 'publication_frequency', new_frequency)

    def render_operations_editor(self, session: EditingSession):
        """Render operations section editor."""
        production = session.imprint.production
        distribution = session.imprint.distribution
        
        # Workflow stages
        st.markdown("**Production Workflow**")
        workflow_stages = production.workflow_stages or []
        stages_text = "\n".join(workflow_stages) if workflow_stages else ""
        new_stages_text = st.text_area(
            "Workflow Stages (one per line)",
            value=stages_text,
            help="Steps in your production workflow"
        )
        new_stages = [s.strip() for s in new_stages_text.split('\n') if s.strip()]
        if new_stages != production.workflow_stages:
            st.session_state.imprint_editor.update_field(session, 'production', 'workflow_stages', new_stages)
        
        # Distribution channels
        st.markdown("**Distribution Channels**")
        available_channels = [
            "Amazon KDP", "IngramSpark", "Barnes & Noble", "Apple Books", 
            "Kobo", "Direct Sales", "Bookstores", "Libraries"
        ]
        # Safe access to primary_channels - handle None values
        primary_channels = getattr(distribution, 'primary_channels', None) or []
        selected_channels = st.multiselect(
            "Primary Distribution Channels",
            available_channels,
            default=[ch for ch in primary_channels if ch in available_channels],
            help="Where your books will be sold"
        )
        if selected_channels != distribution.primary_channels:
            st.session_state.imprint_editor.update_field(session, 'distribution', 'primary_channels', selected_channels)
        
        # Automation settings
        st.markdown("**Automation Settings**")
        col1, col2 = st.columns(2)
        
        with col1:
            auto_formatting = st.checkbox(
                "Auto-formatting",
                value=production.automation_settings.get('auto_formatting', False),
                help="Automatically format manuscripts"
            )
            if auto_formatting != production.automation_settings.get('auto_formatting', False):
                new_automation = production.automation_settings.copy()
                new_automation['auto_formatting'] = auto_formatting
                st.session_state.imprint_editor.update_field(session, 'production', 'automation_settings', new_automation)
        
        with col2:
            auto_validation = st.checkbox(
                "Auto-validation",
                value=production.automation_settings.get('auto_validation', False),
                help="Automatically validate content"
            )
            if auto_validation != production.automation_settings.get('auto_validation', False):
                new_automation = production.automation_settings.copy()
                new_automation['auto_validation'] = auto_validation
                st.session_state.imprint_editor.update_field(session, 'production', 'automation_settings', new_automation)

    def render_artifact_generation(self):
        """Render artifact generation interface."""
        st.header("Generate Artifacts")
        
        if 'current_imprint' not in st.session_state:
            st.info("👈 Create an imprint first using the 'Create Imprint' tab")
            return
        
        imprint = st.session_state.current_imprint
        
        branding = safe_getattr(imprint, 'branding', {})
        imprint_name = safe_getattr(branding, 'imprint_name', 'Unnamed Imprint')
        st.markdown(f"### Generate artifacts for **{imprint_name}**")
        
        # Artifact selection
        st.markdown("**Select artifacts to generate:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            generate_templates = st.checkbox("📄 LaTeX Templates", value=True)
            generate_prompts = st.checkbox("🤖 LLM Prompts", value=True)
            generate_configs = st.checkbox("⚙️ Configuration Files", value=True)
        
        with col2:
            generate_workflow = st.checkbox("📋 Workflow Definitions", value=True)
            generate_docs = st.checkbox("📚 Documentation", value=True)
            validate_artifacts = st.checkbox("✅ Validate Generated Files", value=True)
        
        # Output directory
        branding = safe_getattr(imprint, 'branding', {})
        imprint_name = safe_getattr(branding, 'imprint_name', 'unnamed_imprint')
        output_dir = st.text_input(
            "Output Directory",
            value=f"output/{imprint_name.lower().replace(' ', '_')}_artifacts",
            help="Where to save the generated artifacts"
        )
        
        # Generate button
        if st.button("🔧 Generate Artifacts", type="primary"):
            with st.spinner("Generating artifacts..."):
                try:
                    results = st.session_state.artifact_generator.generate_all_artifacts(
                        imprint, output_dir
                    )
                    
                    # Display results
                    st.success("✅ Artifacts generated successfully!")
                    
                    # Show summary
                    st.markdown("### 📊 Generation Summary")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Artifacts Created", len(results.get('artifacts', {})))
                    
                    with col2:
                        st.metric("Errors", len(results.get('errors', [])))
                    
                    with col3:
                        st.metric("Warnings", len(results.get('warnings', [])))
                    
                    # Show details
                    for artifact_type, artifact_result in results.get('artifacts', {}).items():
                        with st.expander(f"📁 {artifact_type.title()}"):
                            if artifact_result.get('status') == 'success':
                                st.success("Generated successfully")
                                if 'files_generated' in artifact_result:
                                    st.write("**Files created:**")
                                    for file in artifact_result['files_generated']:
                                        st.write(f"• {file}")
                                if 'output_directory' in artifact_result:
                                    st.write(f"**Location:** `{artifact_result['output_directory']}`")
                            else:
                                st.error(f"Generation failed: {artifact_result.get('error', 'Unknown error')}")
                    
                    # Validation results
                    if 'validation' in results:
                        validation = results['validation']
                        st.markdown("### 🔍 Validation Results")
                        
                        if validation.get('overall_valid', False):
                            st.success("All artifacts passed validation")
                        else:
                            st.warning("Some validation issues found")
                            
                            for validation_type, validation_result in validation.items():
                                if validation_type != 'overall_valid' and isinstance(validation_result, dict):
                                    if not validation_result.get('valid', True):
                                        st.write(f"**{validation_type.title()}:**")
                                        issues = validation_result.get('issues', None) or []
                                        for issue in issues:
                                            st.write(f"• {issue}")
                    
                    # Download option
                    st.markdown("### 📥 Download")
                    st.info(f"Artifacts saved to: `{output_dir}`")
                    
                except Exception as e:
                    st.error(f"Error generating artifacts: {str(e)}")
                    self.logger.error(f"Error in artifact generation: {e}")

    def render_schedule_planning(self):
        """Render schedule planning interface."""
        st.header("Schedule Planning")
        
        if 'current_imprint' not in st.session_state:
            st.info("👈 Create an imprint first using the 'Create Imprint' tab")
            return
        
        imprint = st.session_state.current_imprint
        
        branding = safe_getattr(imprint, 'branding', {})
        imprint_name = safe_getattr(branding, 'imprint_name', 'Unnamed Imprint')
        st.markdown(f"### Plan publication schedule for **{imprint_name}**")
        
        # Schedule parameters
        col1, col2 = st.columns(2)
        
        with col1:
            num_books = st.number_input(
                "Number of Books",
                min_value=1,
                max_value=50,
                value=12,
                help="How many books to include in the initial schedule"
            )
            
            planning_horizon = st.number_input(
                "Planning Horizon (months)",
                min_value=6,
                max_value=36,
                value=18,
                help="How far ahead to plan"
            )
        
        with col2:
            books_per_year = st.number_input(
                "Target Books Per Year",
                min_value=1,
                max_value=100,
                value=12,
                help="Annual publication target"
            )
            
            start_date = st.date_input(
                "Schedule Start Date",
                value=datetime.now().date(),
                help="When to start the publication schedule"
            )
        
        # Generate schedule button
        if st.button("📅 Generate Schedule", type="primary"):
            with st.spinner("Generating publication schedule..."):
                try:
                    # Generate initial schedule
                    schedules = st.session_state.schedule_generator.generate_initial_schedule(
                        imprint, num_books, planning_horizon
                    )
                    
                    # Store in session state
                    st.session_state.current_schedules = schedules
                    
                    # Display results
                    st.success(f"✅ Generated schedule for {len(schedules)} books!")
                    
                    # Schedule overview
                    st.markdown("### 📊 Schedule Overview")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Books", len(schedules))
                    
                    with col2:
                        # Safe access to schedules - handle None values
                        safe_schedules = schedules or []
                        high_priority = sum(1 for s in safe_schedules if getattr(s, 'priority', None) == 'high')
                        st.metric("High Priority", high_priority)
                    
                    with col3:
                        avg_timeline = sum((s.publication_date - s.start_date).days for s in schedules) / len(schedules)
                        st.metric("Avg Timeline (days)", int(avg_timeline))
                    
                    with col4:
                        total_words = sum(s.estimated_word_count for s in schedules)
                        st.metric("Total Words", f"{total_words:,}")
                    
                    # Schedule table
                    st.markdown("### 📋 Book Schedule")
                    
                    schedule_data = []
                    for schedule in schedules:
                        schedule_data.append({
                            "Title": schedule.title,
                            "Author": schedule.author,
                            "Genre": schedule.genre,
                            "Priority": schedule.priority,
                            "Start Date": schedule.start_date.strftime("%Y-%m-%d"),
                            "Publication Date": schedule.publication_date.strftime("%Y-%m-%d"),
                            "Word Count": f"{schedule.estimated_word_count:,}",
                            "Timeline (days)": (schedule.publication_date - schedule.start_date).days
                        })
                    
                    st.dataframe(schedule_data, use_container_width=True)
                    
                    # Timeline visualization
                    st.markdown("### 📈 Timeline Visualization")
                    
                    # Create a simple timeline chart
                    import pandas as pd
                    
                    timeline_data = []
                    for schedule in schedules:
                        timeline_data.append({
                            "Book": schedule.title,
                            "Start": schedule.start_date,
                            "End": schedule.publication_date,
                            "Priority": schedule.priority
                        })
                    
                    df = pd.DataFrame(timeline_data)
                    st.dataframe(df, use_container_width=True)
                    
                    # Export options
                    st.markdown("### 📥 Export Schedule")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("💾 Save Schedule"):
                            branding = safe_getattr(imprint, 'branding', {})
                            imprint_name = safe_getattr(branding, 'imprint_name', 'unnamed_imprint')
                            schedule_file = f"schedules/{imprint_name.lower().replace(' ', '_')}_schedule.json"
                            st.session_state.schedule_generator.save_schedule(schedules, schedule_file)
                            st.success(f"Schedule saved to {schedule_file}")
                    
                    with col2:
                        # Convert to CSV for download
                        csv_data = pd.DataFrame(schedule_data).to_csv(index=False)
                        st.download_button(
                            "📊 Download CSV",
                            csv_data,
                            f"{imprint_name}_schedule.csv",
                            "text/csv"
                        )
                
                except Exception as e:
                    st.error(f"Error generating schedule: {str(e)}")
                    self.logger.error(f"Error in schedule generation: {e}")

    def render_management_interface(self):
        """Render imprint management interface."""
        st.header("Imprint Management")
        
        # Current imprint status
        if 'current_imprint' in st.session_state:
            imprint = st.session_state.current_imprint
            
            branding = safe_getattr(imprint, 'branding', {})
            imprint_name = safe_getattr(branding, 'imprint_name', 'Unnamed Imprint')
            st.markdown(f"### Current Imprint: **{imprint_name}**")
            
            # Status overview
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Created", imprint.expanded_at.strftime("%Y-%m-%d"))
            
            with col2:
                if 'editing_session' in st.session_state:
                    changes = len(st.session_state.editing_session.change_history)
                    st.metric("Changes Made", changes)
                else:
                    st.metric("Changes Made", 0)
            
            with col3:
                if 'current_schedules' in st.session_state:
                    books = len(st.session_state.current_schedules)
                    st.metric("Scheduled Books", books)
                else:
                    st.metric("Scheduled Books", 0)
            
            with col4:
                primary_genres = getattr(imprint.publishing, 'primary_genres', None) or []
                st.metric("Primary Genres", len(primary_genres))
            
            # Actions
            st.markdown("### 🔧 Actions")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 Export Imprint Definition"):
                    imprint_data = imprint.to_dict()
                    json_str = json.dumps(imprint_data, indent=2, default=str)
                    st.download_button(
                        "💾 Download JSON",
                        json_str,
                        f"{imprint_name}_definition.json",
                        "application/json"
                    )
            
            with col2:
                if st.button("🔄 Reset Imprint"):
                    # Clear session state
                    keys_to_clear = ['current_imprint', 'current_concept', 'editing_session', 'current_schedules']
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.success("Imprint reset successfully!")
                    st.rerun()
            
            with col3:
                if st.button("📋 Generate Summary Report"):
                    self.generate_summary_report(imprint)
        
        else:
            st.info("No imprint currently loaded. Create one using the 'Create Imprint' tab.")
        
        # Import imprint
        st.markdown("### 📥 Import Imprint")
        
        uploaded_file = st.file_uploader(
            "Upload Imprint Definition",
            type=['json'],
            help="Upload a previously exported imprint definition"
        )
        
        if uploaded_file is not None:
            try:
                imprint_data = json.load(uploaded_file)
                
                # Reconstruct imprint (simplified - would need proper deserialization)
                st.success("Imprint definition loaded successfully!")
                st.json(imprint_data)
                
            except Exception as e:
                st.error(f"Error loading imprint definition: {str(e)}")

    def generate_summary_report(self, imprint: ExpandedImprint):
        """Generate a summary report for the imprint."""
        st.markdown("### 📊 Imprint Summary Report")
        
        branding = safe_getattr(imprint, 'branding', {})
        imprint_name = safe_getattr(branding, 'imprint_name', 'Unnamed Imprint')
        
        report = f"""
# {imprint_name} - Summary Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Branding
- **Mission:** {safe_getattr(imprint.branding, 'mission_statement', 'Not specified')}
- **Tagline:** {safe_getattr(imprint.branding, 'tagline', 'Not specified')}
- **Brand Values:** {', '.join(safe_getattr(imprint.branding, 'brand_values', []))}
- **USP:** {safe_getattr(imprint.branding, 'unique_selling_proposition', 'Not specified')}

## Publishing Strategy
- **Primary Genres:** {', '.join(imprint.publishing.primary_genres or [])}
- **Target Audience:** {imprint.publishing.target_audience}
- **Publication Frequency:** {imprint.publishing.publication_frequency}

## Design Guidelines
- **Primary Color:** {(getattr(imprint.design, 'color_palette', None) or {}).get('primary_color', 'Not specified')}
- **Primary Font:** {(getattr(imprint.design, 'typography', None) or {}).get('primary_font', 'Not specified')}
- **Trim Sizes:** {', '.join(getattr(imprint.design, 'trim_sizes', None) or [])}

## Operations
- **Workflow Stages:** {len(getattr(imprint.production, 'workflow_stages', None) or [])} stages
- **Distribution Channels:** {', '.join(getattr(imprint.distribution, 'primary_channels', None) or [])}
- **Automation Level:** {'High' if imprint.production.automation_settings.get('auto_formatting') else 'Standard'}

## Status
- **Created:** {imprint.created_at.strftime("%Y-%m-%d")}
- **Completeness:** Ready for production
        """
        
        st.markdown(report)
        
        # Download report
        st.download_button(
            "📄 Download Report",
            report,
            f"{imprint_name}_report.md",
            "text/markdown"
        )


    def render_marketing_editor(self, session: EditingSession):
        """Render marketing section editor."""
        marketing = session.imprint.marketing_approach
        
        st.markdown("**Target Platforms**")
        current_platforms = safe_getattr(marketing, 'target_platforms', [])
        platforms_text = "\n".join(current_platforms) if current_platforms else ""
        new_platforms_text = st.text_area(
            "Marketing Platforms (one per line)",
            value=platforms_text,
            help="Digital and traditional platforms for marketing"
        )
        new_platforms = [p.strip() for p in new_platforms_text.split('\n') if p.strip()]
        if new_platforms != current_platforms:
            st.session_state.imprint_editor.update_field(session, 'marketing_approach', 'target_platforms', new_platforms)
        
        # Promotional Activities
        st.markdown("**Promotional Activities**")
        current_activities = safe_getattr(marketing, 'promotional_activities', [])
        activities_text = "\n".join(current_activities) if current_activities else ""
        new_activities_text = st.text_area(
            "Promotional Activities (one per line)",
            value=activities_text,
            help="Specific campaigns and activities"
        )
        new_activities = [a.strip() for a in new_activities_text.split('\n') if a.strip()]
        if new_activities != current_activities:
            st.session_state.imprint_editor.update_field(session, 'marketing_approach', 'promotional_activities', new_activities)
        
        # Audience Engagement
        current_engagement = safe_getattr(marketing, 'audience_engagement_tactics', '')
        new_engagement = st.text_area(
            "Audience Engagement Tactics",
            value=current_engagement,
            help="Strategies to build and nurture community"
        )
        if new_engagement != current_engagement:
            st.session_state.imprint_editor.update_field(session, 'marketing_approach', 'audience_engagement_tactics', new_engagement)
        
        # Budget Allocation
        st.markdown("**Budget Allocation**")
        budget_allocation = safe_getattr(marketing, 'budget_allocation', {})
        
        col1, col2 = st.columns(2)
        with col1:
            digital_ads = st.slider("Digital Ads (%)", 0, 100, 
                                   int(budget_allocation.get('digital_ads', '40%').replace('%', '')))
            influencer = st.slider("Influencer Marketing (%)", 0, 100, 
                                 int(budget_allocation.get('influencer_marketing', '30%').replace('%', '')))
        with col2:
            events = st.slider("Events (%)", 0, 100, 
                             int(budget_allocation.get('events', '20%').replace('%', '')))
            pr = st.slider("PR (%)", 0, 100, 
                         int(budget_allocation.get('PR', '10%').replace('%', '')))
        
        new_budget = {
            'digital_ads': f'{digital_ads}%',
            'influencer_marketing': f'{influencer}%',
            'events': f'{events}%',
            'PR': f'{pr}%'
        }
        if new_budget != budget_allocation:
            st.session_state.imprint_editor.update_field(session, 'marketing_approach', 'budget_allocation', new_budget)

    def render_financial_editor(self, session: EditingSession):
        """Render financial section editor."""
        financial = session.imprint.financial_projections
        
        # Revenue Target
        current_revenue = safe_getattr(financial, 'first_year_revenue_target', 250000)
        new_revenue = st.number_input(
            "First Year Revenue Target ($)",
            min_value=0,
            value=int(current_revenue) if isinstance(current_revenue, (int, float)) else 250000,
            step=10000,
            help="Realistic revenue target for the first year"
        )
        if new_revenue != current_revenue:
            st.session_state.imprint_editor.update_field(session, 'financial_projections', 'first_year_revenue_target', new_revenue)
        
        # Profit Margin
        current_margin = safe_getattr(financial, 'profit_margin_goal', 0.25)
        new_margin = st.slider(
            "Profit Margin Goal (%)",
            0.0, 1.0, 
            float(current_margin) if isinstance(current_margin, (int, float)) else 0.25,
            step=0.05,
            format="%.0%",
            help="Target profit margin as a percentage"
        )
        if new_margin != current_margin:
            st.session_state.imprint_editor.update_field(session, 'financial_projections', 'profit_margin_goal', new_margin)
        
        # Investment Required
        current_investment = safe_getattr(financial, 'investment_required', 100000)
        new_investment = st.number_input(
            "Investment Required ($)",
            min_value=0,
            value=int(current_investment) if isinstance(current_investment, (int, float)) else 100000,
            step=5000,
            help="Estimated initial investment needed"
        )
        if new_investment != current_investment:
            st.session_state.imprint_editor.update_field(session, 'financial_projections', 'investment_required', new_investment)
        
        # Funding Sources
        current_sources = safe_getattr(financial, 'funding_sources', [])
        sources_text = "\n".join(current_sources) if current_sources else ""
        new_sources_text = st.text_area(
            "Funding Sources (one per line)",
            value=sources_text,
            help="Potential sources of funding"
        )
        new_sources = [s.strip() for s in new_sources_text.split('\n') if s.strip()]
        if new_sources != current_sources:
            st.session_state.imprint_editor.update_field(session, 'financial_projections', 'funding_sources', new_sources)
        
        # Royalty Rates
        st.markdown("**Royalty Rates Structure**")
        royalty_rates = safe_getattr(financial, 'royalty_rates_structure', {})
        
        col1, col2 = st.columns(2)
        with col1:
            authors_rate = st.text_input(
                "Authors Royalty Rate",
                value=royalty_rates.get('authors', '10-15%'),
                help="Typical royalty percentage for authors"
            )
        with col2:
            agents_rate = st.text_input(
                "Agents Commission Rate",
                value=royalty_rates.get('agents', '15%'),
                help="Typical commission percentage for agents"
            )
        
        new_royalty_rates = {
            'authors': authors_rate,
            'agents': agents_rate
        }
        if new_royalty_rates != royalty_rates:
            st.session_state.imprint_editor.update_field(session, 'financial_projections', 'royalty_rates_structure', new_royalty_rates)

def render_imprint_builder_page():
    """Main function to render the imprint builder page."""
    builder = StreamlitImprintBuilder()
    builder.render_main_interface()


# For standalone testing
if __name__ == "__main__":
    render_imprint_builder_page()