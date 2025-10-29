# ollama run gpt-oss:20b
"""
Publisher's Note Generator - Enhanced Publisher's Note generation with structured formatting
"""

import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PublishersNoteGenerator:
    """Enhanced Publisher's Note generation with structured formatting"""
    
    def __init__(self):
        self.max_paragraphs = 3
        self.max_chars_per_paragraph = 600
        self.pilsa_explanation_included = False
        self.current_events_keywords = [
            'contemporary', 'modern', 'current', 'today', 'recent',
            'emerging', 'evolving', 'changing', 'dynamic', 'relevant'
        ]
    
    def generate_publishers_note(self, book_data: Dict[str, Any], 
                                content_context: Optional[str] = None) -> str:
        """Generate structured Publisher's Note with exactly 3 paragraphs"""
        try:
            title = book_data.get('title', 'This Book')
            author = book_data.get('author', 'AI Lab for Book-Lovers')
            stream = book_data.get('stream', 'General Knowledge')
            description = book_data.get('description', '')
            quotes_count = len(book_data.get('quotes', []))
            
            # Reset pilsa explanation flag for each generation
            self.pilsa_explanation_included = False
            
            # Generate three structured paragraphs
            paragraph_1 = self._generate_introduction_paragraph(
                title, author, stream, description
            )
            
            paragraph_2 = self._generate_content_paragraph(
                title, quotes_count, content_context
            )
            
            paragraph_3 = self._generate_motivation_paragraph(
                title, stream
            )
            
            # Validate paragraph lengths
            paragraph_1 = self._ensure_paragraph_length(paragraph_1, 1)
            paragraph_2 = self._ensure_paragraph_length(paragraph_2, 2)
            paragraph_3 = self._ensure_paragraph_length(paragraph_3, 3)
            
            # Combine paragraphs
            publishers_note = f"{paragraph_1}\n\n{paragraph_2}\n\n{paragraph_3}"
            
            # Validate final structure
            if not self._validate_publishers_note(publishers_note):
                logger.warning("Generated Publisher's Note failed validation, using fallback")
                return self._generate_fallback_publishers_note(book_data)
            
            logger.info(f"Generated Publisher's Note with {len(publishers_note)} characters")
            return publishers_note
            
        except Exception as e:
            logger.error(f"Error generating Publisher's Note: {e}")
            return self._generate_fallback_publishers_note(book_data)
    
    def _generate_introduction_paragraph(self, title: str, author: str, 
                                       stream: str, description: str) -> str:
        """Generate introduction paragraph with pilsa book explanation"""
        try:
            # Include pilsa explanation in first paragraph
            pilsa_explanation = "This pilsa book presents"
            self.pilsa_explanation_included = True
            
            # Create introduction focusing on the book's purpose
            intro_parts = [
                f"{pilsa_explanation} \"{title}\" as an essential exploration of {stream.lower()}.",
                f"Developed by {author}, this work synthesizes key insights and perspectives",
                f"to provide readers with a comprehensive understanding of {description[:100]}..." if len(description) > 100 else f"that illuminate {description}.",
                "The carefully curated content serves both as an educational resource and a catalyst for deeper reflection."
            ]
            
            paragraph = " ".join(intro_parts)
            return self._add_current_events_reference(paragraph)
            
        except Exception as e:
            logger.error(f"Error generating introduction paragraph: {e}")
            return f"This pilsa book, \"{title}\", offers valuable insights into {stream}."
    
    def _generate_content_paragraph(self, title: str, quotes_count: int, 
                                  content_context: Optional[str]) -> str:
        """Generate content-focused paragraph"""
        try:
            content_parts = []
            
            # Describe the content structure
            if quotes_count > 0:
                content_parts.append(f"The book features {quotes_count} carefully selected quotations")
                content_parts.append("that represent diverse perspectives and timeless wisdom.")
            else:
                content_parts.append("The book presents thoughtfully organized content")
                content_parts.append("that draws from authoritative sources and expert analysis.")
            
            # Add context-specific information
            if content_context:
                context_snippet = content_context[:150] + "..." if len(content_context) > 150 else content_context
                content_parts.append(f"The material explores {context_snippet}")
            
            # Emphasize practical value
            content_parts.append("Each section is designed to engage readers intellectually")
            content_parts.append("while providing practical insights for contemporary application.")
            
            paragraph = " ".join(content_parts)
            return self._add_current_events_reference(paragraph)
            
        except Exception as e:
            logger.error(f"Error generating content paragraph: {e}")
            return f"This comprehensive work presents valuable content for understanding {title}."
    
    def _generate_motivation_paragraph(self, title: str, stream: str) -> str:
        """Generate motivation paragraph for publishers and readers"""
        try:
            motivation_parts = []
            
            # Publisher motivation
            motivation_parts.append("For publishers, this work represents an opportunity")
            motivation_parts.append("to offer readers meaningful content that bridges")
            motivation_parts.append("academic rigor with accessible presentation.")
            
            # Reader motivation
            motivation_parts.append("For readers, the book serves as both")
            motivation_parts.append("an educational journey and a practical guide")
            motivation_parts.append(f"for navigating the complexities of {stream.lower()}.")
            
            # Call to action
            motivation_parts.append("Whether used for personal enrichment, academic study,")
            motivation_parts.append("or professional development, this pilsa book")
            motivation_parts.append("delivers lasting value and intellectual satisfaction.")
            
            paragraph = " ".join(motivation_parts)
            return self._add_current_events_reference(paragraph)
            
        except Exception as e:
            logger.error(f"Error generating motivation paragraph: {e}")
            return f"This pilsa book offers valuable insights for both publishers and readers interested in {stream}."
    
    def _add_current_events_reference(self, paragraph: str) -> str:
        """Add current events references without date-specific content"""
        try:
            # Check if paragraph already has current events references
            has_current_ref = any(keyword in paragraph.lower() for keyword in self.current_events_keywords)
            
            if not has_current_ref:
                # Add subtle current events reference
                current_phrases = [
                    "in today's evolving landscape",
                    "within contemporary contexts",
                    "addressing modern challenges",
                    "relevant to current discourse",
                    "reflecting contemporary understanding"
                ]
                
                # Insert a current events phrase naturally
                import random
                phrase = random.choice(current_phrases)
                
                # Find a good insertion point (after a comma or period)
                sentences = paragraph.split('. ')
                if len(sentences) > 1:
                    # Insert in the middle sentence
                    middle_idx = len(sentences) // 2
                    sentences[middle_idx] = f"{sentences[middle_idx]}, {phrase},"
                    paragraph = '. '.join(sentences)
            
            return paragraph
            
        except Exception as e:
            logger.error(f"Error adding current events reference: {e}")
            return paragraph
    
    def _ensure_paragraph_length(self, paragraph: str, paragraph_num: int) -> str:
        """Ensure paragraph meets length requirements (max 600 characters)"""
        try:
            if len(paragraph) <= self.max_chars_per_paragraph:
                return paragraph
            
            # Truncate at sentence boundary if possible
            sentences = paragraph.split('. ')
            truncated = ""
            
            for sentence in sentences:
                test_length = len(truncated + sentence + '. ')
                if test_length <= self.max_chars_per_paragraph:
                    truncated += sentence + '. '
                else:
                    break
            
            # Remove trailing '. ' and add proper ending
            truncated = truncated.rstrip('. ') + '.'
            
            if len(truncated) < 50:  # Too short after truncation
                # Use first part of original paragraph
                truncated = paragraph[:self.max_chars_per_paragraph - 3] + '...'
            
            logger.info(f"Truncated paragraph {paragraph_num} from {len(paragraph)} to {len(truncated)} characters")
            return truncated
            
        except Exception as e:
            logger.error(f"Error ensuring paragraph length: {e}")
            return paragraph[:self.max_chars_per_paragraph]
    
    def _validate_publishers_note(self, publishers_note: str) -> bool:
        """Validate Publisher's Note structure and content"""
        try:
            # Check paragraph count
            paragraphs = [p.strip() for p in publishers_note.split('\n\n') if p.strip()]
            if len(paragraphs) != self.max_paragraphs:
                logger.warning(f"Invalid paragraph count: {len(paragraphs)} (expected {self.max_paragraphs})")
                return False
            
            # Check paragraph lengths
            for i, paragraph in enumerate(paragraphs, 1):
                if len(paragraph) > self.max_chars_per_paragraph:
                    logger.warning(f"Paragraph {i} too long: {len(paragraph)} characters")
                    return False
                if len(paragraph) < 50:  # Minimum reasonable length
                    logger.warning(f"Paragraph {i} too short: {len(paragraph)} characters")
                    return False
            
            # Check for pilsa explanation
            if not self.pilsa_explanation_included or 'pilsa' not in publishers_note.lower():
                logger.warning("Missing pilsa book explanation")
                return False
            
            # Check for current events reference
            has_current_ref = any(keyword in publishers_note.lower() for keyword in self.current_events_keywords)
            if not has_current_ref:
                logger.warning("Missing current events reference")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating Publisher's Note: {e}")
            return False
    
    def _generate_fallback_publishers_note(self, book_data: Dict[str, Any]) -> str:
        """Generate fallback Publisher's Note if main generation fails"""
        try:
            title = book_data.get('title', 'This Book')
            stream = book_data.get('stream', 'knowledge')
            
            paragraph_1 = f"This pilsa book, \"{title}\", presents essential insights into {stream}. " \
                         f"The work synthesizes key perspectives to provide readers with comprehensive understanding. " \
                         f"Contemporary challenges require thoughtful exploration of these important topics."
            
            paragraph_2 = f"The carefully curated content serves both educational and practical purposes. " \
                         f"Each section engages readers intellectually while offering relevant applications. " \
                         f"Modern contexts demand accessible yet rigorous treatment of complex subjects."
            
            paragraph_3 = f"For publishers, this work offers meaningful content that bridges academic depth with readability. " \
                         f"For readers, the book provides both learning opportunities and practical guidance. " \
                         f"This pilsa book delivers lasting value in today's evolving landscape."
            
            # Ensure each paragraph meets length requirements
            paragraph_1 = self._ensure_paragraph_length(paragraph_1, 1)
            paragraph_2 = self._ensure_paragraph_length(paragraph_2, 2)
            paragraph_3 = self._ensure_paragraph_length(paragraph_3, 3)
            
            return f"{paragraph_1}\n\n{paragraph_2}\n\n{paragraph_3}"
            
        except Exception as e:
            logger.error(f"Error generating fallback Publisher's Note: {e}")
            return "This pilsa book offers valuable insights for contemporary readers and publishers."
    
    def analyze_publishers_note(self, publishers_note: str) -> Dict[str, Any]:
        """Analyze Publisher's Note structure and content"""
        try:
            paragraphs = [p.strip() for p in publishers_note.split('\n\n') if p.strip()]
            
            analysis = {
                'paragraph_count': len(paragraphs),
                'total_characters': len(publishers_note),
                'paragraph_lengths': [len(p) for p in paragraphs],
                'has_pilsa_explanation': 'pilsa' in publishers_note.lower(),
                'has_current_events': any(keyword in publishers_note.lower() for keyword in self.current_events_keywords),
                'validation_passed': self._validate_publishers_note(publishers_note)
            }
            
            # Check length compliance
            analysis['length_compliant'] = all(
                length <= self.max_chars_per_paragraph for length in analysis['paragraph_lengths']
            )
            
            # Identify current events keywords found
            found_keywords = [
                keyword for keyword in self.current_events_keywords 
                if keyword in publishers_note.lower()
            ]
            analysis['current_events_keywords'] = found_keywords
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing Publisher's Note: {e}")
            return {'error': str(e)}
    
    def get_generation_summary(self) -> Dict[str, Any]:
        """Get summary of generation configuration"""
        return {
            'max_paragraphs': self.max_paragraphs,
            'max_chars_per_paragraph': self.max_chars_per_paragraph,
            'current_events_keywords': self.current_events_keywords,
            'pilsa_explanation_required': True,
            'structure': 'introduction -> content -> motivation'
        }