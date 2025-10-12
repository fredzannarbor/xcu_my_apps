# src/codexes/modules/sensitivity/standards.py
# version 1.1.0
from dataclasses import dataclass, field
from typing import List, Dict, Literal, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class DomainStandard:
    """
    A simple data structure to hold a custom, domain-specific sensitivity standard.
    The precedence value determines the order of application (lower numbers are applied first).
    """
    name: str
    description: str
    precedence: int = 10  # Default precedence


class SensitivityReading:
    """
    Manages sensitivity reading standards, levels, and style guides for content analysis.

    This class centralizes the rules for sensitivity checks, allowing for a tiered
    system of standards to be applied. It is designed to configure a "Synthetic Reader"
    (a hypothetical analysis agent) with a specific set of guidelines.

    Attributes:
        STANDARD_LEVELS (tuple): Predefined sensitivity levels from None to High.
        AVAILABLE_STYLE_GUIDES (tuple): A list of common, recognized style guides.
    """
    STANDARD_LEVELS = ('None', 'Low', 'Moderate', 'High')
    # FIX: Expanded the list to include specific versions, which resolves the error.
    AVAILABLE_STYLE_GUIDES = ('AP', 'Chicago 17th', 'Chicago 18th', 'MLA', 'NYT')

    def __init__(self,
                 level: Literal['None', 'Low', 'Moderate', 'High'] = 'Low',
                 domain_standards: Optional[List[DomainStandard]] = None,
                 style_guides: Optional[List[str]] = None):
        """
        Initializes the sensitivity reading configuration with sensible defaults.

        Args:
            level (str): The overall sensitivity level. Defaults to 'Low'.
            domain_standards (list, optional): A list of custom DomainStandard objects.
            style_guides (list, optional): A list of strings representing style guides.
        """
        if level not in self.STANDARD_LEVELS:
            raise ValueError(f"Invalid sensitivity level '{level}'. Must be one of {self.STANDARD_LEVELS}")
        self.level = level

        self.domain_standards: List[DomainStandard] = domain_standards if domain_standards is not None else []
        self.style_guides: List[str] = style_guides if style_guides is not None else []

        # Assign a sensible default style guide if the level is not 'None'
        if self.level != 'None' and not self.style_guides:
            self.style_guides.append('AP')
            logger.info("Defaulted to 'AP' style guide for 'Low' sensitivity level.")

        self._sort_domain_standards()

    def __repr__(self) -> str:
        """Provides a clear string representation of the current configuration."""
        return (f"SensitivityReading(level='{self.level}', "
                f"domain_standards={[s.name for s in self.domain_standards]}, "
                f"style_guides={self.style_guides})")

    def _sort_domain_standards(self):
        """Private helper to sort domain standards by precedence (lower numbers first)."""
        self.domain_standards.sort(key=lambda x: x.precedence)

    def set_level(self, level: Literal['None', 'Low', 'Moderate', 'High']):
        """
        Sets the overall sensitivity level for the analysis.

        Args:
            level (str): The desired sensitivity level.
        """
        if level not in self.STANDARD_LEVELS:
            raise ValueError(f"Invalid sensitivity level '{level}'. Must be one of {self.STANDARD_LEVELS}")
        self.level = level
        logger.info(f"Sensitivity level set to '{self.level}'.")

    def add_domain_standard(self, name: str, description: str, precedence: int = 10):
        """
        Creates and adds a new custom, domain-specific standard from user input.

        Args:
            name (str): The unique name for the standard.
            description (str): A brief description of what the standard covers.
            precedence (int): The priority of the rule. Lower numbers are applied first.
        """
        if any(s.name.lower() == name.lower() for s in self.domain_standards):
            logger.warning(f"Domain standard '{name}' already exists and will not be added again.")
            return

        standard = DomainStandard(name=name, description=description, precedence=precedence)
        self.domain_standards.append(standard)
        self._sort_domain_standards()
        logger.info(f"Added domain standard '{name}' with precedence {precedence}.")

    def add_style_guide(self, guide_name: str):
        """
        Adds a recognized style guide to the configuration.

        Args:
            guide_name (str): The name of the style guide to add (e.g., 'AP', 'Chicago').
        """
        if guide_name not in self.AVAILABLE_STYLE_GUIDES:
            raise ValueError(
                f"'{guide_name}' is not a recognized style guide. Available: {self.AVAILABLE_STYLE_GUIDES}")
        if guide_name not in self.style_guides:
            self.style_guides.append(guide_name)
            logger.info(f"Added style guide '{guide_name}'.")

    def get_configuration(self) -> Dict:
        """
        Returns the complete sensitivity configuration as a dictionary.
        This structured data can be used to configure a synthetic reader or analysis tool.

        Returns:
            A dictionary containing the current level, a list of domain standards,
            and a list of style guides.
        """
        return {
            "level": self.level,
            "domain_standards": [s.__dict__ for s in self.domain_standards],
            "style_guides": self.style_guides
        }

    def configure_synthetic_reader(self, reader_instance: object):
        """
        Placeholder method to demonstrate how this class would configure another object.

        In a real implementation, this would call methods on the `reader_instance`
        to apply the standards.

        Args:
            reader_instance: An instance of a hypothetical SyntheticReader class.
        """
        config = self.get_configuration()
        logger.info(f"Configuring reader '{reader_instance.__class__.__name__}' with: {config}")

        # Example of how it might interact with a reader object:
        # if hasattr(reader_instance, 'set_sensitivity_level'):
        #     reader_instance.set_sensitivity_level(config['level'])
        # if hasattr(reader_instance, 'apply_domain_standards'):
        #     reader_instance.apply_domain_standards(config['domain_standards'])
        # if hasattr(reader_instance, 'apply_style_guides'):
        #     reader_instance.apply_style_guides(config['style_guides'])
