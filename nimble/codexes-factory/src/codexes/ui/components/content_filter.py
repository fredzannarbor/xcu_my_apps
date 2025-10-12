"""
Content Filter Component

Advanced filtering and search capabilities for CodexObject collections.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re

from ..core.simple_codex_object import SimpleCodexObject as CodexObject, CodexObjectType


class ContentFilter:
    """Advanced filtering and search component for CodexObject collections."""
    
    def __init__(self):
        self.session_key = "content_filter_state"
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state for the filter component."""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                'search_history': [],
                'saved_filters': {},
                'active_filters': {},
                'search_query': '',
                'last_search_time': None
            }
    
    def render_advanced_filters(self, objects: List[CodexObject]) -> Dict[str, Any]:
        """
        Render advanced filtering interface.
        
        Returns:
            Dict containing filter criteria and settings
        """
        if not objects:
            return {}
        
        st.markdown("### 🔍 Advanced Search & Filters")
        
        # Create tabs for different filter types
        tab1, tab2, tab3, tab4 = st.tabs(["🔎 Search", "📊 Filters", "💾 Saved", "📈 Analytics"])
        
        with tab1:
            search_filters = self._render_search_interface(objects)
        
        with tab2:
            content_filters = self._render_content_filters(objects)
        
        with tab3:
            saved_filters = self._render_saved_filters()
        
        with tab4:
            analytics = self._render_search_analytics(objects)
        
        # Combine all filters
        combined_filters = {
            **search_filters,
            **content_filters,
            **saved_filters
        }
        
        return combined_filters
    
    def _render_search_interface(self, objects: List[CodexObject]) -> Dict[str, Any]:
        """Render the advanced search interface."""
        st.markdown("#### 🔎 Smart Search")
        
        # Search input with suggestions
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "Search content, titles, and metadata",
                value=st.session_state[self.session_key]['search_query'],
                placeholder="Try: 'fantasy adventure', 'word_count:>1000', 'type:idea', 'created:today'",
                help="Use advanced search syntax: field:value, field:>value, field:<value, 'quoted phrases'",
                key="advanced_search_input"
            )
        
        with col2:
            search_mode = st.selectbox(
                "Search Mode",
                options=["Smart", "Exact", "Regex"],
                help="Smart: Intelligent matching, Exact: Precise matches, Regex: Regular expressions"
            )
        
        # Update search query in session state
        if search_query != st.session_state[self.session_key]['search_query']:
            st.session_state[self.session_key]['search_query'] = search_query
            self._add_to_search_history(search_query)
        
        # Search suggestions and history
        if search_query:
            suggestions = self._generate_search_suggestions(search_query, objects)
            if suggestions:
                st.write("**Suggestions:**")
                suggestion_cols = st.columns(min(len(suggestions), 4))
                for i, suggestion in enumerate(suggestions[:4]):
                    with suggestion_cols[i]:
                        if st.button(f"💡 {suggestion}", key=f"suggestion_{i}"):
                            st.session_state[self.session_key]['search_query'] = suggestion
                            st.rerun()
        
        # Search history
        history = st.session_state[self.session_key]['search_history']
        if history:
            with st.expander("📚 Recent Searches", expanded=False):
                for i, (query, timestamp) in enumerate(history[-5:]):  # Show last 5
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"'{query}'")
                    with col2:
                        st.caption(timestamp.strftime("%H:%M"))
                    with col3:
                        if st.button("🔄", key=f"reuse_search_{i}", help="Use this search"):
                            st.session_state[self.session_key]['search_query'] = query
                            st.rerun()
        
        return {
            'search_query': search_query,
            'search_mode': search_mode
        }
    
    def _render_content_filters(self, objects: List[CodexObject]) -> Dict[str, Any]:
        """Render content-based filters."""
        st.markdown("#### 📊 Content Filters")
        
        # Extract filter options from objects
        filter_options = self._extract_filter_options(objects)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Content type filter
            selected_types = st.multiselect(
                "Content Types",
                options=filter_options['types'],
                default=[],
                help="Filter by content type"
            )
            
            # Genre filter
            selected_genres = st.multiselect(
                "Genres",
                options=filter_options['genres'],
                default=[],
                help="Filter by genre"
            )
            
            # Audience filter
            selected_audiences = st.multiselect(
                "Target Audiences",
                options=filter_options['audiences'],
                default=[],
                help="Filter by target audience"
            )
        
        with col2:
            # Word count filter
            word_counts = [obj.word_count for obj in objects if obj.word_count]
            if word_counts:
                min_words, max_words = min(word_counts), max(word_counts)
                
                # Handle case where all objects have the same word count
                if min_words == max_words:
                    st.write(f"**Word Count:** {min_words} words (all objects)")
                    word_range = (min_words, max_words)
                else:
                    word_range = st.slider(
                        "Word Count Range",
                        min_value=min_words,
                        max_value=max_words,
                        value=(min_words, max_words),
                        help="Filter by word count range"
                    )
            else:
                word_range = (0, 0)
            
            # Date filter
            date_filter = st.selectbox(
                "Created Date",
                options=["All Time", "Today", "This Week", "This Month", "Custom Range"],
                help="Filter by creation date"
            )
            
            custom_date_range = None
            if date_filter == "Custom Range":
                col_start, col_end = st.columns(2)
                with col_start:
                    start_date = st.date_input("From", value=datetime.now().date() - timedelta(days=30))
                with col_end:
                    end_date = st.date_input("To", value=datetime.now().date())
                custom_date_range = (start_date, end_date)
            
            # Tags filter (if objects have tags)
            all_tags = set()
            for obj in objects:
                if hasattr(obj, 'tags') and obj.tags:
                    tags = [tag.strip() for tag in obj.tags.split(',') if tag.strip()]
                    all_tags.update(tags)
            
            selected_tags = []
            if all_tags:
                selected_tags = st.multiselect(
                    "Tags",
                    options=sorted(all_tags),
                    default=[],
                    help="Filter by tags"
                )
        
        return {
            'selected_types': selected_types,
            'selected_genres': selected_genres,
            'selected_audiences': selected_audiences,
            'word_range': word_range,
            'date_filter': date_filter,
            'custom_date_range': custom_date_range,
            'selected_tags': selected_tags
        }
    
    def _render_saved_filters(self) -> Dict[str, Any]:
        """Render saved filters interface."""
        st.markdown("#### 💾 Saved Filters")
        
        saved_filters = st.session_state[self.session_key]['saved_filters']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Save current filter
            filter_name = st.text_input(
                "Save Current Filter As:",
                placeholder="My Custom Filter",
                help="Give your current filter combination a name"
            )
            
            if filter_name and st.button("💾 Save Filter"):
                current_filters = st.session_state[self.session_key]['active_filters']
                saved_filters[filter_name] = {
                    'filters': current_filters.copy(),
                    'created': datetime.now(),
                    'usage_count': 0
                }
                st.session_state[self.session_key]['saved_filters'] = saved_filters
                st.success(f"Filter '{filter_name}' saved!")
        
        with col2:
            # Load saved filter
            if saved_filters:
                selected_filter = st.selectbox(
                    "Load Saved Filter:",
                    options=[""] + list(saved_filters.keys()),
                    format_func=lambda x: f"{x} (used {saved_filters[x]['usage_count']} times)" if x else "Select a filter..."
                )
                
                if selected_filter and st.button("📂 Load Filter"):
                    filter_data = saved_filters[selected_filter]
                    filter_data['usage_count'] += 1
                    st.session_state[self.session_key]['active_filters'] = filter_data['filters'].copy()
                    st.success(f"Loaded filter '{selected_filter}'!")
                    st.rerun()
        
        # Show saved filters
        if saved_filters:
            st.write("**Saved Filters:**")
            for name, data in saved_filters.items():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"📁 {name}")
                with col2:
                    st.caption(f"Used {data['usage_count']} times")
                with col3:
                    if st.button("🗑️", key=f"delete_filter_{name}", help="Delete filter"):
                        del saved_filters[name]
                        st.session_state[self.session_key]['saved_filters'] = saved_filters
                        st.rerun()
        
        return {'loaded_filter': saved_filters.get(selected_filter, {}) if 'selected_filter' in locals() and selected_filter else {}}
    
    def _render_search_analytics(self, objects: List[CodexObject]) -> Dict[str, Any]:
        """Render search analytics and insights."""
        st.markdown("#### 📈 Search Analytics")
        
        if not objects:
            st.info("No objects to analyze")
            return {}
        
        # Content statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Content Distribution:**")
            
            # Type distribution
            type_counts = {}
            for obj in objects:
                obj_type = obj.object_type.value.title()
                type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
            
            for content_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(objects)) * 100
                st.write(f"• {content_type}: {count} ({percentage:.1f}%)")
        
        with col2:
            st.write("**Content Insights:**")
            
            # Word count statistics
            word_counts = [obj.word_count for obj in objects if obj.word_count > 0]
            if word_counts:
                avg_words = sum(word_counts) / len(word_counts)
                st.write(f"• Average words: {avg_words:.0f}")
                st.write(f"• Total words: {sum(word_counts):,}")
                st.write(f"• Longest piece: {max(word_counts):,} words")
                st.write(f"• Shortest piece: {min(word_counts):,} words")
        
        # Search patterns
        history = st.session_state[self.session_key]['search_history']
        if history:
            st.write("**Search Patterns:**")
            
            # Most common search terms
            all_terms = []
            for query, _ in history:
                # Extract individual words (simple tokenization)
                terms = re.findall(r'\b\w+\b', query.lower())
                all_terms.extend(terms)
            
            if all_terms:
                from collections import Counter
                common_terms = Counter(all_terms).most_common(5)
                
                st.write("Most searched terms:")
                for term, count in common_terms:
                    st.write(f"• '{term}': {count} times")
        
        return {}
    
    def apply_filters(self, objects: List[CodexObject], filters: Dict[str, Any]) -> List[CodexObject]:
        """Apply filters to the object collection."""
        if not objects or not filters:
            return objects
        
        filtered_objects = objects.copy()
        
        # Apply search query
        search_query = filters.get('search_query', '').strip()
        if search_query:
            filtered_objects = self._apply_search_query(filtered_objects, search_query, filters.get('search_mode', 'Smart'))
        
        # Apply content type filter
        selected_types = filters.get('selected_types', [])
        if selected_types:
            filtered_objects = [obj for obj in filtered_objects if obj.object_type.value.title() in selected_types]
        
        # Apply genre filter
        selected_genres = filters.get('selected_genres', [])
        if selected_genres:
            filtered_objects = [
                obj for obj in filtered_objects 
                if hasattr(obj, 'genre') and obj.genre in selected_genres
            ]
        
        # Apply audience filter
        selected_audiences = filters.get('selected_audiences', [])
        if selected_audiences:
            filtered_objects = [
                obj for obj in filtered_objects 
                if hasattr(obj, 'target_audience') and obj.target_audience in selected_audiences
            ]
        
        # Apply word count filter
        word_range = filters.get('word_range')
        if word_range and word_range != (0, 0):
            min_words, max_words = word_range
            filtered_objects = [
                obj for obj in filtered_objects 
                if min_words <= obj.word_count <= max_words
            ]
        
        # Apply date filter
        date_filter = filters.get('date_filter', 'All Time')
        if date_filter != 'All Time':
            filtered_objects = self._apply_date_filter(filtered_objects, date_filter, filters.get('custom_date_range'))
        
        # Apply tags filter
        selected_tags = filters.get('selected_tags', [])
        if selected_tags:
            filtered_objects = [
                obj for obj in filtered_objects
                if hasattr(obj, 'tags') and obj.tags and 
                any(tag.strip() in selected_tags for tag in obj.tags.split(','))
            ]
        
        return filtered_objects
    
    def _apply_search_query(self, objects: List[CodexObject], query: str, mode: str) -> List[CodexObject]:
        """Apply search query to objects."""
        if not query:
            return objects
        
        # Parse advanced search syntax
        parsed_query = self._parse_search_query(query)
        
        filtered_objects = []
        
        for obj in objects:
            if self._object_matches_query(obj, parsed_query, mode):
                filtered_objects.append(obj)
        
        return filtered_objects
    
    def _parse_search_query(self, query: str) -> Dict[str, Any]:
        """Parse advanced search query syntax."""
        parsed = {
            'text_terms': [],
            'field_filters': {},
            'quoted_phrases': []
        }
        
        # Extract quoted phrases
        quoted_pattern = r'"([^"]*)"'
        quoted_matches = re.findall(quoted_pattern, query)
        parsed['quoted_phrases'] = quoted_matches
        
        # Remove quoted phrases from query for further processing
        query_without_quotes = re.sub(quoted_pattern, '', query)
        
        # Extract field filters (field:value, field:>value, field:<value)
        field_pattern = r'(\w+):(>|<|>=|<=|=)?([^\s]+)'
        field_matches = re.findall(field_pattern, query_without_quotes)
        
        for field, operator, value in field_matches:
            if not operator:
                operator = '='
            parsed['field_filters'][field] = {'operator': operator, 'value': value}
        
        # Remove field filters from query
        query_without_fields = re.sub(field_pattern, '', query_without_quotes)
        
        # Extract remaining text terms
        text_terms = [term.strip() for term in query_without_fields.split() if term.strip()]
        parsed['text_terms'] = text_terms
        
        return parsed
    
    def _object_matches_query(self, obj: CodexObject, parsed_query: Dict[str, Any], mode: str) -> bool:
        """Check if an object matches the parsed search query."""
        # Check quoted phrases
        for phrase in parsed_query['quoted_phrases']:
            if not self._object_contains_phrase(obj, phrase, mode):
                return False
        
        # Check field filters
        for field, filter_data in parsed_query['field_filters'].items():
            if not self._object_matches_field_filter(obj, field, filter_data):
                return False
        
        # Check text terms
        for term in parsed_query['text_terms']:
            if not self._object_contains_term(obj, term, mode):
                return False
        
        return True
    
    def _object_contains_phrase(self, obj: CodexObject, phrase: str, mode: str) -> bool:
        """Check if object contains a specific phrase."""
        searchable_text = self._get_searchable_text(obj).lower()
        phrase_lower = phrase.lower()
        
        if mode == 'Exact':
            return phrase_lower in searchable_text
        elif mode == 'Regex':
            try:
                return bool(re.search(phrase, searchable_text, re.IGNORECASE))
            except re.error:
                return phrase_lower in searchable_text
        else:  # Smart mode
            # Smart matching with fuzzy logic
            words = phrase_lower.split()
            return all(word in searchable_text for word in words)
    
    def _object_contains_term(self, obj: CodexObject, term: str, mode: str) -> bool:
        """Check if object contains a specific term."""
        return self._object_contains_phrase(obj, term, mode)
    
    def _object_matches_field_filter(self, obj: CodexObject, field: str, filter_data: Dict[str, str]) -> bool:
        """Check if object matches a field filter."""
        operator = filter_data['operator']
        value = filter_data['value']
        
        # Get field value from object
        field_value = self._get_field_value(obj, field)
        
        if field_value is None:
            return False
        
        # Handle different operators
        if operator == '=':
            return str(field_value).lower() == value.lower()
        elif operator == '>':
            try:
                return float(field_value) > float(value)
            except (ValueError, TypeError):
                return str(field_value).lower() > value.lower()
        elif operator == '<':
            try:
                return float(field_value) < float(value)
            except (ValueError, TypeError):
                return str(field_value).lower() < value.lower()
        elif operator == '>=':
            try:
                return float(field_value) >= float(value)
            except (ValueError, TypeError):
                return str(field_value).lower() >= value.lower()
        elif operator == '<=':
            try:
                return float(field_value) <= float(value)
            except (ValueError, TypeError):
                return str(field_value).lower() <= value.lower()
        
        return False
    
    def _get_field_value(self, obj: CodexObject, field: str) -> Any:
        """Get field value from object."""
        field_mapping = {
            'type': obj.object_type.value,
            'title': obj.title,
            'content': obj.content,
            'word_count': obj.word_count,
            'words': obj.word_count,
            'genre': getattr(obj, 'genre', ''),
            'audience': getattr(obj, 'target_audience', ''),
            'tags': getattr(obj, 'tags', ''),
            'created': obj.created_timestamp
        }
        
        return field_mapping.get(field.lower())
    
    def _get_searchable_text(self, obj: CodexObject) -> str:
        """Get all searchable text from an object."""
        searchable_parts = [
            obj.title or '',
            obj.content or '',
            getattr(obj, 'genre', '') or '',
            getattr(obj, 'target_audience', '') or '',
            getattr(obj, 'tags', '') or ''
        ]
        
        # Add type-specific metadata
        if hasattr(obj, 'premise'):
            searchable_parts.append(getattr(obj, 'premise', '') or '')
        if hasattr(obj, 'protagonist'):
            searchable_parts.append(getattr(obj, 'protagonist', '') or '')
        if hasattr(obj, 'antagonist'):
            searchable_parts.append(getattr(obj, 'antagonist', '') or '')
        
        return ' '.join(searchable_parts)
    
    def _apply_date_filter(self, objects: List[CodexObject], date_filter: str, custom_range: Optional[Tuple]) -> List[CodexObject]:
        """Apply date-based filtering."""
        now = datetime.now()
        
        if date_filter == "Today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif date_filter == "This Week":
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif date_filter == "This Month":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif date_filter == "Custom Range" and custom_range:
            start_date = datetime.combine(custom_range[0], datetime.min.time())
            end_date = datetime.combine(custom_range[1], datetime.max.time())
        else:
            return objects
        
        filtered_objects = []
        for obj in objects:
            try:
                obj_date = datetime.fromisoformat(obj.created_timestamp.replace('Z', '+00:00'))
                if start_date <= obj_date <= end_date:
                    filtered_objects.append(obj)
            except (ValueError, AttributeError):
                # If date parsing fails, include the object
                filtered_objects.append(obj)
        
        return filtered_objects
    
    def _extract_filter_options(self, objects: List[CodexObject]) -> Dict[str, List[str]]:
        """Extract available filter options from objects."""
        types = set()
        genres = set()
        audiences = set()
        
        for obj in objects:
            types.add(obj.object_type.value.title())
            
            if hasattr(obj, 'genre') and obj.genre:
                genres.add(obj.genre)
            
            if hasattr(obj, 'target_audience') and obj.target_audience:
                audiences.add(obj.target_audience)
        
        return {
            'types': sorted(list(types)),
            'genres': sorted([g for g in genres if g and g != 'Not Specified']),
            'audiences': sorted([a for a in audiences if a and a != 'Not Specified'])
        }
    
    def _generate_search_suggestions(self, query: str, objects: List[CodexObject]) -> List[str]:
        """Generate search suggestions based on current query and available content."""
        suggestions = []
        
        # If query is short, suggest common searches
        if len(query) < 3:
            suggestions.extend([
                "type:idea",
                "word_count:>500",
                "created:today",
                "genre:fantasy"
            ])
        else:
            # Suggest field-based searches
            if ':' not in query:
                suggestions.extend([
                    f"title:{query}",
                    f"content:{query}",
                    f"genre:{query}"
                ])
        
        return suggestions[:4]  # Limit to 4 suggestions
    
    def _add_to_search_history(self, query: str):
        """Add search query to history."""
        if not query.strip():
            return
        
        history = st.session_state[self.session_key]['search_history']
        
        # Remove duplicate if exists
        history = [(q, t) for q, t in history if q != query]
        
        # Add new query
        history.append((query, datetime.now()))
        
        # Keep only last 20 searches
        if len(history) > 20:
            history = history[-20:]
        
        st.session_state[self.session_key]['search_history'] = history
        st.session_state[self.session_key]['last_search_time'] = datetime.now()