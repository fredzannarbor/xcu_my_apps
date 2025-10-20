"""
Repository pattern implementation for Imprint persistence.

This module handles all persistence operations for Imprint entities,
abstracting away the storage mechanism (JSON files) from the domain layer.
"""

import json
from pathlib import Path
from typing import List, Optional
import shutil

from ...domain.models.imprint import Imprint


class ImprintRepository:
    """
    Repository for persisting and retrieving Imprint entities.

    Uses JSON files for storage with one file per imprint.
    """

    def __init__(self, base_path: Path):
        """
        Initialize the imprint repository.

        Args:
            base_path: Base directory for imprint configurations
        """
        self.base_path = Path(base_path)
        self.imprints_dir = self.base_path / "imprints"
        self.prompts_dir = self.base_path / "prompts"
        self._ensure_directories()

    def save(self, imprint: Imprint) -> None:
        """
        Persist an imprint to storage.

        Args:
            imprint: Imprint to save

        Raises:
            IOError: If save operation fails
        """
        config_path = self.imprints_dir / f"{imprint.slug}.json"

        try:
            # Serialize to JSON
            data = imprint.to_dict()

            # Write to file with pretty formatting
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Create default prompts directory if it doesn't exist
            self._create_default_prompts(imprint.slug)

        except Exception as e:
            raise IOError(f"Failed to save imprint '{imprint.slug}': {e}") from e

    def get_by_slug(self, slug: str) -> Optional[Imprint]:
        """
        Retrieve an imprint by its slug.

        Args:
            slug: URL-safe identifier for the imprint

        Returns:
            Imprint or None if not found

        Raises:
            IOError: If read operation fails
        """
        config_path = self.imprints_dir / f"{slug}.json"

        if not config_path.exists():
            return None

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return Imprint.from_dict(data)

        except Exception as e:
            raise IOError(f"Failed to load imprint '{slug}': {e}") from e

    def get_all(self) -> List[Imprint]:
        """
        Retrieve all imprints.

        Returns:
            List of all Imprint entities

        Raises:
            IOError: If read operation fails
        """
        imprints = []

        if not self.imprints_dir.exists():
            return imprints

        try:
            for config_file in self.imprints_dir.glob("*.json"):
                slug = config_file.stem
                imprint = self.get_by_slug(slug)
                if imprint:
                    imprints.append(imprint)

            # Sort by created date (newest first)
            imprints.sort(key=lambda x: x.created_at, reverse=True)

            return imprints

        except Exception as e:
            raise IOError(f"Failed to load imprints: {e}") from e

    def get_active(self) -> List[Imprint]:
        """
        Retrieve all active imprints.

        Returns:
            List of active Imprint entities

        Raises:
            IOError: If read operation fails
        """
        all_imprints = self.get_all()
        return [imp for imp in all_imprints if imp.is_active]

    def delete(self, slug: str) -> bool:
        """
        Delete an imprint and its associated files.

        Args:
            slug: Slug of imprint to delete

        Returns:
            bool: True if deleted, False if not found

        Raises:
            IOError: If delete operation fails
        """
        config_path = self.imprints_dir / f"{slug}.json"

        if not config_path.exists():
            return False

        try:
            # Delete config file
            config_path.unlink()

            # Delete prompts directory if it exists
            prompts_path = self.prompts_dir / slug
            if prompts_path.exists() and prompts_path.is_dir():
                shutil.rmtree(prompts_path)

            return True

        except Exception as e:
            raise IOError(f"Failed to delete imprint '{slug}': {e}") from e

    def exists(self, slug: str) -> bool:
        """
        Check if an imprint exists.

        Args:
            slug: Slug to check

        Returns:
            bool: True if imprint exists
        """
        config_path = self.imprints_dir / f"{slug}.json"
        return config_path.exists()

    def _ensure_directories(self) -> None:
        """
        Ensure required directories exist.

        Creates imprints and prompts directories if they don't exist.
        """
        self.imprints_dir.mkdir(parents=True, exist_ok=True)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

    def _create_default_prompts(self, slug: str) -> None:
        """
        Create default prompt files for an imprint.

        Args:
            slug: Imprint slug
        """
        prompts_path = self.prompts_dir / slug
        prompts_path.mkdir(parents=True, exist_ok=True)

        # Create default prompt templates if they don't exist
        default_prompts = {
            'book_concept.txt': (
                'Generate a book concept for the {imprint_name} imprint.\n\n'
                'Charter: {charter}\n\n'
                'Focus: {focus}\n\n'
                'Create an innovative book concept that aligns with the imprint\'s mission.'
            ),
            'evaluate_manuscript.txt': (
                'Evaluate the following manuscript for the {imprint_name} imprint.\n\n'
                'Charter: {charter}\n\n'
                'Manuscript: {manuscript}\n\n'
                'Provide a detailed editorial assessment.'
            ),
        }

        for filename, content in default_prompts.items():
            prompt_file = prompts_path / filename
            if not prompt_file.exists():
                with open(prompt_file, 'w', encoding='utf-8') as f:
                    f.write(content)

    def __repr__(self) -> str:
        return f"ImprintRepository(base_path='{self.base_path}')"
