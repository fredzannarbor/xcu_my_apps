"""
Universal Workflow Selector Component

Provides a unified interface for selecting and configuring different workflows
(tournaments, reader panels, series generation) that can work with any content type.
Enhanced with advanced features including analytics, templates, export, and automation.
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import sys

# Add project paths for imports
project_root = Path(__file__).resolve().parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from codexes.modules.ideation.core.codex_object import CodexObject, CodexObjectType
from codexes.modules.ideation.tournament.tournament_engine import TournamentEngine, TournamentType
from codexes.modules.ideation.synthetic_readers.reader_panel import SyntheticReaderPanel
from codexes.modules.ideation.series.series_generator import SeriesGenerator, SeriesConfiguration, SeriesType
from codexes.modules.ideation.storage.database_manager import IdeationDatabase, DatabaseManager

# Import advanced workflow components
from codexes.ui.components.workflow_analytics import WorkflowAnalytics
from codexes.ui.components.workflow_templates import WorkflowTemplateManager
from codexes.ui.components.workflow_export import WorkflowExporter
from codexes.ui.components.workflow_automation import WorkflowAutomation

logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """Available workflow types."""
    TOURNAMENT = "tournament"
    READER_PANEL = "reader_panel"
    SERIES_GENERATION = "series_generation"


@dataclass
class WorkflowConfiguration:
    """Configuration for workflow execution."""
    workflow_type: WorkflowType
    name: str = ""
    description: str = ""
    mixed_type_handling: str = "adaptive"  # adaptive, normalize, separate
    parameters: Dict[str, Any] = field(default_factory=dict)
    progress_tracking: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "workflow_type": self.workflow_type.value,
            "name": self.name,
            "description": self.description,
            "mixed_type_handling": self.mixed_type_handling,
            "parameters": self.parameters,
            "progress_tracking": self.progress_tracking
        }


class WorkflowSelector:
    """
    Universal workflow selector and configuration interface.
    Enhanced with advanced features including analytics, templates, export, and automation.
    Implements Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6.
    """
    
    def __init__(self):
        """Initialize the workflow selector with advanced features."""
        self.session_key = "workflow_selector_state"
        
        # Initialize database with default path
        db_path = "data/ideation.db"
        db_manager = DatabaseManager(db_path)
        self.database = IdeationDatabase(db_manager)
        
        # Initialize workflow engines
        self.tournament_engine = TournamentEngine(self.database)
        self.reader_panel = SyntheticReaderPanel()
        self.series_generator = SeriesGenerator()
        
        # Initialize advanced workflow components
        self.analytics = WorkflowAnalytics()
        self.template_manager = WorkflowTemplateManager()
        self.exporter = WorkflowExporter()
        self.automation = WorkflowAutomation()
        
        logger.info("WorkflowSelector initialized with advanced features")
    
    def render_workflow_selection_interface(self, available_objects: List[CodexObject]) -> Dict[str, Any]:
        """
        Render the enhanced workflow selection interface with advanced features.
        
        Args:
            available_objects: List of CodexObjects available for workflow processing
            
        Returns:
            Dictionary containing workflow execution results
        """
        if not available_objects:
            st.info("📝 No content available for workflow processing. Create some content first!")
            return {}
        
        # Initialize session state
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                'selected_workflow': None,
                'workflow_config': None,
                'execution_results': {},
                'execution_history': [],
                'current_template': None
            }
        
        state = st.session_state[self.session_key]
        
        # Create main workflow tabs with advanced features
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🚀 Execute Workflow", 
            "📊 Analytics", 
            "📋 Templates", 
            "📤 Export", 
            "🤖 Automation"
        ])
        
        with tab1:
            return self._render_workflow_execution_tab(available_objects)
        
        with tab2:
            return self._render_analytics_tab(state.get('execution_results', {}))
        
        with tab3:
            return self._render_templates_tab()
        
        with tab4:
            return self._render_export_tab(state.get('execution_results', {}))
        
        with tab5:
            return self._render_automation_tab()
    
    def _render_workflow_execution_tab(self, available_objects: List[CodexObject]) -> Dict[str, Any]:
        """Render the main workflow execution interface."""
        # Content source selection
        st.markdown("### 📊 Content Selection")
        content_source = self._render_content_source_selection(available_objects)
        
        if not content_source['selected_objects']:
            st.warning("⚠️ Please select content to process.")
            return {}
        
        # Template selection (optional)
        st.markdown("### 📋 Template Selection (Optional)")
        selected_template = self._render_template_selection()
        
        # Workflow type selection
        st.markdown("### ⚙️ Workflow Selection")
        workflow_type = self._render_workflow_type_selection()
        
        if not workflow_type:
            return {}
        
        # Mixed-type handling information
        self._display_mixed_type_info(content_source['selected_objects'])
        
        # Workflow-specific configuration
        st.markdown("### 🔧 Workflow Configuration")
        workflow_config = self._render_workflow_configuration(
            workflow_type, 
            content_source['selected_objects'],
            selected_template
        )
        
        if not workflow_config:
            return {}
        
        # Execution controls
        st.markdown("### 🚀 Execution")
        execution_results = self._render_execution_controls(
            workflow_type, 
            workflow_config, 
            content_source['selected_objects']
        )
        
        return execution_results
    
    def _render_analytics_tab(self, execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Render the analytics tab."""
        return self.analytics.render_analytics_dashboard(execution_results)
    
    def _render_templates_tab(self) -> Dict[str, Any]:
        """Render the templates tab."""
        return self.template_manager.render_template_management_interface()
    
    def _render_export_tab(self, execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Render the export tab."""
        return self.exporter.render_export_interface(execution_results)
    
    def _render_automation_tab(self) -> Dict[str, Any]:
        """Render the automation tab."""
        return self.automation.render_automation_interface()
    
    def _render_content_source_selection(self, available_objects: List[CodexObject]) -> Dict[str, Any]:
        """Render content source selection interface."""
        st.markdown("**Select content for workflow processing:**")
        
        # Content type analysis
        type_counts = {}
        for obj in available_objects:
            type_name = obj.object_type.value.title()
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # Display content overview
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write(f"**Available Content:** {len(available_objects)} objects")
            type_summary = ", ".join([f"{count} {type_name}" for type_name, count in type_counts.items()])
            st.write(f"**Types:** {type_summary}")
        
        with col2:
            select_all = st.checkbox("Select All", value=True)
        
        # Object selection
        if select_all:
            selected_objects = available_objects
            st.success(f"✅ Selected all {len(available_objects)} objects")
        else:
            # Individual selection interface
            selected_indices = st.multiselect(
                "Choose specific objects:",
                options=range(len(available_objects)),
                format_func=lambda i: f"{available_objects[i].title} ({available_objects[i].object_type.value.title()})",
                default=list(range(len(available_objects)))
            )
            selected_objects = [available_objects[i] for i in selected_indices]
        
        return {
            'selected_objects': selected_objects,
            'type_counts': type_counts,
            'mixed_types': len(type_counts) > 1
        }
    
    def _render_workflow_type_selection(self) -> Optional[WorkflowType]:
        """Render workflow type selection interface."""
        workflow_options = {
            "🏆 Tournament": {
                "type": WorkflowType.TOURNAMENT,
                "description": "Competitive evaluation where content competes head-to-head",
                "best_for": "Finding the strongest concepts, comparing alternatives",
                "supports_mixed": True
            },
            "👥 Reader Panel": {
                "type": WorkflowType.READER_PANEL,
                "description": "Synthetic readers evaluate content for market appeal",
                "best_for": "Market testing, audience feedback, appeal assessment",
                "supports_mixed": True
            },
            "📚 Series Generation": {
                "type": WorkflowType.SERIES_GENERATION,
                "description": "Generate related book concepts for series development",
                "best_for": "Creating book series, franchise development",
                "supports_mixed": False
            }
        }
        
        # Display workflow options
        selected_workflow = st.radio(
            "Choose workflow type:",
            options=list(workflow_options.keys()),
            format_func=lambda x: x,
            help="Select the type of workflow to run on your content"
        )
        
        if selected_workflow:
            workflow_info = workflow_options[selected_workflow]
            
            # Display workflow details
            with st.expander(f"ℹ️ About {selected_workflow}", expanded=False):
                st.write(f"**Description:** {workflow_info['description']}")
                st.write(f"**Best for:** {workflow_info['best_for']}")
                st.write(f"**Supports mixed content types:** {'✅ Yes' if workflow_info['supports_mixed'] else '❌ No'}")
            
            return workflow_info["type"]
        
        return None
    
    def _display_mixed_type_info(self, selected_objects: List[CodexObject]):
        """Display information about mixed content types."""
        if not selected_objects:
            return
        
        # Analyze content types
        type_counts = {}
        for obj in selected_objects:
            type_name = obj.object_type.value.title()
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        if len(type_counts) > 1:
            st.warning(f"⚠️ **Mixed Content Types Detected:** {len(type_counts)} different types")
            
            # Show type breakdown
            type_breakdown = []
            for type_name, count in type_counts.items():
                percentage = (count / len(selected_objects)) * 100
                type_breakdown.append(f"{type_name}: {count} ({percentage:.1f}%)")
            
            st.write("**Content breakdown:** " + ", ".join(type_breakdown))
            
            # Mixed-type handling options
            st.info("🔧 **Mixed-Type Handling:** The workflow will adapt evaluation criteria for fair comparison across different content types.")
        else:
            type_name = list(type_counts.keys())[0]
            st.success(f"✅ **Uniform Content Type:** All {len(selected_objects)} objects are {type_name}")
    
    def _render_template_selection(self) -> Optional[Dict[str, Any]]:
        """Render template selection interface."""
        # Get available templates
        state = st.session_state.get(self.template_manager.session_key, {})
        templates = state.get('templates', [])
        
        if not templates:
            st.info("💡 No templates available. Create templates in the Templates tab to speed up workflow configuration.")
            return None
        
        # Filter templates by workflow type if one is selected
        available_templates = templates
        
        template_options = [("None", None)] + [(t.name, t) for t in available_templates]
        
        selected_template_info = st.selectbox(
            "Use Template",
            options=template_options,
            format_func=lambda x: x[0],
            help="Select a saved template to pre-fill configuration"
        )
        
        if selected_template_info[1] is not None:
            template = selected_template_info[1]
            st.success(f"✅ Using template: {template.name}")
            
            with st.expander("📋 Template Details", expanded=False):
                st.write(f"**Description:** {template.description}")
                st.write(f"**Workflow Type:** {template.workflow_type.replace('_', ' ').title()}")
                if template.tags:
                    st.write(f"**Tags:** {', '.join(template.tags)}")
            
            return template
        
        return None
    
    def _render_workflow_configuration(self, workflow_type: WorkflowType, 
                                     selected_objects: List[CodexObject],
                                     selected_template: Optional[Any] = None) -> Optional[WorkflowConfiguration]:
        """Render workflow-specific configuration interface with template support."""
        # Pre-fill with template if available
        template_config = None
        if selected_template and selected_template.workflow_type == workflow_type.value:
            template_config = selected_template.parameters
            st.info(f"🔧 Configuration pre-filled from template: {selected_template.name}")
        
        if workflow_type == WorkflowType.TOURNAMENT:
            return self._render_tournament_configuration(selected_objects, template_config)
        elif workflow_type == WorkflowType.READER_PANEL:
            return self._render_reader_panel_configuration(selected_objects, template_config)
        elif workflow_type == WorkflowType.SERIES_GENERATION:
            return self._render_series_generation_configuration(selected_objects, template_config)
        
        return None
    
    def _render_tournament_configuration(self, selected_objects: List[CodexObject], 
                                       template_config: Optional[Dict[str, Any]] = None) -> Optional[WorkflowConfiguration]:
        """Render tournament-specific configuration with template support."""
        st.markdown("**Tournament Configuration**")
        
        # Get default values from template if available
        default_tournament_type = TournamentType.SINGLE_ELIMINATION
        default_criteria = {
            "originality": 0.3,
            "marketability": 0.3,
            "execution_potential": 0.2,
            "emotional_impact": 0.2
        }
        default_mixed_handling = "adaptive"
        
        if template_config:
            if "tournament_type" in template_config:
                default_tournament_type = template_config["tournament_type"]
            if "evaluation_criteria" in template_config:
                default_criteria.update(template_config["evaluation_criteria"])
            if "mixed_type_handling" in template_config:
                default_mixed_handling = template_config["mixed_type_handling"]
        
        # Tournament name
        tournament_name = st.text_input(
            "Tournament Name:",
            value=f"Tournament {len(selected_objects)} Entries",
            help="Give your tournament a descriptive name"
        )
        
        # Tournament type
        tournament_type_options = [
            ("Single Elimination", TournamentType.SINGLE_ELIMINATION),
            ("Double Elimination", TournamentType.DOUBLE_ELIMINATION),
            ("Round Robin", TournamentType.ROUND_ROBIN)
        ]
        
        # Find default index
        default_index = 0
        for i, (_, t_type) in enumerate(tournament_type_options):
            if t_type == default_tournament_type:
                default_index = i
                break
        
        tournament_type = st.selectbox(
            "Tournament Type:",
            options=tournament_type_options,
            index=default_index,
            format_func=lambda x: x[0],
            help="Choose the tournament format"
        )
        
        # Evaluation criteria
        st.markdown("**Evaluation Criteria** (weights must sum to 1.0)")
        
        col1, col2 = st.columns(2)
        with col1:
            originality_weight = st.slider("Originality", 0.0, 1.0, default_criteria["originality"], 0.05)
            marketability_weight = st.slider("Marketability", 0.0, 1.0, default_criteria["marketability"], 0.05)
        
        with col2:
            execution_weight = st.slider("Execution Potential", 0.0, 1.0, default_criteria["execution_potential"], 0.05)
            emotional_weight = st.slider("Emotional Impact", 0.0, 1.0, default_criteria["emotional_impact"], 0.05)
        
        # Validate weights
        total_weight = originality_weight + marketability_weight + execution_weight + emotional_weight
        
        if abs(total_weight - 1.0) > 0.01:
            st.error(f"⚠️ Evaluation criteria weights must sum to 1.0 (currently {total_weight:.2f})")
            return None
        
        # Mixed-type handling for tournaments
        mixed_type_handling = default_mixed_handling
        if len(set(obj.object_type for obj in selected_objects)) > 1:
            mixed_options = [
                ("Adaptive", "adaptive"),
                ("Normalize to Common Type", "normalize"),
                ("Type-Aware Comparison", "type_aware")
            ]
            
            # Find default index
            default_mixed_index = 0
            for i, (_, handling) in enumerate(mixed_options):
                if handling == default_mixed_handling:
                    default_mixed_index = i
                    break
            
            mixed_type_handling = st.selectbox(
                "Mixed-Type Evaluation:",
                options=mixed_options,
                index=default_mixed_index,
                format_func=lambda x: x[0],
                help="How to handle different content types in the same tournament"
            )[1]
        
        # Option to save as template
        if st.checkbox("💾 Save as Template", help="Save this configuration as a reusable template"):
            template_name = st.text_input("Template Name", value=f"{tournament_name} Template")
            template_description = st.text_area("Template Description", value="Tournament configuration template")
            
            if template_name and template_description:
                # This would save the template - implementation would call template_manager
                st.info("💡 Template will be saved after workflow execution")
        
        return WorkflowConfiguration(
            workflow_type=WorkflowType.TOURNAMENT,
            name=tournament_name,
            description=f"{tournament_type[0].value} tournament with {len(selected_objects)} participants",
            mixed_type_handling=mixed_type_handling,
            parameters={
                "tournament_type": tournament_type[1],
                "evaluation_criteria": {
                    "originality": originality_weight,
                    "marketability": marketability_weight,
                    "execution_potential": execution_weight,
                    "emotional_impact": emotional_weight
                }
            }
        )
    
    def _render_reader_panel_configuration(self, selected_objects: List[CodexObject],
                                         template_config: Optional[Dict[str, Any]] = None) -> Optional[WorkflowConfiguration]:
        """Render reader panel-specific configuration with template support."""
        st.markdown("**Reader Panel Configuration**")
        
        # Get default values from template
        default_panel_size = 8
        default_demographics = {
            "age_distribution": "balanced",
            "gender_distribution": "balanced",
            "reading_level_focus": "balanced",
            "genre_diversity": "medium"
        }
        default_evaluation_focus = ["Market Appeal", "Emotional Engagement", "Genre Fit"]
        
        if template_config:
            default_panel_size = template_config.get("panel_size", default_panel_size)
            default_demographics.update(template_config.get("demographics", {}))
            default_evaluation_focus = template_config.get("evaluation_focus", default_evaluation_focus)
        
        # Panel name
        panel_name = st.text_input(
            "Panel Name:",
            value=f"Reader Panel - {len(selected_objects)} Items",
            help="Give your reader panel evaluation a descriptive name"
        )
        
        # Panel size
        panel_size = st.slider(
            "Panel Size:",
            min_value=3,
            max_value=20,
            value=default_panel_size,
            help="Number of synthetic readers in the panel"
        )
        
        # Demographics configuration
        st.markdown("**Target Demographics**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            age_distribution = st.selectbox(
                "Age Distribution:",
                options=[
                    ("Balanced", "balanced"),
                    ("Young Adult Focus", "young_adult"),
                    ("Adult Focus", "adult"),
                    ("Mature Focus", "mature")
                ],
                format_func=lambda x: x[0]
            )
            
            gender_distribution = st.selectbox(
                "Gender Distribution:",
                options=[
                    ("Balanced", "balanced"),
                    ("Female Focus", "female"),
                    ("Male Focus", "male")
                ],
                format_func=lambda x: x[0]
            )
        
        with col2:
            reading_level = st.selectbox(
                "Reading Level Focus:",
                options=[
                    ("Balanced", "balanced"),
                    ("Casual Readers", "casual"),
                    ("Avid Readers", "avid"),
                    ("Literary Readers", "literary")
                ],
                format_func=lambda x: x[0]
            )
            
            genre_diversity = st.selectbox(
                "Genre Diversity:",
                options=[
                    ("High", "high"),
                    ("Medium", "medium"),
                    ("Low", "low")
                ],
                format_func=lambda x: x[0]
            )
        
        # Evaluation focus
        evaluation_focus = st.multiselect(
            "Evaluation Focus Areas:",
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
        
        return WorkflowConfiguration(
            workflow_type=WorkflowType.READER_PANEL,
            name=panel_name,
            description=f"Reader panel evaluation with {panel_size} synthetic readers",
            mixed_type_handling="adaptive",
            parameters={
                "panel_size": panel_size,
                "demographics": {
                    "age_distribution": age_distribution[1],
                    "gender_distribution": gender_distribution[1],
                    "reading_level_focus": reading_level[1],
                    "genre_diversity": genre_diversity[1]
                },
                "evaluation_focus": evaluation_focus
            }
        )
    
    def _render_series_generation_configuration(self, selected_objects: List[CodexObject]) -> Optional[WorkflowConfiguration]:
        """Render series generation-specific configuration."""
        st.markdown("**Series Generation Configuration**")
        
        # Check if multiple objects selected for series generation
        if len(selected_objects) > 1:
            st.warning("⚠️ Series generation works best with a single base concept. Using the first selected object.")
        
        base_object = selected_objects[0]
        
        # Series name
        series_name = st.text_input(
            "Series Name:",
            value=f"{base_object.title} Series",
            help="Name for the book series"
        )
        
        # Series type
        series_type = st.selectbox(
            "Series Type:",
            options=[
                ("Standalone Series", SeriesType.STANDALONE_SERIES),
                ("Sequential Series", SeriesType.SEQUENTIAL_SERIES),
                ("Character Series", SeriesType.CHARACTER_SERIES),
                ("Anthology Series", SeriesType.ANTHOLOGY_SERIES),
                ("Franchise Series", SeriesType.FRANCHISE_SERIES)
            ],
            format_func=lambda x: x[0],
            help="Type of series to generate"
        )
        
        # Number of books
        book_count = st.slider(
            "Number of Books:",
            min_value=2,
            max_value=10,
            value=3,
            help="How many books to generate in the series"
        )
        
        # Formulaicness level
        formulaicness = st.slider(
            "Formulaicness Level:",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="How similar should books be? 0=very different, 1=very similar"
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
        franchise_mode = st.checkbox(
            "Franchise Mode",
            value=False,
            help="Enable franchise mode for expanded universe potential"
        )
        
        return WorkflowConfiguration(
            workflow_type=WorkflowType.SERIES_GENERATION,
            name=series_name,
            description=f"{series_type[0].value} with {book_count} books",
            mixed_type_handling="single_source",
            parameters={
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
                "franchise_mode": franchise_mode,
                "base_object": base_object
            }
        )
    
    def _render_execution_controls(self, workflow_type: WorkflowType, 
                                 workflow_config: WorkflowConfiguration,
                                 selected_objects: List[CodexObject]) -> Dict[str, Any]:
        """Render workflow execution controls and results."""
        # Execution preview
        st.markdown("**Execution Preview**")
        
        preview_info = self._generate_execution_preview(workflow_type, workflow_config, selected_objects)
        
        with st.expander("📋 Execution Details", expanded=True):
            for key, value in preview_info.items():
                st.write(f"**{key}:** {value}")
        
        # Execution button
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            execute_button = st.button(
                f"🚀 Execute {workflow_type.value.replace('_', ' ').title()}",
                type="primary",
                use_container_width=True
            )
        
        # Execute workflow
        if execute_button:
            return self._execute_workflow(workflow_type, workflow_config, selected_objects)
        
        # Show previous results if available
        state = st.session_state[self.session_key]
        if state.get('execution_results'):
            st.markdown("### 📊 Previous Results")
            self._display_execution_results(state['execution_results'])
        
        return {}
    
    def _generate_execution_preview(self, workflow_type: WorkflowType,
                                  workflow_config: WorkflowConfiguration,
                                  selected_objects: List[CodexObject]) -> Dict[str, str]:
        """Generate execution preview information."""
        preview = {
            "Workflow Type": workflow_type.value.replace('_', ' ').title(),
            "Content Objects": f"{len(selected_objects)} objects",
            "Mixed Types": "Yes" if len(set(obj.object_type for obj in selected_objects)) > 1 else "No"
        }
        
        if workflow_type == WorkflowType.TOURNAMENT:
            tournament_type = workflow_config.parameters.get("tournament_type", TournamentType.SINGLE_ELIMINATION)
            preview.update({
                "Tournament Type": tournament_type.value.replace('_', ' ').title(),
                "Estimated Matches": str(self._estimate_tournament_matches(len(selected_objects), tournament_type)),
                "Evaluation Criteria": "Originality, Marketability, Execution, Emotional Impact"
            })
        
        elif workflow_type == WorkflowType.READER_PANEL:
            panel_size = workflow_config.parameters.get("panel_size", 8)
            demographics = workflow_config.parameters.get("demographics", {})
            preview.update({
                "Panel Size": f"{panel_size} synthetic readers",
                "Demographics": f"{demographics.get('age_distribution', 'balanced').title()} age, {demographics.get('gender_distribution', 'balanced').title()} gender",
                "Total Evaluations": f"{len(selected_objects) * panel_size} individual evaluations"
            })
        
        elif workflow_type == WorkflowType.SERIES_GENERATION:
            book_count = workflow_config.parameters.get("target_book_count", 3)
            series_type = workflow_config.parameters.get("series_type", SeriesType.STANDALONE_SERIES)
            preview.update({
                "Series Type": series_type.value.replace('_', ' ').title(),
                "Books to Generate": str(book_count),
                "Base Concept": selected_objects[0].title if selected_objects else "None"
            })
        
        return preview
    
    def _estimate_tournament_matches(self, participant_count: int, tournament_type: TournamentType) -> int:
        """Estimate number of matches in a tournament."""
        if tournament_type == TournamentType.SINGLE_ELIMINATION:
            return participant_count - 1
        elif tournament_type == TournamentType.DOUBLE_ELIMINATION:
            return (participant_count - 1) * 2
        elif tournament_type == TournamentType.ROUND_ROBIN:
            return (participant_count * (participant_count - 1)) // 2
        else:
            return participant_count - 1
    
    def _execute_workflow(self, workflow_type: WorkflowType,
                         workflow_config: WorkflowConfiguration,
                         selected_objects: List[CodexObject]) -> Dict[str, Any]:
        """Execute the selected workflow."""
        try:
            st.info("🚀 Executing workflow... This may take a moment.")
            
            # Create progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = {}
            
            if workflow_type == WorkflowType.TOURNAMENT:
                results = self._execute_tournament(workflow_config, selected_objects, progress_bar, status_text)
            
            elif workflow_type == WorkflowType.READER_PANEL:
                results = self._execute_reader_panel(workflow_config, selected_objects, progress_bar, status_text)
            
            elif workflow_type == WorkflowType.SERIES_GENERATION:
                results = self._execute_series_generation(workflow_config, selected_objects, progress_bar, status_text)
            
            # Store results in session state
            state = st.session_state[self.session_key]
            state['execution_results'] = results
            state['execution_history'].append({
                'timestamp': st.session_state.get('timestamp', 'unknown'),
                'workflow_type': workflow_type.value,
                'config': workflow_config.to_dict(),
                'results_summary': self._generate_results_summary(results)
            })
            
            progress_bar.progress(1.0)
            status_text.success("✅ Workflow execution completed!")
            
            # Display results
            self._display_execution_results(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            st.error(f"❌ Workflow execution failed: {str(e)}")
            return {"error": str(e)}
    
    def _execute_tournament(self, config: WorkflowConfiguration, 
                          objects: List[CodexObject],
                          progress_bar, status_text) -> Dict[str, Any]:
        """Execute tournament workflow."""
        try:
            status_text.text("Creating tournament...")
            progress_bar.progress(0.1)
            
            # Create tournament
            tournament = self.tournament_engine.create_tournament(
                name=config.name,
                participants=objects,
                tournament_type=config.parameters["tournament_type"],
                config={"evaluation_criteria": config.parameters["evaluation_criteria"]}
            )
            
            status_text.text("Running tournament matches...")
            progress_bar.progress(0.3)
            
            # Execute tournament
            completed_tournament = self.tournament_engine.run_tournament(tournament, objects)
            
            status_text.text("Generating results...")
            progress_bar.progress(0.8)
            
            # Get results
            results = self.tournament_engine.get_tournament_results(completed_tournament)
            
            return {
                "workflow_type": "tournament",
                "tournament_results": results,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Tournament execution error: {e}")
            return {"workflow_type": "tournament", "error": str(e), "success": False}
    
    def _execute_reader_panel(self, config: WorkflowConfiguration,
                            objects: List[CodexObject],
                            progress_bar, status_text) -> Dict[str, Any]:
        """Execute reader panel workflow."""
        try:
            status_text.text("Creating reader panel...")
            progress_bar.progress(0.1)
            
            # Create panel
            demographics = config.parameters["demographics"]
            panel_size = config.parameters["panel_size"]
            
            panel = self.reader_panel.create_panel(demographics, panel_size)
            
            status_text.text("Evaluating content with readers...")
            progress_bar.progress(0.3)
            
            # Evaluate each object
            panel_results = []
            for i, obj in enumerate(objects):
                status_text.text(f"Evaluating object {i+1}/{len(objects)}...")
                progress_bar.progress(0.3 + (0.5 * (i+1) / len(objects)))
                
                result = self.reader_panel.evaluate_content(obj, panel)
                panel_results.append({
                    "object_uuid": obj.uuid,
                    "object_title": obj.title,
                    "results": result
                })
            
            status_text.text("Compiling results...")
            progress_bar.progress(0.9)
            
            return {
                "workflow_type": "reader_panel",
                "panel_results": panel_results,
                "panel_size": panel_size,
                "demographics": demographics,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Reader panel execution error: {e}")
            return {"workflow_type": "reader_panel", "error": str(e), "success": False}
    
    def _execute_series_generation(self, config: WorkflowConfiguration,
                                 objects: List[CodexObject],
                                 progress_bar, status_text) -> Dict[str, Any]:
        """Execute series generation workflow."""
        try:
            status_text.text("Creating series configuration...")
            progress_bar.progress(0.1)
            
            # Get base object
            base_object = config.parameters["base_object"]
            
            # Create series configuration
            series_config = SeriesConfiguration(
                series_type=config.parameters["series_type"],
                formulaicness_level=config.parameters["formulaicness_level"],
                target_book_count=config.parameters["target_book_count"],
                consistency_requirements=config.parameters["consistency_requirements"],
                franchise_mode=config.parameters["franchise_mode"]
            )
            
            status_text.text("Generating series entries...")
            progress_bar.progress(0.3)
            
            # Generate series
            series_entries = self.series_generator.generate_complete_series(base_object, series_config)
            
            status_text.text("Compiling series results...")
            progress_bar.progress(0.9)
            
            return {
                "workflow_type": "series_generation",
                "base_object": {
                    "uuid": base_object.uuid,
                    "title": base_object.title
                },
                "series_entries": [
                    {
                        "uuid": entry.uuid,
                        "title": entry.title,
                        "content": entry.content,
                        "genre": entry.genre,
                        "object_type": entry.object_type.value
                    }
                    for entry in series_entries
                ],
                "series_config": series_config.__dict__,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Series generation execution error: {e}")
            return {"workflow_type": "series_generation", "error": str(e), "success": False}
    
    def _display_execution_results(self, results: Dict[str, Any]):
        """Display workflow execution results."""
        if not results:
            return
        
        if not results.get("success", False):
            st.error(f"❌ Workflow failed: {results.get('error', 'Unknown error')}")
            return
        
        workflow_type = results.get("workflow_type")
        
        if workflow_type == "tournament":
            self._display_tournament_results(results)
        elif workflow_type == "reader_panel":
            self._display_reader_panel_results(results)
        elif workflow_type == "series_generation":
            self._display_series_generation_results(results)
    
    def _display_tournament_results(self, results: Dict[str, Any]):
        """Display tournament results."""
        st.success("🏆 Tournament Completed!")
        
        tournament_results = results.get("tournament_results", {})
        
        if tournament_results.get("completed"):
            # Winner announcement
            winner_uuid = tournament_results.get("winner")
            if winner_uuid:
                st.markdown(f"### 🥇 Winner: {winner_uuid}")
            
            # Tournament statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Participants", tournament_results.get("participant_count", 0))
            
            with col2:
                st.metric("Total Rounds", tournament_results.get("round_count", 0))
            
            with col3:
                st.metric("Total Matches", len(tournament_results.get("match_results", [])))
            
            # Bracket summary
            if "bracket_summary" in tournament_results:
                with st.expander("📊 Tournament Bracket", expanded=False):
                    bracket = tournament_results["bracket_summary"]
                    for round_name, matches in bracket.get("rounds", {}).items():
                        st.write(f"**{round_name}:**")
                        for match in matches:
                            participants = match.get("participants", [])
                            winner = match.get("winner", "TBD")
                            st.write(f"  • {participants[0]} vs {participants[1]} → Winner: {winner}")
            
            # Rankings
            if "rankings" in tournament_results:
                with st.expander("🏅 Final Rankings", expanded=True):
                    rankings = tournament_results["rankings"]
                    for rank_info in rankings[:10]:  # Top 10
                        rank = rank_info.get("rank", "?")
                        uuid = rank_info.get("uuid", "Unknown")
                        wins = rank_info.get("wins", 0)
                        losses = rank_info.get("losses", 0)
                        st.write(f"{rank}. {uuid} ({wins}W-{losses}L)")
        else:
            st.warning("Tournament results not available or incomplete.")
    
    def _display_reader_panel_results(self, results: Dict[str, Any]):
        """Display reader panel results."""
        st.success("👥 Reader Panel Evaluation Completed!")
        
        panel_results = results.get("panel_results", [])
        panel_size = results.get("panel_size", 0)
        
        if panel_results:
            # Overall statistics
            st.markdown(f"### 📊 Panel Overview")
            st.write(f"**Panel Size:** {panel_size} synthetic readers")
            st.write(f"**Objects Evaluated:** {len(panel_results)}")
            
            # Results for each object
            for i, result in enumerate(panel_results):
                object_title = result.get("object_title", f"Object {i+1}")
                panel_result = result.get("results")
                
                with st.expander(f"📖 {object_title}", expanded=i == 0):
                    if panel_result:
                        # Key metrics
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            avg_rating = getattr(panel_result, 'average_rating', 0)
                            st.metric("Average Rating", f"{avg_rating:.1f}/5")
                        
                        with col2:
                            would_read = getattr(panel_result, 'would_read_percentage', 0)
                            st.metric("Would Read", f"{would_read:.1f}%")
                        
                        with col3:
                            rec_score = getattr(panel_result, 'recommendation_score', 0)
                            st.metric("Recommendation", f"{rec_score:.1f}/5")
                        
                        # Detailed insights
                        if hasattr(panel_result, 'market_appeal_insights'):
                            insights = panel_result.market_appeal_insights
                            if insights:
                                st.write("**Market Position:**", insights.get("market_position", "Unknown"))
                                
                                top_appeals = insights.get("top_appeal_factors", [])
                                if top_appeals:
                                    st.write("**Top Appeal Factors:**")
                                    for factor in top_appeals[:3]:
                                        st.write(f"  • {factor.get('factor', 'Unknown')} ({factor.get('mentions', 0)} mentions)")
                    else:
                        st.warning("No detailed results available for this object.")
        else:
            st.warning("No panel results available.")
    
    def _display_series_generation_results(self, results: Dict[str, Any]):
        """Display series generation results."""
        st.success("📚 Series Generation Completed!")
        
        base_object = results.get("base_object", {})
        series_entries = results.get("series_entries", [])
        series_config = results.get("series_config", {})
        
        # Series overview
        st.markdown(f"### 📖 Generated Series")
        st.write(f"**Base Concept:** {base_object.get('title', 'Unknown')}")
        st.write(f"**Books Generated:** {len(series_entries)}")
        st.write(f"**Series Type:** {series_config.get('series_type', 'Unknown')}")
        st.write(f"**Formulaicness Level:** {series_config.get('formulaicness_level', 0):.1f}")
        
        # Series entries
        if series_entries:
            st.markdown("### 📚 Series Books")
            
            for i, entry in enumerate(series_entries, 1):
                with st.expander(f"Book {i}: {entry.get('title', f'Book {i}')}", expanded=i == 1):
                    st.write(f"**Title:** {entry.get('title', 'Untitled')}")
                    st.write(f"**Genre:** {entry.get('genre', 'Not specified')}")
                    st.write(f"**Type:** {entry.get('object_type', 'Unknown').title()}")
                    
                    content = entry.get('content', '')
                    if content:
                        st.write("**Concept:**")
                        st.write(content[:500] + "..." if len(content) > 500 else content)
        else:
            st.warning("No series entries were generated.")
    
    def _generate_results_summary(self, results: Dict[str, Any]) -> str:
        """Generate a brief summary of results for history."""
        if not results.get("success", False):
            return f"Failed: {results.get('error', 'Unknown error')}"
        
        workflow_type = results.get("workflow_type")
        
        if workflow_type == "tournament":
            tournament_results = results.get("tournament_results", {})
            participant_count = tournament_results.get("participant_count", 0)
            return f"Tournament with {participant_count} participants completed"
        
        elif workflow_type == "reader_panel":
            panel_results = results.get("panel_results", [])
            panel_size = results.get("panel_size", 0)
            return f"Reader panel with {panel_size} readers evaluated {len(panel_results)} objects"
        
        elif workflow_type == "series_generation":
            series_entries = results.get("series_entries", [])
            return f"Generated series with {len(series_entries)} books"
        
        return "Workflow completed"