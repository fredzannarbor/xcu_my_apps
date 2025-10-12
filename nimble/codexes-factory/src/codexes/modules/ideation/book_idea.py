"""
Book idea data models and management classes.
Enhanced version of the original Idea class with codexes-factory integration.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Iterable
from pathlib import Path

from ...core.llm_integration import LLMCaller

logger = logging.getLogger(__name__)


@dataclass
class BookIdea:
    """Enhanced version of the Idea class with codexes-factory integration."""
    title: str = ""
    logline: str = ""
    description: str = ""
    genre: str = ""
    target_audience: str = ""
    imprint_alignment: float = 0.0
    tournament_performance: Dict[str, Any] = field(default_factory=dict)
    reader_feedback: List[Dict[str, Any]] = field(default_factory=list)
    generation_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "generated"  # generated, tournament, reader_review, approved, rejected
    seed: Optional[int] = None

    def __post_init__(self):
        """Initialize and validate the book idea."""
        if not self.title and not self.logline:
            raise ValueError("BookIdea must have either a title or logline")
        
        # Ensure we have a title if only logline is provided
        if not self.title and self.logline:
            self.title = self.logline[:50] + "..." if len(self.logline) > 50 else self.logline

    def is_specific_enough_for_book(self) -> bool:
        """
        Determine if this idea is specific enough to be developed into a book.
        Enhanced logic considering multiple factors.
        """
        # Check if we have sufficient detail
        has_title = bool(self.title and len(self.title.strip()) > 5)
        has_logline = bool(self.logline and len(self.logline.strip()) > 20)
        has_description = bool(self.description and len(self.description.strip()) > 50)
        
        # At minimum, need title and logline
        if not (has_title and has_logline):
            return False
            
        # Bonus points for additional detail
        detail_score = sum([has_title, has_logline, has_description, bool(self.genre), bool(self.target_audience)])
        return detail_score >= 3

    def to_dict(self) -> Dict[str, Any]:
        """Convert BookIdea to dictionary format."""
        return {
            'title': self.title,
            'logline': self.logline,
            'description': self.description,
            'genre': self.genre,
            'target_audience': self.target_audience,
            'imprint_alignment': self.imprint_alignment,
            'tournament_performance': self.tournament_performance,
            'reader_feedback': self.reader_feedback,
            'generation_metadata': self.generation_metadata,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'status': self.status,
            'seed': self.seed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BookIdea':
        """Create BookIdea from dictionary format."""
        # Handle datetime conversion
        if 'created_at' in data and isinstance(data['created_at'], str):
            try:
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            except ValueError:
                data['created_at'] = datetime.now()
        
        return cls(**data)

    def create_idea_with_llm(self, llm_caller: LLMCaller, prompt_template: str = None) -> None:
        """
        Generate content for a BookIdea using LLM.
        Enhanced version using codexes-factory LLM infrastructure.
        """
        if prompt_template:
            prompt = prompt_template
        else:
            prompt = """
            You are an AI book publisher and editor with exhaustive knowledge of all genres of publishing. 
            Create a promising book idea with the following format:
            
            Title: [Compelling book title]
            Logline: [One sentence description of the book's core concept]
            Description: [2-3 sentence expanded description]
            Genre: [Primary genre]
            Target Audience: [Primary target audience]
            
            Make the idea commercially viable and engaging for modern readers.
            """

        try:
            response = llm_caller.call_llm(
                prompt=prompt,
                model="mistral",
                temperature=0.7
            )
            
            if response and response.get('content'):
                content = response['content']
                self._parse_llm_response(content)
                self.generation_metadata['llm_generated'] = True
                self.generation_metadata['generation_time'] = datetime.now().isoformat()
                
        except Exception as e:
            logger.error(f"Error generating idea with LLM: {e}")
            # Fallback to basic idea if LLM fails
            if not self.title:
                self.title = "Generated Book Idea"
            if not self.logline:
                self.logline = "A compelling story waiting to be told."

    def _parse_llm_response(self, content: str):
        """Parse LLM response and extract book idea components."""
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('Title:'):
                self.title = line.replace('Title:', '').strip()
            elif line.startswith('Logline:'):
                self.logline = line.replace('Logline:', '').strip()
            elif line.startswith('Description:'):
                self.description = line.replace('Description:', '').strip()
            elif line.startswith('Genre:'):
                self.genre = line.replace('Genre:', '').strip()
            elif line.startswith('Target Audience:'):
                self.target_audience = line.replace('Target Audience:', '').strip()

    def __str__(self) -> str:
        """String representation of the book idea."""
        return f"BookIdea: {self.title[:50]}..."

    def __repr__(self) -> str:
        """Detailed string representation of the book idea."""
        return f"BookIdea(title='{self.title[:30]}...', status='{self.status}')"


class IdeaSet:
    """A collection of book ideas with management functionality."""

    def __init__(self, ideas: Optional[List[BookIdea]] = None):
        self._ideas: List[BookIdea] = ideas if ideas is not None else []
        self.metadata: Dict[str, Any] = {}

    def add_idea(self, idea: BookIdea):
        """Add an idea to the collection."""
        if not isinstance(idea, BookIdea):
            raise TypeError("Only BookIdea instances can be added")
        self._ideas.append(idea)

    def remove_idea(self, idea: BookIdea):
        """Remove an idea from the collection."""
        if idea in self._ideas:
            self._ideas.remove(idea)

    def get_ideas(self) -> List[BookIdea]:
        """Get all ideas in the collection."""
        return self._ideas.copy()

    def get_ideas_by_status(self, status: str) -> List[BookIdea]:
        """Get ideas filtered by status."""
        return [idea for idea in self._ideas if idea.status == status]

    def get_ideas_by_genre(self, genre: str) -> List[BookIdea]:
        """Get ideas filtered by genre."""
        return [idea for idea in self._ideas if idea.genre.lower() == genre.lower()]

    def filter_ideas(self, filter_func) -> List[BookIdea]:
        """Filter ideas using a custom function."""
        return [idea for idea in self._ideas if filter_func(idea)]

    def sort_ideas(self, key_func, reverse: bool = False) -> List[BookIdea]:
        """Sort ideas using a custom key function."""
        return sorted(self._ideas, key=key_func, reverse=reverse)

    def save_to_json(self, file_path: str):
        """Save the idea set to a JSON file."""
        data = {
            'metadata': self.metadata,
            'ideas': [idea.to_dict() for idea in self._ideas],
            'saved_at': datetime.now().isoformat()
        }
        
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_from_json(self, file_path: str):
        """Load ideas from a JSON file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            self.metadata = data.get('metadata', {})
            ideas_data = data.get('ideas', [])
            self._ideas = [BookIdea.from_dict(idea_data) for idea_data in ideas_data]
            
        except Exception as e:
            logger.error(f"Error loading ideas from {file_path}: {e}")
            raise

    def save_to_csv(self, file_path: str):
        """Save ideas to CSV format for compatibility."""
        import pandas as pd
        
        if not self._ideas:
            logger.warning("No ideas to save to CSV")
            return
            
        # Convert ideas to DataFrame
        data = []
        for idea in self._ideas:
            row = {
                'title': idea.title,
                'logline': idea.logline,
                'description': idea.description,
                'genre': idea.genre,
                'target_audience': idea.target_audience,
                'status': idea.status,
                'created_at': idea.created_at.isoformat() if isinstance(idea.created_at, datetime) else idea.created_at,
                'imprint_alignment': idea.imprint_alignment
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(file_path, index=False)

    def __len__(self) -> int:
        """Get the number of ideas in the collection."""
        return len(self._ideas)

    def __iter__(self):
        """Make the collection iterable."""
        return iter(self._ideas)

    def __str__(self) -> str:
        """String representation of the idea set."""
        return f"IdeaSet with {len(self._ideas)} ideas"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"IdeaSet(ideas={len(self._ideas)}, metadata={self.metadata})"