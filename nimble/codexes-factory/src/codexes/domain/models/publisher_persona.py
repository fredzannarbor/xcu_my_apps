"""
Rich domain model for Publisher Persona entities.

This module defines the publisher persona that makes editorial decisions
for an imprint, including personality traits, decision-making styles,
and vulnerabilities.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
import random


class RiskTolerance(Enum):
    """Risk tolerance level for editorial decisions."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class DecisionStyle(Enum):
    """Decision-making approach used by the persona."""
    DATA_DRIVEN = "data_driven"
    INTUITIVE = "intuitive"
    COLLABORATIVE = "collaborative"
    AUTHORITATIVE = "authoritative"


@dataclass
class EditorialDecision:
    """
    Represents a decision made by a publisher persona about a book concept.

    This is the output of the persona's evaluation process.
    """
    decision: str  # "accept", "reject", "revise", etc.
    confidence: float  # 0.0 to 1.0
    reasoning: str
    persona_name: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'decision': self.decision,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'persona_name': self.persona_name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EditorialDecision':
        """Create instance from dictionary."""
        return cls(
            decision=data['decision'],
            confidence=data['confidence'],
            reasoning=data['reasoning'],
            persona_name=data['persona_name'],
        )

    def __repr__(self) -> str:
        return f"EditorialDecision(decision='{self.decision}', confidence={self.confidence:.2f})"


class PublisherPersona:
    """
    Rich domain model representing a publisher's editorial persona.

    The persona embodies the editorial philosophy and decision-making
    characteristics of an imprint's publisher, including their biases,
    preferences, and vulnerabilities.
    """

    def __init__(
        self,
        name: str,
        bio: str,
        risk_tolerance: RiskTolerance = RiskTolerance.MODERATE,
        decision_style: DecisionStyle = DecisionStyle.DATA_DRIVEN,
        preferred_topics: Optional[List[str]] = None,
        target_demographics: Optional[List[str]] = None,
        vulnerabilities: Optional[List[str]] = None,
        glyph: Optional[str] = None,
    ):
        """
        Initialize a PublisherPersona.

        Args:
            name: Name of the publisher persona
            bio: Background and personality description
            risk_tolerance: Appetite for risky or experimental projects
            decision_style: Primary decision-making approach
            preferred_topics: Topics the persona is drawn to
            target_demographics: Demographic groups the persona focuses on
            vulnerabilities: Weaknesses or blind spots in decision-making
            glyph: AI-generated visual representation
        """
        if not name or not name.strip():
            raise ValueError("Publisher persona name cannot be empty")

        if not bio or not bio.strip():
            raise ValueError("Publisher persona bio cannot be empty")

        self.name = name
        self.bio = bio
        self.risk_tolerance = risk_tolerance
        self.decision_style = decision_style
        self.preferred_topics = preferred_topics or []
        self.target_demographics = target_demographics or []
        self.vulnerabilities = vulnerabilities or []
        self.glyph = glyph

    def evaluate_book_concept(self, concept: str, context: Optional[Dict[str, Any]] = None) -> EditorialDecision:
        """
        Evaluate a book concept based on this persona's characteristics.

        This is a placeholder for AI-driven evaluation. In production, this would
        call an LLM with the persona's characteristics to make a decision.

        Args:
            concept: Description of the book concept to evaluate
            context: Additional context (genre, market data, etc.)

        Returns:
            EditorialDecision: The persona's evaluation and decision
        """
        # Placeholder logic - in production, this would use LLM
        context = context or {}

        # Base confidence on risk tolerance and decision style
        base_confidence = 0.7
        if self.decision_style == DecisionStyle.DATA_DRIVEN:
            base_confidence = 0.8 if context else 0.5
        elif self.decision_style == DecisionStyle.INTUITIVE:
            base_confidence = 0.6

        # Adjust for risk tolerance
        if self.risk_tolerance == RiskTolerance.CONSERVATIVE:
            base_confidence -= 0.1
        elif self.risk_tolerance == RiskTolerance.AGGRESSIVE:
            base_confidence += 0.1

        # Check if concept matches preferred topics
        concept_lower = concept.lower()
        matches_preference = any(
            topic.lower() in concept_lower
            for topic in self.preferred_topics
        )

        if matches_preference:
            decision = "accept"
            confidence = min(base_confidence + 0.2, 1.0)
            reasoning = (
                f"This concept aligns well with my editorial focus on "
                f"{', '.join(self.preferred_topics)}. "
                f"My {self.decision_style.value} approach suggests this is a good fit."
            )
        else:
            decision = "consider"
            confidence = base_confidence
            reasoning = (
                f"While this concept is interesting, it doesn't strongly align with "
                f"my typical focus areas. I'd need more data to make a confident decision."
            )

        return EditorialDecision(
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            persona_name=self.name,
        )

    def add_vulnerability(self, vulnerability: str) -> None:
        """
        Add a decision-making vulnerability or blind spot.

        Args:
            vulnerability: Description of the vulnerability
        """
        if vulnerability and vulnerability not in self.vulnerabilities:
            self.vulnerabilities.append(vulnerability)

    def get_glyph(self) -> str:
        """
        Get the AI-generated glyph representing this persona.

        Returns:
            str: Glyph or emoji representation
        """
        if self.glyph:
            return self.glyph

        # Generate a simple glyph based on characteristics
        glyphs = {
            RiskTolerance.CONSERVATIVE: "🛡️",
            RiskTolerance.MODERATE: "⚖️",
            RiskTolerance.AGGRESSIVE: "🚀",
        }
        return glyphs.get(self.risk_tolerance, "📚")

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize persona to dictionary.

        Returns:
            Dict containing all persona data
        """
        return {
            'name': self.name,
            'bio': self.bio,
            'risk_tolerance': self.risk_tolerance.value,
            'decision_style': self.decision_style.value,
            'preferred_topics': self.preferred_topics,
            'target_demographics': self.target_demographics,
            'vulnerabilities': self.vulnerabilities,
            'glyph': self.glyph,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PublisherPersona':
        """
        Deserialize persona from dictionary.

        Args:
            data: Dictionary containing persona data

        Returns:
            PublisherPersona instance
        """
        return cls(
            name=data['name'],
            bio=data['bio'],
            risk_tolerance=RiskTolerance(data.get('risk_tolerance', 'moderate')),
            decision_style=DecisionStyle(data.get('decision_style', 'data_driven')),
            preferred_topics=data.get('preferred_topics', []),
            target_demographics=data.get('target_demographics', []),
            vulnerabilities=data.get('vulnerabilities', []),
            glyph=data.get('glyph'),
        )

    def __repr__(self) -> str:
        return (
            f"PublisherPersona(name='{self.name}', "
            f"risk_tolerance={self.risk_tolerance.value}, "
            f"decision_style={self.decision_style.value})"
        )

    def __str__(self) -> str:
        return f"{self.name} ({self.get_glyph()})"
