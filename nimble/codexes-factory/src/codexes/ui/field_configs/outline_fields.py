"""
Outline Field Configuration

Fields specific to outline-type content.
"""

from typing import List
from .universal_fields import FieldDefinition, UniversalFieldConfig


class OutlineFieldConfig(UniversalFieldConfig):
    """Field configuration for outline-type content."""
    
    def _define_universal_fields(self) -> List[FieldDefinition]:
        """Define fields specific to outlines, plus universal fields."""
        # Start with universal fields
        fields = super()._define_universal_fields()
        
        # Add outline-specific fields
        outline_fields = [
            FieldDefinition(
                name="outline_type",
                label="Outline Type",
                field_type="selectbox",
                help_text="What type of outline is this?",
                options=[
                    "Chapter Outline",
                    "Scene Outline", 
                    "Beat Sheet",
                    "Treatment",
                    "Story Structure",
                    "Character Outline",
                    "Plot Outline",
                    "Series Outline",
                    "Other"
                ],
                default_value="Chapter Outline"
            ),
            FieldDefinition(
                name="structure_method",
                label="Structure Method",
                field_type="selectbox",
                help_text="What structural approach does this outline follow?",
                options=[
                    "Not Specified",
                    "Three-Act Structure",
                    "Hero's Journey",
                    "Save the Cat Beat Sheet",
                    "Freytag's Pyramid",
                    "Seven-Point Story Structure",
                    "Snowflake Method",
                    "Custom Structure"
                ],
                default_value="Not Specified"
            ),
            FieldDefinition(
                name="chapter_count",
                label="Number of Chapters/Sections",
                field_type="number_input",
                help_text="How many chapters or major sections?",
                min_value=1,
                max_value=100,
                default_value=1
            ),
            FieldDefinition(
                name="estimated_words_per_chapter",
                label="Est. Words per Chapter",
                field_type="number_input",
                help_text="Estimated word count per chapter",
                min_value=100,
                max_value=10000,
                default_value=2000
            ),
            FieldDefinition(
                name="pacing_notes",
                label="Pacing Notes",
                field_type="text_area",
                help_text="Notes about pacing, tension, and story rhythm",
                placeholder="Fast-paced opening, slow build in middle...",
                required=False
            ),
            FieldDefinition(
                name="character_focus",
                label="Character Focus",
                field_type="text_input",
                help_text="Which characters are featured prominently?",
                placeholder="Sarah (protagonist), Marcus (love interest)..."
            ),
            FieldDefinition(
                name="plot_threads",
                label="Plot Threads",
                field_type="text_area",
                help_text="Major plot threads and subplots tracked in this outline",
                placeholder="Main mystery, romantic subplot, family drama...",
                required=False
            ),
            FieldDefinition(
                name="completion_status",
                label="Completion Status",
                field_type="selectbox",
                help_text="How complete is this outline?",
                options=[
                    "Rough Draft",
                    "Partially Complete",
                    "Nearly Complete",
                    "Complete",
                    "Revised",
                    "Final"
                ],
                default_value="Rough Draft"
            )
        ]
        
        # Insert outline-specific fields after title but before genre
        title_index = next(i for i, f in enumerate(fields) if f.name == "title")
        for i, field in enumerate(outline_fields):
            fields.insert(title_index + 1 + i, field)
        
        return fields