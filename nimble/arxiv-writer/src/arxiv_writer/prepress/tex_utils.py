"""
LaTeX utilities for text processing and formatting.
"""

import re
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def escape_latex(text: str) -> str:
    """
    Escape special LaTeX characters in text.
    
    Args:
        text: Text to escape
        
    Returns:
        LaTeX-escaped text
    """
    if not text:
        return text
    
    # Define LaTeX special characters and their escapes
    latex_escapes = {
        '\\': r'\textbackslash{}',
        '{': r'\{',
        '}': r'\}',
        '$': r'\$',
        '&': r'\&',
        '%': r'\%',
        '#': r'\#',
        '^': r'\textasciicircum{}',
        '_': r'\_',
        '~': r'\textasciitilde{}',
    }
    
    # Apply escapes
    escaped_text = text
    for char, escape in latex_escapes.items():
        escaped_text = escaped_text.replace(char, escape)
    
    return escaped_text


def markdown_to_latex(markdown_text: str) -> str:
    """
    Convert basic Markdown formatting to LaTeX.
    
    Args:
        markdown_text: Markdown text to convert
        
    Returns:
        LaTeX-formatted text
    """
    if not markdown_text:
        return markdown_text
    
    text = markdown_text
    
    # Convert headers
    text = re.sub(r'^### (.+)$', r'\\subsubsection{\1}', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'\\subsection{\1}', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'\\section{\1}', text, flags=re.MULTILINE)
    
    # Convert bold and italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', text)
    text = re.sub(r'\*(.+?)\*', r'\\textit{\1}', text)
    text = re.sub(r'_(.+?)_', r'\\textit{\1}', text)
    
    # Convert code
    text = re.sub(r'`(.+?)`', r'\\texttt{\1}', text)
    
    # Convert lists (basic)
    text = re.sub(r'^- (.+)$', r'\\item \1', text, flags=re.MULTILINE)
    text = re.sub(r'^\* (.+)$', r'\\item \1', text, flags=re.MULTILINE)
    
    # Convert links
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'\\href{\2}{\1}', text)
    
    return text