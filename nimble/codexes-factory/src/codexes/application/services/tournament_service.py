"""
Application service for tournament management.

This service coordinates tournament lifecycle, from creation through
voting to winner selection and imprint creation.
"""

from typing import Optional, List, Dict, Any

from ...domain.models.tournament import (
    Tournament,
    ImprintIdea,
    TournamentStatus,
)
from ...domain.models.imprint import (
    Imprint,
    BrandingSpecification,
    PublishingFocus,
)
from ...infrastructure.repositories.tournament_repository import TournamentRepository
from .imprint_creation_service import ImprintCreationService


class TournamentService:
    """
    Service for managing imprint idea tournaments.

    Coordinates tournament creation, idea submission, voting,
    and conversion of winning ideas to imprints.
    """

    def __init__(
        self,
        repository: TournamentRepository,
        imprint_service: ImprintCreationService,
        idea_generator: Optional[Any] = None,
    ):
        """
        Initialize the tournament service.

        Args:
            repository: Repository for tournament persistence
            imprint_service: Service for creating imprints
            idea_generator: Optional AI generator for ideas
        """
        self.repository = repository
        self.imprint_service = imprint_service
        self.idea_generator = idea_generator

    def create_tournament(
        self,
        name: str,
        size: int,
        criteria: str,
        allow_public_voting: bool = False,
    ) -> Tournament:
        """
        Create a new tournament.

        Args:
            name: Tournament name
            size: Number of ideas (4, 8, 16, or 32)
            criteria: Evaluation criteria
            allow_public_voting: Whether to allow public voting

        Returns:
            Tournament: The created tournament

        Raises:
            ValueError: If tournament parameters are invalid
            IOError: If save operation fails
        """
        tournament = Tournament(
            name=name,
            tournament_size=size,
            evaluation_criteria=criteria,
            allow_public_voting=allow_public_voting,
        )

        # Save to repository
        self.repository.save(tournament)

        return tournament

    def add_user_idea(
        self,
        tournament: Tournament,
        name: str,
        charter: str,
        focus: str,
    ) -> ImprintIdea:
        """
        Add a user-submitted idea to the tournament.

        Args:
            tournament: Tournament to add idea to
            name: Imprint name
            charter: Mission statement
            focus: Publishing focus description

        Returns:
            ImprintIdea: The created idea

        Raises:
            ValueError: If tournament is full or already started
            IOError: If save operation fails
        """
        idea = ImprintIdea(
            name=name,
            charter=charter,
            focus=focus,
            source="user",
        )

        tournament.add_idea(idea)
        self.repository.save(tournament)

        return idea

    def generate_ai_ideas(
        self,
        tournament: Tournament,
        count: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ImprintIdea]:
        """
        Generate AI ideas for the tournament.

        Args:
            tournament: Tournament to add ideas to
            count: Number of ideas to generate
            context: Optional context for generation

        Returns:
            List of generated ImprintIdea objects

        Raises:
            ValueError: If AI generator not configured or tournament is full
            IOError: If save operation fails
        """
        if not self.idea_generator:
            raise ValueError(
                "AI generator not configured. Cannot generate AI ideas."
            )

        available_slots = tournament.tournament_size - len(tournament.ideas)
        if count > available_slots:
            raise ValueError(
                f"Cannot generate {count} ideas. Only {available_slots} slots available."
            )

        ideas = []
        for i in range(count):
            # Generate idea using AI
            # This is a placeholder - actual implementation would call LLM
            idea_data = self._generate_single_idea(
                tournament=tournament,
                context=context,
                iteration=i,
            )

            idea = ImprintIdea(
                name=idea_data['name'],
                charter=idea_data['charter'],
                focus=idea_data['focus'],
                source="ai",
            )

            tournament.add_idea(idea)
            ideas.append(idea)

        # Save tournament with new ideas
        self.repository.save(tournament)

        return ideas

    def start_tournament(self, tournament: Tournament) -> None:
        """
        Start a tournament and create brackets.

        Args:
            tournament: Tournament to start

        Raises:
            ValueError: If tournament cannot be started
            IOError: If save operation fails
        """
        tournament.start()
        self.repository.save(tournament)

        # Set as active tournament
        self.repository.set_active(tournament)

    def record_vote(
        self,
        tournament: Tournament,
        matchup_id: str,
        idea_id: str,
    ) -> None:
        """
        Record a vote in a tournament matchup.

        Args:
            tournament: Tournament containing the matchup
            matchup_id: ID of matchup to vote in
            idea_id: ID of idea to vote for

        Raises:
            ValueError: If matchup or idea not found
            IOError: If save operation fails
        """
        # Find the matchup in the current round
        current_round = tournament.get_current_round()
        if not current_round:
            raise ValueError("No active round found")

        matchup = None
        for m in current_round.matchups:
            if m.id == matchup_id:
                matchup = m
                break

        if not matchup:
            raise ValueError(f"Matchup '{matchup_id}' not found in current round")

        # Record the vote
        matchup.vote_for(idea_id)

        # Update idea vote count
        idea = tournament.get_idea_by_id(idea_id)
        if idea:
            idea.vote()

        # Save tournament
        self.repository.save(tournament)

        # Check if round is complete and advance if needed
        if current_round.is_complete:
            self._try_advance_tournament(tournament)

    def get_active_tournament(self) -> Optional[Tournament]:
        """
        Get the currently active tournament.

        Returns:
            Tournament or None if no active tournament
        """
        return self.repository.get_active()

    def create_imprint_from_winner(
        self,
        tournament: Tournament,
        publisher: str = "Tournament Winner",
        branding_config: Optional[Dict[str, Any]] = None,
    ) -> Imprint:
        """
        Create an imprint from the tournament winner.

        Args:
            tournament: Completed tournament
            publisher: Publisher name for the imprint
            branding_config: Optional branding configuration

        Returns:
            Imprint: Created imprint from winning idea

        Raises:
            ValueError: If tournament is not complete or has no winner
            IOError: If creation fails
        """
        if tournament.status != TournamentStatus.COMPLETED:
            raise ValueError("Tournament must be completed to create imprint")

        if not tournament.winner:
            raise ValueError("Tournament has no winner")

        winner = tournament.winner

        # Create branding from config or defaults
        branding_data = branding_config or {}
        branding = BrandingSpecification(
            display_name=branding_data.get('display_name', winner.name),
            tagline=branding_data.get('tagline', f"Winner of {tournament.name}"),
            mission_statement=branding_data.get('mission_statement', winner.charter),
            brand_values=branding_data.get('brand_values', []),
            primary_color=branding_data.get('primary_color'),
            secondary_color=branding_data.get('secondary_color'),
            font_family=branding_data.get('font_family'),
        )

        # Parse focus into publishing focus
        # This is simplified - in production, would use AI to parse
        publishing_focus = PublishingFocus(
            primary_genres=self._extract_genres(winner.focus),
            target_audience=self._extract_audience(winner.focus),
        )

        # Create imprint using imprint service
        imprint = self.imprint_service.create_from_wizard(
            name=winner.name,
            publisher=publisher,
            charter=winner.charter,
            branding=branding,
            publishing_focus=publishing_focus,
            auto_activate=False,
        )

        return imprint

    def advance_round_manually(self, tournament: Tournament) -> None:
        """
        Manually advance tournament to next round.

        Args:
            tournament: Tournament to advance

        Raises:
            ValueError: If round cannot be advanced
            IOError: If save operation fails
        """
        tournament.advance_round()
        self.repository.save(tournament)

    def _try_advance_tournament(self, tournament: Tournament) -> None:
        """
        Try to advance tournament if current round is complete.

        Args:
            tournament: Tournament to potentially advance
        """
        current_round = tournament.get_current_round()

        if current_round and current_round.is_complete:
            try:
                tournament.advance_round()
                self.repository.save(tournament)
            except ValueError:
                # Round complete but can't advance (probably tournament done)
                pass

    def _generate_single_idea(
        self,
        tournament: Tournament,
        context: Optional[Dict[str, Any]],
        iteration: int,
    ) -> Dict[str, Any]:
        """
        Generate a single imprint idea using AI.

        This is a placeholder implementation. In production, this would
        call an LLM API to generate the idea.

        Args:
            tournament: Tournament context
            context: Additional context
            iteration: Iteration number for uniqueness

        Returns:
            Dict containing idea data
        """
        # Placeholder implementation
        # In production, this would call the AI generator
        return {
            'name': f'AI Idea {iteration + 1}',
            'charter': f'AI generated charter based on {tournament.evaluation_criteria}',
            'focus': 'AI generated focus description',
        }

    def _extract_genres(self, focus_text: str) -> List[str]:
        """
        Extract genres from focus text.

        Placeholder implementation - in production would use NLP or LLM.

        Args:
            focus_text: Focus description

        Returns:
            List of genre strings
        """
        # Simple keyword extraction
        genres = []
        genre_keywords = {
            'fiction': 'Fiction',
            'mystery': 'Mystery',
            'science fiction': 'Science Fiction',
            'fantasy': 'Fantasy',
            'romance': 'Romance',
            'thriller': 'Thriller',
            'horror': 'Horror',
            'literary': 'Literary Fiction',
            'young adult': 'Young Adult',
            'children': 'Children\'s',
        }

        focus_lower = focus_text.lower()
        for keyword, genre in genre_keywords.items():
            if keyword in focus_lower:
                genres.append(genre)

        return genres if genres else ['General Fiction']

    def _extract_audience(self, focus_text: str) -> str:
        """
        Extract target audience from focus text.

        Placeholder implementation - in production would use NLP or LLM.

        Args:
            focus_text: Focus description

        Returns:
            Audience description
        """
        # Simple keyword detection
        focus_lower = focus_text.lower()

        if 'young adult' in focus_lower or 'ya' in focus_lower:
            return 'Young Adult readers'
        elif 'children' in focus_lower:
            return 'Children and families'
        elif 'academic' in focus_lower:
            return 'Academic and professional readers'
        else:
            return 'General readers'

    def __repr__(self) -> str:
        return f"TournamentService(repository={self.repository})"
