"""
Imprint concept parsing and management.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ...core.llm_integration import LLMCaller

logger = logging.getLogger(__name__)


@dataclass
class ImprintConcept:
    """
    Represents a parsed imprint concept with structured information.
    """
    name: str
    description: str
    target_audience: str
    genre_focus: List[str]
    unique_value_proposition: str
    brand_personality: str
    target_books_per_year: int
    priority_focus: str
    budget_range: str
    automation_level: str
    raw_input: str
    parsed_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'description': self.description,
            'target_audience': self.target_audience,
            'genre_focus': self.genre_focus,
            'unique_value_proposition': self.unique_value_proposition,
            'brand_personality': self.brand_personality,
            'target_books_per_year': self.target_books_per_year,
            'priority_focus': self.priority_focus,
            'budget_range': self.budget_range,
            'automation_level': self.automation_level,
            'raw_input': self.raw_input,
            'parsed_at': self.parsed_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImprintConcept':
        """Create from dictionary representation."""
        return cls(
            name=data['name'],
            description=data['description'],
            target_audience=data['target_audience'],
            genre_focus=data['genre_focus'],
            unique_value_proposition=data['unique_value_proposition'],
            brand_personality=data['brand_personality'],
            target_books_per_year=data['target_books_per_year'],
            priority_focus=data['priority_focus'],
            budget_range=data['budget_range'],
            automation_level=data['automation_level'],
            raw_input=data['raw_input'],
            parsed_at=datetime.fromisoformat(data['parsed_at'])
        )


class ImprintConceptParser:
    """
    Parses natural language imprint descriptions into structured concepts.
    """
    
    def __init__(self, llm_caller: LLMCaller):
        self.llm_caller = llm_caller
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def parse_concept(
        self,
        description: str,
        target_books_per_year: int = 12,
        priority_focus: str = "Quality",
        budget_range: str = "Medium",
        automation_level: str = "High"
    ) -> ImprintConcept:
        """
        Parse a natural language description into a structured imprint concept.
        
        Args:
            description: Natural language description of the imprint
            target_books_per_year: Target number of books per year
            priority_focus: Priority focus (Quality, Speed, Cost)
            budget_range: Budget range (Low, Medium, High)
            automation_level: Desired automation level (Low, Medium, High)
            
        Returns:
            Parsed imprint concept
        """
        self.logger.info(f"Parsing imprint concept from description: {description[:100]}...")
        
        prompt = f"""
        Parse the following imprint description into structured components.
        
        Description: {description}
        Target Books Per Year: {target_books_per_year}
        Priority Focus: {priority_focus}
        Budget Range: {budget_range}
        Automation Level: {automation_level}
        
        Extract and provide the information in valid JSON format only. Do not include any other text.
        
        Required JSON structure:
        {{
            "name": "suggested imprint name",
            "description": "clear description summary",
            "target_audience": "target audience description",
            "genre_focus": ["genre1", "genre2"],
            "unique_value_proposition": "what makes this imprint unique",
            "brand_personality": "personality description"
        }}
        """
        
        try:
            response = self.llm_caller.call_llm(
                prompt=prompt,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse JSON response - handle potential markdown formatting
            import json
            import re
            
            # Clean up response - remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = re.sub(r'^```json\s*', '', cleaned_response)
            if cleaned_response.endswith('```'):
                cleaned_response = re.sub(r'\s*```$', '', cleaned_response)
            
            parsed_data = json.loads(cleaned_response)
            
            concept = ImprintConcept(
                name=parsed_data['name'],
                description=parsed_data['description'],
                target_audience=parsed_data['target_audience'],
                genre_focus=parsed_data['genre_focus'],
                unique_value_proposition=parsed_data['unique_value_proposition'],
                brand_personality=parsed_data['brand_personality'],
                target_books_per_year=target_books_per_year,
                priority_focus=priority_focus,
                budget_range=budget_range,
                automation_level=automation_level,
                raw_input=description,
                parsed_at=datetime.now()
            )
            
            self.logger.info(f"Successfully parsed concept: {concept.name}")
            return concept
            
        except Exception as e:
            self.logger.error(f"Error parsing concept: {e}")
            # Return a basic concept as fallback
            return ImprintConcept(
                name="New Imprint",
                description=description,
                target_audience="General readers",
                genre_focus=["Fiction"],
                unique_value_proposition="Quality publishing",
                brand_personality="Professional and approachable",
                target_books_per_year=target_books_per_year,
                priority_focus=priority_focus,
                budget_range=budget_range,
                automation_level=automation_level,
                raw_input=description,
                parsed_at=datetime.now()
            )