# book_idea_series.py
from typing import Set, Optional, Dict, List
from .book_idea import BookIdea
from .book_idea_set import BookIdeaSet
import logging

logger = logging.getLogger(__name__)


class BookIdeaSeries(BookIdeaSet):
    """
    Manages a collection of book ideas that belong to the same series.
    """

    def __init__(self, series_name: str, ideas: Optional[Set[BookIdea]] = None) -> None:
        """
        Initialize a series-specific collection of book ideas.

        Args:
            series_name: Name of the series
            ideas: Optional set of BookIdea objects that belong to this series
        """
        super().__init__(ideas)
        self.series_name = series_name
        self.series_metadata: Dict[str, str] = {
            'series_name': series_name,
            'reading_order': 'chronological',  # default value
            'target_books': '0',  # planned number of books
            'series_status': 'active'
        }

    def add_idea(self, title: Optional[str] = None, logline: Optional[str] = None,
                 description: Optional[str] = None, note: Optional[str] = None,
                 book_number: Optional[int] = None) -> BookIdea:
        """
        Adds a new book idea to the series with series-specific metadata.

        Args:
            title: The title of the book idea
            logline: A one-sentence summary of the book idea
            description: Detailed description of the book idea
            note: Additional notes about the book idea
            book_number: The book's position in the series

        Returns:
            BookIdea: The newly created and added BookIdea object
        """
        idea = super().add_idea(title, logline, description, note)
        idea.series_info = {
            'series_name': self.series_name,
            'book_number': book_number,
            'series_arc_role': ''  # How this book contributes to the overall series arc
        }
        logger.info(f"Added new idea to series '{self.series_name}': {title if title else 'Untitled'}")
        return idea

    def reorder_books(self, new_order: List[BookIdea]) -> None:
        """
        Reorders the books in the series.

        Args:
            new_order: List of BookIdea objects in their new order
        """
        if set(new_order) != self.ideas:
            raise ValueError("New order must contain exactly the same books as the current series")

        for index, book in enumerate(new_order, 1):
            if hasattr(book, 'series_info'):
                book.series_info['book_number'] = index

        logger.info(f"Reordered books in series '{self.series_name}'")

    def get_series_metadata(self) -> Dict[str, str]:
        """Returns the series metadata."""
        return self.series_metadata

    def update_series_metadata(self, **kwargs) -> None:
        """
        Updates the series metadata.

        Args:
            **kwargs: Key-value pairs of metadata to update
        """
        self.series_metadata.update(kwargs)
        logger.info(f"Updated metadata for series '{self.series_name}'")


# book_ideas_by_imprint.py
class BookIdeasByImprint(BookIdeaSet):
    """
    Manages a collection of book ideas associated with a specific publishing imprint.
    """

    def __init__(self, imprint_name: str, ideas: Optional[Set[BookIdea]] = None) -> None:
        """
        Initialize an imprint-specific collection of book ideas.

        Args:
            imprint_name: Name of the publishing imprint
            ideas: Optional set of BookIdea objects for this imprint
        """
        super().__init__(ideas)
        self.imprint_name = imprint_name
        self.imprint_metadata: Dict[str, str] = {
            'imprint_name': imprint_name,
            'target_audience': '',
            'genre_focus': '',
            'typical_length': '',
            'active_status': 'active'
        }

    def add_idea(self, title: Optional[str] = None, logline: Optional[str] = None,
                 description: Optional[str] = None, note: Optional[str] = None,
                 genre: Optional[str] = None, target_length: Optional[str] = None) -> BookIdea:
        """
        Adds a new book idea to the imprint with imprint-specific metadata.

        Args:
            title: The title of the book idea
            logline: A one-sentence summary of the book idea
            description: Detailed description of the book idea
            note: Additional notes about the book idea
            genre: The book's genre within the imprint's focus
            target_length: Target word count or book length

        Returns:
            BookIdea: The newly created and added BookIdea object
        """
        idea = super().add_idea(title, logline, description, note)
        idea.imprint_info = {
            'imprint_name': self.imprint_name,
            'genre': genre,
            'target_length': target_length,
            'market_position': ''  # How this book fits the imprint's market
        }
        logger.info(f"Added new idea to imprint '{self.imprint_name}': {title if title else 'Untitled'}")
        return idea

    def get_ideas_by_genre(self, genre: str) -> Set[BookIdea]:
        """
        Returns all ideas in the imprint matching a specific genre.

        Args:
            genre: The genre to filter by

        Returns:
            Set of BookIdea objects in the specified genre
        """
        return {idea for idea in self.ideas
                if hasattr(idea, 'imprint_info')
                and idea.imprint_info.get('genre') == genre}

    def get_imprint_metadata(self) -> Dict[str, str]:
        """Returns the imprint metadata."""
        return self.imprint_metadata

    def update_imprint_metadata(self, **kwargs) -> None:
        """
        Updates the imprint metadata.

        Args:
            **kwargs: Key-value pairs of metadata to update
        """
        self.imprint_metadata.update(kwargs)
        logger.info(f"Updated metadata for imprint '{self.imprint_name}'")

    def get_imprint_statistics(self) -> Dict[str, Any]:
        """
        Returns statistical information about the imprint's ideas.

        Returns:
            Dictionary containing various statistics about the ideas in this imprint
        """
        stats = super().get_statistics()
        genres = {idea.imprint_info['genre']
                  for idea in self.ideas
                  if hasattr(idea, 'imprint_info')
                  and idea.imprint_info.get('genre')}

        stats.update({
            'genres_count': len(genres),
            'genres': list(genres),
            'avg_target_length': self._calculate_average_length()
        })
        return stats

    def _calculate_average_length(self) -> Optional[float]:
        """Calculate average target length of books in the imprint."""
        lengths = [float(idea.imprint_info['target_length'].replace('k', '000'))
                   for idea in self.ideas
                   if hasattr(idea, 'imprint_info')
                   and idea.imprint_info.get('target_length')
                   and idea.imprint_info['target_length'].replace('k', '000').isdigit()]

        return sum(lengths) / len(lengths) if lengths else None
