"""
Mnemonics JSON processor with proper structure validation.
"""

from typing import Dict, List, Any, Optional
import logging
import json
from src.codexes.core.enhanced_llm_caller import EnhancedLLMCaller

logger = logging.getLogger(__name__)


class MnemonicsJSONProcessor:
    """Process mnemonics generation with proper JSON structure validation"""
    
    def __init__(self, llm_caller: Optional[EnhancedLLMCaller] = None):
        self.llm_caller = llm_caller or EnhancedLLMCaller()
        self.required_keys = ['mnemonics_data']
    
    def generate_mnemonics_with_validation(self, book_content: str) -> Dict[str, Any]:
        """Generate mnemonics ensuring proper JSON structure with required keys"""
        try:
            prompt = self._create_mnemonics_prompt(book_content)
            
            response = self.llm_caller.call_llm_json_with_retry(
                prompt=prompt,
                expected_keys=self.required_keys,
                model_name="gemini/gemini-2.5-flash"
            )
            
            if self.validate_mnemonics_response(response):
                return response
            else:
                return self.handle_missing_keys_error(response)
                
        except Exception as e:
            logger.error(f"Error generating mnemonics: {e}")
            return self._create_fallback_response()
    
    def _create_mnemonics_prompt(self, book_content: str) -> str:
        """Create prompt for mnemonics generation with required JSON structure"""
        return f"""
Based on the following book content, generate mnemonics that help readers remember key concepts.

Book content: {book_content[:2000]}...

Create mnemonics with the following structure:
- Each mnemonic should have an acronym, expansion, and explanation
- Focus on the main themes and concepts from the book
- Make them memorable and relevant

IMPORTANT: Return JSON with this exact structure:
{{
    "mnemonics_data": [
        {{
            "acronym": "EXAMPLE",
            "expansion": "Each X-factor Amplifies Meaningful Personal Learning Experiences",
            "explanation": "This mnemonic helps remember the key principles..."
        }}
    ]
}}

The response MUST include the "mnemonics_data" key with a list of mnemonic objects.
"""
    
    def validate_mnemonics_response(self, response: Dict[str, Any]) -> bool:
        """Validate that response contains expected mnemonics_data key"""
        try:
            if not isinstance(response, dict):
                logger.warning("Response is not a dictionary")
                return False
            
            if 'mnemonics_data' not in response:
                logger.warning("Missing 'mnemonics_data' key in response")
                return False
            
            mnemonics_data = response['mnemonics_data']
            if not isinstance(mnemonics_data, list):
                logger.warning("'mnemonics_data' is not a list")
                return False
            
            # Validate each mnemonic entry
            for i, mnemonic in enumerate(mnemonics_data):
                if not isinstance(mnemonic, dict):
                    logger.warning(f"Mnemonic {i} is not a dictionary")
                    return False
                
                required_mnemonic_keys = ['acronym', 'expansion', 'explanation']
                for key in required_mnemonic_keys:
                    if key not in mnemonic:
                        logger.warning(f"Mnemonic {i} missing key: {key}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating mnemonics response: {e}")
            return False
    
    def handle_missing_keys_error(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Handle responses missing expected keys with fallback behavior"""
        try:
            logger.warning(f"Handling missing keys in response: {response}")
            
            # Try to extract mnemonic data from alternative structures
            if isinstance(response, dict):
                # Check for alternative key names
                alternative_keys = ['mnemonics', 'mnemonic_list', 'data', 'results']
                for key in alternative_keys:
                    if key in response and isinstance(response[key], list):
                        logger.info(f"Found mnemonics data under alternative key: {key}")
                        return {'mnemonics_data': response[key]}
                
                # Check if response contains mnemonic-like data directly
                if 'acronym' in response and 'expansion' in response:
                    logger.info("Converting single mnemonic to list format")
                    return {'mnemonics_data': [response]}
            
            # If no recovery possible, create fallback
            logger.warning("Could not recover mnemonics data, using fallback")
            return self._create_fallback_response()
            
        except Exception as e:
            logger.error(f"Error handling missing keys: {e}")
            return self._create_fallback_response()
    
    def create_mnemonics_tex(self, mnemonics_data: Dict[str, Any]) -> str:
        """Create mnemonics.tex file from validated JSON data"""
        try:
            if not self.validate_mnemonics_response(mnemonics_data):
                logger.error("Invalid mnemonics data for TeX creation")
                return ""
            
            mnemonics_list = mnemonics_data['mnemonics_data']
            
            tex_content = []
            tex_content.append("% Mnemonics section")
            tex_content.append("\\chapter{Mnemonics}")
            tex_content.append("")
            
            for mnemonic in mnemonics_list:
                acronym = mnemonic.get('acronym', '')
                expansion = mnemonic.get('expansion', '')
                explanation = mnemonic.get('explanation', '')
                
                if acronym and expansion:
                    tex_content.append(f"\\section*{{{acronym}}}")
                    tex_content.append("")
                    
                    # Create itemized list for each letter
                    tex_content.append("\\begin{itemize}")
                    words = expansion.split()
                    for i, word in enumerate(words):
                        if i < len(acronym):
                            letter = acronym[i].upper()
                            tex_content.append(f"\\item \\textbf{{{letter}}} -- {word}")
                    tex_content.append("\\end{itemize}")
                    tex_content.append("")
                    
                    if explanation:
                        tex_content.append(explanation)
                        tex_content.append("")
                    
                    tex_content.append("\\vspace{1em}")
                    tex_content.append("")
            
            return "\n".join(tex_content)
            
        except Exception as e:
            logger.error(f"Error creating mnemonics TeX: {e}")
            return "% Error creating mnemonics content"
    
    def _create_fallback_response(self) -> Dict[str, Any]:
        """Create fallback mnemonics response"""
        return {
            'mnemonics_data': [
                {
                    'acronym': 'GROW',
                    'expansion': 'Goals Reflection Opportunities Wisdom',
                    'explanation': 'This mnemonic represents the journey of personal development through structured reflection and learning.'
                }
            ]
        }
    
    def extract_key_concepts(self, book_content: str) -> List[str]:
        """Extract key concepts from book content for mnemonic generation"""
        try:
            import re
            
            # Look for key terms and concepts
            concepts = []
            
            # Extract capitalized terms (likely important concepts)
            capitalized_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', book_content)
            concepts.extend(capitalized_terms[:10])  # Limit to top 10
            
            # Extract terms from headings
            headings = re.findall(r'\\(?:chapter|section|subsection)\{([^}]+)\}', book_content)
            concepts.extend(headings)
            
            # Remove duplicates and common words
            common_words = {'The', 'And', 'But', 'For', 'With', 'This', 'That', 'Chapter', 'Section'}
            unique_concepts = list(set(concepts) - common_words)
            
            return unique_concepts[:20]  # Return top 20 concepts
            
        except Exception as e:
            logger.error(f"Error extracting key concepts: {e}")
            return ['Growth', 'Learning', 'Development', 'Success', 'Achievement']