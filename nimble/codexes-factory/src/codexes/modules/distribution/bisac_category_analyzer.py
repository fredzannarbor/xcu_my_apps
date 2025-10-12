"""
BISAC category analyzer for generating specific, relevant categories.
"""

from typing import Dict, List, Any, Optional
import logging
import re
from src.codexes.core.enhanced_llm_caller import EnhancedLLMCaller

logger = logging.getLogger(__name__)


class BISACCategoryAnalyzer:
    """Analyze book content to generate specific, relevant BISAC categories"""
    
    def __init__(self, llm_caller: Optional[EnhancedLLMCaller] = None):
        self.llm_caller = llm_caller or EnhancedLLMCaller()
        self.generic_categories = ['Business>General', 'Self-Help>General', 'Reference>General']
    
    def analyze_content_for_categories(self, book_content: str) -> List[str]:
        """Analyze book content to determine specific BISAC categories"""
        try:
            # Extract key themes and topics
            content_analysis = self._analyze_content_themes(book_content)
            
            # Generate specific categories based on analysis
            categories = self.get_technical_categories(content_analysis)
            
            # Validate and refine categories
            validated_categories = self.validate_category_specificity(categories)
            
            return validated_categories[:3]  # Return top 3 categories
            
        except Exception as e:
            logger.error(f"Error analyzing content for BISAC categories: {e}")
            return self._get_fallback_categories()
    
    def _analyze_content_themes(self, content: str) -> Dict[str, Any]:
        """Analyze content to identify main themes and topics"""
        try:
            # Extract key terms and concepts
            themes = {
                'technology_terms': [],
                'science_terms': [],
                'business_terms': [],
                'psychology_terms': [],
                'space_terms': [],
                'sustainability_terms': []
            }
            
            # Define keyword patterns for different domains
            patterns = {
                'technology_terms': r'\b(?:AI|artificial intelligence|technology|digital|software|algorithm|data|computer|innovation)\b',
                'science_terms': r'\b(?:research|experiment|hypothesis|theory|scientific|analysis|discovery|physics|chemistry|biology)\b',
                'business_terms': r'\b(?:management|leadership|strategy|organization|corporate|enterprise|profit|market|economy)\b',
                'psychology_terms': r'\b(?:psychology|behavior|cognitive|mental|emotional|therapy|mindfulness|meditation|consciousness)\b',
                'space_terms': r'\b(?:space|Mars|planet|exploration|astronaut|rocket|satellite|universe|solar|cosmic)\b',
                'sustainability_terms': r'\b(?:sustainable|environment|climate|renewable|green|ecology|conservation|carbon)\b'
            }
            
            content_lower = content.lower()
            
            for theme, pattern in patterns.items():
                matches = re.findall(pattern, content_lower, re.IGNORECASE)
                themes[theme] = list(set(matches))  # Remove duplicates
            
            # Calculate theme scores
            theme_scores = {theme: len(terms) for theme, terms in themes.items()}
            
            return {
                'themes': themes,
                'theme_scores': theme_scores,
                'dominant_theme': max(theme_scores, key=theme_scores.get),
                'content_length': len(content),
                'technical_density': sum(theme_scores.values()) / len(content) * 1000
            }
            
        except Exception as e:
            logger.error(f"Error analyzing content themes: {e}")
            return {'themes': {}, 'theme_scores': {}, 'dominant_theme': 'general'}
    
    def get_technical_categories(self, content_analysis: Dict[str, Any]) -> List[str]:
        """Generate technical BISAC categories based on content analysis"""
        try:
            dominant_theme = content_analysis.get('dominant_theme', 'general')
            theme_scores = content_analysis.get('theme_scores', {})
            
            categories = []
            
            # Map themes to specific BISAC categories
            theme_category_map = {
                'technology_terms': [
                    'COMPUTERS / Artificial Intelligence / General',
                    'TECHNOLOGY & ENGINEERING / Engineering (General)',
                    'SCIENCE / Technology'
                ],
                'science_terms': [
                    'SCIENCE / General',
                    'SCIENCE / Research & Methodology',
                    'SCIENCE / Physics / General'
                ],
                'space_terms': [
                    'SCIENCE / Space Science / Astronomy',
                    'SCIENCE / Space Science / Cosmology',
                    'TECHNOLOGY & ENGINEERING / Aeronautics & Astronautics'
                ],
                'business_terms': [
                    'BUSINESS & ECONOMICS / Management',
                    'BUSINESS & ECONOMICS / Leadership',
                    'BUSINESS & ECONOMICS / Strategic Planning'
                ],
                'psychology_terms': [
                    'PSYCHOLOGY / Cognitive Psychology',
                    'SELF-HELP / Personal Growth / Success',
                    'PHILOSOPHY / Mind & Body'
                ],
                'sustainability_terms': [
                    'SCIENCE / Environmental Science',
                    'NATURE / Environmental Conservation & Protection',
                    'POLITICAL SCIENCE / Public Policy / Environmental Policy'
                ]
            }
            
            # Get categories for dominant theme
            if dominant_theme in theme_category_map:
                categories.extend(theme_category_map[dominant_theme])
            
            # Add categories for other significant themes
            for theme, score in sorted(theme_scores.items(), key=lambda x: x[1], reverse=True):
                if theme != dominant_theme and score > 5 and theme in theme_category_map:
                    categories.extend(theme_category_map[theme][:1])  # Add top category
            
            return categories[:5]  # Return top 5 categories
            
        except Exception as e:
            logger.error(f"Error generating technical categories: {e}")
            return self._get_fallback_categories()
    
    def validate_category_specificity(self, categories: List[str]) -> List[str]:
        """Replace generic categories with more specific ones based on content"""
        try:
            validated_categories = []
            
            for category in categories:
                # Check if category is too generic
                if any(generic in category for generic in self.generic_categories):
                    logger.warning(f"Replacing generic category: {category}")
                    continue
                
                # Validate category format
                if '>' in category or '/' in category:
                    validated_categories.append(category)
                else:
                    logger.warning(f"Invalid category format: {category}")
            
            # If no valid categories, use fallback
            if not validated_categories:
                validated_categories = self._get_fallback_categories()
            
            return validated_categories
            
        except Exception as e:
            logger.error(f"Error validating category specificity: {e}")
            return categories
    
    def ensure_category_relevance(self, categories: List[str], book_metadata: Dict[str, Any]) -> List[str]:
        """Ensure all categories are relevant to the book's actual content"""
        try:
            title = book_metadata.get('title', '').lower()
            description = book_metadata.get('description', '').lower()
            
            relevant_categories = []
            
            for category in categories:
                category_lower = category.lower()
                
                # Check relevance based on title and description
                if any(keyword in title or keyword in description 
                       for keyword in self._extract_category_keywords(category_lower)):
                    relevant_categories.append(category)
                else:
                    logger.info(f"Category may not be relevant: {category}")
            
            # Ensure we have at least one category
            if not relevant_categories and categories:
                relevant_categories = categories[:1]
            
            return relevant_categories
            
        except Exception as e:
            logger.error(f"Error ensuring category relevance: {e}")
            return categories
    
    def _extract_category_keywords(self, category: str) -> List[str]:
        """Extract keywords from BISAC category for relevance checking"""
        try:
            # Extract meaningful words from category
            words = re.findall(r'\b[a-z]+\b', category)
            
            # Filter out common words
            common_words = {'general', 'the', 'and', 'or', 'of', 'in', 'for', 'with'}
            keywords = [word for word in words if word not in common_words and len(word) > 3]
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting category keywords: {e}")
            return []
    
    def _get_fallback_categories(self) -> List[str]:
        """Get fallback categories when analysis fails"""
        return [
            'SELF-HELP / Personal Growth / Success',
            'PHILOSOPHY / Mind & Body',
            'REFERENCE / Personal & Practical Guides'
        ]
    
    def generate_categories_with_llm(self, book_content: str, book_metadata: Dict[str, Any]) -> List[str]:
        """Use LLM to generate specific BISAC categories"""
        try:
            title = book_metadata.get('title', 'Unknown Title')
            description = book_metadata.get('description', '')
            
            prompt = f"""
Analyze this book and suggest 3 specific BISAC categories. Avoid generic categories like "Business>General" or "Self-Help>General".

Title: {title}
Description: {description}
Content sample: {book_content[:1000]}...

Based on the specific content and themes, suggest precise BISAC categories in this format:
CATEGORY / SUBCATEGORY / SPECIFIC AREA

Examples of good specific categories:
- SCIENCE / Space Science / Astronomy
- TECHNOLOGY & ENGINEERING / Aeronautics & Astronautics  
- PSYCHOLOGY / Cognitive Psychology
- BUSINESS & ECONOMICS / Strategic Planning

Return JSON with key "categories" containing a list of 3 specific categories.
"""
            
            response = self.llm_caller.call_llm_json_with_retry(
                prompt=prompt,
                expected_keys=['categories'],
                model_name="gemini/gemini-2.5-flash"
            )
            
            if response and 'categories' in response:
                return response['categories'][:3]
            else:
                return self._get_fallback_categories()
                
        except Exception as e:
            logger.error(f"Error generating categories with LLM: {e}")
            return self._get_fallback_categories()