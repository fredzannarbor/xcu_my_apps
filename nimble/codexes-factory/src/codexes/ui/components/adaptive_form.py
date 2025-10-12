"""
Adaptive Form Component

Creates forms that adapt to content types with intelligent field suggestions.
"""

from typing import Dict, Any, Optional, List
import streamlit as st
import re

from ..core.simple_codex_object import CodexObjectType
from ..field_configs import (
    UniversalFieldConfig,
    IdeaFieldConfig,
    SynopsisFieldConfig,
    OutlineFieldConfig,
    DraftFieldConfig
)


class FormAdapter:
    """Adapts forms to content types with intelligent suggestions."""
    
    def __init__(self):
        self.field_configs = {
            CodexObjectType.IDEA: IdeaFieldConfig(),
            CodexObjectType.LOGLINE: IdeaFieldConfig(),  # Use idea config for loglines
            CodexObjectType.SUMMARY: SynopsisFieldConfig(),
            CodexObjectType.SYNOPSIS: SynopsisFieldConfig(),
            CodexObjectType.OUTLINE: OutlineFieldConfig(),
            CodexObjectType.DRAFT: DraftFieldConfig(),
            CodexObjectType.MANUSCRIPT: DraftFieldConfig()
        }
        self.universal_config = UniversalFieldConfig()
    
    def render_adaptive_form(self, content_type: CodexObjectType, content: str, key_suffix: str = "") -> Dict[str, Any]:
        """Render an adaptive form based on content type."""
        st.markdown(f"### 📋 {content_type.value.title()} Metadata")
        
        # Get the appropriate field configuration
        field_config = self.field_configs.get(content_type, self.universal_config)
        
        # Generate intelligent suggestions
        suggestions = self._generate_suggestions(content_type, content)
        
        # Show suggestions if available
        if suggestions:
            with st.expander("💡 Smart Suggestions", expanded=True):
                self._display_suggestions(suggestions)
        
        # Render form fields
        form_data = {}
        
        # Group fields for better organization
        field_groups = self._organize_fields(field_config.fields)
        
        for group_name, group_fields in field_groups.items():
            if group_name != "Basic Information":
                st.markdown(f"**{group_name}**")
            
            # Create columns for better layout
            if len(group_fields) > 1 and group_name in ["Basic Information", "Content Details"]:
                cols = st.columns(2)
                for i, field in enumerate(group_fields):
                    with cols[i % 2]:
                        suggested_value = suggestions.get(field.name) if suggestions else None
                        form_data[field.name] = field_config.render_field(
                            field, 
                            key_suffix=key_suffix,
                            value=suggested_value
                        )
            else:
                for field in group_fields:
                    suggested_value = suggestions.get(field.name) if suggestions else None
                    form_data[field.name] = field_config.render_field(
                        field,
                        key_suffix=key_suffix, 
                        value=suggested_value
                    )
        
        return form_data
    
    def _organize_fields(self, fields) -> Dict[str, List]:
        """Organize fields into logical groups."""
        groups = {
            "Basic Information": [],
            "Content Details": [],
            "Development": [],
            "Additional Information": []
        }
        
        basic_fields = {"title", "genre", "target_audience"}
        content_fields = {
            "premise", "protagonist", "antagonist", "setting", "central_conflict",
            "outline_type", "structure_method", "draft_type", "current_word_count"
        }
        development_fields = {
            "development_stage", "completion_status", "writing_stage", 
            "completion_percentage", "revision_notes", "writing_goals"
        }
        
        for field in fields:
            if field.name in basic_fields:
                groups["Basic Information"].append(field)
            elif field.name in content_fields:
                groups["Content Details"].append(field)
            elif field.name in development_fields:
                groups["Development"].append(field)
            else:
                groups["Additional Information"].append(field)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def _generate_suggestions(self, content_type: CodexObjectType, content: str) -> Dict[str, Any]:
        """Generate intelligent suggestions based on content analysis."""
        suggestions = {}
        
        # Generate title suggestion
        title_suggestion = self._suggest_title(content)
        if title_suggestion:
            suggestions["title"] = title_suggestion
        
        # Generate genre suggestions
        genre_suggestion = self._suggest_genre(content)
        if genre_suggestion:
            suggestions["genre"] = genre_suggestion
        
        # Generate audience suggestions
        audience_suggestion = self._suggest_audience(content)
        if audience_suggestion:
            suggestions["target_audience"] = audience_suggestion
        
        # Content-type specific suggestions
        if content_type in [CodexObjectType.IDEA, CodexObjectType.LOGLINE]:
            suggestions.update(self._suggest_idea_fields(content))
        elif content_type in [CodexObjectType.SYNOPSIS, CodexObjectType.SUMMARY]:
            suggestions.update(self._suggest_synopsis_fields(content))
        elif content_type == CodexObjectType.OUTLINE:
            suggestions.update(self._suggest_outline_fields(content))
        elif content_type in [CodexObjectType.DRAFT, CodexObjectType.MANUSCRIPT]:
            suggestions.update(self._suggest_draft_fields(content))
        
        return suggestions
    
    def _suggest_title(self, content: str) -> Optional[str]:
        """Suggest a title based on content analysis."""
        if not content:
            return None
        
        lines = content.strip().split('\n')
        first_line = lines[0].strip()
        
        # If first line looks like a title (short, no period)
        if len(first_line) < 100 and not first_line.endswith('.') and len(first_line.split()) <= 10:
            return first_line
        
        # Extract potential titles from content
        title_patterns = [
            r'^#\s+(.+)$',  # Markdown header
            r'^(.+):$',     # Line ending with colon
            r'"([^"]+)"',   # Quoted text
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                title = matches[0].strip()
                if 3 <= len(title) <= 100:
                    return title
        
        # Fallback: use first few words
        words = content.strip().split()[:6]
        if words:
            title = ' '.join(words)
            if title.endswith('.'):
                title = title[:-1]
            return title[:100] if len(title) > 100 else title
        
        return None
    
    def _suggest_genre(self, content: str) -> Optional[str]:
        """Suggest genre based on content keywords."""
        content_lower = content.lower()
        
        genre_keywords = {
            "Science Fiction": ["space", "alien", "robot", "future", "technology", "time travel", "spaceship", "galaxy"],
            "Fantasy": ["magic", "dragon", "wizard", "spell", "kingdom", "quest", "sword", "elf", "dwarf"],
            "Mystery": ["detective", "murder", "clue", "investigate", "suspect", "crime", "police", "evidence"],
            "Romance": ["love", "heart", "kiss", "relationship", "wedding", "romance", "passion", "dating"],
            "Horror": ["ghost", "monster", "scary", "fear", "nightmare", "haunted", "demon", "terror"],
            "Thriller": ["chase", "danger", "escape", "suspense", "threat", "conspiracy", "spy", "action"],
            "Historical Fiction": ["century", "war", "historical", "period", "ancient", "medieval", "victorian"],
            "Young Adult": ["teenager", "high school", "coming of age", "teen", "adolescent", "youth"]
        }
        
        genre_scores = {}
        for genre, keywords in genre_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                genre_scores[genre] = score
        
        if genre_scores:
            return max(genre_scores, key=genre_scores.get)
        
        return None
    
    def _suggest_audience(self, content: str) -> Optional[str]:
        """Suggest target audience based on content analysis."""
        content_lower = content.lower()
        
        audience_indicators = {
            "Children (0-8)": ["child", "kid", "simple", "animal", "picture book"],
            "Middle Grade (9-12)": ["school", "friend", "adventure", "family", "growing up"],
            "Young Adult (13-17)": ["teenager", "high school", "first love", "identity", "rebellion"],
            "Adult (25+)": ["career", "marriage", "parent", "complex", "mature themes"]
        }
        
        for audience, indicators in audience_indicators.items():
            if any(indicator in content_lower for indicator in indicators):
                return audience
        
        return None
    
    def _suggest_idea_fields(self, content: str) -> Dict[str, Any]:
        """Generate suggestions for idea-specific fields."""
        suggestions = {}
        
        # Suggest premise if content looks like a "what if" statement
        if "what if" in content.lower() or "imagine" in content.lower():
            suggestions["premise"] = content[:200] + "..." if len(content) > 200 else content
        
        # Suggest development stage based on content length and detail
        word_count = len(content.split())
        if word_count < 20:
            suggestions["development_stage"] = "Raw Concept"
        elif word_count < 50:
            suggestions["development_stage"] = "Basic Premise"
        else:
            suggestions["development_stage"] = "Partially Developed"
        
        return suggestions
    
    def _suggest_synopsis_fields(self, content: str) -> Dict[str, Any]:
        """Generate suggestions for synopsis-specific fields."""
        suggestions = {}
        
        # Look for character names (capitalized words that appear multiple times)
        words = re.findall(r'\b[A-Z][a-z]+\b', content)
        word_counts = {}
        for word in words:
            if len(word) > 2:  # Skip short words
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Suggest protagonist (most frequent capitalized word)
        if word_counts:
            protagonist = max(word_counts, key=word_counts.get)
            if word_counts[protagonist] > 1:
                suggestions["protagonist"] = protagonist
        
        # Suggest plot structure based on content patterns
        if "act" in content.lower() or "three" in content.lower():
            suggestions["plot_structure"] = "Three-Act Structure"
        elif "journey" in content.lower() or "hero" in content.lower():
            suggestions["plot_structure"] = "Hero's Journey"
        
        return suggestions
    
    def _suggest_outline_fields(self, content: str) -> Dict[str, Any]:
        """Generate suggestions for outline-specific fields."""
        suggestions = {}
        
        # Count chapters/sections
        chapter_count = len(re.findall(r'chapter\s+\d+', content, re.IGNORECASE))
        if chapter_count == 0:
            chapter_count = len(re.findall(r'^\d+\.', content, re.MULTILINE))
        
        if chapter_count > 0:
            suggestions["chapter_count"] = chapter_count
            suggestions["outline_type"] = "Chapter Outline"
        
        # Suggest structure method
        if "beat" in content.lower():
            suggestions["structure_method"] = "Save the Cat Beat Sheet"
        elif "act" in content.lower():
            suggestions["structure_method"] = "Three-Act Structure"
        
        return suggestions
    
    def _suggest_draft_fields(self, content: str) -> Dict[str, Any]:
        """Generate suggestions for draft-specific fields."""
        suggestions = {}
        
        # Calculate current word count
        word_count = len(content.split())
        suggestions["current_word_count"] = word_count
        
        # Suggest target word count based on current length
        if word_count < 1000:
            suggestions["target_word_count"] = 5000
        elif word_count < 10000:
            suggestions["target_word_count"] = 50000
        else:
            suggestions["target_word_count"] = 80000
        
        # Suggest completion percentage
        if word_count < 1000:
            suggestions["completion_percentage"] = 5
        elif word_count < 10000:
            suggestions["completion_percentage"] = 15
        elif word_count < 50000:
            suggestions["completion_percentage"] = 50
        else:
            suggestions["completion_percentage"] = 80
        
        return suggestions
    
    def _display_suggestions(self, suggestions: Dict[str, Any]):
        """Display intelligent suggestions to the user."""
        st.write("Based on your content, here are some suggestions:")
        
        suggestion_items = []
        for field_name, value in suggestions.items():
            if value and str(value).strip():
                # Make field names more readable
                readable_name = field_name.replace('_', ' ').title()
                if isinstance(value, (int, float)):
                    suggestion_items.append(f"**{readable_name}**: {value}")
                else:
                    # Truncate long suggestions
                    display_value = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                    suggestion_items.append(f"**{readable_name}**: {display_value}")
        
        if suggestion_items:
            for item in suggestion_items[:5]:  # Show top 5 suggestions
                st.write(f"• {item}")
        else:
            st.write("No specific suggestions available for this content.")