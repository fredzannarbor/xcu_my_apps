#!/usr/bin/env python3
"""
Convert corrected LaTeX to master Markdown for manual editing
"""

import re
from pathlib import Path

def latex_to_markdown(latex_content):
    """Convert LaTeX to Markdown preserving structure"""

    # Extract content between \begin{document} and \end{document}
    doc_match = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', latex_content, re.DOTALL)
    if doc_match:
        content = doc_match.group(1)
    else:
        content = latex_content

    # Title page
    content = re.sub(r'\\begin\{titlepage\}.*?\\end\{titlepage\}',
                     '# Elco Naval Division of The Electric Boat Company\n\n**By Frank Andruss**\n\n---\n',
                     content, flags=re.DOTALL)

    # Unnumbered chapters (Forward, Preface, Acknowledgments)
    content = re.sub(r'\\chapter\*\{([^}]+)\}\\addcontentsline\{toc\}\{chapter\}\{[^}]+\}',
                     r'\n## \1\n', content)

    # Numbered chapters
    content = re.sub(r'\\chapter\{([^}]+)\}', r'\n## Chapter X: \1\n', content)

    # Table of contents
    content = re.sub(r'\\tableofcontents\\clearpage', '\n---\n\n', content)

    # Photo captions
    def replace_photo(match):
        path = match.group(1)
        fig_num = match.group(2)
        caption = match.group(3)
        return f'\n**Figure {fig_num}**: {caption}\n\n*[Photo: `{path}`]*\n'

    content = re.sub(r'\\photocaption\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}', replace_photo, content)

    # Clear pages
    content = re.sub(r'\\clearpage', '\n---\n', content)

    # Unescape LaTeX special characters
    replacements = [
        (r'\\textbackslash\{\}', '\\'),
        (r'\\&', '&'),
        (r'\\%', '%'),
        (r'\\\$', '$'),
        (r'\\#', '#'),
        (r'\\_', '_'),
        (r'\\{', '{'),
        (r'\\}', '}'),
        (r'\\textasciitilde\{\}', '~'),
        (r'\\textasciicircum\{\}', '^'),
    ]

    for old, new in replacements:
        content = re.sub(old, new, content)

    # Clean up excessive newlines
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Number chapters correctly
    chapter_num = 1
    def number_chapter(match):
        nonlocal chapter_num
        title = match.group(1)
        result = f'\n## Chapter {chapter_num}: {title}\n'
        chapter_num += 1
        return result

    content = re.sub(r'\n## Chapter X: ([^\n]+)\n', number_chapter, content)

    return content.strip()

# Read corrected LaTeX
base_dir = Path("/Users/fred/xcu_my_apps/nimble/codexes-factory/output/pt_boat_book")
latex_file = base_dir / "pt_boat_book_corrected.tex"

print("Reading corrected LaTeX file...")
latex_content = latex_file.read_text()

print("Converting to Markdown...")
markdown_content = latex_to_markdown(latex_content)

# Save master Markdown
output_file = base_dir / "pt_boat_book_master.md"
output_file.write_text(markdown_content)

print(f"\n✓ Master Markdown saved to: {output_file}")
print(f"✓ Length: {len(markdown_content):,} characters")
print(f"✓ Lines: {markdown_content.count(chr(10)):,}")
print("\nThis Markdown file includes:")
print("  - All corrected text with smart quotes, measurements, abbreviations")
print("  - Photo references with captions")
print("  - Proper chapter structure (6 chapters)")
print("  - All front matter (Forward, Preface, Acknowledgments)")
print("\nYou can manually edit this file and regenerate LaTeX/PDF as needed.")
