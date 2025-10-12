"""
Content transformation system for ideation workflows.
Handles transformation between different content types and development stages.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum

from .codex_object import CodexObject, CodexObjectType, DevelopmentStage
from .classification import ContentClassifier, ClassificationResult
from nimble_llm_caller.core.llm_caller import LLMCaller
from nimble_llm_caller.models.request import LLMRequest, ResponseFormat

# Create global instance
enhanced_llm_caller = LLMCaller()

logger = logging.getLogger(__name__)


class TransformationType(Enum):
    """Types of content transformations."""
    EXPAND = "expand"  # Expand to more detailed form
    CONDENSE = "condense"  # Condense to shorter form
    RESTRUCTURE = "restructure"  # Change structure/format
    ENHANCE = "enhance"  # Add details without changing type
    CONVERT = "convert"  # Convert between types


@dataclass
class TransformationResult:
    """Result of a content transformation."""
    success: bool
    transformed_object: Optional[CodexObject]
    transformation_type: TransformationType
    source_type: CodexObjectType
    target_type: CodexObjectType
    confidence_score: float
    transformation_notes: str
    error_message: Optional[str] = None


class ContentTransformer:
    """
    Transforms CodexObjects between different types and development stages.
    Implements Requirements 0.3, 0.4 for content transformation.
    """
    
    def __init__(self):
        """Initialize the content transformer."""
        self.classifier = ContentClassifier()
        self.transformation_history: List[TransformationResult] = []
        logger.info("ContentTransformer initialized")
    
    def transform_content(self, source_object: CodexObject, 
                         target_type: CodexObjectType,
                         target_stage: Optional[DevelopmentStage] = None) -> TransformationResult:
        """
        Transform content to target type and stage.
        
        Args:
            source_object: Source CodexObject to transform
            target_type: Target content type
            target_stage: Optional target development stage
            
        Returns:
            TransformationResult with transformed content
        """
        try:
            # Classify current content
            current_classification = self.classifier.classify_content(
                source_object.content, 
                self._extract_metadata(source_object)
            )
            
            # Determine transformation type
            transformation_type = self._determine_transformation_type(
                current_classification.object_type, target_type
            )
            
            # Perform transformation
            if transformation_type == TransformationType.EXPAND:
                result = self._expand_content(source_object, target_type, target_stage)
            elif transformation_type == TransformationType.CONDENSE:
                result = self._condense_content(source_object, target_type, target_stage)
            elif transformation_type == TransformationType.RESTRUCTURE:
                result = self._restructure_content(source_object, target_type, target_stage)
            elif transformation_type == TransformationType.ENHANCE:
                result = self._enhance_content(source_object, target_type, target_stage)
            else:  # CONVERT
                result = self._convert_content(source_object, target_type, target_stage)
            
            # Store transformation history
            self.transformation_history.append(result)
            
            logger.info(f"Transformed {current_classification.object_type.value} to {target_type.value}")
            return result
            
        except Exception as e:
            logger.error(f"Error transforming content: {e}")
            return TransformationResult(
                success=False,
                transformed_object=None,
                transformation_type=TransformationType.CONVERT,
                source_type=source_object.object_type,
                target_type=target_type,
                confidence_score=0.0,
                transformation_notes=f"Transformation failed: {str(e)}",
                error_message=str(e)
            )
    
    def _determine_transformation_type(self, source_type: CodexObjectType, 
                                     target_type: CodexObjectType) -> TransformationType:
        """Determine the type of transformation needed."""
        # Define type hierarchy for expansion/condensation
        type_hierarchy = [
            CodexObjectType.IDEA,
            CodexObjectType.LOGLINE,
            CodexObjectType.SUMMARY,
            CodexObjectType.SYNOPSIS,
            CodexObjectType.TREATMENT,
            CodexObjectType.OUTLINE,
            CodexObjectType.DETAILED_OUTLINE,
            CodexObjectType.DRAFT,
            CodexObjectType.MANUSCRIPT
        ]
        
        try:
            source_index = type_hierarchy.index(source_type)
            target_index = type_hierarchy.index(target_type)
            
            if target_index > source_index:
                return TransformationType.EXPAND
            elif target_index < source_index:
                return TransformationType.CONDENSE
            else:
                return TransformationType.ENHANCE
                
        except ValueError:
            # Types not in hierarchy, default to convert
            return TransformationType.CONVERT
    
    def _expand_content(self, source_object: CodexObject, target_type: CodexObjectType,
                       target_stage: Optional[DevelopmentStage]) -> TransformationResult:
        """Expand content to a more detailed form."""
        try:
            # Build expansion prompt
            prompt = f"""Expand this {source_object.object_type.value} into a {target_type.value}:

