"""
Universal Content Input Component

Provides a universal input interface that accepts any creative content
and creates CodexObjects with intelligent content type detection.
"""

from typing import List, Optional, Dict, Any, Tuple
import streamlit as st
from datetime import datetime
from pathlib import Path

from ..core.simple_codex_object import SimpleCodexObject as CodexObject, CodexObjectType
from .content_detector import ContentTypeDetector
from .file_handler import FileHandler
from .adaptive_form import FormAdapter
from .object_datatable import ObjectDataTable
from ..config.model_config import ModelConfigManager


class UniversalContentInput:
    """Universal content input component that accepts any content type."""
    
    def __init__(self):
        self.session_key = "universal_input_state"
        self.content_detector = ContentTypeDetector()
        self.model_config = ModelConfigManager()
        self.file_handler = FileHandler()
        self.form_adapter = FormAdapter()
        self.data_table = ObjectDataTable()
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state for the component."""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                'created_objects': [],
                'last_content': '',
                'object_counter': 0
            }
    
    def _show_imprint_guidance_if_selected(self):
        """Show imprint guidance if an imprint is selected in session state."""
        selected_imprint = st.session_state.get('selected_imprint')
        if selected_imprint:
            st.info(f"🏢 **Imprint Context:** {selected_imprint}")
            
            # Try to import and use the imprint bridge for guidance
            try:
                from .imprint_ideation_bridge import ImprintIdeationBridge
                bridge = ImprintIdeationBridge()
                
                if selected_imprint in bridge.available_imprints:
                    imprint_context = bridge.available_imprints[selected_imprint]
                    
                    # Show quick guidance
                    with st.expander("📋 Imprint Guidelines", expanded=False):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if "preferred_genres" in imprint_context.constraints:
                                genres = imprint_context.constraints["preferred_genres"][:3]
                                st.write(f"**Preferred Genres:** {', '.join(genres)}")
                            
                            if "target_audience" in imprint_context.constraints:
                                st.write(f"**Target Audience:** {imprint_context.constraints['target_audience']}")
                        
                        with col2:
                            if "brand_tagline" in imprint_context.guidance:
                                st.write(f"**Brand Focus:** {imprint_context.guidance['brand_tagline']}")
                            
                            if "specialization" in imprint_context.guidance:
                                st.write(f"**Specialization:** {imprint_context.guidance['specialization']}")
            except ImportError:
                # Imprint bridge not available, show basic info
                st.write(f"Content will be created with {selected_imprint} context")
    
    def render_intelligent_input_interface(self) -> Optional[CodexObject]:
        """Render the intelligent input interface with multiple input methods."""
        st.subheader("📝 Universal Content Input")
        
        # Input method selection
        input_method = st.radio(
            "Choose input method:",
            options=["Text Input", "File Upload", "Directory Browse"],
            horizontal=True,
            help="Select how you want to provide content"
        )
        
        content_items = []
        
        if input_method == "Text Input":
            content_items = self._render_text_input()
        elif input_method == "File Upload":
            content_items = self._render_file_upload()
        elif input_method == "Directory Browse":
            content_items = self._render_directory_browse()
        
        if content_items:
            return self._process_content_items(content_items)
        
        return None
    
    def _render_text_input(self) -> List[Tuple[str, str]]:
        """Render text input interface."""
        st.write("Enter any creative content - the system will automatically detect the type!")
        
        # Show imprint guidance if an imprint is selected
        self._show_imprint_guidance_if_selected()
        
        # Main content input
        content = st.text_area(
            "Content", 
            placeholder="Enter any creative content here...\n\nExamples:\n- A story about time travel\n- Chapter 1: The Discovery...\n- Plot outline with three acts\n- Character development notes",
            height=200,
            help="The system will automatically analyze your content and suggest the most appropriate type."
        )
        
        if content and content.strip():
            return [("Pasted Content", content)]
        return []
    
    def _render_file_upload(self) -> List[Tuple[str, str]]:
        """Render file upload interface supporting multiple formats."""
        supported_extensions = [ext[1:] for ext in self.file_handler.supported_formats]  # Remove dots
        supported_extensions.append('zip')  # Always support ZIP
        
        st.write(f"**Supported formats:** {', '.join(['.' + ext for ext in supported_extensions])}")
        
        uploaded_files = st.file_uploader(
            "Upload files or archives",
            type=supported_extensions,
            accept_multiple_files=True,
            help="Upload individual files or ZIP archives containing multiple documents"
        )
        
        if uploaded_files:
            content_items = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, uploaded_file in enumerate(uploaded_files):
                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                status_text.text(f"Processing {uploaded_file.name}...")
                
                # Validate file
                is_valid, validation_message = self.file_handler.validate_file(uploaded_file)
                if not is_valid:
                    st.warning(f"Skipping {uploaded_file.name}: {validation_message}")
                    continue
                
                if uploaded_file.name.endswith('.zip'):
                    # Handle ZIP archives
                    zip_contents = self.file_handler.extract_zip_contents(uploaded_file)
                    content_items.extend(zip_contents)
                    st.success(f"Extracted {len(zip_contents)} files from {uploaded_file.name}")
                else:
                    # Handle individual files
                    content = self.file_handler.extract_content(uploaded_file)
                    if content.strip():
                        content_items.append((uploaded_file.name, content))
                        st.success(f"Processed {uploaded_file.name}")
                    else:
                        st.warning(f"No content extracted from {uploaded_file.name}")
            
            progress_bar.empty()
            status_text.empty()
            
            if content_items:
                st.info(f"Successfully processed {len(content_items)} files")
            
            return content_items
        return []
    
    def _render_directory_browse(self) -> List[Tuple[str, str]]:
        """Render directory browser for data/ and output/ directories."""
        st.write("**Browse directories:** data/, output/")
        
        selected_directory = st.selectbox(
            "Select directory:",
            options=self.file_handler.allowed_directories,
            help="Choose a directory to browse for content files"
        )
        
        if selected_directory:
            # Get files from selected directory
            available_files = self.file_handler.list_directory_files(
                selected_directory, 
                self.file_handler.supported_formats
            )
            
            if available_files:
                # Show file information
                st.write(f"**Files in {selected_directory}:**")
                
                # Create a more detailed file list with info
                file_info_list = []
                for file_path in available_files:
                    info = self.file_handler.get_file_info(file_path)
                    if info:
                        file_info_list.append({
                            'path': file_path,
                            'name': info['name'],
                            'size': info['size_human'],
                            'extension': info['extension']
                        })
                
                if file_info_list:
                    selected_files = st.multiselect(
                        f"Select files from {selected_directory}:",
                        options=[f['path'] for f in file_info_list],
                        format_func=lambda x: f"{Path(x).name} ({next(f['size'] for f in file_info_list if f['path'] == x)})",
                        help="Choose one or more files to process"
                    )
                    
                    # Batch processing options
                    if selected_files:
                        with st.expander("🔧 Batch Processing Options", expanded=False):
                            preserve_structure = st.checkbox(
                                "Preserve directory structure in titles",
                                value=True,
                                help="Include directory path in generated titles"
                            )
                            
                            apply_metadata = st.checkbox(
                                "Apply consistent metadata",
                                value=False,
                                help="Apply the same metadata to all files"
                            )
                        
                        if st.button("Process Selected Files", type="primary"):
                            content_items = []
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for i, file_path in enumerate(selected_files):
                                progress = (i + 1) / len(selected_files)
                                progress_bar.progress(progress)
                                status_text.text(f"Processing {Path(file_path).name}...")
                                
                                content = self.file_handler.read_file(file_path)
                                if content.strip():
                                    # Use full path or just filename based on option
                                    display_name = file_path if preserve_structure else Path(file_path).name
                                    content_items.append((display_name, content))
                            
                            progress_bar.empty()
                            status_text.empty()
                            
                            if content_items:
                                st.success(f"Successfully processed {len(content_items)} files")
                            
                            return content_items
            else:
                st.info(f"No supported files found in {selected_directory}")
        
        return []
    
    def _process_content_items(self, content_items: List[Tuple[str, str]]) -> Optional[List[CodexObject]]:
        """Process multiple content items and create CodexObjects."""
        if not content_items:
            return None
        
        # If single item, use existing single object flow
        if len(content_items) == 1:
            filename, content = content_items[0]
            return self._process_single_content_item(filename, content)
        
        # Multiple items - show batch processing interface
        st.markdown("### 📁 Batch Content Processing")
        st.write(f"Processing {len(content_items)} content items")
        
        # Show preview of items
        with st.expander("📋 Content Items Preview", expanded=False):
            for i, (filename, content) in enumerate(content_items[:10]):  # Show first 10
                preview = content[:100] + "..." if len(content) > 100 else content
                st.write(f"**{i+1}. {filename}** ({len(content.split())} words): {preview}")
            
            if len(content_items) > 10:
                st.write(f"... and {len(content_items) - 10} more items")
        
        # Batch processing options
        col1, col2 = st.columns(2)
        
        with col1:
            auto_detect = st.checkbox(
                "Auto-detect content types",
                value=True,
                help="Automatically detect the type of each content item"
            )
        
        with col2:
            use_llm_batch = st.checkbox(
                "Use LLM for batch detection",
                value=False,
                help="Use AI models for more sophisticated content analysis"
            )
        
        if use_llm_batch:
            selected_model = self.model_config.render_model_selector(
                "batch_detection",
                key="batch_detection_model"
            )
        else:
            selected_model = None
        
        # Process all items
        if st.button("Create All CodexObjects", type="primary"):
            created_objects = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, (filename, content) in enumerate(content_items):
                progress = (i + 1) / len(content_items)
                progress_bar.progress(progress)
                status_text.text(f"Processing {filename}...")
                
                if auto_detect:
                    # Detect content type
                    detection_result = self.content_detector.detect_type_and_multiplicity(
                        content, use_llm=use_llm_batch, selected_model=selected_model
                    )
                    
                    if detection_result['is_multiple']:
                        # Handle multiple objects in single file
                        for obj_data in detection_result['objects']:
                            title = f"{filename} - Part {obj_data['index']}"
                            codex_object = self._create_codex_object(
                                obj_data['content'], 
                                obj_data['type'], 
                                title
                            )
                            created_objects.append(codex_object)
                    else:
                        # Single object
                        title = self._suggest_title_from_filename(filename, content)
                        codex_object = self._create_codex_object(
                            content, 
                            detection_result['type'], 
                            title
                        )
                        created_objects.append(codex_object)
                else:
                    # Default to idea type
                    title = self._suggest_title_from_filename(filename, content)
                    codex_object = self._create_codex_object(
                        content, 
                        CodexObjectType.IDEA, 
                        title
                    )
                    created_objects.append(codex_object)
            
            progress_bar.empty()
            status_text.empty()
            
            # Store in session state
            state = st.session_state[self.session_key]
            state['created_objects'].extend(created_objects)
            state['object_counter'] += len(created_objects)
            
            st.success(f"✅ Created {len(created_objects)} CodexObjects!")
            st.balloons()
            return created_objects
        
        return None
    
    def _process_single_content_item(self, filename: str, content: str) -> Optional[CodexObject]:
        """Process a single content item with full detection interface."""
        if content and content.strip():
            # Pre-detection LLM settings
            st.markdown("### 🔍 Content Detection Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                use_llm_initial = st.checkbox(
                    "Use LLM Detection",
                    value=False,
                    help="Use AI model for more sophisticated content analysis",
                    key="initial_llm_detection"
                )
            
            with col2:
                if use_llm_initial:
                    selected_model_initial = self.model_config.render_model_selector(
                        "content_detection",
                        key="initial_detection_model"
                    )
                else:
                    selected_model_initial = None
            
            # Perform initial content detection
            detection_result = self.content_detector.detect_type_and_multiplicity(
                content, use_llm=use_llm_initial, selected_model=selected_model_initial
            )
            
            # Display detection results with redo option
            self._render_detection_results_with_multiplicity_and_redo(detection_result, content, filename)
            
            # Handle object creation based on detection results
            if detection_result.get('force_single', False):
                # User chose to treat as single object
                return self._handle_single_object_creation(detection_result, content, filename)
            elif detection_result['is_multiple']:
                return self._handle_multiple_objects_creation(detection_result, content, filename)
            else:
                return self._handle_single_object_creation(detection_result, content, filename)
        
        return None
    
    def render_created_objects_display(self):
        """Display recently created objects (legacy simple view)."""
        state = st.session_state[self.session_key]
        created_objects = state['created_objects']
        
        if created_objects:
            st.subheader("📚 Created Objects")
            
            # Show the most recent objects
            recent_objects = created_objects[-5:]  # Show last 5
            
            for obj in reversed(recent_objects):  # Most recent first
                with st.expander(f"📄 {obj.title} ({obj.object_type.value.title()})", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write("**Content Preview:**")
                        preview = obj.content[:300] + "..." if len(obj.content) > 300 else obj.content
                        st.write(preview)
                    
                    with col2:
                        st.write("**Metadata:**")
                        st.write(f"**Type:** {obj.object_type.value.title()}")
                        st.write(f"**Word Count:** {obj.word_count}")
                        st.write(f"**Created:** {obj.created_timestamp[:10]}")
                        if hasattr(obj, 'genre') and obj.genre:
                            st.write(f"**Genre:** {obj.genre}")
                        if hasattr(obj, 'target_audience') and obj.target_audience:
                            st.write(f"**Audience:** {obj.target_audience}")
            
            # Show total count
            if len(created_objects) > 5:
                st.info(f"Showing 5 most recent objects. Total created: {len(created_objects)}")
        else:
            st.info("No objects created yet. Use the input above to create your first CodexObject!")
    
    def render_enhanced_objects_display(self):
        """Display objects using the enhanced data table."""
        state = st.session_state[self.session_key]
        created_objects = state['created_objects']
        
        # Render the data table
        table_result = self.data_table.render_object_table(created_objects)
        
        # Handle bulk actions
        if table_result['actions']:
            self._handle_bulk_actions(table_result['actions'])
        
        return table_result
    
    def _handle_bulk_actions(self, actions: Dict[str, Any]):
        """Handle bulk actions from the data table."""
        if 'export' in actions:
            self._handle_export_action(actions['export'])
        
        if 'add_tags' in actions:
            self._handle_add_tags_action(actions['add_tags'])
        
        if 'copy_titles' in actions:
            self._handle_copy_titles_action(actions['copy_titles'])
        
        if 'delete' in actions:
            self._handle_delete_action(actions['delete'])
    
    def _handle_export_action(self, selected_objects: List[CodexObject]):
        """Handle export action for selected objects."""
        st.markdown("### 📤 Export Selected Objects")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Export Format",
                options=["CSV", "JSON", "Text"],
                help="Choose the export format"
            )
        
        with col2:
            if st.button("Download Export", type="primary"):
                if export_format == "CSV":
                    export_data = self.data_table.export_objects_to_csv(selected_objects)
                    st.download_button(
                        "📥 Download CSV",
                        data=export_data,
                        file_name=f"codex_objects_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                elif export_format == "JSON":
                    export_data = self.data_table.export_objects_to_json(selected_objects)
                    st.download_button(
                        "📥 Download JSON",
                        data=export_data,
                        file_name=f"codex_objects_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                elif export_format == "Text":
                    export_data = "\n\n".join([f"Title: {obj.title}\nType: {obj.object_type.value}\nContent:\n{obj.content}" for obj in selected_objects])
                    st.download_button(
                        "📥 Download Text",
                        data=export_data,
                        file_name=f"codex_objects_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
    
    def _handle_add_tags_action(self, selected_objects: List[CodexObject]):
        """Handle add tags action for selected objects."""
        st.markdown("### 🏷️ Add Tags to Selected Objects")
        
        new_tags = st.text_input(
            "Tags to add (comma-separated)",
            placeholder="adventure, fantasy, completed...",
            help="Enter tags separated by commas"
        )
        
        if new_tags and st.button("Add Tags", type="primary"):
            tags_list = [tag.strip() for tag in new_tags.split(',') if tag.strip()]
            
            for obj in selected_objects:
                # Add tags to existing tags or create new tags attribute
                existing_tags = getattr(obj, 'tags', '')
                if existing_tags:
                    combined_tags = existing_tags + ', ' + ', '.join(tags_list)
                else:
                    combined_tags = ', '.join(tags_list)
                
                setattr(obj, 'tags', combined_tags)
            
            st.success(f"✅ Added tags to {len(selected_objects)} objects!")
    
    def _handle_copy_titles_action(self, selected_objects: List[CodexObject]):
        """Handle copy titles action for selected objects."""
        titles = [obj.title for obj in selected_objects]
        titles_text = '\n'.join(titles)
        
        st.markdown("### 📋 Copy Titles")
        st.text_area(
            "Titles (copy from here)",
            value=titles_text,
            height=150,
            help="Select all and copy these titles"
        )
        
        st.success(f"✅ {len(titles)} titles ready to copy!")
    
    def _handle_delete_action(self, selected_objects: List[CodexObject]):
        """Handle delete action for selected objects."""
        st.markdown("### 🗑️ Delete Selected Objects")
        
        st.warning(f"⚠️ You are about to delete {len(selected_objects)} objects. This action cannot be undone.")
        
        # Show objects to be deleted
        with st.expander("Objects to be deleted"):
            for obj in selected_objects:
                st.write(f"• {obj.title} ({obj.object_type.value.title()})")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("❌ Cancel", type="secondary"):
                st.info("Delete operation cancelled.")
        
        with col2:
            if st.button("🗑️ Confirm Delete", type="primary"):
                # Remove objects from session state
                state = st.session_state[self.session_key]
                
                # Create a set of objects to delete for faster lookup
                objects_to_delete = set(id(obj) for obj in selected_objects)
                
                # Filter out deleted objects
                state['created_objects'] = [
                    obj for obj in state['created_objects'] 
                    if id(obj) not in objects_to_delete
                ]
                
                st.success(f"✅ Deleted {len(selected_objects)} objects!")
                st.rerun()
    
    def _create_codex_object(self, content: str, content_type: CodexObjectType, title: str) -> CodexObject:
        """Create a CodexObject from input data (legacy method)."""
        # Generate title if not provided
        if not title or not title.strip():
            title = self._suggest_title(content)
        
        # Create the CodexObject using the existing structure
        codex_object = CodexObject(
            content=content.strip(),
            object_type=content_type,
            title=title.strip(),
            word_count=len(content.split()),
            genre="",
            target_audience=""
        )
        
        return codex_object
    
    def _create_enhanced_codex_object(self, content: str, content_type: CodexObjectType, form_data: Dict[str, Any]) -> CodexObject:
        """Create a CodexObject with enhanced metadata from form data."""
        # Use title from form or generate one
        title = form_data.get('title', '').strip()
        if not title:
            title = self._suggest_title(content)
        
        # Create the CodexObject with enhanced metadata
        codex_object = CodexObject(
            content=content.strip(),
            object_type=content_type,
            title=title,
            word_count=len(content.split()),
            genre=form_data.get('genre', ''),
            target_audience=form_data.get('target_audience', '')
        )
        
        # Add additional metadata as attributes
        for key, value in form_data.items():
            if key not in ['title', 'genre', 'target_audience'] and value:
                # Convert field names to valid attribute names
                attr_name = key.replace(' ', '_').lower()
                setattr(codex_object, attr_name, value)
        
        return codex_object
    
    def _suggest_title(self, content: str) -> str:
        """Suggest a title based on content."""
        if not content or not content.strip():
            return ""
        
        # Simple title suggestion logic
        lines = content.strip().split('\n')
        first_line = lines[0].strip()
        
        # If first line is short and looks like a title, use it
        if len(first_line) < 100 and not first_line.endswith('.'):
            return first_line
        
        # Otherwise, create a title from first few words
        words = content.strip().split()[:6]
        suggested_title = ' '.join(words)
        
        # Clean up the title
        if suggested_title.endswith('.'):
            suggested_title = suggested_title[:-1]
        
        return suggested_title if len(suggested_title) < 100 else suggested_title[:97] + "..."
    
    def _suggest_title_from_filename(self, filename: str, content: str) -> str:
        """Suggest a title based on filename and content."""
        if filename:
            # Use filename without extension as base title
            base_title = Path(filename).stem
            # Clean up the filename
            base_title = base_title.replace('_', ' ').replace('-', ' ')
            base_title = ' '.join(word.capitalize() for word in base_title.split())
            
            # If the base title is reasonable, use it
            if 3 <= len(base_title) <= 100:
                return base_title
        
        # Fallback to content-based title
        return self._suggest_title(content)
    
    def _render_detection_results(self, detected_type: CodexObjectType, confidence: float, reasoning: str, content: str):
        """Render the content detection results."""
        st.markdown("### 🔍 Content Analysis Results")
        
        # Main detection result
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            confidence_color = "green" if confidence > 0.7 else "orange" if confidence > 0.4 else "red"
            st.markdown(f"**Detected Type:** :{confidence_color}[{detected_type.value.title()}]")
        
        with col2:
            st.metric("Confidence", f"{confidence:.1%}")
        
        with col3:
            word_count = len(content.split())
            st.metric("Word Count", f"{word_count:,}")
        
        # Reasoning
        with st.expander("📋 Detection Reasoning", expanded=False):
            st.write(reasoning)
            
            # Additional details
            details = self.content_detector.get_detection_details(content)
            st.write("**Content Statistics:**")
            st.write(f"- Characters: {details['content_length']:,}")
            st.write(f"- Words: {details['word_count']:,}")
            st.write(f"- Lines: {details['line_count']:,}")
        
        # Confidence indicator
        if confidence < 0.5:
            st.warning("⚠️ Low confidence detection. Consider manual override or providing more content.")
        elif confidence < 0.7:
            st.info("ℹ️ Moderate confidence. You may want to verify the detected type.")
        else:
            st.success("✅ High confidence detection!")   
 
    def _render_detection_results_with_multiplicity_and_redo(self, detection_result: Dict, content: str, filename: str = None):
        """Render detection results with redo options and single object override."""
        st.markdown("### 🔍 Content Analysis Results")
        
        if detection_result['is_multiple']:
            # Multiple objects detected
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**Multiple Objects Detected:** :blue[{detection_result['count']} objects]")
            
            with col2:
                st.metric("Detection Confidence", f"{detection_result['confidence']:.1%}")
            
            with col3:
                word_count = len(content.split())
                st.metric("Total Word Count", f"{word_count:,}")
            
            # Show reasoning and object breakdown
            with st.expander("📋 Multiple Objects Analysis", expanded=True):
                st.write(f"**Detection Reasoning:** {detection_result['reasoning']}")
                st.write(f"**Separator Type:** {detection_result.get('separator_type', 'Unknown')}")
                
                st.write("**Individual Objects Preview:**")
                for i, obj in enumerate(detection_result['objects'][:5]):  # Show first 5
                    preview = obj['content'][:100] + "..." if len(obj['content']) > 100 else obj['content']
                    st.write(f"{i+1}. **{obj['type'].value.title()}** ({obj['confidence']:.1%}): {preview}")
                
                if len(detection_result['objects']) > 5:
                    st.write(f"... and {len(detection_result['objects']) - 5} more objects")
            
            # Override options for multiple objects
            st.markdown("### ⚙️ Detection Override Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Redo Detection with LLM", help="Re-analyze content using AI model"):
                    # Store the redo request in session state
                    st.session_state['redo_detection'] = True
                    st.session_state['redo_content'] = content
                    st.session_state['redo_filename'] = filename
                    st.rerun()
            
            with col2:
                if st.button("📄 Treat All as Single Object", help="Override detection and create one object"):
                    # Force single object creation
                    detection_result['force_single'] = True
                    detection_result['is_multiple'] = False
                    # Use the most common type or first detected type
                    if detection_result['objects']:
                        most_common_type = max(set(obj['type'] for obj in detection_result['objects']), 
                                             key=lambda x: sum(1 for obj in detection_result['objects'] if obj['type'] == x))
                        detection_result['type'] = most_common_type
                    st.success("✅ Will treat content as a single object")
                    st.rerun()
        
        else:
            # Single object - show results with redo option
            self._render_detection_results(
                detection_result['type'], 
                detection_result['confidence'], 
                detection_result['reasoning'], 
                content
            )
            
            # Redo option for single objects
            st.markdown("### ⚙️ Detection Options")
            if st.button("🔄 Redo Detection with LLM", help="Re-analyze content using AI model"):
                st.session_state['redo_detection'] = True
                st.session_state['redo_content'] = content
                st.session_state['redo_filename'] = filename
                st.rerun()
        
        # Handle redo detection if requested
        if st.session_state.get('redo_detection', False):
            self._handle_redo_detection()
    
    def _handle_redo_detection(self):
        """Handle redo detection with LLM."""
        st.markdown("### 🔄 Redo Detection with LLM")
        
        content = st.session_state.get('redo_content', '')
        filename = st.session_state.get('redo_filename', '')
        
        if content:
            col1, col2 = st.columns(2)
            
            with col1:
                selected_model_redo = self.model_config.render_model_selector(
                    "redo_detection",
                    key="redo_detection_model"
                )
            
            with col2:
                if st.button("🚀 Run LLM Detection", type="primary"):
                    # Perform LLM detection
                    new_detection_result = self.content_detector.detect_type_and_multiplicity(
                        content, use_llm=True, selected_model=selected_model_redo
                    )
                    
                    # Clear redo state and update with new results
                    st.session_state['redo_detection'] = False
                    st.session_state['current_detection'] = new_detection_result
                    st.success("✅ Detection completed with LLM!")
                    st.rerun()
            
            if st.button("❌ Cancel Redo"):
                st.session_state['redo_detection'] = False
                st.rerun()
    
    def _render_detection_results_with_multiplicity(self, detection_result: Dict, content: str):
        """Render detection results including multiplicity information (legacy method)."""
        # This method is kept for backward compatibility
        self._render_detection_results_with_multiplicity_and_redo(detection_result, content)
    
    def _handle_multiple_objects_creation(self, detection_result: Dict, content: str, filename: str = None) -> Optional[List[CodexObject]]:
        """Handle creation of multiple CodexObjects."""
        st.markdown("### 📝 Multiple Objects Creation")
        
        # Show options for handling multiple objects
        creation_mode = st.radio(
            "How would you like to create these objects?",
            options=[
                "Treat all as single object",
                "Create all as detected types",
                "Create all as same type",
                "Review and customize each"
            ],
            help="Choose how to handle the multiple objects detected in your content"
        )
        
        created_objects = []
        
        if creation_mode == "Treat all as single object":
            # Treat the entire content as a single object
            st.info("💡 Creating a single object from all content")
            
            # Let user choose the type for the single object
            all_types = [
                CodexObjectType.IDEA,
                CodexObjectType.LOGLINE,
                CodexObjectType.SUMMARY,
                CodexObjectType.SYNOPSIS,
                CodexObjectType.OUTLINE,
                CodexObjectType.DRAFT,
                CodexObjectType.MANUSCRIPT
            ]
            
            # Use the most common detected type as default
            most_common_type = max(set(obj['type'] for obj in detection_result['objects']), 
                                 key=lambda x: sum(1 for obj in detection_result['objects'] if obj['type'] == x))
            
            chosen_type = st.selectbox(
                "Choose type for the single object:",
                options=all_types,
                index=all_types.index(most_common_type),
                format_func=lambda x: x.value.title(),
                help="Select the content type for treating all content as one object"
            )
            
            if filename:
                suggested_title = self._suggest_title_from_filename(filename, content)
            else:
                suggested_title = self._suggest_title(content)
            
            title = st.text_input(
                "Title for the single object:",
                value=suggested_title,
                help="Enter a title for the combined content"
            )
            
            if st.button("Create Single Object", type="primary"):
                state = st.session_state[self.session_key]
                
                codex_object = self._create_codex_object(
                    content, 
                    chosen_type, 
                    title
                )
                created_objects.append(codex_object)
                state['created_objects'].append(codex_object)
                state['object_counter'] += 1
                
                st.success(f"✅ Created single CodexObject: {title}")
                st.balloons()
                return created_objects
        
        elif creation_mode == "Create all as detected types":
            # Create all objects with their detected types
            if st.button("Create All Objects", type="primary"):
                state = st.session_state[self.session_key]
                
                for i, obj_data in enumerate(detection_result['objects']):
                    if filename:
                        base_title = self._suggest_title_from_filename(filename, obj_data['content'])
                        title = f"{base_title} (Part {i+1})" if len(detection_result['objects']) > 1 else base_title
                    else:
                        title = self._suggest_title(obj_data['content'])
                        if len(detection_result['objects']) > 1:
                            title = f"{title} (Part {i+1})"
                    
                    codex_object = self._create_codex_object(
                        obj_data['content'], 
                        obj_data['type'], 
                        title
                    )
                    created_objects.append(codex_object)
                    state['created_objects'].append(codex_object)
                    state['object_counter'] += 1
                
                st.success(f"✅ Created {len(created_objects)} CodexObjects!")
                st.balloons()
                return created_objects
        
        elif creation_mode == "Create all as same type":
            # Let user choose a single type for all objects
            all_types = [
                CodexObjectType.IDEA,
                CodexObjectType.LOGLINE,
                CodexObjectType.SUMMARY,
                CodexObjectType.SYNOPSIS,
                CodexObjectType.OUTLINE,
                CodexObjectType.DRAFT,
                CodexObjectType.MANUSCRIPT
            ]
            
            chosen_type = st.selectbox(
                "Choose type for all objects:",
                options=all_types,
                index=all_types.index(detection_result['type']),
                format_func=lambda x: x.value.title()
            )
            
            if st.button("Create All as Same Type", type="primary"):
                state = st.session_state[self.session_key]
                
                for i, obj_data in enumerate(detection_result['objects']):
                    if filename:
                        base_title = self._suggest_title_from_filename(filename, obj_data['content'])
                        title = f"{base_title} (Part {i+1})" if len(detection_result['objects']) > 1 else base_title
                    else:
                        title = self._suggest_title(obj_data['content'])
                        if len(detection_result['objects']) > 1:
                            title = f"{title} (Part {i+1})"
                    
                    codex_object = self._create_codex_object(
                        obj_data['content'], 
                        chosen_type, 
                        title
                    )
                    created_objects.append(codex_object)
                    state['created_objects'].append(codex_object)
                    state['object_counter'] += 1
                
                st.success(f"✅ Created {len(created_objects)} CodexObjects as {chosen_type.value.title()}!")
                st.balloons()
                return created_objects
        
        elif creation_mode == "Review and customize each":
            # Show detailed interface for each object
            st.write("**Review each object individually:**")
            
            # Store customizations in session state
            if 'object_customizations' not in st.session_state:
                st.session_state.object_customizations = {}
            
            for i, obj_data in enumerate(detection_result['objects']):
                with st.expander(f"Object {i+1}: {obj_data['type'].value.title()}", expanded=i == 0):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if filename:
                            default_title = self._suggest_title_from_filename(filename, obj_data['content'])
                            if len(detection_result['objects']) > 1:
                                default_title = f"{default_title} (Part {i+1})"
                        else:
                            default_title = self._suggest_title(obj_data['content'])
                            if len(detection_result['objects']) > 1:
                                default_title = f"{default_title} (Part {i+1})"
                        
                        custom_title = st.text_input(
                            f"Title for object {i+1}:",
                            value=st.session_state.object_customizations.get(f'title_{i}', default_title),
                            key=f"title_{i}"
                        )
                        st.session_state.object_customizations[f'title_{i}'] = custom_title
                    
                    with col2:
                        all_types = [
                            CodexObjectType.IDEA,
                            CodexObjectType.LOGLINE,
                            CodexObjectType.SUMMARY,
                            CodexObjectType.SYNOPSIS,
                            CodexObjectType.OUTLINE,
                            CodexObjectType.DRAFT,
                            CodexObjectType.MANUSCRIPT
                        ]
                        
                        try:
                            default_index = all_types.index(obj_data['type'])
                        except ValueError:
                            default_index = 0
                        
                        custom_type = st.selectbox(
                            f"Type for object {i+1}:",
                            options=all_types,
                            index=default_index,
                            format_func=lambda x: x.value.title(),
                            key=f"type_{i}"
                        )
                    
                    # Show content preview
                    preview = obj_data['content'][:200] + "..." if len(obj_data['content']) > 200 else obj_data['content']
                    st.text_area(
                        f"Content preview (Object {i+1}):",
                        value=preview,
                        height=100,
                        disabled=True
                    )
            
            if st.button("Create Customized Objects", type="primary"):
                state = st.session_state[self.session_key]
                
                for i, obj_data in enumerate(detection_result['objects']):
                    title = st.session_state.object_customizations.get(f'title_{i}', f"Object {i+1}")
                    obj_type = st.session_state[f"type_{i}"]
                    
                    codex_object = self._create_codex_object(
                        obj_data['content'], 
                        obj_type, 
                        title
                    )
                    created_objects.append(codex_object)
                    state['created_objects'].append(codex_object)
                    state['object_counter'] += 1
                
                # Clear customizations
                st.session_state.object_customizations = {}
                
                st.success(f"✅ Created {len(created_objects)} customized CodexObjects!")
                st.balloons()
                return created_objects
        
        return None
    
    def _handle_single_object_creation(self, detection_result: Dict, content: str, filename: str = None) -> Optional[CodexObject]:
        """Handle creation of a single CodexObject with adaptive form."""
        st.markdown("### 📝 Single Object Creation")
        
        # Content type selection
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Detected Type:**")
            st.info(f"{detection_result['type'].value.title()} ({detection_result['confidence']:.1%} confidence)")
        
        with col2:
            manual_override = st.checkbox(
                "Override Detection",
                value=False,
                help="Override the automatic detection and choose manually"
            )
        
        if manual_override:
            all_types = [
                CodexObjectType.IDEA,
                CodexObjectType.LOGLINE,
                CodexObjectType.SUMMARY,
                CodexObjectType.SYNOPSIS,
                CodexObjectType.OUTLINE,
                CodexObjectType.DRAFT,
                CodexObjectType.MANUSCRIPT
            ]
            
            try:
                default_index = all_types.index(detection_result['type'])
            except ValueError:
                default_index = 0
            
            content_type = st.selectbox(
                "Choose Content Type:",
                options=all_types,
                index=default_index,
                format_func=lambda x: x.value.title(),
                help="Manually select the content type"
            )
        else:
            content_type = detection_result['type']
        
        # Render adaptive form based on content type
        form_data = self.form_adapter.render_adaptive_form(
            content_type, 
            content, 
            key_suffix=f"single_{filename or 'content'}"
        )
        
        # Create CodexObject button
        if st.button("Create CodexObject", type="primary"):
            # Use form data to create enhanced CodexObject
            codex_object = self._create_enhanced_codex_object(content, content_type, form_data)
            
            # Store in session state
            state = st.session_state[self.session_key]
            state['created_objects'].append(codex_object)
            state['object_counter'] += 1
            
            st.success(f"✅ Created CodexObject: {codex_object.title}")
            st.balloons()
            return codex_object
        
        return None