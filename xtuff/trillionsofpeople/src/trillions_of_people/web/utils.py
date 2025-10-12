"""
Utility functions for the web interface.
"""

import os
import streamlit as st
from typing import Optional

from ..core.logging_config import get_logger

logger = get_logger(__name__)


class APIKeyManager:
    """Manages API keys for the Streamlit interface."""

    def __init__(self):
        self.supported_providers = ["openai"]

    def enter_api_key(self, provider: str) -> Optional[str]:
        """Create API key input widget and return the key."""
        if provider not in self.supported_providers:
            st.error(f"Unsupported provider: {provider}")
            return None

        if provider == "openai":
            return self._enter_openai_key()

        return None

    def _enter_openai_key(self) -> Optional[str]:
        """Handle OpenAI API key input."""
        # Try to get from environment first
        env_key = os.getenv("OPENAI_API_KEY")

        if env_key:
            st.success("✅ Using OpenAI API key from environment")
            return env_key

        # Otherwise, use Streamlit input
        api_key = st.text_input(
            "Enter your OpenAI API key:",
            type="password",
            help="Get your API key from https://platform.openai.com/account/api-keys",
            key="openai_key_input"
        )

        if api_key:
            if len(api_key) == 51 and api_key.startswith("sk-"):
                st.success("✅ Valid OpenAI API key format")
                return api_key
            else:
                st.error("❌ Invalid OpenAI API key format")
                return None
        else:
            st.warning("⚠️ Please enter your OpenAI API key to generate personas")
            return None


def create_api_key_manager() -> APIKeyManager:
    """Factory function to create API key manager."""
    return APIKeyManager()


def show_current_version() -> str:
    """Return current version information."""
    try:
        from .. import __version__
        return f"Trillions of People v{__version__}"
    except ImportError:
        return "Trillions of People v1.0.0"


def format_persona_data(persona: dict) -> dict:
    """Format persona data for display."""
    formatted = {}

    # Basic info
    formatted["Name"] = persona.get("name", "Unknown")
    formatted["Age"] = persona.get("age", "Unknown")
    formatted["Gender"] = persona.get("gender", "Unknown")
    formatted["Born"] = persona.get("born", "Unknown")
    formatted["Country"] = persona.get("country", "Unknown")

    # Details
    formatted["Occupation"] = persona.get("occupation", "Unknown")
    formatted["Education"] = persona.get("education", "Unknown")
    formatted["Family"] = persona.get("family_situation", "Unknown")
    formatted["Economic Status"] = persona.get("economic_status", "Unknown")

    # Rich text fields
    traits = persona.get("personality_traits", [])
    if isinstance(traits, list):
        formatted["Personality"] = ", ".join(traits)
    else:
        formatted["Personality"] = str(traits)

    challenges = persona.get("life_challenges", [])
    if isinstance(challenges, list):
        formatted["Challenges"] = ", ".join(challenges)
    else:
        formatted["Challenges"] = str(challenges)

    formatted["Cultural Background"] = persona.get("cultural_background", "Unknown")

    events = persona.get("notable_events", [])
    if isinstance(events, list):
        formatted["Notable Events"] = "; ".join(events)
    else:
        formatted["Notable Events"] = str(events)

    return formatted


def validate_csv_upload(df):
    """Validate uploaded CSV data."""
    required_columns = ["name"]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"

    if df.empty:
        return False, "CSV file is empty"

    return True, "Valid CSV file"