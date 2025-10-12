"""
Content classification system for stage/length-agnostic ideation processing.
Determines content type and development stage using LLM analysis.
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from .codex_object import CodexObject, CodexObjectType, DevelopmentStage
from nimble_llm_caller.core.llm_caller import LLMCaller
from nimble_llm_caller.models.request import LLMRequest, ResponseFormat

# Create global instance
enhanced_llm_caller = LLMCaller()

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of content classification analysis."""
    object_type: CodexObjectType
    development_stage: DevelopmentStage
    confidence_score: float
    word_count: int
    classification_reasoning: str
    suggested_improvements: List[str]
    metadata_completeness: float


class ContentClassifier:
    """
    Classifies content into appropriate CodexObjectType and DevelopmentStage.
    Supports stage/length-agnostic processing for ideation workflows.
    """
    
    def __init__(self):
        """Initialize the content classifier."""
        self.classification_cache: Dict[str, ClassificationResult] = {}
        logger.info("ContentClassifier initialized")
    
    def classify_content(self, content: str, existing_metadata: Optional[Dict[str, Any]] = None) -> ClassificationResult:
        """
        Classify content into type and development stage.
        
        Args:
            content: Text content to classify
            existing_metadata: Optional existing metadata to consider
            
        Returns:
            ClassificationResult with classification details
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key(content, existing_metadata)
            if cache_key in self.classification_cache:
                return self.classification_cache[cache_key]
            
            # Perform heuristic classification
            heuristic_result = self._heuristic_classification(content)
            
            # Enhance with LLM analysis if available
            llm_result = self._llm_classification(content, existing_metadata)
            
            # Combine results
            final_result = self._combine_classifications(heuristic_result, llm_result, content)
            
            # Cache result
            self.classification_cache[cache_key] = final_result
            
            logger.debug(f"Classified content as {final_result.object_type.value} at {final_result.development_stage.value} stage")
            return final_result
            
        except Exception as e:
            logger.error(f"Error classifying content: {e}")
            # Return default classification
            return ClassificationResult(
                object_type=CodexObjectType.UNKNOWN,
                development_stage=DevelopmentStage.CONCEPT,
                confidence_score=0.0,
                word_count=len(content.split()) if content else 0,
                classification_reasoning=f"Classification failed: {str(e)}",
                suggested_improvements=["Unable to analyze content due to error"],
                metadata_completeness=0.0
            )
    
    def _heuristic_classification(self, content: str) -> Tuple[CodexObjectType, float]:
        """Use word count and structure heuristics for initial classification."""
        word_count = len(content.split())
        
        # Basic word count heuristics
        if word_count < 10:
            return CodexObjectType.IDEA, 0.6
        elif word_count < 50:
            return CodexObjectType.LOGLINE, 0.7
        elif word_count < 200:
            return CodexObjectType.SUMMARY, 0.7
        elif word_count < 1000:
            return CodexObjectType.SYNOPSIS, 0.6
        elif word_count < 5000:
            return CodexObjectType.TREATMENT, 0.6
        elif word_count < 20000:
            return CodexObjectType.OUTLINE, 0.5
        else:
            return CodexObjectType.DRAFT, 0.5
    
    def _llm_classification(self, content: str, existing_metadata: Optional[Dict[str, Any]]) -> Optional[ClassificationResult]:
        """Use LLM for enhanced classification analysis."""
        try:
            # Prepare classification prompt
            prompt = self._build_classification_prompt(content, existing_metadata)
            
            # Create LLM request
            request = LLMRequest(
                prompt_key="classification_prompt",
                model="gpt-4",
                response_format=ResponseFormat.JSON,
                model_params={
                    "temperature": 0.1,
                    "max_tokens": 500
                },
                metadata={
                    "content": prompt
                }
            )
            
            # Call LLM
            response = enhanced_llm_caller.call(request)
            
            if response and response.is_success:
                return self._parse_llm_classification(response.content)
            
            return None
            
        except Exception as e:
            logger.error(f"Error in LLM classification: {e}")
            return None
    
    def _build_classification_prompt(self, content: str, existing_metadata: Optional[Dict[str, Any]]) -> str:
        """Build prompt for LLM classification."""
        metadata_context = ""
        if existing_metadata:
            metadata_context = f"\\nExisting metadata: {existing_metadata}"
        
        return f"""Analyze this creative content and classify it:

Content: {content[:1000]}...{metadata_context}

Classify the content type:
- IDEA: Basic concept or inspiration
- LOGLINE: One-sentence story summary
- SUMMARY: Brief story overview
- TREATMENT: Detailed story treatment
- SYNOPSIS: Comprehensive story synopsis
- OUTLINE: Structured story outline
- DRAFT: Partial or complete manuscript
- MANUSCRIPT: Complete finished work

Classify the development stage:
- CONCEPT: Initial idea stage
- DEVELOPMENT: Being developed/expanded
- DRAFT: First draft stage
- REVISION: Being revised/edited
- COMPLETE: Finished work

Provide:
1. Content type
2. Development stage
3. Confidence (0.0-1.0)
4. Reasoning
5. Suggested improvements
6. Metadata completeness (0.0-1.0)

