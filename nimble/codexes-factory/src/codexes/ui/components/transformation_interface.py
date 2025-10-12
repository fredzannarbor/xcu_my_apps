"""
Content Transformation Interface

UI component for transforming CodexObjects between different content types.
Supports both single and batch transformations with history tracking.
"""

from typing import List, Dict, Any, Optional, Tuple
import streamlit as st
from datetime import datetime
import logging
import uuid
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from ...modules.ideation.core.codex_object import CodexObject, CodexObjectType
from .content_detector import ContentTypeDetector
from .file_handler import FileHandler

logger = logging.getLogger(__name__)


class TransformationInterface:
    """Interface for transforming CodexObjects between types."""
    
    def __init__(self):
        self.session_key = "transformation_interface_state"
        self.content_detector = ContentTypeDetector()
        self.file_handler = FileHandler()
        
        # Available transformation types
        self.available_types = [
            CodexObjectType.IDEA,
            CodexObjectType.LOGLINE,
            CodexObjectType.SUMMARY,
            CodexObjectType.SYNOPSIS,
            CodexObjectType.TREATMENT,
            CodexObjectType.OUTLINE,
            CodexObjectType.DETAILED_OUTLINE,
            CodexObjectType.DRAFT,
            CodexObjectType.MANUSCRIPT,
            CodexObjectType.SERIES
        ]
        
        # Transformation approaches
        self.transformation_approaches = {
            'planning': 'Planning (Top-down structured approach)',
            'gardening': 'Gardening (Bottom-up organic approach)'
        }
        
        # Transformation parameters
        self.transformation_parameters = {
            'expand': 'Expand (Add detail and depth)',
            'condense': 'Condense (Summarize and focus)',
            'restructure': 'Restructure (Change format/structure)',
            'enhance': 'Enhance (Improve existing content)'
        }
        
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state for the transformation interface."""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                'transformation_history': [],
                'selected_objects': [],
                'transformation_results': [],
                'last_transformation_time': None,
                'batch_progress': {},
                'transformation_lineage': {},  # Track parent-child relationships
                'rollback_snapshots': {},  # Store snapshots for rollback
                'quality_assessments': {}  # Store quality scores and comparisons
            }
    
    def render_transformation_interface(self, source_objects: Optional[List[CodexObject]] = None) -> Dict[str, Any]:
        """
        Render the main transformation interface.
        
        Args:
            source_objects: Optional pre-selected objects for transformation
            
        Returns:
            Dict containing transformation results and actions
        """
        st.markdown("### 🔄 Content Transformation")
        st.markdown("Transform your content between different types using AI assistance.")
        
        # Create tabs for different transformation workflows
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Single Transform", "📦 Batch Transform", "📈 History & Lineage", "🔄 Rollback", "💡 Suggestions"])
        
        with tab1:
            transformation_results = self._render_single_transformation(source_objects)
        
        with tab2:
            batch_results = self._render_batch_transformation(source_objects)
        
        with tab3:
            history_results = self._render_transformation_history()
        
        with tab4:
            rollback_results = self._render_rollback_interface()
        
        with tab5:
            suggestions_results = self._render_transformation_suggestions(source_objects)
        
        # Combine all results
        combined_results = {
            'single_transformation': transformation_results,
            'batch_transformation': batch_results,
            'history': history_results,
            'rollback': rollback_results,
            'suggestions': suggestions_results
        }
        
        return combined_results
    
    def _render_single_transformation(self, source_objects: Optional[List[CodexObject]]) -> Dict[str, Any]:
        """Render single object transformation interface."""
        st.markdown("#### 🎯 Content Transformation")
        
        # Input method selection
        input_method = st.radio(
            "Content source for transformation:",
            options=["Selected Objects", "Text Input", "File Upload"],
            horizontal=True,
            key="transform_input_method",
            help="Choose how to provide content for transformation"
        )
        
        transformation_objects = []
        
        if input_method == "Selected Objects":
            if source_objects and len(source_objects) > 0:
                transformation_objects = source_objects
                st.success(f"✅ Using {len(source_objects)} available objects")
                
                # Show which objects will be transformed
                st.write("**Objects available for transformation:**")
                for i, obj in enumerate(source_objects[:3]):  # Show first 3
                    st.write(f"• {obj.title} ({obj.object_type.value.title()}) - {obj.word_count} words")
                if len(source_objects) > 3:
                    st.write(f"... and {len(source_objects) - 3} more objects")
            else:
                st.warning("⚠️ No objects available for transformation.")
                st.info("💡 **Next steps:** Create some content in the 'Create Content' tab first, or use 'Text Input' to enter content directly.")
                return {}
        
        elif input_method == "File Upload":
            transformation_objects = self._render_file_upload_input()
        
        elif input_method == "Text Input":
            transformation_objects = self._render_text_input()
        
        if not transformation_objects:
            return {}
        
        # Show source objects
        st.write("**Source Objects:**")
        for i, obj in enumerate(transformation_objects):
            with st.expander(f"📄 {obj.title} ({obj.object_type.value.title()})", expanded=False):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write("**Content Preview:**")
                    preview = obj.content[:200] + "..." if len(obj.content) > 200 else obj.content
                    st.text(preview)
                with col2:
                    st.write(f"**Type:** {obj.object_type.value.title()}")
                    st.write(f"**Words:** {obj.word_count}")
                    if obj.genre:
                        st.write(f"**Genre:** {obj.genre}")
        
        # Transformation configuration
        st.markdown("**Transformation Configuration:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Target type selection
            target_type = st.selectbox(
                "Transform to:",
                options=self.available_types,
                format_func=lambda x: x.value.title(),
                help="Select the target content type for transformation",
                key="single_target_type"
            )
            
            # Transformation approach
            approach_key = st.selectbox(
                "Transformation Approach:",
                options=list(self.transformation_approaches.keys()),
                format_func=lambda x: self.transformation_approaches[x],
                help="Choose the transformation methodology",
                key="single_approach"
            )
        
        with col2:
            # Transformation parameter
            parameter_key = st.selectbox(
                "Transformation Parameter:",
                options=list(self.transformation_parameters.keys()),
                format_func=lambda x: self.transformation_parameters[x],
                help="Choose how to modify the content",
                key="single_parameter"
            )
        
        # Custom instructions
        custom_instructions = st.text_area(
            "Custom Instructions (optional):",
            placeholder="Additional guidance for the transformation process...",
            help="Provide specific instructions for how you want the content transformed",
            key="single_custom_instructions"
        )
        
        # Preview transformation
        if st.button("🔍 Preview Transformation", help="Preview what the transformation will do"):
            self._show_transformation_preview(transformation_objects[0], target_type, parameter_key)
        
        # Execute transformation
        if st.button("🚀 Transform Content", type="primary", help="Execute the transformation"):
            with st.spinner("Transforming content..."):
                try:
                    results = self._execute_single_transformation(
                        transformation_objects[0],  # Transform first object for single mode
                        target_type,
                        approach_key,
                        parameter_key,
                        custom_instructions
                    )
                    
                    if results:
                        st.success("Transformation completed successfully!")
                        self._display_transformation_results([results])
                        return {'transformation_result': results}
                    else:
                        st.error("Transformation failed - no results returned")
                        
                except Exception as e:
                    st.error(f"Transformation error: {str(e)}")
                    logger.error(f"Transformation button error: {e}")
        
        return {}
    
    def _render_batch_transformation(self, source_objects: Optional[List[CodexObject]]) -> Dict[str, Any]:
        """Render batch transformation interface for multiple objects."""
        st.markdown("#### 📦 Batch Transformation")
        st.markdown("Transform multiple objects simultaneously with progress tracking and quality assessment.")
        
        # Input method selection for batch
        input_method = st.radio(
            "Content source for batch transformation:",
            options=["Selected Objects", "File Upload", "Directory Browse"],
            horizontal=True,
            key="batch_input_method",
            help="Choose how to provide multiple objects for batch transformation"
        )
        
        batch_objects = []
        
        if input_method == "Selected Objects":
            if source_objects and len(source_objects) > 1:
                batch_objects = source_objects
                st.success(f"✅ Ready to transform {len(source_objects)} objects")
                
                # Show batch summary
                type_counts = {}
                for obj in source_objects:
                    obj_type = obj.object_type.value
                    type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
                
                st.write("**Batch Summary:**")
                for obj_type, count in type_counts.items():
                    st.write(f"• {count} {obj_type.title()}(s)")
                    
            elif source_objects and len(source_objects) == 1:
                st.warning("⚠️ Only 1 object available. Use 'Single Transform' tab for individual objects.")
                return {}
            else:
                st.warning("⚠️ No objects available for batch transformation.")
                st.info("💡 **Next steps:** Create multiple objects first, or use file upload to process multiple files.")
                return {}
        
        elif input_method == "File Upload":
            batch_objects = self._render_batch_file_upload()
        
        elif input_method == "Directory Browse":
            batch_objects = self._render_batch_directory_browse()
        
        if len(batch_objects) < 2:
            if len(batch_objects) == 1:
                st.info("Only 1 object loaded. Use 'Single Transform' tab for individual transformations.")
            return {}
        
        # Batch transformation configuration
        st.markdown("**Batch Transformation Configuration:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Target type selection
            target_type = st.selectbox(
                "Transform all to:",
                options=self.available_types,
                format_func=lambda x: x.value.title(),
                help="All objects will be transformed to this type",
                key="batch_target_type"
            )
            
            # Transformation approach
            approach_key = st.selectbox(
                "Batch Approach:",
                options=list(self.transformation_approaches.keys()),
                format_func=lambda x: self.transformation_approaches[x],
                help="Transformation methodology for all objects",
                key="batch_approach"
            )
        
        with col2:
            # Transformation parameter
            parameter_key = st.selectbox(
                "Batch Parameter:",
                options=list(self.transformation_parameters.keys()),
                format_func=lambda x: self.transformation_parameters[x],
                help="How to modify all content",
                key="batch_parameter"
            )
            
            # Processing options
            parallel_processing = st.checkbox(
                "Parallel Processing",
                value=True,
                help="Process multiple objects simultaneously for faster completion"
            )
        
        # Quality assessment options
        st.markdown("**Quality Assessment Options:**")
        col1, col2 = st.columns(2)
        
        with col1:
            enable_quality_check = st.checkbox(
                "Enable Quality Assessment",
                value=True,
                help="Assess transformation quality and provide comparison metrics"
            )
        
        with col2:
            create_rollback_snapshot = st.checkbox(
                "Create Rollback Snapshot",
                value=True,
                help="Save current state for potential rollback"
            )
        
        # Custom instructions for batch
        batch_instructions = st.text_area(
            "Batch Instructions (optional):",
            placeholder="Instructions that will apply to all transformations in this batch...",
            help="Provide instructions that will be applied to all objects in the batch",
            key="batch_custom_instructions"
        )
        
        # Preview batch transformation
        if st.button("🔍 Preview Batch Transformation", help="Preview what the batch transformation will do"):
            self._show_batch_transformation_preview(batch_objects, target_type, parameter_key)
        
        # Execute batch transformation
        if st.button("🚀 Transform Batch", type="primary", help="Execute batch transformation"):
            if create_rollback_snapshot:
                snapshot_id = self._create_rollback_snapshot(batch_objects)
                st.info(f"📸 Rollback snapshot created: {snapshot_id}")
            
            with st.spinner("Processing batch transformation..."):
                try:
                    results = self._execute_batch_transformation(
                        batch_objects,
                        target_type,
                        approach_key,
                        parameter_key,
                        batch_instructions,
                        parallel_processing,
                        enable_quality_check
                    )
                    
                    if results:
                        st.success(f"Batch transformation completed! Processed {len(results)} objects.")
                        self._display_batch_transformation_results(results, enable_quality_check)
                        return {'batch_results': results, 'objects_processed': len(results)}
                    else:
                        st.error("Batch transformation failed - no results returned")
                        
                except Exception as e:
                    st.error(f"Batch transformation error: {str(e)}")
                    logger.error(f"Batch transformation error: {e}")
        
        return {}
    
    def _render_batch_file_upload(self) -> List[CodexObject]:
        """Render file upload interface for batch transformation."""
        st.write("**Upload multiple files for batch transformation:**")
        
        uploaded_files = st.file_uploader(
            "Upload files for batch transformation",
            type=['txt', 'docx', 'pdf', 'md', 'rtf', 'zip'],
            accept_multiple_files=True,
            key="batch_upload",
            help="Upload multiple files or ZIP archives for batch transformation"
        )
        
        if uploaded_files:
            objects = []
            
            for uploaded_file in uploaded_files:
                try:
                    if uploaded_file.name.endswith('.zip'):
                        # Handle ZIP archives
                        zip_contents = self.file_handler.extract_zip_contents(uploaded_file)
                        for filename, content in zip_contents:
                            detected_type, confidence = self.content_detector.detect_type(content)
                            obj = CodexObject(
                                content=content,
                                object_type=detected_type,
                                title=filename,
                                word_count=len(content.split())
                            )
                            objects.append(obj)
                    else:
                        # Handle individual files
                        content = self.file_handler.extract_content(uploaded_file)
                        detected_type, confidence = self.content_detector.detect_type(content)
                        
                        obj = CodexObject(
                            content=content,
                            object_type=detected_type,
                            title=uploaded_file.name,
                            word_count=len(content.split())
                        )
                        objects.append(obj)
                        
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            
            if objects:
                st.success(f"Loaded {len(objects)} objects from uploaded files")
                
                # Show batch preview
                if len(objects) > 1:
                    with st.expander(f"📋 Preview {len(objects)} loaded objects", expanded=False):
                        for i, obj in enumerate(objects[:10]):  # Show first 10
                            st.write(f"{i+1}. **{obj.title}** ({obj.object_type.value.title()}) - {obj.word_count} words")
                        if len(objects) > 10:
                            st.write(f"... and {len(objects) - 10} more objects")
            
            return objects
        
        return []
    
    def _render_batch_directory_browse(self) -> List[CodexObject]:
        """Render directory browser for batch transformation."""
        st.write("**Browse directories for batch transformation:**")
        
        selected_directory = st.selectbox(
            "Select directory for batch processing:",
            options=['data/', 'output/'],
            key="batch_directory",
            help="Choose a directory to process all compatible files"
        )
        
        if selected_directory:
            # Get files from selected directory
            available_files = self.file_handler.list_directory_files(
                selected_directory, 
                ['.txt', '.docx', '.pdf', '.md', '.rtf']
            )
            
            if available_files:
                # Allow selection of multiple files
                selected_files = st.multiselect(
                    f"Select files from {selected_directory} for batch processing:",
                    options=available_files,
                    default=available_files[:5] if len(available_files) <= 5 else [],  # Auto-select first 5
                    help="Choose multiple files to process in batch"
                )
                
                if selected_files and len(selected_files) > 1:
                    objects = []
                    
                    for file_path in selected_files:
                        try:
                            content = self.file_handler.read_file(file_path)
                            detected_type, confidence = self.content_detector.detect_type(content)
                            
                            obj = CodexObject(
                                content=content,
                                object_type=detected_type,
                                title=file_path,
                                word_count=len(content.split())
                            )
                            objects.append(obj)
                            
                        except Exception as e:
                            st.error(f"Error processing {file_path}: {str(e)}")
                    
                    if objects:
                        st.success(f"Loaded {len(objects)} objects from {selected_directory}")
                    
                    return objects
                
                elif selected_files and len(selected_files) == 1:
                    st.info("Only 1 file selected. Select multiple files for batch processing.")
            else:
                st.info(f"No compatible files found in {selected_directory}")
        
        return []
    
    def _show_batch_transformation_preview(self, batch_objects: List[CodexObject], 
                                         target_type: CodexObjectType, parameter: str):
        """Show a preview of what the batch transformation will do."""
        st.markdown("**Batch Transformation Preview:**")
        
        # Summary statistics
        total_objects = len(batch_objects)
        total_words = sum(obj.word_count for obj in batch_objects)
        
        # Estimate processing time (rough calculation)
        estimated_time_per_object = 2  # seconds per object
        estimated_total_time = total_objects * estimated_time_per_object
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Objects to Process", total_objects)
        with col2:
            st.metric("Total Words", f"{total_words:,}")
        with col3:
            st.metric("Estimated Time", f"{estimated_total_time}s")
        
        # Show transformation details for first few objects
        st.write("**Sample Transformations:**")
        
        for i, obj in enumerate(batch_objects[:3]):
            with st.expander(f"📄 {obj.title} → {target_type.value.title()}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Before:**")
                    st.write(f"Type: {obj.object_type.value.title()}")
                    st.write(f"Words: {obj.word_count}")
                
                with col2:
                    st.write("**After (Estimated):**")
                    st.write(f"Type: {target_type.value.title()}")
                    
                    if parameter == 'expand':
                        estimated_words = int(obj.word_count * 1.5)
                    elif parameter == 'condense':
                        estimated_words = int(obj.word_count * 0.6)
                    else:
                        estimated_words = int(obj.word_count * 1.1)
                    
                    st.write(f"Estimated Words: ~{estimated_words}")
        
        if len(batch_objects) > 3:
            st.write(f"... and {len(batch_objects) - 3} more objects will be processed similarly.")
    
    def _execute_batch_transformation(self, batch_objects: List[CodexObject], target_type: CodexObjectType,
                                    approach: str, parameter: str, custom_instructions: str,
                                    parallel_processing: bool, enable_quality_check: bool) -> List[Dict[str, Any]]:
        """Execute batch transformation with progress tracking."""
        
        # Create batch ID for tracking
        batch_id = str(uuid.uuid4())[:8]
        
        # Initialize progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Store batch progress in session state
        st.session_state[self.session_key]['batch_progress'][batch_id] = {
            'total_objects': len(batch_objects),
            'completed_objects': 0,
            'failed_objects': 0,
            'start_time': datetime.now(),
            'status': 'processing'
        }
        
        results = []
        
        try:
            if parallel_processing and len(batch_objects) > 1:
                # Parallel processing
                results = self._execute_parallel_transformation(
                    batch_objects, target_type, approach, parameter, 
                    custom_instructions, enable_quality_check, 
                    batch_id, progress_bar, status_text
                )
            else:
                # Sequential processing
                results = self._execute_sequential_transformation(
                    batch_objects, target_type, approach, parameter,
                    custom_instructions, enable_quality_check,
                    batch_id, progress_bar, status_text
                )
            
            # Update final progress
            progress_bar.progress(1.0)
            status_text.success(f"✅ Batch transformation completed! Processed {len(results)} objects.")
            
            # Update batch progress
            st.session_state[self.session_key]['batch_progress'][batch_id]['status'] = 'completed'
            st.session_state[self.session_key]['batch_progress'][batch_id]['end_time'] = datetime.now()
            
            return results
            
        except Exception as e:
            progress_bar.progress(0)
            status_text.error(f"❌ Batch transformation failed: {str(e)}")
            
            # Update batch progress
            st.session_state[self.session_key]['batch_progress'][batch_id]['status'] = 'failed'
            st.session_state[self.session_key]['batch_progress'][batch_id]['error'] = str(e)
            
            logger.error(f"Batch transformation error: {e}")
            raise
    
    def _execute_sequential_transformation(self, batch_objects: List[CodexObject], target_type: CodexObjectType,
                                         approach: str, parameter: str, custom_instructions: str,
                                         enable_quality_check: bool, batch_id: str, 
                                         progress_bar, status_text) -> List[Dict[str, Any]]:
        """Execute transformations sequentially with progress updates."""
        results = []
        total_objects = len(batch_objects)
        
        for i, obj in enumerate(batch_objects):
            try:
                # Update progress
                progress = (i + 1) / total_objects
                progress_bar.progress(progress)
                status_text.text(f"Processing {i + 1}/{total_objects}: {obj.title}")
                
                # Execute single transformation
                result = self._execute_single_transformation(
                    obj, target_type, approach, parameter, custom_instructions
                )
                
                if result:
                    # Add batch metadata
                    result['batch_id'] = batch_id
                    result['batch_index'] = i
                    
                    # Perform quality assessment if enabled
                    if enable_quality_check:
                        quality_score = self._assess_transformation_quality(obj, result['transformed_object'])
                        result['quality_score'] = quality_score
                    
                    results.append(result)
                    
                    # Update batch progress
                    st.session_state[self.session_key]['batch_progress'][batch_id]['completed_objects'] += 1
                else:
                    st.session_state[self.session_key]['batch_progress'][batch_id]['failed_objects'] += 1
                
                # Small delay to show progress (remove in production)
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error transforming object {i}: {e}")
                st.session_state[self.session_key]['batch_progress'][batch_id]['failed_objects'] += 1
                continue
        
        return results
    
    def _execute_parallel_transformation(self, batch_objects: List[CodexObject], target_type: CodexObjectType,
                                       approach: str, parameter: str, custom_instructions: str,
                                       enable_quality_check: bool, batch_id: str,
                                       progress_bar, status_text) -> List[Dict[str, Any]]:
        """Execute transformations in parallel with progress updates."""
        results = []
        total_objects = len(batch_objects)
        completed_count = 0
        
        # Use ThreadPoolExecutor for parallel processing
        max_workers = min(4, len(batch_objects))  # Limit concurrent workers
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all transformation tasks
            future_to_obj = {
                executor.submit(
                    self._execute_single_transformation,
                    obj, target_type, approach, parameter, custom_instructions
                ): (i, obj) for i, obj in enumerate(batch_objects)
            }
            
            # Process completed transformations
            for future in as_completed(future_to_obj):
                i, obj = future_to_obj[future]
                completed_count += 1
                
                try:
                    result = future.result()
                    
                    if result:
                        # Add batch metadata
                        result['batch_id'] = batch_id
                        result['batch_index'] = i
                        
                        # Perform quality assessment if enabled
                        if enable_quality_check:
                            quality_score = self._assess_transformation_quality(obj, result['transformed_object'])
                            result['quality_score'] = quality_score
                        
                        results.append(result)
                        st.session_state[self.session_key]['batch_progress'][batch_id]['completed_objects'] += 1
                    else:
                        st.session_state[self.session_key]['batch_progress'][batch_id]['failed_objects'] += 1
                    
                    # Update progress
                    progress = completed_count / total_objects
                    progress_bar.progress(progress)
                    status_text.text(f"Completed {completed_count}/{total_objects} transformations")
                    
                except Exception as e:
                    logger.error(f"Error in parallel transformation {i}: {e}")
                    st.session_state[self.session_key]['batch_progress'][batch_id]['failed_objects'] += 1
        
        # Sort results by batch index to maintain order
        results.sort(key=lambda x: x.get('batch_index', 0))
        return results
    
    def _assess_transformation_quality(self, source_obj: CodexObject, transformed_obj: CodexObject) -> Dict[str, float]:
        """Assess the quality of a transformation."""
        quality_metrics = {}
        
        try:
            # Content length comparison
            source_words = source_obj.word_count
            transformed_words = transformed_obj.word_count
            
            if source_words > 0:
                length_ratio = transformed_words / source_words
                quality_metrics['length_ratio'] = length_ratio
                
                # Score based on expected length change
                if 0.8 <= length_ratio <= 2.0:  # Reasonable length change
                    quality_metrics['length_score'] = 0.9
                elif 0.5 <= length_ratio <= 3.0:  # Acceptable length change
                    quality_metrics['length_score'] = 0.7
                else:  # Extreme length change
                    quality_metrics['length_score'] = 0.4
            else:
                quality_metrics['length_score'] = 0.5
            
            # Content preservation (simple heuristic)
            source_words_set = set(source_obj.content.lower().split())
            transformed_words_set = set(transformed_obj.content.lower().split())
            
            if source_words_set:
                overlap_ratio = len(source_words_set.intersection(transformed_words_set)) / len(source_words_set)
                quality_metrics['content_preservation'] = overlap_ratio
                
                # Score based on content preservation
                if overlap_ratio >= 0.3:  # Good preservation
                    quality_metrics['preservation_score'] = 0.9
                elif overlap_ratio >= 0.1:  # Moderate preservation
                    quality_metrics['preservation_score'] = 0.7
                else:  # Low preservation
                    quality_metrics['preservation_score'] = 0.4
            else:
                quality_metrics['preservation_score'] = 0.5
            
            # Type appropriateness (heuristic based on content type)
            type_score = self._assess_type_appropriateness(transformed_obj)
            quality_metrics['type_appropriateness'] = type_score
            
            # Overall quality score (weighted average)
            overall_score = (
                quality_metrics.get('length_score', 0.5) * 0.3 +
                quality_metrics.get('preservation_score', 0.5) * 0.4 +
                quality_metrics.get('type_appropriateness', 0.5) * 0.3
            )
            quality_metrics['overall_score'] = overall_score
            
        except Exception as e:
            logger.error(f"Error in quality assessment: {e}")
            quality_metrics = {'overall_score': 0.5, 'error': str(e)}
        
        return quality_metrics
    
    def _assess_type_appropriateness(self, obj: CodexObject) -> float:
        """Assess if content is appropriate for its assigned type."""
        content_length = len(obj.content)
        word_count = obj.word_count
        
        # Simple heuristics based on content type expectations
        if obj.object_type == CodexObjectType.IDEA:
            return 0.9 if 10 <= word_count <= 200 else 0.6
        elif obj.object_type == CodexObjectType.LOGLINE:
            return 0.9 if 10 <= word_count <= 50 else 0.6
        elif obj.object_type == CodexObjectType.SYNOPSIS:
            return 0.9 if 100 <= word_count <= 1000 else 0.6
        elif obj.object_type == CodexObjectType.OUTLINE:
            return 0.9 if 200 <= word_count <= 2000 else 0.6
        elif obj.object_type == CodexObjectType.DRAFT:
            return 0.9 if word_count >= 500 else 0.6
        elif obj.object_type == CodexObjectType.MANUSCRIPT:
            return 0.9 if word_count >= 1000 else 0.6
        else:
            return 0.7  # Default score for other types
    
    def _display_batch_transformation_results(self, results: List[Dict[str, Any]], enable_quality_check: bool):
        """Display batch transformation results with quality metrics."""
        st.markdown("### 🎉 Batch Transformation Results")
        
        if not results:
            st.warning("No results to display.")
            return
        
        # Summary metrics
        total_results = len(results)
        successful_results = sum(1 for r in results if r.get('success', False))
        
        if enable_quality_check:
            avg_quality = sum(r.get('quality_score', {}).get('overall_score', 0) for r in results) / total_results
            quality_scores = [r.get('quality_score', {}).get('overall_score', 0) for r in results]
            min_quality = min(quality_scores) if quality_scores else 0
            max_quality = max(quality_scores) if quality_scores else 0
        
        # Display summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Processed", total_results)
        with col2:
            st.metric("Successful", successful_results)
        with col3:
            success_rate = (successful_results / total_results) * 100 if total_results > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with col4:
            if enable_quality_check:
                st.metric("Avg Quality", f"{avg_quality:.1%}")
        
        # Quality distribution if enabled
        if enable_quality_check and quality_scores:
            st.markdown("**Quality Distribution:**")
            high_quality = sum(1 for score in quality_scores if score >= 0.8)
            medium_quality = sum(1 for score in quality_scores if 0.6 <= score < 0.8)
            low_quality = sum(1 for score in quality_scores if score < 0.6)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("High Quality (≥80%)", high_quality, delta=f"{(high_quality/total_results)*100:.1f}%")
            with col2:
                st.metric("Medium Quality (60-79%)", medium_quality, delta=f"{(medium_quality/total_results)*100:.1f}%")
            with col3:
                st.metric("Low Quality (<60%)", low_quality, delta=f"{(low_quality/total_results)*100:.1f}%")
        
        # Results table
        st.markdown("**Transformation Results:**")
        
        # Create a summary table
        table_data = []
        for i, result in enumerate(results):
            source_obj = result['source_object']
            transformed_obj = result['transformed_object']
            
            row = {
                '#': i + 1,
                'Source Title': source_obj.title[:30] + "..." if len(source_obj.title) > 30 else source_obj.title,
                'From Type': source_obj.object_type.value.title(),
                'To Type': transformed_obj.object_type.value.title(),
                'Source Words': source_obj.word_count,
                'Result Words': transformed_obj.word_count,
                'Status': '✅ Success' if result.get('success') else '❌ Failed'
            }
            
            if enable_quality_check and 'quality_score' in result:
                quality = result['quality_score'].get('overall_score', 0)
                row['Quality'] = f"{quality:.1%}"
            
            table_data.append(row)
        
        # Display table
        if table_data:
            st.dataframe(table_data, use_container_width=True)
        
        # Detailed results in expandable sections
        st.markdown("**Detailed Results:**")
        
        for i, result in enumerate(results):
            source_obj = result['source_object']
            transformed_obj = result['transformed_object']
            
            # Create expandable section for each result
            quality_indicator = ""
            if enable_quality_check and 'quality_score' in result:
                quality = result['quality_score'].get('overall_score', 0)
                if quality >= 0.8:
                    quality_indicator = "🟢"
                elif quality >= 0.6:
                    quality_indicator = "🟡"
                else:
                    quality_indicator = "🔴"
            
            with st.expander(
                f"{quality_indicator} {i+1}. {source_obj.title} → {transformed_obj.object_type.value.title()}",
                expanded=False
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Original:**")
                    st.write(f"**Type:** {source_obj.object_type.value.title()}")
                    st.write(f"**Words:** {source_obj.word_count}")
                    st.text_area(
                        "Original Content:",
                        value=source_obj.content,
                        height=150,
                        disabled=True,
                        key=f"batch_original_{i}"
                    )
                
                with col2:
                    st.markdown("**Transformed:**")
                    st.write(f"**Type:** {transformed_obj.object_type.value.title()}")
                    st.write(f"**Words:** {transformed_obj.word_count}")
                    
                    if enable_quality_check and 'quality_score' in result:
                        quality_metrics = result['quality_score']
                        st.write(f"**Quality:** {quality_metrics.get('overall_score', 0):.1%}")
                        
                        # Show detailed quality metrics
                        with st.expander("Quality Details", expanded=False):
                            for metric, value in quality_metrics.items():
                                if metric != 'overall_score' and isinstance(value, (int, float)):
                                    st.write(f"• {metric.replace('_', ' ').title()}: {value:.2f}")
                    
                    st.text_area(
                        "Transformed Content:",
                        value=transformed_obj.content,
                        height=150,
                        disabled=True,
                        key=f"batch_transformed_{i}"
                    )
                
                # Action buttons for each result
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"💾 Save Result", key=f"batch_save_{i}"):
                        if 'created_objects' not in st.session_state:
                            st.session_state['created_objects'] = []
                        st.session_state['created_objects'].append(transformed_obj)
                        st.success("Result saved!")
                
                with col2:
                    if st.button(f"📋 Copy Content", key=f"batch_copy_{i}"):
                        st.code(transformed_obj.content, language="text")
                
                with col3:
                    if st.button(f"🔄 Transform Again", key=f"batch_retransform_{i}"):
                        st.info("Use the transformation interface to transform this result further")
        
        # Batch actions
        st.markdown("**Batch Actions:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Save All Results", help="Save all transformation results"):
                if 'created_objects' not in st.session_state:
                    st.session_state['created_objects'] = []
                
                for result in results:
                    if result.get('success'):
                        st.session_state['created_objects'].append(result['transformed_object'])
                
                st.success(f"Saved {successful_results} transformation results!")
        
        with col2:
            if st.button("📤 Export Batch Results", help="Export batch results to file"):
                self._export_batch_results(results)
        
        with col3:
            if enable_quality_check and st.button("📊 Quality Report", help="Generate detailed quality report"):
                self._show_quality_report(results)
    
    def _export_batch_results(self, results: List[Dict[str, Any]]):
        """Export batch transformation results."""
        try:
            export_data = []
            
            for i, result in enumerate(results):
                source_obj = result['source_object']
                transformed_obj = result['transformed_object']
                
                export_item = {
                    'index': i + 1,
                    'source_title': source_obj.title,
                    'source_type': source_obj.object_type.value,
                    'source_content': source_obj.content,
                    'source_word_count': source_obj.word_count,
                    'target_type': transformed_obj.object_type.value,
                    'transformed_content': transformed_obj.content,
                    'transformed_word_count': transformed_obj.word_count,
                    'success': result.get('success', False),
                    'transformation_notes': result.get('transformation_notes', ''),
                    'batch_id': result.get('batch_id', ''),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Add quality metrics if available
                if 'quality_score' in result:
                    quality_metrics = result['quality_score']
                    for metric, value in quality_metrics.items():
                        export_item[f'quality_{metric}'] = value
                
                export_data.append(export_item)
            
            # Convert to JSON for download
            json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            st.download_button(
                label="📥 Download Batch Results (JSON)",
                data=json_data,
                file_name=f"batch_transformation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                help="Download complete batch transformation results as JSON file"
            )
            
            st.success("Export prepared! Click the download button above.")
            
        except Exception as e:
            st.error(f"Export error: {str(e)}")
            logger.error(f"Batch export error: {e}")
    
    def _show_quality_report(self, results: List[Dict[str, Any]]):
        """Show detailed quality assessment report."""
        st.markdown("### 📊 Quality Assessment Report")
        
        quality_results = [r for r in results if 'quality_score' in r]
        
        if not quality_results:
            st.warning("No quality assessment data available.")
            return
        
        # Aggregate quality metrics
        all_metrics = {}
        for result in quality_results:
            quality_score = result['quality_score']
            for metric, value in quality_score.items():
                if isinstance(value, (int, float)):
                    if metric not in all_metrics:
                        all_metrics[metric] = []
                    all_metrics[metric].append(value)
        
        # Display aggregated metrics
        st.markdown("**Quality Metrics Summary:**")
        
        for metric, values in all_metrics.items():
            if values:
                avg_value = sum(values) / len(values)
                min_value = min(values)
                max_value = max(values)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"**{metric.replace('_', ' ').title()}**")
                with col2:
                    st.write(f"Avg: {avg_value:.2f}")
                with col3:
                    st.write(f"Min: {min_value:.2f}")
                with col4:
                    st.write(f"Max: {max_value:.2f}")
        
        # Quality distribution
        overall_scores = all_metrics.get('overall_score', [])
        if overall_scores:
            st.markdown("**Quality Score Distribution:**")
            
            # Create simple histogram
            high_count = sum(1 for score in overall_scores if score >= 0.8)
            medium_count = sum(1 for score in overall_scores if 0.6 <= score < 0.8)
            low_count = sum(1 for score in overall_scores if score < 0.6)
            
            total_count = len(overall_scores)
            
            st.write(f"🟢 High Quality (≥80%): {high_count} ({(high_count/total_count)*100:.1f}%)")
            st.write(f"🟡 Medium Quality (60-79%): {medium_count} ({(medium_count/total_count)*100:.1f}%)")
            st.write(f"🔴 Low Quality (<60%): {low_count} ({(low_count/total_count)*100:.1f}%)")
    
    def _create_rollback_snapshot(self, objects: List[CodexObject]) -> str:
        """Create a rollback snapshot of objects before transformation."""
        snapshot_id = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        snapshot_data = {
            'id': snapshot_id,
            'timestamp': datetime.now().isoformat(),
            'objects': []
        }
        
        for obj in objects:
            obj_data = {
                'uuid': obj.uuid,
                'title': obj.title,
                'content': obj.content,
                'object_type': obj.object_type.value,
                'word_count': obj.word_count,
                'genre': obj.genre,
                'target_audience': obj.target_audience
            }
            snapshot_data['objects'].append(obj_data)
        
        # Store snapshot in session state
        st.session_state[self.session_key]['rollback_snapshots'][snapshot_id] = snapshot_data
        
        return snapshot_id
    
    def _render_rollback_interface(self) -> Dict[str, Any]:
        """Render rollback interface for undoing transformations."""
        st.markdown("#### 🔄 Rollback & Recovery")
        st.markdown("Restore previous states of your content before transformations.")
        
        snapshots = st.session_state[self.session_key]['rollback_snapshots']
        
        if not snapshots:
            st.info("No rollback snapshots available. Snapshots are created automatically before batch transformations.")
            return {}
        
        st.markdown("**Available Snapshots:**")
        
        # Display snapshots in reverse chronological order
        sorted_snapshots = sorted(snapshots.items(), key=lambda x: x[1]['timestamp'], reverse=True)
        
        for snapshot_id, snapshot_data in sorted_snapshots:
            timestamp = datetime.fromisoformat(snapshot_data['timestamp'])
            object_count = len(snapshot_data['objects'])
            
            with st.expander(
                f"📸 {snapshot_id} - {timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({object_count} objects)",
                expanded=False
            ):
                st.write(f"**Snapshot ID:** {snapshot_id}")
                st.write(f"**Created:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"**Objects:** {object_count}")
                
                # Show object preview
                st.write("**Objects in snapshot:**")
                for i, obj_data in enumerate(snapshot_data['objects'][:5]):  # Show first 5
                    st.write(f"• {obj_data['title']} ({obj_data['object_type'].title()}) - {obj_data['word_count']} words")
                
                if len(snapshot_data['objects']) > 5:
                    st.write(f"... and {len(snapshot_data['objects']) - 5} more objects")
                
                # Rollback actions
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"🔄 Restore Snapshot", key=f"restore_{snapshot_id}"):
                        restored_objects = self._restore_snapshot(snapshot_id)
                        if restored_objects:
                            st.success(f"Restored {len(restored_objects)} objects from snapshot!")
                            return {'restored_objects': restored_objects}
                
                with col2:
                    if st.button(f"👁️ Preview Objects", key=f"preview_{snapshot_id}"):
                        self._preview_snapshot_objects(snapshot_data['objects'])
                
                with col3:
                    if st.button(f"🗑️ Delete Snapshot", key=f"delete_{snapshot_id}"):
                        del st.session_state[self.session_key]['rollback_snapshots'][snapshot_id]
                        st.success("Snapshot deleted!")
                        st.rerun()
        
        # Cleanup old snapshots
        if len(snapshots) > 10:  # Keep only last 10 snapshots
            st.markdown("---")
            if st.button("🧹 Clean Old Snapshots", help="Keep only the 10 most recent snapshots"):
                self._cleanup_old_snapshots()
                st.success("Old snapshots cleaned up!")
                st.rerun()
        
        return {}
    
    def _restore_snapshot(self, snapshot_id: str) -> List[CodexObject]:
        """Restore objects from a snapshot."""
        try:
            snapshot_data = st.session_state[self.session_key]['rollback_snapshots'][snapshot_id]
            restored_objects = []
            
            for obj_data in snapshot_data['objects']:
                # Recreate CodexObject from snapshot data
                obj = CodexObject(
                    content=obj_data['content'],
                    object_type=CodexObjectType(obj_data['object_type']),
                    title=obj_data['title'],
                    word_count=obj_data['word_count'],
                    genre=obj_data.get('genre'),
                    target_audience=obj_data.get('target_audience')
                )
                
                # Restore original UUID if available
                if 'uuid' in obj_data:
                    obj.uuid = obj_data['uuid']
                
                restored_objects.append(obj)
            
            # Add restored objects to session state
            if 'created_objects' not in st.session_state:
                st.session_state['created_objects'] = []
            
            st.session_state['created_objects'].extend(restored_objects)
            
            return restored_objects
            
        except Exception as e:
            st.error(f"Error restoring snapshot: {str(e)}")
            logger.error(f"Snapshot restore error: {e}")
            return []
    
    def _preview_snapshot_objects(self, objects_data: List[Dict[str, Any]]):
        """Preview objects in a snapshot."""
        st.markdown("**Snapshot Object Preview:**")
        
        for i, obj_data in enumerate(objects_data):
            with st.expander(f"📄 {obj_data['title']} ({obj_data['object_type'].title()})", expanded=False):
                st.write(f"**Type:** {obj_data['object_type'].title()}")
                st.write(f"**Words:** {obj_data['word_count']}")
                if obj_data.get('genre'):
                    st.write(f"**Genre:** {obj_data['genre']}")
                
                st.text_area(
                    "Content:",
                    value=obj_data['content'],
                    height=150,
                    disabled=True,
                    key=f"preview_snapshot_{i}"
                )
    
    def _cleanup_old_snapshots(self):
        """Clean up old snapshots, keeping only the 10 most recent."""
        snapshots = st.session_state[self.session_key]['rollback_snapshots']
        
        if len(snapshots) <= 10:
            return
        
        # Sort by timestamp and keep only the 10 most recent
        sorted_snapshots = sorted(snapshots.items(), key=lambda x: x[1]['timestamp'], reverse=True)
        recent_snapshots = dict(sorted_snapshots[:10])
        
        st.session_state[self.session_key]['rollback_snapshots'] = recent_snapshots
    
    def _render_transformation_history(self) -> Dict[str, Any]:
        """Render transformation history and lineage tracking interface."""
        st.markdown("#### 📈 Transformation History & Lineage")
        
        history = st.session_state[self.session_key]['transformation_history']
        lineage = st.session_state[self.session_key]['transformation_lineage']
        
        if not history:
            st.info("No transformations performed yet. Transform some content to see history here.")
            return {}
        
        # Create sub-tabs for different views
        subtab1, subtab2, subtab3 = st.tabs(["📊 Statistics", "📋 History Log", "🌳 Lineage Tree"])
        
        with subtab1:
            self._render_history_statistics(history)
        
        with subtab2:
            self._render_history_log(history)
        
        with subtab3:
            self._render_lineage_tree(lineage)
        
        return {'history_entries': len(history)}
    
    def _render_history_statistics(self, history: List[Dict[str, Any]]):
        """Render transformation history statistics."""
        st.markdown("**Transformation Statistics:**")
        
        # Basic statistics
        total_transformations = len(history)
        successful_transformations = sum(1 for h in history if h.get('success', False))
        success_rate = (successful_transformations / total_transformations) * 100 if total_transformations > 0 else 0
        
        # Batch vs single statistics
        batch_transformations = sum(1 for h in history if h.get('batch_id'))
        single_transformations = total_transformations - batch_transformations
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Transformations", total_transformations)
        with col2:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with col3:
            st.metric("Batch Transformations", batch_transformations)
        with col4:
            st.metric("Single Transformations", single_transformations)
        
        # Transformation type analysis
        if history:
            st.markdown("**Transformation Patterns:**")
            
            # Count transformation types
            type_pairs = {}
            for entry in history:
                source_type = entry.get('source_type', 'Unknown')
                target_type = entry.get('target_type', 'Unknown')
                pair = f"{source_type} → {target_type}"
                type_pairs[pair] = type_pairs.get(pair, 0) + 1
            
            # Show most common transformations
            sorted_pairs = sorted(type_pairs.items(), key=lambda x: x[1], reverse=True)
            
            st.write("**Most Common Transformations:**")
            for pair, count in sorted_pairs[:5]:
                percentage = (count / total_transformations) * 100
                st.write(f"• {pair}: {count} times ({percentage:.1f}%)")
            
            # Parameter usage
            parameter_usage = {}
            for entry in history:
                param = entry.get('parameter', 'Unknown')
                parameter_usage[param] = parameter_usage.get(param, 0) + 1
            
            st.write("**Parameter Usage:**")
            for param, count in parameter_usage.items():
                percentage = (count / total_transformations) * 100
                st.write(f"• {param.title()}: {count} times ({percentage:.1f}%)")
        
        # Quality trends (if available)
        quality_scores = [h.get('confidence_score', 0) for h in history if h.get('confidence_score')]
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            min_quality = min(quality_scores)
            max_quality = max(quality_scores)
            
            st.markdown("**Quality Trends:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Quality", f"{avg_quality:.1%}")
            with col2:
                st.metric("Best Quality", f"{max_quality:.1%}")
            with col3:
                st.metric("Lowest Quality", f"{min_quality:.1%}")
    
    def _render_history_log(self, history: List[Dict[str, Any]]):
        """Render detailed transformation history log."""
        st.markdown("**Transformation Log:**")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_type = st.selectbox(
                "Filter by type:",
                options=["All", "Single", "Batch"],
                help="Filter transformations by processing type"
            )
        
        with col2:
            filter_success = st.selectbox(
                "Filter by status:",
                options=["All", "Successful", "Failed"],
                help="Filter transformations by success status"
            )
        
        with col3:
            show_count = st.selectbox(
                "Show entries:",
                options=[10, 25, 50, "All"],
                help="Number of entries to display"
            )
        
        # Apply filters
        filtered_history = history.copy()
        
        if filter_type == "Single":
            filtered_history = [h for h in filtered_history if not h.get('batch_id')]
        elif filter_type == "Batch":
            filtered_history = [h for h in filtered_history if h.get('batch_id')]
        
        if filter_success == "Successful":
            filtered_history = [h for h in filtered_history if h.get('success')]
        elif filter_success == "Failed":
            filtered_history = [h for h in filtered_history if not h.get('success')]
        
        # Limit entries
        if isinstance(show_count, int):
            filtered_history = filtered_history[-show_count:]
        
        # Display filtered history
        if not filtered_history:
            st.info("No transformations match the current filters.")
            return
        
        for i, entry in enumerate(reversed(filtered_history)):
            # Create header with icons
            batch_icon = "📦" if entry.get('batch_id') else "🎯"
            success_icon = "✅" if entry.get('success') else "❌"
            
            header = (f"{batch_icon} {success_icon} "
                     f"{entry.get('source_type', 'Unknown')} → {entry.get('target_type', 'Unknown')} "
                     f"({entry.get('timestamp', 'Unknown time')})")
            
            with st.expander(header, expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Source:** {entry.get('source_title', 'Untitled')}")
                    st.write(f"**Result:** {entry.get('result_title', 'Untitled')}")
                    if entry.get('transformation_notes'):
                        st.write(f"**Notes:** {entry['transformation_notes']}")
                    if entry.get('batch_id'):
                        st.write(f"**Batch ID:** {entry['batch_id']}")
                        if entry.get('batch_index') is not None:
                            st.write(f"**Batch Position:** {entry['batch_index'] + 1}")
                
                with col2:
                    st.write(f"**Status:** {success_icon}")
                    if entry.get('confidence_score'):
                        st.write(f"**Confidence:** {entry['confidence_score']:.1%}")
                    st.write(f"**Parameter:** {entry.get('parameter', 'Unknown')}")
                    st.write(f"**Approach:** {entry.get('approach', 'Unknown')}")
                    
                    # Show quality metrics if available
                    if entry.get('quality_score'):
                        quality = entry['quality_score']
                        if isinstance(quality, dict) and 'overall_score' in quality:
                            st.write(f"**Quality:** {quality['overall_score']:.1%}")
        
        # Clear history options
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear All History", help="Clear all transformation history"):
                st.session_state[self.session_key]['transformation_history'] = []
                st.success("Transformation history cleared!")
                st.rerun()
        
        with col2:
            if st.button("📤 Export History", help="Export transformation history to file"):
                self._export_transformation_history(history)
    
    def _render_lineage_tree(self, lineage: Dict[str, Any]):
        """Render transformation lineage tree."""
        st.markdown("**Transformation Lineage:**")
        
        if not lineage:
            st.info("No lineage data available. Lineage tracking shows parent-child relationships between transformations.")
            return
        
        # Build lineage tree structure
        roots = []  # Objects with no parents
        children = {}  # parent_id -> [child_ids]
        
        for obj_id, lineage_data in lineage.items():
            parent_id = lineage_data.get('parent_id')
            
            if not parent_id:
                roots.append(obj_id)
            else:
                if parent_id not in children:
                    children[parent_id] = []
                children[parent_id].append(obj_id)
        
        # Display lineage trees
        if roots:
            st.write("**Transformation Trees:**")
            
            for root_id in roots:
                self._display_lineage_node(root_id, lineage, children, level=0)
        else:
            st.info("No root objects found in lineage data.")
        
        # Lineage statistics
        st.markdown("**Lineage Statistics:**")
        
        total_objects = len(lineage)
        root_objects = len(roots)
        max_depth = self._calculate_max_lineage_depth(lineage, children)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Objects", total_objects)
        with col2:
            st.metric("Root Objects", root_objects)
        with col3:
            st.metric("Max Depth", max_depth)
    
    def _display_lineage_node(self, obj_id: str, lineage: Dict[str, Any], 
                            children: Dict[str, List[str]], level: int = 0):
        """Display a single node in the lineage tree."""
        indent = "  " * level
        lineage_data = lineage.get(obj_id, {})
        
        # Get object information
        title = lineage_data.get('title', 'Unknown')
        obj_type = lineage_data.get('object_type', 'Unknown')
        transformation_type = lineage_data.get('transformation_type', '')
        timestamp = lineage_data.get('timestamp', '')
        
        # Create node display
        if level == 0:
            icon = "🌱"  # Root
        else:
            icon = "🔄"  # Transformed
        
        node_text = f"{indent}{icon} **{title}** ({obj_type})"
        if transformation_type:
            node_text += f" ← {transformation_type}"
        if timestamp:
            node_text += f" ({timestamp})"
        
        st.write(node_text)
        
        # Display children recursively
        if obj_id in children:
            for child_id in children[obj_id]:
                self._display_lineage_node(child_id, lineage, children, level + 1)
    
    def _calculate_max_lineage_depth(self, lineage: Dict[str, Any], 
                                   children: Dict[str, List[str]]) -> int:
        """Calculate the maximum depth of the lineage tree."""
        def get_depth(obj_id: str, current_depth: int = 0) -> int:
            if obj_id not in children:
                return current_depth
            
            max_child_depth = current_depth
            for child_id in children[obj_id]:
                child_depth = get_depth(child_id, current_depth + 1)
                max_child_depth = max(max_child_depth, child_depth)
            
            return max_child_depth
        
        # Find roots and calculate depth from each
        roots = []
        for obj_id, lineage_data in lineage.items():
            if not lineage_data.get('parent_id'):
                roots.append(obj_id)
        
        if not roots:
            return 0
        
        max_depth = 0
        for root_id in roots:
            depth = get_depth(root_id)
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _export_transformation_history(self, history: List[Dict[str, Any]]):
        """Export transformation history to file."""
        try:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_entries': len(history),
                'transformations': history
            }
            
            json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            st.download_button(
                label="📥 Download History (JSON)",
                data=json_data,
                file_name=f"transformation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                help="Download complete transformation history as JSON file"
            )
            
            st.success("History export prepared! Click the download button above.")
            
        except Exception as e:
            st.error(f"Export error: {str(e)}")
            logger.error(f"History export error: {e}")
    
    def _render_transformation_suggestions(self, source_objects: Optional[List[CodexObject]]) -> Dict[str, Any]:
        """Render transformation suggestions interface."""
        st.markdown("#### 💡 Transformation Suggestions")
        
        if not source_objects:
            st.info("Select objects to see transformation suggestions.")
            return {}
        
        suggestions_generated = []
        
        for obj in source_objects[:3]:  # Limit to first 3 objects for performance
            st.write(f"**Suggestions for: {obj.title}**")
            
            suggestions = self._get_transformation_suggestions(obj)
            
            if suggestions:
                for suggestion in suggestions:
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**{suggestion['target_type'].value.title()}**")
                    
                    with col2:
                        st.write(suggestion['reason'])
                    
                    with col3:
                        if st.button(
                            "Apply",
                            key=f"suggest_{obj.uuid}_{suggestion['target_type'].value}",
                            help=f"Transform to {suggestion['target_type'].value.title()}"
                        ):
                            # Execute suggested transformation
                            with st.spinner("Applying suggestion..."):
                                result = self._execute_single_transformation(
                                    obj,
                                    suggestion['target_type'],
                                    'planning',  # Default approach
                                    suggestion.get('parameter', 'expand'),
                                    f"Suggested transformation: {suggestion['reason']}"
                                )
                                
                                if result:
                                    st.success(f"Successfully transformed to {suggestion['target_type'].value.title()}!")
                                    suggestions_generated.append(result)
            else:
                st.write("No specific suggestions available for this content type.")
            
            st.markdown("---")
        
        return {'suggestions_applied': len(suggestions_generated)}
    
    def _render_file_upload_input(self) -> List[CodexObject]:
        """Render file upload interface for transformation input."""
        uploaded_files = st.file_uploader(
            "Upload files for transformation",
            type=['txt', 'docx', 'pdf', 'md', 'rtf'],
            accept_multiple_files=True,
            key="transform_upload",
            help="Upload files to transform to different content types"
        )
        
        if uploaded_files:
            objects = []
            
            for uploaded_file in uploaded_files:
                try:
                    content = self.file_handler.extract_content(uploaded_file)
                    detected_type, confidence = self.content_detector.detect_type(content)
                    
                    obj = CodexObject(
                        content=content,
                        object_type=detected_type,
                        title=uploaded_file.name,
                        word_count=len(content.split())
                    )
                    objects.append(obj)
                    
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            
            if objects:
                st.success(f"Loaded {len(objects)} objects from uploaded files")
            
            return objects
        
        return []
    
    def _render_text_input(self) -> List[CodexObject]:
        """Render text input interface for transformation."""
        content = st.text_area(
            "Content to transform:",
            placeholder="Enter content to transform to a different type...",
            height=200,
            key="transform_text_input",
            help="Enter content directly to transform to a different content type"
        )
        
        if content.strip():
            detected_type, confidence = self.content_detector.detect_type(content)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                title = st.text_input(
                    "Title for this content:",
                    value="Direct Input",
                    key="transform_text_title"
                )
            with col2:
                st.write(f"**Detected Type:** {detected_type.value.title()}")
                st.write(f"**Confidence:** {confidence:.1%}")
            
            obj = CodexObject(
                content=content,
                object_type=detected_type,
                title=title,
                word_count=len(content.split())
            )
            
            return [obj]
        
        return []
    
    def _show_transformation_preview(self, source_obj: CodexObject, target_type: CodexObjectType, parameter: str):
        """Show a preview of what the transformation will do."""
        st.markdown("**Transformation Preview:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Before:**")
            st.write(f"Type: {source_obj.object_type.value.title()}")
            st.write(f"Words: {source_obj.word_count}")
            preview = source_obj.content[:150] + "..." if len(source_obj.content) > 150 else source_obj.content
            st.text_area("Content:", value=preview, height=100, disabled=True, key="preview_before")
        
        with col2:
            st.write("**After (Preview):**")
            st.write(f"Type: {target_type.value.title()}")
            
            # Generate preview based on parameter
            if parameter == 'expand':
                estimated_words = int(source_obj.word_count * 1.5)
                preview_text = f"This {source_obj.object_type.value} will be expanded into a detailed {target_type.value} with additional context, character development, and plot details."
            elif parameter == 'condense':
                estimated_words = int(source_obj.word_count * 0.6)
                preview_text = f"This {source_obj.object_type.value} will be condensed into a focused {target_type.value} highlighting the essential elements."
            elif parameter == 'restructure':
                estimated_words = source_obj.word_count
                preview_text = f"This {source_obj.object_type.value} will be restructured into {target_type.value} format while maintaining the core content."
            else:  # enhance
                estimated_words = int(source_obj.word_count * 1.2)
                preview_text = f"This {source_obj.object_type.value} will be enhanced with improved detail and clarity as a {target_type.value}."
            
            st.write(f"Estimated Words: ~{estimated_words}")
            st.text_area("Expected Result:", value=preview_text, height=100, disabled=True, key="preview_after")
    
    def _execute_single_transformation(self, source_obj: CodexObject, target_type: CodexObjectType,
                                     approach: str, parameter: str, custom_instructions: str) -> Optional[Dict[str, Any]]:
        """Execute a single transformation with lineage tracking."""
        try:
            # For now, implement a simple transformation (type change)
            # In a full implementation, this would use the transformation engine
            transformed_obj = CodexObject(
                content=source_obj.content,
                object_type=target_type,
                title=source_obj.title,
                word_count=source_obj.word_count,
                genre=source_obj.genre,
                target_audience=source_obj.target_audience
            )
            
            # Track lineage relationship
            self._track_transformation_lineage(source_obj, transformed_obj, approach, parameter)
            
            # Store in history
            history_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source_type': source_obj.object_type.value,
                'target_type': target_type.value,
                'source_title': source_obj.title,
                'result_title': transformed_obj.title,
                'source_uuid': source_obj.uuid,
                'result_uuid': transformed_obj.uuid,
                'success': True,
                'confidence_score': 0.8,
                'transformation_notes': f"Transformed from {source_obj.object_type.value} to {target_type.value}",
                'parameter': parameter,
                'approach': approach,
                'custom_instructions': custom_instructions
            }
            
            try:
                st.session_state[self.session_key]['transformation_history'].append(history_entry)
            except Exception as e:
                logger.warning(f"Could not save to history: {e}")
                # Continue without saving to history
            
            return {
                'source_object': source_obj,
                'transformed_object': transformed_obj,
                'success': True,
                'confidence_score': 0.8,
                'transformation_notes': f"Transformed from {source_obj.object_type.value} to {target_type.value}"
            }
        
        except Exception as e:
            logger.error(f"Error in transformation: {e}")
            st.error(f"Transformation error: {str(e)}")
            return None
    
    def _track_transformation_lineage(self, source_obj: CodexObject, transformed_obj: CodexObject,
                                    approach: str, parameter: str):
        """Track lineage relationship between source and transformed objects."""
        try:
            lineage = st.session_state[self.session_key]['transformation_lineage']
            
            # Add source object to lineage if not already present
            if source_obj.uuid not in lineage:
                lineage[source_obj.uuid] = {
                    'title': source_obj.title,
                    'object_type': source_obj.object_type.value,
                    'created_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'parent_id': None,  # Root object
                    'children': []
                }
            
            # Add transformed object to lineage
            lineage[transformed_obj.uuid] = {
                'title': transformed_obj.title,
                'object_type': transformed_obj.object_type.value,
                'created_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'parent_id': source_obj.uuid,
                'transformation_type': f"{approach} {parameter}",
                'transformation_approach': approach,
                'transformation_parameter': parameter,
                'children': []
            }
            
            # Update parent's children list
            if source_obj.uuid in lineage:
                if transformed_obj.uuid not in lineage[source_obj.uuid]['children']:
                    lineage[source_obj.uuid]['children'].append(transformed_obj.uuid)
            
        except Exception as e:
            logger.warning(f"Could not track lineage: {e}")
            # Continue without lineage tracking
    
    def _display_transformation_results(self, results: List[Dict[str, Any]]):
        """Display transformation results."""
        st.markdown("### 🎉 Transformation Results")
        
        for i, result in enumerate(results):
            source_obj = result['source_object']
            transformed_obj = result['transformed_object']
            
            with st.expander(
                f"✨ {source_obj.title} → {transformed_obj.object_type.value.title()}",
                expanded=True
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Original:**")
                    st.write(f"Type: {source_obj.object_type.value.title()}")
                    st.write(f"Words: {source_obj.word_count}")
                    st.text_area(
                        "Original Content:",
                        value=source_obj.content,
                        height=200,
                        disabled=True,
                        key=f"original_{i}"
                    )
                
                with col2:
                    st.markdown("**Transformed:**")
                    st.write(f"Type: {transformed_obj.object_type.value.title()}")
                    st.write(f"Words: {transformed_obj.word_count}")
                    if result.get('confidence_score'):
                        st.write(f"Confidence: {result['confidence_score']:.1%}")
                    
                    st.text_area(
                        "Transformed Content:",
                        value=transformed_obj.content,
                        height=200,
                        disabled=True,
                        key=f"transformed_{i}"
                    )
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"💾 Save Result", key=f"save_{i}"):
                        # Add to session state for use in other components
                        if 'created_objects' not in st.session_state:
                            st.session_state['created_objects'] = []
                        st.session_state['created_objects'].append(transformed_obj)
                        st.success("Result saved to object collection!")
                
                with col2:
                    if st.button(f"📋 Copy Content", key=f"copy_{i}"):
                        st.code(transformed_obj.content, language="text")
                        st.info("Content displayed above for copying")
                
                with col3:
                    if st.button(f"🔄 Transform Again", key=f"retransform_{i}"):
                        st.info("Use the transformation interface above to transform this result further")
    
    def _get_transformation_suggestions(self, obj: CodexObject) -> List[Dict[str, Any]]:
        """Get transformation suggestions for an object."""
        suggestions = []
        
        current_type = obj.object_type
        
        # Define common transformation paths
        if current_type == CodexObjectType.IDEA:
            suggestions.extend([
                {
                    'target_type': CodexObjectType.LOGLINE,
                    'reason': 'Develop into focused logline',
                    'parameter': 'condense'
                },
                {
                    'target_type': CodexObjectType.SYNOPSIS,
                    'reason': 'Expand into full synopsis',
                    'parameter': 'expand'
                },
                {
                    'target_type': CodexObjectType.OUTLINE,
                    'reason': 'Structure into story outline',
                    'parameter': 'restructure'
                }
            ])
        
        elif current_type == CodexObjectType.LOGLINE:
            suggestions.extend([
                {
                    'target_type': CodexObjectType.SYNOPSIS,
                    'reason': 'Develop into comprehensive synopsis',
                    'parameter': 'expand'
                },
                {
                    'target_type': CodexObjectType.TREATMENT,
                    'reason': 'Expand into detailed treatment',
                    'parameter': 'expand'
                }
            ])
        
        elif current_type == CodexObjectType.SYNOPSIS:
            suggestions.extend([
                {
                    'target_type': CodexObjectType.OUTLINE,
                    'reason': 'Structure into detailed outline',
                    'parameter': 'restructure'
                },
                {
                    'target_type': CodexObjectType.TREATMENT,
                    'reason': 'Expand into full treatment',
                    'parameter': 'expand'
                },
                {
                    'target_type': CodexObjectType.LOGLINE,
                    'reason': 'Condense to essential logline',
                    'parameter': 'condense'
                }
            ])
        
        elif current_type == CodexObjectType.OUTLINE:
            suggestions.extend([
                {
                    'target_type': CodexObjectType.DRAFT,
                    'reason': 'Begin writing first draft',
                    'parameter': 'expand'
                },
                {
                    'target_type': CodexObjectType.TREATMENT,
                    'reason': 'Convert to narrative treatment',
                    'parameter': 'restructure'
                }
            ])
        
        # Add enhancement suggestion for all types
        suggestions.append({
            'target_type': current_type,
            'reason': f'Enhance current {current_type.value} with more detail',
            'parameter': 'enhance'
        })
        
        return suggestions[:4]  # Limit to 4 suggestions