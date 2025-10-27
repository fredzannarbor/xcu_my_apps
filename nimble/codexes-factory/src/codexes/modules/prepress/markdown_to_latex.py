#!/usr/bin/env python3
"""
Markdown-to-LaTeX conversion utilities for Nimble Ultra pipeline.

This module converts markdown content from LLM responses into properly
formatted LaTeX for inclusion in Nimble Ultra books. It handles:
- Index entries (persons and places)
- Mnemonics with acronyms and bullet lists
- Proper hanging indents, spacing, and LaTeX formatting

This is part of the "markdown-first" clean break approach to eliminate
LaTeX escaping issues in prompts.
"""

import re
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


def convert_index_markdown_to_latex(markdown: str) -> str:
    """
    Convert index markdown to LaTeX with proper formatting.

    Input format (markdown):
        **Place Name** (Type, Region): page, numbers
        **Person Name** (Role, Context): page, numbers

    Output format (LaTeX):
        \\hangindent=0.2in\\hangafter=1 Place Name (Type, Region), \\footnotesize\\textsc{body}:14, \\footnotesize\\textsc{body}:18

    Features:
    - Removes markdown bold markers (**text**)
    - Adds hanging indent for long entries
    - Converts BODY:N page references to small caps
    - Ensures each entry on separate line with proper spacing
    - Deduplicates page references
    - Handles page ranges (BODY:1, BODY:2, BODY:3 -> BODY:1-3)

    Args:
        markdown: Index entries in markdown format

    Returns:
        LaTeX-formatted index entries

    Examples:
        >>> md = "**Austria** (Country, Europe): 14, 18\\n**Berlin** (City, Germany): 5-7, 12"
        >>> latex = convert_index_markdown_to_latex(md)
        >>> "\\\\hangindent" in latex
        True
        >>> "\\\\textsc{body}" in latex
        True
    """
    if not markdown or not isinstance(markdown, str):
        return ""

    # Remove markdown header if present (will be added by _format_section)
    content = re.sub(r'^#\s+Index of [A-Za-z]+\s*\n+', '', markdown, flags=re.MULTILINE)

    # Remove markdown bold markers
    content = re.sub(r'\*\*([^*]+?)\*\*', r'\1', content)

    # Fix LLM quirk: entries running together on same line
    # Pattern: "BODY:36 Europe (Continent)" -> "BODY:36\n\nEurope (Continent)"
    content = re.sub(
        r'(BODY:\d+(?:[-,]\d+)?)\s+([A-Z][a-zA-Z\s]+\s*\()',
        r'\1\n\n\2',
        content
    )

    # Fix entries separated by comma at wrong spot
    # Example: "Germany, BODY:10,Berlin (Germany)" -> "Germany, BODY:10\n\nBerlin (Germany)"
    content = re.sub(
        r'(BODY:\d+(?:[-,]\s*BODY:\d+)*),\s*([A-Z][a-zA-Z\s]+\s*\()',
        r'\1\n\n\2',
        content
    )

    # Collapse page ranges helper
    def collapse_page_ranges(page_refs: str) -> str:
        """Collapse consecutive page numbers into ranges (e.g., '1, 2, 3' -> '1-3')"""
        # Extract all page numbers
        pages = re.findall(r'\d+', page_refs)
        if not pages:
            return page_refs

        pages = [int(p) for p in pages]
        pages.sort()

        # Group consecutive pages
        ranges = []
        start = pages[0]
        end = pages[0]

        for i in range(1, len(pages)):
            if pages[i] == end + 1:
                end = pages[i]
            else:
                # Add previous range
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = end = pages[i]

        # Add final range
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")

        return ', '.join(ranges)

    # Deduplicate page references and collapse ranges
    def deduplicate_page_refs(line: str) -> str:
        """Remove duplicate BODY:N references from a line and collapse consecutive pages."""
        body_refs = re.findall(r'BODY:\d+(?:[-,]\d+)?', line)
        if len(body_refs) > 1:
            # Remove duplicates while preserving order
            seen = set()
            unique_refs = []
            for ref in body_refs:
                if ref not in seen:
                    seen.add(ref)
                    unique_refs.append(ref)

            # If we removed duplicates, reconstruct the line
            if len(unique_refs) < len(body_refs):
                name_part = line.split('BODY:')[0]
                line = name_part + ', '.join(unique_refs)

        # AFTER deduplication, collapse ranges
        name_part = line.split('BODY:')[0] if 'BODY:' in line else line
        refs_part = line[len(name_part):] if 'BODY:' in line else ''

        if refs_part:
            collapsed = collapse_page_ranges(refs_part)
            line = name_part + collapsed

        return line

    # Apply deduplication and range collapsing line by line
    lines = content.split('\n')
    content = '\n'.join(deduplicate_page_refs(line) for line in lines)

    # Convert BODY:N references to small caps
    def format_body_ref(match):
        page_num = match.group(1)
        return f'\\footnotesize\\textsc{{body}}:{page_num}'

    content = re.sub(r'BODY:(\d+(?:[-,]\d+)?)', format_body_ref, content)

    # Add hanging indent to each entry with letter headings
    lines = content.split('\n')
    formatted_lines = []
    current_letter = None

    for line in lines:
        line = line.strip()
        if not line:
            continue  # Skip empty lines

        # Detect first letter for heading (skip markdown markers and LaTeX commands)
        cleaned_line = re.sub(r'^[\*\\]+', '', line)
        first_char = cleaned_line[0].upper() if cleaned_line else None

        # Add letter heading if we're starting a new letter
        if first_char and first_char.isalpha() and first_char != current_letter:
            if current_letter is not None:
                # Add extra space before new letter section
                formatted_lines.append("\\vspace{12pt}")
            # Add letter heading
            formatted_lines.append(f"\\subsection*{{{first_char}}}")
            formatted_lines.append(f"\\addcontentsline{{toc}}{{subsection}}{{{first_char}}}")
            formatted_lines.append("")  # Blank line after heading
            current_letter = first_char

        # Add hanging indent command with explicit paragraph end
        # CRITICAL: Use \par to end paragraph and reset hanging indent for next entry
        formatted_lines.append(f"\\hangindent=0.2in\\hangafter=1 {line}\\par")
        formatted_lines.append("\\vspace{6pt}")  # Vertical space between entries

    return '\n'.join(formatted_lines)


