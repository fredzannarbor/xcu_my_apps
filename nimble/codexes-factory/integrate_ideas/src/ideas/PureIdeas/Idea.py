import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Iterable
import ollama


@dataclass
class Idea:
    """Base class for creative ideas before they're developed into specific book concepts.
    Currently strings only. In future, will support multimodal descriptions.
    """
    description_of_idea: str = field(default="book idea")


    def __post_init__(self):
        """Initialize the created_date if not provided."""

        # Ensure description is not empty
        if not self.description_of_idea or not self.description_of_idea.strip():
            raise ValueError("Idea must have a description")

    def is_specific_enough_for_book(self) -> bool:
        """
        Determine if this idea is specific enough to be developed into a book.
        Current implementation uses simple word count as a baseline metric.
        """
        return True

    def __str__(self) -> str:
        """String representation of the idea."""
        return f"Idea: {self.description_of_idea[:100]}..."

    def __repr__(self) -> str:
        """Detailed string representation of the idea."""
        return f"Idea(description_of_idea='{self.description_of_idea[:50]}...')"

    def create_idea(self, prompt_template: str = None) -> None:
        """
        Generate content for an Idea using LLM.
        Convenience method.  Usually replaced in practice by more complex idea-creators.

        Args:
            prompt_template: Optional custom prompt template. If None, uses default template.
        """
        content = ""
        if prompt_template:
            prompt = prompt_template
        else:
            prompt = """
            You are an AI book publisher and editor with exhaustive knowledge of all genres of publishing.  At this stage, your goal is to create a promising idea for a book or books, which you will express as a one- paragraph string. No fields, just a concise string of under 25 words.
            """

        try:
            response = ollama.generate(model='mistral', prompt=prompt)

            # Parse the JSON response
            content = json.loads(response['response'])
            print("*****")
            print(content)
            print("*****")
            return content

        except Exception as e:
            print(f"Error generating idea: {e}")

class IdeaSet:
    """A collection of ideas with basic management functionality."""

    def __init__(self, ideas=None):
        self.ideas = ideas if ideas is not None else []
        # add self._ideas
        self._ideas = []

    def add_idea(self, idea: Idea):
        """Add an idea to the collection."""
        self._ideas.append(idea)

    def get_ideas(self) -> Iterable[Idea]:
        """Get all ideas in the collection."""
        return self._ideas

    def __len__(self) -> int:
        """Get the number of ideas in the collection."""
        return len(self._ideas)

    # print ideas in set
    def __str__(self) -> str:
        """String representation of the idea set."""
