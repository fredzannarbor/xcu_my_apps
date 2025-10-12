"""
Pilsa book content processor to ensure proper identification and description.
"""

from typing import Dict, List, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)


class PilsaBookContentProcessor:
    """Ensure all book content properly identifies and describes pilsa format"""
    
    def __init__(self):
        self.pilsa_identifiers = [
            'pilsa book',
            'transcriptive meditation handbook',
            '90 quotations',
            '90 facing pages for journaling'
        ]
    
    def add_pilsa_identification(self, content: str, content_type: str) -> str:
        """Add pilsa book identification to various content types"""
        try:
            if content_type == 'back_cover':
                return self.enhance_back_cover_text(content)
            elif content_type == 'description':
                return self._add_pilsa_to_description(content)
            elif content_type == 'marketing':
                return self.update_marketing_copy(content)
            else:
                return self._add_generic_pilsa_identification(content)
                
        except Exception as e:
            logger.error(f"Error adding pilsa identification: {e}")
            return content
    
    def enhance_back_cover_text(self, back_text: str) -> str:
        """Enhance back cover text with pilsa book description"""
        try:
            if not self.validate_pilsa_description(back_text):
                # Add pilsa description at the beginning
                pilsa_intro = "This pilsa book—a transcriptive meditation handbook—presents 90 carefully selected quotations paired with 90 facing pages designed for personal reflection and journaling. "
                
                # Insert at the beginning or after first sentence
                if back_text:
                    sentences = back_text.split('. ')
                    if len(sentences) > 1:
                        sentences.insert(1, pilsa_intro.rstrip('. '))
                        back_text = '. '.join(sentences)
                    else:
                        back_text = pilsa_intro + back_text
                else:
                    back_text = pilsa_intro
            
            return back_text
            
        except Exception as e:
            logger.error(f"Error enhancing back cover text: {e}")
            return back_text
    
    def _add_pilsa_to_description(self, description: str) -> str:
        """Add pilsa identification to book description"""
        try:
            if not any(identifier.lower() in description.lower() for identifier in self.pilsa_identifiers):
                pilsa_description = " This unique pilsa format combines contemplative reading with structured journaling, featuring 90 quotations and 90 corresponding pages for personal reflection."
                
                # Add to end of first paragraph
                paragraphs = description.split('\n\n')
                if paragraphs:
                    paragraphs[0] += pilsa_description
                    description = '\n\n'.join(paragraphs)
                else:
                    description += pilsa_description
            
            return description
            
        except Exception as e:
            logger.error(f"Error adding pilsa to description: {e}")
            return description
    
    def update_marketing_copy(self, marketing_text: str) -> str:
        """Update marketing copy to emphasize meditative and journaling aspects"""
        try:
            # Key phrases to emphasize pilsa aspects
            pilsa_phrases = [
                "transcriptive meditation experience",
                "structured reflection and journaling",
                "90 quotations for contemplation",
                "facing pages for personal insights",
                "meditative reading practice"
            ]
            
            # Check if marketing copy already includes pilsa elements
            has_pilsa_elements = any(phrase.lower() in marketing_text.lower() 
                                   for phrase in pilsa_phrases)
            
            if not has_pilsa_elements:
                # Add pilsa marketing language
                pilsa_marketing = " Experience the transformative power of transcriptive meditation through this carefully crafted pilsa handbook, designed to deepen your reflective practice through guided quotations and structured journaling."
                marketing_text += pilsa_marketing
            
            return marketing_text
            
        except Exception as e:
            logger.error(f"Error updating marketing copy: {e}")
            return marketing_text
    
    def _add_generic_pilsa_identification(self, content: str) -> str:
        """Add generic pilsa identification to any content type"""
        try:
            if not self.validate_pilsa_description(content):
                pilsa_note = " [This is a pilsa book: a transcriptive meditation handbook with 90 quotations and facing pages for journaling.]"
                content += pilsa_note
            
            return content
            
        except Exception as e:
            logger.error(f"Error adding generic pilsa identification: {e}")
            return content
    
    def validate_pilsa_description(self, content: str) -> bool:
        """Validate that content properly describes pilsa book format"""
        try:
            content_lower = content.lower()
            
            # Check for key pilsa identifiers
            has_pilsa_term = 'pilsa' in content_lower
            has_meditation_term = any(term in content_lower 
                                    for term in ['meditation', 'contemplation', 'reflection'])
            has_quotation_count = '90' in content and 'quotation' in content_lower
            has_journaling_mention = any(term in content_lower 
                                       for term in ['journal', 'writing', 'reflection', 'notes'])
            
            # Content is valid if it has pilsa term OR (meditation + quotations + journaling)
            return has_pilsa_term or (has_meditation_term and has_quotation_count and has_journaling_mention)
            
        except Exception as e:
            logger.error(f"Error validating pilsa description: {e}")
            return False
    
    def extract_pilsa_elements(self, content: str) -> Dict[str, bool]:
        """Extract and analyze pilsa elements in content"""
        try:
            content_lower = content.lower()
            
            return {
                'has_pilsa_term': 'pilsa' in content_lower,
                'has_transcriptive_meditation': 'transcriptive meditation' in content_lower,
                'has_quotation_count': '90' in content and 'quotation' in content_lower,
                'has_journaling_pages': 'facing pages' in content_lower or 'journal' in content_lower,
                'has_meditation_reference': any(term in content_lower 
                                              for term in ['meditation', 'contemplation', 'mindfulness']),
                'has_reflection_reference': any(term in content_lower 
                                              for term in ['reflection', 'introspection', 'self-examination'])
            }
            
        except Exception as e:
            logger.error(f"Error extracting pilsa elements: {e}")
            return {}
    
    def generate_pilsa_summary(self, book_metadata: Dict[str, Any]) -> str:
        """Generate a comprehensive pilsa book summary"""
        try:
            title = book_metadata.get('title', 'This Book')
            topic = book_metadata.get('topic', 'personal development')
            
            summary = f"""
{title} is a pilsa book—a transcriptive meditation handbook designed for deep personal reflection and growth. This unique format presents 90 carefully curated quotations focused on {topic}, each paired with a facing page for journaling and contemplative writing.

The pilsa methodology combines the wisdom of great thinkers with structured space for personal insight, creating a transformative reading and writing experience. Each quotation serves as a meditation prompt, inviting readers to explore their own thoughts, reactions, and insights through guided reflection.

This handbook serves both as a source of inspiration and a practical tool for developing a regular practice of mindful reading and reflective writing, making it an ideal companion for anyone seeking deeper self-understanding and personal growth.
"""
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error generating pilsa summary: {e}")
            return "This pilsa book combines quotations with journaling for personal reflection."