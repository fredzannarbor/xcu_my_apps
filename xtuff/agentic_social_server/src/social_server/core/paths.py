"""
Path utilities for the social server package.

This module provides utilities for resolving file paths relative to the
project directory, ensuring data files are stored in the calling project
rather than in site-packages.
"""

import os
from pathlib import Path
from typing import Union


def get_project_root() -> Path:
    """
    Get the project root directory.

    This function looks for the project root by searching for marker files
    that indicate the root of a social server project.

    Returns:
        Path: The project root directory

    Raises:
        RuntimeError: If project root cannot be determined
    """
    # Start from the current working directory
    current_dir = Path.cwd()

    # Marker files that indicate a social server project root
    marker_files = [
        "app.py",  # Main entry point
        "pyproject.toml",  # Python project file
        "requirements.txt",  # Dependencies
        ".gitignore",  # Git ignore file
    ]

    # Search upward from current directory
    search_dir = current_dir
    for _ in range(10):  # Limit search to 10 levels up
        # Check if any marker files exist in this directory
        if any((search_dir / marker).exists() for marker in marker_files):
            # Additional check: ensure this looks like a social server project
            if (search_dir / "src" / "social_server").exists() or \
               (search_dir / "app.py").exists():
                return search_dir

        # Move up one level
        parent = search_dir.parent
        if parent == search_dir:  # Reached filesystem root
            break
        search_dir = parent

    # If we can't find the project root through marker files,
    # try to use environment variable as fallback
    if "SOCIAL_SERVER_ROOT" in os.environ:
        env_root = Path(os.environ["SOCIAL_SERVER_ROOT"])
        if env_root.exists():
            return env_root

    # As a last resort, use current working directory
    # but issue a warning
    import warnings
    warnings.warn(
        "Could not determine project root directory. Using current working directory. "
        "You may need to set SOCIAL_SERVER_ROOT environment variable.",
        UserWarning
    )
    return current_dir


def get_data_path(relative_path: Union[str, Path]) -> Path:
    """
    Get the absolute path to a data file relative to the project root.

    Args:
        relative_path: Path relative to project root (e.g., "resources/data_tables/file.json")

    Returns:
        Path: Absolute path to the data file
    """
    project_root = get_project_root()
    return project_root / relative_path


def ensure_data_directory(relative_path: Union[str, Path]) -> Path:
    """
    Ensure a data directory exists and return its absolute path.

    Args:
        relative_path: Directory path relative to project root

    Returns:
        Path: Absolute path to the directory
    """
    dir_path = get_data_path(relative_path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_config_path(config_name: str = "config.yaml") -> Path:
    """
    Get the path to a configuration file.

    Args:
        config_name: Name of the config file

    Returns:
        Path: Absolute path to the config file
    """
    return get_data_path(f"resources/yaml/{config_name}")


def get_storage_path(storage_name: str) -> Path:
    """
    Get the path to a data storage file.

    Args:
        storage_name: Name of the storage file

    Returns:
        Path: Absolute path to the storage file
    """
    return get_data_path(f"resources/data_tables/{storage_name}")