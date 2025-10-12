"""
Centralized environment variable loader for xcu_my_apps workspace.

This module implements a two-tier environment loading strategy:
1. Load workspace-level variables from /Users/fred/xcu_my_apps/.env
2. Optionally load app-specific overrides from local .env file

Usage:
    from shared.env import load_env

    # Load central .env, then app-specific overrides from current directory
    load_env()

    # Load central .env, then overrides from specific directory
    load_env(app_dir="/path/to/app")

    # Load only central .env without overrides
    load_env(allow_override=False)
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Workspace root where centralized .env lives
WORKSPACE_ROOT = Path("/Users/fred/xcu_my_apps")
CENTRAL_ENV_FILE = WORKSPACE_ROOT / ".env"


def load_env(
    app_dir: Optional[str] = None,
    allow_override: bool = True,
    verbose: bool = False
) -> None:
    """
    Load environment variables with centralized defaults and optional app-specific overrides.

    Loading order (later values override earlier ones):
    1. /Users/fred/xcu_my_apps/.env (central configuration)
    2. {app_dir}/.env (app-specific overrides, if allow_override=True)

    Args:
        app_dir: Directory containing app-specific .env file.
                If None, uses current working directory.
        allow_override: If True, load app-specific .env after central .env.
                       If False, only load central .env.
        verbose: If True, log detailed information about which files were loaded.

    Examples:
        # From an app's main.py or __init__.py:
        from shared.env import load_env

        # Load central + local override
        load_env()

        # Load only central (no overrides)
        load_env(allow_override=False)

        # Load central + override from specific directory
        load_env(app_dir="/Users/fred/xcu_my_apps/nimble/codexes-factory")
    """
    files_loaded = []

    # 1. Load central workspace .env
    if CENTRAL_ENV_FILE.exists():
        load_dotenv(CENTRAL_ENV_FILE, override=False)
        files_loaded.append(str(CENTRAL_ENV_FILE))
        if verbose:
            logger.info(f"Loaded central environment from: {CENTRAL_ENV_FILE}")
    else:
        logger.warning(f"Central .env file not found: {CENTRAL_ENV_FILE}")

    # 2. Load app-specific overrides (if allowed)
    if allow_override:
        if app_dir is None:
            app_dir = os.getcwd()

        app_env_file = Path(app_dir) / ".env"

        if app_env_file.exists():
            # override=True allows local values to override central values
            load_dotenv(app_env_file, override=True)
            files_loaded.append(str(app_env_file))
            if verbose:
                logger.info(f"Loaded app-specific overrides from: {app_env_file}")
        else:
            if verbose:
                logger.debug(f"No app-specific .env found at: {app_env_file}")

    if verbose and files_loaded:
        logger.info(f"Environment loaded from {len(files_loaded)} file(s): {', '.join(files_loaded)}")


def get_env(
    key: str,
    default: Optional[str] = None,
    required: bool = False
) -> Optional[str]:
    """
    Get an environment variable with optional default and required check.

    Args:
        key: Environment variable name
        default: Default value if variable is not set
        required: If True, raise ValueError if variable is not set

    Returns:
        Value of the environment variable, or default if not set

    Raises:
        ValueError: If required=True and variable is not set

    Examples:
        # Get with default
        api_key = get_env("OPENAI_API_KEY", default="")

        # Get required value (raises if missing)
        api_key = get_env("OPENAI_API_KEY", required=True)

        # Get optional value
        debug_mode = get_env("DEBUG_MODE")
    """
    value = os.getenv(key, default)

    if required and value is None:
        raise ValueError(
            f"Required environment variable '{key}' is not set. "
            f"Please add it to {CENTRAL_ENV_FILE} or your app's local .env file."
        )

    return value


def print_env_info() -> None:
    """
    Print information about the environment loading configuration.
    Useful for debugging.
    """
    print("=" * 70)
    print("Environment Configuration Info")
    print("=" * 70)
    print(f"Workspace root:  {WORKSPACE_ROOT}")
    print(f"Central .env:    {CENTRAL_ENV_FILE}")
    print(f"  Exists:        {CENTRAL_ENV_FILE.exists()}")
    print(f"Current directory: {os.getcwd()}")

    local_env = Path(os.getcwd()) / ".env"
    print(f"Local .env:      {local_env}")
    print(f"  Exists:        {local_env.exists()}")
    print("=" * 70)
