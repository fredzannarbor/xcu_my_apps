"""
Repository pattern implementation for Tournament persistence.

This module handles all persistence operations for Tournament entities,
managing tournament state and history.
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from ...domain.models.tournament import Tournament


class TournamentRepository:
    """
    Repository for persisting and retrieving Tournament entities.

    Uses JSON files for storage with support for active tournament
    and tournament history.
    """

    def __init__(self, base_path: Path):
        """
        Initialize the tournament repository.

        Args:
            base_path: Base directory for tournament data
        """
        self.base_path = Path(base_path)
        self.tournaments_dir = self.base_path / "tournaments"
        self.active_tournament_path = self.tournaments_dir / "active_tournament.json"
        self.history_dir = self.tournaments_dir / "history"
        self._ensure_directories()

    def save(self, tournament: Tournament) -> None:
        """
        Persist a tournament to storage.

        Saves to both the specific tournament file and updates history.

        Args:
            tournament: Tournament to save

        Raises:
            IOError: If save operation fails
        """
        try:
            # Serialize to JSON
            data = tournament.to_dict()

            # Save to tournament-specific file
            tournament_path = self.tournaments_dir / f"{tournament.id}.json"
            with open(tournament_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # If tournament is completed, also save to history
            if tournament.status.value == 'completed':
                self._save_to_history(tournament)

        except Exception as e:
            raise IOError(f"Failed to save tournament '{tournament.id}': {e}") from e

    def get_active(self) -> Optional[Tournament]:
        """
        Retrieve the currently active tournament.

        Returns:
            Tournament or None if no active tournament

        Raises:
            IOError: If read operation fails
        """
        if not self.active_tournament_path.exists():
            return None

        try:
            with open(self.active_tournament_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return Tournament.from_dict(data)

        except Exception as e:
            raise IOError(f"Failed to load active tournament: {e}") from e

    def set_active(self, tournament: Tournament) -> None:
        """
        Set a tournament as the active tournament.

        Args:
            tournament: Tournament to set as active

        Raises:
            IOError: If save operation fails
        """
        try:
            # Save tournament data
            self.save(tournament)

            # Create symlink or copy to active tournament path
            data = tournament.to_dict()
            with open(self.active_tournament_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            raise IOError(f"Failed to set active tournament: {e}") from e

    def get_by_id(self, tournament_id: str) -> Optional[Tournament]:
        """
        Retrieve a specific tournament by ID.

        Args:
            tournament_id: Tournament ID

        Returns:
            Tournament or None if not found

        Raises:
            IOError: If read operation fails
        """
        tournament_path = self.tournaments_dir / f"{tournament_id}.json"

        if not tournament_path.exists():
            # Try looking in history
            return self._get_from_history(tournament_id)

        try:
            with open(tournament_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return Tournament.from_dict(data)

        except Exception as e:
            raise IOError(f"Failed to load tournament '{tournament_id}': {e}") from e

    def clear_active(self) -> bool:
        """
        Clear the active tournament.

        Returns:
            bool: True if cleared, False if no active tournament

        Raises:
            IOError: If delete operation fails
        """
        if not self.active_tournament_path.exists():
            return False

        try:
            self.active_tournament_path.unlink()
            return True

        except Exception as e:
            raise IOError(f"Failed to clear active tournament: {e}") from e

    def _ensure_directories(self) -> None:
        """
        Ensure required directories exist.

        Creates tournaments and history directories if they don't exist.
        """
        self.tournaments_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def _save_to_history(self, tournament: Tournament) -> None:
        """
        Save a completed tournament to history.

        Args:
            tournament: Tournament to archive

        Raises:
            IOError: If save operation fails
        """
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            history_filename = f"{tournament.id}_{timestamp}.json"
            history_path = self.history_dir / history_filename

            # Save to history
            data = tournament.to_dict()
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            raise IOError(f"Failed to save tournament to history: {e}") from e

    def _get_from_history(self, tournament_id: str) -> Optional[Tournament]:
        """
        Retrieve a tournament from history.

        Args:
            tournament_id: Tournament ID to find

        Returns:
            Tournament or None if not found
        """
        if not self.history_dir.exists():
            return None

        try:
            # Look for files starting with tournament_id
            for history_file in self.history_dir.glob(f"{tournament_id}_*.json"):
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                tournament = Tournament.from_dict(data)
                if tournament.id == tournament_id:
                    return tournament

            return None

        except Exception as e:
            raise IOError(f"Failed to retrieve tournament from history: {e}") from e

    def __repr__(self) -> str:
        return f"TournamentRepository(base_path='{self.base_path}')"
