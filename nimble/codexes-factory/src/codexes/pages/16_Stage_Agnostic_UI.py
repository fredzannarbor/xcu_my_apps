"""
Stage-Agnostic UI Page

Universal interface for creating and managing creative content of any type.
This page provides a stage/length-agnostic approach to content creation.
"""

import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Add the project root to Python path for proper imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add the src directory to Python path
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from codexes.ui.components.universal_input import UniversalContentInput
from codexes.ui.config.model_config import ModelConfigManager
from codexes.ui.components.transformation_interface import TransformationInterface
from codexes.ui.components.workflow_selector import WorkflowSelector
from codexes.ui.components.imprint_ideation_bridge import ImprintIdeationBridge, IntegrationMode

def main():
    """Main function for the Stage-Agnostic UI page."""
    st.set_page_config(
        page_title="Stage-Agnostic UI",
        page_icon="🎯",
        layout="wide"
    )

    # Page header
    st.title("🎯 Stage-Agnostic Content Management")
    st.markdown("""
    Welcome to the intelligent content interface! This system automatically detects and adapts to any type of creative content,
    whether you're working with ideas, synopses, outlines, drafts, or complete manuscripts.
    
    ✨ **New Features:**
    - 🔍 **Intelligent Content Detection** - Automatically identifies content type with confidence scores
    - 🤖 **LLM-Powered Analysis** - Optional AI-powered content classification
    - 📊 **Detection Insights** - Detailed reasoning and content statistics
    """)
    
    # Initialize components
    universal_input = UniversalContentInput()
    model_config = ModelConfigManager()
    
    # Initialize imprint bridge with error handling
    try:
        imprint_bridge = ImprintIdeationBridge()
    except Exception as e:
        st.error(f"Failed to initialize ImprintIdeationBridge: {str(e)}")
        imprint_bridge = None
    
    # Initialize transformation interface with error handling
    try:
        transformation_interface = TransformationInterface()
    except Exception as e:
        st.error(f"Failed to initialize TransformationInterface: {str(e)}")
        transformation_interface = None
    
    # Initialize workflow selector with error handling
    try:
        workflow_selector = WorkflowSelector()
    except Exception as e:
        st.error(f"Failed to initialize WorkflowSelector: {str(e)}")
        workflow_selector = None
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Create Content", "📚 Manage Objects", "🔄 Transform Content", "⚙️ Run Workflows", "🏢 Imprint Integration"])
    
    with tab1:
        st.markdown("### Universal Content Input")
        st.markdown("Enter any creative content below. The system will help you create a CodexObject that can be used throughout the ideation workflow.")
        
        # Render the intelligent input interface
        created_object = universal_input.render_intelligent_input_interface()
        
        if created_object:
            st.toast("Successfully created object")
    
    with tab2:
        st.markdown("### Your Created Objects")
        st.markdown("View, search, filter, and manage the CodexObjects you've created in this session.")
        
        # Display enhanced objects table
        table_result = universal_input.render_enhanced_objects_display()
        
        # Show session statistics
        state = st.session_state.get(universal_input.session_key, {})
        created_objects = state.get('created_objects', [])
        
        if created_objects:
            st.markdown("---")
            st.markdown("### 📊 Session Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Objects", len(created_objects))
            
            with col2:
                total_words = sum(obj.word_count for obj in created_objects)
                st.metric("Total Words", f"{total_words:,}")
            
            with col3:
                # Count by type
                type_counts = {}
                for obj in created_objects:
                    type_name = obj.object_type.value.title()
                    type_counts[type_name] = type_counts.get(type_name, 0) + 1
                most_common_type = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "None"
                st.metric("Most Common Type", most_common_type)
            
            with col4:
                avg_words = total_words / len(created_objects) if created_objects else 0
                st.metric("Avg Words/Object", f"{avg_words:.0f}")
            
            # Additional statistics
            if len(created_objects) > 1:
                with st.expander("📈 Detailed Statistics", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Content Types:**")
                        for content_type, count in type_counts.items():
                            percentage = (count / len(created_objects)) * 100
                            st.write(f"• {content_type}: {count} ({percentage:.1f}%)")
                    
                    with col2:
                        st.write("**Content Analysis:**")
                        # Genre distribution
                        genre_counts = {}
                        for obj in created_objects:
                            genre = getattr(obj, 'genre', 'Not Specified')
                            if genre and genre != 'Not Specified':
                                genre_counts[genre] = genre_counts.get(genre, 0) + 1
                        
                        if genre_counts:
                            st.write("**Genres:**")
                            for genre, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                                st.write(f"• {genre}: {count}")
                        else:
                            st.write("No genre information available")
    
    with tab3:
        st.markdown("### 🔄 Content Transformation")
        st.markdown("Transform your content between different types (e.g., idea → synopsis → outline → draft).")
        
        # Get selected objects from the manage objects tab
        state = st.session_state.get(universal_input.session_key, {})
        created_objects = state.get('created_objects', [])
        
        # Get selected objects from the data table if available
        selected_objects = []
        if 'object_datatable_state' in st.session_state:
            datatable_state = st.session_state['object_datatable_state']
            selected_indices = datatable_state.get('selected_objects', set())
            selected_objects = [created_objects[i] for i in selected_indices if i < len(created_objects)]
        
        # If no objects are specifically selected, pass all created objects for transformation
        objects_for_transformation = selected_objects if selected_objects else created_objects
        
        if transformation_interface is None:
            st.error("❌ Transformation interface failed to initialize. Please refresh the page.")
        elif not created_objects:
            st.info("📝 Create some content in the 'Create Content' tab first, then return here to transform it.")
        else:
            # Show available objects info
            if selected_objects:
                st.info(f"🎯 {len(selected_objects)} objects selected for transformation")
            else:
                st.info(f"📚 {len(created_objects)} objects available for transformation")
            
            # Show transformation interface
            try:
                transformation_results = transformation_interface.render_transformation_interface(objects_for_transformation)
            except Exception as e:
                st.error(f"Error loading transformation interface: {str(e)}")
                st.write("Please refresh the page or check the browser console for more details.")
                import traceback
                st.code(traceback.format_exc())
                transformation_results = {}
            
            # Display any transformation results
            if transformation_results:
                # Add transformed objects to the session
                for key, result in transformation_results.items():
                    if isinstance(result, dict) and 'transformed_object' in result:
                        transformed_obj = result['transformed_object']
                        if transformed_obj not in created_objects:
                            created_objects.append(transformed_obj)
                            st.session_state[universal_input.session_key]['created_objects'] = created_objects
                    elif isinstance(result, list):
                        for item in result:
                            if isinstance(item, dict) and 'transformed_object' in item:
                                transformed_obj = item['transformed_object']
                                if transformed_obj not in created_objects:
                                    created_objects.append(transformed_obj)
                                    st.session_state[universal_input.session_key]['created_objects'] = created_objects
    
    with tab4:
        st.markdown("### ⚙️ Advanced Workflow Interface")
        st.markdown("Run sophisticated workflows with mixed content types, analytics, templates, export, and automation.")
        
        # Get created objects for workflow processing
        state = st.session_state.get(universal_input.session_key, {})
        created_objects = state.get('created_objects', [])
        
        if workflow_selector is None:
            st.error("❌ Workflow interface failed to initialize. Please refresh the page.")
        elif not created_objects:
            st.info("📝 Create some content in the 'Create Content' tab first, then return here to run workflows.")
        else:
            # Show enhanced workflow selection interface
            try:
                workflow_results = workflow_selector.render_workflow_selection_interface(created_objects)
                
                # Handle workflow results
                if workflow_results and workflow_results.get("success"):
                    # Add any generated objects back to the session
                    if "series_entries" in workflow_results:
                        series_entries = workflow_results["series_entries"]
                        for entry_data in series_entries:
                            # Convert series entry data back to CodexObject if needed
                            # This would require importing CodexObject and creating objects
                            pass
                    
                    st.success("✅ Advanced workflow completed successfully!")
                    
                    # Show quick analytics summary
                    if workflow_results.get("workflow_type") == "tournament":
                        tournament_results = workflow_results.get("tournament_results", {})
                        rankings = tournament_results.get("final_rankings", [])
                        if rankings:
                            winner = rankings[0]
                            st.info(f"🏆 Tournament Winner: {winner.get('title', 'Unknown')} (Score: {winner.get('final_score', 0):.3f})")
                    
                    elif workflow_results.get("workflow_type") == "reader_panel":
                        panel_results = workflow_results.get("panel_results", [])
                        if panel_results:
                            st.info(f"👥 Reader Panel completed: {len(panel_results)} objects evaluated")
                    
                    elif workflow_results.get("workflow_type") == "series_generation":
                        series_data = workflow_results.get("series_data", {})
                        series_entries = series_data.get("series_entries", [])
                        if series_entries:
                            total_words = sum(entry.get('word_count', 0) for entry in series_entries)
                            st.info(f"📚 Series Generated: {len(series_entries)} books, {total_words:,} total words")
                
            except Exception as e:
                st.error(f"Error loading advanced workflow interface: {str(e)}")
                st.write("Please refresh the page or check the browser console for more details.")
                import traceback
                st.code(traceback.format_exc())
    
    with tab5:
        st.markdown("### 🏢 Imprint Integration & Context")
        st.markdown("Select an imprint context and choose integration features to align your content with publishing brand guidelines.")
        
        if imprint_bridge is None:
            st.error("❌ Imprint bridge failed to initialize. Please refresh the page.")
        else:
            # Render imprint selection interface
            selected_imprint, selected_mode = imprint_bridge.render_imprint_selection_interface()
            
            # Store selections in session state
            if selected_imprint:
                st.session_state['selected_imprint'] = selected_imprint
            if selected_mode:
                st.session_state['selected_integration_mode'] = selected_mode
            
            # Show integration features based on selected mode
            if selected_imprint and selected_mode:
                st.markdown("---")
                
                # Get created objects for integration
                state = st.session_state.get(universal_input.session_key, {})
                created_objects = state.get('created_objects', [])
                
                if selected_mode == IntegrationMode.IMPRINT_DRIVEN:
                    st.markdown("### 🎨 Imprint-Driven Content Generation")
                    
                    if created_objects:
                        st.info(f"📚 {len(created_objects)} objects available for imprint alignment")
                        
                        # Select objects to apply imprint constraints
                        selected_for_alignment = st.multiselect(
                            "Select objects to align with imprint guidelines:",
                            options=range(len(created_objects)),
                            format_func=lambda i: f"{created_objects[i].title} ({created_objects[i].object_type.value.title()})",
                            help="Choose objects to apply imprint brand guidelines and constraints"
                        )
                        
                        if selected_for_alignment and st.button("🎯 Apply Imprint Guidelines", type="primary"):
                            aligned_objects = []
                            for idx in selected_for_alignment:
                                obj = created_objects[idx]
                                
                                # Apply imprint constraints
                                aligned_obj = imprint_bridge.apply_imprint_constraints(obj, selected_imprint)
                                
                                # Validate content
                                validation = imprint_bridge.validate_content_for_imprint(aligned_obj, selected_imprint)
                                st.session_state["validation_results"] = validation
                                
                                aligned_objects.append(aligned_obj)
                                
                                # Show validation results
                                with st.expander(f"✅ {aligned_obj.title} - Alignment Results"):
                                    if validation["valid"]:
                                        st.success("✅ Content aligns with imprint guidelines")
                                    else:
                                        st.error("❌ Content validation failed")
                                        for error in validation["errors"]:
                                            st.error(f"• {error}")
                                    
                                    if validation["warnings"]:
                                        st.warning("⚠️ Warnings:")
                                        for warning in validation["warnings"]:
                                            st.warning(f"• {warning}")
                                    
                                    if validation["suggestions"]:
                                        st.info("💡 Suggestions:")
                                        for suggestion in validation["suggestions"]:
                                            st.info(f"• {suggestion}")
                            
                            # Update objects in session
                            for i, idx in enumerate(selected_for_alignment):
                                created_objects[idx] = aligned_objects[i]
                            st.session_state[universal_input.session_key]['created_objects'] = created_objects
                            
                            st.success(f"✅ Applied imprint guidelines to {len(aligned_objects)} objects")
                    else:
                        st.info("📝 Create some content first to apply imprint guidelines")
                
                elif selected_mode == IntegrationMode.EXPORT_TO_PIPELINE:
                    st.markdown("### 📤 Export to Production Pipeline")
                    
                    if created_objects:
                        st.info(f"📚 {len(created_objects)} objects available for export")
                        
                        # Select objects to export
                        selected_for_export = st.multiselect(
                            "Select objects to export to production pipeline:",
                            options=range(len(created_objects)),
                            format_func=lambda i: f"{created_objects[i].title} ({created_objects[i].object_type.value.title()})",
                            help="Choose objects to convert to book production format"
                        )
                        
                        if selected_for_export:
                            # Show export preview
                            with st.expander("📋 Export Preview", expanded=True):
                                st.write("**Objects to export:**")
                                for idx in selected_for_export:
                                    obj = created_objects[idx]
                                    st.write(f"• {obj.title} ({obj.object_type.value.title()}) - {obj.word_count} words")
                            
                            if st.button("🚀 Export to Pipeline", type="primary"):
                                objects_to_export = [created_objects[i] for i in selected_for_export]
                                export_results = imprint_bridge.export_to_pipeline(objects_to_export, selected_imprint)
                                
                                if export_results["success"]:
                                    st.success(f"✅ Successfully exported {len(export_results['exported_objects'])} objects")
                                    
                                    # Show export details
                                    with st.expander("📊 Export Details", expanded=True):
                                        for export_obj in export_results["exported_objects"]:
                                            col1, col2 = st.columns([2, 1])
                                            with col1:
                                                st.write(f"**{export_obj['title']}**")
                                                if export_obj["pipeline_ready"]:
                                                    st.success("✅ Pipeline ready")
                                                else:
                                                    st.error("❌ Needs attention")
                                            with col2:
                                                st.write(f"UUID: `{export_obj['codex_object_uuid'][:8]}...`")
                                    
                                    # Show warnings if any
                                    if export_results["warnings"]:
                                        st.warning("⚠️ Export Warnings:")
                                        for warning in export_results["warnings"]:
                                            st.warning(f"• {warning}")
                                else:
                                    st.error(f"❌ Export failed: {export_results.get('error', 'Unknown error')}")
                    else:
                        st.info("📝 Create some content first to export to the pipeline")
                
                elif selected_mode == IntegrationMode.BIDIRECTIONAL_SYNC:
                    st.markdown("### 🔄 Bidirectional Synchronization")
                    st.info("🚧 Bidirectional sync is a planned feature for future releases")
                    
                    st.markdown("""
                    **Planned Features:**
                    - Real-time metadata synchronization between ideation and production
                    - Production status updates reflected in ideation system
                    - Cross-system content tracking and lineage
                    - Unified workflow management across both systems
                    """)
                    
                    if created_objects:
                        st.write(f"📚 {len(created_objects)} objects would be available for sync")
            
            elif selected_imprint and not selected_mode:
                # Show imprint guidance for content creation
                st.markdown("---")
                st.markdown("### 📋 Content Creation Guidance")
                
                # Show guidance for different content types
                content_type_tabs = st.tabs(["💡 Ideas", "📖 Synopses", "📝 Outlines", "✍️ Drafts"])
                
                from codexes.modules.ideation.core.codex_object import CodexObjectType
                
                with content_type_tabs[0]:
                    imprint_bridge.render_imprint_guidance(selected_imprint, CodexObjectType.IDEA)
                
                with content_type_tabs[1]:
                    imprint_bridge.render_imprint_guidance(selected_imprint, CodexObjectType.SYNOPSIS)
                
                with content_type_tabs[2]:
                    imprint_bridge.render_imprint_guidance(selected_imprint, CodexObjectType.OUTLINE)
                
                with content_type_tabs[3]:
                    imprint_bridge.render_imprint_guidance(selected_imprint, CodexObjectType.DRAFT)
    
    # Footer with helpful information
    st.markdown("---")
    with st.expander("ℹ️ About Stage-Agnostic UI"):
        st.markdown("""
        **What is Stage-Agnostic UI?**
        
        This interface is designed to work with creative content at any stage of development:
        
        - **Ideas**: Brief concepts or premises (usually 1-3 sentences)
        - **Loglines**: One-sentence story summaries
        - **Summaries**: Brief story overviews (1-2 paragraphs)
        - **Synopses**: Detailed story summaries (multiple paragraphs)
        - **Outlines**: Structured story breakdowns with scenes/chapters
        - **Drafts**: Partial or complete manuscript text
        - **Manuscripts**: Complete story text
        
        **Key Features:**
        - Universal input that accepts any content type
        - Automatic content analysis and suggestions
        - Seamless integration with ideation workflows
        - Progressive enhancement as content matures
        
        **Current Features:**
        - ✅ **Intelligent Content Detection** - Automatic type detection with confidence scores
        - ✅ **Advanced Filtering & Search** - Powerful search with field filters and saved presets
        - ✅ **Content Transformation** - Transform content between different types with AI assistance
        - ✅ **Universal Workflow Interface** - Run tournaments, reader panels, and series generation
        - ✅ **Mixed-Type Handling** - Intelligent adaptation for workflows with different content types
        - ✅ **Rule-based Classification** - Fast, accurate detection using content analysis
        - ✅ **LLM-powered Analysis** - Optional AI model integration for sophisticated detection
        - ✅ **Manual Override** - Full control when you need it
        
        **Advanced Workflow Features:**
        - 🏆 **Tournaments** - Competitive evaluation with sophisticated mixed-type algorithms
        - 👥 **Reader Panels** - Synthetic reader evaluation with demographic targeting
        - 📚 **Series Generation** - Create book series with configurable consistency levels
        - 🔧 **Mixed-Type Evaluation** - Fair comparison algorithms for different content types
        - 📊 **Advanced Analytics** - Comprehensive insights, visualizations, and performance analysis
        - 📋 **Workflow Templates** - Save and reuse workflow configurations
        - 📤 **Export & Sharing** - Multiple export formats and sharing options
        - 🤖 **Automation** - Schedule workflows and automate repetitive tasks
        - ⚖️ **Fairness Algorithms** - Developmental scaling and bias detection
        - 📈 **Performance Insights** - Type-aware analysis and recommendations
        
        **Imprint Integration Features:**
        - 🏢 **Imprint Selection** - Choose from available publishing imprints with brand context
        - 🎨 **Imprint-Driven Content** - Generate content aligned with brand guidelines and constraints
        - 📤 **Export to Pipeline** - Convert ideation outputs to book production pipeline format
        - 🔄 **Bidirectional Sync** - Full synchronization between ideation and production systems (planned)
        - 📋 **Brand Guidelines** - Automatic constraint validation and content recommendations
        - ✅ **Content Validation** - Ensure content aligns with imprint requirements and standards
        """)

if __name__ == "__main__":
    main()