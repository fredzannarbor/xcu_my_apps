"""
Bibliography formatting system with memoir citation fields and hanging indent.
"""

from typing import Dict, List, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)


class BibliographyFormatter:
    """Enhanced bibliography formatting with memoir citation fields"""
    
    def __init__(self, memoir_config: Dict[str, Any]):
        self.hanging_indent = "0.15in"
        self.citation_style = memoir_config.get('citation_style', 'chicago')
        self.memoir_config = memoir_config
        
    def format_bibliography_entry(self, entry: Dict[str, str]) -> str:
        """Format a single bibliography entry with hanging indent"""
        try:
            # Extract entry components
            author = entry.get('author', 'Unknown Author')
            title = entry.get('title', 'Unknown Title')
            publisher = entry.get('publisher', '')
            year = entry.get('year', '')
            isbn = entry.get('isbn', '')
            
            # Format according to Chicago style
            formatted_entry = f"{author}. "
            
            # Add title in italics
            if title:
                formatted_entry += f"\\textit{{{title}}}. "
            
            # Add publisher and year
            if publisher and year:
                formatted_entry += f"{publisher}, {year}."
            elif publisher:
                formatted_entry += f"{publisher}."
            elif year:
                formatted_entry += f"{year}."
                
            # Add ISBN if available
            if isbn:
                formatted_entry += f" ISBN: {isbn}."
                
            return formatted_entry.strip()
            
        except Exception as e:
            logger.error(f"Error formatting bibliography entry: {e}")
            return f"Error formatting entry: {entry}"
    
    def apply_memoir_citation_field(self, entries: List[Dict]) -> str:
        """Apply memoir citation field formatting to bibliography"""
        try:
            formatted_entries = []
            
            for entry in entries:
                formatted_entry = self.format_bibliography_entry(entry)
                formatted_entries.append(formatted_entry)
            
            # Create memoir bibliography environment with hanging indent
            bibliography_latex = "\\begin{thebibliography}{99}\n"
            bibliography_latex += f"\\setlength{{\\itemindent}}{{-{self.hanging_indent}}}\n"
            bibliography_latex += f"\\setlength{{\\leftmargin}}{{{self.hanging_indent}}}\n"
            bibliography_latex += "\\setlength{\\itemsep}{0.5em}\n"
            
            for i, entry in enumerate(formatted_entries, 1):
                bibliography_latex += f"\\bibitem{{{i}}} {entry}\n\n"
            
            bibliography_latex += "\\end{thebibliography}\n"
            
            return bibliography_latex
            
        except Exception as e:
            logger.error(f"Error applying memoir citation field: {e}")
            return "\\textbf{Error generating bibliography}"
    
    def generate_latex_bibliography(self, entries: List[Dict]) -> str:
        """Generate LaTeX code for properly formatted bibliography"""
        try:
            if not entries:
                return ""
            
            # Use memoir citation field formatting
            return self.apply_memoir_citation_field(entries)
            
        except Exception as e:
            logger.error(f"Error generating LaTeX bibliography: {e}")
            return "\\textbf{Bibliography generation failed}"
    
    def validate_bibliography_format(self, latex_output: str) -> bool:
        """Validate that bibliography follows proper formatting"""
        try:
            # Check for required elements
            has_environment = "\\begin{thebibliography}" in latex_output
            has_hanging_indent = self.hanging_indent in latex_output
            has_bibitem = "\\bibitem" in latex_output
            
            return has_environment and has_hanging_indent and has_bibitem
            
        except Exception as e:
            logger.error(f"Error validating bibliography format: {e}")
            return False
    
    def extract_bibliography_from_content(self, content: str) -> List[Dict[str, str]]:
        """Extract bibliography entries from book content"""
        try:
            entries = []
            
            # Look for common bibliography patterns
            patterns = [
                r'(?:References?|Bibliography|Works Cited):\s*(.*?)(?=\n\n|\Z)',
                r'\\bibliography\{([^}]+)\}',
                r'\\bibitem\{[^}]+\}\s*([^\n]+)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    # Parse individual entries (simplified)
                    entry_lines = match.strip().split('\n')
                    for line in entry_lines:
                        if line.strip():
                            # Basic parsing - can be enhanced
                            entry = self._parse_bibliography_line(line.strip())
                            if entry:
                                entries.append(entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"Error extracting bibliography: {e}")
            return []
    
    def _parse_bibliography_line(self, line: str) -> Optional[Dict[str, str]]:
        """Parse a single bibliography line into components"""
        try:
            # Simple parsing - can be enhanced with more sophisticated logic
            parts = line.split('.')
            if len(parts) >= 2:
                author = parts[0].strip()
                title = parts[1].strip() if len(parts) > 1 else ""
                
                # Look for year pattern
                year_match = re.search(r'\b(19|20)\d{2}\b', line)
                year = year_match.group() if year_match else ""
                
                # Look for publisher (simplified)
                publisher = ""
                if len(parts) > 2:
                    publisher = parts[2].strip()
                
                return {
                    'author': author,
                    'title': title,
                    'publisher': publisher,
                    'year': year,
                    'isbn': ''  # Would need more sophisticated parsing
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing bibliography line: {e}")
            return None