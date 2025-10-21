from typing import List, Dict
import sys
from pathlib import Path

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add paths for imports
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

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dotenv import load_dotenv

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

# Load environment variables
load_dotenv()

# Import ideation modules with fallback pattern
try:
    from codexes.modules.ideation import (
        BookIdea, IdeaSet, Tournament, TournamentManager,
        ContinuousIdeaGenerator, IntegratedIdeaGenerator,
        SyntheticReaderPanel, IdeationPipelineBridge
    )
    from codexes.modules.ideation.development_editing_manager import DevelopmentEditingManager
    from codexes.modules.ideation.drafts2reader_panels import Drafts2HighVolumeReaderPanels, EvaluationConfig
    from codexes.modules.ideation.core.codex_object import CodexObject, CodexObjectType, DevelopmentStage
    from codexes.core.llm_integration import LLMCaller
    from codexes.ui.config.model_config import ModelConfigManager
except ImportError:
    from src.codexes.modules.ideation import (
        BookIdea, IdeaSet, Tournament, TournamentManager,
        ContinuousIdeaGenerator, IntegratedIdeaGenerator,
        SyntheticReaderPanel, IdeationPipelineBridge
    )
    from src.codexes.modules.ideation.development_editing_manager import DevelopmentEditingManager
    from src.codexes.modules.ideation.drafts2reader_panels import Drafts2HighVolumeReaderPanels, EvaluationConfig
    from src.codexes.modules.ideation.core.codex_object import CodexObject, CodexObjectType, DevelopmentStage
    from src.codexes.core.llm_integration import LLMCaller
    from src.codexes.ui.config.model_config import ModelConfigManager

# Import safety patterns with fallback
try:
    from codexes.modules.ui.safety_patterns import (
        safe_getattr, safe_dict_get, safe_iteration, safe_len, safe_join,
        validate_not_none, log_none_encounter
    )
    from codexes.modules.ui.safe_components import (
        safe_components, safe_display, display_validation_safely
    )
    from codexes.modules.ui.error_prevention import handle_missing_data
except ImportError:
    try:
        from src.codexes.modules.ui.safety_patterns import (
            safe_getattr, safe_dict_get, safe_iteration, safe_len, safe_join,
            validate_not_none, log_none_encounter
        )
        from src.codexes.modules.ui.safe_components import (
            safe_components, safe_display, display_validation_safely
        )
        from src.codexes.modules.ui.error_prevention import handle_missing_data
    except ImportError:
        # Fallback safety functions
        def safe_getattr(obj, attr, default=None):
            return getattr(obj, attr, default) if obj is not None else default

        def safe_dict_get(d, key, default=None):
            return (d or {}).get(key, default)

        def safe_len(collection):
            return len(collection or [])

        def safe_iteration(collection):
            return collection or []

        def validate_not_none(value, context, attr):
            return value is not None

        def handle_missing_data(data, data_type, context):
            return data if data is not None else ({} if data_type == 'dict' else [])

        safe_components = None
    safe_display = None

# NOTE: st.set_page_config() and render_unified_sidebar() handled by main app