Format as JSON."""
    
    def _parse_llm_classification(self, response: str) -> Optional[ClassificationResult]:
        """Parse LLM classification response."""
        try:
            import json
            
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                # Map string values to enums
                object_type = CodexObjectType.UNKNOWN
                for obj_type in CodexObjectType:
                    if obj_type.value.upper() == data.get("content_type", "").upper():
                        object_type = obj_type
                        break
                
                development_stage = DevelopmentStage.CONCEPT
                for stage in DevelopmentStage:
                    if stage.value.upper() == data.get("development_stage", "").upper():
                        development_stage = stage
                        break
                
                return ClassificationResult(
                    object_type=object_type,
                    development_stage=development_stage,
                    confidence_score=float(data.get("confidence", 0.5)),
                    word_count=len(data.get("content", "").split()),
                    classification_reasoning=data.get("reasoning", "LLM classification"),
                    suggested_improvements=data.get("suggested_improvements", []),
                    metadata_completeness=float(data.get("metadata_completeness", 0.5))
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing LLM classification: {e}")
            return None
    
    def _combine_classifications(self, heuristic: Tuple[CodexObjectType, float], 
                               llm_result: Optional[ClassificationResult], 
                               content: str) -> ClassificationResult:
        """Combine heuristic and LLM classifications."""
        word_count = len(content.split())
        
        if llm_result and llm_result.confidence_score > 0.7:
            # Trust high-confidence LLM result
            return llm_result
        elif llm_result and llm_result.confidence_score > heuristic[1]:
            # LLM result is more confident than heuristic
            return llm_result
        else:
            # Use heuristic result
            object_type, confidence = heuristic
            
            # Determine development stage based on content analysis
            development_stage = self._determine_development_stage(content, object_type)
            
            return ClassificationResult(
                object_type=object_type,
                development_stage=development_stage,
                confidence_score=confidence,
                word_count=word_count,
                classification_reasoning=f"Heuristic classification based on word count ({word_count} words)",
                suggested_improvements=self._generate_improvement_suggestions(object_type, development_stage),
                metadata_completeness=0.5
            )
    
    def _determine_development_stage(self, content: str, object_type: CodexObjectType) -> DevelopmentStage:
        """Determine development stage based on content analysis."""
        # Simple heuristics for development stage
        if object_type in [CodexObjectType.IDEA, CodexObjectType.LOGLINE]:
            return DevelopmentStage.CONCEPT
        elif object_type in [CodexObjectType.SUMMARY, CodexObjectType.SYNOPSIS]:
            return DevelopmentStage.DEVELOPMENT
        elif object_type in [CodexObjectType.TREATMENT, CodexObjectType.OUTLINE]:
            return DevelopmentStage.DEVELOPMENT
        elif object_type == CodexObjectType.DRAFT:
            return DevelopmentStage.DRAFT
        elif object_type == CodexObjectType.MANUSCRIPT:
            return DevelopmentStage.COMPLETE
        else:
            return DevelopmentStage.CONCEPT
    
    def _generate_improvement_suggestions(self, object_type: CodexObjectType, 
                                        development_stage: DevelopmentStage) -> List[str]:
        """Generate improvement suggestions based on classification."""
        suggestions = []
        
        if object_type == CodexObjectType.IDEA:
            suggestions.append("Expand into a more detailed logline or summary")
            suggestions.append("Add genre and target audience information")
        elif object_type == CodexObjectType.LOGLINE:
            suggestions.append("Develop into a full synopsis")
            suggestions.append("Add character details and setting information")
        elif object_type == CodexObjectType.SUMMARY:
            suggestions.append("Expand into a detailed treatment")
            suggestions.append("Add more specific plot points and character arcs")
        
        if development_stage == DevelopmentStage.CONCEPT:
            suggestions.append("Consider developing the concept further")
            suggestions.append("Add more structural elements")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _generate_cache_key(self, content: str, metadata: Optional[Dict[str, Any]]) -> str:
        """Generate cache key for classification result."""
        import hashlib
        
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        metadata_hash = ""
        
        if metadata:
            metadata_str = str(sorted(metadata.items()))
            metadata_hash = hashlib.md5(metadata_str.encode()).hexdigest()[:8]
        
        return f"{content_hash}_{metadata_hash}"
    
    def get_classification_statistics(self) -> Dict[str, Any]:
        """Get statistics about classifications performed."""
        if not self.classification_cache:
            return {"total_classifications": 0}
        
        results = list(self.classification_cache.values())
        
        # Count by type
        type_counts = {}
        for result in results:
            type_name = result.object_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # Count by stage
        stage_counts = {}
        for result in results:
            stage_name = result.development_stage.value
            stage_counts[stage_name] = stage_counts.get(stage_name, 0) + 1
        
        # Average confidence
        avg_confidence = sum(r.confidence_score for r in results) / len(results)
        
        return {
            "total_classifications": len(results),
            "type_distribution": type_counts,
            "stage_distribution": stage_counts,
            "average_confidence": round(avg_confidence, 2)
        }
    
    def clear_cache(self):
        """Clear the classification cache."""
        self.classification_cache.clear()
        logger.info("Classification cache cleared")