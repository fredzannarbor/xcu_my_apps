"""
Universal Content Input Component

Provides a universal input interface that accepts any creative content
and creates CodexObjects with minimal metadata.
"""

from typing import List, Optional
import streamlit as st
from datetime import datetime

from ..core.simple_codex_object import SimpleCodexObject as CodexObject, CodexObjectType


class UniversalContentInput:
    """Universal content input component that accepts any content type."""
    
    def __init__(self):
        self.session_key = "universal_input_state"
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state for the component."""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                'created_objects': [],
                'last_content': '',
                'object_counter': 0
            }
    
    def render_basic_input_interface(self) -> Optional[CodexObject]:
        """Render the basic text input interface."""
        st.subheader("📝 Universal Content Input")
        st.write("Enter any creative content: ideas, synopses, outlines, drafts...")
        
        # Main content input
        content = st.text_area(
            "Content", 
            placeholder="Enter any creative content here...\n\nExamples:\n- A story about time travel\n- Chapter 1: The Discovery...\n- Plot outline with three acts\n- Character development notes",
            height=200,
            help="The system accepts any type of creative content and will create a CodexObject for you."
        )
        
        if content and content.strip():
            # Basic metadata input
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input(
                    "Title (optional)",
                    value=self._suggest_title(content),
                    help="Give your content a title, or leave blank for auto-generation"
                )
            
            with col2:
                # Simple content type selection for now
                content_type = st.selectbox(
                    "Content Type",
                    options=[
                        CodexObjectType.IDEA,
                        CodexObjectType.LOGLINE,
                        CodexObjectType.SUMMARY,
                        CodexObjectType.SYNOPSIS,
                        CodexObjectType.OUTLINE,
                        CodexObjectType.DRAFT,
                        CodexObjectType.MANUSCRIPT
                    ],
                    format_func=lambda x: x.value.title(),
                    help="Select the type of content you're creating"
                )
            
            # Create CodexObject button
            if st.button("Create CodexObject", type="primary"):
                codex_object = self._create_codex_object(content, content_type, title)
                
                # Store in session state
                state = st.session_state[self.session_key]
                state['created_objects'].append(codex_object)
                state['object_counter'] += 1
                
                st.success(f"✅ Created CodexObject: {codex_object.title}")
                return codex_object
        
        return None
    
    def render_created_objects_display(self):
        """Display recently created objects."""
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
    
    def _create_codex_object(self, content: str, content_type: CodexObjectType, title: str) -> CodexObject:
        """Create a CodexObject from input data."""
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