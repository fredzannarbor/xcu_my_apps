from dataclasses import dataclass, field
from pathlib import Path
import json

@dataclass
class Imprint:
    name: str
    path: Path
    prompts: dict = field(default_factory=dict)
    intro: str = ""
    display_name: str = ""

    def __post_init__(self):
        # Default display_name to the slug/directory name if not set
        if not self.display_name:
            self.display_name = self.name
        self.load_prompts()

    def load_prompts(self):
        """Loads the prompts from the imprint's prompts.json file."""
        prompts_file = self.path / 'prompts.json'
        if prompts_file.exists():
            with open(prompts_file, 'r') as f:
                prompts_data = json.load(f)
                self.prompts = prompts_data
                # Only override the internal name if a non-empty value is provided
                # Otherwise, keep the directory/slug so config lookups remain valid.
                loaded_imprint_name = prompts_data.get('imprint_name')
                if loaded_imprint_name:
                    # Keep the slug in self.name, but reflect the human-readable name in display_name
                    self.display_name = loaded_imprint_name
                # Intro text for convenience
                self.intro = prompts_data.get('imprint_intro', '')
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"✅ Successfully loaded imprint prompts from: {prompts_file}")

    @classmethod
    def from_name(cls, imprint_name: str):
        """Creates an Imprint instance from an imprint name."""
        imprint_path = Path('imprints') / imprint_name
        if not imprint_path.is_dir():
            raise FileNotFoundError(f"Imprint directory not found at {imprint_path}")
        return cls(name=imprint_name, path=imprint_path)
