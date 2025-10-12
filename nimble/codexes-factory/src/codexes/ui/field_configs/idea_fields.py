"""
Idea Field Configuration

Fields specific to idea-type content.
"""

from typing import List
from .universal_fields import FieldDefinition, UniversalFieldConfig


class IdeaFieldConfig(UniversalFieldConfig):
    """Field configuration for idea-type content."""
    
    def _define_universal_fields(self) -> List[FieldDefinition]:
        """Define fields specific to ideas, plus universal fields."""
        # Start with universal fields
        fields = super()._define_universal_fields()
        
        # Add idea-specific fields
        idea_fields = [
            FieldDefinition(
                name="premise",
                label="Core Premise",
                field_type="text_area",
                help_text="The central premise or 'what if' of your idea",
                placeholder="What if time travel was possible but...",
                required=False
            ),
            FieldDefinition(
                name="inspiration",
                label="Inspiration Source",
                field_type="text_input",
                help_text="What inspired this idea? (book, movie, dream, news, etc.)",
                placeholder="Inspired by a dream about..."
            ),
            FieldDefinition(
                name="development_stage",
                label="Development Stage",
                field_type="selectbox",
                help_text="How developed is this idea?",
                options=[
                    "Raw Concept",
                    "Basic Premise",
                    "Partially Developed",
                    "Well Developed",
                    "Ready for Expansion"
                ],
                default_value="Raw Concept"
            ),
            FieldDefinition(
                name="potential_length",
                label="Potential Length",
                field_type="selectbox",
                help_text="What length do you envision for this story?",
                options=[
                    "Not Sure",
                    "Flash Fiction (< 1,000 words)",
                    "Short Story (1,000-7,500 words)",
                    "Novelette (7,500-17,500 words)",
                    "Novella (17,500-40,000 words)",
                    "Novel (40,000+ words)",
                    "Series/Multiple Books"
                ],
                default_value="Not Sure"
            ),
            FieldDefinition(
                name="themes",
                label="Potential Themes",
                field_type="text_input",
                help_text="What themes might this idea explore?",
                placeholder="love, sacrifice, redemption, power..."
            ),
            FieldDefinition(
                name="mood_tone",
                label="Mood/Tone",
                field_type="selectbox",
                help_text="What mood or tone do you envision?",
                options=[
                    "Not Specified",
                    "Light/Humorous",
                    "Adventurous",
                    "Mysterious",
                    "Dark/Serious",
                    "Romantic",
                    "Suspenseful",
                    "Melancholic",
                    "Uplifting",
                    "Satirical"
                ],
                default_value="Not Specified"
            )
        ]
        
        # Insert idea-specific fields after title but before genre
        title_index = next(i for i, f in enumerate(fields) if f.name == "title")
        for i, field in enumerate(idea_fields):
            fields.insert(title_index + 1 + i, field)
        
        return fields