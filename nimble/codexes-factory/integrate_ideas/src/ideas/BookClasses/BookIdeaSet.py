# book_idea_set.py
import traceback
from typing import Set, List, Optional, Dict, Any
from pathlib import Path
import pandas as pd
import json
import csv
import logging

#from src.ideas.BookClasses import BookIdea
from src.ideas.BookClasses.BookIdea import BookIdea  # Assuming BookIdea is in book_idea.py in the same directory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BookIdeaSet:
    """
    A collection class for managing sets of book ideas with file I/O capabilities.
    """

    def __init__(self, ideas: Optional[Set[BookIdea]] = None) -> None:
        """
        Initialize a set of book ideas.

        Args:
            ideas: Optional set of BookIdea objects. If None, creates an empty set.
        """
        self.ideas: Set[BookIdea] = ideas if ideas is not None else set()
        self.num_ideas: int = len(self.ideas)

    def __len__(self) -> int:
        """Returns the number of ideas in the set."""
        return self.num_ideas

    def __iter__(self):
        """Makes the class iterable over its ideas."""
        return iter(self.ideas)

    def __contains__(self, item: BookIdea) -> bool:
        """Enables 'in' operator for checking if an idea exists in the set."""
        return item in self.ideas

    def add_idea(self, title: Optional[str] = None, logline: Optional[str] = None,
                 description_of_idea: Optional[str] = None) -> BookIdea:
        idea = BookIdea(title, logline)  # Match the parameter name with __init__
        idea.title = title
        idea.logline = logline
        self.ideas.add(idea)
        self.num_ideas = len(self.ideas)
        logger.info(f"Added new idea: {idea.title if idea.title else 'Untitled'}")
        return idea

    def remove_idea(self, idea: BookIdea) -> bool:
        """
        Removes a book idea from the set.

        Args:
            idea: The BookIdea object to remove

        Returns:
            bool: True if idea was removed, False if it wasn't found
        """
        try:
            self.ideas.remove(idea)
            self.num_ideas = len(self.ideas)
            logger.info(f"Removed idea: {idea.title if idea.title else 'Untitled'}")
            return True
        except KeyError:
            logger.warning("Attempted to remove non-existent idea")
            return False

    def clear(self) -> None:
        """Removes all ideas from the set."""
        self.ideas.clear()
        self.num_ideas = 0
        logger.info("Cleared all ideas from the set")

    def load_ideas_set_from_csv(self, file_path: str) -> list[BookIdea]:
        """
        Loads ideas from a CSV file with enhanced error handling.
    
        Args:
            file_path: Path to the CSV file
    
        Returns:
            List of idea strings
    
        Raises:
            ValueError: If the required 'title' or 'logline' column is missing
            FileNotFoundError: If the file doesn't exist
        """
        try:
            df = pd.read_csv(Path(file_path))
            if 'title' not in df.columns or 'logline' not in df.columns:
                raise ValueError("The CSV file must contain 'title' and 'logline' columns.")

            ideas_added = []
            print("about to iterrow")
            for _, row in df.iterrows():
                title = row.get('title')
                logline = row.get('logline')
                description_of_idea = row.get('description_of_idea')
                if pd.isna(title) or pd.isna(logline):
                    logger.warning("Skipping row with missing title or logline")
                    continue

                book_idea = BookIdea(
                    title=title,
                    logline=logline,
                    description_of_idea=description_of_idea
                )
                self.ideas.add(book_idea)
                ideas_added.append(book_idea)
               # print(type(ideas_added))
            self.num_ideas = len(self.ideas)
            logger.info(f"Successfully loaded {len(ideas_added)} ideas from {file_path}")
            return ideas_added
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading ideas from CSV: {str(e)}")
            raise

    def export_to_format(self, file_path: str, format_type: str = 'json') -> None:
        """
        Exports the idea set to a specified format.

        Args:
            file_path: Path to save the file
            format_type: Format to save as ('json' or 'csv')

        Raises:
            ValueError: If format_type is not supported
        """
        if format_type.lower() == 'json':
            self.save_idea_set_as_json(list(self.ideas), file_path)
        elif format_type.lower() == 'csv':
            self.save_idea_set_as_csv(list(self.ideas), file_path)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")

    @staticmethod
    def save_idea_set_as_json(idea_set: List[BookIdea], file_path: str) -> None:
        """
        Saves a set of BookIdea objects to a JSON file with error handling.

        Args:
            idea_set: List of BookIdea objects
            file_path: Path to save the JSON file
        """
        try:
            data = [idea.to_dict() for idea in idea_set]  # Assuming BookIdea has to_dict method
            with Path(file_path).open('w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            logger.info(f"Successfully saved {len(idea_set)} ideas to {file_path}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {str(e)}")
            raise

    @staticmethod
    def save_idea_set_as_csv(idea_set: List[BookIdea], file_path: str) -> None:
        """
        Saves a set of BookIdea objects to a CSV file with error handling.
        Args:
            idea_set: List of BookIdea objects
            file_path: Path to save the CSV file
        """
        try:
            with Path(file_path).open('w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                # Write header row
                writer.writerow(['title', 'logline', 'description_of_idea', 'genre', 'target_audience', 'estimated_length', 'key_themes', 'notes'])
                # Write data rows
                for idea in idea_set:
                    writer.writerow([
                        idea.title,
                        idea.logline,
                        idea.description_of_idea,
                        idea.genre,
                        idea.target_audience,
                        idea.estimated_length,
                        ','.join(idea.key_themes) if idea.key_themes else '',  # Convert list to comma-separated string
                        idea.notes
                    ])
            logger.info(f"Successfully saved {len(idea_set)} ideas to {file_path}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
            raise




    def load_from_format(self, file_path: str, format_type: str = 'json') -> None:
        """
        Loads ideas from a specified format and adds them to the current set.

        Args:
            file_path: Path to the file to load
            format_type: Format to load from ('json' or 'csv')

        Raises:
            ValueError: If format_type is not supported
        """
        if format_type.lower() == 'json':
            pass
            # loaded_ideas = self.load_idea_set_from_json(file_path)
            # self.ideas.update(loaded_ideas)
        elif format_type.lower() == 'csv':
            loaded_ideas = self.load_ideas_set_from_csv(file_path)
            self.ideas.update(loaded_ideas)
            print('loaded ideas in load_from_format')
            return loaded_ideas
        else:
            raise ValueError(f"Unsupported format type: {format_type}")

        self.num_ideas = len(self.ideas)

    def search_ideas(self, query: str) -> Set[BookIdea]:
        """
        Searches through ideas based on title, logline, or description.

        Args:
            query: Search term to look for

        Returns:
            Set of BookIdea objects that match the search criteria
        """
        query = query.lower()
        return {
            idea for idea in self.ideas
            if any(
                query in str(getattr(idea, field, '')).lower()
                for field in ['title', 'logline', 'description', 'note']
            )
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Returns statistical information about the idea set.

        Returns:
            Dictionary containing various statistics about the ideas
        """
        return {
            'total_ideas': self.num_ideas,
            'ideas_with_titles': sum(1 for idea in self.ideas if idea.title),
            'ideas_with_loglines': sum(1 for idea in self.ideas if idea.logline),
                }