# Import and use page utilities for consistent sidebar and auth
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

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IdeationDashboard:
    """Enhanced Streamlit dashboard for ideation system management."""

    
    def __init__(self):
        # Initialize model config manager
        self.model_config = ModelConfigManager()

        # Safe initialization with None protection
        try:
            self.llm_caller = LLMCaller()
        except Exception as e:
            log_none_encounter('ideation_init', 'LLMCaller')
            self.llm_caller = None
        
        # Safe initialization of components
        try:
            self.tournament_manager = TournamentManager(self.llm_caller) if self.llm_caller else None
        except Exception as e:
            log_none_encounter('ideation_init', 'TournamentManager')
            self.tournament_manager = None
        
        try:
            self.synthetic_reader_panel = SyntheticReaderPanel(self.llm_caller) if self.llm_caller else None
        except Exception as e:
            log_none_encounter('ideation_init', 'SyntheticReaderPanel')
            self.synthetic_reader_panel = None
        
        try:
            self.pipeline_bridge = IdeationPipelineBridge()
        except Exception as e:
            log_none_encounter('ideation_init', 'IdeationPipelineBridge')
            self.pipeline_bridge = None
        
        try:
            self.integrated_generator = IntegratedIdeaGenerator(self.llm_caller) if self.llm_caller else None
        except Exception as e:
            log_none_encounter('ideation_init', 'IntegratedIdeaGenerator')
            self.integrated_generator = None

        try:
            self.development_editing_manager = DevelopmentEditingManager(self.llm_caller) if self.llm_caller else None
        except Exception as e:
            log_none_encounter('ideation_init', 'DevelopmentEditingManager')
            self.development_editing_manager = None

        try:
            self.reader_panels_system = Drafts2HighVolumeReaderPanels(
                llm_caller=self.llm_caller
            ) if self.llm_caller else None
            if self.reader_panels_system:
                self.reader_panels_system.create_default_panels()
        except Exception as e:
            log_none_encounter('ideation_init', 'Drafts2HighVolumeReaderPanels')
            self.reader_panels_system = None

    def render_dashboard(self):
        """Render the main ideation dashboard."""
        st.title('💡 Ideation and Development')
        st.markdown('AI-powered book idea generation, tournament evaluation, and synthetic reader feedback system.')
        
        # Create tabs for different functionalities
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🎯 Idea Generation",
            "🏆 Tournaments",
            "👥 Reader Feedback",
            "✍️ Development Editing",
            "📊 Analytics",
            "⚙️ Settings"
        ])

        with tab1:
            self.render_idea_generation_tab()

        with tab2:
            self.render_tournament_tab()

        with tab3:
            self.render_reader_feedback_tab()

        with tab4:
            self.render_development_editing_tab()

        with tab5:
            self.render_analytics_tab()

        with tab6:
            self.render_settings_tab()

    def render_idea_generation_tab(self):
        """Render idea generation interface."""
        st.header("Book Idea Generation")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Generate New Ideas")
            
            # Generation parameters
            with st.expander("Generation Settings", expanded=True):
                num_ideas = st.slider("Number of ideas to generate", 1, 20, 5)
                model = st.selectbox("Model", ["ollama/mistral:latest", "ollama/llama2:latest", "ollama/deepseek-r1:latest"], index=0)
                temperature = st.slider("Temperature", 0.1, 1.0, 0.7, 0.1)
                
                # Imprint selection
                available_imprints = self._get_available_imprints()
                selected_imprint = st.selectbox("Target Imprint", available_imprints)
                
                # Custom prompt
                use_custom_prompt = st.checkbox("Use custom prompt")
                custom_prompt = ""
                if use_custom_prompt:
                    custom_prompt = st.text_area(
                        "Custom Prompt", 
                        placeholder="Enter your custom idea generation prompt...",
                        height=100
                    )
            
            # Generation buttons
            col_gen1, col_gen2, col_gen3 = st.columns(3)
            
            with col_gen1:
                if st.button("Generate Ideas", type="primary"):
                    self._generate_ideas(num_ideas, model, temperature, selected_imprint, custom_prompt)
            
            with col_gen2:
                if st.button("Start Continuous Generation"):
                    self._start_continuous_generation(selected_imprint, model, temperature)
            
            with col_gen3:
                if st.button("Stop Continuous Generation"):
                    self._stop_continuous_generation(selected_imprint)
        
        with col2:
            st.subheader("Generation Status")
            self._display_generation_status()
        
        # Display recent ideas
        st.subheader("Recent Ideas")
        self._display_recent_ideas()

    def render_tournament_tab(self):
        """Render tournament interface."""
        st.header("Tournament System")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Create Tournament")
            
            # Load available ideas
            available_ideas = self._load_available_ideas()
            
            if available_ideas:
                st.write(f"Available ideas: {len(available_ideas)}")
                
                # Tournament settings
                tournament_size = st.selectbox(
                    "Tournament Size", 
                    [4, 8, 16, 32], 
                    index=1
                )
                
                model = st.selectbox("Judging Model", ["ollama/mistral:latest", "ollama/gpt-oss:20b", "ollama/deepseek-r1:latest"], index=0)

                temperature = st.slider("Judging Temperature", 0.1, 1.0, 0.3, 0.1)
                
                if st.button("Create Tournament", type="primary"):
                    self._create_tournament(available_ideas, tournament_size, model, temperature)
            else:
                st.info("No ideas available for tournament. Generate some ideas first!")
        
        with col2:
            st.subheader("Active Tournaments")
            self._display_active_tournaments()
        
        # Tournament history
        st.subheader("Tournament History")
        self._display_tournament_history()

    def render_reader_feedback_tab(self):
        """Render synthetic reader feedback interface."""
        st.header("Synthetic Reader Feedback")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Evaluate Ideas")
            
            # Load ideas for evaluation
            available_ideas = self._load_available_ideas()
            
            if available_ideas:
                # Select ideas to evaluate
                selected_idea_titles = st.multiselect(
                    "Select ideas to evaluate",
                    [idea.title for idea in available_ideas],
                    max_selections=5
                )
                
                # Select reader personas
                available_personas = [persona.name for persona in self.synthetic_reader_panel.reader_personas]
                selected_personas = st.multiselect(
                    "Select reader personas",
                    available_personas,
                    default=available_personas[:3]
                )
                
                if st.button("Evaluate Ideas", type="primary") and selected_idea_titles:
                    selected_ideas = [idea for idea in available_ideas if idea.title in selected_idea_titles]
                    self._evaluate_ideas_with_readers(selected_ideas, selected_personas)
            else:
                st.info("No ideas available for evaluation. Generate some ideas first!")
        
        with col2:
            st.subheader("Reader Personas")
            self._display_reader_personas()
        
        # Display feedback results
        st.subheader("Recent Feedback")
        self._display_recent_feedback()

    def render_development_editing_tab(self):
        """Render the Development Editing interface."""
        st.header("✍️ Development Editing")
        st.markdown("Move ideas through development stages with synthetic reader feedback loop")

        if not self.development_editing_manager:
            st.error("Development Editing Manager not available. Please check LLM connection.")
            return

        # Create subtabs for different editing functionalities
        edit_tab, panels_tab = st.tabs(["📝 Development Editor", "👥 High-Volume Reader Panels"])

        with edit_tab:
            self._render_development_editor_content()

        with panels_tab:
            self._render_reader_panels_tab()

    def _render_development_editor_content(self):
        """Render the main development editor content."""
        # Main layout with two columns
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.subheader("📝 Select or Create Content")

            # Tab for selecting existing or creating new
            select_tab, create_tab, import_tab = st.tabs(["Select Existing", "Create New", "Import Outline"])

            with select_tab:
                st.write("Browse directories and select files to load")

                # Initialize session state for directory browser
                if 'current_browse_dir' not in st.session_state:
                    # Default to ideation development directory
                    default_dir = Path(__file__).parent.parent.parent.parent / 'data' / 'ideation' / 'development'
                    st.session_state.current_browse_dir = str(default_dir) if default_dir.exists() else str(Path.home())

                # Directory navigation
                st.write(f"**Current Directory:** `{st.session_state.current_browse_dir}`")

                current_path = Path(st.session_state.current_browse_dir)

                # Parent directory button
                col_nav1, col_nav2 = st.columns([1, 3])
                with col_nav1:
                    if st.button("⬆️ Parent", key="parent_dir_btn", use_container_width=True):
                        parent = current_path.parent
                        if parent != current_path:  # Not at root
                            st.session_state.current_browse_dir = str(parent)
                            st.rerun()

                with col_nav2:
                    if st.button("🏠 Reset to Default", key="reset_dir_btn", use_container_width=True):
                        default_dir = Path(__file__).parent.parent.parent.parent / 'data' / 'ideation' / 'development'
                        st.session_state.current_browse_dir = str(default_dir) if default_dir.exists() else str(Path.home())
                        st.rerun()

                # List subdirectories
                try:
                    subdirs = [d for d in current_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
                    subdirs.sort()

                    if subdirs:
                        st.write("**Subdirectories:**")
                        cols = st.columns(min(3, len(subdirs)))
                        for idx, subdir in enumerate(subdirs):
                            with cols[idx % 3]:
                                if st.button(f"📁 {subdir.name}", key=f"subdir_{idx}", use_container_width=True):
                                    st.session_state.current_browse_dir = str(subdir)
                                    st.rerun()

                    st.divider()

                    # List files in current directory
                    files = [f for f in current_path.iterdir() if f.is_file() and f.suffix == '.json']
                    files.sort()

                    if files:
                        st.write(f"**Files in current directory:** ({len(files)} JSON files)")

                        # Multi-select for files
                        if 'selected_files' not in st.session_state:
                            st.session_state.selected_files = []

                        # Select all / Deselect all
                        col_sel1, col_sel2 = st.columns(2)
                        with col_sel1:
                            if st.button("✅ Select All", key="select_all_files"):
                                st.session_state.selected_files = [str(f) for f in files]
                                st.rerun()
                        with col_sel2:
                            if st.button("⬜ Deselect All", key="deselect_all_files"):
                                st.session_state.selected_files = []
                                st.rerun()

                        # Display files with checkboxes
                        file_selection = {}
                        for file in files:
                            file_path_str = str(file)
                            is_selected = file_path_str in st.session_state.selected_files

                            # Try to read basic info from file
                            try:
                                with open(file, 'r') as f:
                                    data = json.load(f)
                                    obj_type = data.get('object_type', 'Unknown')
                                    stage = data.get('development_stage', 'Unknown')
                                    file_label = f"{file.name} ({obj_type}, {stage})"
                            except:
                                file_label = file.name

                            selected = st.checkbox(
                                file_label,
                                value=is_selected,
                                key=f"file_checkbox_{file.name}"
                            )
                            file_selection[file_path_str] = selected

                        # Update session state with selections
                        st.session_state.selected_files = [path for path, selected in file_selection.items() if selected]

                        st.divider()

                        # Load button
                        if st.session_state.selected_files:
                            st.write(f"**{len(st.session_state.selected_files)} file(s) selected**")

                            if st.button("Load Selected Files", type="primary", use_container_width=True):
                                with st.spinner("Loading files..."):
                                    loaded_objects = []
                                    failed_files = []

                                    for file_path in st.session_state.selected_files:
                                        try:
                                            # Try to load as CodexObject first
                                            obj = self.development_editing_manager.load_codex_object(file_path)
                                            if obj:
                                                loaded_objects.append(obj)
                                                logger.info(f"Successfully loaded: {file_path}")
                                            else:
                                                failed_files.append((file_path, "Returned None"))
                                                logger.warning(f"Failed to load (returned None): {file_path}")
                                        except Exception as e:
                                            # Try to detect if it's a book outline and offer conversion
                                            try:
                                                with open(file_path, 'r') as f:
                                                    data = json.load(f)
                                                    if 'book_title' in data or 'chapters' in data:
                                                        # This is a book outline, not a CodexObject
                                                        failed_files.append((file_path, "Book outline format - not a CodexObject. Use 'Create New' to convert."))
                                                    else:
                                                        failed_files.append((file_path, f"Invalid format: {str(e)}"))
                                            except:
                                                failed_files.append((file_path, f"Error: {str(e)}"))
                                            logger.error(f"Error loading {file_path}: {e}")

                                    if loaded_objects:
                                        if len(loaded_objects) == 1:
                                            st.session_state.current_codex_object = loaded_objects[0]
                                            st.success(f"✅ Loaded: {loaded_objects[0].title}")
                                            logger.info(f"Set current_codex_object to: {loaded_objects[0].title}")
                                        else:
                                            st.session_state.current_codex_object = loaded_objects[0]
                                            st.session_state.loaded_objects_batch = loaded_objects
                                            st.success(f"✅ Loaded {len(loaded_objects)} objects. Working with: {loaded_objects[0].title}")
                                            logger.info(f"Loaded batch of {len(loaded_objects)} objects")

                                        if failed_files:
                                            st.warning(f"⚠️ Failed to load {len(failed_files)} file(s)")

                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to load any files. Check file format and permissions.")
                                        if failed_files:
                                            with st.expander("Failed files (click to see details)"):
                                                for file_path, reason in failed_files:
                                                    st.write(f"**{Path(file_path).name}**")
                                                    st.write(f"  └─ {reason}")
                        else:
                            st.info("Select one or more files to load")
                    else:
                        st.info("No JSON files found in this directory")

                except PermissionError:
                    st.error("Permission denied to access this directory")
                except Exception as e:
                    st.error(f"Error browsing directory: {e}")

            with create_tab:
                st.write("Create a new CodexObject from scratch")

                new_title = st.text_input("Title", key="new_obj_title")
                new_type = st.selectbox(
                    "Starting Type",
                    [CodexObjectType.IDEA, CodexObjectType.LOGLINE, CodexObjectType.SUMMARY],
                    format_func=lambda x: x.value,
                    key="new_obj_type"
                )
                new_content = st.text_area("Initial Content", height=200, key="new_obj_content")
                new_genre = st.text_input("Genre (optional)", key="new_obj_genre")
                new_audience = st.text_input("Target Audience (optional)", key="new_obj_audience")

                if st.button("Create Object", type="primary"):
                    if new_title and new_content:
                        new_obj = CodexObject(
                            title=new_title,
                            object_type=new_type,
                            content=new_content,
                            genre=new_genre,
                            target_audience=new_audience,
                            development_stage=DevelopmentStage.CONCEPT
                        )
                        file_path = self.development_editing_manager.save_codex_object(new_obj)
                        if file_path:
                            st.session_state.current_codex_object = new_obj
                            st.success(f"Created and loaded: {new_obj.title}")
                            st.rerun()
                    else:
                        st.warning("Please provide both title and content")

            with import_tab:
                st.write("Import a book outline and convert it to a CodexObject")

                # File uploader
                uploaded_outline = st.file_uploader(
                    "Upload Book Outline (JSON)",
                    type=['json'],
                    key="outline_uploader",
                    help="Upload a JSON file containing a book outline with chapters"
                )

                if uploaded_outline:
                    try:
                        outline_data = json.load(uploaded_outline)

                        # Display outline info
                        st.write("**Outline Preview:**")
                        book_title = outline_data.get('book_title', 'Untitled')
                        total_chapters = outline_data.get('total_chapters', 0)
                        target_wc = outline_data.get('target_word_count', 0)

                        st.write(f"- **Title:** {book_title}")
                        st.write(f"- **Chapters:** {total_chapters}")
                        st.write(f"- **Target Word Count:** {target_wc:,}")

                        # Show metadata if available
                        if 'outline_metadata' in outline_data:
                            metadata = outline_data['outline_metadata']
                            st.write(f"- **Theme:** {metadata.get('primary_theme', 'N/A')}")
                            st.write(f"- **Hook:** {metadata.get('contemporary_hook', 'N/A')}")

                        # Conversion options
                        st.divider()
                        st.write("**Conversion Options:**")

                        import_as_type = st.selectbox(
                            "Import as",
                            [CodexObjectType.OUTLINE, CodexObjectType.DETAILED_OUTLINE, CodexObjectType.SYNOPSIS],
                            format_func=lambda x: x.value,
                            key="import_as_type"
                        )

                        include_chapters = st.checkbox("Include full chapter details", value=True)

                        if st.button("Convert and Import", type="primary"):
                            with st.spinner("Converting outline to CodexObject..."):
                                # Build content from outline
                                content_parts = []

                                # Add title and metadata
                                content_parts.append(f"# {book_title}\n")

                                if 'outline_metadata' in outline_data:
                                    metadata = outline_data['outline_metadata']
                                    content_parts.append(f"**Protagonist:** {metadata.get('protagonist_name', 'N/A')}")
                                    content_parts.append(f"**Primary Theme:** {metadata.get('primary_theme', 'N/A')}")
                                    content_parts.append(f"**Secondary Theme:** {metadata.get('secondary_theme', 'N/A')}")
                                    content_parts.append(f"**Contemporary Hook:** {metadata.get('contemporary_hook', 'N/A')}\n")

                                content_parts.append(f"**Total Chapters:** {total_chapters}")
                                content_parts.append(f"**Target Word Count:** {target_wc:,}\n")

                                # Add chapters
                                if include_chapters and 'chapters' in outline_data:
                                    content_parts.append("## Chapters\n")
                                    for chapter in outline_data['chapters']:
                                        ch_num = chapter.get('chapter_number', '?')
                                        ch_title = chapter.get('chapter_title', 'Untitled')
                                        ch_wc = chapter.get('estimated_word_count', 0)

                                        content_parts.append(f"### Chapter {ch_num}: {ch_title}")
                                        content_parts.append(f"**Word Count:** {ch_wc}")

                                        if 'plot_summary' in chapter:
                                            content_parts.append(f"**Summary:** {chapter['plot_summary']}")

                                        if 'emotional_beats' in chapter:
                                            content_parts.append(f"**Emotional Beats:** {chapter['emotional_beats']}")

                                        if 'chapter_purpose' in chapter:
                                            content_parts.append(f"**Purpose:** {chapter['chapter_purpose']}")

                                        content_parts.append("")  # Blank line between chapters

                                # Create CodexObject
                                converted_content = "\n".join(content_parts)

                                # Extract genre and audience from metadata if available
                                genre = ""
                                audience = ""
                                if 'outline_metadata' in outline_data:
                                    metadata = outline_data['outline_metadata']
                                    audience = metadata.get('primary_theme', '') + " readers"

                                new_obj = CodexObject(
                                    title=book_title,
                                    object_type=import_as_type,
                                    content=converted_content,
                                    genre=genre,
                                    target_audience=audience,
                                    development_stage=DevelopmentStage.DEVELOPMENT
                                )

                                # Save the object
                                file_path = self.development_editing_manager.save_codex_object(new_obj)
                                if file_path:
                                    st.session_state.current_codex_object = new_obj
                                    st.success(f"✅ Converted and loaded: {new_obj.title}")
                                    st.info(f"Saved to: {file_path}")
                                    st.rerun()
                                else:
                                    st.error("Failed to save converted object")

                    except json.JSONDecodeError:
                        st.error("Invalid JSON file. Please upload a valid book outline.")
                    except Exception as e:
                        st.error(f"Error importing outline: {e}")
                        logger.error(f"Outline import error: {e}")
                else:
                    st.info("Upload a book outline JSON file to convert it to a CodexObject")

        with col_right:
            st.subheader("🎯 Quick Actions")

            if 'current_codex_object' in st.session_state and st.session_state.current_codex_object is not None:
                obj = st.session_state.current_codex_object

                st.write(f"**Current:** {obj.title}")
                st.write(f"**Type:** {obj.object_type.value}")
                st.write(f"**Stage:** {obj.development_stage.value}")
                st.write(f"**Words:** {obj.word_count}")

                st.divider()

                # Stage progression controls
                st.write("**Stage Progression:**")

                col_back, col_fwd = st.columns(2)

                with col_back:
                    if st.button("⬅️ Condense", help="Move to previous stage", use_container_width=True):
                        st.session_state.action = "condense"
                        st.rerun()

                with col_fwd:
                    if st.button("Expand ➡️", help="Move to next stage", use_container_width=True):
                        st.session_state.action = "expand"
                        st.rerun()

                st.divider()

                # Feedback controls
                st.write("**Synthetic Readers:**")

                if st.button("📊 Request Feedback", use_container_width=True):
                    st.session_state.action = "request_feedback"
                    st.rerun()

                if obj.reader_feedback:
                    st.write(f"✅ {len(obj.reader_feedback)} feedback received")

                    if st.button("🔄 Apply Revisions", use_container_width=True):
                        st.session_state.action = "apply_revisions"
                        st.rerun()

            else:
                st.info("No object loaded. Select or create one to start.")

        st.divider()

        # Main working area
        if 'current_codex_object' in st.session_state and st.session_state.current_codex_object is not None:
            obj = st.session_state.current_codex_object

            # Handle actions - show action UI if action is set
            if st.session_state.get('action'):
                action = st.session_state.action

                if action == "expand":
                    self._handle_expand_action(obj)
                    return  # Don't show tabs while in action mode
                elif action == "condense":
                    self._handle_condense_action(obj)
                    return
                elif action == "request_feedback":
                    self._handle_feedback_request(obj)
                    return
                elif action == "apply_revisions":
                    self._handle_apply_revisions(obj)
                    return

            # Display tabs for content and feedback
            content_tab, feedback_tab, history_tab = st.tabs(["📄 Content", "💬 Feedback", "📜 History"])

            with content_tab:
                st.subheader(f"{obj.title} - {obj.object_type.value}")

                # Display content
                st.text_area(
                    "Content",
                    value=obj.content,
                    height=400,
                    key="content_display",
                    disabled=True
                )

                # Show metadata
                with st.expander("Metadata"):
                    st.write(f"**UUID:** {obj.uuid}")
                    st.write(f"**Genre:** {obj.genre or 'Not specified'}")
                    st.write(f"**Target Audience:** {obj.target_audience or 'Not specified'}")
                    st.write(f"**Created:** {obj.created_timestamp}")
                    st.write(f"**Modified:** {obj.last_modified}")

            with feedback_tab:
                if obj.reader_feedback:
                    st.subheader(f"Reader Feedback ({len(obj.reader_feedback)})")

                    for i, feedback in enumerate(obj.reader_feedback):
                        with st.expander(f"Feedback {i+1} - {feedback.get('reader_persona', 'Unknown')}"):
                            st.write(f"**Overall Rating:** {feedback.get('overall_rating', 0):.1f}/10")
                            st.write(f"**Market Appeal:** {feedback.get('market_appeal_score', 0):.1f}/10")
                            st.write(f"**Genre Fit:** {feedback.get('genre_fit_score', 0):.1f}/10")
                            st.write(f"**Audience Alignment:** {feedback.get('audience_alignment_score', 0):.1f}/10")

                            st.write("**Detailed Feedback:**")
                            st.write(feedback.get('detailed_feedback', 'No feedback provided'))

                            if feedback.get('recommendations'):
                                st.write("**Recommendations:**")
                                for rec in feedback['recommendations']:
                                    st.write(f"- {rec}")

                            if feedback.get('concerns'):
                                st.write("**Concerns:**")
                                for concern in feedback['concerns']:
                                    st.write(f"- {concern}")
                else:
                    st.info("No feedback yet. Request feedback using the Quick Actions panel.")

            with history_tab:
                if obj.processing_history:
                    st.subheader("Processing History")

                    for event in reversed(obj.processing_history):
                        with st.expander(f"{event.get('action', 'Unknown')} - {event.get('timestamp', '')}"):
                            st.json(event)
                else:
                    st.info("No processing history available.")

    def _handle_expand_action(self, obj: CodexObject):
        """Handle expanding to next stage."""
        st.subheader("Expand to Next Stage")

        # Model selection
        model = st.selectbox(
            "Select Model",
            ["gemini/gemini-2.0-flash-exp", "gemini/gemini-2.5-flash", "anthropic/claude-3-5-sonnet-20241022"],
            key="expand_model"
        )

        # Option to incorporate feedback
        incorporate_feedback = False
        if obj.reader_feedback:
            incorporate_feedback = st.checkbox(
                "Incorporate reader feedback",
                help="Use synthetic reader feedback to guide expansion"
            )

        if st.button("Confirm Expansion", type="primary"):
            with st.spinner(f"Expanding to next stage using {model}..."):
                new_obj = self.development_editing_manager.progress_forward(
                    obj,
                    model=model,
                    incorporate_feedback=incorporate_feedback
                )

                if new_obj:
                    st.session_state.current_codex_object = new_obj
                    st.success(f"Successfully expanded to {new_obj.object_type.value}!")
                    st.rerun()
                else:
                    st.error("Failed to expand. Please try again.")

    def _handle_condense_action(self, obj: CodexObject):
        """Handle condensing to previous stage."""
        st.subheader("Condense to Previous Stage")

        # Model selection
        model = st.selectbox(
            "Select Model",
            ["gemini/gemini-2.0-flash-exp", "gemini/gemini-2.5-flash", "anthropic/claude-3-5-sonnet-20241022"],
            key="condense_model"
        )

        if st.button("Confirm Condensation", type="primary"):
            with st.spinner(f"Condensing to previous stage using {model}..."):
                new_obj = self.development_editing_manager.progress_backward(
                    obj,
                    model=model
                )

                if new_obj:
                    st.session_state.current_codex_object = new_obj
                    st.success(f"Successfully condensed to {new_obj.object_type.value}!")
                    st.rerun()
                else:
                    st.error("Failed to condense. Please try again.")

    def _handle_feedback_request(self, obj: CodexObject):
        """Handle requesting synthetic reader feedback."""
        st.subheader("📊 Request Synthetic Reader Feedback")

        # Cancel button
        if st.button("⬅️ Cancel", key="cancel_feedback"):
            st.session_state.action = None
            st.rerun()

        st.divider()

        # Check if synthetic reader panel is available
        if not self.synthetic_reader_panel:
            st.error("Synthetic Reader Panel not available. Check LLM connection.")
            return

        # Select personas
        try:
            available_personas = [p.name for p in self.synthetic_reader_panel.reader_personas]
        except Exception as e:
            st.error(f"Error loading reader personas: {e}")
            logger.error(f"Reader persona error: {e}")
            return

        if not available_personas:
            st.warning("No reader personas available.")
            return

        selected_personas = st.multiselect(
            "Select Reader Personas",
            available_personas,
            default=available_personas[:min(3, len(available_personas))],
            key="feedback_personas",
            help="Choose which synthetic readers should evaluate your content"
        )

        st.divider()

        # Model selection using standard widget
        selected_model = self.model_config.render_model_selector(
            component_name="synthetic_reader_feedback",
            key="feedback_model_selector"
        )

        # Select feedback types (future enhancement)
        st.write("**Feedback Types:**")
        st.info("All feedback types will be requested (market appeal, genre fit, audience alignment)")

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("📊 Request Feedback", type="primary", use_container_width=True):
                if selected_personas:
                    with st.spinner(f"Collecting feedback from {len(selected_personas)} readers..."):
                        try:
                            # Log what we're sending
                            logger.info(f"Requesting feedback for: {obj.title}")
                            logger.info(f"Selected personas: {selected_personas}")
                            logger.info(f"Selected model: {selected_model}")
                            logger.info(f"Object type: {obj.object_type.value}")
                            logger.info(f"Content length: {len(obj.content)} chars")

                            feedback_list = self.development_editing_manager.request_synthetic_feedback(
                                obj,
                                selected_personas=selected_personas,
                                model=selected_model
                            )

                            logger.info(f"Received feedback list: {len(feedback_list) if feedback_list else 0} items")

                            if feedback_list and len(feedback_list) > 0:
                                # Save the updated object
                                file_path = self.development_editing_manager.save_codex_object(obj)
                                logger.info(f"Saved updated object to: {file_path}")

                                # Reload to ensure we have latest
                                updated_obj = self.development_editing_manager.load_codex_object(file_path)
                                st.session_state.current_codex_object = updated_obj

                                st.success(f"✅ Received {len(feedback_list)} feedback responses!")

                                # Display summary
                                avg_rating = sum(f.overall_rating for f in feedback_list) / len(feedback_list)
                                st.metric("Average Rating", f"{avg_rating:.1f}/10")

                                # Clear action and reload
                                st.session_state.action = None
                                st.rerun()
                            else:
                                st.error("❌ Failed to collect feedback. Check logs for details.")
                                st.info("Possible issues: LLM connection, API keys, or reader persona configuration")
                                # Show object info for debugging
                                with st.expander("Debug Info"):
                                    st.write(f"Object UUID: {obj.uuid}")
                                    st.write(f"Object Type: {obj.object_type.value}")
                                    st.write(f"Content Length: {len(obj.content)}")
                                    st.write(f"Has Logline: {bool(obj.logline)}")
                                    st.write(f"Has Description: {bool(obj.description)}")
                        except Exception as e:
                            st.error(f"❌ Error requesting feedback: {e}")
                            logger.error(f"Feedback request exception: {e}", exc_info=True)
                            with st.expander("Error Details"):
                                st.code(str(e))
                else:
                    st.warning("Please select at least one reader persona.")

    def _handle_apply_revisions(self, obj: CodexObject):
        """Handle applying feedback-driven revisions."""
        st.subheader("Apply Feedback Revisions")

        if not obj.reader_feedback:
            st.warning("No feedback available to apply.")
            return

        # Synthesize feedback first
        with st.spinner("Analyzing feedback..."):
            # Convert to ReaderFeedback objects
            from codexes.modules.ideation.synthetic_reader import ReaderFeedback

            feedback_objects = []
            for fb_dict in obj.reader_feedback:
                try:
                    feedback_obj = ReaderFeedback.from_dict(fb_dict)
                    feedback_objects.append(feedback_obj)
                except Exception as e:
                    logger.warning(f"Error converting feedback: {e}")
                    continue

            if feedback_objects:
                insights_dict = self.development_editing_manager.evaluate_feedback(feedback_objects)
                insights = insights_dict.get(obj.uuid) if insights_dict else None

                if insights:
                    st.write("**Synthesized Insights:**")
                    st.write(f"**Consensus:** {insights.overall_consensus}")
                    st.write(f"**Market Potential:** {insights.market_potential:.1f}/10")

                    st.write("**Top Improvements:**")
                    for imp in insights.recommended_improvements[:5]:
                        st.write(f"- {imp}")

                    # Model selection
                    model = st.selectbox(
                        "Select Model for Revisions",
                        ["gemini/gemini-2.0-flash-exp", "gemini/gemini-2.5-flash", "anthropic/claude-3-5-sonnet-20241022"],
                        key="revise_model"
                    )

                    if st.button("Apply Revisions", type="primary"):
                        with st.spinner("Applying feedback revisions..."):
                            revised_obj = self.development_editing_manager.apply_feedback_revisions(
                                obj,
                                insights,
                                model=model
                            )

                            if revised_obj:
                                st.session_state.current_codex_object = revised_obj
                                st.success("Successfully applied revisions!")
                                st.rerun()
                            else:
                                st.error("Failed to apply revisions. Please try again.")
                else:
                    st.error("Failed to synthesize feedback insights.")
            else:
                st.error("No valid feedback to process.")

    def _render_reader_panels_tab(self):
        """Render the High-Volume Reader Panels interface."""
        st.subheader("👥 High-Volume Reader Panels")
        st.markdown("""
        Get statistically significant feedback from diverse reader panels including children, young adults,
        parents, reading experts, and purchasing decision makers. Perfect for market testing book concepts and outlines.
        """)

        if not self.reader_panels_system:
            st.error("Reader Panels System not available. Please check LLM connection.")
            return

        # Main layout
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.subheader("📄 Select Draft Files")

            # File selection options
            file_source = st.radio(
                "File Source",
                ["Upload Files", "Browse Directory", "Use Current Object"],
                horizontal=True,
                key="panels_file_source"
            )

            selected_files = []

            if file_source == "Upload Files":
                uploaded_files = st.file_uploader(
                    "Upload Draft Files",
                    type=['json', 'md', 'txt'],
                    accept_multiple_files=True,
                    key="panels_file_uploader",
                    help="Upload book outlines, chapter drafts, or concept documents"
                )

                if uploaded_files:
                    # Save uploaded files temporarily
                    import tempfile
                    temp_dir = Path(tempfile.mkdtemp())
                    for uploaded_file in uploaded_files:
                        temp_file = temp_dir / uploaded_file.name
                        with open(temp_file, 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                        selected_files.append(temp_file)

                    st.success(f"✅ {len(selected_files)} file(s) uploaded")

            elif file_source == "Browse Directory":
                # Initialize session state for directory browser
                if 'panels_browse_dir' not in st.session_state:
                    default_dir = Path(__file__).parent.parent.parent.parent / 'data' / 'ideation' / 'development'
                    st.session_state.panels_browse_dir = str(default_dir) if default_dir.exists() else str(Path.home())

                st.write(f"**Current Directory:** `{st.session_state.panels_browse_dir}`")
                current_path = Path(st.session_state.panels_browse_dir)

                # Navigation buttons
                col_nav1, col_nav2 = st.columns(2)
                with col_nav1:
                    if st.button("⬆️ Parent", key="panels_parent_dir"):
                        parent = current_path.parent
                        if parent != current_path:
                            st.session_state.panels_browse_dir = str(parent)
                            st.rerun()

                with col_nav2:
                    if st.button("🏠 Reset", key="panels_reset_dir"):
                        default_dir = Path(__file__).parent.parent.parent.parent / 'data' / 'ideation' / 'development'
                        st.session_state.panels_browse_dir = str(default_dir) if default_dir.exists() else str(Path.home())
                        st.rerun()

                try:
                    # List subdirectories
                    subdirs = [d for d in current_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
                    subdirs.sort()

                    if subdirs:
                        st.write("**Subdirectories:**")
                        cols = st.columns(min(3, len(subdirs)))
                        for idx, subdir in enumerate(subdirs):
                            with cols[idx % 3]:
                                if st.button(f"📁 {subdir.name}", key=f"panels_subdir_{idx}"):
                                    st.session_state.panels_browse_dir = str(subdir)
                                    st.rerun()

                    st.divider()

                    # List files
                    files = [f for f in current_path.iterdir()
                            if f.is_file() and f.suffix in ['.json', '.md', '.txt']]
                    files.sort()

                    if files:
                        st.write(f"**Files:** ({len(files)} files)")

                        # Multi-select
                        if 'panels_selected_files' not in st.session_state:
                            st.session_state.panels_selected_files = []

                        # Select all / Deselect all
                        col_sel1, col_sel2 = st.columns(2)
                        with col_sel1:
                            if st.button("✅ Select All", key="panels_select_all"):
                                st.session_state.panels_selected_files = [str(f) for f in files]
                                st.rerun()
                        with col_sel2:
                            if st.button("⬜ Deselect All", key="panels_deselect_all"):
                                st.session_state.panels_selected_files = []
                                st.rerun()

                        # Display files with checkboxes
                        file_selection = {}
                        for file in files:
                            file_path_str = str(file)
                            is_selected = file_path_str in st.session_state.panels_selected_files

                            selected = st.checkbox(
                                file.name,
                                value=is_selected,
                                key=f"panels_file_checkbox_{file.name}"
                            )
                            file_selection[file_path_str] = selected

                        # Update session state
                        st.session_state.panels_selected_files = [
                            path for path, selected in file_selection.items() if selected
                        ]

                        selected_files = [Path(p) for p in st.session_state.panels_selected_files]

                        if selected_files:
                            st.success(f"✅ {len(selected_files)} file(s) selected")

                    else:
                        st.info("No compatible files found in this directory")

                except PermissionError:
                    st.error("Permission denied to access this directory")
                except Exception as e:
                    st.error(f"Error browsing directory: {e}")

            elif file_source == "Use Current Object":
                if 'current_codex_object' in st.session_state and st.session_state.current_codex_object:
                    obj = st.session_state.current_codex_object
                    st.write(f"**Using:** {obj.title}")
                    st.write(f"**Type:** {obj.object_type.value}")
                    st.write(f"**Words:** {obj.word_count}")

                    # Save current object to temp file for processing
                    temp_dir = Path(tempfile.mkdtemp())
                    temp_file = temp_dir / f"{obj.uuid}.json"

                    # Export to JSON format that reader panels can parse
                    export_data = {
                        'book_title': obj.title,
                        'content': obj.content,
                        'genre': obj.genre or '',
                        'target_audience': obj.target_audience or '',
                        'object_type': obj.object_type.value,
                        'word_count': obj.word_count
                    }

                    with open(temp_file, 'w') as f:
                        json.dump(export_data, f, indent=2)

                    selected_files = [temp_file]
                    st.success("✅ Current object ready for evaluation")
                else:
                    st.info("No object currently loaded. Use 'Development Editor' tab to load an object.")

        with col_right:
            st.subheader("⚙️ Panel Configuration")

            # Available panels
            available_panels = {
                'children_9_10': '👧 Children (9-10) - 100 evals',
                'young_adult': '🧑 Young Adult (12-17) - 80 evals',
                'parents': '👨‍👩‍👧 Parents - 80 evals',
                'reading_experts': '📚 Reading Experts - 50 evals',
                'purchasing': '💼 Purchasing - 40 evals'
            }

            st.write("**Select Panels:**")
            selected_panels = []
            for panel_id, panel_label in available_panels.items():
                if st.checkbox(panel_label, value=True, key=f"panel_checkbox_{panel_id}"):
                    selected_panels.append(panel_id)

            if selected_panels:
                total_evals = sum({
                    'children_9_10': 100,
                    'young_adult': 80,
                    'parents': 80,
                    'reading_experts': 50,
                    'purchasing': 40
                }.get(p, 0) for p in selected_panels)

                st.metric("Total Evaluations", total_evals)
                st.metric("Est. Time", f"{total_evals * 0.5:.0f}-{total_evals * 1:.0f} min")

            st.divider()

            # Model selection
            selected_model = self.model_config.render_model_selector(
                component_name="reader_panels",
                key="panels_model_selector"
            )

            # Advanced settings
            with st.expander("Advanced Settings"):
                max_workers = st.slider(
                    "Parallel Workers",
                    min_value=1,
                    max_value=20,
                    value=10,
                    help="Number of parallel evaluation threads"
                )

                temperature = st.slider(
                    "Temperature",
                    min_value=0.1,
                    max_value=1.0,
                    value=0.7,
                    step=0.1,
                    help="LLM temperature for evaluation responses"
                )

        st.divider()

        # Execution controls
        col_exec1, col_exec2, col_exec3 = st.columns([2, 1, 1])

        with col_exec1:
            can_execute = len(selected_files) > 0 and len(selected_panels) > 0

            if st.button(
                "🚀 Run Reader Panel Evaluations",
                type="primary",
                disabled=not can_execute,
                use_container_width=True
            ):
                st.session_state.panels_running = True
                st.session_state.panels_files = selected_files
                st.session_state.panels_selected = selected_panels
                st.session_state.panels_model = selected_model
                st.session_state.panels_config = EvaluationConfig(
                    model=selected_model,
                    temperature=temperature,
                    max_workers=max_workers
                )
                st.rerun()

        # Show execution status
        if st.session_state.get('panels_running'):
            st.divider()
            st.subheader("🔄 Evaluation in Progress")

            with st.spinner("Running reader panel evaluations..."):
                try:
                    # Get files and config from session state
                    files_to_eval = st.session_state.panels_files
                    panels_to_use = st.session_state.panels_selected
                    config = st.session_state.panels_config

                    # Update reader panels config
                    self.reader_panels_system.config = config

                    # Create progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    completed_evals = 0
                    total_evals = sum({
                        'children_9_10': 100,
                        'young_adult': 80,
                        'parents': 80,
                        'reading_experts': 50,
                        'purchasing': 40
                    }.get(p, 0) for p in panels_to_use)

                    def progress_callback(current, total, panel_name):
                        nonlocal completed_evals
                        completed_evals += 1
                        progress = completed_evals / total_evals
                        progress_bar.progress(min(progress, 1.0))
                        status_text.text(f"Evaluating with {panel_name}: {current}/{total} complete ({completed_evals}/{total_evals} total)")

                    # Run evaluations
                    results = self.reader_panels_system.evaluate_drafts(
                        draft_paths=files_to_eval,
                        panel_names=panels_to_use,
                        progress_callback=progress_callback
                    )

                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()

                    # Store results
                    st.session_state.panels_results = results
                    st.session_state.panels_running = False

                    st.success(f"✅ Completed {total_evals} evaluations across {len(panels_to_use)} panels!")

                    # Display summary
                    st.subheader("📊 Results Summary")

                    for draft_slug, panel_results in results.items():
                        with st.expander(f"Results for: {draft_slug}", expanded=True):
                            for panel_name, feedback_list in panel_results.items():
                                if feedback_list:
                                    avg_rating = sum(f.overall_rating for f in feedback_list) / len(feedback_list)
                                    avg_market = sum(f.market_appeal_score for f in feedback_list) / len(feedback_list)
                                    avg_genre = sum(f.genre_fit_score for f in feedback_list) / len(feedback_list)
                                    avg_audience = sum(f.audience_alignment_score for f in feedback_list) / len(feedback_list)

                                    st.write(f"**{panel_name}** ({len(feedback_list)} evaluations)")
                                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                                    col_m1.metric("Overall", f"{avg_rating:.1f}/10")
                                    col_m2.metric("Market", f"{avg_market:.1f}/10")
                                    col_m3.metric("Genre", f"{avg_genre:.1f}/10")
                                    col_m4.metric("Audience", f"{avg_audience:.1f}/10")

                    # Offer downloads
                    output_dir = self.reader_panels_system.output_dir / draft_slug
                    if output_dir.exists():
                        st.download_button(
                            "📥 Download Full Report",
                            data=(output_dir / "COMPLETE_PANEL_SUMMARY.md").read_text() if (output_dir / "COMPLETE_PANEL_SUMMARY.md").exists() else "Report not generated",
                            file_name=f"{draft_slug}_reader_panel_report.md",
                            mime="text/markdown"
                        )

                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error running evaluations: {e}")
                    logger.error(f"Reader panels error: {e}", exc_info=True)
                    st.session_state.panels_running = False

        # Display previous results if available
        if st.session_state.get('panels_results') and not st.session_state.get('panels_running'):
            st.divider()
            st.subheader("📈 Previous Results")

            results = st.session_state.panels_results

            for draft_slug, panel_results in results.items():
                with st.expander(f"Results for: {draft_slug}", expanded=False):
                    for panel_name, feedback_list in panel_results.items():
                        if feedback_list:
                            st.write(f"**{panel_name}** - {len(feedback_list)} evaluations")

                            # Show sample feedback
                            if st.checkbox(f"Show sample feedback - {panel_name}", key=f"show_sample_{draft_slug}_{panel_name}"):
                                sample = feedback_list[:3]  # Show first 3
                                for i, fb in enumerate(sample):
                                    with st.expander(f"Sample {i+1} - {fb.reader_persona}"):
                                        st.write(f"**Rating:** {fb.overall_rating:.1f}/10")
                                        st.write(fb.detailed_feedback)

    def render_analytics_tab(self):
        """Render analytics and insights."""
        st.header("Analytics & Insights")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_ideas = self._get_total_ideas_count()
            st.metric("Total Ideas Generated", total_ideas)
        
        with col2:
            tournaments_run = self._get_tournaments_count()
            st.metric("Tournaments Run", tournaments_run)
        
        with col3:
            feedback_sessions = self._get_feedback_sessions_count()
            st.metric("Feedback Sessions", feedback_sessions)
        
        with col4:
            promoted_ideas = self._get_promoted_ideas_count()
            st.metric("Ideas Promoted", promoted_ideas)
        
        # Charts
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("Ideas Generated Over Time")
            self._display_generation_chart()
        
        with col_chart2:
            st.subheader("Tournament Performance")
            self._display_tournament_chart()
        
        # Insights
        st.subheader("AI Insights")
        self._display_ai_insights()

    def render_settings_tab(self):
        """Render system settings."""
        st.header("System Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Generation Settings")
            
            # Default model settings
            st.selectbox("Default Model", ["ollama/mistral:latest", "openai/gpt-oss:20b", "deepseek/deepseek-r1:latest"], key="default_model")
            st.slider("Default Temperature", 0.1, 1.0, 0.7, 0.1, key="default_temp")
            st.number_input("Default Batch Size", 1, 50, 5, key="default_batch")
            st.number_input("Batch Interval (seconds)", 60, 3600, 300, key="batch_interval")
            
            if st.button("Save Generation Settings"):
                st.success("Settings saved!")
        
        with col2:
            st.subheader("System Status")
            
            # System health checks
            st.write("**LLM Connection:**", "✅ Connected" if self._check_llm_connection() else "❌ Disconnected")
            st.write("**Storage:**", "✅ Available" if self._check_storage() else "❌ Issues")
            st.write("**Tournaments:**", f"{len(self.tournament_manager.active_tournaments)} active")
            
            # Maintenance actions
            if st.button("Clear Cache"):
                st.success("Cache cleared!")
            
            if st.button("Export Data"):
                self._export_system_data()

    def _generate_ideas(self, num_ideas: int, model: str, temperature: float,
                       imprint: str, custom_prompt: str):
        """Generate new ideas."""
        try:
            # Create progress bar and status text
            progress_bar = st.progress(0)
            status_text = st.empty()

            generator = ContinuousIdeaGenerator(
                llm_caller=self.llm_caller,
                ideas_per_batch=num_ideas,
                model=model,
                temperature=temperature,
                custom_prompt=custom_prompt if custom_prompt else None
            )

            # Progress callback function
            def update_progress(current, total):
                progress = current / total
                progress_bar.progress(progress)
                status_text.text(f"Generating ideas... {current}/{total} ({progress*100:.0f}%)")

            # Generate with progress updates
            results = generator.generate_single_batch(progress_callback=update_progress)

            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()

            if results:
                st.success(f"Generated {len(results)} ideas successfully!")

                # Display generated ideas
                for idea_id, idea in results.items():
                    with st.expander(f"💡 {idea.title}"):
                        st.write(f"**Logline:** {idea.logline}")
                        if idea.description:
                            st.write(f"**Description:** {idea.description}")
                        if idea.genre:
                            st.write(f"**Genre:** {idea.genre}")
            else:
                st.error("Failed to generate ideas. Please try again.")
                    
        except Exception as e:
            st.error(f"Error generating ideas: {str(e)}")
            logger.error(f"Idea generation error: {e}")

    def _start_continuous_generation(self, imprint: str, model: str, temperature: float):
        """Start continuous generation for an imprint."""
        try:
            config = {
                'model': model,
                'temperature': temperature,
                'ideas_per_batch': 5,
                'batch_interval': 300
            }
            
            self.integrated_generator.start_continuous_generation(imprint, config)
            st.success(f"Started continuous generation for {imprint}")
            
        except Exception as e:
            st.error(f"Error starting continuous generation: {str(e)}")

    def _stop_continuous_generation(self, imprint: str):
        """Stop continuous generation for an imprint."""
        try:
            self.integrated_generator.stop_continuous_generation(imprint)
            st.success(f"Stopped continuous generation for {imprint}")
            
        except Exception as e:
            st.error(f"Error stopping continuous generation: {str(e)}")

    def _display_generation_status(self):
        """Display current generation status."""
        # Get status for all imprints
        imprints = self._get_available_imprints()
        
        for imprint in imprints:
            status = self.integrated_generator.get_generator_status(imprint)
            
            if status['status'] == 'running':
                st.success(f"**{imprint}**: Running")
                st.write(f"Generated: {status.get('generation_count', 0)} batches")
                st.write(f"Success rate: {status.get('successful_generations', 0)}/{status.get('successful_generations', 0) + status.get('failed_generations', 0)}")
            elif status['status'] == 'stopped':
                st.warning(f"**{imprint}**: Stopped")
            else:
                st.info(f"**{imprint}**: Not running")

    def _display_recent_ideas(self):
        """Display recently generated ideas."""
        try:
            # Load recent ideas from cumulative file
            cumulative_path = Path("output/resources/cumulative.csv")
            
            if cumulative_path.exists():
                df = pd.read_csv(cumulative_path)
                
                if not df.empty:
                    # Show last 10 ideas
                    recent_df = df.tail(10)
                    
                    for _, row in recent_df.iterrows():
                        with st.expander(f"💡 {row['title']}"):
                            st.write(f"**Logline:** {row['logline']}")
                            st.write(f"**Model:** {row.get('model', 'Unknown')}")
                            st.write(f"**Generated:** {row.get('timestamp', 'Unknown')}")
                else:
                    st.info("No ideas generated yet.")
            else:
                st.info("No ideas generated yet.")
                
        except Exception as e:
            st.error(f"Error loading recent ideas: {str(e)}")

    def _load_available_ideas(self) -> List[BookIdea]:
        """Load available ideas for tournaments and evaluation."""
        ideas = []

        try:
            # Load from cumulative CSV
            cumulative_path = Path("output/resources/cumulative.csv")

            if cumulative_path.exists():
                df = pd.read_csv(cumulative_path)

                for _, row in df.iterrows():
                    idea = BookIdea(
                        title=row['title'],
                        logline=row['logline'],
                        generation_metadata={
                            'idea_id': row.get('idea_id', ''),
                            'model': row.get('model', 'unknown'),
                            'temperature': row.get('temperature', 0.7)
                        }
                    )
                    ideas.append(idea)

        except Exception as e:
            logger.error(f"Error loading ideas: {e}")

        return ideas

    def _create_tournament(self, available_ideas: List[BookIdea], tournament_size: int,
                          model: str, temperature: float):
        """Create and run a tournament."""
        try:
            # Select random ideas for tournament
            import random
            selected_ideas = random.sample(available_ideas, min(tournament_size, len(available_ideas)))
            
            with st.spinner("Creating tournament..."):
                # Create tournament
                tournament_config = {'model': model, 'temperature': temperature}
                tournament = self.tournament_manager.create_tournament(selected_ideas, tournament_config)
                
                # Run tournament
                results = self.tournament_manager.run_tournament(tournament)
                
                st.success("Tournament completed!")
                
                # Display results
                winner = results.get('winner')
                if winner:
                    st.write(f"🏆 **Winner:** {winner.title}")
                    st.write(f"**Logline:** {winner.logline}")
                
                finalists = results.get('finalists', [])
                if finalists:
                    st.write("🥈 **Finalists:**")
                    for finalist in finalists:
                        st.write(f"- {finalist.title}")
                
                # Option to promote winner
                if st.button("Promote Winner to Pipeline"):
                    self._promote_tournament_winner(results)
                    
        except Exception as e:
            st.error(f"Error creating tournament: {str(e)}")

    def _promote_tournament_winner(self, tournament_results: Dict):
        """Promote tournament winner to production pipeline."""
        try:
            imprint = st.selectbox("Select target imprint", self._get_available_imprints())
            
            if st.button("Confirm Promotion"):
                promoted = self.pipeline_bridge.promote_tournament_winners(
                    tournament_results, imprint, auto_promote=True
                )
                
                if promoted:
                    st.success(f"Promoted {len(promoted)} ideas to {imprint} pipeline!")
                else:
                    st.warning("No ideas were promoted.")
                    
        except Exception as e:
            st.error(f"Error promoting winner: {str(e)}")

    def _display_active_tournaments(self):
        """Display currently active tournaments."""
        active = self.tournament_manager.get_active_tournaments()
        
        if active:
            for tournament_id, tournament in active.items():
                st.write(f"**{tournament_id}**: {tournament.total_ideas} participants")
        else:
            st.info("No active tournaments")

    def _display_tournament_history(self):
        """Display tournament history."""
        history = self.tournament_manager.get_tournament_history()
        
        if history:
            for result in history[-5:]:  # Show last 5
                with st.expander(f"Tournament {result['tournament_id']}"):
                    st.write(f"**Winner:** {result['winner'].title if result['winner'] else 'None'}")
                    st.write(f"**Participants:** {result['total_participants']}")
                    st.write(f"**Completed:** {result['completed_at']}")
        else:
            st.info("No tournament history available")

    def _evaluate_ideas_with_readers(self, ideas: List[BookIdea], personas: List[str]):
        """Evaluate ideas with synthetic readers."""
        try:
            with st.spinner("Evaluating ideas with synthetic readers..."):
                feedback = self.synthetic_reader_panel.evaluate_ideas(ideas, personas)
                
                if feedback:
                    st.success(f"Collected {len(feedback)} feedback responses!")
                    
                    # Synthesize insights
                    insights = self.synthetic_reader_panel.synthesize_feedback(feedback)
                    
                    # Display results
                    for idea_id, insight in insights.items():
                        idea_title = next((idea.title for idea in ideas 
                                         if idea.generation_metadata.get('idea_id') == idea_id), 
                                        f"Idea {idea_id}")
                        
                        with st.expander(f"📊 {idea_title} - Rating: {insight.market_potential:.1f}/10"):
                            st.write(f"**Consensus:** {insight.overall_consensus}")
                            st.write(f"**Market Potential:** {insight.market_potential:.1f}/10")
                            
                            if insight.recommended_improvements:
                                st.write("**Improvements:**")
                                for improvement in insight.recommended_improvements[:3]:
                                    st.write(f"- {improvement}")
                            
                            if insight.imprint_suggestions:
                                st.write("**Imprint Suggestions:**")
                                for suggestion in insight.imprint_suggestions:
                                    st.write(f"- {suggestion}")
                else:
                    st.warning("No feedback collected.")
                    
        except Exception as e:
            st.error(f"Error evaluating ideas: {str(e)}")

    def _display_reader_personas(self):
        """Display available reader personas."""
        for persona in self.synthetic_reader_panel.reader_personas:
            with st.expander(f"👤 {persona.name}"):
                st.write(f"**Age:** {persona.age_range}")
                st.write(f"**Genres:** {', '.join(persona.preferred_genres)}")
                st.write(f"**Traits:** {', '.join(persona.personality_traits)}")

    def _display_recent_feedback(self):
        """Display recent reader feedback."""
        # This would load from saved feedback files
        st.info("Recent feedback display not yet implemented")

    def _get_available_imprints(self) -> List[str]:
        """Get list of available imprints."""
        try:
            imprints_dir = Path("configs/imprints")
            if imprints_dir.exists():
                return [f.stem for f in imprints_dir.glob("*.json")]
            else:
                return ["xynapse_traces", "default"]
        except:
            return ["xynapse_traces", "default"]

    def _get_total_ideas_count(self) -> int:
        """Get total number of ideas generated."""
        try:
            cumulative_path = Path("output/resources/cumulative.csv")
            if cumulative_path.exists():
                df = pd.read_csv(cumulative_path)
                return len(df)
        except:
            pass
        return 0

    def _get_tournaments_count(self) -> int:
        """Get total number of tournaments run."""
        return len(self.tournament_manager.get_tournament_history())

    def _get_feedback_sessions_count(self) -> int:
        """Get number of feedback sessions."""
        # This would count feedback files
        return 0

    def _get_promoted_ideas_count(self) -> int:
        """Get number of ideas promoted to pipeline."""
        # This would count promoted ideas
        return 0

    def _display_generation_chart(self):
        """Display ideas generation over time chart."""
        try:
            cumulative_path = Path("output/resources/cumulative.csv")
            if cumulative_path.exists():
                df = pd.read_csv(cumulative_path)
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    daily_counts = df.groupby(df['timestamp'].dt.date).size()
                    
                    fig = px.line(x=daily_counts.index, y=daily_counts.values,
                                title="Ideas Generated Per Day")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No timestamp data available")
            else:
                st.info("No generation data available")
        except Exception as e:
            st.error(f"Error displaying chart: {str(e)}")

    def _display_tournament_chart(self):
        """Display tournament performance chart."""
        history = self.tournament_manager.get_tournament_history()
        if history:
            participants = [result['total_participants'] for result in history]
            dates = [result['completed_at'][:10] for result in history]  # Extract date
            
            fig = px.bar(x=dates, y=participants, title="Tournament Participants Over Time")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No tournament data available")

    def _display_ai_insights(self):
        """Display AI-generated insights about the ideation system."""
        st.info("AI insights feature coming soon...")

    def _check_llm_connection(self) -> bool:
        """Check if LLM connection is working."""
        try:
            response = self.llm_caller.call_llm("Test", model="mistral", temperature=0.1)
            return bool(response)
        except:
            return False

    def _check_storage(self) -> bool:
        """Check if storage is available."""
        try:
            Path("output").mkdir(exist_ok=True)
            return True
        except:
            return False

    def _export_system_data(self):
        """Export system data."""
        st.info("Data export feature coming soon...")

# Initialize and render dashboard
if __name__ == "__main__":
    dashboard = IdeationDashboard()
    dashboard.render_dashboard()