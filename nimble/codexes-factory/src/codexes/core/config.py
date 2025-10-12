# core/config.py
from datetime import datetime

# List of models for UI dropdowns and CLI validation
MODELS_CHOICE = [
    "gemini/gemini-2.5-pro",
    "xai/grok-3-latest",
    "ollama/mistral",
    "openai/gpt-5",
    "openai/gpt-5-mini"
]

# Default name for the user prompts JSON file
PROMPT_FILE_NAME = "codexes_user_prompts.json"

def get_version_as_dict():
    """Placeholder for a versioning system."""
    return {"version": "3.1", "build_date": datetime.now().strftime("%Y-%m-%d")}