"""
Content Type Detection System

Provides intelligent content type detection using both rule-based and LLM-based approaches.
"""

import re
from typing import Tuple, Dict, Any, List, Union
from ..core.simple_codex_object import CodexObjectType
from ..config.model_config import ModelConfigManager


class RuleBasedClassifier:
    """Rule-based content type classification using heuristics."""
    
    def __init__(self):
        self.patterns = {
            'list_separators': [
                r'^\d+\.\s+',  # 1. Item
                r'^-\s+',      # - Item
                r'^•\s+',      # • Item
                r'^\*\s+',     # * Item
                r'^\w+:\s*$',  # Title: (followed by content)
                r'^={3,}',     # === separator
                r'^-{3,}',     # --- separator
                r'^\n\s*\n',   # Double line breaks
            ],
            'multi_object_indicators': [
                r'idea\s*\d+',     # "Idea 1", "Idea 2"
                r'story\s*\d+',    # "Story 1", "Story 2"
                r'concept\s*\d+',  # "Concept 1", "Concept 2"
                r'option\s*\d+',   # "Option 1", "Option 2"
                r'version\s*\d+',  # "Version 1", "Version 2"
            ],
            'outline_markers': [
                r'^\d+\.',  # 1. 2. 3.
                r'^-\s',    # - bullet points
                r'^•\s',    # • bullet points
                r'^Chapter \d+',  # Chapter 1
                r'^Scene \d+',    # Scene 1
                r'^Act [IVX]+',   # Act I, Act II
                r'^Part \d+',     # Part 1
                r'^\w+:$',        # Character: (dialogue format)
            ],
            'narrative_indicators': [
                r'"[^"]*"',  # Dialogue in quotes
                r"'[^']*'",  # Dialogue in single quotes
                r'"[^"]*"',  # Dialogue in smart quotes
                r'\bsaid\b', r'\basked\b', r'\breplied\b',  # Dialogue tags
                r'\bHe\b', r'\bShe\b', r'\bThey\b',  # Pronouns indicating narrative
            ],
            'synopsis_indicators': [
                r'\bprotagonist\b', r'\bantagonist\b', r'\bcharacter\b',
                r'\bplot\b', r'\bstory\b', r'\bnarrative\b',
                r'\bbeginning\b', r'\bmiddle\b', r'\bend\b',
                r'\bconflict\b', r'\bresolution\b', r'\bclimax\b',
            ]
        }
    
    def classify(self, content: str) -> Dict[str, Any]:
        """Classify content using rule-based heuristics."""
        if not content or not content.strip():
            return {
                'type': CodexObjectType.IDEA,
                'confidence': 0.1,
                'reasoning': 'Empty content defaulted to idea'
            }
        
        content = content.strip()
        word_count = len(content.split())
        line_count = len(content.split('\n'))
        
        # Very short content (1-10 words)
        if word_count <= 10:
            if self._has_outline_structure(content):
                return {
                    'type': CodexObjectType.OUTLINE,
                    'confidence': 0.9,
                    'reasoning': f'Very short ({word_count} words) with outline structure'
                }
            elif self._looks_like_logline(content):
                return {
                    'type': CodexObjectType.LOGLINE,
                    'confidence': 0.8,
                    'reasoning': f'Very short ({word_count} words) with logline structure'
                }
            else:
                return {
                    'type': CodexObjectType.IDEA,
                    'confidence': 0.9,
                    'reasoning': f'Very short content ({word_count} words)'
                }
        
        # Short content (11-50 words)
        elif word_count <= 50:
            if self._has_outline_structure(content):
                return {
                    'type': CodexObjectType.OUTLINE,
                    'confidence': 0.9,
                    'reasoning': f'Short content ({word_count} words) with clear outline structure'
                }
            elif self._looks_like_logline(content):
                return {
                    'type': CodexObjectType.LOGLINE,
                    'confidence': 0.9,
                    'reasoning': f'Short content ({word_count} words) with logline structure'
                }
            else:
                return {
                    'type': CodexObjectType.IDEA,
                    'confidence': 0.8,
                    'reasoning': f'Short content ({word_count} words)'
                }
        
        # Medium content (51-500 words)
        elif word_count <= 500:
            if self._has_outline_structure(content):
                return {
                    'type': CodexObjectType.OUTLINE,
                    'confidence': 0.9,
                    'reasoning': f'Medium length ({word_count} words) with outline structure'
                }
            elif self._has_synopsis_indicators(content):
                return {
                    'type': CodexObjectType.SYNOPSIS,
                    'confidence': 0.7,
                    'reasoning': f'Medium length ({word_count} words) with synopsis indicators'
                }
            else:
                return {
                    'type': CodexObjectType.SUMMARY,
                    'confidence': 0.6,
                    'reasoning': f'Medium length content ({word_count} words)'
                }
        
        # Long content (501-2000 words)
        elif word_count <= 2000:
            if self._has_outline_structure(content):
                return {
                    'type': CodexObjectType.OUTLINE,
                    'confidence': 0.8,
                    'reasoning': f'Long content ({word_count} words) with outline structure'
                }
            elif self._has_narrative_structure(content):
                return {
                    'type': CodexObjectType.DRAFT,
                    'confidence': 0.7,
                    'reasoning': f'Long content ({word_count} words) with narrative elements'
                }
            else:
                return {
                    'type': CodexObjectType.SYNOPSIS,
                    'confidence': 0.7,
                    'reasoning': f'Long content ({word_count} words) without clear structure'
                }
        
        # Very long content (2000+ words)
        else:
            if self._has_narrative_structure(content):
                return {
                    'type': CodexObjectType.MANUSCRIPT,
                    'confidence': 0.8,
                    'reasoning': f'Very long content ({word_count} words) with narrative structure'
                }
            else:
                return {
                    'type': CodexObjectType.DRAFT,
                    'confidence': 0.6,
                    'reasoning': f'Very long content ({word_count} words)'
                }
    
    def _looks_like_logline(self, content: str) -> bool:
        """Check if content looks like a logline."""
        # Loglines are typically one sentence with specific structure
        sentences = content.split('.')
        if len(sentences) > 2:
            return False
        
        # Look for logline keywords
        logline_keywords = ['when', 'must', 'after', 'discovers', 'finds', 'learns']
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in logline_keywords)
    
    def _has_outline_structure(self, content: str) -> bool:
        """Check if content has outline-like structure."""
        outline_score = 0
        
        for pattern in self.patterns['outline_markers']:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            outline_score += len(matches)
        
        # Also check for multiple lines that look like headings/sections
        lines = content.split('\n')
        heading_lines = 0
        for line in lines:
            line = line.strip()
            if line and (line.endswith(':') or 
                        re.match(r'^(Chapter|Scene|Act|Part)\s+\w+', line, re.IGNORECASE) or
                        re.match(r'^\d+\.', line) or
                        line.startswith('-') or line.startswith('•')):
                heading_lines += 1
        
        return outline_score > 0 or heading_lines >= 2
    
    def _has_narrative_structure(self, content: str) -> bool:
        """Check if content has narrative prose structure."""
        narrative_score = 0
        
        # Check for dialogue
        for pattern in self.patterns['narrative_indicators']:
            matches = re.findall(pattern, content, re.IGNORECASE)
            narrative_score += len(matches)
        
        # Check for paragraph structure
        paragraphs = content.split('\n\n')
        if len(paragraphs) > 2:
            narrative_score += 2
        
        return narrative_score > 3
    
    def _has_synopsis_indicators(self, content: str) -> bool:
        """Check if content has synopsis-like indicators."""
        synopsis_score = 0
        content_lower = content.lower()
        
        for pattern in self.patterns['synopsis_indicators']:
            matches = re.findall(pattern, content_lower)
            synopsis_score += len(matches)
        
        return synopsis_score > 2
    
    def detect_multiple_objects(self, content: str) -> Dict[str, Any]:
        """Detect if content contains multiple CodexObjects."""
        if not content or not content.strip():
            return {
                'is_multiple': False,
                'count': 0,
                'separator_type': None,
                'confidence': 0.0,
                'reasoning': 'Empty content'
            }
        
        content = content.strip()
        lines = content.split('\n')
        
        # Count potential separators
        separator_counts = {}
        total_separators = 0
        
        for separator_type, patterns in [
            ('numbered_list', [r'^\d+\.\s+']),
            ('bullet_list', [r'^[-•*]\s+']),
            ('titled_sections', [r'^\w+:\s*$', r'^.{1,50}:$']),
            ('line_separators', [r'^={3,}', r'^-{3,}']),
            ('multi_indicators', self.patterns['multi_object_indicators'])
        ]:
            count = 0
            for pattern in patterns:
                for line in lines:
                    if re.search(pattern, line.strip(), re.IGNORECASE):
                        count += 1
            
            if count > 0:
                separator_counts[separator_type] = count
                total_separators += count
        
        # Check for paragraph-based separation (double line breaks)
        paragraphs = re.split(r'\n\s*\n', content)
        meaningful_paragraphs = [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 10]
        
        # Determine if this looks like multiple objects
        is_multiple = False
        estimated_count = 1
        primary_separator = None
        confidence = 0.0
        reasoning = "Single object detected"
        
        # Check for chapter/section patterns (even without perfect formatting)
        chapter_patterns = [
            r'chapter\s+\d+',
            r'scene\s+\d+', 
            r'act\s+[ivx]+',
            r'part\s+\d+',
            r'section\s+\d+'
        ]
        
        chapter_count = 0
        for pattern in chapter_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            chapter_count += len(matches)
        
        # Check for character/concept patterns
        concept_patterns = [
            r'character\s+\d+',
            r'idea\s+\d+',
            r'concept\s+\d+',
            r'story\s+\d+',
            r'option\s+\d+'
        ]
        
        concept_count = 0
        for pattern in concept_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            concept_count += len(matches)
        
        # Strong indicators of multiple objects
        if separator_counts.get('numbered_list', 0) >= 2:
            is_multiple = True
            estimated_count = separator_counts['numbered_list']
            primary_separator = 'numbered_list'
            confidence = 0.9
            reasoning = f"Found {estimated_count} numbered items"
        
        elif separator_counts.get('bullet_list', 0) >= 2:
            is_multiple = True
            estimated_count = separator_counts['bullet_list']
            primary_separator = 'bullet_list'
            confidence = 0.9
            reasoning = f"Found {estimated_count} bulleted items"
        
        elif chapter_count >= 2:
            is_multiple = True
            estimated_count = chapter_count
            primary_separator = 'chapters'
            confidence = 0.9
            reasoning = f"Found {estimated_count} chapters/sections"
        
        elif concept_count >= 2:
            is_multiple = True
            estimated_count = concept_count
            primary_separator = 'concepts'
            confidence = 0.8
            reasoning = f"Found {estimated_count} numbered concepts/characters"
        
        elif separator_counts.get('titled_sections', 0) >= 2:
            is_multiple = True
            estimated_count = separator_counts['titled_sections']
            primary_separator = 'titled_sections'
            confidence = 0.8
            reasoning = f"Found {estimated_count} titled sections"
        
        elif separator_counts.get('multi_indicators', 0) >= 2:
            is_multiple = True
            estimated_count = separator_counts['multi_indicators']
            primary_separator = 'multi_indicators'
            confidence = 0.8
            reasoning = f"Found {estimated_count} numbered concepts/ideas"
        
        elif len(meaningful_paragraphs) >= 3 and len(meaningful_paragraphs) <= 10:
            # Multiple substantial paragraphs might be multiple objects
            # But be conservative - only if they look like separate concepts
            if self._paragraphs_look_like_separate_objects(meaningful_paragraphs):
                is_multiple = True
                estimated_count = len(meaningful_paragraphs)
                primary_separator = 'paragraphs'
                confidence = 0.6
                reasoning = f"Found {estimated_count} distinct paragraphs that appear to be separate objects"
        
        return {
            'is_multiple': is_multiple,
            'count': estimated_count,
            'separator_type': primary_separator,
            'confidence': confidence,
            'reasoning': reasoning,
            'separator_counts': separator_counts,
            'paragraph_count': len(meaningful_paragraphs)
        }
    
    def _paragraphs_look_like_separate_objects(self, paragraphs: List[str]) -> bool:
        """Check if paragraphs look like separate objects rather than one continuous text."""
        if len(paragraphs) < 2:
            return False
        
        # Look for indicators that these are separate concepts
        separate_indicators = 0
        
        for para in paragraphs:
            para_lower = para.lower()
            # Each paragraph starts like a new concept
            if (para.startswith(('A ', 'An ', 'The ')) or
                any(word in para_lower[:50] for word in ['story about', 'idea:', 'concept:', 'what if', 'imagine'])):
                separate_indicators += 1
        
        # If most paragraphs look like separate concepts
        return separate_indicators >= len(paragraphs) * 0.6
    
    def split_multiple_objects(self, content: str) -> List[str]:
        """Split content into individual objects based on detected separators."""
        detection = self.detect_multiple_objects(content)
        
        if not detection['is_multiple']:
            return [content]
        
        separator_type = detection['separator_type']
        
        if separator_type == 'numbered_list':
            # Split on numbered items
            parts = re.split(r'\n(?=\d+\.\s+)', content)
            return [part.strip() for part in parts if part.strip()]
        
        elif separator_type == 'bullet_list':
            # Split on bullet points
            parts = re.split(r'\n(?=[-•*]\s+)', content)
            return [part.strip() for part in parts if part.strip()]
        
        elif separator_type == 'titled_sections':
            # Split on titles (lines ending with colon)
            parts = re.split(r'\n(?=\w+:\s*$)', content, flags=re.MULTILINE)
            return [part.strip() for part in parts if part.strip()]
        
        elif separator_type == 'line_separators':
            # Split on separator lines
            parts = re.split(r'\n(?:={3,}|-{3,})\n', content)
            return [part.strip() for part in parts if part.strip()]
        
        elif separator_type == 'paragraphs':
            # Split on double line breaks
            parts = re.split(r'\n\s*\n', content)
            return [part.strip() for part in parts if part.strip() and len(part.strip()) > 10]
        
        else:
            # Fallback: try to split intelligently
            return [content]


