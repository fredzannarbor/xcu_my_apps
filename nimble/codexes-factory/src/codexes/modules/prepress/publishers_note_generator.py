"""
Publisher's Note generator with structured formatting requirements.
"""

from typing import Dict, List, Any, Optional
import logging
from src.codexes.core.enhanced_llm_caller import EnhancedLLMCaller

logger = logging.getLogger(__name__)


class PublishersNoteGenerator:
    """Generate structured Publisher's Notes with specific formatting requirements"""
    
    def __init__(self, llm_caller: Optional[EnhancedLLMCaller] = None, llm_config: Optional[Dict[str, Any]] = None):
        self.llm_caller = llm_caller or EnhancedLLMCaller()
        self.llm_config = llm_config or {
            'model': 'gemini/gemini-2.5-pro',  # Default model
            'temperature': 0.7,
            'max_tokens': 8000
        }
        self.max_paragraph_length = 600
        self.required_paragraphs = 3
        
        logger.info(f"PublishersNoteGenerator initialized with model: {self.llm_config['model']}")
    
    def generate_publishers_note(self, book_metadata: Dict[str, Any]) -> str:
        """Generate 3-paragraph Publisher's Note with pilsa book explanation"""
        try:
            prompt = self._create_publishers_note_prompt(book_metadata)
            
            model_to_use = self.llm_config['model']
            logger.info(f"Generating publisher's note with model: {model_to_use}")
            
            response = self.llm_caller.call_llm_json_with_retry(
                prompt=prompt,
                expected_keys=['paragraph_1', 'paragraph_2', 'paragraph_3'],
                model_name=model_to_use
            )
            
            if response and all(f'paragraph_{i}' in response for i in range(1, 4)):
                # Validate and format paragraphs
                paragraphs = []
                for i in range(1, 4):
                    paragraph = response[f'paragraph_{i}']
                    if self.validate_paragraph_length(paragraph):
                        paragraphs.append(paragraph)
                    else:
                        # Truncate if too long
                        paragraphs.append(paragraph[:self.max_paragraph_length] + "...")
                
                # Ensure pilsa explanation is included
                note_text = "\n\n".join(paragraphs)
                note_text = self.ensure_pilsa_explanation(note_text)
                
                return note_text
            else:
                logger.error("Invalid response format for Publisher's Note")
                return self._generate_fallback_note(book_metadata)
                
        except Exception as e:
            logger.error(f"Error generating Publisher's Note: {e}")
            return self._generate_fallback_note(book_metadata)
    
    def _create_publishers_note_prompt(self, book_metadata: Dict[str, Any]) -> str:
        """Create prompt for Publisher's Note generation"""
        title = book_metadata.get('title', 'this book')
        topic = book_metadata.get('topic', 'personal development')
        
        return f"""
Generate a Publisher's Note for "{title}" with exactly 3 paragraphs. Each paragraph must be no more than 600 characters.

Requirements:
1. Explain once that this is a pilsa book (transcriptive meditation handbook with 90 quotations and 90 facing pages for journaling)
2. Include relevant current events context without being date-specific
3. Focus on motivating both publishers and readers
4. Topic focus: {topic}

Return JSON with keys: paragraph_1, paragraph_2, paragraph_3
"""
    
    def validate_paragraph_length(self, paragraph: str) -> bool:
        """Validate paragraph does not exceed 600 character limit"""
        return len(paragraph) <= self.max_paragraph_length
    
    def ensure_pilsa_explanation(self, content: str) -> str:
        """Ensure pilsa book explanation is included exactly once"""
        try:
            pilsa_keywords = ['pilsa', 'transcriptive meditation', '90 quotations', 'journaling']
            
            # Check if pilsa explanation already exists
            has_pilsa_explanation = any(keyword in content.lower() for keyword in pilsa_keywords)
            
            if not has_pilsa_explanation:
                # Add pilsa explanation to first paragraph
                paragraphs = content.split('\n\n')
                if paragraphs:
                    pilsa_sentence = " This pilsa book—a transcriptive meditation handbook—provides 90 carefully selected quotations with facing pages for personal reflection and journaling."
                    paragraphs[0] += pilsa_sentence
                    content = '\n\n'.join(paragraphs)
            
            return content
            
        except Exception as e:
            logger.error(f"Error ensuring pilsa explanation: {e}")
            return content
    
    def add_current_events_context(self, content: str, book_topic: str) -> str:
        """Add relevant current events without date-specific references"""
        try:
            # Generic current events context based on topic
            context_map = {
                'technology': 'rapid technological advancement',
                'space': 'renewed interest in space exploration',
                'sustainability': 'growing environmental awareness',
                'leadership': 'evolving workplace dynamics',
                'personal_development': 'increasing focus on mental wellness'
            }
            
            context = context_map.get(book_topic.lower(), 'current global challenges')
            
            # Add context naturally to content
            if 'in today\'s' not in content.lower() and 'current' not in content.lower():
                # Find appropriate place to insert context
                sentences = content.split('. ')
                if len(sentences) > 1:
                    # Insert after first sentence
                    sentences[1] = f"In today's era of {context}, {sentences[1].lower()}"
                    content = '. '.join(sentences)
            
            return content
            
        except Exception as e:
            logger.error(f"Error adding current events context: {e}")
            return content
    
    def _generate_fallback_note(self, book_metadata: Dict[str, Any]) -> str:
        """Generate fallback Publisher's Note when LLM fails"""
        title = book_metadata.get('title', 'this work')
        
        return f"""This pilsa book—a transcriptive meditation handbook—presents 90 carefully curated quotations with facing pages designed for personal reflection and journaling. Each quote has been selected to inspire deep contemplation and meaningful self-discovery.

In our rapidly evolving world, the need for thoughtful reflection and personal growth has never been more important. "{title}" offers readers a structured approach to meditation and self-examination through the wisdom of great thinkers and leaders.

We believe this collection will serve both as a valuable resource for publishers seeking meaningful content and as a transformative tool for readers committed to personal development and mindful living."""