def convert_mnemonics_markdown_to_latex(markdown: str) -> str:
    """
    Convert mnemonics markdown to LaTeX with proper structure.

    Input format (markdown):
        ## Mnemonics

        **ACRONYM** (Theme Description)

        - **Letter**: Meaning
        - **Letter**: Meaning

    Output format (LaTeX):
        \\chapter*{Mnemonics}
        \\addcontentsline{toc}{chapter}{Mnemonics}

        \\textbf{ACRONYM} (Theme Description)

        \\begin{itemize}
            \\item \\textbf{Letter} - Meaning
            \\item \\textbf{Letter} - Meaning
        \\end{itemize}

        \\cleardoublepage

    Features:
    - Converts ## headers to \\chapter*{}
    - Converts **bold** to \\textbf{}
    - Converts bullet lists to itemize environments
    - Adds proper spacing and cleardoublepage
    - Removes any \\documentclass or \\begin{document} artifacts

    Args:
        markdown: Mnemonics content in markdown format

    Returns:
        LaTeX-formatted mnemonics

    Examples:
        >>> md = "## Mnemonics\\n\\n**S.A.F.E.** (Security Acronym)\\n\\n- **S**: Secure\\n- **A**: Assess"
        >>> latex = convert_mnemonics_markdown_to_latex(md)
        >>> "\\\\chapter*{Mnemonics}" in latex
        True
        >>> "\\\\begin{itemize}" in latex
        True
    """
    if not markdown or not isinstance(markdown, str):
        return ""

    content = markdown.strip()

    # Remove any document preamble artifacts (LLMs sometimes add these)
    content = re.sub(r'\\documentclass.*?\n', '', content)
    content = re.sub(r'\\begin\{document\}', '', content)
    content = re.sub(r'\\end\{document\}', '', content)
    content = re.sub(r'% .*?\n', '', content)  # Remove comments

    # If content is already LaTeX (has \chapter or \section), return as-is
    if '\\chapter' in content or '\\section' in content:
        logger.info("Content appears to already be LaTeX, minimal processing")
        # Just ensure proper spacing and cleardoublepage
        if not content.strip().endswith("\\cleardoublepage"):
            content = content.rstrip() + "\n\n\\cleardoublepage\n"
        return content

    # Convert ## Headers to \chapter*{}
    def convert_header(match):
        level = len(match.group(1))
        title = match.group(2).strip()
        if level == 2:  # ## Header
            return f"\\chapter*{{{title}}}\n\\addcontentsline{{toc}}{{chapter}}{{{title}}}\n"
        elif level == 3:  # ### Subheader
            return f"\\section*{{{title}}}\n"
        else:
            return f"\\subsection*{{{title}}}\n"

    content = re.sub(r'^(#{2,})\s+(.+)$', convert_header, content, flags=re.MULTILINE)

    # Escape LaTeX special characters before conversion
    # Must escape & because it's a table alignment character in LaTeX
    content = content.replace('&', '\\&')

    # Convert **bold** to \textbf{}
    content = re.sub(r'\*\*([^*]+?)\*\*', r'\\textbf{\1}', content)

    # Convert bullet lists to itemize environments
    # This is more complex - need to find bullet groups
    lines = content.split('\n')
    result_lines = []
    in_list = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Check if line is a bullet
        is_bullet = stripped.startswith('-') or stripped.startswith('*') or stripped.startswith('•')

        if is_bullet and not in_list:
            # Start of list
            result_lines.append('\n\\begin{itemize}')
            in_list = True
        elif not is_bullet and in_list and stripped:
            # End of list (non-empty non-bullet line)
            result_lines.append('\\end{itemize}\n')
            in_list = False

        if is_bullet:
            # Convert bullet line to \item
            # Remove leading bullet marker
            item_text = re.sub(r'^\s*[-*•]\s+', '', stripped)
            result_lines.append(f'    \\item {item_text}')
        elif stripped or not in_list:
            # Non-bullet lines (like acrostic headings) need \par to close paragraph
            if stripped and not in_list and not line.startswith('\\'):
                # This is a content line (like "BLOCK (...)"), add \par
                result_lines.append(f"{line}\\par")
            else:
                # Keep LaTeX commands and empty lines as-is
                result_lines.append(line)

    # Close list if still open at end
    if in_list:
        result_lines.append('\\end{itemize}\n')

    content = '\n'.join(result_lines)

    # Add proper spacing around structural elements
    content = re.sub(r'(\\chapter\*\{[^}]+\})\s*', r'\1\n', content)
    content = re.sub(r'(\\addcontentsline\{[^}]+\}\{[^}]+\}\{[^}]+\})\s*', r'\1\n\n', content)
    content = re.sub(r'\\begin\{itemize\}', r'\n\\begin{itemize}\n', content)
    content = re.sub(r'\\end\{itemize\}', r'\n\\end{itemize}\n\n', content)

    # Ensure it ends with cleardoublepage
    if not content.strip().endswith("\\cleardoublepage"):
        content = content.rstrip() + "\n\n\\cleardoublepage\n"

    return content


def escape_latex(text: str) -> str:
    """
    Escape special LaTeX characters in text.

    This is a helper function for any remaining text that needs escaping.
    Note: In the markdown-first approach, we minimize the need for this
    by requesting markdown from LLMs and converting it programmatically.

    Args:
        text: Text to escape

    Returns:
        LaTeX-safe text
    """
    if not text:
        return ""

    # Characters that need escaping in LaTeX
    replacements = {
        '\\': r'\textbackslash{}',
        '{': r'\{',
        '}': r'\}',
        '$': r'\$',
        '&': r'\&',
        '%': r'\%',
        '#': r'\#',
        '_': r'\_',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
    }

    # Apply replacements
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)

    return text


# Export public API
__all__ = [
    'convert_index_markdown_to_latex',
    'convert_mnemonics_markdown_to_latex',
    'escape_latex'
]