class MockLLMClassifier:
    """Mock LLM classifier for testing purposes."""
    
    def __init__(self, model_config: ModelConfigManager):
        self.model_config = model_config
    
    def classify(self, content: str, selected_model: str) -> Dict[str, Any]:
        """Mock LLM classification - returns rule-based result with slight variation."""
        # For now, use rule-based classification as a mock
        rule_classifier = RuleBasedClassifier()
        result = rule_classifier.classify(content)
        
        # Add some mock LLM reasoning
        result['reasoning'] = f"LLM analysis ({selected_model}): {result['reasoning']}"
        result['confidence'] = min(result['confidence'] + 0.1, 1.0)  # Slightly higher confidence
        
        return result


class ContentTypeDetector:
    """Main content type detector that combines rule-based and LLM approaches."""
    
    def __init__(self):
        self.rule_classifier = RuleBasedClassifier()
        self.model_config = ModelConfigManager()
        self.llm_classifier = MockLLMClassifier(self.model_config)
        self.cache = {}  # Simple cache for repeated content
    
    def detect_type_and_multiplicity(self, content: str, use_llm: bool = False, selected_model: str = None) -> Dict[str, Any]:
        """
        Detect content type and whether it contains multiple objects.
        
        Args:
            content: The content to analyze
            use_llm: Whether to use LLM classification
            selected_model: Which model to use for LLM classification
            
        Returns:
            Dict with type, confidence, reasoning, and multiplicity info
        """
        if not content or not content.strip():
            return {
                'type': CodexObjectType.IDEA,
                'confidence': 0.1,
                'reasoning': "Empty content defaulted to idea",
                'is_multiple': False,
                'count': 0,
                'objects': []
            }
        
        # First check for multiple objects
        multiplicity = self.rule_classifier.detect_multiple_objects(content)
        
        if multiplicity['is_multiple']:
            # Split into individual objects and classify each
            individual_objects = self.rule_classifier.split_multiple_objects(content)
            object_results = []
            
            for i, obj_content in enumerate(individual_objects):
                obj_type, obj_confidence, obj_reasoning = self.detect_type(obj_content, use_llm, selected_model)
                object_results.append({
                    'content': obj_content,
                    'type': obj_type,
                    'confidence': obj_confidence,
                    'reasoning': obj_reasoning,
                    'index': i + 1
                })
            
            # Determine overall classification
            most_common_type = max(set(obj['type'] for obj in object_results), 
                                 key=lambda x: sum(1 for obj in object_results if obj['type'] == x))
            
            avg_confidence = sum(obj['confidence'] for obj in object_results) / len(object_results)
            combined_confidence = min(avg_confidence * multiplicity['confidence'], 1.0)
            
            return {
                'type': most_common_type,
                'confidence': combined_confidence,
                'reasoning': f"Multiple objects detected: {multiplicity['reasoning']}. Most common type: {most_common_type.value}",
                'is_multiple': True,
                'count': len(object_results),
                'objects': object_results,
                'separator_type': multiplicity['separator_type']
            }
        else:
            # Single object - use existing detection
            obj_type, obj_confidence, obj_reasoning = self.detect_type(content, use_llm, selected_model)
            return {
                'type': obj_type,
                'confidence': obj_confidence,
                'reasoning': obj_reasoning,
                'is_multiple': False,
                'count': 1,
                'objects': [{
                    'content': content,
                    'type': obj_type,
                    'confidence': obj_confidence,
                    'reasoning': obj_reasoning,
                    'index': 1
                }]
            }
    
    def detect_type(self, content: str, use_llm: bool = False, selected_model: str = None) -> Tuple[CodexObjectType, float, str]:
        """
        Detect content type with confidence score and reasoning.
        
        Args:
            content: The content to analyze
            use_llm: Whether to use LLM classification
            selected_model: Which model to use for LLM classification
            
        Returns:
            Tuple of (content_type, confidence, reasoning)
        """
        if not content or not content.strip():
            return CodexObjectType.IDEA, 0.1, "Empty content defaulted to idea"
        
        # Check cache first
        cache_key = f"{hash(content)}_{use_llm}_{selected_model}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            return cached['type'], cached['confidence'], cached['reasoning']
        
        # Get rule-based classification
        rule_result = self.rule_classifier.classify(content)
        
        if not use_llm:
            # Use rule-based result
            result = {
                'type': rule_result['type'],
                'confidence': rule_result['confidence'],
                'reasoning': f"Rule-based: {rule_result['reasoning']}"
            }
        else:
            # Use LLM classification
            if not selected_model:
                selected_model = self.model_config.get_available_models()[0]
            
            llm_result = self.llm_classifier.classify(content, selected_model)
            
            # Use LLM result if confidence is higher, otherwise use rule-based
            if llm_result['confidence'] > rule_result['confidence']:
                result = {
                    'type': llm_result['type'],
                    'confidence': llm_result['confidence'],
                    'reasoning': llm_result['reasoning']
                }
            else:
                result = {
                    'type': rule_result['type'],
                    'confidence': rule_result['confidence'],
                    'reasoning': f"Rule-based (higher confidence): {rule_result['reasoning']}"
                }
        
        # Cache the result
        self.cache[cache_key] = result
        
        return result['type'], result['confidence'], result['reasoning']
    
    def get_detection_details(self, content: str, use_llm: bool = False, selected_model: str = None) -> Dict[str, Any]:
        """Get detailed detection information including both rule-based and LLM results."""
        rule_result = self.rule_classifier.classify(content)
        
        details = {
            'content_length': len(content),
            'word_count': len(content.split()) if content else 0,
            'line_count': len(content.split('\n')) if content else 0,
            'rule_based': rule_result
        }
        
        if use_llm:
            if not selected_model:
                selected_model = self.model_config.get_available_models()[0]
            llm_result = self.llm_classifier.classify(content, selected_model)
            details['llm_based'] = llm_result
            details['selected_model'] = selected_model
        
        return details