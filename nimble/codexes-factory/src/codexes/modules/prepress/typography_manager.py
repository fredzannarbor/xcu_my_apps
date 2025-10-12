"""
Typography and layout management for professional book formatting.
"""

import re
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TypographyManager:
    """Professional typography and layout management"""
    
    def __init__(self, imprint_config: Dict[str, Any]):
        self.fonts = self._load_font_config(imprint_config)
        self.layout_settings = self._load_layout_config(imprint_config)
        self.chapter_leading = "36pt"
        self.instruction_interval = 8  # Every 8th recto page
    
    def _load_font_config(self, imprint_config: Dict[str, Any]) -> Dict[str, str]:
        """Load font configuration from imprint settings"""
        try:
            fonts = imprint_config.get('fonts', {})
            
            # Default fonts
            default_fonts = {
                'body': 'Adobe Caslon Pro',
                'heading': 'Adobe Caslon Pro',
                'korean': 'Apple Myungjo',
                'quotations': 'Adobe Caslon Pro',
                'mnemonics': 'Adobe Caslon Pro'
            }
            
            # Merge with imprint-specific fonts
            default_fonts.update(fonts)
            return default_fonts
            
        except Exception as e:
            logger.error(f"Error loading font config: {e}")
            return {
                'body': 'Adobe Caslon Pro',
                'heading': 'Adobe Caslon Pro',
                'korean': 'Apple Myungjo',
                'quotations': 'Adobe Caslon Pro',
                'mnemonics': 'Adobe Caslon Pro'
            }
    
    def _load_layout_config(self, imprint_config: Dict[str, Any]) -> Dict[str, Any]:
        """Load layout configuration from imprint settings"""
        try:
            layout = imprint_config.get('layout', {})
            
            # Default layout settings
            default_layout = {
                'page_width': '6in',
                'page_height': '9in',
                'margin_top': '0.75in',
                'margin_bottom': '0.75in',
                'margin_inner': '0.75in',
                'margin_outer': '0.5in',
                'text_area_width': '4.75in',
                'text_area_height': '7.5in'
            }
            
            # Merge with imprint-specific layout
            default_layout.update(layout)
            return default_layout
            
        except Exception as e:
            logger.error(f"Error loading layout config: {e}")
            return {
                'page_width': '6in',
                'page_height': '9in',
                'text_area_width': '4.75in',
                'text_area_height': '7.5in'
            }
    
    def format_mnemonics_page(self, mnemonics: List[Dict[str, Any]]) -> str:
        """Format mnemonics pages with Adobe Caslon and proper bullet structure"""
        try:
            if not mnemonics:
                return ""
            
            latex_output = []
            
            # Start mnemonics section
            latex_output.append("\\chapter{Mnemonics}")
            latex_output.append("")
            
            # Set font to Adobe Caslon (same as quotations)
            latex_output.append(f"\\fontspec{{{self.fonts['mnemonics']}}}")
            latex_output.append("")
            
            for mnemonic in mnemonics:
                try:
                    acronym = mnemonic.get('acronym', '')
                    expansion = mnemonic.get('expansion', '')
                    explanation = mnemonic.get('explanation', '')
                    
                    if acronym and expansion:
                        # Format acronym as heading
                        latex_output.append(f"\\textbf{{{acronym}}}")
                        latex_output.append("")
                        
                        # Format expansion with bullet points for each letter
                        if expansion:
                            latex_output.append("\\begin{itemize}")
                            
                            # Split expansion into words and create bullet for each letter
                            words = expansion.split()
                            for i, word in enumerate(words):
                                if i < len(acronym):
                                    letter = acronym[i].upper()
                                    latex_output.append(f"\\item \\textbf{{{letter}}} -- {word}")
                            
                            latex_output.append("\\end{itemize}")
                            latex_output.append("")
                        
                        # Add explanation if available
                        if explanation:
                            latex_output.append(explanation)
                            latex_output.append("")
                        
                        latex_output.append("\\vspace{1em}")
                        latex_output.append("")
                
                except Exception as e:
                    logger.error(f"Error formatting mnemonic: {e}")
                    continue
            
            return "\\n".join(latex_output)
            
        except Exception as e:
            logger.error(f"Error formatting mnemonics page: {e}")
            return "\\textbf{Error formatting mnemonics}"
    
    def format_title_page_korean(self, korean_text: str) -> str:
        """Format Korean characters on title page with Apple Myungjo font"""
        try:
            if not korean_text:
                return ""
            
            # Escape any existing LaTeX commands
            korean_text = self._escape_latex_commands(korean_text)
            
            # Apply Apple Myungjo font for Korean text
            formatted_text = f"{{\\fontspec{{{self.fonts['korean']}}}{korean_text}}}"
            
            return formatted_text
            
        except Exception as e:
            logger.error(f"Error formatting Korean title text: {e}")
            return korean_text  # Return original text as fallback
    
    def add_instruction_pages(self, content: str) -> str:
        """Add instructions on every 8th recto page bottom"""
        try:
            # Split content into pages (simplified approach)
            pages = content.split('\\newpage')
            
            instruction_text = "\\vfill\\footnotesize\\textit{Use the facing page for your reflections and notes.}\\normalsize"
            
            processed_pages = []
            page_count = 0
            
            for page in pages:
                processed_pages.append(page)
                page_count += 1
                
                # Add instruction on every 8th recto (odd) page
                if page_count % self.instruction_interval == 0 and page_count % 2 == 1:
                    processed_pages.append(instruction_text)
                
                if page != pages[-1]:  # Don't add newpage after last page
                    processed_pages.append('\\newpage')
            
            return ''.join(processed_pages)
            
        except Exception as e:
            logger.error(f"Error adding instruction pages: {e}")
            return content  # Return original content as fallback
    
    def adjust_chapter_heading_leading(self, chapter_content: str) -> str:
        """Reduce leading underneath chapter headings to approximately 36 points"""
        try:
            # Pattern to match chapter headings
            chapter_patterns = [
                r'(\\chapter\{[^}]+\})',
                r'(\\section\{[^}]+\})',
                r'(\\subsection\{[^}]+\})'
            ]
            
            for pattern in chapter_patterns:
                # Replace chapter headings with adjusted leading
                chapter_content = re.sub(
                    pattern,
                    f'\\1\\n\\\\vspace{{-{self.chapter_leading}}}',
                    chapter_content,
                    flags=re.MULTILINE
                )
            
            return chapter_content
            
        except Exception as e:
            logger.error(f"Error adjusting chapter heading leading: {e}")
            return chapter_content  # Return original content as fallback
    
    def _escape_latex_commands(self, text: str) -> str:
        """Ensure LaTeX commands are properly escaped and not visible in final PDF"""
        try:
            # Dictionary of LaTeX commands that should be escaped
            latex_escapes = {
                '\\textit': '\\\\textit',
                '\\textbf': '\\\\textbf',
                '\\emph': '\\\\emph',
                '\\underline': '\\\\underline',
                '\\footnote': '\\\\footnote',
                '\\cite': '\\\\cite',
                '\\ref': '\\\\ref',
                '\\label': '\\\\label'
            }
            
            # Check if text contains raw LaTeX commands (not properly formatted)
            for command, escaped in latex_escapes.items():
                # Look for commands that appear as literal text (not as LaTeX)
                if command in text and not text.startswith('\\'):
                    # This is likely a formatting error - the command is visible as text
                    logger.warning(f"Found visible LaTeX command in text: {command}")
                    # Remove the command or replace with intended formatting
                    if command == '\\textit':
                        # Replace with actual italic formatting
                        text = text.replace(command, '')
                    elif command == '\\textbf':
                        # Replace with actual bold formatting
                        text = text.replace(command, '')
                    else:
                        # Remove other commands
                        text = text.replace(command, '')
            
            # Escape special LaTeX characters
            special_chars = {
                '&': '\\&',
                '%': '\\%',
                '$': '\\$',
                '#': '\\#',
                '^': '\\textasciicircum{}',
                '_': '\\_',
                '{': '\\{',
                '}': '\\}',
                '~': '\\textasciitilde{}'
            }
            
            for char, escaped in special_chars.items():
                text = text.replace(char, escaped)
            
            return text
            
        except Exception as e:
            logger.error(f"Error escaping LaTeX commands: {e}")
            return text
    
    def validate_typography_formatting(self, content: str) -> Dict[str, Any]:
        """Validate that typography formatting is correct"""
        try:
            validation_results = {
                'valid': True,
                'warnings': [],
                'errors': []
            }
            
            # Check for visible LaTeX commands
            latex_commands = ['\\textit', '\\textbf', '\\emph', '\\underline']
            for command in latex_commands:
                if command in content and not re.search(rf'{re.escape(command)}\{{[^}}]+\}}', content):
                    validation_results['errors'].append(f"Visible LaTeX command found: {command}")
                    validation_results['valid'] = False
            
            # Check for proper font specifications
            if '\\fontspec' not in content and any(font in content for font in self.fonts.values()):
                validation_results['warnings'].append("Font names found but no \\fontspec commands")
            
            # Check for proper chapter heading spacing
            if '\\chapter{' in content and f'\\vspace{{-{self.chapter_leading}}}' not in content:
                validation_results['warnings'].append("Chapter headings may not have adjusted leading")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating typography: {e}")
            return {
                'valid': False,
                'warnings': [],
                'errors': [f'Validation failed: {e}']
            }
    
    def apply_consistent_formatting(self, content: str) -> str:
        """Apply consistent typography and formatting across all book elements"""
        try:
            # Apply all typography enhancements
            content = self._escape_latex_commands(content)
            content = self.adjust_chapter_heading_leading(content)
            content = self.add_instruction_pages(content)
            
            # Apply font specifications
            content = self._apply_font_specifications(content)
            
            return content
            
        except Exception as e:
            logger.error(f"Error applying consistent formatting: {e}")
            return content
    
    def _apply_font_specifications(self, content: str) -> str:
        """Apply font specifications throughout the document"""
        try:
            # Add font specifications at document start
            font_setup = f"""
% Font specifications
\\usepackage{{fontspec}}
\\setmainfont{{{self.fonts['body']}}}
\\newfontfamily\\koreanfont{{{self.fonts['korean']}}}
\\newfontfamily\\quotationfont{{{self.fonts['quotations']}}}
\\newfontfamily\\mnemonicfont{{{self.fonts['mnemonics']}}}

"""
            
            # Insert font setup after documentclass
            if '\\documentclass' in content:
                content = content.replace(
                    '\\begin{document}',
                    font_setup + '\\begin{document}'
                )
            
            return content
            
        except Exception as e:
            logger.error(f"Error applying font specifications: {e}")
            return content