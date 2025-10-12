"""
Universal Field Configuration

Fields that apply to all content types.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import streamlit as st


@dataclass
class FieldDefinition:
    """Definition of a form field."""
    name: str
    label: str
    field_type: str  # 'text_input', 'text_area', 'selectbox', 'multiselect', 'number_input', 'slider'
    help_text: str
    required: bool = False
    default_value: Any = None
    options: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    placeholder: Optional[str] = None


class UniversalFieldConfig:
    """Universal field configuration that applies to all content types."""
    
    def __init__(self):
        self.fields = self._define_universal_fields()
    
    def _define_universal_fields(self) -> List[FieldDefinition]:
        """Define fields that apply to all content types."""
        return [
            FieldDefinition(
                name="title",
                label="Title",
                field_type="text_input",
                help_text="A descriptive title for your content",
                required=True,
                placeholder="Enter a title for your content..."
            ),
            FieldDefinition(
                name="genre",
                label="Genre",
                field_type="selectbox",
                help_text="The primary genre of your content",
                options=[
                    "Not Specified",
                    "Science Fiction",
                    "Fantasy", 
                    "Mystery",
                    "Thriller",
                    "Romance",
                    "Horror",
                    "Adventure",
                    "Drama",
                    "Comedy",
                    "Historical Fiction",
                    "Literary Fiction",
                    "Young Adult",
                    "Children's",
                    "Non-Fiction",
                    "Biography",
                    "Memoir",
                    "Self-Help",
                    "Business",
                    "Other"
                ],
                default_value="Not Specified"
            ),
            FieldDefinition(
                name="target_audience",
                label="Target Audience",
                field_type="selectbox",
                help_text="The intended audience for your content",
                options=[
                    "Not Specified",
                    "Children (0-8)",
                    "Middle Grade (9-12)",
                    "Young Adult (13-17)",
                    "New Adult (18-25)",
                    "Adult (25+)",
                    "General Audience",
                    "Academic",
                    "Professional"
                ],
                default_value="Not Specified"
            ),
            FieldDefinition(
                name="tags",
                label="Tags",
                field_type="text_input",
                help_text="Comma-separated tags to help categorize your content",
                placeholder="adventure, magic, coming-of-age..."
            ),
            FieldDefinition(
                name="notes",
                label="Notes",
                field_type="text_area",
                help_text="Additional notes or comments about your content",
                placeholder="Any additional thoughts, inspirations, or notes..."
            )
        ]
    
    def get_field_by_name(self, name: str) -> Optional[FieldDefinition]:
        """Get a field definition by name."""
        for field in self.fields:
            if field.name == name:
                return field
        return None
    
    def get_field_names(self) -> List[str]:
        """Get list of all field names."""
        return [field.name for field in self.fields]
    
    def render_field(self, field: FieldDefinition, key_suffix: str = "", value: Any = None) -> Any:
        """Render a single field and return its value."""
        field_key = f"{field.name}_{key_suffix}" if key_suffix else field.name
        
        # Use provided value or default
        if value is None:
            value = field.default_value
        
        if field.field_type == "text_input":
            return st.text_input(
                field.label,
                value=value or "",
                help=field.help_text,
                placeholder=field.placeholder,
                key=field_key
            )
        
        elif field.field_type == "text_area":
            return st.text_area(
                field.label,
                value=value or "",
                help=field.help_text,
                placeholder=field.placeholder,
                key=field_key,
                height=100
            )
        
        elif field.field_type == "selectbox":
            if field.options:
                try:
                    index = field.options.index(value) if value in field.options else 0
                except (ValueError, TypeError):
                    index = 0
                
                return st.selectbox(
                    field.label,
                    options=field.options,
                    index=index,
                    help=field.help_text,
                    key=field_key
                )
        
        elif field.field_type == "multiselect":
            if field.options:
                default_values = value if isinstance(value, list) else []
                return st.multiselect(
                    field.label,
                    options=field.options,
                    default=default_values,
                    help=field.help_text,
                    key=field_key
                )
        
        elif field.field_type == "number_input":
            return st.number_input(
                field.label,
                value=value or 0,
                min_value=field.min_value,
                max_value=field.max_value,
                help=field.help_text,
                key=field_key
            )
        
        elif field.field_type == "slider":
            return st.slider(
                field.label,
                min_value=field.min_value or 0,
                max_value=field.max_value or 100,
                value=value or field.min_value or 0,
                help=field.help_text,
                key=field_key
            )
        
        else:
            st.error(f"Unknown field type: {field.field_type}")
            return None