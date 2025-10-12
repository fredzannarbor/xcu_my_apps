# ideas/transformers/idea_transformer.py

import logging
from typing import List, Optional
from src.ideas.PureIdeas.Idea import Idea, IdeaSet
from src.ideas.BookClasses import BookIdeaSet
from src.ideas.BookClasses.BookIdea import BookIdea
from src.ideas.BookClasses.Model2BookIdeas import Models2BookIdeas

class IdeaTransformer:
    """
    Transforms Ideas into BookIdeas with support for 1:1, 1:many, and many:many transformations.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the transformer with optional custom logger.

        Args:
            logger: Optional custom logger. If None, creates a module-specific logger.
        """
        self.logger = logger or logging.getLogger(__name__)
        self.expander = Models2BookIdeas()  # For generating variations

    def transform_single(self, idea: Idea) -> BookIdea:
        """
        Transform a single Idea into a BookIdea (1:1 transformation).

        Args:
            idea: Source Idea object

        Returns:
            BookIdea: Transformed book idea
        """
        try:
            book_idea = BookIdea(
                title="TK",
                description_of_idea=idea.description_of_idea,
                genre="",  # To be filled by user/system late
                logline="test",#idea.get_summary() if hasattr(idea, 'get_summary') else "",
                key_themes=[],  # To be derived from content anar
                target_audience="General",
                estimated_length="Novel",
                notes=f"Transformed from Idea: {idea.id if hasattr(idea, 'id') else 'Unknown'}"
            )

            self.logger.debug(f"Successfully transformed idea '{idea.title}' to BookIdea")
            return book_idea

        except Exception as e:
            self.logger.error(f"Error transforming idea: {str(e)}")
            raise

    def transform_to_multiple(self, idea: Idea, variations: int = 3) -> List[BookIdea]:
        """
        Transform a single Idea into multiple BookIdeas (1:many transformation).

        Args:
            idea: Source Idea object
            variations: Number of variations to generate

        Returns:
            List[BookIdea]: List of transformed book ideas including variations
        """
        try:
            # Create base BookIdea
            base_book_idea = self.transform_single(idea)
            self.logger.info = idea.__repr__()
            variations_list = [base_book_idea]

            # Generate variations using existing Models2BookIdeas
            try:
                additional_variations = self.expander.expand_idea(base_book_idea, variations)
                variations_list.extend(additional_variations)
            except Exception as e:
                self.logger.warning(f"Error generating variations: {str(e)}. Returning base idea only.")

            return variations_list

        except Exception as e:
            self.logger.error(f"Error in transform_to_multiple: {str(e)}")
            raise

    def transform_set(self, ideas: List[Idea], variations_per_idea: int = 2) -> BookIdeaSet:
        """
        Transform multiple Ideas into a BookIdeaSet (many:many transformation).

        Args:
            ideas: List of source Idea objects
            variations_per_idea: Number of variations to generate per idea

        Returns:
            BookIdeaSet: Set containing all transformed ideas and their variations
        """
        try:
            book_idea_set = BookIdeaSet()

            for idea in ideas:
                try:
                    variations = self.transform_to_multiple(idea, variations_per_idea)
                    for book_idea in variations:
                        book_idea_set.add_idea(book_idea)
                except Exception as e:
                    self.logger.warning(f"Error processing idea '{idea.title}': {str(e)}")
                    continue

            return book_idea_set

        except Exception as e:
            self.logger.error(f"Error in transform_set: {str(e)}")
            raise
