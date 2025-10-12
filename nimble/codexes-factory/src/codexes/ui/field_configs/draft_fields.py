"""
Draft Field Configuration

Fields specific to draft and manuscript-type content.
"""

from typing import List
from .universal_fields import FieldDefinition, UniversalFieldConfig


class DraftFieldConfig(UniversalFieldConfig):
    """Field configuration for draft and manuscript-type content."""
    
    def _define_universal_fields(self) -> List[FieldDefinition]:
        """Define fields specific to drafts/manuscripts, plus universal fields."""
        # Start with universal fields
        fields = super()._define_universal_fields()
        
        # Add draft-specific fields
        draft_fields = [
            FieldDefinition(
                name="draft_type",
                label="Draft Type",
                field_type="selectbox",
                help_text="What type of draft is this?",
                options=[
                    "First Draft",
                    "Second Draft",
                    "Revision",
                    "Final Draft",
                    "Excerpt",
                    "Sample Chapter",
                    "Complete Manuscript",
                    "Work in Progress"
                ],
                default_value="First Draft"
            ),
            FieldDefinition(
                name="current_word_count",
                label="Current Word Count",
                field_type="number_input",
                help_text="Current word count of this draft",
                min_value=0,
                max_value=500000,
                default_value=0
            ),
            FieldDefinition(
                name="target_word_count",
                label="Target Word Count",
                field_type="number_input",
                help_text="Target word count for the completed work",
                min_value=0,
                max_value=500000,
                default_value=80000
            ),
            FieldDefinition(
                name="completion_percentage",
                label="Completion Percentage",
                field_type="slider",
                help_text="How complete is this draft?",
                min_value=0,
                max_value=100,
                default_value=0
            ),
            FieldDefinition(
                name="writing_stage",
                label="Writing Stage",
                field_type="selectbox",
                help_text="What stage of the writing process is this?",
                options=[
                    "Brainstorming",
                    "Outlining",
                    "First Draft",
                    "Self-Editing",
                    "Beta Reading",
                    "Professional Editing",
                    "Revision",
                    "Final Polish",
                    "Ready for Submission"
                ],
                default_value="First Draft"
            ),
            FieldDefinition(
                name="revision_notes",
                label="Revision Notes",
                field_type="text_area",
                help_text="Notes about what needs to be revised or improved",
                placeholder="Need to strengthen character motivation in chapter 3...",
                required=False
            ),
            FieldDefinition(
                name="writing_goals",
                label="Writing Goals",
                field_type="text_area",
                help_text="What are you trying to achieve with this draft?",
                placeholder="Focus on dialogue, improve pacing...",
                required=False
            ),
            FieldDefinition(
                name="feedback_received",
                label="Feedback Status",
                field_type="selectbox",
                help_text="Have you received feedback on this draft?",
                options=[
                    "No Feedback Yet",
                    "Self-Review Only",
                    "Peer Feedback",
                    "Beta Reader Feedback",
                    "Professional Feedback",
                    "Multiple Sources"
                ],
                default_value="No Feedback Yet"
            ),
            FieldDefinition(
                name="submission_ready",
                label="Submission Ready",
                field_type="selectbox",
                help_text="Is this ready for submission to agents/publishers?",
                options=[
                    "Not Ready",
                    "Needs Minor Revisions",
                    "Needs Major Revisions",
                    "Nearly Ready",
                    "Ready for Submission"
                ],
                default_value="Not Ready"
            )
        ]
        
        # Insert draft-specific fields after title but before genre
        title_index = next(i for i, f in enumerate(fields) if f.name == "title")
        for i, field in enumerate(draft_fields):
            fields.insert(title_index + 1 + i, field)
        
        return fields