Current content: {source_object.content}

Genre: {source_object.genre}
Target audience: {source_object.target_audience}

Please expand this into a detailed {target_type.value} while maintaining the core concept and adding appropriate detail for this content type."""
            
            # Create LLM request for expansion
            request = LLMRequest(
                prompt_key="expansion_prompt",
                model="gpt-4",
                response_format=ResponseFormat.TEXT,
                model_params={
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                metadata={
                    "content": prompt
                }
            )
            
            # Call LLM for expansion
            response = enhanced_llm_caller.call(request)
            
            if response and response.is_success:
                expanded_content = response.content
                
                # Create transformed object
                transformed_object = CodexObject(
                    title=source_object.title,
                    content=expanded_content,
                    genre=source_object.genre,
                    target_audience=source_object.target_audience,
                    object_type=target_type,
                    development_stage=target_stage or DevelopmentStage.DEVELOPMENT,
                    parent_uuid=source_object.uuid
                )
                
                return TransformationResult(
                    success=True,
                    transformed_object=transformed_object,
                    transformation_type=TransformationType.EXPAND,
                    source_type=source_object.object_type,
                    target_type=target_type,
                    confidence_score=0.8,
                    transformation_notes=f"Expanded from {source_object.object_type.value} to {target_type.value}"
                )
            else:
                raise ValueError("LLM expansion failed")
                
        except Exception as e:
            logger.error(f"Error expanding content: {e}")
            return TransformationResult(
                success=False,
                transformed_object=None,
                transformation_type=TransformationType.EXPAND,
                source_type=source_object.object_type,
                target_type=target_type,
                confidence_score=0.0,
                transformation_notes=f"Expansion failed: {str(e)}",
                error_message=str(e)
            )
    
    def _condense_content(self, source_object: CodexObject, target_type: CodexObjectType,
                         target_stage: Optional[DevelopmentStage]) -> TransformationResult:
        """Condense content to a shorter form."""
        try:
            # Build condensation prompt
            prompt = f"""Condense this {source_object.object_type.value} into a {target_type.value}:

Current content: {source_object.content}

Please condense this into a concise {target_type.value} while preserving the essential elements and core concept."""
            
            # Create LLM request for condensation
            request = LLMRequest(
                prompt_key="condensation_prompt",
                model="gpt-4",
                response_format=ResponseFormat.TEXT,
                model_params={
                    "temperature": 0.5,
                    "max_tokens": 500
                },
                metadata={
                    "content": prompt
                }
            )
            
            # Call LLM for condensation
            response = enhanced_llm_caller.call(request)
            
            if response and response.is_success:
                condensed_content = response.content
                
                # Create transformed object
                transformed_object = CodexObject(
                    title=source_object.title,
                    content=condensed_content,
                    genre=source_object.genre,
                    target_audience=source_object.target_audience,
                    object_type=target_type,
                    development_stage=target_stage or DevelopmentStage.CONCEPT,
                    parent_uuid=source_object.uuid
                )
                
                return TransformationResult(
                    success=True,
                    transformed_object=transformed_object,
                    transformation_type=TransformationType.CONDENSE,
                    source_type=source_object.object_type,
                    target_type=target_type,
                    confidence_score=0.8,
                    transformation_notes=f"Condensed from {source_object.object_type.value} to {target_type.value}"
                )
            else:
                raise ValueError("LLM condensation failed")
                
        except Exception as e:
            logger.error(f"Error condensing content: {e}")
            return TransformationResult(
                success=False,
                transformed_object=None,
                transformation_type=TransformationType.CONDENSE,
                source_type=source_object.object_type,
                target_type=target_type,
                confidence_score=0.0,
                transformation_notes=f"Condensation failed: {str(e)}",
                error_message=str(e)
            )
    
    def _restructure_content(self, source_object: CodexObject, target_type: CodexObjectType,
                           target_stage: Optional[DevelopmentStage]) -> TransformationResult:
        """Restructure content into a different format."""
        try:
            # Simple restructuring - copy content with new type
            transformed_object = CodexObject(
                title=source_object.title,
                content=source_object.content,
                genre=source_object.genre,
                target_audience=source_object.target_audience,
                object_type=target_type,
                development_stage=target_stage or source_object.development_stage,
                parent_uuid=source_object.uuid
            )
            
            return TransformationResult(
                success=True,
                transformed_object=transformed_object,
                transformation_type=TransformationType.RESTRUCTURE,
                source_type=source_object.object_type,
                target_type=target_type,
                confidence_score=0.9,
                transformation_notes=f"Restructured from {source_object.object_type.value} to {target_type.value}"
            )
            
        except Exception as e:
            logger.error(f"Error restructuring content: {e}")
            return TransformationResult(
                success=False,
                transformed_object=None,
                transformation_type=TransformationType.RESTRUCTURE,
                source_type=source_object.object_type,
                target_type=target_type,
                confidence_score=0.0,
                transformation_notes=f"Restructuring failed: {str(e)}",
                error_message=str(e)
            )
    
    def _enhance_content(self, source_object: CodexObject, target_type: CodexObjectType,
                        target_stage: Optional[DevelopmentStage]) -> TransformationResult:
        """Enhance content without changing its fundamental type."""
        try:
            # Build enhancement prompt
            prompt = f"""Enhance this {source_object.object_type.value} with additional detail and depth:

