"""
Object DataTable Component

Efficient display and management of CodexObject collections with sorting, filtering, and bulk operations.
"""

from typing import List, Dict, Any, Optional, Set
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from ..core.simple_codex_object import SimpleCodexObject as CodexObject, CodexObjectType
from .content_filter import ContentFilter


class ObjectDataTable:
    """Data table component for managing CodexObject collections."""
    
    def __init__(self):
        self.session_key = "object_datatable_state"
        self.content_filter = ContentFilter()
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state for the data table."""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                'selected_objects': set(),
                'sort_column': 'created_timestamp',
                'sort_ascending': False,
                'filters': {},
                'search_query': '',
                'page_size': 10,
                'current_page': 0
            }
    
    def render_object_table(self, objects: List[CodexObject]) -> Dict[str, Any]:
        """
        Render the object data table with filtering, sorting, and selection.
        
        Returns:
            Dict containing selected objects and table actions
        """
        if not objects:
            st.info("📝 No objects to display. Create some content to see it here!")
            return {'selected_objects': [], 'actions': {}}
        
        st.markdown("### 📚 Object Collection")
        
        # Render advanced filters first
        advanced_filters = self.content_filter.render_advanced_filters(objects)
        
        # Apply advanced filters to objects
        filtered_objects = self.content_filter.apply_filters(objects, advanced_filters)
        
        # Convert filtered objects to DataFrame
        df = self._objects_to_dataframe(filtered_objects)
        
        # Render filters and search
        filtered_df = self._render_filters_and_search(df)
        
        # Render table controls
        table_controls = self._render_table_controls(filtered_df)
        
        # Render the main data table
        selected_objects = self._render_data_table(filtered_df, filtered_objects)
        
        # Render bulk actions
        bulk_actions = self._render_bulk_actions(selected_objects)
        
        return {
            'selected_objects': selected_objects,
            'actions': bulk_actions,
            'table_controls': table_controls
        }
    
    def _objects_to_dataframe(self, objects: List[CodexObject]) -> pd.DataFrame:
        """Convert CodexObject list to pandas DataFrame."""
        data = []
        
        for i, obj in enumerate(objects):
            # Parse timestamp
            try:
                created_date = datetime.fromisoformat(obj.created_timestamp.replace('Z', '+00:00'))
                created_str = created_date.strftime('%Y-%m-%d %H:%M')
            except:
                created_str = obj.created_timestamp[:16] if obj.created_timestamp else 'Unknown'
            
            # Get additional metadata
            genre = getattr(obj, 'genre', '') or 'Not Specified'
            audience = getattr(obj, 'target_audience', '') or 'Not Specified'
            
            # Calculate content preview
            content_preview = obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
            
            data.append({
                'index': i,
                'title': obj.title,
                'type': obj.object_type.value.title(),
                'genre': genre,
                'audience': audience,
                'word_count': obj.word_count,
                'created': created_str,
                'created_timestamp': obj.created_timestamp,
                'content_preview': content_preview,
                'full_content': obj.content
            })
        
        return pd.DataFrame(data)
    
    def _render_filters_and_search(self, df: pd.DataFrame) -> pd.DataFrame:
        """Render filter controls and apply filtering."""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            # Search box
            search_query = st.text_input(
                "🔍 Search objects",
                value=st.session_state[self.session_key]['search_query'],
                placeholder="Search titles, content, or metadata...",
                key="object_search"
            )
            st.session_state[self.session_key]['search_query'] = search_query
        
        with col2:
            # Type filter
            available_types = ['All Types'] + sorted(df['type'].unique().tolist())
            type_filter = st.selectbox(
                "Filter by Type",
                options=available_types,
                key="type_filter"
            )
        
        with col3:
            # Genre filter
            available_genres = ['All Genres'] + sorted([g for g in df['genre'].unique() if g != 'Not Specified'])
            genre_filter = st.selectbox(
                "Filter by Genre", 
                options=available_genres,
                key="genre_filter"
            )
        
        # Apply filters
        filtered_df = df.copy()
        
        # Apply search filter
        if search_query:
            search_mask = (
                df['title'].str.contains(search_query, case=False, na=False) |
                df['content_preview'].str.contains(search_query, case=False, na=False) |
                df['genre'].str.contains(search_query, case=False, na=False) |
                df['audience'].str.contains(search_query, case=False, na=False)
            )
            filtered_df = filtered_df[search_mask]
        
        # Apply type filter
        if type_filter != 'All Types':
            filtered_df = filtered_df[filtered_df['type'] == type_filter]
        
        # Apply genre filter
        if genre_filter != 'All Genres':
            filtered_df = filtered_df[filtered_df['genre'] == genre_filter]
        
        return filtered_df
    
    def _render_table_controls(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Render table control options."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Sort options
            sort_options = {
                'Title': 'title',
                'Type': 'type', 
                'Genre': 'genre',
                'Word Count': 'word_count',
                'Created Date': 'created_timestamp'
            }
            
            sort_by = st.selectbox(
                "Sort by",
                options=list(sort_options.keys()),
                index=list(sort_options.values()).index(st.session_state[self.session_key]['sort_column']),
                key="sort_by"
            )
            st.session_state[self.session_key]['sort_column'] = sort_options[sort_by]
        
        with col2:
            # Sort direction
            sort_ascending = st.checkbox(
                "Ascending",
                value=st.session_state[self.session_key]['sort_ascending'],
                key="sort_ascending"
            )
            st.session_state[self.session_key]['sort_ascending'] = sort_ascending
        
        with col3:
            # Page size
            page_size = st.selectbox(
                "Items per page",
                options=[5, 10, 20, 50, 100],
                index=[5, 10, 20, 50, 100].index(st.session_state[self.session_key]['page_size']),
                key="page_size"
            )
            st.session_state[self.session_key]['page_size'] = page_size
        
        with col4:
            # Results info
            st.metric("Total Objects", len(df))
        
        return {
            'sort_column': st.session_state[self.session_key]['sort_column'],
            'sort_ascending': sort_ascending,
            'page_size': page_size
        }
    
    def _render_data_table(self, df: pd.DataFrame, original_objects: List[CodexObject]) -> List[CodexObject]:
        """Render the main data table with selection."""
        if df.empty:
            st.info("No objects match the current filters.")
            return []
        
        # Apply sorting
        sort_column = st.session_state[self.session_key]['sort_column']
        sort_ascending = st.session_state[self.session_key]['sort_ascending']
        
        if sort_column in df.columns:
            df_sorted = df.sort_values(sort_column, ascending=sort_ascending)
        else:
            df_sorted = df
        
        # Apply pagination
        page_size = st.session_state[self.session_key]['page_size']
        total_pages = (len(df_sorted) - 1) // page_size + 1
        
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if st.button("◀ Previous", disabled=st.session_state[self.session_key]['current_page'] == 0):
                    st.session_state[self.session_key]['current_page'] -= 1
                    st.rerun()
            
            with col2:
                current_page = st.session_state[self.session_key]['current_page']
                st.write(f"Page {current_page + 1} of {total_pages}")
            
            with col3:
                if st.button("Next ▶", disabled=st.session_state[self.session_key]['current_page'] >= total_pages - 1):
                    st.session_state[self.session_key]['current_page'] += 1
                    st.rerun()
        
        # Get current page data
        current_page = st.session_state[self.session_key]['current_page']
        start_idx = current_page * page_size
        end_idx = start_idx + page_size
        page_df = df_sorted.iloc[start_idx:end_idx]
        
        # Render table with selection
        selected_objects = []
        
        # Select all checkbox
        col1, col2 = st.columns([1, 10])
        with col1:
            select_all = st.checkbox("All", key="select_all_objects")
        with col2:
            if select_all:
                st.write(f"**Selected all {len(page_df)} objects on this page**")
        
        # Table headers
        header_cols = st.columns([1, 3, 2, 2, 2, 1, 2, 2])
        headers = ["☑️", "Title", "Type", "Genre", "Audience", "Words", "Created", "Actions"]
        
        for col, header in zip(header_cols, headers):
            col.write(f"**{header}**")
        
        # Table rows
        for _, row in page_df.iterrows():
            cols = st.columns([1, 3, 2, 2, 2, 1, 2, 2])
            
            # Selection checkbox
            with cols[0]:
                is_selected = select_all or st.checkbox(
                    "",
                    key=f"select_obj_{row['index']}",
                    value=row['index'] in st.session_state[self.session_key]['selected_objects']
                )
                
                if is_selected:
                    st.session_state[self.session_key]['selected_objects'].add(row['index'])
                    selected_objects.append(original_objects[row['index']])
                else:
                    st.session_state[self.session_key]['selected_objects'].discard(row['index'])
            
            # Object data
            with cols[1]:
                st.write(f"**{row['title'][:30]}{'...' if len(row['title']) > 30 else ''}**")
                st.caption(row['content_preview'][:50] + "..." if len(row['content_preview']) > 50 else row['content_preview'])
            
            with cols[2]:
                st.write(row['type'])
            
            with cols[3]:
                st.write(row['genre'])
            
            with cols[4]:
                st.write(row['audience'])
            
            with cols[5]:
                st.write(f"{row['word_count']:,}")
            
            with cols[6]:
                st.write(row['created'])
            
            with cols[7]:
                # Action buttons
                if st.button("👁️", key=f"view_{row['index']}", help="View details"):
                    self._show_object_details(original_objects[row['index']])
                
                # Edit and delete buttons would go here in future tasks
        
        return selected_objects
    
    def _render_bulk_actions(self, selected_objects: List[CodexObject]) -> Dict[str, Any]:
        """Render bulk action controls."""
        if not selected_objects:
            return {}
        
        st.markdown("---")
        st.markdown(f"### 🔧 Bulk Actions ({len(selected_objects)} selected)")
        
        col1, col2, col3, col4 = st.columns(4)
        
        actions = {}
        
        with col1:
            if st.button("📤 Export Selected", help="Export selected objects"):
                actions['export'] = selected_objects
        
        with col2:
            if st.button("🏷️ Add Tags", help="Add tags to selected objects"):
                actions['add_tags'] = selected_objects
        
        with col3:
            if st.button("📋 Copy Titles", help="Copy titles to clipboard"):
                actions['copy_titles'] = selected_objects
        
        with col4:
            if st.button("🗑️ Delete Selected", help="Delete selected objects", type="secondary"):
                actions['delete'] = selected_objects
        
        return actions
    
    def _show_object_details(self, obj: CodexObject):
        """Show detailed view of an object in a modal-like expander."""
        with st.expander(f"📄 {obj.title} - Details", expanded=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**Content:**")
                st.text_area(
                    "Full Content",
                    value=obj.content,
                    height=200,
                    disabled=True,
                    label_visibility="collapsed"
                )
            
            with col2:
                st.markdown("**Metadata:**")
                st.write(f"**Type:** {obj.object_type.value.title()}")
                st.write(f"**Word Count:** {obj.word_count:,}")
                st.write(f"**Created:** {obj.created_timestamp[:16] if obj.created_timestamp else 'Unknown'}")
                
                # Show additional metadata if available
                if hasattr(obj, 'genre') and obj.genre:
                    st.write(f"**Genre:** {obj.genre}")
                if hasattr(obj, 'target_audience') and obj.target_audience:
                    st.write(f"**Audience:** {obj.target_audience}")
                
                # Show type-specific metadata
                self._show_type_specific_metadata(obj)
    
    def _show_type_specific_metadata(self, obj: CodexObject):
        """Show metadata specific to the object type."""
        # Ideas
        if hasattr(obj, 'premise') and obj.premise:
            st.write(f"**Premise:** {obj.premise[:100]}{'...' if len(obj.premise) > 100 else ''}")
        if hasattr(obj, 'development_stage') and obj.development_stage:
            st.write(f"**Development Stage:** {obj.development_stage}")
        
        # Synopses
        if hasattr(obj, 'protagonist') and obj.protagonist:
            st.write(f"**Protagonist:** {obj.protagonist}")
        if hasattr(obj, 'plot_structure') and obj.plot_structure:
            st.write(f"**Plot Structure:** {obj.plot_structure}")
        
        # Outlines
        if hasattr(obj, 'outline_type') and obj.outline_type:
            st.write(f"**Outline Type:** {obj.outline_type}")
        if hasattr(obj, 'chapter_count') and obj.chapter_count:
            st.write(f"**Chapters:** {obj.chapter_count}")
        
        # Drafts
        if hasattr(obj, 'completion_percentage') and obj.completion_percentage:
            st.write(f"**Completion:** {obj.completion_percentage}%")
        if hasattr(obj, 'writing_stage') and obj.writing_stage:
            st.write(f"**Writing Stage:** {obj.writing_stage}")
    
    def export_objects_to_csv(self, objects: List[CodexObject]) -> str:
        """Export objects to CSV format."""
        df = self._objects_to_dataframe(objects)
        
        # Add full content column
        df['full_content'] = [obj.content for obj in objects]
        
        # Select relevant columns for export
        export_columns = [
            'title', 'type', 'genre', 'audience', 'word_count', 
            'created', 'content_preview', 'full_content'
        ]
        
        export_df = df[export_columns]
        return export_df.to_csv(index=False)
    
    def export_objects_to_json(self, objects: List[CodexObject]) -> str:
        """Export objects to JSON format."""
        export_data = []
        
        for obj in objects:
            obj_data = {
                'title': obj.title,
                'type': obj.object_type.value,
                'content': obj.content,
                'word_count': obj.word_count,
                'created_timestamp': obj.created_timestamp,
                'genre': getattr(obj, 'genre', ''),
                'target_audience': getattr(obj, 'target_audience', '')
            }
            
            # Add type-specific metadata
            for attr in dir(obj):
                if not attr.startswith('_') and attr not in obj_data:
                    value = getattr(obj, attr)
                    if not callable(value):
                        obj_data[attr] = value
            
            export_data.append(obj_data)
        
        import json
        return json.dumps(export_data, indent=2, default=str)