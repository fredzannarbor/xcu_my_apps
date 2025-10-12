"""
Workflow Templates Component

Provides functionality for creating, saving, and managing workflow templates
and configurations for reuse across different content sets.
"""

import streamlit as st
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).resolve().parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from codexes.modules.ideation.core.codex_object import CodexObjectType
from codexes.modules.ideation.tournament.tournament_engine import TournamentType
from codexes.modules.ideation.series.series_generator import SeriesType

logger = logging.getLogger(__name__)


@dataclass
class WorkflowTemplate:
    """Template for workflow configurations."""
    id: str
    name: str
    description: str
    workflow_type: str
    parameters: Dict[str, Any]
    created_date: str
    last_used: Optional[str] = None
    usage_count: int = 0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowTemplate':
        """Create from dictionary."""
        return cls(**data)


class WorkflowTemplateManager:
    """
    Manages workflow templates and saved configurations.
    Provides functionality for creating, saving, loading, and organizing templates.
    """
    
    def __init__(self):
        """Initialize the workflow template manager."""
        self.session_key = "workflow_templates_state"
        self.templates_file = Path("data/workflow_templates.json")
        self.templates_file.parent.mkdir(exist_ok=True)
        
        # Initialize session state
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                'templates': self._load_templates(),
                'current_template': None,
                'template_categories': ['Tournament', 'Reader Panel', 'Series Generation', 'Custom']
            }
        
        logger.info("WorkflowTemplateManager initialized")
    
    def render_template_management_interface(self) -> Dict[str, Any]:
        """
        Render the template management interface.
        
        Returns:
            Dictionary containing template management results
        """
        st.markdown("### 📋 Workflow Templates")
        
        # Create tabs for different template operations
        tab1, tab2, tab3, tab4 = st.tabs(["📚 Browse Templates", "➕ Create Template", "📝 Edit Templates", "📊 Template Analytics"])
        
        with tab1:
            return self._render_browse_templates()
        
        with tab2:
            return self._render_create_template()
        
        with tab3:
            return self._render_edit_templates()
        
        with tab4:
            return self._render_template_analytics()
    
    def _render_browse_templates(self) -> Dict[str, Any]:
        """Render template browsing interface."""
        st.markdown("#### 📚 Available Templates")
        
        state = st.session_state[self.session_key]
        templates = state['templates']
        
        if not templates:
            st.info("No templates available. Create your first template in the 'Create Template' tab!")
            return {}
        
        # Filter and search
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_term = st.text_input("🔍 Search templates", placeholder="Search by name or description...")
        
        with col2:
            category_filter = st.selectbox(
                "Category Filter",
                options=["All"] + state['template_categories']
            )
        
        with col3:
            sort_by = st.selectbox(
                "Sort By",
                options=["Name", "Created Date", "Usage Count", "Last Used"]
            )
        
        # Filter templates
        filtered_templates = self._filter_templates(templates, search_term, category_filter)
        
        # Sort templates
        filtered_templates = self._sort_templates(filtered_templates, sort_by)
        
        if not filtered_templates:
            st.warning("No templates match your search criteria.")
            return {}
        
        # Display templates
        st.markdown(f"**Found {len(filtered_templates)} templates:**")
        
        selected_template = None
        
        for template in filtered_templates:
            with st.expander(f"📋 {template.name}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Description:** {template.description}")
                    st.write(f"**Type:** {template.workflow_type.replace('_', ' ').title()}")
                    st.write(f"**Created:** {template.created_date}")
                    st.write(f"**Used:** {template.usage_count} times")
                    
                    if template.tags:
                        st.write(f"**Tags:** {', '.join(template.tags)}")
                    
                    # Show template parameters preview
                    with st.expander("⚙️ Configuration Preview", expanded=False):
                        st.json(template.parameters)
                
                with col2:
                    if st.button(f"Use Template", key=f"use_{template.id}"):
                        selected_template = template
                        self._update_template_usage(template.id)
                    
                    if st.button(f"Duplicate", key=f"dup_{template.id}"):
                        self._duplicate_template(template)
                        st.rerun()
        
        if selected_template:
            return {
                "action": "template_selected",
                "template": selected_template,
                "template_config": selected_template.parameters
            }
        
        return {}
    
    def _render_create_template(self) -> Dict[str, Any]:
        """Render template creation interface."""
        st.markdown("#### ➕ Create New Template")
        
        # Template basic information
        template_name = st.text_input(
            "Template Name *",
            placeholder="e.g., 'Fantasy Tournament Standard', 'Reader Panel - YA Focus'"
        )
        
        template_description = st.text_area(
            "Description *",
            placeholder="Describe what this template is for and when to use it..."
        )
        
        # Workflow type selection
        workflow_type = st.selectbox(
            "Workflow Type *",
            options=[
                ("Tournament", "tournament"),
                ("Reader Panel", "reader_panel"),
                ("Series Generation", "series_generation")
            ],
            format_func=lambda x: x[0]
        )
        
        if not workflow_type:
            return {}
        
        workflow_type_value = workflow_type[1]
        
        # Template tags
        template_tags = st.multiselect(
            "Tags (optional)",
            options=["Fantasy", "Sci-Fi", "Romance", "Mystery", "YA", "Adult", "Quick", "Detailed", "Beginner", "Advanced"],
            help="Add tags to help organize and find templates"
        )
        
        custom_tags = st.text_input(
            "Custom Tags (comma-separated)",
            placeholder="custom, tag, names"
        )
        
        if custom_tags:
            custom_tag_list = [tag.strip() for tag in custom_tags.split(",") if tag.strip()]
            template_tags.extend(custom_tag_list)
        
        # Workflow-specific configuration
        st.markdown("#### ⚙️ Workflow Configuration")
        
        template_config = None
        
        if workflow_type_value == "tournament":
            template_config = self._render_tournament_template_config()
        elif workflow_type_value == "reader_panel":
            template_config = self._render_reader_panel_template_config()
        elif workflow_type_value == "series_generation":
            template_config = self._render_series_template_config()
        
        # Save template
        if template_name and template_description and template_config:
            if st.button("💾 Save Template", type="primary"):
                template_id = self._generate_template_id(template_name)
                
                new_template = WorkflowTemplate(
                    id=template_id,
                    name=template_name,
                    description=template_description,
                    workflow_type=workflow_type_value,
                    parameters=template_config,
                    created_date=datetime.now().isoformat(),
                    tags=template_tags
                )
                
                self._save_template(new_template)
                st.success(f"✅ Template '{template_name}' saved successfully!")
                st.rerun()
        
        return {}
    
    def _render_edit_templates(self) -> Dict[str, Any]:
        """Render template editing interface."""
        st.markdown("#### 📝 Edit Templates")
        
        state = st.session_state[self.session_key]
        templates = state['templates']
        
        if not templates:
            st.info("No templates available to edit.")
            return {}
        
        # Select template to edit
        template_options = [(t.name, t.id) for t in templates]
        selected_template_info = st.selectbox(
            "Select Template to Edit",
            options=template_options,
            format_func=lambda x: x[0]
        )
        
        if not selected_template_info:
            return {}
        
        selected_template = next(t for t in templates if t.id == selected_template_info[1])
        
        # Edit template
        with st.form("edit_template_form"):
            st.markdown(f"**Editing: {selected_template.name}**")
            
            # Basic information
            new_name = st.text_input("Template Name", value=selected_template.name)
            new_description = st.text_area("Description", value=selected_template.description)
            new_tags = st.multiselect(
                "Tags",
                options=["Fantasy", "Sci-Fi", "Romance", "Mystery", "YA", "Adult", "Quick", "Detailed", "Beginner", "Advanced"],
                default=selected_template.tags
            )
            
            # Configuration editing (simplified - show as JSON for now)
            st.markdown("**Configuration:**")
            config_json = st.text_area(
                "Template Configuration (JSON)",
                value=json.dumps(selected_template.parameters, indent=2),
                height=300
            )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.form_submit_button("💾 Save Changes", type="primary"):
                    try:
                        new_config = json.loads(config_json)
                        
                        # Update template
                        selected_template.name = new_name
                        selected_template.description = new_description
                        selected_template.tags = new_tags
                        selected_template.parameters = new_config
                        
                        self._update_template(selected_template)
                        st.success("✅ Template updated successfully!")
                        st.rerun()
                        
                    except json.JSONDecodeError:
                        st.error("❌ Invalid JSON configuration. Please check the format.")
            
            with col2:
                if st.form_submit_button("🗑️ Delete Template"):
                    self._delete_template(selected_template.id)
                    st.success("✅ Template deleted successfully!")
                    st.rerun()
            
            with col3:
                if st.form_submit_button("📋 Duplicate Template"):
                    self._duplicate_template(selected_template)
                    st.success("✅ Template duplicated successfully!")
                    st.rerun()
        
        return {}
    
    def _render_template_analytics(self) -> Dict[str, Any]:
        """Render template analytics and usage statistics."""
        st.markdown("#### 📊 Template Analytics")
        
        state = st.session_state[self.session_key]
        templates = state['templates']
        
        if not templates:
            st.info("No templates available for analytics.")
            return {}
        
        # Overall statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Templates", len(templates))
        
        with col2:
            total_usage = sum(t.usage_count for t in templates)
            st.metric("Total Usage", total_usage)
        
        with col3:
            workflow_types = len(set(t.workflow_type for t in templates))
            st.metric("Workflow Types", workflow_types)
        
        with col4:
            avg_usage = total_usage / len(templates) if templates else 0
            st.metric("Avg Usage", f"{avg_usage:.1f}")
        
        # Usage statistics
        st.markdown("#### 📈 Usage Statistics")
        
        # Most used templates
        most_used = sorted(templates, key=lambda t: t.usage_count, reverse=True)[:5]
        
        if most_used:
            st.markdown("**Most Used Templates:**")
            for i, template in enumerate(most_used):
                st.write(f"{i+1}. **{template.name}** - {template.usage_count} uses ({template.workflow_type})")
        
        # Template distribution by type
        type_counts = {}
        for template in templates:
            workflow_type = template.workflow_type.replace('_', ' ').title()
            type_counts[workflow_type] = type_counts.get(workflow_type, 0) + 1
        
        if type_counts:
            st.markdown("**Templates by Type:**")
            for workflow_type, count in type_counts.items():
                percentage = (count / len(templates)) * 100
                st.write(f"• {workflow_type}: {count} ({percentage:.1f}%)")
        
        # Tag analysis
        all_tags = []
        for template in templates:
            all_tags.extend(template.tags)
        
        if all_tags:
            tag_counts = {}
            for tag in all_tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            st.markdown("**Popular Tags:**")
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            for tag, count in sorted_tags:
                st.write(f"• {tag}: {count}")
        
        return {}
    
    def _render_tournament_template_config(self) -> Dict[str, Any]:
        """Render tournament template configuration."""
        st.markdown("**Tournament Configuration**")
        
        # Tournament type
        tournament_type = st.selectbox(
            "Tournament Type",
            options=[
                ("Single Elimination", TournamentType.SINGLE_ELIMINATION),
                ("Double Elimination", TournamentType.DOUBLE_ELIMINATION),
                ("Round Robin", TournamentType.ROUND_ROBIN)
            ],
            format_func=lambda x: x[0]
        )
        
        # Evaluation criteria
        st.markdown("**Evaluation Criteria** (weights must sum to 1.0)")
        
        col1, col2 = st.columns(2)
        with col1:
            originality_weight = st.slider("Originality", 0.0, 1.0, 0.3, 0.05)
            marketability_weight = st.slider("Marketability", 0.0, 1.0, 0.3, 0.05)
        
        with col2:
            execution_weight = st.slider("Execution Potential", 0.0, 1.0, 0.2, 0.05)
            emotional_weight = st.slider("Emotional Impact", 0.0, 1.0, 0.2, 0.05)
        
        # Validate weights
        total_weight = originality_weight + marketability_weight + execution_weight + emotional_weight
        
        if abs(total_weight - 1.0) > 0.01:
            st.error(f"⚠️ Evaluation criteria weights must sum to 1.0 (currently {total_weight:.2f})")
            return None
        
        # Mixed-type handling
        mixed_type_handling = st.selectbox(
            "Mixed-Type Handling",
            options=[
                ("Adaptive", "adaptive"),
                ("Normalize to Common Type", "normalize"),
                ("Type-Aware Comparison", "type_aware")
            ],
            format_func=lambda x: x[0]
        )
        
        return {
            "tournament_type": tournament_type[1],
            "evaluation_criteria": {
                "originality": originality_weight,
                "marketability": marketability_weight,
                "execution_potential": execution_weight,
                "emotional_impact": emotional_weight
            },
            "mixed_type_handling": mixed_type_handling[1]
        }
    
    def _render_reader_panel_template_config(self) -> Dict[str, Any]:
        """Render reader panel template configuration."""
        st.markdown("**Reader Panel Configuration**")
        
        # Panel size
        panel_size = st.slider("Panel Size", min_value=3, max_value=20, value=8)
        
        # Demographics
        col1, col2 = st.columns(2)
        
        with col1:
            age_distribution = st.selectbox(
                "Age Distribution",
                options=[
                    ("Balanced", "balanced"),
                    ("Young Adult Focus", "young_adult"),
                    ("Adult Focus", "adult"),
                    ("Mature Focus", "mature")
                ],
                format_func=lambda x: x[0]
            )
            
            gender_distribution = st.selectbox(
                "Gender Distribution",
                options=[
                    ("Balanced", "balanced"),
                    ("Female Focus", "female"),
                    ("Male Focus", "male")
                ],
                format_func=lambda x: x[0]
            )
        
        with col2:
            reading_level = st.selectbox(
                "Reading Level Focus",
                options=[
                    ("Balanced", "balanced"),
                    ("Casual Readers", "casual"),
                    ("Avid Readers", "avid"),
                    ("Literary Readers", "literary")
                ],
                format_func=lambda x: x[0]
            )
            
            genre_diversity = st.selectbox(
                "Genre Diversity",
                options=[
                    ("High", "high"),
                    ("Medium", "medium"),
                    ("Low", "low")
                ],
                format_func=lambda x: x[0]
            )
        
        # Evaluation focus
        evaluation_focus = st.multiselect(
            "Evaluation Focus Areas",
            options=[
                "Market Appeal",
                "Emotional Engagement",
                "Character Development",
                "Plot Structure",
                "Writing Quality",
                "Genre Fit",
                "Target Audience Match"
            ],
            default=["Market Appeal", "Emotional Engagement", "Genre Fit"]
        )
        
        return {
            "panel_size": panel_size,
            "demographics": {
                "age_distribution": age_distribution[1],
                "gender_distribution": gender_distribution[1],
                "reading_level_focus": reading_level[1],
                "genre_diversity": genre_diversity[1]
            },
            "evaluation_focus": evaluation_focus
        }
    
    def _render_series_template_config(self) -> Dict[str, Any]:
        """Render series generation template configuration."""
        st.markdown("**Series Generation Configuration**")
        
        # Series type
        series_type = st.selectbox(
            "Series Type",
            options=[
                ("Standalone Series", SeriesType.STANDALONE_SERIES),
                ("Sequential Series", SeriesType.SEQUENTIAL_SERIES),
                ("Character Series", SeriesType.CHARACTER_SERIES),
                ("Anthology Series", SeriesType.ANTHOLOGY_SERIES),
                ("Franchise Series", SeriesType.FRANCHISE_SERIES)
            ],
            format_func=lambda x: x[0]
        )
        
        # Number of books
        book_count = st.slider("Number of Books", min_value=2, max_value=10, value=3)
        
        # Formulaicness level
        formulaicness = st.slider(
            "Formulaicness Level",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1
        )
        
        # Consistency requirements
        st.markdown("**Consistency Requirements**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            setting_consistency = st.slider("Setting", 0.0, 1.0, 0.8, 0.1)
            tone_consistency = st.slider("Tone", 0.0, 1.0, 0.7, 0.1)
            genre_consistency = st.slider("Genre", 0.0, 1.0, 0.9, 0.1)
        
        with col2:
            theme_consistency = st.slider("Themes", 0.0, 1.0, 0.6, 0.1)
            character_consistency = st.slider("Character Types", 0.0, 1.0, 0.5, 0.1)
        
        # Franchise mode
        franchise_mode = st.checkbox("Franchise Mode", value=False)
        
        return {
            "series_type": series_type[1],
            "target_book_count": book_count,
            "formulaicness_level": formulaicness,
            "consistency_requirements": {
                "setting": setting_consistency,
                "tone": tone_consistency,
                "genre": genre_consistency,
                "themes": theme_consistency,
                "character_types": character_consistency
            },
            "franchise_mode": franchise_mode
        }
    
    def _filter_templates(self, templates: List[WorkflowTemplate], search_term: str, category: str) -> List[WorkflowTemplate]:
        """Filter templates based on search and category."""
        filtered = templates
        
        # Search filter
        if search_term:
            search_lower = search_term.lower()
            filtered = [
                t for t in filtered
                if search_lower in t.name.lower() or search_lower in t.description.lower()
            ]
        
        # Category filter
        if category != "All":
            category_mapping = {
                "Tournament": "tournament",
                "Reader Panel": "reader_panel",
                "Series Generation": "series_generation"
            }
            
            if category in category_mapping:
                filtered = [t for t in filtered if t.workflow_type == category_mapping[category]]
        
        return filtered
    
    def _sort_templates(self, templates: List[WorkflowTemplate], sort_by: str) -> List[WorkflowTemplate]:
        """Sort templates based on criteria."""
        if sort_by == "Name":
            return sorted(templates, key=lambda t: t.name.lower())
        elif sort_by == "Created Date":
            return sorted(templates, key=lambda t: t.created_date, reverse=True)
        elif sort_by == "Usage Count":
            return sorted(templates, key=lambda t: t.usage_count, reverse=True)
        elif sort_by == "Last Used":
            return sorted(templates, key=lambda t: t.last_used or "", reverse=True)
        else:
            return templates
    
    def _generate_template_id(self, name: str) -> str:
        """Generate unique template ID."""
        import hashlib
        timestamp = datetime.now().isoformat()
        unique_string = f"{name}_{timestamp}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    def _save_template(self, template: WorkflowTemplate):
        """Save template to session state and file."""
        state = st.session_state[self.session_key]
        state['templates'].append(template)
        self._save_templates_to_file(state['templates'])
    
    def _update_template(self, template: WorkflowTemplate):
        """Update existing template."""
        state = st.session_state[self.session_key]
        templates = state['templates']
        
        for i, t in enumerate(templates):
            if t.id == template.id:
                templates[i] = template
                break
        
        self._save_templates_to_file(templates)
    
    def _delete_template(self, template_id: str):
        """Delete template."""
        state = st.session_state[self.session_key]
        state['templates'] = [t for t in state['templates'] if t.id != template_id]
        self._save_templates_to_file(state['templates'])
    
    def _duplicate_template(self, template: WorkflowTemplate):
        """Duplicate existing template."""
        new_template = WorkflowTemplate(
            id=self._generate_template_id(f"{template.name}_copy"),
            name=f"{template.name} (Copy)",
            description=template.description,
            workflow_type=template.workflow_type,
            parameters=template.parameters.copy(),
            created_date=datetime.now().isoformat(),
            tags=template.tags.copy()
        )
        
        self._save_template(new_template)
    
    def _update_template_usage(self, template_id: str):
        """Update template usage statistics."""
        state = st.session_state[self.session_key]
        templates = state['templates']
        
        for template in templates:
            if template.id == template_id:
                template.usage_count += 1
                template.last_used = datetime.now().isoformat()
                break
        
        self._save_templates_to_file(templates)
    
    def _load_templates(self) -> List[WorkflowTemplate]:
        """Load templates from file."""
        try:
            if self.templates_file.exists():
                with open(self.templates_file, 'r') as f:
                    templates_data = json.load(f)
                    return [WorkflowTemplate.from_dict(data) for data in templates_data]
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
        
        return []
    
    def _save_templates_to_file(self, templates: List[WorkflowTemplate]):
        """Save templates to file."""
        try:
            templates_data = [template.to_dict() for template in templates]
            with open(self.templates_file, 'w') as f:
                json.dump(templates_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving templates: {e}")
    
    def get_template_by_id(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get template by ID."""
        state = st.session_state[self.session_key]
        templates = state['templates']
        
        for template in templates:
            if template.id == template_id:
                return template
        
        return None
    
    def apply_template_to_workflow(self, template: WorkflowTemplate) -> Dict[str, Any]:
        """Apply template configuration to workflow."""
        return {
            "workflow_type": template.workflow_type,
            "name": f"From Template: {template.name}",
            "description": template.description,
            "parameters": template.parameters.copy(),
            "template_id": template.id
        }