Current content: {source_object.content}

Genre: {source_object.genre}
Target audience: {source_object.target_audience}

Please enhance the content by adding more detail, depth, and richness while maintaining the same content type and core concept."""
            
            # Create LLM request for enhancement
            request = LLMRequest(
                prompt_key="enhancement_prompt",
                model="gpt-4",
                response_format=ResponseFormat.TEXT,
                model_params={
                    "temperature": 0.6,
                    "max_tokens": 1500
                },
                metadata={
                    "content": prompt
                }
            )
            
            # Call LLM for enhancement
            response = enhanced_llm_caller.call(request)
            
            if response and response.is_success:
                enhanced_content = response.content
                
                # Create enhanced object
                transformed_object = CodexObject(
                    title=source_object.title,
                    content=enhanced_content,
                    genre=source_object.genre,
                    target_audience=source_object.target_audience,
                    object_type=target_type,
                    development_stage=target_stage or DevelopmentStage.DEVELOPMENT,
                    parent_uuid=source_object.uuid
                )
                
                return TransformationResult(
                    success=True,
                    transformed_object=transformed_object,
                    transformation_type=TransformationType.ENHANCE,
                    source_type=source_object.object_type,
                    target_type=target_type,
                    confidence_score=0.8,
                    transformation_notes=f"Enhanced {source_object.object_type.value} with additional detail"
                )
            else:
                raise ValueError("LLM enhancement failed")
                
        except Exception as e:
            logger.error(f"Error enhancing content: {e}")
            return TransformationResult(
                success=False,
                transformed_object=None,
                transformation_type=TransformationType.ENHANCE,
                source_type=source_object.object_type,
                target_type=target_type,
                confidence_score=0.0,
                transformation_notes=f"Enhancement failed: {str(e)}",
                error_message=str(e)
            )
    
    def _convert_content(self, source_object: CodexObject, target_type: CodexObjectType,
                        target_stage: Optional[DevelopmentStage]) -> TransformationResult:
        """Convert content between different types."""
        try:
            # Generic conversion - copy with new type
            transformed_object = CodexObject(
                title=source_object.title,
                content=source_object.content,
                genre=source_object.genre,
                target_audience=source_object.target_audience,
                object_type=target_type,
                development_stage=target_stage or source_object.development_stage,
                parent_uuid=source_object.uuid
            )
            
            return TransformationResult(
                success=True,
                transformed_object=transformed_object,
                transformation_type=TransformationType.CONVERT,
                source_type=source_object.object_type,
                target_type=target_type,
                confidence_score=0.7,
                transformation_notes=f"Converted from {source_object.object_type.value} to {target_type.value}"
            )
            
        except Exception as e:
            logger.error(f"Error converting content: {e}")
            return TransformationResult(
                success=False,
                transformed_object=None,
                transformation_type=TransformationType.CONVERT,
                source_type=source_object.object_type,
                target_type=target_type,
                confidence_score=0.0,
                transformation_notes=f"Conversion failed: {str(e)}",
                error_message=str(e)
            )
    
    def _extract_metadata(self, codex_object: CodexObject) -> Dict[str, Any]:
        """Extract metadata from CodexObject for classification."""
        return {
            "title": codex_object.title,
            "genre": codex_object.genre,
            "target_audience": codex_object.target_audience,
            "word_count": codex_object.word_count,
            "object_type": codex_object.object_type.value,
            "development_stage": codex_object.development_stage.value
        }
    
    def get_transformation_suggestions(self, source_object: CodexObject) -> List[Dict[str, Any]]:
        """Get suggestions for possible transformations."""
        suggestions = []
        
        try:
            current_type = source_object.object_type
            
            # Suggest expansions
            if current_type == CodexObjectType.IDEA:
                suggestions.extend([
                    {"target_type": CodexObjectType.LOGLINE, "reason": "Develop into focused logline"},
                    {"target_type": CodexObjectType.SUMMARY, "reason": "Expand into story summary"}
                ])
            elif current_type == CodexObjectType.LOGLINE:
                suggestions.extend([
                    {"target_type": CodexObjectType.SYNOPSIS, "reason": "Develop into full synopsis"},
                    {"target_type": CodexObjectType.TREATMENT, "reason": "Expand into detailed treatment"}
                ])
            elif current_type == CodexObjectType.SUMMARY:
                suggestions.extend([
                    {"target_type": CodexObjectType.SYNOPSIS, "reason": "Develop into comprehensive synopsis"},
                    {"target_type": CodexObjectType.OUTLINE, "reason": "Structure into story outline"}
                ])
            
            # Suggest condensations
            if current_type in [CodexObjectType.SYNOPSIS, CodexObjectType.TREATMENT]:
                suggestions.append({
                    "target_type": CodexObjectType.LOGLINE, 
                    "reason": "Condense to essential logline"
                })
            
            # Suggest enhancements
            suggestions.append({
                "target_type": current_type,
                "reason": "Enhance current content with more detail"
            })
            
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            logger.error(f"Error getting transformation suggestions: {e}")
            return []
    
    def batch_transform(self, objects: List[CodexObject], target_type: CodexObjectType,
                       target_stage: Optional[DevelopmentStage] = None) -> List[TransformationResult]:
        """Transform multiple objects in batch."""
        results = []
        
        for obj in objects:
            try:
                result = self.transform_content(obj, target_type, target_stage)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in batch transformation for {obj.uuid}: {e}")
                results.append(TransformationResult(
                    success=False,
                    transformed_object=None,
                    transformation_type=TransformationType.CONVERT,
                    source_type=obj.object_type,
                    target_type=target_type,
                    confidence_score=0.0,
                    transformation_notes=f"Batch transformation failed: {str(e)}",
                    error_message=str(e)
                ))
        
        successful_count = sum(1 for r in results if r.success)
        logger.info(f"Batch transformation completed: {successful_count}/{len(objects)} successful")
        
        return results
    
    def get_transformation_statistics(self) -> Dict[str, Any]:
        """Get statistics about transformations performed."""
        if not self.transformation_history:
            return {"total_transformations": 0}
        
        total_transformations = len(self.transformation_history)
        successful_transformations = sum(1 for t in self.transformation_history if t.success)
        
        # Count by transformation type
        type_counts = {}
        for result in self.transformation_history:
            type_name = result.transformation_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # Average confidence
        successful_results = [t for t in self.transformation_history if t.success]
        avg_confidence = 0.0
        if successful_results:
            avg_confidence = sum(r.confidence_score for r in successful_results) / len(successful_results)
        
        return {
            "total_transformations": total_transformations,
            "successful_transformations": successful_transformations,
            "success_rate": successful_transformations / total_transformations if total_transformations > 0 else 0,
            "transformation_type_distribution": type_counts,
            "average_confidence": round(avg_confidence, 2)
        }
    
    def clear_history(self):
        """Clear transformation history."""
        self.transformation_history.clear()
        logger.info("Transformation history cleared")