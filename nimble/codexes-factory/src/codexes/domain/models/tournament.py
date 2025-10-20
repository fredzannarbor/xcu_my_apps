"""
Rich domain model for Tournament entities.

This module defines the tournament system for competing imprint ideas,
including bracket management, voting, and winner selection.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
import uuid


class TournamentStatus(Enum):
    """Lifecycle status of a tournament."""
    SETUP = "setup"
    COLLECTING_IDEAS = "collecting_ideas"
    RUNNING = "running"
    COMPLETED = "completed"


@dataclass
class ImprintIdea:
    """
    Represents a single imprint idea submitted to a tournament.

    Ideas can come from users or AI generation, and compete in
    bracket-style matchups.
    """
    name: str
    charter: str
    focus: str
    source: str  # "user", "ai", "imported"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    votes: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def vote(self) -> None:
        """Increment the vote count for this idea."""
        self.votes += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'charter': self.charter,
            'focus': self.focus,
            'source': self.source,
            'votes': self.votes,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImprintIdea':
        """Create instance from dictionary."""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data['name'],
            charter=data['charter'],
            focus=data['focus'],
            source=data.get('source', 'user'),
            votes=data.get('votes', 0),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
        )

    def __repr__(self) -> str:
        return f"ImprintIdea(id='{self.id[:8]}...', name='{self.name}', votes={self.votes})"

    def __str__(self) -> str:
        return f"{self.name} ({self.votes} votes)"


@dataclass
class Matchup:
    """
    Represents a single matchup between two ideas in a tournament round.

    Tracks voting and determines the winner.
    """
    idea1_id: str
    idea2_id: str
    round_num: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    winner_id: Optional[str] = None
    idea1_votes: int = 0
    idea2_votes: int = 0

    def vote_for(self, idea_id: str) -> None:
        """
        Record a vote for one of the ideas in this matchup.

        Args:
            idea_id: ID of the idea to vote for

        Raises:
            ValueError: If idea_id is not part of this matchup
        """
        if idea_id == self.idea1_id:
            self.idea1_votes += 1
        elif idea_id == self.idea2_id:
            self.idea2_votes += 1
        else:
            raise ValueError(f"Idea {idea_id} is not part of this matchup")

        # Auto-determine winner if vote threshold is met
        self._update_winner()

    def _update_winner(self) -> None:
        """Update winner based on current vote counts."""
        if self.idea1_votes > self.idea2_votes:
            self.winner_id = self.idea1_id
        elif self.idea2_votes > self.idea1_votes:
            self.winner_id = self.idea2_id

    @property
    def is_complete(self) -> bool:
        """Check if this matchup has a winner."""
        return self.winner_id is not None

    @property
    def vote_count(self) -> int:
        """Get total votes for this matchup."""
        return self.idea1_votes + self.idea2_votes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'idea1_id': self.idea1_id,
            'idea2_id': self.idea2_id,
            'round_num': self.round_num,
            'winner_id': self.winner_id,
            'idea1_votes': self.idea1_votes,
            'idea2_votes': self.idea2_votes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Matchup':
        """Create instance from dictionary."""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            idea1_id=data['idea1_id'],
            idea2_id=data['idea2_id'],
            round_num=data['round_num'],
            winner_id=data.get('winner_id'),
            idea1_votes=data.get('idea1_votes', 0),
            idea2_votes=data.get('idea2_votes', 0),
        )

    def __repr__(self) -> str:
        status = "complete" if self.is_complete else "in progress"
        return f"Matchup(round={self.round_num}, votes={self.vote_count}, {status})"


class TournamentRound:
    """
    Represents a single round in a tournament bracket.

    Contains all matchups for that round and tracks completion.
    """

    def __init__(self, round_number: int, matchups: Optional[List[Matchup]] = None):
        """
        Initialize a tournament round.

        Args:
            round_number: Round number (1-indexed)
            matchups: List of matchups in this round
        """
        self.round_number = round_number
        self.matchups = matchups or []

    def add_matchup(self, matchup: Matchup) -> None:
        """
        Add a matchup to this round.

        Args:
            matchup: Matchup to add
        """
        self.matchups.append(matchup)

    @property
    def is_complete(self) -> bool:
        """Check if all matchups in this round are complete."""
        return all(m.is_complete for m in self.matchups) if self.matchups else False

    def get_winners(self) -> List[str]:
        """
        Get list of winner IDs from all matchups.

        Returns:
            List[str]: IDs of ideas that won their matchups
        """
        return [m.winner_id for m in self.matchups if m.winner_id]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'round_number': self.round_number,
            'matchups': [m.to_dict() for m in self.matchups],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TournamentRound':
        """Create instance from dictionary."""
        matchups = [Matchup.from_dict(m) for m in data.get('matchups', [])]
        return cls(
            round_number=data['round_number'],
            matchups=matchups,
        )

    def __repr__(self) -> str:
        complete_count = sum(1 for m in self.matchups if m.is_complete)
        return f"TournamentRound(round={self.round_number}, matchups={len(self.matchups)}, complete={complete_count})"


class Tournament:
    """
    Rich domain model representing an imprint idea tournament.

    Manages the full lifecycle of a bracket-style competition between
    imprint ideas, from setup through voting to winner selection.
    """

    def __init__(
        self,
        name: str,
        tournament_size: int,
        evaluation_criteria: str,
        allow_public_voting: bool = False,
        tournament_id: Optional[str] = None,
        status: TournamentStatus = TournamentStatus.SETUP,
        ideas: Optional[List[ImprintIdea]] = None,
        rounds: Optional[List[TournamentRound]] = None,
        created_at: Optional[datetime] = None,
        started_at: Optional[datetime] = None,
        winner: Optional[ImprintIdea] = None,
    ):
        """
        Initialize a tournament.

        Args:
            name: Tournament name
            tournament_size: Number of ideas (must be power of 2: 4, 8, 16, 32)
            evaluation_criteria: Criteria for judging ideas
            allow_public_voting: Whether to allow public voting
            tournament_id: Unique identifier
            status: Current tournament status
            ideas: List of submitted ideas
            rounds: List of tournament rounds
            created_at: Creation timestamp
            started_at: Start timestamp
            winner: Winning idea (after completion)
        """
        if tournament_size not in [4, 8, 16, 32]:
            raise ValueError("Tournament size must be 4, 8, 16, or 32")

        self.id = tournament_id or str(uuid.uuid4())
        self.name = name
        self.tournament_size = tournament_size
        self.evaluation_criteria = evaluation_criteria
        self.allow_public_voting = allow_public_voting
        self.status = status
        self.ideas = ideas or []
        self.rounds = rounds or []
        self.created_at = created_at or datetime.now()
        self.started_at = started_at
        self.winner = winner

    def add_idea(self, idea: ImprintIdea) -> None:
        """
        Add an idea to the tournament.

        Args:
            idea: ImprintIdea to add

        Raises:
            ValueError: If tournament is full or already started
        """
        if self.status not in [TournamentStatus.SETUP, TournamentStatus.COLLECTING_IDEAS]:
            raise ValueError("Cannot add ideas to a tournament that has started")

        if len(self.ideas) >= self.tournament_size:
            raise ValueError(f"Tournament is full (max {self.tournament_size} ideas)")

        self.ideas.append(idea)

        # Update status to collecting ideas if this is first idea
        if self.status == TournamentStatus.SETUP and len(self.ideas) > 0:
            self.status = TournamentStatus.COLLECTING_IDEAS

    def can_start(self) -> bool:
        """
        Check if tournament has enough ideas to start.

        Returns:
            bool: True if tournament can be started
        """
        return len(self.ideas) == self.tournament_size

    def start(self) -> None:
        """
        Start the tournament and create initial brackets.

        Raises:
            ValueError: If tournament cannot be started
        """
        if not self.can_start():
            raise ValueError(
                f"Tournament needs exactly {self.tournament_size} ideas to start "
                f"(currently has {len(self.ideas)})"
            )

        if self.status == TournamentStatus.RUNNING:
            raise ValueError("Tournament is already running")

        if self.status == TournamentStatus.COMPLETED:
            raise ValueError("Tournament is already completed")

        self.status = TournamentStatus.RUNNING
        self.started_at = datetime.now()
        self._create_brackets()

    def get_current_round(self) -> Optional[TournamentRound]:
        """
        Get the currently active round.

        Returns:
            TournamentRound or None if no active round
        """
        for round_obj in self.rounds:
            if not round_obj.is_complete:
                return round_obj
        return None

    def advance_round(self) -> None:
        """
        Advance to the next round after current round is complete.

        Raises:
            ValueError: If current round is not complete or tournament is over
        """
        current_round = self.get_current_round()

        if current_round and not current_round.is_complete:
            raise ValueError("Cannot advance: current round is not complete")

        if not self.rounds:
            raise ValueError("No rounds exist")

        # Check if we're at the final round
        last_round = self.rounds[-1]
        if last_round.is_complete:
            # Tournament is over, declare winner
            self._declare_winner()
            return

        # Create next round from winners
        winners = current_round.get_winners() if current_round else []
        if len(winners) < 2:
            raise ValueError("Not enough winners to create next round")

        next_round_num = current_round.round_number + 1 if current_round else 1
        next_round = TournamentRound(next_round_num)

        # Create matchups from winners
        for i in range(0, len(winners), 2):
            if i + 1 < len(winners):
                matchup = Matchup(
                    idea1_id=winners[i],
                    idea2_id=winners[i + 1],
                    round_num=next_round_num,
                )
                next_round.add_matchup(matchup)

        self.rounds.append(next_round)

    def get_idea_by_id(self, idea_id: str) -> Optional[ImprintIdea]:
        """
        Find an idea by its ID.

        Args:
            idea_id: ID of idea to find

        Returns:
            ImprintIdea or None if not found
        """
        for idea in self.ideas:
            if idea.id == idea_id:
                return idea
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize tournament to dictionary.

        Returns:
            Dict containing all tournament data
        """
        data = {
            'id': self.id,
            'name': self.name,
            'tournament_size': self.tournament_size,
            'evaluation_criteria': self.evaluation_criteria,
            'allow_public_voting': self.allow_public_voting,
            'status': self.status.value,
            'ideas': [idea.to_dict() for idea in self.ideas],
            'rounds': [round_obj.to_dict() for round_obj in self.rounds],
            'created_at': self.created_at.isoformat(),
        }

        if self.started_at:
            data['started_at'] = self.started_at.isoformat()

        if self.winner:
            data['winner'] = self.winner.to_dict()

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tournament':
        """
        Deserialize tournament from dictionary.

        Args:
            data: Dictionary containing tournament data

        Returns:
            Tournament instance
        """
        ideas = [ImprintIdea.from_dict(i) for i in data.get('ideas', [])]
        rounds = [TournamentRound.from_dict(r) for r in data.get('rounds', [])]

        winner = None
        if 'winner' in data:
            winner = ImprintIdea.from_dict(data['winner'])

        return cls(
            tournament_id=data['id'],
            name=data['name'],
            tournament_size=data['tournament_size'],
            evaluation_criteria=data['evaluation_criteria'],
            allow_public_voting=data.get('allow_public_voting', False),
            status=TournamentStatus(data.get('status', 'setup')),
            ideas=ideas,
            rounds=rounds,
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else None,
            started_at=datetime.fromisoformat(data['started_at']) if 'started_at' in data else None,
            winner=winner,
        )

    def _create_brackets(self) -> None:
        """
        Create the initial tournament bracket structure.

        Creates first round matchups from all submitted ideas.
        """
        if len(self.ideas) != self.tournament_size:
            raise ValueError("Incorrect number of ideas for bracket creation")

        # Create first round
        first_round = TournamentRound(1)

        # Pair up ideas for first round matchups
        for i in range(0, len(self.ideas), 2):
            matchup = Matchup(
                idea1_id=self.ideas[i].id,
                idea2_id=self.ideas[i + 1].id,
                round_num=1,
            )
            first_round.add_matchup(matchup)

        self.rounds = [first_round]

    def _declare_winner(self) -> None:
        """
        Declare the tournament winner from the final round.

        Sets tournament status to COMPLETED and sets the winner.
        """
        if not self.rounds:
            raise ValueError("No rounds to determine winner from")

        final_round = self.rounds[-1]
        if not final_round.is_complete:
            raise ValueError("Final round is not complete")

        winners = final_round.get_winners()
        if len(winners) != 1:
            raise ValueError(f"Expected 1 winner, found {len(winners)}")

        winner_idea = self.get_idea_by_id(winners[0])
        if not winner_idea:
            raise ValueError(f"Winner idea {winners[0]} not found")

        self.winner = winner_idea
        self.status = TournamentStatus.COMPLETED

    def __repr__(self) -> str:
        return (
            f"Tournament(id='{self.id[:8]}...', name='{self.name}', "
            f"size={self.tournament_size}, status={self.status.value}, "
            f"ideas={len(self.ideas)}, rounds={len(self.rounds)})"
        )

    def __str__(self) -> str:
        return f"{self.name} ({len(self.ideas)}/{self.tournament_size} ideas, {self.status.value})"
