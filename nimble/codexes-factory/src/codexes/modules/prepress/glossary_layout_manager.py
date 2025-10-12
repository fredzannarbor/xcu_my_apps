"""
Single-column glossary layout manager with Korean/English term stacking.
"""

from typing import Dict, List, Any, Tuple, Optional
import logging
import math

logger = logging.getLogger(__name__)


class GlossaryLayoutManager:
    """Single-column glossary layout with Korean/English term stacking"""
    
    def __init__(self, page_config: Dict[str, Any]):
        self.column_count = 1
        self.page_text_area = page_config.get('text_area', {})
        self.term_spacing = page_config.get('term_spacing', '0.5em')

    
    def format_glossary_single_column(self, terms: List[Dict[str, Any]]) -> str:
        """Format glossary in single column layout"""
        try:
            if not terms:
                return ""
            
            # Generate LaTeX for single-column layout
            latex_output = []
            
            # Start glossary section
            latex_output.append("\\chapter*{Glossary}")
            latex_output.append("\\addcontentsline{toc}{chapter}{Glossary}")
            latex_output.append("")
            
            # Format all terms in single column
            for term in terms:
                formatted_term = self.stack_korean_english_terms(
                    term.get('korean', ''),
                    term.get('english', ''),
                    term.get('definition', '')
                )
                latex_output.append(formatted_term)
            
            return "\n".join(latex_output)
            
        except Exception as e:
            logger.error(f"Error formatting single-column glossary: {e}")
            return "\\textbf{Error formatting glossary}"
    
    def stack_korean_english_terms(self, korean_term: str, english_term: str, definition: str = "") -> str:
        """Format Korean and English terms on same line with definition underneath"""
        try:
            formatted_entry = []
            
            # Create term entry with Korean and English on same line separated by space
            if korean_term or english_term:
                term_line = []
                
                # Korean term (bold)
                if korean_term:
                    term_line.append(f"\\textbf{{\\korean{{{korean_term}}}}}")
                
                # English term (italic, same line with space)
                if english_term:
                    term_line.append(f"\\textit{{{english_term}}}")
                
                # Combine Korean and English with space
                if term_line:
                    formatted_entry.append(" ".join(term_line))
                
                # Definition on next line with normal single leading
                if definition:
                    formatted_entry.append(f"{definition}")
                
                # Reduce space between entries by 12pts
                formatted_entry.append("\\vspace{12pt}")
            
            return "\n".join(formatted_entry) + "\n"
            
        except Exception as e:
            logger.error(f"Error formatting Korean/English terms: {e}")
            return f"\\textbf{{Error formatting term: {korean_term} / {english_term}}}"
    

    
    def validate_glossary_layout(self, latex_output: str) -> Dict[str, Any]:
        """Validate that glossary layout meets requirements"""
        try:
            validation_results = {
                'valid': True,
                'warnings': [],
                'errors': []
            }
            
            # Check for single-column format (no multicols)
            if '\\begin{multicols}' in latex_output:
                validation_results['errors'].append("Glossary should not use multicols for single-column layout")
                validation_results['valid'] = False
            
            # Check for Korean/English stacking
            if '\\\\' not in latex_output:
                validation_results['warnings'].append("No term stacking detected")
            
            # Check for proper spacing
            if f'\\vspace{{{self.term_spacing}}}' not in latex_output:
                validation_results['warnings'].append("Term spacing may not be applied")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating glossary layout: {e}")
            return {
                'valid': False,
                'warnings': [],
                'errors': [f'Validation failed: {e}']
            }
    
    def extract_glossary_terms(self, content: str) -> List[Dict[str, Any]]:
        """Extract glossary terms from book content"""
        try:
            import re
            
            terms = []
            
            # Look for glossary patterns in content
            patterns = [
                # Korean - English pattern
                r'([가-힣]+)\s*[-–—]\s*([A-Za-z\s]+)(?:\s*:\s*([^.\n]+))?',
                # English - Korean pattern  
                r'([A-Za-z\s]+)\s*[-–—]\s*([가-힣]+)(?:\s*:\s*([^.\n]+))?',
                # Definition list pattern
                r'\\item\[([^\]]+)\]\s*([^\\]+)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                for match in matches:
                    if len(match) >= 2:
                        # Determine which is Korean and which is English
                        term1, term2 = match[0].strip(), match[1].strip()
                        definition = match[2].strip() if len(match) > 2 else ""
                        
                        # Check if first term contains Korean characters
                        if re.search(r'[가-힣]', term1):
                            korean_term = term1
                            english_term = term2
                        else:
                            korean_term = term2 if re.search(r'[가-힣]', term2) else ""
                            english_term = term1
                        
                        terms.append({
                            'korean': korean_term,
                            'english': english_term,
                            'definition': definition
                        })
            
            # Remove duplicates
            unique_terms = []
            seen = set()
            for term in terms:
                key = (term['korean'], term['english'])
                if key not in seen:
                    unique_terms.append(term)
                    seen.add(key)
            
            logger.info(f"Extracted {len(unique_terms)} unique glossary terms")
            return unique_terms
            
        except Exception as e:
            logger.error(f"Error extracting glossary terms: {e}")
            return []
    
    def sort_glossary_terms(self, terms: List[Dict[str, Any]], sort_by: str = 'english') -> List[Dict[str, Any]]:
        """Sort glossary terms alphabetically"""
        try:
            if sort_by == 'korean':
                # Sort by Korean term
                return sorted(terms, key=lambda x: x.get('korean', ''))
            else:
                # Sort by English term (default)
                return sorted(terms, key=lambda x: x.get('english', '').lower())
                
        except Exception as e:
            logger.error(f"Error sorting glossary terms: {e}")
            return terms
    
    def generate_glossary_from_content(self, content: str, sort_by: str = 'english') -> str:
        """Generate complete glossary from book content"""
        try:
            # Extract terms from content
            terms = self.extract_glossary_terms(content)
            
            if not terms:
                logger.warning("No glossary terms found in content")
                return ""
            
            # Sort terms
            sorted_terms = self.sort_glossary_terms(terms, sort_by)
            
            # Format as single-column glossary
            return self.format_glossary_single_column(sorted_terms)
            
        except Exception as e:
            logger.error(f"Error generating glossary from content: {e}")
            return "\\textbf{Error generating glossary}"
    
    def get_layout_statistics(self, terms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about glossary layout"""
        try:
            return {
                'total_terms': len(terms),
                'korean_terms': len([t for t in terms if t.get('korean')]),
                'english_terms': len([t for t in terms if t.get('english')]),
                'terms_with_definitions': len([t for t in terms if t.get('definition')])
            }
            
        except Exception as e:
            logger.error(f"Error getting layout statistics: {e}")
            return {}