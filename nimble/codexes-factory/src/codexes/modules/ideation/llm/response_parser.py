"""
Response parsing for ideation LLM operations.
Handles parsing and validation of LLM responses for ideation workflows.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ParsedResponse:
    """Represents a parsed LLM response."""
    success: bool
    parsed_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    raw_response: Optional[str] = None


class IdeationResponseParser:
    """Parses LLM responses for ideation-specific operations."""
    
    def __init__(self):
        """Initialize the response parser."""
        logger.info("IdeationResponseParser initialized")
    
    def parse_concept_generation(self, response: str) -> ParsedResponse:
        """Parse a concept generation response."""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                data = json.loads(response)
                return ParsedResponse(
                    success=True,
                    parsed_data=data,
                    raw_response=response
                )
            
            # Fallback to text parsing
            lines = response.strip().split('\n')
            concept_data = {
                "title": "Generated Concept",
                "premise": response.strip(),
                "genre": "General Fiction",
                "themes": ["creativity"],
                "setting": "Contemporary",
                "tone": "Engaging"
            }
            
            return ParsedResponse(
                success=True,
                parsed_data=concept_data,
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"Error parsing concept generation response: {e}")
            return ParsedResponse(
                success=False,
                error_message=str(e),
                raw_response=response
            )
    
    def parse_tournament_evaluation(self, response: str) -> ParsedResponse:
        """Parse a tournament evaluation response."""
        try:
            # Try JSON parsing first
            if response.strip().startswith('{'):
                data = json.loads(response)
                return ParsedResponse(
                    success=True,
                    parsed_data=data,
                    raw_response=response
                )
            
            # Fallback parsing
            lines = response.strip().split('\n')
            winner = "concept_a"  # Default
            reasoning = response.strip()
            confidence = 0.7
            
            # Simple text analysis
            if "concept b" in response.lower() or "second" in response.lower():
                winner = "concept_b"
            
            evaluation_data = {
                "winner": winner,
                "reasoning": reasoning,
                "confidence": confidence
            }
            
            return ParsedResponse(
                success=True,
                parsed_data=evaluation_data,
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"Error parsing tournament evaluation response: {e}")
            return ParsedResponse(
                success=False,
                error_message=str(e),
                raw_response=response
            )
    
    def parse_series_entry(self, response: str) -> ParsedResponse:
        """Parse a series entry generation response."""
        try:
            # Try JSON parsing first
            if response.strip().startswith('{'):
                data = json.loads(response)
                return ParsedResponse(
                    success=True,
                    parsed_data=data,
                    raw_response=response
                )
            
            # Fallback parsing
            entry_data = {
                "title": "Series Entry",
                "premise": response.strip(),
                "genre": "Series Fiction",
                "themes": ["continuity"],
                "setting": "Series Setting"
            }
            
            return ParsedResponse(
                success=True,
                parsed_data=entry_data,
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"Error parsing series entry response: {e}")
            return ParsedResponse(
                success=False,
                error_message=str(e),
                raw_response=response
            )
    
    def parse_series_name(self, response: str) -> ParsedResponse:
        """Parse a series name generation response."""
        try:
            # Try JSON parsing first
            if response.strip().startswith('{'):
                data = json.loads(response)
                return ParsedResponse(
                    success=True,
                    parsed_data=data,
                    raw_response=response
                )
            
            # Extract series name from text
            series_name = response.strip().split('\n')[0].strip()
            if series_name.startswith('"') and series_name.endswith('"'):
                series_name = series_name[1:-1]
            
            name_data = {
                "series_name": series_name
            }
            
            return ParsedResponse(
                success=True,
                parsed_data=name_data,
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"Error parsing series name response: {e}")
            return ParsedResponse(
                success=False,
                error_message=str(e),
                raw_response=response
            )
    
    def parse_reader_evaluation(self, response: str) -> ParsedResponse:
        """Parse a reader evaluation response."""
        try:
            # Try JSON parsing first
            if response.strip().startswith('{'):
                data = json.loads(response)
                return ParsedResponse(
                    success=True,
                    parsed_data=data,
                    raw_response=response
                )
            
            # Fallback parsing
            evaluation_data = {
                "appeal_score": 0.7,
                "reasoning": response.strip(),
                "market_appeal": 0.6,
                "demographic_fit": 0.8
            }
            
            return ParsedResponse(
                success=True,
                parsed_data=evaluation_data,
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"Error parsing reader evaluation response: {e}")
            return ParsedResponse(
                success=False,
                error_message=str(e),
                raw_response=response
            )
    
    def parse_element_extraction(self, response: str) -> ParsedResponse:
        """Parse an element extraction response."""
        try:
            # Try JSON parsing first
            if response.strip().startswith('{'):
                data = json.loads(response)
                return ParsedResponse(
                    success=True,
                    parsed_data=data,
                    raw_response=response
                )
            
            # Fallback parsing
            elements_data = {
                "characters": [{"name": "Character", "type": "protagonist", "description": "Main character"}],
                "settings": [{"name": "Setting", "type": "location", "description": "Story location"}],
                "themes": [{"name": "Theme", "type": "theme", "description": "Central theme"}],
                "plot_devices": [{"name": "Plot Device", "type": "structure", "description": "Story structure"}]
            }
            
            return ParsedResponse(
                success=True,
                parsed_data=elements_data,
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"Error parsing element extraction response: {e}")
            return ParsedResponse(
                success=False,
                error_message=str(e),
                raw_response=response
            )
    
    def parse_element_recombination(self, response: str) -> ParsedResponse:
        """Parse an element recombination response."""
        try:
            # Try JSON parsing first
            if response.strip().startswith('{'):
                data = json.loads(response)
                return ParsedResponse(
                    success=True,
                    parsed_data=data,
                    raw_response=response
                )
            
            # Fallback parsing
            recombined_data = {
                "title": "Recombined Concept",
                "premise": response.strip(),
                "genre": "Mixed Genre",
                "themes": ["synthesis"],
                "setting": "Combined Setting"
            }
            
            return ParsedResponse(
                success=True,
                parsed_data=recombined_data,
                raw_response=response
            )
            
        except Exception as e:
            logger.error(f"Error parsing element recombination response: {e}")
            return ParsedResponse(
                success=False,
                error_message=str(e),
                raw_response=response
            )
    
    def parse_idea_generation_response(self, response: str) -> Dict[str, Any]:
        """
        Parse an idea generation response into structured data.
        
        Args:
            response: Raw LLM response text
            
        Returns:
            Dictionary with parsed idea data
        """
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{') or response.strip().startswith('['):
                return json.loads(response)
            
            # Parse text-based response
            ideas = []
            current_idea = {}
            
            lines = response.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Look for structured fields
                if line.lower().startswith('title:'):
                    if current_idea:  # Save previous idea
                        ideas.append(current_idea)
                    current_idea = {'title': line[6:].strip()}
                elif line.lower().startswith('logline:'):
                    current_idea['logline'] = line[8:].strip()
                elif line.lower().startswith('description:'):
                    current_idea['description'] = line[12:].strip()
                elif line.lower().startswith('genre:'):
                    current_idea['genre'] = line[6:].strip()
                elif line.lower().startswith('target audience:'):
                    current_idea['target_audience'] = line[16:].strip()
                elif current_idea and 'description' in current_idea:
                    # Continue description if we're in description mode
                    current_idea['description'] += ' ' + line
            
            # Add the last idea
            if current_idea:
                ideas.append(current_idea)
            
            # If no structured parsing worked, create a single idea from the whole response
            if not ideas:
                ideas = [{
                    'title': 'Generated Concept',
                    'logline': response[:200] + '...' if len(response) > 200 else response,
                    'description': response,
                    'genre': 'General Fiction',
                    'target_audience': 'General'
                }]
            
            return {'ideas': ideas}
            
        except Exception as e:
            logger.error(f"Error parsing idea generation response: {e}")
            # Return a fallback structure
            return {
                'ideas': [{
                    'title': 'Generated Concept',
                    'logline': 'A compelling story concept',
                    'description': response[:500] if response else 'Generated concept',
                    'genre': 'General Fiction',
                    'target_audience': 'General'
                }]
            }