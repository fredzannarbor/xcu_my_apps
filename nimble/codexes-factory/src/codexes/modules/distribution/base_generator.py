from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseGenerator(ABC):
    """Abstract Base Class for all output generators."""
    @abstractmethod
    def generate(self, responses: Dict[str, List[Dict]], output_path: str, **kwargs):
        """
        Processes LLM responses and generates the final output file.
        """
        pass