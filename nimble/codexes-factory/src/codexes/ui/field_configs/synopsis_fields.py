"""
Synopsis Field Configuration

Fields specific to synopsis-type content.
"""

from typing import List
from .universal_fields import FieldDefinition, UniversalFieldConfig


class SynopsisFieldConfig(UniversalFieldConfig):
    """Field configuration for synopsis-type content."""
    
    def _define_universal_fields(self) -> List[FieldDefinition]:
        """Define fields specific to synopses, plus universal fields."""
        # Start with universal fields
        fields = super()._define_universal_fields()
        
        # Add synopsis-specific fields
        synopsis_fields = [
            FieldDefinition(
                name="protagonist",
                label="Protagonist",
                field_type="text_input",
                help_text="Main character name and brief description",
                placeholder="Sarah Chen, a detective with psychic abilities..."
            ),
            FieldDefinition(
                name="antagonist",
                label="Antagonist",
                field_type="text_input",
                help_text="Primary antagonist or opposing force",
                placeholder="The Shadow Killer, a serial murderer who..."
            ),
            FieldDefinition(
                name="setting",
                label="Setting",
                field_type="text_input",
                help_text="Where and when the story takes place",
                placeholder="Modern-day San Francisco, with flashbacks to..."
            ),
            FieldDefinition(
                name="central_conflict",
                label="Central Conflict",
                field_type="text_area",
                help_text="The main conflict or problem driving the story",
                placeholder="The protagonist must overcome...",
                required=False
            ),
            FieldDefinition(
                name="plot_structure",
                label="Plot Structure",
                field_type="selectbox",
                help_text="What narrative structure does this follow?",
                options=[
                    "Not Specified",
                    "Three-Act Structure",
                    "Hero's Journey",
                    "Five-Act Structure",
                    "Freytag's Pyramid",
                    "Episodic",
                    "Non-Linear",
                    "Circular",
                    "Other"
                ],
                default_value="Not Specified"
            ),
            FieldDefinition(
                name="word_count_estimate",
                label="Estimated Word Count",
                field_type="selectbox",
                help_text="Estimated length of the full work",
                options=[
                    "Not Specified",
                    "Short Story (1,000-7,500)",
                    "Novelette (7,500-17,500)",
                    "Novella (17,500-40,000)",
                    "Short Novel (40,000-60,000)",
                    "Standard Novel (60,000-90,000)",
                    "Long Novel (90,000+)"
                ],
                default_value="Not Specified"
            ),
            FieldDefinition(
                name="key_themes",
                label="Key Themes",
                field_type="text_input",
                help_text="Major themes explored in the story",
                placeholder="justice, redemption, the nature of time..."
            ),
            FieldDefinition(
                name="character_arcs",
                label="Character Development",
                field_type="text_area",
                help_text="How do the main characters change throughout the story?",
                placeholder="The protagonist learns to trust others...",
                required=False
            )
        ]
        
        # Insert synopsis-specific fields after title but before genre
        title_index = next(i for i, f in enumerate(fields) if f.name == "title")
        for i, field in enumerate(synopsis_fields):
            fields.insert(title_index + 1 + i, field)
        
        return fields