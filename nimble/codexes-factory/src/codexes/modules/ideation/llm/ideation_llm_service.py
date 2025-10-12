"""
LLM service layer for ideation workflows.
Provides specialized LLM interactions for ideation-specific tasks.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

from codexes.core.enhanced_llm_caller import enhanced_llm_caller
from .prompt_manager import IdeationPromptManager
from .response_parser import IdeationResponseParser
from ..core.codex_object import CodexObject, CodexObjectType

logger = logging.getLogger(__name__)


@dataclass
class IdeationLLMRequest:
    """Request configuration for ideation LLM operations."""
    operation_type: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    context_data: Dict[str, Any] = None
    prompt_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context_data is None:
            self.context_data = {}
        if self.prompt_config is None:
            self.prompt_config = {}


@dataclass
class IdeationLLMResponse:
    """Response from ideation LLM operations."""
    success: bool
    content: Optional[str]
    parsed_data: Optional[Dict[str, Any]]
    operation_type: str
    model_used: str
    error_message: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class IdeationLLMService:
    """
    Service layer for all ideation LLM interactions.
    Provides high-level methods for common ideation tasks.
    """
    
    def __init__(self):
        """Initialize the ideation LLM service."""
        self.llm_caller = enhanced_llm_caller
        self.prompt_manager = IdeationPromptManager()
        self.response_parser = IdeationResponseParser()
        
        logger.info("IdeationLLMService initialized")
    
    def generate_ideas(self, request: IdeationLLMRequest) -> IdeationLLMResponse:
        """
        Generate new ideas using LLM.
        
        Args:
            request: LLM request configuration
            
        Returns:
            LLM response with generated ideas
        """
        try:
            prompt = self.prompt_manager.get_idea_generation_prompt(
                request.context_data, request.prompt_config
            )
            
            messages = [
                {"role": "system", "content": "You are a creative writing assistant specializing in generating compelling story ideas."},
                {"role": "user", "content": prompt}
            ]
            
            llm_response = self.llm_caller.call_llm_with_retry(
                model=request.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            if not llm_response or not llm_response.get('content'):
                return IdeationLLMResponse(
                    success=False,
                    content=None,
                    parsed_data=None,
                    operation_type="generate_ideas",
                    model_used=request.model,
                    error_message="LLM failed to generate response"
                )
            
            # Parse the response
            parsed_data = self.response_parser.parse_idea_generation_response(
                llm_response['content']
            )
            
            return IdeationLLMResponse(
                success=True,
                content=llm_response['content'],
                parsed_data=parsed_data,
                operation_type="generate_ideas",
                model_used=request.model,
                metadata={
                    "usage": llm_response.get('usage', {}),
                    "attempts": llm_response.get('attempts', 1)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in generate_ideas: {e}")
            return IdeationLLMResponse(
                success=False,
                content=None,
                parsed_data=None,
                operation_type="generate_ideas",
                model_used=request.model,
                error_message=str(e)
            )
    
    def evaluate_tournament_match(self, obj1: CodexObject, obj2: CodexObject, 
                                 evaluation_criteria: Dict[str, Any] = None) -> IdeationLLMResponse:
        """
        Evaluate a tournament match between two CodexObjects.
        
        Args:
            obj1: First CodexObject
            obj2: Second CodexObject
            evaluation_criteria: Criteria for evaluation
            
        Returns:
            LLM response with match evaluation
        """
        try:
            criteria = evaluation_criteria or {
                "originality": 0.3,
                "marketability": 0.3,
                "execution_potential": 0.2,
                "emotional_impact": 0.2
            }
            
            prompt = self.prompt_manager.get_tournament_evaluation_prompt(
                obj1, obj2, criteria
            )
            
            messages = [
                {"role": "system", "content": "You are an expert literary judge evaluating creative works for a tournament."},
                {"role": "user", "content": prompt}
            ]
            
            llm_response = self.llm_caller.call_llm_json_with_retry(
                model="gpt-4o-mini",
                messages=messages,
                expected_keys=["winner", "reasoning", "scores"],
                temperature=0.5
            )
            
            if not llm_response:
                return IdeationLLMResponse(
                    success=False,
                    content=None,
                    parsed_data=None,
                    operation_type="tournament_evaluation",
                    model_used="gpt-4o-mini",
                    error_message="LLM failed to evaluate tournament match"
                )
            
            # Validate and parse the response
            parsed_data = self.response_parser.parse_tournament_evaluation_response(
                llm_response, obj1, obj2
            )
            
            return IdeationLLMResponse(
                success=True,
                content=str(llm_response),
                parsed_data=parsed_data,
                operation_type="tournament_evaluation",
                model_used="gpt-4o-mini",
                metadata={
                    "evaluation_criteria": criteria,
                    "participants": [obj1.uuid, obj2.uuid]
                }
            )
            
        except Exception as e:
            logger.error(f"Error in evaluate_tournament_match: {e}")
            return IdeationLLMResponse(
                success=False,
                content=None,
                parsed_data=None,
                operation_type="tournament_evaluation",
                model_used="gpt-4o-mini",
                error_message=str(e)
            )
    
    def simulate_reader_evaluation(self, obj: CodexObject, 
                                  reader_persona: Dict[str, Any]) -> IdeationLLMResponse:
        """
        Simulate a synthetic reader's evaluation of a CodexObject.
        
        Args:
            obj: CodexObject to evaluate
            reader_persona: Reader persona configuration
            
        Returns:
            LLM response with reader evaluation
        """
        try:
            prompt = self.prompt_manager.get_reader_evaluation_prompt(
                obj, reader_persona
            )
            
            messages = [
                {"role": "system", "content": f"You are simulating a reader with these characteristics: {reader_persona.get('description', 'general reader')}"},
                {"role": "user", "content": prompt}
            ]
            
            llm_response = self.llm_caller.call_llm_json_with_retry(
                model="gpt-4o-mini",
                messages=messages,
                expected_keys=["rating", "feedback", "would_read"],
                temperature=0.8  # Higher temperature for more varied reader responses
            )
            
            if not llm_response:
                return IdeationLLMResponse(
                    success=False,
                    content=None,
                    parsed_data=None,
                    operation_type="reader_evaluation",
                    model_used="gpt-4o-mini",
                    error_message="LLM failed to simulate reader evaluation"
                )
            
            # Parse and validate the response
            parsed_data = self.response_parser.parse_reader_evaluation_response(
                llm_response, reader_persona
            )
            
            return IdeationLLMResponse(
                success=True,
                content=str(llm_response),
                parsed_data=parsed_data,
                operation_type="reader_evaluation",
                model_used="gpt-4o-mini",
                metadata={
                    "reader_persona": reader_persona,
                    "object_uuid": obj.uuid
                }
            )
            
        except Exception as e:
            logger.error(f"Error in simulate_reader_evaluation: {e}")
            return IdeationLLMResponse(
                success=False,
                content=None,
                parsed_data=None,
                operation_type="reader_evaluation",
                model_used="gpt-4o-mini",
                error_message=str(e)
            )
    
    def generate_series_concepts(self, base_concept: str, 
                               series_config: Dict[str, Any]) -> IdeationLLMResponse:
        """
        Generate multiple related concepts for a book series.
        
        Args:
            base_concept: Base concept for the series
            series_config: Series generation configuration
            
        Returns:
            LLM response with series concepts
        """
        try:
            prompt = self.prompt_manager.get_series_generation_prompt(
                base_concept, series_config
            )
            
            messages = [
                {"role": "system", "content": "You are a series development expert creating cohesive multi-book narratives."},
                {"role": "user", "content": prompt}
            ]
            
            llm_response = self.llm_caller.call_llm_json_with_retry(
                model="gpt-4o-mini",
                messages=messages,
                expected_keys=["series_title", "books", "consistency_elements"],
                temperature=0.7
            )
            
            if not llm_response:
                return IdeationLLMResponse(
                    success=False,
                    content=None,
                    parsed_data=None,
                    operation_type="series_generation",
                    model_used="gpt-4o-mini",
                    error_message="LLM failed to generate series concepts"
                )
            
            # Parse the series response
            parsed_data = self.response_parser.parse_series_generation_response(
                llm_response, series_config
            )
            
            return IdeationLLMResponse(
                success=True,
                content=str(llm_response),
                parsed_data=parsed_data,
                operation_type="series_generation",
                model_used="gpt-4o-mini",
                metadata={
                    "base_concept": base_concept,
                    "series_config": series_config
                }
            )
            
        except Exception as e:
            logger.error(f"Error in generate_series_concepts: {e}")
            return IdeationLLMResponse(
                success=False,
                content=None,
                parsed_data=None,
                operation_type="series_generation",
                model_used="gpt-4o-mini",
                error_message=str(e)
            )
    
    def extract_story_elements(self, obj: CodexObject, 
                              element_types: List[str] = None) -> IdeationLLMResponse:
        """
        Extract story elements from a CodexObject.
        
        Args:
            obj: CodexObject to analyze
            element_types: Types of elements to extract
            
        Returns:
            LLM response with extracted elements
        """
        try:
            if element_types is None:
                element_types = ["characters", "settings", "themes", "plot_devices", "conflicts"]
            
            prompt = self.prompt_manager.get_element_extraction_prompt(
                obj, element_types
            )
            
            messages = [
                {"role": "system", "content": "You are a story analysis expert specializing in identifying and categorizing narrative elements."},
                {"role": "user", "content": prompt}
            ]
            
            llm_response = self.llm_caller.call_llm_json_with_retry(
                model="gpt-4o-mini",
                messages=messages,
                expected_keys=["elements"],
                temperature=0.3  # Lower temperature for more consistent analysis
            )
            
            if not llm_response:
                return IdeationLLMResponse(
                    success=False,
                    content=None,
                    parsed_data=None,
                    operation_type="element_extraction",
                    model_used="gpt-4o-mini",
                    error_message="LLM failed to extract story elements"
                )
            
            # Parse the elements response
            parsed_data = self.response_parser.parse_element_extraction_response(
                llm_response, element_types
            )
            
            return IdeationLLMResponse(
                success=True,
                content=str(llm_response),
                parsed_data=parsed_data,
                operation_type="element_extraction",
                model_used="gpt-4o-mini",
                metadata={
                    "source_object": obj.uuid,
                    "element_types": element_types
                }
            )
            
        except Exception as e:
            logger.error(f"Error in extract_story_elements: {e}")
            return IdeationLLMResponse(
                success=False,
                content=None,
                parsed_data=None,
                operation_type="element_extraction",
                model_used="gpt-4o-mini",
                error_message=str(e)
            )
    
    def recombine_elements(self, elements: List[Dict[str, Any]], 
                          recombination_config: Dict[str, Any]) -> IdeationLLMResponse:
        """
        Recombine story elements into new concepts.
        
        Args:
            elements: List of story elements to recombine
            recombination_config: Configuration for recombination
            
        Returns:
            LLM response with recombined concept
        """
        try:
            prompt = self.prompt_manager.get_element_recombination_prompt(
                elements, recombination_config
            )
            
            messages = [
                {"role": "system", "content": "You are a creative synthesis expert who combines story elements into innovative new concepts."},
                {"role": "user", "content": prompt}
            ]
            
            llm_response = self.llm_caller.call_llm_json_with_retry(
                model="gpt-4o-mini",
                messages=messages,
                expected_keys=["new_concept", "element_usage", "synthesis_reasoning"],
                temperature=0.8  # Higher temperature for creative recombination
            )
            
            if not llm_response:
                return IdeationLLMResponse(
                    success=False,
                    content=None,
                    parsed_data=None,
                    operation_type="element_recombination",
                    model_used="gpt-4o-mini",
                    error_message="LLM failed to recombine elements"
                )
            
            # Parse the recombination response
            parsed_data = self.response_parser.parse_element_recombination_response(
                llm_response, elements
            )
            
            return IdeationLLMResponse(
                success=True,
                content=str(llm_response),
                parsed_data=parsed_data,
                operation_type="element_recombination",
                model_used="gpt-4o-mini",
                metadata={
                    "source_elements": [elem.get('uuid') for elem in elements],
                    "recombination_config": recombination_config
                }
            )
            
        except Exception as e:
            logger.error(f"Error in recombine_elements: {e}")
            return IdeationLLMResponse(
                success=False,
                content=None,
                parsed_data=None,
                operation_type="element_recombination",
                model_used="gpt-4o-mini",
                error_message=str(e)
            )
    
    def enhance_content(self, obj: CodexObject, 
                       enhancement_type: str = "general") -> IdeationLLMResponse:
        """
        Enhance the content of a CodexObject.
        
        Args:
            obj: CodexObject to enhance
            enhancement_type: Type of enhancement (general, character, plot, style)
            
        Returns:
            LLM response with enhanced content
        """
        try:
            prompt = self.prompt_manager.get_content_enhancement_prompt(
                obj, enhancement_type
            )
            
            messages = [
                {"role": "system", "content": "You are an expert editor and writing coach specializing in content enhancement."},
                {"role": "user", "content": prompt}
            ]
            
            llm_response = self.llm_caller.call_llm_with_retry(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.6
            )
            
            if not llm_response or not llm_response.get('content'):
                return IdeationLLMResponse(
                    success=False,
                    content=None,
                    parsed_data=None,
                    operation_type="content_enhancement",
                    model_used="gpt-4o-mini",
                    error_message="LLM failed to enhance content"
                )
            
            # Parse the enhancement response
            parsed_data = self.response_parser.parse_content_enhancement_response(
                llm_response['content'], enhancement_type
            )
            
            return IdeationLLMResponse(
                success=True,
                content=llm_response['content'],
                parsed_data=parsed_data,
                operation_type="content_enhancement",
                model_used="gpt-4o-mini",
                metadata={
                    "source_object": obj.uuid,
                    "enhancement_type": enhancement_type,
                    "original_word_count": obj.word_count
                }
            )
            
        except Exception as e:
            logger.error(f"Error in enhance_content: {e}")
            return IdeationLLMResponse(
                success=False,
                content=None,
                parsed_data=None,
                operation_type="content_enhancement",
                model_used="gpt-4o-mini",
                error_message=str(e)
            )
    
    def batch_process_objects(self, objects: List[CodexObject], 
                             operation_type: str,
                             operation_config: Dict[str, Any] = None) -> List[IdeationLLMResponse]:
        """
        Process multiple CodexObjects in batch.
        
        Args:
            objects: List of CodexObjects to process
            operation_type: Type of operation to perform
            operation_config: Configuration for the operation
            
        Returns:
            List of LLM responses
        """
        results = []
        config = operation_config or {}
        
        for obj in objects:
            try:
                if operation_type == "enhance":
                    response = self.enhance_content(obj, config.get("enhancement_type", "general"))
                elif operation_type == "extract_elements":
                    response = self.extract_story_elements(obj, config.get("element_types"))
                elif operation_type == "reader_evaluation":
                    response = self.simulate_reader_evaluation(obj, config.get("reader_persona", {}))
                else:
                    response = IdeationLLMResponse(
                        success=False,
                        content=None,
                        parsed_data=None,
                        operation_type=operation_type,
                        model_used="unknown",
                        error_message=f"Unknown operation type: {operation_type}"
                    )
                
                results.append(response)
                
            except Exception as e:
                logger.error(f"Error processing object {obj.uuid} in batch: {e}")
                results.append(IdeationLLMResponse(
                    success=False,
                    content=None,
                    parsed_data=None,
                    operation_type=operation_type,
                    model_used="unknown",
                    error_message=str(e)
                ))
        
        return results
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get statistics about the LLM service usage."""
        # This could be expanded to track actual usage statistics
        return {
            "service_name": "IdeationLLMService",
            "available_operations": [
                "generate_ideas",
                "evaluate_tournament_match", 
                "simulate_reader_evaluation",
                "generate_series_concepts",
                "extract_story_elements",
                "recombine_elements",
                "enhance_content",
                "batch_process_objects"
            ],
            "default_model": "gpt-4o-mini",
            "prompt_manager_loaded": self.prompt_manager is not None,
            "response_parser_loaded": self.response_parser is not None
        }