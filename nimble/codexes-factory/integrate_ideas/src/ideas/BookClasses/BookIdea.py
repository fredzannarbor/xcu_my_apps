
from src.ideas.PureIdeas.Idea import Idea

class BookIdea(Idea):
    # title property
    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value: str):
        if not value:
            raise ValueError("Title cannot be empty.")
        self._title = value

    # logline property
    @property
    def logline(self):
        return self._logline

    @logline.setter
    def logline(self, value: str):
        if not value:
            raise ValueError("Logline cannot be empty.")
        self._logline = value

    # description_of_idea property
    @property
    def description_of_idea(self):
        return self.description_of_idea

    @description_of_idea.setter
    def description_of_idea(self, value: str):
        self.description_of_idea = value

    def __init__(self,
                 title: str,
                 logline: str,
                 description_of_idea: str = None,
                 genre: str = None,
                 target_audience: str = None,
                 estimated_length: int = None,
                 key_themes: list[str] = None,
                 notes: str = None) -> None:



        """
        Represents an idea specifically for a codex-style book (immersive linear text).
        Only title and logline are required at creation - other fields can be populated
        during idea development.

        Args:
            title: Working or final title of the book (required).
            logline: One-sentence summary of the book's premise (required).
            description_of_idea: The core concept of the book (optional).
            genre: Primary genre classification (optional).
            target_audience: Intended readership (optional).
            estimated_length: Approximate word count (optional).
            key_themes: List of main themes in the book (optional).
            notes: Additional thoughts, references, or development ideas (optional).
        """
        super().__init__(self.description_of_idea)
        if not title or not logline:
            raise ValueError("Both title and logline are required for a BookIdea")

        self.title = title
        self.logline = logline
        self.genre = genre
        self.target_audience = target_audience
        self.estimated_length = estimated_length
        self.key_themes = key_themes or []
        self.notes = notes

    def __hash__(self):
        # Only include title and logline in hash as they are the core required fields
        return hash((self.title, self.logline))

    def __eq__(self, other):
        if not isinstance(other, BookIdea):
            return False
        # Primary equality check on required fields
        return (self.title == other.title and
                self.logline == other.logline)

    def is_fully_developed(self) -> bool:
        """
        Checks if all optional fields have been populated during development.
        """
        return all([
            self.description_of_idea,
            self.genre,
            self.target_audience,
            self.estimated_length,
            self.key_themes,
            self.notes
        ])

    def to_minimal_pitch(self) -> str:
        """
        Generate a basic pitch using just the required elements.
        """
        return f"TITLE: {self.title}\nLOGLINE: {self.logline}"

    def to_full_pitch(self) -> str:
        """
        Generate a complete pitch including any available optional elements.
        """
        pitch_parts = [self.to_minimal_pitch()]

        if self.description_of_idea:
            pitch_parts.append(f"CONCEPT: {self.description_of_idea}")
        if self.genre:
            pitch_parts.append(f"GENRE: {self.genre}")
        if self.target_audience:
            pitch_parts.append(f"TARGET AUDIENCE: {self.target_audience}")
        if self.key_themes:
            themes = ", ".join(self.key_themes)
            pitch_parts.append(f"THEMES: {themes}")
        if self.estimated_length:
            pitch_parts.append(f"ESTIMATED LENGTH: {self.estimated_length:,} words")
        if self.notes:
            pitch_parts.append(f"NOTES: {self.notes}")

        return "\n".join(pitch_parts)
    

    




