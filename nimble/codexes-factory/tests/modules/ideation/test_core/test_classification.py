"""
Unit tests for ContentClassifier.
"""

import pytest
from unittest.mock import Mock, patch

from codexes.modules.ideation.core.classification import (
    ContentClassifier, ClassificationResult
)
from codexes.modules.ideation.core.codex_object import (
    CodexObject, CodexObjectType, DevelopmentStage
)


class TestContentClassifier:
    """Test cases for ContentClassifier class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = ContentClassifier()
    
    def test_classifier_initialization(self):
        """Test classifier initialization."""
        assert self.classifier.llm_caller is not None
        assert self.classifier.classification_prompts is not None
        assert len(self.classifier.word_count_thresholds) > 0
    
    def test_heuristic_classification_logline(self):
        """Test heuristic classification for logline content."""
        content = "A young wizard discovers he has magical powers."
        
        object_type, confidence = self.classifier._heuristic_classification(content)
        
        assert object_type == CodexObjectType.LOGLINE
        assert confidence > 0.5
    
    def test_heuristic_classification_idea(self):
        """Test heuristic classification for idea content."""
        content = """
        A story about a detective in Victorian London who solves supernatural mysteries.
        The detective has a special ability to see ghosts and communicate with spirits.
        Each case involves both traditional detective work and supernatural elements.
        """
        
        object_type, confidence = self.classifier._heuristic_classification(content)
        
        assert object_type == CodexObjectType.IDEA
        assert confidence > 0.5
    
    def test_heuristic_classification_synopsis(self):
        """Test heuristic classification for synopsis content."""
        content = """
        Detective Sarah Chen has always been able to see things others cannot. When a series of 
        mysterious deaths plague Victorian London, she discovers that the victims were all 
        connected to an ancient artifact. As she investigates deeper, she realizes that the 
        artifact is a gateway between the world of the living and the dead. With the help of 
        her ghostly informants, Sarah must solve the case before more innocent people die. 
        But the killer is not human, and Sarah's supernatural abilities may be the only thing 
        standing between London and a supernatural catastrophe. The investigation leads her 
        through the dark underbelly of London society, from opium dens to aristocratic mansions, 
        as she races against time to prevent an otherworldly invasion.
        """ * 3  # Make it longer
        
        object_type, confidence = self.classifier._heuristic_classification(content)
        
        assert object_type in [CodexObjectType.SYNOPSIS, CodexObjectType.TREATMENT]
        assert confidence > 0.4
    
    def test_heuristic_classification_outline(self):
        """Test heuristic classification for outline content."""
        content = """
        Chapter 1: The First Death
        - Introduction of Detective Sarah Chen
        - Discovery of the first victim
        - Initial investigation reveals supernatural elements
        
        Chapter 2: The Pattern Emerges
        - Second victim found with similar circumstances
        - Sarah's ghostly informants provide clues
        - Connection to ancient artifact discovered
        
        Chapter 3: Into the Underground
        - Investigation leads to London's criminal underworld
        - Sarah encounters resistance from both living and dead
        - Artifact's true purpose begins to emerge
        """ * 5  # Make it longer
        
        object_type, confidence = self.classifier._heuristic_classification(content)
        
        assert object_type in [CodexObjectType.OUTLINE, CodexObjectType.DETAILED_OUTLINE]
        assert confidence > 0.5
    
    @patch('src.codexes.modules.ideation.core.classification.enhanced_llm_caller')
    def test_llm_classification_success(self, mock_llm_caller):
        """Test successful LLM classification."""
        # Mock LLM response
        mock_response = {
            "object_type": "SYNOPSIS",
            "development_stage": "DEVELOPMENT",
            "confidence_score": 0.85,
            "reasoning": "Content shows detailed plot development typical of a synopsis",
            "word_count_analysis": "Word count appropriate for synopsis",
            "structure_analysis": "Narrative structure with plot progression",
            "completeness_analysis": "Well-developed with clear beginning, middle, end"
        }
        
        mock_llm_caller.call_llm_json_with_retry.return_value = mock_response
        
        content = "A detailed story about a detective solving supernatural mysteries."
        result = self.classifier._llm_classification(content)
        
        assert result is not None
        assert result.object_type == CodexObjectType.SYNOPSIS
        assert result.development_stage == DevelopmentStage.DEVELOPMENT
        assert result.confidence_score == 0.85
        assert "detailed plot development" in result.reasoning
    
    @patch('src.codexes.modules.ideation.core.classification.enhanced_llm_caller')
    def test_llm_classification_failure(self, mock_llm_caller):
        """Test LLM classification failure handling."""
        mock_llm_caller.call_llm_json_with_retry.return_value = None
        
        content = "Test content"
        result = self.classifier._llm_classification(content)
        
        assert result is None
    
    @patch('src.codexes.modules.ideation.core.classification.enhanced_llm_caller')
    def test_classify_content_empty(self, mock_llm_caller):
        """Test classification of empty content."""
        result = self.classifier.classify_content("")
        
        assert result.object_type == CodexObjectType.UNKNOWN
        assert result.confidence_score == 0.0
        assert "No content provided" in result.reasoning
    
    @patch('src.codexes.modules.ideation.core.classification.enhanced_llm_caller')
    def test_classify_content_with_llm_agreement(self, mock_llm_caller):
        """Test classification when heuristic and LLM agree."""
        # Mock LLM response that agrees with heuristic
        mock_response = {
            "object_type": "IDEA",
            "development_stage": "CONCEPT",
            "confidence_score": 0.8,
            "reasoning": "Content is a basic story concept",
            "word_count_analysis": "Appropriate length for idea",
            "structure_analysis": "Simple concept structure"
        }
        
        mock_llm_caller.call_llm_json_with_retry.return_value = mock_response
        
        content = "A story about time travel and its consequences on history."
        result = self.classifier.classify_content(content)
        
        assert result.object_type == CodexObjectType.IDEA
        assert result.confidence_score > 0.8  # Should be boosted due to agreement
        assert "agree" in result.reasoning.lower()
    
    @patch('src.codexes.modules.ideation.core.classification.enhanced_llm_caller')
    def test_classify_content_with_llm_disagreement(self, mock_llm_caller):
        """Test classification when heuristic and LLM disagree."""
        # Mock LLM response that disagrees with heuristic (high confidence)
        mock_response = {
            "object_type": "SYNOPSIS",
            "development_stage": "DEVELOPMENT",
            "confidence_score": 0.9,
            "reasoning": "Despite short length, content shows synopsis characteristics",
            "word_count_analysis": "Concise but complete",
            "structure_analysis": "Synopsis-like structure"
        }
        
        mock_llm_caller.call_llm_json_with_retry.return_value = mock_response
        
        # Short content that heuristic would classify as IDEA
        content = "A detective story with supernatural elements."
        result = self.classifier.classify_content(content)
        
        # Should use LLM classification due to high confidence
        assert result.object_type == CodexObjectType.SYNOPSIS
        assert "override" in result.reasoning.lower()
    
    @patch('src.codexes.modules.ideation.core.classification.enhanced_llm_caller')
    def test_check_similarity_to_existing(self, mock_llm_caller):
        """Test similarity checking against existing classes."""
        mock_llm_caller.call_llm_with_retry.return_value = {
            'content': 'Mystery'
        }
        
        content = "A detective solving crimes in London"
        existing_classes = ["Mystery", "Romance", "Science Fiction"]
        
        result = self.classifier._check_similarity_to_existing(content, existing_classes)
        
        assert result == "Mystery"
    
    @patch('src.codexes.modules.ideation.core.classification.enhanced_llm_caller')
    def test_check_similarity_unknown(self, mock_llm_caller):
        """Test similarity checking returning UNKNOWN."""
        mock_llm_caller.call_llm_with_retry.return_value = {
            'content': 'UNKNOWN'
        }
        
        content = "A very unique and unusual story concept"
        existing_classes = ["Mystery", "Romance", "Science Fiction"]
        
        result = self.classifier._check_similarity_to_existing(content, existing_classes)
        
        assert result == "UNKNOWN"
    
    def test_assign_to_class_with_similarity(self):
        """Test assigning content to existing class."""
        with patch.object(self.classifier, '_check_similarity_to_existing') as mock_similarity:
            mock_similarity.return_value = "Fantasy"
            
            content = "A story about magic and wizards"
            existing_classes = ["Fantasy", "Mystery", "Romance"]
            
            result = self.classifier.assign_to_class(content, existing_classes)
            
            assert result == "Fantasy"
    
    def test_assign_to_class_unknown(self):
        """Test assigning content to UNKNOWN class."""
        with patch.object(self.classifier, '_check_similarity_to_existing') as mock_similarity:
            mock_similarity.return_value = "UNKNOWN"
            
            content = "A completely unique story concept"
            existing_classes = ["Fantasy", "Mystery", "Romance"]
            
            result = self.classifier.assign_to_class(content, existing_classes)
            
            assert result == "UNKNOWN"
    
    @patch('src.codexes.modules.ideation.core.classification.enhanced_llm_caller')
    def test_assess_development_potential(self, mock_llm_caller):
        """Test development potential assessment."""
        mock_response = {
            "development_completeness": 0.75,
            "readiness_for_next_stage": True,
            "suggested_next_stage": "SYNOPSIS",
            "missing_elements": ["character development"],
            "strengths": ["compelling premise"],
            "improvement_suggestions": ["Add character details"]
        }
        
        mock_llm_caller.call_llm_json_with_retry.return_value = mock_response
        
        codex_object = CodexObject(
            title="Test Idea",
            content="A story about time travel",
            object_type=CodexObjectType.IDEA
        )
        
        result = self.classifier.assess_development_potential(codex_object)
        
        assert result["development_completeness"] == 0.75
        assert result["readiness_for_next_stage"] is True
        assert result["suggested_next_stage"] == "SYNOPSIS"
        assert "character development" in result["missing_elements"]
    
    def test_get_classification_confidence(self):
        """Test getting classification confidence."""
        codex_object = CodexObject(
            title="Test",
            content="Test content"
        )
        codex_object.confidence_score = 0.85
        
        confidence = self.classifier.get_classification_confidence(codex_object)
        
        assert confidence == 0.85
    
    def test_suggest_reclassification_low_confidence(self):
        """Test reclassification suggestion for low confidence."""
        codex_object = CodexObject(
            title="Test",
            content="Test content for reclassification"
        )
        codex_object.confidence_score = 0.4  # Low confidence
        
        with patch.object(self.classifier, 'classify_content') as mock_classify:
            mock_result = ClassificationResult(
                object_type=CodexObjectType.SYNOPSIS,
                development_stage=DevelopmentStage.CONCEPT,
                confidence_score=0.8,
                reasoning="Reclassified with higher confidence",
                suggested_improvements=[],
                metadata={}
            )
            mock_classify.return_value = mock_result
            
            result = self.classifier.suggest_reclassification(codex_object)
            
            assert result is not None
            assert result.object_type == CodexObjectType.SYNOPSIS
            assert result.confidence_score == 0.8
    
    def test_suggest_reclassification_content_growth(self):
        """Test reclassification suggestion for significant content growth."""
        codex_object = CodexObject(
            title="Test",
            content="This is much longer content that has grown significantly from the original short idea. " * 50
        )
        codex_object.confidence_score = 0.8  # High confidence
        
        # Add processing history with old word count
        codex_object.processing_history.append({
            "action": "classified",
            "timestamp": "2024-01-01T00:00:00",
            "details": {"word_count": 10}  # Much smaller than current
        })
        
        with patch.object(self.classifier, 'classify_content') as mock_classify:
            mock_result = ClassificationResult(
                object_type=CodexObjectType.SYNOPSIS,
                development_stage=DevelopmentStage.DEVELOPMENT,
                confidence_score=0.9,
                reasoning="Reclassified due to content growth",
                suggested_improvements=[],
                metadata={}
            )
            mock_classify.return_value = mock_result
            
            result = self.classifier.suggest_reclassification(codex_object)
            
            assert result is not None
            assert result.object_type == CodexObjectType.SYNOPSIS
    
    def test_suggest_reclassification_no_need(self):
        """Test no reclassification needed for high confidence, stable content."""
        codex_object = CodexObject(
            title="Test",
            content="Stable content that doesn't need reclassification"
        )
        codex_object.confidence_score = 0.9  # High confidence
        
        result = self.classifier.suggest_reclassification(codex_object)
        
        assert result is None


class TestClassificationResult:
    """Test cases for ClassificationResult dataclass."""
    
    def test_classification_result_creation(self):
        """Test ClassificationResult creation."""
        result = ClassificationResult(
            object_type=CodexObjectType.SYNOPSIS,
            development_stage=DevelopmentStage.DEVELOPMENT,
            confidence_score=0.85,
            reasoning="Test reasoning",
            suggested_improvements=["Add more detail"],
            metadata={"test": "data"}
        )
        
        assert result.object_type == CodexObjectType.SYNOPSIS
        assert result.development_stage == DevelopmentStage.DEVELOPMENT
        assert result.confidence_score == 0.85
        assert result.reasoning == "Test reasoning"
        assert "Add more detail" in result.suggested_improvements
        assert result.metadata["test"] == "data"


class TestClassificationIntegration:
    """Integration tests for classification system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = ContentClassifier()
    
    def test_full_classification_workflow(self):
        """Test complete classification workflow."""
        # Create content that should be classified as IDEA
        content = """
        A young programmer discovers that reality is actually a computer simulation.
        She must decide whether to expose the truth or live in comfortable ignorance.
        The story explores themes of reality, choice, and the nature of existence.
        """
        
        with patch('src.codexes.modules.ideation.core.classification.enhanced_llm_caller') as mock_llm:
            # Mock LLM response
            mock_llm.call_llm_json_with_retry.return_value = {
                "object_type": "IDEA",
                "development_stage": "CONCEPT",
                "confidence_score": 0.8,
                "reasoning": "Content presents a basic story concept with clear premise",
                "word_count_analysis": "Appropriate length for idea stage",
                "structure_analysis": "Simple conceptual structure"
            }
            
            result = self.classifier.classify_content(content)
            
            assert result.object_type == CodexObjectType.IDEA
            assert result.development_stage == DevelopmentStage.CONCEPT
            assert result.confidence_score > 0.8
            assert len(result.suggested_improvements) >= 0
    
    def test_classification_with_existing_classes(self):
        """Test classification with existing class matching."""
        content = "A detective story set in Victorian London"
        existing_classes = ["Mystery", "Historical Fiction", "Romance"]
        
        with patch('src.codexes.modules.ideation.core.classification.enhanced_llm_caller') as mock_llm:
            # Mock classification response
            mock_llm.call_llm_json_with_retry.return_value = {
                "object_type": "IDEA",
                "development_stage": "CONCEPT",
                "confidence_score": 0.7,
                "reasoning": "Basic detective story concept"
            }
            
            # Mock similarity response
            mock_llm.call_llm_with_retry.return_value = {
                'content': 'Mystery'
            }
            
            result = self.classifier.classify_content(content, existing_classes)
            
            assert result.object_type == CodexObjectType.IDEA
            assert result.metadata.get("similar_to_existing") == "Mystery"